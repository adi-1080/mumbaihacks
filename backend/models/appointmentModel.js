const Appointment = require('../schemas/Appointment');
const Patient = require('../schemas/Patient');
const Doctor = require('../schemas/Doctor');
const logger = require('../config/logger');

/**
 * Appointment Model
 * Manages appointment creation, updates, and queries
 */
class AppointmentModel {
  /**
   * Create a new appointment from booking data
   * @param {Object} bookingData - Data from Python booking result
   * @param {Object} requestData - Original request data
   * @returns {Promise<Object>} Created appointment
   */
  async createAppointment(bookingData, requestData) {
    try {
      // Find or create patient
      let patient = await Patient.findOne({ tokenNumber: bookingData.token_number });
      
      if (!patient) {
        logger.warn(`Patient with token ${bookingData.token_number} not found in Patient collection`);
        // Patient might be created by Python script, we'll create a placeholder reference
      }

      // Parse booking result to extract data
      const bookingInfo = this.parseBookingResult(bookingData.result);

      // Create appointment document
      const appointmentData = {
        tokenNumber: bookingData.token_number,
        patient: patient?._id,
        
        patientInfo: {
          name: requestData.name,
          contactNumber: requestData.contact_number,
          age: requestData.age,
          gender: requestData.gender,
        },

        symptoms: requestData.symptoms,
        location: requestData.location,
        
        emergencyLevel: requestData.emergency_level || 'NORMAL',
        urgencyScore: requestData.urgency_score || 5,
        priorityScore: bookingData.priority_score || this.calculatePriorityScore(requestData),

        queuePosition: bookingData.queue_position,
        
        estimatedWaitTime: bookingInfo.estimatedWaitTime || 0,
        estimatedConsultationTime: bookingInfo.estimatedConsultationTime || 15,
        
        bookingTime: bookingInfo.bookingTime || new Date(),
        scheduledTime: bookingInfo.scheduledTime,
        estimatedArrivalTime: bookingInfo.estimatedArrivalTime,

        status: 'scheduled',
        
        metadata: {
          source: 'web',
        },

        orchestration: {
          enabled: true,
          actionsExecuted: [],
          optimizationRuns: 0,
        },
      };

      // Add travel data if available
      if (bookingData.travel_data) {
        appointmentData.travelData = {
          distance_km: bookingData.travel_data.distance_km,
          travel_time_mins: bookingData.travel_data.travel_time_mins,
        };
      }

      // Add symptoms analysis if available
      if (bookingData.symptoms_analysis) {
        appointmentData.symptomsAnalysis = {
          category: bookingData.symptoms_analysis.category,
          urgency_score: bookingData.symptoms_analysis.urgency_score,
          priority_category: bookingData.symptoms_analysis.priority_category,
        };
      }

      const appointment = new Appointment(appointmentData);
      await appointment.save();

      logger.info(`✅ Appointment created: ${appointment.appointmentId} (Token #${appointment.tokenNumber})`);

      return appointment;
    } catch (error) {
      logger.error('Error creating appointment:', error);
      throw error;
    }
  }

  /**
   * Get appointment by token number
   */
  async getByTokenNumber(tokenNumber) {
    try {
      const appointment = await Appointment.findOne({ 
        tokenNumber: parseInt(tokenNumber),
        isActive: true 
      })
      .populate('patient')
      .populate('doctor');

      return appointment;
    } catch (error) {
      logger.error(`Error getting appointment by token ${tokenNumber}:`, error);
      throw error;
    }
  }

  /**
   * Get appointment by ID
   */
  async getById(appointmentId) {
    try {
      const appointment = await Appointment.findOne({ 
        appointmentId,
        isActive: true 
      })
      .populate('patient')
      .populate('doctor');

      return appointment;
    } catch (error) {
      logger.error(`Error getting appointment ${appointmentId}:`, error);
      throw error;
    }
  }

  /**
   * Get all active appointments
   */
  async getActiveAppointments(filters = {}) {
    try {
      const query = {
        status: { $in: ['scheduled', 'confirmed', 'waiting', 'in-progress'] },
        isActive: true,
        ...filters,
      };

      const appointments = await Appointment.find(query)
        .sort({ priorityScore: -1, bookingTime: 1 })
        .populate('patient')
        .populate('doctor');

      return appointments;
    } catch (error) {
      logger.error('Error getting active appointments:', error);
      throw error;
    }
  }

  /**
   * Get today's appointments
   */
  async getTodayAppointments(doctorId = null) {
    try {
      const appointments = await Appointment.getTodayAppointments(doctorId);
      return appointments;
    } catch (error) {
      logger.error('Error getting today\'s appointments:', error);
      throw error;
    }
  }

  /**
   * Get appointments by patient
   */
  async getByPatient(patientId) {
    try {
      const appointments = await Appointment.find({
        patient: patientId,
        isActive: true,
      })
      .sort({ bookingTime: -1 })
      .populate('doctor');

      return appointments;
    } catch (error) {
      logger.error(`Error getting appointments for patient ${patientId}:`, error);
      throw error;
    }
  }

  /**
   * Get appointments by doctor
   */
  async getByDoctor(doctorId) {
    try {
      const appointments = await Appointment.find({
        'doctorInfo.doctorId': doctorId,
        isActive: true,
      })
      .sort({ scheduledTime: 1 })
      .populate('patient');

      return appointments;
    } catch (error) {
      logger.error(`Error getting appointments for doctor ${doctorId}:`, error);
      throw error;
    }
  }

  /**
   * Update appointment status
   */
  async updateStatus(tokenNumber, newStatus) {
    try {
      const appointment = await this.getByTokenNumber(tokenNumber);
      
      if (!appointment) {
        throw new Error(`Appointment with token ${tokenNumber} not found`);
      }

      appointment.status = newStatus;

      // Set timestamps based on status
      switch (newStatus) {
        case 'waiting':
          appointment.arrivalTime = new Date();
          break;
        case 'in-progress':
          appointment.consultationStartTime = new Date();
          break;
        case 'completed':
          appointment.consultationEndTime = new Date();
          break;
      }

      await appointment.save();
      
      logger.info(`Appointment ${appointment.appointmentId} status updated to ${newStatus}`);
      
      return appointment;
    } catch (error) {
      logger.error(`Error updating appointment status:`, error);
      throw error;
    }
  }

  /**
   * Complete appointment
   */
  async completeAppointment(tokenNumber, consultationDetails = {}) {
    try {
      const appointment = await this.getByTokenNumber(tokenNumber);
      
      if (!appointment) {
        throw new Error(`Appointment with token ${tokenNumber} not found`);
      }

      await appointment.markCompleted(consultationDetails);
      
      logger.info(`✅ Appointment ${appointment.appointmentId} completed`);
      
      return appointment;
    } catch (error) {
      logger.error(`Error completing appointment:`, error);
      throw error;
    }
  }

  /**
   * Cancel appointment
   */
  async cancelAppointment(tokenNumber, cancelledBy, reason) {
    try {
      const appointment = await this.getByTokenNumber(tokenNumber);
      
      if (!appointment) {
        throw new Error(`Appointment with token ${tokenNumber} not found`);
      }

      await appointment.cancelAppointment(cancelledBy, reason);
      
      logger.info(`Appointment ${appointment.appointmentId} cancelled by ${cancelledBy}`);
      
      return appointment;
    } catch (error) {
      logger.error(`Error cancelling appointment:`, error);
      throw error;
    }
  }

  /**
   * Add orchestration action to appointment
   */
  async addOrchestrationAction(tokenNumber, action, status, details = {}) {
    try {
      const appointment = await this.getByTokenNumber(tokenNumber);
      
      if (!appointment) {
        logger.warn(`Appointment with token ${tokenNumber} not found for orchestration tracking`);
        return null;
      }

      await appointment.addOrchestrationAction(action, status, details);
      
      return appointment;
    } catch (error) {
      logger.error(`Error adding orchestration action:`, error);
      // Don't throw - orchestration tracking is non-critical
      return null;
    }
  }

  /**
   * Update queue position
   */
  async updateQueuePosition(tokenNumber, newPosition) {
    try {
      const appointment = await Appointment.findOneAndUpdate(
        { tokenNumber: parseInt(tokenNumber), isActive: true },
        { 
          queuePosition: newPosition,
          updatedAt: new Date(),
        },
        { new: true }
      );

      if (appointment) {
        logger.info(`Queue position updated for token ${tokenNumber}: ${newPosition}`);
      }

      return appointment;
    } catch (error) {
      logger.error(`Error updating queue position:`, error);
      throw error;
    }
  }

  /**
   * Update estimated wait time
   */
  async updateEstimatedWaitTime(tokenNumber, waitTimeMins) {
    try {
      const appointment = await Appointment.findOneAndUpdate(
        { tokenNumber: parseInt(tokenNumber), isActive: true },
        { 
          estimatedWaitTime: waitTimeMins,
          updatedAt: new Date(),
        },
        { new: true }
      );

      return appointment;
    } catch (error) {
      logger.error(`Error updating wait time:`, error);
      throw error;
    }
  }

  /**
   * Get appointment statistics
   */
  async getStatistics(filters = {}) {
    try {
      const today = new Date();
      today.setHours(0, 0, 0, 0);

      const stats = await Appointment.aggregate([
        {
          $match: {
            isActive: true,
            bookingTime: { $gte: today },
            ...filters,
          }
        },
        {
          $group: {
            _id: '$status',
            count: { $sum: 1 },
            avgWaitTime: { $avg: '$estimatedWaitTime' },
            avgPriorityScore: { $avg: '$priorityScore' },
          }
        }
      ]);

      return stats;
    } catch (error) {
      logger.error('Error getting appointment statistics:', error);
      throw error;
    }
  }

  /**
   * Parse booking result string to extract structured data
   */
  parseBookingResult(resultString) {
    const info = {
      bookingTime: new Date(),
      estimatedWaitTime: 0,
      estimatedConsultationTime: 15,
    };

    if (!resultString) return info;

    // Extract wait time (e.g., "Estimated Wait Time: 384 minutes")
    const waitMatch = resultString.match(/Estimated Wait Time:\s*(\d+)\s*minutes/i);
    if (waitMatch) {
      info.estimatedWaitTime = parseInt(waitMatch[1]);
    }

    // Extract ETA (e.g., "Estimated Time of Appointment: 08:55 IST")
    const etaMatch = resultString.match(/Estimated Time of Appointment:\s*(\d{2}:\d{2})/i);
    if (etaMatch) {
      const [hours, minutes] = etaMatch[1].split(':').map(Number);
      const eta = new Date();
      eta.setHours(hours, minutes, 0, 0);
      info.estimatedArrivalTime = eta;
      info.scheduledTime = eta;
    }

    return info;
  }

  /**
   * Calculate priority score from request data
   */
  calculatePriorityScore(requestData) {
    let score = 50; // Base score

    // Add urgency component
    if (requestData.urgency_score) {
      score += requestData.urgency_score * 3;
    }

    // Add emergency level component
    const emergencyMultipliers = {
      'CRITICAL': 30,
      'HIGH': 20,
      'PRIORITY': 15,
      'MODERATE': 10,
      'NORMAL': 0,
    };
    score += emergencyMultipliers[requestData.emergency_level] || 0;

    return score;
  }

  /**
   * Format appointment for API response
   */
  formatAppointment(appointment) {
    if (!appointment) return null;

    return {
      appointmentId: appointment.appointmentId,
      tokenNumber: appointment.tokenNumber,
      patient: {
        name: appointment.patientInfo.name,
        contact: appointment.patientInfo.contactNumber,
        age: appointment.patientInfo.age,
        gender: appointment.patientInfo.gender,
      },
      doctor: appointment.doctorInfo ? {
        id: appointment.doctorInfo.doctorId,
        name: appointment.doctorInfo.name,
        specialization: appointment.doctorInfo.specialization,
      } : null,
      symptoms: appointment.symptoms,
      location: appointment.location,
      priority: {
        score: appointment.priorityScore,
        urgencyScore: appointment.urgencyScore,
        emergencyLevel: appointment.emergencyLevel,
      },
      queue: {
        position: appointment.queuePosition,
        estimatedWaitTime: appointment.estimatedWaitTime,
      },
      timing: {
        bookingTime: appointment.bookingTime,
        scheduledTime: appointment.scheduledTime,
        estimatedArrivalTime: appointment.estimatedArrivalTime,
      },
      status: appointment.status,
      orchestration: appointment.orchestration ? {
        actionsCount: appointment.orchestration.actionsExecuted?.length || 0,
        lastAction: appointment.orchestration.actionsExecuted?.slice(-1)[0],
      } : null,
      createdAt: appointment.createdAt,
      updatedAt: appointment.updatedAt,
    };
  }
}

module.exports = new AppointmentModel();
