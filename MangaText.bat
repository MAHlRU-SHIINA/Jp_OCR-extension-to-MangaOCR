@echo off
ECHO Starting Manga OCR Tool...

REM Change directory to the script's location
cd /d "%~dp0"

REM Activate the virtual environment
call "venv\Scripts\activate.bat"

REM Run the Python script
python JP_OCR.py