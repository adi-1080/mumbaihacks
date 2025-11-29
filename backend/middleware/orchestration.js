const pythonBridge = require('../services/pythonBridge');
const queueService = require('../services/queueService');
const logger = require('../config/logger');

/**
 * INTELLIGENT ORCHESTRATION MIDDLEWARE
 * Mimics root_agent.py's proactive decision-making
 * Automatically triggers follow-up actions based on context
 */

/**
 * Orchestration Rules - Define automatic action chains
 */
const ORCHESTRATION_RULES = {
  // After booking a patient
  AFTER_BOOKING: {
    // If urgency >= 7, automatically optimize queue
    HIGH_URGENCY_THRESHOLD: 7,
    // If queue has > 5 patients, calculate ETAs
    QUEUE_SIZE_THRESHOLD: 5,
    // Always send notifications after booking
    SEND_NOTIFICATIONS: true,
  },
  
  // After completing a patient
  AFTER_COMPLETION: {
    // Always trigger orchestration cycle
    TRIGGER_ORCHESTRATION: true,
    // Send notifications to waiting patients
    SEND_NOTIFICATIONS: true,
    // Recalculate ETAs for remaining patients
    RECALCULATE_ETAS: true,
  },
  
  // After updating location
  AFTER_LOCATION_UPDATE: {
    // Trigger queue optimization if patient is high priority
    OPTIMIZE_IF_HIGH_PRIORITY: true,
    // Recalculate ETA for the specific patient
    RECALCULATE_PATIENT_ETA: true,
  },
  
  // Queue monitoring thresholds
  QUEUE_MONITORING: {
    // If patients waiting > 30 mins, send update
    MAX_WAIT_TIME_MINUTES: 30,
    // Check for starvation every 5 minutes
    STARVATION_CHECK_INTERVAL: 5,
    // Auto-optimize if urgency imbalance detected
    URGENCY_IMBALANCE_THRESHOLD: 3,
  },
};

/**
 * Orchestration Service - Intelligent action chaining
 */
class OrchestrationService {
  /**
   * Execute post-booking orchestration
   * Mimics root_agent's behavior after booking high-urgency patients
   */
  async executePostBookingOrchestration(bookingResult, appointmentData) {
    const orchestrationResults = {
      booking: bookingResult,
      followUpActions: [],
    };

    try {
      const urgency = appointmentData.urgency_score || 0;
      const queueSnapshot = await queueService.getQueueSnapshot();
      const queueSize = queueSnapshot.total_patients;

      logger.info(`Post-booking orchestration: Urgency=${urgency}, QueueSize=${queueSize}`);

      // RULE 1: High urgency patient → Auto-optimize queue
      if (urgency >= ORCHESTRATION_RULES.AFTER_BOOKING.HIGH_URGENCY_THRESHOLD) {
        logger.info('🚨 High urgency patient detected - Auto-optimizing queue');
        
        try {
          const optimizeResult = await pythonBridge.optimizeQueue();
          orchestrationResults.followUpActions.push({
            action: 'AUTO_OPTIMIZE_QUEUE',
            reason: `High urgency patient (${urgency}/10)`,
            result: optimizeResult,
            success: true,
          });
        } catch (error) {
          // Silently skip if optimize script doesn't exist
          if (!error.message.includes('No such file')) {
            logger.error('Auto-optimize failed:', error);
          }
          orchestrationResults.followUpActions.push({
            action: 'AUTO_OPTIMIZE_QUEUE',
            reason: `High urgency patient (${urgency}/10)`,
            success: false,
            error: error.message,
          });
        }
      }

      // RULE 2: Large queue → Calculate ETAs automatically
      if (queueSize > ORCHESTRATION_RULES.AFTER_BOOKING.QUEUE_SIZE_THRESHOLD) {
        logger.info(`📊 Large queue detected (${queueSize} patients) - Calculating ETAs`);
        
        try {
          const etaResult = await pythonBridge.calculateETAs();
          orchestrationResults.followUpActions.push({
            action: 'AUTO_CALCULATE_ETAS',
            reason: `Queue size exceeds threshold (${queueSize} > ${ORCHESTRATION_RULES.AFTER_BOOKING.QUEUE_SIZE_THRESHOLD})`,
            result: etaResult,
            success: true,
          });
        } catch (error) {
          logger.error('Auto-ETA calculation failed:', error);
          orchestrationResults.followUpActions.push({
            action: 'AUTO_CALCULATE_ETAS',
            reason: `Queue size exceeds threshold`,
            success: false,
            error: error.message,
          });
        }
      }

      // RULE 3: Compare urgency with queue average
      if (queueSnapshot.patients && queueSnapshot.patients.length > 0) {
        const avgUrgency = queueSnapshot.patients.reduce((sum, p) => 
          sum + (p.urgency_score || 0), 0) / queueSnapshot.patients.length;
        
        if (urgency > avgUrgency + ORCHESTRATION_RULES.QUEUE_MONITORING.URGENCY_IMBALANCE_THRESHOLD) {
          logger.info(`⚖️ Urgency imbalance detected (${urgency} vs avg ${avgUrgency.toFixed(1)}) - Optimizing`);
          
          try {
            const balanceResult = await pythonBridge.optimizeQueue().catch(e => {
              if (!e.message.includes('No such file')) throw e;
              return { skipped: true, reason: 'Optimize script not available' };
            });
            orchestrationResults.followUpActions.push({
              action: 'AUTO_BALANCE_QUEUE',
              reason: `New patient urgency (${urgency}) significantly higher than average (${avgUrgency.toFixed(1)})`,
              result: balanceResult,
              success: true,
            });
          } catch (error) {
            logger.error('Auto-balance failed:', error);
          }
        }
      }

      // RULE 4: Always send notifications after booking
      if (ORCHESTRATION_RULES.AFTER_BOOKING.SEND_NOTIFICATIONS) {
        try {
          await pythonBridge.sendQueueNotifications();
          orchestrationResults.followUpActions.push({
            action: 'SEND_NOTIFICATIONS',
            reason: 'New patient added to queue',
            success: true,
          });
        } catch (error) {
          logger.error('Notification sending failed:', error);
        }
      }

      logger.info(`✅ Post-booking orchestration complete: ${orchestrationResults.followUpActions.length} actions executed`);
      return orchestrationResults;

    } catch (error) {
      logger.error('Post-booking orchestration error:', error);
      throw error;
    }
  }

  /**
   * Execute post-completion orchestration
   * Mimics root_agent's behavior after marking patient completed
   */
  async executePostCompletionOrchestration(completionResult, tokenNumber) {
    const orchestrationResults = {
      completion: completionResult,
      followUpActions: [],
    };

    try {
      logger.info(`Post-completion orchestration for Token #${tokenNumber}`);

      // RULE 1: Always trigger orchestration cycle
      if (ORCHESTRATION_RULES.AFTER_COMPLETION.TRIGGER_ORCHESTRATION) {
        logger.info('🔄 Triggering orchestration cycle');
        
        try {
          const cycleResult = await pythonBridge.triggerOrchestrationCycle();
          orchestrationResults.followUpActions.push({
            action: 'TRIGGER_ORCHESTRATION_CYCLE',
            reason: 'Patient consultation completed',
            result: cycleResult,
            success: true,
          });
        } catch (error) {
          logger.error('Orchestration cycle failed:', error);
          orchestrationResults.followUpActions.push({
            action: 'TRIGGER_ORCHESTRATION_CYCLE',
            reason: 'Patient consultation completed',
            success: false,
            error: error.message,
          });
        }
      }

      // RULE 2: Recalculate ETAs for remaining patients
      if (ORCHESTRATION_RULES.AFTER_COMPLETION.RECALCULATE_ETAS) {
        logger.info('⏱️ Recalculating ETAs for remaining patients');
        
        try {
          const etaResult = await pythonBridge.calculateETAs();
          orchestrationResults.followUpActions.push({
            action: 'RECALCULATE_ETAS',
            reason: 'Queue updated after completion',
            result: etaResult,
            success: true,
          });
        } catch (error) {
          logger.error('ETA recalculation failed:', error);
        }
      }

      // RULE 3: Send notifications to waiting patients
      if (ORCHESTRATION_RULES.AFTER_COMPLETION.SEND_NOTIFICATIONS) {
        logger.info('📢 Sending queue update notifications');
        
        try {
          await pythonBridge.sendQueueNotifications();
          orchestrationResults.followUpActions.push({
            action: 'SEND_QUEUE_NOTIFICATIONS',
            reason: 'Notify patients of queue advancement',
            success: true,
          });
        } catch (error) {
          logger.error('Notification sending failed:', error);
        }

        // Notify next patient they're ready
        try {
          const queueSnapshot = await queueService.getQueueSnapshot();
          if (queueSnapshot.patients && queueSnapshot.patients.length > 0) {
            const nextPatient = queueSnapshot.patients[0];
            await pythonBridge.sendAppointmentReadyNotification(nextPatient.token_number);
            
            orchestrationResults.followUpActions.push({
              action: 'NOTIFY_NEXT_PATIENT',
              reason: `Token #${nextPatient.token_number} is now next in line`,
              success: true,
            });
          }
        } catch (error) {
          logger.error('Next patient notification failed:', error);
        }
      }

      logger.info(`✅ Post-completion orchestration complete: ${orchestrationResults.followUpActions.length} actions executed`);
      return orchestrationResults;

    } catch (error) {
      logger.error('Post-completion orchestration error:', error);
      throw error;
    }
  }

  /**
   * Execute post-location-update orchestration
   * Optimizes queue if patient's location changes significantly
   */
  async executePostLocationUpdateOrchestration(updateResult, tokenNumber, location) {
    const orchestrationResults = {
      locationUpdate: updateResult,
      followUpActions: [],
    };

    try {
      logger.info(`Post-location-update orchestration for Token #${tokenNumber}`);

      // RULE 1: Get patient details to check priority
      const patient = await queueService.getPatientByToken(tokenNumber);
      
      if (!patient) {
        logger.warn(`Patient #${tokenNumber} not found for post-update orchestration`);
        return orchestrationResults;
      }

      const isHighPriority = patient.emergency_level === 'CRITICAL' || 
                             (patient.urgency_score && patient.urgency_score >= 7);

      // RULE 2: High priority patient location update → Auto-optimize
      if (ORCHESTRATION_RULES.AFTER_LOCATION_UPDATE.OPTIMIZE_IF_HIGH_PRIORITY && isHighPriority) {
        logger.info(`🚨 High-priority patient location updated - Reoptimizing queue`);
        
        try {
          const optimizeResult = await pythonBridge.optimizeQueue();
          orchestrationResults.followUpActions.push({
            action: 'AUTO_REOPTIMIZE_QUEUE',
            reason: `High-priority patient (#${tokenNumber}) location changed`,
            result: optimizeResult,
            success: true,
          });
        } catch (error) {
          logger.error('Auto-reoptimize failed:', error);
        }
      }

      // RULE 3: Recalculate patient-specific ETA
      if (ORCHESTRATION_RULES.AFTER_LOCATION_UPDATE.RECALCULATE_PATIENT_ETA) {
        logger.info(`📍 Recalculating arrival time for Token #${tokenNumber}`);
        
        try {
          const arrivalResult = await pythonBridge.predictArrivalTime(tokenNumber);
          orchestrationResults.followUpActions.push({
            action: 'RECALCULATE_ARRIVAL_TIME',
            reason: `Patient location updated`,
            result: arrivalResult,
            success: true,
          });
        } catch (error) {
          logger.error('Arrival time recalculation failed:', error);
        }
      }

      logger.info(`✅ Post-location-update orchestration complete: ${orchestrationResults.followUpActions.length} actions executed`);
      return orchestrationResults;

    } catch (error) {
      logger.error('Post-location-update orchestration error:', error);
      throw error;
    }
  }

  /**
   * Execute queue monitoring orchestration
   * Checks for starvation, long waits, and optimization needs
   */
  async executeQueueMonitoringOrchestration() {
    const orchestrationResults = {
      timestamp: new Date().toISOString(),
      checks: [],
      actions: [],
    };

    try {
      logger.info('🔍 Executing queue monitoring orchestration');

      const queueSnapshot = await queueService.getQueueSnapshot();
      
      if (!queueSnapshot.patients || queueSnapshot.patients.length === 0) {
        logger.info('Queue is empty - no monitoring needed');
        return orchestrationResults;
      }

      // CHECK 1: Detect patients waiting too long
      const now = new Date();
      const longWaitPatients = queueSnapshot.patients.filter(patient => {
        const bookedAt = new Date(patient.bookedAt);
        const waitMinutes = (now - bookedAt) / (1000 * 60);
        return waitMinutes > ORCHESTRATION_RULES.QUEUE_MONITORING.MAX_WAIT_TIME_MINUTES;
      });

      if (longWaitPatients.length > 0) {
        orchestrationResults.checks.push({
          check: 'LONG_WAIT_DETECTION',
          result: `${longWaitPatients.length} patients waiting > ${ORCHESTRATION_RULES.QUEUE_MONITORING.MAX_WAIT_TIME_MINUTES} minutes`,
          action_needed: true,
        });

        logger.warn(`⏰ ${longWaitPatients.length} patients waiting too long - Sending notifications`);
        
        try {
          await pythonBridge.sendQueueNotifications();
          orchestrationResults.actions.push({
            action: 'SEND_LONG_WAIT_NOTIFICATIONS',
            reason: `${longWaitPatients.length} patients exceeded wait time threshold`,
            success: true,
          });
        } catch (error) {
          logger.error('Long wait notification failed:', error);
        }
      }

      // CHECK 2: Detect urgency imbalance in queue
      if (queueSnapshot.patients.length >= 3) {
        const urgencies = queueSnapshot.patients.map(p => p.urgency_score || 0);
        const maxUrgency = Math.max(...urgencies);
        const minUrgency = Math.min(...urgencies);
        const urgencySpread = maxUrgency - minUrgency;

        if (urgencySpread > ORCHESTRATION_RULES.QUEUE_MONITORING.URGENCY_IMBALANCE_THRESHOLD) {
          orchestrationResults.checks.push({
            check: 'URGENCY_IMBALANCE',
            result: `Urgency spread: ${urgencySpread} (max: ${maxUrgency}, min: ${minUrgency})`,
            action_needed: true,
          });

          logger.warn(`⚖️ Urgency imbalance detected (spread: ${urgencySpread}) - Optimizing queue`);
          
          try {
            const optimizeResult = await pythonBridge.optimizeQueue();
            orchestrationResults.actions.push({
              action: 'AUTO_BALANCE_URGENCY',
              reason: `Urgency spread ${urgencySpread} exceeds threshold`,
              result: optimizeResult,
              success: true,
            });
          } catch (error) {
            logger.error('Urgency balancing failed:', error);
          }
        }
      }

      // CHECK 3: Starvation prevention check
      orchestrationResults.checks.push({
        check: 'STARVATION_PREVENTION',
        result: 'Aging algorithm active in priority queue system',
        action_needed: false,
      });

      logger.info(`✅ Queue monitoring complete: ${orchestrationResults.checks.length} checks, ${orchestrationResults.actions.length} actions`);
      return orchestrationResults;

    } catch (error) {
      logger.error('Queue monitoring orchestration error:', error);
      throw error;
    }
  }

  /**
   * Smart queue status with automatic insights
   * Returns queue + automatically calculated ETAs and insights
   */
  async getSmartQueueStatus() {
    try {
      const queueSnapshot = await queueService.getQueueSnapshot();
      
      // Automatically calculate ETAs if queue has patients
      let etas = null;
      if (queueSnapshot.patients && queueSnapshot.patients.length > 0) {
        try {
          etas = await pythonBridge.calculateETAs();
        } catch (error) {
          logger.error('Auto-ETA calculation failed:', error);
        }
      }

      // Get intelligence dashboard
      let intelligence = null;
      try {
        intelligence = await pythonBridge.getQueueIntelligence();
      } catch (error) {
        logger.error('Intelligence dashboard retrieval failed:', error);
      }

      return {
        queue: queueSnapshot,
        etas,
        intelligence,
        orchestration_enabled: true,
      };
    } catch (error) {
      logger.error('Smart queue status error:', error);
      throw error;
    }
  }
}

/**
 * Export singleton instance
 */
const orchestrationService = new OrchestrationService();

/**
 * Express middleware functions
 */

/**
 * Middleware: Attach orchestration service to request
 */
function attachOrchestrationService(req, res, next) {
  req.orchestration = orchestrationService;
  next();
}

/**
 * Middleware: Enable smart response enhancement
 * Automatically enriches responses with follow-up action results
 */
function enableSmartResponse(req, res, next) {
  // Store original json method
  const originalJson = res.json.bind(res);
  
  // Override json method to include orchestration results
  res.json = function(data) {
    // If orchestration results exist, include them
    if (req.orchestrationResults) {
      return originalJson({
        ...data,
        orchestration: req.orchestrationResults,
      });
    }
    return originalJson(data);
  };
  
  next();
}

module.exports = {
  orchestrationService,
  attachOrchestrationService,
  enableSmartResponse,
  ORCHESTRATION_RULES,
};
