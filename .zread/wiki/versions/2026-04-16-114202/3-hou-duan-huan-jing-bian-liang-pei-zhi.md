本文档详细说明 BobCFC 平台后端服务的环境变量配置。环境变量通过 `pydantic-settings` 自动加载，配置文件 `.env` 位于 `backend/` 目录。项目启动时，`config.py` 中的 `Settings` 类会自动读取 `.env` 文件并验证配置值。

Sources: [config.py](backend/app/config.py#L1-L75), [.env.example](backend/.env.example#L1-L48)

## 配置加载机制

后端采用 `pydantic-settings` 实现环境变量管理。`Settings` 类继承 `BaseSettings`，通过 `model_config` 指定从 `.env` 文件加载配置：

```python
model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}
```

所有配置项均定义在 `Settings` 类中，每个字段对应一个环境变量。字段名称采用蛇形命名（snake_case），环境变量使用大写形式，Pydantic 会自动进行名称转换。

Sources: [config.py](backend/app/config.py#L69)

## 环境变量速查表

| 变量名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `DATABASE_URL` | str | `postgresql+asyncpg://bobcfc:bobcfc_secret@localhost:5432/bobcfc` | PostgreSQL 数据库连接字符串 |
| `REDIS_URL` | str | `redis://localhost:6379/0` | Redis 缓存服务连接地址 |
| `ROCKETMQ_NAMESRV` | str | `localhost:9876` | RocketMQ 名称服务器地址 |
| `ROCKETMQ_GROUP` | str | `backend-group` | RocketMQ 消费者组名称 |
| `MINIO_ENDPOINT` | str | `localhost:9000` | MinIO 对象存储服务地址 |
| `MINIO_ACCESS_KEY` | str | `minioadmin` | MinIO 访问密钥 |
| `MINIO_SECRET_KEY` | str | `minioadmin` | MinIO 秘密密钥 |
| `MINIO_BUCKET` | str | `artifacts` | MinIO 存储桶名称 |
| `MINIO_SECURE` | bool | `false` | 是否启用 HTTPS 连接 |
| `JWT_SECRET` | str | `change-me-in-production` | JWT 签名密钥（生产环境必须修改） |
| `JWT_ALGORITHM` | str | `HS256` | JWT 加密算法 |
| `JWT_EXPIRE_MINUTES` | int | `1440` | JWT 令牌过期时间（分钟） |
| `OIDC_PROVIDER` | str | 空 | OIDC 提供商类型：`entra`、`adfs` 或空（演示模式） |
| `ENTRA_CLIENT_ID` | str | 空 | Microsoft Entra ID 客户端 ID |
| `ENTRA_CLIENT_SECRET` | str | 空 | Microsoft Entra ID 客户端密钥 |
| `ENTRA_TENANT_ID` | str | `common` | Azure 租户 ID |
| `ENTRA_AUTHORITY` | str | `https://login.microsoftonline.com` | Entra 授权服务器地址 |
| `ENTRA_ROLE_MAPPINGS` | dict | `{}` | Entra 角色映射配置（JSON 格式） |
| `ADFS_CLIENT_ID` | str | 空 | ADFS 客户端 ID |
| `ADFS_CLIENT_SECRET` | str | 空 | ADFS 客户端密钥 |
| `ADFS_ISSUER` | str | 空 | ADFS 发行者标识 |
| `ADFS_AUTHORIZATION_URL` | str | 空 | ADFS 授权端点 |
| `ADFS_TOKEN_URL` | str | 空 | ADFS 令牌端点 |
| `ADFS_USERINFO_URL` | str | 空 | ADFS 用户信息端点 |
| `ADFS_ROLE_MAPPINGS` | dict | `{}` | ADFS 角色映射配置（JSON 格式） |
| `SESSION_MAX_AGE` | int | `28800` | 会话最大存活时间（秒，默认 8 小时） |
| `GEMINI_API_KEY` | str | 空 | Google Gemini API 密钥 |
| `HOST` | str | `0.0.0.0` | 服务器绑定地址 |
| `PORT` | int | `8000` | 服务器监听端口 |
| `CORS_ORIGINS` | list[str] | `["http://localhost:3000"]` | 允许的 CORS 来源列表 |

Sources: [.env.example](backend/.env.example#L1-L48)

## 数据库配置

### PostgreSQL 连接

`DATABASE_URL` 定义数据库连接字符串，采用异步驱动 `asyncpg`。格式为：

```
postgresql+asyncpg://用户名:密码@主机:端口/数据库名
```

开发环境默认值配置了本地 PostgreSQL 服务，容器环境需根据实际部署修改。

### Redis 缓存

`REDIS_URL` 配置 Redis 连接，支持本地或远程 Redis 实例。默认连接本地 6379 端口的零号数据库。缓存服务用于存储会话数据和加速查询。

Sources: [config.py](backend/app/config.py#L11-L14), [.env.example](backend/.env.example#L1-L6)

## 对象存储配置

项目使用 MinIO 作为对象存储服务，存储生成的制品文件（如 PPT、音频等）。相关配置包括：

| 配置项 | 说明 | 安全建议 |
|--------|------|----------|
| `MINIO_ENDPOINT` | MinIO 服务器地址和端口 | 生产环境使用内网地址 |
| `MINIO_ACCESS_KEY` | 访问密钥 | 生产环境必须修改为复杂密码 |
| `MINIO_SECRET_KEY` | 秘密密钥 | 生产环境必须修改为复杂密码 |
| `MINIO_BUCKET` | 存储桶名称 | 可按环境创建不同桶 |
| `MINIO_SECURE` | 是否使用 HTTPS | 生产环境必须启用 |

Sources: [config.py](backend/app/config.py#L21-L26)

## 消息队列配置

RocketMQ 配置用于异步消息处理，当前为预留实现：

- `ROCKETMQ_NAMESRV`：名称服务器地址
- `ROCKETMQ_GROUP`：消费者组标识

Sources: [config.py](backend/app/config.py#L17-L18), [.env.example](backend/.env.example#L8-L11)

## 认证与授权配置

### JWT 配置

JWT 用于会话令牌签名和验证：

| 配置项 | 说明 | 生产环境要求 |
|--------|------|--------------|
| `JWT_SECRET` | 签名密钥 | 必须修改为至少 32 位的随机字符串 |
| `JWT_ALGORITHM` | 加密算法 | 建议保持 HS256 |
| `JWT_EXPIRE_MINUTES` | 过期时间 | 可根据业务需求调整 |

### OIDC 认证配置

项目支持三种认证模式，通过 `OIDC_PROVIDER` 变量控制：

```mermaid
flowchart LR
    A[OIDC_PROVIDER] --> B{空值}
    A --> C{entra}
    A --> D{adfs}
    B --> E[演示模式]
    C --> F[Microsoft Entra ID]
    D --> G[ADFS]
```

#### 演示模式（默认）

`OIDC_PROVIDER` 为空时，系统运行在演示模式，无需外部认证服务。自动创建超级管理员用户，可直接登录进行功能测试。

#### Microsoft Entra ID 配置

配置企业级 Azure AD 认证：

```bash
OIDC_PROVIDER=entra
ENTRA_CLIENT_ID=你的应用程序客户端ID
ENTRA_CLIENT_SECRET=你的客户端密钥
ENTRA_TENANT_ID=你的租户ID
ENTRA_ROLE_MAPPINGS={"Global Administrator":"admin","User":"user"}
```

#### ADFS 配置

配置本地 Active Directory 联合认证：

```bash
OIDC_PROVIDER=adfs
ADFS_CLIENT_ID=你的客户端ID
ADFS_CLIENT_SECRET=你的客户端密钥
ADFS_ISSUER=发行者标识符
ADFS_AUTHORIZATION_URL=https://你的ADFS服务器/adfs/oauth2/authorize
ADFS_TOKEN_URL=https://你的ADFS服务器/adfs/oauth2/token
ADFS_USERINFO_URL=https://你的ADFS服务器/adfs/userinfo
ADFS_ROLE_MAPPINGS={"CN=Admins,OU=Groups,DC=company,DC=com":"admin"}
```

Sources: [config.py](backend/app/config.py#L29-L55), [CLAUDE.md](backend/CLAUDE.md#L60-L78)

## AI 服务配置

`GEMINI_API_KEY` 用于连接 Google Gemini AI 服务。获取方式：

1. 访问 [Google AI Studio](https://aistudio.google.com/apikey)
2. 创建 API 密钥
3. 将密钥填入环境变量

Sources: [config.py](backend/app/config.py#L59)

## 服务器配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `HOST` | `0.0.0.0` | 监听所有网络接口 |
| `PORT` | `8000` | HTTP 服务端口 |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | 允许跨域请求的前端地址 |
| `FRONTEND_URL` | `http://localhost:3000` | 前端应用地址（用于 OIDC 重定向） |
| `SESSION_MAX_AGE` | `28800` | 会话有效期（秒） |

CORS 配置支持多个来源，格式为 JSON 数组：

```bash
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173","https://your-domain.com"]
```

Sources: [config.py](backend/app/config.py#L62-L68), [main.py](backend/app/main.py#L36-L40)

## 角色映射配置

角色映射（`ENTRA_ROLE_MAPPINGS` 和 `ADFS_ROLE_MAPPINGS`）将外部 IdP 的角色/组映射到系统内部角色。格式为 JSON 对象：

```json
{
  "外部角色名称": "系统角色",
  "Global Administrator": "SUPER_ADMIN",
  "User": "REGULAR_USER"
}
```

配置示例：

```bash
ENTRA_ROLE_MAPPINGS='{"Global Administrator":"SUPER_ADMIN","User":"REGULAR_USER"}'
```

系统在初始化时，如果角色映射字段为字符串，会自动解析为字典对象。

Sources: [config.py](backend/app/config.py#L71-L74)

## 配置验证与依赖获取

项目使用单例模式管理配置，通过 `@lru_cache` 装饰器确保配置只加载一次：

```python
@lru_cache
def get_settings() -> Settings:
    return Settings()
```

在应用任何位置可通过 `get_settings()` 获取配置实例。FastAPI 依赖注入系统也使用此函数获取当前配置。

Sources: [config.py](backend/app/config.py#L76-L78), [main.py](backend/app/main.py#L36), [dependencies.py](backend/app/dependencies.py#L23)

## 环境配置示例

### 本地开发环境

复制 `.env.example` 为 `.env`，保持大部分默认值不变：

```bash
cd backend
cp .env.example .env
```

仅需确保 PostgreSQL、Redis、MinIO 服务在本地运行。

### Docker Compose 部署

使用 `docker-compose.yml` 启动基础服务时，数据库和存储服务的连接信息需与 docker-compose 配置保持一致：

```bash
# docker-compose.yml 中的服务
services:
  postgres:
    environment:
      POSTGRES_DB: bobcfc
      POSTGRES_USER: bobcfc
      POSTGRES_PASSWORD: bobcfc_secret
```

对应的 `DATABASE_URL` 应为：

```bash
DATABASE_URL=postgresql+asyncpg://bobcfc:bobcfc_secret@postgres:5432/bobcfc
```

注意：容器间通信使用服务名 `postgres` 而非 `localhost`。

Sources: [docker-compose.yml](backend/docker-compose.yml#L1-L50)

### 生产环境要点

生产部署时必须修改以下配置：

| 配置项 | 生产要求 |
|--------|----------|
| `DATABASE_URL` | 使用云数据库连接串 |
| `JWT_SECRET` | 使用 `openssl rand -hex 32` 生成随机密钥 |
| `MINIO_ACCESS_KEY` / `MINIO_SECRET_KEY` | 使用云存储凭据 |
| `ENTRA_CLIENT_SECRET` / `ADFS_CLIENT_SECRET` | 使用强密码并安全存储 |
| `GEMINI_API_KEY` | 使用生产环境 API 密钥 |
| `MINIO_SECURE` | 设为 `true` |

## 故障排除

### 配置未生效

1. 确认 `.env` 文件位于 `backend/` 目录
2. 检查环境变量名称是否正确（区分大小写）
3. 重启服务使配置重新加载

### 数据库连接失败

1. 验证 `DATABASE_URL` 格式正确
2. 确认 PostgreSQL 服务正在运行
3. 检查用户名密码是否匹配

### OIDC 认证异常

1. 确认 `OIDC_PROVIDER` 设置正确（`entra` 或 `adfs`）
2. 检查各 OIDC 端点 URL 是否可访问
3. 验证 `ENTRA_ROLE_MAPPINGS` 格式为有效 JSON

---

## 下一步

配置完成后，继续以下步骤：

- **本地开发**：了解 [本地开发模式](5-ben-di-kai-fa-mo-shi) 启动完整开发环境
- **Docker 部署**：参考 [Docker Compose 部署](6-docker-compose-bu-shu) 使用容器化部署
- **前端配置**：配置 [前端环境变量](4-qian-duan-huan-jing-bian-liang-pei-zhi)