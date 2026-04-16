本文档介绍如何在本地开发环境中启动和运行 BobCFC 平台。平台采用前后端分离架构，前端使用 React + Vite 构建开发服务器，后端使用 FastAPI 构建 REST API 服务。

## 前置条件

在开始本地开发前，请确保已安装以下软件：

| 软件 | 版本要求 | 说明 |
|------|----------|------|
| Node.js | ≥18.0.0 | 前端运行时环境 |
| Python | ≥3.10 | 后端运行时环境 |
| Docker Desktop | 最新版本 | 用于启动数据库和缓存服务 |
| Git | 任意版本 | 代码版本管理 |

Sources: [backend/CLAUDE.md](backend/CLAUDE.md#L1-L10), [frontend/CLAUDE.md](frontend/CLAUDE.md#L1-L8)

## 环境架构概览

本地开发模式涉及多个服务的协调工作。以下流程图展示了从启动到完整运行的完整链路：

```mermaid
flowchart TB
    subgraph Infrastructure["基础设施服务 (Docker)"]
        PG[PostgreSQL<br/>端口: 5432]
        RD[Redis<br/>端口: 6379]
        MINIO[MinIO<br/>端口: 9000/9001]
        RMQ[RocketMQ<br/>端口: 9876]
    end
    
    subgraph Backend["后端服务 (Python/FastAPI)"]
        API[FastAPI 应用<br/>端口: 8000]
        WORKER[Worker 进程]
    end
    
    subgraph Frontend["前端服务 (Node.js/Express)"]
        DEV_SERVER[Express + Vite<br/>端口: 3000]
        REACT[React 应用]
    end
    
    USER[开发者浏览器]
    
    USER -->|HTTP :3000| DEV_SERVER
    DEV_SERVER -->|代理 /api/*| API
    API --> PG
    API --> RD
    API --> MINIO
    API --> RMQ
    
    style USER fill:#e1f5fe
    style DEV_SERVER fill:#fff3e0
    style API fill:#e8f5e9
```

## 基础设施服务启动

本地开发需要依赖 PostgreSQL、Redis、MinIO 和 RocketMQ 服务。这些服务通过 Docker Compose 管理。

### 启动命令

```bash
cd backend
docker compose up -d postgres redis minio
```

执行此命令后，Docker 将自动拉取并启动以下容器：

| 服务 | 镜像 | 本地端口 | 数据卷 |
|------|------|----------|--------|
| PostgreSQL | postgres:16-alpine | 5432 | pgdata |
| Redis | redis:7-alpine | 6379 | redisdata |
| MinIO | minio/minio | 9000/9001 | miniodata |
| RocketMQ | apache/rocketmq:5.3.1 | 9876/10911 | - |

Sources: [backend/docker-compose.yml](backend/docker-compose.yml#L1-L50)

### 验证服务状态

等待所有服务健康检查通过后，可通过以下命令验证：

```bash
docker compose ps
```

确保 postgres、redis 和 minio 的状态为 `healthy`。

## 后端环境配置

### 创建环境变量文件

从示例文件复制并创建 `.env` 文件：

```bash
cd backend
cp .env.example .env
```

### 关键配置项

以下配置项需要在 `.env` 文件中进行设置：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `DATABASE_URL` | postgresql+asyncpg://bobcfc:bobcfc_secret@localhost:5432/bobcfc | 数据库连接字符串 |
| `REDIS_URL` | redis://localhost:6379/0 | Redis 连接地址 |
| `MINIO_ENDPOINT` | localhost:9000 | MinIO 服务地址 |
| `MINIO_ACCESS_KEY` | minioadmin | MinIO 用户名 |
| `MINIO_SECRET_KEY` | minioadmin | MinIO 密码 |
| `GEMINI_API_KEY` | - | **必填**，Google Gemini API 密钥 |
| `OIDC_PROVIDER` | (空) | 空值表示演示模式，设为 `entra` 或 `adfs` 启用 OIDC 认证 |

Sources: [backend/.env.example](backend/.env.example#L1-L53)

### 演示模式说明

在本地开发环境中，建议保持 `OIDC_PROVIDER` 为空（演示模式）。此模式下：
- 无需配置 Microsoft Entra ID 或 ADFS
- 登录时自动以管理员身份认证
- 适合功能开发和界面调试

Sources: [backend/CLAUDE.md](backend/CLAUDE.md#L12-L14)

## 后端服务启动

### 数据库迁移

首次启动或数据库结构变更后，需要执行数据库迁移：

```bash
cd backend
alembic upgrade head
```

此命令会根据 `alembic/versions/` 目录下的迁移脚本创建或更新数据库表结构。

Sources: [backend/CLAUDE.md](backend/CLAUDE.md#L8)

### 启动 FastAPI 开发服务器

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

启动参数说明：
- `--reload`：启用热重载，代码变更后自动重启服务
- `--port 8000`：指定服务监听端口

服务启动后将显示以下日志：

```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

Sources: [backend/CLAUDE.md](backend/CLAUDE.md#L8)

### 启动后台 Worker（可选）

如需处理异步消息队列任务，可启动 Worker 进程：

```bash
cd backend
docker compose --profile workers up -d workers
```

Sources: [backend/docker-compose.yml](backend/docker-compose.yml#L65-L77)

## 前端环境配置

### 安装依赖

```bash
cd frontend
npm install
```

### 创建环境变量文件

```bash
cd frontend
cp .env.example .env
```

编辑 `.env` 文件，配置必需的环境变量：

```bash
# 必填：Google Gemini API 密钥
GEMINI_API_KEY="your-gemini-api-key-here"
```

Sources: [frontend/.env.example](frontend/.env.example#L1-L10)

### 获取 Gemini API 密钥

1. 访问 [Google AI Studio](https://aistudio.google.com/)
2. 登录 Google 账号
3. 在 "Get API key" 页面创建新的 API 密钥
4. 将密钥复制到 `.env` 文件的 `GEMINI_API_KEY` 配置项

## 前端服务启动

### 启动开发服务器

```bash
cd frontend
npm run dev
```

此命令会启动 Express 服务器，并同时运行 Vite 开发服务器：
- Express 监听端口：**3000**
- Vite 处理前端资源热更新

Sources: [frontend/CLAUDE.md](frontend/CLAUDE.md#L5-L6)

### API 代理配置

前端开发服务器配置了自动代理，将 `/api/*` 请求转发到后端服务：

```typescript
// vite.config.ts
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
},
```

这意味着前端代码中可以直接使用相对路径：

```typescript
// 无需写成 http://localhost:8000/api/agents
const response = await fetch('/api/agents');
```

Sources: [frontend/vite.config.ts](frontend/vite.config.ts#L19-L24)

### 访问应用

打开浏览器访问 `http://localhost:3000`，进入登录页面。演示模式下，点击登录按钮将自动以管理员身份登录。

## 完整启动流程

以下流程图展示了从零开始启动本地开发环境的完整步骤：

```mermaid
flowchart TD
    A[开始] --> B[启动 Docker 服务]
    B --> C{backend/docker-compose.yml 存在?}
    C -->|是| D[cd backend]
    C -->|否| E[克隆代码仓库]
    E --> D
    D --> F[docker compose up -d postgres redis minio]
    F --> G[创建并配置 backend/.env]
    G --> H[alembic upgrade head]
    H --> I[uvicorn app.main:app --reload --port 8000]
    I --> J[新终端窗口]
    J --> K[cd frontend]
    K --> L[cp .env.example .env]
    L --> M[配置 GEMINI_API_KEY]
    M --> N[npm install]
    N --> O[npm run dev]
    O --> P[访问 http://localhost:3000]
    P --> Q[完成]
    
    style A fill:#e1f5fe
    style Q fill:#c8e6c9
    style P fill:#fff3e0
```

## 前端独立运行模式

前端内置了演示模式，可以在后端服务不可用时独立运行。在此模式下：

- 所有 API 请求使用内存存储
- 预置了演示用户、Agent 和技能数据
- 登录用户固定为 `wang20110277@gmail.com`（SUPER_ADMIN 角色）

Sources: [frontend/CLAUDE.md](frontend/CLAUDE.md#L10-L12)

### 使用演示模式

当后端服务未启动时，Express 服务器会自动使用内置的演示路由处理请求：

```typescript
// server.ts 中的演示模式路由
app.get('/api/auth/me', (req, res) => {
  res.json(currentUser);
});

app.post('/api/auth/login', (req, res) => {
  currentUser = users[1] as User;  // 固定用户
  res.json({ status: 'ok' });
});
```

Sources: [frontend/server.ts](frontend/server.ts#L72-L82)

## 常见问题排查

### 数据库连接失败

**症状**：后端启动时报错 `Connection refused`

**解决方案**：
1. 确认 Docker 容器正在运行：`docker ps`
2. 检查 PostgreSQL 端口是否被占用：`lsof -i :5432`
3. 验证连接字符串配置是否正确

### 前端无法调用 API

**症状**：浏览器控制台显示 `Failed to fetch` 或 `Network Error`

**解决方案**：
1. 确认后端服务正在运行（`http://localhost:8000/health`）
2. 检查 Vite 代理配置是否正确
3. 确认 CORS 配置包含前端地址

Sources: [backend/app/main.py](backend/app/main.py#L30-L35)

### Gemini API 调用失败

**症状**：聊天功能报错 `Invalid API key`

**解决方案**：
1. 确认 `GEMINI_API_KEY` 已正确配置在前端 `.env` 文件
2. 检查 API 密钥是否有效（访问 Google AI Studio 验证）
3. 确认网络可以访问 Google API 服务

### 热重载不生效

**症状**：修改代码后页面未自动更新

**解决方案**：
1. 检查终端中 uvicorn 是否显示 `INFO:     Detected change in 'xxx.py', reloading`
2. 清除浏览器缓存后硬刷新（Cmd+Shift+R）
3. 重启开发服务器

## 环境清理

### 停止所有服务

```bash
# 停止后端容器
cd backend
docker compose down

# 停止前端开发服务器
# 在前端终端按 Ctrl+C
```

### 清除数据（重置环境）

```bash
# 删除 Docker 数据卷（清除所有数据）
docker compose down -v

# 重新初始化数据库
alembic upgrade head
```

## 后续步骤

完成本地开发环境配置后，建议阅读以下文档：

| 文档 | 说明 |
|------|------|
| [环境配置](3-hou-duan-huan-jing-bian-liang-pei-zhi) | 深入了解后端所有配置项 |
| [前端环境变量配置](4-qian-duan-huan-jing-bian-liang-pei-zhi) | 深入了解前端环境变量 |
| [整体架构概览](7-zheng-ti-jia-gou-gai-lan) | 了解平台整体架构设计 |
| [Docker Compose 部署](6-docker-compose-bu-shu) | 学习生产环境部署方式 |