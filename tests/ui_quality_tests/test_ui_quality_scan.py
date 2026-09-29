import pytest

from bth_qa_reporter import report
from pages.dashboard_page import Dashboard
from pages.login_page import LoginPage
from pages.sampling_page import SamplingPage
from ui_quality.scanner import UIQualityScanner


@pytest.mark.ui_quality
def test_sampling_management_ui_quality(page):
    """
    Baseline-free UI quality scan for Sampling Management.

    The test reuses the existing CVA login/dashboard POM and then scans
    the Sample Report Overview page for:
      - suspicious mixed capitalization such as 'OverView'
      - spelling/grammar issues through LanguageTool
      - button height/font/style outliers

    """

    login = LoginPage(page)
    dashboard = Dashboard(page)
    sampling = SamplingPage(page)

    with report.step("Login for UI quality scan"):
        login.load()
        login.login("SuperAdmin", "Welcome@2")
        report.assert_visible(
            login.userIcon,
            "User icon visible after login",
            timeout=15000,
        )

    with report.step("Select Country"):
        page.wait_for_timeout(3000)
        dashboard.select_country()

    with report.step("Select Project"):
        page.wait_for_timeout(3000)
        dashboard.select_project()

    with report.step("Open Sample Report Overview"):
        sampling.sampling.click()
        page.wait_for_timeout(1000)
        sampling.sample_report_overview.click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)

    scanner = UIQualityScanner(
        language=os.getenv("UI_QUALITY_LANGUAGE", "en-US")
    )

    with report.step("Run baseline-free UI quality scan"):
        result = scanner.scan(
            page,
            page_name="Sample Report Overview",
        )

    _log_section(
        "CONTENT / CAPITALIZATION",
        result.content_issues,
    )
    _log_section(
        "SPELLING / GRAMMAR",
        result.language_issues,
    )
    _log_section(
        "BUTTON / UI CONSISTENCY",
        result.ui_issues,
    )
    for category, issues in (
        ("CONTENT / CAPITALIZATION", result.content_issues),
        ("SPELLING / GRAMMAR", result.language_issues),
        ("BUTTON / UI CONSISTENCY", result.ui_issues),
    ):
        for index, issue in enumerate(issues, start=1):
            issue["evidence"] = report.attach_issue_screenshot(
                page,
                issue,
                category,
                index,
                result.page_name,
            )

    report.add_quality_scan(result)

    assert result.total_issues == 0, (
        f"UI quality scan found {result.total_issues} issue(s) "
        f"on {result.page_name}."
    )


def _log_section(title: str, issues: list[dict]) -> None:
    report.log(f"===== {title} =====", "UI-QUALITY")

    if not issues:
        report.log("PASS - no issues detected.", "UI-QUALITY")
        return

    for issue in issues:
        report.log(
            _format_issue(issue),
            "UI-QUALITY",
        )


def _format_issue(issue: dict) -> str:
    parts = [
        f"{issue.get('type', 'Issue')}",
        f"Element/Text: {issue.get('element') or issue.get('text') or '<n/a>'}",
        issue.get("message", ""),
    ]

    if issue.get("actual") is not None:
        parts.append(f"Actual: {issue['actual']}")

    if issue.get("expected") is not None:
        parts.append(f"Expected: {issue['expected']}")

    if issue.get("suggestion"):
        parts.append(f"Suggestion: {issue['suggestion']}")

    if issue.get("suggestions"):
        parts.append(
            "Suggestions: " + ", ".join(issue["suggestions"])
        )

    if issue.get("context"):
        parts.append(f"Context: {issue['context']}")

    return " | ".join(part for part in parts if part)
