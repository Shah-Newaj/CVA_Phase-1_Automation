import pytest

from bth_qa_reporter import reporter as reporter_module
from bth_qa_reporter.reporter import Reporter


def test_assert_visible_records_pass(monkeypatch):
    class FakeExpect:
        def __init__(self, locator):
            self.locator = locator

        def to_be_visible(self, timeout=30000):
            assert timeout == 5000

    monkeypatch.setattr(reporter_module, "expect", lambda locator: FakeExpect(locator))

    reporter = Reporter()
    reporter.start_test("case:visible", "visible test")
    reporter.assert_visible(object(), "Dashboard loaded", timeout=5000)

    step = reporter.results["case:visible"]["steps"][-1]
    assert step["status"] == "PASS"
    assert step["expected"] == "visible"
    assert step["actual"] == "visible"


def test_assert_visible_records_fail_and_raises(monkeypatch):
    class FakeExpect:
        def __init__(self, locator):
            self.locator = locator

        def to_be_visible(self, timeout=30000):
            raise AssertionError("Element not visible")

    monkeypatch.setattr(reporter_module, "expect", lambda locator: FakeExpect(locator))

    reporter = Reporter()
    reporter.start_test("case:visible_fail", "visible fail test")

    with pytest.raises(AssertionError, match="Element not visible"):
        reporter.assert_visible(object(), "Dashboard loaded")

    step = reporter.results["case:visible_fail"]["steps"][-1]
    assert step["status"] == "FAIL"
    assert "Element not visible" in step["details"]
