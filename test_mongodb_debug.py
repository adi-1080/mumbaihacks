import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.mongodb_utils import get_mongodb_manager, PatientModel

# Get MongoDB manager
manager = get_mongodb_manager()
db = manager.get_database()

print(f"Database name: {db.name if db is not None else 'None'}")
print(f"MongoDB URI: {os.getenv('MONGODB_URI', 'Not set')}")

# Get patient model
patient_model = PatientModel()

# Get all patients
patients = patient_model.get_active_queue()
print(f"\nActive queue patients: {len(patients)}")
for p in patients:
    print(f"  Token #{p['tokenNumber']}: {p['name']}")

# Get all patients (not just active)
if patient_model.collection:
    all_patients = list(patient_model.collection.find({}))
    print(f"\nAll patients in collection: {len(all_patients)}")
    for p in all_patients:
        print(f"  Token #{p['tokenNumber']}: {p['name']} (Status: {p.get('status', 'Unknown')})")
