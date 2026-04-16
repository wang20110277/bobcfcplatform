from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db.session import init_db, close_db
from app.services.cache_service import init_redis, close_redis
from app.db.seed import seed_all
from app.db.session import async_session


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


settings = get_settings()

app = FastAPI(
    title="BobCFC AI Agent Platform",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.agents import router as agents_router
from app.api.skills import router as skills_router
from app.api.conversations import router as conversations_router
from app.api.chat import router as chat_router
from app.api.chat_ws import router as chat_ws_router
from app.api.artifacts import router as artifacts_router

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(agents_router)
app.include_router(skills_router)
app.include_router(conversations_router)
app.include_router(chat_router)
app.include_router(chat_ws_router)
app.include_router(artifacts_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
