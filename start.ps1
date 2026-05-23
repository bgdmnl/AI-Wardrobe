# Write-Host colored header
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Starting Wardrobe Tracker (PowerShell)" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Start the FastAPI backend in a new PowerShell window
Write-Host "[1/2] Launching FastAPI backend in a new window..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; .\venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

# Start the Next.js frontend in the current window
Write-Host "[2/2] Starting Next.js frontend in this window..." -ForegroundColor Green
cd frontend
npm run dev
