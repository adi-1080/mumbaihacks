"""
MongoDB Utilities for ADK Agent Workflow
MongoDB connection manager and model classes for patient queue system
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import PyMongoError, DuplicateKeyError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = "medisync"  # Same as backend database

# Global singleton instance
_mongodb_manager = None


class MongoDBManager:
    """Singleton MongoDB connection manager"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._client = None
        self._db = None
        self._initialize_connection()
    
    def _initialize_connection(self):
        """Initialize MongoDB connection"""
        try:
            # Connect to MongoDB
            if "mongodb://" in MONGODB_URI or "mongodb+srv://" in MONGODB_URI:
                self._client = MongoClient(
                    MONGODB_URI,
                    serverSelectionTimeoutMS=5000,
                    socketTimeoutMS=45000
                )
                
                # Extract database name from URI
                # Format: mongodb+srv://user:pass@host.net/database?options
                uri_without_protocol = MONGODB_URI.split("://")[1]  # Remove mongodb+srv://
                if "/" in uri_without_protocol:
                    # Split on first / to get the part after host
                    after_host = uri_without_protocol.split("/", 1)[1]
                    # Database name is before ? (if present)
                    db_name = after_host.split("?")[0] if "?" in after_host else after_host
                    if db_name and db_name not in ["", "admin", "test"]:
                        self._db = self._client[db_name]
                    else:
                        self._db = self._client[DB_NAME]
                else:
                    self._db = self._client[DB_NAME]
            else:
                self._db = self._client[DB_NAME]
            
            # Test connection
            self._client.server_info()
            print(f"[OK] MongoDB connected successfully: {self._db.name}")
            
            # Create indexes
            self._create_indexes()
            
        except PyMongoError as e:
            print(f"[WARNING] MongoDB connection failed: {e}")
            print("Falling back to local storage (limited functionality)")
            self._client = None
            self._db = None
    
    def _create_indexes(self):
        """Create necessary indexes for performance"""
        if self._db is None:
            return
        
        try:
            # Patient collection indexes
            patients = self._db.patients
            patients.create_index("tokenNumber", unique=True)
            patients.create_index([("status", ASCENDING), ("isActive", ASCENDING)])
            patients.create_index([("emergencyLevel", DESCENDING), ("priorityScore", ASCENDING)])
            patients.create_index("bookingTime")
            
            # QueueState collection indexes
            queue_state = self._db.queuestate
            queue_state.create_index("type", unique=True)
            
            # Notification collection indexes
            notifications = self._db.notifications
            notifications.create_index([("tokenNumber", ASCENDING), ("createdAt", DESCENDING)])
            notifications.create_index([("status", ASCENDING), ("scheduledFor", ASCENDING)])
            
            print("[OK] MongoDB indexes created successfully")
        except PyMongoError as e:
            print(f"[WARNING] Index creation warning: {e}")
    
    def get_database(self):
        """Get database instance"""
        return self._db
    
    def get_client(self):
        """Get MongoDB client"""
        return self._client
    
    def is_connected(self):
        """Check if MongoDB is connected"""
        return self._db is not None


def get_mongodb_manager():
    """Get or create MongoDB manager singleton"""
    global _mongodb_manager
    if _mongodb_manager is None:
        _mongodb_manager = MongoDBManager()
    return _mongodb_manager


class PatientModel:
    """MongoDB model for patient operations"""
    
    def __init__(self):
        self.manager = get_mongodb_manager()
        self.db = self.manager.get_database()
        self.collection = self.db.patients if self.db is not None else None
    
    def create(self, patient_data: Dict) -> Optional[Dict]:
        """Create new patient document"""
        if self.collection is None:
            print("[WARNING] MongoDB not available")
            return None
        
        try:
            # Add metadata
            patient_data["createdAt"] = datetime.utcnow()
            patient_data["updatedAt"] = datetime.utcnow()
            patient_data["isActive"] = True
            
            result = self.collection.insert_one(patient_data)
            patient_data["_id"] = result.inserted_id
            
            print(f"[OK] Patient created in MongoDB: Token #{patient_data['tokenNumber']}")
            return patient_data
        except DuplicateKeyError:
            print(f"[WARNING] Patient token #{patient_data['tokenNumber']} already exists")
            return None
        except PyMongoError as e:
            print(f"[WARNING] MongoDB error creating patient: {e}")
            return None
    
    def find_by_token(self, token_number: int) -> Optional[Dict]:
        """Find patient by token number"""
        if self.collection is None:
            return None
        
        try:
            return self.collection.find_one({"tokenNumber": token_number})
        except PyMongoError as e:
            print(f"[WARNING] MongoDB error finding patient: {e}")
            return None
    
    def get_active_queue(self) -> List[Dict]:
        """Get active queue sorted by priority"""
        if self.collection is None:
            return []
        
        try:
            # Get WAITING patients, sorted by emergency level (desc) then priority score (asc)
            patients = list(self.collection.find({
                "status": "WAITING",
                "isActive": True
            }).sort([
                ("emergencyLevel", DESCENDING),
                ("priorityScore", ASCENDING)
            ]))
            
            return patients
        except PyMongoError as e:
            print(f"[WARNING] MongoDB error getting queue: {e}")
            return []
    
    def update_patient(self, token_number: int, updates: Dict) -> bool:
        """Update patient attributes"""
        if self.collection is None:
            return False
        
        try:
            updates["updatedAt"] = datetime.utcnow()
            
            result = self.collection.update_one(
                {"tokenNumber": token_number},
                {"$set": updates}
            )
            
            return result.modified_count > 0
        except PyMongoError as e:
            print(f"[WARNING] MongoDB error updating patient: {e}")
            return False
    
    def start_consultation(self, token_number: int) -> bool:
        """Mark patient as in consultation"""
        if self.collection is None:
            return False
        
        try:
            result = self.collection.update_one(
                {"tokenNumber": token_number},
                {"$set": {
                    "status": "IN_CONSULTATION",
                    "consultationStartTime": datetime.utcnow(),
                    "updatedAt": datetime.utcnow()
                }}
            )
            
            return result.modified_count > 0
        except PyMongoError as e:
            print(f"[WARNING] MongoDB error starting consultation: {e}")
            return False
    
    def complete_patient(self, token_number: int) -> bool:
        """Mark patient as completed"""
        if self.collection is None:
            return False
        
        try:
            patient = self.find_by_token(token_number)
            if not patient:
                return False
            
            consultation_start = patient.get("consultationStartTime")
            actual_consultation_mins = None
            
            if consultation_start:
                duration = datetime.utcnow() - consultation_start
                actual_consultation_mins = duration.total_seconds() / 60
            
            result = self.collection.update_one(
                {"tokenNumber": token_number},
                {"$set": {
                    "status": "COMPLETED",
                    "completedAt": datetime.utcnow(),
                    "isActive": False,
                    "actualConsultationMins": actual_consultation_mins,
                    "updatedAt": datetime.utcnow()
                }}
            )
            
            return result.modified_count > 0
        except PyMongoError as e:
            print(f"[WARNING] MongoDB error completing patient: {e}")
            return False
    
    def cancel_patient(self, token_number: int) -> bool:
        """Cancel patient appointment"""
        if self.collection is None:
            return False
        
        try:
            result = self.collection.update_one(
                {"tokenNumber": token_number},
                {"$set": {
                    "status": "CANCELLED",
                    "isActive": False,
                    "updatedAt": datetime.utcnow()
                }}
            )
            
            return result.modified_count > 0
        except PyMongoError as e:
            print(f"[WARNING] MongoDB error cancelling patient: {e}")
            return False


class QueueStateModel:
    """MongoDB model for queue state operations"""
    
    def __init__(self):
        self.manager = get_mongodb_manager()
        self.db = self.manager.get_database()
        self.collection = self.db.queuestate if self.db is not None else None
    
    def get_global_state(self) -> Optional[Dict]:
        """Get or create global queue state"""
        if self.collection is None:
            return None
        
        try:
            state = self.collection.find_one({"type": "GLOBAL"})
            
            if not state:
                # Create initial state
                state = {
                    "type": "GLOBAL",
                    "currentTokenNumber": 0,
                    "dailyStats": {
                        "date": datetime.utcnow().date().isoformat(),
                        "totalBookings": 0,
                        "completedConsultations": 0,
                        "cancelledAppointments": 0,
                        "emergencyPatients": 0,
                        "averageWaitTimeMins": 0,
                        "averageConsultationMins": 0
                    },
                    "currentMetrics": {
                        "patientsWaiting": 0,
                        "patientsInConsultation": 0,
                        "emergencyCount": 0,
                        "totalReorders": 0
                    },
                    "config": {
                        "agingRateMins": 5,
                        "starvationThresholdMins": 30,
                        "maxWaitTimeMins": 120,
                        "defaultConsultationMins": 15
                    },
                    "createdAt": datetime.utcnow(),
                    "updatedAt": datetime.utcnow()
                }
                
                self.collection.insert_one(state)
            
            return state
        except PyMongoError as e:
            print(f"[WARNING] MongoDB error getting queue state: {e}")
            return None
    
    def get_next_token(self) -> int:
        """Get and increment token number atomically"""
        if self.collection is None:
            return 1
        
        try:
            result = self.collection.find_one_and_update(
                {"type": "GLOBAL"},
                {
                    "$inc": {"currentTokenNumber": 1},
                    "$set": {"updatedAt": datetime.utcnow()}
                },
                return_document=True
            )
            
            if result:
                return result["currentTokenNumber"]
            
            return 1
        except PyMongoError as e:
            print(f"[WARNING] MongoDB error getting next token: {e}")
            return 1
    
    def record_booking(self, is_emergency: bool = False) -> bool:
        """Record a new booking in stats"""
        if self.collection is None:
            return False
        
        try:
            update = {
                "$inc": {"dailyStats.totalBookings": 1},
                "$set": {"updatedAt": datetime.utcnow()}
            }
            
            if is_emergency:
                update["$inc"]["dailyStats.emergencyPatients"] = 1
            
            result = self.collection.update_one(
                {"type": "GLOBAL"},
                update
            )
            
            return result.modified_count > 0
        except PyMongoError as e:
            print(f"[WARNING] MongoDB error recording booking: {e}")
            return False
    
    def record_completion(self, consultation_mins: float = None) -> bool:
        """Record completed consultation"""
        if self.collection is None:
            return False
        
        try:
            result = self.collection.update_one(
                {"type": "GLOBAL"},
                {
                    "$inc": {"dailyStats.completedConsultations": 1},
                    "$set": {"updatedAt": datetime.utcnow()}
                }
            )
            
            return result.modified_count > 0
        except PyMongoError as e:
            print(f"[WARNING] MongoDB error recording completion: {e}")
            return False
    
    def record_cancellation(self) -> bool:
        """Record cancelled appointment"""
        if self.collection is None:
            return False
        
        try:
            result = self.collection.update_one(
                {"type": "GLOBAL"},
                {
                    "$inc": {"dailyStats.cancelledAppointments": 1},
                    "$set": {"updatedAt": datetime.utcnow()}
                }
            )
            
            return result.modified_count > 0
        except PyMongoError as e:
            print(f"[WARNING] MongoDB error recording cancellation: {e}")
            return False
    
    def record_reorder(self) -> bool:
        """Record queue reorder event"""
        if self.collection is None:
            return False
        
        try:
            result = self.collection.update_one(
                {"type": "GLOBAL"},
                {
                    "$inc": {"currentMetrics.totalReorders": 1},
                    "$set": {
                        "currentMetrics.lastReorderTime": datetime.utcnow(),
                        "updatedAt": datetime.utcnow()
                    }
                }
            )
            
            return result.modified_count > 0
        except PyMongoError as e:
            print(f"[WARNING] MongoDB error recording reorder: {e}")
            return False


class NotificationModel:
    """MongoDB model for notification operations"""
    
    def __init__(self):
        self.manager = get_mongodb_manager()
        self.db = self.manager.get_database()
        self.collection = self.db.notifications if self.db is not None else None
    
    def create(self, notification_data: Dict) -> Optional[Dict]:
        """Create new notification"""
        if self.collection is None:
            return None
        
        try:
            notification_data["createdAt"] = datetime.utcnow()
            notification_data["updatedAt"] = datetime.utcnow()
            
            result = self.collection.insert_one(notification_data)
            notification_data["_id"] = result.inserted_id
            
            return notification_data
        except PyMongoError as e:
            print(f"[WARNING] MongoDB error creating notification: {e}")
            return None
    
    def get_patient_notifications(self, token_number: int, limit: int = 50) -> List[Dict]:
        """Get notification history for patient"""
        if self.collection is None:
            return []
        
        try:
            notifications = list(self.collection.find({
                "tokenNumber": token_number
            }).sort("createdAt", DESCENDING).limit(limit))
            
            return notifications
        except PyMongoError as e:
            print(f"[WARNING] MongoDB error getting notifications: {e}")
            return []
