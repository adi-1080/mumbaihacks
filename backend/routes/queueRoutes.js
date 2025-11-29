const express = require('express');
const router = express.Router();
const queueController = require('../controllers/queueController');

/**
 * @route   GET /api/v1/queue
 * @desc    Get current queue status with all patients
 * @access  Public
 */
router.get('/', queueController.getQueueStatus);

/**
 * @route   GET /api/v1/queue/current-token
 * @desc    Get current token number and next token
 * @access  Public
 */
router.get('/current-token', queueController.getCurrentToken);

/**
 * @route   GET /api/v1/queue/position/:tokenNumber
 * @desc    Get queue position for specific token
 * @access  Public
 */
router.get('/position/:tokenNumber', queueController.getQueuePosition);

/**
 * @route   GET /api/v1/queue/etas
 * @desc    Get calculated ETAs for all patients
 * @access  Public
 */
router.get('/etas', queueController.getETAs);

/**
 * @route   GET /api/v1/queue/ongoing
 * @desc    Get ongoing consultations
 * @access  Doctor only
 */
router.get('/ongoing', queueController.getOngoingConsultations);

/**
 * @route   GET /api/v1/queue/completed
 * @desc    Get completed consultations today
 * @access  Doctor only
 */
router.get('/completed', queueController.getCompletedConsultations);

/**
 * @route   GET /api/v1/queue/stats
 * @desc    Get clinic statistics
 * @access  Public
 */
router.get('/stats', queueController.getClinicStats);

/**
 * @route   GET /api/v1/queue/doctor-status
 * @desc    Get intelligent doctor status
 * @access  Public
 */
router.get('/doctor-status', queueController.getDoctorStatus);

/**
 * @route   POST /api/v1/queue/optimize
 * @desc    Trigger queue optimization
 * @access  Doctor only
 */
router.post('/optimize', queueController.optimizeQueue);

/**
 * @route   GET /api/v1/queue/intelligence
 * @desc    Get queue intelligence dashboard
 * @access  Public
 */
router.get('/intelligence', queueController.getQueueIntelligence);

/**
 * @route   GET /api/v1/queue/insights/:tokenNumber
 * @desc    Get patient-specific insights
 * @access  Public
 */
router.get('/insights/:tokenNumber', queueController.getPatientInsights);

/**
 * @route   POST /api/v1/queue/orchestration/execute
 * @desc    Execute orchestration cycle
 * @access  System
 */
router.post('/orchestration/execute', queueController.executeOrchestration);

/**
 * @route   GET /api/v1/queue/orchestration/monitor
 * @desc    Monitor orchestration triggers
 * @access  System
 */
router.get('/orchestration/monitor', queueController.monitorOrchestration);

/**
 * @route   GET /api/v1/queue/orchestration/dashboard
 * @desc    Get orchestration dashboard
 * @access  Public
 */
router.get('/orchestration/dashboard', queueController.getOrchestrationDashboard);

/**
 * @route   POST /api/v1/queue/orchestration/trigger
 * @desc    Manually trigger orchestration cycle
 * @access  Doctor only
 */
router.post('/orchestration/trigger', queueController.triggerOrchestrationCycle);

/**
 * @route   GET /api/v1/queue/monitor
 * @desc    Execute queue monitoring orchestration (checks long waits, urgency imbalance, starvation)
 * @access  Public
 */
router.get('/monitor', queueController.monitorQueue);

module.exports = router;
