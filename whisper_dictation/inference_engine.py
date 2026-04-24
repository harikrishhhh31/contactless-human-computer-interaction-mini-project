from faster_whisper import WhisperModel
import torch
import numpy as np
import os
import json

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', 'voice_settings.json')

DEFAULT_SETTINGS = {
    "voice": {
        "silence_threshold": 0.8,
        "model_size": "turbo"
    }
}

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(DEFAULT_SETTINGS, f, indent=2)
        print(f"Created default settings file: {SETTINGS_FILE}")
        return DEFAULT_SETTINGS
    
    try:
        with open(SETTINGS_FILE, 'r') as f:
            settings = json.load(f)
        print(f"Loaded settings from: {SETTINGS_FILE}")
        return settings
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading settings: {e}. Using defaults.")
        return DEFAULT_SETTINGS


class WhisperInference:
    def __init__(self, model_size=None, device="cuda", compute_type="float16"):
        if model_size is None:
            settings = load_settings()
            model_size = settings.get("voice", {}).get("model_size", "turbo")
        
        print(f"Loading Whisper model '{model_size}' on {device} ({compute_type})...")
        self.model = WhisperModel(
            model_size, 
            device=device, 
            compute_type=compute_type,
            download_root=None # Use default or specify if needed
        )
        print("Model loaded successfully.")
        
        # Fixed parameters as per requirements
        self.inference_params = {
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

    def transcribe(self, audio_array):
        """
        Transcribes the given audio array.
        audio_array: numpy array of float32 samples at 16000Hz.
        """
        segments, info = self.model.transcribe(
            audio_array,
            **self.inference_params
        )
        
        results = []
        for segment in segments:
            results.append({
                "text": segment.text.strip(),
                "start": segment.start,
                "end": segment.end,
                "no_speech_prob": segment.no_speech_prob
            })
            
        return results, info

if __name__ == "__main__":
    # Test loading
    try:
        engine = WhisperInference()
        print("Test: Engine initialized.")
    except Exception as e:
        print(f"Error initializing engine: {e}")
