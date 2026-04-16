"""OIDC authentication service using Authlib.

Supports Microsoft Entra ID (Azure AD) and ADFS via OAuth2/OIDC.
"""

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from authlib.integrations.httpx_client import AsyncOAuth2Client
from authlib.jose import jwt
from authlib.oidc.core import CodeIDToken

from app.config import get_settings

logger = logging.getLogger(__name__)

# In-memory state store for OAuth2 CSRF protection
_oauth_states: dict[str, dict[str, Any]] = {}

# Session cookie name
SESSION_COOKIE = "session_token"

# JWKS cache
_jwks_cache: dict[str, dict[str, Any]] = {}


def _get_entra_client() -> AsyncOAuth2Client:
    settings = get_settings()
    return AsyncOAuth2Client(
        client_id=settings.entra_client_id,
        client_secret=settings.entra_client_secret,
        scope="openid email profile",
        redirect_uri="http://localhost:3000/api/auth/callback/microsoft",
    )


def _get_adfs_client() -> AsyncOAuth2Client:
    settings = get_settings()
    return AsyncOAuth2Client(
        client_id=settings.adfs_client_id,
        client_secret=settings.adfs_client_secret,
        scope="openid email profile",
        redirect_uri="http://localhost:3000/api/auth/callback/adfs",
    )


async def get_authorization_url(provider: str) -> tuple[str, str]:
    """Generate authorization URL and store state/nonce for callback verification.

    Returns (authorization_url, state).
    """
    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)

    settings = get_settings()

    if provider == "entra":
        client = _get_entra_client()
        authority = settings.entra_authority
        tenant = settings.entra_tenant_id
        authorize_url = f"{authority}/{tenant}/oauth2/v2.0/authorize"
        auth_url, _ = client.create_authorization_url(
            url=authorize_url,
            state=state,
            nonce=nonce,
        )
    elif provider == "adfs":
        client = _get_adfs_client()
        auth_url, _ = client.create_authorization_url(
            url=settings.adfs_authorization_url,
            state=state,
            nonce=nonce,
        )
    else:
        raise ValueError(f"Unknown OIDC provider: {provider}")

    # Store state for callback verification
    _oauth_states[state] = {
        "provider": provider,
        "nonce": nonce,
        "created_at": datetime.now(timezone.utc),
    }

    return auth_url, state


async def handle_callback(provider: str, code: str, state: str) -> dict[str, Any]:
    """Exchange authorization code for tokens and validate OIDC response.

    Returns dict with token info and claims.
    """
    # Verify state
    stored = _oauth_states.pop(state, None)
    if not stored:
        raise ValueError("Invalid or expired state parameter")
    if stored["provider"] != provider:
        raise ValueError("State/provider mismatch")

    nonce = stored["nonce"]
    settings = get_settings()

    if provider == "entra":
        client = _get_entra_client()
        authority = settings.entra_authority
        tenant = settings.entra_tenant_id
        token_url = f"{authority}/{tenant}/oauth2/v2.0/token"

        token = await client.fetch_token(
            url=token_url,
            code=code,
            grant_type="authorization_code",
        )

        # Decode ID token with JWKS from Microsoft
        id_token = token.get("id_token", "")
        claims = await _decode_entra_id_token(id_token, tenant, nonce)

        return {
            "provider": provider,
            "token": token,
            "claims": claims,
            "id_token": id_token,
        }

    elif provider == "adfs":
        client = _get_adfs_client()

        token = await client.fetch_token(
            url=settings.adfs_token_url,
            code=code,
            grant_type="authorization_code",
        )

        # ADFS: try to decode ID token from response
        id_token = token.get("id_token", "")
        claims = {}
        if id_token:
            try:
                claims = _decode_adfs_id_token(id_token, nonce)
            except Exception as e:
                logger.warning(f"Failed to decode ADFS ID token: {e}")
                # Try userinfo endpoint as fallback
                claims = await _fetch_userinfo(client, token, settings.adfs_userinfo_url)

        return {
            "provider": provider,
            "token": token,
            "claims": claims,
            "id_token": id_token,
        }

    raise ValueError(f"Unknown OIDC provider: {provider}")


async def _fetch_jwks(tenant: str) -> dict:
    """Fetch Microsoft JWKS for ID token verification."""
    if tenant in _jwks_cache:
        return _jwks_cache[tenant]

    url = f"https://login.microsoftonline.com/{tenant}/discovery/v2.0/keys"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        resp.raise_for_status()
        jwks = resp.json()

    _jwks_cache[tenant] = jwks
    return jwks


async def _decode_entra_id_token(id_token: str, tenant: str, expected_nonce: str) -> dict:
    """Decode and verify Entra ID ID token using JWKS."""
    jwks = await _fetch_jwks(tenant)
    key = jwt.decode(id_token, jwks, claims_cls=CodeIDToken)
    key.validate()

    data = dict(key)

    # Verify nonce
    token_nonce = data.get("nonce")
    if token_nonce and token_nonce != expected_nonce:
        raise ValueError("Nonce mismatch")

    return data


def _decode_adfs_id_token(id_token: str, expected_nonce: str) -> dict:
    """Decode ADFS ID token (simplified — may use HS256 or RS256)."""
    # For ADFS, we may not have the JWKS readily available.
    # Try to decode without full verification if needed.
    try:
        claims = jwt.decode(id_token, None, claims_cls=CodeIDToken)
        data = dict(claims)
    except Exception:
        # Fallback: decode without verification
        import base64
        import json
        parts = id_token.split(".")
        if len(parts) >= 2:
            payload = parts[1]
            # Add padding if needed
            padding = 4 - len(payload) % 4
            if padding != 4:
                payload += "=" * padding
            data = json.loads(base64.urlsafe_b64decode(payload))
        else:
            raise ValueError("Invalid ID token format")

    # Verify nonce
    token_nonce = data.get("nonce")
    if token_nonce and token_nonce != expected_nonce:
        raise ValueError("Nonce mismatch")

    return data


async def _fetch_userinfo(client: AsyncOAuth2Client, token: dict, userinfo_url: str) -> dict:
    """Fetch user info from OIDC userinfo endpoint."""
    try:
        resp = await client.get(userinfo_url, token=token.get("access_token", ""))
        return resp.json()
    except Exception as e:
        logger.error(f"UserInfo fetch failed: {e}")
        return {}


def cleanup_expired_states():
    """Remove expired OAuth states (older than 10 minutes)."""
    now = datetime.now(timezone.utc)
    expired = [
        s
        for s, data in _oauth_states.items()
        if now - data["created_at"] > timedelta(minutes=10)
    ]
    for s in expired:
        del _oauth_states[s]


def get_provider_logout_url(provider: str, post_logout_redirect: str = "http://localhost:3000") -> str | None:
    """Get the federated logout URL for the provider."""
    settings = get_settings()

    if provider == "entra":
        tenant = settings.entra_tenant_id
        encoded_redirect = post_logout_redirect
        return f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/logout?post_logout_redirect_uri={encoded_redirect}"
    elif provider == "adfs":
        issuer = settings.adfs_issuer.rstrip("/")
        return f"{issuer}/ls/?wa=wsignout1.0"

    return None
