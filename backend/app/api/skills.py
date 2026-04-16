from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.skill import Skill

router = APIRouter(prefix="/api/skills", tags=["skills"])


@router.get("")
async def list_skills(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Skill).order_by(Skill.id))
    skills = result.scalars().all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "description": s.description,
            "type": s.type,
            "status": s.status,
        }
        for s in skills
    ]
