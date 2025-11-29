const Doctor = require('../schemas/Doctor');
const logger = require('../config/logger');

/**
 * Doctor Model
 * Manages doctor information and availability
 */

class DoctorModel {
  /**
   * Get all doctors
   */
  async getAllDoctors() {
    try {
      let doctors = await Doctor.find({ isActive: true }).sort({ doctorId: 1 });
      
      if (doctors.length === 0) {
        // Create default doctors if none exist
        await this.createDefaultDoctors();
        doctors = await Doctor.find({ isActive: true }).sort({ doctorId: 1 });
      }

      return doctors.map(doc => this.formatDoctor(doc));
    } catch (error) {
      logger.error('Error getting all doctors:', error);
      throw error;
    }
  }

  /**
   * Create default doctors in MongoDB
   */
  async createDefaultDoctors() {
    const defaultDoctors = [
      {
        doctorId: 'DOC_001',
        name: 'Dr. Rajesh Kumar',
        specialization: 'General Physician',
        qualification: 'MBBS, MD',
        experienceYears: 15,
        available: true,
        contact: {
          phone: '+91-9876543210',
          email: 'rajesh.kumar@medisync.health',
        },
        statistics: {
          averageConsultationTime: 15,
        },
        rating: 4.8,
        languages: ['English', 'Hindi', 'Marathi'],
      },
      {
        doctorId: 'DOC_002',
        name: 'Dr. Priya Sharma',
        specialization: 'Pediatrician',
        qualification: 'MBBS, MD (Pediatrics)',
        experienceYears: 10,
        available: true,
        contact: {
          phone: '+91-9876543211',
          email: 'priya.sharma@medisync.health',
        },
        statistics: {
          averageConsultationTime: 20,
        },
        rating: 4.9,
        languages: ['English', 'Hindi'],
      },
      {
        doctorId: 'DOC_003',
        name: 'Dr. Amit Patel',
        specialization: 'Emergency Medicine',
        qualification: 'MBBS, MD (Emergency)',
        experienceYears: 12,
        available: true,
        contact: {
          phone: '+91-9876543212',
          email: 'amit.patel@medisync.health',
        },
        statistics: {
          averageConsultationTime: 10,
        },
        rating: 4.7,
        languages: ['English', 'Hindi', 'Gujarati'],
      },
    ];

    try {
      await Doctor.insertMany(defaultDoctors);
      logger.info('Default doctors created in MongoDB');
    } catch (error) {
      logger.error('Error creating default doctors:', error);
      throw error;
    }
  }

  /**
   * Get doctor by ID
   */
  async getDoctorById(doctorId) {
    try {
      const doctor = await Doctor.findOne({ doctorId, isActive: true });
      
      if (!doctor) {
        return null;
      }

      return this.formatDoctor(doctor);
    } catch (error) {
      logger.error(`Error getting doctor ${doctorId}:`, error);
      throw error;
    }
  }

  /**
   * Format doctor document for API response
   */
  formatDoctor(doctor) {
    return {
      id: doctor.doctorId,
      doctorId: doctor.doctorId,
      name: doctor.name,
      specialization: doctor.specialization,
      qualification: doctor.qualification,
      experienceYears: doctor.experienceYears,
      contact: doctor.contact,
      schedule: doctor.schedule ? Object.fromEntries(doctor.schedule) : {},
      available: doctor.available,
      statistics: doctor.statistics,
      rating: doctor.rating,
      languages: doctor.languages,
      createdAt: doctor.createdAt,
      updatedAt: doctor.updatedAt,
    };
  }

  /**
   * Get available doctors count
   */
  async getAvailableDoctorsCount() {
    try {
      const count = await Doctor.countDocuments({ available: true, isActive: true });
      return count;
    } catch (error) {
      logger.error('Error getting available doctors count:', error);
      return 0;
    }
  }

  /**
   * Add new doctor
   */
  async addDoctor(doctorData) {
    try {
      // Generate doctor ID if not provided
      const lastDoctor = await Doctor.findOne().sort({ doctorId: -1 });
      let nextId = 1;
      
      if (lastDoctor && lastDoctor.doctorId) {
        const match = lastDoctor.doctorId.match(/DOC_(\d+)/);
        if (match) {
          nextId = parseInt(match[1]) + 1;
        }
      }
      
      const doctorId = `DOC_${String(nextId).padStart(3, '0')}`;
      
      const doctor = new Doctor({
        doctorId,
        name: doctorData.name,
        specialization: doctorData.specialization,
        qualification: doctorData.qualification,
        experienceYears: doctorData.experience_years || doctorData.experienceYears,
        contact: doctorData.contact || {},
        schedule: doctorData.schedule,
        available: doctorData.available !== undefined ? doctorData.available : true,
        rating: doctorData.rating || 4.5,
        languages: doctorData.languages || ['English', 'Hindi'],
        isActive: true,
      });

      await doctor.save();
      logger.info(`Doctor ${doctorId} added successfully to MongoDB`);
      
      return this.formatDoctor(doctor);
    } catch (error) {
      logger.error('Error adding doctor:', error);
      throw error;
    }
  }

  /**
   * Update doctor information
   */
  async updateDoctor(doctorId, updateData) {
    try {
      const doctor = await Doctor.findOne({ doctorId, isActive: true });
      
      if (!doctor) {
        throw new Error(`Doctor ${doctorId} not found`);
      }

      // Update fields
      if (updateData.name) doctor.name = updateData.name;
      if (updateData.specialization) doctor.specialization = updateData.specialization;
      if (updateData.qualification) doctor.qualification = updateData.qualification;
      if (updateData.experience_years || updateData.experienceYears) {
        doctor.experienceYears = updateData.experience_years || updateData.experienceYears;
      }
      if (updateData.contact) {
        doctor.contact = { ...doctor.contact, ...updateData.contact };
      }
      if (updateData.schedule) doctor.schedule = new Map(Object.entries(updateData.schedule));
      if (updateData.available !== undefined) doctor.available = updateData.available;
      if (updateData.rating) doctor.rating = updateData.rating;
      if (updateData.languages) doctor.languages = updateData.languages;

      await doctor.save();
      logger.info(`Doctor ${doctorId} updated successfully`);
      
      return this.formatDoctor(doctor);
    } catch (error) {
      logger.error(`Error updating doctor ${doctorId}:`, error);
      throw error;
    }
  }

  /**
   * Toggle doctor availability
   */
  async toggleAvailability(doctorId) {
    try {
      const doctor = await Doctor.findOne({ doctorId, isActive: true });
      
      if (!doctor) {
        throw new Error(`Doctor ${doctorId} not found`);
      }

      await doctor.toggleAvailability();
      logger.info(`Doctor ${doctorId} availability toggled to ${doctor.available}`);
      
      return this.formatDoctor(doctor);
    } catch (error) {
      logger.error(`Error toggling availability for ${doctorId}:`, error);
      throw error;
    }
  }

  /**
   * Get doctor statistics
   */
  async getDoctorStats(doctorId) {
    try {
      const doctor = await Doctor.findOne({ doctorId, isActive: true });
      
      if (!doctor) {
        return {
          doctor_id: doctorId,
          consultations_today: 0,
          consultations_total: 0,
          average_consultation_time: 15,
        };
      }

      return {
        doctor_id: doctorId,
        consultations_today: doctor.statistics.consultationsToday,
        consultations_total: doctor.statistics.totalConsultations,
        average_consultation_time: doctor.statistics.averageConsultationTime,
        last_consultation_date: doctor.statistics.lastConsultationDate,
      };
    } catch (error) {
      logger.error(`Error getting stats for ${doctorId}:`, error);
      throw error;
    }
  }

  /**
   * Update doctor statistics (called after consultation)
   */
  async updateStats(doctorId, consultationTime) {
    try {
      const doctor = await Doctor.findOne({ doctorId, isActive: true });
      
      if (!doctor) {
        throw new Error(`Doctor ${doctorId} not found`);
      }

      await doctor.updateConsultationStats(consultationTime);
      logger.info(`Stats updated for doctor ${doctorId}`);
      
      return {
        doctor_id: doctorId,
        consultations_today: doctor.statistics.consultationsToday,
        consultations_total: doctor.statistics.totalConsultations,
        average_consultation_time: doctor.statistics.averageConsultationTime,
        last_consultation_date: doctor.statistics.lastConsultationDate,
      };
    } catch (error) {
      logger.error(`Error updating stats for ${doctorId}:`, error);
      throw error;
    }
  }

  /**
   * Reset daily statistics (call at midnight)
   */
  async resetDailyStats() {
    try {
      await Doctor.resetAllDailyStats();
      logger.info('Daily doctor statistics reset in MongoDB');
    } catch (error) {
      logger.error('Error resetting daily stats:', error);
      throw error;
    }
  }
}

module.exports = new DoctorModel();
