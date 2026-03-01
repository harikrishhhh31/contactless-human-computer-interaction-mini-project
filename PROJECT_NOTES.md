# Project Notes - Heisenberg Tutorial Software

## Discussion Summary (Date: 2026-03-01)

### Mouse Gestures (mouse.bat → mouse_control.py)
- Index finger: Move cursor
- Index + Thumb: Left click
- Index + Middle: Right click  
- Index + Middle + Ring: Double click
- Four fingers: Scroll (up/down)
- Thumbs Up: Volume increase
- Thumbs Down: Volume decrease
- Cross-platform: Yes (Windows/macOS/Linux)

### Voice Commands (voice.bat → heisenberg.py)
- Web search, YouTube, Time/Date, Volume, Brightness
- Window controls (minimize/maximize/close/switch)
- Open/Close applications
- Dictation mode
- OS-Independent: ~13 commands
- Windows-only: ~1 command (close app by name)

---

## Planned Tasks / TODO

- [x] Create heisenberg_gui directory structure
- [x] Copy and rename gesture images to assets folder
- [x] Create main.py with pywebview
- [x] Create CSS style file (opencode white theme)
- [x] Create JavaScript navigation file
- [x] Create index.html (Welcome page)
- [x] Create hand.html (Hand gesture tutorial)
- [x] Create voice.html (Voice command tutorial)
- [x] Update requirements.txt with pywebview
- [x] Test the application

---

## Action Items

- [ ] None

---

## Project Structure

```
heisenberg_gui/
├── main_web.py                  # FastAPI server (hosts website)
├── main_gui.py                  # pywebview client (shows website)
├── heisenberg_gui.bat          # Launcher for main_gui.py
├── assets/
│   ├── css/style.css           # Styling
│   ├── js/app.js              # Navigation
│   └── images/                # 7 gesture images
│       ├── gesture-1-finger.png
│       ├── gesture-2-fingers.png
│       ├── gesture-3-fingers.png
│       ├── gesture-4-fingers.png
│       ├── gesture-5-fingers-scroll.png
│       ├── gesture-thumbs-up.png
│       └── gesture-thumbs-down.png
└── templates/
    ├── index.html             # Welcome page
    ├── hand.html              # Hand gesture tutorial
    └── voice.html             # Voice commands tutorial
```

---

## How to Run

### Terminal 1: Start Server
```bash
py main_web.py
```

### Terminal 2: Open GUI
```bash
py main_gui.py
```
OR double-click `heisenberg_gui.bat`

---

## Requirements

- pywebview
- fastapi
- uvicorn

---

## Design Style Requirements

- **Theme:** White theme 
- **Font:** Same font as opencode (system fonts: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto)
- **Tech Stack:** Modern HTML, CSS, JS
- **Background:** #ffffff (white)
- **Text Primary:** #1a1a1a (dark gray)
- **Accent Color:** #3b82f6 (blue)
- **Card Style:** Clean, minimal, card-based layout with subtle shadows
- **Border Radius:** 8px
- **Buttons:** Blue accent with hover effects

---

## Notes

1. No changes to existing mouse_control.py or heisenberg.py
2. Static tutorial only (no interactive testing from GUI)
3. User will provide gesture images (all 7 provided)
4. Opencode white theme applied
5. Voice commands displayed as text/cmd list (no images needed)
