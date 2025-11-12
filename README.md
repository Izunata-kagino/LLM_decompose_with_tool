# LLM Decompose Tool

一个强大的 LLM 工具调用和思考可视化系统，支持并行对话和实时展示。

## 项目目标

创建一个接口系统，能够：
- 使用通用 LLM API 持续进行工具调用和思考
- 在 GUI 上实时显示整个过程
- 支持并行线程对话功能

## 特性

- **多 LLM 支持**: 兼容 OpenAI、Anthropic Claude 等多个 LLM 提供商
- **工具系统**: 可扩展的工具注册和执行引擎
- **思考可视化**: 实时展示 LLM 的思考过程和决策链
- **并行对话**: 支持多个会话并行运行
- **实时通信**: 基于 WebSocket 的实时消息推送
- **现代化 UI**: 基于 React + Material-UI 的美观界面

## 技术栈

### 后端
- **框架**: FastAPI
- **语言**: Python 3.11+
- **数据库**: SQLite/PostgreSQL
- **缓存**: Redis (可选)
- **LLM 集成**: OpenAI, Anthropic

### 前端
- **框架**: React 18 + TypeScript
- **构建工具**: Vite
- **UI 库**: Material-UI
- **状态管理**: Zustand
- **可视化**: React Flow

## 快速开始

### 使用 Docker（推荐）

```bash
# 克隆仓库
git clone https://github.com/yourusername/LLM_decompose_with_tool.git
cd LLM_decompose_with_tool

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的 API 密钥

# 启动服务
docker-compose up -d

# 访问应用
# 前端: http://localhost:3000
# 后端: http://localhost:8000
```

### 本地开发

详细的本地开发指南请参考 [README_DEV.md](./README_DEV.md)

## 项目结构

```
├── backend/          # Python FastAPI 后端
├── frontend/         # React TypeScript 前端
├── docs/            # 文档
├── tests/           # 测试
├── PLAN.md          # 详细开发计划
└── README_DEV.md    # 开发文档
```

## 开发计划

详细的开发路线图和里程碑请查看 [PLAN.md](./PLAN.md)

## 文档

- [开发文档](./README_DEV.md)
- [项目计划](./PLAN.md)
- [API 文档](http://localhost:8000/docs) (需要先启动后端)

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License
