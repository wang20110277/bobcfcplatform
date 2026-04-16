from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from functools import lru_cache
import json


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://bobcfc:bobcfc_secret@localhost:5432/bobcfc"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # RocketMQ
    rocketmq_namesrv: str = "localhost:9876"
    rocketmq_group: str = "backend-group"

    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "artifacts"
    minio_secure: bool = False

    # Auth (JWT, kept for API token signing if needed)
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    # OIDC Authentication
    oidc_provider: str = ""  # "entra" or "adfs", empty = demo mode (no OIDC)

    # Microsoft Entra ID
    entra_client_id: str = ""
    entra_client_secret: str = ""
    entra_tenant_id: str = "common"
    entra_authority: str = "https://login.microsoftonline.com"
    entra_role_mappings: dict = Field(default_factory=lambda: {})

    # ADFS
    adfs_client_id: str = ""
    adfs_client_secret: str = ""
    adfs_issuer: str = ""
    adfs_authorization_url: str = ""
    adfs_token_url: str = ""
    adfs_userinfo_url: str = ""
    adfs_role_mappings: dict = Field(default_factory=lambda: {})

    # Session
    session_max_age: int = 28800  # 8 hours

    # Gemini
    gemini_api_key: str = ""

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    frontend_url: str = "http://localhost:3000"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    def model_post_init(self, __context):
        # Parse JSON string role mappings if they came from env
        if isinstance(self.entra_role_mappings, str):
            self.entra_role_mappings = json.loads(self.entra_role_mappings)
        if isinstance(self.adfs_role_mappings, str):
            self.adfs_role_mappings = json.loads(self.adfs_role_mappings)


@lru_cache
def get_settings() -> Settings:
    return Settings()
