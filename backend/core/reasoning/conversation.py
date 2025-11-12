"""
Conversation manager for handling LLM message history
"""
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from models.llm_models import Message, MessageRole, ToolCall

logger = logging.getLogger(__name__)


class ConversationManager:
    """
    Manages conversation history for LLM interactions

    Handles:
    - Message history management
    - Context window limits
    - Tool call tracking
    - Message formatting
    """

    def __init__(
        self,
        system_message: Optional[str] = None,
        max_messages: Optional[int] = None,
        max_tokens: Optional[int] = None
    ):
        """
        Initialize conversation manager

        Args:
            system_message: System message to prepend
            max_messages: Maximum number of messages to keep
            max_tokens: Maximum estimated tokens (rough estimate)
        """
        self.messages: List[Message] = []
        self.system_message = system_message
        self.max_messages = max_messages
        self.max_tokens = max_tokens

        # Add system message if provided
        if system_message:
            self.add_system_message(system_message)

    def add_system_message(self, content: str) -> None:
        """Add or update system message"""
        # Remove existing system message if any
        self.messages = [m for m in self.messages if m.role != MessageRole.SYSTEM]

        # Add new system message at the beginning
        self.messages.insert(
            0,
            Message(role=MessageRole.SYSTEM, content=content)
        )

    def add_user_message(self, content: str) -> None:
        """Add user message"""
        self.messages.append(
            Message(role=MessageRole.USER, content=content)
        )
        self._trim_history()

    def add_assistant_message(
        self,
        content: Optional[str] = None,
        tool_calls: Optional[List[ToolCall]] = None
    ) -> None:
        """Add assistant message"""
        self.messages.append(
            Message(
                role=MessageRole.ASSISTANT,
                content=content,
                tool_calls=tool_calls
            )
        )
        self._trim_history()

    def add_tool_result(
        self,
        tool_call_id: str,
        tool_name: str,
        content: str
    ) -> None:
        """Add tool result message"""
        self.messages.append(
            Message(
                role=MessageRole.TOOL,
                content=content,
                tool_call_id=tool_call_id,
                name=tool_name
            )
        )
        self._trim_history()

    def add_message(self, message: Message) -> None:
        """Add a message directly"""
        self.messages.append(message)
        self._trim_history()

    def get_messages(self) -> List[Message]:
        """Get all messages"""
        return self.messages.copy()

    def get_recent_messages(self, n: int) -> List[Message]:
        """Get n most recent messages (excluding system message)"""
        system_msgs = [m for m in self.messages if m.role == MessageRole.SYSTEM]
        other_msgs = [m for m in self.messages if m.role != MessageRole.SYSTEM]

        return system_msgs + other_msgs[-n:]

    def get_last_assistant_message(self) -> Optional[Message]:
        """Get the last assistant message"""
        for message in reversed(self.messages):
            if message.role == MessageRole.ASSISTANT:
                return message
        return None

    def get_tool_calls_pending(self) -> List[ToolCall]:
        """Get tool calls that haven't been responded to yet"""
        last_assistant = self.get_last_assistant_message()
        if not last_assistant or not last_assistant.tool_calls:
            return []

        # Get tool call IDs that have been responded to
        responded_ids = set()
        for msg in self.messages:
            if msg.role == MessageRole.TOOL and msg.tool_call_id:
                responded_ids.add(msg.tool_call_id)

        # Return tool calls that haven't been responded to
        return [
            tc for tc in last_assistant.tool_calls
            if tc.id not in responded_ids
        ]

    def clear(self, keep_system: bool = True) -> None:
        """Clear conversation history"""
        if keep_system and self.system_message:
            system_msg = self.messages[0] if self.messages and self.messages[0].role == MessageRole.SYSTEM else None
            self.messages = [system_msg] if system_msg else []
        else:
            self.messages = []

    def _trim_history(self) -> None:
        """Trim history to stay within limits"""
        if not self.max_messages and not self.max_tokens:
            return

        # Separate system message
        system_msgs = [m for m in self.messages if m.role == MessageRole.SYSTEM]
        other_msgs = [m for m in self.messages if m.role != MessageRole.SYSTEM]

        # Trim by message count
        if self.max_messages and len(other_msgs) > self.max_messages:
            other_msgs = other_msgs[-self.max_messages:]

        # Trim by estimated token count (rough estimate: 4 chars ≈ 1 token)
        if self.max_tokens:
            estimated_tokens = self._estimate_tokens(system_msgs + other_msgs)
            while estimated_tokens > self.max_tokens and len(other_msgs) > 1:
                # Remove oldest non-system message
                other_msgs.pop(0)
                estimated_tokens = self._estimate_tokens(system_msgs + other_msgs)

        self.messages = system_msgs + other_msgs

    def _estimate_tokens(self, messages: List[Message]) -> int:
        """Rough token count estimate"""
        total_chars = 0
        for msg in messages:
            if msg.content:
                total_chars += len(msg.content)
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    total_chars += len(tc.name)
                    if isinstance(tc.arguments, str):
                        total_chars += len(tc.arguments)
                    else:
                        total_chars += len(str(tc.arguments))

        # Rough estimate: 4 characters ≈ 1 token
        return total_chars // 4

    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get conversation statistics"""
        role_counts = {}
        for msg in self.messages:
            role = msg.role.value if hasattr(msg.role, 'value') else str(msg.role)
            role_counts[role] = role_counts.get(role, 0) + 1

        return {
            "total_messages": len(self.messages),
            "by_role": role_counts,
            "estimated_tokens": self._estimate_tokens(self.messages),
            "has_pending_tool_calls": len(self.get_tool_calls_pending()) > 0
        }

    def __len__(self) -> int:
        """Get number of messages"""
        return len(self.messages)

    def __repr__(self) -> str:
        """String representation"""
        return f"ConversationManager(messages={len(self.messages)})"


def format_tool_result_for_llm(
    tool_name: str,
    success: bool,
    output: Any,
    error: Optional[str] = None
) -> str:
    """
    Format tool execution result for LLM consumption

    Args:
        tool_name: Name of the tool
        success: Whether execution was successful
        output: Tool output
        error: Error message if failed

    Returns:
        Formatted string
    """
    if success:
        return f"Tool '{tool_name}' executed successfully.\nResult: {output}"
    else:
        return f"Tool '{tool_name}' failed.\nError: {error}"


def extract_final_answer(text: str, stop_phrases: List[str]) -> Optional[str]:
    """
    Extract final answer from text based on stop phrases

    Args:
        text: Text to search
        stop_phrases: List of phrases that indicate final answer

    Returns:
        Extracted answer or None
    """
    text_lower = text.lower()

    for phrase in stop_phrases:
        phrase_lower = phrase.lower()
        if phrase_lower in text_lower:
            # Find the position of the phrase
            pos = text_lower.index(phrase_lower)
            # Extract everything after the phrase
            answer = text[pos + len(phrase):].strip()

            # Clean up the answer
            # Remove common prefixes
            for prefix in ["-", ":", "：", "—"]:
                if answer.startswith(prefix):
                    answer = answer[1:].strip()

            return answer

    return None


def create_react_system_message(available_tools: List[str]) -> str:
    """
    Create system message for ReAct-style prompting

    Args:
        available_tools: List of available tool names

    Returns:
        System message
    """
    tools_str = "\n".join(f"- {tool}" for tool in available_tools)

    return f"""You are a helpful AI assistant that can use tools to accomplish tasks.

Available tools:
{tools_str}

When solving a problem, follow the ReAct (Reasoning and Acting) pattern:
1. **Thought**: Think about what you need to do next
2. **Action**: Choose a tool to use and specify its arguments
3. **Observation**: Analyze the tool's result
4. **Repeat**: Continue until you can provide a final answer

When you have gathered enough information and can answer the question, provide your final answer clearly.

Be systematic and thorough in your reasoning. Break down complex problems into smaller steps.
"""
