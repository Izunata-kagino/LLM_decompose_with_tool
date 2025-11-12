"""
Anthropic/Claude provider implementation (2025)
Supports: Claude 4.x series - Sonnet 4.5, Haiku 4.5, Opus 4.1
Knowledge cutoff: January 2025 (most extensive), July 2025 (Sonnet 4.5 trained on)
Context window: Up to 1M tokens with context-1m-2025-08-07 header
"""
from typing import AsyncIterator, List, Optional
import json

from .base import BaseLLMProvider
from models.llm_models import (
    LLMRequest,
    LLMResponse,
    LLMStreamChunk,
    Message,
    MessageRole,
    ToolCall,
    LLMUsage
)


class AnthropicProvider(BaseLLMProvider):
    """Anthropic provider for Claude models (2025)"""

    DEFAULT_BASE_URL = "https://api.anthropic.com/v1"
    SUPPORTED_MODELS = [
        # Claude 4.5 Series (2025) - Latest flagship models
        "claude-sonnet-4-5",        # September 2025 - Best coding model, $3/$15 per 1M tokens
        "claude-haiku-4-5",         # October 2025 - Fast and economical, $1/$5 per 1M tokens

        # Claude 4.1 Series (2025)
        "claude-opus-4-1",          # August 2025 - Agentic tasks, $15/$75 per 1M tokens

        # Claude 4 Series (May 2025)
        "claude-sonnet-4",
        "claude-opus-4",

        # Legacy Claude 3.x models (still available)
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
        "claude-3-5-sonnet-20240620",
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022",
    ]
    API_VERSION = "2023-06-01"

    def __init__(self, api_key: str, base_url: Optional[str] = None, timeout: int = 120):
        super().__init__(
            api_key=api_key,
            base_url=base_url or self.DEFAULT_BASE_URL,
            timeout=timeout
        )

    @property
    def provider_name(self) -> str:
        return "anthropic"

    def supports_structured_output(self) -> bool:
        return True  # Via tool calling with JSON schema

    def supports_tool_calling(self) -> bool:
        return True

    def get_supported_models(self) -> List[str]:
        return self.SUPPORTED_MODELS

    def _convert_messages(self, messages: List[Message]) -> tuple[str, List[dict]]:
        """
        Convert unified messages to Anthropic format
        Returns: (system_prompt, messages_list)
        """
        system_prompt = ""
        claude_messages = []

        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                # Anthropic uses separate system parameter
                system_prompt = msg.content or ""
            elif msg.role == MessageRole.TOOL:
                # Tool result message
                claude_messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": msg.tool_call_id,
                            "content": msg.content or ""
                        }
                    ]
                })
            elif msg.tool_calls:
                # Assistant message with tool calls
                content_blocks = []
                if msg.content:
                    content_blocks.append({
                        "type": "text",
                        "text": msg.content
                    })

                for tc in msg.tool_calls:
                    content_blocks.append({
                        "type": "tool_use",
                        "id": tc.id,
                        "name": tc.name,
                        "input": tc.get_arguments_dict()
                    })

                claude_messages.append({
                    "role": "assistant",
                    "content": content_blocks
                })
            else:
                # Regular message
                role = "user" if msg.role == MessageRole.USER else "assistant"
                claude_messages.append({
                    "role": role,
                    "content": msg.content or ""
                })

        return system_prompt, claude_messages

    def _convert_tools(self, tools: List) -> List[dict]:
        """Convert unified tools to Anthropic format"""
        claude_tools = []

        for tool in tools:
            claude_tools.append({
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.parameters
            })

        return claude_tools

    def _convert_request(self, request: LLMRequest) -> dict:
        """Convert unified request to Anthropic format"""
        system_prompt, messages = self._convert_messages(request.messages)

        payload = {
            "model": request.model,
            "messages": messages,
            "max_tokens": request.max_tokens or 4096,  # Required for Claude
            "temperature": request.temperature,
        }

        if system_prompt:
            payload["system"] = system_prompt

        if request.top_p:
            payload["top_p"] = request.top_p

        if request.stop:
            payload["stop_sequences"] = request.stop

        if request.stream:
            payload["stream"] = True

        # Handle tools
        if request.tools:
            payload["tools"] = self._convert_tools(request.tools)
            if request.tool_choice:
                if isinstance(request.tool_choice, str):
                    if request.tool_choice == "auto":
                        payload["tool_choice"] = {"type": "auto"}
                    elif request.tool_choice == "required":
                        payload["tool_choice"] = {"type": "any"}
                else:
                    payload["tool_choice"] = request.tool_choice

        # Handle structured output via tool calling
        if request.structured_output:
            # Create a special tool for structured output
            structured_tool = {
                "name": request.structured_output.name,
                "description": request.structured_output.description or "Generate structured output",
                "input_schema": request.structured_output.schema
            }
            payload["tools"] = [structured_tool]
            payload["tool_choice"] = {"type": "tool", "name": request.structured_output.name}

        return payload

    def _convert_response(self, response: dict, request: LLMRequest) -> LLMResponse:
        """Convert Anthropic response to unified format"""
        content_blocks = response.get("content", [])

        # Build message
        message_content = ""
        tool_calls = []

        for block in content_blocks:
            if block["type"] == "text":
                message_content += block["text"]
            elif block["type"] == "tool_use":
                tool_calls.append(ToolCall(
                    id=block["id"],
                    name=block["name"],
                    arguments=block["input"]
                ))

        message = Message(
            role=MessageRole.ASSISTANT,
            content=message_content if message_content else None,
            tool_calls=tool_calls if tool_calls else None
        )

        # Extract usage
        usage = None
        if "usage" in response:
            usage = LLMUsage(
                prompt_tokens=response["usage"]["input_tokens"],
                completion_tokens=response["usage"]["output_tokens"],
                total_tokens=response["usage"]["input_tokens"] + response["usage"]["output_tokens"]
            )

        return LLMResponse(
            id=response["id"],
            model=response["model"],
            message=message,
            usage=usage,
            finish_reason=response.get("stop_reason"),
            raw_response=response
        )

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Send completion request to Anthropic"""
        payload = self._convert_request(request)

        # Anthropic requires special headers
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self.API_VERSION,
            "Content-Type": "application/json"
        }

        # Override authorization header
        response = await self._make_request("/messages", payload, headers)
        return self._convert_response(response, request)

    async def _make_request(
        self,
        endpoint: str,
        payload: dict,
        headers: Optional[dict] = None
    ) -> dict:
        """Override to use x-api-key instead of Authorization header"""
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")

        default_headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": self.API_VERSION
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

    async def stream_complete(self, request: LLMRequest) -> AsyncIterator[LLMStreamChunk]:
        """Send streaming completion request to Anthropic"""
        request.stream = True
        payload = self._convert_request(request)

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self.API_VERSION,
            "Content-Type": "application/json"
        }

        async for chunk_data in self._stream_request("/messages", payload, headers):
            event_type = chunk_data.get("type")

            if event_type == "content_block_delta":
                delta = chunk_data.get("delta", {})
                yield LLMStreamChunk(
                    id=chunk_data.get("index", ""),
                    model=request.model,
                    delta=delta,
                    finish_reason=None
                )
            elif event_type == "message_stop":
                yield LLMStreamChunk(
                    id="final",
                    model=request.model,
                    delta={},
                    finish_reason="stop"
                )
