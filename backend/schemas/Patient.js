const mongoose = require('mongoose');

/**
 * Patient Queue Schema - MongoDB version of priority queue patient data
 * Replaces Redis patient_map storage
 */
const PatientSchema = new mongoose.Schema({
  // Core identification
  tokenNumber: {
    type: Number,
    required: [true, 'Token number is required'],
    unique: true,
    index: true,
  },
  
  // Basic patient info
  name: {
    type: String,
    required: [true, 'Patient name is required'],
    trim: true,
    maxlength: 100,
  },
  contactNumber: {
    type: String,
    required: [true, 'Contact number is required'],
    match: [/^\+?[\d\s-()]+$/, 'Invalid contact number format'],
  },
  
  // Medical information
  symptoms: {
    type: String,
    required: [true, 'Symptoms are required'],
  },
  symptomsAnalysis: {
    category: String,
    urgency_score: { type: Number, min: 0, max: 10 },
    priority_category: String,
    estimated_consultation_mins: Number,
    specialist_required: String,
    triage_level: String,
  },
  
  // Location and travel
  location: {
    type: String,
    required: true,
  },
  travelData: {
    origin: {
      latitude: Number,
      longitude: Number,
      address: String,
    },
    clinic: {
      latitude: Number,
      longitude: Number,
      address: String,
    },
    travel_options: {
      driving: {
        distance_km: Number,
        normal_duration_mins: Number,
        traffic_duration_mins: Number,
        traffic_delay_mins: Number,
      },
    },
    astar_eta: {
      method: String,
      travel_time_mins: Number,
      distance_km: Number,
      path_nodes: Number,
    },
  },
  
  // Priority queue attributes
  priorityScore: {
    type: Number,
    required: true,
    index: true,
  },
  emergencyLevel: {
    type: String,
    enum: ['NORMAL', 'PRIORITY', 'CRITICAL'],
    default: 'NORMAL',
    index: true,
  },
  travelEtaMins: {
    type: Number,
    required: true,
    default: 20,
  },
  predictedConsultMins: {
    type: Number,
    default: 15,
  },
  waitingTimeMins: {
    type: Number,
    default: 0,
  },
  arrivalProbability: {
    type: Number,
    min: 0,
    max: 1,
    default: 1.0,
  },
  
  // Timestamps
  bookingTime: {
    type: Date,
    required: true,
    default: Date.now,
  },
  expectedArrival: Date,
  actualArrival: Date,
  lastPriorityUpdate: {
    type: Date,
    default: Date.now,
  },
  
  // Status tracking
  status: {
    type: String,
    enum: ['WAITING', 'IN_CONSULTATION', 'COMPLETED', 'CANCELLED', 'NO_SHOW'],
    default: 'WAITING',
    index: true,
  },
  consultationStartTime: Date,
  consultationEndTime: Date,
  actualConsultationMins: Number,
  
  // Queue position history
  positionHistory: [Number],
  
  // Metadata
  isActive: {
    type: Boolean,
    default: true,
    index: true,
  },
}, {
  timestamps: true, // Adds createdAt, updatedAt
  collection: 'patients',
});

// Indexes for efficient queries
PatientSchema.index({ status: 1, isActive: 1 });
PatientSchema.index({ emergencyLevel: 1, priorityScore: 1 });
PatientSchema.index({ bookingTime: 1 });
// tokenNumber unique index is already defined in schema field

// Virtual: Full patient display
PatientSchema.virtual('displayInfo').get(function() {
  return `Token #${this.tokenNumber} - ${this.name} (${this.emergencyLevel})`;
});

// Instance method: Update priority score
PatientSchema.methods.updatePriority = function(newScore) {
  this.priorityScore = newScore;
  this.lastPriorityUpdate = new Date();
  return this.save();
};

// Instance method: Mark as in consultation
PatientSchema.methods.startConsultation = function() {
  this.status = 'IN_CONSULTATION';
  this.consultationStartTime = new Date();
  return this.save();
};

// Instance method: Mark as completed
PatientSchema.methods.complete = function() {
  this.status = 'COMPLETED';
  this.consultationEndTime = new Date();
  if (this.consultationStartTime) {
    this.actualConsultationMins = Math.round(
      (this.consultationEndTime - this.consultationStartTime) / 60000
    );
  }
  this.isActive = false;
  return this.save();
};

// Static method: Get active queue
PatientSchema.statics.getActiveQueue = function() {
  return this.find({ 
    status: 'WAITING', 
    isActive: true 
  }).sort({ 
    emergencyLevel: -1,  // CRITICAL > PRIORITY > NORMAL
    priorityScore: 1      // Lower score = higher priority
  });
};

// Static method: Get emergency patients
PatientSchema.statics.getEmergencyPatients = function() {
  return this.find({
    emergencyLevel: { $in: ['PRIORITY', 'CRITICAL'] },
    status: 'WAITING',
    isActive: true,
  }).sort({ priorityScore: 1 });
};

// Static method: Get next patient to serve
PatientSchema.statics.getNextPatient = function() {
  return this.findOne({
    status: 'WAITING',
    isActive: true,
  }).sort({
    emergencyLevel: -1,
    priorityScore: 1,
  });
};

// Static method: Get patients in consultation
PatientSchema.statics.getInConsultation = function() {
  return this.find({ 
    status: 'IN_CONSULTATION',
    isActive: true 
  });
};

// Static method: Get daily statistics
PatientSchema.statics.getDailyStats = async function() {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  
  const stats = await this.aggregate([
    {
      $match: {
        bookingTime: { $gte: today },
      },
    },
    {
      $group: {
        _id: '$status',
        count: { $sum: 1 },
      },
    },
  ]);
  
  return stats;
};

// Pre-save hook: Update lastPriorityUpdate when priorityScore changes
PatientSchema.pre('save', function(next) {
  if (this.isModified('priorityScore')) {
    this.lastPriorityUpdate = new Date();
  }
  next();
});

module.exports = mongoose.model('Patient', PatientSchema);
