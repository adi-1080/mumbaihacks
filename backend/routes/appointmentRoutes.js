const express = require('express');
const router = express.Router();
const appointmentController = require('../controllers/appointmentController');
const { validateAppointment } = require('../middleware/validation');

/**
 * @route   POST /api/v1/appointments/book
 * @desc    Book a new appointment
 * @access  Public
 */
router.post('/book', validateAppointment, appointmentController.bookAppointment);

/**
 * @route   GET /api/v1/appointments/patient/:contactNumber/upcoming
 * @desc    Get upcoming appointments for a patient by contact number
 * @access  Public
 */
router.get('/patient/:contactNumber/upcoming', appointmentController.getPatientUpcomingAppointments);

/**
 * @route   GET /api/v1/appointments/patient/:contactNumber/past
 * @desc    Get past appointments for a patient by contact number
 * @access  Public
 */
router.get('/patient/:contactNumber/past', appointmentController.getPatientPastAppointments);

/**
 * @route   GET /api/v1/appointments
 * @desc    Get all appointments with optional filters
 * @access  Public
 */
router.get('/', appointmentController.getAllAppointments);

/**
 * @route   GET /api/v1/appointments/today
 * @desc    Get today's appointments
 * @access  Public
 */
router.get('/today', appointmentController.getTodayAppointments);

/**
 * @route   GET /api/v1/appointments/statistics
 * @desc    Get appointment statistics
 * @access  Public
 */
router.get('/statistics', appointmentController.getStatistics);

/**
 * @route   GET /api/v1/appointments/id/:appointmentId
 * @desc    Get appointment by appointment ID
 * @access  Public
 */
router.get('/id/:appointmentId', appointmentController.getAppointmentById);

/**
 * @route   GET /api/v1/appointments/:tokenNumber
 * @desc    Get appointment details by token number
 * @access  Public
 */
router.get('/:tokenNumber', appointmentController.getAppointment);

/**
 * @route   DELETE /api/v1/appointments/:tokenNumber
 * @desc    Cancel an appointment
 * @access  Public
 */
router.delete('/:tokenNumber', appointmentController.cancelAppointment);

/**
 * @route   PATCH /api/v1/appointments/:tokenNumber/location
 * @desc    Update patient location
 * @access  Public
 */
router.patch('/:tokenNumber/location', appointmentController.updateLocation);

/**
 * @route   POST /api/v1/appointments/:tokenNumber/complete
 * @desc    Mark patient consultation as completed
 * @access  Doctor only
 */
router.post('/:tokenNumber/complete', appointmentController.completeConsultation);

/**
 * @route   POST /api/v1/appointments/analyze-symptoms
 * @desc    Analyze patient symptoms
 * @access  Public
 */
router.post('/analyze-symptoms', appointmentController.analyzeSymptoms);

/**
 * @route   POST /api/v1/appointments/analyze-location
 * @desc    Analyze patient location and travel time
 * @access  Public
 */
router.post('/analyze-location', appointmentController.analyzeLocation);

/**
 * @route   GET /api/v1/appointments/:tokenNumber/predict-arrival
 * @desc    Predict optimal arrival time for patient
 * @access  Public
 */
router.get('/:tokenNumber/predict-arrival', appointmentController.predictArrivalTime);

/**
 * @route   PATCH /api/v1/appointments/:tokenNumber/status
 * @desc    Update patient status
 * @access  Doctor only
 */
router.patch('/:tokenNumber/status', appointmentController.updatePatientStatus);

module.exports = router;
