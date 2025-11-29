import os
import json
import redis
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Import Priority Queue Manager
from tools.priority_queue_manager import get_priority_queue_manager

# Redis connection
try:
    redis_client = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        password=os.getenv("REDIS_PASSWORD", None),
        db=0,
        decode_responses=True,
    )
    redis_client.ping()
    print("[OK] Clinic Monitor: Successfully connected to Redis.")
except redis.exceptions.ConnectionError as e:
    print(f"[ERROR] Clinic Monitor: Could not connect to Redis. Error: {e}")
    redis_client = None

# Get priority queue manager instance
pq_manager = get_priority_queue_manager(redis_client) if redis_client else None

def update_ongoing_patient_status(patient_token: int, status: str = "IN_CONSULTATION") -> str:
    """
    Update the status of currently ongoing patient.
    
    Args:
        patient_token: Token of patient currently being treated
        status: Status update (IN_CONSULTATION, COMPLETED, etc.)
        
    Returns:
        Status update confirmation
    """
    if not redis_client:
        return "[ERROR] Error: Cannot connect to clinic monitoring system."
    
    print(f"👨‍[MEDICAL] [Clinic Monitor] Updating Token #{patient_token} status to {status}")
    
    # Update ongoing patient tracker
    ongoing_data = {
        "current_patient_token": patient_token,
        "status": status,
        "start_time": datetime.utcnow().isoformat(),
        "last_updated": datetime.utcnow().isoformat()
    }
    
    redis_client.set("ongoing_patient_status", json.dumps(ongoing_data))
    
    # Log the status change
    status_log = {
        "patient_token": patient_token,
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "logged_by": "ClinicMonitor"
    }
    
    log_key = f"status_log:{patient_token}:{datetime.utcnow().timestamp()}"
    redis_client.set(log_key, json.dumps(status_log), ex=86400)  # 24 hour expiry
    
    return f"""
👨‍[MEDICAL] PATIENT STATUS UPDATED
==========================
Patient Token: #{patient_token}
New Status: {status}
Updated At: {datetime.utcnow().strftime('%H:%M:%S UTC')}

[OK] Ongoing patient tracker updated successfully!
[CYCLE] System ready for automatic queue optimization triggers.
"""

def mark_patient_completed(patient_token: int) -> str:
    """
    Mark a patient as completed and trigger queue optimization.
    
    Args:
        patient_token: Token of completed patient
        
    Returns:
        Completion confirmation with next steps
    """
    if not redis_client:
        return "[ERROR] Error: Cannot connect to clinic monitoring system."
    
    print(f"[OK] [Clinic Monitor] Marking Token #{patient_token} as COMPLETED")
    
    # Remove patient from active queues
    patient_removed = _remove_patient_from_queues(patient_token)
    
    # Update ongoing status
    completion_data = {
        "completed_patient_token": patient_token,
        "completion_time": datetime.utcnow().isoformat(),
        "next_patient_ready": True,
        "optimization_trigger": True
    }
    
    redis_client.set("last_completed_patient", json.dumps(completion_data))
    redis_client.delete("ongoing_patient_status")  # Clear ongoing status
    
    # Get next patient in line
    next_patient = _get_next_patient_in_queue()
    
    result = f"""
[OK] PATIENT CONSULTATION COMPLETED
================================
Completed: Token #{patient_token}
Completion Time: {datetime.utcnow().strftime('%H:%M:%S UTC')}
Patient Removed: {'[OK] Success' if patient_removed else '[ERROR] Not found'}

🎯 NEXT PATIENT READY:
"""
    
    if next_patient:
        result += f"""├─ Next Patient: {next_patient.get('name')} (Token #{next_patient.get('token_number')})
├─ Estimated Consultation: {next_patient.get('symptoms_analysis', {}).get('estimated_consultation_mins', 15)} minutes
└─ Queue Position: #1

[CYCLE] AUTOMATIC TRIGGERS ACTIVATED:
├─ Queue optimization will run automatically
├─ ETA recalculation for remaining patients
└─ Patient notifications will be sent

[OK] System orchestration in progress..."""
    else:
        result += """├─ Queue Status: Empty
└─ No patients waiting

🎉 All patients have been served!"""
    
    return result.strip()

def get_clinic_status_dashboard() -> str:
    """
    Get comprehensive clinic status dashboard.
    
    Returns:
        Real-time clinic status
    """
    if not redis_client:
        return "[ERROR] Error: Cannot connect to clinic monitoring system."
    
    # Get ongoing patient info
    ongoing_data = redis_client.get("ongoing_patient_status")
    ongoing_patient = json.loads(ongoing_data) if ongoing_data else None
    
    # Get last completed patient
    completed_data = redis_client.get("last_completed_patient")
    last_completed = json.loads(completed_data) if completed_data else None
    
    # Get queue stats from Priority Queue Manager
    if pq_manager:
        queue_snapshot = pq_manager.get_queue_snapshot()
        regular_queue_length = queue_snapshot.get("main_queue_size", 0)
        emergency_queue_length = queue_snapshot.get("emergency_queue_size", 0)
    else:
        regular_queue_length = 0
        emergency_queue_length = 0
    
    # Get time stats
    current_time = datetime.utcnow().strftime('%H:%M:%S UTC')
    
    dashboard = f"""
👨‍[MEDICAL] MEDISYNC CLINIC STATUS DASHBOARD
===================================
🕐 Current Time: {current_time}
[STATS] Live Monitoring: Active

[CLINIC] CURRENT CONSULTATION:
"""
    
    if ongoing_patient:
        consultation_duration = _calculate_duration(ongoing_patient.get('start_time'))
        dashboard += f"""├─ Patient: Token #{ongoing_patient.get('current_patient_token')}
├─ Status: {ongoing_patient.get('status')}
├─ Duration: {consultation_duration} minutes
└─ Started: {ongoing_patient.get('start_time', 'Unknown')[:16]}"""
    else:
        dashboard += """├─ Status: No ongoing consultation
├─ Availability: Ready for next patient
└─ Waiting Time: 0 minutes"""
    
    dashboard += f"""

📋 QUEUE STATUS:
├─ Regular Queue: {regular_queue_length} patients
├─ Emergency Queue: {emergency_queue_length} patients
├─ Total Waiting: {regular_queue_length + emergency_queue_length} patients
└─ Estimated Total Wait: {(regular_queue_length * 15)} minutes

[CYCLE] RECENT ACTIVITY:
"""
    
    if last_completed:
        completion_time = last_completed.get('completion_time', 'Unknown')[:16]
        dashboard += f"""├─ Last Completed: Token #{last_completed.get('completed_patient_token')}
├─ Completed At: {completion_time}
└─ System Status: Optimization triggered"""
    else:
        dashboard += """├─ No recent completions
└─ System Status: Awaiting first consultation"""
    
    dashboard += f"""

[FAST] SYSTEM PERFORMANCE:
├─ Auto-optimization: Active
├─ Real-time monitoring: Enabled
├─ Patient notifications: Active
└─ Queue intelligence: Running

[TIP] RECOMMENDATIONS:
"""
    
    if regular_queue_length > 5:
        dashboard += "├─ High queue volume - consider optimization"
    elif regular_queue_length == 0 and emergency_queue_length == 0:
        dashboard += "├─ No patients waiting - excellent efficiency"
    else:
        dashboard += "├─ Queue operating at optimal levels"
    
    return dashboard.strip()

def trigger_orchestration_cycle() -> str:
    """
    Manually trigger the orchestration cycle.
    
    Returns:
        Orchestration trigger confirmation
    """
    if not redis_client:
        return "[ERROR] Error: Cannot connect to clinic monitoring system."
    
    trigger_data = {
        "trigger_type": "MANUAL",
        "triggered_at": datetime.utcnow().isoformat(),
        "triggered_by": "ClinicMonitor",
        "reason": "Manual orchestration cycle request"
    }
    
    redis_client.set("orchestration_trigger", json.dumps(trigger_data), ex=300)  # 5 min expiry
    
    return f"""
[CYCLE] ORCHESTRATION CYCLE TRIGGERED
===============================
Trigger Type: Manual
Triggered At: {datetime.utcnow().strftime('%H:%M:%S UTC')}

🎯 ORCHESTRATION SEQUENCE:
├─ Step 1: ETA Calculation Agent activated
├─ Step 2: Queue Brain optimization initiated  
├─ Step 3: Patient notifications prepared
└─ Step 4: System state updated

[FAST] Automatic orchestration cycle in progress...
[OK] All agents will execute in sequence.
"""

def _remove_patient_from_queues(patient_token: int) -> bool:
    """Remove patient from priority queue using Priority Queue Manager"""
    try:
        if not pq_manager:
            print("[ERROR] Priority Queue Manager not initialized")
            return False

        # Check if patient exists in the queue
        patient = pq_manager.patient_map.get(patient_token)
        if not patient:
            print(f"[ERROR] Patient with token {patient_token} not found in queue")
            return False

        # Remove patient from priority queue by token
        removed = pq_manager.remove_patient(patient_token)
        if removed:
            print(f"[OK] Successfully removed patient {patient_token} from priority queue")
            return True
        else:
            print(f"[ERROR] Failed to remove patient {patient_token} from priority queue")
            return False

    except Exception as e:
        print(f"[ERROR] Error removing patient from queues: {e}")
        return False

def _get_next_patient_in_queue() -> Optional[Dict]:
    """Get next patient in line using Priority Queue Manager"""
    try:
        if not pq_manager:
            print("[ERROR] Priority Queue Manager not initialized")
            return None
        
        # Peek at the next patient without removing them
        next_patient = pq_manager.peek()
        if next_patient:
            # Convert PatientNode object to dict for compatibility
            return {
                "token_number": next_patient.token_number,
                "name": next_patient.name,
                "contact_number": next_patient.contact_number,
                "symptoms": next_patient.symptoms,
                "symptoms_analysis": next_patient.symptoms_analysis,
                "priority_score": next_patient.priority_score,
                "is_emergency": next_patient.emergency_level == 2  # CRITICAL = 2
            }
        
        return None
    except Exception as e:
        print(f"[ERROR] Error getting next patient: {e}")
        return None

def _calculate_duration(start_time_str: str) -> int:
    """Calculate duration in minutes from start time"""
    try:
        start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
        current_time = datetime.utcnow().replace(tzinfo=start_time.tzinfo)
        return int((current_time - start_time).total_seconds() / 60)
    except Exception:
        return 0