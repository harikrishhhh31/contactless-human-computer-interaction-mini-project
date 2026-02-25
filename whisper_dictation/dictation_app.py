import os
import sys
import time
import threading
from .audio_streamer import AudioStreamer
from .inference_engine import WhisperInference
from .streaming_manager import StreamingManager

class DictationApp:
    def __init__(self):
        self.streamer = AudioStreamer()
        self.engine = WhisperInference()
        self.manager = StreamingManager(self.engine)
        self.is_running = False
        self.last_audio_time = time.time()
        self.silence_threshold_s = 0.8 # VAD finalized after 800ms silence

    def run(self):
        self.is_running = True
        self.streamer.start()
        
        print("\n--- REAL-TIME WHISPER DICTATION ---")
        print("Speak now. Press Ctrl+C to stop.\n")
        
        try:
            while self.is_running:
                # 1. Capture audio
                audio = self.streamer.get_audio_chunk(duration_ms=500)
                
                if audio is not None and len(audio) > 0:
                    self.last_audio_time = time.time()
                    # 2. Process through manager
                    _, text = self.manager.process_audio(audio)
                    
                    # 3. Dynamic Console Output (Overwrite line)
                    sys.stdout.write("\r" + " " * 100 + "\r") # Clear line
                    sys.stdout.write(f"Dictation: {text}")
                    sys.stdout.flush()
                else:
                    # Check for silence to finalize
                    if time.time() - self.last_audio_time > self.silence_threshold_s:
                        if self.manager.finalize_segment():
                             sys.stdout.write("\n") # New line for finalized segment
                             sys.stdout.flush()
                             self.last_audio_time = time.time()
                
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\nStopping...")
        finally:
            self.streamer.stop()
            print("\nFinal Transcript:")
            print(self.manager.get_full_text())

if __name__ == "__main__":
    # Ensure we can import from the same package
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    app = DictationApp()
    app.run()
