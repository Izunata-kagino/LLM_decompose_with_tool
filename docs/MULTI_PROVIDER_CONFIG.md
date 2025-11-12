# 多提供商配置文档

## 概述

本系统支持使用 YAML 配置文件管理多个 LLM 提供商，每个提供商可以有自定义的显示名称。这使您可以：

- ✅ 配置多个相同类型提供商的不同账户（例如：个人 OpenAI、公司 OpenAI）
- ✅ 为每个提供商设置自定义显示名称
- ✅ 灵活启用/禁用提供商
- ✅ 安全地管理 API 密钥（通过环境变量）
- ✅ 明文存储环境变量名称（可版本控制）

## 快速开始

### 1. 创建配置文件

```bash
cp llm_providers.yaml.example llm_providers.yaml
```

### 2. 编辑配置文件

```yaml
# llm_providers.yaml
default_provider_id: openai_personal

providers:
  - provider_id: openai_personal
    provider_type: openai
    display_name: "个人 OpenAI 账户"
    api_key_env: OPENAI_PERSONAL_KEY
    default_model: gpt-4
    enabled: true

  - provider_id: openai_work
    provider_type: openai
    display_name: "公司 OpenAI 账户"
    api_key_env: OPENAI_WORK_KEY
    default_model: gpt-3.5-turbo
    enabled: true

  - provider_id: claude_main
    provider_type: anthropic
    display_name: "主 Claude 账户"
    api_key_env: ANTHROPIC_API_KEY
    default_model: claude-3-5-sonnet-20241022
    enabled: true
```

### 3. 设置环境变量

在 `.env` 文件或 shell 中设置：

```bash
# 个人 OpenAI 账户
export OPENAI_PERSONAL_KEY="sk-proj-..."

# 公司 OpenAI 账户
export OPENAI_WORK_KEY="sk-proj-..."

# Claude 账户
export ANTHROPIC_API_KEY="sk-ant-..."
```

### 4. 在代码中使用

```python
from core.llm import initialize_providers_from_yaml, get_global_manager

# 初始化提供商
initialize_providers_from_yaml()

# 获取管理器
manager = get_global_manager()

# 使用特定提供商
provider = manager.get_provider("openai_personal")

# 或使用默认提供商
default_provider = manager.get_provider()

# 列出所有提供商
providers = manager.list_providers()
for p in providers:
    print(f"{p['name']}: {p['provider_type']}")
```

## 配置文件格式

### 完整配置示例

```yaml
# 默认使用的提供商 ID
default_provider_id: openai_personal

# 提供商列表
providers:
  - provider_id: unique_identifier        # 必需：唯一标识符
    provider_type: openai                 # 必需：提供商类型
    display_name: "显示名称"              # 必需：用户可见的名称
    api_key_env: ENV_VAR_NAME            # 必需：API 密钥的环境变量名
    default_model: gpt-4                 # 可选：默认模型
    base_url: https://api.custom.com     # 可选：自定义 API 端点
    enabled: true                         # 可选：是否启用（默认 true）
    metadata:                            # 可选：自定义元数据
      description: "描述信息"
      tier: "personal"
      rate_limit: "standard"
```

### 字段说明

#### provider_id（必需）

- 提供商的唯一标识符
- 用于在代码中引用此提供商
- 必须在所有提供商中唯一
- 建议使用小写字母、数字和下划线
- 示例：`openai_personal`, `claude_work`, `gemini_test`

#### provider_type（必需）

- LLM 提供商的类型
- 支持的值：
  - `openai` - OpenAI (GPT 系列)
  - `anthropic` - Anthropic (Claude 系列)
  - `gemini` - Google Gemini
  - `grok` - Grok (X.AI)
- 可以有多个相同类型的提供商

#### display_name（必需）

- 用户可见的显示名称
- 在 UI 和日志中显示
- 可以包含 Unicode 字符（中文、日文等）
- 示例：`"个人 OpenAI 账户"`, `"Work Claude"`, `"测试环境"`

#### api_key_env（必需）

- API 密钥对应的环境变量名称
- **重要**: API 密钥本身从不存储在配置文件中
- 此字段是明文的，可以安全地提交到版本控制
- 系统会从环境变量读取实际的 API 密钥
- 示例：`OPENAI_PERSONAL_KEY`, `ANTHROPIC_API_KEY`

#### default_model（可选）

- 此提供商默认使用的模型
- 可以在每个请求中覆盖
- 如果不指定，提供商会使用自己的默认值
- 示例：
  - OpenAI: `gpt-4`, `gpt-3.5-turbo`, `gpt-4-turbo`
  - Anthropic: `claude-3-5-sonnet-20241022`, `claude-3-opus-20240229`
  - Gemini: `gemini-pro`, `gemini-1.5-pro`
  - Grok: `grok-beta`, `grok-2`

#### base_url（可选）

- 自定义 API 端点 URL
- 用于 OpenAI 兼容的服务
- 官方 API 不需要设置
- 示例：`https://api.openai-compatible-service.com/v1`

#### enabled（可选，默认 true）

- 是否启用此提供商
- `true`: 提供商会被初始化（如果 API 密钥可用）
- `false`: 提供商会被跳过，不会初始化
- 用于临时禁用某些提供商而不删除配置

#### metadata（可选）

- 自定义元数据字典
- 可以存储任何额外信息
- 用于文档、注释或自定义逻辑
- 示例：
  ```yaml
  metadata:
    description: "用于机器学习项目的账户"
    tier: "enterprise"
    rate_limit: "high"
    cost_center: "R&D"
    contact: "admin@company.com"
  ```

## 配置文件搜索路径

系统按以下优先级搜索配置文件：

1. `./llm_providers.yaml` - 当前目录
2. `config/llm_providers.yaml` - config 子目录
3. `.config/llm_providers.yaml` - 隐藏配置目录
4. 如果都没找到，使用默认配置（从环境变量）

您也可以手动指定配置文件路径：

```python
initialize_providers_from_yaml("path/to/custom_config.yaml")
```

## 使用场景

### 场景 1: 个人和工作账户分离

```yaml
default_provider_id: openai_work

providers:
  - provider_id: openai_personal
    provider_type: openai
    display_name: "个人 OpenAI 账户"
    api_key_env: OPENAI_PERSONAL_KEY
    default_model: gpt-4
    enabled: true
    metadata:
      usage: "个人项目和学习"

  - provider_id: openai_work
    provider_type: openai
    display_name: "公司 OpenAI 账户"
    api_key_env: OPENAI_WORK_KEY
    default_model: gpt-4-turbo
    enabled: true
    metadata:
      usage: "生产环境"
      billing: "公司账单"
```

使用：

```python
# 工作项目使用工作账户
work_provider = manager.get_provider("openai_work")

# 个人项目使用个人账户
personal_provider = manager.get_provider("openai_personal")
```

### 场景 2: 多环境配置

```yaml
default_provider_id: openai_prod

providers:
  - provider_id: openai_dev
    provider_type: openai
    display_name: "开发环境 OpenAI"
    api_key_env: OPENAI_DEV_KEY
    default_model: gpt-3.5-turbo
    enabled: true
    metadata:
      environment: "development"

  - provider_id: openai_staging
    provider_type: openai
    display_name: "测试环境 OpenAI"
    api_key_env: OPENAI_STAGING_KEY
    default_model: gpt-4
    enabled: true
    metadata:
      environment: "staging"

  - provider_id: openai_prod
    provider_type: openai
    display_name: "生产环境 OpenAI"
    api_key_env: OPENAI_PROD_KEY
    default_model: gpt-4-turbo
    enabled: true
    metadata:
      environment: "production"
```

### 场景 3: 多个 LLM 提供商

```yaml
default_provider_id: claude_main

providers:
  - provider_id: claude_main
    provider_type: anthropic
    display_name: "主 Claude 账户"
    api_key_env: ANTHROPIC_API_KEY
    default_model: claude-3-5-sonnet-20241022
    enabled: true
    metadata:
      preferred: true
      reason: "最佳性能"

  - provider_id: openai_backup
    provider_type: openai
    display_name: "备用 OpenAI"
    api_key_env: OPENAI_API_KEY
    default_model: gpt-4
    enabled: true
    metadata:
      fallback: true

  - provider_id: gemini_experimental
    provider_type: gemini
    display_name: "实验性 Gemini"
    api_key_env: GEMINI_API_KEY
    default_model: gemini-pro
    enabled: false  # 仅在实验时启用
    metadata:
      experimental: true
```

### 场景 4: 自定义 OpenAI 兼容服务

```yaml
providers:
  - provider_id: local_llm
    provider_type: openai
    display_name: "本地 LLM 服务"
    api_key_env: LOCAL_LLM_KEY  # 可以是任何值
    base_url: "http://localhost:8000/v1"
    default_model: "local-model"
    enabled: true
    metadata:
      type: "self-hosted"
      location: "local"
```

## API 参考

### 加载配置

```python
from core.llm import LLMConfigLoader, load_llm_config

# 从默认位置加载
config = load_llm_config()

# 从指定文件加载
config = LLMConfigLoader.load_from_file("path/to/config.yaml")

# 加载并初始化提供商
from core.llm import initialize_providers_from_yaml
count = initialize_providers_from_yaml()  # 返回初始化的提供商数量
```

### 使用提供商

```python
from core.llm import get_global_manager

manager = get_global_manager()

# 获取特定提供商
provider = manager.get_provider("openai_personal")

# 获取默认提供商
default = manager.get_provider()

# 列出所有提供商
providers = manager.list_providers()

# 设置默认提供商
manager.set_default_provider("claude_main")
```

### 获取显示名称

```python
from core.llm import get_provider_display_names

# 获取所有显示名称映射
names = get_provider_display_names()
# {"openai_personal": "个人 OpenAI 账户", ...}

# 使用
for provider_id, display_name in names.items():
    print(f"{display_name}: {provider_id}")
```

### 创建和保存配置

```python
from core.llm import LLMProvidersConfig, ProviderConfig, LLMConfigLoader

# 创建配置
config = LLMProvidersConfig(
    default_provider_id="openai_main",
    providers=[
        ProviderConfig(
            provider_id="openai_main",
            provider_type="openai",
            display_name="主 OpenAI 账户",
            api_key_env="OPENAI_API_KEY",
            default_model="gpt-4",
            enabled=True
        )
    ]
)

# 保存到文件
LLMConfigLoader.save_to_file(config, "llm_providers.yaml")
```

## 安全最佳实践

### ✅ 正确做法

1. **在配置文件中存储环境变量名称**
   ```yaml
   api_key_env: OPENAI_API_KEY  # ✅ 这是明文的环境变量名
   ```

2. **在环境变量或 .env 文件中存储 API 密钥**
   ```bash
   export OPENAI_API_KEY="sk-proj-..."  # ✅ 密钥在环境中
   ```

3. **将 .env 添加到 .gitignore**
   ```gitignore
   .env
   .env.local
   *.key
   ```

4. **配置文件可以提交到版本控制**
   ```bash
   git add llm_providers.yaml  # ✅ 安全，不含密钥
   ```

### ❌ 错误做法

1. **❌ 在配置文件中存储 API 密钥**
   ```yaml
   api_key: "sk-proj-..."  # ❌ 危险！不要这样做！
   ```

2. **❌ 将 .env 文件提交到 Git**
   ```bash
   git add .env  # ❌ 危险！
   ```

## 故障排除

### 问题：提供商未初始化

**症状**: `initialize_providers_from_yaml()` 返回 0

**可能原因**:

1. 配置文件未找到
   ```bash
   # 检查文件是否存在
   ls -la llm_providers.yaml
   ```

2. API 密钥环境变量未设置
   ```bash
   # 检查环境变量
   echo $OPENAI_API_KEY
   ```

3. 提供商被禁用
   ```yaml
   enabled: false  # 检查此设置
   ```

**解决方案**:
- 确保配置文件在正确的位置
- 设置所需的环境变量
- 检查 `enabled` 字段

### 问题：找不到提供商

**症状**: `Provider 'xxx' not found`

**原因**: `provider_id` 不匹配

**解决方案**:
```python
# 列出所有提供商 ID
manager = get_global_manager()
providers = manager.list_providers()
for p in providers:
    print(p['name'])  # 使用这些名称
```

### 问题：API 密钥无效

**症状**: 认证错误或 API 调用失败

**解决方案**:
1. 检查环境变量是否正确设置
2. 确认 API 密钥有效且未过期
3. 验证环境变量名称拼写正确

```python
import os
# 检查 API 密钥
key = os.getenv("OPENAI_API_KEY")
print(f"API Key: {key[:10]}..." if key else "Not set")
```

## 迁移指南

### 从旧配置迁移

如果您之前使用 `initialize_providers_from_config()`:

**旧方式**:
```python
initialize_providers_from_config({
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
    "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
})
```

**新方式**:

1. 创建 `llm_providers.yaml`:
   ```yaml
   default_provider_id: openai
   providers:
     - provider_id: openai
       provider_type: openai
       display_name: "OpenAI"
       api_key_env: OPENAI_API_KEY
       enabled: true

     - provider_id: anthropic
       provider_type: anthropic
       display_name: "Claude"
       api_key_env: ANTHROPIC_API_KEY
       enabled: true
   ```

2. 更新代码:
   ```python
   initialize_providers_from_yaml()
   ```

**优势**:
- 配置与代码分离
- 支持自定义名称
- 更容易管理多个提供商
- 配置可重用

## 示例

完整的示例代码请参考：
- `backend/examples/multi_provider_demo.py` - 完整演示
- `llm_providers.yaml.example` - 配置示例

运行演示：
```bash
cd backend
python examples/multi_provider_demo.py
```

## 相关文档

- [LLM 集成文档](./LLM_INTEGRATION.md)
- [LLM 2025 模型文档](./LLM_MODELS_2025.md)
- [推理系统文档](./REASONING_SYSTEM.md)
