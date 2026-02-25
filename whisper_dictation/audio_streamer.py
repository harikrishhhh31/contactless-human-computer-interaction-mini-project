import pyaudio
import numpy as np
import threading
import queue
import time

class AudioStreamer:
    def __init__(self, sample_rate=16000, chunk_size=1024):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.audio_format = pyaudio.paInt16
        self.channels = 1
        self.pa = pyaudio.PyAudio()
        self.stream = None
        self.buffer = queue.Queue()
        self.is_running = False
        self.thread = None

    def _callback(self, in_data, frame_count, time_info, status):
        if status:
            print(f"Audio status: {status}")
        self.buffer.put(in_data)
        return (None, pyaudio.paContinue)

    def start(self):
        if self.is_running:
            return
        
        self.stream = self.pa.open(
            format=self.audio_format,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size,
            stream_callback=self._callback
        )
        
        self.is_running = True
        self.stream.start_stream()
        print("Audio stream started.")

    def stop(self):
        self.is_running = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.pa.terminate()
        print("Audio stream stopped.")

    def get_audio_chunk(self, duration_ms=None):
        """Returns accumulated audio as a numpy array."""
        chunks = []
        if duration_ms:
            # Approximate number of chunks for the duration
            needed_bytes = int(self.sample_rate * (duration_ms / 1000) * 2) # 2 bytes per sample (int16)
            current_bytes = 0
            while current_bytes < needed_bytes:
                try:
                    chunk = self.buffer.get(timeout=0.1)
                    chunks.append(chunk)
                    current_bytes += len(chunk)
                except queue.Empty:
                    break
        else:
            # Get everything currently in the buffer
            while not self.buffer.empty():
                chunks.append(self.buffer.get_nowait())
        
        if not chunks:
            return None
            
        audio_data = b"".join(chunks)
        return np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

if __name__ == "__main__":
    # Simple test
    streamer = AudioStreamer()
    streamer.start()
    try:
        print("Recording for 3 seconds...")
        time.sleep(3)
        audio = streamer.get_audio_chunk()
        if audio is not None:
            print(f"Captured {len(audio)} samples ({len(audio)/16000:.2f} seconds)")
    finally:
        streamer.stop()
