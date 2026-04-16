# AI Agent Collaboration Platform

北京银行消费金融公司 — 大模型服务平台，提供多 AI Agent 协作、对话、技能管理与制品生成。

## Quick Start

```bash
cd frontend
npm install
npm run dev          # starts Express + Vite on http://localhost:3000
npm run build        # production Vite build
npm run preview      # serve production build
```

`GEMINI_API_KEY` required in `.env` for AI chat to work.

## Architecture

- **Monorepo-style**: Express backend (`server.ts`) and React frontend (`src/`) in the same repo.
- **No external state management**: All state is local React `useState` + server-side in-memory arrays.
- **API calls**: `fetch()` made directly in components — no API client abstraction layer.
- **Demo data**: All users/skills/agents are hard-coded in `server.ts`. Login always authenticates as `wang20110277@gmail.com` (SUPER_ADMIN). Conversations and artifacts are ephemeral.

## Routing

| Route | Component | Guard |
|---|---|---|
| `/` | Chat | Auth required |
| `/chat/:conversationId` | Chat | Auth required |
| `/artifacts` | Artifacts | Auth required |
| `/admin` | Admin | SUPER_ADMIN only |

## Key Files

| File | Purpose |
|---|---|
| `src/App.tsx` | Root component — auth check, routing, initial load |
| `src/main.tsx` | React entry point |
| `src/types.ts` | All TypeScript interfaces (User, Skill, Agent, Message, Conversation, Artifact) |
| `src/i18n.ts` | i18next config with `en`/`zh` locales (~45 keys) |
| `src/index.css` | Tailwind v4 + theme CSS variables (`data-theme` on `<html>`) |
| `src/lib/utils.ts` | `cn()` utility (clsx + tailwind-merge) |
| `src/components/Chat.tsx` | Main chat — 3-panel layout, Gemini integration, artifact sidebar |
| `src/components/Sidebar.tsx` | Left sidebar — nav, history, agent list, theme/lang toggles |
| `src/components/Admin.tsx` | Admin panel — Users/Agents/Skills tabs |
| `src/components/Artifacts.tsx` | Artifact grid — filter by type (PPT/AUDIO/SUMMARY) |
| `src/components/Login.tsx` | Branded landing page |
| `src/components/SkillRepositoryModal.tsx` | Admin-only skill picker modal |
| `server.ts` | Express server — auth, CRUD, Gemini AI chat endpoint |
| `vite.config.ts` | Vite + React + Tailwind plugins, path alias `@/*` → `./` |

## Tech Stack

- **Runtime**: Node.js + tsx (TypeScript execution)
- **Frontend**: React 19, React Router 7, Vite 6
- **Styling**: Tailwind CSS 4 (via `@tailwindcss/vite` plugin), CSS custom properties for theming
- **Animation**: `motion/react` (Framer Motion 12) — message entrance, tab indicators, modal backdrop, staggered lists
- **Icons**: `lucide-react`
- **i18n**: `i18next` + `react-i18next` + `i18next-browser-languagedetector` (fallback: `zh`)
- **Backend**: Express 4, `@google/generative-ai` SDK (gemini-2.0-flash default)

## Themes

Two themes via `data-theme` attribute on `<html>`:

- **Aegis AI** (default, blue): accent `#2563EB`, slate tones
- **Nexus AI** (green): accent `#10B981`, emerald tones

Persisted in `localStorage` under key `theme`.

## Role-Based Access Control

- **SUPER_ADMIN**: Sees all agents, accesses `/admin`, manages users, adds skills to agents.
- **REGULAR_USER**: Sees only agents in their `allowedAgentIds` list, no admin access.

## API Endpoints (server.ts)

All endpoints are in-memory, no database.

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/auth/me` | Current user |
| POST | `/api/auth/login` | Login (hard-coded to user 2) |
| POST | `/api/auth/logout` | Logout |
| GET | `/api/agents` | List agents (`?sidebar=true` for sidebar filter) |
| PUT | `/api/agents/:id` | Update agent |
| GET | `/api/skills` | List skills |
| GET | `/api/conversations` | List conversations |
| GET | `/api/conversations/:id` | Get conversation |
| POST | `/api/conversations` | Create conversation |
| PATCH | `/api/conversations/:id` | Update conversation model |
| POST | `/api/chat` | **Core** — send message to Gemini with history + agent context |
| POST | `/api/artifacts/generate` | Create mock artifact (always COMPLETED) |
| GET | `/api/artifacts` | List artifacts |
| GET | `/api/users` | List users (SUPER_ADMIN only) |
| PUT | `/api/users/:id` | Update user (SUPER_ADMIN only) |

## Models Supported

- `gemini-2.0-flash` (default)
- `gemini-1.5-flash`
- `gemini-1.5-pro`

## Type Definitions

```
User { id, username, role: 'SUPER_ADMIN' | 'REGULAR_USER', email, allowedAgentIds? }
Skill { id, name, description, type, status: 'ACTIVE' | 'INACTIVE' }
Agent { id, name, description, status: 'ACTIVE' | 'INACTIVE', skillIds, recommendedModel? }
Message { role: 'user' | 'assistant', content, timestamp }
Conversation { id, userId, agentId?, messages, title, modelId? }
Artifact { id, sessionId, name, type, status: 'PENDING' | 'COMPLETED' | 'FAILED', createdAt, storagePath }
```

## Code Quality Notes

- `Sidebar.tsx`: duplicate `useEffect` for theme setting (lines 35-38 and 51-54).
- `Artifacts.tsx`: inline `Box` SVG component instead of lucide import.
- Minimal error handling — `console.error` in catch blocks only.
- No error boundaries or retry logic on failed API calls.
- No loading skeletons — only `App.tsx` has an initial load spinner.
