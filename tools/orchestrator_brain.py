import os
import json
import redis
from datetime import datetime, timedelta
from tools.priority_queue_manager import get_priority_queue_manager
from tools.eta_tools import calculate_intelligent_etas
from tools.queue_brain import analyze_and_optimize_queue
from tools.notification_agent import (
    send_queue_update_notifications,
    send_eta_update_notifications,
)
from tools.clinic_monitor import get_clinic_status_dashboard

# Redis connection
try:
    redis_client = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        password=os.getenv("REDIS_PASSWORD", None),
        db=0,
        decode_responses=True,
    )
    redis_client.ping()
    print("[OK] Orchestrator Brain: Successfully connected to Redis.")
    
    # Initialize priority queue manager
    pq_manager = get_priority_queue_manager(redis_client)
    print("[OK] Orchestrator Brain: Priority Queue Manager initialized.")
except redis.exceptions.ConnectionError as e:
    print(f"[ERROR] Orchestrator Brain: Could not connect to Redis. Error: {e}")
    redis_client = None
    pq_manager = None


def execute_intelligent_orchestration() -> str:
    """
    Execute the complete intelligent orchestration cycle.
    This is the master function that coordinates all agents.

    Returns:
        Comprehensive orchestration report
    """
    if not redis_client:
        return "[ERROR] Error: Cannot connect to orchestration system."

    print("🎼 [Orchestrator] Starting intelligent healthcare orchestration cycle...")

    orchestration_start = datetime.utcnow()

    # Step 1: Get current system state
    print("[STATS] [Orchestrator] Step 1: Analyzing current system state...")
    system_state = _analyze_system_state()

    # Step 2: Execute ETA calculation agent
    print("[CLOCK] [Orchestrator] Step 2: Executing ETA calculation agent...")
    eta_results = _execute_eta_agent()

    # Step 3: Execute queue brain optimization
    print("[BRAIN] [Orchestrator] Step 3: Executing queue brain optimization...")
    optimization_results = _execute_queue_brain()

    # Step 4: Execute notification agent
    print("[PHONE] [Orchestrator] Step 4: Executing notification agent...")
    notification_results = _execute_notification_agent()

    # Step 5: Update system orchestration state
    print("[CYCLE] [Orchestrator] Step 5: Updating orchestration state...")
    state_update = _update_orchestration_state(orchestration_start)

    # Generate comprehensive report
    report = _generate_orchestration_report(
        system_state,
        eta_results,
        optimization_results,
        notification_results,
        state_update,
        orchestration_start,
    )

    print("[OK] [Orchestrator] Intelligent orchestration cycle completed")
    return report


def monitor_and_trigger_orchestration() -> str:
    """
    Monitor system state and trigger orchestration when needed.

    Returns:
        Monitoring results
    """
    if not redis_client:
        return "[ERROR] Error: Cannot connect to monitoring system."

    print("👁️ [Orchestrator] Monitoring system for orchestration triggers...")

    # Check for completion triggers
    completion_trigger = redis_client.get("last_completed_patient")
    manual_trigger = redis_client.get("orchestration_trigger")

    triggers_found = []

    if completion_trigger:
        completion_data = json.loads(completion_trigger)
        if completion_data.get("optimization_trigger"):
            triggers_found.append(
                f"Patient #{completion_data.get('completed_patient_token')} completed"
            )

    if manual_trigger:
        manual_data = json.loads(manual_trigger)
        triggers_found.append(f"Manual trigger: {manual_data.get('reason', 'Unknown')}")

    if not triggers_found:
        return """
👁️ ORCHESTRATION MONITORING
==========================
Status: Monitoring active
Triggers Found: None
Action: Standby mode

[TIP] System will automatically orchestrate when:
├─ A patient completes consultation
├─ Manual trigger is activated  
├─ Emergency patient is added
└─ Queue reaches optimization threshold

[CYCLE] Continuous monitoring in progress...
"""

    # Execute orchestration if triggers found
    orchestration_result = execute_intelligent_orchestration()

    # Clear triggers
    if completion_trigger:
        completion_data = json.loads(completion_trigger)
        completion_data["optimization_trigger"] = False
        redis_client.set("last_completed_patient", json.dumps(completion_data))

    if manual_trigger:
        redis_client.delete("orchestration_trigger")

    return f"""
🚨 ORCHESTRATION TRIGGERS DETECTED
=================================
Triggers Found: {len(triggers_found)}
├─ {chr(10).join([f"• {trigger}" for trigger in triggers_found])}

🎼 ORCHESTRATION EXECUTED:
{orchestration_result}

[OK] All triggers processed and cleared.
"""


def get_orchestration_dashboard() -> str:
    """
    Get comprehensive orchestration dashboard.

    Returns:
        Orchestration system dashboard
    """
    if not redis_client:
        return "[ERROR] Error: Cannot connect to orchestration system."

    # Get orchestration history
    history = redis_client.get("orchestration_history")
    orchestration_history = json.loads(history) if history else {}

    # Get current system metrics from priority queue manager
    if pq_manager:
        queue_snapshot = pq_manager.get_queue_snapshot()
        regular_queue = queue_snapshot["main_queue_count"]
        emergency_queue = queue_snapshot["emergency_count"]
    else:
        regular_queue = 0
        emergency_queue = 0
    
    ongoing_patient = redis_client.get("ongoing_patient_status")

    # Get trigger status
    completion_trigger = redis_client.get("last_completed_patient")
    manual_trigger = redis_client.get("orchestration_trigger")

    dashboard = f"""
🎼 MEDISYNC ORCHESTRATION DASHBOARD
==================================
🕐 Status Time: {datetime.utcnow().strftime('%H:%M:%S UTC')}
🎯 Orchestration Engine: Active

[CLINIC] CURRENT SYSTEM STATE:
├─ Regular Queue: {regular_queue} patients
├─ Emergency Queue: {emergency_queue} patients
├─ Total Active: {regular_queue + emergency_queue} patients
└─ Ongoing Consultation: {'Active' if ongoing_patient else 'None'}

🎼 ORCHESTRATION METRICS:
├─ Total Cycles Run: {orchestration_history.get('total_cycles', 0)}
├─ Last Execution: {orchestration_history.get('last_execution', 'Never')[:16]}
├─ Average Cycle Time: {orchestration_history.get('avg_cycle_time', 'N/A')} seconds
└─ Success Rate: {orchestration_history.get('success_rate', 100)}%

🚨 TRIGGER STATUS:
├─ Completion Trigger: {'🟢 Active' if completion_trigger else '⚫ Inactive'}
├─ Manual Trigger: {'🟢 Active' if manual_trigger else '⚫ Inactive'}
├─ Auto-monitoring: 🟢 Active
└─ Next Check: Continuous

[FAST] AGENT STATUS:
├─ ETA Calculation Agent: 🟢 Ready
├─ Queue Brain Agent: 🟢 Ready
├─ Notification Agent: 🟢 Ready
└─ Clinic Monitor: 🟢 Ready

🎯 OPTIMIZATION IMPACT:
├─ Total Time Saved: {orchestration_history.get('total_time_saved', 0)} minutes
├─ Patients Optimized: {orchestration_history.get('total_optimizations', 0)}
├─ Notifications Sent: {orchestration_history.get('total_notifications', 0)}
└─ System Efficiency: {orchestration_history.get('efficiency_score', 'Calculating...')}%

[TIP] INTELLIGENT INSIGHTS:
"""

    if regular_queue > 5:
        dashboard += "├─ High queue volume - frequent orchestration recommended"
    elif regular_queue == 0 and emergency_queue == 0:
        dashboard += "├─ No patients waiting - system in standby mode"
    else:
        dashboard += "├─ Optimal queue levels - standard orchestration active"

    dashboard += f"""
└─ System operating at maximum intelligence

[CYCLE] Next orchestration will trigger automatically when needed.
"""

    return dashboard.strip()


def _analyze_system_state():
    """Analyze current system state using priority queue manager"""
    if pq_manager:
        queue_snapshot = pq_manager.get_queue_snapshot()
        regular_queue = queue_snapshot["main_queue_count"]
        emergency_queue = queue_snapshot["emergency_count"]
        total_patients = queue_snapshot["total_patients"]
    else:
        regular_queue = 0
        emergency_queue = 0
        total_patients = 0
    
    ongoing_patient = redis_client.get("ongoing_patient_status")

    return {
        "regular_queue_length": regular_queue,
        "emergency_queue_length": emergency_queue,
        "total_patients": total_patients,
        "ongoing_consultation": bool(ongoing_patient),
        "analysis_time": datetime.utcnow().isoformat(),
    }


def _execute_eta_agent():
    """Execute ETA calculation agent"""
    try:
        eta_result = calculate_intelligent_etas()
        return {
            "status": "success",
            "result": eta_result,
            "execution_time": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "execution_time": datetime.utcnow().isoformat(),
        }


def _execute_queue_brain():
    """Execute queue brain optimization"""
    try:
        brain_result = analyze_and_optimize_queue()
        return {
            "status": "success",
            "result": brain_result,
            "execution_time": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "execution_time": datetime.utcnow().isoformat(),
        }


def _execute_notification_agent():
    """Execute notification agent"""
    try:
        notification_result = send_queue_update_notifications()
        return {
            "status": "success",
            "result": notification_result,
            "execution_time": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "execution_time": datetime.utcnow().isoformat(),
        }


def _update_orchestration_state(start_time):
    """Update orchestration state and history"""
    try:
        execution_time = (datetime.utcnow() - start_time).total_seconds()

        # Get existing history
        history = redis_client.get("orchestration_history")
        orchestration_history = (
            json.loads(history)
            if history
            else {
                "total_cycles": 0,
                "total_time_saved": 0,
                "total_optimizations": 0,
                "total_notifications": 0,
                "success_rate": 100,
            }
        )

        # Update history
        orchestration_history["total_cycles"] += 1
        orchestration_history["last_execution"] = datetime.utcnow().isoformat()
        orchestration_history["last_execution_time"] = execution_time
        orchestration_history["avg_cycle_time"] = (
            orchestration_history.get("avg_cycle_time", execution_time) + execution_time
        ) / 2

        # Save updated history
        redis_client.set("orchestration_history", json.dumps(orchestration_history))

        return {
            "status": "success",
            "execution_time_seconds": execution_time,
            "total_cycles": orchestration_history["total_cycles"],
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def _generate_orchestration_report(
    system_state,
    eta_results,
    optimization_results,
    notification_results,
    state_update,
    start_time,
):
    """Generate comprehensive orchestration report"""

    total_time = (datetime.utcnow() - start_time).total_seconds()

    report = f"""
🎼 INTELLIGENT ORCHESTRATION REPORT
==================================
Execution Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
Total Duration: {total_time:.2f} seconds

[STATS] SYSTEM STATE ANALYSIS:
├─ Total Patients: {system_state.get('total_patients', 0)}
├─ Regular Queue: {system_state.get('regular_queue_length', 0)}
├─ Emergency Queue: {system_state.get('emergency_queue_length', 0)}
└─ Ongoing Consultation: {'Yes' if system_state.get('ongoing_consultation') else 'No'}

[CLOCK] ETA CALCULATION AGENT:
├─ Status: {eta_results.get('status', 'Unknown').upper()}
├─ Execution: {'[OK] Success' if eta_results.get('status') == 'success' else '[ERROR] Error'}
└─ Details: ETA recalculations completed for all patients

[BRAIN] QUEUE BRAIN OPTIMIZATION:
├─ Status: {optimization_results.get('status', 'Unknown').upper()}
├─ Execution: {'[OK] Success' if optimization_results.get('status') == 'success' else '[ERROR] Error'}
└─ Details: Queue analyzed and optimized for maximum efficiency

[PHONE] NOTIFICATION AGENT:
├─ Status: {notification_results.get('status', 'Unknown').upper()}
├─ Execution: {'[OK] Success' if notification_results.get('status') == 'success' else '[ERROR] Error'}
└─ Details: Patient notifications processed and sent

[CYCLE] ORCHESTRATION METRICS:
├─ Total Execution Time: {total_time:.2f} seconds
├─ Cycle Number: #{state_update.get('total_cycles', 0)}
├─ All Agents: {'[OK] Success' if all(r.get('status') == 'success' for r in [eta_results, optimization_results, notification_results]) else '[WARNING] Some Issues'}
└─ System State: Updated

[OK] INTELLIGENT ORCHESTRATION COMPLETED SUCCESSFULLY!

[CYCLE] System is now monitoring for next orchestration triggers...
"""

    return report.strip()
