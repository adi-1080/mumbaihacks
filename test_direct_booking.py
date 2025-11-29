import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.clinic_tools_priority_queue import book_intelligent_patient_appointment

# Test booking
result = book_intelligent_patient_appointment(
    name="Debug Patient",
    contact_number="8888888888",
    symptoms="test symptoms for debugging",
    location="Andheri, Mumbai"
)

print("=== BOOKING RESULT ===")
print(result)
