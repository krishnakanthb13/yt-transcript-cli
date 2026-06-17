@echo off
REM ytt.bat — Windows launcher for ytt.py. Ensures deps, then passes all args through.
REM Usage:  ytt https://youtu.be/VIDEOID --format srt --out "C:\My Transcripts"
REM         ytt              (prompts for a URL/ID and saves into this folder)
setlocal

python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not on PATH. Get it from https://python.org
    pause
    exit /b 1
)

python -c "import youtube_transcript_api" 2>nul || (
    echo Installing youtube-transcript-api ...
    pip install youtube-transcript-api
)
python -c "import pyperclip" 2>nul || (
    echo Installing pyperclip ^(clipboard support^) ...
    pip install pyperclip
)

REM Run ytt.py from this script's own folder and forward every argument.
python "%~dp0ytt.py" %*
set "code=%errorlevel%"

REM Pause only when double-clicked (no arguments) so the window stays readable.
if "%~1"=="" pause
exit /b %code%
