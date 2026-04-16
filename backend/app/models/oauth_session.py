from sqlalchemy import Column, String, ForeignKey, DateTime, BigInteger
from sqlalchemy.orm import relationship

from app.models.base import Base


class OAuthSession(Base):
    __tablename__ = "oauth_sessions"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    provider = Column(String(50), nullable=False)
    access_token = Column(String(4000), nullable=True)
    refresh_token = Column(String(4000), nullable=True)
    id_token = Column(String(8000), nullable=True)
    expires_at = Column(BigInteger, nullable=True)

    user = relationship("User")
