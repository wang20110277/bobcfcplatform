from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services.chat_service import generate_response

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat")
async def chat(
    body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    conversation_id = body.get("conversationId")
    message = body.get("message")

    if not conversation_id or not message:
        raise HTTPException(status_code=400, detail="conversationId and message are required")

    try:
        result = await generate_response(conversation_id, message, db)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to generate response")
