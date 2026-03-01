import os
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'assets')

app.mount("/assets", StaticFiles(directory=STATIC_DIR), name="assets")

@app.get("/")
async def root(request: Request):
    return FileResponse(os.path.join(TEMPLATES_DIR, 'index.html'))

@app.get("/{page}")
async def serve_page(page: str, request: Request):
    if page in ['index.html', 'hand.html', 'voice.html']:
        return FileResponse(os.path.join(TEMPLATES_DIR, page))
    return FileResponse(os.path.join(TEMPLATES_DIR, 'index.html'))

if __name__ == '__main__':
    import uvicorn
    print("Starting server at http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)
