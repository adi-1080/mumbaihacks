import os
import json
import redis
from datetime import datetime, timedelta
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
    print("[OK] Notification Agent: Successfully connected to Redis.")
except redis.exceptions.ConnectionError as e:
    print(f"[ERROR] Notification Agent: Could not connect to Redis. Error: {e}")
    redis_client = None

# Get priority queue manager
pq_manager = get_priority_queue_manager(redis_client) if redis_client else None


def send_queue_update_notifications() -> str:
    """
    Send notifications to patients whose queue positions have changed.
    Automatically detects recent position changes and sends appropriate notifications.

    Returns:
        Notification summary
    """
    if not redis_client:
        return "[ERROR] Error: Cannot connect to notification system."

    print("[PHONE] [Notification Agent] Checking for patients needing position updates...")

    # Get recent position changes from Redis
    affected_patients = _get_recent_position_changes()

    if not affected_patients:
        return "[PHONE] No recent position changes detected - no notifications needed."

    notifications_sent = []

    for patient in affected_patients:
        notification = _create_position_update_notification(patient)

        # Store notification in Redis for tracking
        notification_key = f"notification:{patient.get('token_number')}:{datetime.utcnow().timestamp()}"
        redis_client.set(
            notification_key, json.dumps(notification), ex=3600
        )  # 1 hour expiry

        notifications_sent.append(notification)
        print(
            f"📤 [Notification] Sent to Token #{patient.get('token_number')}: {notification['message_type']}"
        )

    summary = f"""
[PHONE] PATIENT NOTIFICATIONS SENT
============================
Total Notifications: {len(notifications_sent)}

📤 NOTIFICATION DETAILS:
"""

    for notification in notifications_sent:
        summary += f"""
├─ Token #{notification['patient_token']}: {notification['patient_name']}
│  └─ {notification['message_type']} - {notification['summary']}"""

    summary += f"""

[OK] All notifications delivered successfully!
[STATS] Notification system performance: {len(notifications_sent)} messages processed
"""

    return summary.strip()


def send_appointment_ready_notification(patient_token: int) -> str:
    """
    Send notification when patient's appointment is ready.

    Args:
        patient_token: Patient's token number

    Returns:
        Notification result
    """
    if not redis_client:
        return "[ERROR] Error: Cannot connect to notification system."

    patient_data = _get_patient_data(patient_token)
    if not patient_data:
        return f"[ERROR] Patient with Token #{patient_token} not found."

    notification = {
        "patient_token": patient_token,
        "patient_name": patient_data.get("name", "Unknown"),
        "contact": patient_data.get("contact", "Unknown"),
        "message_type": "APPOINTMENT_READY",
        "title": "[CLINIC] Your Appointment is Ready!",
        "message": f"Hello {patient_data.get('name')}, please proceed to the consultation room. Your wait is over!",
        "priority": "HIGH",
        "timestamp": datetime.utcnow().isoformat(),
        "auto_generated": True,
    }

    # Store notification
    notification_key = (
        f"notification:{patient_token}:ready:{datetime.utcnow().timestamp()}"
    )
    redis_client.set(
        notification_key, json.dumps(notification), ex=1800
    )  # 30 min expiry

    return f"""
[CLINIC] APPOINTMENT READY NOTIFICATION
================================
Patient: {patient_data.get('name')} (Token #{patient_token})
Contact: {patient_data.get('contact')}
Message: {notification['message']}

[OK] High-priority notification sent successfully!
"""


def send_eta_update_notifications() -> str:
    """
    Send ETA updates to patients when timing changes significantly.
    Automatically detects patients with significant ETA changes.

    Returns:
        Notification summary
    """
    if not redis_client:
        return "[ERROR] Error: Cannot connect to notification system."

    print("[CLOCK] [Notification Agent] Checking for significant ETA changes...")

    # Get patients with ETA changes from Redis
    patients_with_eta_changes = _get_patients_with_eta_changes()

    if not patients_with_eta_changes:
        return "[CLOCK] No significant ETA changes detected - no notifications needed."

    significant_changes = []

    for patient in patients_with_eta_changes:
        eta_change_mins = patient.get("eta_change_mins", 0)

        # Only notify for significant changes (>10 minutes)
        if abs(eta_change_mins) >= 10:
            notification = _create_eta_update_notification(patient)
            significant_changes.append(notification)

            # Store notification
            notification_key = f"notification:{patient.get('token_number')}:eta:{datetime.utcnow().timestamp()}"
            redis_client.set(notification_key, json.dumps(notification), ex=3600)

    if not significant_changes:
        return "[CLOCK] ETA changes were minor (<10 min) - no notifications sent."

    summary = f"""
[CLOCK] ETA UPDATE NOTIFICATIONS
==========================
Significant Changes: {len(significant_changes)}

📤 NOTIFICATIONS SENT:
"""

    for notification in significant_changes:
        summary += f"""
├─ Token #{notification['patient_token']}: {notification['patient_name']}
│  └─ {notification['summary']}"""

    return summary.strip()


def get_notification_history(patient_token: int = 0) -> str:
    """
    Get notification history for a patient or all notifications.

    Args:
        patient_token: Specific patient token (0 for all notifications)

    Returns:
        Notification history
    """
    if not redis_client:
        return "[ERROR] Error: Cannot connect to notification system."

    try:
        if patient_token and patient_token > 0:
            pattern = f"notification:{patient_token}:*"
            title = f"NOTIFICATION HISTORY - Token #{patient_token}"
        else:
            pattern = "notification:*"
            title = "ALL NOTIFICATIONS HISTORY"

        keys = redis_client.keys(pattern)

        if not keys:
            return f"[PHONE] No notification history found."

        notifications = []
        for key in keys:
            try:
                notification_data = redis_client.get(key)
                if notification_data:
                    notification = json.loads(notification_data)
                    notifications.append(notification)
            except Exception:
                continue

        # Sort by timestamp
        notifications.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        history = f"""
[PHONE] {title}
{'=' * len(title)}
Total Notifications: {len(notifications)}

📤 RECENT NOTIFICATIONS:
"""

        for notification in notifications[:10]:  # Show last 10
            history += f"""
├─ {notification.get('timestamp', 'Unknown')[:16]}
│  └─ Token #{notification.get('patient_token')}: {notification.get('message_type')}
│     {notification.get('title')}"""

        return history.strip()

    except Exception as e:
        return f"[ERROR] Error retrieving notification history: {str(e)}"


def _get_recent_position_changes():
    """Get patients with recent position changes"""
    try:
        # Check for position changes in the last optimization
        changes_key = "recent_position_changes"
        changes_data = redis_client.get(changes_key)

        if changes_data:
            return json.loads(changes_data)
        return []
    except Exception:
        return []


def _get_patients_with_eta_changes():
    """Get patients with recent ETA changes"""
    try:
        # Check for ETA changes in the last calculation
        eta_changes_key = "recent_eta_changes"
        eta_data = redis_client.get(eta_changes_key)

        if eta_data:
            return json.loads(eta_data)
        return []
    except Exception:
        return []


def _create_position_update_notification(patient):
    """Create position update notification"""
    old_pos = patient.get("old_position", 0)
    new_pos = patient.get("new_position", 0)

    if new_pos < old_pos:
        message_type = "POSITION_IMPROVED"
        title = "[START] Good News - Your Position Improved!"
        message = f"Hello {patient.get('name')}, you've moved up in the queue from position #{old_pos} to #{new_pos}. Your wait time has decreased!"
    else:
        message_type = "POSITION_DELAYED"
        title = "[CLOCK] Queue Update - Slight Delay"
        message = f"Hello {patient.get('name')}, due to urgent cases, you've moved from position #{old_pos} to #{new_pos}. We appreciate your patience!"

    return {
        "patient_token": patient.get("token_number"),
        "patient_name": patient.get("name", "Unknown"),
        "contact": patient.get("contact", "Unknown"),
        "message_type": message_type,
        "title": title,
        "message": message,
        "old_position": old_pos,
        "new_position": new_pos,
        "summary": f"Position {old_pos}→{new_pos}",
        "priority": "NORMAL",
        "timestamp": datetime.utcnow().isoformat(),
        "auto_generated": True,
    }


def _create_eta_update_notification(patient):
    """Create ETA update notification"""
    eta_change = patient.get("eta_change_mins", 0)

    if eta_change < 0:
        message_type = "ETA_IMPROVED"
        title = "[FAST] Your Appointment is Earlier!"
        message = f"Great news {patient.get('name')}! Your appointment is now {abs(eta_change)} minutes earlier than expected."
    else:
        message_type = "ETA_DELAYED"
        title = "[CLOCK] Updated Timing"
        message = f"Hello {patient.get('name')}, your appointment is delayed by {eta_change} minutes due to queue optimization. Thank you for your patience!"

    return {
        "patient_token": patient.get("token_number"),
        "patient_name": patient.get("name", "Unknown"),
        "contact": patient.get("contact", "Unknown"),
        "message_type": message_type,
        "title": title,
        "message": message,
        "eta_change_mins": eta_change,
        "summary": f"ETA {'+' if eta_change > 0 else ''}{eta_change} min",
        "priority": "NORMAL" if abs(eta_change) < 20 else "HIGH",
        "timestamp": datetime.utcnow().isoformat(),
        "auto_generated": True,
    }


def _get_patient_data(patient_token: int):
    """Get patient data from priority queue manager"""
    try:
        if not pq_manager:
            return None
        
        # Check if patient exists in patient_map
        if patient_token in pq_manager.patient_map:
            patient_node = pq_manager.patient_map[patient_token]
            return {
                "token_number": patient_node.token_number,
                "name": patient_node.name,
                "contact_number": patient_node.contact_number,
                "symptoms": patient_node.symptoms,
                "symptoms_analysis": patient_node.symptoms_analysis,
                "travel_data": patient_node.travel_data,
            }
        return None
    except Exception:
        return None
