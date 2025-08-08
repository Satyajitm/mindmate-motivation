import asyncio
import websockets
import base64
import json

async def test_websocket_audio():
    uri = "ws://localhost:8000/ws"
    
    # Read a test audio file (you can record a short audio clip and save it as test_audio.wav)
    try:
        with open("test_audio.wav", "rb") as audio_file:
            audio_bytes = audio_file.read()
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
    except FileNotFoundError:
        print("Please create a test_audio.wav file in the same directory first.")
        return
    
    async with websockets.connect(uri) as websocket:
        # Send audio data
        await websocket.send(json.dumps({
            "type": "audio",
            "audio": audio_base64
        }))
        
        # Wait for response
        response = await websocket.recv()
        print(f"Received response: {response}")

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(test_websocket_audio())
