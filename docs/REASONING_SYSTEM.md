# 推理系统文档

## 概述

推理系统是 LLM 分解工具项目的核心组件，实现了 **ReAct (Reasoning and Acting)** 模式，将大语言模型（LLM）、工具调用和思考链（Chain-of-Thought）整合在一起，使 AI 能够像人类一样思考和行动来解决复杂问题。

## 核心概念

### ReAct 模式

ReAct 是一种将推理（Reasoning）和行动（Acting）相结合的提示工程方法：

1. **Thought（思考）**: LLM 分析问题，思考下一步该做什么
2. **Action（行动）**: LLM 决定使用哪个工具，并指定参数
3. **Observation（观察）**: 分析工具执行的结果
4. **Repeat（重复）**: 继续上述循环，直到找到最终答案

### 思考链（Chain-of-Thought）

思考链记录了解决问题的完整过程，包括：
- 每一步的思考内容
- 工具调用和参数
- 工具执行结果
- 最终答案

## 架构设计

### 核心组件

```
┌─────────────────────────────────────────────┐
│          Reasoning Engine                    │
│  ┌───────────────────────────────────────┐  │
│  │   Conversation Manager                │  │
│  │   (管理对话历史)                      │  │
│  └───────────────────────────────────────┘  │
│                     │                        │
│                     ▼                        │
│  ┌───────────────────────────────────────┐  │
│  │    LLM Provider                       │  │
│  │    (执行推理)                         │  │
│  └───────────────────────────────────────┘  │
│                     │                        │
│                     ▼                        │
│  ┌───────────────────────────────────────┐  │
│  │    Tool Executor                      │  │
│  │    (执行工具)                         │  │
│  └───────────────────────────────────────┘  │
│                     │                        │
│                     ▼                        │
│  ┌───────────────────────────────────────┐  │
│  │    Reasoning Chain                    │  │
│  │    (记录推理过程)                     │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

### 数据模型

#### 1. ReasoningChain（推理链）

记录完整的推理过程：

```python
class ReasoningChain:
    chain_id: str                      # 链 ID
    task: str                          # 原始任务
    steps: List[ReasoningStep]         # 推理步骤列表
    status: StepStatus                 # 状态
    final_answer: Optional[str]        # 最终答案
    started_at: datetime               # 开始时间
    completed_at: datetime             # 完成时间
    metadata: Dict[str, Any]           # 元数据
```

#### 2. ReasoningStep（推理步骤）

单个推理步骤：

```python
class ReasoningStep:
    step_id: str                       # 步骤 ID
    step_type: StepType                # 步骤类型
    status: StepStatus                 # 状态
    content: Optional[str]             # 内容（思考、观察等）
    tool_call: Optional[ToolCallStep]  # 工具调用信息
    tool_result: Optional[ToolResultStep]  # 工具结果
    timestamp: datetime                # 时间戳
    metadata: Dict[str, Any]           # 元数据
```

#### 3. StepType（步骤类型）

```python
class StepType(Enum):
    THOUGHT = "thought"            # LLM 思考
    TOOL_CALL = "tool_call"        # 工具调用
    TOOL_RESULT = "tool_result"    # 工具结果
    OBSERVATION = "observation"     # LLM 观察
    ANSWER = "answer"              # 最终答案
    ERROR = "error"                # 错误
```

#### 4. ReasoningConfig（推理配置）

```python
class ReasoningConfig:
    max_iterations: int = 10       # 最大推理迭代次数
    max_tool_calls: int = 20       # 最大工具调用次数
    timeout: float = 300.0         # 超时时间（秒）
    enable_reflection: bool = True # 启用自我反思
    verbose: bool = False          # 详细日志
    stop_phrases: List[str]        # 停止短语
    temperature: float = 0.7       # LLM 温度
    max_tokens: int = 2000         # 最大 tokens
```

## 使用指南

### 基础使用

```python
import asyncio
from core.llm import get_global_manager
from core.tools import get_global_executor, get_global_registry
from core.reasoning import ReasoningEngine, ReasoningConfig

async def solve_problem():
    # 初始化组件
    llm_manager = get_global_manager()
    provider = llm_manager.get_provider("openai")
    tool_executor = get_global_executor()
    tool_registry = get_global_registry()

    # 创建推理引擎
    config = ReasoningConfig(
        max_iterations=10,
        max_tool_calls=15,
        verbose=True
    )

    engine = ReasoningEngine(
        llm_provider=provider,
        tool_executor=tool_executor,
        tool_registry=tool_registry,
        config=config
    )

    # 解决问题
    task = "计算 (sqrt(144) + 10) * 2 的值"

    async with provider:
        result = await engine.solve(task)

    # 输出结果
    print(f"成功: {result.success}")
    print(f"答案: {result.final_answer}")
    print(f"步骤数: {result.stats['total_steps']}")
    print(f"工具调用: {result.stats['tool_calls']}")

asyncio.run(solve_problem())
```

### 实时监控推理过程

```python
def print_step(step: ReasoningStep):
    """打印推理步骤"""
    if step.step_type == StepType.THOUGHT:
        print(f"💭 思考: {step.content}")
    elif step.step_type == StepType.TOOL_CALL:
        print(f"🔧 工具调用: {step.tool_call.tool_name}")
        print(f"   参数: {step.tool_call.arguments}")
    elif step.step_type == StepType.TOOL_RESULT:
        print(f"✓ 工具结果: {step.tool_result.output}")
    elif step.step_type == StepType.ANSWER:
        print(f"🎯 最终答案: {step.content}")

# 设置回调
engine.set_step_callback(print_step)

# 解决问题（会实时打印步骤）
result = await engine.solve(task)
```

### 高级配置

```python
# 创建自定义配置
config = ReasoningConfig(
    max_iterations=15,              # 增加迭代次数
    max_tool_calls=25,              # 增加工具调用次数
    timeout=600.0,                  # 10分钟超时
    temperature=0.3,                # 降低温度，更确定性
    max_tokens=3000,                # 增加输出长度
    stop_phrases=[                  # 自定义停止短语
        "Final Answer:",
        "最终答案：",
        "答案是："
    ]
)
```

## 推理流程

### 完整流程图

```
开始
  │
  ▼
初始化对话
  │
  ▼
┌─────────────────┐
│  LLM 推理       │◄───────┐
│  (获取响应)     │        │
└─────────────────┘        │
  │                        │
  ▼                        │
检查是否有最终答案          │
  │                        │
  ├─ 是 ──► 返回答案       │
  │                        │
  └─ 否                    │
     │                     │
     ▼                     │
  是否有工具调用            │
     │                     │
     ├─ 否 ──► 继续迭代 ───┘
     │
     └─ 是
        │
        ▼
  ┌──────────────┐
  │ 执行工具调用  │
  └──────────────┘
        │
        ▼
  记录工具结果
        │
        ▼
  检查停止条件
        │
        ├─ 继续 ──────────┘
        │
        └─ 停止 ──► 返回结果
```

### 停止条件

推理引擎会在以下情况停止：

1. **COMPLETED**: 找到最终答案
2. **MAX_ITERATIONS**: 达到最大迭代次数
3. **MAX_TOOL_CALLS**: 达到最大工具调用次数
4. **TIMEOUT**: 超过时间限制
5. **ERROR**: 发生错误
6. **USER_INTERRUPT**: 用户中断

## 示例场景

### 场景 1: 数学计算

**任务**: "计算 sqrt(256) 的平方根，然后乘以 2"

**推理过程**:
1. **Thought**: "我需要计算 sqrt(256) 的平方根，然后将结果乘以 2"
2. **Tool Call**: calculator(expression="sqrt(256)")
3. **Tool Result**: "16.0"
4. **Thought**: "sqrt(256) = 16，现在需要计算 16 * 2"
5. **Tool Call**: calculator(expression="16 * 2")
6. **Tool Result**: "32"
7. **Answer**: "答案是 32"

### 场景 2: 文件操作

**任务**: "创建一个文件 notes.txt，内容是'Hello World'，然后读取它"

**推理过程**:
1. **Thought**: "我需要先创建文件，然后读取"
2. **Tool Call**: file_operations(operation="write", path="notes.txt", content="Hello World")
3. **Tool Result**: "成功写入 11 字符"
4. **Thought**: "文件已创建，现在读取内容"
5. **Tool Call**: file_operations(operation="read", path="notes.txt")
6. **Tool Result**: "Hello World"
7. **Answer**: "文件内容是：Hello World"

### 场景 3: 多步推理

**任务**: "计算一个边长为 sqrt(144) 的正方形的周长和面积"

**推理过程**:
1. **Thought**: "需要先计算边长"
2. **Tool Call**: calculator(expression="sqrt(144)")
3. **Tool Result**: "12.0"
4. **Thought**: "边长是 12，周长 = 4 * 12，面积 = 12 * 12"
5. **Tool Call**: calculator(expression="4 * 12")
6. **Tool Result**: "48"
7. **Tool Call**: calculator(expression="12 * 12")
8. **Tool Result**: "144"
9. **Answer**: "周长是 48，面积是 144"

## 对话管理

### ConversationManager

管理 LLM 对话历史：

```python
from core.reasoning import ConversationManager

# 创建对话管理器
conv = ConversationManager(
    system_message="You are a helpful assistant",
    max_messages=20,          # 最多保留 20 条消息
    max_tokens=4000           # 粗略的 token 限制
)

# 添加消息
conv.add_user_message("Hello")
conv.add_assistant_message("Hi there!")

# 添加工具调用
conv.add_assistant_message(
    content="Let me calculate that",
    tool_calls=[tool_call_object]
)

# 添加工具结果
conv.add_tool_result(
    tool_call_id="call-123",
    tool_name="calculator",
    content="Result: 42"
)

# 获取消息
messages = conv.get_messages()

# 获取摘要
summary = conv.get_conversation_summary()
print(summary)
# {
#     "total_messages": 5,
#     "by_role": {"system": 1, "user": 1, "assistant": 2, "tool": 1},
#     "estimated_tokens": 150,
#     "has_pending_tool_calls": False
# }
```

### 上下文窗口管理

对话管理器自动管理上下文窗口：

1. **消息数量限制**: 超过 `max_messages` 时，删除最旧的消息（保留系统消息）
2. **Token 限制**: 粗略估算 tokens，超出时删除旧消息
3. **系统消息保护**: 系统消息始终保留

## 最佳实践

### 1. 合理设置迭代次数

```python
# 简单任务
config = ReasoningConfig(max_iterations=5)

# 中等复杂度任务
config = ReasoningConfig(max_iterations=10)

# 复杂任务
config = ReasoningConfig(max_iterations=20)
```

### 2. 使用适当的温度

```python
# 需要精确答案（数学、代码）
config = ReasoningConfig(temperature=0.1)

# 平衡（默认）
config = ReasoningConfig(temperature=0.7)

# 需要创造性
config = ReasoningConfig(temperature=0.9)
```

### 3. 监控推理过程

```python
def step_callback(step: ReasoningStep):
    # 记录到日志
    logger.info(f"Step: {step.step_type} - {step.content[:100]}")

    # 发送到前端
    websocket.send(step.dict())

    # 检查异常
    if step.step_type == StepType.ERROR:
        alert_admin(step.content)

engine.set_step_callback(step_callback)
```

### 4. 错误处理

```python
try:
    result = await engine.solve(task)

    if result.success:
        print(f"答案: {result.final_answer}")
    else:
        print(f"失败: {result.stop_reason}")
        print(f"错误: {result.error}")

        # 根据停止原因采取行动
        if result.stop_reason == StopReason.MAX_ITERATIONS:
            # 可能需要增加迭代次数
            pass
        elif result.stop_reason == StopReason.TIMEOUT:
            # 可能需要增加超时时间
            pass

except Exception as e:
    logger.error(f"推理失败: {e}")
```

### 5. 性能优化

```python
# 使用更快的模型进行简单任务
result = await engine.solve(
    task="简单计算: 2 + 2",
    model="gpt-3.5-turbo"  # 更快，更便宜
)

# 复杂任务使用更强大的模型
result = await engine.solve(
    task="复杂的多步推理任务",
    model="gpt-4"  # 更强大
)
```

## 测试

### 单元测试

运行单元测试：

```bash
cd backend
python examples/reasoning_unittest.py
```

测试覆盖：
- 推理链模型
- 对话管理器
- ReAct 提示词生成
- 最终答案提取
- 推理配置
- 步骤类型

### 集成测试（需要 API 密钥）

```bash
cd backend
export OPENAI_API_KEY=your_key_here
python examples/reasoning_demo.py
```

## 扩展开发

### 自定义停止条件

```python
class CustomReasoningEngine(ReasoningEngine):
    def _check_stop_conditions(self, chain):
        # 自定义停止逻辑
        if chain.get_tool_calls_count() >= 5:
            return StopReason.MAX_TOOL_CALLS, True

        # 检查是否卡在循环中
        recent_steps = chain.steps[-5:]
        if all(s.step_type == StepType.THOUGHT for s in recent_steps):
            return StopReason.NO_PROGRESS, True

        return super()._check_stop_conditions(chain)
```

### 自定义提示词

```python
def create_custom_system_message(tools):
    return f"""你是一个专业的数学助手。

可用工具: {', '.join(tools)}

解题步骤：
1. 分析问题
2. 选择合适的工具
3. 验证结果
4. 给出答案

请严格按照步骤进行。"""

# 在创建对话时使用
conversation = ConversationManager(
    system_message=create_custom_system_message(tools)
)
```

## 性能指标

### 单元测试结果

- ✅ 推理链模型测试
- ✅ 对话管理器测试
- ✅ ReAct 提示词生成测试
- ✅ 最终答案提取测试
- ✅ 推理配置测试
- ✅ 步骤类型测试

**测试通过率: 100%**

### 典型性能

- **简单任务（1-2步）**: < 5 秒
- **中等任务（3-5步）**: 10-20 秒
- **复杂任务（5-10步）**: 30-60 秒

*注：实际时间取决于 LLM 响应速度和工具执行时间*

## 未来改进

### 短期计划

- [ ] 添加思考质量评分
- [ ] 实现自我纠错机制
- [ ] 优化上下文管理
- [ ] 添加推理缓存

### 长期计划

- [ ] 支持多 Agent 协作
- [ ] 实现分层推理
- [ ] 添加推理可视化
- [ ] 支持推理回放和调试

## 相关文档

- [工具系统文档](./TOOL_SYSTEM.md)
- [LLM 集成文档](./LLM_INTEGRATION.md)
- [项目计划](../PLAN.md)

## 参考资料

- [ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629)
- [Chain-of-Thought Prompting](https://arxiv.org/abs/2201.11903)
- [Tool Learning with Foundation Models](https://arxiv.org/abs/2304.08354)
