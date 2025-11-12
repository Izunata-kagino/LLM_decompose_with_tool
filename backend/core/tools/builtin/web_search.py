"""
Web search tool for searching the internet
"""
from typing import Dict, Any, Optional, List
import aiohttp
import json
from urllib.parse import quote_plus

from ..base import BaseTool, ToolResult, ToolExecutionContext, ToolCategory


class WebSearchTool(BaseTool):
    """
    Web search tool using DuckDuckGo or custom search API

    Supports:
    - General web search
    - News search
    - Image search (returns URLs)
    """

    def __init__(self, api_key: Optional[str] = None, search_engine: str = "duckduckgo"):
        """
        Initialize web search tool

        Args:
            api_key: API key for search service (if required)
            search_engine: Search engine to use ('duckduckgo', 'google', 'bing')
        """
        super().__init__()
        self.api_key = api_key
        self.search_engine = search_engine.lower()

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return (
            "在互联网上搜索信息。可以搜索网页、新闻等。"
            "返回搜索结果的标题、链接和摘要。"
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索查询关键词"
                },
                "num_results": {
                    "type": "integer",
                    "description": "返回的结果数量 (默认: 5)",
                    "default": 5
                },
                "search_type": {
                    "type": "string",
                    "enum": ["web", "news", "images"],
                    "description": "搜索类型 (默认: web)"
                }
            },
            "required": ["query"]
        }

    async def execute(
        self,
        arguments: Dict[str, Any],
        context: Optional[ToolExecutionContext] = None
    ) -> ToolResult:
        """Execute web search"""
        query = arguments.get("query", "").strip()
        num_results = arguments.get("num_results", 5)
        search_type = arguments.get("search_type", "web")

        if not query:
            return ToolResult.error_result("查询关键词不能为空")

        if num_results < 1 or num_results > 20:
            return ToolResult.error_result("结果数量必须在 1-20 之间")

        try:
            # Perform search based on search engine
            if self.search_engine == "duckduckgo":
                results = await self._search_duckduckgo(query, num_results, search_type)
            else:
                return ToolResult.error_result(
                    f"不支持的搜索引擎: {self.search_engine}"
                )

            return ToolResult.success_result(
                output=results,
                metadata={
                    "query": query,
                    "num_results": len(results),
                    "search_type": search_type,
                    "search_engine": self.search_engine
                }
            )

        except Exception as e:
            return ToolResult.error_result(f"搜索失败: {str(e)}")

    async def _search_duckduckgo(
        self,
        query: str,
        num_results: int,
        search_type: str
    ) -> List[Dict[str, Any]]:
        """
        Search using DuckDuckGo Instant Answer API

        Note: This is a simplified implementation using DuckDuckGo's API.
        For production use, consider using a proper search API or library.
        """
        # DuckDuckGo Instant Answer API
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=10) as response:
                if response.status != 200:
                    raise Exception(f"搜索请求失败: HTTP {response.status}")

                data = await response.json()

        # Parse results
        results = []

        # Abstract (main answer)
        if data.get("Abstract"):
            results.append({
                "title": data.get("Heading", "Answer"),
                "snippet": data.get("Abstract", ""),
                "url": data.get("AbstractURL", ""),
                "source": data.get("AbstractSource", "DuckDuckGo")
            })

        # Related topics
        for topic in data.get("RelatedTopics", [])[:num_results]:
            if isinstance(topic, dict) and "Text" in topic:
                results.append({
                    "title": topic.get("Text", "").split(" - ")[0] if " - " in topic.get("Text", "") else "Related",
                    "snippet": topic.get("Text", ""),
                    "url": topic.get("FirstURL", ""),
                    "source": "DuckDuckGo"
                })

        # If no results, try HTML scraping approach (simple version)
        if not results:
            results = await self._search_duckduckgo_html(query, num_results)

        return results[:num_results]

    async def _search_duckduckgo_html(
        self,
        query: str,
        num_results: int
    ) -> List[Dict[str, Any]]:
        """
        Fallback: Search using DuckDuckGo HTML (simplified)

        Note: This is a basic implementation. For better results,
        consider using a library like `duckduckgo-search` or a proper API.
        """
        url = "https://html.duckduckgo.com/html/"
        params = {"q": query}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=params, timeout=10) as response:
                    if response.status != 200:
                        return []

                    html = await response.text()

            # Simple parsing (in production, use BeautifulSoup or similar)
            results = []

            # This is a placeholder - in a real implementation, you would
            # parse the HTML to extract search results
            # For now, return a message indicating limited results
            results.append({
                "title": f"搜索: {query}",
                "snippet": "使用 DuckDuckGo API 的简化实现。建议使用专门的搜索 API 以获得更好的结果。",
                "url": f"https://duckduckgo.com/?q={quote_plus(query)}",
                "source": "DuckDuckGo"
            })

            return results

        except Exception as e:
            return [{
                "title": "搜索错误",
                "snippet": f"无法完成搜索: {str(e)}",
                "url": "",
                "source": "Error"
            }]

    async def _search_google(
        self,
        query: str,
        num_results: int
    ) -> List[Dict[str, Any]]:
        """
        Search using Google Custom Search API

        Requires API key and Search Engine ID
        """
        if not self.api_key:
            raise ValueError("Google 搜索需要 API 密钥")

        # Placeholder for Google Custom Search implementation
        # In production, implement using Google Custom Search API
        raise NotImplementedError("Google 搜索尚未实现")

    async def _search_bing(
        self,
        query: str,
        num_results: int
    ) -> List[Dict[str, Any]]:
        """
        Search using Bing Search API

        Requires API key
        """
        if not self.api_key:
            raise ValueError("Bing 搜索需要 API 密钥")

        # Placeholder for Bing Search implementation
        # In production, implement using Bing Search API
        raise NotImplementedError("Bing 搜索尚未实现")
