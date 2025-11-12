"""
Reasoning engine demonstration and integration test

This demonstrates the complete reasoning system:
- LLM integration
- Tool calling
- Chain-of-thought processing
- ReAct pattern
"""
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.llm import get_global_manager, initialize_providers_from_config
from core.tools import (
    initialize_builtin_tools,
    get_global_registry,
    get_global_executor,
)
from core.reasoning import (
    ReasoningEngine,
    ReasoningConfig,
    ReasoningStep,
    StepType,
)
from config import settings


def print_step(step: ReasoningStep):
    """Pretty print a reasoning step"""
    step_type = step.step_type
    status = step.status

    # Color codes
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

    if step_type == StepType.THOUGHT:
        print(f"\n{BLUE}{BOLD}💭 THOUGHT:{RESET}")
        print(f"{step.content}")

    elif step_type == StepType.TOOL_CALL:
        tool_name = step.tool_call.tool_name
        args = step.tool_call.arguments
        print(f"\n{YELLOW}{BOLD}🔧 TOOL CALL:{RESET} {tool_name}")
        print(f"Arguments: {args}")

    elif step_type == StepType.TOOL_RESULT:
        success = step.tool_result.success
        color = GREEN if success else RED
        symbol = "✓" if success else "✗"
        print(f"\n{color}{BOLD}{symbol} TOOL RESULT:{RESET}")
        if success:
            print(f"{step.tool_result.output}")
        else:
            print(f"Error: {step.tool_result.error}")

    elif step_type == StepType.ANSWER:
        print(f"\n{GREEN}{BOLD}🎯 FINAL ANSWER:{RESET}")
        print(f"{step.content}")

    elif step_type == StepType.ERROR:
        print(f"\n{RED}{BOLD}❌ ERROR:{RESET}")
        print(f"{step.content}")


async def test_basic_calculation():
    """Test basic calculation with tools"""
    print("\n" + "=" * 70)
    print("测试 1: 基础计算")
    print("=" * 70)

    # Initialize
    llm_manager = get_global_manager()
    provider = llm_manager.get_provider("openai")
    tool_executor = get_global_executor()
    tool_registry = get_global_registry()

    # Create reasoning engine
    config = ReasoningConfig(
        max_iterations=5,
        max_tool_calls=10,
        verbose=True,
        temperature=0.3
    )

    engine = ReasoningEngine(
        llm_provider=provider,
        tool_executor=tool_executor,
        tool_registry=tool_registry,
        config=config
    )

    # Set callback to print steps
    engine.set_step_callback(print_step)

    # Solve task
    task = "计算 (sqrt(144) + 10) * 2 的值"

    print(f"\n📝 任务: {task}\n")

    async with provider:
        result = await engine.solve(task)

    # Print result
    print("\n" + "=" * 70)
    print("结果")
    print("=" * 70)
    print(f"成功: {result.success}")
    print(f"停止原因: {result.stop_reason}")
    if result.final_answer:
        print(f"最终答案: {result.final_answer}")
    if result.error:
        print(f"错误: {result.error}")

    print(f"\n统计:")
    for key, value in result.stats.items():
        print(f"  {key}: {value}")


async def test_file_operations():
    """Test file operations"""
    print("\n" + "=" * 70)
    print("测试 2: 文件操作")
    print("=" * 70)

    llm_manager = get_global_manager()
    provider = llm_manager.get_provider("openai")
    tool_executor = get_global_executor()
    tool_registry = get_global_registry()

    config = ReasoningConfig(
        max_iterations=10,
        max_tool_calls=15,
        verbose=True,
        temperature=0.3
    )

    engine = ReasoningEngine(
        llm_provider=provider,
        tool_executor=tool_executor,
        tool_registry=tool_registry,
        config=config
    )

    engine.set_step_callback(print_step)

    task = """创建一个名为 'test_output.txt' 的文件，内容是：
Hello from reasoning engine!
This is line 2.
然后读取这个文件并告诉我文件内容。"""

    print(f"\n📝 任务: {task}\n")

    async with provider:
        result = await engine.solve(task)

    print("\n" + "=" * 70)
    print("结果")
    print("=" * 70)
    print(f"成功: {result.success}")
    print(f"最终答案: {result.final_answer}")
    print(f"\n统计: {result.stats}")


async def test_multi_step_reasoning():
    """Test multi-step reasoning"""
    print("\n" + "=" * 70)
    print("测试 3: 多步推理")
    print("=" * 70)

    llm_manager = get_global_manager()
    provider = llm_manager.get_provider("openai")
    tool_executor = get_global_executor()
    tool_registry = get_global_registry()

    config = ReasoningConfig(
        max_iterations=15,
        max_tool_calls=20,
        verbose=True,
        temperature=0.5
    )

    engine = ReasoningEngine(
        llm_provider=provider,
        tool_executor=tool_executor,
        tool_registry=tool_registry,
        config=config
    )

    engine.set_step_callback(print_step)

    task = """我有一个正方形，边长是 sqrt(256)。
1. 计算这个正方形的周长
2. 计算这个正方形的面积
3. 将计算结果写入文件 'square_results.txt'
4. 读取文件确认内容"""

    print(f"\n📝 任务: {task}\n")

    async with provider:
        result = await engine.solve(task)

    print("\n" + "=" * 70)
    print("结果")
    print("=" * 70)
    print(f"成功: {result.success}")
    print(f"停止原因: {result.stop_reason}")
    if result.final_answer:
        print(f"最终答案: {result.final_answer}")

    print(f"\n统计:")
    for key, value in result.stats.items():
        print(f"  {key}: {value}")


async def test_code_execution():
    """Test code execution reasoning"""
    print("\n" + "=" * 70)
    print("测试 4: 代码执行推理")
    print("=" * 70)

    llm_manager = get_global_manager()
    provider = llm_manager.get_provider("openai")
    tool_executor = get_global_executor()
    tool_registry = get_global_registry()

    config = ReasoningConfig(
        max_iterations=10,
        max_tool_calls=15,
        verbose=True,
        temperature=0.3
    )

    engine = ReasoningEngine(
        llm_provider=provider,
        tool_executor=tool_executor,
        tool_registry=tool_registry,
        config=config
    )

    engine.set_step_callback(print_step)

    task = """使用 Python 代码计算斐波那契数列的前 15 个数，
然后告诉我第 10 个斐波那契数是多少。"""

    print(f"\n📝 任务: {task}\n")

    async with provider:
        result = await engine.solve(task)

    print("\n" + "=" * 70)
    print("结果")
    print("=" * 70)
    print(f"成功: {result.success}")
    print(f"最终答案: {result.final_answer}")
    print(f"\n统计: {result.stats}")


async def main():
    """Main test function"""
    print("\n" + "=" * 70)
    print("推理引擎演示")
    print("=" * 70)

    # Check for API key
    if not settings.OPENAI_API_KEY:
        print("\n⚠️  警告: 未设置 OPENAI_API_KEY")
        print("请在 .env 文件中设置 OPENAI_API_KEY")
        print("\n运行模拟测试...\n")
        return

    # Initialize LLM providers
    print("\n初始化 LLM 提供商...")
    initialize_providers_from_config({
        "OPENAI_API_KEY": settings.OPENAI_API_KEY,
        "ANTHROPIC_API_KEY": settings.ANTHROPIC_API_KEY,
    })
    print("✓ LLM 提供商已初始化")

    # Initialize tools
    print("\n初始化工具系统...")
    tools = initialize_builtin_tools(
        workspace_dir="/tmp/reasoning_test",
        allow_file_delete=False,
        allow_code_execution=True
    )
    print(f"✓ 已注册 {len(tools)} 个工具: {', '.join(tools)}")

    # Run tests
    try:
        # Test 1: Basic calculation
        await test_basic_calculation()

        # Test 2: File operations
        # await test_file_operations()

        # Test 3: Multi-step reasoning
        # await test_multi_step_reasoning()

        # Test 4: Code execution
        # await test_code_execution()

        print("\n" + "=" * 70)
        print("✓ 所有测试完成!")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
