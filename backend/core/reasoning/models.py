"""
Data models for reasoning and thought chain system
"""
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class StepType(str, Enum):
    """Type of reasoning step"""
    THOUGHT = "thought"  # LLM thinking/reasoning
    TOOL_CALL = "tool_call"  # Tool invocation
    TOOL_RESULT = "tool_result"  # Tool execution result
    OBSERVATION = "observation"  # LLM observing tool result
    ANSWER = "answer"  # Final answer
    ERROR = "error"  # Error occurred


class StepStatus(str, Enum):
    """Status of a reasoning step"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ToolCallStep(BaseModel):
    """Tool call information"""
    tool_name: str
    arguments: Dict[str, Any]
    tool_call_id: Optional[str] = None


class ToolResultStep(BaseModel):
    """Tool execution result"""
    tool_name: str
    tool_call_id: Optional[str] = None
    success: bool
    output: Any
    error: Optional[str] = None
    execution_time: float = 0.0


class ReasoningStep(BaseModel):
    """A single step in the reasoning chain"""
    step_id: str
    step_type: StepType
    status: StepStatus = StepStatus.PENDING
    content: Optional[str] = None  # Text content (thought, observation, answer)
    tool_call: Optional[ToolCallStep] = None
    tool_result: Optional[ToolResultStep] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class ReasoningChain(BaseModel):
    """Complete reasoning chain for a task"""
    chain_id: str
    task: str  # Original task/question
    steps: List[ReasoningStep] = Field(default_factory=list)
    status: StepStatus = StepStatus.PENDING
    final_answer: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True

    def add_step(self, step: ReasoningStep) -> None:
        """Add a step to the chain"""
        self.steps.append(step)

    def get_last_step(self) -> Optional[ReasoningStep]:
        """Get the last step in the chain"""
        return self.steps[-1] if self.steps else None

    def get_steps_by_type(self, step_type: StepType) -> List[ReasoningStep]:
        """Get all steps of a specific type"""
        return [step for step in self.steps if step.step_type == step_type]

    def is_complete(self) -> bool:
        """Check if the chain is complete"""
        return self.status in [StepStatus.COMPLETED, StepStatus.FAILED]

    def get_tool_calls_count(self) -> int:
        """Get the number of tool calls made"""
        return len(self.get_steps_by_type(StepType.TOOL_CALL))

    def get_execution_time(self) -> float:
        """Get total execution time in seconds"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return 0.0


class ReasoningConfig(BaseModel):
    """Configuration for reasoning engine"""
    max_iterations: int = 10  # Maximum reasoning iterations
    max_tool_calls: int = 20  # Maximum tool calls per chain
    timeout: float = 300.0  # Maximum time in seconds
    enable_reflection: bool = True  # Enable self-reflection
    verbose: bool = False  # Verbose logging
    stop_phrases: List[str] = Field(
        default_factory=lambda: [
            "Final Answer:",
            "FINAL ANSWER:",
            "最终答案：",
            "答案：",
        ]
    )
    temperature: float = 0.7
    max_tokens: Optional[int] = 2000


class StopReason(str, Enum):
    """Reason for stopping the reasoning chain"""
    COMPLETED = "completed"  # Task completed successfully
    MAX_ITERATIONS = "max_iterations"  # Reached max iterations
    MAX_TOOL_CALLS = "max_tool_calls"  # Reached max tool calls
    TIMEOUT = "timeout"  # Exceeded time limit
    ERROR = "error"  # Error occurred
    USER_INTERRUPT = "user_interrupt"  # User interrupted
    NO_PROGRESS = "no_progress"  # No progress being made


class ReasoningResult(BaseModel):
    """Result of a reasoning process"""
    chain: ReasoningChain
    success: bool
    final_answer: Optional[str] = None
    stop_reason: StopReason
    error: Optional[str] = None
    stats: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_chain(
        cls,
        chain: ReasoningChain,
        stop_reason: StopReason,
        error: Optional[str] = None
    ) -> "ReasoningResult":
        """Create result from chain"""
        success = stop_reason == StopReason.COMPLETED and error is None

        stats = {
            "total_steps": len(chain.steps),
            "tool_calls": chain.get_tool_calls_count(),
            "execution_time": chain.get_execution_time(),
            "iterations": len([s for s in chain.steps if s.step_type == StepType.THOUGHT]),
        }

        return cls(
            chain=chain,
            success=success,
            final_answer=chain.final_answer,
            stop_reason=stop_reason,
            error=error,
            stats=stats
        )
