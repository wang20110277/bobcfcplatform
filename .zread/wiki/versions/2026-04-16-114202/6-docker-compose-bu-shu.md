本文档详细说明如何使用 Docker Compose 在生产或预发布环境中部署 BOB-CFC 平台。该部署方案基于容器化架构，包含后端服务、消息队列消费者、关系型数据库、缓存服务、对象存储和消息中间件等核心组件。

## 架构概览

BOB-CFC 平台采用微服务架构风格，通过 Docker Compose 实现服务的编排与部署。系统由七个核心服务组成，分为数据层、服务层和计算层三个层级。

```mermaid
graph TB
    subgraph DataLayer["数据层"]
        Postgres[(PostgreSQL<br/>数据库)]
        Redis[(Redis<br/>缓存)]
        MinIO[(MinIO<br/>对象存储)]
    end
    
    subgraph MessageLayer["消息层"]
        RMQNamesrv[RocketMQ<br/>NameServer]
        RMQBroker[RocketMQ<br/>Broker]
    end
    
    subgraph ServiceLayer["服务层"]
        Backend[FastAPI<br/>后端服务]
        Workers[消息消费者<br/>Workers]
    end
    
    Backend --> Postgres
    Backend --> Redis
    Backend --> MinIO
    Backend --> RMQBroker
    
    Workers --> Postgres
    Workers --> Redis
    Workers --> RMQBroker
    Workers --> MinIO
    
    RMQBroker --> RMQNamesrv
```

**数据流说明**：后端服务处理前端请求并与数据库交互，同时将异步任务发送到 RocketMQ 消息队列。Workers 服务订阅消息队列，执行聊天处理和制品生成等计算密集型任务，结果存储至 MinIO 对象存储。

Sources: [docker-compose.yml](backend/docker-compose.yml#L1-L112)

## 服务组件详解

### 服务配置总览

| 服务名称 | 镜像版本 | 端口映射 | 健康检查 | 依赖关系 |
|---------|---------|---------|---------|---------|
| `postgres` | postgres:16-alpine | 5432 | pg_isready | 无 |
| `redis` | redis:7-alpine | 6379 | redis-cli ping | 无 |
| `rocketmq-namesrv` | apache/rocketmq:5.3.1 | 9876 | nc -z localhost 9876 | 无 |
| `rocketmq-broker` | apache/rocketmq:5.3.1 | 10909, 10911, 8081 | nc -z localhost 10911 | rocketmq-namesrv |
| `minio` | minio/minio:latest | 9000, 9001 | 无 | 无 |
| `backend` | 本地构建 | 8000 | 无 | postgres, redis, minio |
| `workers` | 本地构建 | - | 无 | postgres, redis, rocketmq-broker, minio |

Sources: [docker-compose.yml](backend/docker-compose.yml#L4-L106)

### 数据库服务 (PostgreSQL)

PostgreSQL 16 Alpine 版本提供轻量级关系型数据库支持。容器配置包含预置数据库和用户初始化，挂载持久化卷确保数据安全。

```yaml
postgres:
  image: postgres:16-alpine
  environment:
    POSTGRES_DB: bobcfc
    POSTGRES_USER: bobcfc
    POSTGRES_PASSWORD: bobcfc_secret
  ports:
    - "5432:5432"
  volumes:
    - pgdata:/var/lib/postgresql/data
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U bobcfc"]
    interval: 5s
    retries: 5
```

健康检查机制通过 `pg_isready` 命令验证数据库可用性，确保依赖服务在启动前完成初始化。

Sources: [docker-compose.yml](backend/docker-compose.yml#L4-L18)

### 缓存服务 (Redis)

Redis 7 Alpine 版本提供高性能键值缓存，支持会话存储和消息队列持久化。容器配置启用持久化存储。

```yaml
redis:
  image: redis:7-alpine
  ports:
    - "6379:6379"
  volumes:
    - redisdata:/data
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 5s
    retries: 5
```

Sources: [docker-compose.yml](backend/docker-compose.yml#L19-L28)

### 消息中间件 (RocketMQ)

RocketMQ 5.3.1 版本提供企业级消息服务，包含 NameServer 和 Broker 两个组件，采用分离部署模式提升可靠性。

**NameServer 配置**：

```yaml
rocketmq-namesrv:
  image: apache/rocketmq:5.3.1
  command: sh mqnamesrv
  ports:
    - "9876:9876"
  environment:
    JAVA_OPT_EXT: "-Xms256m -Xmx256m"
```

**Broker 配置**：

```yaml
rocketmq-broker:
  image: apache/rocketmq:5.3.1
  command: sh mqbroker -n rocketmq-namesrv:9876 --enable-proxy
  ports:
    - "10909:10909"
    - "10911:10911"
    - "8081:8081"
  environment:
    NAMESRV_ADDR: rocketmq-namesrv:9876
    JAVA_OPT_EXT: "-Xms256m -Xmx512m"
```

Broker 启用 Proxy 模式简化客户端连接，配置 `--enable-proxy` 参数即可支持 gRPC 协议。

Sources: [docker-compose.yml](backend/docker-compose.yml#L30-L60)

### 对象存储 (MinIO)

MinIO 提供 S3 兼容的对象存储服务，用于存储生成的制品文件。控制台独立端口 9001 提供可视化界面。

```yaml
minio:
  image: minio/minio:latest
  command: server /data --console-address ":9001"
  ports:
    - "9000:9000"
    - "9001:9001"
  environment:
    MINIO_ROOT_USER: minioadmin
    MINIO_ROOT_PASSWORD: minioadmin
  volumes:
    - miniodata:/data
```

**默认凭证**：`minioadmin` / `minioadmin`，生产环境务必修改。

Sources: [docker-compose.yml](backend/docker-compose.yml#L62-L73)

### 后端服务 (Backend)

FastAPI 后端服务基于 Python 3.12 构建，提供 RESTful API 和 WebSocket 通信支持。

```yaml
backend:
  build: .
  ports:
    - "8000:8000"
  env_file: .env
  depends_on:
    postgres:
      condition: service_healthy
    redis:
      condition: service_healthy
    minio:
      condition: service_started
  command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
  volumes:
    - .:/app
```

**启动时序控制**：通过 `depends_on` 和 `condition` 参数确保数据库和缓存服务就绪后再启动后端。

Sources: [docker-compose.yml](backend/docker-compose.yml#L74-L88)

### 消息消费者 (Workers)

Workers 服务独立运行 RocketMQ 消费者，处理聊天消息和制品生成任务。

```yaml
workers:
  build: .
  env_file: .env
  depends_on:
    postgres:
      condition: service_healthy
    redis:
      condition: service_healthy
    rocketmq-broker:
      condition: service_healthy
    minio:
      condition: service_started
  command: python scripts/run_workers.py
  volumes:
    - .:/app
  profiles:
    - workers
```

**Profile 机制**：Workers 服务使用 `profiles: [workers]` 配置，仅在显式激活时启动，避免资源占用。

Sources: [docker-compose.yml](backend/docker-compose.yml#L90-L106), [run_workers.py](backend/scripts/run_workers.py#L1-L50)

## 部署前准备

### 环境要求

| 组件 | 最低要求 | 推荐配置 |
|-----|---------|---------|
| Docker | 20.10+ | 24.0+ |
| Docker Compose | 2.0+ | 2.20+ |
| 内存 | 4GB | 8GB |
| 磁盘 | 20GB | 50GB SSD |

### 配置文件创建

从示例文件复制并配置环境变量：

```bash
cd backend
cp .env.example .env
```

**关键配置项说明**：

| 配置项 | 说明 | 示例值 |
|-------|------|-------|
| `DATABASE_URL` | PostgreSQL 连接字符串 | `postgresql+asyncpg://bobcfc:bobcfc_secret@postgres:5432/bobcfc` |
| `REDIS_URL` | Redis 连接地址 | `redis://redis:6379/0` |
| `ROCKETMQ_NAMESRV` | RocketMQ NameServer 地址 | `rocketmq-namesrv:9876` |
| `MINIO_ENDPOINT` | MinIO 服务地址 | `minio:9000` |
| `JWT_SECRET` | JWT 签名密钥 | 生产环境使用随机字符串 |
| `OIDC_PROVIDER` | OIDC 提供商 | `entra` / `adfs` / 空 |

Sources: [.env.example](backend/.env.example#L1-L53)

### 端口占用检查

确保以下端口未被占用：

```bash
# 检查端口占用
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
lsof -i :9876  # RocketMQ NameServer
lsof -i :10909 # RocketMQ Broker
lsof -i :10911 # RocketMQ Broker
lsof -i :8081  # RocketMQ Proxy
lsof -i :9000  # MinIO API
lsof -i :9001  # MinIO Console
lsof -i :8000  # Backend API
```

## 部署步骤

### 标准部署流程

```mermaid
flowchart TD
    A[1. 检查环境依赖] --> B[2. 创建配置文件]
    B --> C[3. 启动基础服务]
    C --> D{等待健康检查}
    D -->|失败| E[检查日志诊断]
    E --> C
    D -->|成功| F[4. 启动后端服务]
    F --> G{后端就绪?}
    G -->|否| H[查看后端日志]
    H --> F
    G -->|是| I[5. 验证服务状态]
    I --> J[部署完成]
```

### 步骤一：启动基础服务

```bash
# 启动数据库、缓存、消息队列和对象存储
docker-compose up -d postgres redis rocketmq-namesrv rocketmq-broker minio
```

### 步骤二：等待服务就绪

```bash
# 查看服务状态
docker-compose ps

# 查看特定服务日志
docker-compose logs -f postgres
docker-compose logs -f redis
docker-compose logs -f rocketmq-namesrv
```

### 步骤三：初始化数据库

```bash
# 进入后端容器执行数据库迁移
docker-compose exec backend alembic upgrade head
```

### 步骤四：启动后端服务

```bash
# 启动后端服务
docker-compose up -d backend
```

### 步骤五：启动消息消费者（可选）

```bash
# 仅在需要处理异步任务时启动 Workers
docker-compose --profile workers up -d workers
```

## 生产环境配置

### 生产环境 .env 示例

```bash
# 数据库 - 使用外部托管或高可用配置
DATABASE_URL=postgresql+asyncpg://bobcfc:secure_password@pg-primary:5432/bobcfc

# Redis - 使用集群或哨兵模式
REDIS_URL=redis://redis-cluster:6379/0

# RocketMQ - 使用多 Broker 配置
ROCKETMQ_NAMESRV=rmq-namesrv-1:9876;rmq-namesrv-2:9876

# MinIO - 使用分布式存储
MINIO_ENDPOINT=minio-cluster:9000

# 安全配置
JWT_SECRET=your-256-bit-secret-key-here
OIDC_PROVIDER=entra
ENTRA_CLIENT_ID=your-azure-client-id
ENTRA_CLIENT_SECRET=your-azure-client-secret
```

### 资源限制配置

建议在生产环境中为各服务添加资源限制：

```yaml
services:
  postgres:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 512M
  
  redis:
    deploy:
      resources:
        limits:
          memory: 1G
  
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

## 运维管理

### 服务监控

```bash
# 查看所有服务状态
docker-compose ps

# 查看资源使用
docker stats

# 查看后端日志
docker-compose logs -f backend

# 查看 Workers 日志
docker-compose logs -f workers
```

### 常见操作

| 操作 | 命令 |
|-----|------|
| 停止所有服务 | `docker-compose down` |
| 重启后端 | `docker-compose restart backend` |
| 进入后端容器 | `docker-compose exec backend bash` |
| 查看服务依赖 | `docker-compose config --services` |
| 重建后端镜像 | `docker-compose build backend` |

### 日志诊断

```bash
# 查看服务启动日志
docker-compose logs backend | tail -100

# 查看错误日志
docker-compose logs backend | grep -i error

# 跟踪实时日志
docker-compose logs -f --tail=50
```

## 故障排除

### 服务启动失败

**症状**：服务容器持续重启或处于 unhealthy 状态。

**诊断步骤**：

```bash
# 1. 检查容器状态
docker-compose ps -a

# 2. 查看详细日志
docker-compose logs <service-name>

# 3. 检查端口占用
netstat -tuln | grep <port>
```

**常见原因及解决方案**：

| 原因 | 解决方案 |
|-----|---------|
| 端口被占用 | 修改 docker-compose.yml 端口映射或停止占用进程 |
| 磁盘空间不足 | 清理 Docker 资源：`docker system prune -a` |
| 内存不足 | 增加 Docker 分配内存或降低服务资源限制 |
| 配置文件错误 | 检查 .env 文件格式和必填项 |

### 数据库连接失败

**症状**：后端服务日志显示 `Connection refused` 或 `could not connect to server`。

**检查项**：

```bash
# 1. 确认 PostgreSQL 容器运行中
docker-compose ps postgres

# 2. 检查数据库健康状态
docker-compose exec postgres pg_isready

# 3. 验证连接信息
docker-compose exec backend env | grep DATABASE
```

### MinIO 访问异常

**症状**：制品上传/下载失败或超时。

**检查项**：

```bash
# 1. 确认 MinIO 服务运行
docker-compose ps minio

# 2. 检查 MinIO 健康状态
curl http://localhost:9000/minio/health/live

# 3. 验证存储桶存在
docker-compose exec minio mc ls local/artifacts
```

Sources: [config.py](backend/app/config.py#L1-L75), [docker-compose.yml](backend/docker-compose.yml#L1-L112)

## 后续步骤

部署完成后，建议阅读以下文档深入了解平台架构和配置：

- [Docker Compose 部署](6-docker-compose-bu-shu)（当前页面）
- [整体架构概览](7-zheng-ti-jia-gou-gai-lan) - 深入理解平台技术架构
- [数据库模型设计](10-shu-ju-ku-mo-xing-she-hi) - 了解数据层设计
- [OIDC 认证流程](18-oidc-ren-zheng-liu-cheng) - 配置企业身份认证