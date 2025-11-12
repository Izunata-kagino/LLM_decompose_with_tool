"""
Base classes for tool system
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field
import asyncio
from concurrent.futures import ThreadPoolExecutor


class ToolParameter(BaseModel):
    """Tool parameter schema"""
    type: str
    description: Optional[str] = None
    enum: Optional[List[Any]] = None
    default: Optional[Any] = None
    required: bool = True


class ToolSchema(BaseModel):
    """Complete tool schema"""
    name: str
    description: str
    parameters: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_tool(cls, tool: "BaseTool") -> "ToolSchema":
        """Create schema from tool instance"""
        return cls(
            name=tool.name,
            description=tool.description,
            parameters=tool.parameters
        )


class ToolExecutionContext(BaseModel):
    """Context for tool execution"""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True


class ToolResult(BaseModel):
    """Result from tool execution"""
    success: bool
    output: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def success_result(cls, output: Any, metadata: Optional[Dict[str, Any]] = None) -> "ToolResult":
        """Create a success result"""
        return cls(
            success=True,
            output=output,
            error=None,
            metadata=metadata or {}
        )

    @classmethod
    def error_result(cls, error: str, metadata: Optional[Dict[str, Any]] = None) -> "ToolResult":
        """Create an error result"""
        return cls(
            success=False,
            output=None,
            error=error,
            metadata=metadata or {}
        )

    def __str__(self) -> str:
        """String representation for LLM consumption"""
        if self.success:
            return str(self.output)
        else:
            return f"Error: {self.error}"


class BaseTool(ABC):
    """Base class for all tools"""

    def __init__(self):
        self._executor = ThreadPoolExecutor(max_workers=4)

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description"""
        pass

    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """Tool parameters in JSON Schema format"""
        pass

    @abstractmethod
    async def execute(
        self,
        arguments: Dict[str, Any],
        context: Optional[ToolExecutionContext] = None
    ) -> ToolResult:
        """
        Execute the tool with given arguments

        Args:
            arguments: Tool arguments
            context: Execution context

        Returns:
            ToolResult with success status and output/error
        """
        pass

    def get_schema(self) -> ToolSchema:
        """Get tool schema"""
        return ToolSchema.from_tool(self)

    def validate_arguments(self, arguments: Dict[str, Any]) -> bool:
        """
        Validate tool arguments against schema

        Args:
            arguments: Arguments to validate

        Returns:
            True if valid, False otherwise
        """
        required = self.parameters.get("required", [])
        properties = self.parameters.get("properties", {})

        # Check required parameters
        for req in required:
            if req not in arguments:
                return False

        # Check parameter types (basic validation)
        for key, value in arguments.items():
            if key not in properties:
                continue

            expected_type = properties[key].get("type")
            if expected_type == "string" and not isinstance(value, str):
                return False
            elif expected_type == "integer" and not isinstance(value, int):
                return False
            elif expected_type == "number" and not isinstance(value, (int, float)):
                return False
            elif expected_type == "boolean" and not isinstance(value, bool):
                return False
            elif expected_type == "array" and not isinstance(value, list):
                return False
            elif expected_type == "object" and not isinstance(value, dict):
                return False

        return True

    async def safe_execute(
        self,
        arguments: Dict[str, Any],
        context: Optional[ToolExecutionContext] = None,
        timeout: Optional[float] = 30.0
    ) -> ToolResult:
        """
        Safely execute tool with validation and timeout

        Args:
            arguments: Tool arguments
            context: Execution context
            timeout: Maximum execution time in seconds

        Returns:
            ToolResult
        """
        # Validate arguments
        if not self.validate_arguments(arguments):
            return ToolResult.error_result(
                f"Invalid arguments for tool '{self.name}'"
            )

        try:
            # Execute with timeout
            if timeout:
                result = await asyncio.wait_for(
                    self.execute(arguments, context),
                    timeout=timeout
                )
            else:
                result = await self.execute(arguments, context)

            return result

        except asyncio.TimeoutError:
            return ToolResult.error_result(
                f"Tool execution timed out after {timeout} seconds"
            )
        except Exception as e:
            return ToolResult.error_result(
                f"Tool execution failed: {str(e)}"
            )

    async def _run_sync(self, func, *args, **kwargs):
        """Run synchronous function in thread pool"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            lambda: func(*args, **kwargs)
        )

    def __del__(self):
        """Cleanup"""
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=False)


class ToolCategory:
    """Tool categories"""
    COMPUTATION = "computation"
    FILE_SYSTEM = "file_system"
    NETWORK = "network"
    CODE_EXECUTION = "code_execution"
    DATA_PROCESSING = "data_processing"
    UTILITIES = "utilities"
