import os
import sys
import time
import signal
import threading
import tempfile
import subprocess
import atexit
from dotenv import load_dotenv
import speech_recognition as sr
from gtts import gTTS
import soundfile as sf
import sounddevice as sd
import openai

# Global flag for graceful shutdown
shutdown_flag = False

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global shutdown_flag
    print("\n🛑 Shutdown signal received. Cleaning up...")
    shutdown_flag = True

# Register signal handlers for graceful shutdown
signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # System shutdown

# Ensure cleanup on normal exit
atexit.register(lambda: signal_handler(None, None))

# Load environment variables from .env file
load_dotenv()

# Initialize speech recognition and text-to-speech engines
recognizer = sr.Recognizer()

# Get OpenAI API key from environment variable
openai.api_key = os.getenv('OPENAI_API_KEY')
if not openai.api_key:
    raise ValueError("OpenAI API key not found in environment variables. Please set the OPENAI_API_KEY in your .env file.")

def initialize_tts():
    """Initialize the text-to-speech engine with default settings"""
    try:
        print("✅ Text-to-speech engine initialized")
        return True
    except Exception as e:
        print(f"❌ Error initializing TTS: {str(e)}")
        return False

def get_audio_input(source, recognizer, timeout=5, phrase_time_limit=5):
    """Helper function to get audio input with error handling
    
    Args:
        source: Audio source (microphone)
        recognizer: Speech recognizer instance
        timeout (int): Timeout in seconds for listening
        phrase_time_limit (int): Maximum phrase length in seconds
        
    Returns:
        AudioData or None: Captured audio or None if failed
    """
    try:
        print("🔊 Adjusting for ambient noise...")
        start_time = time.time()
        recognizer.adjust_for_ambient_noise(source, duration=min(1.0, timeout/2))
        print(f"✅ Adjusted for ambient noise in {time.time() - start_time:.1f}s")
        
        print("🎤 Listening...")
        audio = recognizer.listen(
            source,
            timeout=timeout,
            phrase_time_limit=min(phrase_time_limit, 15)  # Max 15 seconds
        )
        print("✅ Audio captured")
        return audio
        
    except sr.WaitTimeoutError:
        print("⏰ No speech detected within the time limit")
        return None
    except Exception as e:
        print(f"❌ Error capturing audio: {str(e)}")
        return None

def listen_to_speech(max_attempts=3, initial_timeout=5):
    """Listen to user's speech and convert to text with improved error handling
    
    Args:
        max_attempts (int): Maximum number of listening attempts
        initial_timeout (int): Initial timeout in seconds for listening
        
    Returns:
        str: Recognized text or None if unsuccessful
    """
    if not isinstance(max_attempts, int) or max_attempts < 1:
        max_attempts = 3
    if not isinstance(initial_timeout, (int, float)) or initial_timeout <= 0:
        initial_timeout = 5
        
    attempts = 0
    timeout = initial_timeout
    
    while attempts < max_attempts and not shutdown_flag:
        try:
            # Initialize recognizer with fresh settings each attempt
            recognizer = sr.Recognizer()
            recognizer.dynamic_energy_threshold = True
            recognizer.pause_threshold = 0.8
            recognizer.energy_threshold = 3000  # Slightly lower for better sensitivity
            recognizer.operation_timeout = timeout + 2  # Slightly longer than listen timeout
            
            with sr.Microphone() as source:
                if attempts > 0:
                    attempt_msg = f"Attempt {attempts + 1}/{max_attempts}..."
                    print(f"\n🔄 {attempt_msg}")
                    speak_text("I didn't catch that. Please try again.")
                
                # Get audio input
                audio = get_audio_input(source, recognizer, timeout=timeout)
                if audio is None:
                    attempts += 1
                    timeout = min(timeout * 1.5, 10)  # Increase timeout up to 10s
                    continue
                
                try:
                    # Convert speech to text
                    print("🔄 Converting speech to text...")
                    start_time = time.time()
                    text = recognizer.recognize_google(audio)
                    print(f"✅ Speech recognized in {time.time() - start_time:.1f}s")
                    
                    if text and text.strip():
                        print(f"\n🗣️ You said: {text}")
                        return text.strip()
                    
                    print("❌ Empty speech detected")
                    
                except sr.UnknownValueError:
                    print("😕 Could not understand audio")
                except sr.RequestError as e:
                    print(f"❌ Speech recognition service error: {str(e)}")
                    return None
                except Exception as e:
                    print(f"❌ Error processing speech: {str(e)}")
                
        except OSError as e:
            print(f"❌ Microphone error: {str(e)}")
            if "No Default Input Device Available" in str(e):
                return None
        except Exception as e:
            print(f"❌ Unexpected error in listen_to_speech: {str(e)}")
        
        attempts += 1
        if attempts < max_attempts:
            wait_time = min(timeout, 5)  # Max 5 seconds wait between attempts
            print(f"⏳ Waiting {wait_time} seconds before next attempt...")
            time.sleep(wait_time)
            timeout = min(timeout * 1.5, 15)  # Exponential backoff, max 15s
    
    print("❌ Maximum speech recognition attempts reached")
    return None

def cleanup_temp_file(file_path):
    """Safely remove a temporary file if it exists"""
    try:
        if file_path and os.path.exists(file_path):
            os.unlink(file_path)
    except Exception as e:
        print(f"⚠️  Warning: Could not remove temporary file {file_path}: {str(e)}")

def sanitize_text(text, max_length=500):
    """Sanitize and truncate text for TTS
    
    Args:
        text (str): Input text to sanitize
        max_length (int): Maximum allowed length of text
        
    Returns:
        str: Sanitized and truncated text
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Remove any non-printable characters and control characters
    sanitized = "".join(c for c in text if c.isprintable() or c.isspace())
    sanitized = sanitized.strip()
    
    # Truncate if too long
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rsplit(' ', 1)[0] + "..."
    
    return sanitized

def speak_text(text, rate=1.0, volume=1.0):
    """Convert text to speech using gTTS with improved error handling
    
    Args:
        text (str): The text to be spoken
        rate (float): Speech rate
        volume (float): Speech volume
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Validate and sanitize input
    sanitized_text = sanitize_text(text)
    if not sanitized_text:
        print("⚠️  No valid text to speak")
        return False
    
    # Validate rate and volume
    rate = max(0.5, min(2.0, float(rate)))  # Clamp between 0.5 and 2.0
    volume = max(0.0, min(1.0, float(volume)))  # Clamp between 0.0 and 1.0
    
    temp_file = None
    success = False
    
    try:
        # Create a temporary file with a unique name
        temp_file = tempfile.mktemp(suffix='.mp3')
        
        # Convert text to speech
        print(f"🔊 Converting text to speech (length: {len(sanitized_text)} chars)...")
        tts = gTTS(
            text=sanitized_text,
            lang='en',
            slow=False,
            lang_check=True
        )
        
        # Save to temp file
        tts.save(temp_file)
        
        if not os.path.exists(temp_file) or os.path.getsize(temp_file) == 0:
            raise IOError("Failed to generate speech file")
        
        # Load audio file
        print(f"▶️  Playing audio...")
        data, fs = sf.read(temp_file)
        
        # Apply volume
        if volume != 1.0:
            data = data * volume
        
        # Play audio with error handling
        try:
            # Try playing with sounddevice first
            sd.play(data, fs * rate)
            sd.wait()
            success = True
        except Exception as e:
            print(f"⚠️  Error playing with sounddevice: {str(e)}")
            print("⚠️  Falling back to system default player...")
            
            # Fallback: Use system default player
            try:
                if sys.platform == 'win32':
                    os.startfile(temp_file)
                elif sys.platform == 'darwin':  # macOS
                    subprocess.run(['afplay', temp_file], check=True)
                else:  # Linux and others
                    subprocess.run(['xdg-open', temp_file], check=True)
                success = True
            except Exception as fallback_e:
                print(f"❌ Error with fallback player: {str(fallback_e)}")
                # Last resort: just print the text
                print(f"📢 {sanitized_text}")
    
    except Exception as e:
        print(f"❌ Error in text-to-speech: {str(e)}")
        # Fall back to printing the text if TTS fails
        print(f"📢 {sanitized_text}")
    
    finally:
        # Clean up the temporary file
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
            except Exception as e:
                print(f"⚠️  Could not delete temporary file: {str(e)}")
    
    return success

def validate_input(text, max_length=1000):
    """Validate and sanitize user input
    
    Args:
        text (str): Input text to validate
        max_length (int): Maximum allowed length of text
        
    Returns:
        tuple: (is_valid, result) where result is either the sanitized text or an error message
    """
    if not text or not isinstance(text, str):
        return False, "I didn't catch that. Could you please repeat?"
        
    # Remove any potentially harmful characters
    text = text.strip()
    if not text:
        return False, "I didn't catch that. Could you please repeat?"
        
    if len(text) > max_length:
        return False, f"Your message is too long. Please keep it under {max_length} characters."
        
    return True, text

def process_text(text, max_retries=3, initial_delay=1):
    """Process the recognized text and generate a response with retry logic
    
    Args:
        text (str): The user's input text
        max_retries (int): Maximum number of retry attempts
        initial_delay (float): Initial delay between retries in seconds
        
    Returns:
        str: The assistant's response or an error message
    """
    # Validate input
    is_valid, result = validate_input(text)
    if not is_valid:
        return result
    
    text = result  # Use the sanitized text
    retry_count = 0
    delay = initial_delay
    
    while retry_count < max_retries and not shutdown_flag:
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": text}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            if not response.choices:
                raise ValueError("No response from the model")
                
            return response.choices[0].message['content'].strip()
            
        except openai.error.RateLimitError as e:
            retry_count += 1
            if retry_count >= max_retries:
                print(f"❌ Rate limit exceeded after {max_retries} attempts")
                return "I'm getting too many requests. Please try again later."
                
            print(f"⚠️  Rate limited, retrying in {delay} seconds... (Attempt {retry_count}/{max_retries})")
            time.sleep(delay)
            delay = min(delay * 2, 10)  # Exponential backoff, max 10s
            
        except openai.error.APIError as e:
            print(f"❌ API Error: {str(e)}")
            return "I'm having trouble connecting to the service. Please try again later."
            
        except Exception as e:
            print(f"❌ Unexpected error in process_text: {str(e)}")
            retry_count += 1
            if retry_count >= max_retries:
                return "I'm sorry, I encountered an error processing your request. Please try again later."
    
    return "I'm having trouble processing your request. Please try again later."

def check_microphone_available():
    """Check if a microphone is available for use"""
    try:
        with sr.Microphone() as source:
            print("✅ Microphone is available")
            return True
    except OSError as e:
        print(f"❌ No microphone found: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Error checking microphone: {str(e)}")
        return False

def main():
    """Main function to run the voice assistant with improved error handling"""
    print("\n" + "="*50)
    print("🎙️  Starting MindMate Voice Assistant")
    print("="*50 + "\n")
    
    # Check for required environment variables
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("Please create a .env file with your OpenAI API key")
        return
    
    # Check microphone availability
    if not check_microphone_available():
        print("\n❌ Please connect a microphone and try again.")
        return
    
    # Initialize TTS engine
    print("\n🔊 Initializing text-to-speech engine...")
    if not initialize_tts():
        print("❌ Failed to initialize TTS engine. Exiting...")
        return
    
    # Initial greeting
    print("\n" + "="*50)
    print("✨ MindMate is ready!")
    print("="*50 + "\n")
    
    speak_text("Hello! I'm your MindMate assistant. How can I help you today?")
    
    conversation_active = True
    consecutive_errors = 0
    MAX_CONSECUTIVE_ERRORS = 3
    
    while conversation_active and not shutdown_flag:
        try:
            # Listen for user input
            print("\n" + "-"*30)
            print("🎤 Listening... (Say 'goodbye' to exit)")
            user_input = listen_to_speech()
            
            # Check for shutdown flag between operations
            if shutdown_flag:
                break
            
            # Check if user wants to exit
            if user_input and any(exit_word in user_input.lower() for exit_word in ["exit", "quit", "bye", "goodbye"]):
                print("\n👋 User requested to exit")
                speak_text("Goodbye! Have a great day!")
                conversation_active = False
                break
            
            # Process and respond if we got valid input
            if user_input:
                print(f"\n🤖 Processing your request...")
                response = process_text(user_input)
                
                if shutdown_flag:
                    break
                    
                if response:
                    print(f"\n💬 Response: {response[:100]}..." if len(response) > 100 else f"💬 Response: {response}")
                    speak_text(response)
                else:
                    print("⚠️  No response generated")
                    speak_text("I'm sorry, I couldn't generate a response. Please try again.")
                
                consecutive_errors = 0  # Reset error counter on successful interaction
            else:
                print("⚠️  No valid input detected. Please try again.")
                speak_text("I didn't catch that. Could you please repeat?")
                consecutive_errors += 1
                
                # If we have too many consecutive errors, suggest exiting
                if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                    print(f"\n⚠️  Multiple consecutive errors detected. You might want to check your microphone or connection.")
                    speak_text("I'm having trouble understanding you. Please check your microphone and try again.")
                    consecutive_errors = 0  # Reset counter after warning
                
        except KeyboardInterrupt:
            print("\n🛑 Keyboard interrupt received. Shutting down...")
            speak_text("Goodbye!")
            conversation_active = False
            break
            
        except Exception as e:
            print(f"\n❌ An unexpected error occurred: {str(e)}")
            speak_text("I encountered an error. Let's try that again.")
            consecutive_errors += 1
            
            # If we have too many consecutive errors, exit to prevent infinite error loops
            if consecutive_errors > MAX_CONSECUTIVE_ERRORS * 2:
                print(f"\n❌ Too many errors. Shutting down for safety.")
                speak_text("I'm having too many issues. Please restart me.")
                conversation_active = False
                break
            
            # Add a small delay to prevent tight error loops
            time.sleep(1)
            continue
    
    print("\n" + "="*50)
    print("👋 MindMate is shutting down. Goodbye!")
    print("="*50)


if __name__ == "__main__":
    main()
