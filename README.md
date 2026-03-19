# Contactless Human-Computer Interaction (Heisenberg)

A sophisticated system for controlling your Windows PC using hand gestures and voice commands. This project combines computer vision (MediaPipe/OpenCV) and speech recognition to provide a seamless, touchless interface for daily computing tasks.

## Key Features

###  Hand Gesture Control
Master your mouse and system settings through intuitive hand movements:
- **Cursor Movement**: Move your index finger within the tracking box.
- **Right Click**: Raise both Index and Middle fingers.
- **Double Click**: Raise Index, Middle, and Ring fingers.
- **Volume Control**: 
  - **Thumbs Up**: Increase volume.
  - **Thumbs Down**: Decrease volume.
- **Scrolling**: Raise four fingers (Index, Middle, Ring, Pinky) and move the hand to the top or bottom half of the tracking box.

###  Voice Assistant (Heisenberg)
A powerful voice-controlled manager for your applications and information:
- **Application Control**: "open Notepad", "open Chrome", "close Chrome".
- **Web Search**: "google [query]", "search for [query]", "play [video] on YouTube".
- **System Commands**: "maximize window", "minimize window", "switch window", "what's the time", "what's the date".
- **Dictation Mode**: Say "kc mode" to start typing using your voice. Exit by saying "kc end".

## Technology Stack
- **Languages**: Python
- **Vision**: OpenCV, MediaPipe
- **Voice**: SpeechRecognition, pyttsx3, PyAudio
- **OS Interaction**: PyAutoGUI, pycaw, psutil, pywin32, WMI

##  Setup & Installation

### Prerequisites
- Windows OS
- Python 3.10 or higher
- Webcam and Microphone

### Installation
1. Clone the repository to your local machine.
2. Create and activate a virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```
3. Install the required dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

##  How to Run

The project includes batch files for easy execution:

- **Hand Control**: Run `mouse.bat` or execute `python mouse_control.py`.
- **Voice Assistant**: Run `voice.bat` or execute `python heisenberg.py`.

### Tips for Best Performance
- **Lighting**: Ensure your hand is well-lit for accurate tracking.
- **Background**: A neutral background improves gesture recognition.
- **Voice**: Speak clearly; the assistant uses Google's speech recognition engine (requires internet connection).

##  Project Structure
- `mouse_control.py`: The main engine for hand tracking and mouse emulation.
- `heisenberg.py`: The entry point for the voice assistant.
- `utils/commandManager.py`: Logic for processing voice commands and system interactions.
- `utils/keyboardInput.py`: Handles typing and dictation functionality.
- `utils/systemMonitor.py`: Provides system-level information.
