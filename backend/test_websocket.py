#!/usr/bin/env python3
"""Quick WebSocket test to verify agent responses."""

import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws/fd11c4bc-f5be-4897-a176-370e8c8d4679"

    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket")

            # Send test message
            message = {
                "type": "chat_message",
                "data": {"message": "AGENT STATUS RESET - Please respond now!"}
            }

            await websocket.send(json.dumps(message))
            print(f"Sent: {message}")

            # Wait for responses for 10 seconds
            try:
                for i in range(10):
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    print(f"Received: {response}")
            except asyncio.TimeoutError:
                print("No more responses after 10 seconds")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())