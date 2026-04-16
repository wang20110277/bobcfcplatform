from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import require_admin
from app.models.user import User
from app.models.agent import user_allowed_agents
from app.schemas import UserSchema, UserUpdate

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("")
async def list_users(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User))
    users = result.scalars().all()

    output = []
    for u in users:
        ar = await db.execute(
            select(user_allowed_agents.c.agent_id).where(user_allowed_agents.c.user_id == u.id)
        )
        allowed = [row[0] for row in ar.all()]
        output.append({
            "id": u.id,
            "username": u.username,
            "role": u.role,
            "email": u.email,
            "allowedAgentIds": allowed if allowed else None,
        })
    return output


@router.put("/{user_id}")
async def update_user(
    user_id: str,
    body: UserUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if body.role is not None:
        user.role = body.role
    if body.username is not None:
        user.username = body.username
    if body.email is not None:
        user.email = body.email
    if body.allowed_agent_ids is not None:
        # Clear existing
        from sqlalchemy import delete
        await db.execute(delete(user_allowed_agents).where(user_allowed_agents.c.user_id == user_id))
        # Insert new
        from sqlalchemy import insert
        for aid in body.allowed_agent_ids:
            await db.execute(insert(user_allowed_agents).values(user_id=user_id, agent_id=aid))
        await db.commit()

    await db.commit()
    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "email": user.email,
        "allowedAgentIds": body.allowed_agent_ids,
    }
