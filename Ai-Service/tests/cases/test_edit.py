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
async def test_edit():
    # Generate a test token
    payload = {
        "id": "00000000-0000-0000-0000-000000000000",
        "email": "test@example.com",
        "role": "user",
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")

    uri = f"ws://localhost:8000/ws/chat?session_id=test_edit_sess&token={token}"
    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket")
        
        # 1. Send Edit Request
        msg = {
            "type": "user_message",
            "payload": {
                "session_id": "test_edit_sess",
                "message_id": "msg_edit_1",
                "text": "Update the risks section for Google to include concerns about AI regulation."
            }
        }
        print(f"> Sent: {msg}")
        await websocket.send(json.dumps(msg))

        # 2. Listen for responses
        while True:
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=60)
                print(f"< Received: {response}")
                
                data = json.loads(response)
                if data.get("type") == "plan_update":
                    print("\n✅ SUCCESS: Received plan update!")
                    break
                    
            except asyncio.TimeoutError:
                print("Timeout waiting for response")
                break
            except Exception as e:
                print(f"Error: {e}")
                break

if __name__ == "__main__":
    asyncio.run(test_edit())
