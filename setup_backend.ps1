# MediSync Backend Setup Script
Write-Host "🏥 MediSync Backend Setup" -ForegroundColor Cyan
Write-Host "=" * 50

# Check if Node.js is installed
Write-Host "`n📦 Checking Node.js installation..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version
    Write-Host "✅ Node.js $nodeVersion installed" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js not found! Please install Node.js v16+ from https://nodejs.org" -ForegroundColor Red
    exit 1
}

# Check if Redis is running
Write-Host "`n🔄 Checking Redis connection..." -ForegroundColor Yellow
try {
    $redisTest = redis-cli ping 2>&1
    if ($redisTest -eq "PONG") {
        Write-Host "✅ Redis is running" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Redis not responding. Please start Redis server." -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Redis CLI not found. Assuming Redis is running on localhost:6379" -ForegroundColor Yellow
}

# Navigate to backend directory
Write-Host "`n📂 Navigating to backend directory..." -ForegroundColor Yellow
Set-Location -Path "backend"

# Check if package.json exists
if (-Not (Test-Path "package.json")) {
    Write-Host "❌ package.json not found! Are you in the correct directory?" -ForegroundColor Red
    exit 1
}

# Install dependencies
Write-Host "`n📥 Installing Node.js dependencies..." -ForegroundColor Yellow
npm install

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Dependencies installed successfully" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Create .env file if it doesn't exist
if (-Not (Test-Path ".env")) {
    Write-Host "`n📝 Creating .env file..." -ForegroundColor Yellow
    Copy-Item ".env.example" -Destination ".env"
    Write-Host "✅ .env file created from .env.example" -ForegroundColor Green
    Write-Host "⚠️  Please edit .env file if you need custom configuration" -ForegroundColor Yellow
} else {
    Write-Host "`n✅ .env file already exists" -ForegroundColor Green
}

# Create logs directory
if (-Not (Test-Path "logs")) {
    Write-Host "`n📁 Creating logs directory..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path "logs" | Out-Null
    Write-Host "✅ Logs directory created" -ForegroundColor Green
}

# Setup complete
Write-Host "`n" + "=" * 50 -ForegroundColor Cyan
Write-Host "🎉 Setup Complete!" -ForegroundColor Green
Write-Host "=" * 50 -ForegroundColor Cyan

Write-Host "`n📋 Next Steps:" -ForegroundColor Yellow
Write-Host "1. Make sure Redis is running on localhost:6379"
Write-Host "2. Start the backend server:"
Write-Host "   Development: npm run dev" -ForegroundColor Cyan
Write-Host "   Production:  npm start" -ForegroundColor Cyan
Write-Host "`n3. Test the API:"
Write-Host "   Health Check: curl http://localhost:3000/health" -ForegroundColor Cyan
Write-Host "   API Docs:     curl http://localhost:3000/api/v1" -ForegroundColor Cyan

Write-Host "`n📖 Documentation available in:" -ForegroundColor Yellow
Write-Host "   - README.md (Full documentation)"
Write-Host "   - QUICK_START.md (Quick test commands)"

Write-Host "`n🚀 Ready to start MediSync Backend!" -ForegroundColor Green
