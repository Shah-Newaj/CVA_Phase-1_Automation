from bth_qa_reporter.reporter import Reporter
from ui_quality.content_checker import ContentChecker
from ui_quality.language_checker import LanguageToolChecker
from ui_quality.scanner import ScanResult, UIQualityScanner


class _Body:
    def inner_text(self, timeout):
        return "Sample Report OverView"


class _Page:
    url = "https://example.test/SampleReportOverView"

    def locator(self, selector):
        assert selector == "body"
        return _Body()


class _UnavailableLanguageTool:
    def check(self, text, language):
        raise OSError("certificate verify failed")


class _NoButtonIssues:
    def scan_buttons(self, page):
        return []


def test_mixed_capitalization_suggests_expected_case():
    issue = ContentChecker().find_mixed_capitalization(
        "Sample Report OverView"
    )[0]

    assert issue["text"] == "OverView"
    assert issue["expected"] == "Overview"


def test_language_tool_failure_is_a_warning_not_an_issue():
    scanner = UIQualityScanner(enable_language_tool=True)
    scanner.language_checker = _UnavailableLanguageTool()
    scanner.ui_checker = _NoButtonIssues()

    result = scanner.scan(_Page(), page_name="Sample Report Overview")

    assert result.total_issues == 1
    assert result.content_issues[0]["expected"] == "Overview"
    assert result.language_issues == []
    assert result.scanner_warnings[0]["type"] == "LanguageTool Warning"


def test_reporter_serializes_only_the_three_required_issue_groups():
    reporter = Reporter()
    reporter.start_test("ui-quality", "UI quality")
    result = ScanResult(
        page_name="Sample Report Overview",
        url="https://example.test/SampleReportOverView",
        content_issues=[{"type": "Mixed Capitalization", "text": "OverView"}],
    )

    reporter.add_quality_scan(result)

    scan = reporter.current_test["quality_scans"][0]
    assert set(scan) == {
        "page_name",
        "url",
        "content_issues",
        "language_issues",
        "ui_issues",
        "scanner_warnings",
        "total_issues",
    }
    assert scan["total_issues"] == 1


def test_language_tool_uses_context_offset_and_deduplicates_matches(monkeypatch):
    class _Response:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "matches": [
                    {
                        "offset": 100,
                        "length": 10,
                        "context": {
                            "text": "... Beneficary was approved ...",
                            "offset": 4,
                        },
                        "message": "Possible spelling mistake",
                        "replacements": [{"value": "Beneficiary"}],
                    },
                    {
                        "offset": 200,
                        "length": 10,
                        "context": {
                            "text": "... Beneficary is pending ...",
                            "offset": 4,
                        },
                        "message": "Possible spelling mistake",
                        "replacements": [{"value": "Beneficiary"}],
                    },
                    {
                        "offset": 300,
                        "length": 5,
                        "context": {"text": "... text ..."},
                        "message": "Invalid empty match",
                        "replacements": [],
                    },
                ]
            }

    monkeypatch.setattr(
        "ui_quality.language_checker.requests.post",
        lambda *args, **kwargs: _Response(),
    )

    issues = LanguageToolChecker().check("Beneficary text")

    assert len(issues) == 1
    assert issues[0]["text"] == "Beneficary"
    assert issues[0]["suggestions"] == ["Beneficiary"]


def test_content_checker_ignores_application_ids_and_person_names():
    issues = ContentChecker().find_mixed_capitalization(
        "Sample Report OverView AdminSuper AfN Habib Saffat"
    )

    assert [issue["text"] for issue in issues] == ["OverView"]


def test_language_tool_ignores_domain_and_person_metadata(monkeypatch):
    class _Response:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "matches": [
                    {
                        "length": 12,
                        "context": {
                            "text": "Current Domain: sci-co-niger Language",
                            "offset": 16,
                        },
                        "message": "Possible spelling mistake",
                        "replacements": [{"value": "sci-co-Niger"}],
                    },
                    {
                        "length": 5,
                        "context": {
                            "text": "Submitted By: Saffat Habib",
                            "offset": 14,
                        },
                        "message": "Possible spelling mistake",
                        "replacements": [{"value": "Jaffa"}],
                    },
                ]
            }

    monkeypatch.setattr(
        "ui_quality.language_checker.requests.post",
        lambda *args, **kwargs: _Response(),
    )

    issues = LanguageToolChecker().check(
        "Current Domain: sci-co-niger Submitted By: Saffat Habib"
    )

    assert issues == []


def test_issue_evidence_screenshot_is_written_and_targets_page_content(page, tmp_path):
    reporter = Reporter()
    reporter.configure(tmp_path)
    reporter.start_test("issue-evidence", "Issue evidence")
    page.set_content(
        """
        <nav><a class="nav-link">OverView</a></nav>
        <main data-bth-quality-scan-root="1">
          <h2>Sample Report <span>OverView</span></h2>
        </main>
        """
    )

    evidence = reporter.attach_issue_screenshot(
        page,
        {
            "type": "Mixed Capitalization",
            "text": "OverView",
            "message": "Incorrect capitalization",
        },
        "CONTENT / CAPITALIZATION",
        1,
        "Sample Report Overview",
    )

    assert evidence is not None
    image_path = tmp_path / evidence
    assert image_path.is_file()
    assert image_path.stat().st_size > 0
    assert page.locator("main h2").inner_text() == "Sample Report OverView"


def test_ui_checker_detects_wrapped_header_save_control(page):
    from ui_quality.ui_consistency_checker import UIConsistencyChecker

    page.set_content(
        """
        <div class="rf-form-header-action-save" style="
             width:31.46875px;height:30px;border-radius:5px;
             background:rgb(69,179,131);color:white;
             font-size:15px;font-weight:600">
          <div class="rf-form-header-action-save-only">Save</div>
        </div>
        """
    )

    issues = UIConsistencyChecker().scan_buttons(page)

    assert any(
        issue["type"] == "UI Spacing Anomaly"
        and issue["element"] == "Save"
        for issue in issues
    )


def test_ui_checker_does_not_flag_add_new_icon_as_text_wrapping(page):
    from ui_quality.ui_consistency_checker import UIConsistencyChecker

    page.set_content(
        """
        <button class="button-rf" style="width:auto;height:30px;padding:3px 10px;">
            <i class="fa fa-plus"></i><span>Add New</span>
        </button>
        """
    )

    issues = UIConsistencyChecker().scan_buttons(page)

    assert not any(
        issue["type"] == "Button Text Wrapping"
        and issue["element"] == "Add New"
        for issue in issues
    )


def test_ui_checker_does_not_flag_working_save(page):
    from ui_quality.ui_consistency_checker import UIConsistencyChecker

    page.set_content(
        """
        <div class="rf-form-header-action-save" style="
             width:51.46875px;height:30px;padding:3px 10px;
             border-radius:5px;background:rgb(69,179,131);color:white;
             font-size:15px;font-weight:600">
          <div class="rf-form-header-action-save-only">Save</div>
        </div>
        """
    )

    issues = UIConsistencyChecker().scan_buttons(page)

    assert not any(
        issue.get("element") == "Save"
        and issue.get("type") == "UI Spacing Anomaly"
        for issue in issues
    )
