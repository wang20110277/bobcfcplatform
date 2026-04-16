本文档帮助开发者在本地环境快速启动 BobCFC AI Agent 协作平台。项目采用前后端分离架构，通过 Docker Compose 可在 5 分钟内完成基础设施部署，或选择手动模式进行深度定制开发。

## 系统架构概览

BobCFC 平台是一个基于 FastAPI 和 React 的多 AI Agent 协作系统，支持 Gemini 大语言模型、OIDC 企业认证和制品存储功能。系统采用微服务架构设计，各组件通过 Docker 容器化部署。

```mermaid
flowchart TB
    subgraph Frontend["前端 (React + Vite)"]
        FE[前端应用<br/>localhost:3000]
    end
    
    subgraph Backend["后端 (FastAPI)"]
        API[API 服务<br/>localhost:8000]
        WS[WebSocket<br/>/api/ws/chat]
    end
    
    subgraph Infrastructure["基础设施 (Docker)"]
        PG[(PostgreSQL<br/>:5432)]
        RD[(Redis<br/>:6379)]
        MQ[RocketMQ<br/>:9876, :10911]
        MIN[(MinIO<br/>:9000)]
    end
    
    subgraph External["外部服务"]
        GEMINI[Gemini API]
        OIDC[Microsoft Entra ID<br/>ADFS]
    end
    
    FE <-->|"代理 /api/*"| API
    FE <-->|WebSocket| WS
    API <--> PG
    API <--> RD
    API <--> MQ
    API <--> MIN
    API <--> GEMINI
    API <--> OIDC
    
    style Frontend fill:#e1f5fe
    style Backend fill:#fff3e0
    style Infrastructure fill:#f3e5f5
    style External fill:#ffebee
```

## 前置条件

| 工具 | 版本要求 | 用途 |
|------|----------|------|
| Docker | ≥ 20.10 | 容器化基础设施服务 |
| Docker Compose | ≥ 2.0 | 多容器编排 |
| Node.js | ≥ 18.0 | 前端开发环境 |
| Python | ≥ 3.12 | 后端开发环境 |
| Git | 任意版本 | 代码版本控制 |

Sources: [backend/pyproject.toml](backend/pyproject.toml#L4)

## 快速启动方式

### 方式一：Docker Compose 一键部署（推荐）

这是最快速的启动方式，适用于完整功能体验和演示环境。

```mermaid
flowchart LR
    A[克隆代码] --> B[启动基础设施]
    B --> C[配置环境变量]
    C --> D[运行数据库迁移]
    D --> E[启动后端服务]
    E --> F[安装前端依赖]
    F --> G[启动前端应用]
    G --> H[访问 localhost:3000]
```

**步骤 1：启动基础设施服务**

后端目录中包含完整的 Docker Compose 配置，自动启动 PostgreSQL、Redis、MinIO 和 RocketMQ：

```bash
cd backend
docker compose up -d postgres redis minio
```

Sources: [backend/docker-compose.yml](backend/docker-compose.yml#L3-L32)

**步骤 2：配置环境变量**

复制环境变量模板文件并创建本地配置：

```bash
cd backend
cp .env.example .env
```

关键配置项说明：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `DATABASE_URL` | `postgresql+asyncpg://bobcfc:bobcfc_secret@localhost:5432/bobcfc` | PostgreSQL 连接字符串 |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis 连接地址 |
| `MINIO_ENDPOINT` | `localhost:9000` | MinIO 对象存储端点 |
| `JWT_SECRET` | `change-me-in-production` | JWT 签名密钥（生产环境必须修改） |
| `OIDC_PROVIDER` | 空 | OIDC 提供商，设为 `entra` 或 `adfs` 启用企业认证 |
| `GEMINI_API_KEY` | 空 | Gemini API 密钥（必需） |

Sources: [backend/.env.example](backend/.env.example#L1-L53)

**步骤 3：运行数据库迁移**

使用 Alembic 初始化数据库 schema：

```bash
cd backend
alembic upgrade head
```

Sources: [backend/alembic/versions/001_initial.py](backend/alembic/versions/001_initial.py#L1-L133)

**步骤 4：启动后端服务**

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

后端服务将在 `http://localhost:8000` 启动，访问 `/docs` 可查看 Swagger API 文档。

Sources: [backend/app/main.py](backend/app/main.py#L1-L74)

**步骤 5：启动前端应用**

```bash
cd frontend
npm install
cp .env.example .env.local
# 编辑 .env.local，配置 GEMINI_API_KEY
npm run dev
```

Sources: [frontend/README.md](frontend/README.md#L10-L19)

前端开发服务器会在 `http://localhost:3000` 启动，并自动代理 API 请求到后端。

Sources: [frontend/server.ts](frontend/server.ts#L55-L70)

### 方式二：全 Docker Compose 部署

如果希望后端也通过 Docker 运行，可以使用完整的服务栈：

```bash
cd backend
docker compose up -d
```

此命令将启动所有服务，包括后端 API 服务器。

Sources: [backend/docker-compose.yml](backend/docker-compose.yml#L33-L55)

### 方式三：手动开发模式

适用于需要调试后端代码或进行深度定制的开发者。

**后端设置：**

```bash
cd backend
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -e .

# 启动基础设施
docker compose up -d postgres redis minio

# 运行迁移
alembic upgrade head

# 启动开发服务器
uvicorn app.main:app --reload --port 8000
```

Sources: [backend/CLAUDE.md](backend/CLAUDE.md#L4-L11)

**前端设置：**

```bash
cd frontend
npm install
npm run dev
```

Sources: [frontend/package.json](frontend/package.json#L7-L8)

## 演示模式

平台内置演示模式，无需配置任何第三方服务即可体验完整功能。

**启用条件：** 环境变量 `OIDC_PROVIDER` 为空（默认值）。

在演示模式下，系统会：

- 自动使用预设的演示用户登录
- 跳过 OIDC 认证流程
- 所有 AI Agent 默认可用

Sources: [backend/app/config.py](backend/app/config.py#L28)

访问 `http://localhost:3000` 后，系统会自动以演示管理员身份登录，可立即开始使用聊天和制品生成功能。

Sources: [frontend/server.ts](frontend/server.ts#L87-L90)

## 验证部署

部署完成后，通过以下方式验证系统状态：

| 检查项 | 端点 | 预期响应 |
|--------|------|----------|
| 后端健康检查 | `http://localhost:8000/health` | `{"status":"ok"}` |
| API 文档 | `http://localhost:8000/docs` | Swagger UI |
| 前端应用 | `http://localhost:3000` | React 应用界面 |
| MinIO 控制台 | `http://localhost:9001` | MinIO 管理界面 |

Sources: [backend/app/main.py](backend/app/main.py#L71-L74)

## 项目目录结构

```
bobcfcplatform/
├── backend/                      # FastAPI 后端
│   ├── app/
│   │   ├── main.py              # 应用入口，CORS 配置
│   │   ├── config.py            # Pydantic Settings 配置
│   │   ├── dependencies.py      # 依赖注入（认证、缓存）
│   │   ├── api/                 # API 路由模块
│   │   │   ├── auth.py          # 认证接口
│   │   │   ├── agents.py        # Agent 管理
│   │   │   ├── chat.py          # REST 聊天
│   │   │   ├── chat_ws.py       # WebSocket 聊天
│   │   │   └── artifacts.py     # 制品生成
│   │   ├── models/              # SQLAlchemy 模型
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── services/            # 业务逻辑服务
│   │   │   ├── chat_service.py  # Gemini 聊天服务
│   │   │   ├── cache_service.py # Redis 缓存服务
│   │   │   └── minio_service.py # 对象存储服务
│   │   └── db/
│   │       ├── session.py       # 数据库会话
│   │       └── seed.py          # 初始数据
│   ├── alembic/versions/        # 数据库迁移文件
│   ├── docker-compose.yml       # Docker 编排配置
│   └── pyproject.toml           # Python 依赖
│
└── frontend/                    # React 前端
    ├── src/
    │   ├── main.tsx             # React 入口
    │   ├── App.tsx              # 主应用组件
    │   ├── components/          # UI 组件
    │   ├── types.ts             # TypeScript 类型定义
    │   └── i18n.ts               # 国际化配置
    ├── server.ts                # 开发服务器 + API 代理
    ├── package.json             # Node.js 依赖
    └── vite.config.ts           # Vite 配置
```

Sources: [backend/CLAUDE.md](backend/CLAUDE.md#L15-L50)

## 后续步骤

完成快速启动后，建议继续阅读以下文档深入了解系统：

- [后端环境变量配置](3-hou-duan-huan-jing-bian-liang-pei-zhi) — 详细了解各配置项的作用
- [本地开发模式](5-ben-di-kai-fa-mo-shi) — 掌握开发调试技巧
- [整体架构概览](7-zheng-ti-jia-gou-gai-lan) — 深入理解系统架构设计

如需进行生产环境部署，请参考：

- [Docker Compose 部署](6-docker-compose-bu-shu) — 生产环境容器编排
- [OIDC 认证流程](18-oidc-ren-zheng-liu-cheng) — 配置企业身份认证