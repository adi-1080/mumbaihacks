#!/usr/bin/env python3
"""
API Wrapper: Update Patient Location
Called by Node.js backend to update patient location and trigger queue reordering
"""

import sys
import os
import json
import redis

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

from tools.clinic_tools_priority_queue import update_patient_realtime_location

def main():
    try:
        # Get arguments from command line
        if len(sys.argv) < 3:
            print(json.dumps({"error": "Token number and location data required"}))
            sys.exit(1)
        
        token_number = int(sys.argv[1])
        location_data = json.loads(sys.argv[2])
        
        # Connect to Redis
        redis_client = redis.Redis(
            host='localhost',
            port=6379,
            decode_responses=True
        )
        
        # Update patient location with suppressed debug output
        with SuppressDebugOutput():
            result = update_patient_realtime_location(
                token_number=token_number,
                new_location=f"{location_data.get('latitude')},{location_data.get('longitude')}",
                redis_client=redis_client
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
