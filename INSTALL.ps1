# ========================================
# NCCR Rehabilitation Platform
# Smart Installation Script
# ========================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "NCCR Rehabilitation Platform" -ForegroundColor Cyan
Write-Host "Smart Installation Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check Python installation
Write-Host "Step 1: Checking Python installation..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python is not installed!" -ForegroundColor Red
    Write-Host "Please install Python 3.9+ from python.org" -ForegroundColor Red
    Write-Host "Make sure to check 'Add Python to PATH' during installation" -ForegroundColor Red
    pause
    exit
}
Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
Write-Host ""

# Step 2: Create virtual environment
Write-Host "Step 2: Creating virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "✓ Virtual environment already exists" -ForegroundColor Green
} else {
    python -m venv venv
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Virtual environment created successfully" -ForegroundColor Green
    } else {
        Write-Host "ERROR: Failed to create virtual environment" -ForegroundColor Red
        pause
        exit
    }
}
Write-Host ""

# Step 3: Activate virtual environment (optional)
Write-Host "Step 3: Activating virtual environment..." -ForegroundColor Yellow
$venvPython = ".\venv\Scripts\python.exe"
if (-Not (Test-Path $venvPython)) {
    Write-Host "ERROR: Virtual environment python not found!" -ForegroundColor Red
    pause
    exit
}
Write-Host "✓ Virtual environment ready" -ForegroundColor Green
Write-Host ""

# Step 4: Ensure we're using the virtual environment's Python
Write-Host "Step 4: Installing dependencies from requirements.txt..." -ForegroundColor Yellow

# Make sure we're using the virtual environment's Python, not system-wide Python
$venvPython = ".\venv\Scripts\python.exe"

# Use the venv Python to upgrade pip and install dependencies
& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Pip upgraded successfully" -ForegroundColor Green
} else {
    Write-Host "ERROR: Failed to upgrade pip" -ForegroundColor Red
    pause
    exit
}

& $venvPython -m pip install -r requirements.txt
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ All dependencies installed successfully" -ForegroundColor Green
} else {
    Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
    pause
    exit
}
Write-Host ""

# Step 5: Check database and initialize if needed
Write-Host "Step 5: Checking database..." -ForegroundColor Yellow
if (Test-Path "nccr_rehabilitation.db") {
    Write-Host "✓ Database already exists - skipping initialization" -ForegroundColor Green
    Write-Host "  (Your existing patient data is safe)" -ForegroundColor Cyan
} else {
    Write-Host "! Database not found - initializing new database..." -ForegroundColor Yellow
    & $venvPython scripts/init_database.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Database initialized successfully" -ForegroundColor Green
    } else {
        Write-Host "ERROR: Failed to initialize database" -ForegroundColor Red
        pause
        exit
    }
}
Write-Host ""

# Step 6: Installation complete
Write-Host "========================================" -ForegroundColor Green
Write-Host "✓ Installation Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "To start the software:" -ForegroundColor Cyan
Write-Host "  1. Double-click START_SYSTEM.vbs" -ForegroundColor White
Write-Host "  2. Wait 10 seconds for browser to open" -ForegroundColor White
Write-Host "  3. Start using the platform!" -ForegroundColor White
Write-Host ""
Write-Host "To stop the software:" -ForegroundColor Cyan
Write-Host "  - Click the 'Shutdown System' button in the sidebar" -ForegroundColor White
Write-Host ""
Write-Host "Enjoy using NCCR Rehabilitation Platform!" -ForegroundColor Green
Write-Host ""
pause
