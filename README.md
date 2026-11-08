# AegisSentinel: Autonomous Cyber Arena & Proof-Carrying Immunity Engine

AegisSentinel is an autonomous, self-healing cyber defense platform that stages automated adversarial duels between two specialized AI agents inside a quarantined, stateful sandbox on Vultr Cloud Compute:

- **Red Agent (The Breaker):** Explores target microservices and software architectures to detect zero-day vulnerabilities, logic flaws, and resource exhaustion vectors.
- **Blue Agent (The Maker):** Analyzes forensic execution telemetry, synthesizes hardened hotpatches, and eliminates vulnerabilities.
- **Deterministic Arbiter:** Enforces strict containment policies inside an ephemeral sandbox, verifying results strictly via POSIX exit codes and cryptographic receipts.

---

## Key Features

- **Blast Radius Zero Containment:** Hardware and kernel-level isolation (gVisor `runsc` / Docker), dropped Linux capabilities (`--cap-drop=ALL`), read-only root filesystems, and strict memory/CPU quotas.
- **Multi-Modal Threat Operations:** Voice-driven incident command (`whisper-large-v3-turbo`), real-time vocal telemetry (`qwen3-tts`), visual screenshot inspection, and automated threat topology rendering (`z-image-turbo`).
- **Verifiable Proof of Immunity:** Every verified fix is signed with an Ed25519 digital signature and anchored to an immutable, sequential SHA-256 hash-chained audit ledger.
- **Vultr Infrastructure Native:** Built on Vultr Cloud Compute (VX1) with Vultr Serverless Inference (`deepseek-v4.1-flash-1017` and `qwen3.8-27b`).

---

## License

MIT License.
