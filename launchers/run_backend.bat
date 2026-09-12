@echo off
cd /d "%~dp0\.."
echo Starting JewelMind FastAPI Backend on http://127.0.0.1:8000 ...
.\backend\.venv\Scripts\python.exe -m uvicorn --app-dir backend app.main:app --host 127.0.0.1 --port 8000 --reload
