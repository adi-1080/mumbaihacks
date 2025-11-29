#!/usr/bin/env python3
"""
API Wrapper: Book Appointment
Called by Node.js backend to book appointments through Priority Queue Manager
"""

import sys
import os
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Suppress all print statements from imported modules
class SuppressDebugOutput:
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = sys.stderr  # Redirect all prints to stderr
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self._original_stdout

from tools.clinic_tools_priority_queue import book_intelligent_patient_appointment

def main():
    try:
        # Get appointment data from command line argument
        if len(sys.argv) < 2:
            print(json.dumps({"error": "No appointment data provided"}))
            sys.exit(1)
        
        appointment_data = json.loads(sys.argv[1])
        
        # Book appointment with suppressed debug output
        with SuppressDebugOutput():
            result = book_intelligent_patient_appointment(
                name=appointment_data.get('name'),
                contact_number=appointment_data.get('contact_number'),
                symptoms=appointment_data.get('symptoms'),
                location=appointment_data.get('location', 'Not provided')
            )
        
        # Return result as JSON
        print(json.dumps({
            "success": True,
            "result": result
        }))
        
    except Exception as e:
        print(json.dumps({
            "success": False,
            "error": str(e)
        }))
        sys.exit(1)

if __name__ == "__main__":
    main()
