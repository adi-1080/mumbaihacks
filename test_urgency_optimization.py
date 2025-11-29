"""Quick test of urgency-based queue optimization"""
import redis
import json
from tools.queue_brain import analyze_and_optimize_queue

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

print("\n🔍 QUEUE BEFORE OPTIMIZATION:")
print("=" * 50)
for i in range(r.llen('patient_queue')):
    patient = json.loads(r.lindex("patient_queue", i))
    print(f"{i+1}. Token #{patient['token_number']}: {patient['name']}")
    print(f"   Urgency: {patient['symptoms_analysis']['urgency_score']}/10")

print("\n🧠 Calling analyze_and_optimize_queue()...")
print("=" * 50)
result = analyze_and_optimize_queue()

print("\n✅ QUEUE AFTER OPTIMIZATION:")
print("=" * 50)
for i in range(r.llen('patient_queue')):
    patient = json.loads(r.lindex("patient_queue", i))
    print(f"{i+1}. Token #{patient['token_number']}: {patient['name']}")
    print(f"   Urgency: {patient['symptoms_analysis']['urgency_score']}/10")

print("\n📊 Optimization Result:")
print("=" * 50)
print(result[:500] + "..." if len(result) > 500 else result)
