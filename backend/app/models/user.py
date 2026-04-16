from sqlalchemy import Column, String, CheckConstraint, JSON
from app.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)
    role = Column(String(20), nullable=False, default="REGULAR_USER")

    # OIDC fields
    provider = Column(String(50), nullable=True)
    provider_user_id = Column(String(255), nullable=True)
    claims_data = Column(JSON, nullable=True)

    __table_args__ = (
        CheckConstraint("role IN ('SUPER_ADMIN', 'REGULAR_USER')", name="ck_user_role"),
    )
