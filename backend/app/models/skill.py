from sqlalchemy import Column, String, Text, CheckConstraint
from app.models.base import Base, TimestampMixin


class Skill(Base, TimestampMixin):
    __tablename__ = "skills"

    id = Column(String(50), primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    type = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, default="ACTIVE")

    __table_args__ = (
        CheckConstraint("status IN ('ACTIVE', 'INACTIVE')", name="ck_skill_status"),
    )
