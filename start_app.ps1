# NCCR Rehabilitation Platform - Quick Start Script
# This script starts both the backend API and Streamlit UI

Write-Host "🏥 NCCR Rehabilitation Platform" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (Test-Path "venv\Scripts\activate.ps1") {
    Write-Host "✅ Activating virtual environment..." -ForegroundColor Green
    & "venv\Scripts\activate.ps1"
} else {
    Write-Host "⚠️  No virtual environment found. Using system Python..." -ForegroundColor Yellow
}

# Start FastAPI backend in background
Write-Host ""
Write-Host "🚀 Starting FastAPI backend on http://localhost:8000..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; python main.py"

# Wait a moment for backend to start
Write-Host "⏳ Waiting for backend to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Start Streamlit UI
Write-Host ""
Write-Host "🌐 Starting Streamlit UI..." -ForegroundColor Green
Write-Host "💡 The browser will open automatically" -ForegroundColor Cyan
Write-Host ""
Write-Host "📖 Access Points:" -ForegroundColor Cyan
Write-Host "   - Streamlit UI: Will open in browser" -ForegroundColor White
Write-Host "   - API Backend: http://localhost:8000" -ForegroundColor White
Write-Host "   - API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "⚠️  Press Ctrl+C to stop the UI" -ForegroundColor Yellow
Write-Host "⚠️  Close the backend PowerShell window separately" -ForegroundColor Yellow
Write-Host ""

streamlit run app_streamlit.py
