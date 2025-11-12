"""
File operations tool for reading, writing, and managing files
"""
from typing import Dict, Any, Optional
import os
import json
from pathlib import Path

from ..base import BaseTool, ToolResult, ToolExecutionContext, ToolCategory


class FileOperationsTool(BaseTool):
    """
    File operations tool for safe file system operations

    Supports:
    - read: Read file contents
    - write: Write content to file
    - append: Append content to file
    - list: List directory contents
    - exists: Check if file/directory exists
    - delete: Delete file (requires explicit permission)
    """

    def __init__(self, workspace_dir: Optional[str] = None, allow_delete: bool = False):
        """
        Initialize file operations tool

        Args:
            workspace_dir: Root directory for file operations (for safety)
            allow_delete: Whether to allow file deletion
        """
        super().__init__()
        self.workspace_dir = Path(workspace_dir) if workspace_dir else Path.cwd()
        self.allow_delete = allow_delete

    @property
    def name(self) -> str:
        return "file_operations"

    @property
    def description(self) -> str:
        return (
            "执行文件系统操作，包括读取、写入、列出文件等。"
            "操作: read, write, append, list, exists, delete"
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["read", "write", "append", "list", "exists", "delete"],
                    "description": "要执行的操作类型"
                },
                "path": {
                    "type": "string",
                    "description": "文件或目录的路径"
                },
                "content": {
                    "type": "string",
                    "description": "要写入或追加的内容 (仅用于 write/append 操作)"
                },
                "encoding": {
                    "type": "string",
                    "description": "文件编码 (默认: utf-8)"
                }
            },
            "required": ["operation", "path"]
        }

    async def execute(
        self,
        arguments: Dict[str, Any],
        context: Optional[ToolExecutionContext] = None
    ) -> ToolResult:
        """Execute file operation"""
        operation = arguments.get("operation")
        path_str = arguments.get("path")
        content = arguments.get("content", "")
        encoding = arguments.get("encoding", "utf-8")

        if not operation or not path_str:
            return ToolResult.error_result("operation 和 path 是必需参数")

        # Resolve path and check if it's within workspace
        try:
            file_path = self._resolve_path(path_str)
        except ValueError as e:
            return ToolResult.error_result(str(e))

        # Execute operation
        try:
            if operation == "read":
                result = await self._read_file(file_path, encoding)
            elif operation == "write":
                result = await self._write_file(file_path, content, encoding)
            elif operation == "append":
                result = await self._append_file(file_path, content, encoding)
            elif operation == "list":
                result = await self._list_directory(file_path)
            elif operation == "exists":
                result = await self._check_exists(file_path)
            elif operation == "delete":
                result = await self._delete_file(file_path)
            else:
                return ToolResult.error_result(f"未知操作: {operation}")

            return result

        except Exception as e:
            return ToolResult.error_result(f"{operation} 操作失败: {str(e)}")

    def _resolve_path(self, path_str: str) -> Path:
        """
        Resolve and validate path

        Args:
            path_str: Path string

        Returns:
            Resolved Path object

        Raises:
            ValueError: If path is outside workspace
        """
        # Resolve path
        path = Path(path_str)
        if not path.is_absolute():
            path = self.workspace_dir / path

        path = path.resolve()

        # Check if path is within workspace
        try:
            path.relative_to(self.workspace_dir.resolve())
        except ValueError:
            raise ValueError(
                f"路径 '{path}' 在工作空间 '{self.workspace_dir}' 之外"
            )

        return path

    async def _read_file(self, path: Path, encoding: str) -> ToolResult:
        """Read file contents"""
        if not path.exists():
            return ToolResult.error_result(f"文件不存在: {path}")

        if not path.is_file():
            return ToolResult.error_result(f"不是文件: {path}")

        def _read():
            with open(path, 'r', encoding=encoding) as f:
                return f.read()

        content = await self._run_sync(_read)

        return ToolResult.success_result(
            output=content,
            metadata={
                "path": str(path),
                "size": path.stat().st_size,
                "encoding": encoding
            }
        )

    async def _write_file(self, path: Path, content: str, encoding: str) -> ToolResult:
        """Write content to file"""
        # Create parent directory if it doesn't exist
        path.parent.mkdir(parents=True, exist_ok=True)

        def _write():
            with open(path, 'w', encoding=encoding) as f:
                f.write(content)
            return len(content)

        bytes_written = await self._run_sync(_write)

        return ToolResult.success_result(
            output=f"成功写入 {bytes_written} 字符到 {path}",
            metadata={
                "path": str(path),
                "bytes_written": bytes_written,
                "encoding": encoding
            }
        )

    async def _append_file(self, path: Path, content: str, encoding: str) -> ToolResult:
        """Append content to file"""
        # Create parent directory if it doesn't exist
        path.parent.mkdir(parents=True, exist_ok=True)

        def _append():
            with open(path, 'a', encoding=encoding) as f:
                f.write(content)
            return len(content)

        bytes_written = await self._run_sync(_append)

        return ToolResult.success_result(
            output=f"成功追加 {bytes_written} 字符到 {path}",
            metadata={
                "path": str(path),
                "bytes_written": bytes_written,
                "encoding": encoding
            }
        )

    async def _list_directory(self, path: Path) -> ToolResult:
        """List directory contents"""
        if not path.exists():
            return ToolResult.error_result(f"目录不存在: {path}")

        if not path.is_dir():
            return ToolResult.error_result(f"不是目录: {path}")

        def _list():
            items = []
            for item in path.iterdir():
                items.append({
                    "name": item.name,
                    "type": "file" if item.is_file() else "directory",
                    "size": item.stat().st_size if item.is_file() else None
                })
            return items

        items = await self._run_sync(_list)

        return ToolResult.success_result(
            output=items,
            metadata={
                "path": str(path),
                "count": len(items)
            }
        )

    async def _check_exists(self, path: Path) -> ToolResult:
        """Check if file or directory exists"""
        exists = path.exists()
        item_type = None

        if exists:
            if path.is_file():
                item_type = "file"
            elif path.is_dir():
                item_type = "directory"
            else:
                item_type = "other"

        return ToolResult.success_result(
            output={
                "exists": exists,
                "type": item_type,
                "path": str(path)
            },
            metadata={"path": str(path)}
        )

    async def _delete_file(self, path: Path) -> ToolResult:
        """Delete file or directory"""
        if not self.allow_delete:
            return ToolResult.error_result(
                "删除操作被禁用。请在初始化时设置 allow_delete=True"
            )

        if not path.exists():
            return ToolResult.error_result(f"文件不存在: {path}")

        def _delete():
            if path.is_file():
                path.unlink()
                return "file"
            elif path.is_dir():
                # Only delete empty directories
                if any(path.iterdir()):
                    raise ValueError("目录不为空")
                path.rmdir()
                return "directory"
            else:
                raise ValueError("无法删除此类型的项")

        item_type = await self._run_sync(_delete)

        return ToolResult.success_result(
            output=f"成功删除 {item_type}: {path}",
            metadata={
                "path": str(path),
                "type": item_type
            }
        )
