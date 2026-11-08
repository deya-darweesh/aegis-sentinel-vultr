"""FastAPI Presentation Router.

Exposes REST endpoints and real-time SSE streams for sandboxed execution,
the 1-click Chaos Test, audit trails, and cryptographic receipts.
Endpoints delegate execution lifecycle to TaskExecutionService (Rule 5).
"""

from api.schemas import (
    AuditEventSchema,
    AuditEventsResponse,
    ExecuteTaskRequest,
    ExecuteTaskResponse,
    ExecutionReceiptSchema,
    HealthStatusResponse,
    InitiateDuelRequest,
    InitiateDuelResponse,
    ListMissionsResponse,
    MissionSummarySchema,
    ReceiptVerificationResponse,
    ThreatDiagramRequest,
    ThreatDiagramResponse,
    TriggerChaosResponse,
    VisionInspectionRequest,
    VisionInspectionResponse,
    VoiceCommandResponse,
)
from api.sse_broker import SSEBroker
from application.services.combat_duel_service import CombatDuelService
from application.services.task_execution_service import TaskExecutionService
from application.use_cases.execute_sandboxed_task import ExecuteSandboxedTaskUseCase
from application.use_cases.initiate_combat_duel import InitiateCombatDuelUseCase
from application.use_cases.trigger_chaos_probe import TriggerChaosProbeUseCase
from application.use_cases.verify_receipt import VerifyReceiptUseCase
from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, Response, UploadFile
from fastapi.responses import StreamingResponse
from infrastructure.config import settings
from infrastructure.crypto.receipt_signer import ReceiptSigner
from infrastructure.gateway.mock_inference_adapter import MockInferenceAdapter
from infrastructure.gateway.vultr_inference_adapter import VultrInferenceAdapter
from infrastructure.persistence.database import async_session_factory
from infrastructure.persistence.mission_repository import MissionRepository
from infrastructure.sandbox.docker_runner_adapter import DockerRunnerAdapter
from infrastructure.telemetry.audit_ledger_adapter import AuditLedgerAdapter

router = APIRouter()

# Instantiate Singletons for the Modular Monolith
sse_broker = SSEBroker()
ledger = AuditLedgerAdapter()
signer = ReceiptSigner()
runner = DockerRunnerAdapter()
repository = MissionRepository(session_factory=async_session_factory)

# Select Inference Gateway based on MOCK_MODE configuration ($200 Credit Protection)
if settings.MOCK_MODE:
    llm_gateway = MockInferenceAdapter()
else:
    llm_gateway = VultrInferenceAdapter()

task_executor = ExecuteSandboxedTaskUseCase(runner=runner, ledger=ledger, signer=signer)
chaos_probe = TriggerChaosProbeUseCase(executor=task_executor)
receipt_verifier = VerifyReceiptUseCase(signer=signer)

duel_use_case = InitiateCombatDuelUseCase(
    runner=runner,
    ledger=ledger,
    signer=signer,
    repository=repository,
    llm_gateway=llm_gateway,
)

task_execution_service = TaskExecutionService(
    task_executor=task_executor,
    chaos_probe=chaos_probe,
    broadcast_fn=sse_broker.broadcast,
)

combat_duel_service = CombatDuelService(
    duel_use_case=duel_use_case,
    llm_gateway=llm_gateway,
    repository=repository,
    broadcast_fn=sse_broker.broadcast,
)


@router.get("/health", response_model=HealthStatusResponse)
def health_status() -> HealthStatusResponse:
    """Returns runtime engine status, mock mode toggle, and cryptographic signer key."""
    return HealthStatusResponse(
        status="operational",
        mock_mode=settings.MOCK_MODE,
        runtime_engine=runner._detect_runtime(),
        docker_available=runner.is_docker_available(),
        default_model=settings.DEFAULT_MODEL,
        public_key_ed25519=signer.public_key_hex,
        latest_audit_hash=ledger.get_latest_chain_hash()[:16] + "...",
    )


@router.post("/api/execute", response_model=ExecuteTaskResponse)
async def execute_task(payload: ExecuteTaskRequest, background_tasks: BackgroundTasks) -> ExecuteTaskResponse:
    """Executes arbitrary code inside the sealed quarantine container."""
    task_id, run_pipeline = task_execution_service.prepare_execution_pipeline(
        task_slug=payload.task_slug,
        code=payload.code,
        target_file=payload.target_file,
    )
    background_tasks.add_task(run_pipeline)
    return ExecuteTaskResponse(task_id=task_id, status="initiated")


@router.post("/api/chaos-test", response_model=TriggerChaosResponse)
async def trigger_chaos_test(background_tasks: BackgroundTasks) -> TriggerChaosResponse:
    """1-Click Red-Team Chaos Simulation testing filesystem, secret, and PID limits."""
    task_id, run_chaos = task_execution_service.prepare_chaos_pipeline()
    background_tasks.add_task(run_chaos)
    return TriggerChaosResponse(task_id=task_id, status="chaos_probe_dispatched")


@router.get("/api/stream/{task_id}")
async def stream_task_output(task_id: str):
    """Streams live container stdout/stderr events over SSE."""
    queue = sse_broker.subscribe(task_id)

    async def event_generator():
        try:
            while True:
                msg = await queue.get()
                yield msg
        except Exception:
            pass
        finally:
            sse_broker.unsubscribe(task_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/api/audit-events", response_model=AuditEventsResponse)
def get_audit_events(limit: int = 50) -> AuditEventsResponse:
    """Retrieves recent SHA-256 hash-chained audit events."""
    events = ledger.list_recent_events(limit=limit)
    return AuditEventsResponse(
        events=[
            AuditEventSchema(
                event_id=e.event_id,
                timestamp=float(e.timestamp),
                task_slug=e.task_slug,
                event_type=e.event_type,
                container_id=e.container_id,
                payload=e.payload,
                prev_hash=e.prev_hash,
                event_hash=e.event_hash,
            )
            for e in events
        ]
    )


@router.get("/api/receipt/{receipt_id}", response_model=ReceiptVerificationResponse)
async def get_receipt(receipt_id: str) -> ReceiptVerificationResponse:
    """Fetches and cryptographically verifies an ExecutionReceipt."""
    receipt = ledger.get_receipt(receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")

    result = await receipt_verifier.execute(receipt)
    receipt_schema = ExecutionReceiptSchema(
        receipt_id=receipt.receipt_id,
        timestamp=receipt.timestamp,
        task_slug=receipt.task_slug,
        status=receipt.status,
        exit_code=receipt.exit_code,
        duration_ms=receipt.duration_ms,
        memory_peak_mb=receipt.memory_peak_mb,
        runtime_engine=receipt.runtime_engine,
        container_id=receipt.container_id,
        digest_sha256=receipt.digest_sha256,
        ed25519_signature=receipt.ed25519_signature,
        public_key=receipt.public_key,
        violation=receipt.violation,
    )
    return ReceiptVerificationResponse(
        receipt=receipt_schema,
        cryptographically_verified=result.is_valid,
        verification_message=result.message,
    )


@router.post("/api/duel", response_model=InitiateDuelResponse)
async def initiate_duel(payload: InitiateDuelRequest, background_tasks: BackgroundTasks) -> InitiateDuelResponse:
    """Initiates an autonomous multi-round Maker-Breaker duel."""
    mission_id, run_duel = combat_duel_service.prepare_duel_pipeline(
        scenario_preset=payload.scenario_preset,
        target_code=payload.target_code,
        max_rounds=payload.max_rounds,
    )
    background_tasks.add_task(run_duel)
    return InitiateDuelResponse(mission_id=mission_id, status="duel_initiated")


@router.post("/api/voice-command", response_model=VoiceCommandResponse)
async def process_voice_command(file: UploadFile = File(...)) -> VoiceCommandResponse:
    """Transcribes spoken audio command using whisper-large-v3-turbo."""
    audio_content = await file.read()
    text = await combat_duel_service.transcribe_audio_command(
        audio_bytes=audio_content,
        filename=file.filename or "audio.wav",
    )
    return VoiceCommandResponse(transcribed_text=text)


@router.post("/api/voice-alert")
async def generate_voice_alert(text: str = Form("Alert: Containment violation intercepted.")) -> Response:
    """Synthesizes voice audio alert using qwen3-tts-12hz-1.7b."""
    audio_bytes = await combat_duel_service.synthesize_voice_alert(text)
    return Response(content=audio_bytes, media_type="audio/wav")


@router.post("/api/threat-diagram", response_model=ThreatDiagramResponse)
async def generate_threat_diagram(payload: ThreatDiagramRequest) -> ThreatDiagramResponse:
    """Generates an attack topology diagram using z-image-turbo."""
    diagram_url = await combat_duel_service.generate_threat_diagram(payload.prompt)
    return ThreatDiagramResponse(diagram_url=diagram_url)


@router.post("/api/vision-inspect", response_model=VisionInspectionResponse)
async def inspect_vision_artifact(
    file: UploadFile = File(...),
    prompt: str = Form("Inspect visual log for containment violations"),
) -> VisionInspectionResponse:
    """Analyzes an image using deepseek-v4.1-flash-1017 vision mode."""
    image_bytes = await file.read()
    analysis = await combat_duel_service.inspect_visual_artifact(image_bytes, prompt)
    return VisionInspectionResponse(analysis=analysis)


@router.get("/api/missions", response_model=ListMissionsResponse)
async def list_missions(limit: int = 20) -> ListMissionsResponse:
    """Queries persistent mission history."""
    records = await combat_duel_service.get_recent_missions(limit=limit)
    return ListMissionsResponse(
        missions=[
            MissionSummarySchema(
                mission_id=r["mission_id"],
                task_slug=r["task_slug"],
                status=r["status"],
                tokens_used=r["tokens_used"],
                created_at=r["created_at"],
                completed_at=r["completed_at"],
            )
            for r in records
        ]
    )
