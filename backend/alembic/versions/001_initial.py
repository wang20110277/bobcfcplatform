"""initial schema

Revision ID: 001_initial
Revises:
Create Date: 2026-04-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("username", sa.String(100), unique=True, nullable=False),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("role", sa.String(20), nullable=False, server_default="REGULAR_USER"),
        # OIDC fields
        sa.Column("provider", sa.String(50), nullable=True),
        sa.Column("provider_user_id", sa.String(255), nullable=True),
        sa.Column("claims_data", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("role IN ('SUPER_ADMIN', 'REGULAR_USER')", name="ck_user_role"),
    )
    op.create_index("ix_users_username", "users", ["username"])
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "oauth_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("access_token", sa.String(4000), nullable=True),
        sa.Column("refresh_token", sa.String(4000), nullable=True),
        sa.Column("id_token", sa.String(8000), nullable=True),
        sa.Column("expires_at", sa.BigInteger, nullable=True),
    )
    op.create_index("ix_oauth_sessions_user_id", "oauth_sessions", ["user_id"])

    op.create_table(
        "skills",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("type", sa.String(100), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('ACTIVE', 'INACTIVE')", name="ck_skill_status"),
    )

    op.create_table(
        "agents",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE"),
        sa.Column("recommended_model", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('ACTIVE', 'INACTIVE')", name="ck_agent_status"),
    )

    op.create_table(
        "agent_skills",
        sa.Column("agent_id", sa.String(50), sa.ForeignKey("agents.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("skill_id", sa.String(50), sa.ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "user_allowed_agents",
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("agent_id", sa.String(50), nullable=False, primary_key=True),
    )

    op.create_table(
        "conversations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_id", sa.String(50), sa.ForeignKey("agents.id"), nullable=True),
        sa.Column("title", sa.String(500), nullable=False, server_default="New Conversation"),
        sa.Column("model_id", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_conversations_user_id", "conversations", ["user_id"])

    op.create_table(
        "messages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("conversation_id", sa.String(36), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("role IN ('user', 'assistant')", name="ck_message_role"),
    )
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])

    op.create_table(
        "artifacts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("session_id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("type", sa.String(100), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("storage_path", sa.String(1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('PENDING', 'COMPLETED', 'FAILED')", name="ck_artifact_status"),
    )
    op.create_index("ix_artifacts_session_id", "artifacts", ["session_id"])


def downgrade() -> None:
    op.drop_table("oauth_sessions")
    op.drop_table("artifacts")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("user_allowed_agents")
    op.drop_table("agent_skills")
    op.drop_table("agents")
    op.drop_table("skills")
    op.drop_table("users")
