const mongoose = require('mongoose');

/**
 * Clinic Schema
 * Stores hospital/clinic information
 */
const clinicSchema = new mongoose.Schema(
  {
    name: {
      type: String,
      required: [true, 'Clinic name is required'],
      trim: true,
      maxlength: [200, 'Clinic name cannot exceed 200 characters'],
    },
    address: {
      type: String,
      required: [true, 'Address is required'],
      trim: true,
    },
    location: {
      latitude: {
        type: Number,
        required: [true, 'Latitude is required'],
        min: [-90, 'Latitude must be between -90 and 90'],
        max: [90, 'Latitude must be between -90 and 90'],
      },
      longitude: {
        type: Number,
        required: [true, 'Longitude is required'],
        min: [-180, 'Longitude must be between -180 and 180'],
        max: [180, 'Longitude must be between -180 and 180'],
      },
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
      website: {
        type: String,
        trim: true,
      },
    },
    operatingHours: {
      monday: { type: String, default: '09:00-18:00' },
      tuesday: { type: String, default: '09:00-18:00' },
      wednesday: { type: String, default: '09:00-18:00' },
      thursday: { type: String, default: '09:00-18:00' },
      friday: { type: String, default: '09:00-18:00' },
      saturday: { type: String, default: '09:00-14:00' },
      sunday: { type: String, default: 'Closed' },
    },
    specializations: {
      type: [String],
      default: ['General Medicine', 'Pediatrics', 'Emergency Care'],
    },
    facilities: {
      type: [String],
      default: [],
    },
    isActive: {
      type: Boolean,
      default: true,
    },
  },
  {
    timestamps: true,
    collection: 'clinics',
  }
);

// Indexes
clinicSchema.index({ name: 1 });
clinicSchema.index({ 'location.latitude': 1, 'location.longitude': 1 });

// Virtual for full location
clinicSchema.virtual('fullLocation').get(function () {
  return {
    latitude: this.location.latitude,
    longitude: this.location.longitude,
    address: this.address,
  };
});

// Method to get operating hours for a specific day
clinicSchema.methods.getHoursForDay = function (day) {
  const dayLower = day.toLowerCase();
  return this.operatingHours[dayLower] || 'Closed';
};

// Static method to get active clinic
clinicSchema.statics.getActiveClinic = async function () {
  return await this.findOne({ isActive: true });
};

const Clinic = mongoose.model('Clinic', clinicSchema);

module.exports = Clinic;
