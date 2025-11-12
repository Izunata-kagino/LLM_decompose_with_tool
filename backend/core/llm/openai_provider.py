"""
OpenAI/GPT provider implementation
Supports: GPT-4, GPT-4-Turbo, GPT-3.5, with structured output and tool calling
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


class OpenAIProvider(BaseLLMProvider):
    """OpenAI provider for GPT models"""

    DEFAULT_BASE_URL = "https://api.openai.com/v1"
    SUPPORTED_MODELS = [
        "gpt-4-turbo-preview",
        "gpt-4-1106-preview",
        "gpt-4",
        "gpt-4-0613",
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-1106",
        "gpt-4o",
        "gpt-4o-mini",
    ]

    def __init__(self, api_key: str, base_url: Optional[str] = None, timeout: int = 120):
        super().__init__(
            api_key=api_key,
            base_url=base_url or self.DEFAULT_BASE_URL,
            timeout=timeout
        )

    @property
    def provider_name(self) -> str:
        return "openai"

    def supports_structured_output(self) -> bool:
        return True

    def supports_tool_calling(self) -> bool:
        return True

    def get_supported_models(self) -> List[str]:
        return self.SUPPORTED_MODELS

    def _convert_messages(self, messages: List[Message]) -> List[dict]:
        """Convert unified messages to OpenAI format"""
        openai_messages = []

        for msg in messages:
            openai_msg = {"role": msg.role.value}

            # Handle different message types
            if msg.role == MessageRole.TOOL:
                # Tool result message
                openai_msg["role"] = "tool"
                openai_msg["content"] = msg.content or ""
                openai_msg["tool_call_id"] = msg.tool_call_id
            elif msg.tool_calls:
                # Assistant message with tool calls
                openai_msg["role"] = "assistant"
                if msg.content:
                    openai_msg["content"] = msg.content
                openai_msg["tool_calls"] = [
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
                openai_msg["content"] = msg.content or ""

            openai_messages.append(openai_msg)

        return openai_messages

    def _convert_tools(self, tools: List) -> List[dict]:
        """Convert unified tools to OpenAI format"""
        openai_tools = []

        for tool in tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters
                }
            })

        return openai_tools

    def _convert_request(self, request: LLMRequest) -> dict:
        """Convert unified request to OpenAI format"""
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
            # For OpenAI, we use response_format with json_schema (GPT-4+ feature)
            if "gpt-4" in request.model.lower() or "gpt-4o" in request.model.lower():
                payload["response_format"] = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": request.structured_output.name,
                        "description": request.structured_output.description,
                        "schema": request.structured_output.schema,
                        "strict": request.structured_output.strict
                    }
                }
            else:
                # Fallback to json_object mode for older models
                payload["response_format"] = {"type": "json_object"}

        return payload

    def _convert_response(self, response: dict, request: LLMRequest) -> LLMResponse:
        """Convert OpenAI response to unified format"""
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
        """Send completion request to OpenAI"""
        payload = self._convert_request(request)
        response = await self._make_request("/chat/completions", payload)
        return self._convert_response(response, request)

    async def stream_complete(self, request: LLMRequest) -> AsyncIterator[LLMStreamChunk]:
        """Send streaming completion request to OpenAI"""
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
