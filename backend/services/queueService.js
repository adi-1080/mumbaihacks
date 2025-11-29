const Patient = require('../schemas/Patient');
const QueueState = require('../schemas/QueueState');
const logger = require('../config/logger');

/**
 * Queue Service - MongoDB Version
 * This service interacts with MongoDB for all queue operations
 * Migrated from Redis to MongoDB for full persistence
 */

class QueueService {
  /**
   * Get Queue Snapshot from MongoDB
   */
  async getQueueSnapshot() {
    try {
      // Get all active waiting patients, sorted by priority
      const patients = await Patient.getActiveQueue();
      
      if (!patients || patients.length === 0) {
        return {
          total_patients: 0,
          emergency_count: 0,
          main_queue_count: 0,
          patients: [],
        };
      }

      // Format patient data
      const formattedPatients = patients.map(p => ({
        token_number: p.tokenNumber,
        name: p.name,
        contact_number: p.contactNumber,
        symptoms: p.symptoms,
        emergency_level: p.emergencyLevel,
        priority_score: p.priorityScore,
        waiting_time_mins: p.waitingTimeMins,
        travel_eta_mins: p.travelEtaMins,
        predicted_consult_mins: p.predictedConsultMins,
        booking_time: p.bookingTime,
        status: p.status,
      }));

      const emergencyCount = formattedPatients.filter(p => 
        ['PRIORITY', 'CRITICAL'].includes(p.emergency_level)
      ).length;

      return {
        total_patients: formattedPatients.length,
        emergency_count: emergencyCount,
        main_queue_count: formattedPatients.length - emergencyCount,
        patients: formattedPatients,
      };
    } catch (error) {
      logger.error('Error getting queue snapshot from MongoDB:', error);
      throw error;
    }
  }

  /**
   * Get Patient by Token Number from MongoDB
   */
  async getPatientByToken(tokenNumber) {
    try {
      const patient = await Patient.findOne({ tokenNumber });
      
      if (!patient) {
        return null;
      }

      return {
        token_number: patient.tokenNumber,
        name: patient.name,
        contact_number: patient.contactNumber,
        symptoms: patient.symptoms,
        emergency_level: patient.emergencyLevel,
        priority_score: patient.priorityScore,
        waiting_time_mins: patient.waitingTimeMins,
        status: patient.status,
        booking_time: patient.bookingTime,
      };
    } catch (error) {
      logger.error(`Error getting patient ${tokenNumber} from MongoDB:`, error);
      throw error;
    }
  }

  /**
   * Get Current Token Number Counter from MongoDB
   */
  async getCurrentTokenNumber() {
    try {
      const tokenNumber = await QueueState.getCurrentToken();
      return tokenNumber;
    } catch (error) {
      logger.error('Error getting current token number from MongoDB:', error);
      throw error;
    }
  }

  /**
   * Get Next Token Number (for display purposes)
   */
  async getNextTokenNumber() {
    try {
      const currentToken = await this.getCurrentTokenNumber();
      return currentToken + 1;
    } catch (error) {
      logger.error('Error getting next token number from MongoDB:', error);
      throw error;
    }
  }

  /**
   * Get Clinic Statistics from MongoDB
   */
  async getClinicStats() {
    try {
      const [dailyStats, currentToken, queueSnapshot] = await Promise.all([
        QueueState.getDailyStats(),
        QueueState.getCurrentToken(),
        this.getQueueSnapshot(),
      ]);

      return {
        total_bookings_today: dailyStats.totalBookings || 0,
        completed_today: dailyStats.completedConsultations || 0,
        cancelled_today: dailyStats.cancelledAppointments || 0,
        no_shows_today: dailyStats.noShows || 0,
        emergency_patients_today: dailyStats.emergencyPatients || 0,
        current_token_number: currentToken,
        patients_in_queue: queueSnapshot.total_patients,
        emergency_patients: queueSnapshot.emergency_count,
        average_wait_time_mins: dailyStats.averageWaitTimeMins || 0,
        average_consultation_mins: dailyStats.averageConsultationMins || 0,
      };
    } catch (error) {
      logger.error('Error getting clinic stats from MongoDB:', error);
      throw error;
    }
  }

  /**
   * Get Completed Consultations Today from MongoDB
   */
  async getCompletedConsultationsToday() {
    try {
      // Get start of today (midnight)
      const startOfDay = new Date();
      startOfDay.setHours(0, 0, 0, 0);

      // Find all patients completed today
      const completedPatients = await Patient.find({
        status: 'COMPLETED',
        completedAt: { $gte: startOfDay },
      }).sort({ completedAt: -1 }).limit(50); // Last 50 completed

      // Format patient data
      return completedPatients.map(p => ({
        token_number: p.tokenNumber,
        name: p.name,
        contact_number: p.contactNumber,
        symptoms: p.symptoms,
        emergency_level: p.emergencyLevel,
        is_emergency: ['PRIORITY', 'CRITICAL'].includes(p.emergencyLevel),
        urgency_score: p.urgencyScore || 0,
        diagnosis: p.diagnosis || 'N/A',
        completed_at: p.completedAt,
        consultation_duration_mins: p.consultationDurationMins || 0,
      }));
    } catch (error) {
      logger.error('Error getting completed consultations from MongoDB:', error);
      throw error;
    }
  }

  /**
   * Check if patient exists in queue
   */
  async patientExists(tokenNumber) {
    try {
      const patient = await this.getPatientByToken(tokenNumber);
      return patient !== null;
    } catch (error) {
      logger.error(`Error checking patient existence ${tokenNumber}:`, error);
      throw error;
    }
  }

  /**
   * Get Queue Position for a Token
   */
  async getQueuePosition(tokenNumber) {
    try {
      const snapshot = await this.getQueueSnapshot();
      const position = snapshot.patients.findIndex(
        p => p.token_number === tokenNumber
      );
      
      if (position === -1) {
        return null;
      }

      return {
        position: position + 1,
        total_ahead: position,
        estimated_wait_mins: position * 15,
        is_emergency: ['PRIORITY', 'CRITICAL'].includes(
          snapshot.patients[position].emergency_level
        ),
      };
    } catch (error) {
      logger.error(`Error getting queue position for ${tokenNumber}:`, error);
      throw error;
    }
  }

  /**
   * Get patients currently being consulted from MongoDB
   */
  async getOngoingConsultations() {
    try {
      const ongoingPatients = await Patient.getInConsultation();
      
      return ongoingPatients.map(p => ({
        token_number: p.tokenNumber,
        name: p.name,
        contact_number: p.contactNumber,
        symptoms: p.symptoms,
        consultation_start_time: p.consultationStartTime,
        status: p.status,
      }));
    } catch (error) {
      logger.error('Error getting ongoing consultations from MongoDB:', error);
      throw error;
    }
  }
}

module.exports = new QueueService();
