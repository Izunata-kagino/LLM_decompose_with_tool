"""
Reasoning system for Chain-of-Thought processing

This module provides a complete reasoning system that combines:
- LLM inference
- Tool calling
- Chain-of-thought tracking
- ReAct pattern implementation
"""

from .models import (
    ReasoningChain,
    ReasoningStep,
    ReasoningConfig,
    ReasoningResult,
    StepType,
    StepStatus,
    StopReason,
    ToolCallStep,
    ToolResultStep,
)

from .conversation import (
    ConversationManager,
    format_tool_result_for_llm,
    extract_final_answer,
    create_react_system_message,
)

from .engine import ReasoningEngine

__all__ = [
    # Models
    "ReasoningChain",
    "ReasoningStep",
    "ReasoningConfig",
    "ReasoningResult",
    "StepType",
    "StepStatus",
    "StopReason",
    "ToolCallStep",
    "ToolResultStep",
    # Conversation
    "ConversationManager",
    "format_tool_result_for_llm",
    "extract_final_answer",
    "create_react_system_message",
    # Engine
    "ReasoningEngine",
]
