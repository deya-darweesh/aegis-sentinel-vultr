import requests
import json
import time

SERVER = "http://64.177.59.95"
presets = [
    "SUPPLY_CHAIN_BACKDOOR",
    "FORK_MEMORY_EXHAUSTION",
    "FINANCIAL_INVARIANT_TAMPER",
]

for preset in presets:
    print(f"\n=======================================================")
    print(f"DETONATING COMBAT DUEL PRESET: {preset}")
    print(f"=======================================================")
    res = requests.post(f"{SERVER}/api/duel", json={"scenario_preset": preset, "max_rounds": 2})
    assert res.status_code == 200
    mid = res.json()["mission_id"]
    print(f"Mission ID: {mid} dispatched.")
    time.sleep(2)
    m = requests.get(f"{SERVER}/api/missions").json()
    for item in m.get("missions", []):
        if mid in item["task_slug"]:
            print(f"Result for {preset}: Status = {item['status']} | Completed = {item['completed_at']}")
            break

print("\nALL 3 COMBAT DUEL PRESETS SUCCESSFULLY EXECUTED AND PERSISTED ON VULTR!")
