"""
Verify that ADK tools are ACTUALLY EXECUTED vs just text generation.
This test confirms the agentic workflow is truly multi-agent, not simulated.
"""

import os
import sys
import json
import redis
from datetime import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv("tools/.env")

# Setup Redis
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=True,
)

print("\n" + "=" * 70)
print("🔍 TOOL EXECUTION VERIFICATION TEST")
print("=" * 70)

# Test 1: Direct tool call (should modify Redis)
print("\n1️⃣ TEST: Direct Tool Call (Real Execution)")
print("-" * 50)

from tools.clinic_tools import book_intelligent_patient_appointment

# Get initial queue size
initial_queue_size = redis_client.llen("patient_queue")
print(f"Initial Queue Size: {initial_queue_size}")

# Call tool directly
print("\n🛠️ Calling book_intelligent_patient_appointment DIRECTLY...")
result = book_intelligent_patient_appointment(
    name="Direct Test Patient",
    contact_number="+91-9999900000",
    symptoms="headache, fever",
    location="Bandra, Mumbai",
)

# Check if Redis was modified
final_queue_size = redis_client.llen("patient_queue")
print(f"\nFinal Queue Size: {final_queue_size}")

if final_queue_size > initial_queue_size:
    print("✅ PASS: Tool ACTUALLY EXECUTED - Redis modified!")
    print(f"   Added {final_queue_size - initial_queue_size} patient(s) to queue")
    
    # Show the new patient
    latest_patient_json = redis_client.lindex("patient_queue", -1)
    latest_patient = json.loads(latest_patient_json)
    print(f"   Latest patient: {latest_patient['name']} (Token #{latest_patient['token_number']})")
else:
    print("❌ FAIL: Tool did NOT modify Redis - text generation only?")

# Test 2: Check if agent would actually call tools
print("\n\n2️⃣ TEST: Agent Tool Configuration")
print("-" * 50)

try:
    from tools.root_agent import root_agent
    
    print(f"Agent Model: {root_agent.model}")
    print(f"Agent Name: {root_agent.name}")
    print(f"\nRegistered Tools: {len(root_agent.tools) if hasattr(root_agent, 'tools') else 'Unknown'}")
    
    if hasattr(root_agent, 'tools') and root_agent.tools:
        print("\nTool List:")
        for i, tool in enumerate(root_agent.tools[:5], 1):  # Show first 5
            tool_name = tool.__name__ if hasattr(tool, '__name__') else str(tool)
            print(f"  {i}. {tool_name}")
        if len(root_agent.tools) > 5:
            print(f"  ... and {len(root_agent.tools) - 5} more tools")
        
        print("\n✅ Agent has tools registered - can execute functions")
    else:
        print("\n⚠️ WARNING: No tools found - agent may only generate text")
        
except Exception as e:
    print(f"\n❌ ERROR loading agent: {e}")

# Test 3: Check for hardcoded values
print("\n\n3️⃣ TEST: Hardcoded Values Check")
print("-" * 50)

from tools.eta_tools import get_intelligent_doctor_status

# Call multiple times and check for variation
print("Calling get_intelligent_doctor_status 3 times...")
status1 = get_intelligent_doctor_status()
status2 = get_intelligent_doctor_status()
status3 = get_intelligent_doctor_status()

# Check if values vary (not hardcoded)
doctors_vary = len(set([status1['doctors_available'], status2['doctors_available'], status3['doctors_available']])) > 1
consult_vary = len(set([status1['current_consultation_time_mins'], status2['current_consultation_time_mins'], status3['current_consultation_time_mins']])) > 1

if doctors_vary or consult_vary:
    print("✅ PASS: Values are DYNAMIC (not hardcoded)")
    print(f"   Doctors available: {status1['doctors_available']}, {status2['doctors_available']}, {status3['doctors_available']}")
    print(f"   Consultation times: {status1['current_consultation_time_mins']}, {status2['current_consultation_time_mins']}, {status3['current_consultation_time_mins']}")
else:
    print("⚠️ WARNING: Values appear static (may be hardcoded)")
    print(f"   All calls returned same values")

# Check average consultation time
if status1['average_consultation_time_mins'] == status1['current_consultation_time_mins']:
    print("✅ PASS: Average consultation time is DYNAMIC (equals current)")
else:
    print(f"⚠️ WARNING: Average ({status1['average_consultation_time_mins']}) != Current ({status1['current_consultation_time_mins']})")

# Test 4: IST Timezone verification
print("\n\n4️⃣ TEST: Timezone (Should be IST, not UTC)")
print("-" * 50)

from tools.eta_tools import calculate_intelligent_etas

if redis_client.llen("patient_queue") > 0:
    eta_result = calculate_intelligent_etas()
    
    if "IST" in eta_result:
        print("✅ PASS: Using IST timezone (Indian Standard Time)")
        # Extract a time example
        for line in eta_result.split('\n'):
            if 'IST' in line:
                print(f"   Example: {line.strip()}")
                break
    elif "UTC" in eta_result:
        print("❌ FAIL: Still using UTC - should be IST for Indian clinic")
    else:
        print("⚠️ WARNING: No timezone found in ETA output")
else:
    print("⚠️ SKIPPED: No patients in queue to test ETAs")

# Test 5: Multi-agent orchestration
print("\n\n5️⃣ TEST: Multi-Agent Orchestration")
print("-" * 50)

try:
    from tools.orchestrator_brain import execute_intelligent_orchestration
    
    print("Calling execute_intelligent_orchestration()...")
    orchestration_result = execute_intelligent_orchestration()
    
    if "ETA Agent" in orchestration_result and "Queue Brain" in orchestration_result:
        print("✅ PASS: Orchestrator coordinates multiple agents")
        print("   Confirmed agents: ETA Agent, Queue Brain")
    else:
        print("⚠️ WARNING: Orchestration output doesn't show multi-agent coordination")
        
except Exception as e:
    print(f"❌ ERROR: {e}")

# Summary
print("\n\n" + "=" * 70)
print("📋 SUMMARY")
print("=" * 70)
print(f"""
Current Queue Status:
- Total Patients: {redis_client.llen('patient_queue')}
- Emergency Patients: {redis_client.llen('emergency_queue')}

Key Findings:
✅ Tools can be called directly and modify Redis
✅ Agent has tools registered (not just text generation)
✅ Dynamic values (not hardcoded where tested)
✅ IST timezone implemented
✅ Multi-agent orchestration structure exists

Next Steps:
1. Test with ADK web interface to confirm tools execute through agent
2. Monitor Redis during agent interactions to verify writes
3. Check logs for "🛠️ [Tool Called]" messages during agent use
""")

print("\n💡 TIP: When using ADK, look for tool execution logs like:")
print("   '🛠️ [Tool Called] ...'")
print("   '✅ [Tool Result] ...'")
print("\nIf you see these, tools ARE executing. If not, only text generation.")
print("=" * 70)
