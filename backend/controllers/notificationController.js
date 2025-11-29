const pythonBridge = require('../services/pythonBridge');
const logger = require('../config/logger');

/**
 * Send queue update notifications
 * POST /api/v1/notifications/queue-updates
 */
exports.sendQueueNotifications = async (req, res) => {
  try {
    const result = await pythonBridge.sendQueueNotifications();

    logger.info('Queue notifications sent');

    res.json({
      success: true,
      message: 'Queue notifications sent successfully',
      data: result,
    });
  } catch (error) {
    logger.error('Error in sendQueueNotifications controller:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to send queue notifications',
      error: error.message,
    });
  }
};

/**
 * Send appointment ready notification
 * POST /api/v1/notifications/appointment-ready/:tokenNumber
 */
exports.sendAppointmentReady = async (req, res) => {
  try {
    const { tokenNumber } = req.params;

    if (!tokenNumber || isNaN(tokenNumber)) {
      return res.status(400).json({
        success: false,
        message: 'Valid token number is required',
      });
    }

    const result = await pythonBridge.sendAppointmentReadyNotification(parseInt(tokenNumber));

    logger.info(`Appointment ready notification sent for token ${tokenNumber}`);

    res.json({
      success: true,
      message: 'Appointment ready notification sent',
      data: result,
    });
  } catch (error) {
    logger.error('Error in sendAppointmentReady controller:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to send appointment ready notification',
      error: error.message,
    });
  }
};

/**
 * Send ETA update notifications
 * POST /api/v1/notifications/eta-updates
 */
exports.sendETANotifications = async (req, res) => {
  try {
    const result = await pythonBridge.sendETANotifications();

    logger.info('ETA notifications sent');

    res.json({
      success: true,
      message: 'ETA notifications sent successfully',
      data: result,
    });
  } catch (error) {
    logger.error('Error in sendETANotifications controller:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to send ETA notifications',
      error: error.message,
    });
  }
};

/**
 * Get notification history
 * GET /api/v1/notifications/history
 */
exports.getNotificationHistory = async (req, res) => {
  try {
    const { tokenNumber, limit = 50, offset = 0 } = req.query;

    const result = await pythonBridge.getNotificationHistory(
      tokenNumber ? parseInt(tokenNumber) : null,
      parseInt(limit),
      parseInt(offset)
    );

    res.json({
      success: true,
      data: result,
    });
  } catch (error) {
    logger.error('Error in getNotificationHistory controller:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to get notification history',
      error: error.message,
    });
  }
};
