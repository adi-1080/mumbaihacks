"""
Final System Verification Script
Tests all migrated components and confirms no legacy dependencies
"""

import redis
import json
from datetime import datetime

# Colors for output
GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def print_header(text):
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}{text.center(70)}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✅ {text}{RESET}")

def print_error(text):
    print(f"{RED}❌ {text}{RESET}")

def print_info(text):
    print(f"{YELLOW}ℹ️  {text}{RESET}")

def verify_no_legacy_redis():
    """Verify no data in old Redis lists"""
    try:
        redis_client = redis.Redis(decode_responses=True)
        
        patient_queue_len = redis_client.llen("patient_queue")
        emergency_queue_len = redis_client.llen("emergency_queue")
        
        if patient_queue_len == 0 and emergency_queue_len == 0:
            print_success("No legacy Redis list data found")
            return True
        else:
            print_error(f"Legacy data found! patient_queue: {patient_queue_len}, emergency_queue: {emergency_queue_len}")
            return False
    except Exception as e:
        print_error(f"Redis check failed: {e}")
        return False

def verify_priority_queue_manager():
    """Verify priority queue manager is working"""
    try:
        from tools.priority_queue_manager import get_priority_queue_manager
        import redis
        
        redis_client = redis.Redis(decode_responses=True)
        pq_manager = get_priority_queue_manager(redis_client)
        
        # Test basic operations
        snapshot = pq_manager.get_queue_snapshot()
        
        print_success("Priority Queue Manager initialized")
        print_info(f"  Total patients: {snapshot['total_patients']}")
        print_info(f"  Emergency queue: {snapshot['emergency_count']}")
        print_info(f"  Main queue: {snapshot['main_queue_count']}")
        
        return True
    except Exception as e:
        print_error(f"Priority Queue Manager check failed: {e}")
        return False

def verify_file_imports():
    """Verify all updated files can be imported"""
    files_to_check = [
        ("tools.clinic_monitor", "Clinic Monitor"),
        ("tools.emergency_handler", "Emergency Handler"),
        ("tools.eta_tools", "ETA Tools"),
        ("tools.orchestrator_brain", "Orchestrator Brain"),
        ("tools.notification_agent", "Notification Agent"),
        ("tools.queue_brain", "Queue Brain"),
        ("tools.queue_intelligence", "Queue Intelligence"),
        ("tools.queue_reorder_tools", "Queue Reorder Tools"),
        ("tools.clinic_tools_priority_queue", "Clinic Tools (Priority Queue)"),
    ]
    
    all_success = True
    for module_name, display_name in files_to_check:
        try:
            __import__(module_name)
            print_success(f"{display_name} imports successfully")
        except Exception as e:
            print_error(f"{display_name} import failed: {e}")
            all_success = False
    
    return all_success

def verify_no_old_clinic_tools():
    """Verify old clinic_tools.py is not imported"""
    try:
        with open("tools/root_agent.py", "r", encoding="utf-8") as f:
            content = f.read()
            
        if "from tools.clinic_tools import" in content:
            print_error("Old clinic_tools.py is still imported in root_agent.py!")
            return False
        
        if "from tools.clinic_tools_priority_queue import" in content:
            print_success("Correct clinic_tools_priority_queue.py is imported")
            return True
        
        print_error("No clinic tools imported in root_agent.py!")
        return False
    except Exception as e:
        print_error(f"File check failed: {e}")
        return False

def check_pq_manager_in_files():
    """Check if all files have priority queue manager"""
    files_to_check = {
        "tools/clinic_monitor.py": "get_priority_queue_manager",
        "tools/emergency_handler.py": "get_priority_queue_manager",
        "tools/eta_tools.py": "get_priority_queue_manager",
        "tools/notification_agent.py": "get_priority_queue_manager",
        "tools/queue_intelligence.py": "get_priority_queue_manager",
        "tools/queue_reorder_tools.py": "get_priority_queue_manager",
    }
    
    all_success = True
    for file_path, import_name in files_to_check.items():
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            if import_name in content:
                print_success(f"{file_path.split('/')[-1]} has priority queue manager")
            else:
                print_error(f"{file_path.split('/')[-1]} missing priority queue manager!")
                all_success = False
        except Exception as e:
            print_error(f"Check failed for {file_path}: {e}")
            all_success = False
    
    return all_success

def main():
    print_header("MEDISYNC PRIORITY QUEUE SYSTEM - FINAL VERIFICATION")
    
    results = {}
    
    # Test 1: Legacy Redis
    print_header("TEST 1: Legacy Redis Data Check")
    results["no_legacy_data"] = verify_no_legacy_redis()
    
    # Test 2: Priority Queue Manager
    print_header("TEST 2: Priority Queue Manager")
    results["pq_manager_works"] = verify_priority_queue_manager()
    
    # Test 3: File Imports
    print_header("TEST 3: Updated File Imports")
    results["imports_work"] = verify_file_imports()
    
    # Test 4: Old Clinic Tools
    print_header("TEST 4: Old Clinic Tools Not Used")
    results["no_old_tools"] = verify_no_old_clinic_tools()
    
    # Test 5: Priority Queue Manager in Files
    print_header("TEST 5: Priority Queue Manager Integration")
    results["pq_in_files"] = check_pq_manager_in_files()
    
    # Summary
    print_header("VERIFICATION SUMMARY")
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status.ljust(15)} {test_name}")
    
    print(f"\n{BLUE}{'='*70}{RESET}")
    if passed_tests == total_tests:
        print_success(f"ALL TESTS PASSED ({passed_tests}/{total_tests})")
        print_success("🎉 SYSTEM FULLY MIGRATED AND VERIFIED! 🎉")
    else:
        print_error(f"SOME TESTS FAILED ({passed_tests}/{total_tests})")
        print_error("⚠️ Please review failed tests above")
    print(f"{BLUE}{'='*70}{RESET}\n")

if __name__ == "__main__":
    main()
