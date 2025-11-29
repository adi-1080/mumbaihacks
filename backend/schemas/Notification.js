const mongoose = require('mongoose');

/**
 * Notification Schema - Track all patient notifications
 * Replaces Redis notification storage
 */
const NotificationSchema = new mongoose.Schema({
  // Patient identification
  tokenNumber: {
    type: Number,
    required: [true, 'Token number is required'],
    index: true,
  },
  patientName: {
    type: String,
    required: true,
  },
  contactNumber: {
    type: String,
    required: true,
  },
  
  // Notification details
  type: {
    type: String,
    required: true,
    enum: [
      'BOOKING_CONFIRMATION',
      'QUEUE_UPDATE',
      'APPOINTMENT_READY',
      'ETA_UPDATE',
      'POSITION_CHANGE',
      'REMINDER',
      'CANCELLATION',
      'COMPLETION',
    ],
    index: true,
  },
  
  // Message content
  title: {
    type: String,
    required: true,
  },
  message: {
    type: String,
    required: true,
  },
  
  // Notification data
  data: {
    queuePosition: Number,
    estimatedWaitMins: Number,
    etaMins: Number,
    priorityScore: Number,
    emergencyLevel: String,
    optimalDepartureTime: Date,
  },
  
  // Delivery tracking
  status: {
    type: String,
    enum: ['PENDING', 'SENT', 'DELIVERED', 'FAILED', 'READ'],
    default: 'PENDING',
    index: true,
  },
  channel: {
    type: String,
    enum: ['SMS', 'EMAIL', 'PUSH', 'WHATSAPP', 'IN_APP'],
    default: 'IN_APP',
  },
  
  // Timestamps
  scheduledFor: Date,
  sentAt: Date,
  deliveredAt: Date,
  readAt: Date,
  
  // Metadata
  priority: {
    type: String,
    enum: ['LOW', 'NORMAL', 'HIGH', 'URGENT'],
    default: 'NORMAL',
  },
  retryCount: {
    type: Number,
    default: 0,
  },
  errorMessage: String,
}, {
  timestamps: true,
  collection: 'notifications',
});

// Indexes for efficient queries
NotificationSchema.index({ tokenNumber: 1, createdAt: -1 });
NotificationSchema.index({ status: 1, scheduledFor: 1 });
NotificationSchema.index({ type: 1, createdAt: -1 });
NotificationSchema.index({ createdAt: -1 });

// Virtual: Display info
NotificationSchema.virtual('displayInfo').get(function() {
  return `[${this.type}] Token #${this.tokenNumber} - ${this.title}`;
});

// Instance method: Mark as sent
NotificationSchema.methods.markSent = function() {
  this.status = 'SENT';
  this.sentAt = new Date();
  return this.save();
};

// Instance method: Mark as delivered
NotificationSchema.methods.markDelivered = function() {
  this.status = 'DELIVERED';
  this.deliveredAt = new Date();
  return this.save();
};

// Instance method: Mark as read
NotificationSchema.methods.markRead = function() {
  this.status = 'READ';
  this.readAt = new Date();
  return this.save();
};

// Instance method: Mark as failed
NotificationSchema.methods.markFailed = function(error) {
  this.status = 'FAILED';
  this.errorMessage = error;
  this.retryCount += 1;
  return this.save();
};

// Static method: Get notifications for patient
NotificationSchema.statics.getPatientNotifications = function(tokenNumber) {
  return this.find({ tokenNumber })
    .sort({ createdAt: -1 })
    .limit(50);
};

// Static method: Get pending notifications
NotificationSchema.statics.getPending = function() {
  return this.find({
    status: 'PENDING',
    $or: [
      { scheduledFor: null },
      { scheduledFor: { $lte: new Date() } },
    ],
  }).sort({ priority: -1, scheduledFor: 1 });
};

// Static method: Get recent notifications
NotificationSchema.statics.getRecent = function(limit = 100) {
  return this.find()
    .sort({ createdAt: -1 })
    .limit(limit);
};

// Static method: Get notifications by type
NotificationSchema.statics.getByType = function(type, limit = 50) {
  return this.find({ type })
    .sort({ createdAt: -1 })
    .limit(limit);
};

// Static method: Get failed notifications (for retry)
NotificationSchema.statics.getFailed = function() {
  return this.find({
    status: 'FAILED',
    retryCount: { $lt: 3 },
  }).sort({ createdAt: 1 });
};

// Static method: Get daily notification stats
NotificationSchema.statics.getDailyStats = async function() {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  
  const stats = await this.aggregate([
    {
      $match: {
        createdAt: { $gte: today },
      },
    },
    {
      $group: {
        _id: {
          type: '$type',
          status: '$status',
        },
        count: { $sum: 1 },
      },
    },
  ]);
  
  return stats;
};

// Pre-save hook: Set sentAt if status changed to SENT
NotificationSchema.pre('save', function(next) {
  if (this.isModified('status') && this.status === 'SENT' && !this.sentAt) {
    this.sentAt = new Date();
  }
  next();
});

module.exports = mongoose.model('Notification', NotificationSchema);
