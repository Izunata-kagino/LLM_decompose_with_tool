"""
Example: Using LLM providers with tool calling and structured output
"""
import asyncio
import json
from typing import Dict, Any

from core.llm import (
    get_global_manager,
    initialize_providers_from_config,
    ProviderType
)
from models import (
    LLMRequest,
    Message,
    MessageRole,
    ToolDefinition,
    StructuredOutputSchema
)
from config import settings


async def example_basic_completion():
    """Example 1: Basic completion without tools"""
    print("\n=== Example 1: Basic Completion ===")

    # Initialize providers from config
    initialize_providers_from_config({
        "OPENAI_API_KEY": settings.OPENAI_API_KEY,
        "ANTHROPIC_API_KEY": settings.ANTHROPIC_API_KEY,
        "GROK_API_KEY": settings.GROK_API_KEY,
    })

    manager = get_global_manager()
    provider = manager.get_provider("openai")

    async with provider:
        request = LLMRequest(
            model="gpt-4-turbo-preview",
            messages=[
                Message(role=MessageRole.SYSTEM, content="You are a helpful assistant."),
                Message(role=MessageRole.USER, content="What is 2+2?"),
            ],
            temperature=0.7,
            max_tokens=100
        )

        response = await provider.complete(request)
        print(f"Response: {response.message.content}")
        print(f"Tokens used: {response.usage.total_tokens if response.usage else 'N/A'}")


async def example_tool_calling():
    """Example 2: Tool calling"""
    print("\n=== Example 2: Tool Calling ===")

    # Define a calculator tool
    calculator_tool = ToolDefinition(
        name="calculator",
        description="Perform basic arithmetic operations",
        parameters={
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["add", "subtract", "multiply", "divide"],
                    "description": "The arithmetic operation to perform"
                },
                "a": {
                    "type": "number",
                    "description": "First number"
                },
                "b": {
                    "type": "number",
                    "description": "Second number"
                }
            },
            "required": ["operation", "a", "b"]
        }
    )

    manager = get_global_manager()
    provider = manager.get_provider()

    async with provider:
        # First request - LLM decides to use tool
        request = LLMRequest(
            model="gpt-4-turbo-preview",
            messages=[
                Message(role=MessageRole.USER, content="What is 123 multiplied by 456?"),
            ],
            tools=[calculator_tool],
            tool_choice="auto"
        )

        response = await provider.complete(request)
        print(f"LLM Response: {response.message.content}")

        if response.message.tool_calls:
            print(f"\nLLM wants to call tool:")
            for tool_call in response.message.tool_calls:
                print(f"  Tool: {tool_call.name}")
                print(f"  Arguments: {tool_call.get_arguments_dict()}")

                # Simulate tool execution
                args = tool_call.get_arguments_dict()
                if args["operation"] == "multiply":
                    result = args["a"] * args["b"]
                    print(f"  Result: {result}")


async def example_structured_output():
    """Example 3: Structured output"""
    print("\n=== Example 3: Structured Output ===")

    # Define schema for structured output
    person_schema = StructuredOutputSchema(
        name="person_info",
        description="Extract person information",
        schema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Person's full name"
                },
                "age": {
                    "type": "integer",
                    "description": "Person's age"
                },
                "occupation": {
                    "type": "string",
                    "description": "Person's occupation"
                },
                "skills": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of skills"
                }
            },
            "required": ["name", "age", "occupation", "skills"]
        },
        strict=True
    )

    manager = get_global_manager()
    provider = manager.get_provider()

    async with provider:
        request = LLMRequest(
            model="gpt-4-turbo-preview",
            messages=[
                Message(
                    role=MessageRole.USER,
                    content="John Smith is a 35 year old software engineer. He specializes in Python, JavaScript, and cloud architecture."
                ),
            ],
            structured_output=person_schema
        )

        response = await provider.complete(request)
        print("Structured Output:")
        if response.message.content:
            data = json.loads(response.message.content)
            print(json.dumps(data, indent=2))


async def example_streaming():
    """Example 4: Streaming response"""
    print("\n=== Example 4: Streaming Response ===")

    manager = get_global_manager()
    provider = manager.get_provider()

    async with provider:
        request = LLMRequest(
            model="gpt-4-turbo-preview",
            messages=[
                Message(role=MessageRole.USER, content="Write a short poem about coding"),
            ],
            stream=True
        )

        print("Streaming response:")
        async for chunk in provider.stream_complete(request):
            if "content" in chunk.delta:
                print(chunk.delta["content"], end="", flush=True)
        print()


async def example_multi_provider():
    """Example 5: Using multiple providers"""
    print("\n=== Example 5: Multiple Providers ===")

    manager = get_global_manager()

    # List all available providers
    print("Available providers:")
    for provider_info in manager.list_providers():
        print(f"  - {provider_info['name']} ({provider_info['provider_type']})")
        print(f"    Tools: {provider_info['supports_tools']}")
        print(f"    Structured Output: {provider_info['supports_structured_output']}")

    # Use different providers for the same task
    prompt = Message(role=MessageRole.USER, content="Say hello in one sentence")

    for provider_name in ["openai", "anthropic", "grok"]:
        try:
            provider = manager.get_provider(provider_name)
            async with provider:
                request = LLMRequest(
                    model=provider.get_supported_models()[0],
                    messages=[prompt],
                    max_tokens=50
                )
                response = await provider.complete(request)
                print(f"\n{provider_name}: {response.message.content}")
        except Exception as e:
            print(f"\n{provider_name}: Error - {e}")


async def example_complex_tool_conversation():
    """Example 6: Multi-turn conversation with tools"""
    print("\n=== Example 6: Complex Tool Conversation ===")

    # Define multiple tools
    tools = [
        ToolDefinition(
            name="get_weather",
            description="Get current weather for a location",
            parameters={
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City name"},
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
                },
                "required": ["location"]
            }
        ),
        ToolDefinition(
            name="search_web",
            description="Search the web for information",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        )
    ]

    manager = get_global_manager()
    provider = manager.get_provider()

    messages = [
        Message(role=MessageRole.USER, content="What's the weather like in Paris?")
    ]

    async with provider:
        # First turn - LLM calls tool
        request = LLMRequest(
            model="gpt-4-turbo-preview",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )

        response = await provider.complete(request)
        messages.append(response.message)

        if response.message.tool_calls:
            print(f"LLM called tool: {response.message.tool_calls[0].name}")
            print(f"Arguments: {response.message.tool_calls[0].get_arguments_dict()}")

            # Simulate tool execution
            tool_result = Message(
                role=MessageRole.TOOL,
                content="The weather in Paris is sunny with a temperature of 22°C",
                tool_call_id=response.message.tool_calls[0].id
            )
            messages.append(tool_result)

            # Second turn - LLM uses tool result
            request = LLMRequest(
                model="gpt-4-turbo-preview",
                messages=messages
            )

            response = await provider.complete(request)
            print(f"\nFinal response: {response.message.content}")


async def main():
    """Run all examples"""
    print("=" * 60)
    print("LLM Provider Examples")
    print("=" * 60)

    # Run examples
    try:
        await example_basic_completion()
    except Exception as e:
        print(f"Error: {e}")

    try:
        await example_tool_calling()
    except Exception as e:
        print(f"Error: {e}")

    try:
        await example_structured_output()
    except Exception as e:
        print(f"Error: {e}")

    try:
        await example_streaming()
    except Exception as e:
        print(f"Error: {e}")

    try:
        await example_multi_provider()
    except Exception as e:
        print(f"Error: {e}")

    try:
        await example_complex_tool_conversation()
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
