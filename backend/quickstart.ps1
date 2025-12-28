# Quick Start Script for Student Information Service Platform Backend

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "Student Information Service Platform Setup" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "[1/5] Checking Python version..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python not found. Please install Python 3.8 or higher." -ForegroundColor Red
    exit 1
}
Write-Host "✓ Found: $pythonVersion" -ForegroundColor Green
Write-Host ""

# Install dependencies
Write-Host "[2/5] Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install dependencies." -ForegroundColor Red
    exit 1
}
Write-Host "✓ Dependencies installed successfully" -ForegroundColor Green
Write-Host ""

# Check if .env exists
Write-Host "[3/5] Checking configuration..." -ForegroundColor Yellow
if (!(Test-Path ".env")) {
    Write-Host "! .env file not found. Creating from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "✓ Created .env file" -ForegroundColor Green
    Write-Host "⚠ IMPORTANT: Please edit .env and configure your database connection!" -ForegroundColor Magenta
} else {
    Write-Host "✓ .env file exists" -ForegroundColor Green
}
Write-Host ""

# Initialize database
Write-Host "[4/5] Initializing database..." -ForegroundColor Yellow
Write-Host "This will create tables and seed test data." -ForegroundColor Gray
python init_db.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Database initialization failed. Please check your DATABASE_URL in .env" -ForegroundColor Red
    Write-Host "Make sure MySQL is running and the database exists." -ForegroundColor Yellow
    exit 1
}
Write-Host "✓ Database initialized successfully" -ForegroundColor Green
Write-Host ""

# All done
Write-Host "[5/5] Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "1. Review and edit .env file if needed" -ForegroundColor White
Write-Host "2. Start the server with: python main.py" -ForegroundColor White
Write-Host "3. Access API docs at: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "Test Accounts:" -ForegroundColor Yellow
Write-Host "  Admin:    username=admin, password=admin123" -ForegroundColor Gray
Write-Host "  Student:  username=student001, password=password123" -ForegroundColor Gray
Write-Host ""
