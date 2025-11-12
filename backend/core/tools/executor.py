"""
Tool executor for running tools safely and efficiently
"""
from typing import Dict, List, Optional, Any
import asyncio
import logging
import json
from datetime import datetime

from .base import BaseTool, ToolResult, ToolExecutionContext
from .registry import ToolRegistry, get_global_registry

logger = logging.getLogger(__name__)


class ExecutionRecord(dict):
    """Record of a tool execution"""

    def __init__(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        result: ToolResult,
        execution_time: float,
        timestamp: datetime,
        context: Optional[ToolExecutionContext] = None
    ):
        super().__init__(
            tool_name=tool_name,
            arguments=arguments,
            result=result.dict(),
            execution_time=execution_time,
            timestamp=timestamp.isoformat(),
            context=context.dict() if context else None
        )


class ToolExecutor:
    """Executor for running tools with monitoring and control"""

    def __init__(self, registry: Optional[ToolRegistry] = None):
        """
        Initialize executor

        Args:
            registry: Tool registry to use (default: global registry)
        """
        self.registry = registry or get_global_registry()
        self._execution_history: List[ExecutionRecord] = []
        self._max_history_size = 1000

    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        context: Optional[ToolExecutionContext] = None,
        timeout: Optional[float] = 30.0
    ) -> ToolResult:
        """
        Execute a single tool

        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments
            context: Execution context
            timeout: Maximum execution time in seconds

        Returns:
            ToolResult with execution outcome
        """
        start_time = asyncio.get_event_loop().time()

        # Get tool from registry
        tool = self.registry.get(tool_name)
        if not tool:
            result = ToolResult.error_result(
                f"Tool '{tool_name}' not found in registry"
            )
            self._record_execution(tool_name, arguments, result, 0, context)
            return result

        logger.info(f"Executing tool: {tool_name} with args: {arguments}")

        # Execute tool safely
        try:
            result = await tool.safe_execute(arguments, context, timeout)
        except Exception as e:
            logger.error(f"Unexpected error executing tool '{tool_name}': {e}")
            result = ToolResult.error_result(
                f"Unexpected error: {str(e)}"
            )

        # Record execution
        execution_time = asyncio.get_event_loop().time() - start_time
        self._record_execution(tool_name, arguments, result, execution_time, context)

        logger.info(
            f"Tool '{tool_name}' executed in {execution_time:.3f}s, "
            f"success: {result.success}"
        )

        return result

    async def execute_multiple(
        self,
        tool_calls: List[Dict[str, Any]],
        context: Optional[ToolExecutionContext] = None,
        parallel: bool = False,
        timeout: Optional[float] = 30.0
    ) -> List[ToolResult]:
        """
        Execute multiple tools

        Args:
            tool_calls: List of tool calls with 'name' and 'arguments'
            context: Execution context
            parallel: Whether to execute in parallel
            timeout: Maximum execution time per tool

        Returns:
            List of ToolResult objects
        """
        if parallel:
            # Execute all tools concurrently
            tasks = [
                self.execute_tool(
                    call["name"],
                    call.get("arguments", {}),
                    context,
                    timeout
                )
                for call in tool_calls
            ]
            return await asyncio.gather(*tasks, return_exceptions=False)
        else:
            # Execute tools sequentially
            results = []
            for call in tool_calls:
                result = await self.execute_tool(
                    call["name"],
                    call.get("arguments", {}),
                    context,
                    timeout
                )
                results.append(result)
            return results

    async def execute_from_llm_call(
        self,
        tool_call: Dict[str, Any],
        context: Optional[ToolExecutionContext] = None,
        timeout: Optional[float] = 30.0
    ) -> ToolResult:
        """
        Execute tool from LLM tool call format

        Args:
            tool_call: Tool call in LLM format with 'name' and 'arguments'
            context: Execution context
            timeout: Maximum execution time

        Returns:
            ToolResult
        """
        tool_name = tool_call.get("name")
        arguments_str = tool_call.get("arguments", "{}")

        # Parse arguments if string
        if isinstance(arguments_str, str):
            try:
                arguments = json.loads(arguments_str)
            except json.JSONDecodeError as e:
                return ToolResult.error_result(
                    f"Failed to parse arguments: {str(e)}"
                )
        else:
            arguments = arguments_str

        return await self.execute_tool(tool_name, arguments, context, timeout)

    def _record_execution(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        result: ToolResult,
        execution_time: float,
        context: Optional[ToolExecutionContext] = None
    ):
        """Record tool execution in history"""
        record = ExecutionRecord(
            tool_name=tool_name,
            arguments=arguments,
            result=result,
            execution_time=execution_time,
            timestamp=datetime.now(),
            context=context
        )

        self._execution_history.append(record)

        # Limit history size
        if len(self._execution_history) > self._max_history_size:
            self._execution_history = self._execution_history[-self._max_history_size:]

    def get_execution_history(
        self,
        tool_name: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[ExecutionRecord]:
        """
        Get execution history

        Args:
            tool_name: Optional filter by tool name
            limit: Maximum number of records to return

        Returns:
            List of execution records
        """
        history = self._execution_history

        if tool_name:
            history = [r for r in history if r["tool_name"] == tool_name]

        if limit:
            history = history[-limit:]

        return history

    def clear_history(self):
        """Clear execution history"""
        self._execution_history.clear()

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get execution statistics

        Returns:
            Dictionary with statistics
        """
        if not self._execution_history:
            return {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "average_execution_time": 0,
                "tools_used": {}
            }

        total = len(self._execution_history)
        successful = sum(
            1 for r in self._execution_history
            if r["result"]["success"]
        )
        failed = total - successful

        avg_time = sum(
            r["execution_time"] for r in self._execution_history
        ) / total

        # Count tool usage
        tools_used = {}
        for record in self._execution_history:
            tool_name = record["tool_name"]
            if tool_name not in tools_used:
                tools_used[tool_name] = {
                    "count": 0,
                    "success": 0,
                    "failed": 0,
                    "avg_time": 0
                }

            tools_used[tool_name]["count"] += 1
            if record["result"]["success"]:
                tools_used[tool_name]["success"] += 1
            else:
                tools_used[tool_name]["failed"] += 1

        # Calculate average time per tool
        for tool_name in tools_used:
            tool_records = [
                r for r in self._execution_history
                if r["tool_name"] == tool_name
            ]
            if tool_records:
                tools_used[tool_name]["avg_time"] = sum(
                    r["execution_time"] for r in tool_records
                ) / len(tool_records)

        return {
            "total_executions": total,
            "successful_executions": successful,
            "failed_executions": failed,
            "success_rate": successful / total if total > 0 else 0,
            "average_execution_time": avg_time,
            "tools_used": tools_used
        }


# Global executor instance
_global_executor: Optional[ToolExecutor] = None


def get_global_executor() -> ToolExecutor:
    """
    Get the global tool executor instance

    Returns:
        Global ToolExecutor instance
    """
    global _global_executor
    if _global_executor is None:
        _global_executor = ToolExecutor()
    return _global_executor


async def execute_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    context: Optional[ToolExecutionContext] = None,
    timeout: Optional[float] = 30.0
) -> ToolResult:
    """
    Execute a tool using the global executor

    Args:
        tool_name: Name of the tool
        arguments: Tool arguments
        context: Execution context
        timeout: Maximum execution time

    Returns:
        ToolResult
    """
    executor = get_global_executor()
    return await executor.execute_tool(tool_name, arguments, context, timeout)
