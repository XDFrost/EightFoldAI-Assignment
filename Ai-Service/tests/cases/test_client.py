import asyncio
import websockets
import json
import jwt
import sys
import os
import time

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from app.Config.dataConfig import Config

settings = Config.Config.from_env()
async def hello():
    # Generate a test token
    payload = {
        "id": "00000000-0000-0000-0000-000000000000",
        "email": "test@example.com",
        "role": "user",
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
    
    uri = f"ws://localhost:8000/ai-service/ws/chat?session_id=test_sess&token={token}"
    async with websockets.connect(uri, additional_headers={"Origin": "http://localhost:3000"}) as websocket:
        # Send a research request
        msg = {
            "type": "user_message",
            "payload": {
                "session_id": "test_sess",
                "message_id": "msg_1",
                "text": "Generate an account plan for Google"
            }
        }
        await websocket.send(json.dumps(msg))
        print(f"> Sent: {msg}")

        while True:
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=60)
                print(f"< Received: {response}")
            except asyncio.TimeoutError:
                print("Timeout waiting for response")
                break
            except Exception as e:
                print(f"Error: {e}")
                break

if __name__ == "__main__":
    asyncio.run(hello())
