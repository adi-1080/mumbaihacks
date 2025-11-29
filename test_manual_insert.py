import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.mongodb_utils import get_mongodb_manager, PatientModel

# Initialize MongoDB
manager = get_mongodb_manager()
patient_model = PatientModel()

# Create a simple test patient
test_patient = {
    "tokenNumber": 999,
    "name": "Manual Test Patient",
    "contactNumber": "0000000000",
    "symptoms": "manual test",
    "symptomsAnalysis": {},
    "location": "Test Location",
    "travelData": {},
    "priorityScore": 50.0,
    "emergencyLevel": "NORMAL",
    "travelEtaMins": 20,
    "predictedConsultMins": 15,
    "waitingTimeMins": 0.0,
    "arrivalProbability": 1.0,
    "bookingTime": datetime.utcnow(),
    "lastPriorityUpdate": datetime.utcnow(),
    "status": "WAITING",
    "isActive": True,
}

print("Creating patient...")
result = patient_model.create(test_patient)

if result:
    print(f"✅ Patient created successfully: {result['_id']}")
    
    # Verify it exists
    found = patient_model.find_by_token(999)
    if found:
        print(f"✅ Patient found in database: Token #{found['tokenNumber']}")
    else:
        print("❌ Patient NOT found in database!")
else:
    print("❌ Failed to create patient")

# List all patients
all_patients = list(patient_model.collection.find({}))
print(f"\nTotal patients in database: {len(all_patients)}")
for p in all_patients:
    print(f"  Token #{p['tokenNumber']}: {p['name']}")
