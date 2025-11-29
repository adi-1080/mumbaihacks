# 🏥 MediSync - Complete API Integration Guide
# Test all endpoints and generate comprehensive documentation

$baseUrl = "http://localhost:3000"
$apiBase = "$baseUrl/api/v1"

# Color functions
function Write-Section {
    param([string]$text)
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host $text -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
}

function Write-API {
    param([string]$method, [string]$endpoint)
    Write-Host "[$method] " -NoNewline -ForegroundColor Yellow
    Write-Host $endpoint -ForegroundColor White
}

function Write-Success {
    param([string]$text)
    Write-Host "[SUCCESS] $text" -ForegroundColor Green
}

function Write-Error {
    param([string]$text)
    Write-Host "[ERROR] $text" -ForegroundColor Red
}

function Write-Info {
    param([string]$text)
    Write-Host "[INFO] $text" -ForegroundColor Blue
}

# Store results
$results = @{}
$tokenNumbers = @()

# Function to make API call and store result
function Test-API {
    param(
        [string]$Method,
        [string]$Endpoint,
        [string]$Description,
        [object]$Body = $null,
        [string]$Category,
        [string]$UserType = "Both"
    )
    
    Write-API $Method $Endpoint
    Write-Host "Description: $Description" -ForegroundColor Gray
    
    try {
        $params = @{
            Uri = "$apiBase$Endpoint"
            Method = $Method
            ContentType = "application/json"
        }
        
        if ($Body) {
            $params.Body = ($Body | ConvertTo-Json -Depth 10)
            Write-Host "Request Body:" -ForegroundColor Gray
            Write-Host ($Body | ConvertTo-Json -Depth 10) -ForegroundColor DarkGray
        }
        
        $response = Invoke-RestMethod @params -ErrorAction Stop
        
        Write-Success "Response received"
        Write-Host "Response:" -ForegroundColor Gray
        Write-Host ($response | ConvertTo-Json -Depth 10) -ForegroundColor DarkGray
        
        $key = "$Category|$Method|$Endpoint"
        $results[$key] = @{
            Method = $Method
            Endpoint = $Endpoint
            Description = $Description
            Category = $Category
            UserType = $UserType
            RequestBody = $Body
            Response = $response
            Status = "Success"
        }
        
        return $response
        
    } catch {
        Write-Error "Failed: $($_.Exception.Message)"
        $key = "$Category|$Method|$Endpoint"
        $results[$key] = @{
            Method = $Method
            Endpoint = $Endpoint
            Description = $Description
            Category = $Category
            UserType = $UserType
            RequestBody = $Body
            Error = $_.Exception.Message
            Status = "Failed"
        }
        return $null
    }
    
    Start-Sleep -Milliseconds 500
}

# ====================
# START TESTING
# ====================

Write-Host @"
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     🏥 MediSync API - Complete Integration Guide            ║
║     Testing All Endpoints with Real Responses               ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"@ -ForegroundColor Cyan

Start-Sleep -Seconds 2

# ====================
# 1. HEALTH CHECK
# ====================
Write-Section "1. HEALTH CHECK"
Test-API -Method "GET" -Endpoint "/../../health" -Description "Check if server is running and all services are connected" -Category "System" -UserType "Both"

# ====================
# 2. CLINIC INFORMATION
# ====================
Write-Section "2. CLINIC INFORMATION APIs"

Test-API -Method "GET" -Endpoint "/clinic/info" -Description "Get complete clinic information including name, address, contact details" -Category "Clinic" -UserType "Both"

Test-API -Method "GET" -Endpoint "/clinic/location" -Description "Get clinic GPS coordinates for navigation" -Category "Clinic" -UserType "Patient"

Test-API -Method "GET" -Endpoint "/clinic/hours" -Description "Get today's operating hours" -Category "Clinic" -UserType "Both"

Test-API -Method "GET" -Endpoint "/clinic/doctors" -Description "Get list of all doctors with specializations and availability" -Category "Clinic" -UserType "Both"

# ====================
# 3. QUEUE STATUS (Before Booking)
# ====================
Write-Section "3. QUEUE STATUS - Before Booking"

$queueBefore = Test-API -Method "GET" -Endpoint "/queue" -Description "Get complete queue status with smart features (ETAs, intelligence dashboard)" -Category "Queue" -UserType "Both"

Test-API -Method "GET" -Endpoint "/queue/stats" -Description "Get clinic statistics (total patients, average wait time, etc.)" -Category "Queue" -UserType "Both"

Test-API -Method "GET" -Endpoint "/queue/current-token" -Description "Get current token being served and next token number" -Category "Queue" -UserType "Both"

Test-API -Method "GET" -Endpoint "/queue/doctor-status" -Description "Get doctor availability and current workload" -Category "Queue" -UserType "Both"

# ====================
# 4. SYMPTOM ANALYSIS (Optional Pre-Booking)
# ====================
Write-Section "4. SYMPTOM ANALYSIS - Pre-Booking Intelligence"

$symptomAnalysis = Test-API -Method "POST" -Endpoint "/appointments/analyze-symptoms" `
    -Description "AI-powered symptom analysis to determine urgency and emergency level" `
    -Category "Appointment" -UserType "Patient" `
    -Body @{
        symptoms = "Severe chest pain, difficulty breathing, sweating"
        age = 55
        existing_conditions = @("Hypertension")
    }

# ====================
# 5. BOOK APPOINTMENTS
# ====================
Write-Section "5. BOOK APPOINTMENTS - Patient Flow"

Write-Info "Booking CRITICAL patient (triggers full orchestration)..."
$booking1 = Test-API -Method "POST" -Endpoint "/appointments/book" `
    -Description "Book CRITICAL priority patient - triggers automatic ETA calculation, queue optimization, and notifications" `
    -Category "Appointment" -UserType "Patient" `
    -Body @{
        name = "Rajesh Kumar"
        contact_number = "+91-9876543210"
        symptoms = "Severe chest pain, difficulty breathing, sweating"
        location = "Andheri West, Mumbai"
        age = 55
        gender = "Male"
        emergency_level = "CRITICAL"
        urgency_score = 9
    }

if ($booking1 -and $booking1.patient) {
    $tokenNumbers += $booking1.patient.tokenNumber
}

Start-Sleep -Seconds 2

Write-Info "Booking HIGH priority patient..."
$booking2 = Test-API -Method "POST" -Endpoint "/appointments/book" `
    -Description "Book HIGH priority patient - triggers automatic queue optimization" `
    -Category "Appointment" -UserType "Patient" `
    -Body @{
        name = "Priya Sharma"
        contact_number = "+91-9988776655"
        symptoms = "High fever, severe headache, vomiting"
        location = "Bandra West, Mumbai"
        age = 32
        gender = "Female"
        emergency_level = "HIGH"
        urgency_score = 7
    }

if ($booking2 -and $booking2.patient) {
    $tokenNumbers += $booking2.patient.tokenNumber
}

Start-Sleep -Seconds 2

Write-Info "Booking MODERATE priority patient..."
$booking3 = Test-API -Method "POST" -Endpoint "/appointments/book" `
    -Description "Book MODERATE priority patient - standard booking with basic orchestration" `
    -Category "Appointment" -UserType "Patient" `
    -Body @{
        name = "Amit Patel"
        contact_number = "+91-9123456789"
        symptoms = "Fever and cough for 3 days"
        location = "Juhu, Mumbai"
        age = 28
        gender = "Male"
        emergency_level = "MODERATE"
        urgency_score = 5
    }

if ($booking3 -and $booking3.patient) {
    $tokenNumbers += $booking3.patient.tokenNumber
}

Start-Sleep -Seconds 2

Write-Info "Booking NORMAL priority patient..."
$booking4 = Test-API -Method "POST" -Endpoint "/appointments/book" `
    -Description "Book NORMAL priority patient - routine checkup" `
    -Category "Appointment" -UserType "Patient" `
    -Body @{
        name = "Sneha Desai"
        contact_number = "+91-9001122334"
        symptoms = "Routine checkup, minor cold"
        location = "Powai, Mumbai"
        age = 25
        gender = "Female"
        emergency_level = "NORMAL"
        urgency_score = 3
    }

if ($booking4 -and $booking4.patient) {
    $tokenNumbers += $booking4.patient.tokenNumber
}

# ====================
# 6. QUEUE STATUS (After Booking)
# ====================
Write-Section "6. QUEUE STATUS - After Bookings"

$queueAfter = Test-API -Method "GET" -Endpoint "/queue" -Description "View updated queue with all new patients and their positions" -Category "Queue" -UserType "Both"

Test-API -Method "GET" -Endpoint "/queue/etas" -Description "Get calculated ETAs for all patients with travel time and appointment time" -Category "Queue" -UserType "Both"

Test-API -Method "GET" -Endpoint "/queue/intelligence" -Description "Get queue intelligence dashboard (aging stats, reorder history, optimization insights)" -Category "Queue" -UserType "Doctor"

# ====================
# 7. PATIENT-SPECIFIC APIs
# ====================
Write-Section "7. PATIENT-SPECIFIC APIs"

if ($tokenNumbers.Count -gt 0) {
    $testToken = $tokenNumbers[0]
    
    Test-API -Method "GET" -Endpoint "/appointments/$testToken" -Description "Get complete appointment details for specific patient" -Category "Appointment" -UserType "Patient"
    
    Test-API -Method "GET" -Endpoint "/queue/position/$testToken" -Description "Get queue position and estimated wait time for patient" -Category "Queue" -UserType "Patient"
    
    Test-API -Method "GET" -Endpoint "/queue/insights/$testToken" -Description "Get AI-powered insights for patient (priority changes, wait time analysis)" -Category "Queue" -UserType "Patient"
}

# ====================
# 8. UPDATE LOCATION (Patient en-route)
# ====================
Write-Section "8. UPDATE PATIENT LOCATION - En-route Feature"

if ($tokenNumbers.Count -gt 1) {
    $updateToken = $tokenNumbers[1]
    
    Test-API -Method "PATCH" -Endpoint "/appointments/$updateToken/location" `
        -Description "Update patient location while traveling - triggers ETA recalculation and queue reoptimization" `
        -Category "Appointment" -UserType "Patient" `
        -Body @{
            latitude = 19.0596
            longitude = 72.8295
            address = "Near Juhu Beach, Mumbai"
        }
}

# ====================
# 9. QUEUE OPTIMIZATION (Doctor Controls)
# ====================
Write-Section "9. QUEUE OPTIMIZATION - Doctor Controls"

Test-API -Method "POST" -Endpoint "/queue/optimize" -Description "Manually trigger queue optimization (reorders patients based on priority)" -Category "Queue" -UserType "Doctor"

Test-API -Method "GET" -Endpoint "/queue/ongoing" -Description "Get list of patients currently in consultation" -Category "Queue" -UserType "Doctor"

# ====================
# 10. ORCHESTRATION APIs
# ====================
Write-Section "10. ORCHESTRATION SYSTEM APIs"

Test-API -Method "GET" -Endpoint "/queue/orchestration/dashboard" -Description "Get orchestration dashboard with all automated actions and their status" -Category "Orchestration" -UserType "Doctor"

Test-API -Method "GET" -Endpoint "/queue/orchestration/monitor" -Description "Monitor orchestration triggers and conditions" -Category "Orchestration" -UserType "Doctor"

Test-API -Method "POST" -Endpoint "/queue/orchestration/trigger" -Description "Manually trigger complete orchestration cycle (ETA calculation, notifications, optimization)" -Category "Orchestration" -UserType "Doctor"

Test-API -Method "POST" -Endpoint "/queue/orchestration/execute" -Description "Execute orchestration cycle programmatically" -Category "Orchestration" -UserType "System"

# ====================
# 11. NOTIFICATIONS
# ====================
Write-Section "11. NOTIFICATION APIs"

Test-API -Method "POST" -Endpoint "/notifications/queue-updates" -Description "Send queue position update notifications to all waiting patients" -Category "Notification" -UserType "System"

Test-API -Method "POST" -Endpoint "/notifications/eta-updates" -Description "Send ETA update notifications when times change" -Category "Notification" -UserType "System"

Test-API -Method "GET" -Endpoint "/notifications/history" -Description "Get notification history with timestamps and delivery status" -Category "Notification" -UserType "Both"

# ====================
# 12. COMPLETE CONSULTATION (Doctor)
# ====================
Write-Section "12. COMPLETE CONSULTATION - Doctor Flow"

if ($tokenNumbers.Count -gt 0) {
    $completeToken = $tokenNumbers[0]
    
    Write-Info "Completing consultation for token #$completeToken (CRITICAL patient)..."
    $completion = Test-API -Method "POST" -Endpoint "/appointments/$completeToken/complete" `
        -Description "Mark patient consultation as completed - triggers full orchestration cycle (queue reorder, ETA recalc, notify next patient)" `
        -Category "Appointment" -UserType "Doctor"
    
    Start-Sleep -Seconds 2
    
    # Check queue after completion
    Test-API -Method "GET" -Endpoint "/queue" -Description "View queue after patient completion" -Category "Queue" -UserType "Both"
}

# ====================
# 13. CANCEL APPOINTMENT
# ====================
Write-Section "13. CANCEL APPOINTMENT"

if ($tokenNumbers.Count -gt 3) {
    $cancelToken = $tokenNumbers[3]
    
    Test-API -Method "DELETE" -Endpoint "/appointments/$cancelToken" `
        -Description "Cancel appointment and remove from queue" `
        -Category "Appointment" -UserType "Patient"
}

# ====================
# GENERATE DOCUMENTATION
# ====================
Write-Section "GENERATING COMPREHENSIVE DOCUMENTATION"

$docPath = Join-Path $PSScriptRoot "COMPLETE_API_DOCUMENTATION.md"

$markdown = @"
# 🏥 MediSync - Complete API Documentation
**Generated on:** $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
**Base URL:** $apiBase

---

## 📋 Table of Contents
1. [System APIs](#system-apis)
2. [Clinic Information APIs](#clinic-information-apis)
3. [Queue Management APIs](#queue-management-apis)
4. [Appointment APIs](#appointment-apis)
5. [Orchestration APIs](#orchestration-apis)
6. [Notification APIs](#notification-apis)

---

"@

$categories = $results.Values | Group-Object -Property Category | Sort-Object Name

foreach ($category in $categories) {
    $markdown += @"
## $($category.Name) APIs

"@
    
    foreach ($api in ($category.Group | Sort-Object Endpoint)) {
        $markdown += @"
### [$($api.Method)] $($api.Endpoint)
**Description:** $($api.Description)
**User Type:** $($api.UserType)

"@
        
        if ($api.RequestBody) {
            $markdown += @"
**Request Body:**
``````json
$($api.RequestBody | ConvertTo-Json -Depth 10)
``````

"@
        }
        
        if ($api.Status -eq "Success") {
            $markdown += @"
**Response:**
``````json
$($api.Response | ConvertTo-Json -Depth 10)
``````

"@
        } else {
            $markdown += @"
**Status:** ❌ Failed
**Error:** $($api.Error)

"@
        }
        
        $markdown += @"
---

"@
    }
}

# Add integration examples
$markdown += @"
## 🔄 Integration Flows

### Patient Flow (Patient Mobile App)

1. **Check Queue Status** → `GET /queue`
2. **Analyze Symptoms (Optional)** → `POST /appointments/analyze-symptoms`
3. **Book Appointment** → `POST /appointments/book`
   - System automatically triggers:
     - ETA calculation if queue > 5
     - Queue optimization if urgency ≥ 7
     - Notifications to all patients
4. **Get Token Details** → `GET /appointments/{tokenNumber}`
5. **Track Queue Position** → `GET /queue/position/{tokenNumber}`
6. **Update Location (En-route)** → `PATCH /appointments/{tokenNumber}/location`
7. **Get Personal Insights** → `GET /queue/insights/{tokenNumber}`

### Doctor Flow (Doctor Dashboard)

1. **View Clinic Stats** → `GET /queue/stats`
2. **View Queue** → `GET /queue` (with smart mode)
3. **View Doctor Status** → `GET /queue/doctor-status`
4. **View Ongoing Consultations** → `GET /queue/ongoing`
5. **Complete Consultation** → `POST /appointments/{tokenNumber}/complete`
   - System automatically triggers:
     - Orchestration cycle
     - ETA recalculation
     - Notify next patient
6. **View Orchestration Dashboard** → `GET /queue/orchestration/dashboard`
7. **Manually Optimize Queue** → `POST /queue/optimize`

---

## 🧠 Intelligent Orchestration

The backend automatically performs these actions based on context:

### After Booking:
- **High Urgency (≥7/10)** → Auto-optimize queue
- **Queue Size >5** → Calculate ETAs for all
- **Always** → Send notifications

### After Completion:
- **Always** → Trigger orchestration cycle
- **Always** → Recalculate ETAs
- **Always** → Notify next patient

### After Location Update:
- **High Priority Patient** → Reoptimize queue
- **Always** → Recalculate patient ETA

---

## 📊 Response Formats

### Structured Booking Response:
``````json
{
  "success": true,
  "message": "✅ Appointment booked successfully",
  "patient": {
    "name": "Patient Name",
    "tokenNumber": "123",
    "bookingTime": "2025-11-29 12:00:00 IST"
  },
  "location": {
    "from": "Patient Location",
    "to": "Clinic Name",
    "distance": "5.2 km",
    "travelTime": "15 minutes"
  },
  "medical": {
    "symptomsCategory": "Critical",
    "urgencyLevel": "9/10",
    "emergencyClassification": "CRITICAL",
    "priorityScore": 15.5
  },
  "queue": {
    "position": 5,
    "totalPatients": 20,
    "estimatedWait": "45 minutes",
    "appointmentETA": "12:45 IST"
  },
  "orchestration": {
    "enabled": true,
    "actionsExecuted": 3,
    "actions": [...]
  }
}
``````

### Structured ETA Response:
``````json
{
  "success": true,
  "message": "✅ ETAs calculated successfully",
  "queue": {
    "currentTime": "12:00:00 IST",
    "doctorsAvailable": 1,
    "currentLoad": "HIGH",
    "emergencyQueue": {
      "count": 5,
      "patients": [...]
    },
    "regularQueue": {
      "count": 15,
      "patients": [...]
    }
  }
}
``````

---

## 🔐 Authentication Notes
Currently all endpoints are public. Add authentication middleware for production:
- Patient endpoints: JWT token from patient app
- Doctor endpoints: JWT token with doctor role
- System endpoints: API key or internal service authentication

---

## 🚀 Testing with Postman
Import the Postman collection: \`MediSync_Postman_Collection.json\`

---

**Total APIs Tested:** $($results.Count)
**Successful:** $($results.Values | Where-Object { $_.Status -eq "Success" } | Measure-Object | Select-Object -ExpandProperty Count)
**Failed:** $($results.Values | Where-Object { $_.Status -eq "Failed" } | Measure-Object | Select-Object -ExpandProperty Count)

Generated by MediSync API Testing Suite
"@

$markdown | Out-File -FilePath $docPath -Encoding UTF8

Write-Success "Documentation generated: $docPath"

# ====================
# SUMMARY
# ====================
Write-Section "TEST SUMMARY"

$successCount = ($results.Values | Where-Object { $_.Status -eq "Success" }).Count
$failCount = ($results.Values | Where-Object { $_.Status -eq "Failed" }).Count
$totalCount = $results.Count

Write-Host "Total APIs Tested: $totalCount" -ForegroundColor White
Write-Host "✅ Successful: $successCount" -ForegroundColor Green
Write-Host "❌ Failed: $failCount" -ForegroundColor Red

if ($tokenNumbers.Count -gt 0) {
    Write-Host "`nGenerated Token Numbers:" -ForegroundColor Yellow
    $tokenNumbers | ForEach-Object { Write-Host "  Token #$_" -ForegroundColor White }
}

Write-Host "`n📄 Full documentation saved to: $docPath" -ForegroundColor Cyan
Write-Host "`n✅ All API testing complete!" -ForegroundColor Green
