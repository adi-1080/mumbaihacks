/**
 * Response Formatter Utility
 * Formats raw Python tool outputs into clean, structured JSON responses
 */

/**
 * Parse booking output text into structured data
 */
function parseBookingOutput(rawOutput) {
  if (!rawOutput) return null;

  // Extract key information using regex patterns
  const patterns = {
    tokenNumber: /Token Number: #(\d+)/,
    bookingTime: /Booking Time: (.+)/,
    patientName: /Patient: (.+)/,
    location: /From: (.+)/,
    destination: /To: (.+)/,
    travelTime: /Travel Time: (\d+) minutes/,
    distance: /Distance: ([\d.]+) km/,
    trafficStatus: /Traffic Status: (.+)/,
    symptomsCategory: /Symptoms Category: (.+)/,
    urgencyLevel: /Urgency Level: (\d+)\/10/,
    emergencyClass: /Emergency Classification: (\w+)/,
    consultationTime: /Expected Consultation: (\d+) minutes/,
    priorityScore: /Priority Score: ([\d.]+)/,
    queuePosition: /Position: #(\d+) out of (\d+) patients/,
    estimatedWait: /Estimated Wait: (\d+) minutes/,
    appointmentETA: /Appointment ETA: (.+)/,
    departureTime: /Recommended Departure: (.+)/,
  };

  const extracted = {};
  for (const [key, pattern] of Object.entries(patterns)) {
    const match = rawOutput.match(pattern);
    if (match) {
      extracted[key] = match[1];
      if (key === 'queuePosition') {
        extracted.totalPatients = match[2];
      }
    }
  }

  return extracted;
}

/**
 * Parse ETA output text into structured data
 */
function parseETAOutput(rawOutput) {
  if (!rawOutput) return null;

  const result = {
    currentTime: null,
    doctorsAvailable: null,
    currentLoad: null,
    emergencyQueue: [],
    regularQueue: [],
  };

  // Extract current time
  const timeMatch = rawOutput.match(/Current Time: (.+)/);
  if (timeMatch) result.currentTime = timeMatch[1];

  // Extract doctors available
  const doctorsMatch = rawOutput.match(/Doctors Available: (\d+)/);
  if (doctorsMatch) result.doctorsAvailable = parseInt(doctorsMatch[1]);

  // Extract current load
  const loadMatch = rawOutput.match(/Current Load: (\w+)/);
  if (loadMatch) result.currentLoad = loadMatch[1];

  // Parse emergency queue entries
  const emergencyPattern = /Token #(\d+): (.+?)\n\s+Status: (.+?)\n\s+ETA: (.+?)\n\s+Expected Duration: (\d+) minutes/g;
  let match;
  while ((match = emergencyPattern.exec(rawOutput)) !== null) {
    result.emergencyQueue.push({
      tokenNumber: match[1],
      patientName: match[2],
      status: match[3],
      eta: match[4],
      duration: parseInt(match[5]),
    });
  }

  // Parse regular queue entries
  const regularPattern = /Token #(\d+): (.+?)\n\s+Queue Position: #(\d+)\n\s+Priority Score: ([\d.]+)\n\s+Symptoms: (.+?)\n\s+Urgency: (\d+)\/10\n\s+Expected Consultation: (\d+) minutes\n\s+Appointment ETA: (.+?)\n\s+Depart By: (.+?)\n/g;
  while ((match = regularPattern.exec(rawOutput)) !== null) {
    result.regularQueue.push({
      tokenNumber: match[1],
      patientName: match[2],
      queuePosition: parseInt(match[3]),
      priorityScore: parseFloat(match[4]),
      symptoms: match[5],
      urgency: parseInt(match[6]),
      consultationTime: parseInt(match[7]),
      appointmentETA: match[8],
      departBy: match[9],
    });
  }

  return result;
}

/**
 * Format booking response for API
 */
function formatBookingResponse(pythonResult, orchestrationResults) {
  const parsed = parseBookingOutput(pythonResult.result || pythonResult.output);

  // Build clean response structure
  const response = {
    success: true,
    message: '✅ Appointment booked successfully',
    patient: {
      name: parsed?.patientName || 'N/A',
      tokenNumber: parsed?.tokenNumber || pythonResult.token_number || 'N/A',
      bookingTime: parsed?.bookingTime || new Date().toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' }),
    },
    location: parsed ? {
      from: parsed.location,
      to: parsed.destination,
      distance: parsed.distance ? `${parsed.distance} km` : null,
      travelTime: parsed.travelTime ? `${parsed.travelTime} minutes` : null,
      trafficStatus: parsed.trafficStatus || null,
    } : null,
    medical: parsed ? {
      symptomsCategory: parsed.symptomsCategory,
      urgencyLevel: parsed.urgencyLevel ? `${parsed.urgencyLevel}/10` : null,
      emergencyClassification: parsed.emergencyClass,
      expectedConsultation: parsed.consultationTime ? `${parsed.consultationTime} minutes` : null,
      priorityScore: parsed.priorityScore ? parseFloat(parsed.priorityScore) : null,
    } : null,
    queue: parsed ? {
      position: parsed.queuePosition ? parseInt(parsed.queuePosition) : null,
      totalPatients: parsed.totalPatients ? parseInt(parsed.totalPatients) : null,
      estimatedWait: parsed.estimatedWait ? `${parsed.estimatedWait} minutes` : null,
      appointmentETA: parsed.appointmentETA || null,
      recommendedDeparture: parsed.departureTime || null,
    } : null,
  };

  // Add orchestration if available
  if (orchestrationResults) {
    response.orchestration = {
      enabled: true,
      actionsExecuted: orchestrationResults.followUpActions.length,
      actions: orchestrationResults.followUpActions.map(action => ({
        action: action.action,
        status: action.success ? '✅ Success' : '❌ Failed',
        reason: action.reason,
        details: action.result?.success ? 'Completed' : action.result?.error || 'No details',
      })),
    };
  }

  // Keep raw output for debugging if needed
  response._raw = {
    pythonOutput: pythonResult.result || pythonResult.output,
  };

  return response;
}

/**
 * Format ETA response for API
 */
function formatETAResponse(pythonResult) {
  const parsed = parseETAOutput(pythonResult.etas || pythonResult.output);

  if (!parsed) {
    return {
      success: false,
      message: 'Failed to parse ETA data',
      _raw: pythonResult,
    };
  }

  return {
    success: true,
    message: '✅ ETAs calculated successfully',
    queue: {
      currentTime: parsed.currentTime,
      doctorsAvailable: parsed.doctorsAvailable,
      currentLoad: parsed.currentLoad,
      emergencyQueue: {
        count: parsed.emergencyQueue.length,
        patients: parsed.emergencyQueue.map(p => ({
          tokenNumber: `#${p.tokenNumber}`,
          patient: p.patientName,
          status: p.status,
          eta: p.eta,
          expectedDuration: `${p.duration} minutes`,
        })),
      },
      regularQueue: {
        count: parsed.regularQueue.length,
        patients: parsed.regularQueue.map(p => ({
          tokenNumber: `#${p.tokenNumber}`,
          patient: p.patientName,
          position: p.queuePosition,
          priorityScore: p.priorityScore,
          symptoms: p.symptoms,
          urgency: `${p.urgency}/10`,
          consultation: `${p.consultationTime} minutes`,
          appointmentETA: p.appointmentETA,
          departBy: p.departBy,
        })),
      },
    },
    _raw: {
      pythonOutput: pythonResult.etas || pythonResult.output,
    },
  };
}

/**
 * Format completion response for API
 */
function formatCompletionResponse(pythonResult, orchestrationResults) {
  return {
    success: true,
    message: '✅ Patient consultation completed',
    tokenNumber: pythonResult.token_number || 'N/A',
    completionTime: new Date().toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' }),
    orchestration: orchestrationResults ? {
      enabled: true,
      actionsExecuted: orchestrationResults.followUpActions.length,
      actions: orchestrationResults.followUpActions.map(action => ({
        action: action.action,
        status: action.success ? '✅ Success' : '❌ Failed',
        reason: action.reason,
      })),
    } : null,
    _raw: {
      pythonOutput: pythonResult.result || pythonResult.output,
    },
  };
}

module.exports = {
  formatBookingResponse,
  formatETAResponse,
  formatCompletionResponse,
  parseBookingOutput,
  parseETAOutput,
};
