from sqlalchemy import Column, String, Text, Table, ForeignKey, CheckConstraint
from app.models.base import Base, TimestampMixin

# Junction table: agent -> skills
agent_skills = Table(
    "agent_skills",
    Base.metadata,
    Column("agent_id", String(50), ForeignKey("agents.id", ondelete="CASCADE"), primary_key=True),
    Column("skill_id", String(50), ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
)

# Junction table: user -> allowed agents
user_allowed_agents = Table(
    "user_allowed_agents",
    Base.metadata,
    Column("user_id", String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("agent_id", String(50), nullable=False, primary_key=True),
)


class Agent(Base, TimestampMixin):
    __tablename__ = "agents"

    id = Column(String(50), primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="ACTIVE")
    recommended_model = Column(String(100), nullable=True)

    __table_args__ = (
        CheckConstraint("status IN ('ACTIVE', 'INACTIVE')", name="ck_agent_status"),
    )
