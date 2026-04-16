from fastapi import Depends, HTTPException, Request, Cookie
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import redis.asyncio as redis

from app.db.session import get_db
from app.services.auth_service import decode_access_token
from app.models.user import User
from app.services.cache_service import get_redis
from app.config import get_settings
from app.services.oidc_service import SESSION_COOKIE


async def get_current_user(
    request: Request,
    token: str | None = Cookie(None, alias="token"),
    session_token: str | None = Cookie(None, alias=SESSION_COOKIE),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Extract user from JWT cookie. Returns None (not 401) if not authenticated.

    Supports both demo mode (token cookie) and OIDC mode (session_token cookie).
    """
    settings = get_settings()

    # Try token cookie first (demo mode)
    jwt_token = token or session_token
    if not jwt_token:
        # Also check Authorization header as fallback
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            jwt_token = auth_header[7:]
        else:
            return None

    payload = decode_access_token(jwt_token)
    if not payload:
        return None

    user = await db.get(User, payload["sub"])
    return user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user or current_user.role != "SUPER_ADMIN":
        raise HTTPException(status_code=403, detail="Forbidden")
    return current_user


async def get_cache():
    """Dependency for CacheService."""
    r = await get_redis()
    from app.services.cache_service import CacheService
    return CacheService(r)
