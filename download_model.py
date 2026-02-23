import requests
import os
import sys

# URL for Mistral-Nemo 12B (approx 10GB for Q6_K quality)
# High intelligence, fits the "Engineering Student" requirement perfectly.
MODEL_URL = "https://huggingface.co/bartowski/Mistral-Nemo-12B-Instruct-v1-GGUF/resolve/main/Mistral-Nemo-12B-Instruct-v1-Q6_K.gguf"
DEST_FOLDER = "models"
DEST_FILE = "heisenberg_neural_core.gguf"
FULL_PATH = os.path.join(DEST_FOLDER, DEST_FILE)

def download_model():
    if not os.path.exists(DEST_FOLDER):
        os.makedirs(DEST_FOLDER)
        
    print(f"🚀 INITIATING DOWNLOAD: {DEST_FILE}")
    print(f"🔗 Source: {MODEL_URL}")
    print("⚠️  Size: ~10 GB. This may take a while depending on your WiFi.")
    print("----------------------------------------------------------------")

    response = requests.get(MODEL_URL, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024 # 1 Kibibyte
    
    with open(FULL_PATH, 'wb') as f:
        downloaded = 0
        for data in response.iter_content(block_size):
            downloaded += len(data)
            f.write(data)
            
            # Progress Bar logic
            done = int(50 * downloaded / total_size)
            sys.stdout.write(f"\r[{'=' * done}{' ' * (50-done)}] {downloaded//(1024*1024)} MB / {total_size//(1024*1024)} MB")
            sys.stdout.flush()
            
    print("\n\n✅ DOWNLOAD COMPLETE.")
    print(f"🧠 Neural Core installed at: {FULL_PATH}")
    print("Run 'run_elite_system.bat' to activate Heisenberg.")

if __name__ == "__main__":
    download_model()
