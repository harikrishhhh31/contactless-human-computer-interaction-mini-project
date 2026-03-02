import pyttsx3
import pyaudio
import numpy as np
import torch
from faster_whisper import WhisperModel

from utils.commandManager import CommandManager


class VoiceAssistant(CommandManager):
    
    def __init__(self):
        self.engine = pyttsx3.init()
        self.setup_voice()
        self.setup_whisper()
        self.setup_audio()
        
    def setup_voice(self):
        voices = self.engine.getProperty('voices')
        self.engine.setProperty('voice', voices[0].id)
        self.engine.setProperty('rate', 175)
        self.engine.setProperty('volume', 0.9)
    
    def setup_whisper(self):
        if torch.cuda.is_available():
            device = "cuda"
            compute_type = "float16"
            print("Using CUDA for Whisper inference")
        else:
            device = "cpu"
            compute_type = "int8"
            print("Using CPU for Whisper inference")
        
        self.whisper_model = WhisperModel("turbo", device=device, compute_type=compute_type)
        self.transcribe_params = {
            "beam_size": 1,
            "best_of": 1,
            "temperature": 0,
            "condition_on_previous_text": False,
            "language": "en",
            "task": "transcribe",
            "vad_filter": True,
            "vad_parameters": dict(
                min_silence_duration_ms=300,
                speech_pad_ms=150,
                threshold=0.5
            )
        }
    
    def setup_audio(self):
        self.audio = pyaudio.PyAudio()
        self.sample_rate = 16000
        self.chunk_size = 1024
        self.stream = None
        
    def start_audio_stream(self):
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size
        )
        
    def stop_audio_stream(self):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
    
    def speak(self, text):
        print(f"Assistant: {text}")
        self.engine.say(text)
        self.engine.runAndWait()
    
    def listen(self):
        if not self.stream:
            self.start_audio_stream()
            
        print("Listening...")
        frames = []
        silence_count = 0
        max_silence = 30
        
        while silence_count < max_silence:
            try:
                data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                frames.append(data)
                
                audio_np = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                if np.abs(audio_np).mean() < 0.01:
                    silence_count += 1
                else:
                    silence_count = 0
            except Exception as e:
                print(f"Audio read error: {e}")
                break
        
        if not frames:
            return ""
            
        audio_data = b"".join(frames)
        audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
        
        if len(audio_array) < self.sample_rate * 0.3:
            return ""
        
        segments, info = self.whisper_model.transcribe(audio_array, **self.transcribe_params)
        
        text = ""
        for segment in segments:
            text += segment.text
        
        text = text.strip()
        if text:
            print(f"You said: {text}")
        return text.lower()
    
    def run(self):
        self.list_available_software()
        self.speak("Voice assistant activated. How can I help you?")
        
        while True:
            command = self.listen()
            if command:
                if not self.process_command(command):
                    break
        
        self.stop_audio_stream()
        self.audio.terminate()

if __name__ == "__main__":
    assistant = VoiceAssistant()
    assistant.run()
