#!/usr/bin/env python3
"""
API Wrapper: Cancel Appointment
Called by Node.js backend to cancel appointments
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

from tools.priority_queue_manager import get_priority_queue_manager

def main():
    try:
        # Get token number from command line argument
        if len(sys.argv) < 2:
            print(json.dumps({"error": "No token number provided"}))
            sys.exit(1)
        
        token_number = int(sys.argv[1])
        
        # Connect to Redis
        redis_client = redis.Redis(
            host='localhost',
            port=6379,
            decode_responses=True
        )
        
        # Suppress debug output during operations
        with SuppressDebugOutput():
            # Get priority queue manager
            pq_manager = get_priority_queue_manager(redis_client)
            
            # Remove patient from queue
            success = pq_manager.remove_patient(token_number)
        
        if success:
            print(json.dumps({
                "success": True,
                "message": f"Appointment #{token_number} canceled successfully"
            }))
        else:
            print(json.dumps({
                "success": False,
                "error": f"Patient #{token_number} not found in queue"
            }))
            sys.exit(1)
        
    except Exception as e:
        print(json.dumps({
            "success": False,
            "error": str(e)
        }))
        sys.exit(1)

if __name__ == "__main__":
    main()
