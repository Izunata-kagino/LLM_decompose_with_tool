"""
Reasoning engine for Chain-of-Thought processing with tool calling
"""
from typing import Optional, List, Dict, Any, Callable
import logging
import asyncio
import uuid
from datetime import datetime

from core.llm.base import BaseLLMProvider
from core.tools.executor import ToolExecutor
from core.tools.registry import ToolRegistry
from models.llm_models import (
    Message, MessageRole, LLMRequest, LLMResponse,
    ToolDefinition, ToolCall
)

from .models import (
    ReasoningChain, ReasoningStep, ReasoningConfig, ReasoningResult,
    StepType, StepStatus, StopReason,
    ToolCallStep, ToolResultStep
)
from .conversation import (
    ConversationManager,
    format_tool_result_for_llm,
    extract_final_answer,
    create_react_system_message
)

logger = logging.getLogger(__name__)


class ReasoningEngine:
    """
    Reasoning engine that combines LLM, tools, and chain-of-thought processing

    Implements ReAct (Reasoning and Acting) pattern:
    1. Thought: LLM reasons about the problem
    2. Action: LLM decides to use a tool
    3. Observation: Process tool result
    4. Repeat until final answer
    """

    def __init__(
        self,
        llm_provider: BaseLLMProvider,
        tool_executor: ToolExecutor,
        tool_registry: ToolRegistry,
        config: Optional[ReasoningConfig] = None
    ):
        """
        Initialize reasoning engine

        Args:
            llm_provider: LLM provider for inference
            tool_executor: Tool executor
            tool_registry: Tool registry
            config: Configuration
        """
        self.llm_provider = llm_provider
        self.tool_executor = tool_executor
        self.tool_registry = tool_registry
        self.config = config or ReasoningConfig()

        # Callback for step updates
        self.step_callback: Optional[Callable[[ReasoningStep], None]] = None

    async def solve(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None
    ) -> ReasoningResult:
        """
        Solve a task using reasoning and tool calling

        Args:
            task: Task description or question
            context: Optional context information
            model: LLM model to use

        Returns:
            ReasoningResult with solution
        """
        # Create reasoning chain
        chain = ReasoningChain(
            chain_id=str(uuid.uuid4()),
            task=task,
            status=StepStatus.IN_PROGRESS,
            started_at=datetime.now(),
            metadata=context or {}
        )

        # Initialize conversation
        available_tools = self.tool_registry.list_tools()
        system_message = create_react_system_message(available_tools)
        conversation = ConversationManager(
            system_message=system_message,
            max_messages=self.config.max_iterations * 4  # Rough estimate
        )

        # Add initial user message
        conversation.add_user_message(task)

        # Get tool definitions
        tool_definitions = self._get_tool_definitions()

        # Reasoning loop
        stop_reason = StopReason.COMPLETED
        error_msg = None

        try:
            for iteration in range(self.config.max_iterations):
                if self.config.verbose:
                    logger.info(f"Iteration {iteration + 1}/{self.config.max_iterations}")

                # Check stop conditions
                stop_reason, should_stop = self._check_stop_conditions(chain)
                if should_stop:
                    break

                # Get LLM response
                llm_response = await self._get_llm_response(
                    conversation=conversation,
                    tool_definitions=tool_definitions,
                    model=model
                )

                # Process response
                assistant_message = llm_response.message

                # Check for final answer
                if assistant_message.content:
                    final_answer = extract_final_answer(
                        assistant_message.content,
                        self.config.stop_phrases
                    )
                    if final_answer:
                        # Found final answer
                        step = self._create_answer_step(final_answer)
                        chain.add_step(step)
                        self._notify_step(step)

                        chain.final_answer = final_answer
                        chain.status = StepStatus.COMPLETED
                        stop_reason = StopReason.COMPLETED
                        break

                # Add thought step if there's content
                if assistant_message.content:
                    step = self._create_thought_step(assistant_message.content)
                    chain.add_step(step)
                    self._notify_step(step)

                # Add assistant message to conversation
                conversation.add_assistant_message(
                    content=assistant_message.content,
                    tool_calls=assistant_message.tool_calls
                )

                # Handle tool calls
                if assistant_message.tool_calls:
                    await self._handle_tool_calls(
                        tool_calls=assistant_message.tool_calls,
                        chain=chain,
                        conversation=conversation
                    )
                else:
                    # No tool calls and no final answer - might be stuck
                    if not final_answer:
                        # Add observation and continue
                        if iteration >= self.config.max_iterations - 1:
                            stop_reason = StopReason.MAX_ITERATIONS
                            break

        except asyncio.TimeoutError:
            stop_reason = StopReason.TIMEOUT
            error_msg = "Reasoning exceeded time limit"
            logger.error(error_msg)
        except Exception as e:
            stop_reason = StopReason.ERROR
            error_msg = f"Error during reasoning: {str(e)}"
            logger.error(error_msg, exc_info=True)

            # Add error step
            error_step = self._create_error_step(error_msg)
            chain.add_step(error_step)
            self._notify_step(error_step)

        # Finalize chain
        chain.completed_at = datetime.now()
        chain.status = StepStatus.COMPLETED if stop_reason == StopReason.COMPLETED else StepStatus.FAILED

        # Create result
        result = ReasoningResult.from_chain(
            chain=chain,
            stop_reason=stop_reason,
            error=error_msg
        )

        return result

    async def _get_llm_response(
        self,
        conversation: ConversationManager,
        tool_definitions: List[ToolDefinition],
        model: Optional[str] = None
    ) -> LLMResponse:
        """Get response from LLM"""
        request = LLMRequest(
            model=model or self.llm_provider.default_model,
            messages=conversation.get_messages(),
            tools=tool_definitions if tool_definitions else None,
            tool_choice="auto" if tool_definitions else None,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )

        response = await self.llm_provider.complete(request)
        return response

    async def _handle_tool_calls(
        self,
        tool_calls: List[ToolCall],
        chain: ReasoningChain,
        conversation: ConversationManager
    ) -> None:
        """Handle tool calls from LLM"""
        for tool_call in tool_calls:
            # Add tool call step
            tool_call_step_obj = ToolCallStep(
                tool_name=tool_call.name,
                arguments=tool_call.get_arguments_dict(),
                tool_call_id=tool_call.id
            )

            step = ReasoningStep(
                step_id=str(uuid.uuid4()),
                step_type=StepType.TOOL_CALL,
                status=StepStatus.IN_PROGRESS,
                tool_call=tool_call_step_obj
            )
            chain.add_step(step)
            self._notify_step(step)

            # Execute tool
            start_time = asyncio.get_event_loop().time()

            try:
                result = await self.tool_executor.execute_tool(
                    tool_name=tool_call.name,
                    arguments=tool_call.get_arguments_dict(),
                    timeout=30.0
                )
                execution_time = asyncio.get_event_loop().time() - start_time

                # Update step status
                step.status = StepStatus.COMPLETED

                # Create tool result step
                tool_result_obj = ToolResultStep(
                    tool_name=tool_call.name,
                    tool_call_id=tool_call.id,
                    success=result.success,
                    output=result.output,
                    error=result.error,
                    execution_time=execution_time
                )

                result_step = ReasoningStep(
                    step_id=str(uuid.uuid4()),
                    step_type=StepType.TOOL_RESULT,
                    status=StepStatus.COMPLETED,
                    content=format_tool_result_for_llm(
                        tool_call.name,
                        result.success,
                        result.output,
                        result.error
                    ),
                    tool_result=tool_result_obj
                )
                chain.add_step(result_step)
                self._notify_step(result_step)

                # Add tool result to conversation
                conversation.add_tool_result(
                    tool_call_id=tool_call.id,
                    tool_name=tool_call.name,
                    content=result_step.content
                )

            except Exception as e:
                # Tool execution failed
                step.status = StepStatus.FAILED

                error_msg = f"Tool execution failed: {str(e)}"
                logger.error(error_msg)

                result_step = ReasoningStep(
                    step_id=str(uuid.uuid4()),
                    step_type=StepType.ERROR,
                    status=StepStatus.FAILED,
                    content=error_msg
                )
                chain.add_step(result_step)
                self._notify_step(result_step)

                # Add error to conversation
                conversation.add_tool_result(
                    tool_call_id=tool_call.id,
                    tool_name=tool_call.name,
                    content=error_msg
                )

    def _check_stop_conditions(
        self,
        chain: ReasoningChain
    ) -> tuple[StopReason, bool]:
        """
        Check if reasoning should stop

        Returns:
            (stop_reason, should_stop)
        """
        # Check max tool calls
        if chain.get_tool_calls_count() >= self.config.max_tool_calls:
            return StopReason.MAX_TOOL_CALLS, True

        # Check if already completed
        if chain.is_complete():
            return StopReason.COMPLETED, True

        return StopReason.COMPLETED, False

    def _get_tool_definitions(self) -> List[ToolDefinition]:
        """Get tool definitions from registry"""
        schemas = self.tool_registry.get_schemas()
        return [
            ToolDefinition(
                name=schema.name,
                description=schema.description,
                parameters=schema.parameters
            )
            for schema in schemas
        ]

    def _create_thought_step(self, content: str) -> ReasoningStep:
        """Create a thought step"""
        return ReasoningStep(
            step_id=str(uuid.uuid4()),
            step_type=StepType.THOUGHT,
            status=StepStatus.COMPLETED,
            content=content
        )

    def _create_answer_step(self, content: str) -> ReasoningStep:
        """Create an answer step"""
        return ReasoningStep(
            step_id=str(uuid.uuid4()),
            step_type=StepType.ANSWER,
            status=StepStatus.COMPLETED,
            content=content
        )

    def _create_error_step(self, content: str) -> ReasoningStep:
        """Create an error step"""
        return ReasoningStep(
            step_id=str(uuid.uuid4()),
            step_type=StepType.ERROR,
            status=StepStatus.FAILED,
            content=content
        )

    def _notify_step(self, step: ReasoningStep) -> None:
        """Notify about a new step"""
        if self.step_callback:
            try:
                self.step_callback(step)
            except Exception as e:
                logger.error(f"Error in step callback: {e}")

    def set_step_callback(
        self,
        callback: Callable[[ReasoningStep], None]
    ) -> None:
        """Set callback for step updates"""
        self.step_callback = callback
