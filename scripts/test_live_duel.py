import json
import time
import requests

SERVER = "http://64.177.59.95"

print("1. Triggering new autonomous Maker-Breaker duel (SUPPLY_CHAIN_BACKDOOR)...")
res = requests.post(
    f"{SERVER}/api/duel",
    json={"scenario_preset": "SUPPLY_CHAIN_BACKDOOR", "max_rounds": 2},
    timeout=10,
)
print("Initiate response:", res.status_code, res.json())
mission_id = res.json()["mission_id"]

print(f"\n2. Monitoring Mission ID: {mission_id}...")
for i in range(12):
    time.sleep(1.5)
    resp = requests.get(f"{SERVER}/api/missions").json()
    missions = resp.get("missions", [])
    for m in missions:
        if mission_id in m["task_slug"] or m["mission_id"] == mission_id:
            print(f"[{i*1.5:.1f}s] Status: {m['status']} | Tokens: {m['tokens_used']} | Completed: {m['completed_at']}")
            if m["status"] in ("VERIFIED_PASSED", "COMPLETED", "ASSERTION_FAILED"):
                print("\n[SUCCESS] Duel finished with final verified state:\n", json.dumps(m, indent=2))
                exit(0)

print("\nFinal missions list:")
print(json.dumps(requests.get(f"{SERVER}/api/missions").json(), indent=2))
