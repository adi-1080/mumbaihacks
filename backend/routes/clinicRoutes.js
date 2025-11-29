const express = require('express');
const router = express.Router();
const clinicController = require('../controllers/clinicController');

/**
 * @route   GET /api/v1/clinic/info
 * @desc    Get clinic information
 * @access  Public
 */
router.get('/info', clinicController.getClinicInfo);

/**
 * @route   PUT /api/v1/clinic/info
 * @desc    Update clinic information
 * @access  Admin only
 */
router.put('/info', clinicController.updateClinicInfo);

/**
 * @route   GET /api/v1/clinic/location
 * @desc    Get clinic location coordinates
 * @access  Public
 */
router.get('/location', clinicController.getClinicLocation);

/**
 * @route   GET /api/v1/clinic/hours
 * @desc    Get operating hours for specific day
 * @access  Public
 */
router.get('/hours', clinicController.getOperatingHours);

/**
 * @route   GET /api/v1/clinic/doctors
 * @desc    Get all doctors
 * @access  Public
 */
router.get('/doctors', clinicController.getAllDoctors);

/**
 * @route   GET /api/v1/clinic/doctors/:doctorId
 * @desc    Get doctor by ID
 * @access  Public
 */
router.get('/doctors/:doctorId', clinicController.getDoctorById);

/**
 * @route   POST /api/v1/clinic/doctors
 * @desc    Add new doctor
 * @access  Admin only
 */
router.post('/doctors', clinicController.addDoctor);

/**
 * @route   PUT /api/v1/clinic/doctors/:doctorId
 * @desc    Update doctor information
 * @access  Admin only
 */
router.put('/doctors/:doctorId', clinicController.updateDoctor);

/**
 * @route   PATCH /api/v1/clinic/doctors/:doctorId/availability
 * @desc    Toggle doctor availability
 * @access  Doctor only
 */
router.patch('/doctors/:doctorId/availability', clinicController.toggleDoctorAvailability);

/**
 * @route   GET /api/v1/clinic/dashboard
 * @desc    Get comprehensive clinic dashboard
 * @access  Public
 */
router.get('/dashboard', clinicController.getClinicDashboard);

module.exports = router;
