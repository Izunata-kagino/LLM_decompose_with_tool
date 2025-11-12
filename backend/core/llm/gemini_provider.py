"""
Google Gemini provider implementation (2025)
Supports: Gemini 2.5 Pro, Flash, Computer Use
Knowledge cutoff: Varies by model
Context window: Varies (Pro has longer context)
Note: Gemini 1.x models are fully retired as of April 2025
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


class GeminiProvider(BaseLLMProvider):
    """Google Gemini provider (2025)"""

    DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
    SUPPORTED_MODELS = [
        # Gemini 2.5 Series (2025)
        "gemini-2.5-pro",                    # Most powerful model with adaptive thinking
        "gemini-2.5-flash",                  # Fast and efficient, #2 on LMarena leaderboard
        "gemini-2.5-flash-preview-05-20",   # Preview with better reasoning
        "gemini-2.5-computer-use",          # Specialized UI interaction model

        # Specialized models
        "gemini-2.5-image-preview",         # Native image generation

        # Note: Gemini 1.x models retired April 29, 2025
        # Use gemini-2.5-flash-lite for lightweight tasks
        "gemini-2.5-flash-lite",
    ]

    def __init__(self, api_key: str, base_url: Optional[str] = None, timeout: int = 120):
        super().__init__(
            api_key=api_key,
            base_url=base_url or self.DEFAULT_BASE_URL,
            timeout=timeout
        )

    @property
    def provider_name(self) -> str:
        return "gemini"

    def supports_structured_output(self) -> bool:
        return True

    def supports_tool_calling(self) -> bool:
        return True

    def get_supported_models(self) -> List[str]:
        return self.SUPPORTED_MODELS

    def _convert_messages(self, messages: List[Message]) -> tuple[Optional[str], List[dict]]:
        """
        Convert unified messages to Gemini format
        Returns: (system_instruction, contents)
        """
        system_instruction = None
        gemini_contents = []

        for msg in messages:
            if msg.role == MessageRole.SYSTEM:
                # Gemini uses separate system_instruction
                system_instruction = msg.content
            elif msg.role == MessageRole.TOOL:
                # Tool response
                gemini_contents.append({
                    "role": "function",
                    "parts": [{
                        "functionResponse": {
                            "name": msg.name or "unknown",
                            "response": {
                                "content": msg.content or ""
                            }
                        }
                    }]
                })
            elif msg.tool_calls:
                # Assistant message with tool calls
                parts = []
                if msg.content:
                    parts.append({"text": msg.content})

                for tc in msg.tool_calls:
                    parts.append({
                        "functionCall": {
                            "name": tc.name,
                            "args": tc.get_arguments_dict()
                        }
                    })

                gemini_contents.append({
                    "role": "model",
                    "parts": parts
                })
            else:
                # Regular message
                role = "user" if msg.role == MessageRole.USER else "model"
                gemini_contents.append({
                    "role": role,
                    "parts": [{"text": msg.content or ""}]
                })

        return system_instruction, gemini_contents

    def _convert_tools(self, tools: List) -> List[dict]:
        """Convert unified tools to Gemini format"""
        gemini_tools = []

        for tool in tools:
            # Gemini uses function declarations
            function_declaration = {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            }
            gemini_tools.append(function_declaration)

        return [{
            "function_declarations": gemini_tools
        }] if gemini_tools else []

    def _convert_request(self, request: LLMRequest) -> dict:
        """Convert unified request to Gemini format"""
        system_instruction, contents = self._convert_messages(request.messages)

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": request.temperature,
            }
        }

        if request.max_tokens:
            payload["generationConfig"]["maxOutputTokens"] = request.max_tokens

        if request.top_p:
            payload["generationConfig"]["topP"] = request.top_p

        if request.stop:
            payload["generationConfig"]["stopSequences"] = request.stop

        if system_instruction:
            payload["system_instruction"] = {
                "parts": [{"text": system_instruction}]
            }

        # Handle tools
        if request.tools:
            payload["tools"] = self._convert_tools(request.tools)

            # Tool choice configuration
            if request.tool_choice:
                if request.tool_choice == "required":
                    payload["toolConfig"] = {
                        "functionCallingConfig": {"mode": "ANY"}
                    }
                elif request.tool_choice == "auto":
                    payload["toolConfig"] = {
                        "functionCallingConfig": {"mode": "AUTO"}
                    }
                elif request.tool_choice == "none":
                    payload["toolConfig"] = {
                        "functionCallingConfig": {"mode": "NONE"}
                    }

        # Handle structured output via response schema
        if request.structured_output:
            payload["generationConfig"]["responseMimeType"] = "application/json"
            payload["generationConfig"]["responseSchema"] = request.structured_output.schema

        return payload

    def _convert_response(self, response: dict, request: LLMRequest) -> LLMResponse:
        """Convert Gemini response to unified format"""
        candidate = response["candidates"][0]
        content_parts = candidate["content"]["parts"]

        # Build message
        message_content = ""
        tool_calls = []

        for i, part in enumerate(content_parts):
            if "text" in part:
                message_content += part["text"]
            elif "functionCall" in part:
                func_call = part["functionCall"]
                tool_calls.append(ToolCall(
                    id=f"call_{i}",  # Gemini doesn't provide IDs
                    name=func_call["name"],
                    arguments=func_call.get("args", {})
                ))

        message = Message(
            role=MessageRole.ASSISTANT,
            content=message_content if message_content else None,
            tool_calls=tool_calls if tool_calls else None
        )

        # Extract usage
        usage = None
        if "usageMetadata" in response:
            metadata = response["usageMetadata"]
            usage = LLMUsage(
                prompt_tokens=metadata.get("promptTokenCount", 0),
                completion_tokens=metadata.get("candidatesTokenCount", 0),
                total_tokens=metadata.get("totalTokenCount", 0)
            )

        return LLMResponse(
            id=response.get("id", "gemini-response"),
            model=request.model,
            message=message,
            usage=usage,
            finish_reason=candidate.get("finishReason"),
            raw_response=response
        )

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Send completion request to Gemini"""
        payload = self._convert_request(request)

        # Gemini uses API key as query parameter
        endpoint = f"/models/{request.model}:generateContent?key={self.api_key}"

        # Override headers for Gemini
        headers = {"Content-Type": "application/json"}

        response = await self._make_gemini_request(endpoint, payload, headers)
        return self._convert_response(response, request)

    async def stream_complete(self, request: LLMRequest) -> AsyncIterator[LLMStreamChunk]:
        """Send streaming completion request to Gemini"""
        payload = self._convert_request(request)

        # Gemini uses API key as query parameter
        endpoint = f"/models/{request.model}:streamGenerateContent?key={self.api_key}"

        headers = {"Content-Type": "application/json"}

        async for chunk_data in self._stream_gemini_request(endpoint, payload, headers):
            if "candidates" in chunk_data and len(chunk_data["candidates"]) > 0:
                candidate = chunk_data["candidates"][0]
                delta = {}

                if "content" in candidate and "parts" in candidate["content"]:
                    parts = candidate["content"]["parts"]
                    if parts and "text" in parts[0]:
                        delta["content"] = parts[0]["text"]

                yield LLMStreamChunk(
                    id=chunk_data.get("id", "gemini-stream"),
                    model=request.model,
                    delta=delta,
                    finish_reason=candidate.get("finishReason")
                )

    async def _make_gemini_request(
        self,
        endpoint: str,
        payload: dict,
        headers: Optional[dict] = None
    ) -> dict:
        """Make HTTP request to Gemini API"""
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")

        url = f"{self.base_url}{endpoint}"

        async with self.session.post(
            url,
            json=payload,
            headers=headers or {}
        ) as response:
            response.raise_for_status()
            return await response.json()

    async def _stream_gemini_request(
        self,
        endpoint: str,
        payload: dict,
        headers: Optional[dict] = None
    ) -> AsyncIterator[dict]:
        """Make streaming HTTP request to Gemini API"""
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")

        url = f"{self.base_url}{endpoint}"

        async with self.session.post(
            url,
            json=payload,
            headers=headers or {}
        ) as response:
            response.raise_for_status()

            async for line in response.content:
                line_str = line.decode('utf-8').strip()
                if line_str:
                    try:
                        yield json.loads(line_str)
                    except json.JSONDecodeError:
                        continue
