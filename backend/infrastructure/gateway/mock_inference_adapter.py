"""Deterministic Offline Mock Inference Adapter.

Implements LLMGatewayPort for local development, CI, and testing.
Consumes $0.00 of Vultr credits while fully simulating tool calling, code generation,
and self-healing scenarios.
"""

import json
from typing import Dict, List, Optional

from application.dtos.llm_completion_dto import LLMCompletionDTO, LLMTokenUsageDTO
from application.ports.i_llm_gateway import ILLMGateway
from domain.values.token_budget import TokenBudget


class MockInferenceAdapter(ILLMGateway):
    """Deterministic, zero-cost mock inference provider."""

    async def generate_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        budget: TokenBudget,
        tools: Optional[List[dict]] = None,
        temperature: float = 0.2,
    ) -> LLMCompletionDTO:
        last_message = messages[-1]["content"].lower() if messages else ""

        # Scenario 1: Red-Team Chaos Probe simulation
        if any(w in last_message for w in ("chaos", "red-team", "exploit", "probe")):
            return LLMCompletionDTO(
                role="assistant",
                content="Executing compliance validation test inside sealed container.",
                tool_calls=[
                    {
                        "id": "call_chaos_01",
                        "type": "function",
                        "function": {
                            "name": "run_quarantined_script",
                            "arguments": json.dumps(
                                {
                                    "code": (
                                        "import os, sys\n"
                                        "print('--- [CHAOS PROBE] Testing Blast Radius Containment ---')\n"
                                        "print('[VECTOR 1] Testing secret scrubbing...')\n"
                                        "print('VULTR_KEY in env: False')\n"
                                        "print('[VECTOR 2] Testing read-only rootfs...')\n"
                                        "try:\n"
                                        "    with open('/etc/chaos_probe.txt', 'w') as f: f.write('escape')\n"
                                        "except OSError as e:\n"
                                        "    print(f'BLOCKED: {e}')\n"
                                        "print('[VECTOR 3] Simulating fork bomb...')\n"
                                        "print('FORK_BOMB_PREVENTED: pids_limit=64')\n"
                                        "print('--- [CHAOS PROBE FINISHED] ---')\n"
                                    )
                                }
                            ),
                        },
                    }
                ],
                usage=LLMTokenUsageDTO(prompt_tokens=50, completion_tokens=100, total_tokens=150),
            )

        # Scenario 2: Benign code generation test
        if "calculation" in last_message or "stats" in last_message:
            return LLMCompletionDTO(
                role="assistant",
                content="Here is a verified numerical implementation.",
                tool_calls=[
                    {
                        "id": "call_exec_01",
                        "type": "function",
                        "function": {
                            "name": "run_quarantined_script",
                            "arguments": json.dumps(
                                {
                                    "code": (
                                        "import math\n"
                                        "values = [12.4, 15.6, 18.2, 22.1, 24.8]\n"
                                        "mean = sum(values) / len(values)\n"
                                        "variance = sum((x - mean) ** 2 for x in values) / len(values)\n"
                                        "print(f'Mean: {mean:.2f}')\n"
                                        "print(f'StdDev: {math.sqrt(variance):.2f}')\n"
                                        "print('SUCCESS: Execution completed deterministically.')\n"
                                    )
                                }
                            ),
                        },
                    }
                ],
                usage=LLMTokenUsageDTO(prompt_tokens=60, completion_tokens=90, total_tokens=150),
            )

        # Scenario 3: Standard safe chat completion
        return LLMCompletionDTO(
            role="assistant",
            content=f"[MOCK_ENGINE] Verified response from simulated {model}. No credits consumed.",
            tool_calls=None,
            usage=LLMTokenUsageDTO(prompt_tokens=40, completion_tokens=30, total_tokens=70),
        )

    async def transcribe_audio(self, audio_bytes: bytes, filename: str) -> str:
        """Mock audio speech-to-text using whisper-large-v3-turbo."""
        if len(audio_bytes) == 0:
            return ""
        return "Detonate memory bomb and test cgroup containment on payment gateway"

    async def synthesize_speech(self, text: str) -> bytes:
        """Mock audio text-to-speech using qwen3-tts-12hz-1.7b.

        Returns a valid 44-byte standard RIFF WAV header for browser audio players.
        """
        # Minimal valid WAV header (44 bytes, 8000Hz, 16-bit mono PCM, 0 data samples)
        wav_header = (
            b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00"
            b"\x40\x1f\x00\x00\x80\x3e\x00\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
        )
        return wav_header

    async def generate_threat_diagram(self, prompt: str) -> str:
        """Mock architectural threat diagram generation using z-image-turbo."""
        svg_diagram = (
            "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 800 450' width='100%' height='100%'>"
            "<defs><linearGradient id='bg' x1='0%' y1='0%' x2='100%' y2='100%'>"
            "<stop offset='0%' stop-color='#090d16'/><stop offset='100%' stop-color='#0f172a'/>"
            "</linearGradient></defs>"
            "<rect width='800' height='450' fill='url(#bg)' rx='12'/>"
            "<text x='400' y='40' font-family='monospace' font-size='18' fill='#00F0FF' text-anchor='middle' font-weight='bold'>"
            "AEGISSENTINEL THREAT TOPOLOGY MAP (z-image-turbo)"
            "</text>"
            "<rect x='50' y='80' width='200' height='120' rx='8' fill='#1e1b4b' stroke='#ef4444' stroke-width='2'/>"
            "<text x='150' y='120' font-family='monospace' font-size='14' fill='#f87171' text-anchor='middle' font-weight='bold'>RED AGENT</text>"
            "<text x='150' y='145' font-family='monospace' font-size='11' fill='#94a3b8' text-anchor='middle'>deepseek-v4.1-flash</text>"
            "<text x='150' y='170' font-family='monospace' font-size='10' fill='#ef4444' text-anchor='middle'>[EXPLOIT SYNTHESIS]</text>"
            "<line x1='250' y1='140' x2='340' y2='140' stroke='#ef4444' stroke-width='2' stroke-dasharray='4'/>"
            "<rect x='340' y='60' width='180' height='160' rx='8' fill='#022c22' stroke='#10b981' stroke-width='2'/>"
            "<text x='430' y='95' font-family='monospace' font-size='14' fill='#34d399' text-anchor='middle' font-weight='bold'>VULTR QUARANTINE</text>"
            "<text x='430' y='125' font-family='monospace' font-size='11' fill='#6ee7b7' text-anchor='middle'>gVisor runsc Sandbox</text>"
            "<text x='430' y='150' font-family='monospace' font-size='10' fill='#a7f3d0' text-anchor='middle'>--network=none</text>"
            "<text x='430' y='175' font-family='monospace' font-size='10' fill='#a7f3d0' text-anchor='middle'>cgroups: 256MB RAM</text>"
            "<text x='430' y='200' font-family='monospace' font-size='10' fill='#34d399' text-anchor='middle'>[BLAST RADIUS ZERO]</text>"
            "<line x1='520' y1='140' x2='610' y2='140' stroke='#38bdf8' stroke-width='2'/>"
            "<rect x='610' y='80' width='150' height='120' rx='8' fill='#082f49' stroke='#38bdf8' stroke-width='2'/>"
            "<text x='685' y='120' font-family='monospace' font-size='14' fill='#38bdf8' text-anchor='middle' font-weight='bold'>BLUE AGENT</text>"
            "<text x='685' y='145' font-family='monospace' font-size='11' fill='#94a3b8' text-anchor='middle'>qwen3.8-27b</text>"
            "<text x='685' y='170' font-family='monospace' font-size='10' fill='#38bdf8' text-anchor='middle'>[IMMUNITY PATCH]</text>"
            "<rect x='50' y='260' width='710' height='150' rx='8' fill='#0f172a' stroke='#6366f1' stroke-width='1.5'/>"
            "<text x='70' y='295' font-family='monospace' font-size='13' fill='#818cf8' font-weight='bold'>ARBITER AUDIT DOSSIER &amp; CRYPTOGRAPHIC PROOF</text>"
            "<text x='70' y='325' font-family='monospace' font-size='11' fill='#cbd5e1'>- Containment Interception: Exit Code 137 (cgroups OOM killed within 0.42s)</text>"
            "<text x='70' y='350' font-family='monospace' font-size='11' fill='#cbd5e1'>- Host Integrity: 0 secrets leaked | 0 network packets egressed | Read-only rootfs held</text>"
            "<text x='70' y='375' font-family='monospace' font-size='11' fill='#10b981'>- Verified Immunity: Ed25519 Canonical Signature Verified | Merkle Hash Chain Validated</text>"
            "</svg>"
        )
        return f"data:image/svg+xml;utf8,{svg_diagram}"

    async def inspect_image(self, image_bytes: bytes, prompt: str) -> str:
        """Mock visual analysis of logs or core dumps."""
        return (
            "[VISION_ANALYZER: deepseek-v4.1-flash] Analyzed image artifact: "
            "Detected visual stack trace with OOM panic signature. "
            "Memory spike registered at 256MB threshold. Zero-trust containment preserved."
        )
