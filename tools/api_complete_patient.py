#!/usr/bin/env python3
"""
API Wrapper: Complete Patient Consultation
Called by Node.js backend to mark patient as completed via MongoDB
"""

import sys
import json
import os
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Suppress all print statements from imported modules
class SuppressDebugOutput:
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = sys.stderr  # Redirect all prints to stderr
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self._original_stdout

from mongodb_utils import PatientModel

def complete_patient(token_number):
    """
    Mark a patient as completed and remove from active queue
    
    Args:
        token_number (int): Patient's token number
        
    Returns:
        dict: Result with success status and message
    """
    try:
        # Get patient model (MongoDB connection handled internally)
        patient_model = PatientModel()
        
        # Find patient in MongoDB
        patient_doc = patient_model.find_by_token(token_number)
        
        if not patient_doc:
            return {
                "success": False,
                "error": f"Patient with token #{token_number} not found"
            }
        
        # Check if already completed
        if patient_doc.get("status") == "COMPLETED":
            return {
                "success": False,
                "error": f"Patient with token #{token_number} is already completed"
            }
        
        # Update patient status in MongoDB
        result = patient_model.collection.update_one(
            {"tokenNumber": token_number},
            {
                "$set": {
                    "status": "COMPLETED",
                    "isActive": False,
                    "completedAt": datetime.utcnow(),
                    "lastPriorityUpdate": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count > 0:
            return {
                "success": True,
                "message": f"Patient #{token_number} ({patient_doc['name']}) marked as COMPLETED",
                "data": {
                    "token_number": token_number,
                    "name": patient_doc["name"],
                    "status": "COMPLETED",
                    "completed_at": datetime.utcnow().isoformat()
                }
            }
        else:
            return {
                "success": False,
                "error": "Failed to update patient status in MongoDB"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Error completing patient: {str(e)}"
        }

def main():
    try:
        # Get token number from command line argument
        if len(sys.argv) < 2:
            print(json.dumps({"success": False, "error": "No token number provided"}))
            sys.exit(1)
        
        token_number = int(sys.argv[1])
        
        # Complete the patient with suppressed debug output
        with SuppressDebugOutput():
            result = complete_patient(token_number)
        
        # Return result as JSON
        print(json.dumps(result, default=str))
        
        if not result.get("success"):
            sys.exit(1)
        
    except ValueError:
        print(json.dumps({"success": False, "error": "Token number must be an integer"}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main()
