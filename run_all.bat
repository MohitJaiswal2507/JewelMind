@echo off
echo ========================================================
echo   Launching JewelMind Full Stack (3 Services)
echo ========================================================
start "JewelMind Backend (:8000)" cmd /k ".\backend\.venv\Scripts\python.exe -m uvicorn --app-dir backend app.main:app --host 127.0.0.1 --port 8000 --reload"
start "JewelMind AI Worker (:8001)" cmd /k "C:\Users\usern\miniconda3\envs\tgpu\python.exe -m ai.workers.local_worker"
start "JewelMind Frontend (:5173)" cmd /k "cd frontend && npm run dev"
echo All 3 services launched in separate windows!
