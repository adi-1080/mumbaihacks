import os
import json
import redis
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

class StarvationTracker:
    """
    Tracks patients who have been moved down in the queue to prevent starvation.
    Ensures no patient waits too long due to constant queue reordering.
    """
    
    def __init__(self, redis_client):
        self.redis_client = redis_client
        self.starvation_key = "patient_starvation_tracker"
        self.max_moves_per_patient = 3  # Max times a patient can be moved down
        self.starvation_threshold_mins = 45  # After 45 min, patient gets priority boost
        
    def track_queue_move(self, patient_token: int, old_position: int, new_position: int, reason: str) -> Dict:
        """
        Track when a patient is moved in the queue.
        
        Args:
            patient_token: Patient's token number
            old_position: Previous queue position
            new_position: New queue position  
            reason: Reason for the move
            
        Returns:
            Tracking result with starvation data
        """
        if not self.redis_client:
            return {"error": "Redis not available"}
            
        print(f"[STATS] [Starvation Tracker] Tracking move for Token #{patient_token}: #{old_position} → #{new_position}")
        
        # Get current starvation data
        starvation_data = self._get_starvation_data()
        patient_key = str(patient_token)
        
        # Initialize patient tracking if not exists
        if patient_key not in starvation_data:
            starvation_data[patient_key] = {
                "token": patient_token,
                "first_booking_time": datetime.utcnow().isoformat(),
                "total_moves": 0,
                "moves_down": 0,
                "moves_up": 0,
                "move_history": [],
                "starvation_score": 0.0,
                "protection_active": False
            }
        
        # Record the move
        move_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "old_position": old_position,
            "new_position": new_position,
            "reason": reason,
            "move_type": "down" if new_position > old_position else "up"
        }
        
        starvation_data[patient_key]["move_history"].append(move_record)
        starvation_data[patient_key]["total_moves"] += 1
        
        if new_position > old_position:
            starvation_data[patient_key]["moves_down"] += 1
        else:
            starvation_data[patient_key]["moves_up"] += 1
            
        # Calculate starvation score
        starvation_data[patient_key] = self._update_starvation_score(starvation_data[patient_key])
        
        # Check if patient needs protection
        starvation_data[patient_key] = self._check_starvation_protection(starvation_data[patient_key])
        
        # Save updated data
        self._save_starvation_data(starvation_data)
        
        return {
            "success": True,
            "patient_token": patient_token,
            "starvation_score": starvation_data[patient_key]["starvation_score"],
            "protection_active": starvation_data[patient_key]["protection_active"],
            "total_moves": starvation_data[patient_key]["total_moves"],
            "moves_down": starvation_data[patient_key]["moves_down"]
        }
    
    def get_patient_starvation_status(self, patient_token: int) -> Dict:
        """
        Get starvation status for a specific patient.
        
        Args:
            patient_token: Patient's token number
            
        Returns:
            Patient's starvation status
        """
        starvation_data = self._get_starvation_data()
        patient_key = str(patient_token)
        
        if patient_key not in starvation_data:
            return {
                "found": False,
                "starvation_score": 0.0,
                "protection_active": False,
                "total_moves": 0
            }
        
        patient_data = starvation_data[patient_key]
        
        # Update starvation score based on current time
        patient_data = self._update_starvation_score(patient_data)
        
        return {
            "found": True,
            "token": patient_token,
            "starvation_score": patient_data["starvation_score"],
            "protection_active": patient_data["protection_active"],
            "total_moves": patient_data["total_moves"],
            "moves_down": patient_data["moves_down"],
            "moves_up": patient_data["moves_up"],
            "first_booking_time": patient_data["first_booking_time"],
            "waiting_time_mins": self._calculate_waiting_time(patient_data["first_booking_time"])
        }
    
    def get_all_protected_patients(self) -> List[int]:
        """
        Get list of patient tokens that are protected from being moved down.
        
        Returns:
            List of protected patient tokens
        """
        starvation_data = self._get_starvation_data()
        protected_patients = []
        
        for patient_key, patient_data in starvation_data.items():
            # Update starvation score
            patient_data = self._update_starvation_score(patient_data)
            patient_data = self._check_starvation_protection(patient_data)
            
            if patient_data["protection_active"]:
                protected_patients.append(patient_data["token"])
        
        # Save updated data
        self._save_starvation_data(starvation_data)
        
        return protected_patients
    
    def _get_starvation_data(self) -> Dict:
        """Get starvation data from Redis"""
        if not self.redis_client:
            return {}
            
        try:
            data = self.redis_client.get(self.starvation_key)
            return json.loads(data) if data else {}
        except Exception as e:
            print(f"[ERROR] [Starvation Tracker] Error getting data: {e}")
            return {}
    
    def _save_starvation_data(self, data: Dict):
        """Save starvation data to Redis"""
        if not self.redis_client:
            return
            
        try:
            self.redis_client.set(self.starvation_key, json.dumps(data))
        except Exception as e:
            print(f"[ERROR] [Starvation Tracker] Error saving data: {e}")
    
    def _update_starvation_score(self, patient_data: Dict) -> Dict:
        """
        Calculate starvation score based on:
        1. Number of times moved down
        2. Total waiting time
        3. Time since last move down
        """
        # Base score from moves down
        moves_down_score = patient_data["moves_down"] * 10
        
        # Waiting time score
        waiting_mins = self._calculate_waiting_time(patient_data["first_booking_time"])
        waiting_score = max(0, (waiting_mins - 20) * 0.5)  # After 20 min, start adding score
        
        # Time since last move penalty
        last_move_penalty = 0
        if patient_data["move_history"]:
            last_move = patient_data["move_history"][-1]
            if last_move["move_type"] == "down":
                mins_since_move = self._calculate_waiting_time(last_move["timestamp"])
                if mins_since_move > 15:  # If moved down more than 15 min ago
                    last_move_penalty = mins_since_move * 0.3
        
        # Total starvation score
        total_score = moves_down_score + waiting_score + last_move_penalty
        patient_data["starvation_score"] = round(total_score, 2)
        
        return patient_data
    
    def _check_starvation_protection(self, patient_data: Dict) -> Dict:
        """Check if patient needs starvation protection"""
        waiting_mins = self._calculate_waiting_time(patient_data["first_booking_time"])
        
        # Activate protection if:
        # 1. Moved down too many times, OR
        # 2. Waiting too long, OR  
        # 3. High starvation score
        protection_needed = (
            patient_data["moves_down"] >= self.max_moves_per_patient or
            waiting_mins >= self.starvation_threshold_mins or
            patient_data["starvation_score"] >= 25.0
        )
        
        patient_data["protection_active"] = protection_needed
        
        if protection_needed:
            print(f"🛡️ [Starvation Protection] Activated for Token #{patient_data['token']}")
        
        return patient_data
    
    def _calculate_waiting_time(self, start_time_str: str) -> float:
        """Calculate waiting time in minutes from start time"""
        try:
            start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
            current_time = datetime.utcnow().replace(tzinfo=start_time.tzinfo)
            return (current_time - start_time).total_seconds() / 60
        except Exception:
            return 0.0

# Global functions for tool integration
def track_patient_queue_move(patient_token: int, old_position: int, new_position: int, reason: str, redis_client) -> Dict:
    """
    Track a patient's queue position change.
    
    Args:
        patient_token: Patient's token number
        old_position: Previous position in queue
        new_position: New position in queue
        reason: Reason for the move
        redis_client: Redis connection
        
    Returns:
        Tracking result
    """
    tracker = StarvationTracker(redis_client)
    return tracker.track_queue_move(patient_token, old_position, new_position, reason)

def get_protected_patients(redis_client) -> List[int]:
    """
    Get list of patients protected from being moved down.
    
    Args:
        redis_client: Redis connection
        
    Returns:
        List of protected patient token numbers
    """
    tracker = StarvationTracker(redis_client)
    return tracker.get_all_protected_patients()

def get_starvation_status(patient_token: int, redis_client) -> Dict:
    """
    Get starvation status for a patient.
    
    Args:
        patient_token: Patient's token number
        redis_client: Redis connection
        
    Returns:
        Patient's starvation status
    """
    tracker = StarvationTracker(redis_client)
    return tracker.get_patient_starvation_status(patient_token)