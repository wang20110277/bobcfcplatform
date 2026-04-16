from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.db.session import async_session
from app.services.chat_service import generate_response
from app.websocket.manager import ws_manager

router = APIRouter(prefix="/api/ws", tags=["websocket"])


@router.websocket("/chat")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket endpoint for real-time chat.
    Client sends: {"conversationId": "uuid", "message": "text"}
    Server responds: {"content": "reply", "conversation": {...}}
    """
    conv_id = None
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            conversation_id = data.get("conversationId")
            message = data.get("message")

            if not conversation_id or not message:
                await websocket.send_json({"error": "conversationId and message required"})
                continue

            # Connect to manager for broadcast (future use with RocketMQ)
            if conv_id != conversation_id:
                if conv_id:
                    await ws_manager.disconnect(websocket, conv_id)
                conv_id = conversation_id
                await ws_manager.connect(websocket, conversation_id)

            async with async_session() as db:
                try:
                    result = await generate_response(conversation_id, message, db)
                    await db.commit()
                    await websocket.send_json(result)
                except Exception as e:
                    await websocket.send_json({"error": str(e)})

    except WebSocketDisconnect:
        if conv_id:
            await ws_manager.disconnect(websocket, conv_id)
    except Exception:
        if conv_id:
            await ws_manager.disconnect(websocket, conv_id)
