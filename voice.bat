@echo on
cd /d "%~dp0"
call venv\Scripts\activate
python heisenberg.py
pause
