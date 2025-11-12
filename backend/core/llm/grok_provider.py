"""
Grok (X.AI) provider implementation
Supports: Grok models with tool calling and structured output
Based on OpenAI-compatible API
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


class GrokProvider(BaseLLMProvider):
    """Grok provider for X.AI models"""

    DEFAULT_BASE_URL = "https://api.x.ai/v1"
    SUPPORTED_MODELS = [
        "grok-beta",
        "grok-1",
        "grok-2",
    ]

    def __init__(self, api_key: str, base_url: Optional[str] = None, timeout: int = 120):
        super().__init__(
            api_key=api_key,
            base_url=base_url or self.DEFAULT_BASE_URL,
            timeout=timeout
        )

    @property
    def provider_name(self) -> str:
        return "grok"

    def supports_structured_output(self) -> bool:
        return True

    def supports_tool_calling(self) -> bool:
        return True

    def get_supported_models(self) -> List[str]:
        return self.SUPPORTED_MODELS

    def _convert_messages(self, messages: List[Message]) -> List[dict]:
        """Convert unified messages to Grok (OpenAI-like) format"""
        grok_messages = []

        for msg in messages:
            grok_msg = {"role": msg.role.value}

            # Handle different message types
            if msg.role == MessageRole.TOOL:
                # Tool result message
                grok_msg["role"] = "tool"
                grok_msg["content"] = msg.content or ""
                grok_msg["tool_call_id"] = msg.tool_call_id
            elif msg.tool_calls:
                # Assistant message with tool calls
                grok_msg["role"] = "assistant"
                if msg.content:
                    grok_msg["content"] = msg.content
                grok_msg["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": tc.arguments if isinstance(tc.arguments, str)
                            else json.dumps(tc.arguments)
                        }
                    }
                    for tc in msg.tool_calls
                ]
            else:
                # Regular message
                grok_msg["content"] = msg.content or ""

            grok_messages.append(grok_msg)

        return grok_messages

    def _convert_tools(self, tools: List) -> List[dict]:
        """Convert unified tools to Grok format"""
        grok_tools = []

        for tool in tools:
            grok_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters
                }
            })

        return grok_tools

    def _convert_request(self, request: LLMRequest) -> dict:
        """Convert unified request to Grok format"""
        payload = {
            "model": request.model,
            "messages": self._convert_messages(request.messages),
            "temperature": request.temperature,
        }

        if request.max_tokens:
            payload["max_tokens"] = request.max_tokens

        if request.top_p:
            payload["top_p"] = request.top_p

        if request.stop:
            payload["stop"] = request.stop

        if request.stream:
            payload["stream"] = True

        # Handle tools
        if request.tools:
            payload["tools"] = self._convert_tools(request.tools)
            if request.tool_choice:
                if isinstance(request.tool_choice, str):
                    payload["tool_choice"] = request.tool_choice
                else:
                    payload["tool_choice"] = request.tool_choice

        # Handle structured output (using response_format for JSON mode)
        if request.structured_output:
            # Grok supports JSON schema in response_format
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": request.structured_output.name,
                    "description": request.structured_output.description,
                    "schema": request.structured_output.schema,
                    "strict": request.structured_output.strict
                }
            }

        return payload

    def _convert_response(self, response: dict, request: LLMRequest) -> LLMResponse:
        """Convert Grok response to unified format"""
        choice = response["choices"][0]
        message_data = choice["message"]

        # Build message
        message = Message(
            role=MessageRole.ASSISTANT,
            content=message_data.get("content")
        )

        # Handle tool calls
        if "tool_calls" in message_data and message_data["tool_calls"]:
            tool_calls = []
            for tc in message_data["tool_calls"]:
                tool_calls.append(ToolCall(
                    id=tc["id"],
                    name=tc["function"]["name"],
                    arguments=tc["function"]["arguments"]
                ))
            message.tool_calls = tool_calls

        # Extract usage
        usage = None
        if "usage" in response:
            usage = LLMUsage(
                prompt_tokens=response["usage"]["prompt_tokens"],
                completion_tokens=response["usage"]["completion_tokens"],
                total_tokens=response["usage"]["total_tokens"]
            )

        return LLMResponse(
            id=response["id"],
            model=response["model"],
            message=message,
            usage=usage,
            finish_reason=choice.get("finish_reason"),
            raw_response=response
        )

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Send completion request to Grok"""
        payload = self._convert_request(request)
        response = await self._make_request("/chat/completions", payload)
        return self._convert_response(response, request)

    async def stream_complete(self, request: LLMRequest) -> AsyncIterator[LLMStreamChunk]:
        """Send streaming completion request to Grok"""
        request.stream = True
        payload = self._convert_request(request)

        async for chunk_data in self._stream_request("/chat/completions", payload):
            if "choices" in chunk_data and len(chunk_data["choices"]) > 0:
                choice = chunk_data["choices"][0]
                yield LLMStreamChunk(
                    id=chunk_data["id"],
                    model=chunk_data["model"],
                    delta=choice.get("delta", {}),
                    finish_reason=choice.get("finish_reason")
                )
