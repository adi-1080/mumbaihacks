require('dotenv').config();
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const rateLimit = require('express-rate-limit');

const { initRedis, closeRedis } = require('./config/redis');
const { initMongoDB, closeMongoDB } = require('./config/mongodb');
const logger = require('./config/logger');
const { errorHandler, notFoundHandler } = require('./middleware/errorHandler');

// Import routes
const appointmentRoutes = require('./routes/appointmentRoutes');
const queueRoutes = require('./routes/queueRoutes');
const clinicRoutes = require('./routes/clinicRoutes');
const notificationRoutes = require('./routes/notificationRoutes');

// Initialize Express app
const app = express();
const PORT = process.env.PORT || 3000;

// ===== MIDDLEWARE =====

// Security headers
app.use(helmet());

// CORS configuration
const corsOptions = {
  origin: process.env.ALLOWED_ORIGINS?.split(',') || '*',
  credentials: true,
  optionsSuccessStatus: 200,
};
app.use(cors(corsOptions));

// Body parsing
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Logging
if (process.env.NODE_ENV !== 'test') {
  app.use(morgan('combined', { stream: { write: (message) => logger.info(message.trim()) } }));
}

// Rate limiting
const limiter = rateLimit({
  windowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS || '900000'), // 15 minutes
  max: parseInt(process.env.RATE_LIMIT_MAX_REQUESTS || '100'),
  message: 'Too many requests from this IP, please try again later.',
});
app.use('/api/', limiter);

// ===== ROUTES =====

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({
    success: true,
    message: 'MediSync Backend is running',
    timestamp: new Date().toISOString(),
    environment: process.env.NODE_ENV,
  });
});

// API routes
const API_PREFIX = process.env.API_PREFIX || '/api/v1';
app.use(`${API_PREFIX}/appointments`, appointmentRoutes);
app.use(`${API_PREFIX}/queue`, queueRoutes);
app.use(`${API_PREFIX}/clinic`, clinicRoutes);
app.use(`${API_PREFIX}/notifications`, notificationRoutes);

// API documentation endpoint
app.get(`${API_PREFIX}`, (req, res) => {
  res.json({
    success: true,
    message: 'MediSync Priority Queue API v1.0 - Complete ADK Workflow',
    endpoints: {
      appointments: {
        'POST /appointments/book': 'Book a new appointment',
        'GET /appointments/:tokenNumber': 'Get appointment details',
        'DELETE /appointments/:tokenNumber': 'Cancel appointment',
        'PATCH /appointments/:tokenNumber/location': 'Update patient location',
        'POST /appointments/:tokenNumber/complete': 'Complete consultation',
        'POST /appointments/analyze-symptoms': 'Analyze patient symptoms',
        'POST /appointments/analyze-location': 'Analyze location and travel',
        'GET /appointments/:tokenNumber/predict-arrival': 'Predict optimal arrival',
        'PATCH /appointments/:tokenNumber/status': 'Update patient status',
      },
      queue: {
        'GET /queue': 'Get current queue status',
        'GET /queue/current-token': 'Get current token number',
        'GET /queue/position/:tokenNumber': 'Get queue position',
        'GET /queue/etas': 'Get calculated ETAs',
        'GET /queue/ongoing': 'Get ongoing consultations',
        'GET /queue/stats': 'Get clinic statistics',
        'GET /queue/doctor-status': 'Get intelligent doctor status',
        'POST /queue/optimize': 'Trigger queue optimization',
        'GET /queue/intelligence': 'Get queue intelligence dashboard',
        'GET /queue/insights/:tokenNumber': 'Get patient insights',
      },
      orchestration: {
        'POST /queue/orchestration/execute': 'Execute orchestration cycle',
        'GET /queue/orchestration/monitor': 'Monitor orchestration triggers',
        'GET /queue/orchestration/dashboard': 'Get orchestration dashboard',
        'POST /queue/orchestration/trigger': 'Manually trigger cycle',
      },
      clinic: {
        'GET /clinic/info': 'Get clinic information',
        'PUT /clinic/info': 'Update clinic information',
        'GET /clinic/location': 'Get clinic coordinates',
        'GET /clinic/hours': 'Get operating hours',
        'GET /clinic/doctors': 'Get all doctors',
        'GET /clinic/doctors/:id': 'Get doctor by ID',
        'POST /clinic/doctors': 'Add new doctor',
        'PUT /clinic/doctors/:id': 'Update doctor',
        'PATCH /clinic/doctors/:id/availability': 'Toggle availability',
        'GET /clinic/dashboard': 'Get comprehensive dashboard',
      },
      notifications: {
        'POST /notifications/queue-updates': 'Send queue updates',
        'POST /notifications/appointment-ready/:token': 'Notify appointment ready',
        'POST /notifications/eta-updates': 'Send ETA updates',
        'GET /notifications/history': 'Get notification history',
      },
    },
    features: [
      'Priority Queue Management',
      'Intelligent ETA Calculation',
      'Symptom-Based Priority',
      'Real-Time Location Tracking',
      'Doctor Availability Management',
      'Automated Orchestration',
      'Smart Notifications',
      'Queue Intelligence Dashboard',
    ],
    documentation: 'See README.md and API_REFERENCE.json',
  });
});

// ===== ERROR HANDLING =====

// 404 handler
app.use(notFoundHandler);

// Global error handler
app.use(errorHandler);

// ===== SERVER INITIALIZATION =====

const startServer = async () => {
  try {
    // Initialize MongoDB connection
    await initMongoDB();
    logger.info('✅ MongoDB connection established');

    // Initialize Redis connection
    await initRedis();
    logger.info('✅ Redis connection established');

    // Start Express server
    app.listen(PORT, () => {
      logger.info(`🚀 MediSync Backend running on port ${PORT}`);
      logger.info(`📍 Environment: ${process.env.NODE_ENV || 'development'}`);
      logger.info(`🔗 API Endpoint: http://localhost:${PORT}${API_PREFIX}`);
      logger.info(`💊 Health Check: http://localhost:${PORT}/health`);
      logger.info(`🗄️  Database: MongoDB + Redis`);
    });
  } catch (error) {
    logger.error('Failed to start server:', error);
    process.exit(1);
  }
};

// ===== GRACEFUL SHUTDOWN =====

process.on('SIGTERM', async () => {
  logger.info('SIGTERM signal received: closing HTTP server');
  await closeMongoDB();
  await closeRedis();
  process.exit(0);
});

process.on('SIGINT', async () => {
  logger.info('SIGINT signal received: closing HTTP server');
  await closeMongoDB();
  await closeRedis();
  process.exit(0);
});

// Start the server
startServer();

module.exports = app;
