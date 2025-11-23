from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.schemas.websocket_messages import ErrorMessage
from app.core.orchestrator import Orchestrator
from app.Config.dataConfig import Config
from app.schemas.websocket_messages import UserMessage
from app.utils.logger import logger
import jwt

settings = Config.Config.from_env()
router = APIRouter()
orchestrator = Orchestrator()

@router.websocket("/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # Verify Token
    token = websocket.query_params.get("token")
    session_id = websocket.query_params.get("session_id", "default_session")
    user_id = None
    
    if not token:
        await websocket.close(code=1008, reason="Missing authentication token")
        return

    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("id")
    except jwt.ExpiredSignatureError:
        await websocket.close(code=1008, reason="Token expired")
        return
    except jwt.InvalidTokenError:
        await websocket.close(code=1008, reason="Invalid token")
        return

    async def send_callback(message_model):
        try:
            await websocket.send_json(message_model.dict())
        except Exception as e:
            logger.warning(f"Failed to send message to client (disconnected?): {e}")

    while True:
        data = await websocket.receive_json()
        # Basic validation
        try:
            user_msg = UserMessage(**data)
            payload = user_msg.payload

            text = payload.text
            selected_text = payload.selected_text
            source_message_id = payload.source_message_id
            
            if text:
                await orchestrator.handle_message(text, session_id, send_callback, user_id, selected_text, source_message_id)
        except WebSocketDisconnect:
            raise 
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            try:
                await websocket.send_json(ErrorMessage(payload={"code": "PROCESSING_ERROR", "message": str(e)}).dict())
            except Exception:
                logger.warning("Could not send error message to client (connection likely closed).")
            
