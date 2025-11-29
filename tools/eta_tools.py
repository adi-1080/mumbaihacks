import os
import json
import redis
from datetime import datetime, timedelta
import random

# --- CORRECTED IMPORT ---
from tools.symptom_analyzer import analyze_patient_symptoms
from tools.priority_queue_manager import get_priority_queue_manager

# --- END CORRECTION ---


# --- Redis Connection ---
try:
    redis_client = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        password=os.getenv("REDIS_PASSWORD", None),
        db=0,
        decode_responses=True,
    )
    redis_client.ping()
    print("[OK] ETA Tools: Successfully connected to Redis.")
except redis.exceptions.ConnectionError as e:
    print(f"[ERROR] ETA Tools: Could not connect to Redis. Error: {e}")
    redis_client = None

# Initialize priority queue manager
pq_manager = get_priority_queue_manager(redis_client) if redis_client else None


def get_intelligent_doctor_status() -> dict:
    """
    Get enhanced doctor status with intelligent scheduling insights.

    Returns:
        Comprehensive doctor and clinic status information
    """
    print("[TOOL] [Tool Called] Getting intelligent doctor status")

    # Simulate intelligent doctor status
    # In production, this would connect to clinic management system
    # Use IST timezone (UTC + 5:30)
    current_time = datetime.utcnow() + timedelta(hours=5, minutes=30)
    hour = current_time.hour

    # Adjust availability based on time of day
    if 9 <= hour <= 11:  # Morning peak
        doctors_available = random.randint(2, 4)
        efficiency_factor = 0.9
    elif 11 <= hour <= 14:  # Pre-lunch rush
        doctors_available = random.randint(3, 5)
        efficiency_factor = 1.0
    elif 14 <= hour <= 16:  # Post-lunch
        doctors_available = random.randint(2, 3)
        efficiency_factor = 0.8
    elif 16 <= hour <= 18:  # Evening rush
        doctors_available = random.randint(3, 4)
        efficiency_factor = 0.95
    else:  # Off-peak
        doctors_available = random.randint(1, 2)
        efficiency_factor = 1.1

    current_consult_time = random.randint(8, 20)
    
    status = {
        "doctors_available": doctors_available,
        "current_consultation_time_mins": current_consult_time,
        "average_consultation_time_mins": current_consult_time,  # Dynamic, not hardcoded
        "efficiency_factor": efficiency_factor,
        "break_time_mins": random.choice([0, 0, 0, 5]),
        "peak_hours": "9-11 AM, 12-2 PM, 4-6 PM",
        "current_load": "normal" if doctors_available >= 3 else "high",
        "estimated_processing_rate": f"{doctors_available * 4}-{doctors_available * 5} patients/hour",
    }

    print(
        f"[OK] [Tool Result] Doctor status: {doctors_available} doctors available, {status['current_load']} load"
    )
    return status


def calculate_intelligent_etas() -> str:
    """
    Calculate intelligent ETAs using symptom analysis and real-time data.

    Returns:
        Comprehensive ETA analysis for all patients
    """
    if not redis_client:
        return "Error: Cannot connect to the patient queue for ETA calculation."

    print("[TOOL] [Tool Called] Calculating intelligent ETAs")

    # Get queue snapshot from priority queue manager
    if not pq_manager:
        return "Error: Priority Queue Manager not initialized."
    
    queue_snapshot = pq_manager.get_queue_snapshot()
    
    if queue_snapshot["total_patients"] == 0:
        return "No patients in queue. No ETAs to calculate."

    # Get doctor status
    doctor_status = get_intelligent_doctor_status()

    eta_results = []
    current_time_ist = datetime.utcnow() + timedelta(hours=5, minutes=30)
    eta_results.extend(
        [
            "[BRAIN] INTELLIGENT ETA CALCULATIONS",
            "=" * 60,
            f"Current Time: {current_time_ist.strftime('%H:%M:%S IST')}",
            f"Doctors Available: {doctor_status['doctors_available']}",
            f"Current Load: {doctor_status['current_load'].upper()}",
            f"Processing Rate: {doctor_status['estimated_processing_rate']}",
            "",
        ]
    )

    current_time = datetime.utcnow()
    cumulative_time = 0

    # Get sorted patients from queue snapshot (emergency first, then main queue)
    all_patients = queue_snapshot["patients"]
    
    if len(all_patients) == 0:
        return "No patients to calculate ETAs for."

    # Process all patients in priority order
    for patient in all_patients:
        is_emergency = patient["emergency_level"] in ["PRIORITY", "CRITICAL"]
        
        if is_emergency:
            # Emergency patients section header (only show once)
            if cumulative_time == 0:
                eta_results.extend(["🚨 EMERGENCY QUEUE - IMMEDIATE PRIORITY", "=" * 45])
            
            # Emergency patients get immediate attention
            eta_time = current_time + timedelta(minutes=cumulative_time)
            consultation_time = patient.get("symptoms_analysis", {}).get(
                "estimated_consultation_mins", 20
            )
            cumulative_time += consultation_time

            eta_time_ist = eta_time + timedelta(hours=5, minutes=30)
            eta_results.extend(
                [
                    f"🚨 Token #{patient['token_number']}: {patient['name']}",
                    f"   Status: EMERGENCY - IMMEDIATE ATTENTION",
                    f"   ETA: {eta_time_ist.strftime('%H:%M IST')} (NOW)",
                    f"   Expected Duration: {consultation_time} minutes",
                    "",
                ]
            )
        else:
            # Regular queue section header (only show once)
            if "👥 REGULAR QUEUE SCHEDULE" not in "\n".join(eta_results):
                if queue_snapshot["emergency_count"] > 0:
                    eta_results.extend(["", "👥 REGULAR QUEUE SCHEDULE", "=" * 30])
                else:
                    eta_results.extend(["👥 REGULAR QUEUE SCHEDULE", "=" * 30])
            
            symptoms_analysis = patient.get("symptoms_analysis", {})

            # Calculate intelligent wait time
            consultation_time = symptoms_analysis.get(
                "estimated_consultation_mins", 15
            )

            # Apply efficiency factors
            adjusted_time = consultation_time * doctor_status["efficiency_factor"]

            # Consider multiple doctors
            if doctor_status["doctors_available"] > 1:
                parallel_factor = min(0.7, 1 / doctor_status["doctors_available"])
                adjusted_time *= 1 - parallel_factor

            cumulative_time += adjusted_time

            # Calculate ETAs
            eta_time = current_time + timedelta(minutes=cumulative_time)
            travel_time = patient.get("travel_data", {}).get("travel_options", {}).get("driving", {}).get("traffic_duration_mins", 20)
            should_leave_at = eta_time - timedelta(minutes=travel_time)

            # Status based on travel time
            time_to_leave = (should_leave_at - current_time).total_seconds() / 60
            if time_to_leave <= 0:
                travel_status = "[TRAVEL] Should leave NOW"
            elif time_to_leave <= 5:
                travel_status = f"🟡 Leave in {int(time_to_leave)} minutes"
            else:
                travel_status = f"🟢 Leave in {int(time_to_leave)} minutes"

            eta_time_ist = eta_time + timedelta(hours=5, minutes=30)
            should_leave_ist = should_leave_at + timedelta(hours=5, minutes=30)
            
            eta_results.extend(
                [
                    f"🎫 Token #{patient['token_number']}: {patient['name']}",
                    f"   Queue Position: #{all_patients.index(patient) + 1}",
                    f"   Priority Score: {patient.get('priority_score', 'N/A')}",
                    f"   Symptoms: {symptoms_analysis.get('category', 'General').replace('_', ' ').title()}",
                    f"   Urgency: {symptoms_analysis.get('urgency_score', 5)}/10",
                    f"   Expected Consultation: {consultation_time} minutes",
                    f"   Appointment ETA: {eta_time_ist.strftime('%H:%M IST')}",
                    f"   Depart By: {should_leave_ist.strftime('%H:%M IST')}",
                    f"   Travel Recommendation: {travel_status}",
                    "",
                ]
            )

    result = "\n".join(eta_results)
    print(
        f"[OK] [Tool Result] Calculated intelligent ETAs for {len(all_patients)} patients"
    )
    return result


def predict_optimal_arrival_time(token_number: int) -> str:
    """
    Predict optimal arrival time for a specific patient.

    Args:
        token_number: Patient's token number

    Returns:
        Personalized arrival time recommendation
    """
    if not redis_client:
        return "Error: Cannot connect to the patient queue."

    print(f"[TOOL] [Tool Called] Predicting optimal arrival for token #{token_number}")

    # Find the patient using priority queue manager
    if not pq_manager:
        return "Error: Priority Queue Manager not initialized."
    
    queue_snapshot = pq_manager.get_queue_snapshot()
    patient_found = None
    queue_position = -1

    # Find patient in sorted queue
    for i, patient in enumerate(queue_snapshot["patients"]):
        if patient["token_number"] == token_number:
            patient_found = patient
            queue_position = i
            break

    if not patient_found:
        return f"Patient with token #{token_number} not found in queue."

    # Calculate personalized prediction
    doctor_status = get_intelligent_doctor_status()
    symptoms_analysis = patient_found.get("symptoms_analysis", {})

    # Estimate wait time based on priority queue position
    estimated_wait = queue_position * (
        symptoms_analysis.get("estimated_consultation_mins", 15)
        * doctor_status["efficiency_factor"]
    )

    if doctor_status["doctors_available"] > 1:
        estimated_wait *= 0.7  # Multiple doctors reduce wait

    # Calculate optimal times (in IST)
    current_time = datetime.utcnow()
    appointment_time = current_time + timedelta(minutes=estimated_wait)
    travel_time = patient_found.get("travel_data", {}).get("travel_options", {}).get("driving", {}).get("traffic_duration_mins", 20)
    optimal_departure = appointment_time - timedelta(minutes=travel_time)

    # Buffer recommendation
    early_departure = optimal_departure - timedelta(minutes=10)
    late_departure = optimal_departure + timedelta(minutes=5)

    # Convert all to IST
    appointment_time_ist = appointment_time + timedelta(hours=5, minutes=30)
    optimal_departure_ist = optimal_departure + timedelta(hours=5, minutes=30)
    early_departure_ist = early_departure + timedelta(hours=5, minutes=30)
    late_departure_ist = late_departure + timedelta(hours=5, minutes=30)

    result = f"""
[CLOCK] PERSONALIZED ARRIVAL PREDICTION
==================================
Patient: {patient_found['name']}
Token: #{token_number}
Queue Position: #{queue_position + 1}

[CLINIC] APPOINTMENT DETAILS
Estimated Appointment Time: {appointment_time_ist.strftime('%H:%M IST')}
Expected Wait: {int(estimated_wait)} minutes
Consultation Duration: {symptoms_analysis.get('estimated_consultation_mins', 15)} minutes

[TRAVEL] TRAVEL RECOMMENDATIONS
Your Travel Time: {travel_time} minutes
Optimal Departure: {optimal_departure_ist.strftime('%H:%M IST')}
Early Window: {early_departure_ist.strftime('%H:%M IST')} (recommended)
Late Window: {late_departure_ist.strftime('%H:%M IST')} (maximum delay)

[TIP] SMART TIPS
- Leave 10 minutes early to account for traffic
- Check queue status before leaving
- Arrive 5-10 minutes before your slot for check-in

[FAST] Current clinic load: {doctor_status['current_load'].upper()}
"""

    print(
        f"[OK] [Tool Result] Generated personalized arrival prediction for token #{token_number}"
    )
    return result.strip()
