# MediSync Backend - Easy Startup Script
# This script will start your backend server with all necessary steps

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "   MediSync Backend - Starting Server" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check if in correct directory
Write-Host "[1/4] Checking directory..." -ForegroundColor Yellow
if (!(Test-Path ".\server.js")) {
    Write-Host "Error: Please run this script from the backend directory" -ForegroundColor Red
    exit 1
}
Write-Host "      ✅ Correct directory" -ForegroundColor Green

# Step 2: Check Node.js
Write-Host ""
Write-Host "[2/4] Checking Node.js..." -ForegroundColor Yellow
$nodeVersion = node --version
Write-Host "      ✅ Node.js version: $nodeVersion" -ForegroundColor Green

# Step 3: Seed database (optional - comment out if already seeded)
Write-Host ""
Write-Host "[3/4] Seeding database..." -ForegroundColor Yellow
Write-Host "      (You can skip this step by pressing Ctrl+C if already seeded)" -ForegroundColor Gray
Start-Sleep -Seconds 2
try {
    npm run seed 2>&1 | Out-Null
    Write-Host "      ✅ Database seeded successfully" -ForegroundColor Green
} catch {
    Write-Host "      ⚠️  Skipping seed (may be already seeded)" -ForegroundColor Yellow
}

# Step 4: Start server
Write-Host ""
Write-Host "[4/4] Starting server..." -ForegroundColor Yellow
Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "   Server Starting on Port 3000" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "📍 API Base URL: http://localhost:3000/api/v1" -ForegroundColor Cyan
Write-Host "💊 Health Check: http://localhost:3000/health" -ForegroundColor Cyan
Write-Host "📬 Import: MediSync_Postman_Collection.json to Postman" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Gray
Write-Host ""

npm start
