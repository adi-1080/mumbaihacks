const mongoose = require('mongoose');

/**
 * Queue State Schema - Global queue system state and counters
 * Replaces Redis counters and stats
 */
const QueueStateSchema = new mongoose.Schema({
  // Counter type (singleton pattern - only one document per type)
  type: {
    type: String,
    required: true,
    unique: true,
    enum: ['GLOBAL'],
    default: 'GLOBAL',
  },
  
  // Token number counter
  currentTokenNumber: {
    type: Number,
    required: true,
    default: 0,
  },
  
  // Daily statistics
  dailyStats: {
    date: {
      type: Date,
      required: true,
      default: () => {
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        return today;
      },
    },
    totalBookings: {
      type: Number,
      default: 0,
    },
    completedConsultations: {
      type: Number,
      default: 0,
    },
    cancelledAppointments: {
      type: Number,
      default: 0,
    },
    noShows: {
      type: Number,
      default: 0,
    },
    emergencyPatients: {
      type: Number,
      default: 0,
    },
    averageWaitTimeMins: {
      type: Number,
      default: 0,
    },
    averageConsultationMins: {
      type: Number,
      default: 0,
    },
  },
  
  // Current queue metrics
  currentMetrics: {
    patientsWaiting: {
      type: Number,
      default: 0,
    },
    patientsInConsultation: {
      type: Number,
      default: 0,
    },
    emergencyCount: {
      type: Number,
      default: 0,
    },
    longestWaitMins: {
      type: Number,
      default: 0,
    },
    totalReorders: {
      type: Number,
      default: 0,
    },
    lastReorderTime: Date,
  },
  
  // System configuration
  config: {
    agingRateMins: {
      type: Number,
      default: 5,
    },
    starvationThresholdMins: {
      type: Number,
      default: 30,
    },
    maxWaitTimeMins: {
      type: Number,
      default: 120,
    },
    defaultConsultationMins: {
      type: Number,
      default: 15,
    },
  },
  
  // Last update tracking
  lastMetricsUpdate: {
    type: Date,
    default: Date.now,
  },
  lastDailyReset: {
    type: Date,
    default: Date.now,
  },
}, {
  timestamps: true,
  collection: 'queuestate',
});

// Index for efficient queries (unique constraint in schema definition handles this)

// Instance method: Increment token number
QueueStateSchema.methods.getNextToken = async function() {
  this.currentTokenNumber += 1;
  await this.save();
  return this.currentTokenNumber;
};

// Instance method: Record new booking
QueueStateSchema.methods.recordBooking = async function(isEmergency = false) {
  this.dailyStats.totalBookings += 1;
  if (isEmergency) {
    this.dailyStats.emergencyPatients += 1;
  }
  this.lastMetricsUpdate = new Date();
  await this.save();
};

// Instance method: Record completion
QueueStateSchema.methods.recordCompletion = async function(consultationMins) {
  this.dailyStats.completedConsultations += 1;
  
  // Update average consultation time
  const total = this.dailyStats.completedConsultations;
  const currentAvg = this.dailyStats.averageConsultationMins;
  this.dailyStats.averageConsultationMins = 
    ((currentAvg * (total - 1)) + consultationMins) / total;
  
  this.lastMetricsUpdate = new Date();
  await this.save();
};

// Instance method: Record cancellation
QueueStateSchema.methods.recordCancellation = async function() {
  this.dailyStats.cancelledAppointments += 1;
  this.lastMetricsUpdate = new Date();
  await this.save();
};

// Instance method: Record no-show
QueueStateSchema.methods.recordNoShow = async function() {
  this.dailyStats.noShows += 1;
  this.lastMetricsUpdate = new Date();
  await this.save();
};

// Instance method: Update current metrics
QueueStateSchema.methods.updateMetrics = async function(metrics) {
  this.currentMetrics = {
    ...this.currentMetrics,
    ...metrics,
  };
  this.lastMetricsUpdate = new Date();
  await this.save();
};

// Instance method: Record queue reorder
QueueStateSchema.methods.recordReorder = async function() {
  this.currentMetrics.totalReorders += 1;
  this.currentMetrics.lastReorderTime = new Date();
  await this.save();
};

// Instance method: Reset daily stats (should run at midnight)
QueueStateSchema.methods.resetDailyStats = async function() {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  
  this.dailyStats = {
    date: today,
    totalBookings: 0,
    completedConsultations: 0,
    cancelledAppointments: 0,
    noShows: 0,
    emergencyPatients: 0,
    averageWaitTimeMins: 0,
    averageConsultationMins: 0,
  };
  
  this.lastDailyReset = new Date();
  await this.save();
};

// Static method: Get or create global state
QueueStateSchema.statics.getGlobalState = async function() {
  let state = await this.findOne({ type: 'GLOBAL' });
  
  if (!state) {
    state = await this.create({
      type: 'GLOBAL',
      currentTokenNumber: 0,
      dailyStats: {
        date: new Date(),
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
    });
  }
  
  // Check if we need to reset daily stats
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  
  const stateDate = new Date(state.dailyStats.date);
  stateDate.setHours(0, 0, 0, 0);
  
  if (stateDate < today) {
    await state.resetDailyStats();
  }
  
  return state;
};

// Static method: Get current token number
QueueStateSchema.statics.getCurrentToken = async function() {
  const state = await this.getGlobalState();
  return state.currentTokenNumber;
};

// Static method: Get next token number
QueueStateSchema.statics.getNextToken = async function() {
  const state = await this.getGlobalState();
  return await state.getNextToken();
};

// Static method: Get daily stats
QueueStateSchema.statics.getDailyStats = async function() {
  const state = await this.getGlobalState();
  return state.dailyStats;
};

// Static method: Get current metrics
QueueStateSchema.statics.getCurrentMetrics = async function() {
  const state = await this.getGlobalState();
  return state.currentMetrics;
};

module.exports = mongoose.model('QueueState', QueueStateSchema);
