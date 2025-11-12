# LLM Integration Documentation

## 概述

本项目提供了统一的 LLM 集成层，支持多个 LLM 提供商，包括：
- **OpenAI** (GPT-4, GPT-3.5, GPT-4o)
- **Anthropic** (Claude 3 Opus, Sonnet, Haiku)
- **Grok** (X.AI)

所有提供商都支持：
- ✅ 工具调用（Tool Calling）
- ✅ 结构化输出（Structured Output）
- ✅ 流式响应（Streaming）
- ✅ 异步操作（Async/Await）

## 核心特性

### 1. 统一接口

无需学习不同提供商的 API 差异，使用统一的接口调用所有模型：

```python
from core.llm import get_global_manager
from models import LLMRequest, Message, MessageRole

manager = get_global_manager()
provider = manager.get_provider("openai")  # 或 "anthropic", "grok"

async with provider:
    request = LLMRequest(
        model="gpt-4-turbo-preview",
        messages=[
            Message(role=MessageRole.USER, content="Hello!")
        ]
    )
    response = await provider.complete(request)
    print(response.message.content)
```

### 2. 工具调用

定义工具并让 LLM 自动决定何时调用：

```python
from models import ToolDefinition

# 定义工具
calculator = ToolDefinition(
    name="calculator",
    description="执行数学计算",
    parameters={
        "type": "object",
        "properties": {
            "expression": {"type": "string", "description": "数学表达式"}
        },
        "required": ["expression"]
    }
)

# 使用工具
request = LLMRequest(
    model="gpt-4-turbo-preview",
    messages=[Message(role=MessageRole.USER, content="计算 123 * 456")],
    tools=[calculator],
    tool_choice="auto"  # 让 LLM 决定是否使用工具
)

response = await provider.complete(request)
if response.message.tool_calls:
    tool_call = response.message.tool_calls[0]
    print(f"LLM 想要调用: {tool_call.name}")
    print(f"参数: {tool_call.get_arguments_dict()}")
```

### 3. 结构化输出

确保 LLM 返回符合 JSON Schema 的结构化数据：

```python
from models import StructuredOutputSchema

# 定义输出结构
schema = StructuredOutputSchema(
    name="person",
    description="提取人物信息",
    schema={
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "skills": {
                "type": "array",
                "items": {"type": "string"}
            }
        },
        "required": ["name", "age", "skills"]
    },
    strict=True  # 严格模式
)

request = LLMRequest(
    model="gpt-4-turbo-preview",
    messages=[Message(role=MessageRole.USER, content="John 是一个 30 岁的程序员")],
    structured_output=schema
)

response = await provider.complete(request)
data = json.loads(response.message.content)
# data = {"name": "John", "age": 30, "skills": ["编程"]}
```

### 4. 流式响应

实时接收 LLM 的响应：

```python
request = LLMRequest(
    model="gpt-4-turbo-preview",
    messages=[Message(role=MessageRole.USER, content="写一首诗")],
    stream=True
)

async for chunk in provider.stream_complete(request):
    if "content" in chunk.delta:
        print(chunk.delta["content"], end="", flush=True)
```

## 提供商管理

### 初始化提供商

```python
from core.llm import initialize_providers_from_config
from config import settings

# 从配置自动初始化
initialize_providers_from_config({
    "OPENAI_API_KEY": settings.OPENAI_API_KEY,
    "ANTHROPIC_API_KEY": settings.ANTHROPIC_API_KEY,
    "GROK_API_KEY": settings.GROK_API_KEY,
})
```

### 手动添加提供商

```python
from core.llm import get_global_manager, ProviderType

manager = get_global_manager()

# 添加 OpenAI
manager.add_provider(
    name="my_openai",
    provider_type=ProviderType.OPENAI,
    api_key="sk-...",
    set_as_default=True
)

# 添加 Claude
manager.add_provider(
    name="my_claude",
    provider_type=ProviderType.ANTHROPIC,
    api_key="sk-ant-..."
)
```

### 列出可用提供商

```python
for provider in manager.list_providers():
    print(f"{provider['name']}: {provider['provider_type']}")
    print(f"  支持工具: {provider['supports_tools']}")
    print(f"  支持结构化输出: {provider['supports_structured_output']}")
```

## 支持的模型

### OpenAI
- `gpt-4-turbo-preview`
- `gpt-4`
- `gpt-4o`
- `gpt-4o-mini`
- `gpt-3.5-turbo`

### Anthropic
- `claude-3-opus-20240229`
- `claude-3-sonnet-20240229`
- `claude-3-haiku-20240307`
- `claude-3-5-sonnet-20240620`
- `claude-3-5-sonnet-20241022`

### Grok
- `grok-beta`
- `grok-1`
- `grok-2`

## 多轮对话

```python
messages = []

# 第一轮
messages.append(Message(role=MessageRole.USER, content="你好"))
request = LLMRequest(model="gpt-4", messages=messages)
response = await provider.complete(request)
messages.append(response.message)

# 第二轮
messages.append(Message(role=MessageRole.USER, content="我的名字是 Alice"))
request = LLMRequest(model="gpt-4", messages=messages)
response = await provider.complete(request)
messages.append(response.message)

# 第三轮
messages.append(Message(role=MessageRole.USER, content="我的名字是什么？"))
request = LLMRequest(model="gpt-4", messages=messages)
response = await provider.complete(request)
# LLM 会记住: "你的名字是 Alice"
```

## 工具调用完整流程

```python
from models import Message, MessageRole, ToolResult

# 1. 定义工具
tools = [...]

# 2. 发送请求
messages = [Message(role=MessageRole.USER, content="天气怎么样?")]
request = LLMRequest(model="gpt-4", messages=messages, tools=tools)
response = await provider.complete(request)

# 3. 处理工具调用
if response.message.tool_calls:
    messages.append(response.message)

    for tool_call in response.message.tool_calls:
        # 执行工具
        result = execute_tool(tool_call.name, tool_call.get_arguments_dict())

        # 添加工具结果
        messages.append(Message(
            role=MessageRole.TOOL,
            content=str(result),
            tool_call_id=tool_call.id
        ))

    # 4. 获取最终响应
    request = LLMRequest(model="gpt-4", messages=messages)
    final_response = await provider.complete(request)
    print(final_response.message.content)
```

## 错误处理

```python
try:
    response = await provider.complete(request)
except aiohttp.ClientError as e:
    print(f"网络错误: {e}")
except Exception as e:
    print(f"其他错误: {e}")
```

## 配置选项

在 `.env` 文件中配置：

```env
# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GROK_API_KEY=xai-...

# 默认设置
DEFAULT_PROVIDER=openai
DEFAULT_MODEL=gpt-4-turbo-preview
MAX_TOKENS=4096
TEMPERATURE=0.7
ALLOW_STRUCTURED_OUTPUT=True
```

## 最佳实践

1. **使用异步上下文管理器**: 确保连接正确关闭
   ```python
   async with provider:
       response = await provider.complete(request)
   ```

2. **设置最大 tokens**: 避免意外的高成本
   ```python
   request = LLMRequest(..., max_tokens=1000)
   ```

3. **处理工具调用循环**: 设置最大迭代次数
   ```python
   max_iterations = 10
   for i in range(max_iterations):
       response = await provider.complete(request)
       if not response.message.tool_calls:
           break
       # 处理工具调用...
   ```

4. **错误重试**: 对于网络错误，实现重试逻辑
   ```python
   for attempt in range(3):
       try:
           response = await provider.complete(request)
           break
       except aiohttp.ClientError:
           if attempt == 2:
               raise
           await asyncio.sleep(2 ** attempt)
   ```

5. **监控 token 使用**: 跟踪成本
   ```python
   if response.usage:
       print(f"Total tokens: {response.usage.total_tokens}")
       print(f"Cost estimate: ${response.usage.total_tokens * 0.00001}")
   ```

## 示例代码

完整的示例代码请查看: `backend/examples/llm_usage.py`

运行示例:
```bash
cd backend
python examples/llm_usage.py
```
