@echo on
cd /d "%~dp0"
call venv\Scripts\activate
python mouse_control.py
pause
