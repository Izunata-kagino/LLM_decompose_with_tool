"""
Tool system usage examples and tests
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.tools import (
    initialize_builtin_tools,
    get_global_registry,
    get_global_executor,
    ToolExecutionContext,
)


async def test_calculator():
    """Test calculator tool"""
    print("\n" + "=" * 60)
    print("测试计算器工具")
    print("=" * 60)

    executor = get_global_executor()

    # Test cases
    test_cases = [
        ("2 + 2", "基本加法"),
        ("10 * 5 + 3", "混合运算"),
        ("sqrt(16)", "平方根"),
        ("sin(pi/2)", "三角函数"),
        ("log(100, 10)", "对数"),
        ("2 ** 10", "幂运算"),
        ("max([1, 5, 3, 9, 2])", "最大值"),
    ]

    for expression, description in test_cases:
        print(f"\n{description}: {expression}")
        result = await executor.execute_tool(
            "calculator",
            {"expression": expression}
        )
        if result.success:
            print(f"✓ 结果: {result.output}")
        else:
            print(f"✗ 错误: {result.error}")


async def test_file_operations():
    """Test file operations tool"""
    print("\n" + "=" * 60)
    print("测试文件操作工具")
    print("=" * 60)

    executor = get_global_executor()
    test_dir = "/tmp/tool_test"
    test_file = f"{test_dir}/test.txt"

    # Create test directory
    os.makedirs(test_dir, exist_ok=True)

    # Test write
    print("\n1. 写入文件")
    result = await executor.execute_tool(
        "file_operations",
        {
            "operation": "write",
            "path": test_file,
            "content": "Hello, Tool System!\n这是一个测试文件。"
        }
    )
    print(f"{'✓' if result.success else '✗'} {result.output if result.success else result.error}")

    # Test read
    print("\n2. 读取文件")
    result = await executor.execute_tool(
        "file_operations",
        {
            "operation": "read",
            "path": test_file
        }
    )
    if result.success:
        print(f"✓ 内容:\n{result.output}")
    else:
        print(f"✗ 错误: {result.error}")

    # Test append
    print("\n3. 追加内容")
    result = await executor.execute_tool(
        "file_operations",
        {
            "operation": "append",
            "path": test_file,
            "content": "\n追加的内容"
        }
    )
    print(f"{'✓' if result.success else '✗'} {result.output if result.success else result.error}")

    # Test list
    print("\n4. 列出目录")
    result = await executor.execute_tool(
        "file_operations",
        {
            "operation": "list",
            "path": test_dir
        }
    )
    if result.success:
        print(f"✓ 文件列表:")
        for item in result.output:
            print(f"  - {item['name']} ({item['type']})")
    else:
        print(f"✗ 错误: {result.error}")

    # Test exists
    print("\n5. 检查文件是否存在")
    result = await executor.execute_tool(
        "file_operations",
        {
            "operation": "exists",
            "path": test_file
        }
    )
    if result.success:
        print(f"✓ {result.output}")
    else:
        print(f"✗ 错误: {result.error}")


async def test_web_search():
    """Test web search tool"""
    print("\n" + "=" * 60)
    print("测试网络搜索工具")
    print("=" * 60)

    executor = get_global_executor()

    print("\n搜索: Python programming")
    result = await executor.execute_tool(
        "web_search",
        {
            "query": "Python programming",
            "num_results": 3
        }
    )

    if result.success:
        print(f"✓ 找到 {len(result.output)} 个结果:")
        for i, item in enumerate(result.output, 1):
            print(f"\n{i}. {item['title']}")
            print(f"   {item['snippet'][:100]}...")
            print(f"   {item['url']}")
    else:
        print(f"✗ 错误: {result.error}")


async def test_code_executor():
    """Test code executor tool"""
    print("\n" + "=" * 60)
    print("测试代码执行工具")
    print("=" * 60)

    executor = get_global_executor()

    # Test cases
    test_cases = [
        (
            "print('Hello, World!')",
            "打印输出"
        ),
        (
            """
import math
result = math.sqrt(144) + math.pi
print(f"Result: {result}")
""",
            "使用数学库"
        ),
        (
            """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

result = [fibonacci(i) for i in range(10)]
print(f"Fibonacci sequence: {result}")
""",
            "递归函数"
        ),
        (
            """
data = [1, 2, 3, 4, 5]
result = sum(x**2 for x in data)
print(f"Sum of squares: {result}")
""",
            "列表推导式"
        ),
    ]

    for code, description in test_cases:
        print(f"\n{description}:")
        print(f"代码:\n{code.strip()}\n")

        result = await executor.execute_tool(
            "code_executor",
            {"code": code}
        )

        if result.success:
            print(f"✓ {result.output}")
        else:
            print(f"✗ 错误: {result.error}")


async def test_registry_and_executor():
    """Test registry and executor features"""
    print("\n" + "=" * 60)
    print("测试注册表和执行器功能")
    print("=" * 60)

    registry = get_global_registry()
    executor = get_global_executor()

    # List all tools
    print("\n1. 已注册的工具:")
    for tool_name in registry.list_tools():
        tool = registry.get(tool_name)
        print(f"  - {tool_name}: {tool.description}")

    # Get schemas
    print("\n2. 工具模式 (LLM 格式):")
    schemas = registry.get_tools_for_llm()
    for schema in schemas:
        func = schema["function"]
        print(f"\n  {func['name']}:")
        print(f"    描述: {func['description']}")
        print(f"    参数: {list(func['parameters'].get('properties', {}).keys())}")

    # Get statistics
    print("\n3. 执行统计:")
    stats = executor.get_statistics()
    print(f"  总执行次数: {stats['total_executions']}")
    print(f"  成功次数: {stats['successful_executions']}")
    print(f"  失败次数: {stats['failed_executions']}")
    if stats['total_executions'] > 0:
        print(f"  成功率: {stats['success_rate']:.1%}")
        print(f"  平均执行时间: {stats['average_execution_time']:.3f}s")

        print(f"\n  各工具使用情况:")
        for tool_name, tool_stats in stats['tools_used'].items():
            print(f"    {tool_name}:")
            print(f"      调用次数: {tool_stats['count']}")
            print(f"      成功: {tool_stats['success']}, 失败: {tool_stats['failed']}")
            print(f"      平均时间: {tool_stats['avg_time']:.3f}s")


async def main():
    """Main test function"""
    print("\n" + "=" * 60)
    print("工具系统测试")
    print("=" * 60)

    # Initialize built-in tools
    print("\n初始化内置工具...")
    tools = initialize_builtin_tools(
        workspace_dir="/tmp/tool_test",
        allow_file_delete=False,
        allow_code_execution=True
    )
    print(f"✓ 已注册 {len(tools)} 个工具: {', '.join(tools)}")

    # Run tests
    try:
        await test_calculator()
        await test_file_operations()
        await test_web_search()
        await test_code_executor()
        await test_registry_and_executor()

        print("\n" + "=" * 60)
        print("✓ 所有测试完成!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
