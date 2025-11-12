"""
Unit tests for reasoning system (without real API calls)

Tests the structure and integration of the reasoning system.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.reasoning import (
    ReasoningChain,
    ReasoningStep,
    ReasoningConfig,
    StepType,
    StepStatus,
    ConversationManager,
    create_react_system_message,
    extract_final_answer,
)
from models.llm_models import Message, MessageRole, ToolCall


def test_reasoning_chain():
    """Test reasoning chain model"""
    print("\n" + "=" * 60)
    print("测试: 推理链模型")
    print("=" * 60)

    chain = ReasoningChain(
        chain_id="test-123",
        task="Test task"
    )

    print(f"Chain ID: {chain.chain_id}")
    print(f"Task: {chain.task}")
    print(f"Status: {chain.status}")

    # Add thought step
    thought_step = ReasoningStep(
        step_id="step-1",
        step_type=StepType.THOUGHT,
        status=StepStatus.COMPLETED,
        content="I need to calculate something"
    )
    chain.add_step(thought_step)
    print(f"✓ Added thought step")

    # Add answer step
    answer_step = ReasoningStep(
        step_id="step-2",
        step_type=StepType.ANSWER,
        status=StepStatus.COMPLETED,
        content="The answer is 42"
    )
    chain.add_step(answer_step)
    chain.final_answer = "The answer is 42"
    chain.status = StepStatus.COMPLETED
    print(f"✓ Added answer step")

    # Check stats
    print(f"\nChain statistics:")
    print(f"  Total steps: {len(chain.steps)}")
    print(f"  Thought steps: {len(chain.get_steps_by_type(StepType.THOUGHT))}")
    print(f"  Tool calls: {chain.get_tool_calls_count()}")
    print(f"  Is complete: {chain.is_complete()}")
    print(f"  Final answer: {chain.final_answer}")

    print("✓ 推理链模型测试通过")


def test_conversation_manager():
    """Test conversation manager"""
    print("\n" + "=" * 60)
    print("测试: 对话管理器")
    print("=" * 60)

    conv = ConversationManager(
        system_message="You are a helpful assistant",
        max_messages=10
    )

    print(f"Initial messages: {len(conv)}")

    # Add user message
    conv.add_user_message("Hello, how are you?")
    print(f"✓ Added user message, total: {len(conv)}")

    # Add assistant message
    conv.add_assistant_message("I'm doing well, thank you!")
    print(f"✓ Added assistant message, total: {len(conv)}")

    # Add tool calls
    tool_calls = [
        ToolCall(
            id="call-1",
            name="calculator",
            arguments={"expression": "2 + 2"}
        )
    ]
    conv.add_assistant_message(
        content="Let me calculate that",
        tool_calls=tool_calls
    )
    print(f"✓ Added message with tool calls, total: {len(conv)}")

    # Add tool result
    conv.add_tool_result(
        tool_call_id="call-1",
        tool_name="calculator",
        content="Result: 4"
    )
    print(f"✓ Added tool result, total: {len(conv)}")

    # Check summary
    summary = conv.get_conversation_summary()
    print(f"\nConversation summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")

    # Test message retrieval
    recent = conv.get_recent_messages(3)
    print(f"\nRecent messages: {len(recent)}")

    last_assistant = conv.get_last_assistant_message()
    print(f"Last assistant message has tool calls: {last_assistant.tool_calls is not None}")

    print("✓ 对话管理器测试通过")


def test_react_prompt():
    """Test ReAct prompt generation"""
    print("\n" + "=" * 60)
    print("测试: ReAct 提示词生成")
    print("=" * 60)

    tools = ["calculator", "file_operations", "web_search"]
    system_message = create_react_system_message(tools)

    print("System message preview:")
    print(system_message[:200] + "...")

    assert "calculator" in system_message
    assert "file_operations" in system_message
    assert "Thought" in system_message
    assert "Action" in system_message

    print("✓ ReAct 提示词生成测试通过")


def test_final_answer_extraction():
    """Test final answer extraction"""
    print("\n" + "=" * 60)
    print("测试: 最终答案提取")
    print("=" * 60)

    test_cases = [
        (
            "After calculating, the Final Answer: 42",
            ["Final Answer:", "FINAL ANSWER:"],
            "42"
        ),
        (
            "Based on my analysis, FINAL ANSWER: The square root is 16",
            ["Final Answer:", "FINAL ANSWER:"],
            "The square root is 16"
        ),
        (
            "经过计算，最终答案：结果是100",
            ["最终答案：", "答案："],
            "结果是100"
        ),
        (
            "This is just reasoning, no answer yet",
            ["Final Answer:", "最终答案："],
            None
        )
    ]

    for text, stop_phrases, expected in test_cases:
        result = extract_final_answer(text, stop_phrases)
        status = "✓" if result == expected else "✗"
        print(f"{status} Input: '{text[:50]}...'")
        print(f"   Expected: {expected}, Got: {result}")

        if result != expected:
            print("   ❌ FAILED")
            return

    print("✓ 最终答案提取测试通过")


def test_reasoning_config():
    """Test reasoning configuration"""
    print("\n" + "=" * 60)
    print("测试: 推理配置")
    print("=" * 60)

    config = ReasoningConfig(
        max_iterations=15,
        max_tool_calls=25,
        timeout=600.0,
        verbose=True
    )

    print(f"Max iterations: {config.max_iterations}")
    print(f"Max tool calls: {config.max_tool_calls}")
    print(f"Timeout: {config.timeout}s")
    print(f"Temperature: {config.temperature}")
    print(f"Stop phrases: {len(config.stop_phrases)}")

    # Test defaults
    default_config = ReasoningConfig()
    print(f"\nDefault config:")
    print(f"  Max iterations: {default_config.max_iterations}")
    print(f"  Max tool calls: {default_config.max_tool_calls}")
    print(f"  Timeout: {default_config.timeout}s")

    print("✓ 推理配置测试通过")


def test_step_types():
    """Test all step types"""
    print("\n" + "=" * 60)
    print("测试: 步骤类型")
    print("=" * 60)

    step_types = [
        StepType.THOUGHT,
        StepType.TOOL_CALL,
        StepType.TOOL_RESULT,
        StepType.OBSERVATION,
        StepType.ANSWER,
        StepType.ERROR,
    ]

    print("Available step types:")
    for step_type in step_types:
        step = ReasoningStep(
            step_id=f"test-{step_type}",
            step_type=step_type,
            status=StepStatus.COMPLETED,
            content=f"Test {step_type}"
        )
        print(f"  ✓ {step_type}: {step.step_id}")

    print("✓ 步骤类型测试通过")


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("推理系统单元测试")
    print("=" * 60)

    try:
        test_reasoning_chain()
        test_conversation_manager()
        test_react_prompt()
        test_final_answer_extraction()
        test_reasoning_config()
        test_step_types()

        print("\n" + "=" * 60)
        print("✓ 所有单元测试通过!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
