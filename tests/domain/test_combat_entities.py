"""Domain Unit Tests for ExploitPayload and Mission Extensions."""

import pytest
from domain.aggregates.verification_mission import MissionStatus, VerificationMission
from domain.entities.code_patch import CodePatch
from domain.entities.exploit_payload import ExploitPayload


def test_exploit_payload_creation_and_hash():
    payload = ExploitPayload(
        exploit_id="exp-001",
        attack_vector="SUPPLY_CHAIN_BACKDOOR",
        code_payload="import socket; s = socket.socket()",
        round_number=1,
    )
    assert payload.exploit_id == "exp-001"
    assert payload.attack_vector == "SUPPLY_CHAIN_BACKDOOR"
    assert len(payload.sha256_hash) == 64
    assert not payload.intercepted

    payload.record_interception(exit_code=1, reason="Network unreachable")
    assert payload.intercepted
    assert payload.exit_code == 1
    assert payload.interception_reason == "Network unreachable"


def test_verification_mission_attach_exploit():
    mission = VerificationMission.create(
        task_slug="test-duel-01",
        target_file="target.py",
    )
    assert mission.status == MissionStatus.INITIALIZED
    assert len(mission.exploits) == 0

    exploit = ExploitPayload(
        exploit_id="exp-002",
        attack_vector="FORK_MEMORY_EXHAUSTION",
        code_payload="while True: os.fork()",
        round_number=1,
    )
    mission.attach_exploit(exploit)

    assert len(mission.exploits) == 1
    assert mission.exploits[0].exploit_id == "exp-002"
    # Verify audit event recorded
    audit_types = [e["event_type"] for e in mission.audit_chain]
    assert "EXPLOIT_ATTACHED" in audit_types
