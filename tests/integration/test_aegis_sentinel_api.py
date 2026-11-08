"""Integration Tests for AegisSentinel REST and Multi-Modal Endpoints."""

import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health_check_endpoint(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert "public_key_ed25519" in data
    assert "latest_audit_hash" in data


def test_initiate_duel_endpoint(client: TestClient):
    payload = {
        "scenario_preset": "SUPPLY_CHAIN_BACKDOOR",
        "max_rounds": 2,
    }
    response = client.post("/api/duel", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "mission_id" in data
    assert data["status"] == "duel_initiated"


def test_voice_command_endpoint(client: TestClient):
    # Upload mock WAV audio
    files = {"file": ("command.wav", b"RIFF....WAVEfmt ....data....", "audio/wav")}
    response = client.post("/api/voice-command", files=files)
    assert response.status_code == 200
    data = response.json()
    assert "transcribed_text" in data
    assert len(data["transcribed_text"]) > 0


def test_voice_alert_endpoint(client: TestClient):
    response = client.post("/api/voice-alert", data={"text": "Containment alert"})
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert len(response.content) > 0


def test_threat_diagram_endpoint(client: TestClient):
    payload = {"prompt": "Threat topology for payment gateway exploit"}
    response = client.post("/api/threat-diagram", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "diagram_url" in data
    assert data["diagram_url"].startswith("data:image/")


def test_vision_inspect_endpoint(client: TestClient):
    files = {"file": ("screenshot.png", b"\x89PNG\r\n\x1a\n....", "image/png")}
    response = client.post("/api/vision-inspect", files=files, data={"prompt": "Detect OOM error"})
    assert response.status_code == 200
    data = response.json()
    assert "analysis" in data


def test_list_missions_endpoint(client: TestClient):
    response = client.get("/api/missions?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert "missions" in data
    assert isinstance(data["missions"], list)


def test_audit_events_endpoint(client: TestClient):
    response = client.get("/api/audit-events?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "events" in data
    assert isinstance(data["events"], list)


def test_receipt_not_found(client: TestClient):
    response = client.get("/api/receipt/rcpt-nonexistent")
    assert response.status_code == 404


def test_chat_secops_copilot_endpoint(client: TestClient):
    payload = {
        "message": "Detonate fork bomb memory exhaustion exploit and immunize",
        "session_id": "test-session-001",
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "mission_id" in data
    assert data["scenario"] == "FORK_MEMORY_EXHAUSTION"
    assert data["status"] == "IMMUNIZED"
    assert "CVSS" in data["cvss_score"]
    assert data["pdf_report_url"] == f"/api/report/pdf/{data['mission_id']}"
    assert len(data["ed25519_signature"]) > 0


def test_generate_pdf_report_endpoint(client: TestClient):
    response = client.get("/api/report/pdf/msn-audit-integration-test")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment; filename=" in response.headers["content-disposition"]
    assert response.content.startswith(b"%PDF-")
