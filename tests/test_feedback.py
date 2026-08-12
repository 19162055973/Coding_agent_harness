from forgeloop.feedback.classifier import (
    classify_failure_message,
    dominant_classification,
    parse_pytest_output,
)
from forgeloop.feedback.sensor import TestSensor
from forgeloop.models import TestFailure


def test_classify_messages():
    assert classify_failure_message("AssertionError: boom") == "assertion"
    assert classify_failure_message("ModuleNotFoundError: No module named 'x'") == "import"
    assert classify_failure_message("SyntaxError: invalid syntax") == "syntax"


def test_parse_pytest_and_feedback(tmp_path):
    raw = "FAILED tests/test_x.py::test_one\nAssertionError: expected 1\n1 failed, 0 passed"
    failures = parse_pytest_output(raw)
    assert failures
    assert failures[0].classification == "assertion"
    sensor = TestSensor(tmp_path)
    # don't rely on real pytest here — unit the to_feedback path
    from forgeloop.models import TestReport

    report = TestReport(passed=False, total=1, failed=1, failures=failures, raw=raw)
    fb = sensor.to_feedback(report)
    assert fb.kind == "tests_failed"
    assert fb.classification == "assertion"


def test_dominant():
    fs = [
        TestFailure("a", "AssertionError", "assertion"),
        TestFailure("b", "AssertionError", "assertion"),
        TestFailure("c", "ImportError", "import"),
    ]
    assert dominant_classification(fs) == "assertion"
