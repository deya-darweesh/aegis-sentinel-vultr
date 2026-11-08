"""Verify live AegisSentinel deployment on Vultr Cloud Compute (64.177.59.95)."""

import json
import requests
import time

SERVER = "http://64.177.59.95"

def test_endpoints():
    print(f"=== TESTING LIVE DEPLOYMENT ON {SERVER} ===\n")

    # 1. Health check
    res = requests.get(f"{SERVER}/health")
    print(f"1. GET /health: {res.status_code}")
    print(json.dumps(res.json(), indent=2))
    assert res.status_code == 200

    # 2. Main Dashboard UI
    res = requests.get(f"{SERVER}/")
    print(f"\n2. GET /: {res.status_code} ({len(res.text)} bytes)")
    assert res.status_code == 200
    assert "AEGISSENTINEL" in res.text

    # 3. Threat Diagram Generation (Multi-modal)
    print("\n3. POST /api/threat-diagram...")
    res = requests.post(f"{SERVER}/api/threat-diagram", json={"prompt": "Attack vector topology"})
    print(f"Status: {res.status_code}")
    diagram_data = res.json()
    preview = diagram_data.get("diagram_url", "")[:80] + "..." if len(diagram_data.get("diagram_url", "")) > 80 else diagram_data.get("diagram_url")
    print(f'{{"diagram_url": "{preview}"}}')
    assert res.status_code == 200
    assert "diagram_url" in diagram_data

    # 4. Chaos Test (3-Vector Containment Validation)
    print("\n4. POST /api/chaos-test...")
    res = requests.post(f"{SERVER}/api/chaos-test")
    print(f"Status: {res.status_code}")
    chaos_data = res.json()
    print(json.dumps(chaos_data, indent=2))
    assert res.status_code == 200
    task_id = chaos_data["task_id"]

    # 5. Wait a moment and check missions
    time.sleep(2)
    print("\n5. GET /api/missions...")
    res = requests.get(f"{SERVER}/api/missions")
    print(f"Status: {res.status_code}")
    data = res.json()
    missions_list = data.get("missions", [])
    print(f"Found {len(missions_list)} recorded missions in database.")
    if missions_list:
        print(json.dumps(missions_list[0], indent=2))

    print("\n[SUCCESS] ALL LIVE TESTS PASSED ON VULTR CLOUD COMPUTE!")

if __name__ == "__main__":
    test_endpoints()
