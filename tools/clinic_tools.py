import os
import json
import redis
from datetime import datetime, timedelta

# --- CORRECTED IMPORTS ---
from tools.free_maps import (
    get_comprehensive_patient_travel_data,
    get_real_clinic_location,
)
from tools.symptom_analyzer import analyze_patient_symptoms

# --- END CORRECTIONS ---


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
    print("[OK] Enhanced Clinic Tools: Successfully connected to Redis.")
except redis.exceptions.ConnectionError as e:
    print(f"[ERROR] Enhanced Clinic Tools: Could not connect to Redis. Error: {e}")
    redis_client = None


def analyze_patient_location_and_travel(patient_location: str) -> str:
    """
    Analyze patient location and provide comprehensive travel information.

    Args:
        patient_location: Patient's location description

    Returns:
        Detailed travel analysis with multiple transport options
    """
    print(f"[TOOL] [Tool Called] Analyzing location and travel for: '{patient_location}'")

    # Get comprehensive travel data
    travel_data = get_comprehensive_patient_travel_data(patient_location)
    clinic_location = get_real_clinic_location()

    # Format the response
    result = f"""
[CLINIC] MEDISYNC TRAVEL ANALYSIS
==========================
[LOCATION] From: {travel_data['origin']['address']}
🎯 To: {clinic_location}
📅 Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

[TRAVEL] DRIVING OPTIONS:
"""

    driving = travel_data["travel_options"].get("driving", {})
    if driving.get("status") in ["success", "fallback"]:
        result += f"""   Normal Time: {driving.get('duration_mins', 'Unknown')} minutes
  With Traffic: {driving.get('traffic_duration_mins', driving.get('duration_mins', 'Unknown'))} minutes
  Distance: {driving.get('distance_km', 'Unknown')} km
  Traffic Delay: {driving.get('traffic_delay_mins', 0)} minutes

  🔴 Traffic Status: {"Heavy" if driving.get('traffic_delay_mins', 0) > 10 else "Moderate" if driving.get('traffic_delay_mins', 0) > 5 else "Light"}
"""

    walking = travel_data["travel_options"].get("walking", {})
    if walking.get("status") in ["success", "fallback"]:
        result += f"""
🚶 WALKING OPTION:
  Walking Time: {walking.get('duration_mins', 'Unknown')} minutes
  Distance: {walking.get('distance_km', 'Unknown')} km
"""

    # Add recommendations
    if driving.get("status") in ["success", "fallback"]:
        recommended_time = driving.get(
            "traffic_duration_mins", driving.get("duration_mins", 30)
        )
        result += f"""
[TIP] RECOMMENDATIONS:
  • Best Option: Driving ({recommended_time} minutes)
  • Leave Buffer: +10 minutes for parking/check-in
  • Optimal Departure: {recommended_time + 10} minutes before appointment
  • Consider traffic patterns during peak hours (9-11 AM, 12-2 PM, 4-6 PM)
"""

    print(f"[OK] [Tool Result] Travel analysis completed")
    return result.strip()


def book_intelligent_patient_appointment(
    name: str, contact_number: str, symptoms: str, location: str
) -> str:
    """
    Complete intelligent patient booking with real location analysis.

    Args:
        name: Patient's full name
        contact_number: Patient's contact number
        symptoms: Patient's symptoms description
        location: Patient's current location

    Returns:
        Complete booking confirmation with token and intelligent insights
    """
    if not redis_client:
        return "[ERROR] Error: Cannot connect to the patient queue. Please try again."

    print(f"[TOOL] [Tool Called] Complete intelligent booking for '{name}'")

    try:
        # Step 1: Analyze location and get real travel data
        travel_data = get_comprehensive_patient_travel_data(location)

        # Step 2: Analyze symptoms for urgency and timing
        symptoms_analysis = analyze_patient_symptoms(symptoms)

        # Step 3: Generate token number
        current_queue_length = redis_client.llen("patient_queue")
        emergency_queue_length = redis_client.llen("emergency_queue")
        token_number = current_queue_length + emergency_queue_length + 1

        # Step 4: Create comprehensive patient record
        patient_data = {
            "token_number": token_number,
            "name": name,
            "contact_number": contact_number,
            "symptoms": symptoms,
            "location": location,
            "status": "confirmed",
            "booking_time": (datetime.utcnow() + timedelta(hours=5, minutes=30)).isoformat(),  # IST
            "travel_data": travel_data,
            "symptoms_analysis": symptoms_analysis,
            "clinic_location": get_real_clinic_location(),
            "priority_score": 0,
        }

        # Step 5: Check for emergency cases
        is_emergency = symptoms_analysis.get("is_emergency", False)

        if is_emergency:
            # Emergency handling
            redis_client.lpush("emergency_queue", json.dumps(patient_data))
            result = f"""
🚨 EMERGENCY APPOINTMENT CONFIRMED
==================================
Patient: {name}
Token Number: #{token_number}
Status: 🔴 EMERGENCY PRIORITY

[FAST] EMERGENCY DETECTED - You will be seen IMMEDIATELY upon arrival.

[LOCATION] LOCATION VERIFIED:
From: {travel_data['origin']['address']}
To: {get_real_clinic_location()}

[TRAVEL] IMMEDIATE TRAVEL REQUIRED:
Best Route: Driving ({travel_data['travel_options']['driving'].get('traffic_duration_mins', 30)} minutes with current traffic)
🚨 LEAVE IMMEDIATELY - Emergency cases get instant attention

[MEDICAL] MEDICAL PRIORITY:
Symptoms: {symptoms_analysis['category'].replace('_', ' ').title()}
Urgency: {symptoms_analysis['urgency_score']}/10 (CRITICAL)
Expected Consultation: {symptoms_analysis['estimated_consultation_mins']} minutes

📞 Contact clinic immediately: {os.getenv('CLINIC_CONTACT', '555-MEDISYNC')}
"""
        else:
            # Regular booking
            redis_client.rpush("patient_queue", json.dumps(patient_data))

            # Calculate estimated appointment time
            driving_time = travel_data["travel_options"]["driving"].get(
                "traffic_duration_mins", 30
            )
            current_time_utc = datetime.utcnow()
            current_time = current_time_utc + timedelta(hours=5, minutes=30)  # IST

            # Estimate queue wait dynamically based on symptoms
            avg_consult_mins = symptoms_analysis.get("estimated_consultation_mins", 15)
            estimated_wait = current_queue_length * avg_consult_mins
            appointment_eta = current_time + timedelta(minutes=estimated_wait)
            optimal_departure = appointment_eta - timedelta(
                minutes=driving_time + 10
            )  # +10 for buffer

            result = f"""
[OK] APPOINTMENT SUCCESSFULLY BOOKED
==================================
Patient: {name}
Token Number: #{token_number}
Booking Time: {current_time.strftime('%Y-%m-%d %H:%M:%S IST')}

[LOCATION] LOCATION CONFIRMED:
From: {travel_data['origin']['address']}
To: {get_real_clinic_location()}

[TRAVEL] TRAVEL INTELLIGENCE:
Driving Time: {driving_time} minutes (with current traffic)
Distance: {travel_data['travel_options']['driving'].get('distance_km', 'Unknown')} km
Traffic Delay: {travel_data['travel_options']['driving'].get('traffic_delay_mins', 0)} minutes

[CLOCK] APPOINTMENT SCHEDULING:
Queue Position: #{current_queue_length + 1}
Estimated Wait: {estimated_wait} minutes
Appointment ETA: {appointment_eta.strftime('%H:%M IST')}
Recommended Departure: {optimal_departure.strftime('%H:%M IST')}

[MEDICAL] MEDICAL ASSESSMENT:
Symptoms Category: {symptoms_analysis['category'].replace('_', ' ').title()}
Urgency Level: {symptoms_analysis['urgency_score']}/10
Expected Consultation: {symptoms_analysis['estimated_consultation_mins']} minutes

[TIP] SMART RECOMMENDATIONS:
• Leave 10 minutes before recommended departure for parking
• Check traffic updates before leaving
• Arrive 5-10 minutes early for check-in
• Keep this token number handy: #{token_number}

[PHONE] You can check your queue status anytime by providing your token number.
"""

        print(
            f"[OK] [Tool Result] Complete booking confirmed for '{name}' - Token #{token_number}"
        )
        return result.strip()

    except Exception as e:
        error_message = f"[ERROR] Booking Error: {str(e)}"
        print(f"[ERROR] [Tool Error] {error_message}")
        return f"Sorry {name}, there was an error processing your booking. Please try again. Error: {error_message}"


def get_current_queue_with_real_data() -> str:
    """
    Get enhanced queue status with real location and timing data.

    Returns:
        Comprehensive queue status with real-time information
    """
    if not redis_client:
        return "[ERROR] Error: Cannot connect to the patient queue."

    print("[TOOL] [Tool Called] Getting enhanced queue with real data")

    # Get queue data
    regular_queue = redis_client.llen("patient_queue")
    emergency_queue = redis_client.llen("emergency_queue")

    if regular_queue == 0 and emergency_queue == 0:
        return f"""
🎉 QUEUE STATUS: EMPTY
=====================
The clinic queue is currently empty!

[OK] Perfect time for immediate appointments
[FAST] New patients can be seen almost immediately
[LOCATION] Clinic Location: {get_real_clinic_location()}
📞 Contact: {os.getenv('CLINIC_CONTACT', '555-MEDISYNC')}
"""

    current_time = datetime.utcnow() + timedelta(hours=5, minutes=30)  # IST
    status_lines = [
        "[STATS] REAL-TIME QUEUE STATUS",
        "=" * 50,
        f"🕐 Current Time: {current_time.strftime('%Y-%m-%d %H:%M:%S IST')}",
        f"[CLINIC] Clinic: {get_real_clinic_location()}",
        "",
    ]

    # Emergency queue
    if emergency_queue > 0:
        status_lines.extend(["🚨 EMERGENCY QUEUE (PRIORITY):", "-" * 35])

        for i in range(emergency_queue):
            patient_json = redis_client.lindex("emergency_queue", i)
            if patient_json:
                patient = json.loads(patient_json)
                travel_info = (
                    patient.get("travel_data", {})
                    .get("travel_options", {})
                    .get("driving", {})
                )

                status_lines.extend(
                    [
                        f"🚨 #{patient['token_number']}: {patient['name']} - EMERGENCY",
                        f"   Location: {patient.get('location', 'Unknown')}",
                        f"   Travel Time: {travel_info.get('traffic_duration_mins', 'Unknown')} minutes",
                        "",
                    ]
                )

    # Regular queue
    if regular_queue > 0:
        status_lines.extend([f"👥 REGULAR QUEUE ({regular_queue} patients):", "-" * 40])

        cumulative_wait = 0
        for i in range(min(regular_queue, 8)):  # Show first 8
            patient_json = redis_client.lindex("patient_queue", i)
            if patient_json:
                patient = json.loads(patient_json)
                symptoms_info = patient.get("symptoms_analysis", {})
                travel_info = (
                    patient.get("travel_data", {})
                    .get("travel_options", {})
                    .get("driving", {})
                )

                # Calculate ETA
                consultation_time = symptoms_info.get("estimated_consultation_mins", 15)
                cumulative_wait += consultation_time
                eta_time = current_time + timedelta(minutes=cumulative_wait)

                status_lines.extend(
                    [
                        f"#{i+1} Token #{patient['token_number']}: {patient['name']}",
                        f"   [LOCATION] From: {patient.get('location', 'Unknown')}",
                        f"   [TRAVEL] Travel: {travel_info.get('traffic_duration_mins', 'Unknown')}min (driving)",
                        f"   [MEDICAL] Symptoms: {symptoms_info.get('category', 'General').replace('_', ' ').title()}",
                        f"   [CLOCK] Est. Appointment: {eta_time.strftime('%H:%M UTC')}",
                        f"   🔢 Urgency: {symptoms_info.get('urgency_score', 5)}/10",
                        "",
                    ]
                )

        if regular_queue > 8:
            status_lines.append(f"... and {regular_queue - 8} more patients")

    status_lines.extend(
        [
            "",
            "[TIP] CLINIC INFORMATION:",
            f"[CLINIC] Address: {get_real_clinic_location()}",
            f"📞 Contact: {os.getenv('CLINIC_CONTACT', '555-MEDISYNC')}",
            "🕐 Peak Hours: 9-11 AM, 12-2 PM, 4-6 PM",
        ]
    )

    result = "\n".join(status_lines)
    print(
        f"[OK] [Tool Result] Enhanced queue status retrieved - {regular_queue + emergency_queue} total patients"
    )
    return result
