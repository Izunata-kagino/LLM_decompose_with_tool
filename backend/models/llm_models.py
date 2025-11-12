"""
Data models for LLM integration
"""
from typing import Optional, List, Dict, Any, Literal, Union
from pydantic import BaseModel, Field
from enum import Enum


class MessageRole(str, Enum):
    """Message role types"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    FUNCTION = "function"  # For backward compatibility


class ToolParameter(BaseModel):
    """Tool parameter definition"""
    type: str
    description: Optional[str] = None
    enum: Optional[List[str]] = None
    items: Optional[Dict[str, Any]] = None
    properties: Optional[Dict[str, Any]] = None
    required: Optional[List[str]] = None


class ToolDefinition(BaseModel):
    """Tool definition following OpenAI/Anthropic format"""
    name: str
    description: str
    parameters: Dict[str, Any] = Field(default_factory=dict)

    @property
    def json_schema(self) -> Dict[str, Any]:
        """Convert to JSON schema format"""
        return {
            "type": "object",
            "properties": self.parameters.get("properties", {}),
            "required": self.parameters.get("required", [])
        }


class ToolCall(BaseModel):
    """Tool call from LLM"""
    id: str
    name: str
    arguments: Union[str, Dict[str, Any]]  # String (JSON) or parsed dict

    def get_arguments_dict(self) -> Dict[str, Any]:
        """Get arguments as dictionary"""
        if isinstance(self.arguments, str):
            import json
            return json.loads(self.arguments)
        return self.arguments


class ToolResult(BaseModel):
    """Result from tool execution"""
    tool_call_id: str
    name: str
    content: str
    is_error: bool = False


class Message(BaseModel):
    """Unified message format"""
    role: MessageRole
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None  # For tool result messages
    name: Optional[str] = None  # Tool name for tool messages


class StructuredOutputSchema(BaseModel):
    """Schema for structured output"""
    name: str
    description: Optional[str] = None
    schema: Dict[str, Any]
    strict: bool = True  # Enforce strict schema adherence


class LLMRequest(BaseModel):
    """Unified LLM request"""
    messages: List[Message]
    model: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    tools: Optional[List[ToolDefinition]] = None
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None  # "auto", "none", "required", or specific tool
    structured_output: Optional[StructuredOutputSchema] = None
    stream: bool = False
    top_p: Optional[float] = None
    stop: Optional[List[str]] = None


class LLMUsage(BaseModel):
    """Token usage information"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class LLMResponse(BaseModel):
    """Unified LLM response"""
    id: str
    model: str
    message: Message
    usage: Optional[LLMUsage] = None
    finish_reason: Optional[str] = None  # "stop", "length", "tool_calls", etc.
    raw_response: Optional[Dict[str, Any]] = None  # Original provider response


class LLMStreamChunk(BaseModel):
    """Stream chunk for streaming responses"""
    id: str
    model: str
    delta: Dict[str, Any]  # Incremental changes
    finish_reason: Optional[str] = None
