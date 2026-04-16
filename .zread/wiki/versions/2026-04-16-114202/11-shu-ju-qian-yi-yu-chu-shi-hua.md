本页面详细说明 BobCFC 平台的数据库 schema 迁移机制与初始化数据填充流程，涵盖 Alembic 迁移配置、初始数据库模型、数据种子脚本以及双模式（开发/生产）的表创建策略。

## 迁移系统架构

BobCFC 后端采用 **Alembic** 作为数据库版本控制工具，配合 SQLAlchemy ORM 的异步驱动（`asyncpg`）实现 schema 变更管理。迁移系统支持两种运行模式：**离线模式**（生成 SQL 脚本）和**在线模式**（直接执行迁移）。

```mermaid
flowchart TB
    subgraph "Alembic 迁移配置"
        A["alembic.ini<br/>配置连接字符串"] --> B["alembic/env.py<br/>读取配置 + 加载模型"]
        B --> C["alembic/versions/<br/>迁移脚本目录"]
    end
    
    subgraph "迁移执行路径"
        D{"运行模式"} -->|"离线"| E["run_migrations_offline()<br/>生成 SQL 脚本"]
        D -->|"在线"| F["run_migrations_online()<br/>异步执行迁移"]
    end
    
    subgraph "数据库"
        G["PostgreSQL 16<br/>bobcfc 数据库"]
    end
    
    E --> G
    F --> G
```

Sources: [alembic/env.py](backend/alembic/env.py#L1-L60), [alembic.ini](backend/alembic.ini#L1-L38)

### 核心配置文件

`backend/alembic.ini` 定义了 Alembic 的基本配置，包括 SQLAlchemy 数据库 URL 和日志级别。实际的数据库连接字符串通过 `app/config.py` 中的 `get_settings()` 动态读取环境变量 `DATABASE_URL`，而非硬编码在 `alembic.ini` 中。

Sources: [app/config.py](backend/app/config.py#L1-L75)

```python
# alembic.ini (第 3-4 行)
[alembic]
sqlalchemy.url = postgresql+asyncpg://bobcfc:bobcfc_secret@localhost:5432/bobcfc
```

`env.py` 中的 `run_migrations_online()` 函数使用 `create_async_engine` 创建异步引擎连接，配合 `asyncio.run()` 在异步上下文中执行同步迁移函数 `run_migrations()`。

Sources: [alembic/env.py](backend/alembic/env.py#L40-L60)

## 初始迁移脚本

初始迁移文件 `001_initial.py` 创建了平台的全部 9 张核心数据表，包括用户系统、智能体、技能、会话和制品等业务表，以及多对多关联表。

Sources: [alembic/versions/001_initial.py](backend/alembic/versions/001_initial.py#L1-L133)

### 数据库模型关系图

```mermaid
erDiagram
    USERS ||--o{ CONVERSATIONS : "拥有"
    USERS ||--o{ OAUTH_SESSIONS : "持有"
    USERS ||--o{ USER_ALLOWED_AGENTS : "可访问"
    AGENTS ||--o{ AGENT_SKILLS : "拥有"
    SKILLS ||--o{ AGENT_SKILLS : "被关联"
    CONVERSATIONS ||--o{ MESSAGES : "包含"
    CONVERSATIONS }o--|| AGENTS : "选择"
    ARTIFACTS ||--o| CONVERSATIONS : "关联"

    USERS {
        string id PK
        string username UK
        string email UK
        string role "SUPER_ADMIN|REGULAR_USER"
    }
    SKILLS {
        string id PK
        string name
        string type
        string status "ACTIVE|INACTIVE"
    }
    AGENTS {
        string id PK
        string name
        string status "ACTIVE|INACTIVE"
        string recommended_model
    }
    AGENT_SKILLS {
        string agent_id FK
        string skill_id FK
    }
    USER_ALLOWED_AGENTS {
        string user_id FK
        string agent_id
    }
    CONVERSATIONS {
        string id PK
        string user_id FK
        string agent_id FK
        string title
    }
    MESSAGES {
        string id PK
        string conversation_id FK
        string role "user|assistant"
        text content
    }
    ARTIFACTS {
        string id PK
        string session_id
        string status "PENDING|COMPLETED|FAILED"
        string storage_path
    }
    OAUTH_SESSIONS {
        string id PK
        string user_id FK
        string provider
    }
```

### 表结构概览

| 表名 | 主键类型 | 关联关系 | 关键约束 |
|------|---------|---------|---------|
| `users` | UUID(36) | 1:多→conversations | role CHECK: SUPER_ADMIN/REGULAR_USER |
| `oauth_sessions` | UUID(36) | 多:1→users | user_id FK ON DELETE CASCADE |
| `skills` | String(50) | 多:多↔agents | status CHECK: ACTIVE/INACTIVE |
| `agents` | String(50) | 多:多↔skills | status CHECK: ACTIVE/INACTIVE |
| `agent_skills` | 复合主键 | 多:1→agents, skills | ON DELETE CASCADE |
| `user_allowed_agents` | 复合主键 | 多:1→users | ON DELETE CASCADE |
| `conversations` | UUID(36) | 多:1→users, agents | - |
| `messages` | UUID(36) | 多:1→conversations | role CHECK: user/assistant |
| `artifacts` | UUID(36) | - | status CHECK: PENDING/COMPLETED/FAILED |

Sources: [alembic/versions/001_initial.py](backend/alembic/versions/001_initial.py#L1-L133)

## 模型基类设计

平台定义了统一的 `Base` 基类和 `TimestampMixin` 混合类，所有业务模型继承自这两个组件，确保 ID 生成策略和时间戳字段的一致性。

Sources: [app/models/base.py](backend/app/models/base.py#L1-L21)

```python
# app/models/base.py
class TimestampMixin:
    id = Column(String(36), default=lambda: str(uuid4()), primary_key=True)
    created_at = Column(DateTime(timezone=True), 
                        default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc),
                        nullable=False)
```

业务模型通过多重继承使用混合类，例如 `User` 模型继承 `Base` 和 `TimestampMixin`：

Sources: [app/models/user.py](backend/app/models/user.py#L1-L21), [app/models/__init__.py](backend/app/models/__init__.py#L1-L11)

```python
class User(Base, TimestampMixin):
    __tablename__ = "users"
    # ... 业务字段
```

## 数据初始化机制

### 双模式表创建策略

平台采用**开发模式自动建表**和**生产模式 Alembic 迁移**的双轨策略，通过 `app/db/session.py` 中的 `init_db()` 函数实现。

Sources: [app/db/session.py](backend/app/db/session.py#L1-L36)

```python
async def init_db():
    """Create tables if they don't exist (for dev; use Alembic in prod)."""
    from app.models.base import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

在 `app/main.py` 的应用生命周期管理中，`init_db()` 在 FastAPI 启动时自动调用：

Sources: [app/main.py](backend/app/main.py#L1-L74)

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    
    # Init database
    await init_db()
    
    # Init Redis
    await init_redis()
    
    # Seed data
    async with async_session() as db:
        await seed_all(db)
    
    yield
    
    # Cleanup
    await close_db()
    await close_redis()
```

### 数据种子脚本

`app/db/seed.py` 实现了完整的数据初始化逻辑，包括最小化种子（管理员用户）和完整种子（智能体、技能及其关联关系）。

Sources: [app/db/seed.py](backend/app/db/seed.py#L1-L87)

#### 最小化种子 (`seed_minimal`)

仅在用户表为空时创建一个 SUPER_ADMIN 用户：

```python
async def seed_minimal(db: AsyncSession):
    # 检查是否已有用户
    result = await db.execute(select(User))
    if result.scalars().first():
        return  # 已有数据则跳过
    
    # 创建 admin 用户
    user = User(
        id=str(uuid.uuid4()),
        username="admin",
        email="wang20110277@gmail.com",
        password_hash=hash_password("admin"),  # bcrypt 加密
        role="SUPER_ADMIN",
    )
    db.add(user)
    await db.commit()
    
    # 将 admin 关联到所有智能体
    for agent_id in ["a1", "a2", "a3", "a4"]:
        stmt = insert(user_allowed_agents).values(
            user_id=user.id, agent_id=agent_id
        )
        try:
            await db.execute(stmt)
        except Exception:
            pass  # 忽略重复插入
```

#### 完整种子 (`seed_all`)

包含完整的智能体、技能及其关联关系：

Sources: [app/db/seed.py](backend/app/db/seed.py#L40-L87)

| 智能体 ID | 名称 | 描述 | 推荐模型 |
|----------|------|------|---------|
| `a1` | Summary Agent | 使用 AI 总结文本 | gemini-2.0-flash |
| `a2` | PPT Agent | 生成 PowerPoint 演示文稿 | gemini-2.0-flash |
| `a3` | Audio Agent | 生成音频内容 | gemini-2.0-flash |
| `a4` | SkillCreator | 构建和优化新 AI 技能 | gemini-2.0-flash |

| 技能 ID | 名称 | 类型 |
|--------|------|------|
| `s1` | Text Summary | TEXT_SUMMARY |
| `s2` | PPT Generation | PPT_GENERATION |
| `s3` | Audio Generation | AUDIO_GENERATION |
| `s4` | Skill Creation | SKILL_CREATION |

智能体-技能映射关系：
- `a1` → `s1` (文本摘要)
- `a2` → `s2` (PPT 生成)
- `a3` → `s3` (音频生成)
- `a4` → `s4` (技能创建)

### 默认管理员凭据

| 用户名 | 密码 | 邮箱 | 角色 |
|-------|------|------|------|
| `admin` | `admin` | wang20110277@gmail.com | SUPER_ADMIN |

> ⚠️ **安全提示**：默认凭据仅用于本地开发环境，生产部署必须修改或删除此账户。

## 迁移命令参考

### 本地开发

```bash
# 启动基础设施（PostgreSQL、Redis、MinIO）
docker compose up -d postgres redis minio

# 运行 Alembic 迁移
alembic upgrade head

# 启动开发服务器（自动建表 + 数据种子）
uvicorn app.main:app --reload --port 8000
```

### 生产部署

```bash
# 使用离线模式生成迁移 SQL 脚本
alembic upgrade head --sql > migrations.sql

# 手动执行迁移脚本（通过 DBA）
psql -U bobcfc -d bobcfc -f migrations.sql
```

### 常用 Alembic 命令

| 命令 | 描述 |
|------|------|
| `alembic revision -m "description"` | 创建新迁移脚本 |
| `alembic upgrade head` | 升级到最新版本 |
| `alembic downgrade -1` | 回退一个版本 |
| `alembic history` | 查看迁移历史 |
| `alembic current` | 查看当前版本 |

## 初始化流程图

```mermaid
sequenceDiagram
    participant App as FastAPI 应用
    participant DB as PostgreSQL
    participant Seed as seed_all()
    
    Note over App: 启动时 lifespan 事件
    
    App->>DB: init_db() 创建表
    DB-->>App: 表创建完成
    
    App->>Seed: seed_all(db)
    
    alt 用户表为空
        Seed->>DB: 创建 admin 用户
        Seed->>DB: 关联 admin 到所有智能体
    end
    
    alt 技能表为空
        Seed->>DB: 插入 4 个技能 (s1-s4)
    end
    
    alt 智能体表为空
        Seed->>DB: 插入 4 个智能体 (a1-a4)
    end
    
    Seed->>DB: 插入智能体-技能关联
    
    DB-->>Seed: 数据插入完成
    Seed-->>App: 种子数据加载完成
    
    Note over App: 应用就绪，处理请求
```

## 环境配置

数据迁移相关的环境变量在 `.env` 文件中配置：

Sources: [app/config.py](backend/app/config.py#L1-L75), [.env.example](backend/.env.example)

| 变量名 | 默认值 | 描述 |
|-------|-------|------|
| `DATABASE_URL` | `postgresql+asyncpg://bobcfc:bobcfc_secret@localhost:5432/bobcfc` | 异步 PostgreSQL 连接字符串 |

## 下一步

完成数据迁移与初始化后，建议继续阅读以下页面：

- [数据库模型设计](10-shu-ju-ku-mo-xing-she-ji) — 深入了解各业务模型的字段定义和业务逻辑
- [后端技术架构](8-hou-duan-ji-zhu-jia-gou) — 了解整体后端技术栈和服务组织
- [API 端点参考](17-api-duan-dian-can-kao) — 查看完整的 REST API 接口文档