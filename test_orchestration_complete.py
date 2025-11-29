#!/usr/bin/env python3
"""
Test orchestration after fixes - tests booking with all orchestration features
"""
import requests
import json

BASE_URL = "http://localhost:3000/api/v1"

def test_booking_with_orchestration():
    """Test booking a patient with full orchestration enabled"""
    print("🧪 Testing booking with complete orchestration...")
    print("=" * 60)
    
    # Book a NORMAL priority patient (should trigger ETA calculation due to queue size)
    booking_data = {
        "name": "Test Patient Orchestration",
        "contact_number": "9876543210",
        "symptoms": "Headache, Fever",
        "location": "Mumbai Central"
    }
    
    print(f"\n📝 Booking patient: {booking_data['name']}")
    print(f"   Symptoms: {booking_data['symptoms']}")
    
    response = requests.post(
        f"{BASE_URL}/appointments/book",
        json=booking_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"\n📊 Response Status: {response.status_code}")
    
    if response.status_code == 201:
        result = response.json()
        print(f"\n✅ Booking successful!")
        print(f"   Token: {result.get('tokenNumber', 'N/A')}")
        print(f"   Priority: {result.get('priority', 'N/A')}")
        print(f"   Queue Position: {result.get('queuePosition', 'N/A')}")
        
        # Check orchestration results
        orchestration = result.get('orchestration', {})
        print(f"\n🎼 Orchestration Status:")
        print(f"   Enabled: {orchestration.get('enabled', False)}")
        print(f"   Actions Executed: {orchestration.get('actions_executed', 0)}")
        
        if orchestration.get('details'):
            print(f"\n📋 Orchestration Actions:")
            for action in orchestration['details']:
                status = "✅ SUCCESS" if action.get('success') else "❌ FAILED"
                print(f"   {status} - {action.get('action', 'Unknown')}")
                if action.get('reason'):
                    print(f"      Reason: {action.get('reason')}")
                if not action.get('success') and action.get('error'):
                    print(f"      Error: {action.get('error')}")
                if action.get('result'):
                    print(f"      Result: {json.dumps(action.get('result'), indent=6)}")
        
        return True
    else:
        print(f"\n❌ Booking failed!")
        print(f"   Error: {response.text}")
        return False

def test_queue_stats():
    """Get queue statistics"""
    print(f"\n\n📊 Fetching Queue Statistics...")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/queue/stats")
    
    if response.status_code == 200:
        stats = response.json()
        print(f"\n📈 Queue Stats:")
        print(f"   Total Patients: {stats.get('total_patients', 0)}")
        print(f"   CRITICAL: {stats.get('critical_count', 0)}")
        print(f"   HIGH: {stats.get('high_count', 0)}")
        print(f"   NORMAL: {stats.get('normal_count', 0)}")
        print(f"   Average Wait: {stats.get('average_wait_time', 0)} mins")
        return True
    else:
        print(f"❌ Failed to get stats: {response.text}")
        return False

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🏥 MEDISYNC ORCHESTRATION TEST")
    print("=" * 60)
    
    # Test booking with orchestration
    booking_success = test_booking_with_orchestration()
    
    # Test queue stats
    stats_success = test_queue_stats()
    
    print("\n\n" + "=" * 60)
    if booking_success and stats_success:
        print("✅ ALL TESTS PASSED!")
        print("   - Booking with orchestration: ✅")
        print("   - Queue statistics: ✅")
        print("   - ETA calculation: Check orchestration details above")
        print("   - Notifications: Check orchestration details above")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 60)
