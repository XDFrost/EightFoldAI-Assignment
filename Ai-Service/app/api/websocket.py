from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from app.schemas.websocket_messages import ErrorMessage
from app.schemas.websocket_messages import UserMessage
from app.core.orchestrator import Orchestrator
from app.Config.dataConfig import Config
from app.utils.logger import logger
import asyncio
import json
import jwt
import re
import uuid
from app.services.voice_service import VoiceService

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

    try:
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
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                try:
                    await websocket.send_json(ErrorMessage(payload={"code": "PROCESSING_ERROR", "message": str(e)}).dict())
                except Exception:
                    logger.warning("Could not send error message to client (connection likely closed).")
    except WebSocketDisconnect:
        logger.info(f"Client disconnected: {session_id}")
    except Exception as e:
        logger.error(f"Error in websocket endpoint: {e}")
        await websocket.close(code=1008, reason="Internal server error")

@router.websocket("/voice")
async def voice_websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # Generate a unique session ID for this voice connection
    voice_session_id = str(uuid.uuid4())
    
    # Verify Token
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008, reason="Missing authentication token")
        return

    try:
        jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
    except Exception:
        await websocket.close(code=1008, reason="Invalid token")
        return

    # Initialize Voice Service
    from app.services.voice_service import VoiceService
    voice_service = VoiceService()
    
    if not voice_service.client:
        await websocket.close(code=1008, reason="Voice service unavailable")
        return

    audio_queue = asyncio.Queue()
    text_queue = asyncio.Queue()

    # Start transcription task
    transcription_task = asyncio.create_task(voice_service.transcribe_stream(audio_queue, text_queue))

    # Decode token to get user_id
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.ALGORITHM])
        user_id = payload.get("id")
    except Exception as e:
        logger.error(f"Invalid token: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Audio queue for incoming chunks
    audio_queue = asyncio.Queue()
    
    # Start transcription task
    transcription_task = asyncio.create_task(voice_service.transcribe_stream(audio_queue, text_queue))
    
    # Shared state for interruption
    state = {"interrupted": False}

    async def process_text():
        try:
            while True:
                text = await text_queue.get()
                if text is None:
                    break
                
                state["interrupted"] = False
                await websocket.send_json({"type": "transcription", "text": text})
                
                full_response = []
                
                async def voice_callback(message_model):
                    if state["interrupted"]: return
                    try:
                        msg_dict = message_model.dict()
                        if msg_dict.get("type") == "status_update":
                            await websocket.send_json({"type": "status_update", "text": msg_dict.get("payload", {}).get("message")})
                        elif msg_dict.get("type") == "assistant_chunk":
                            chunk = msg_dict.get("payload", {}).get("chunk", "")
                            if chunk: full_response.append(chunk)
                    except Exception as e:
                        logger.error(f"Error in voice callback: {e}")

                # Use the persistent voice_session_id
                await orchestrator.handle_message(text, voice_session_id, voice_callback, user_id, save_messages=False)

                if state["interrupted"]: continue

                response_text = "".join(full_response)
                if response_text:
                    # Send text response to frontend for display
                    await websocket.send_json({"type": "ai_response", "text": response_text})
                    
                    # Clean text for TTS (remove markdown)
                    tts_text = re.sub(r'\*\*|__', '', response_text) # Remove bold
                    tts_text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', tts_text) # Remove links
                    tts_text = re.sub(r'^\s*#+\s*', '', tts_text, flags=re.MULTILINE) # Remove headers
                    
                    logger.info(f"Generating TTS for: {tts_text}")
                    audio_bytes = await voice_service.text_to_speech(tts_text)
                    
                    if state["interrupted"]:
                         logger.info("Skipping audio send due to interruption.")
                         continue

                    if audio_bytes:
                        await websocket.send_bytes(audio_bytes)
        except Exception as e:
            logger.error(f"Error processing text: {e}")

    processing_task = asyncio.create_task(process_text())

    try:
        while True:
            data = await websocket.receive()
            
            if "bytes" in data:
                await audio_queue.put(data["bytes"])
            elif "text" in data:
                try:
                    msg = json.loads(data["text"])
                    if msg.get("type") == "interrupt":
                        logger.info("Received interrupt signal.")
                        state["interrupted"] = True
                except:
                    pass
            
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await audio_queue.put(None) # Signal transcription to exit
        await text_queue.put(None) # Signal process_text to exit
        
        # Cancel tasks
        transcription_task.cancel()
        processing_task.cancel()
        
        try:
            await transcription_task
            await processing_task
        except asyncio.CancelledError:
            pass

