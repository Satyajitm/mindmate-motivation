import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws"
    try:
        async with websockets.connect(uri) as websocket:
            # Send a test message
            message = json.dumps({
                "type": "text",
                "text": "Hello, MindMate!"
            })
            print(f"Sending: {message}")
            await websocket.send(message)
            
            # Wait for the response
            response = await websocket.recv()
            print(f"Received: {response}")
            
    except Exception as e:
        print(f"Error: {e}")

# Run the test
if __name__ == "__main__":
    asyncio.run(test_websocket())
