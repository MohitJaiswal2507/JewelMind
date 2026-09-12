@echo off
cd /d "%~dp0\.."
echo Starting JewelMind Frontend on http://localhost:5173 ...
cd frontend && npm run dev
