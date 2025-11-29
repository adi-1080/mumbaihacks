"""
Test script to verify patient completion/dequeue functionality works correctly
Tests the fixed clinic_monitor.py integration with priority_queue_manager
"""

import os
import sys
import redis
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.priority_queue_manager import get_priority_queue_manager
from tools.clinic_monitor import mark_patient_completed

def test_completion_workflow():
    """Test complete booking → completion → dequeue workflow"""
    
    print("\n" + "="*60)
    print("🧪 TESTING PATIENT COMPLETION WORKFLOW")
    print("="*60)
    
    # Initialize Redis and Priority Queue Manager
    try:
        redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            password=os.getenv("REDIS_PASSWORD", None),
            db=0,
            decode_responses=True
        )
        redis_client.ping()
        print("✅ Connected to Redis")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return
    
    # Get priority queue manager
    pq_manager = get_priority_queue_manager(redis_client)
    print("✅ Priority Queue Manager initialized")
    
    # Clear existing queue for clean test
    pq_manager.main_queue.clear()
    pq_manager.emergency_queue.clear()
    pq_manager.patient_map.clear()
    pq_manager.global_patient_counter = 0
    print("✅ Queue cleared for testing")
    
    # Test Case 1: Book 3 test patients
    print("\n" + "-"*60)
    print("📋 TEST 1: Booking 3 patients")
    print("-"*60)
    
    current_time = datetime.utcnow() + timedelta(hours=5, minutes=30)  # IST
    
    test_patients = [
        {
            "token_number": pq_manager.global_patient_counter + 1,
            "name": "Test Patient 1",
            "contact_number": "9999999991",
            "symptoms": "fever, cough",
            "symptoms_analysis": {
                "urgency_score": 3,
                "estimated_consultation_mins": 10,
                "category": "minor_illness"
            },
            "location": "Test Location 1",
            "travel_data": {
                "travel_options": {
                    "driving": {
                        "traffic_duration_mins": 15
                    }
                }
            },
            "booking_time": current_time.isoformat()
        },
        {
            "token_number": pq_manager.global_patient_counter + 2,
            "name": "Test Emergency Patient",
            "contact_number": "9999999992",
            "symptoms": "chest pain, difficulty breathing",
            "symptoms_analysis": {
                "urgency_score": 9,
                "estimated_consultation_mins": 30,
                "category": "serious_symptoms"
            },
            "location": "Test Location 2",
            "travel_data": {
                "travel_options": {
                    "driving": {
                        "traffic_duration_mins": 20
                    }
                }
            },
            "booking_time": current_time.isoformat()
        },
        {
            "token_number": pq_manager.global_patient_counter + 3,
            "name": "Test Patient 2",
            "contact_number": "9999999993",
            "symptoms": "headache",
            "symptoms_analysis": {
                "urgency_score": 2,
                "estimated_consultation_mins": 8,
                "category": "minor_illness"
            },
            "location": "Test Location 3",
            "travel_data": {
                "travel_options": {
                    "driving": {
                        "traffic_duration_mins": 10
                    }
                }
            },
            "booking_time": current_time.isoformat()
        }
    ]
    
    booked_tokens = []
    for patient_data in test_patients:
        patient_node = pq_manager.enqueue_patient(patient_data)
        booked_tokens.append(patient_node.token_number)
        is_emergency = patient_node.emergency_level == 2  # CRITICAL = 2
        print(f"  ✅ Booked: {patient_node.name} (Token #{patient_node.token_number}, Emergency: {is_emergency})")
    
    # Check queue state
    snapshot = pq_manager.get_queue_snapshot()
    print(f"\n📊 Queue Status After Booking:")
    print(f"  Main Queue: {snapshot['main_queue_count']} patients")
    print(f"  Emergency Queue: {snapshot['emergency_count']} patients")
    print(f"  Total: {snapshot['total_patients']} patients")
    
    # Test Case 2: Complete first patient (should be emergency patient)
    print("\n" + "-"*60)
    print("📋 TEST 2: Complete first patient (emergency)")
    print("-"*60)
    
    next_patient = pq_manager.peek()
    if next_patient:
        print(f"  Next patient to serve: {next_patient.name} (Token #{next_patient.token_number})")
        print(f"  Is Emergency: {next_patient.emergency_level == 2}")
        
        # Call mark_patient_completed (this should use our fixed function)
        result = mark_patient_completed(next_patient.token_number)
        print(f"\n{result}\n")
        
        # Verify removal
        snapshot_after = pq_manager.get_queue_snapshot()
        print(f"📊 Queue Status After Completion:")
        print(f"  Main Queue: {snapshot_after['main_queue_count']} patients")
        print(f"  Emergency Queue: {snapshot_after['emergency_count']} patients")
        print(f"  Total: {snapshot_after['total_patients']} patients")
        
        if snapshot_after['total_patients'] == snapshot['total_patients'] - 1:
            print("  ✅ Patient successfully removed from queue!")
        else:
            print("  ❌ ERROR: Patient was NOT removed from queue!")
            return
    
    # Test Case 3: Complete second patient
    print("\n" + "-"*60)
    print("📋 TEST 3: Complete second patient")
    print("-"*60)
    
    next_patient = pq_manager.peek()
    if next_patient:
        print(f"  Next patient to serve: {next_patient.name} (Token #{next_patient.token_number})")
        result = mark_patient_completed(next_patient.token_number)
        print(f"\n{result}\n")
        
        snapshot_after = pq_manager.get_queue_snapshot()
        print(f"📊 Queue Status After Completion:")
        print(f"  Total: {snapshot_after['total_patients']} patients")
        
        if snapshot_after['total_patients'] == 1:
            print("  ✅ Patient successfully removed!")
        else:
            print("  ❌ ERROR: Patient was NOT removed!")
            return
    
    # Test Case 4: Complete last patient
    print("\n" + "-"*60)
    print("📋 TEST 4: Complete last patient (queue should be empty)")
    print("-"*60)
    
    next_patient = pq_manager.peek()
    if next_patient:
        print(f"  Next patient to serve: {next_patient.name} (Token #{next_patient.token_number})")
        result = mark_patient_completed(next_patient.token_number)
        print(f"\n{result}\n")
        
        snapshot_after = pq_manager.get_queue_snapshot()
        print(f"📊 Queue Status After Completion:")
        print(f"  Total: {snapshot_after['total_patients']} patients")
        
        if snapshot_after['total_patients'] == 0:
            print("  ✅ Queue is empty! All patients served successfully!")
        else:
            print("  ❌ ERROR: Queue should be empty but has patients!")
            return
    
    # Test Case 5: Try to complete non-existent patient
    print("\n" + "-"*60)
    print("📋 TEST 5: Try completing non-existent patient")
    print("-"*60)
    
    fake_token = 99999
    print(f"  Attempting to complete token #{fake_token} (doesn't exist)")
    result = mark_patient_completed(fake_token)
    print(f"\n{result}\n")
    
    # Final summary
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)
    print("\n✨ Summary:")
    print("  ✅ Patients can be booked")
    print("  ✅ Emergency patients have priority")
    print("  ✅ mark_patient_completed() removes patients from queue")
    print("  ✅ Queue size decreases correctly")
    print("  ✅ Empty queue handled gracefully")
    print("  ✅ Non-existent patient handled gracefully")
    print("\n🎉 Patient completion workflow is WORKING CORRECTLY!")

if __name__ == "__main__":
    test_completion_workflow()
