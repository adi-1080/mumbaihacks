const clinicModel = require('../models/clinicModel');
const doctorModel = require('../models/doctorModel');
const pythonBridge = require('../services/pythonBridge');
const logger = require('../config/logger');

/**
 * Get clinic information
 * GET /api/v1/clinic/info
 */
exports.getClinicInfo = async (req, res) => {
  try {
    const clinicInfo = await clinicModel.getClinicInfo();
    
    res.json({
      success: true,
      data: clinicInfo,
    });
  } catch (error) {
    logger.error('Error in getClinicInfo:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to get clinic information',
      error: error.message,
    });
  }
};

/**
 * Update clinic information
 * PUT /api/v1/clinic/info
 */
exports.updateClinicInfo = async (req, res) => {
  try {
    const updated = await clinicModel.updateClinicInfo(req.body);
    
    res.json({
      success: true,
      message: 'Clinic information updated successfully',
      data: updated,
    });
  } catch (error) {
    logger.error('Error in updateClinicInfo:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to update clinic information',
      error: error.message,
    });
  }
};

/**
 * Get clinic location
 * GET /api/v1/clinic/location
 */
exports.getClinicLocation = async (req, res) => {
  try {
    const location = await clinicModel.getClinicLocation();
    
    res.json({
      success: true,
      data: location,
    });
  } catch (error) {
    logger.error('Error in getClinicLocation:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to get clinic location',
      error: error.message,
    });
  }
};

/**
 * Get clinic operating hours
 * GET /api/v1/clinic/hours
 */
exports.getOperatingHours = async (req, res) => {
  try {
    const { day } = req.query;
    const hours = await clinicModel.getOperatingHours(day ? parseInt(day) : undefined);
    
    res.json({
      success: true,
      data: hours,
    });
  } catch (error) {
    logger.error('Error in getOperatingHours:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to get operating hours',
      error: error.message,
    });
  }
};

/**
 * Get all doctors
 * GET /api/v1/clinic/doctors
 */
exports.getAllDoctors = async (req, res) => {
  try {
    const doctors = await doctorModel.getAllDoctors();
    
    res.json({
      success: true,
      data: {
        total: doctors.length,
        available: doctors.filter(d => d.available).length,
        doctors,
      },
    });
  } catch (error) {
    logger.error('Error in getAllDoctors:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to get doctors list',
      error: error.message,
    });
  }
};

/**
 * Get doctor by ID
 * GET /api/v1/clinic/doctors/:doctorId
 */
exports.getDoctorById = async (req, res) => {
  try {
    const { doctorId } = req.params;
    const doctor = await doctorModel.getDoctorById(doctorId);
    
    if (!doctor) {
      return res.status(404).json({
        success: false,
        message: `Doctor ${doctorId} not found`,
      });
    }

    // Get doctor stats
    const stats = await doctorModel.getDoctorStats(doctorId);
    
    res.json({
      success: true,
      data: {
        ...doctor,
        statistics: stats,
      },
    });
  } catch (error) {
    logger.error('Error in getDoctorById:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to get doctor information',
      error: error.message,
    });
  }
};

/**
 * Add new doctor
 * POST /api/v1/clinic/doctors
 */
exports.addDoctor = async (req, res) => {
  try {
    const doctor = await doctorModel.addDoctor(req.body);
    
    logger.info(`New doctor added: ${doctor.id}`);
    
    res.status(201).json({
      success: true,
      message: 'Doctor added successfully',
      data: doctor,
    });
  } catch (error) {
    logger.error('Error in addDoctor:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to add doctor',
      error: error.message,
    });
  }
};

/**
 * Update doctor information
 * PUT /api/v1/clinic/doctors/:doctorId
 */
exports.updateDoctor = async (req, res) => {
  try {
    const { doctorId } = req.params;
    const updated = await doctorModel.updateDoctor(doctorId, req.body);
    
    res.json({
      success: true,
      message: 'Doctor information updated',
      data: updated,
    });
  } catch (error) {
    logger.error('Error in updateDoctor:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to update doctor',
      error: error.message,
    });
  }
};

/**
 * Toggle doctor availability
 * PATCH /api/v1/clinic/doctors/:doctorId/availability
 */
exports.toggleDoctorAvailability = async (req, res) => {
  try {
    const { doctorId } = req.params;
    const updated = await doctorModel.toggleAvailability(doctorId);
    
    res.json({
      success: true,
      message: `Doctor ${doctorId} availability toggled`,
      data: updated,
    });
  } catch (error) {
    logger.error('Error in toggleDoctorAvailability:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to toggle availability',
      error: error.message,
    });
  }
};

/**
 * Get clinic dashboard with all info
 * GET /api/v1/clinic/dashboard
 */
exports.getClinicDashboard = async (req, res) => {
  try {
    const [clinicInfo, doctors, dashboardData] = await Promise.all([
      clinicModel.getClinicInfo(),
      doctorModel.getAllDoctors(),
      pythonBridge.getClinicDashboard(),
    ]);

    res.json({
      success: true,
      data: {
        clinic: clinicInfo,
        doctors: {
          total: doctors.length,
          available: doctors.filter(d => d.available).length,
          list: doctors,
        },
        queue: dashboardData,
      },
    });
  } catch (error) {
    logger.error('Error in getClinicDashboard:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to get clinic dashboard',
      error: error.message,
    });
  }
};
