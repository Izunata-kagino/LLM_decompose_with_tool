"""
Demo: Multiple LLM Providers with Custom Names

This demonstrates how to configure and use multiple LLM providers
with custom display names.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.llm import (
    initialize_providers_from_yaml,
    get_global_manager,
    get_provider_display_names,
    LLMConfigLoader,
    load_llm_config,
)


def demo_config_loading():
    """Demo configuration loading"""
    print("\n" + "=" * 70)
    print("演示: 配置加载")
    print("=" * 70)

    # Load configuration
    config = load_llm_config()

    print(f"\n默认提供商 ID: {config.default_provider_id}")
    print(f"\n配置的提供商数量: {len(config.providers)}")

    print("\n提供商列表:")
    for provider_config in config.providers:
        status = "✓" if provider_config.has_api_key() else "✗"
        enabled = "启用" if provider_config.enabled else "禁用"

        print(f"\n{status} {provider_config.display_name}")
        print(f"  ID: {provider_config.provider_id}")
        print(f"  类型: {provider_config.provider_type}")
        print(f"  状态: {enabled}")
        print(f"  API Key 环境变量: {provider_config.api_key_env}")
        print(f"  API Key 已设置: {'是' if provider_config.has_api_key() else '否'}")
        if provider_config.default_model:
            print(f"  默认模型: {provider_config.default_model}")
        if provider_config.metadata:
            print(f"  元数据: {provider_config.metadata}")


def demo_provider_initialization():
    """Demo provider initialization"""
    print("\n" + "=" * 70)
    print("演示: 提供商初始化")
    print("=" * 70)

    # Initialize providers
    print("\n初始化提供商...")
    count = initialize_providers_from_yaml()
    print(f"✓ 成功初始化 {count} 个提供商")

    # Get manager
    manager = get_global_manager()

    # List providers
    print("\n已加载的提供商:")
    providers = manager.list_providers()
    for p in providers:
        default_mark = " [默认]" if p['is_default'] else ""
        print(f"\n- {p['name']}{default_mark}")
        print(f"  类型: {p['provider_type']}")
        print(f"  支持工具调用: {'是' if p['supports_tools'] else '否'}")
        print(f"  支持结构化输出: {'是' if p['supports_structured_output'] else '否'}")

    # Get display names
    print("\n提供商显示名称:")
    display_names = get_provider_display_names()
    for provider_id, display_name in display_names.items():
        print(f"  {provider_id}: {display_name}")


async def demo_using_providers():
    """Demo using different providers"""
    print("\n" + "=" * 70)
    print("演示: 使用不同的提供商")
    print("=" * 70)

    manager = get_global_manager()
    providers_list = manager.list_providers()

    if not providers_list:
        print("\n⚠️  没有可用的提供商")
        print("请设置环境变量并在 llm_providers.yaml 中配置提供商")
        return

    from models.llm_models import LLMRequest, Message, MessageRole

    # Test each provider
    for provider_info in providers_list:
        provider_id = provider_info['name']
        provider = manager.get_provider(provider_id)

        print(f"\n测试提供商: {provider_id}")
        print(f"类型: {provider.provider_name}")

        # Create a simple request
        request = LLMRequest(
            model=provider.default_model,
            messages=[
                Message(
                    role=MessageRole.USER,
                    content="用一句话介绍你自己"
                )
            ],
            max_tokens=100
        )

        try:
            async with provider:
                response = await provider.complete(request)

            print(f"✓ 响应: {response.message.content[:100]}...")

        except Exception as e:
            print(f"✗ 错误: {e}")


def demo_creating_config():
    """Demo creating a new configuration file"""
    print("\n" + "=" * 70)
    print("演示: 创建配置文件")
    print("=" * 70)

    # Create a sample configuration
    from core.llm import LLMProvidersConfig, ProviderConfig

    config = LLMProvidersConfig(
        default_provider_id="openai_personal",
        providers=[
            ProviderConfig(
                provider_id="openai_personal",
                provider_type="openai",
                display_name="个人 OpenAI 账户",
                api_key_env="OPENAI_PERSONAL_KEY",
                default_model="gpt-4",
                enabled=True,
                metadata={"tier": "personal"}
            ),
            ProviderConfig(
                provider_id="claude_main",
                provider_type="anthropic",
                display_name="主 Claude 账户",
                api_key_env="ANTHROPIC_API_KEY",
                default_model="claude-3-5-sonnet-20241022",
                enabled=True,
                metadata={"tier": "professional"}
            ),
        ]
    )

    # Save to file
    output_path = "/tmp/llm_providers_example.yaml"
    LLMConfigLoader.save_to_file(config, output_path)
    print(f"\n✓ 配置文件已保存到: {output_path}")

    # Read and display
    with open(output_path, 'r') as f:
        content = f.read()

    print("\n文件内容:")
    print("-" * 70)
    print(content)


def print_setup_guide():
    """Print setup guide"""
    print("\n" + "=" * 70)
    print("设置指南")
    print("=" * 70)

    print("""
1. 复制示例配置文件:
   cp llm_providers.yaml.example llm_providers.yaml

2. 编辑 llm_providers.yaml，自定义提供商名称和设置

3. 设置环境变量（在 .env 文件或 shell 中）:

   # 个人 OpenAI 账户
   export OPENAI_PERSONAL_KEY="sk-proj-..."

   # 公司 OpenAI 账户
   export OPENAI_WORK_KEY="sk-proj-..."

   # Claude 账户
   export ANTHROPIC_API_KEY="sk-ant-..."

   # Gemini 账户
   export GEMINI_API_KEY="AIza..."

4. 在代码中使用:

   from core.llm import initialize_providers_from_yaml, get_global_manager

   # 初始化提供商
   initialize_providers_from_yaml()

   # 获取管理器
   manager = get_global_manager()

   # 使用特定提供商
   provider = manager.get_provider("openai_personal")

5. 配置文件搜索路径（按优先级）:
   - ./llm_providers.yaml
   - config/llm_providers.yaml
   - .config/llm_providers.yaml
   - 如果都没找到，将使用默认配置
""")


async def main():
    """Main function"""
    print("\n" + "=" * 70)
    print("多提供商配置演示")
    print("=" * 70)

    # Demo 1: Configuration loading
    demo_config_loading()

    # Demo 2: Provider initialization
    demo_provider_initialization()

    # Demo 3: Using providers (requires API keys)
    # Uncomment to test with real API keys
    # await demo_using_providers()

    # Demo 4: Creating config file
    demo_creating_config()

    # Setup guide
    print_setup_guide()

    print("\n" + "=" * 70)
    print("演示完成!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
