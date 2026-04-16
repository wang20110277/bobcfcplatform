"""OIDC claim mapping for Entra ID and ADFS.

Mirrors the reference implementation in auth-utils.ts.
"""

import json
import logging
from dataclasses import dataclass

from app.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class StandardUserClaims:
    id: str
    name: str
    email: str
    username: str
    provider: str
    provider_id: str
    roles: list[str]


def normalize_role(role: str) -> str:
    """Strip LDAP-style prefixes like CN=, OU=, DC=."""
    if not role:
        return ""
    cleaned = role.split("=", 1)[-1] if "=" in role else role
    first = cleaned.split(",")[0]
    return first.lower().strip()


def merge_claim_roles(roles: list[str]) -> list[str]:
    """Deduplicate and normalize roles."""
    return list({normalize_role(r) for r in roles if r})


def _get_role_mappings(provider: str) -> dict:
    settings = get_settings()
    if provider == "entra":
        return settings.entra_role_mappings
    return settings.adfs_role_mappings


def map_claims_to_user(claims: dict, provider: str) -> StandardUserClaims:
    """Map raw OIDC claims to a standard user profile."""
    if provider == "entra":
        return _map_entra_claims(claims)
    return _map_adfs_claims(claims)


def _map_entra_claims(claims: dict) -> StandardUserClaims:
    oid = claims.get("oid") or claims.get("sub", "")
    email = (
        claims.get("email")
        or claims.get("preferred_username")
        or ""
    )
    username = (
        claims.get("preferred_username")
        or claims.get("email")
        or ""
    )
    roles = _extract_entra_roles(claims)
    name = claims.get("name", "")

    return StandardUserClaims(
        id=str(oid),
        name=name,
        email=email,
        username=username,
        provider="entra",
        provider_id=str(oid),
        roles=roles,
    )


def _extract_entra_roles(claims: dict) -> list[str]:
    roles = claims.get("roles", []) or []
    groups = claims.get("groups", []) or []
    if not isinstance(roles, list):
        roles = [roles]
    if not isinstance(groups, list):
        groups = [groups]

    mappings = _get_role_mappings("entra")
    all_roles = []
    for role in list(roles) + list(groups):
        mapped = mappings.get(role, role)
        normalized = normalize_role(str(role))
        if normalized:
            all_roles.append(normalized)
    return list(set(all_roles))


def _map_adfs_claims(claims: dict) -> StandardUserClaims:
    email = _extract_adfs_email(claims)

    provider_id = (
        claims.get("sub")
        or claims.get("unique_name")
        or claims.get("upn")
        or ""
    )
    username = (
        claims.get("unique_name")
        or claims.get("upn")
        or email
        or ""
    )
    name = (
        claims.get("name")
        or claims.get("displayname")
        or claims.get("unique_name")
        or ""
    )
    roles = _extract_adfs_roles(claims)

    return StandardUserClaims(
        id=str(provider_id),
        name=name,
        email=email,
        username=username,
        provider="adfs",
        provider_id=str(provider_id),
        roles=roles,
    )


def _extract_adfs_email(claims: dict) -> str:
    """Extract email from ADFS claims, checking multiple possible field names."""
    return (
        claims.get("upn")
        or claims.get("http://schemas.xmlsoap.org/ws/2005/05/identity/claims/upn")
        or claims.get("email")
        or claims.get("emailaddress")
        or claims.get("http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress")
        or ""
    )


def _extract_adfs_roles(claims: dict) -> list[str]:
    role_claim = claims.get("role")
    group_claim = claims.get("group")

    roles = []
    if role_claim is not None:
        roles = [role_claim] if isinstance(role_claim, str) else list(role_claim)
    groups = []
    if group_claim is not None:
        groups = [group_claim] if isinstance(group_claim, str) else list(group_claim)

    mappings = _get_role_mappings("adfs")
    all_roles = []
    for role in roles + groups:
        mapped = mappings.get(role, role)
        normalized = normalize_role(str(role))
        if normalized:
            all_roles.append(normalized)
    return list(set(all_roles))
