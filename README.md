# Contactless Human-Computer Interaction (Heisenberg)

A sophisticated system for controlling your computer using hand gestures and voice commands. Heisenberg provides a seamless, touchless interface for daily computing tasks by combining Computer Vision (MediaPipe/OpenCV) with high-accuracy Speech Recognition.

---

## 🚀 Quick Start (Recommended)

To set up and run the entire system with a single command:

```bash
python run.py
```

*This script will automatically create a virtual environment, install all required dependencies, and launch all services.*

---

## ✨ Key Features

### ✋ Hand Gesture Control
Master your mouse and system settings through intuitive hand movements:
- **Cursor Movement**: Move your index finger within the tracking box.
- **Right Click**: Raise both Index and Middle fingers.
- **Double Click**: Raise Index, Middle, and Ring fingers.
- **Volume Control**: 
  - **Thumbs Up**: Increase volume.
  - **Thumbs Down**: Decrease volume.
- **Scrolling**: Raise four fingers (Index, Middle, Ring, Pinky) and move your hand to the top or bottom half of the tracking box.

### 🎙️ Voice Assistant (Heisenberg)
A powerful command manager with smart context awareness:
- **Smart Window Control**: Point your cursor at any window and say **"maximize"**, **"minimize"**, or **"close"**. The assistant will act on the window under your mouse!
- **Application Control**: "open Notepad", "open Chrome", "close Chrome".
- **Web Search**: "google [query]", "search for [query]", "play [video] on YouTube".
- **Dictation Mode**: Say "kc mode" to start typing using your voice. Exit by saying "kc end".

### 🖼️ Desktop GUI Window
A native desktop window for easy access. If you close it, you can reopen it anytime by running:

```bash
python heisenberg_gui/main_gui.py
```

---

## 🛠️ Technology Stack
- **Languages**: Python
- **Vision**: OpenCV, MediaPipe
- **Voice**: Faster-Whisper, SpeechRecognition, pyttsx3
- **OS Interaction**: PyAutoGUI, pycaw, psutil, pywin32, xdotool (Linux)
- **Web**: FastAPI, pywebview

---

## 📥 Setup & Installation

### Prerequisites
- **Python**: 3.10 or higher
- **Hardware**: Webcam and Microphone
- **Linux Users**: Install `xdotool` (`sudo apt install xdotool`)
- **Windows Users**: Ensure `pywin32` is available.

---

## ▶️ How to Run

```bash
python run.py
```
---
## 📁 Project Structure

| File | Description |
|------|-------------|
| `run.py` | Auto setup & launcher - creates venv, installs deps, runs everything |
| `launcher_no_gui.py` | Master process manager - starts all 4 services |
| `mouse_ctl_no_gui.py` | Hand gesture control (no camera view) |
| `heisenberg.py` | Voice assistant |
| `heisenberg_gui/main_web.py` | Web server (FastAPI) |
| `heisenberg_gui/main_gui.py` | Desktop GUI window (pywebview) |
| `config/` | Settings folder (`mouse_settings.json`, `voice_settings.json`) |
| `utils/` | Command manager, system monitor, keyboard input |

---

## ⚙️ Settings

Configuration files are located in the `config/` folder:

| File | Purpose |
|------|-------------|
| `config/mouse_settings.json` | Mouse sensitivity, gesture thresholds, scroll speed |
| `config/voice_settings.json` | Voice model size, silence threshold |

Edit these files directly or use the web dashboard at http://127.0.0.1:8000

---

## ⚡ Performance Tips
- **Lighting**: Bright, even lighting significantly improves hand tracking accuracy.
- **Microphone**: For best voice recognition, use a dedicated microphone and speak clearly.
- **Internet**: An active connection is required for high-quality speech-to-text.
