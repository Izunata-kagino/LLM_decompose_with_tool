"""
Tool registry system for managing and discovering tools
"""
from typing import Dict, List, Optional, Type
import logging
from .base import BaseTool, ToolSchema

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry for managing tools"""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._categories: Dict[str, List[str]] = {}

    def register(
        self,
        tool: BaseTool,
        category: Optional[str] = None,
        override: bool = False
    ) -> bool:
        """
        Register a tool

        Args:
            tool: Tool instance to register
            category: Optional category for the tool
            override: Whether to override existing tool with same name

        Returns:
            True if registered successfully, False otherwise
        """
        tool_name = tool.name

        # Check if tool already exists
        if tool_name in self._tools and not override:
            logger.warning(f"Tool '{tool_name}' already registered. Use override=True to replace.")
            return False

        # Register the tool
        self._tools[tool_name] = tool
        logger.info(f"Registered tool: {tool_name}")

        # Add to category
        if category:
            if category not in self._categories:
                self._categories[category] = []
            if tool_name not in self._categories[category]:
                self._categories[category].append(tool_name)

        return True

    def unregister(self, tool_name: str) -> bool:
        """
        Unregister a tool

        Args:
            tool_name: Name of tool to unregister

        Returns:
            True if unregistered, False if tool not found
        """
        if tool_name not in self._tools:
            logger.warning(f"Tool '{tool_name}' not found in registry")
            return False

        del self._tools[tool_name]

        # Remove from categories
        for category, tools in self._categories.items():
            if tool_name in tools:
                tools.remove(tool_name)

        logger.info(f"Unregistered tool: {tool_name}")
        return True

    def get(self, tool_name: str) -> Optional[BaseTool]:
        """
        Get a tool by name

        Args:
            tool_name: Name of the tool

        Returns:
            Tool instance or None if not found
        """
        return self._tools.get(tool_name)

    def list_tools(self, category: Optional[str] = None) -> List[str]:
        """
        List all registered tools

        Args:
            category: Optional category filter

        Returns:
            List of tool names
        """
        if category:
            return self._categories.get(category, [])
        return list(self._tools.keys())

    def get_schemas(self, category: Optional[str] = None) -> List[ToolSchema]:
        """
        Get schemas for all tools

        Args:
            category: Optional category filter

        Returns:
            List of tool schemas
        """
        tool_names = self.list_tools(category)
        schemas = []

        for name in tool_names:
            tool = self._tools.get(name)
            if tool:
                schemas.append(tool.get_schema())

        return schemas

    def get_tools_for_llm(self, category: Optional[str] = None) -> List[Dict]:
        """
        Get tool definitions in LLM-compatible format

        Args:
            category: Optional category filter

        Returns:
            List of tool definitions for LLM
        """
        schemas = self.get_schemas(category)
        return [
            {
                "type": "function",
                "function": {
                    "name": schema.name,
                    "description": schema.description,
                    "parameters": schema.parameters
                }
            }
            for schema in schemas
        ]

    def has_tool(self, tool_name: str) -> bool:
        """
        Check if a tool is registered

        Args:
            tool_name: Name of the tool

        Returns:
            True if tool exists, False otherwise
        """
        return tool_name in self._tools

    def clear(self):
        """Clear all registered tools"""
        self._tools.clear()
        self._categories.clear()
        logger.info("Cleared all tools from registry")

    def list_categories(self) -> List[str]:
        """
        List all categories

        Returns:
            List of category names
        """
        return list(self._categories.keys())

    def get_category_info(self) -> Dict[str, int]:
        """
        Get information about categories

        Returns:
            Dict mapping category names to tool counts
        """
        return {
            category: len(tools)
            for category, tools in self._categories.items()
        }

    def __len__(self) -> int:
        """Get number of registered tools"""
        return len(self._tools)

    def __contains__(self, tool_name: str) -> bool:
        """Check if tool is registered"""
        return tool_name in self._tools

    def __repr__(self) -> str:
        """String representation"""
        return f"ToolRegistry(tools={len(self._tools)}, categories={len(self._categories)})"


# Global registry instance
_global_registry: Optional[ToolRegistry] = None


def get_global_registry() -> ToolRegistry:
    """
    Get the global tool registry instance

    Returns:
        Global ToolRegistry instance
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry


def register_tool(
    tool: BaseTool,
    category: Optional[str] = None,
    override: bool = False
) -> bool:
    """
    Register a tool to the global registry

    Args:
        tool: Tool instance
        category: Optional category
        override: Whether to override existing tool

    Returns:
        True if registered successfully
    """
    registry = get_global_registry()
    return registry.register(tool, category, override)


def get_tool(tool_name: str) -> Optional[BaseTool]:
    """
    Get a tool from the global registry

    Args:
        tool_name: Name of the tool

    Returns:
        Tool instance or None
    """
    registry = get_global_registry()
    return registry.get(tool_name)
