#!/usr/bin/env python3
"""
Quick test to verify ETA calculation works
"""
import requests
import json

BASE_URL = "http://localhost:3000/api/v1"

print("\n🧪 Testing ETA Calculation Fix...")
print("=" * 60)

# Test direct ETA endpoint
print("\n📊 Test 1: Direct ETA Calculation")
try:
    response = requests.get(f"{BASE_URL}/queue/etas", timeout=15)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("✅ SUCCESS! ETA calculation working!")
        print(f"Response keys: {list(result.keys())}")
        if result.get('success'):
            print(f"✅ Success flag: {result['success']}")
            print(f"📋 ETA data present: {'data' in result or 'etas' in result}")
    else:
        print(f"❌ FAILED with status {response.status_code}")
        print(f"Error: {response.text}")
except Exception as e:
    print(f"❌ ERROR: {e}")

# Test booking with orchestration
print("\n\n📝 Test 2: Book Patient (Orchestration with ETA)")
booking_data = {
    "name": "Test ETA Patient",
    "contact_number": "9876543210",
    "symptoms": "Test symptoms",
    "location": "Mumbai"
}

try:
    response = requests.post(
        f"{BASE_URL}/appointments/book",
        json=booking_data,
        timeout=20
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 201:
        result = response.json()
        print("✅ Booking successful!")
        
        if result.get('orchestration'):
            orch = result['orchestration']
            print(f"\n🎼 Orchestration Details:")
            print(f"   Enabled: {orch.get('enabled')}")
            print(f"   Actions: {orch.get('actions_executed')}")
            
            for detail in orch.get('details', []):
                action = detail.get('action')
                success = detail.get('success')
                status_icon = "✅" if success else "❌"
                print(f"   {status_icon} {action}: {'SUCCESS' if success else 'FAILED'}")
                if not success and detail.get('error'):
                    print(f"      Error: {detail.get('error')}")
    else:
        print(f"❌ Booking failed: {response.text}")
except Exception as e:
    print(f"❌ ERROR: {e}")

print("\n" + "=" * 60)
print("Test complete!")
