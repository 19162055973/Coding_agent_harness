from __future__ import annotations

import re
import subprocess
from pathlib import Path

from forgeloop.feedback.classifier import dominant_classification, parse_pytest_output
from forgeloop.models import FeedbackEvent, TestReport


class TestSensor:
    """Deterministic feedback sensor: run tests and structure the result."""

    __test__ = False

    def __init__(self, workspace: str | Path, command: str = "python -m pytest -q"):
        self.workspace = Path(workspace)
        self.command = command

    def run(self, extra: str = "", timeout: float = 120.0) -> TestReport:
        cmd = self.command if not extra else f"{self.command} {extra}"
        try:
            proc = subprocess.run(
                cmd,
                shell=True,
                cwd=str(self.workspace),
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except FileNotFoundError as exc:
            return TestReport(passed=False, raw=str(exc), failures=[])
        except subprocess.TimeoutExpired:
            return TestReport(passed=False, raw=f"timeout: {cmd}", failures=[])

        raw = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
        failures = parse_pytest_output(raw)
        # summary line like "1 failed, 2 passed"
        failed = 0
        total = 0
        m = re.search(r"(\d+)\s+failed", raw)
        if m:
            failed = int(m.group(1))
        m2 = re.search(r"(\d+)\s+passed", raw)
        passed_n = int(m2.group(1)) if m2 else 0
        if failed or passed_n:
            total = failed + passed_n
        elif failures:
            failed = len(failures)
            total = failed
        passed = proc.returncode == 0
        if not passed and failed == 0 and failures:
            failed = len(failures)
        return TestReport(
            passed=passed,
            total=total,
            failed=failed if not passed else 0,
            failures=failures,
            raw=raw,
        )

    def to_feedback(self, report: TestReport) -> FeedbackEvent:
        if report.passed:
            return FeedbackEvent(
                kind="tests_passed",
                classification="none",
                summary="All tests passed.",
                raw_ref=report.raw[:500],
            )
        klass = dominant_classification(report.failures)
        bits = [f"{f.nodeid}: {f.classification}" for f in report.failures[:5]]
        summary = (
            f"Tests failed (dominant={klass}). "
            + ("; ".join(bits) if bits else report.raw[:300])
        )
        return FeedbackEvent(
            kind="tests_failed",
            classification=klass,
            summary=summary,
            raw_ref=report.raw[:1000],
        )
