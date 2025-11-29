#!/usr/bin/env python3
"""
API Wrapper: Queue Intelligence Dashboard
Provides intelligent insights and analytics about the queue
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

from tools.queue_intelligence import IntelligentQueue

def main():
    try:
        # Connect to Redis
        redis_client = redis.Redis(
            host='localhost',
            port=6379,
            decode_responses=True
        )
        
        # Get queue intelligence with suppressed debug output
        with SuppressDebugOutput():
            intelligent_queue = IntelligentQueue(redis_client)
            result = intelligent_queue.optimize_queue_order()
        
        # Return ONLY clean JSON to stdout
        print(json.dumps({
            "success": True,
            "intelligence": result
        }))
        
    except Exception as e:
        # Log error to stderr for debugging
        print(f"[ERROR] Queue intelligence failed: {e}", file=sys.stderr)
        # Return error JSON to stdout
        print(json.dumps({
            "success": False,
            "error": str(e)
        }))
        sys.exit(1)

if __name__ == "__main__":
    main()
