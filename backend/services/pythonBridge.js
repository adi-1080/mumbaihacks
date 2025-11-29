const { spawn } = require('child_process');
const path = require('path');
const logger = require('../config/logger');

/**
 * Python Bridge Service - Execute Python tools from Node.js
 * This service calls the Python priority queue system tools
 */

class PythonBridge {
  constructor() {
    this.pythonPath = process.env.PYTHON_PATH || 'python';
    this.toolsPath = path.resolve(__dirname, '../../tools');
  }

  /**
   * Execute Python script and return result
   */
  async executePythonScript(scriptName, args = [], timeout = 30000) {
    return new Promise((resolve, reject) => {
      const scriptPath = path.join(this.toolsPath, scriptName);
      
      logger.debug(`Executing Python script: ${scriptPath} with args:`, args);
      console.log(`🐍 Starting Python: ${scriptName}`);

      // Add AI directory to PYTHONPATH for proper imports
      const aiRootPath = path.resolve(__dirname, '../..');
      const pythonPath = process.env.PYTHONPATH
        ? `${aiRootPath}${path.delimiter}${process.env.PYTHONPATH}`
        : aiRootPath;

      // Set Python to use UTF-8 encoding for output and add PYTHONPATH
      const pythonProcess = spawn(this.pythonPath, [scriptPath, ...args], {
        env: { 
          ...process.env, 
          PYTHONIOENCODING: 'utf-8',
          PYTHONPATH: pythonPath
        }
      });

      let stdout = '';
      let stderr = '';
      let timeoutId = null;

      // Set timeout
      timeoutId = setTimeout(() => {
        pythonProcess.kill();
        logger.error(`Python script ${scriptName} timed out after ${timeout}ms`);
        reject(new Error(`Python script execution timed out after ${timeout}ms`));
      }, timeout);

      pythonProcess.stdout.on('data', (data) => {
        const output = data.toString();
        stdout += output;
        console.log(`🐍 Python stdout: ${output.substring(0, 200)}`);
      });

      pythonProcess.stderr.on('data', (data) => {
        const error = data.toString();
        stderr += error;
        console.error(`🐍 Python stderr: ${error}`);
      });

      pythonProcess.on('close', (code) => {
        clearTimeout(timeoutId);
        console.log(`🐍 Python exited with code ${code}`);
        
        if (code !== 0) {
          logger.error(`Python script failed with code ${code}:`, stderr);
          reject(new Error(`Python script execution failed: ${stderr}`));
        } else {
          try {
            console.log(`🐍 Python stdout length: ${stdout.length} chars`);
            
            // Extract JSON from output (Python scripts output logs + JSON)
            // Look for the last valid JSON object in the output
            let jsonResult = null;
            const lines = stdout.split('\n');
            
            // Try to find JSON - look for lines starting with { or [
            for (let i = lines.length - 1; i >= 0; i--) {
              const line = lines[i].trim();
              if (line.startsWith('{') || line.startsWith('[')) {
                try {
                  jsonResult = JSON.parse(line);
                  console.log(`✅ Found JSON at line ${i}: ${line.substring(0, 100)}`);
                  break;
                } catch (e) {
                  // Not valid JSON, continue searching
                  continue;
                }
              }
            }
            
            if (jsonResult) {
              console.log(`✅ Python result parsed successfully`);
              resolve(jsonResult);
            } else {
              // Try parsing entire stdout as JSON (fallback)
              try {
                const result = JSON.parse(stdout);
                console.log(`✅ Python result parsed from full output`);
                resolve(result);
              } catch (error) {
                console.error(`❌ Failed to parse Python output as JSON:`, error.message);
                console.log(`🐍 Full stdout: ${stdout}`);
                // If not JSON, return raw output
                resolve({ output: stdout.trim() });
              }
            }
          } catch (error) {
            console.error(`❌ Error processing Python output:`, error.message);
            resolve({ output: stdout.trim() });
          }
        }
      });

      pythonProcess.on('error', (error) => {
        clearTimeout(timeoutId);
        logger.error('Failed to start Python process:', error);
        console.error(`❌ Python process error:`, error);
        reject(error);
      });
    });
  }

  /**
   * Book appointment through Python tool
   */
  async bookAppointment(appointmentData) {
    try {
      const result = await this.executePythonScript('api_book_appointment.py', [
        JSON.stringify(appointmentData)
      ]);
      
      console.log('📋 Raw booking result:', JSON.stringify(result, null, 2));
      
      // Extract token number from result text
      if (result && result.result) {
        console.log('🔍 Searching for token in result text...');
        const tokenMatch = result.result.match(/Token Number: #(\d+)/);
        const positionMatch = result.result.match(/Position: #(\d+)/);
        
        console.log('🔍 Token match:', tokenMatch);
        console.log('🔍 Position match:', positionMatch);
        
        if (tokenMatch) {
          result.token_number = parseInt(tokenMatch[1]);
          result.queue_position = positionMatch ? parseInt(positionMatch[1]) : null;
          console.log(`✅ Extracted token: #${result.token_number}, position: #${result.queue_position}`);
        } else {
          console.log('❌ Could not extract token number from result');
        }
      }
      
      return result;
    } catch (error) {
      logger.error('Error booking appointment:', error);
      throw error;
    }
  }

  /**
   * Cancel appointment through Python tool
   */
  async cancelAppointment(tokenNumber) {
    try {
      const result = await this.executePythonScript('api_cancel_appointment.py', [
        tokenNumber.toString()
      ]);
      return result;
    } catch (error) {
      logger.error('Error canceling appointment:', error);
      throw error;
    }
  }

  /**
   * Calculate ETAs through Python tool
   */
  async calculateETAs() {
    try {
      const result = await this.executePythonScript('api_calculate_etas.py');
      return result;
    } catch (error) {
      logger.error('Error calculating ETAs:', error);
      throw error;
    }
  }

  /**
   * Mark patient as completed
   */
  async completePatient(tokenNumber) {
    try {
      const result = await this.executePythonScript('api_complete_patient.py', [
        tokenNumber.toString()
      ]);
      return result;
    } catch (error) {
      logger.error('Error completing patient:', error);
      throw error;
    }
  }

  /**
   * Update patient location
   */
  async updateLocation(tokenNumber, location) {
    try {
      const result = await this.executePythonScript('api_update_location.py', [
        tokenNumber.toString(),
        JSON.stringify(location)
      ]);
      return result;
    } catch (error) {
      logger.error('Error updating location:', error);
      throw error;
    }
  }

  /**
   * Analyze patient symptoms
   */
  async analyzeSymptoms(symptoms) {
    try {
      const result = await this.executePythonScript('api_analyze_symptoms.py', [
        symptoms
      ]);
      return result;
    } catch (error) {
      logger.error('Error analyzing symptoms:', error);
      throw error;
    }
  }

  /**
   * Analyze patient location and travel
   */
  async analyzeLocationTravel(location) {
    try {
      const result = await this.executePythonScript('api_analyze_location.py', [
        location
      ]);
      return result;
    } catch (error) {
      logger.error('Error analyzing location:', error);
      throw error;
    }
  }

  /**
   * Get intelligent doctor status
   */
  async getDoctorStatus() {
    try {
      const result = await this.executePythonScript('api_doctor_status.py');
      return result;
    } catch (error) {
      logger.error('Error getting doctor status:', error);
      throw error;
    }
  }

  /**
   * Predict optimal arrival time
   */
  async predictArrivalTime(tokenNumber) {
    try {
      const result = await this.executePythonScript('api_predict_arrival.py', [
        tokenNumber.toString()
      ]);
      return result;
    } catch (error) {
      logger.error('Error predicting arrival:', error);
      throw error;
    }
  }

  /**
   * Analyze and optimize queue
   */
  async optimizeQueue() {
    try {
      // ....Check if optimize script exists
      const fs = require('fs');
      const scriptPath = path.join(this.toolsPath, 'api_optimize_queue.py');
      
      if (!fs.existsSync(scriptPath)) {
        logger.debug('Optimize queue script not available, skipping');
        return { 
          success: false, 
          skipped: true,
          message: 'Queue optimization script not available' 
        };
      }
      
      const result = await this.executePythonScript('api_optimize_queue.py');
      return result;
    } catch (error) {
      // Only log if it's not a "file not found" error
      if (!error.message.includes('No such file') && !error.message.includes('ENOENT')) {
        logger.error('Error optimizing queue:', error);
      }
      throw error;
    }
  }

  /**
   * Get queue intelligence dashboard
   */
  async getQueueIntelligence() {
    try {
      const result = await this.executePythonScript('api_queue_intelligence.py');
      return result;
    } catch (error) {
      logger.error('Error getting queue intelligence:', error);
      throw error;
    }
  }

  /**
   * Get patient queue insights
   */
  async getPatientInsights(tokenNumber) {
    try {
      const result = await this.executePythonScript('api_patient_insights.py', [
        tokenNumber.toString()
      ]);
      return result;
    } catch (error) {
      logger.error('Error getting patient insights:', error);
      throw error;
    }
  }

  /**
   * Execute intelligent orchestration
   */
  async executeOrchestration() {
    try {
      const result = await this.executePythonScript('api_execute_orchestration.py');
      return result;
    } catch (error) {
      logger.error('Error executing orchestration:', error);
      throw error;
    }
  }

  /**
   * Monitor and trigger orchestration
   */
  async monitorOrchestration() {
    try {
      const result = await this.executePythonScript('api_monitor_orchestration.py');
      return result;
    } catch (error) {
      logger.error('Error monitoring orchestration:', error);
      throw error;
    }
  }

  /**
   * Get orchestration dashboard
   */
  async getOrchestrationDashboard() {
    try {
      const result = await this.executePythonScript('api_orchestration_dashboard.py');
      return result;
    } catch (error) {
      logger.error('Error getting orchestration dashboard:', error);
      throw error;
    }
  }

  /**
   * Send queue update notifications
   */
  async sendQueueNotifications() {
    try {
      const result = await this.executePythonScript('api_send_notifications.py');
      return result;
    } catch (error) {
      logger.error('Error sending notifications:', error);
      throw error;
    }
  }

  /**
   * Send appointment ready notification
   */
  async sendAppointmentReadyNotification(tokenNumber) {
    try {
      const result = await this.executePythonScript('api_notify_ready.py', [
        tokenNumber.toString()
      ]);
      return result;
    } catch (error) {
      logger.error('Error sending ready notification:', error);
      throw error;
    }
  }

  /**
   * Send ETA update notifications
   */
  async sendETANotifications() {
    try {
      const result = await this.executePythonScript('api_send_eta_notifications.py');
      return result;
    } catch (error) {
      logger.error('Error sending ETA notifications:', error);
      throw error;
    }
  }

  /**
   * Get notification history
   */
  async getNotificationHistory() {
    try {
      const result = await this.executePythonScript('api_notification_history.py');
      return result;
    } catch (error) {
      logger.error('Error getting notification history:', error);
      throw error;
    }
  }

  /**
   * Update ongoing patient status
   */
  async updatePatientStatus(tokenNumber, status) {
    try {
      const result = await this.executePythonScript('api_update_status.py', [
        tokenNumber.toString(),
        status
      ]);
      return result;
    } catch (error) {
      logger.error('Error updating patient status:', error);
      throw error;
    }
  }

  /**
   * Get clinic status dashboard
   */
  async getClinicDashboard() {
    try {
      const result = await this.executePythonScript('api_clinic_dashboard.py');
      return result;
    } catch (error) {
      logger.error('Error getting clinic dashboard:', error);
      throw error;
    }
  }

  /**
   * Trigger orchestration cycle
   */
  async triggerOrchestrationCycle() {
    try {
      const result = await this.executePythonScript('api_trigger_cycle.py');
      return result;
    } catch (error) {
      logger.error('Error triggering orchestration cycle:', error);
      throw error;
    }
  }
}

module.exports = new PythonBridge();
