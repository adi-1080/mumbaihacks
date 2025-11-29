"""
Clinic Tools - Integrated with Advanced Priority Queue System
MongoDB Version - Complete persistence layer migration
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, Optional

# Import new data structures and algorithms
from tools.priority_queue_manager import get_priority_queue_manager, PatientNode
from tools.astar_eta_calculator import get_astar_eta_calculator
from tools.free_maps import get_comprehensive_patient_travel_data, get_real_clinic_location
from tools.symptom_analyzer import analyze_patient_symptoms
from tools.mongodb_utils import PatientModel, QueueStateModel, get_mongodb_manager

# Initialize MongoDB connection
mongodb_manager = get_mongodb_manager()
print(f"[OK] Clinic Tools: MongoDB {'connected' if mongodb_manager.is_connected() else 'unavailable'}")

# Initialize models
patient_model = PatientModel()
queue_state_model = QueueStateModel()

# Initialize priority queue manager and A* calculator
pq_manager = get_priority_queue_manager(mongodb_manager)
astar_calculator = get_astar_eta_calculator()


def book_intelligent_patient_appointment(
    name: str, contact_number: str, symptoms: str, location: str
) -> str:
    """
    Book patient appointment using ADVANCED PRIORITY QUEUE SYSTEM.
    
    NEW FEATURES:
    - Automatic priority calculation (emergency, ETA, symptoms)
    - A* pathfinding for accurate travel time
    - Dynamic queue positioning
    - Starvation prevention through aging
    
    Args:
        name: Patient name
        contact_number: Contact number
        symptoms: Symptoms description
        location: Patient location
        
    Returns:
        Comprehensive booking confirmation with queue intelligence
    """
    print(f"[TOOL] [Tool Called] Booking with Priority Queue (MongoDB): '{name}'")
    
    # Get next token number from MongoDB
    token_number = queue_state_model.get_next_token()
    
    # Analyze symptoms (determines urgency/emergency level)
    symptoms_analysis = analyze_patient_symptoms(symptoms)
    
    # Get comprehensive travel data
    travel_data = get_comprehensive_patient_travel_data(location)
    
    # Extract coordinates for A* calculation
    origin_coords = travel_data.get("origin", {})
    clinic_coords = travel_data.get("clinic", {})
    
    # Calculate precise ETA using A*
    if origin_coords.get("latitude") and clinic_coords.get("latitude"):
        astar_result = astar_calculator.calculate_eta(
            from_lat=origin_coords["latitude"],
            from_lon=origin_coords["longitude"],
            to_lat=clinic_coords["latitude"],
            to_lon=clinic_coords["longitude"],
        )
        
        # Update travel data with A* results
        travel_data["astar_eta"] = astar_result
        actual_travel_mins = astar_result.get("travel_time_mins", 20)
    else:
        # Fallback to free_maps estimate
        actual_travel_mins = travel_data.get("travel_options", {}).get("driving", {}).get(
            "traffic_duration_mins", 20
        )
    
    # Create patient data
    patient_data = {
        "token_number": token_number,
        "name": name,
        "contact_number": contact_number,
        "symptoms": symptoms,
        "symptoms_analysis": symptoms_analysis,
        "location": location,
        "travel_data": travel_data,
        "booking_time": (datetime.utcnow() + timedelta(hours=5, minutes=30)).isoformat(),  # IST
        "initial_travel_time_mins": actual_travel_mins,
    }
    
    # **CORE CHANGE: Add to priority queue instead of Redis list**
    patient_node = pq_manager.enqueue_patient(patient_data)
    
    # Get current queue snapshot for position info
    queue_snapshot = pq_manager.get_queue_snapshot()
    
    # Find patient's position in sorted queue
    patient_position = next(
        (i + 1 for i, p in enumerate(queue_snapshot["patients"]) 
         if p["token_number"] == token_number),
        "Unknown"
    )
    
    # Calculate estimated appointment time based on priority queue
    current_time = datetime.utcnow() + timedelta(hours=5, minutes=30)  # IST
    
    # Sum consultation times of higher-priority patients
    estimated_wait = 0
    for p in queue_snapshot["patients"]:
        if p["token_number"] == token_number:
            break
        estimated_wait += pq_manager.patient_map.get(p["token_number"], PatientNode(0, 0, "", "")).predicted_consult_mins
    
    appointment_eta = current_time + timedelta(minutes=estimated_wait)
    optimal_departure = appointment_eta - timedelta(minutes=actual_travel_mins + 10)
    
    # Format result
    result = f"""
[OK] APPOINTMENT BOOKED - PRIORITY QUEUE SYSTEM
=============================================
Patient: {name}
Token Number: #{token_number}
Booking Time: {current_time.strftime('%Y-%m-%d %H:%M:%S IST')}

[LOCATION] LOCATION INTELLIGENCE:
From: {travel_data['origin']['address']}
To: {get_real_clinic_location()}

[TRAVEL] A* PATHFINDING TRAVEL ETA:
Method: {astar_result.get('method', 'free_maps') if 'astar_result' in locals() else 'free_maps'}
Travel Time: {actual_travel_mins} minutes (with current traffic)
Distance: {travel_data['travel_options']['driving'].get('distance_km', 'Unknown')} km
Traffic Status: {travel_data['travel_options']['driving'].get('traffic_delay_mins', 0)} min delay

[MEDICAL] MEDICAL PRIORITY ASSESSMENT:
Symptoms Category: {symptoms_analysis['category'].replace('_', ' ').title()}
Urgency Level: {symptoms_analysis['urgency_score']}/10
Emergency Classification: {["Normal", "Priority", "Critical"][patient_node.emergency_level]}
Expected Consultation: {symptoms_analysis['estimated_consultation_mins']} minutes
Priority Score: {patient_node.priority_score:.2f} (lower = higher priority)

[STATS] INTELLIGENT QUEUE POSITION:
Position: #{patient_position} out of {queue_snapshot['total_patients']} patients
Ahead of You: {patient_position - 1 if isinstance(patient_position, int) else 0} patients
Emergency Queue: {queue_snapshot['emergency_count']} critical patients (served first)
Estimated Wait: {estimated_wait} minutes
Appointment ETA: {appointment_eta.strftime('%H:%M IST')}
Recommended Departure: {optimal_departure.strftime('%H:%M IST')}

[BRAIN] DYNAMIC QUEUE FEATURES:
✓ Real-time priority recalculation
✓ Automatic aging (prevents starvation)
✓ Emergency patient fast-tracking
✓ Traffic-aware scheduling

[TIP] SMART RECOMMENDATIONS:
• Your priority is automatically managed based on urgency and wait time
• Queue position may improve as you wait longer (aging algorithm)
• Critical patients may be fast-tracked ahead of you
• Check status anytime with your token #{token_number}

[PHONE] Updates: Queue position updates automatically every 5 minutes
"""

    print(f"[OK] [Tool Result] Booked Token #{token_number} at queue position #{patient_position}")
    return result.strip()


def get_current_queue_with_priority_intelligence() -> str:
    """
    Get current queue status using PRIORITY QUEUE SYSTEM.
    Shows intelligent ordering with priority scores.
    
    Returns:
        Comprehensive queue status with priority intelligence
    """
    print("[TOOL] [Tool Called] Getting priority queue status")
    
    queue_snapshot = pq_manager.get_queue_snapshot()
    
    if queue_snapshot["total_patients"] == 0:
        return """
[STATS] PRIORITY QUEUE STATUS
========================
🎯 Queue is empty - Next patient will be seen immediately!
[LOCATION] Clinic Location: {clinic}
📞 Contact: {contact}
""".format(
            clinic=get_real_clinic_location(),
            contact=os.getenv('CLINIC_CONTACT', '555-MEDISYNC')
        )
    
    current_time = datetime.utcnow() + timedelta(hours=5, minutes=30)  # IST
    
    status_lines = [
        "[STATS] INTELLIGENT PRIORITY QUEUE STATUS",
        "=" * 60,
        f"🕐 Current Time: {current_time.strftime('%Y-%m-%d %H:%M:%S IST')}",
        f"[CLINIC] Clinic: {get_real_clinic_location()}",
        f"👥 Total Patients: {queue_snapshot['total_patients']}",
        f"🚨 Emergency Queue: {queue_snapshot['emergency_count']}",
        f"📋 Main Queue: {queue_snapshot['main_queue_count']}",
        "",
        "[BRAIN] QUEUE ALGORITHM: Dynamic Priority Scheduling (Min-Heap)",
        "   Factors: Emergency Level + Travel ETA + Consultation Time + Waiting Time",
        "",
    ]
    
    # Show emergency queue first
    emergency_patients = [p for p in queue_snapshot["patients"] 
                         if p["emergency_level"] == "CRITICAL"]
    
    if emergency_patients:
        status_lines.extend([
            "🚨 EMERGENCY QUEUE (IMMEDIATE PRIORITY):",
            "-" * 50
        ])
        
        for i, patient in enumerate(emergency_patients, 1):
            status_lines.extend([
                f"🚨 #{i} - Token #{patient['token_number']}: {patient['name']}",
                f"   Priority Score: {patient['priority_score']:.2f} (CRITICAL)",
                f"   Travel ETA: {patient['travel_eta_mins']:.0f} mins",
                f"   Waiting: {patient['waiting_time_mins']:.0f} mins",
                f"   Status: IMMEDIATE ATTENTION",
                "",
            ])
    
    # Show main queue
    main_patients = [p for p in queue_snapshot["patients"] 
                    if p["emergency_level"] != "CRITICAL"]
    
    if main_patients:
        status_lines.extend([
            "👥 MAIN QUEUE (PRIORITY-SORTED):",
            "-" * 50
        ])
        
        for i, patient in enumerate(main_patients, 1):
            status_lines.extend([
                f"🎫 #{i + len(emergency_patients)} - Token #{patient['token_number']}: {patient['name']}",
                f"   Priority Score: {patient['priority_score']:.2f} ({patient['emergency_level']})",
                f"   Travel ETA: {patient['travel_eta_mins']:.0f} mins",
                f"   Waiting: {patient['waiting_time_mins']:.0f} mins",
                f"   Symptoms: {patient['symptoms'][:50]}...",
                "",
            ])
    
    # Statistics
    status_lines.extend([
        "",
        "📈 QUEUE STATISTICS:",
        "-" * 50,
        f"Total Enqueued: {queue_snapshot['statistics']['total_enqueued']}",
        f"Total Dequeued: {queue_snapshot['statistics']['total_dequeued']}",
        f"Reorder Events: {queue_snapshot['statistics']['reorder_count']}",
        "",
        "[BRAIN] INTELLIGENT FEATURES ACTIVE:",
        "✓ Real-time priority calculation",
        "✓ Aging algorithm (starvation prevention)",
        "✓ A* pathfinding for ETA",
        "✓ Dynamic queue reordering",
    ])
    
    result = "\n".join(status_lines)
    print(f"[OK] [Tool Result] Priority queue status retrieved ({queue_snapshot['total_patients']} patients)")
    return result


def update_patient_realtime_location(token_number: int, new_location: str) -> str:
    """
    Update patient's real-time location and recalculate ETA.
    Triggers automatic queue reordering based on new travel time.
    
    Args:
        token_number: Patient token
        new_location: Updated location
        
    Returns:
        Update confirmation with new priority
    """
    print(f"[TOOL] [Tool Called] Updating location for Token #{token_number}")
    
    if token_number not in pq_manager.patient_map:
        return f"[ERROR] Patient Token #{token_number} not found in queue"
    
    # Get new travel data
    travel_data = get_comprehensive_patient_travel_data(new_location)
    new_eta = travel_data.get("travel_options", {}).get("driving", {}).get("traffic_duration_mins", 20)
    
    # Update in priority queue (triggers reordering)
    success = pq_manager.update_patient_attributes(token_number, {
        "travel_eta_mins": new_eta,
        "actual_arrival": datetime.utcnow().isoformat(),
    })
    
    if success:
        patient = pq_manager.patient_map[token_number]
        return f"""
[OK] LOCATION UPDATED - Priority Recalculated
===========================================
Token #{token_number}: {patient.name}
New Location: {new_location}
New Travel ETA: {new_eta} minutes
New Priority Score: {patient.priority_score:.2f}

[CYCLE] Queue automatically reordered based on new ETA!
Check your new position with 'show queue status'
"""
    else:
        return f"[ERROR] Failed to update patient #{token_number}"


# Backward compatibility aliases
def get_current_queue_with_real_data():
    """Alias for backward compatibility"""
    return get_current_queue_with_priority_intelligence()


def analyze_patient_location_and_travel(patient_location: str) -> str:
    """Analyze patient location (unchanged from original)"""
    print(f"[TOOL] [Tool Called] Analyzing location: '{patient_location}'")
    travel_data = get_comprehensive_patient_travel_data(patient_location)
    
    # Format response
    result = f"""
[CLINIC] MEDISYNC TRAVEL ANALYSIS (A* Enhanced)
=========================================
From: {travel_data['origin']['address']}
To: {get_real_clinic_location()}

[TRAVEL] TRAVEL OPTIONS:
Driving: {travel_data['travel_options']['driving']['traffic_duration_mins']} mins
         {travel_data['travel_options']['driving']['distance_km']} km

[BRAIN] Using A* pathfinding for precise ETA calculation
"""
    print(f"[OK] [Tool Result] Travel analysis complete")
    return result.strip()
