import sounddevice as sd
import soundfile as sf
import numpy as np

def record_audio(seconds=3, filename="test_audio.wav"):
    print("Recording for", seconds, "seconds...")
    fs = 44100  # Sample rate
    recording = sd.rec(int(seconds * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()  # Wait until recording is finished
    sf.write(filename, recording, fs)
    print(f"Audio saved as {filename}")

if __name__ == "__main__":
    record_audio(5)  # Record for 5 seconds
