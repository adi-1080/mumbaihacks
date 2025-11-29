const mongoose = require('mongoose');
const logger = require('./logger');

let isConnected = false;

/**
 * Initialize MongoDB connection
 */
const initMongoDB = async () => {
  if (isConnected) {
    logger.info('MongoDB already connected');
    return;
  }

  try {
    const mongoURI = process.env.MONGODB_URI || 'mongodb://localhost:27017/medisync';
    
    await mongoose.connect(mongoURI, {
      serverSelectionTimeoutMS: 5000,
      socketTimeoutMS: 45000,
    });

    isConnected = true;
    logger.info('✅ Connected to MongoDB successfully');

    // Handle connection events
    mongoose.connection.on('error', (err) => {
      logger.error('MongoDB connection error:', err);
    });

    mongoose.connection.on('disconnected', () => {
      logger.warn('MongoDB disconnected');
      isConnected = false;
    });

    mongoose.connection.on('reconnected', () => {
      logger.info('MongoDB reconnected');
      isConnected = true;
    });

  } catch (error) {
    logger.error('Failed to connect to MongoDB:', error);
    throw error;
  }
};

/**
 * Close MongoDB connection gracefully
 */
const closeMongoDB = async () => {
  if (!isConnected) {
    return;
  }

  try {
    await mongoose.connection.close();
    isConnected = false;
    logger.info('MongoDB connection closed');
  } catch (error) {
    logger.error('Error closing MongoDB connection:', error);
    throw error;
  }
};

/**
 * Get MongoDB connection instance
 */
const getMongoConnection = () => {
  return mongoose.connection;
};

/**
 * Check if MongoDB is connected
 */
const isMongoConnected = () => {
  return isConnected && mongoose.connection.readyState === 1;
};

module.exports = {
  initMongoDB,
  closeMongoDB,
  getMongoConnection,
  isMongoConnected,
};
