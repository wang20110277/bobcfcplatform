# Backend AI Agent Collaboration Platform

FastAPI backend for BobCFC — multi-AI agent collaboration with OIDC authentication, Gemini-powered chat, artifact generation, and MinIO storage.

## Quick Start

```bash
cd backend
pip install -e .
docker compose up -d postgres redis minio     # infrastructure
alembic upgrade head                          # run migrations
uvicorn app.main:app --reload --port 8000     # dev server
```

All services via Docker Compose: `docker compose up -d`

## Architecture

- **FastAPI** with async SQLAlchemy + asyncpg
- **OIDC authentication** (Microsoft Entra ID / ADFS) via Authlib, with demo mode
- **Gemini AI** via LangChain for chat responses and artifact generation
- **RocketMQ** message queue (placeholder — chat/artifacts run synchronously)
- **Redis** caching layer
- **MinIO** object storage for generated artifacts
- **WebSocket** support for real-time chat (`/api/ws/chat`)

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI + uvicorn |
| Database | PostgreSQL 16 + SQLAlchemy (async) + asyncpg + Alembic |
| Auth | Authlib (OIDC), python-jose (JWT), passlib+bcrypt |
| AI | LangChain + langchain-google-genai (Gemini 2.0 flash default) |
| Cache | Redis (hiredis) |
| Queue | RocketMQ 5.3.1 |
| Storage | MinIO |
| Config | pydantic-settings + .env |

## Directory Structure

```
backend/
├── app/
│   ├── main.py                  # FastAPI app entry, CORS, router registration
│   ├── config.py                # Pydantic Settings from .env
│   ├── dependencies.py          # get_current_user, require_admin, get_cache
│   ├── api/
│   │   ├── auth.py              # OIDC login/callback/logout, demo mode
│   │   ├── users.py             # User CRUD (admin only)
│   │   ├── agents.py            # Agent list/update (role-filtered)
│   │   ├── skills.py            # Skill listing (public)
│   │   ├── conversations.py     # Conversation CRUD
│   │   ├── chat.py              # REST chat endpoint
│   │   ├── chat_ws.py           # WebSocket chat endpoint
│   │   └── artifacts.py         # Artifact listing + generation
│   ├── models/
│   │   ├── base.py              # Base + TimestampMixin
│   │   ├── user.py              # User + OAuthSession relationship
│   │   ├── agent.py             # Agent + agent_skills, user_allowed_agents
│   │   ├── skill.py             # Skill
│   │   ├── conversation.py      # Conversation + messages relationship
│   │   ├── message.py           # Message
│   │   ├── artifact.py          # Artifact
│   │   └── oauth_session.py     # OAuthSession (tokens storage)
│   ├── schemas/                 # Pydantic schemas (camelCase aliases)
│   ├── services/
│   │   ├── auth_service.py      # JWT create/decode, bcrypt passwords
│   │   ├── oidc_service.py      # Entra ID + ADFS OAuth2 flow
│   │   ├── claim_mapper.py      # OIDC claim normalization
│   │   ├── chat_service.py      # Gemini chat via LangChain
│   │   ├── artifact_service.py  # Gemini artifact content generation
│   │   ├── cache_service.py     # Redis wrapper
│   │   └── minio_service.py     # MinIO client
│   ├── db/
│   │   ├── session.py           # Async engine, session factory, get_db
│   │   └── seed.py              # Seed data (users, agents, skills)
│   ├── mq/                      # RocketMQ (placeholder)
│   └── websocket/
│       └── manager.py           # WebSocket connection manager
├── alembic/versions/001_initial.py
├── scripts/run_workers.py       # RocketMQ consumer workers
├── Dockerfile
├── docker-compose.yml
└── nginx.conf
```

## Database Models (10 tables)

```
User 1──* Conversation 1──* Message
User *──* Agent (via user_allowed_agents)
Agent *──* Skill (via agent_skills)
User 1──* OAuthSession
```

| Table | Key Fields |
|---|---|
| `users` | id, username, email, password_hash, role (SUPER_ADMIN/REGULAR_USER), provider, provider_user_id, claims_data (JSON) |
| `oauth_sessions` | id, user_id FK, provider, access_token (4000), refresh_token (4000), id_token (8000), expires_at |
| `skills` | id (string key), name, description, type, status (ACTIVE/INACTIVE) |
| `agents` | id (string key), name, description, status, recommended_model |
| `agent_skills` | agent_id FK, skill_id FK (junction) |
| `user_allowed_agents` | user_id FK, agent_id (junction) |
| `conversations` | id, user_id FK, agent_id FK, title, model_id |
| `messages` | id, conversation_id FK, role (user/assistant), content, timestamp |
| `artifacts` | id, session_id, name, type, status (PENDING/COMPLETED/FAILED), storage_path |

Base model: `id` is `String(36)` UUID, `created_at`/`updated_at` auto-managed.

## API Endpoints

### Auth (`/api/auth`)

| Method | Path | Description |
|---|---|---|
| GET | `/api/auth/me` | Current user (with allowedAgentIds). Returns None if unauthenticated. |
| GET | `/api/auth/config` | `{ oidcEnabled, oidcProvider }` |
| GET | `/api/auth/login` | Demo: auto-login as admin. OIDC: redirect to IdP. |
| POST | `/api/auth/login` | Demo: set JWT cookie. OIDC: return `{ authUrl }`. |
| GET | `/api/auth/callback/microsoft` | Entra callback — creates user, sets session_token cookie, redirects to frontend. |
| GET | `/api/auth/callback/adfs` | ADFS callback — same flow as Entra. |
| POST | `/api/auth/logout` | Delete session, clear cookies. OIDC: return `{ logoutUrl }` for federated logout. |

### Users (admin only)

| Method | Path | Description |
|---|---|---|
| GET | `/api/users` | List all users with allowedAgentIds |
| PUT | `/api/users/{id}` | Update role, username, email, allowedAgentIds |

### Agents

| Method | Path | Description |
|---|---|---|
| GET | `/api/agents` | Role-filtered: anonymous→ACTIVE only, regular→ACTIVE+allowed, admin→all (or ACTIVE with `?sidebar=true`) |
| PUT | `/api/agents/{id}` | Admin: update name, description, status, recommendedModel, skillIds |

### Skills

| Method | Path | Description |
|---|---|---|
| GET | `/api/skills` | List all skills (public) |

### Conversations

| Method | Path | Description |
|---|---|---|
| GET | `/api/conversations` | Current user's conversations (empty messages array for performance) |
| GET | `/api/conversations/{id}` | Single conversation with full message history |
| POST | `/api/conversations` | Create. Auto-picks agent's recommendedModel, defaults `gemini-2.0-flash` |
| PATCH | `/api/conversations/{id}` | Update modelId only |

### Chat

| Method | Path | Description |
|---|---|---|
| POST | `/api/chat` | REST chat. Request: `{ message, conversationId }`. Response: `{ content, conversation }` |
| WS | `/api/ws/chat` | WebSocket chat. Send: `{ conversationId, message }`. Receive: `{ content, conversation }` |

### Artifacts

| Method | Path | Description |
|---|---|---|
| GET | `/api/artifacts` | List all artifacts |
| POST | `/api/artifacts/generate` | Generate artifact (PPT/AUDIO/SUMMARY). Creates content via Gemini, uploads to MinIO. |

### Health

| Method | Path | Description |
|---|---|---|
| GET | `/health` | `{ status: "ok" }` |

## Authentication

Three modes via `OIDC_PROVIDER` env var:

### Demo Mode (`OIDC_PROVIDER` empty)
- `POST /api/auth/login` auto-logs in as seeded SUPER_ADMIN, sets `token` cookie (JWT)
- `get_current_user` reads `token` cookie

### OIDC Mode (`OIDC_PROVIDER=entra` or `adfs`)
1. User → `GET /api/auth/login` → 302 redirect to IdP authorize URL
2. IdP authenticates user → callback to `/api/auth/callback/microsoft` (Entra) or `/api/auth/callback/adfs`
3. Backend: verify state → exchange code for tokens → decode ID token (JWKS for Entra, base64 fallback for ADFS) → map claims → create/update user → create OAuthSession → set `session_token` cookie (JWT) → redirect to `FRONTEND_URL`
4. `get_current_user` reads `session_token` cookie or `Authorization: Bearer` header

### Claim Mapping (see `services/claim_mapper.py`)
- **Entra ID**: id=`claims.oid`, email=`claims.email`/`preferred_username`, username=`claims.preferred_username`, roles=`claims.roles`+`claims.groups`
- **ADFS**: id=`claims.sub`/`unique_name`/`upn`, email=UPN/email/emailaddress (with XML namespace fallbacks), username=`claims.unique_name`, roles=`claims.role`+`claims.group`

Role determination: `_determine_role()` in `auth.py` checks mapped roles against admin role mappings from config.

## Session Cookie

| Mode | Cookie Name | Content |
|---|---|---|
| Demo | `token` | JWT (HS256) |
| OIDC | `session_token` | JWT (HS256) |

Both set with `httponly=True, samesite="lax", path="/", max_age=86400` (demo) or `SESSION_MAX_AGE` (OIDC).

## Chat Flow (`services/chat_service.py`)

1. Load conversation + agent + skills from DB
2. Load message history (selectin loaded on Conversation.messages)
3. Build system prompt: `"You are {agent.name}: {agent.description}. Available skills: {skill names}. Respond helpfully and concisely."`
4. Create LangChain message list: SystemMessage + history (user/model pairs) + current HumanMessage
5. Call `ChatGoogleGenerativeAI` (conversation's model_id or agent's recommended_model or `gemini-2.0-flash`)
6. Save user + assistant messages to DB
7. Auto-title conversation on first message: truncate to 30 chars
8. Return `{ content, conversation }`

## Artifact Generation (`services/artifact_service.py`)

- **PPT**: Generate slide outline via Gemini prompt
- **AUDIO**: Generate narration script via Gemini
- **SUMMARY**: Generate summary document via Gemini

Content is generated as bytes, uploaded to MinIO, and the storage_path is saved to the artifact record.

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://bobcfc:bobcfc_secret@localhost:5432/bobcfc` | Async PostgreSQL |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis |
| `ROCKETMQ_NAMESRV` | `localhost:9876` | RocketMQ nameserver |
| `MINIO_ENDPOINT` | `localhost:9000` | MinIO |
| `MINIO_ACCESS_KEY` | `minioadmin` | MinIO key |
| `MINIO_SECRET_KEY` | `minioadmin` | MinIO secret |
| `MINIO_BUCKET` | `artifacts` | MinIO bucket |
| `JWT_SECRET` | `change-me-in-production` | JWT signing key |
| `JWT_EXPIRE_MINUTES` | `1440` | JWT expiry |
| `OIDC_PROVIDER` | `""` | `entra`, `adfs`, or empty (demo) |
| `ENTRA_CLIENT_ID` | `""` | Azure AD client ID |
| `ENTRA_CLIENT_SECRET` | `""` | Azure AD secret |
| `ENTRA_TENANT_ID` | `common` | Azure AD tenant |
| `ENTRA_AUTHORITY` | `https://login.microsoftonline.com` | Azure authority |
| `ENTRA_ROLE_MAPPINGS` | `{}` | JSON: OIDC role → app role |
| `ADFS_CLIENT_ID` | `""` | ADFS client ID |
| `ADFS_CLIENT_SECRET` | `""` | ADFS secret |
| `ADFS_ISSUER` | `""` | ADFS issuer URL |
| `ADFS_AUTHORIZATION_URL` | `""` | ADFS auth URL |
| `ADFS_TOKEN_URL` | `""` | ADFS token URL |
| `ADFS_USERINFO_URL` | `""` | ADFS userinfo URL |
| `ADFS_ROLE_MAPPINGS` | `{}` | JSON: ADFS role → app role |
| `SESSION_MAX_AGE` | `28800` | Session cookie max age (8h) |
| `GEMINI_API_KEY` | `""` | Google Gemini API key |
| `FRONTEND_URL` | `http://localhost:3000` | Frontend URL for OIDC redirects |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | Allowed origins |

## Docker Compose Services

| Service | Image | Ports | Notes |
|---|---|---|---|
| `postgres` | postgres:16-alpine | 5432 | Healthcheck, pgdata volume |
| `redis` | redis:7-alpine | 6379 | Healthcheck, redisdata volume |
| `rocketmq-namesrv` | apache/rocketmq:5.3.1 | 9876 | |
| `rocketmq-broker` | apache/rocketmq:5.3.1 | 10909, 10911, 8081 | |
| `minio` | minio/minio:latest | 9000, 9001 | miniodata volume |
| `backend` | Dockerfile | 8000 | Hot reload with `--reload`, source mounted |
| `workers` | Dockerfile | - | Optional (`--profile workers`), runs RocketMQ consumers |

## Seed Data (`db/seed.py`)

- 3 users: admin (SUPER_ADMIN), wang20110277 (SUPER_ADMIN), regular_user (REGULAR_USER)
- 4 agents: Summary(a1/Text), PPT(a2/Presentation), Audio(a3/Audio), SkillCreator(a4/Coding)
- 4 skills: s1 (Text Summary), s2 (PPT Generation), s3 (Audio Generation), s4 (Skill Creation)
- Agent-skill mappings: a1→[s1], a2→[s1,s2], a3→[s3], a4→[s4]
- Admin user has access to all agents (user_allowed_agents)

## Pydantic Schemas

All schemas use `_to_camel` alias generator (`snake_case` → `camelCase`) for frontend compatibility. Located in `schemas/__init__.py` and `schemas/user.py`.

Key schemas: UserSchema, UserCreate, UserUpdate, AgentSchema, AgentUpdate, SkillSchema, MessageSchema, ConversationSchema, ChatRequest, ChatResponse, ArtifactSchema, ArtifactGenerate.

## Dependencies (`app/dependencies.py`)

- `get_current_user` — Reads `token` or `session_token` cookie, or `Authorization: Bearer` header. Decodes JWT, fetches User from DB. Returns `None` (not 401) for unauthenticated requests.
- `require_admin` — Raises 403 if user is not SUPER_ADMIN.
- `get_cache` — Returns CacheService instance.

## Key Implementation Notes

- `get_current_user` returns `None` for unauthenticated requests, not 401 — endpoints must handle `current_user: User | None` explicitly
- Agent filtering by role happens in the API layer (`agents.py`), not in DB queries
- Conversations list returns empty messages array for performance — full history only on single conversation fetch
- OAuth2 state/nonce stored in-memory (`_oauth_states` dict in `oidc_service.py`) — not persisted across restarts
- bcrypt pinned to `4.0.1` due to passlib incompatibility with 5.x (72-byte limit)
- MinIO bucket auto-created on startup via `ensure_bucket()`
