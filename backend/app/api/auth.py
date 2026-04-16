from fastapi import APIRouter, Depends, Response, Cookie
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.oauth_session import OAuthSession
from app.db.seed import seed_minimal
from app.services.auth_service import create_access_token
from app.services.oidc_service import (
    get_authorization_url,
    handle_callback,
    get_provider_logout_url,
    SESSION_COOKIE,
)
from app.services.claim_mapper import map_claims_to_user
from app.config import get_settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/me")
async def get_me(
    current_user: User | None = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    settings = get_settings()

    # Demo mode: return seed user
    if not settings.oidc_provider:
        await seed_minimal(db)
        result = await db.execute(select(User).where(User.role == "SUPER_ADMIN"))
        user = result.scalars().first()
        if not user:
            return None

        from app.models.agent import user_allowed_agents
        result = await db.execute(
            select(user_allowed_agents.c.agent_id).where(user_allowed_agents.c.user_id == user.id)
        )
        allowed = [row[0] for row in result.all()]

        return {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "email": user.email,
            "allowedAgentIds": allowed if allowed else None,
        }

    # OIDC mode
    if not current_user:
        return None

    # Include allowedAgentIds
    from app.models.agent import user_allowed_agents
    result = await db.execute(
        select(user_allowed_agents.c.agent_id).where(user_allowed_agents.c.user_id == current_user.id)
    )
    allowed = [row[0] for row in result.all()]

    return {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
        "email": current_user.email,
        "allowedAgentIds": allowed if allowed else None,
    }


@router.get("/config")
async def auth_config():
    """Return auth config so frontend knows login method."""
    settings = get_settings()
    return {
        "oidcEnabled": bool(settings.oidc_provider),
        "oidcProvider": settings.oidc_provider or "",
    }


@router.get("/login")
async def login_get():
    """GET /api/auth/login — OIDC login initiation.

    In demo mode, this performs the demo login directly.
    In OIDC mode, redirects to IdP authorization URL.
    """
    settings = get_settings()

    if not settings.oidc_provider:
        # Demo mode: perform login directly (no redirect needed)
        from app.db.session import async_session
        async with async_session() as db:
            await seed_minimal(db)
            result = await db.execute(select(User).where(User.role == "SUPER_ADMIN"))
            user = result.scalars().first()
            if not user:
                from fastapi.responses import JSONResponse
                return JSONResponse(status_code=401, content={"error": "No admin user found"})

            token = create_access_token(user.id, user.role, user.email)
            response = RedirectResponse(url=f"{settings.frontend_url}/")
            response.set_cookie(
                key="token",
                value=token,
                httponly=True,
                samesite="lax",
                path="/",
                max_age=86400,
            )
            return response

    # OIDC mode: redirect to IdP
    provider = settings.oidc_provider
    auth_url, state = await get_authorization_url(provider)
    return RedirectResponse(url=auth_url)


@router.post("/login")
async def login_post(
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """POST /api/auth/login — kept for frontend compatibility.

    In demo mode, performs login (JWT cookie).
    In OIDC mode, returns the authorization URL for the frontend to redirect to.
    """
    settings = get_settings()

    if not settings.oidc_provider:
        # Demo mode: auto-login with JWT cookie
        await seed_minimal(db)
        result = await db.execute(select(User).where(User.role == "SUPER_ADMIN"))
        user = result.scalars().first()
        if not user:
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=401, content={"error": "No admin user found"})

        token = create_access_token(user.id, user.role, user.email)
        response.set_cookie(
            key="token",
            value=token,
            httponly=True,
            samesite="lax",
            path="/",
            max_age=86400,
        )
        return {"status": "ok"}

    # OIDC mode: return the authorization URL
    provider = settings.oidc_provider
    auth_url, state = await get_authorization_url(provider)
    return {"authUrl": auth_url}


@router.get("/callback/microsoft")
async def auth_callback_entra(
    response: Response,
    code: str | None = None,
    state: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Handle Entra ID callback from IdP."""
    settings = get_settings()

    if not code or not state:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=400, content={"error": "Missing code or state parameter"})

    provider = "entra"

    try:
        callback_result = await handle_callback(provider, code, state)

        claims = callback_result["claims"]
        token = callback_result["token"]
        id_token = callback_result["id_token"]

        # Map claims to standard user
        user_claims = map_claims_to_user(claims, provider)

        # Determine user role from mapped roles
        role = _determine_role(user_claims.roles, provider)

        # Find or create user
        result = await db.execute(
            select(User).where(User.provider_user_id == user_claims.provider_id)
        )
        user = result.scalars().first()

        if not user:
            # Create new user
            import uuid
            user = User(
                id=str(uuid.uuid4()),
                username=user_claims.username or user_claims.email,
                email=user_claims.email,
                role=role,
                provider=user_claims.provider,
                provider_user_id=user_claims.provider_id,
                claims_data=claims,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        else:
            # Update existing user
            user.email = user_claims.email or user.email
            user.username = user_claims.username or user.username
            user.role = role
            user.claims_data = claims
            await db.commit()
            await db.refresh(user)

        # Create OAuth session
        import uuid
        session_id = str(uuid.uuid4())
        expires_at = int(token.get("expires_at", 0)) if isinstance(token.get("expires_at"), (int, float)) else None

        oauth_session = OAuthSession(
            id=session_id,
            user_id=user.id,
            provider=provider,
            access_token=token.get("access_token", ""),
            refresh_token=token.get("refresh_token"),
            id_token=id_token,
            expires_at=expires_at,
        )
        db.add(oauth_session)
        await db.commit()

        # Create session JWT for cookie
        session_jwt = create_access_token(user.id, user.role, user.email)

        # Set session cookie on the redirect response
        redirect_response = RedirectResponse(url=f"{settings.frontend_url}/", status_code=302)
        redirect_response.set_cookie(
            key=SESSION_COOKIE,
            value=session_jwt,
            httponly=True,
            samesite="lax",
            path="/",
            max_age=settings.session_max_age,
        )
        return redirect_response

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Entra ID callback failed: {e}", exc_info=True)
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=500, content={"error": f"Authentication failed: {str(e)}"})


@router.get("/callback/adfs")
async def auth_callback_adfs(
    response: Response,
    code: str | None = None,
    state: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Handle ADFS callback from IdP."""
    settings = get_settings()

    if not code or not state:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=400, content={"error": "Missing code or state parameter"})

    provider = "adfs"

    try:
        callback_result = await handle_callback(provider, code, state)

        claims = callback_result["claims"]
        token = callback_result["token"]
        id_token = callback_result["id_token"]

        # Map claims to standard user
        user_claims = map_claims_to_user(claims, provider)

        # Determine user role from mapped roles
        role = _determine_role(user_claims.roles, provider)

        # Find or create user
        result = await db.execute(
            select(User).where(User.provider_user_id == user_claims.provider_id)
        )
        user = result.scalars().first()

        if not user:
            import uuid
            user = User(
                id=str(uuid.uuid4()),
                username=user_claims.username or user_claims.email,
                email=user_claims.email,
                role=role,
                provider=user_claims.provider,
                provider_user_id=user_claims.provider_id,
                claims_data=claims,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        else:
            user.email = user_claims.email or user.email
            user.username = user_claims.username or user.username
            user.role = role
            user.claims_data = claims
            await db.commit()
            await db.refresh(user)

        import uuid
        session_id = str(uuid.uuid4())
        expires_at = int(token.get("expires_at", 0)) if isinstance(token.get("expires_at"), (int, float)) else None

        oauth_session = OAuthSession(
            id=session_id,
            user_id=user.id,
            provider=provider,
            access_token=token.get("access_token", ""),
            refresh_token=token.get("refresh_token"),
            id_token=id_token,
            expires_at=expires_at,
        )
        db.add(oauth_session)
        await db.commit()

        session_jwt = create_access_token(user.id, user.role, user.email)
        redirect_response = RedirectResponse(url=f"{settings.frontend_url}/", status_code=302)
        redirect_response.set_cookie(
            key=SESSION_COOKIE,
            value=session_jwt,
            httponly=True,
            samesite="lax",
            path="/",
            max_age=settings.session_max_age,
        )
        return redirect_response

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"ADFS callback failed: {e}", exc_info=True)
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=500, content={"error": f"Authentication failed: {str(e)}"})


@router.post("/logout")
async def logout(
    response: Response,
    current_user: User | None = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Logout endpoint."""
    settings = get_settings()

    # Delete OAuth session
    if current_user:
        from sqlalchemy import delete
        stmt = delete(OAuthSession).where(OAuthSession.user_id == current_user.id)
        await db.execute(stmt)
        await db.commit()

    # Clear cookies
    response.delete_cookie(key="token", path="/")
    response.delete_cookie(key=SESSION_COOKIE, path="/")

    # OIDC mode: return provider logout URL
    if settings.oidc_provider and current_user:
        provider = current_user.provider or settings.oidc_provider
        logout_url = get_provider_logout_url(provider)
        if logout_url:
            return {"logoutUrl": logout_url}

    return {"status": "ok"}


def _determine_role(roles: list[str], provider: str) -> str:
    """Determine user role from OIDC roles."""
    settings = get_settings()
    admin_roles = []

    if provider == "entra":
        admin_roles = [
            r.lower() for r in settings.entra_role_mappings.values()
            if "admin" in r.lower()
        ]
    elif provider == "adfs":
        admin_roles = [
            r.lower() for r in settings.adfs_role_mappings.values()
            if "admin" in r.lower()
        ]

    for role in roles:
        if role.lower() in admin_roles or "admin" in role.lower():
            return "SUPER_ADMIN"

    return "REGULAR_USER"
