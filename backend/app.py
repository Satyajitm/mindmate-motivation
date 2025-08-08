import os
import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse
import openai
from dotenv import load_dotenv
import base64
import tempfile
import os
import uvicorn
from pathlib import Path
from typing import Optional
from pydantic import BaseModel
import json
from gtts import gTTS

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI()

# Get the directory of the current file
BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / 'frontend'

# Configure static files
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR / 'static')), name="static")

# Templates
templates = Jinja2Templates(directory=str(FRONTEND_DIR / 'templates'))

# CORS middleware to allow frontend-backend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=[*"*"],
    allow_headers=[*"*"],
)

# Global variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable not set")

openai.api_key = OPENAI_API_KEY

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

manager = ConnectionManager()

# Text-to-speech function
async def text_to_speech(text: str):
    """Convert text to speech and return base64 encoded audio"""
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as fp:
            tts = gTTS(text=text, lang='en')
            tts.save(fp.name)
            
            # Read the file and convert to base64
            with open(fp.name, 'rb') as audio_file:
                audio_data = audio_file.read()
                return base64.b64encode(audio_data).decode('utf-8')
    except Exception as e:
        print(f"Error in text_to_speech: {str(e)}")
        return None

# Process text with OpenAI
async def process_text_with_openai(text: str):
    """Process text using OpenAI's API with a friendly, human-like personality"""
    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system", 
                    "content": """You are a friendly, supportive, and empathetic friend named MindMate. 
                    Your personality is warm, understanding, and always positive. You never mention being an AI or chatbot. 
                    Instead, you're just a good friend who's always there to listen and help. 
                    Keep your responses natural, casual, and conversational. Use casual language, occasional emojis, 
                    and show genuine interest in the conversation. Be concise but thoughtful in your responses.
                    
                    Guidelines:
                    - Never mention you're an AI, assistant, or bot
                    - Don't discuss your system settings or how you work
                    - Keep responses friendly and natural, like a close friend
                    - Show empathy and understanding
                    - Use casual language and occasional emojis when appropriate
                    - Be concise but thoughtful in your responses"""
                },
                {"role": "user", "content": text}
            ],
            temperature=0.8,  # Slightly more creative responses
            max_tokens=200    # Keep responses concise
        )
        return response.choices[0].message['content']
    except Exception as e:
        print(f"Error in process_text_with_openai: {str(e)}")
        return "Hmm, I'm having trouble thinking of a response right now. Could we try that again?"

# WebSocket endpoint for real-time communication
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Receive data from the client
            data = await websocket.receive_text()
            data = json.loads(data)
            
            if data.get("type") == "audio":
                # Process audio data using OpenAI's Whisper API
                audio_base64 = data.get("audio")
                if not audio_base64:
                    await websocket.send_json({
                        "type": "error",
                        "text": "No audio data received"
                    })
                    continue
                
                try:
                    # Save the audio to a temporary file
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as audio_file:
                        audio_file.write(base64.b64decode(audio_base64))
                        audio_path = audio_file.name
                    
                    # Transcribe audio using OpenAI's Whisper API
                    with open(audio_path, "rb") as audio_file:
                        transcript = await openai.Audio.atranscribe(
                            "whisper-1",
                            audio_file
                        )
                    
                    user_text = transcript["text"]
                    
                    # Get response from OpenAI
                    response_text = await process_text_with_openai(user_text)
                    
                    # Convert response to speech
                    audio_data = await text_to_speech(response_text)
                    
                    # Send the response back to the client
                    await websocket.send_json({
                        "type": "audio_response",
                        "text": response_text,
                        "audio": audio_data
                    })
                    
                except Exception as e:
                    print(f"Error processing audio: {str(e)}")
                    await websocket.send_json({
                        "type": "error",
                        "text": f"Error processing audio: {str(e)}"
                    })
                
            elif data.get("type") == "text":
                # Process text input
                user_text = data.get("text", "")
                
                # Get response from OpenAI
                response_text = await process_text_with_openai(user_text)
                
                # Convert response to speech
                audio_data = await text_to_speech(response_text)
                
                # Send the response back to the client
                await websocket.send_json({
                    "type": "text_response",
                    "text": response_text,
                    "audio": audio_data
                })
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
        await websocket.close()

# API endpoint for text-based interaction
class TextRequest(BaseModel):
    text: str

@app.post("/api/chat")
async def chat(request: TextRequest):
    """Handle text-based chat requests"""
    try:
        response_text = await process_text_with_openai(request.text)
        return {"response": response_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Serve the main page
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Serve static files
@app.get("/static/{file_path:path}")
async def serve_static(file_path: str):
    static_file = FRONTEND_DIR / 'static' / file_path
    if static_file.exists():
        return FileResponse(static_file)
    raise HTTPException(status_code=404, detail="File not found")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "MindMate Voice Assistant is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
