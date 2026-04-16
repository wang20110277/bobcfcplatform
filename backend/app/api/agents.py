from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.agent import Agent, agent_skills, user_allowed_agents
from app.schemas import AgentUpdate

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.get("")
async def list_agents(
    sidebar: str | None = Query(None),
    current_user: User | None = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Agent)

    if not current_user:
        query = query.where(Agent.status == "ACTIVE")
    elif current_user.role != "SUPER_ADMIN":
        # Regular user: only ACTIVE agents in their allowed list
        subq = (
            select(user_allowed_agents.c.agent_id)
            .where(user_allowed_agents.c.user_id == current_user.id)
        )
        query = query.where(Agent.status == "ACTIVE").where(Agent.id.in_(subq))
    elif sidebar == "true":
        # Super admin + sidebar: only ACTIVE
        query = query.where(Agent.status == "ACTIVE")

    result = await db.execute(query.order_by(Agent.id))
    agents = result.scalars().all()

    output = []
    for a in agents:
        sr = await db.execute(
            select(agent_skills.c.skill_id).where(agent_skills.c.agent_id == a.id)
        )
        skill_ids = [row[0] for row in sr.all()]
        output.append({
            "id": a.id,
            "name": a.name,
            "description": a.description,
            "status": a.status,
            "skillIds": skill_ids,
            "recommendedModel": a.recommended_model,
        })
    return output


@router.put("/{agent_id}")
async def update_agent(
    agent_id: str,
    body: AgentUpdate,
    current_user: User | None = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user or current_user.role != "SUPER_ADMIN":
        raise HTTPException(status_code=403, detail="Forbidden")
    agent = await db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if body.name is not None:
        agent.name = body.name
    if body.description is not None:
        agent.description = body.description
    if body.status is not None:
        agent.status = body.status
    if body.recommended_model is not None:
        agent.recommended_model = body.recommended_model
    if body.skill_ids is not None:
        from sqlalchemy import delete, insert
        await db.execute(delete(agent_skills).where(agent_skills.c.agent_id == agent_id))
        for sid in body.skill_ids:
            await db.execute(insert(agent_skills).values(agent_id=agent_id, skill_id=sid))

    await db.commit()

    sr = await db.execute(select(agent_skills.c.skill_id).where(agent_skills.c.agent_id == agent_id))
    skill_ids = [row[0] for row in sr.all()]

    return {
        "id": agent.id,
        "name": agent.name,
        "description": agent.description,
        "status": agent.status,
        "skillIds": skill_ids,
        "recommendedModel": agent.recommended_model,
    }
