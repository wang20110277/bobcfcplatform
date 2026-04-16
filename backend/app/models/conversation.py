from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin


class Conversation(Base, TimestampMixin):
    __tablename__ = "conversations"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(String(50), ForeignKey("agents.id"), nullable=True)
    title = Column(String(500), nullable=False, default="New Conversation")
    model_id = Column(String(100), nullable=True)

    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", lazy="selectin")
