# 🏥 MedSahay - AI-Powered Healthcare Queue Management System

![MedSahay Banner](https://img.shields.io/badge/Healthcare-AI%20Powered-blue?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active-success?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

## 📋 Table of Contents
- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Installation & Setup](#installation--setup)
- [API Documentation](#api-documentation)
- [AI Agent System](#ai-agent-system)
- [Contributing](#contributing)

---

## 🎯 Overview

**MedSahay** is an intelligent healthcare queue management system designed to optimize patient flow in clinics and hospitals. It leverages AI-powered orchestration, real-time ETA calculations, priority queue management, and autonomous decision-making to enhance patient experience and clinic efficiency.

### Key Highlights
- 🤖 **AI-Powered Orchestration**: 24+ specialized AI agents for autonomous queue management
- 📊 **Real-Time Analytics**: Live dashboard with queue statistics and patient tracking
- 🚨 **Emergency Prioritization**: Automatic triage based on symptom severity
- 🗺️ **Smart ETA Calculation**: A* pathfinding algorithm for accurate wait time predictions
- 📱 **Multi-Role Interface**: Separate dashboards for doctors, patients, and administrators
- 🔔 **Intelligent Notifications**: Automated alerts for queue updates and appointments

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        MedSahay Frontend                         │
│                    (React 19 + Vite + Tailwind)                 │
│                         Port: 5173                               │
└───────────────┬─────────────────────────────────────────────────┘
                │
                ├──────────────────┬──────────────────────────────┐
                │                  │                              │
                ▼                  ▼                              ▼
┌───────────────────────┐ ┌────────────────────┐ ┌──────────────────────┐
│   Auth Backend        │ │  Queue Backend     │ │   Python AI Layer    │
│  (medsahay-backend)   │ │    (backend)       │ │   (tools/ + main.py) │
│                       │ │                    │ │                      │
│  • JWT Authentication │ │  • Queue Mgmt      │ │  • 24+ AI Agents     │
│  • User Profiles      │ │  • Appointments    │ │  • Root Orchestrator │
│  • Doctor Management  │ │  • ETA Calculation │ │  • Priority Queue    │
│  • Patient Records    │ │  • Notifications   │ │  • Symptom Analysis  │
│                       │ │  • Analytics       │ │  • Emergency Handler │
│  Port: 5000           │ │  Port: 3000        │ │  • Clinic Monitor    │
│  MongoDB: auth_db     │ │  MongoDB: queue_db │ │  • Starvation Track  │
└───────────────────────┘ └────────────────────┘ └──────────────────────┘
         │                        │                        │
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  ▼
                    ┌──────────────────────────┐
                    │     MongoDB Atlas        │
                    │   (Database Layer)       │
                    │                          │
                    │  • Users & Auth          │
                    │  • Patients & Queue      │
                    │  • Appointments          │
                    │  • Clinic State          │
                    │  • Analytics Data        │
                    └──────────────────────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │      Redis Cache         │
                    │   (Real-Time State)      │
                    │                          │
                    │  • Queue State           │
                    │  • Session Data          │
                    │  • ETA Cache             │
                    └──────────────────────────┘
```

---

## ✨ Features

### 🎨 Frontend Features (MedSahay_frontend)
- **🔐 Authentication System**
  - Secure login/signup for doctors and patients
  - JWT-based session management
  - Role-based access control (RBAC)

- **👨‍⚕️ Doctor Dashboard**
  - Real-time queue monitoring with live token updates
  - Patient management with detailed consultation history
  - Prescription and diagnosis recording
  - Completed consultations tracking
  - Performance analytics and statistics
  - Emergency patient alerts

- **🧑‍🤝‍🧑 Patient Interface**
  - Easy appointment booking with symptom input
  - Real-time queue position tracking
  - Estimated wait time (ETA) display
  - Appointment history and records
  - Notification center

- **🤖 AI Orchestration Demo**
  - Visual representation of AI agent interactions
  - Live execution logs with 3D data structures
  - Input/output monitoring for debugging
  - Agent coordination visualization

- **📊 Analytics Dashboard**
  - Daily patient statistics
  - Average wait times and consultation duration
  - Emergency case tracking
  - Queue efficiency metrics

### 🔧 Backend Features (backend/)
- **📅 Queue Management**
  - Dynamic priority queue with real-time reordering
  - A* pathfinding for ETA calculation
  - Emergency level assessment (ROUTINE, PRIORITY, CRITICAL)
  - Starvation prevention for long-waiting patients
  - Automatic queue cycling

- **🏥 Appointment System**
  - Booking, rescheduling, and cancellation
  - Conflict detection and resolution
  - Follow-up appointment scheduling
  - Doctor availability management

- **🔔 Notification Service**
  - Queue position updates
  - Appointment reminders
  - Emergency alerts
  - Doctor notifications for critical cases

- **📈 Analytics Engine**
  - Real-time statistics computation
  - Historical data analysis
  - Performance metrics tracking
  - Custom report generation

### 🔑 Auth Backend Features (medsahay-backend/)
- **👤 User Management**
  - Secure registration and authentication
  - Profile management (doctors and patients)
  - Credential encryption with bcrypt
  - Session token validation

- **🏥 Doctor Profiles**
  - Specialization and qualification management
  - Working hours and availability
  - Consultation fee configuration
  - Performance ratings

- **🧑‍🤝‍🧑 Patient Records**
  - Medical history storage
  - Appointment tracking
  - Prescription records
  - Emergency contact information

### 🤖 AI Agent System (Python Layer)
- **🧠 Root Orchestrator** (`root_agent.py`)
  - Coordinates all 24+ specialized agents
  - Autonomous decision-making
  - Context-aware task execution
  - Error handling and recovery

- **🚨 Emergency Handler** (`emergency_handler.py`)
  - Symptom severity analysis
  - Automatic priority escalation
  - Critical case alerts

- **📊 Queue Intelligence** (`queue_intelligence.py`)
  - Predictive queue optimization
  - Load balancing across doctors
  - Wait time minimization

- **🗺️ ETA Calculator** (`astar_eta_calculator.py`)
  - A* pathfinding algorithm
  - Real-time recalculation on queue changes
  - Accurate wait time prediction

- **🔄 Clinic Monitor** (`clinic_monitor.py`)
  - Real-time clinic state tracking
  - Performance anomaly detection
  - Resource utilization monitoring

- **⏱️ Starvation Tracker** (`starvation_tracker.py`)
  - Prevents indefinite waiting
  - Priority boosting for long waits
  - Fair queue management

---

## 🛠️ Tech Stack

### Frontend
```json
{
  "framework": "React 19",
  "build_tool": "Vite",
  "styling": "Tailwind CSS",
  "routing": "React Router v7",
  "http_client": "Axios",
  "icons": "Lucide React + React Icons",
  "state": "React Hooks (useState, useEffect)"
}
```

### Backend (Queue & Orchestration)
```json
{
  "runtime": "Node.js",
  "framework": "Express.js",
  "database": "MongoDB (Mongoose ODM)",
  "cache": "Redis",
  "security": "Helmet + CORS + Rate Limiting",
  "logging": "Winston",
  "validation": "Joi",
  "testing": "Jest"
}
```

### Backend (Auth & Profiles)
```json
{
  "runtime": "Node.js",
  "framework": "Express.js",
  "database": "MongoDB (Mongoose ODM)",
  "auth": "JWT (jsonwebtoken)",
  "encryption": "bcryptjs",
  "validation": "Custom middleware"
}
```

### AI Layer
```json
{
  "language": "Python 3.10+",
  "ai_framework": "Google ADK (Agentic Development Kit)",
  "llm": "Google Gemini",
  "database_client": "PyMongo",
  "cache_client": "Redis-py",
  "api_framework": "FastAPI (for Python endpoints)",
  "http_client": "Requests",
  "environment": "python-dotenv"
}
```

### Infrastructure
- **Database**: MongoDB Atlas (Cloud-hosted)
- **Cache**: Redis (Local/Cloud)
- **Version Control**: Git + GitHub
- **Development**: VS Code, Postman, MongoDB Compass

---

## 📁 Project Structure

```
AgenticAi/AI/
├── 📂 MedSahay_frontend/          # React Frontend Application
│   ├── src/
│   │   ├── Components/
│   │   │   ├── Doctor/             # Doctor-specific components
│   │   │   │   ├── DashboardNew.jsx           # Main doctor dashboard
│   │   │   │   ├── ViewDoctorProfile.jsx      # Doctor profile view
│   │   │   │   ├── PatientDetails.jsx         # Patient details page
│   │   │   │   ├── PatientList.jsx            # List of all patients
│   │   │   │   └── AgentOrchestrationDemoEnhanced.jsx
│   │   │   ├── Patient/            # Patient-specific components
│   │   │   │   ├── BookAppointment.jsx        # Appointment booking
│   │   │   │   ├── QueueStatus.jsx            # Queue position tracker
│   │   │   │   └── PatientDashboard.jsx       # Patient dashboard
│   │   │   └── Shared/             # Reusable components
│   │   │       ├── Sidebar.jsx                # Navigation sidebar
│   │   │       └── Header.jsx                 # App header
│   │   ├── services/
│   │   │   ├── doctorApi.js        # Doctor API calls
│   │   │   ├── patientApi.js       # Patient API calls
│   │   │   └── authApi.js          # Authentication APIs
│   │   ├── App.jsx                 # Main app component
│   │   └── main.jsx                # Entry point
│   ├── public/                     # Static assets
│   ├── package.json
│   └── vite.config.js
│
├── 📂 backend/                     # Queue Management Backend (Port 3000)
│   ├── config/
│   │   ├── mongodb.js              # MongoDB connection
│   │   ├── redis.js                # Redis connection
│   │   └── logger.js               # Winston logger setup
│   ├── controllers/
│   │   ├── appointmentController.js # Appointment logic
│   │   ├── queueController.js       # Queue management logic
│   │   ├── clinicController.js      # Clinic operations
│   │   └── notificationController.js # Notification handling
│   ├── models/
│   │   ├── Patient.js              # Patient schema
│   │   ├── Appointment.js          # Appointment schema
│   │   ├── QueueState.js           # Queue state schema
│   │   └── Clinic.js               # Clinic schema
│   ├── routes/
│   │   ├── appointmentRoutes.js    # /api/v1/appointments
│   │   ├── queueRoutes.js          # /api/v1/queue
│   │   ├── clinicRoutes.js         # /api/v1/clinic
│   │   └── notificationRoutes.js   # /api/v1/notifications
│   ├── services/
│   │   ├── queueService.js         # Queue business logic
│   │   ├── appointmentService.js   # Appointment business logic
│   │   └── notificationService.js  # Notification logic
│   ├── middleware/
│   │   ├── errorHandler.js         # Global error handling
│   │   └── validator.js            # Request validation
│   ├── schemas/
│   │   └── appointmentSchemas.js   # Joi validation schemas
│   ├── server.js                   # Express server
│   ├── seed.js                     # Database seeder
│   └── package.json
│
├── 📂 medsahay-backend/            # Auth Backend (Port 5000)
│   ├── controllers/
│   │   ├── authController.js       # Login/signup logic
│   │   ├── doctorController.js     # Doctor management
│   │   └── patientController.js    # Patient management
│   ├── models/
│   │   ├── User.js                 # User schema
│   │   ├── Doctor.js               # Doctor schema
│   │   └── Patient.js              # Patient schema
│   ├── routes/
│   │   ├── authRoutes.js           # /api/v1/auth
│   │   ├── doctorRoutes.js         # /api/v1/doctors
│   │   └── patientRoutes.js        # /api/v1/patients
│   ├── middleware/
│   │   └── authMiddleware.js       # JWT verification
│   ├── index.js                    # Server entry point
│   └── package.json
│
├── 📂 tools/                       # Python AI Agent System
│   ├── root_agent.py               # 🧠 Main orchestrator (24+ tools)
│   ├── orchestrator_brain.py       # 🎯 Coordination logic
│   ├── queue_intelligence.py       # 📊 Queue optimization
│   ├── emergency_handler.py        # 🚨 Emergency triage
│   ├── astar_eta_calculator.py     # 🗺️ ETA calculation
│   ├── clinic_monitor.py           # 👀 Clinic state tracking
│   ├── starvation_tracker.py       # ⏱️ Prevent long waits
│   ├── symptom_analyzer.py         # 🩺 Symptom assessment
│   ├── priority_queue_manager.py   # 📋 Priority queue logic
│   ├── notification_agent.py       # 🔔 Smart notifications
│   ├── mongodb_utils.py            # 💾 Database utilities
│   ├── api_*.py                    # 🔌 API integration tools
│   └── requirements.txt
│
├── main.py                         # FastAPI server for Python tools
├── run_system.py                   # System startup script
├── requirements.txt                # Python dependencies
└── README.md                       # 📖 This file
```

---

## 🚀 Installation & Setup

### Prerequisites
- **Node.js**: v18+ (LTS recommended)
- **Python**: 3.10+
- **MongoDB**: Atlas account or local instance
- **Redis**: Local or cloud instance (optional but recommended)
- **Git**: For cloning the repository

### Step 1: Clone the Repository
```bash
git clone https://github.com/yourusername/medsahay.git
cd medsahay/AI

2. **Environment Configuration**
```bash
cp .env.example .env
# Edit .env with your API keys and Redis configuration
```

3. **Start Redis**
```bash
# Using Docker
docker run -d -p 6379:6379 redis:latest

# Or install locally
redis-server
```

4. **Run the System**
```bash
# Using Google ADK
adk run
```

## 🎯 Usage Examples

### Patient Booking Flow
```
User: "I need to book an appointment"
System: Collects patient info, analyzes symptoms, gets real-time travel data
Result: Intelligent booking with optimized queue position
```

### Emergency Handling
```
Symptoms: "Severe chest pain, difficulty breathing"
System: Auto-detects emergency, moves to priority queue
Result: Immediate attention notification
```

### Queue Optimization
```
System: Analyzes all patients in queue
Factors: Travel time, symptom urgency, consultation duration
Result: Dynamically reordered queue for optimal efficiency
```

## 🧠 Intelligence Features

### Edge Cases Handled
- **Traffic Delays**: Real-time traffic integration with Google Maps
- **Emergency Cases**: Automatic detection and prioritization
- **Distance Optimization**: Nearby patients prioritized when appropriate
- **Consultation Time Variance**: Symptom-based time predictions
- **Multiple Doctors**: Parallel processing optimization

### Symptom Analysis Categories
- Routine checkups (8-12 min)
- Minor illness (8-10 min)  
- Digestive issues (15 min)
- Pain management (18 min)
- Respiratory conditions (20 min)
- Serious symptoms (25 min)
- Emergency cases (30+ min)

### Queue Optimization Factors
1. **Urgency Score** (40% weight): Based on symptom analysis
2. **Travel Efficiency** (30% weight): Distance and traffic conditions
3. **Waiting Time** (20% weight): First-come consideration
4. **Consultation Efficiency** (10% weight): Flow optimization

## 🔧 Configuration

### Redis Configuration
```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_password
```

### Google API Setup
```env
GOOGLE_API_KEY=your_google_api_key
```

Required Google Cloud APIs:
- Distance Matrix API
- Maps JavaScript API  
- Places API
- Geolocation API

## 📊 System Architecture

```
Patient Request → Intelligent Booking Agent
                ↓
Real-time Travel & Symptom Analysis
                ↓  
Advanced ETA Calculation Agent
                ↓
Smart Queue Management Agent
                ↓
Optimized Queue & Notifications
```

## 🚨 Emergency Handling

The system automatically detects emergency cases based on symptoms:
- Keywords: "severe", "chest pain", "difficulty breathing", "emergency"
- Immediate queue prioritization
- Real-time staff notifications
- Zero wait time for critical cases

## 📈 Analytics & Insights

- Real-time queue metrics
- Patient flow optimization
- Doctor utilization analysis
- Traffic pattern insights
- Symptom category trends

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Implement your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

Copyright (c) 2024 MediSync Team. All rights reserved.

## 📞 Support

For technical support or questions:
- Email: support@medisync.health
- Documentation: [Link to docs]
- Issues: [GitHub Issues]

---

**MediSync**: Making healthcare smarter, one appointment at a time. 🏥✨