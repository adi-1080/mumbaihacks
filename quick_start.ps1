#!/usr/bin/env powershell
# Quick Start Script for MediSync Agentic AI
# Fixes all issues and starts the system

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "🚀 MEDISYNC AGENTIC AI - QUICK START" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Step 1: Check Redis
Write-Host "1️⃣ Checking Redis..." -ForegroundColor Yellow
$redisRunning = $false
try {
    $result = redis-cli ping 2>&1
    if ($result -eq "PONG") {
        Write-Host "   ✅ Redis is running`n" -ForegroundColor Green
        $redisRunning = $true
    }
} catch {
    Write-Host "   ❌ Redis not running`n" -ForegroundColor Red
}

if (-not $redisRunning) {
    Write-Host "   📍 Please start Redis manually:" -ForegroundColor Yellow
    Write-Host "      - Windows: Start Redis service from Services" -ForegroundColor Gray
    Write-Host "      - Or install: https://github.com/tporadowski/redis/releases`n" -ForegroundColor Gray
    Write-Host "   Press Enter after starting Redis..." -ForegroundColor Yellow
    Read-Host
}

# Step 2: Check Gemini API Key
Write-Host "2️⃣ Checking Gemini API Key..." -ForegroundColor Yellow
$envFile = "tools\.env"
$apiKeyValid = $false

if (Test-Path $envFile) {
    $content = Get-Content $envFile -Raw
    if ($content -match 'GOOGLE_API_KEY=AIza[a-zA-Z0-9_-]{35}') {
        Write-Host "   ✅ API key found`n" -ForegroundColor Green
        $apiKeyValid = $true
    } else {
        Write-Host "   ⚠️  API key not configured or invalid`n" -ForegroundColor Red
        Write-Host "   📍 Get free API key: https://makersuite.google.com/app/apikey" -ForegroundColor Yellow
        Write-Host "   📍 Then update $envFile`n" -ForegroundColor Yellow
        
        $apiKey = Read-Host "Enter your Gemini API key (or press Enter to skip)"
        if ($apiKey) {
            $content = $content -replace 'GOOGLE_API_KEY=.*', "GOOGLE_API_KEY=$apiKey"
            Set-Content $envFile $content
            Write-Host "   ✅ API key updated`n" -ForegroundColor Green
            $apiKeyValid = $true
        }
    }
} else {
    Write-Host "   ❌ .env file not found`n" -ForegroundColor Red
}

# Step 3: Verify Fixes Applied
Write-Host "3️⃣ Verifying fixes..." -ForegroundColor Yellow

$rootAgentFile = "tools\root_agent.py"
$fixes = @{
    "Model Changed" = $false
    "Hardcoded Date Removed" = $false
    "Tool-First Instructions" = $false
}

if (Test-Path $rootAgentFile) {
    $content = Get-Content $rootAgentFile -Raw
    
    if ($content -match 'gemini-1\.5-flash') {
        $fixes["Model Changed"] = $true
        Write-Host "   ✅ Model: gemini-1.5-flash (15 req/min)" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Model still gemini-2.5-pro (2 req/min)" -ForegroundColor Red
    }
    
    if ($content -notmatch 'September 21, 2025') {
        $fixes["Hardcoded Date Removed"] = $true
        Write-Host "   ✅ Hardcoded date removed" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Hardcoded date still present" -ForegroundColor Red
    }
    
    if ($content -match 'ALWAYS call the appropriate tools') {
        $fixes["Tool-First Instructions"] = $true
        Write-Host "   ✅ Tool-first instructions enabled" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Tool instructions may not be optimal" -ForegroundColor Yellow
    }
}

Write-Host ""

# Step 4: Run Verification Test
Write-Host "4️⃣ Running verification test..." -ForegroundColor Yellow
if ($redisRunning) {
    Write-Host "   🧪 Testing tool execution...`n" -ForegroundColor Cyan
    python verify_tool_execution.py
} else {
    Write-Host "   ⏭️  Skipping (Redis not running)`n" -ForegroundColor Yellow
}

# Step 5: Start Options
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "🎯 READY TO START" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

if ($redisRunning -and $apiKeyValid) {
    Write-Host "✅ All prerequisites met! Choose an option:`n" -ForegroundColor Green
    
    Write-Host "1. Start ADK Web Interface (Recommended)" -ForegroundColor White
    Write-Host "2. Run Backend Server" -ForegroundColor White
    Write-Host "3. Exit" -ForegroundColor White
    Write-Host ""
    
    $choice = Read-Host "Enter choice (1-3)"
    
    switch ($choice) {
        "1" {
            Write-Host "`n🚀 Starting ADK Web Interface..." -ForegroundColor Cyan
            Write-Host "   Access at: http://localhost:8080`n" -ForegroundColor Yellow
            cd tools
            adk web
        }
        "2" {
            Write-Host "`n🚀 Starting Backend Server..." -ForegroundColor Cyan
            python backend/main.py
        }
        "3" {
            Write-Host "`nGoodbye! 👋`n" -ForegroundColor Cyan
        }
        default {
            Write-Host "`n❌ Invalid choice`n" -ForegroundColor Red
        }
    }
} else {
    Write-Host "⚠️  Prerequisites not met:" -ForegroundColor Yellow
    if (-not $redisRunning) {
        Write-Host "   - Start Redis server" -ForegroundColor Gray
    }
    if (-not $apiKeyValid) {
        Write-Host "   - Configure Gemini API key in tools\.env" -ForegroundColor Gray
    }
    Write-Host ""
}

Write-Host "`n📖 For detailed info, see FIXES_APPLIED.md`n" -ForegroundColor Cyan
