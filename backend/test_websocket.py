
import asyncio
import websockets

async def test_websocket():
    uri = "ws://localhost:8000/ws"
    try:
        async with websockets.connect(uri) as websocket:
            print(f"Connected to {uri}")
            # You can send a message and receive a response here if needed
            # await websocket.send("Hello, server!")
            # response = await websocket.recv()
            # print(f"Received from server: {response}")
    except Exception as e:
        print(f"Failed to connect to {uri}: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())
