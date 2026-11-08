# 🛡️ AegisSentinel: Autonomous Cyber Shield & Proof-Carrying Immunity Engine

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Next.js: 15](https://img.shields.io/badge/Next.js-15-black.svg)](https://nextjs.org/)
[![Vultr: Cloud Compute](https://img.shields.io/badge/Vultr-Cloud%20Compute%20%2B%20Inference-007BFC.svg)](https://www.vultr.com/)
[![Tests: 55 Passed](https://img.shields.io/badge/Tests-55%20Passed%20(100%25%20Domain%20Coverage)-brightgreen.svg)]()
[![Containment: Blast Radius Zero](https://img.shields.io/badge/Blast%20Radius-ZERO-red.svg)]()

> **Live Production Server:** [http://64.177.59.95/](http://64.177.59.95/)  
> **Official Submission for:** Vultr Agent Rush Hackathon 2026 (Co-located with KubeCon NA 2026)  
> **Qualifying Tracks:** **Track 1 (Blast Radius Zero)** & **Track 2 (Future of Work)**

---

## ⚡ Executive Summary

Autonomous AI coding and execution agents represent the future of software engineering, but granting them access to system shells and compilers creates catastrophic attack surfaces:
- **Supply-Chain Exfiltration:** Malicious or hallucinated agent code stealing `.env`, private keys, and cloud credentials.
- **Resource Denial-of-Service:** Memory exhaustion, CPU starvation, and fork-bombs crashing host nodes.
- **Financial & Logic Invariant Corruption:** Silent floating-point drifts, race conditions, or unverified arithmetic bugs.

**AegisSentinel** solves this challenge through a **Proof-Carrying Immunity Engine** staging an automated, round-based combat duel between two adversarial AI models inside a zero-trust, quarantined sandbox on **Vultr Cloud Compute**:
1. **Red Agent (The Breaker):** Stochastically discovers logic flaws, supply-chain leaks, and resource vulnerabilities.
2. **Deterministic Arbiter:** Intercepts execution via Linux cgroups v2, AST static filters, and zero-mount container standard input streaming.
3. **Blue Agent (The Maker):** Synthesizes minimal, backward-compatible, hardened hotpatches to neutralize the threat.
4. **Retaliation Gate & Cryptographic Notary:** Re-runs the red attack against the hotpatch. Upon verification, issues an **Ed25519-signed canonical JSON receipt** anchored to an immutable, sequential **SHA-256 hash-chained audit ledger**.

---

## 🏗️ Architectural Topology

```text
                               +-------------------------------------------------------------+
                               |                  MISSION CONTROL HUD (Next.js 15)           |
                               |  - Live Gauge Visualizer        - Real-Time SSE Stream      |
                               |  - Split Duel Terminal          - 1-Click Attack Presets    |
                               |  - Audio Waveform Player        - Cryptographic Notary      |
                               +------------------------------+------------------------------+
                                                              | HTTP / SSE Stream
                                                              v
+-------------------------------------------------------------------------------------------------------------------------+
|                                        AEGISSENTINEL MODULAR MONOLITH (FastAPI)                                         |
|                                                                                                                         |
|  [ API LAYER ]              FastAPI Routers, SSE Broker, Strict Pydantic Schemas, RFC 8785 Canonical Serialization      |
|                                                                                                                         |
|  [ APPLICATION LAYER ]      InitiateCombatDuelUseCase, ExecuteSandboxedTaskUseCase, VerifyReceiptUseCase,               |
|                             TaskExecutionService, CombatDuelService, Ports: IAuditLedger, ILlmGateway, ISandboxRunner  |
|                                                                                                                         |
|  [ DOMAIN LAYER (Pure) ]    VerificationMission Aggregate, SandboxSession, ContainmentPolicy, SecurityViolation,        |
|                             AstBlastRadiusGuard, MakerBreakerArbiter, SecretScrubber, ExecutionReceipt                  |
|                                                                                                                         |
|  [ INFRASTRUCTURE LAYER ]   DockerRunnerAdapter (Zero-Mount Stdin), VultrInferenceAdapter (Circuit Breaker),            |
|                             ReceiptSigner (PyNaCl Ed25519), AuditLedgerAdapter (Hash Chaining), Alembic/Postgres/SQLite |
+-------------------------------------------------------------+-----------------------------------------------------------+
                                                              |
                  +-------------------------------------------+-------------------------------------------+
                  |                                                                                       |
                  v                                                                                       v
+-----------------------------------+                                                   +-----------------------------------+
|     VULTR SERVERLESS INFERENCE    |                                                   |     QUARANTINED DOCKER RUNNER     |
|   (api.vultrinference.com/v1)     |                                                   |        (Blast Radius Zero)        |
|                                   |                                                   |                                   |
| - Red Agent: deepseek-v4.1-flash  |                                                   | - Zero-Mount Stdin Streaming      |
| - Blue Agent: qwen3.8-27b         |                                                   | - Linux cgroups v2 (256MB / 0.5c) |
| - Voice In: whisper-large-turbo   |                                                   | - Read-Only Root + 64MB Tmpfs     |
| - Voice Out: qwen3-tts-12hz-1.7b  |                                                   | - Air-Gapped Network (--net=none) |
| - Vision In: deepseek-v4.1-flash  |                                                   | - Dropped Capabilities (ALL)      |
| - Topology Out: z-image-turbo     |                                                   | - Wall-Clock SIGKILL Watchdog     |
+-----------------------------------+                                                   +-----------------------------------+
```

---

## 🔒 Track 1: Blast Radius Zero — The 4 Containment Pillars

AegisSentinel enforces **Tier-1 Real-Time Runtime Interception** to guarantee that untrusted agent code cannot breach host boundaries:

| Pillar | Mechanism | Implementation Details |
|---|---|---|
| **1. Zero-Mount Stdin Streaming** | Direct Stdin Pipe | Bypasses Docker host-mount vulnerabilities. The container filesystem is completely disconnected from host storage; untrusted code is piped directly to `python3 -u -` via standard input. |
| **2. Kernel Isolation & Caps** | `--cap-drop=ALL` & No-New-Privileges | Drops all 38 Linux capabilities, disallows privilege escalation (`no-new-privileges=true`), and drops execution to an unprivileged user (`uid=10001:gid=10001`). Compatible with gVisor `runsc`. |
| **3. Ephemeral Air-Gap** | `--network=none` & Read-Only Root | Root filesystem is mounted strictly read-only (`--read-only`), with a size-bounded, no-exec memory scratchpad (`--tmpfs /tmp:rw,noexec,nosuid,size=64m`). Outbound socket operations fail immediately at the kernel layer. |
| **4. AST Static Blast Radius Guard** | Python Abstract Syntax Tree Inspection | Pre-execution 0.02ms AST scan rejects forbidden modules (`socket`, `subprocess`, `ctypes`, `shutil`) and sensitive files before any process fork. |

---

## 🤖 Track 2: Future of Work — Autonomous Maker-Breaker Duel

Rather than relying on static linters or human review, AegisSentinel turns security into an **autonomous co-evolutionary tournament**:
1. **Round 1 (Breaker Exploit Fuzzing):** Red Agent analyzes target source code, identifies logic/security vulnerabilities, and generates an exploit payload designed to trigger non-zero exits or assertion failures.
2. **Containment Arbiter:** Untrusted target and exploit code execute inside the zero-mount sandbox. Exit codes, peak RAM, stdout, and security violations are captured.
3. **Round 2 (Maker Hotpatch Synthesis):** Blue Agent receives telemetry, analyzes the vulnerability vector, and synthesizes a hardened, backward-compatible patch.
4. **Round 3 (Automated Retaliation Gate):** The Arbiter recompiles and executes the hotpatch against both:
   - The original baseline test suite (regression prevention).
   - The Red Agent's exploit payload (retaliation validation).
5. **Round 4 (Cryptographic Notarization):** If both suites pass, AegisSentinel issues an **Ed25519 digital signature** over the RFC 8785 canonical JSON digest, anchoring it to the sequential SHA-256 hash ledger ($H_n = \text{SHA256}(H_{n-1} + \text{Payload})$).

---

## 🎙️ 6-Model Multi-Modal Vultr Inference Pipeline

AegisSentinel integrates **6 specialized AI models** via Vultr Serverless Inference (`api.vultrinference.com/v1`), complete with an automatic circuit breaker fallback:

| Modality | Channel | Model Name | Role in AegisSentinel |
|---|---|---|---|
| **Text Reasoning** | Red Agent (Breaker) | `deepseek-v4.1-flash-1017` | Generates adversarial exploits and fuzzing payloads using reasoning tokens. |
| **Code Synthesis** | Blue Agent (Maker) | `qwen3.8-27b` | Synthesizes hardened Python patches and eliminates root vulnerabilities. |
| **Audio In** | Voice Detonation | `whisper-large-v3-turbo` | Transcribes spoken incident response commands from security operators. |
| **Audio Out** | Real-Time Vocal Alarm | `qwen3-tts-12hz-1.7b` | Speaks synthesized voice status and incident alerts in real time. |
| **Vision In** | Visual Log Inspection | `deepseek-v4.1-flash-1017` | Inspects terminal screenshots and container diagrams for suspicious anomalies. |
| **Image Out** | Attack Topology Render | `z-image-turbo` | Dynamically generates visual attack surface and network topology diagrams. |

---

## 📜 Cryptographic Proof of Immunity (RFC 8785 + Ed25519)

Every verified remediation produces a tamper-proof receipt:

```json
{
  "receipt_id": "rcpt-c1cbde9687e3",
  "timestamp": 1731091705.52,
  "task_slug": "sentinel-duel-supply-chain-backdoor",
  "status": "VERIFIED_PASSED",
  "exit_code": 0,
  "duration_ms": 142.8,
  "memory_peak_mb": 14.2,
  "runtime_engine": "runc",
  "container_id": "aegis-runner-35ca40c2f9",
  "digest_sha256": "4b68058dd5aee3fc59a11728be26c6d3...",
  "ed25519_signature": "6cb3b7d15664dae576ecae2890610332822a106a77e...",
  "public_key": "e79cd06e5d2110c7cc096a34f5f0ff7d8fc00ce03ae2559971d0847524a14cd5",
  "violation": null
}
```

Third-party auditors can verify receipts offline or via the `/api/receipt/{receipt_id}` endpoint without trusting the server.

---

## 🧪 Comprehensive Test Suite & Quality Control

AegisSentinel enforces strict Domain-Driven Design (DDD) rules:
- **Zero Framework Contamination:** The `domain/` layer has 0 imports of FastAPI, Pydantic, SQLAlchemy, or Docker.
- **Diff Coverage:** 100% test coverage across all domain aggregates, entities, services, and values.
- **Overall Coverage:** 90% across the full backend codebase.

Run the test suite locally:
```bash
# Run 55 tests
pytest

# Run tests with code coverage report
pytest --cov=backend --cov-report=term-missing
```

---

## 🚀 Quickstart & Verification

### 1. Inspect Live Production Deployment
- **Web HUD:** [http://64.177.59.95/](http://64.177.59.95/)
- **Health Check:** `curl -s http://64.177.59.95/health`
- **Audit Ledger:** `curl -s http://64.177.59.95/api/audit-stream`
- **Mission History:** `curl -s http://64.177.59.95/api/missions`

### 2. Trigger 1-Click Chaos Probe
```bash
curl -X POST http://64.177.59.95/api/chaos-test
```

### 3. Initiate Autonomous Maker-Breaker Duel
```bash
curl -X POST http://64.177.59.95/api/duel \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_preset": "supply_chain_leak",
    "target_code": "# microservice logic\ndef authenticate(): pass",
    "max_rounds": 2
  }'
```

### 4. Run Locally with Docker Compose
```bash
# Clone the repository
git clone https://github.com/deya-darweesh/aegis-sentinel-vultr.git
cd aegis-sentinel-vultr

# Copy environment variables
cp .env.example .env

# Start stack with Docker Compose
docker compose up -d --build

# Run database migrations
docker compose exec backend python -m alembic upgrade head
```

---

## 👥 Hackathon Team & Acknowledgments

- **Lead Engineer & System Architect:** Deya Darweesh
- **Event:** Vultr Agent Rush Hackathon 2026 (Co-located with KubeCon NA 2026)
- **Infrastructure Provider:** Vultr Cloud Compute & Vultr Serverless Inference Engine
