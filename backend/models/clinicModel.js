const Clinic = require('../schemas/Clinic');
const logger = require('../config/logger');

/**
 * Clinic/Hospital Model
 * Manages clinic/hospital information using MongoDB
 */

class ClinicModel {
  /**
   * Get clinic configuration from MongoDB or create default
   */
  async getClinicInfo() {
    try {
      let clinic = await Clinic.getActiveClinic();
      
      if (!clinic) {
        // Create default clinic if none exists
        clinic = await this.createDefaultClinic();
      }

      return {
        id: clinic._id,
        name: clinic.name,
        address: clinic.address,
        location: {
          latitude: clinic.location.latitude,
          longitude: clinic.location.longitude,
        },
        contact: clinic.contact,
        operatingHours: clinic.operatingHours,
        specializations: clinic.specializations,
        facilities: clinic.facilities,
        createdAt: clinic.createdAt,
        updatedAt: clinic.updatedAt,
      };
    } catch (error) {
      logger.error('Error getting clinic info:', error);
      throw error;
    }
  }

  /**
   * Create default clinic
   */
  async createDefaultClinic() {
    try {
      const defaultClinic = new Clinic({
        name: process.env.CLINIC_NAME || 'MediSync Health Center',
        address: process.env.CLINIC_ADDRESS || 'Lilavati Hospital, Bandra West, Mumbai, Maharashtra, India',
        location: {
          latitude: parseFloat(process.env.CLINIC_LAT || '19.0560'),
          longitude: parseFloat(process.env.CLINIC_LON || '72.8311'),
        },
        contact: {
          phone: '+91-22-2656-1000',
          email: 'info@medisync.health',
          website: 'https://medisync.health',
        },
        operatingHours: {
          monday: '09:00-18:00',
          tuesday: '09:00-18:00',
          wednesday: '09:00-18:00',
          thursday: '09:00-18:00',
          friday: '09:00-18:00',
          saturday: '09:00-14:00',
          sunday: 'Closed',
        },
        specializations: ['General Medicine', 'Pediatrics', 'Emergency Care'],
        facilities: ['24/7 Emergency', 'Pharmacy', 'Laboratory', 'X-Ray'],
        isActive: true,
      });

      await defaultClinic.save();
      logger.info('Default clinic created in MongoDB');
      return defaultClinic;
    } catch (error) {
      logger.error('Error creating default clinic:', error);
      throw error;
    }
  }

  /**
   * Update clinic configuration
   */
  async updateClinicInfo(clinicData) {
    try {
      let clinic = await Clinic.getActiveClinic();
      
      if (!clinic) {
        clinic = await this.createDefaultClinic();
      }

      // Update fields
      if (clinicData.name) clinic.name = clinicData.name;
      if (clinicData.address) clinic.address = clinicData.address;
      if (clinicData.location) {
        if (clinicData.location.latitude) clinic.location.latitude = clinicData.location.latitude;
        if (clinicData.location.longitude) clinic.location.longitude = clinicData.location.longitude;
      }
      if (clinicData.contact) {
        clinic.contact = { ...clinic.contact, ...clinicData.contact };
      }
      if (clinicData.operatingHours) {
        clinic.operatingHours = { ...clinic.operatingHours, ...clinicData.operatingHours };
      }
      if (clinicData.specializations) clinic.specializations = clinicData.specializations;
      if (clinicData.facilities) clinic.facilities = clinicData.facilities;

      await clinic.save();
      logger.info('Clinic configuration updated in MongoDB');
      
      return {
        id: clinic._id,
        name: clinic.name,
        address: clinic.address,
        location: clinic.location,
        contact: clinic.contact,
        operatingHours: clinic.operatingHours,
        specializations: clinic.specializations,
        facilities: clinic.facilities,
      };
    } catch (error) {
      logger.error('Error updating clinic info:', error);
      throw error;
    }
  }

  /**
   * Get clinic location (for maps/travel calculations)
   */
  async getClinicLocation() {
    try {
      const clinic = await Clinic.getActiveClinic();
      
      if (!clinic) {
        const defaultClinic = await this.createDefaultClinic();
        return {
          address: defaultClinic.address,
          latitude: defaultClinic.location.latitude,
          longitude: defaultClinic.location.longitude,
        };
      }

      return {
        address: clinic.address,
        latitude: clinic.location.latitude,
        longitude: clinic.location.longitude,
      };
    } catch (error) {
      logger.error('Error getting clinic location:', error);
      throw error;
    }
  }

  /**
   * Get clinic operating hours for a specific day
   */
  async getOperatingHours(day = new Date().getDay()) {
    try {
      const clinic = await Clinic.getActiveClinic() || await this.createDefaultClinic();
      const dayName = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'][day];
      
      const hours = clinic.getHoursForDay(dayName);
      
      return {
        day: dayName,
        hours: hours,
        status: hours.toLowerCase() === 'closed' ? 'closed' : 'open',
      };
    } catch (error) {
      logger.error('Error getting operating hours:', error);
      throw error;
    }
  }
}

module.exports = new ClinicModel();
