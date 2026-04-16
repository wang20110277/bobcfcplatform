from datetime import datetime, timezone
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.agent import Agent

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


def _to_schema(conv: Conversation) -> dict:
    messages = []
    for m in sorted(conv.messages, key=lambda x: x.timestamp):
        ts = m.timestamp
        if isinstance(ts, datetime) and ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        messages.append({
            "role": m.role,
            "content": m.content,
            "timestamp": ts.isoformat() if isinstance(ts, datetime) else str(ts),
        })
    return {
        "id": conv.id,
        "userId": conv.user_id,
        "agentId": conv.agent_id,
        "messages": messages,
        "title": conv.title,
        "modelId": conv.model_id,
    }


@router.get("")
async def list_conversations(
    current_user: User | None = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user:
        return []
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
    )
    convs = result.scalars().all()
    # Return with empty messages list for the sidebar (lightweight)
    return [
        {
            "id": c.id,
            "userId": c.user_id,
            "agentId": c.agent_id,
            "messages": [],
            "title": c.title,
            "modelId": c.model_id,
        }
        for c in convs
    ]


@router.get("/{conv_id}")
async def get_conversation(
    conv_id: str,
    current_user: User | None = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    result = await db.execute(
        select(Conversation).where(Conversation.id == conv_id, Conversation.user_id == current_user.id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return _to_schema(conv)


@router.post("")
async def create_conversation(
    body: dict,
    current_user: User | None = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    import uuid
    agent_id = body.get("agentId")
    title = body.get("title") or "New Conversation"
    model_id = body.get("modelId")

    # Default model from agent
    if not model_id and agent_id:
        agent = await db.get(Agent, agent_id)
        if agent and agent.recommended_model:
            model_id = agent.recommended_model

    if not model_id:
        model_id = "gemini-2.0-flash"

    conv = Conversation(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        agent_id=agent_id,
        title=title,
        model_id=model_id,
    )
    db.add(conv)
    await db.commit()
    await db.refresh(conv)

    return _to_schema(conv)


@router.patch("/{conv_id}")
async def update_conversation(
    conv_id: str,
    body: dict,
    current_user: User | None = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    result = await db.execute(
        select(Conversation).where(Conversation.id == conv_id, Conversation.user_id == current_user.id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if body.get("modelId") is not None:
        conv.model_id = body["modelId"]

    await db.commit()
    return _to_schema(conv)
