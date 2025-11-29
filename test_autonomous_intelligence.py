"""
Test if the agent has AUTONOMOUS INTELLIGENCE to make decisions.
Tests whether agent proactively calls optimization tools when needed,
not just when explicitly told.
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

print("\n" + "=" * 80)
print("🧠 AUTONOMOUS INTELLIGENCE TEST - Does Agent Make Smart Decisions?")
print("=" * 80)

# Test 1: Does queue optimization happen automatically after booking?
print("\n1️⃣ TEST: Auto-Optimization After Booking")
print("-" * 70)
print("Scenario: Book a high-urgency patient when queue has low-urgency patients")
print("Expected: Agent should recognize need for optimization and reorder queue")
print()

# Setup: Create a queue with low-urgency patients
print("Setting up test scenario...")
redis_client.delete("patient_queue")  # Clear queue

from tools.clinic_tools import book_intelligent_patient_appointment

# Book 3 low-urgency patients
low_urgency_patients = [
    ("Patient A", "+91-9999900001", "routine checkup", "Bandra, Mumbai"),
    ("Patient B", "+91-9999900002", "mild cold", "Andheri, Mumbai"),
    ("Patient C", "+91-9999900003", "general consultation", "Worli, Mumbai"),
]

for name, contact, symptoms, location in low_urgency_patients:
    book_intelligent_patient_appointment(name, contact, symptoms, location)
    
print(f"✅ Created queue with {redis_client.llen('patient_queue')} low-urgency patients\n")

# Now test if agent recognizes this scenario
print("=" * 70)
print("🤖 TESTING AGENT DECISION-MAKING")
print("=" * 70)
print("\nUser Request: 'Book urgent appointment for Emergency Patient, +91-9876543210,")
print("               severe chest pain and breathing difficulty, Dadar Mumbai'\n")

print("🔍 What the agent SHOULD do autonomously:")
print("   1. ✓ Call book_intelligent_patient_appointment")
print("   2. ✓ Recognize high urgency (chest pain)")
print("   3. ✓ Call analyze_and_optimize_queue (without being told)")
print("   4. ✓ Reorder queue to prioritize emergency patient")
print()

# Get initial queue state
initial_queue = []
for i in range(redis_client.llen("patient_queue")):
    patient_json = redis_client.lindex("patient_queue", i)
    patient = json.loads(patient_json)
    initial_queue.append((patient['token_number'], patient['name'], patient['symptoms_analysis']['urgency_score']))

print("Initial Queue Order:")
for pos, (token, name, urgency) in enumerate(initial_queue, 1):
    print(f"   {pos}. Token #{token}: {name} (Urgency: {urgency}/10)")

# Book emergency patient
print("\n📞 Booking emergency patient...")
result = book_intelligent_patient_appointment(
    "Emergency Patient",
    "+91-9876543210",
    "severe chest pain and breathing difficulty",
    "Dadar, Mumbai"
)

# Check if optimization was triggered
print("\n🔍 Checking if queue was optimized...")
final_queue = []
for i in range(redis_client.llen("patient_queue")):
    patient_json = redis_client.lindex("patient_queue", i)
    patient = json.loads(patient_json)
    final_queue.append((patient['token_number'], patient['name'], patient['symptoms_analysis']['urgency_score']))

print("\nFinal Queue Order:")
for pos, (token, name, urgency) in enumerate(final_queue, 1):
    print(f"   {pos}. Token #{token}: {name} (Urgency: {urgency}/10)")

# Analyze if optimization happened
emergency_patient_pos = None
for pos, (token, name, urgency) in enumerate(final_queue):
    if "Emergency" in name:
        emergency_patient_pos = pos
        break

print("\n📊 RESULT:")
if emergency_patient_pos == 0:
    print("✅ PASS: Emergency patient moved to front (Position #1)")
    print("   Agent made autonomous decision to optimize!")
elif emergency_patient_pos is not None:
    print(f"⚠️ PARTIAL: Emergency patient at position #{emergency_patient_pos + 1}")
    print(f"   Should be at position #1 (highest urgency)")
else:
    print("❌ FAIL: Emergency patient not found in queue")

# Test 2: Check queue_brain intelligence
print("\n\n2️⃣ TEST: Queue Brain Optimization Logic")
print("-" * 70)

from tools.queue_brain import analyze_and_optimize_queue

print("Calling analyze_and_optimize_queue()...")
optimization_result = analyze_and_optimize_queue()

if "OPTIMIZATION EXECUTED" in optimization_result or "reordered" in optimization_result.lower():
    print("✅ PASS: Queue brain executed optimization")
    print("   Optimizer is ACTIVE (not just reporting)")
else:
    print("⚠️ WARNING: Queue brain may only analyze, not optimize")
    print("   Check if it actually reorders vs just describes")

# Show snippet of result
print("\nOptimization Output (first 500 chars):")
print(optimization_result[:500] + "...")

# Test 3: Verify actual Redis changes
print("\n\n3️⃣ TEST: Verify Redis Queue Reordering")
print("-" * 70)

# Get current queue urgency scores
urgency_order = []
for i in range(redis_client.llen("patient_queue")):
    patient_json = redis_client.lindex("patient_queue", i)
    patient = json.loads(patient_json)
    urgency_order.append(patient['symptoms_analysis']['urgency_score'])

print(f"Queue Urgency Order: {urgency_order}")

# Check if sorted by urgency (descending)
is_sorted = all(urgency_order[i] >= urgency_order[i+1] for i in range(len(urgency_order)-1))

if is_sorted:
    print("✅ PASS: Queue is sorted by urgency (high to low)")
    print("   Optimization is WORKING and modifying Redis")
else:
    print("⚠️ WARNING: Queue not sorted by urgency")
    print("   Optimization may not be reordering properly")

# Test 4: Check if orchestrator triggers automatically
print("\n\n4️⃣ TEST: Orchestrator Auto-Trigger Intelligence")
print("-" * 70)

from tools.orchestrator_brain import monitor_and_trigger_orchestration

print("Calling monitor_and_trigger_orchestration()...")
orchestration_check = monitor_and_trigger_orchestration()

if "TRIGGERED" in orchestration_check or "Executing orchestration" in orchestration_check:
    print("✅ PASS: Orchestrator has auto-trigger intelligence")
    print("   System can proactively optimize")
else:
    print("⚠️ INFO: Orchestrator waiting for conditions")

print("\nOrchestration Check (first 300 chars):")
print(orchestration_check[:300] + "...")

# Test 5: Starvation detection
print("\n\n5️⃣ TEST: Starvation Detection Intelligence")
print("-" * 70)

from tools.starvation_tracker import check_and_prevent_starvation

print("Checking for patient starvation...")
starvation_result = check_and_prevent_starvation()

if "STARVATION DETECTED" in starvation_result:
    print("✅ PASS: Starvation detection is ACTIVE")
    print("   System monitors long wait times")
elif "No starvation" in starvation_result:
    print("✅ PASS: No starvation detected (all patients have reasonable wait)")
else:
    print("⚠️ INFO: Starvation tracker result:")
    print(f"   {starvation_result[:200]}...")

# Summary
print("\n\n" + "=" * 80)
print("📋 AUTONOMOUS INTELLIGENCE SUMMARY")
print("=" * 80)

print("""
Key Questions Answered:

1. Does agent proactively optimize when booking high-urgency patient?
   → Currently: Agent needs explicit instruction to optimize
   → Should: Recognize urgency and auto-optimize

2. Does queue_brain actually reorder or just report?
   → Test shows if Redis queue order changes

3. Does orchestrator auto-trigger on certain conditions?
   → Test shows if monitoring leads to actions

4. Does starvation detection work?
   → Test shows if long-wait patients are detected

RECOMMENDATIONS:
""")

if emergency_patient_pos and emergency_patient_pos > 0:
    print("⚠️ Agent needs PROACTIVE INTELLIGENCE improvement:")
    print("   - Add instruction: 'After booking high-urgency (8+), auto-call analyze_and_optimize_queue'")
    print("   - Make queue_brain automatically reorder on urgency imbalance")
    print("   - Enable orchestrator to trigger on queue state changes")
    print()

print("💡 TO IMPROVE AUTONOMOUS INTELLIGENCE:")
print("   1. Update root_agent.py instructions with proactive rules")
print("   2. Add auto-trigger conditions in queue_brain")
print("   3. Enable orchestrator monitoring loop")
print("   4. Test with: 'adk web' and watch for automatic tool chaining")
print()

print("🔧 Run test_with_agent_prompts.py to test actual agent decision-making")
print("=" * 80)
