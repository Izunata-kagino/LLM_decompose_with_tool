# LLM Decompose Tool - 开发文档

## 项目简介

这是一个支持持续 LLM 工具调用和思考的界面系统，具有并行线程对话功能。

## 技术栈

### 后端
- Python 3.11+
- FastAPI
- SQLite/PostgreSQL
- Redis (可选)
- OpenAI/Anthropic API

### 前端
- React 18
- TypeScript
- Material-UI
- Vite
- Zustand (状态管理)
- React Flow (可视化)

## 快速开始

### 方式一：使用 Docker Compose（推荐）

1. 复制环境变量文件：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，填入你的 API 密钥

3. 启动服务：
```bash
docker-compose up -d
```

4. 访问应用：
- 前端：http://localhost:3000
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

### 方式二：本地开发

#### 后端设置

1. 进入后端目录：
```bash
cd backend
```

2. 创建虚拟环境：
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 复制并配置环境变量：
```bash
cp ../.env.example ../.env
# 编辑 .env 文件
```

5. 运行后端：
```bash
python main.py
```

#### 前端设置

1. 进入前端目录：
```bash
cd frontend
```

2. 安装依赖：
```bash
npm install
```

3. 运行开发服务器：
```bash
npm run dev
```

## 项目结构

```
LLM_decompose_with_tool/
├── backend/                    # 后端代码
│   ├── api/                   # API 路由
│   │   ├── routes/           # REST API 路由
│   │   └── websocket/        # WebSocket 端点
│   ├── core/                 # 核心功能
│   │   ├── llm/              # LLM 集成
│   │   ├── tools/            # 工具系统
│   │   ├── reasoning/        # 思考链
│   │   └── session/          # 会话管理
│   ├── models/               # 数据模型
│   ├── config.py             # 配置
│   ├── main.py               # 入口文件
│   └── requirements.txt      # 依赖
├── frontend/                  # 前端代码
│   ├── src/
│   │   ├── components/       # React 组件
│   │   ├── pages/            # 页面
│   │   ├── services/         # API 服务
│   │   ├── store/            # 状态管理
│   │   └── utils/            # 工具函数
│   ├── package.json
│   └── vite.config.ts
├── docs/                      # 文档
├── tests/                     # 测试
├── .env.example              # 环境变量示例
├── docker-compose.yml        # Docker 配置
├── PLAN.md                   # 开发计划
└── README.md                 # 项目说明
```

## 开发计划

详细的开发计划请参考 [PLAN.md](./PLAN.md)

## API 文档

启动后端后，访问以下地址查看 API 文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 测试

### 后端测试
```bash
cd backend
pytest
```

### 前端测试
```bash
cd frontend
npm test
```

## 代码风格

### Python
使用 Black 和 Flake8：
```bash
cd backend
black .
flake8 .
```

### TypeScript
使用 ESLint：
```bash
cd frontend
npm run lint
```

## 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

MIT License

## 联系方式

如有问题，请提交 Issue。
