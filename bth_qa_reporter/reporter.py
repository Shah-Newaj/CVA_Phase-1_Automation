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
            "quality_scans": [],
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

    def add_quality_scan(self, result):
        """Store a serializable UI-quality scan result for the HTML report."""
        if self.current_test is None:
            return

        def issue_copy(issue):
            return dict(issue)

        scan = {
            "page_name": result.page_name,
            "url": result.url,
            "content_issues": [issue_copy(x) for x in result.content_issues],
            "language_issues": [issue_copy(x) for x in result.language_issues],
            "ui_issues": [issue_copy(x) for x in result.ui_issues],
            "scanner_warnings": [
                issue_copy(x)
                for x in getattr(result, "scanner_warnings", [])
            ],
            "total_issues": result.total_issues,
        }
        self.current_test.setdefault("quality_scans", []).append(scan)

    def attach_issue_screenshot(
        self,
        page,
        issue: dict,
        category: str,
        index: int,
        page_name: str,
    ):
        """        Capture full-page evidence with URL and exact issue highlighted.

        The page URL is shown in the report; the screenshot stays unobstructed
        so the highlighted element remains visible.
        """
        if not self.current_test:
            return None

        safe_page = "".join(
            c if c.isalnum() or c in "._-" else "_"
            for c in page_name
        )[:80]
        safe_category = "".join(
            c if c.isalnum() or c in "._-" else "_"
            for c in category.lower()
        )[:40]
        filename = (
            f"issue_{safe_page}_{safe_category}_{index}_"
            f"{int(time.time() * 1000)}.png"
        )
        path = self.output_dir / "screenshots" / filename
        rel = f"screenshots/{filename}"

        issue_type = str(issue.get("type", "UI Quality Issue"))
        issue_text = str(issue.get("element") or issue.get("text") or "<n/a>")
        message = str(issue.get("message") or "")
        suggestion = str(issue.get("suggestion") or "")
        target = issue.get("target")

        payload = {
            "url": page.url,
            "page_name": page_name,
            "category": category,
            "issue_type": issue_type,
            "issue_text": issue_text,
            "message": message,
            "suggestion": suggestion,
            "target": target[0] if isinstance(target, list) and target else target,
        }

        try:
            highlighted = page.evaluate(
                """
                (data) => {
                    const oldStyle = document.getElementById('__bth_issue_style');
                    const isVisible = el => {
                        if (!el) return false;
                        for (let current = el; current; current = current.parentElement) {
                            const style = getComputedStyle(current);
                            if (style.display === 'none'
                                || style.visibility === 'hidden'
                                || Number(style.opacity) === 0
                                || current.getAttribute('aria-hidden') === 'true'
                                || current.hasAttribute('inert')) return false;
                        }
                        return el.getClientRects().length > 0;
                    };
                    if (oldStyle) oldStyle.remove();
                    document.querySelectorAll('[data-bth-issue-highlight="1"]').forEach(el => {
                        el.removeAttribute('data-bth-issue-highlight');
                        el.style.removeProperty('outline');
                        el.style.removeProperty('outline-offset');
                        el.style.removeProperty('box-shadow');
                    });

                    let target = null;
                    if (data.target) {
                        try { target = document.querySelector(data.target); } catch (_) {}
                    }

                    const wanted = (data.issue_text || '').trim();
                    let issueRange = null;
                    if (!target && wanted) {
                        const walker = document.createTreeWalker(
                            document.querySelector('[data-bth-quality-scan-root]') || document.body,
                            NodeFilter.SHOW_TEXT,
                            {acceptNode: node => {
                                const value = (node.nodeValue || '');
                                const element = node.parentElement;
                                return isVisible(element)
                                    && !element.closest(
                                        'nav, aside, [role="navigation"], a.nav-link, tbody, tr, [role="row"], .table-rf-row'
                                    )
                                    && value.toLowerCase().includes(wanted.toLowerCase())
                                    ? NodeFilter.FILTER_ACCEPT
                                    : NodeFilter.FILTER_REJECT;
                            }}
                        );
                        const matches = [];
                        let node;
                        while ((node = walker.nextNode())) {
                            const value = node.nodeValue || '';
                            const start = value.toLowerCase().indexOf(wanted.toLowerCase());
                            if (start < 0) continue;
                            const before = value[start - 1] || '';
                            const after = value[start + wanted.length] || '';
                            if (/[a-z0-9_]/i.test(before)
                                || /[a-z0-9_]/i.test(after)) continue;
                            const parent = node.parentElement;
                            const nav = parent.closest(
                                    'nav, aside, [role="navigation"], a.nav-link'
                            );
                            const heading = parent.closest(
                                    'h1,h2,h3,h4,h5,h6,[role="heading"]'
                            );
                            const exactParent =
                                    (parent.innerText || '').trim().toLowerCase()
                                    === wanted.toLowerCase();
                            matches.push({
                                    node,
                                    start,
                                    score: (heading ? 100 : 0)
                                        + (exactParent ? 20 : 0)
                                        - (nav ? 100 : 0)
                                        - (parent.innerText || '').trim().length / 100
                            });
                        }
                        matches.sort((a, b) => b.score - a.score);
                        const match = matches[0];
                        const textNode = match && match.node;
                        if (textNode) {
                            issueRange = document.createRange();
                            issueRange.setStart(textNode, match.start);
                            issueRange.setEnd(textNode, match.start + wanted.length);
                            target = textNode.parentElement;
                        }
                    }

                    if (!target && wanted) {
                        const candidates = Array.from(document.querySelectorAll(
                            'button,a,input,label,span,div,h1,h2,h3,h4,h5,h6,td,th,p'
                        ));
                        const scanRoot = document.querySelector(
                            '[data-bth-quality-scan-root]'
                        );
                        target = candidates
                            .filter(el => {
                                const text = (el.innerText || el.value || el.getAttribute('aria-label') || '').trim();
                                if (!isVisible(el)
                                    || (scanRoot && !scanRoot.contains(el))
                                    || el.closest('nav, aside, [role="navigation"], a.nav-link, tbody, tr, [role="row"], .table-rf-row')
                                    || !text
                                    || text.length > Math.max(160, wanted.length * 8)) return false;
                                const index = text.toLowerCase().indexOf(wanted.toLowerCase());
                                if (index < 0) return false;
                                const before = text[index - 1] || '';
                                const after = text[index + wanted.length] || '';
                                return !/[a-z0-9_]/i.test(before)
                                    && !/[a-z0-9_]/i.test(after);
                            })
                            .sort((a,b) => {
                                const at = (a.innerText || a.value || '').trim().length;
                                const bt = (b.innerText || b.value || '').trim().length;
                                return at - bt;
                            })[0] || null;
                    }

                    const style = document.createElement('style');
                    style.id = '__bth_issue_style';
                    style.textContent = `
                        [data-bth-issue-highlight="1"] {
                            outline: 4px solid #e11d48 !important;
                            outline-offset: 4px !important;
                            box-shadow: 0 0 0 8px rgba(225,29,72,.22) !important;
                            position: relative !important;
                            z-index: 2147483640 !important;
                        }
                    `;
                    document.head.appendChild(style);

                    if (target) {
                        target.setAttribute('data-bth-issue-highlight', '1');
                        target.scrollIntoView({block: 'center', inline: 'center'});
                    }
                    if (issueRange && window.CSS && CSS.highlights && window.Highlight) {
                        const style = document.createElement('style');
                        style.id = '__bth_issue_text_style';
                        style.textContent = `
                            ::highlight(bthIssueText) {
                                background: #fff200;
                                color: #111;
                                text-decoration: underline 3px #e11d48;
                            }
                        `;
                        document.head.appendChild(style);
                        CSS.highlights.set('bthIssueText', new Highlight(issueRange));
                    }
                    return Boolean(target);
                }
                """,
                payload,
            )

            if not highlighted:
                raise LookupError(
                    f"Could not locate exact visible text {issue_text!r} "
                    "for screenshot evidence."
                )

            screenshot_error = None
            for attempt in range(2):
                try:
                    page.screenshot(
                        path=str(path),
                        full_page=True,
                        timeout=30000,
                    )
                    if not path.is_file() or path.stat().st_size == 0:
                        raise OSError("Screenshot file is missing or empty.")
                    screenshot_error = None
                    break
                except Exception as exc:
                    screenshot_error = exc
                    if attempt == 0:
                        page.wait_for_timeout(500)

            if screenshot_error is not None:
                raise screenshot_error
        finally:
            try:
                page.evaluate(
                    """
                    () => {
                        const style = document.getElementById('__bth_issue_style');
                        const textStyle = document.getElementById('__bth_issue_text_style');
                        if (style) style.remove();
                        if (textStyle) textStyle.remove();
                        if (window.CSS && CSS.highlights) {
                            CSS.highlights.delete('bthIssueText');
                        }
                        document.querySelectorAll('[data-bth-issue-highlight="1"]').forEach(el => {
                            el.removeAttribute('data-bth-issue-highlight');
                            el.style.removeProperty('outline');
                            el.style.removeProperty('outline-offset');
                            el.style.removeProperty('box-shadow');
                        });
                    }
                    """
                )
            except Exception:
                pass

        return rel

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
