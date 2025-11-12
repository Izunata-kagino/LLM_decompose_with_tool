"""
Base LLM provider interface
"""
from abc import ABC, abstractmethod
from typing import Optional, AsyncIterator, List
import aiohttp
import json

from models.llm_models import (
    LLMRequest,
    LLMResponse,
    LLMStreamChunk,
    Message,
    ToolDefinition
)


class BaseLLMProvider(ABC):
    """Base class for all LLM providers"""

    def __init__(self, api_key: str, base_url: Optional[str] = None, timeout: int = 120):
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider identifier"""
        pass

    @abstractmethod
    def _convert_request(self, request: LLMRequest) -> dict:
        """Convert unified request to provider-specific format"""
        pass

    @abstractmethod
    def _convert_response(self, response: dict, request: LLMRequest) -> LLMResponse:
        """Convert provider-specific response to unified format"""
        pass

    @abstractmethod
    async def complete(self, request: LLMRequest) -> LLMResponse:
        """
        Send completion request to LLM provider

        Args:
            request: Unified LLM request

        Returns:
            Unified LLM response
        """
        pass

    @abstractmethod
    async def stream_complete(self, request: LLMRequest) -> AsyncIterator[LLMStreamChunk]:
        """
        Send streaming completion request to LLM provider

        Args:
            request: Unified LLM request

        Yields:
            Stream chunks
        """
        pass

    async def _make_request(
        self,
        endpoint: str,
        payload: dict,
        headers: Optional[dict] = None
    ) -> dict:
        """
        Make HTTP request to provider API

        Args:
            endpoint: API endpoint
            payload: Request payload
            headers: Additional headers

        Returns:
            Response JSON
        """
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")

        default_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        if headers:
            default_headers.update(headers)

        url = f"{self.base_url}{endpoint}" if self.base_url else endpoint

        async with self.session.post(
            url,
            json=payload,
            headers=default_headers
        ) as response:
            response.raise_for_status()
            return await response.json()

    async def _stream_request(
        self,
        endpoint: str,
        payload: dict,
        headers: Optional[dict] = None
    ) -> AsyncIterator[dict]:
        """
        Make streaming HTTP request to provider API

        Args:
            endpoint: API endpoint
            payload: Request payload
            headers: Additional headers

        Yields:
            Response chunks as JSON
        """
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")

        default_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        if headers:
            default_headers.update(headers)

        url = f"{self.base_url}{endpoint}" if self.base_url else endpoint

        async with self.session.post(
            url,
            json=payload,
            headers=default_headers
        ) as response:
            response.raise_for_status()

            async for line in response.content:
                line_str = line.decode('utf-8').strip()
                if line_str.startswith('data: '):
                    data_str = line_str[6:]
                    if data_str == '[DONE]':
                        break
                    try:
                        yield json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

    def supports_structured_output(self) -> bool:
        """Check if provider supports structured output"""
        return False

    def supports_tool_calling(self) -> bool:
        """Check if provider supports tool calling"""
        return False

    def get_supported_models(self) -> List[str]:
        """Get list of supported models"""
        return []
