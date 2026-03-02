import os
import json
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'assets')

PROJECT_ROOT = os.path.dirname(BASE_DIR)
MOUSE_SETTINGS_FILE = os.path.join(PROJECT_ROOT, 'mouse_settings.json')
VOICE_SETTINGS_FILE = os.path.join(PROJECT_ROOT, 'voice_settings.json')

DEFAULT_MOUSE_SETTINGS = {
    "cursor": {"smooth_factor": 5, "click_threshold": 40, "pinch_threshold": 3},
    "gesture": {"detection_confidence": 0.7, "tracking_confidence": 0.7, "hold_time": 0.5},
    "control": {"box_size": 0.6, "box_from_top": 0.45, "volume_step": 0.05, "scroll_amount": 150, "acceleration_threshold": 1.5, "acceleration_multiplier": 2}
}

DEFAULT_VOICE_SETTINGS = {
    "voice": {"silence_threshold": 0.8, "model_size": "turbo"}
}

def load_json_file(filepath, defaults):
    if not os.path.exists(filepath):
        with open(filepath, 'w') as f:
            json.dump(defaults, f, indent=2)
        return defaults
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return defaults

def save_json_file(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

app.mount("/assets", StaticFiles(directory=STATIC_DIR), name="assets")

@app.get("/api/settings")
async def get_settings():
    mouse_settings = load_json_file(MOUSE_SETTINGS_FILE, DEFAULT_MOUSE_SETTINGS)
    voice_settings = load_json_file(VOICE_SETTINGS_FILE, DEFAULT_VOICE_SETTINGS)
    return {"mouse": mouse_settings, "voice": voice_settings}

@app.post("/api/settings")
async def update_settings(request: Request):
    data = await request.json()
    
    if "mouse" in data:
        save_json_file(MOUSE_SETTINGS_FILE, data["mouse"])
    if "voice" in data:
        save_json_file(VOICE_SETTINGS_FILE, data["voice"])
    
    return {"status": "success", "message": "Settings saved. Restart the application for changes to take effect."}

@app.post("/api/settings/reset")
async def reset_settings():
    save_json_file(MOUSE_SETTINGS_FILE, DEFAULT_MOUSE_SETTINGS)
    save_json_file(VOICE_SETTINGS_FILE, DEFAULT_VOICE_SETTINGS)
    return {"status": "success", "message": "Settings reset to defaults."}

@app.get("/")
async def root(request: Request):
    return FileResponse(os.path.join(TEMPLATES_DIR, 'index.html'))

@app.get("/{page}")
async def serve_page(page: str, request: Request):
    if page in ['index.html', 'hand.html', 'voice.html', 'settings.html']:
        return FileResponse(os.path.join(TEMPLATES_DIR, page))
    return FileResponse(os.path.join(TEMPLATES_DIR, 'index.html'))

if __name__ == '__main__':
    import uvicorn
    print("Starting server at http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)
