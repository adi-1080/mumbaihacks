import json
import redis
from datetime import datetime
from typing import Dict, List

# --- CORRECTED IMPORTS ---
from tools.symptom_analyzer import analyze_patient_symptoms
from tools.priority_queue_manager import get_priority_queue_manager

# --- END CORRECTIONS ---


class EmergencyHandler:
    def __init__(self, redis_client):
        self.redis_client = redis_client
        self.pq_manager = get_priority_queue_manager(redis_client)

    def handle_emergency_case(self, patient_data: Dict) -> Dict:
        """
        Handle emergency cases with immediate prioritization.

        Args:
            patient_data: Patient information dictionary

        Returns:
            Updated patient data with emergency handling
        """
        symptoms_analysis = analyze_patient_symptoms(patient_data["symptoms"])

        if symptoms_analysis["is_emergency"]:
            print(f"🚨 [Emergency] Detected emergency case: {patient_data['name']}")

            # Update patient data for emergency
            patient_data.update(
                {
                    "status": "emergency",
                    "urgency_score": symptoms_analysis["urgency_score"],
                    "emergency_flagged_at": datetime.utcnow().isoformat(),
                    "estimated_consultation_mins": symptoms_analysis[
                        "estimated_consultation_mins"
                    ],
                    "priority_level": "EMERGENCY",
                }
            )

            # Move to emergency queue
            self._move_to_emergency_queue(patient_data)

            return {
                "is_emergency": True,
                "action_taken": "moved_to_emergency_queue",
                "message": f"🚨 EMERGENCY CASE DETECTED for {patient_data['name']}. Moved to priority queue.",
                "estimated_wait_mins": 0,  # Emergency cases get immediate attention
            }

        return {"is_emergency": False}

    def _move_to_emergency_queue(self, patient_data: Dict):
        """Move patient to emergency priority queue using Priority Queue Manager"""
        if self.pq_manager:
            # Add to priority queue - will automatically go to emergency queue
            self.pq_manager.enqueue_patient(patient_data)
            print(f"[OK] [Emergency] Added {patient_data['name']} to emergency priority queue")


def handle_emergency_patient(patient_data: Dict, redis_client) -> Dict:
    """
    Standalone function to handle emergency patients.

    Args:
        patient_data: Patient information
        redis_client: Redis connection

    Returns:
        Emergency handling results
    """
    handler = EmergencyHandler(redis_client)
    return handler.handle_emergency_case(patient_data)
