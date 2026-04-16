from sqlalchemy import Column, String, ForeignKey, CheckConstraint
from app.models.base import Base, TimestampMixin


class Artifact(Base, TimestampMixin):
    __tablename__ = "artifacts"

    session_id = Column(String(36), nullable=False, index=True)
    name = Column(String(500), nullable=False)
    type = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, default="PENDING")
    storage_path = Column(String(1000), nullable=True)

    __table_args__ = (
        CheckConstraint("status IN ('PENDING', 'COMPLETED', 'FAILED')", name="ck_artifact_status"),
    )
