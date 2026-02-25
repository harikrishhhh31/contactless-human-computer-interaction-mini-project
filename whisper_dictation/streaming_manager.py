import time
import numpy as np
from .inference_engine import WhisperInference

class StreamingManager:
    def __init__(self, inference_engine, chunk_duration_s=3.0, overlap_duration_s=1.0):
        self.engine = inference_engine
        self.chunk_duration_s = chunk_duration_s
        self.overlap_duration_s = overlap_duration_s
        
        self.audio_buffer = np.array([], dtype=np.float32)
        self.sample_rate = 16000
        
        self.finalized_text = ""
        self.partial_text = ""
        
        # To avoid duplicate tokens across windows
        self.last_segment_end_time = 0.0

    def process_audio(self, new_audio):
        """
        Main logic for sliding window processing.
        Returns (is_finalized, current_display_text)
        """
        if new_audio is None or len(new_audio) == 0:
            return False, self.finalized_text + self.partial_text

        # Append new audio to our sliding window buffer
        self.audio_buffer = np.concatenate((self.audio_buffer, new_audio))
        
        # If we have enough audio for a chunk
        if len(self.audio_buffer) >= self.chunk_duration_s * self.sample_rate:
            # Perform inference
            segments, info = self.engine.transcribe(self.audio_buffer)
            
            # Simple deduplication and capitalization logic
            current_chunk_text = ""
            for s in segments:
                current_chunk_text += s['text'] + " "
            
            current_chunk_text = current_chunk_text.strip()
            
            # Update partial text
            self.partial_text = current_chunk_text
            
            # If VAD filter is active, the segments list will only contain speech.
            # If no segments are returned and our buffer is full-ish, we might consider it a pause.
            # For "real-time" feel, we emit partials immediately.
            
            # Keep overlap for next window
            overlap_samples = int(self.overlap_duration_s * self.sample_rate)
            if len(self.audio_buffer) > overlap_samples:
                 self.audio_buffer = self.audio_buffer[-overlap_samples:]
            
            return False, self.finalized_text + self.partial_text
            
        return False, self.finalized_text + self.partial_text

    def finalize_segment(self):
        """Called when silence is detected for a significant period."""
        if self.partial_text:
            text = self.partial_text.strip()
            if text:
                # Capitalize first letter of finalized segment
                if not self.finalized_text or self.finalized_text.endswith(('.', '!', '?')):
                    text = text[0].upper() + text[1:] if len(text) > 0 else text
                
                self.finalized_text += text + " "
                self.partial_text = ""
                # Clear buffer on finalization to start fresh
                self.audio_buffer = np.array([], dtype=np.float32)
                return True
        return False

    def get_full_text(self):
        return (self.finalized_text + self.partial_text).strip()
