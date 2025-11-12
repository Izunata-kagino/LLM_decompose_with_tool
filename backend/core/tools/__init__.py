"""
Tool system for LLM integration

This module provides a complete tool system for LLM applications:
- Base classes for creating custom tools
- Tool registry for managing tools
- Tool executor for running tools safely
- Built-in tools for common operations
"""

from .base import (
    BaseTool,
    ToolResult,
    ToolSchema,
    ToolExecutionContext,
    ToolCategory,
)

from .registry import (
    ToolRegistry,
    get_global_registry,
    register_tool,
    get_tool,
)

from .executor import (
    ToolExecutor,
    ExecutionRecord,
    get_global_executor,
    execute_tool,
)

from .builtin import (
    CalculatorTool,
    FileOperationsTool,
    WebSearchTool,
    CodeExecutorTool,
)

__all__ = [
    # Base classes
    "BaseTool",
    "ToolResult",
    "ToolSchema",
    "ToolExecutionContext",
    "ToolCategory",
    # Registry
    "ToolRegistry",
    "get_global_registry",
    "register_tool",
    "get_tool",
    # Executor
    "ToolExecutor",
    "ExecutionRecord",
    "get_global_executor",
    "execute_tool",
    # Built-in tools
    "CalculatorTool",
    "FileOperationsTool",
    "WebSearchTool",
    "CodeExecutorTool",
]


def initialize_builtin_tools(
    workspace_dir: str = None,
    allow_file_delete: bool = False,
    allow_code_execution: bool = True,
    web_search_api_key: str = None
):
    """
    Initialize and register all built-in tools

    Args:
        workspace_dir: Workspace directory for file operations
        allow_file_delete: Whether to allow file deletion
        allow_code_execution: Whether to enable code execution tool
        web_search_api_key: API key for web search (optional)

    Returns:
        List of registered tool names
    """
    registry = get_global_registry()

    # Calculator
    calculator = CalculatorTool()
    registry.register(calculator, category=ToolCategory.COMPUTATION)

    # File operations
    file_ops = FileOperationsTool(
        workspace_dir=workspace_dir,
        allow_delete=allow_file_delete
    )
    registry.register(file_ops, category=ToolCategory.FILE_SYSTEM)

    # Web search
    web_search = WebSearchTool(api_key=web_search_api_key)
    registry.register(web_search, category=ToolCategory.NETWORK)

    # Code executor
    if allow_code_execution:
        code_executor = CodeExecutorTool()
        registry.register(code_executor, category=ToolCategory.CODE_EXECUTION)

    return registry.list_tools()
