from __future__ import annotations

import re

from forgeloop.models import TestFailure


def classify_failure_message(message: str) -> str:
    text = message or ""
    lower = text.lower()
    if "syntaxerror" in lower or "indentationalerror" in lower or "indentationerror" in lower:
        return "syntax"
    if "modulenotfounderror" in lower or "importerror" in lower or "no module named" in lower:
        return "import"
    if "assertionerror" in lower or "assert " in lower:
        return "assertion"
    if "nameerror" in lower or "typeerror" in lower or "attributeerror" in lower:
        return "runtime"
    return "unknown"


def classify_failures(failures: list[TestFailure]) -> list[TestFailure]:
    out: list[TestFailure] = []
    for f in failures:
        out.append(
            TestFailure(
                nodeid=f.nodeid,
                message=f.message,
                classification=classify_failure_message(f.message),
            )
        )
    return out


def dominant_classification(failures: list[TestFailure]) -> str:
    if not failures:
        return "none"
    counts: dict[str, int] = {}
    for f in failures:
        counts[f.classification] = counts.get(f.classification, 0) + 1
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]


_FAIL_HEADER = re.compile(r"^FAIL(?:ED)?\s+(.*)$", re.MULTILINE)
_ERROR_HEADER = re.compile(r"^ERROR\s+(.*)$", re.MULTILINE)


def parse_pytest_output(raw: str) -> list[TestFailure]:
    """Best-effort parse of pytest -q / short output into failures."""
    failures: list[TestFailure] = []
    for pat in (_FAIL_HEADER, _ERROR_HEADER):
        for m in pat.finditer(raw or ""):
            nodeid = m.group(1).strip()
            failures.append(TestFailure(nodeid=nodeid, message=nodeid))

    # assertion snippets
    for m in re.finditer(r"(AssertionError:.*)", raw or ""):
        if failures:
            failures[-1] = TestFailure(
                nodeid=failures[-1].nodeid,
                message=m.group(1),
            )
        else:
            failures.append(TestFailure(nodeid="unknown", message=m.group(1)))

    for m in re.finditer(r"(ModuleNotFoundError:.*|ImportError:.*|SyntaxError:.*)", raw or ""):
        if failures:
            failures[-1] = TestFailure(nodeid=failures[-1].nodeid, message=m.group(1))
        else:
            failures.append(TestFailure(nodeid="unknown", message=m.group(1)))

    return classify_failures(failures)
