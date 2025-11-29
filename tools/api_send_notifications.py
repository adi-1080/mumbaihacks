#!/usr/bin/env python3
"""
API Wrapper: Send Queue Notifications
Sends position update notifications to all affected patients
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

from tools.notification_agent import send_queue_update_notifications

def main():
    try:
        # Connect to Redis
        redis_client = redis.Redis(
            host='localhost',
            port=6379,
            decode_responses=True
        )
        
        # Send notifications with suppressed debug output
        with SuppressDebugOutput():
            result = send_queue_update_notifications()
        
        # Return ONLY clean JSON to stdout
        print(json.dumps({
            "success": True,
            "message": "Notifications sent successfully",
            "data": result if isinstance(result, dict) else {"message": result}
        }))
        
    except Exception as e:
        # Log error to stderr for debugging
        print(f"[ERROR] Notification sending failed: {e}", file=sys.stderr)
        # Return error JSON to stdout
        print(json.dumps({
            "success": False,
            "error": str(e)
        }))
        sys.exit(1)

if __name__ == "__main__":
    main()
