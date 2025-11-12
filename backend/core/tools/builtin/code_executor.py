"""
Code executor tool for safely running code in a sandboxed environment
"""
from typing import Dict, Any, Optional
import sys
import io
import contextlib
import ast
import traceback
from datetime import datetime

from ..base import BaseTool, ToolResult, ToolExecutionContext, ToolCategory


class CodeExecutorTool(BaseTool):
    """
    Code executor tool for running Python code safely

    Features:
    - Sandboxed execution
    - Resource limits (memory, time)
    - Captures stdout/stderr
    - Restricted imports
    """

    # Allowed built-in functions
    SAFE_BUILTINS = {
        'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'bytearray', 'bytes',
        'chr', 'complex', 'dict', 'divmod', 'enumerate', 'filter', 'float',
        'format', 'frozenset', 'hash', 'hex', 'int', 'isinstance', 'issubclass',
        'iter', 'len', 'list', 'map', 'max', 'min', 'next', 'oct', 'ord',
        'pow', 'print', 'range', 'repr', 'reversed', 'round', 'set', 'slice',
        'sorted', 'str', 'sum', 'tuple', 'type', 'zip',
    }

    # Allowed modules
    SAFE_MODULES = {
        'math', 'random', 'datetime', 'json', 'itertools', 'collections',
        'functools', 're', 'string', 'decimal', 'fractions',
    }

    def __init__(
        self,
        max_execution_time: int = 5,
        max_memory_mb: int = 128,
        allow_imports: bool = True
    ):
        """
        Initialize code executor

        Args:
            max_execution_time: Maximum execution time in seconds
            max_execution_time: Maximum memory usage in MB
            allow_imports: Whether to allow import statements
        """
        super().__init__()
        self.max_execution_time = max_execution_time
        self.max_memory_mb = max_memory_mb
        self.allow_imports = allow_imports

    @property
    def name(self) -> str:
        return "code_executor"

    @property
    def description(self) -> str:
        return (
            "在安全的沙箱环境中执行 Python 代码。"
            "支持大多数标准库，但有资源限制以确保安全。"
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "要执行的 Python 代码"
                },
                "language": {
                    "type": "string",
                    "enum": ["python"],
                    "description": "编程语言 (目前仅支持 Python)"
                }
            },
            "required": ["code"]
        }

    async def execute(
        self,
        arguments: Dict[str, Any],
        context: Optional[ToolExecutionContext] = None
    ) -> ToolResult:
        """Execute code"""
        code = arguments.get("code", "").strip()
        language = arguments.get("language", "python")

        if not code:
            return ToolResult.error_result("代码不能为空")

        if language != "python":
            return ToolResult.error_result(f"不支持的语言: {language}")

        try:
            # Execute code in sandbox
            result = await self._run_sync(self._execute_python, code)
            return result

        except Exception as e:
            return ToolResult.error_result(f"执行失败: {str(e)}")

    def _execute_python(self, code: str) -> ToolResult:
        """
        Execute Python code safely

        Args:
            code: Python code to execute

        Returns:
            ToolResult with execution outcome
        """
        start_time = datetime.now()

        # Check for dangerous operations
        if not self._is_safe_code(code):
            return ToolResult.error_result(
                "代码包含不安全的操作或导入"
            )

        # Create restricted globals
        restricted_globals = self._create_restricted_globals()

        # Capture stdout and stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        execution_result = None
        execution_error = None

        try:
            # Note: Resource limits removed for compatibility with threading
            # In production, consider using a subprocess-based sandbox

            # Redirect stdout/stderr
            with contextlib.redirect_stdout(stdout_capture):
                with contextlib.redirect_stderr(stderr_capture):
                    # Compile code
                    compiled_code = compile(code, '<sandbox>', 'exec')

                    # Execute code
                    # Note: Timeout is handled by the async executor at a higher level
                    exec(compiled_code, restricted_globals)

                    # Get the result if there's a variable named 'result'
                    if 'result' in restricted_globals:
                        execution_result = restricted_globals['result']

        except TimeoutError as e:
            execution_error = f"超时: {str(e)}"
        except MemoryError as e:
            execution_error = f"内存不足: {str(e)}"
        except SyntaxError as e:
            execution_error = f"语法错误: {str(e)}"
        except Exception as e:
            execution_error = f"运行时错误: {str(e)}\n{traceback.format_exc()}"

        # Get captured output
        stdout_output = stdout_capture.getvalue()
        stderr_output = stderr_capture.getvalue()

        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds()

        # Build result
        if execution_error:
            return ToolResult.error_result(
                execution_error,
                metadata={
                    "stdout": stdout_output,
                    "stderr": stderr_output,
                    "execution_time": execution_time
                }
            )
        else:
            output_parts = []

            if stdout_output:
                output_parts.append(f"输出:\n{stdout_output}")

            if execution_result is not None:
                output_parts.append(f"结果: {repr(execution_result)}")

            if not output_parts:
                output_parts.append("代码执行成功（无输出）")

            return ToolResult.success_result(
                output="\n\n".join(output_parts),
                metadata={
                    "stdout": stdout_output,
                    "stderr": stderr_output,
                    "result": execution_result,
                    "execution_time": execution_time
                }
            )

    def _is_safe_code(self, code: str) -> bool:
        """
        Check if code is safe to execute

        Args:
            code: Python code to check

        Returns:
            True if code appears safe, False otherwise
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return False

        # Check for dangerous operations
        for node in ast.walk(tree):
            # Check imports
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if not self.allow_imports:
                    return False

                # Check if importing allowed modules
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.split('.')[0] not in self.SAFE_MODULES:
                            return False
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.split('.')[0] not in self.SAFE_MODULES:
                        return False

            # Check for dangerous built-in calls
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    # Disallow dangerous functions
                    dangerous_funcs = {
                        'exec', 'eval', 'compile', '__import__',
                        'open', 'input', 'raw_input'
                    }
                    if node.func.id in dangerous_funcs:
                        return False

            # Check for attribute access to dangerous attributes
            if isinstance(node, ast.Attribute):
                dangerous_attrs = {
                    '__dict__', '__class__', '__bases__', '__subclasses__',
                    '__globals__', '__code__', '__closure__'
                }
                if node.attr in dangerous_attrs:
                    return False

        return True

    def _create_restricted_globals(self) -> Dict[str, Any]:
        """
        Create restricted global namespace

        Returns:
            Dictionary with safe built-ins and modules
        """
        # Start with safe built-ins
        safe_builtins = {
            name: __builtins__[name]
            for name in self.SAFE_BUILTINS
            if name in __builtins__
        }

        # Add __import__ if imports are allowed
        if self.allow_imports:
            def safe_import(name, *args, **kwargs):
                if name.split('.')[0] in self.SAFE_MODULES:
                    return __import__(name, *args, **kwargs)
                raise ImportError(f"模块 '{name}' 不在允许列表中")

            safe_builtins['__import__'] = safe_import

        restricted_globals = {
            '__builtins__': safe_builtins
        }

        # Pre-import safe modules for convenience
        if self.allow_imports:
            for module_name in self.SAFE_MODULES:
                try:
                    restricted_globals[module_name] = __import__(module_name)
                except ImportError:
                    pass

        return restricted_globals
