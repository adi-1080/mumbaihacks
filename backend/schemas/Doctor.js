const mongoose = require('mongoose');

/**
 * Doctor Schema
 * Stores doctor information and statistics
 */
const doctorSchema = new mongoose.Schema(
  {
    doctorId: {
      type: String,
      required: [true, 'Doctor ID is required'],
      unique: true,
      trim: true,
      uppercase: true,
      match: [/^DOC_\d{3}$/, 'Doctor ID must be in format DOC_XXX'],
    },
    name: {
      type: String,
      required: [true, 'Doctor name is required'],
      trim: true,
      maxlength: [100, 'Name cannot exceed 100 characters'],
    },
    specialization: {
      type: String,
      required: [true, 'Specialization is required'],
      trim: true,
    },
    qualification: {
      type: String,
      required: [true, 'Qualification is required'],
      trim: true,
    },
    experienceYears: {
      type: Number,
      required: [true, 'Experience years is required'],
      min: [0, 'Experience years cannot be negative'],
      max: [70, 'Experience years cannot exceed 70'],
    },
    contact: {
      phone: {
        type: String,
        trim: true,
      },
      email: {
        type: String,
        trim: true,
        lowercase: true,
        match: [/^\S+@\S+\.\S+$/, 'Please enter a valid email address'],
      },
    },
    schedule: {
      type: Map,
      of: String,
      default: new Map([
        ['monday', '09:00-18:00'],
        ['tuesday', '09:00-18:00'],
        ['wednesday', '09:00-18:00'],
        ['thursday', '09:00-18:00'],
        ['friday', '09:00-18:00'],
        ['saturday', '09:00-14:00'],
        ['sunday', 'Off'],
      ]),
    },
    available: {
      type: Boolean,
      default: true,
    },
    statistics: {
      consultationsToday: {
        type: Number,
        default: 0,
        min: 0,
      },
      totalConsultations: {
        type: Number,
        default: 0,
        min: 0,
      },
      averageConsultationTime: {
        type: Number,
        default: 15,
        min: 0,
      },
      lastConsultationDate: {
        type: Date,
        default: null,
      },
    },
    rating: {
      type: Number,
      default: 4.5,
      min: [0, 'Rating cannot be less than 0'],
      max: [5, 'Rating cannot exceed 5'],
    },
    languages: {
      type: [String],
      default: ['English', 'Hindi'],
    },
    isActive: {
      type: Boolean,
      default: true,
    },
  },
  {
    timestamps: true,
    collection: 'doctors',
  }
);

// Indexes (doctorId unique index already defined in schema field)
doctorSchema.index({ specialization: 1 });
doctorSchema.index({ available: 1, isActive: 1 });

// Virtual for full name with qualification
doctorSchema.virtual('fullName').get(function () {
  return `${this.name}, ${this.qualification}`;
});

// Method to toggle availability
doctorSchema.methods.toggleAvailability = async function () {
  this.available = !this.available;
  return await this.save();
};

// Method to update statistics after consultation
doctorSchema.methods.updateConsultationStats = async function (consultationTime) {
  this.statistics.consultationsToday += 1;
  this.statistics.totalConsultations += 1;
  this.statistics.lastConsultationDate = new Date();

  // Update average consultation time
  const total = this.statistics.totalConsultations;
  const currentAvg = this.statistics.averageConsultationTime;
  this.statistics.averageConsultationTime = Math.round(
    (currentAvg * (total - 1) + consultationTime) / total
  );

  return await this.save();
};

// Method to reset daily stats (should be called at midnight)
doctorSchema.methods.resetDailyStats = async function () {
  this.statistics.consultationsToday = 0;
  return await this.save();
};

// Static method to get available doctors
doctorSchema.statics.getAvailableDoctors = async function () {
  return await this.find({ available: true, isActive: true });
};

// Static method to get doctor by specialization
doctorSchema.statics.getBySpecialization = async function (specialization) {
  return await this.find({
    specialization: new RegExp(specialization, 'i'),
    isActive: true,
  });
};

// Static method to reset all daily stats
doctorSchema.statics.resetAllDailyStats = async function () {
  return await this.updateMany(
    {},
    { $set: { 'statistics.consultationsToday': 0 } }
  );
};

const Doctor = mongoose.model('Doctor', doctorSchema);

module.exports = Doctor;
