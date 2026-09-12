@echo off
cd /d "%~dp0\.."
echo Starting JewelMind AI Worker on http://127.0.0.1:8001 ...
C:\Users\usern\miniconda3\envs\tgpu\python.exe -m ai.workers.local_worker
