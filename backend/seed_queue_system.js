const mongoose = require('mongoose');
const QueueState = require('./schemas/QueueState');
const logger = require('./config/logger');
require('dotenv').config();

/**
 * Initialize Queue System State in MongoDB
 * Creates the global queue state document with default values
 */

async function seedQueueSystem() {
  try {
    // Connect to MongoDB
    logger.info('Connecting to MongoDB...');
    await mongoose.connect(process.env.MONGODB_URI);
    logger.info('✅ Connected to MongoDB');

    // Check if queue state already exists
    let queueState = await QueueState.findOne({ type: 'GLOBAL' });
    
    if (queueState) {
      logger.info('✅ Queue state already exists');
      logger.info(`   Current Token Number: ${queueState.currentTokenNumber}`);
      logger.info(`   Total Bookings Today: ${queueState.dailyStats.totalBookings}`);
      logger.info(`   Completed Today: ${queueState.dailyStats.completedConsultations}`);
    } else {
      // Create new queue state
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      
      queueState = await QueueState.create({
        type: 'GLOBAL',
        currentTokenNumber: 0,
        dailyStats: {
          date: today,
          totalBookings: 0,
          completedConsultations: 0,
          cancelledAppointments: 0,
          noShows: 0,
          emergencyPatients: 0,
          averageWaitTimeMins: 0,
          averageConsultationMins: 0,
        },
        currentMetrics: {
          patientsWaiting: 0,
          patientsInConsultation: 0,
          emergencyCount: 0,
          longestWaitMins: 0,
          totalReorders: 0,
        },
        config: {
          agingRateMins: 5,
          starvationThresholdMins: 30,
          maxWaitTimeMins: 120,
          defaultConsultationMins: 15,
        },
      });
      
      logger.info('✅ Created new queue state in MongoDB');
      logger.info('   Queue System Configuration:');
      logger.info(`   - Aging Rate: ${queueState.config.agingRateMins} minutes`);
      logger.info(`   - Starvation Threshold: ${queueState.config.starvationThresholdMins} minutes`);
      logger.info(`   - Max Wait Time: ${queueState.config.maxWaitTimeMins} minutes`);
      logger.info(`   - Default Consultation: ${queueState.config.defaultConsultationMins} minutes`);
    }

    logger.info('\n✅ Queue system initialization complete!');
    logger.info('🚀 Ready to process patient bookings with MongoDB priority queue');
    
  } catch (error) {
    logger.error('❌ Error seeding queue system:', error);
    process.exit(1);
  } finally {
    await mongoose.connection.close();
    logger.info('Database connection closed');
  }
}

// Run seed
seedQueueSystem();
