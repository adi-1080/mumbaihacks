"""
Advanced Priority Queue Management System - MongoDB Version
Uses Min-Heap for dynamic patient scheduling with multiple weighted factors.

Data Structures:
- Min-Heap Priority Queue: O(log n) insertion/removal
- MongoDB: Persistent patient data and queue state
- Balanced aging system: Starvation prevention

Algorithms:
- Dynamic Priority Scheduling
- Aging Algorithm (prevents starvation)
- Real-time priority recalculation

MIGRATION: Now uses MongoDB instead of Redis for all persistence
"""

import heapq
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import IntEnum

# Import MongoDB utilities instead of Redis
from tools.mongodb_utils import PatientModel, QueueStateModel, get_mongodb_manager


class EmergencyLevel(IntEnum):
    """Emergency priority levels"""
    NORMAL = 0
    PRIORITY = 1
    CRITICAL = 2


@dataclass(order=True)
class PatientNode:
    """
    Patient node for priority queue with computed priority score.
    Lower priority_score = higher priority (served first).
    """
    priority_score: float
    token_number: int = field(compare=False)
    name: str = field(compare=False)
    contact_number: str = field(compare=False)
    
    # Core attributes for priority calculation
    emergency_level: int = field(compare=False, default=0)
    travel_eta_mins: float = field(compare=False, default=20.0)
    predicted_consult_mins: int = field(compare=False, default=15)
    waiting_time_mins: float = field(compare=False, default=0.0)
    arrival_probability: float = field(compare=False, default=1.0)
    
    # Additional data
    symptoms: str = field(compare=False, default="")
    symptoms_analysis: Dict = field(compare=False, default_factory=dict)
    location: str = field(compare=False, default="")
    travel_data: Dict = field(compare=False, default_factory=dict)
    booking_time: str = field(compare=False, default="")
    expected_arrival: Optional[str] = field(compare=False, default=None)
    actual_arrival: Optional[str] = field(compare=False, default=None)
    
    # Metadata
    last_priority_update: str = field(compare=False, default="")
    position_history: List[int] = field(compare=False, default_factory=list)


class PriorityWeights:
    """
    Configurable weights for priority calculation.
    Fine-tune these based on clinic's priorities.
    """
    EMERGENCY = 5.0          # Highest weight
    TRAVEL_ETA = 2.0         # Favor patients arriving soon
    CONSULTATION_TIME = 1.0  # Slightly favor quick consultations
    WAITING_TIME = -3.0      # Negative = reduces priority score (aging boost)
    ARRIVAL_PROB = 1.5       # Favor patients likely to arrive


class PriorityQueueManager:
    """
    Advanced priority queue manager using min-heap and MongoDB.
    
    Features:
    - O(log n) insertion and removal
    - MongoDB persistence for all patient data
    - Dynamic priority recalculation
    - Starvation prevention through aging
    - Emergency patient handling
    
    MIGRATION: Uses MongoDB instead of Redis for persistence
    """
    
    def __init__(self, mongodb_manager=None):
        # Main queue (min-heap)
        self.main_queue: List[PatientNode] = []
        
        # Emergency queue (max-heap using negative scores)
        self.emergency_queue: List[PatientNode] = []
        
        # Fast lookup: token_number -> PatientNode
        self.patient_map: Dict[int, PatientNode] = {}
        
        # Waiting time tracker for aging
        self.wait_tracker: Dict[int, float] = {}
        
        # Configuration
        self.weights = PriorityWeights()
        self.aging_rate_mins = 5  # Boost priority every 5 minutes
        self.starvation_threshold_mins = 30  # Alert if waiting >30 mins
        
        # MongoDB for persistence
        self.mongodb_manager = mongodb_manager or get_mongodb_manager()
        self.patient_model = PatientModel()
        self.queue_state = QueueStateModel()
        
        # Statistics
        self.total_enqueued = 0
        self.total_dequeued = 0
        self.reorder_count = 0
        
        # Load existing patients from MongoDB
        self._load_from_mongodb()
        
        print("[OK] Priority Queue Manager initialized (MongoDB)")
        print(f"   Weights: Emergency={self.weights.EMERGENCY}, "
              f"Travel={self.weights.TRAVEL_ETA}, "
              f"Waiting={self.weights.WAITING_TIME}")
    
    def calculate_priority_score(self, patient: PatientNode) -> float:
        """
        Calculate dynamic priority score using weighted factors.
        Lower score = higher priority (served first).
        
        Formula:
        PriorityScore = 
            w1 * emergency_level         (lower is better)
          + w2 * travel_eta              (lower ETA = earlier service)
          + w3 * consultation_time       (quick patients slightly favored)
          + w4 * waiting_time            (negative = aging boost)
          + w5 * arrival_probability     (likely arrivals favored)
        """
        score = (
            self.weights.EMERGENCY * patient.emergency_level +
            self.weights.TRAVEL_ETA * patient.travel_eta_mins +
            self.weights.CONSULTATION_TIME * patient.predicted_consult_mins +
            self.weights.WAITING_TIME * patient.waiting_time_mins +
            self.weights.ARRIVAL_PROB * (1.0 - patient.arrival_probability)
        )
        
        return round(score, 2)
    
    def enqueue_patient(self, patient_data: Dict) -> PatientNode:
        """
        Add patient to priority queue and MongoDB.
        
        Args:
            patient_data: Patient information dict
            
        Returns:
            PatientNode inserted into queue
        """
        # Create patient node
        symptoms_analysis = patient_data.get("symptoms_analysis", {})
        travel_data = patient_data.get("travel_data", {})
        
        # Determine emergency level from urgency score
        urgency = symptoms_analysis.get("urgency_score", 5)
        if urgency >= 8:
            emergency_level = EmergencyLevel.CRITICAL
            emergency_level_str = "CRITICAL"
        elif urgency >= 6:
            emergency_level = EmergencyLevel.PRIORITY
            emergency_level_str = "PRIORITY"
        else:
            emergency_level = EmergencyLevel.NORMAL
            emergency_level_str = "NORMAL"
        
        # Extract travel ETA
        travel_eta = travel_data.get("travel_options", {}).get("driving", {}).get(
            "traffic_duration_mins", 20
        )
        
        patient = PatientNode(
            priority_score=0.0,  # Will be calculated
            token_number=patient_data["token_number"],
            name=patient_data["name"],
            contact_number=patient_data["contact_number"],
            emergency_level=emergency_level,
            travel_eta_mins=travel_eta,
            predicted_consult_mins=symptoms_analysis.get("estimated_consultation_mins", 15),
            waiting_time_mins=0.0,
            symptoms=patient_data.get("symptoms", ""),
            symptoms_analysis=symptoms_analysis,
            location=patient_data.get("location", ""),
            travel_data=travel_data,
            booking_time=patient_data.get("booking_time", datetime.utcnow().isoformat()),
        )
        
        # Calculate priority score
        patient.priority_score = self.calculate_priority_score(patient)
        patient.last_priority_update = datetime.utcnow().isoformat()
        
        # Persist to MongoDB
        mongo_patient_data = {
            "tokenNumber": patient.token_number,
            "name": patient.name,
            "contactNumber": patient.contact_number,
            "symptoms": patient.symptoms,
            "symptomsAnalysis": symptoms_analysis,
            "location": patient.location,
            "travelData": travel_data,
            "priorityScore": patient.priority_score,
            "emergencyLevel": emergency_level_str,
            "travelEtaMins": travel_eta,
            "predictedConsultMins": patient.predicted_consult_mins,
            "waitingTimeMins": 0.0,
            "arrivalProbability": patient.arrival_probability,
            "bookingTime": datetime.utcnow(),
            "lastPriorityUpdate": datetime.utcnow(),
            "status": "WAITING",
            "isActive": True,
        }
        
        self.patient_model.create(mongo_patient_data)
        
        # Record booking in queue state
        self.queue_state.record_booking(is_emergency=(emergency_level != EmergencyLevel.NORMAL))
        
        # Add to appropriate queue
        if patient.emergency_level == EmergencyLevel.CRITICAL:
            # Emergency queue (max-heap via negative scores)
            emergency_node = PatientNode(
                priority_score=-patient.priority_score,  # Negative for max-heap
                token_number=patient.token_number,
                name=patient.name,
                contact_number=patient.contact_number,
                emergency_level=patient.emergency_level,
                travel_eta_mins=patient.travel_eta_mins,
                predicted_consult_mins=patient.predicted_consult_mins,
                symptoms=patient.symptoms,
                symptoms_analysis=patient.symptoms_analysis,
            )
            heapq.heappush(self.emergency_queue, emergency_node)
            print(f"🚨 [Emergency Queue] Added Token #{patient.token_number} (Critical)")
        else:
            # Main queue (min-heap)
            heapq.heappush(self.main_queue, patient)
            print(f"[OK] [Main Queue] Added Token #{patient.token_number} (Priority: {patient.priority_score})")
        
        # Add to hash map for O(1) lookups
        self.patient_map[patient.token_number] = patient
        self.wait_tracker[patient.token_number] = 0.0
        
        self.total_enqueued += 1
        
        return patient
    
    def dequeue_next_patient(self) -> Optional[PatientNode]:
        """
        Remove and return highest priority patient.
        Emergency patients are always served first.
        Updates MongoDB status to IN_CONSULTATION.
        
        Returns:
            Next patient to be served, or None if queue empty
        """
        # Check emergency queue first
        if self.emergency_queue:
            patient = heapq.heappop(self.emergency_queue)
            patient.priority_score = -patient.priority_score  # Restore original score
            print(f"🚨 [Dequeue] Emergency patient: Token #{patient.token_number}")
        elif self.main_queue:
            patient = heapq.heappop(self.main_queue)
            print(f"[OK] [Dequeue] Main queue patient: Token #{patient.token_number}")
        else:
            return None
        
        # Update MongoDB status to IN_CONSULTATION
        self.patient_model.start_consultation(patient.token_number)
        
        # Remove from tracking
        if patient.token_number in self.patient_map:
            del self.patient_map[patient.token_number]
        if patient.token_number in self.wait_tracker:
            del self.wait_tracker[patient.token_number]
        
        self.total_dequeued += 1
        
        return patient
    
    def peek(self) -> Optional[PatientNode]:
        """
        Get the next patient without removing them from the queue.
        Emergency patients are checked first.
        
        Returns:
            Next patient to be served, or None if queue empty
        """
        # Check emergency queue first
        if self.emergency_queue:
            patient = self.emergency_queue[0]
            # Return a copy with restored positive score
            peek_patient = PatientNode(
                priority_score=-patient.priority_score,
                token_number=patient.token_number,
                name=patient.name,
                contact_number=patient.contact_number,
                emergency_level=patient.emergency_level,
                travel_eta_mins=patient.travel_eta_mins,
                predicted_consult_mins=patient.predicted_consult_mins,
                symptoms=patient.symptoms,
                symptoms_analysis=patient.symptoms_analysis,
            )
            return peek_patient
        elif self.main_queue:
            return self.main_queue[0]
        else:
            return None
    
    def remove_patient(self, token_number: int) -> bool:
        """
        Remove a specific patient from the queue by token number.
        Marks as CANCELLED in MongoDB.
        
        Args:
            token_number: Token number of patient to remove
            
        Returns:
            True if patient was found and removed, False otherwise
        """
        if token_number not in self.patient_map:
            print(f"[WARNING] Patient token #{token_number} not found in queue")
            return False
        
        patient = self.patient_map[token_number]
        
        # Mark as cancelled in MongoDB
        self.patient_model.cancel_patient(token_number)
        self.queue_state.record_cancellation()
        
        # Remove from appropriate queue
        if patient.emergency_level == EmergencyLevel.CRITICAL:
            # Remove from emergency queue
            self.emergency_queue = [p for p in self.emergency_queue if p.token_number != token_number]
            heapq.heapify(self.emergency_queue)
            print(f"🚨 [Remove] Removed Token #{token_number} from emergency queue")
        else:
            # Remove from main queue
            self.main_queue = [p for p in self.main_queue if p.token_number != token_number]
            heapq.heapify(self.main_queue)
            print(f"[OK] [Remove] Removed Token #{token_number} from main queue")
        
        # Remove from tracking
        del self.patient_map[token_number]
        if token_number in self.wait_tracker:
            del self.wait_tracker[token_number]
        
        self.total_dequeued += 1
        
        return True
    
    def update_patient_attributes(self, token_number: int, updates: Dict) -> bool:
        """
        Update patient attributes and recalculate priority.
        Triggers automatic reordering and MongoDB update.
        
        Args:
            token_number: Patient token
            updates: Dict of attributes to update
            
        Returns:
            True if updated successfully
        """
        if token_number not in self.patient_map:
            print(f"[WARNING] Patient token #{token_number} not found in queue")
            return False
        
        patient = self.patient_map[token_number]
        
        # Prepare MongoDB update
        mongo_updates = {}
        
        # Update attributes
        if "travel_eta_mins" in updates:
            patient.travel_eta_mins = updates["travel_eta_mins"]
            mongo_updates["travelEtaMins"] = updates["travel_eta_mins"]
        if "actual_arrival" in updates:
            patient.actual_arrival = updates["actual_arrival"]
            mongo_updates["actualArrival"] = updates["actual_arrival"]
        if "arrival_probability" in updates:
            patient.arrival_probability = updates["arrival_probability"]
            mongo_updates["arrivalProbability"] = updates["arrival_probability"]
        
        # Recalculate priority
        old_score = patient.priority_score
        patient.priority_score = self.calculate_priority_score(patient)
        patient.last_priority_update = datetime.utcnow().isoformat()
        
        mongo_updates["priorityScore"] = patient.priority_score
        mongo_updates["lastPriorityUpdate"] = datetime.utcnow()
        
        # Update MongoDB
        self.patient_model.update_patient(token_number, mongo_updates)
        
        print(f"[CYCLE] [Update] Token #{token_number}: Priority {old_score} → {patient.priority_score}")
        
        # Reheapify (O(n) but necessary for correctness)
        self._reheapify_queue()
        
        return True
    
    def apply_aging(self, elapsed_mins: float = 1.0):
        """
        Apply aging algorithm to prevent starvation.
        Automatically boosts priority of waiting patients.
        
        Args:
            elapsed_mins: Time elapsed since last aging cycle
        """
        aging_boosts = 0
        
        for token, patient in self.patient_map.items():
            # Increment waiting time
            self.wait_tracker[token] += elapsed_mins
            patient.waiting_time_mins = self.wait_tracker[token]
            
            # Recalculate priority (aging reduces score = higher priority)
            old_score = patient.priority_score
            patient.priority_score = self.calculate_priority_score(patient)
            
            if patient.priority_score < old_score:
                aging_boosts += 1
                
                # Alert if approaching starvation
                if patient.waiting_time_mins > self.starvation_threshold_mins:
                    print(f"[WARNING] [Starvation Alert] Token #{token} waiting {patient.waiting_time_mins:.0f} mins")
        
        if aging_boosts > 0:
            print(f"[CLOCK] [Aging] Boosted {aging_boosts} patients' priority")
            self._reheapify_queue()
    
    def get_queue_snapshot(self) -> Dict:
        """
        Get current queue state without modifying it.
        
        Returns:
            Dict with queue statistics and patient list
        """
        # Merge and sort all patients by priority
        all_patients = []
        
        # Emergency patients (convert negative scores back)
        for p in self.emergency_queue:
            patient_dict = {
                "token_number": p.token_number,
                "name": p.name,
                "priority_score": -p.priority_score,  # Restore original
                "emergency_level": "CRITICAL",
                "waiting_time_mins": self.wait_tracker.get(p.token_number, 0),
                "travel_eta_mins": p.travel_eta_mins,
                "symptoms": p.symptoms,
            }
            all_patients.append(patient_dict)
        
        # Main queue patients
        for p in self.main_queue:
            patient_dict = {
                "token_number": p.token_number,
                "name": p.name,
                "priority_score": p.priority_score,
                "emergency_level": ["NORMAL", "PRIORITY", "CRITICAL"][p.emergency_level],
                "waiting_time_mins": self.wait_tracker.get(p.token_number, 0),
                "travel_eta_mins": p.travel_eta_mins,
                "symptoms": p.symptoms,
            }
            all_patients.append(patient_dict)
        
        # Sort: Emergency patients first (by priority), then main queue patients
        # Emergency patients have their actual priority score, main queue already sorted by heap
        emergency_patients = [p for p in all_patients if p["emergency_level"] in ["PRIORITY", "CRITICAL"]]
        main_patients = [p for p in all_patients if p["emergency_level"] == "NORMAL"]
        
        emergency_patients.sort(key=lambda x: x["priority_score"])
        main_patients.sort(key=lambda x: x["priority_score"])
        
        # Emergency patients always come first
        sorted_patients = emergency_patients + main_patients
        
        return {
            "total_patients": len(sorted_patients),
            "emergency_count": len(emergency_patients),
            "main_queue_count": len(main_patients),
            "patients": sorted_patients,
            "statistics": {
                "total_enqueued": self.total_enqueued,
                "total_dequeued": self.total_dequeued,
                "reorder_count": self.reorder_count,
            }
        }
    
    def _reheapify_queue(self):
        """Rebuild heap structure after priority updates"""
        heapq.heapify(self.main_queue)
        heapq.heapify(self.emergency_queue)
        self.reorder_count += 1
        
        # Record reorder in MongoDB
        self.queue_state.record_reorder()
    
    def _load_from_mongodb(self):
        """Load existing active patients from MongoDB on startup"""
        try:
            # Get all active waiting patients from MongoDB
            patients = self.patient_model.get_active_queue()
            
            for mongo_patient in patients:
                # Convert to PatientNode
                emergency_map = {"CRITICAL": EmergencyLevel.CRITICAL, "PRIORITY": EmergencyLevel.PRIORITY, "NORMAL": EmergencyLevel.NORMAL}
                
                patient = PatientNode(
                    priority_score=mongo_patient.get("priorityScore", 0),
                    token_number=mongo_patient["tokenNumber"],
                    name=mongo_patient["name"],
                    contact_number=mongo_patient["contactNumber"],
                    emergency_level=emergency_map.get(mongo_patient.get("emergencyLevel", "NORMAL"), EmergencyLevel.NORMAL),
                    travel_eta_mins=mongo_patient.get("travelEtaMins", 20),
                    predicted_consult_mins=mongo_patient.get("predictedConsultMins", 15),
                    waiting_time_mins=mongo_patient.get("waitingTimeMins", 0),
                    symptoms=mongo_patient.get("symptoms", ""),
                    symptoms_analysis=mongo_patient.get("symptomsAnalysis", {}),
                    location=mongo_patient.get("location", ""),
                    travel_data=mongo_patient.get("travelData", {}),
                    booking_time=str(mongo_patient.get("bookingTime", datetime.utcnow())),
                )
                
                # Add to appropriate queue
                if patient.emergency_level == EmergencyLevel.CRITICAL:
                    heapq.heappush(self.emergency_queue, PatientNode(
                        priority_score=-patient.priority_score,
                        token_number=patient.token_number,
                        name=patient.name,
                        contact_number=patient.contact_number,
                        emergency_level=patient.emergency_level,
                        travel_eta_mins=patient.travel_eta_mins,
                        predicted_consult_mins=patient.predicted_consult_mins,
                        symptoms=patient.symptoms,
                        symptoms_analysis=patient.symptoms_analysis,
                    ))
                else:
                    heapq.heappush(self.main_queue, patient)
                
                # Add to map
                self.patient_map[patient.token_number] = patient
                self.wait_tracker[patient.token_number] = patient.waiting_time_mins
            
            if patients:
                print(f"[OK] Loaded {len(patients)} patients from MongoDB")
        
        except Exception as e:
            print(f"[WARNING] Error loading from MongoDB: {e}")


# Global singleton instance
_priority_queue_manager: Optional[PriorityQueueManager] = None


def get_priority_queue_manager(mongodb_manager=None) -> PriorityQueueManager:
    """Get or create global priority queue manager (MongoDB version)"""
    global _priority_queue_manager
    if _priority_queue_manager is None:
        _priority_queue_manager = PriorityQueueManager(mongodb_manager)
    return _priority_queue_manager
