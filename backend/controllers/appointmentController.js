const queueService = require('../services/queueService');
const pythonBridge = require('../services/pythonBridge');
const logger = require('../config/logger');
const { orchestrationService } = require('../middleware/orchestration');
const { formatBookingResponse, formatCompletionResponse } = require('../utils/responseFormatter');
const Appointment = require('../schemas/Appointment');

/**
 * Book a new appointment
 * POST /api/v1/appointments/book
 * WITH INTELLIGENT ORCHESTRATION (mimics root_agent behavior)
 */
exports.bookAppointment = async (req, res) => {
  try {
    const {
      name,
      contact_number,
      symptoms,
      location,
      age,
      gender,
      emergency_level,
      urgency_score,
    } = req.body;
    // Validate required fields
    if (!name || !contact_number || !symptoms) {
      return res.status(400).json({
        success: false,
        message: 'Name, contact number, and symptoms are required',
      });
    }
    console.log("Hello World!!!");

    // Call Python booking tool
    const appointmentData = {
      name,
      contact_number,
      symptoms,
      location: location || 'Not provided',
      age: age || null,
      gender: gender || null,
      emergency_level: emergency_level || 'NORMAL',
      urgency_score: urgency_score || null,
    };

    const result = await pythonBridge.bookAppointment(appointmentData);

    logger.info(`Appointment booked: Token #${result.token_number}`);

    // 💾 SAVE APPOINTMENT TO DATABASE
    let appointment = null;
    try {
      // Structure data according to Appointment schema
      const appointmentDoc = {
        tokenNumber: result.token_number,
        patientInfo: {
          name: appointmentData.name,
          contactNumber: appointmentData.contact_number,
          age: appointmentData.age,
          gender: appointmentData.gender,
        },
        doctorInfo: {
          name: req.body.doctor_name || 'Dr. Assigned',
          specialization: req.body.doctor_specialty || 'General Physician',
          hospital: req.body.doctor_hospital || 'Clinic Location',
          fee: req.body.doctor_fee || 'Rs. 500/-',
        },
        symptoms: appointmentData.symptoms,
        location: appointmentData.location,
        emergencyLevel: appointmentData.emergency_level || 'NORMAL',
        urgencyScore: appointmentData.urgency_score || 5,
        priorityScore: result.priority_score || 50,
        queuePosition: result.queue_position,
        status: 'scheduled',
        orchestration: {
          enabled: true,
          actionsExecuted: [],
          optimizationRuns: 0,
        },
      };

      // Add optional fields from result if available
      if (result.symptoms_analysis) {
        appointmentDoc.symptomsAnalysis = {
          category: result.symptoms_analysis.category,
          urgency_score: result.symptoms_analysis.urgency_score,
          priority_category: result.symptoms_analysis.priority_category,
        };
      }

      if (result.travel_data) {
        appointmentDoc.travelData = {
          distance_km: result.travel_data.distance_km,
          travel_time_mins: result.travel_data.travel_time_mins,
        };
      }

      appointment = await Appointment.create(appointmentDoc);
      console.log("Saved to DB");
      logger.info(`✅ Appointment saved to database: ${appointment.appointmentId}`);
    } catch (dbError) {
      logger.error('Failed to save appointment to database (non-critical):', dbError);
      // Continue even if DB save fails - booking is already in queue
    }

    // 🧠 INTELLIGENT ORCHESTRATION - Auto-trigger follow-up actions
    // Mimics root_agent's proactive behavior
    let orchestrationResults = null;
    try {
      orchestrationResults = await orchestrationService.executePostBookingOrchestration(
        result, 
        appointmentData
      );
      
      logger.info(`✅ Orchestration complete: ${orchestrationResults.followUpActions.length} automatic actions executed`);
      
      // Track orchestration in appointment
      if (appointment && orchestrationResults.followUpActions) {
        for (const action of orchestrationResults.followUpActions) {
          await appointment.addOrchestrationAction(
            action.action,
            action.status,
            action.result
          );
        }
      }
    } catch (error) {
      logger.error('Orchestration failed (non-critical):', error);
    }

    // Format response for clean, structured output
    const formattedResponse = formatBookingResponse(result, orchestrationResults);
    
    // Add appointment ID to response
    if (appointment) {
      formattedResponse.appointmentId = appointment.appointmentId;
      formattedResponse.appointmentDetails = {
        tokenNumber: appointment.tokenNumber,
        appointmentId: appointment.appointmentId,
        patientInfo: appointment.patientInfo,
        symptoms: appointment.symptoms,
        location: appointment.location,
        status: appointment.status,
        queuePosition: appointment.queuePosition,
        emergencyLevel: appointment.emergencyLevel,
        bookingTime: appointment.bookingTime,
      };
    }
    
    res.status(201).json(formattedResponse);
  } catch (error) {
    // logger.error('Error in bookAppointment controller:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to book appointment',
      error: error.message,
    });
  }
};

/**
 * Cancel an appointment
 * DELETE /api/v1/appointments/:tokenNumber
 */
exports.cancelAppointment = async (req, res) => {
  try {
    const { tokenNumber } = req.params;

    if (!tokenNumber || isNaN(tokenNumber)) {
      return res.status(400).json({
        success: false,
        message: 'Valid token number is required',
      });
    }

    // Check if patient exists
    const exists = await queueService.patientExists(parseInt(tokenNumber));
    if (!exists) {
      return res.status(404).json({
        success: false,
        message: `Patient with token #${tokenNumber} not found`,
      });
    }

    const result = await pythonBridge.cancelAppointment(parseInt(tokenNumber));

    logger.info(`Appointment canceled: Token #${tokenNumber}`);

    // 💾 UPDATE APPOINTMENT STATUS IN DATABASE
    try {
      const appointment = await Appointment.findOne({ tokenNumber: parseInt(tokenNumber) });
      if (appointment) {
        await appointment.cancelAppointment('patient', 'Cancelled by patient request');
        logger.info(`✅ Appointment marked as cancelled in database`);
      }
    } catch (dbError) {
      logger.error('Failed to update appointment cancellation in database (non-critical):', dbError);
    }

    res.json({
      success: true,
      message: `Appointment for token #${tokenNumber} canceled successfully`,
      data: result,
    });
  } catch (error) {
    logger.error('Error in cancelAppointment controller:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to cancel appointment',
      error: error.message,
    });
  }
};

/**
 * Get appointment details by token number
 * GET /api/v1/appointments/:tokenNumber
 */
exports.getAppointment = async (req, res) => {
  try {
    const { tokenNumber } = req.params;

    if (!tokenNumber || isNaN(tokenNumber)) {
      return res.status(400).json({
        success: false,
        message: 'Valid token number is required',
      });
    }

    // Try to get from appointment database first
    let appointment = await Appointment.findOne({ tokenNumber: parseInt(tokenNumber) })
      .populate('patient')
      .populate('doctor');
    
    if (appointment) {
      // Get latest queue position from queue service
      const position = await queueService.getQueuePosition(parseInt(tokenNumber));
      
      // Update appointment if position changed
      if (position !== appointment.queuePosition) {
        appointment.queuePosition = position;
        await appointment.save();
      }

      return res.json({
        success: true,
        data: {
          tokenNumber: appointment.tokenNumber,
          appointmentId: appointment.appointmentId,
          patientInfo: appointment.patientInfo,
          symptoms: appointment.symptoms,
          location: appointment.location,
          status: appointment.status,
          queuePosition: appointment.queuePosition,
          emergencyLevel: appointment.emergencyLevel,
          bookingTime: appointment.bookingTime,
        },
      });
    }

    // Fallback to queue service if not in appointments DB
    const patient = await queueService.getPatientByToken(parseInt(tokenNumber));

    if (!patient) {
      return res.status(404).json({
        success: false,
        message: `Patient with token #${tokenNumber} not found`,
      });
    }

    // Get queue position
    const position = await queueService.getQueuePosition(parseInt(tokenNumber));

    res.json({
      success: true,
      data: {
        ...patient,
        queue_position: position,
      },
    });
  } catch (error) {
    logger.error('Error in getAppointment controller:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to get appointment details',
      error: error.message,
    });
  }
};

/**
 * Update patient location
 * PATCH /api/v1/appointments/:tokenNumber/location
 * WITH INTELLIGENT ORCHESTRATION (mimics root_agent behavior)
 */
exports.updateLocation = async (req, res) => {
  try {
    const { tokenNumber } = req.params;
    const { latitude, longitude, address } = req.body;

    if (!tokenNumber || isNaN(tokenNumber)) {
      return res.status(400).json({
        success: false,
        message: 'Valid token number is required',
      });
    }

    if (!latitude || !longitude) {
      return res.status(400).json({
        success: false,
        message: 'Latitude and longitude are required',
      });
    }

    const exists = await queueService.patientExists(parseInt(tokenNumber));
    if (!exists) {
      return res.status(404).json({
        success: false,
        message: `Patient with token #${tokenNumber} not found`,
      });
    }

    const location = { latitude, longitude, address };
    const result = await pythonBridge.updateLocation(parseInt(tokenNumber), location);

    logger.info(`Location updated for token #${tokenNumber}`);

    // 💾 UPDATE LOCATION IN DATABASE
    try {
      const appointment = await Appointment.findOne({ tokenNumber: parseInt(tokenNumber) });
      if (appointment) {
        appointment.location = address || `${latitude}, ${longitude}`;
        appointment.travelData = {
          ...appointment.travelData,
          origin: { latitude, longitude, address },
        };
        await appointment.save();
        logger.info(`✅ Location updated in database`);
      }
    } catch (dbError) {
      logger.error('Failed to update location in database (non-critical):', dbError);
    }

    // 🧠 INTELLIGENT ORCHESTRATION - Auto-optimize if high priority
    // Automatically recalculates arrival time and reoptimizes queue if needed
    let orchestrationResults = null;
    try {
      orchestrationResults = await orchestrationService.executePostLocationUpdateOrchestration(
        result,
        parseInt(tokenNumber),
        location
      );
      
      logger.info(`✅ Post-location-update orchestration: ${orchestrationResults.followUpActions.length} actions executed`);
    } catch (error) {
      logger.error('Post-location orchestration failed (non-critical):', error);
    }

    res.json({
      success: true,
      message: 'Location updated successfully',
      data: result,
      orchestration: orchestrationResults ? {
        enabled: true,
        actions_executed: orchestrationResults.followUpActions.length,
        details: orchestrationResults.followUpActions,
      } : null,
    });
  } catch (error) {
    logger.error('Error in updateLocation controller:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to update location',
      error: error.message,
    });
  }
};

/**
 * Complete patient consultation
 * POST /api/v1/appointments/:tokenNumber/complete
 * WITH INTELLIGENT ORCHESTRATION (mimics root_agent behavior)
 */
exports.completeConsultation = async (req, res) => {
  try {
    const { tokenNumber } = req.params;
    const { prescription, completed_by } = req.body;

    if (!tokenNumber || isNaN(tokenNumber)) {
      return res.status(400).json({
        success: false,
        message: 'Valid token number is required',
      });
    }

    const exists = await queueService.patientExists(parseInt(tokenNumber));
    if (!exists) {
      return res.status(404).json({
        success: false,
        message: `Patient with token #${tokenNumber} not found`,
      });
    }

    const result = await pythonBridge.completePatient(parseInt(tokenNumber));

    logger.info(`Patient consultation completed: Token #${tokenNumber}`);

    // 💾 UPDATE APPOINTMENT STATUS IN DATABASE WITH PRESCRIPTION
    try {
      const appointment = await Appointment.findOne({ tokenNumber: parseInt(tokenNumber) });
      if (appointment) {
        // Save prescription data if provided
        if (prescription) {
          appointment.prescription = JSON.stringify(prescription);
          appointment.prescribedBy = completed_by;
          appointment.prescribedAt = new Date();
          logger.info(`✅ Prescription saved for Token #${tokenNumber}`);
        }
        
        await appointment.markCompleted();
        logger.info(`✅ Appointment ${appointment.appointmentId} marked as completed in database`);
      }
    } catch (dbError) {
      logger.error('Failed to update appointment in database (non-critical):', dbError);
    }

    // 🧠 INTELLIGENT ORCHESTRATION - Auto-trigger follow-up actions
    // Automatically: trigger orchestration cycle, notify patients, recalculate ETAs
    let orchestrationResults = null;
    try {
      orchestrationResults = await orchestrationService.executePostCompletionOrchestration(
        result,
        parseInt(tokenNumber)
      );
      
      logger.info(`✅ Post-completion orchestration: ${orchestrationResults.followUpActions.length} actions executed`);
      
      // Track orchestration in appointment
      if (orchestrationResults.followUpActions) {
        const appointment = await Appointment.findOne({ tokenNumber: parseInt(tokenNumber) });
        if (appointment) {
          for (const action of orchestrationResults.followUpActions) {
            await appointment.addOrchestrationAction(
              action.action,
              action.status,
              action.result
            );
          }
        }
      }
    } catch (error) {
      logger.error('Post-completion orchestration failed (non-critical):', error);
    }

    // Format response for clean, structured output
    const formattedResponse = formatCompletionResponse(result, orchestrationResults);
    
    res.json(formattedResponse);
  } catch (error) {
    logger.error('Error in completeConsultation controller:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to complete consultation',
      error: error.message,
    });
  }
};

/**
 * Analyze patient symptoms
 * POST /api/v1/appointments/analyze-symptoms
 */
exports.analyzeSymptoms = async (req, res) => {
  try {
    const { symptoms } = req.body;

    if (!symptoms) {
      return res.status(400).json({
        success: false,
        message: 'Symptoms are required',
      });
    }

    const result = await pythonBridge.analyzeSymptoms(symptoms);

    res.json({
      success: true,
      data: result,
    });
  } catch (error) {
    logger.error('Error in analyzeSymptoms controller:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to analyze symptoms',
      error: error.message,
    });
  }
};

/**
 * Analyze patient location and travel
 * POST /api/v1/appointments/analyze-location
 */
exports.analyzeLocation = async (req, res) => {
  try {
    const { location } = req.body;

    if (!location) {
      return res.status(400).json({
        success: false,
        message: 'Location is required',
      });
    }

    const result = await pythonBridge.analyzeLocationTravel(location);

    res.json({
      success: true,
      data: result,
    });
  } catch (error) {
    logger.error('Error in analyzeLocation controller:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to analyze location',
      error: error.message,
    });
  }
};

/**
 * Predict optimal arrival time
 * GET /api/v1/appointments/:tokenNumber/predict-arrival
 */
exports.predictArrivalTime = async (req, res) => {
  try {
    const { tokenNumber } = req.params;

    if (!tokenNumber || isNaN(tokenNumber)) {
      return res.status(400).json({
        success: false,
        message: 'Valid token number is required',
      });
    }

    const result = await pythonBridge.predictArrivalTime(parseInt(tokenNumber));

    res.json({
      success: true,
      data: result,
    });
  } catch (error) {
    logger.error('Error in predictArrivalTime controller:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to predict arrival time',
      error: error.message,
    });
  }
};

/**
 * Update patient status
 * PATCH /api/v1/appointments/:tokenNumber/status
 */
exports.updatePatientStatus = async (req, res) => {
  try {
    const { tokenNumber } = req.params;
    const { status } = req.body;

    if (!tokenNumber || isNaN(tokenNumber)) {
      return res.status(400).json({
        success: false,
        message: 'Valid token number is required',
      });
    }

    if (!status) {
      return res.status(400).json({
        success: false,
        message: 'Status is required',
      });
    }

    const result = await pythonBridge.updatePatientStatus(parseInt(tokenNumber), status);

    // Update appointment status in database
    try {
      const appointment = await Appointment.findOne({ tokenNumber: parseInt(tokenNumber) });
      if (appointment) {
        appointment.status = status;
        await appointment.save();
      }
    } catch (dbError) {
      logger.error('Failed to update appointment status in database:', dbError);
    }

    res.json({
      success: true,
      message: 'Patient status updated',
      data: result,
    });
  } catch (error) {
    logger.error('Error in updatePatientStatus controller:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to update patient status',
      error: error.message,
    });
  }
};

/**
 * Get all appointments with filters
 * GET /api/v1/appointments
 */
exports.getAllAppointments = async (req, res) => {
  try {
    const { status, date, doctorId } = req.query;
    
    const filters = {};
    if (status) filters.status = status;
    if (doctorId) filters['doctorInfo.doctorId'] = doctorId;
    
    if (date) {
      const startDate = new Date(date);
      startDate.setHours(0, 0, 0, 0);
      const endDate = new Date(date);
      endDate.setHours(23, 59, 59, 999);
      filters.bookingTime = { $gte: startDate, $lte: endDate };
    }

    const query = {
      status: { $in: ['scheduled', 'confirmed', 'waiting', 'in-progress'] },
      isActive: true,
      ...filters,
    };
    
    const appointments = await Appointment.find(query)
      .sort({ priorityScore: -1, bookingTime: 1 });

    res.json({
      success: true,
      count: appointments.length,
      data: appointments.map(apt => ({
        tokenNumber: apt.tokenNumber,
        appointmentId: apt.appointmentId,
        patientInfo: apt.patientInfo,
        symptoms: apt.symptoms,
        status: apt.status,
        queuePosition: apt.queuePosition,
        bookingTime: apt.bookingTime,
      })),
    });
  } catch (error) {
    logger.error('Error in getAllAppointments controller:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to get appointments',
      error: error.message,
    });
  }
};

/**
 * Get today's appointments
 * GET /api/v1/appointments/today
 */
exports.getTodayAppointments = async (req, res) => {
  try {
    const { doctorId } = req.query;
    
    const appointments = await Appointment.getTodayAppointments(doctorId);

    res.json({
      success: true,
      count: appointments.length,
      data: appointments.map(apt => ({
        tokenNumber: apt.tokenNumber,
        appointmentId: apt.appointmentId,
        patientInfo: apt.patientInfo,
        symptoms: apt.symptoms,
        status: apt.status,
        queuePosition: apt.queuePosition,
        bookingTime: apt.bookingTime,
      })),
    });
  } catch (error) {
    logger.error('Error in getTodayAppointments controller:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to get today\'s appointments',
      error: error.message,
    });
  }
};

/**
 * Get appointment statistics
 * GET /api/v1/appointments/statistics
 */
exports.getStatistics = async (req, res) => {
  try {
    const stats = await Appointment.aggregate([
      {
        $group: {
          _id: '$status',
          count: { $sum: 1 },
        },
      },
    ]);

    res.json({
      success: true,
      data: stats,
    });
  } catch (error) {
    logger.error('Error in getStatistics controller:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to get statistics',
      error: error.message,
    });
  }
};

/**
 * Get appointment by ID
 * GET /api/v1/appointments/id/:appointmentId
 */
exports.getAppointmentById = async (req, res) => {
  try {
    const { appointmentId } = req.params;

    const appointment = await Appointment.findOne({ appointmentId });

    if (!appointment) {
      return res.status(404).json({
        success: false,
        message: `Appointment ${appointmentId} not found`,
      });
    }

    res.json({
      success: true,
      data: {
        tokenNumber: appointment.tokenNumber,
        appointmentId: appointment.appointmentId,
        patientInfo: appointment.patientInfo,
        symptoms: appointment.symptoms,
        location: appointment.location,
        status: appointment.status,
        queuePosition: appointment.queuePosition,
        emergencyLevel: appointment.emergencyLevel,
        bookingTime: appointment.bookingTime,
      },
    });
  } catch (error) {
    logger.error('Error in getAppointmentById controller:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to get appointment',
      error: error.message,
    });
  }
};

/**
 * Get patient's upcoming appointments
 * GET /api/v1/appointments/patient/:contactNumber/upcoming
 */
exports.getPatientUpcomingAppointments = async (req, res) => {
  try {
    const { contactNumber } = req.params;

    if (!contactNumber) {
      return res.status(400).json({
        success: false,
        message: 'Contact number is required',
      });
    }

    // Normalize contact number (remove +91 prefix if present)
    const normalizedContact = contactNumber.replace(/^\+91/, '');

    // Find upcoming appointments (scheduled, confirmed, waiting, in-progress)
    const appointments = await Appointment.find({
      'patientInfo.contactNumber': { 
        $in: [normalizedContact, `+91${normalizedContact}`] 
      },
      status: { $in: ['scheduled', 'confirmed', 'waiting', 'in-progress'] },
      isActive: true,
    })
      .sort({ bookingTime: -1 })
      .limit(20);

    res.json({
      success: true,
      count: appointments.length,
      data: appointments.map(apt => ({
        id: apt._id,
        tokenNumber: apt.tokenNumber,
        appointmentId: apt.appointmentId,
        doctor_name: apt.doctorInfo?.name || 'Dr. Assigned',
        specialty: apt.doctorInfo?.specialization || 'General',
        hospital: apt.doctorInfo?.hospital || 'Clinic Location',
        date: apt.bookingTime.toLocaleDateString('en-US', { 
          month: 'short', 
          day: 'numeric',
          year: 'numeric' 
        }),
        time: apt.bookingTime.toLocaleTimeString('en-US', { 
          hour: 'numeric', 
          minute: '2-digit',
          hour12: true 
        }),
        status: apt.status,
        type: 'In-person',
        fee: `Rs. ${apt.billing?.consultationFee || 500}/-`,
        symptoms: apt.symptoms,
        location: apt.location,
        emergencyLevel: apt.emergencyLevel,
        queuePosition: apt.queuePosition,
      })),
    });
  } catch (error) {
    logger.error('Error in getPatientUpcomingAppointments controller:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to get upcoming appointments',
      error: error.message,
    });
  }
};

/**
 * Get patient's past appointments
 * GET /api/v1/appointments/patient/:contactNumber/past
 */
exports.getPatientPastAppointments = async (req, res) => {
  try {
    const { contactNumber } = req.params;

    if (!contactNumber) {
      return res.status(400).json({
        success: false,
        message: 'Contact number is required',
      });
    }

    // Normalize contact number (remove +91 prefix if present)
    const normalizedContact = contactNumber.replace(/^\+91/, '');

    // Find past appointments (completed, cancelled, no-show)
    const appointments = await Appointment.find({
      'patientInfo.contactNumber': { 
        $in: [normalizedContact, `+91${normalizedContact}`] 
      },
      status: { $in: ['completed', 'cancelled', 'no-show'] },
      isActive: true,
    })
      .sort({ bookingTime: -1 })
      .limit(50);

    res.json({
      success: true,
      count: appointments.length,
      data: appointments.map(apt => ({
        id: apt._id,
        tokenNumber: apt.tokenNumber,
        appointmentId: apt.appointmentId,
        doctor_name: apt.doctorInfo?.name || 'Dr. Assigned',
        specialty: apt.doctorInfo?.specialization || 'General',
        hospital: apt.doctorInfo?.hospital || 'Clinic Location',
        date: apt.bookingTime.toLocaleDateString('en-US', { 
          month: 'short', 
          day: 'numeric',
          year: 'numeric' 
        }),
        time: apt.bookingTime.toLocaleTimeString('en-US', { 
          hour: 'numeric', 
          minute: '2-digit',
          hour12: true 
        }),
        status: apt.status,
        type: 'In-person',
        fee: `Rs. ${apt.billing?.consultationFee || 500}/-`,
        rating: apt.status === 'completed' ? 5 : null,
        symptoms: apt.symptoms,
        consultation: apt.consultation,
      })),
    });
  } catch (error) {
    logger.error('Error in getPatientPastAppointments controller:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to get past appointments',
      error: error.message,
    });
  }
};
