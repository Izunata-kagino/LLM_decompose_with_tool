# LLM Models Guide - 2025 Edition

## 概述

本文档列出了 2025 年支持的所有最新 LLM 模型及其特性。

## 支持的提供商

1. **OpenAI** - GPT-5, GPT-4.1 系列, O-series 推理模型
2. **Anthropic** - Claude 4.5, 4.1, 4 系列
3. **Google Gemini** - Gemini 2.5 Pro, Flash
4. **Grok (X.AI)** - Grok 4, Grok 3 系列

---

## OpenAI Models (2025)

### GPT-5 (August 2025)
**最新旗舰模型** - OpenAI 最先进的模型
- Model ID: `gpt-5`
- 描述: "PhD-level expert in your pocket"
- 擅长: 代码、数学、健康建议、图像分析
- 所有任务的最佳选择

### GPT-4.1 系列
**1M context window, June 2024 knowledge**

#### GPT-4.1
- Model ID: `gpt-4.1`
- Context: 1M tokens
- 特点: 超越 GPT-4o，编码和指令遵循有重大提升
- 长上下文理解能力增强

#### GPT-4.1 Mini
- Model ID: `gpt-4.1-mini`
- 更快更便宜的版本

#### GPT-4.1 Nano
- Model ID: `gpt-4.1-nano`
- 最轻量版本

### O-Series 推理模型
**专注于推理和问题解决**

#### O3
- Model ID: `o3`
- 特点: 花更多时间处理请求
- 擅长: 科学、编码、数学

#### O4-Mini / O4-Mini-High
- Model ID: `o4-mini`, `o4-mini-high`
- 轻量级推理模型

### Legacy Models
- `gpt-4o` - 多模态模型 (Legacy)
- `gpt-4o-mini` - 更快更便宜
- `gpt-4-turbo` - 较旧但仍可用
- `gpt-4` - 经典模型
- `gpt-3.5-turbo` - 最便宜的选项

### 推荐用途
| 任务 | 推荐模型 | 原因 |
|------|---------|------|
| 通用任务 | `gpt-5` | 最强大 |
| 编码 | `gpt-4.1` | 编码提升 |
| 推理/数学 | `o3` | 专门优化 |
| 快速响应 | `gpt-4.1-mini` | 性价比 |
| 预算有限 | `gpt-3.5-turbo` | 最便宜 |

---

## Anthropic Models (2025)

### Claude 4.5 系列 (最新)

#### Claude Sonnet 4.5 (September 2025)
**世界上最好的编码模型**
- Model ID: `claude-sonnet-4-5`
- Context: 1M tokens (with header)
- 价格: $3/$15 per 1M tokens
- 特点: 推理和数学能力大幅提升
- Knowledge: Trained on July 2025, extensive through Jan 2025

#### Claude Haiku 4.5 (October 2025)
**快速且经济**
- Model ID: `claude-haiku-4-5`
- 价格: $1/$5 per 1M tokens
- 特点: 与 Sonnet 4 相似的编码性能，1/3成本，2倍速度

### Claude 4.1 系列

#### Claude Opus 4.1 (August 2025)
**专注于代理任务**
- Model ID: `claude-opus-4-1`
- 价格: $15/$75 per 1M tokens
- 特点: 升级版 Opus 4，专注于代理任务、实际编码和推理

### Claude 4 系列 (May 2025)

#### Claude Sonnet 4
- Model ID: `claude-sonnet-4`
- 特点: 混合模型，两种模式
  - 近乎即时的响应
  - 扩展思考进行深度推理

#### Claude Opus 4
- Model ID: `claude-opus-4`
- 最强大的 Claude 4 模型

### Legacy Claude 3.x
- `claude-3-opus-20240229`
- `claude-3-sonnet-20240229`
- `claude-3-haiku-20240307`
- `claude-3-5-sonnet-20240620`
- `claude-3-5-sonnet-20241022`
- `claude-3-5-haiku-20241022`

### 推荐用途
| 任务 | 推荐模型 | 原因 |
|------|---------|------|
| 编码 | `claude-sonnet-4-5` | 世界最佳 |
| 快速任务 | `claude-haiku-4-5` | 快速+便宜 |
| 复杂代理 | `claude-opus-4-1` | 代理优化 |
| 深度推理 | `claude-opus-4` | 扩展思考模式 |

---

## Google Gemini Models (2025)

**重要**: 所有 Gemini 1.0 和 1.5 模型于 2025年4月29日退役

### Gemini 2.5 系列

#### Gemini 2.5 Pro
**最强大和完整的模型**
- Model ID: `gemini-2.5-pro`
- 特点: 自适应思考 (adaptive thinking)
- 用途: 长文本生成、企业场景

#### Gemini 2.5 Flash
**性能优秀且经济**
- Model ID: `gemini-2.5-flash`
- 特点: LMarena leaderboard #2 (仅次于 2.5 Pro)
- 用途: 大多数任务的最佳选择

#### Gemini 2.5 Flash Preview
- Model ID: `gemini-2.5-flash-preview-05-20`
- 特点: 在推理、代码和长上下文方面优于之前的预览版

#### Gemini 2.5 Flash Lite
- Model ID: `gemini-2.5-flash-lite`
- 用途: 轻量级任务

### 专用模型

#### Gemini 2.5 Computer Use
- Model ID: `gemini-2.5-computer-use`
- 特点: 专门构建用于 UI 交互的模型
- 用途: 能够与用户界面交互的代理

#### Gemini 2.5 Image Preview
- Model ID: `gemini-2.5-image-preview`
- 用途: 原生图像生成

### 推荐用途
| 任务 | 推荐模型 | 原因 |
|------|---------|------|
| 通用任务 | `gemini-2.5-flash` | 高性能+成本 |
| 复杂任务 | `gemini-2.5-pro` | 最强大 |
| UI 自动化 | `gemini-2.5-computer-use` | 专用模型 |
| 图像生成 | `gemini-2.5-image-preview` | 原生支持 |
| 轻量任务 | `gemini-2.5-flash-lite` | 最便宜 |

---

## Grok Models (2025)

### Grok 4 (2025)
**世界上最智能的模型**
- Model ID: `grok-4`, `grok-4-0709`
- Context: 256K tokens
- 价格: $3/$15 per 1M tokens
- 特点:
  - 原生工具使用
  - 实时搜索集成 (Live Search - $25/1K sources)
- Knowledge: November 2024 (可通过 Live Search 获取实时信息)

### Grok 3 系列

#### Grok 3
- Model ID: `grok-3`
- Knowledge: November 2024
- 特点: Live Search 支持

#### Grok 3 Mini
**轻量级推理模型**
- Model ID: `grok-3-mini`
- 特点: 思考后响应，擅长数学和推理

### 专用模型

#### Grok Code Fast 1
- Model ID: `grok-code-fast-1`
- 特点: 快速且经济的推理模型
- 用途: 代理编码任务

#### Grok 2 Image
- Model ID: `grok-2-image`
- 用途: 图像生成
- 特点: 可从文本提示生成多张图像

### Legacy
- `grok-2`
- `grok-1`
- `grok-beta`

### 推荐用途
| 任务 | 推荐模型 | 原因 |
|------|---------|------|
| 需要最新信息 | `grok-4` + Live Search | 实时搜索 |
| 数学/推理 | `grok-3-mini` | 专门优化 |
| 快速编码 | `grok-code-fast-1` | 速度优化 |
| 图像生成 | `grok-2-image` | 图像专用 |

---

## 横向比较

### 编码任务
1. **Claude Sonnet 4.5** - 世界最佳编码模型
2. **GPT-4.1** - 编码能力大幅提升
3. **Grok Code Fast 1** - 快速编码
4. **Gemini 2.5 Flash** - 平衡性能

### 推理/数学
1. **O3** (OpenAI) - 专门推理模型
2. **Grok 3 Mini** - 数学和推理优化
3. **Claude Opus 4.1** - 强大推理
4. **Gemini 2.5 Pro** - 自适应思考

### 通用任务
1. **GPT-5** - 最先进
2. **Claude Sonnet 4.5** - 全面优秀
3. **Gemini 2.5 Flash** - 性价比最佳
4. **Grok 4** - 带实时搜索

### 成本效益
1. **Gemini 2.5 Flash Lite** - 最便宜
2. **Claude Haiku 4.5** - $1/$5, 快速
3. **GPT-4.1 Mini** - OpenAI 经济选择
4. **Grok 3 Mini** - 轻量级

### Context Window
1. **GPT-4.1** - 1M tokens
2. **Claude 4.5** - 1M tokens (with header)
3. **Grok 4** - 256K tokens
4. **Gemini 2.5** - 大容量 (具体取决于模型)

---

## 功能支持矩阵

| 提供商 | 工具调用 | 结构化输出 | 流式响应 | 图像输入 | 图像生成 |
|--------|---------|-----------|----------|---------|---------|
| OpenAI | ✅ | ✅ | ✅ | ✅ (GPT-4o) | ❌ |
| Anthropic | ✅ | ✅ | ✅ | ✅ | ❌ |
| Gemini | ✅ | ✅ | ✅ | ✅ | ✅ (Image model) |
| Grok | ✅ | ✅ | ✅ | ❌ | ✅ (2-Image) |

---

## 选择建议

### 如果你需要...

**最强性能**: GPT-5 或 Claude Sonnet 4.5

**编码**: Claude Sonnet 4.5 > GPT-4.1 > Grok Code Fast 1

**推理/数学**: O3 > Grok 3 Mini > Claude Opus 4.1

**实时信息**: Grok 4 with Live Search

**性价比**: Gemini 2.5 Flash > Claude Haiku 4.5

**图像生成**: Gemini 2.5 Image Preview 或 Grok 2 Image

**UI 自动化**: Gemini 2.5 Computer Use

**大 Context**: GPT-4.1 或 Claude 4.5 (1M tokens)

---

## 知识截止日期

| 提供商 | 模型 | 知识截止 |
|--------|------|---------|
| OpenAI | GPT-5 | 取决于训练 |
| OpenAI | GPT-4.1 | June 2024 |
| Anthropic | Claude 4.5 | July 2025 (trained), Jan 2025 (extensive) |
| Gemini | 2.5 系列 | 取决于模型 |
| Grok | Grok 4/3 | November 2024 + Live Search |

---

## 迁移指南

### 从旧模型迁移

**OpenAI:**
- `gpt-4-turbo-preview` → `gpt-4.1` 或 `gpt-5`
- `gpt-4o` → `gpt-5`

**Anthropic:**
- `claude-3-5-sonnet-*` → `claude-sonnet-4-5`
- `claude-3-5-haiku-*` → `claude-haiku-4-5`
- `claude-3-opus-*` → `claude-opus-4-1`

**Gemini:**
- `gemini-1.5-pro` → `gemini-2.5-pro` (已退役，必须迁移)
- `gemini-1.5-flash` → `gemini-2.5-flash`

---

## 使用示例

```python
from core.llm import get_global_manager
from models import LLMRequest, Message, MessageRole

manager = get_global_manager()

# 使用最新模型
async with manager.get_provider("openai") as provider:
    request = LLMRequest(
        model="gpt-5",  # 最新模型
        messages=[Message(role=MessageRole.USER, content="Hello!")]
    )
    response = await provider.complete(request)

# Anthropic
async with manager.get_provider("anthropic") as provider:
    request = LLMRequest(
        model="claude-sonnet-4-5",  # 最佳编码模型
        messages=[Message(role=MessageRole.USER, content="Write code")]
    )
    response = await provider.complete(request)

# Gemini
async with manager.get_provider("gemini") as provider:
    request = LLMRequest(
        model="gemini-2.5-flash",  # 性价比最佳
        messages=[Message(role=MessageRole.USER, content="Explain AI")]
    )
    response = await provider.complete(request)

# Grok
async with manager.get_provider("grok") as provider:
    request = LLMRequest(
        model="grok-4",  # 带实时搜索
        messages=[Message(role=MessageRole.USER, content="Latest news?")]
    )
    response = await provider.complete(request)
```

---

## 更新日志

- **2025-11**: 创建文档，覆盖所有 2025 最新模型
- 下次更新: 当新模型发布时
