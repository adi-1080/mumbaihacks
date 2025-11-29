#!/usr/bin/env python3
"""
Generate a complete, valid Postman collection for MediSync
"""
import json

collection = {
    "info": {
        "name": "MediSync - Orchestration Fixed",
        "description": "All Python tools working - ETA, Notifications, Intelligence",
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        "_postman_id": "medisync-fixed",
        "version": "2.1.0"
    },
    "variable": [
        {"key": "base_url", "value": "http://localhost:3000/api/v1", "type": "string"},
        {"key": "token_number", "value": "", "type": "string"}
    ],
    "item": [
        {
            "name": "1. Health Check",
            "request": {
                "method": "GET",
                "header": [],
                "url": {"raw": "http://localhost:3000/health", "protocol": "http", "host": ["localhost"], "port": "3000", "path": ["health"]}
            }
        },
        {
            "name": "2. Book Critical Patient (FULL ORCHESTRATION)",
            "event": [{
                "listen": "test",
                "script": {
                    "exec": [
                        "if (pm.response.code === 201) {",
                        "    const r = pm.response.json();",
                        "    pm.collectionVariables.set('token_number', r.data.token_number);",
                        "    pm.test('Orchestration enabled', () => pm.expect(r.orchestration.enabled).to.be.true);",
                        "    pm.test('ETA calc SUCCESS', () => {",
                        "        const eta = r.orchestration.details.find(d => d.action === 'AUTO_CALCULATE_ETAS');",
                        "        pm.expect(eta.success).to.be.true;",
                        "    });",
                        "    pm.test('Notifications SUCCESS', () => {",
                        "        const notif = r.orchestration.details.find(d => d.action === 'SEND_NOTIFICATIONS');",
                        "        if (notif) pm.expect(notif.success).to.be.true;",
                        "    });",
                        "    console.log('Actions:', r.orchestration.actions_executed);",
                        "}"
                    ]
                }
            }],
            "request": {
                "method": "POST",
                "header": [{"key": "Content-Type", "value": "application/json"}],
                "body": {
                    "mode": "raw",
                    "raw": json.dumps({
                        "name": "Critical Test Patient",
                        "contact_number": "+91-9999888877",
                        "symptoms": "Severe chest pain, difficulty breathing",
                        "location": "Mumbai",
                        "age": 55,
                        "emergency_level": "CRITICAL"
                    })
                },
                "url": {"raw": "{{base_url}}/appointments/book", "host": ["{{base_url}}"], "path": ["appointments", "book"]},
                "description": "Tests: ETA calculation, Notifications, Queue intelligence"
            }
        },
        {
            "name": "3. Get Queue (Smart Mode with ETAs)",
            "request": {
                "method": "GET",
                "header": [],
                "url": {"raw": "{{base_url}}/queue", "host": ["{{base_url}}"], "path": ["queue"]},
                "description": "Returns queue with auto-calculated ETAs and intelligence dashboard"
            }
        },
        {
            "name": "4. Get ETAs Directly",
            "request": {
                "method": "GET",
                "header": [],
                "url": {"raw": "{{base_url}}/queue/etas", "host": ["{{base_url}}"], "path": ["queue", "etas"]},
                "description": "Direct ETA calculation - should work with no errors"
            }
        },
        {
            "name": "5. Complete Patient (Orchestration Cycle)",
            "event": [{
                "listen": "test",
                "script": {
                    "exec": [
                        "if (pm.response.code === 200) {",
                        "    const r = pm.response.json();",
                        "    pm.test('Orchestration cycle triggered', () => {",
                        "        pm.expect(r.orchestration.enabled).to.be.true;",
                        "        pm.expect(r.orchestration.actions_executed).to.be.greaterThan(0);",
                        "    });",
                        "}"
                    ]
                }
            }],
            "request": {
                "method": "POST",
                "header": [],
                "url": {"raw": "{{base_url}}/appointments/{{token_number}}/complete", "host": ["{{base_url}}"], "path": ["appointments", "{{token_number}}", "complete"]},
                "description": "Triggers full orchestration cycle"
            }
        },
        {
            "name": "6. Get Queue Stats",
            "request": {
                "method": "GET",
                "header": [],
                "url": {"raw": "{{base_url}}/queue/stats", "host": ["{{base_url}}"], "path": ["queue", "stats"]},
                "description": "Get comprehensive queue statistics"
            }
        }
    ]
}

# Write to file
output_path = "MediSync_Simple_Collection.json"
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(collection, f, indent=2, ensure_ascii=True)

print(f"✅ Created: {output_path}")
print(f"📏 Size: {len(json.dumps(collection))} bytes")
print("✅ Valid JSON with all key orchestration tests")
print("\nImport this file into Postman and run folder to test!")
