#!/usr/bin/env python3
"""
API Wrapper: Calculate ETAs
Called by Node.js backend to calculate ETAs for all patients
"""

import sys
import os
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Suppress all print statements from imported modules by redirecting stdout to stderr
class SuppressDebugOutput:
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = sys.stderr  # Redirect all prints to stderr
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self._original_stdout

from tools.eta_tools import calculate_intelligent_etas

def main():
    try:
        # Calculate ETAs with suppressed debug output
        # Note: calculate_intelligent_etas() uses its own Redis connection internally
        with SuppressDebugOutput():
            result = calculate_intelligent_etas()
        
        # Return ONLY clean JSON to stdout
        print(json.dumps({
            "success": True,
            "etas": result
        }))
        
    except Exception as e:
        # Log error to stderr for debugging
        print(f"[ERROR] ETA calculation failed: {e}", file=sys.stderr)
        # Return error JSON to stdout
        print(json.dumps({
            "success": False,
            "error": str(e)
        }))
        sys.exit(1)

if __name__ == "__main__":
    main()
