# Quick Start Script for Fixed Orchestration System
# This script starts the server and helps you test the complete orchestration

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  🏥 MediSync Orchestration - FIXED!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Kill any existing server
Write-Host "🔄 Step 1: Checking for existing server..." -ForegroundColor Yellow
$port = 3000
$proc = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
if ($proc) {
    Stop-Process -Id $proc -Force
    Write-Host "   ✅ Stopped existing server on port $port" -ForegroundColor Green
    Start-Sleep -Seconds 2
} else {
    Write-Host "   ℹ️  No server running on port $port" -ForegroundColor Gray
}

Write-Host ""

# Step 2: Navigate to backend
Write-Host "🔄 Step 2: Starting backend server..." -ForegroundColor Yellow
Set-Location "backend"

# Step 3: Start server in background
Write-Host "   Starting Node.js server..." -ForegroundColor Gray
$job = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    npm start
}

# Wait for server to start
Write-Host "   Waiting for server to initialize..." -ForegroundColor Gray
Start-Sleep -Seconds 5

# Step 4: Check if server is running
$serverRunning = $false
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000/health" -Method GET -TimeoutSec 3 -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        $serverRunning = $true
    }
} catch {
    $serverRunning = $false
}

Write-Host ""
if ($serverRunning) {
    Write-Host "✅ SERVER STARTED SUCCESSFULLY!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🎯 Server Details:" -ForegroundColor Cyan
    Write-Host "   • URL: http://localhost:3000" -ForegroundColor White
    Write-Host "   • API: http://localhost:3000/api/v1" -ForegroundColor White
    Write-Host "   • Health: http://localhost:3000/health" -ForegroundColor White
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  🧪 TESTING INSTRUCTIONS" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Option 1: Test with Postman (Recommended)" -ForegroundColor Green
    Write-Host "   1. Open Postman" -ForegroundColor White
    Write-Host "   2. Import: backend/MediSync_Postman_Collection.json" -ForegroundColor White
    Write-Host "   3. Run folder: '2. Booking Flow'" -ForegroundColor White
    Write-Host "   4. Check 'orchestration' in response" -ForegroundColor White
    Write-Host ""
    Write-Host "Option 2: Test with Python Script" -ForegroundColor Green
    Write-Host "   Open a NEW PowerShell window and run:" -ForegroundColor White
    Write-Host "   cd .." -ForegroundColor Gray
    Write-Host "   python test_orchestration_complete.py" -ForegroundColor Gray
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  ✅ ALL FIXES APPLIED" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "✅ ETA Calculation - FIXED (stdout suppressed)" -ForegroundColor Green
    Write-Host "✅ Notifications - CREATED (new file)" -ForegroundColor Green
    Write-Host "✅ Queue Intelligence - CREATED (new file)" -ForegroundColor Green
    Write-Host "✅ Orchestration Cycle - CREATED (new file)" -ForegroundColor Green
    Write-Host "✅ All Python Tools - FIXED (clean JSON output)" -ForegroundColor Green
    Write-Host ""
    Write-Host "📖 Full Details: ../ORCHESTRATION_FIXES_COMPLETE.md" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Press Ctrl+C to stop the server when done testing" -ForegroundColor Yellow
    Write-Host ""
    
    # Keep script running and show logs
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  📋 SERVER LOGS" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
    # Show job output
    while ($job.State -eq 'Running') {
        Receive-Job -Job $job
        Start-Sleep -Seconds 1
    }
    
} else {
    Write-Host "❌ SERVER FAILED TO START" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "   1. Check MongoDB is running: mongod --version" -ForegroundColor White
    Write-Host "   2. Check Redis is running: redis-cli ping" -ForegroundColor White
    Write-Host "   3. Check port 3000 is free" -ForegroundColor White
    Write-Host "   4. Try manual start: cd backend; npm start" -ForegroundColor White
    Write-Host ""
}

# Cleanup
Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
