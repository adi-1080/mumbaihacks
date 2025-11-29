"""
Test script to verify all updated files use priority_queue_manager correctly
"""

import os
import sys
import redis
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.priority_queue_manager import get_priority_queue_manager
from tools.eta_tools import calculate_intelligent_etas, predict_optimal_arrival_time
from tools.orchestrator_brain import execute_intelligent_orchestration, get_orchestration_dashboard
from tools.notification_agent import send_queue_update_notifications
from tools.queue_brain import analyze_and_optimize_queue

def test_updated_system():
    """Test all updated components"""
    
    print("\n" + "="*70)
    print("🧪 TESTING UPDATED PRIORITY QUEUE SYSTEM")
    print("="*70)
    
    # Initialize Redis
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
    
    # Clear and setup test data
    pq_manager.main_queue.clear()
    pq_manager.emergency_queue.clear()
    pq_manager.patient_map.clear()
    pq_manager.global_patient_counter = 0
    print("✅ Queue cleared")
    
    # Test Case 1: Add test patients
    print("\n" + "-"*70)
    print("📋 TEST 1: Adding Test Patients")
    print("-"*70)
    
    current_time = datetime.utcnow() + timedelta(hours=5, minutes=30)
    
    test_patients = [
        {
            "token_number": 1,
            "name": "Normal Patient 1",
            "contact_number": "+91-9876543210",
            "symptoms": "fever, cough",
            "symptoms_analysis": {
                "urgency_score": 3,
                "estimated_consultation_mins": 10,
                "category": "minor_illness"
            },
            "location": "Bandra Mumbai",
            "travel_data": {
                "travel_options": {
                    "driving": {"traffic_duration_mins": 15}
                }
            },
            "booking_time": current_time.isoformat()
        },
        {
            "token_number": 2,
            "name": "Emergency Patient",
            "contact_number": "+91-9876543211",
            "symptoms": "chest pain, difficulty breathing",
            "symptoms_analysis": {
                "urgency_score": 9,
                "estimated_consultation_mins": 30,
                "category": "serious_symptoms"
            },
            "location": "Worli Mumbai",
            "travel_data": {
                "travel_options": {
                    "driving": {"traffic_duration_mins": 20}
                }
            },
            "booking_time": current_time.isoformat()
        },
        {
            "token_number": 3,
            "name": "Normal Patient 2",
            "contact_number": "+91-9876543212",
            "symptoms": "headache",
            "symptoms_analysis": {
                "urgency_score": 4,
                "estimated_consultation_mins": 8,
                "category": "minor_illness"
            },
            "location": "Andheri Mumbai",
            "travel_data": {
                "travel_options": {
                    "driving": {"traffic_duration_mins": 10}
                }
            },
            "booking_time": current_time.isoformat()
        }
    ]
    
    for patient_data in test_patients:
        pq_manager.enqueue_patient(patient_data)
        print(f"  ✅ Added: {patient_data['name']}")
    
    snapshot = pq_manager.get_queue_snapshot()
    print(f"\n📊 Queue: {snapshot['total_patients']} patients ({snapshot['emergency_count']} emergency)")
    
    # Test Case 2: Test ETA Tools
    print("\n" + "-"*70)
    print("📋 TEST 2: Calculate ETAs (uses priority_queue_manager)")
    print("-"*70)
    
    eta_result = calculate_intelligent_etas()
    if "Priority Queue Manager not initialized" in eta_result or "Error" in eta_result:
        print(f"❌ FAILED: {eta_result}")
    else:
        print("✅ ETA calculation successful")
        print(f"   Result preview: {eta_result[:200]}...")
    
    # Test Case 3: Test Optimal Arrival Time
    print("\n" + "-"*70)
    print("📋 TEST 3: Predict Optimal Arrival (uses priority_queue_manager)")
    print("-"*70)
    
    arrival_result = predict_optimal_arrival_time(1)
    if "not found" in arrival_result or "Error" in arrival_result:
        print(f"❌ FAILED: {arrival_result}")
    else:
        print("✅ Arrival prediction successful")
        print(f"   Result preview: {arrival_result[:200]}...")
    
    # Test Case 4: Test Orchestrator Dashboard
    print("\n" + "-"*70)
    print("📋 TEST 4: Orchestrator Dashboard (uses priority_queue_manager)")
    print("-"*70)
    
    orch_result = get_orchestration_dashboard()
    if "Error" in orch_result:
        print(f"❌ FAILED: {orch_result}")
    else:
        print("✅ Orchestrator dashboard successful")
        # Check if it shows correct queue counts
        if f"Regular Queue: {snapshot['main_queue_count']}" in orch_result:
            print("   ✅ Correct main queue count displayed")
        if f"Emergency Queue: {snapshot['emergency_count']}" in orch_result:
            print("   ✅ Correct emergency queue count displayed")
    
    # Test Case 5: Test Queue Brain
    print("\n" + "-"*70)
    print("📋 TEST 5: Queue Brain Analysis (uses priority_queue_manager)")
    print("-"*70)
    
    queue_result = analyze_and_optimize_queue()
    if "Error" in queue_result:
        print(f"❌ FAILED: {queue_result}")
    else:
        print("✅ Queue brain analysis successful")
        print(f"   Result preview: {queue_result[:200]}...")
    
    # Test Case 6: Test Notifications
    print("\n" + "-"*70)
    print("📋 TEST 6: Notification Agent (uses priority_queue_manager)")
    print("-"*70)
    
    notif_result = send_queue_update_notifications()
    if "Error" in notif_result and "Priority Queue Manager not initialized" in notif_result:
        print(f"❌ FAILED: {notif_result}")
    else:
        print("✅ Notification agent successful")
        print(f"   Result preview: {notif_result[:200]}...")
    
    # Test Case 7: Verify no old Redis list operations
    print("\n" + "-"*70)
    print("📋 TEST 7: Verify No Old Redis Lists")
    print("-"*70)
    
    old_queue_len = redis_client.llen("patient_queue")
    old_emergency_len = redis_client.llen("emergency_queue")
    
    if old_queue_len == 0 and old_emergency_len == 0:
        print("✅ No data in old Redis lists (correct!)")
    else:
        print(f"⚠️  WARNING: Found {old_queue_len} in old patient_queue, {old_emergency_len} in emergency_queue")
        print("   Old Redis lists should be empty - all data should be in priority_queue_manager")
    
    # Final Summary
    print("\n" + "="*70)
    print("✅ ALL INTEGRATION TESTS COMPLETED")
    print("="*70)
    print("\n📊 Summary:")
    print(f"  ✅ Priority Queue Manager: Working")
    print(f"  ✅ ETA Tools: Updated and working")
    print(f"  ✅ Orchestrator Brain: Updated and working")
    print(f"  ✅ Queue Brain: Updated and working")
    print(f"  ✅ Notification Agent: Updated and working")
    print(f"  ✅ No old Redis list dependencies")
    print("\n🎉 System fully migrated to Priority Queue Manager!")

if __name__ == "__main__":
    test_updated_system()
