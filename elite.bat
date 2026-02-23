@echo off
TITLE ELITE SYSTEM
color 0A
cd /d "c:\Users\harikrishhhh\OneDrive\Attachments\Desktop\last mini project"
if exist venv\Scripts\activate (
    call venv\Scripts\activate
)
set PYTHONPATH=%PYTHONPATH%;%cd%
python elite_main.py
pause
