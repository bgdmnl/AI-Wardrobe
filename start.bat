@echo off
echo ==========================================
echo   Starting Wardrobe Tracker
echo ==========================================

echo [1/2] Launching FastAPI backend in a new window...
start cmd /k "cd backend && venv\Scripts\activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

echo [2/2] Starting Next.js frontend here...
cd frontend
npm run dev
