// DOM Elements
const recordButton = document.getElementById('recordButton');
const userInput = document.getElementById('userInput');
const sendButton = document.getElementById('sendButton');
const chatMessages = document.getElementById('chat-messages');
const statusElement = document.getElementById('status');
const audioPlayer = document.getElementById('audioPlayer');

// State
let socket;
let mediaRecorder;
let audioChunks = [];
let isRecording = false;

// Initialize
function init() {
    setupEventListeners();
    connectWebSocket();
}

// Event Listeners
function setupEventListeners() {
    // Record button
    recordButton.addEventListener('mousedown', startRecording);
    recordButton.addEventListener('touchstart', startRecording);
    recordButton.addEventListener('mouseup', stopRecording);
    recordButton.addEventListener('touchend', stopRecording);
    
    // Text input
    sendButton.addEventListener('click', sendTextMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendTextMessage();
    });
}

// WebSocket Connection
function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
    const wsUrl = `wss://your-render-app-url.onrender.com/ws`;
    
    socket = new WebSocket(wsUrl);
    
    socket.onopen = () => updateStatus('Connected');
    socket.onclose = () => {
        updateStatus('Disconnected. Reconnecting...', 'error');
        setTimeout(connectWebSocket, 3000);
    };
    socket.onmessage = (e) => handleServerMessage(JSON.parse(e.data));
    socket.onerror = (e) => {
        console.error('WebSocket error:', e);
        updateStatus('Connection error', 'error');
    };
}

// Handle Server Messages
function handleServerMessage(data) {
    if (data.text) {
        addMessage(data.text, 'bot');
        if (data.audio) playAudio(data.audio);
    }
}

// Audio Recording
async function startRecording(e) {
    e.preventDefault();
    if (isRecording) return;
    
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];
        
        mediaRecorder.ondataavailable = (e) => e.data.size > 0 && audioChunks.push(e.data);
        mediaRecorder.onstop = sendAudioMessage;
        
        mediaRecorder.start();
        isRecording = true;
        recordButton.classList.add('recording');
        updateStatus('Recording...', 'recording');
    } catch (error) {
        console.error('Microphone error:', error);
        updateStatus('Microphone access denied', 'error');
    }
}

function stopRecording() {
    if (!isRecording) return;
    mediaRecorder?.stop();
    mediaRecorder?.stream.getTracks().forEach(track => track.stop());
    isRecording = false;
    recordButton.classList.remove('recording');
    updateStatus('Processing...');
}

// Message Handling
function sendAudioMessage() {
    if (audioChunks.length === 0) return;
    
    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
    const reader = new FileReader();
    
    reader.onload = () => {
        const base64Audio = reader.result.split(',')[1];
        socket?.send(JSON.stringify({ type: 'audio', audio: base64Audio }));
        addMessage('🎤 [Voice message]', 'user');
    };
    
    reader.readAsDataURL(audioBlob);
}

function sendTextMessage() {
    const message = userInput.value.trim();
    if (!message || !socket || socket.readyState !== WebSocket.OPEN) return;
    
    addMessage(message, 'user');
    socket.send(JSON.stringify({ type: 'text', text: message }));
    userInput.value = '';
}

// UI Helpers
function addMessage(text, sender) {
    const message = document.createElement('div');
    message.className = `message ${sender}`;
    message.innerHTML = `<div class="message-content">${text}</div>`;
    chatMessages.appendChild(message);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function playAudio(base64Audio) {
    audioPlayer.src = `data:audio/mp3;base64,${base64Audio}`;
    audioPlayer.play().catch(e => console.error('Audio play failed:', e));
}

function updateStatus(message, type = '') {
    statusElement.textContent = message;
    statusElement.className = `status ${type}`;
}

// Initialize the app
init();
