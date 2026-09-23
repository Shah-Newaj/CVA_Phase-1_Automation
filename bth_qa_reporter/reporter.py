from __future__ import annotations

import json
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from playwright.sync_api import expect


class Reporter:
    """Reusable step, validation and evidence reporter for Python + Pytest + Playwright."""

    def __init__(self):
        self.current_test = None
        self.results: dict[str, dict] = {}
        self.output_dir = Path("test-reports")

    def configure(self, output_dir="test-reports"):
        self.output_dir = Path(output_dir)
        (self.output_dir / "screenshots").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "workers").mkdir(parents=True, exist_ok=True)

    def start(self):
        return time.perf_counter()

    def start_test(self, nodeid: str, name: str):
        self.current_test = {
            "nodeid": nodeid,
            "name": name,
            "outcome": "unknown",
            "duration": 0.0,
            "error": "",
            "steps": [],
            "logs": [],
            "metadata": {},
            "failure_screenshot": None,
        }
        self.results[nodeid] = self.current_test

    def finish_test(self, outcome: str, duration: float, error: str = ""):
        if self.current_test:
            self.current_test["outcome"] = outcome
            self.current_test["duration"] = duration
            self.current_test["error"] = error

    def _current_test(self):
        return self.current_test

    def metadata(self, **values):
        if self.current_test is not None:
            self.current_test.setdefault("metadata", {}).update(
                {k: v for k, v in values.items() if v is not None}
            )

    @contextmanager
    def step(self, name: str, details: str = ""):
        """Record an execution step and automatically determine PASS/FAIL.

        Example:
            with report.step("Login"):
                login.load()
                login.login(username, password)

        If the block raises an exception, the step is marked FAIL, a failure
        screenshot is attached when a Playwright page is available, and the
        original exception is re-raised so pytest still fails the test.
        """
        step = self._add(name, "INFO", details=details, return_step=True)
        try:
            yield step
        except Exception as exc:
            step["status"] = "FAIL"
            if not step.get("details"):
                step["details"] = str(exc)

            page = getattr(self, "_current_page", None)
            if page is not None and not step.get("screenshot"):
                try:
                    self.attach_screenshot(
                        page,
                        f"{name}_failure",
                        attach_to_failed_step=True,
                    )
                except Exception:
                    pass
            raise
        else:
            step["status"] = "PASS"

    def log(self, message, level="INFO"):
        """Record a console/log message against the active test."""
        test = self._current_test()
        if test is None:
            return
        test.setdefault("logs", []).append({
            "level": str(level).upper(),
            "message": str(message),
        })

    def assert_playwright(self, locator, condition: str, name: str, timeout: int = 30000):
        """Run Playwright's built-in expect() assertion and record it in the report."""
        label = name or f"Playwright assertion: {condition}"
        expected = condition
        actual = "not satisfied"
        try:
            if condition == "visible":
                expect(locator).to_be_visible(timeout=timeout)
                actual = "visible"
            elif condition == "enabled":
                expect(locator).to_be_enabled(timeout=timeout)
                actual = "enabled"
            elif condition == "hidden":
                expect(locator).to_be_hidden(timeout=timeout)
                actual = "hidden"
            else:
                raise ValueError(f"Unsupported Playwright condition: {condition}")
            self._add(label, "PASS", details=f"Playwright assertion passed: {condition}", expected=expected, actual=actual)
            return True
        except Exception as exc:
            self._add(label, "FAIL", details=str(exc), expected=expected, actual=actual)
            raise

    def assert_visible(self, locator, name: str, timeout: int = 30000):
        return self.assert_playwright(locator, "visible", name=name, timeout=timeout)

    def assert_enabled(self, locator, name: str, timeout: int = 30000):
        return self.assert_playwright(locator, "enabled", name=name, timeout=timeout)

    def assert_hidden(self, locator, name: str, timeout: int = 30000):
        return self.assert_playwright(locator, "hidden", name=name, timeout=timeout)

    def pass_step(self, name: str, details: str = ""):
        self._add(name, "PASS", details=details)

    def fail_step(self, name: str, details: str = ""):
        self._add(name, "FAIL", details=details)

    def validation(self, label: str, expected: Any, actual: Any, details: str = "", assert_result: bool = False):
        status = "PASS" if expected == actual else "FAIL"
        self._add(label, status, details=details, expected=expected, actual=actual)
        if assert_result and status == "FAIL":
            raise AssertionError(
                f"{label} validation failed | Expected: {expected!r} | Actual: {actual!r}"
            )
        return status == "PASS"

    def assert_validation(self, label: str, expected: Any, actual: Any, details: str = ""):
        return self.validation(label, expected, actual, details, assert_result=True)

    def tile_validation(self, tile_name: str, expected: Any, actual: Any, assert_result: bool = True):
        return self.validation(f"Tile: {tile_name}", expected, actual, assert_result=assert_result)

    def column_validation(self, column_name: str, expected: Any, actual: Any, assert_result: bool = True):
        return self.validation(f"Column: {column_name}", expected, actual, assert_result=assert_result)

    def table_validation(self, title: str, expected: Any, actual: Any, key: str | None = None, assert_result: bool = True):
        expected = expected or []
        actual = actual or []
        if isinstance(expected, dict):
            expected = [expected]
        if isinstance(actual, dict):
            actual = [actual]

        rows = []
        passed = True

        if key:
            e_map = {str(r.get(key)): r for r in expected}
            a_map = {str(r.get(key)): r for r in actual}
            row_keys = list(dict.fromkeys([*e_map.keys(), *a_map.keys()]))
            pairs = [(f"{k}", e_map.get(k, {}), a_map.get(k, {})) for k in row_keys]
        else:
            count = max(len(expected), len(actual))
            pairs = [
                (f"Row {i + 1}", expected[i] if i < len(expected) else {}, actual[i] if i < len(actual) else {})
                for i in range(count)
            ]

        for row_label, e_row, a_row in pairs:
            cols = list(dict.fromkeys([*e_row.keys(), *a_row.keys()]))
            for col in cols:
                e_val, a_val = e_row.get(col), a_row.get(col)
                ok = e_val == a_val
                passed &= ok
                rows.append({
                    "column": f"{row_label} / {col}",
                    "expected": e_val,
                    "actual": a_val,
                    "status": "PASS" if ok else "FAIL",
                })

        self._add(title, "PASS" if passed else "FAIL", details=json.dumps({"rows": rows}, default=str))

        if assert_result and not passed:
            failures = [r for r in rows if r["status"] == "FAIL"]
            raise AssertionError(f"{title} failed: {len(failures)} cell(s) do not match.")
        return passed

    def attach_screenshot(self, page, name="screenshot", attach_to_failed_step: bool = False):
        """Capture a screenshot.

        Normal screenshots are recorded as steps. Failure screenshots are attached to
        the last meaningful execution step and are also stored at test level.
        """
        if not self.current_test:
            return None

        safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in name)
        filename = f"{safe}_{int(time.time() * 1000)}.png"
        path = self.output_dir / "screenshots" / filename
        page.screenshot(path=str(path), full_page=True)
        rel = f"screenshots/{filename}"

        if attach_to_failed_step:
            # Attach to the most recent execution step instead of creating a new step.
            for step in reversed(self.current_test["steps"]):
                if step.get("status") in {"INFO", "PASS", "FAIL"}:
                    step["status"] = "FAIL"
                    step["screenshot"] = rel
                    break
            self.current_test["failure_screenshot"] = rel
        else:
            self._add(f"Screenshot: {name}", "INFO", screenshot=rel)

        return str(path)

    def _add(self, name, status, details="", expected=None, actual=None, screenshot=None, return_step=False):
        if self.current_test is None:
            return None
        step = {
            "name": name,
            "status": status,
            "details": details,
            "expected": expected,
            "actual": actual,
            "screenshot": screenshot,
        }
        self.current_test["steps"].append(step)
        return step if return_step else None

    def export_worker(self, path: str | Path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(list(self.results.values()), default=str, indent=2), encoding="utf-8")


report = Reporter()
