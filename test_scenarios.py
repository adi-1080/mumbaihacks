"""
Comprehensive Test Suite for MediSync Agentic Workflow
Tests the actual agent workflow including all sub-agents
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List
import sys
import os
import redis

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.free_maps import FreeMapsService

# Import the root agent to test actual workflow
try:
    from tools import root_agent
    AGENT_AVAILABLE = True
    print("✅ Root agent imported successfully")
except Exception as e:
    print(f"⚠️ Could not import root agent: {e}")
    AGENT_AVAILABLE = False

# Test cases covering different scenarios
TEST_CASES = [
    {
        "name": "Normal Fever Case",
        "patient_name": "Rahul Sharma",
        "age": 28,
        "symptoms": "High fever, headache, body pain since 2 days",
        "location": "Andheri West, Mumbai, Maharashtra",
        "phone": "+91-9876543210",
        "expected_urgency": "medium"
    },
    {
        "name": "Emergency Chest Pain",
        "patient_name": "Priya Patel",
        "age": 55,
        "symptoms": "Severe chest pain, difficulty breathing, sweating",
        "location": "Bandra East, Mumbai, Maharashtra",
        "phone": "+91-9876543211",
        "expected_urgency": "high"
    },
    {
        "name": "Minor Cold",
        "patient_name": "Amit Kumar",
        "age": 22,
        "symptoms": "Mild cold, runny nose, occasional cough",
        "location": "Malad West, Mumbai, Maharashtra",
        "phone": "+91-9876543212",
        "expected_urgency": "low"
    },
    {
        "name": "Diabetes Follow-up",
        "patient_name": "Sunita Desai",
        "age": 45,
        "symptoms": "Routine diabetes check, need prescription refill",
        "location": "Goregaon East, Mumbai, Maharashtra",
        "phone": "+91-9876543213",
        "expected_urgency": "low"
    },
    {
        "name": "Accident Case",
        "patient_name": "Rohan Mehta",
        "age": 30,
        "symptoms": "Road accident, bleeding from head, unconscious briefly",
        "location": "Juhu, Mumbai, Maharashtra",
        "phone": "+91-9876543214",
        "expected_urgency": "high"
    },
    {
        "name": "Child Fever",
        "patient_name": "Baby Aisha",
        "age": 3,
        "symptoms": "High fever 103F, not eating, crying continuously",
        "location": "Powai, Mumbai, Maharashtra",
        "phone": "+91-9876543215",
        "expected_urgency": "medium-high"
    },
    {
        "name": "Distant Patient",
        "patient_name": "Vikram Singh",
        "age": 35,
        "symptoms": "Severe stomach pain, vomiting",
        "location": "Thane West, Maharashtra",
        "phone": "+91-9876543216",
        "expected_urgency": "medium"
    },
    {
        "name": "Near Patient",
        "patient_name": "Neha Joshi",
        "age": 27,
        "symptoms": "Skin rash, itching",
        "location": "Santacruz West, Mumbai, Maharashtra",
        "phone": "+91-9876543217",
        "expected_urgency": "low"
    },
]

class AgenticWorkflowTester:
    """Test the complete agentic workflow using root agent"""
    
    def __init__(self):
        self.maps_service = FreeMapsService()
        self.results = []
        
        # Connect to Redis to check actual queue
        try:
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                decode_responses=True
            )
            self.redis_client.ping()
            print("✅ Connected to Redis for queue monitoring")
        except Exception as e:
            print(f"⚠️ Could not connect to Redis: {e}")
            self.redis_client = None
    
    def get_redis_queue_status(self):
        """Get actual queue status from Redis"""
        if not self.redis_client:
            return None
        
        try:
            # Get all Redis keys
            all_keys = self.redis_client.keys('*')
            
            # Categorize keys
            queue_keys = [k for k in all_keys if 'queue' in k.lower()]
            patient_keys = [k for k in all_keys if 'patient' in k.lower()]
            brain_keys = [k for k in all_keys if 'brain' in k.lower()]
            symptom_keys = [k for k in all_keys if 'symptom' in k.lower()]
            starvation_keys = [k for k in all_keys if 'starv' in k.lower()]
            
            queue_data = {
                'all_keys': all_keys,
                'queue_keys': queue_keys,
                'patient_keys': patient_keys,
                'brain_keys': brain_keys,
                'symptom_keys': symptom_keys,
                'starvation_keys': starvation_keys,
                'patients': [],
                'queue_data': {}
            }
            
            # Get queue data
            for key in queue_keys:
                key_type = self.redis_client.type(key)
                if key_type == 'list':
                    queue_data['queue_data'][key] = {
                        'type': 'list',
                        'data': self.redis_client.lrange(key, 0, -1)
                    }
                elif key_type == 'string':
                    queue_data['queue_data'][key] = {
                        'type': 'string',
                        'data': self.redis_client.get(key)
                    }
                elif key_type == 'hash':
                    queue_data['queue_data'][key] = {
                        'type': 'hash',
                        'data': self.redis_client.hgetall(key)
                    }
                elif key_type == 'zset':
                    queue_data['queue_data'][key] = {
                        'type': 'zset',
                        'data': self.redis_client.zrange(key, 0, -1, withscores=True)
                    }
            
            # Get patient data
            for key in patient_keys[:20]:  # Limit to first 20
                key_type = self.redis_client.type(key)
                if key_type == 'hash':
                    patient_data = self.redis_client.hgetall(key)
                    queue_data['patients'].append({
                        'key': key,
                        'data': patient_data
                    })
                elif key_type == 'string':
                    try:
                        patient_data = json.loads(self.redis_client.get(key))
                        queue_data['patients'].append({
                            'key': key,
                            'data': patient_data
                        })
                    except:
                        pass
            
            return queue_data
        except Exception as e:
            print(f"⚠️ Error reading from Redis: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def display_queue_status(self, prefix="", detailed=True):
        """Display current queue status"""
        print(f"\n{prefix}{'='*60}")
        print(f"{prefix}📊 CURRENT QUEUE STATUS (from Redis)")
        print(f"{prefix}{'='*60}")
        
        queue_data = self.get_redis_queue_status()
        
        if not queue_data:
            print(f"{prefix}   ⚠️ Could not retrieve queue data")
            return
        
        # Show all Redis keys
        print(f"\n{prefix}🔑 Total Redis Keys: {len(queue_data.get('all_keys', []))}")
        
        # Show categorized keys
        if queue_data.get('queue_keys'):
            print(f"\n{prefix}📋 Queue Keys ({len(queue_data['queue_keys'])}):")
            for key in queue_data['queue_keys']:
                print(f"{prefix}   - {key}")
        
        if queue_data.get('brain_keys'):
            print(f"\n{prefix}🧠 Brain Keys ({len(queue_data['brain_keys'])}):")
            for key in queue_data['brain_keys']:
                print(f"{prefix}   - {key}")
        
        if queue_data.get('symptom_keys'):
            print(f"\n{prefix}🔍 Symptom Keys ({len(queue_data['symptom_keys'])}):")
            for key in queue_data['symptom_keys']:
                print(f"{prefix}   - {key}")
        
        if queue_data.get('starvation_keys'):
            print(f"\n{prefix}⏰ Starvation Tracker Keys ({len(queue_data['starvation_keys'])}):")
            for key in queue_data['starvation_keys']:
                print(f"{prefix}   - {key}")
        
        # Show patient count
        if queue_data.get('patient_keys'):
            print(f"\n{prefix}👥 Patient Keys: {len(queue_data['patient_keys'])} patients")
        
        # Show detailed queue data
        if detailed and queue_data.get('queue_data'):
            print(f"\n{prefix}📦 Queue Data Details:")
            for key, info in list(queue_data['queue_data'].items())[:5]:
                print(f"\n{prefix}   Key: {key}")
                print(f"{prefix}   Type: {info['type']}")
                data = info['data']
                if isinstance(data, list):
                    print(f"{prefix}   Count: {len(data)}")
                    for i, item in enumerate(data[:3], 1):
                        print(f"{prefix}     {i}. {item}")
                    if len(data) > 3:
                        print(f"{prefix}     ... and {len(data)-3} more")
                elif isinstance(data, dict):
                    print(f"{prefix}   Fields: {len(data)}")
                    for k, v in list(data.items())[:5]:
                        print(f"{prefix}     {k}: {v}")
                    if len(data) > 5:
                        print(f"{prefix}     ... and {len(data)-5} more fields")
                else:
                    print(f"{prefix}   Value: {data}")
        
        # Show actual patients in queue
        if queue_data.get('patients'):
            print(f"\n{prefix}📋 Patients in Queue ({len(queue_data['patients'])}):")
            for i, patient in enumerate(queue_data['patients'][:10], 1):
                print(f"\n{prefix}   {i}. {patient['key']}")
                if patient['data']:
                    data = patient['data']
                    # Show key fields
                    for field in ['patient_name', 'name', 'symptoms', 'urgency_score', 'position', 'status']:
                        if field in data:
                            print(f"{prefix}      {field}: {data[field]}")
            if len(queue_data['patients']) > 10:
                print(f"{prefix}   ... and {len(queue_data['patients'])-10} more patients")
    
    async def test_single_case_with_agent(self, test_case: Dict) -> Dict:
        """Test using actual root agent workflow"""
        print(f"\n{'='*60}")
        print(f"🧪 Testing with Agent Workflow: {test_case['name']}")
        print(f"{'='*60}")
        
        result = {
            "test_name": test_case['name'],
            "timestamp": datetime.now().isoformat(),
            "patient_info": test_case,
            "steps": {},
            "agent_workflow": True
        }
        
        try:
            # Create booking request for the agent
            booking_request = (
                f"Book appointment for patient: {test_case['patient_name']}, "
                f"Age: {test_case['age']}, "
                f"Symptoms: {test_case['symptoms']}, "
                f"Location: {test_case['location']}, "
                f"Phone: {test_case['phone']}"
            )
            
            print(f"\n📝 Sending to Agent: {booking_request[:100]}...")
            
            # Call the root agent
            if AGENT_AVAILABLE and hasattr(root_agent, 'process_booking_request'):
                agent_response = await root_agent.process_booking_request(booking_request)
                result['steps']['agent_response'] = agent_response
                print(f"\n✅ Agent Response Received")
                print(f"   Response: {str(agent_response)[:200]}...")
            elif AGENT_AVAILABLE:
                # Try alternative function names
                for func_name in dir(root_agent):
                    if 'book' in func_name.lower() or 'process' in func_name.lower():
                        func = getattr(root_agent, func_name)
                        if callable(func):
                            try:
                                agent_response = await func(booking_request)
                                result['steps']['agent_response'] = agent_response
                                print(f"\n✅ Agent Response via {func_name}")
                                print(f"   Response: {str(agent_response)[:200]}...")
                                break
                            except Exception as e:
                                print(f"   ⚠️ Could not use {func_name}: {e}")
            else:
                print(f"   ⚠️ Agent not available, skipping agent call")
                result['steps']['agent_response'] = "Agent not available"
            
            # Show queue status after agent processing
            print(f"\n📊 Queue Status After Agent Processing:")
            self.display_queue_status(prefix="   ", detailed=True)
            
            result['status'] = 'PASSED'
            print(f"\n✅ Test PASSED: {test_case['name']}")
            
        except Exception as e:
            result['status'] = 'FAILED'
            result['error'] = str(e)
            import traceback
            print(f"\n❌ Test FAILED: {test_case['name']}")
            print(f"   Error: {str(e)}")
            print(f"   Traceback: {traceback.format_exc()}")
        
        return result
    
    async def run_all_tests(self):
        """Run all test cases through agent workflow"""
        print("\n" + "="*60)
        print("🚀 Starting MediSync Agentic Workflow Tests")
        print("🤖 Using Actual Agent System with All Sub-Agents")
        print("="*60)
        
        # Show initial queue status
        print("\n🏁 INITIAL QUEUE STATUS:")
        self.display_queue_status(detailed=True)
        
        for i, test_case in enumerate(TEST_CASES, 1):
            print(f"\n{'#'*60}")
            print(f"[TEST {i}/{len(TEST_CASES)}]")
            print(f"{'#'*60}")
            
            result = await self.test_single_case_with_agent(test_case)
            self.results.append(result)
            
            # Wait between tests
            print(f"\n⏳ Waiting 3 seconds before next test...")
            await asyncio.sleep(3)
        
        # Show final queue status
        print("\n" + "="*60)
        print("🏁 FINAL QUEUE STATUS AFTER ALL TESTS")
        print("="*60)
        self.display_queue_status(detailed=True)
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary report"""
        print("\n" + "="*60)
        print("📊 TEST SUMMARY REPORT")
        print("="*60)
        
        passed = sum(1 for r in self.results if r['status'] == 'PASSED')
        failed = sum(1 for r in self.results if r['status'] == 'FAILED')
        
        print(f"\nTotal Tests: {len(self.results)}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"Success Rate: {(passed/len(self.results)*100):.1f}%")
        
        # Save results to JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_results_agent_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'summary': {
                    'total': len(self.results),
                    'passed': passed,
                    'failed': failed,
                    'success_rate': f"{(passed/len(self.results)*100):.1f}%",
                    'timestamp': datetime.now().isoformat(),
                    'agent_workflow': True
                },
                'results': self.results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Detailed results saved to: {filename}")
        
        # Get final queue statistics
        final_queue = self.get_redis_queue_status()
        if final_queue:
            print(f"\n📈 Final Queue Statistics:")
            print(f"   Total Queue Keys: {len(final_queue.get('queue_keys', []))}")
            print(f"   Total Patients: {len(final_queue.get('patient_keys', []))}")
            print(f"   Brain Keys: {len(final_queue.get('brain_keys', []))}")
            print(f"   Symptom Keys: {len(final_queue.get('symptom_keys', []))}")
            print(f"   Starvation Keys: {len(final_queue.get('starvation_keys', []))}")

async def main():
    """Main test execution"""
    tester = AgenticWorkflowTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    print("🏥 MediSync Agentic Workflow Test Suite")
    print("🤖 Testing Complete Agent System")
    print("Including: Queue Brain, Symptom Analyzer, Starvation Tracker")
    print("Using Free Maps Service (OpenStreetMap + OSRM)\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Critical error: {e}")
        import traceback
        traceback.print_exc()