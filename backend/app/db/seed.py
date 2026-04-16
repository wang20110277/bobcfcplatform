from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.skill import Skill
from app.models.agent import Agent, agent_skills, user_allowed_agents
from app.services.auth_service import hash_password


async def seed_minimal(db: AsyncSession):
    """Seed minimal data: 1 SUPER_ADMIN user."""
    # Check if any users exist
    result = await db.execute(select(User))
    if result.scalars().first():
        return  # Already seeded

    import uuid
    user = User(
        id=str(uuid.uuid4()),
        username="admin",
        email="wang20110277@gmail.com",
        password_hash=hash_password("admin"),
        role="SUPER_ADMIN",
    )
    db.add(user)
    await db.commit()

    # Map admin to all agents
    from sqlalchemy import insert
    for agent_id in ["a1", "a2", "a3", "a4"]:
        stmt = insert(user_allowed_agents).values(user_id=user.id, agent_id=agent_id)
        try:
            await db.execute(stmt)
        except Exception:
            pass
    await db.commit()
    print("Seeded: 1 SUPER_ADMIN user (admin / admin) with all agents")


async def seed_all(db: AsyncSession):
    """Full seed: users, agents, skills matching server.ts defaults."""
    await seed_minimal(db)

    # Skills
    skills = [
        Skill(id="s1", name="Text Summary", description="Summarize long text into key points", type="TEXT_SUMMARY", status="ACTIVE"),
        Skill(id="s2", name="PPT Generation", description="Generate PowerPoint slides from content", type="PPT_GENERATION", status="ACTIVE"),
        Skill(id="s3", name="Audio Generation", description="Generate audio from text", type="AUDIO_GENERATION", status="ACTIVE"),
        Skill(id="s4", name="Skill Creation", description="Create new skills for agents", type="SKILL_CREATION", status="ACTIVE"),
    ]
    for s in skills:
        existing = await db.get(Skill, s.id)
        if not existing:
            db.add(s)
    await db.commit()

    # Agents
    agents = [
        Agent(id="a1", name="Summary Agent", description="Summarizes text using AI", status="ACTIVE", recommended_model="gemini-2.0-flash"),
        Agent(id="a2", name="PPT Agent", description="Generates PowerPoint presentations", status="ACTIVE", recommended_model="gemini-2.0-flash"),
        Agent(id="a3", name="Audio Agent", description="Generates audio content", status="ACTIVE", recommended_model="gemini-2.0-flash"),
        Agent(id="a4", name="SkillCreator", description="Specialized agent for building and refining new AI capabilities", status="ACTIVE", recommended_model="gemini-2.0-flash"),
    ]
    for a in agents:
        result = await db.execute(select(Agent).where(Agent.id == a.id))
        if not result.scalar_one_or_none():
            db.add(a)
    await db.commit()

    # Agent-skill mappings
    agent_skill_map = {
        "a1": ["s1"],
        "a2": ["s2"],
        "a3": ["s3"],
        "a4": ["s4"],
    }
    for agent_id, skill_ids in agent_skill_map.items():
        for skill_id in skill_ids:
            from sqlalchemy import insert
            stmt = insert(agent_skills).values(agent_id=agent_id, skill_id=skill_id)
            try:
                await db.execute(stmt)
            except Exception:
                pass  # Already exists

    await db.commit()
    print("Seeded: 3 agents, 4 skills, agent-skill mappings")
