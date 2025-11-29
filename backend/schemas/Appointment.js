const mongoose = require('mongoose');

/**
 * Appointment Schema
 * Links patients with doctors and tracks appointment lifecycle
 */
const appointmentSchema = new mongoose.Schema(
  {
    // Core identification
    tokenNumber: {
      type: Number,
      required: [true, 'Token number is required'],
      unique: true,
      index: true,
    },
    appointmentId: {
      type: String,
      unique: true,
      index: true,
    },

    // Patient reference (optional - not all bookings have patient account)
    patient: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'Patient',
      index: true,
    },
    
    // Patient snapshot (for quick access without population)
    patientInfo: {
      name: {
        type: String,
        required: true,
        trim: true,
      },
      contactNumber: {
        type: String,
        required: true,
      },
      age: Number,
      gender: {
        type: String,
        enum: ['Male', 'Female', 'Other'],
      },
    },

    // Doctor reference
    doctor: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'Doctor',
      index: true,
    },
    doctorInfo: {
      doctorId: String,
      name: String,
      specialization: String,
      hospital: String,
      fee: String,
    },

    // Medical details
    symptoms: {
      type: String,
      required: [true, 'Symptoms are required'],
    },
    symptomsAnalysis: {
      category: String,
      urgency_score: { 
        type: Number, 
        min: 0, 
        max: 10 
      },
      priority_category: String,
      estimated_consultation_mins: Number,
      specialist_required: String,
      triage_level: String,
    },

    // Priority and urgency
    emergencyLevel: {
      type: String,
      enum: ['NORMAL', 'MODERATE', 'HIGH', 'PRIORITY', 'CRITICAL'],
      default: 'NORMAL',
      index: true,
    },
    urgencyScore: {
      type: Number,
      min: 1,
      max: 10,
      default: 5,
    },
    priorityScore: {
      type: Number,
      required: true,
      index: true,
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
      distance_km: Number,
      travel_time_mins: Number,
      traffic_duration_mins: Number,
      traffic_delay_mins: Number,
    },

    // Queue management
    queuePosition: {
      type: Number,
      index: true,
    },
    queueType: {
      type: String,
      enum: ['main', 'priority', 'walk-in'],
      default: 'main',
    },
    estimatedWaitTime: {
      type: Number, // in minutes
      default: 0,
    },
    estimatedConsultationTime: {
      type: Number, // in minutes
      default: 15,
    },

    // Appointment timing
    bookingTime: {
      type: Date,
      default: Date.now,
      index: true,
    },
    scheduledTime: {
      type: Date,
      index: true,
    },
    arrivalTime: Date,
    consultationStartTime: Date,
    consultationEndTime: Date,
    estimatedArrivalTime: Date,

    // Status tracking
    status: {
      type: String,
      enum: [
        'scheduled',     // Initial booking
        'confirmed',     // Confirmed by patient
        'waiting',       // Patient in waiting room
        'in-progress',   // Consultation ongoing
        'completed',     // Consultation finished
        'cancelled',     // Cancelled by patient/clinic
        'no-show',       // Patient didn't arrive
        'rescheduled'    // Appointment rescheduled
      ],
      default: 'scheduled',
      index: true,
    },
    
    // Orchestration tracking
    orchestration: {
      enabled: {
        type: Boolean,
        default: true,
      },
      actionsExecuted: [{
        action: String,
        timestamp: Date,
        status: String,
        details: mongoose.Schema.Types.Mixed,
      }],
      etaCalculated: {
        type: Boolean,
        default: false,
      },
      notificationsSent: [{
        type: {
          type: String,
          enum: ['sms', 'email', 'push'],
        },
        sentAt: Date,
        status: String,
      }],
      optimizationRuns: Number,
    },

    // Consultation details (filled after completion)
    consultation: {
      diagnosis: String,
      prescription: String,
      notes: String,
      followUpRequired: Boolean,
      followUpDate: Date,
      referralRequired: Boolean,
      referralTo: String,
    },

    // Billing
    billing: {
      consultationFee: {
        type: Number,
        default: 500,
      },
      additionalCharges: Number,
      totalAmount: Number,
      paymentStatus: {
        type: String,
        enum: ['pending', 'paid', 'refunded'],
        default: 'pending',
      },
      paymentMethod: String,
      paidAt: Date,
    },

    // Cancellation details
    cancellation: {
      cancelledAt: Date,
      cancelledBy: {
        type: String,
        enum: ['patient', 'doctor', 'admin'],
      },
      reason: String,
    },

    // Metadata
    metadata: {
      source: {
        type: String,
        enum: ['web', 'mobile', 'walk-in', 'phone'],
        default: 'web',
      },
      deviceInfo: String,
      ipAddress: String,
      userAgent: String,
    },

    // Soft delete
    isActive: {
      type: Boolean,
      default: true,
      index: true,
    },
    deletedAt: Date,
  },
  {
    timestamps: true, // Adds createdAt and updatedAt
    toJSON: { virtuals: true },
    toObject: { virtuals: true },
  }
);

// Indexes for performance
appointmentSchema.index({ tokenNumber: 1, status: 1 });
appointmentSchema.index({ patient: 1, status: 1 });
appointmentSchema.index({ doctor: 1, status: 1 });
appointmentSchema.index({ bookingTime: -1 });
appointmentSchema.index({ scheduledTime: 1, status: 1 });
appointmentSchema.index({ emergencyLevel: 1, priorityScore: -1 });

// Virtual for total duration
appointmentSchema.virtual('totalDuration').get(function() {
  if (this.consultationStartTime && this.consultationEndTime) {
    return Math.round((this.consultationEndTime - this.consultationStartTime) / 60000); // in minutes
  }
  return null;
});

// Virtual for wait duration
appointmentSchema.virtual('actualWaitTime').get(function() {
  if (this.arrivalTime && this.consultationStartTime) {
    return Math.round((this.consultationStartTime - this.arrivalTime) / 60000); // in minutes
  }
  return null;
});

// Pre-save hook to generate appointmentId
appointmentSchema.pre('save', async function() {
  if (!this.appointmentId) {
    const date = new Date();
    const dateStr = date.toISOString().split('T')[0].replace(/-/g, '');
    this.appointmentId = `APT-${dateStr}-${this.tokenNumber.toString().padStart(4, '0')}`;
  }
});

// Pre-save hook to calculate total billing amount
appointmentSchema.pre('save', async function() {
  if (this.billing && this.billing.consultationFee) {
    this.billing.totalAmount = 
      (this.billing.consultationFee || 0) + 
      (this.billing.additionalCharges || 0);
  }
});

// Static method to get today's appointments
appointmentSchema.statics.getTodayAppointments = function(doctorId = null) {
  const startOfDay = new Date();
  startOfDay.setHours(0, 0, 0, 0);
  
  const endOfDay = new Date();
  endOfDay.setHours(23, 59, 59, 999);

  const query = {
    bookingTime: { $gte: startOfDay, $lte: endOfDay },
    isActive: true,
  };

  if (doctorId) {
    query['doctorInfo.doctorId'] = doctorId;
  }

  return this.find(query).sort({ bookingTime: -1 });
};

// Static method to get active appointments
appointmentSchema.statics.getActiveAppointments = function() {
  return this.find({
    status: { $in: ['scheduled', 'confirmed', 'waiting', 'in-progress'] },
    isActive: true,
  }).sort({ priorityScore: -1, bookingTime: 1 });
};

// Instance method to mark as completed
appointmentSchema.methods.markCompleted = function(consultationDetails = {}) {
  this.status = 'completed';
  this.consultationEndTime = new Date();
  if (consultationDetails.diagnosis) {
    this.consultation = {
      ...this.consultation,
      ...consultationDetails,
    };
  }
  return this.save();
};

// Instance method to cancel appointment
appointmentSchema.methods.cancelAppointment = function(cancelledBy, reason) {
  this.status = 'cancelled';
  this.cancellation = {
    cancelledAt: new Date(),
    cancelledBy,
    reason,
  };
  return this.save();
};

// Instance method to add orchestration action
appointmentSchema.methods.addOrchestrationAction = function(action, status, details = {}) {
  if (!this.orchestration) {
    this.orchestration = { actionsExecuted: [] };
  }
  if (!this.orchestration.actionsExecuted) {
    this.orchestration.actionsExecuted = [];
  }
  
  this.orchestration.actionsExecuted.push({
    action,
    timestamp: new Date(),
    status,
    details,
  });
  
  return this.save();
};

const Appointment = mongoose.model('Appointment', appointmentSchema);

module.exports = Appointment;
