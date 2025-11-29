# MediSync Backend API

Node.js REST API for MediSync Priority Queue Management System. This backend interacts with the Python-based priority queue system through Redis and provides HTTP endpoints for appointment booking, queue management, and patient tracking.

## 🚀 Features

- **Appointment Management**: Book, view, cancel appointments
- **Queue Monitoring**: Real-time queue status and position tracking
- **ETA Calculations**: Intelligent wait time predictions
- **Location Updates**: Real-time patient location tracking
- **Doctor Dashboard**: Ongoing consultations and clinic statistics
- **Priority Queue Integration**: Direct Redis integration with Python priority queue system

## 📋 Prerequisites

- **Node.js**: v16+ 
- **Redis**: v5+ (running on localhost:6379)
- **Python**: v3.8+ (for priority queue system)

## 🛠️ Installation

```bash
# Navigate to backend directory
cd backend

# Install dependencies
npm install

# Copy environment file
copy .env.example .env

# Edit .env with your configuration
notepad .env
```

## ⚙️ Environment Variables

```env
PORT=3000
NODE_ENV=development
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
API_PREFIX=/api/v1
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

## 🎯 API Endpoints

### Health Check
```
GET /health
```

### Appointments

#### Book Appointment
```http
POST /api/v1/appointments/book
Content-Type: application/json

{
  "name": "John Doe",
  "contact_number": "+91-9876543210",
  "symptoms": "Fever and cough for 3 days",
  "location": "Mumbai",
  "age": 35,
  "gender": "Male",
  "emergency_level": "NORMAL"
}

Response: 201 Created
{
  "success": true,
  "message": "Appointment booked successfully",
  "data": {
    "token_number": 42,
    "priority_score": 45.5,
    "estimated_wait_mins": 30,
    "queue_position": 5
  }
}
```

#### Get Appointment Details
```http
GET /api/v1/appointments/:tokenNumber

Response: 200 OK
{
  "success": true,
  "data": {
    "token_number": 42,
    "name": "John Doe",
    "symptoms": "Fever and cough",
    "priority_score": 45.5,
    "emergency_level": "NORMAL",
    "queue_position": {
      "position": 5,
      "total_ahead": 4,
      "estimated_wait_mins": 60
    }
  }
}
```

#### Cancel Appointment
```http
DELETE /api/v1/appointments/:tokenNumber

Response: 200 OK
{
  "success": true,
  "message": "Appointment for token #42 canceled successfully"
}
```

#### Update Patient Location
```http
PATCH /api/v1/appointments/:tokenNumber/location
Content-Type: application/json

{
  "latitude": 19.0760,
  "longitude": 72.8777,
  "address": "Andheri, Mumbai"
}

Response: 200 OK
{
  "success": true,
  "message": "Location updated successfully"
}
```

#### Complete Consultation (Doctor)
```http
POST /api/v1/appointments/:tokenNumber/complete

Response: 200 OK
{
  "success": true,
  "message": "Consultation for token #42 marked as completed"
}
```

### Queue Management

#### Get Queue Status
```http
GET /api/v1/queue

Response: 200 OK
{
  "success": true,
  "data": {
    "total_patients": 15,
    "emergency_count": 2,
    "main_queue_count": 13,
    "patients": [
      {
        "token_number": 38,
        "name": "Emergency Patient",
        "emergency_level": "CRITICAL",
        "priority_score": 95.0
      },
      {
        "token_number": 42,
        "name": "John Doe",
        "emergency_level": "NORMAL",
        "priority_score": 45.5
      }
    ]
  }
}
```

#### Get Current Token Number
```http
GET /api/v1/queue/current-token

Response: 200 OK
{
  "success": true,
  "data": {
    "current_token": 42,
    "next_token": 43
  }
}
```

#### Get Queue Position
```http
GET /api/v1/queue/position/:tokenNumber

Response: 200 OK
{
  "success": true,
  "data": {
    "token_number": 42,
    "position": 5,
    "total_ahead": 4,
    "estimated_wait_mins": 60,
    "is_emergency": false
  }
}
```

#### Get ETAs for All Patients
```http
GET /api/v1/queue/etas

Response: 200 OK
{
  "success": true,
  "data": {
    "etas": [
      {
        "token_number": 42,
        "eta_time": "15:30 IST",
        "wait_time_mins": 30
      }
    ]
  }
}
```

#### Get Ongoing Consultations
```http
GET /api/v1/queue/ongoing

Response: 200 OK
{
  "success": true,
  "data": {
    "count": 3,
    "consultations": [
      {
        "token_number": 40,
        "doctor_id": 1,
        "started_at": "14:45 IST"
      }
    ]
  }
}
```

#### Get Clinic Statistics
```http
GET /api/v1/queue/stats

Response: 200 OK
{
  "success": true,
  "data": {
    "total_bookings_today": 67,
    "completed_today": 52,
    "current_token_number": 42,
    "patients_in_queue": 15,
    "emergency_patients": 2,
    "average_wait_time_mins": 45
  }
}
```

## 🏃 Running the Server

### Development Mode
```bash
npm run dev
```

### Production Mode
```bash
npm start
```

The server will start on `http://localhost:3000` (or your configured PORT).

## 🧪 Testing API Endpoints

### Using cURL (PowerShell)

#### Book Appointment
```powershell
curl -X POST http://localhost:3000/api/v1/appointments/book `
  -H "Content-Type: application/json" `
  -d '{\"name\":\"John Doe\",\"contact_number\":\"+91-9876543210\",\"symptoms\":\"Fever\"}'
```

#### Get Queue Status
```powershell
curl http://localhost:3000/api/v1/queue
```

#### Get Token Position
```powershell
curl http://localhost:3000/api/v1/queue/position/42
```

### Using Postman

1. Import the collection (available in `docs/postman_collection.json`)
2. Set base URL: `http://localhost:3000`
3. Test all endpoints with sample data

## 📊 Architecture

```
┌─────────────────────────────────────────┐
│         Node.js Backend (Express)       │
├─────────────────────────────────────────┤
│  Controllers (Business Logic)           │
│  ├─ appointmentController               │
│  └─ queueController                     │
├─────────────────────────────────────────┤
│  Services (Data Layer)                  │
│  ├─ queueService (Redis Direct)         │
│  └─ pythonBridge (Python Tools)         │
├─────────────────────────────────────────┤
│         Redis Database                  │
│  ├─ patient_map (HashMap)               │
│  ├─ counters                            │
│  └─ stats                               │
└─────────────────────────────────────────┘
         ↕️
┌─────────────────────────────────────────┐
│    Python Priority Queue System         │
│  ├─ priority_queue_manager.py           │
│  ├─ clinic_tools_priority_queue.py      │
│  └─ All other tools                     │
└─────────────────────────────────────────┘
```

## 🔄 Data Flow

1. **HTTP Request** → Express routes
2. **Controller** → Business logic validation
3. **Service Layer** → Two paths:
   - **Direct Redis**: Read queue data directly
   - **Python Bridge**: Execute Python tools for complex operations
4. **Redis Database** → Shared data store (patient_map, counters)
5. **Response** → JSON formatted response

## 🛡️ Security Features

- **Helmet.js**: Security headers
- **CORS**: Configurable origins
- **Rate Limiting**: 100 requests per 15 minutes
- **Input Validation**: Joi schema validation
- **Error Handling**: Centralized error middleware

## 📝 Error Handling

All errors return consistent format:

```json
{
  "success": false,
  "message": "Error description",
  "error": "Detailed error (development only)"
}
```

HTTP Status Codes:
- `200`: Success
- `201`: Created
- `400`: Bad Request (validation error)
- `404`: Not Found
- `500`: Internal Server Error

## 🔧 Troubleshooting

### Redis Connection Failed
```
Error: Redis client not initialized
```
**Solution**: Ensure Redis is running on localhost:6379

### Python Tools Not Working
```
Error: Python script execution failed
```
**Solution**: 
1. Check Python is installed and in PATH
2. Verify tools folder exists at `../tools`
3. Install Python dependencies: `pip install -r ../tools/requirements.txt`

### Port Already in Use
```
Error: listen EADDRINUSE :::3000
```
**Solution**: Change PORT in `.env` or kill process using port 3000

## 📦 Project Structure

```
backend/
├── config/
│   ├── redis.js          # Redis connection
│   └── logger.js         # Winston logger
├── controllers/
│   ├── appointmentController.js
│   └── queueController.js
├── services/
│   ├── queueService.js   # Redis operations
│   └── pythonBridge.js   # Python tool execution
├── routes/
│   ├── appointmentRoutes.js
│   └── queueRoutes.js
├── middleware/
│   ├── validation.js
│   └── errorHandler.js
├── logs/                 # Application logs
├── .env                  # Environment variables
├── .env.example          # Example env file
├── server.js             # Main entry point
├── package.json
└── README.md
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

For issues and questions:
- GitHub Issues: [Create Issue](https://github.com/medisync/backend/issues)
- Email: support@medisync.com

---

**Made with ❤️ by MediSync Team**
