const express = require('express');
const router = express.Router();
const notificationController = require('../controllers/notificationController');

/**
 * @route   POST /api/v1/notifications/queue-updates
 * @desc    Send queue update notifications to all patients
 * @access  System
 */
router.post('/queue-updates', notificationController.sendQueueNotifications);

/**
 * @route   POST /api/v1/notifications/appointment-ready/:tokenNumber
 * @desc    Send appointment ready notification to specific patient
 * @access  System
 */
router.post('/appointment-ready/:tokenNumber', notificationController.sendAppointmentReady);

/**
 * @route   POST /api/v1/notifications/eta-updates
 * @desc    Send ETA update notifications to all patients
 * @access  System
 */
router.post('/eta-updates', notificationController.sendETANotifications);

/**
 * @route   GET /api/v1/notifications/history
 * @desc    Get notification history
 * @access  Public
 */
router.get('/history', notificationController.getNotificationHistory);

module.exports = router;
