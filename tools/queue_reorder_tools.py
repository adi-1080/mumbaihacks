import os
import json
import redis
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from tools.starvation_tracker import track_patient_queue_move, get_protected_patients
from tools.priority_queue_manager import get_priority_queue_manager

class QueueReorderManager:
    """
    Advanced queue reordering system that identifies vacant slots and optimizes patient flow.
    """
    
    def __init__(self, redis_client):
        self.redis_client = redis_client
        self.pq_manager = get_priority_queue_manager(redis_client)
        self.vacant_slot_threshold_mins = 15  # If patient arrives 15+ min after their slot, it's vacant
        self.efficiency_boost_threshold = 10   # Boost score if consultation < 10 min
        
    def analyze_queue_for_reordering(self) -> Dict:
        """
        Analyze the current queue to identify optimization opportunities.
        
        Returns:
            Analysis results with reordering recommendations
        """
        if not self.redis_client:
            return {"error": "Redis not available"}
            
        print("[BRAIN] [Queue Brain] Starting advanced queue analysis...")
        
        # Get all patients from queue
        patients = self._get_current_queue()
        if len(patients) < 2:
            return {"message": "Queue too small for optimization", "patients": len(patients)}
        
        # Get protected patients (cannot be moved down)
        protected_patients = get_protected_patients(self.redis_client)
        
        # Analyze each patient's data
        enriched_patients = []
        for i, patient in enumerate(patients):
            enriched = self._enrich_patient_for_analysis(patient, i + 1, protected_patients)
            enriched_patients.append(enriched)
        
        # Find vacant slots and optimization opportunities
        optimization_plan = self._create_optimization_plan(enriched_patients)
        
        return {
            "status": "analysis_complete",
            "total_patients": len(patients),
            "protected_patients": len(protected_patients),
            "vacant_slots_found": len(optimization_plan.get("vacant_slots", [])),
            "optimization_opportunities": len(optimization_plan.get("moves", [])),
            "optimization_plan": optimization_plan,
            "efficiency_gain_mins": optimization_plan.get("total_time_saved", 0)
        }
    
    def execute_queue_reorder(self, optimization_plan: Dict) -> Dict:
        """
        Execute the queue reordering based on optimization plan.
        
        Args:
            optimization_plan: Plan from analyze_queue_for_reordering
            
        Returns:
            Reordering execution results
        """
        if not self.redis_client:
            return {"error": "Redis not available"}
            
        if not optimization_plan.get("moves"):
            return {"message": "No optimization moves to execute"}
        
        print(f"[CYCLE] [Queue Brain] Executing {len(optimization_plan['moves'])} optimization moves...")
        
        # Get current queue
        current_patients = self._get_current_queue()
        
        # Create new queue order
        new_queue_order = self._apply_optimization_moves(current_patients, optimization_plan["moves"])
        
        # Update the queue in Redis
        update_result = self._update_queue_order(new_queue_order)
        
        # Track all moves for starvation prevention
        move_tracking_results = []
        for move in optimization_plan["moves"]:
            tracking_result = track_patient_queue_move(
                patient_token=move["patient_token"],
                old_position=move["old_position"], 
                new_position=move["new_position"],
                reason=move["reason"],
                redis_client=self.redis_client
            )
            move_tracking_results.append(tracking_result)
        
        return {
            "status": "reorder_complete",
            "moves_executed": len(optimization_plan["moves"]),
            "queue_updated": update_result["success"],
            "time_saved_mins": optimization_plan.get("total_time_saved", 0),
            "move_tracking": move_tracking_results,
            "new_queue_length": len(new_queue_order),
            "reorder_summary": self._generate_reorder_summary(optimization_plan["moves"])
        }
    
    def _get_current_queue(self) -> List[Dict]:
        """Get current patient queue from priority queue manager"""
        if not self.pq_manager:
            return []
        
        queue_snapshot = self.pq_manager.get_queue_snapshot()
        return queue_snapshot.get("patients", [])
    
    def _enrich_patient_for_analysis(self, patient: Dict, current_position: int, protected_patients: List[int]) -> Dict:
        """
        Enrich patient data with analysis metrics.
        
        Args:
            patient: Patient data
            current_position: Current queue position
            protected_patients: List of protected patient tokens
            
        Returns:
            Enriched patient data
        """
        # Basic data
        enriched = patient.copy()
        enriched["current_position"] = current_position
        enriched["is_protected"] = patient["token_number"] in protected_patients
        
        # Get travel and symptom data
        travel_data = patient.get("travel_data", {}).get("travel_options", {}).get("driving", {})
        symptoms_data = patient.get("symptoms_analysis", {})
        
        # Calculate key metrics
        travel_time_mins = travel_data.get("traffic_duration_mins", 20)
        consultation_mins = symptoms_data.get("estimated_consultation_mins", 15)
        urgency_score = symptoms_data.get("urgency_score", 5)
        
        # Calculate arrival time from now
        current_time = datetime.utcnow()
        estimated_arrival = current_time + timedelta(minutes=travel_time_mins)
        
        # Calculate expected slot time (based on current position)
        estimated_wait_for_position = (current_position - 1) * 12  # Avg 12 min per patient
        expected_slot_time = current_time + timedelta(minutes=estimated_wait_for_position)
        
        # Calculate slot vacancy (how late patient will be for their slot)
        slot_vacancy_mins = max(0, (estimated_arrival - expected_slot_time).total_seconds() / 60)
        
        # Calculate priority score for reordering
        priority_score = self._calculate_reordering_priority(
            urgency_score, consultation_mins, slot_vacancy_mins, 
            enriched["is_protected"], travel_time_mins
        )
        
        enriched.update({
            "travel_time_mins": travel_time_mins,
            "consultation_mins": consultation_mins,
            "urgency_score": urgency_score,
            "estimated_arrival": estimated_arrival.isoformat(),
            "expected_slot_time": expected_slot_time.isoformat(),
            "slot_vacancy_mins": round(slot_vacancy_mins, 1),
            "priority_score": priority_score,
            "is_vacant_slot": slot_vacancy_mins >= self.vacant_slot_threshold_mins
        })
        
        return enriched
    
    def _create_urgency_based_moves(self, enriched_patients: List[Dict]) -> List[Dict]:
        """
        Create moves based purely on medical urgency prioritization.
        High-urgency patients should be seen before low-urgency ones.
        
        Returns:
            List of urgency-based optimization moves
        """
        moves = []
        
        # Sort by urgency (high to low) to see ideal order
        ideal_order = sorted(enriched_patients, key=lambda x: x["urgency_score"], reverse=True)
        
        # Find patients out of urgency order
        for ideal_pos, ideal_patient in enumerate(ideal_order, 1):
            current_pos = ideal_patient["current_position"]
            
            # Skip if already in correct position or protected
            if current_pos == ideal_pos or ideal_patient["is_protected"]:
                continue
            
            # Only move if urgency difference is significant (3+ points)
            urgency_diff = self._calculate_urgency_advantage(ideal_patient, enriched_patients, current_pos, ideal_pos)
            
            if urgency_diff >= 3:  # Significant urgency advantage
                moves.append({
                    "patient_token": ideal_patient["token_number"],
                    "patient_name": ideal_patient["name"],
                    "old_position": current_pos,
                    "new_position": ideal_pos,
                    "reason": f"High urgency ({ideal_patient['urgency_score']}/10) - medical priority",
                    "improvement_mins": urgency_diff * 2,  # Estimate time saved
                    "urgency_based": True
                })
        
        return moves
    
    def _calculate_urgency_advantage(self, patient: Dict, all_patients: List[Dict], 
                                    current_pos: int, ideal_pos: int) -> int:
        """
        Calculate urgency advantage for moving a patient forward.
        
        Returns:
            Urgency difference score
        """
        # Calculate average urgency of patients between ideal and current position
        patients_in_range = [p for p in all_patients 
                            if ideal_pos <= p["current_position"] < current_pos]
        
        if not patients_in_range:
            return 0
        
        avg_urgency_in_range = sum(p["urgency_score"] for p in patients_in_range) / len(patients_in_range)
        urgency_advantage = patient["urgency_score"] - avg_urgency_in_range
        
        return max(0, int(urgency_advantage))
    
    def _calculate_reordering_priority(self, urgency: int, consultation_mins: int, 
                                     slot_vacancy_mins: float, is_protected: bool, 
                                     travel_time_mins: int) -> float:
        """
        Calculate priority score for queue reordering.
        Higher score = higher priority = should move up in queue
        """
        score = 0.0
        
        # Urgency factor (0-10 scale, weight: 40%)
        score += urgency * 4.0
        
        # Efficiency factor (weight: 25%)
        if consultation_mins <= self.efficiency_boost_threshold:
            score += 5.0  # Quick consultations get priority
        elif consultation_mins >= 25:
            score -= 2.0  # Long consultations get slight penalty
            
        # Availability factor (weight: 20%)
        if travel_time_mins <= 10:
            score += 3.0  # Close patients get bonus for availability
        elif travel_time_mins <= 15:
            score += 1.5
            
        # Slot utilization factor (weight: 15%)
        if slot_vacancy_mins < 5:
            score += 2.0  # Good timing gets bonus
        elif slot_vacancy_mins > 20:
            score -= 3.0  # Very late arrivals get penalty
            
        # Protection factor
        if is_protected:
            score += 10.0  # Protected patients get significant boost
            
        return round(score, 2)
    
    def _create_optimization_plan(self, enriched_patients: List[Dict]) -> Dict:
        """
        Create optimization plan based on enriched patient data.
        
        Args:
            enriched_patients: List of enriched patient data
            
        Returns:
            Optimization plan with moves and expected savings
        """
        vacant_slots = []
        optimization_moves = []
        total_time_saved = 0
        
        # PRIORITY 1: URGENCY-BASED REORDERING (Medical Priority)
        # Check if queue has significant urgency imbalance
        urgency_moves = self._create_urgency_based_moves(enriched_patients)
        optimization_moves.extend(urgency_moves)
        
        # PRIORITY 2: Find vacant slots (patients who will arrive much later than their slot)
        for patient in enriched_patients:
            if patient["is_vacant_slot"] and not patient["is_protected"]:
                vacant_slots.append({
                    "position": patient["current_position"],
                    "patient_token": patient["token_number"],
                    "vacancy_mins": patient["slot_vacancy_mins"],
                    "patient_name": patient["name"]
                })
        
        # Find patients who could fill vacant slots more efficiently
        available_patients = [p for p in enriched_patients if not p["is_protected"]]
        available_patients.sort(key=lambda x: x["priority_score"], reverse=True)
        
        # Create optimization moves
        for vacant_slot in vacant_slots:
            # Find best patient to move into this vacant slot
            best_candidate = None
            best_improvement = 0
            
            for candidate in available_patients:
                # Skip if candidate is already in a better position
                if candidate["current_position"] <= vacant_slot["position"]:
                    continue
                    
                # Skip if candidate would create an even worse vacancy
                if candidate["slot_vacancy_mins"] > vacant_slot["vacancy_mins"]:
                    continue
                
                # Calculate improvement score
                improvement = self._calculate_move_improvement(candidate, vacant_slot)
                
                if improvement > best_improvement and improvement > 5:  # Minimum threshold
                    best_candidate = candidate
                    best_improvement = improvement
            
            # Create move if beneficial
            if best_candidate:
                move = {
                    "patient_token": best_candidate["token_number"],
                    "patient_name": best_candidate["name"],
                    "old_position": best_candidate["current_position"],
                    "new_position": vacant_slot["position"],
                    "reason": f"Filling vacant slot - {best_improvement:.1f} min improvement",
                    "improvement_mins": best_improvement,
                    "vacant_slot_filled": vacant_slot["patient_token"]
                }
                optimization_moves.append(move)
                total_time_saved += best_improvement
                
                # Remove candidate from available list
                available_patients.remove(best_candidate)
        
        return {
            "vacant_slots": vacant_slots,
            "moves": optimization_moves,
            "total_time_saved": round(total_time_saved, 1),
            "optimization_summary": f"{len(optimization_moves)} moves planned, {total_time_saved:.1f} min saved"
        }
    
    def _calculate_move_improvement(self, candidate: Dict, vacant_slot: Dict) -> float:
        """
        Calculate improvement score for moving a candidate to fill a vacant slot.
        
        Returns:
            Improvement score in minutes (higher is better)
        """
        # Time saved by filling the vacant slot
        slot_time_saved = vacant_slot["vacancy_mins"] - candidate["slot_vacancy_mins"]
        
        # Efficiency bonus for quick consultations
        efficiency_bonus = max(0, (15 - candidate["consultation_mins"]) * 0.5)
        
        # Urgency bonus
        urgency_bonus = candidate["urgency_score"] * 0.5
        
        total_improvement = slot_time_saved + efficiency_bonus + urgency_bonus
        return max(0, total_improvement)
    
    def _apply_optimization_moves(self, current_patients: List[Dict], moves: List[Dict]) -> List[Dict]:
        """
        Apply optimization moves to create new queue order.
        
        Args:
            current_patients: Current queue order
            moves: List of moves to apply
            
        Returns:
            New queue order
        """
        new_queue = current_patients.copy()
        
        # Sort moves by new position to avoid conflicts
        sorted_moves = sorted(moves, key=lambda x: x["new_position"])
        
        for move in sorted_moves:
            # Find patient to move
            patient_to_move = None
            old_index = None
            
            for i, patient in enumerate(new_queue):
                if patient["token_number"] == move["patient_token"]:
                    patient_to_move = patient
                    old_index = i
                    break
            
            if patient_to_move and old_index is not None:
                # Remove from old position
                new_queue.pop(old_index)
                
                # Insert at new position (adjust for 1-based position)
                new_position_index = move["new_position"] - 1
                new_queue.insert(new_position_index, patient_to_move)
        
        return new_queue
    
    def _update_queue_order(self, new_queue_order: List[Dict]) -> Dict:
        """
        Update the Redis queue with new order.
        
        Args:
            new_queue_order: New queue order
            
        Returns:
            Update result
        """
        try:
            # Clear current queue
            self.redis_client.delete("patient_queue")
            
            # Add patients in new order
            for patient in new_queue_order:
                self.redis_client.rpush("patient_queue", json.dumps(patient))
            
            print(f"[OK] [Queue Brain] Updated queue order with {len(new_queue_order)} patients")
            
            return {
                "success": True,
                "new_queue_length": len(new_queue_order)
            }
            
        except Exception as e:
            print(f"[ERROR] [Queue Brain] Error updating queue: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_reorder_summary(self, moves: List[Dict]) -> str:
        """Generate human-readable summary of reordering moves"""
        if not moves:
            return "No queue changes needed"
        
        summary_lines = [f"Queue reordered with {len(moves)} moves:"]
        
        for move in moves:
            summary_lines.append(
                f"• {move['patient_name']} moved from #{move['old_position']} → #{move['new_position']} "
                f"({move['improvement_mins']:.1f}min saved)"
            )
        
        return "\n".join(summary_lines)

# Global functions for tool integration
def analyze_queue_for_optimization(redis_client) -> Dict:
    """
    Analyze current queue for optimization opportunities.
    
    Args:
        redis_client: Redis connection
        
    Returns:
        Queue analysis results
    """
    manager = QueueReorderManager(redis_client)
    return manager.analyze_queue_for_reordering()

def execute_intelligent_queue_reorder(redis_client) -> Dict:
    """
    Execute intelligent queue reordering.
    
    Args:
        redis_client: Redis connection
        
    Returns:
        Reordering execution results
    """
    manager = QueueReorderManager(redis_client)
    
    # First analyze
    analysis = manager.analyze_queue_for_reordering()
    
    if analysis.get("optimization_plan", {}).get("moves"):
        # Execute reordering
        return manager.execute_queue_reorder(analysis["optimization_plan"])
    else:
        return {
            "status": "no_optimization_needed",
            "message": "Queue is already optimized",
            "analysis": analysis
        }

def update_queue_order_manually(new_patient_order: List[Dict], redis_client) -> Dict:
    """
    Manually update queue order.
    
    Args:
        new_patient_order: New order of patients
        redis_client: Redis connection
        
    Returns:
        Update result
    """
    manager = QueueReorderManager(redis_client)
    return manager._update_queue_order(new_patient_order)