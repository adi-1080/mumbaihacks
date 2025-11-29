const queueService = require('../services/queueService');
const pythonBridge = require('../services/pythonBridge');
const logger = require('../config/logger');
const { orchestrationService } = require('../middleware/orchestration');
const { formatETAResponse } = require('../utils/responseFormatter');

/**
 * Get current queue status
 * GET /api/v1/queue
 * WITH SMART ENHANCEMENT (automatically includes ETAs and insights)
 */
exports.getQueueStatus = async (req, res) => {
  try {
    // Check if smart mode is requested (default: true)
    const smartMode = req.query.smart !== 'false';
    
    if (smartMode) {
      // 🧠 SMART MODE - Auto-include ETAs and intelligence
      const smartStatus = await orchestrationService.getSmartQueueStatus();
      
      res.json({
        success: true,
        data: smartStatus.queue,
        etas: smartStatus.etas,
        intelligence: smartStatus.intelligence,
        smart_mode: true,
      });
    } else {
      // Basic mode - just queue snapshot
      const snapshot = await queueService.getQueueSnapshot();
      
      res.json({
        success: true,
        data: snapshot,
        smart_mode: false,
      });
    }
  } catch (error) {
    logger.error('Error in getQueueStatus controller:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to get queue status',
      error: error.message,
    });
  }
};

/**
 * Get current token number
 * GET /api/v1/queue/current-token
 */
exports.getCurrentToken = async (req, res) => {
  try {
    const currentToken = await queueService.getCurrentTokenNumber();

    res.json({
      success: true,
      data: {
        current_token: currentToken,
        next_token: currentToken + 1,
      },
    });
  } catch (error) {
    logger.error('Error in getCurrentToken controller:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to get current token',
      error: error.message,
    });
  }
};

/**
 * Get queue position for specific token
 * GET /api/v1/queue/position/:tokenNumber
 */
exports.getQueuePosition = async (req, res) => {
  try {
    const { tokenNumber } = req.params;

    if (!tokenNumber || isNaN(tokenNumber)) {
      return res.status(400).json({
        success: false,
        message: 'Valid token number is required',
      });
    }

    const position = await queueService.getQueuePosition(parseInt(tokenNumber));

    if (!position) {
      return res.status(404).json({
        success: false,
        message: `Token #${tokenNumber} not found in queue`,
      });
    }

    res.json({
      success: true,
      data: {
        token_number: parseInt(tokenNumber),
        ...position,
      },
    });
  } catch (error) {
    logger.error('Error in getQueuePosition controller:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to get queue position',
      error: error.message,
    });
  }
};

/**
 * Get calculated ETAs for all patients
 * GET /api/v1/queue/etas
 */
exports.getETAs = async (req, res) => {
  try {
    const result = await pythonBridge.calculateETAs();

    // Format response for clean, structured output
    const formattedResponse = formatETAResponse(result);
    
    res.json(formattedResponse);
  } catch (error) {
    logger.error('Error in getETAs controller:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to calculate ETAs',
      error: error.message,
    });
  }
};

/**
 * Get ongoing consultations
 * GET /api/v1/queue/ongoing
 */
exports.getOngoingConsultations = async (req, res) => {
  try {
    const ongoingPatients = await queueService.getOngoingConsultations();

    res.json({
      success: true,
      data: {
        count: ongoingPatients.length,
        consultations: ongoingPatients,
      },
    });
  } catch (error) {
    logger.error('Error in getOngoingConsultations controller:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to get ongoing consultations',
      error: error.message,
    });
  }
};

/**
 * Get completed consultations today
 * GET /api/v1/queue/completed
 */
exports.getCompletedConsultations = async (req, res) => {
  try {
    const completedPatients = await queueService.getCompletedConsultationsToday();

    res.json({
      success: true,
      data: {
        consultations: completedPatients,
        count: completedPatients.length,
      },
    });
  } catch (error) {
    logger.error('Error in getCompletedConsultations controller:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to get completed consultations',
      error: error.message,
    });
  }
};

/**
 * Get clinic statistics
 * GET /api/v1/queue/stats
 */
exports.getClinicStats = async (req, res) => {
  try {
    const stats = await queueService.getClinicStats();

    res.json({
      success: true,
      data: stats,
    });
  } catch (error) {
    logger.error('Error in getClinicStats controller:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to get clinic statistics',
      error: error.message,
    });
  }
};

/**
 * Get intelligent doctor status
 * GET /api/v1/queue/doctor-status
 */
exports.getDoctorStatus = async (req, res) => {
  try {
    const result = await pythonBridge.getDoctorStatus();

    res.json({
      success: true,
      data: result,
    });
  } catch (error) {
    logger.error('Error in getDoctorStatus controller:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to get doctor status',
      error: error.message,
    });
  }
};

/**
 * Optimize queue
 * POST /api/v1/queue/optimize
 */
exports.optimizeQueue = async (req, res) => {
  try {
    const result = await pythonBridge.optimizeQueue();

    logger.info('Queue optimization triggered');

    res.json({
      success: true,
      message: 'Queue optimized successfully',
      data: result,
    });
  } catch (error) {
    logger.error('Error in optimizeQueue controller:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to optimize queue',
      error: error.message,
    });
  }
};

/**
 * Get queue intelligence dashboard
 * GET /api/v1/queue/intelligence
 */
exports.getQueueIntelligence = async (req, res) => {
  try {
    const result = await pythonBridge.getQueueIntelligence();

    res.json({
      success: true,
      data: result,
    });
  } catch (error) {
    logger.error('Error in getQueueIntelligence controller:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to get queue intelligence',
      error: error.message,
    });
  }
};

/**
 * Get patient insights
 * GET /api/v1/queue/insights/:tokenNumber
 */
exports.getPatientInsights = async (req, res) => {
  try {
    const { tokenNumber } = req.params;

    if (!tokenNumber || isNaN(tokenNumber)) {
      return res.status(400).json({
        success: false,
        message: 'Valid token number is required',
      });
    }

    const result = await pythonBridge.getPatientInsights(parseInt(tokenNumber));

    res.json({
      success: true,
      data: result,
    });
  } catch (error) {
    logger.error('Error in getPatientInsights controller:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to get patient insights',
      error: error.message,
    });
  }
};

/**
 * Execute orchestration
 * POST /api/v1/queue/orchestration/execute
 */
exports.executeOrchestration = async (req, res) => {
  try {
    const result = await pythonBridge.executeOrchestration();

    logger.info('Orchestration executed');

    res.json({
      success: true,
      message: 'Orchestration executed successfully',
      data: result,
    });
  } catch (error) {
    logger.error('Error in executeOrchestration controller:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to execute orchestration',
      error: error.message,
    });
  }
};

/**
 * Monitor orchestration
 * GET /api/v1/queue/orchestration/monitor
 */
exports.monitorOrchestration = async (req, res) => {
  try {
    const result = await pythonBridge.monitorOrchestration();

    res.json({
      success: true,
      data: result,
    });
  } catch (error) {
    logger.error('Error in monitorOrchestration controller:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to monitor orchestration',
      error: error.message,
    });
  }
};

/**
 * Get orchestration dashboard
 * GET /api/v1/queue/orchestration/dashboard
 */
exports.getOrchestrationDashboard = async (req, res) => {
  try {
    const result = await pythonBridge.getOrchestrationDashboard();

    res.json({
      success: true,
      data: result,
    });
  } catch (error) {
    logger.error('Error in getOrchestrationDashboard controller:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to get orchestration dashboard',
      error: error.message,
    });
  }
};

/**
 * Trigger orchestration cycle
 * POST /api/v1/queue/orchestration/trigger
 */
exports.triggerOrchestrationCycle = async (req, res) => {
  try {
    const result = await pythonBridge.triggerOrchestrationCycle();

    logger.info('Orchestration cycle triggered');

    res.json({
      success: true,
      message: 'Orchestration cycle triggered',
      data: result,
    });
  } catch (error) {
    logger.error('Error in triggerOrchestrationCycle controller:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to trigger orchestration cycle',
      error: error.message,
    });
  }
};

/**
 * Execute queue monitoring orchestration
 * GET /api/v1/queue/monitor
 * Checks for long waits, urgency imbalance, starvation
 */
exports.monitorQueue = async (req, res) => {
  try {
    const monitoringResults = await orchestrationService.executeQueueMonitoringOrchestration();

    logger.info(`Queue monitoring complete: ${monitoringResults.checks.length} checks, ${monitoringResults.actions.length} actions`);

    res.json({
      success: true,
      message: 'Queue monitoring completed',
      data: monitoringResults,
    });
  } catch (error) {
    logger.error('Error in monitorQueue controller:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to monitor queue',
      error: error.message,
    });
  }
};
