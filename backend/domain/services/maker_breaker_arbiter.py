"""Maker-Breaker Arbiter Domain Service.

Coordinates the dual-agent dynamic between the Synthesizer (Maker)
and the Adversarial Fuzzer (Breaker).

Enforces the Yield Guardian Golden Rule:
Neither model decides success. The deterministic execution result is the sole Arbiter.
"""

from dataclasses import dataclass
from typing import Optional, Tuple

from domain.entities.code_patch import CodePatch
from domain.entities.test_suite import TestSuite


@dataclass
class ArbitrationVerdict:
    is_ready_for_release: bool
    synthesizer_passed_standard: bool
    breaker_found_vulnerability: bool
    summary: str
    remediation_prompt: Optional[str] = None


class MakerBreakerArbiter:
    """Impartial deterministic arbiter between Maker and Breaker."""

    def evaluate_round(
        self,
        patch: CodePatch,
        standard_suite: Optional[TestSuite],
        adversarial_suite: Optional[TestSuite],
        exit_code: int,
        stderr: str,
    ) -> ArbitrationVerdict:
        """Determines whether the patch is truly verified or requires self-healing."""

        # 1. Did the sandbox crash or return non-zero exit code?
        if exit_code != 0:
            return ArbitrationVerdict(
                is_ready_for_release=False,
                synthesizer_passed_standard=False,
                breaker_found_vulnerability=False,
                summary=f"Execution failed with Exit Code {exit_code}.",
                remediation_prompt=f"Your code crashed the sandbox runner with stderr:\n{stderr[-1000:]}\nFix the bug and ensure assertions pass.",
            )

        # 2. Check standard test suite assertions
        standard_passed = standard_suite.all_passed if standard_suite else True
        if not standard_passed:
            return ArbitrationVerdict(
                is_ready_for_release=False,
                synthesizer_passed_standard=False,
                breaker_found_vulnerability=False,
                summary="Standard functional assertions failed.",
                remediation_prompt="One or more baseline unit tests failed. Review test expectations and patch code.",
            )

        # 3. Check adversarial test suite assertions (Breaker challenge)
        adversarial_passed = adversarial_suite.all_passed if adversarial_suite else True
        if not adversarial_passed:
            # The Breaker found an edge case or regression!
            failed_tests = [r.name for r in adversarial_suite.results if not r.passed]
            return ArbitrationVerdict(
                is_ready_for_release=False,
                synthesizer_passed_standard=True,
                breaker_found_vulnerability=True,
                summary=f"Adversarial breaker found edge-case vulnerability in: {', '.join(failed_tests)}.",
                remediation_prompt=f"The adversarial reviewer generated stress inputs that broke your implementation on tests: {failed_tests}. Patch your logic to handle these edge cases without breaking baseline functionality.",
            )

        # 4. Both passed!
        return ArbitrationVerdict(
            is_ready_for_release=True,
            synthesizer_passed_standard=True,
            breaker_found_vulnerability=False,
            summary="All baseline and adversarial stress assertions passed deterministically (Exit Code 0).",
            remediation_prompt=None,
        )
