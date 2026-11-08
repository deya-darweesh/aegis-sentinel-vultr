"""API Request and Response Schemas (Pydantic).

HTTP boundary schemas following ENG-STD-001:
{Action}{Concept}Request / {Action}{Concept}Response
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class ExecuteTaskRequest(BaseModel):
    """Payload to initiate quarantined code execution."""

    task_slug: str = Field(default="generic-task", description="Identifier slug for the task")
    code: str = Field(..., description="Python source code to execute inside sandbox")
    target_file: str = Field(default="main.py", description="Target filename inside container")


class ExecuteTaskResponse(BaseModel):
    """Response returned upon dispatching an execution task."""

    task_id: str
    status: str


class TriggerChaosResponse(BaseModel):
    """Response returned upon detonating the 1-click chaos test."""

    task_id: str
    status: str


class AuditEventSchema(BaseModel):
    """Schema for an individual hash-chained audit telemetry event."""

    event_id: str
    timestamp: float
    task_slug: str
    event_type: str
    container_id: Optional[str] = None
    payload: dict
    prev_hash: str
    event_hash: str


class AuditEventsResponse(BaseModel):
    """List of recent SHA-256 hash-chained telemetry events."""

    events: List[AuditEventSchema]


class ExecutionReceiptSchema(BaseModel):
    """Verifiable execution receipt schema."""

    receipt_id: str
    timestamp: str
    task_slug: str
    status: str
    exit_code: int
    duration_ms: float
    memory_peak_mb: float
    runtime_engine: str
    container_id: str
    digest_sha256: str
    ed25519_signature: Optional[str] = None
    public_key: Optional[str] = None
    violation: Optional[str] = None


class ReceiptVerificationResponse(BaseModel):
    """Outcome of cryptographic signature verification."""

    receipt: ExecutionReceiptSchema
    cryptographically_verified: bool
    verification_message: str


class HealthStatusResponse(BaseModel):
    """Diagnostic system health and containment engine status."""

    status: str
    mock_mode: bool
    runtime_engine: str
    docker_available: bool
    default_model: str
    public_key_ed25519: str
    latest_audit_hash: str


class InitiateDuelRequest(BaseModel):
    """Payload to initiate an autonomous Maker-Breaker duel."""

    scenario_preset: str = Field(
        default="SUPPLY_CHAIN_BACKDOOR",
        description="Preset scenario: SUPPLY_CHAIN_BACKDOOR | FORK_MEMORY_EXHAUSTION | FINANCIAL_INVARIANT_TAMPER | CUSTOM",
    )
    target_code: Optional[str] = Field(default=None, description="Optional custom vulnerable code")
    max_rounds: int = Field(default=3, description="Maximum adversarial rounds")


class InitiateDuelResponse(BaseModel):
    """Response returned upon initiating a duel."""

    mission_id: str
    status: str


class VoiceCommandResponse(BaseModel):
    """Transcribed text from spoken voice command."""

    transcribed_text: str


class ThreatDiagramRequest(BaseModel):
    """Prompt for generating threat topology visualization."""

    prompt: str = Field(default="AegisSentinel attack topology diagram", description="Diagram generation prompt")


class ThreatDiagramResponse(BaseModel):
    """Generated attack topology image data URL or link."""

    diagram_url: str


class VisionInspectionRequest(BaseModel):
    """Request for inspecting a visual artifact or screenshot."""

    prompt: str = Field(default="Inspect visual log for containment violations", description="Vision inspection prompt")


class VisionInspectionResponse(BaseModel):
    """Result of vision model analysis."""

    analysis: str


class MissionSummarySchema(BaseModel):
    """Summary of a verification mission."""

    mission_id: str
    task_slug: str
    status: str
    tokens_used: int
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


class ListMissionsResponse(BaseModel):
    """List of recent verification missions."""

    missions: List[MissionSummarySchema]
