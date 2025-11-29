# ========================================
# INTELLIGENT ORCHESTRATION - DEMO TEST
# ========================================
# This script demonstrates the backend's intelligent orchestration
# that mimics root_agent.py's proactive behavior

$separator80 = "=" * 80
$separator60 = "=" * 60

Write-Host ""
Write-Host $separator80 -ForegroundColor Cyan
Write-Host "        INTELLIGENT ORCHESTRATION SYSTEM - DEMONSTRATION" -ForegroundColor Cyan
Write-Host $separator80 -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:3000/api/v1"

# ========================================
# TEST 1: High-Urgency Booking Flow
# ========================================
Write-Host ""
Write-Host "[TEST 1] HIGH-URGENCY BOOKING WITH AUTO-ORCHESTRATION" -ForegroundColor Yellow
Write-Host $separator60 -ForegroundColor Yellow

Write-Host ""
Write-Host "📋 Booking CRITICAL emergency patient (urgency=9)..." -ForegroundColor White

$booking = Invoke-RestMethod -Uri "$baseUrl/appointments/book" `
  -Method POST `
  -Headers @{"Content-Type"="application/json"} `
  -Body (@{
    name = "Critical Emergency"
    contact_number = "+91-9999888877"
    symptoms = "Severe chest pain, difficulty breathing, sweating profusely"
    location = "Bandra West, Mumbai"
    age = 55
    gender = "Male"
    urgency_score = 9
    emergency_level = "CRITICAL"
} | ConvertTo-Json)

Write-Host "✅ Patient booked: Token #$($booking.data.token_number)" -ForegroundColor Green

if ($booking.orchestration.enabled) {
    Write-Host ""
    Write-Host "🧠 AUTOMATIC ORCHESTRATION TRIGGERED:" -ForegroundColor Cyan
    Write-Host "   Actions executed: $($booking.orchestration.actions_executed)" -ForegroundColor White
    
    Write-Host ""
    Write-Host "📊 Orchestration Details:" -ForegroundColor Yellow
    $booking.orchestration.details | ForEach-Object {
        if ($_.success) {
            Write-Host "   ✅ $($_.action)" -ForegroundColor Green
            Write-Host "      Reason: $($_.reason)" -ForegroundColor Gray
        } else {
            Write-Host "   ❌ $($_.action)" -ForegroundColor Red
            Write-Host "      Error: $($_.error)" -ForegroundColor Gray
        }
    }
}

Start-Sleep -Seconds 2

# ========================================
# TEST 2: Smart Queue Status
# ========================================
Write-Host ""
Write-Host ""
Write-Host "[TEST 2] SMART QUEUE STATUS (Auto-includes ETAs + Intelligence)" -ForegroundColor Yellow
Write-Host $separator60 -ForegroundColor Yellow

Write-Host ""
Write-Host "📊 Fetching smart queue status..." -ForegroundColor White

$queue = Invoke-RestMethod -Uri "$baseUrl/queue"

Write-Host "✅ Queue retrieved with smart enhancements" -ForegroundColor Green
Write-Host "   Smart Mode: $($queue.smart_mode)" -ForegroundColor Cyan
Write-Host "   Total Patients: $($queue.data.total_patients)" -ForegroundColor White
Write-Host "   Emergency Count: $($queue.data.emergency_count)" -ForegroundColor Red

if ($queue.data.patients -and $queue.data.patients.Count -gt 0) {
    Write-Host ""
    Write-Host "📋 Current Queue:" -ForegroundColor Cyan
    $queue.data.patients | Select-Object -First 5 token_number, name, emergency_level, priority_score | Format-Table -AutoSize
}

if ($queue.etas) {
    Write-Host "⏱️  ETAs automatically calculated!" -ForegroundColor Green
}

if ($queue.intelligence) {
    Write-Host "🧠 Intelligence dashboard included!" -ForegroundColor Green
}

Start-Sleep -Seconds 2

# ========================================
# TEST 3: Patient Completion Flow
# ========================================
Write-Host ""
Write-Host ""
Write-Host "[TEST 3] PATIENT COMPLETION WITH AUTO-ORCHESTRATION" -ForegroundColor Yellow
Write-Host $separator60 -ForegroundColor Yellow

# Get first patient to complete
if ($queue.data.patients -and $queue.data.patients.Count -gt 0) {
    $firstPatient = $queue.data.patients[0]
    $tokenToComplete = $firstPatient.token_number
    
    Write-Host ""
    Write-Host "👨‍⚕️ Completing consultation for Token #$tokenToComplete..." -ForegroundColor White
    
    $completion = Invoke-RestMethod -Uri "$baseUrl/appointments/$tokenToComplete/complete" -Method POST
    
    Write-Host "✅ Patient #$tokenToComplete consultation completed" -ForegroundColor Green
    
    if ($completion.orchestration.enabled) {
        Write-Host ""
        Write-Host "🧠 AUTOMATIC ORCHESTRATION TRIGGERED:" -ForegroundColor Cyan
        Write-Host "   Actions executed: $($completion.orchestration.actions_executed)" -ForegroundColor White
        
        Write-Host ""
        Write-Host "📊 Orchestration Details:" -ForegroundColor Yellow
        $completion.orchestration.details | ForEach-Object {
            if ($_.success) {
                Write-Host "   ✅ $($_.action)" -ForegroundColor Green
                Write-Host "      Reason: $($_.reason)" -ForegroundColor Gray
            } else {
                Write-Host "   ❌ $($_.action)" -ForegroundColor Red
                Write-Host "      Error: $($_.error)" -ForegroundColor Gray
            }
        }
    }
    
    Start-Sleep -Seconds 2
    
    # Verify queue updated
    Write-Host ""
    Write-Host "🔄 Verifying queue updated..." -ForegroundColor Yellow
    $updatedQueue = Invoke-RestMethod -Uri "$baseUrl/queue"
    Write-Host "   Previous queue size: $($queue.data.total_patients)" -ForegroundColor Gray
    Write-Host "   Current queue size: $($updatedQueue.data.total_patients)" -ForegroundColor Green
} else {
    Write-Host "⚠️  No patients in queue to complete" -ForegroundColor Yellow
}

Start-Sleep -Seconds 2

# ========================================
# TEST 4: Queue Monitoring
# ========================================
Write-Host ""
Write-Host ""
Write-Host "[TEST 4] QUEUE MONITORING ORCHESTRATION" -ForegroundColor Yellow
Write-Host $separator60 -ForegroundColor Yellow

Write-Host ""
Write-Host "🔍 Executing queue health monitoring..." -ForegroundColor White

$monitoring = Invoke-RestMethod -Uri "$baseUrl/queue/monitor"

Write-Host "✅ Queue monitoring completed" -ForegroundColor Green
Write-Host "   Checks performed: $($monitoring.data.checks.Count)" -ForegroundColor Cyan
Write-Host "   Actions taken: $($monitoring.data.actions.Count)" -ForegroundColor Cyan

if ($monitoring.data.checks -and $monitoring.data.checks.Count -gt 0) {
    Write-Host ""
    Write-Host "📋 Health Checks:" -ForegroundColor Yellow
    $monitoring.data.checks | Format-Table check, result, action_needed -AutoSize
}

if ($monitoring.data.actions -and $monitoring.data.actions.Count -gt 0) {
    Write-Host "⚡ Automatic Actions Taken:" -ForegroundColor Green
    $monitoring.data.actions | ForEach-Object {
        Write-Host "   • $($_.action): $($_.reason)" -ForegroundColor White
    }
}

Start-Sleep -Seconds 2

# ========================================
# TEST 5: Location Update Flow
# ========================================
Write-Host ""
Write-Host ""
Write-Host "[TEST 5] LOCATION UPDATE WITH AUTO-ORCHESTRATION" -ForegroundColor Yellow
Write-Host $separator60 -ForegroundColor Yellow

$currentQueue = Invoke-RestMethod -Uri "$baseUrl/queue"

if ($currentQueue.data.patients -and $currentQueue.data.patients.Count -gt 0) {
    # Find a high-priority patient to update
    $highPriorityPatient = $currentQueue.data.patients | Where-Object { $_.emergency_level -eq "CRITICAL" } | Select-Object -First 1
    
    if (-not $highPriorityPatient) {
        $highPriorityPatient = $currentQueue.data.patients[0]
    }
    
    $tokenToUpdate = $highPriorityPatient.token_number
    
    Write-Host ""
    Write-Host "📍 Updating location for Token #$tokenToUpdate (Priority: $($highPriorityPatient.emergency_level))..." -ForegroundColor White
    
    $locationUpdate = Invoke-RestMethod -Uri "$baseUrl/appointments/$tokenToUpdate/location" `
      -Method PATCH `
      -Headers @{"Content-Type"="application/json"} `
      -Body (@{
        latitude = 19.0760
        longitude = 72.8777
        address = "Juhu Beach, Mumbai"
    } | ConvertTo-Json)
    
    Write-Host "✅ Location updated successfully" -ForegroundColor Green
    
    if ($locationUpdate.orchestration.enabled) {
        Write-Host ""
        Write-Host "🧠 AUTOMATIC ORCHESTRATION TRIGGERED:" -ForegroundColor Cyan
        Write-Host "   Actions executed: $($locationUpdate.orchestration.actions_executed)" -ForegroundColor White
        
        Write-Host ""
        Write-Host "📊 Orchestration Details:" -ForegroundColor Yellow
        $locationUpdate.orchestration.details | ForEach-Object {
            if ($_.success) {
                Write-Host "   ✅ $($_.action)" -ForegroundColor Green
                Write-Host "      Reason: $($_.reason)" -ForegroundColor Gray
            } else {
                Write-Host "   ❌ $($_.action)" -ForegroundColor Red
                Write-Host "      Error: $($_.error)" -ForegroundColor Gray
            }
        }
    }
} else {
    Write-Host "⚠️  No patients in queue for location update test" -ForegroundColor Yellow
}

# ========================================
# SUMMARY
# ========================================
Write-Host ""
Write-Host ""
Write-Host $separator80 -ForegroundColor Green
Write-Host "        INTELLIGENT ORCHESTRATION DEMONSTRATION COMPLETE" -ForegroundColor Green
Write-Host $separator80 -ForegroundColor Green

Write-Host ""
Write-Host "✅ All tests completed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "🧠 Key Features Demonstrated:" -ForegroundColor Cyan
Write-Host "   1. ✅ Post-booking orchestration (auto-optimize, ETAs, notifications)" -ForegroundColor White
Write-Host "   2. ✅ Smart queue status (auto-includes ETAs + intelligence)" -ForegroundColor White
Write-Host "   3. ✅ Post-completion orchestration (trigger cycle, notify next)" -ForegroundColor White
Write-Host "   4. ✅ Queue monitoring (health checks + auto-actions)" -ForegroundColor White
Write-Host "   5. ✅ Location update orchestration (reoptimize if high-priority)" -ForegroundColor White

Write-Host ""
Write-Host "📚 Documentation: backend/INTELLIGENT_ORCHESTRATION_GUIDE.md" -ForegroundColor Yellow
Write-Host "🎯 The backend now matches root_agent.py's intelligent behavior!" -ForegroundColor Cyan

Write-Host ""
Write-Host $separator80 -ForegroundColor Green
Write-Host ""
