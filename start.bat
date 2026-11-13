@echo off
setlocal
cd /d "%~dp0" || exit /b 1
echo Starting MathForge...
echo Open http://127.0.0.1:8000
python backend\main.py
pause
