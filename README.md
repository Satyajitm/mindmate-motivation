# MindMate Voice Assistant

A conversational AI voice assistant that uses OpenAI's GPT model for natural language processing and provides voice-based interaction.

## Features

- Voice-to-text and text-to-speech capabilities
- Real-time conversation with AI
- Web-based interface
- Cross-platform compatibility

## Prerequisites

- Python 3.8+
- Node.js 14+ (for frontend development)
- OpenAI API key
- Microphone and speakers

## Local Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/mindmate-voice-assistant.git
cd mindmate-voice-assistant
```

### 2. Set Up Backend

1. Create and activate a virtual environment:
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate
   
   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install backend dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the `backend` directory:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

### 3. Set Up Frontend

The frontend files are already in the `frontend` directory. No additional setup is required for basic usage.

## Running the Application

### Start the Backend Server

From the `backend` directory:

```bash
uvicorn app:app --reload
```

The API will be available at `http://localhost:8000`

### Access the Web Interface

Open your web browser and navigate to:
```
http://localhost:8000
```

## Project Structure

```
mindmate-voice-assistant/
├── backend/               # Backend code
│   ├── app.py            # Main FastAPI application
│   ├── requirements.txt  # Python dependencies
│   └── .env             # Environment variables (create this file)
├── frontend/             # Frontend code
│   ├── static/           # Static files (JS, CSS)
│   └── templates/        # HTML templates
├── README.md            # This file
└── DEPLOYMENT.md        # Deployment instructions
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | Your OpenAI API key | Yes |
| `PORT` | Port to run the application | No (default: 8000) |

## Usage

1. Click and hold the microphone button to record your voice
2. Release the button to send the recording
3. Or type your message and press Enter or click Send
4. The assistant will respond with both text and speech

## Development

### Backend Development

- The backend is built with FastAPI
- API documentation is available at `/docs` when running locally
- The main WebSocket endpoint is `/ws`

### Frontend Development

- The frontend uses vanilla JavaScript
- All static files are served from the `frontend/static` directory
- Templates are in the `frontend/templates` directory

## Testing

To run the tests:

```bash
cd backend
pytest
```

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions to various cloud platforms.

## Troubleshooting

- **Microphone not working**: Ensure your browser has microphone permissions
- **Connection issues**: Check if the backend server is running
- **API errors**: Verify your OpenAI API key is correct and has sufficient credits

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/) and [WebSocket](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)
- Uses [OpenAI's GPT](https://openai.com/) for natural language processing
- Icons by [Font Awesome](https://fontawesome.com/)
