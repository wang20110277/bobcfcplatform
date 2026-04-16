from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.models.message import Message
from app.models.agent import Agent, agent_skills
from app.models.skill import Skill
from app.config import get_settings


def _build_system_prompt(agent: Agent | None, skills: list[Skill]) -> str:
    parts = []
    if agent:
        parts.append(f"You are {agent.name}: {agent.description}.")
        if skills:
            skill_descs = ", ".join(f"{s.name} ({s.description})" for s in skills)
            parts.append(f"Available skills: {skill_descs}.")
        parts.append("Respond helpfully and concisely.")
    return "\n".join(parts)


async def generate_response(
    conversation_id: str,
    user_message: str,
    db: AsyncSession,
) -> dict:
    """
    Core chat logic:
    1. Load conversation + agent + skills
    2. Build LangChain prompt with agent context
    3. Call Gemini
    4. Save messages, auto-title if first
    5. Return {content, conversation}
    """
    # Load conversation
    result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
    conv = result.scalar_one_or_none()
    if not conv:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Load agent and skills
    agent = None
    skills = []
    if conv.agent_id:
        agent = await db.get(Agent, conv.agent_id)
        if agent:
            sr = await db.execute(
                select(agent_skills.c.skill_id).where(agent_skills.c.agent_id == conv.agent_id)
            )
            skill_ids = [row[0] for row in sr.all()]
            if skill_ids:
                sr2 = await db.execute(select(Skill).where(Skill.id.in_(skill_ids)))
                skills = sr2.scalars().all()

    model_id = conv.model_id or "gemini-2.0-flash"

    # Load message history
    msg_result = await db.execute(
        select(Message).where(Message.conversation_id == conversation_id).order_by(Message.timestamp)
    )
    history_msgs = msg_result.scalars().all()

    # Build LangChain prompt and call Gemini
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.messages import SystemMessage, HumanMessage as LCHuman, AIMessage as LCAI

    settings = get_settings()
    llm = ChatGoogleGenerativeAI(model=model_id, google_api_key=settings.gemini_api_key, temperature=0.7)

    messages = []
    system_text = _build_system_prompt(agent, skills)
    if system_text:
        messages.append(SystemMessage(content=system_text))
    for m in history_msgs:
        if m.role == "user":
            messages.append(LCHuman(content=m.content))
        else:
            messages.append(LCAI(content=m.content))

    # Add current user message to history
    messages.append(LCHuman(content=user_message))

    response = await llm.ainvoke(messages)
    assistant_content = response.content

    # Save user message
    import uuid as _uuid
    now = datetime.now(timezone.utc)
    user_msg = Message(
        id=str(_uuid.uuid4()),
        conversation_id=conversation_id,
        role="user",
        content=user_message,
        timestamp=now,
    )
    assistant_msg = Message(
        id=str(_uuid.uuid4()),
        conversation_id=conversation_id,
        role="assistant",
        content=assistant_content,
        timestamp=now,
    )
    db.add(user_msg)
    db.add(assistant_msg)

    # Auto-title if first message pair
    is_first = len(history_msgs) == 0
    if is_first:
        conv.title = user_message[:30]

    await db.commit()

    # Rebuild conversation schema
    all_msgs = history_msgs + [user_msg, assistant_msg]
    messages_list = []
    for m in all_msgs:
        ts = m.timestamp
        if isinstance(ts, datetime) and ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        messages_list.append({
            "role": m.role,
            "content": m.content,
            "timestamp": ts.isoformat(),
        })

    conversation = {
        "id": conv.id,
        "userId": conv.user_id,
        "agentId": conv.agent_id,
        "messages": messages_list,
        "title": conv.title,
        "modelId": conv.model_id,
    }

    return {"content": assistant_content, "conversation": conversation}
