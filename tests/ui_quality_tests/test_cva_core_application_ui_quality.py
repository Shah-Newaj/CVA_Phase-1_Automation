from __future__ import annotations

import os
from typing import Callable

import pytest

from bth_qa_reporter import report

from pages.dashboard_page import Dashboard
from pages.login_page import LoginPage
from pages.beneficiaryList_page import BeneficiaryListPage
from pages.paymentList_page import PaymentListPage
from pages.sampling_page import SamplingPage
from pages.configuration_page import ConfigurationPage

from ui_quality.scanner import ScanResult, UIQualityScanner


# Edit these two values when this test file needs a different report heading.
REPORT_TITLE = "CVA_Phase_1_QA_Automation_Report"
REPORT_SUBTITLE = "URL: https://cashapp.savethechildren.net/"
REPORT_TEST_NAME = "Spelling and UI Issues"
REPORT_TEST_FILE_NAME = "Environment: Prod | Country: Niger CVA | Project: BMZ RESA Training | Browser: Chromium"
os.environ["BTH_REPORT_TITLE"] = REPORT_TITLE
os.environ["BTH_REPORT_SUBTITLE"] = REPORT_SUBTITLE


# ============================================================
# Configuration
# ============================================================

LANGUAGE = os.getenv(
    "UI_QUALITY_LANGUAGE",
    "en-US",
)

# Confirmed popup close locator from the CVA application.
POPUP_CLOSE_LOCATOR = "//i[@class='fa-solid fa-xmark']"


# ============================================================
# Main UI Quality Test
# ============================================================

@pytest.mark.ui_quality
def test_cva_core_application_ui_quality(page):
    """
    Phase-1 full core CVA application UI-quality scan.

    Navigation follows the same Page Object Model used by the
    functional CVA automation.

    Covered pages:

        1. Dashboard

        2. Beneficiary List Overview
        3. Beneficiary List Approval

        4. Payment List Overview
        5. Payment List Approval
        6. Payment Tracking Overview

        7. Sample Report Overview
        8. Sample Report Approval

    Safe modal checks:

        - Create New Beneficiary List
        - Create New Payment List
        - Create New Sample
        - Project Criteria Setup
        - Country Project Mapper

    The test DOES NOT:

        - create business data
        - save business data
        - submit business data
        - approve business data
        - delete business data

    Excluded from this Phase-1 scan:

        - Fetch Data
        - Sync Data
        - Accessibility scanning

    UI-quality categories:

        - Mixed capitalization
        - Spelling / grammar
        - UI consistency
        - Visual issue evidence
    """

    # ========================================================
    # Page Objects
    # ========================================================

    login = LoginPage(page)
    dashboard = Dashboard(page)
    beneficiary = BeneficiaryListPage(page)
    payment = PaymentListPage(page)
    sampling = SamplingPage(page)
    configuration = ConfigurationPage(page)

    scanner = UIQualityScanner(
        language=LANGUAGE,
    )

    page_results: list[ScanResult] = []
    navigation_errors: list[str] = []

    # ========================================================
    # Login
    # ========================================================

    with report.step(
        "Login for core CVA UI quality scan"
    ):

        login.load()

        login.login("SuperAdmin", "Welcome@2")
        report.assert_visible(
            login.userIcon,
            "User icon visible after login",
            timeout=15000,
        )
        page.wait_for_timeout(10000)

    # ========================================================
    # Select Country
    # ========================================================

    with report.step("Select Country"):

        try:

            report.assert_enabled(
                dashboard.country_drp,
                "Country dropdown enabled",
            )
            dashboard.select_country()

            page.wait_for_timeout(1000)

        except Exception as exc:

            navigation_errors.append(
                f"Select Country failed: {exc}"
            )

            report.log(
                f"Select Country failed: {exc}",
                "UI-QUALITY",
            )

    # ========================================================
    # Select Project
    # ========================================================

    with report.step("Select Project"):

        try:

            dashboard.select_project()
            page.wait_for_load_state("networkidle")

        except Exception as exc:

            navigation_errors.append(
                f"Select Project failed: {exc}"
            )

            report.log(
                f"Select Project failed: {exc}",
                "UI-QUALITY",
            )

    # ========================================================
    # 1. Dashboard
    # ========================================================

    scan_current_page(
        page=page,
        scanner=scanner,
        page_results=page_results,
        page_name="Dashboard",
        navigation_errors=navigation_errors,
    )

    # ========================================================
    # 2. Beneficiary List Overview
    # ========================================================

    beneficiary_overview_open = navigate_and_scan(
        page=page,
        scanner=scanner,
        page_results=page_results,
        navigation_errors=navigation_errors,
        page_name="Beneficiary List Overview",
        navigate=lambda: open_beneficiary_overview(
            beneficiary
        ),
    )

    # Safe Create New Beneficiary List modal

    if beneficiary_overview_open:
        scan_safe_modal(
            page=page,
            scanner=scanner,
            page_results=page_results,
            navigation_errors=navigation_errors,
            page_name="Beneficiary List Overview",
            modal_name="Create New Beneficiary List",
            open_action=lambda: beneficiary.create_btn.click(timeout=10000),
        )

    # ========================================================
    # 3. Beneficiary List Approval
    # ========================================================

    navigate_and_scan(
        page=page,
        scanner=scanner,
        page_results=page_results,
        navigation_errors=navigation_errors,
        page_name="Beneficiary List Approval",
        navigate=lambda: open_beneficiary_approval(
            beneficiary
        ),
    )

    # ========================================================
    # 4. Payment List Overview
    # ========================================================

    payment_overview_open = navigate_and_scan(
        page=page,
        scanner=scanner,
        page_results=page_results,
        navigation_errors=navigation_errors,
        page_name="Payment List Overview",
        navigate=lambda: open_payment_overview(
            payment
        ),
    )

    # Safe Create New Payment List modal

    if payment_overview_open:
        scan_safe_modal(
            page=page,
            scanner=scanner,
            page_results=page_results,
            navigation_errors=navigation_errors,
            page_name="Payment List Overview",
            modal_name="Create New Payment List",
            open_action=lambda: payment.create_btn.click(timeout=10000),
        )

    # ========================================================
    # 5. Payment List Approval
    # ========================================================

    navigate_and_scan(
        page=page,
        scanner=scanner,
        page_results=page_results,
        navigation_errors=navigation_errors,
        page_name="Payment List Approval",
        navigate=lambda: open_payment_approval(
            payment
        ),
    )

    # ========================================================
    # 6. Payment Tracking Overview
    # ========================================================

    navigate_and_scan(
        page=page,
        scanner=scanner,
        page_results=page_results,
        navigation_errors=navigation_errors,
        page_name="Payment Tracking Overview",
        navigate=lambda: open_payment_tracking(
            payment
        ),
    )

    # ========================================================
    # 7. Sample Report Overview
    # ========================================================

    sample_overview_open = navigate_and_scan(
        page=page,
        scanner=scanner,
        page_results=page_results,
        navigation_errors=navigation_errors,
        page_name="Sample Report Overview",
        navigate=lambda: open_sample_overview(
            sampling
        ),
    )

    # Safe Create New Sample modal

    if sample_overview_open:
        scan_safe_modal(
            page=page,
            scanner=scanner,
            page_results=page_results,
            navigation_errors=navigation_errors,
            page_name="Sample Report Overview",
            modal_name="Create New Sample",
            open_action=lambda: sampling.create_btn.click(timeout=10000),
        )

    # ========================================================
    # 8. Sample Report Approval
    # ========================================================

    navigate_and_scan(
        page=page,
        scanner=scanner,
        page_results=page_results,
        navigation_errors=navigation_errors,
        page_name="Sample Report Approval",
        navigate=lambda: open_sample_approval(
            sampling
        ),
    )

    # ========================================================
    # 9. Configuration: Project Criteria Setup
    # ========================================================

    criteria_open = navigate_and_scan(
        page=page,
        scanner=scanner,
        page_results=page_results,
        navigation_errors=navigation_errors,
        page_name="Project Criteria Setup List",
        navigate=lambda: open_project_criteria(configuration),
    )

    if criteria_open:
        def open_project_criteria_add_new():
            add_new = configuration.get_visible_add_new()

            if add_new is None:
                raise RuntimeError(
                    "Project Criteria Setup: "
                    "visible/enabled 'Add New' button could not be located."
                )

            add_new.scroll_into_view_if_needed()

            add_new.click(timeout=10000)

        scan_safe_modal(
            page=page,
            scanner=scanner,
            page_results=page_results,
            navigation_errors=navigation_errors,
            page_name="Project Criteria Setup List",
            modal_name="Project Criteria Setup",
            open_action=open_project_criteria_add_new,
        )


    # ========================================================
    # 10. Configuration: Country Project Mapper
    # ========================================================

    country_mapper_open = navigate_and_scan(
        page=page,
        scanner=scanner,
        page_results=page_results,
        navigation_errors=navigation_errors,
        page_name="Country Project Mapper List",
        navigate=lambda: open_country_project_mapper(configuration),
    )

    # --------------------------------------------------------
    # Safe Country Project Mapper Add New modal
    # --------------------------------------------------------
    #
    # This is intentionally handled the same way as the
    # Project Criteria Setup modal.
    #
    # The modal must be opened so the scanner can inspect
    # controls inside it, especially the Save button.
    #
    # No data is entered and Save is NOT clicked.
    # --------------------------------------------------------

    if country_mapper_open:

        def open_country_project_mapper_add_new():
            add_new = configuration.get_visible_add_new()

            if add_new is None:
                raise RuntimeError(
                    "Country Project Mapper: "
                    "visible/enabled 'Add New' button could not be located."
                )

            add_new.scroll_into_view_if_needed()

            add_new.click(timeout=10000)

        scan_safe_modal(
            page=page,
            scanner=scanner,
            page_results=page_results,
            navigation_errors=navigation_errors,
            page_name="Country Project Mapper List",
            modal_name="Country Project Mapper",
            open_action=open_country_project_mapper_add_new,
        )

    # ========================================================
    # Final Summary
    # ========================================================

    total_issues = sum(
        result.total_issues
        for result in page_results
    )

    total_warnings = sum(
        len(getattr(result, "scanner_warnings", []))
        for result in page_results
    )

    log_application_summary(
        page_results=page_results,
        navigation_errors=navigation_errors,
        total_warnings=total_warnings,
    )

    # ========================================================
    # Navigation errors
    # ========================================================

    if navigation_errors:

        report.log(
            "===== NAVIGATION / FLOW WARNINGS =====",
            "UI-QUALITY",
        )

        for error in navigation_errors:

            report.log(
                error,
                "UI-QUALITY",
            )

    # ========================================================
    # Final Result
    # ========================================================

    report.log(
        f"TOTAL PAGES / MODALS SCANNED: "
        f"{len(page_results)}",
        "UI-QUALITY",
    )

    report.log(
        f"TOTAL UI QUALITY ISSUES: "
        f"{total_issues}",
        "UI-QUALITY",
    )

    report.log(
        f"TOTAL SCANNER WARNINGS: "
        f"{total_warnings}",
        "UI-QUALITY",
    )

    # Navigation errors are treated separately from
    # application UI defects.

    assert not navigation_errors, (
        "CVA UI-quality scan encountered "
        "navigation/flow problems:\n"
        + "\n".join(navigation_errors)
    )

    assert total_issues == 0, (
        f"CVA UI-quality scan found "
        f"{total_issues} application UI-quality issue(s)."
    )


# ============================================================
# Generic Page Scan
# ============================================================

def scan_current_page(
    page,
    scanner: UIQualityScanner,
    page_results: list[ScanResult],
    page_name: str,
    navigation_errors: list[str],
) -> bool:

    with report.step(
        f"Scan UI quality: {page_name}"
    ):

        try:

            wait_for_page_ready(page)

            result = scanner.scan(
                page,
                page_name=page_name,
            )

            for category, issues in (
                ("CONTENT / CAPITALIZATION", result.content_issues),
                ("SPELLING / GRAMMAR", result.language_issues),
                ("BUTTON / UI CONSISTENCY", result.ui_issues),
            ):
                for index, issue in enumerate(issues, start=1):
                    try:
                        issue["evidence"] = report.attach_issue_screenshot(
                            page,
                            issue,
                            category,
                            index,
                            page_name,
                        )
                    except Exception as exc:
                        warning = {
                            "type": "Evidence Warning",
                            "message": (
                                f"Could not capture evidence for "
                                f"{issue.get('type', 'issue')}: {exc}"
                            ),
                            "page_name": page_name,
                            "url": page.url,
                        }
                        result.scanner_warnings.append(warning)
                        report.log(warning["message"], "UI-QUALITY")

            page_results.append(result)
            report.add_quality_scan(result)

            log_page_result(result)
            clear_scan_root(page)
            return True

        except Exception as exc:

            navigation_errors.append(
                f"{page_name}: UI-quality scan failed: {exc}"
            )

            report.log(
                f"{page_name}: scan failed: {exc}",
                "UI-QUALITY",
            )
            clear_scan_root(page)
            return False


def clear_scan_root(page) -> None:
    page.locator("[data-bth-quality-scan-root]").evaluate_all(
        "elements => elements.forEach(element => "
        "element.removeAttribute('data-bth-quality-scan-root'))"
    )


# ============================================================
# Navigation + Scan
# ============================================================

def navigate_and_scan(
    page,
    scanner: UIQualityScanner,
    page_results: list[ScanResult],
    navigation_errors: list[str],
    page_name: str,
    navigate: Callable[[], None],
) -> bool:

    with report.step(
        f"Open menu page: {page_name}"
    ):

        try:

            navigate()

            wait_for_page_ready(page)

        except Exception as exc:

            navigation_errors.append(
                f"{page_name}: navigation failed: {exc}"
            )

            report.log(
                f"{page_name}: navigation failed: {exc}",
                "UI-QUALITY",
            )

            return False

    return scan_current_page(
        page=page,
        scanner=scanner,
        page_results=page_results,
        page_name=page_name,
        navigation_errors=navigation_errors,
    )


# ============================================================
# Safe Modal Scan
# ============================================================

def scan_safe_modal(
    page,
    scanner: UIQualityScanner,
    page_results: list[ScanResult],
    navigation_errors: list[str],
    page_name: str,
    modal_name: str,
    open_action: Callable[[], None],
) -> None:

    with report.step(
        f"Open safe modal: {modal_name}"
    ):

        try:

            open_action()

            page.wait_for_timeout(1000)
            page.locator(POPUP_CLOSE_LOCATOR).first.wait_for(
                state="visible",
                timeout=10000,
            )

            wait_for_page_ready(
                page,
                allow_network_idle=False,
            )

        except Exception as exc:

            navigation_errors.append(
                f"{modal_name}: unable to open modal: {exc}"
            )

            report.log(
                f"{modal_name}: unable to open modal: {exc}",
                "UI-QUALITY",
            )

            return

    # --------------------------------------------------------
    # Scan modal
    # --------------------------------------------------------

    modal_page_name = (
        f"{page_name} - {modal_name}"
    )

    try:
        scan_current_page(
            page=page,
            scanner=scanner,
            page_results=page_results,
            page_name=modal_page_name,
            navigation_errors=navigation_errors,
        )
    finally:
        close_cva_popup(
            page=page,
            popup_name=modal_name,
            navigation_errors=navigation_errors,
        )


# ============================================================
# Popup Close
# ============================================================

def close_cva_popup(
    page,
    popup_name: str,
    navigation_errors: list[str],
) -> bool:
    """
    Close CVA modal using the confirmed application locator:

        //i[@class='fa-solid fa-xmark']

    The locator is intentionally restricted to the visible element.

    We do not use Escape or page reload as the first option because
    the application has a dedicated X close button.
    """

    close_locator = page.locator(POPUP_CLOSE_LOCATOR)

    try:

        count = close_locator.count()

    except Exception as exc:

        navigation_errors.append(
            f"{popup_name}: unable to inspect close button: {exc}"
        )

        return False

    if count == 0:

        navigation_errors.append(
            f"{popup_name}: "
            f"close button not found using "
            f"{POPUP_CLOSE_LOCATOR}"
        )

        return False

    # --------------------------------------------------------
    # Find a visible close button
    # --------------------------------------------------------

    clicked_locator = None

    for index in range(count):

        try:

            candidate = close_locator.nth(index)

            if not candidate.is_visible():
                continue

            candidate.scroll_into_view_if_needed()

            candidate.click(timeout=10000)
            clicked_locator = candidate

            break

        except Exception as exc:
            navigation_errors.append(
                f"{popup_name}: close action failed: {exc}"
            )
            return False

    if clicked_locator is None:

        navigation_errors.append(
            f"{popup_name}: "
            f"unable to click close button."
        )

        return False

    try:
        clicked_locator.wait_for(state="hidden", timeout=5000)
        page.locator(".modal-rf-backarea:visible").wait_for(
            state="hidden",
            timeout=5000,
        )
    except Exception as exc:
        navigation_errors.append(
            f"{popup_name}: close button was clicked, but closure "
            f"could not be confirmed: {exc}"
        )
        return False

    report.log(
        f"{popup_name}: closed successfully.",
        "UI-QUALITY",
    )
    return True


# ============================================================
# Application Ready
# ============================================================

def wait_for_page_ready(
    page,
    allow_network_idle: bool = True,
) -> None:

    try:

        page.wait_for_load_state(
            "domcontentloaded",
            timeout=15000,
        )

    except Exception:
        pass

    if allow_network_idle:

        try:

            page.wait_for_load_state(
                "networkidle",
                timeout=15000,
            )

        except Exception:
            # CVA contains ongoing requests / SignalR activity,
            # therefore networkidle is allowed to time out.
            pass

    loading_texts = ("please wait",)
    if not page.locator(POPUP_CLOSE_LOCATOR).is_visible():
        loading_texts = (*loading_texts, "Loading...")

    for loading_text in loading_texts:
        loading = page.get_by_text(loading_text, exact=True)
        for index in range(loading.count()):
            indicator = loading.nth(index)
            if indicator.is_visible():
                indicator.wait_for(state="hidden", timeout=45000)

    page.wait_for_timeout(1000)


# ============================================================
# Beneficiary Navigation
# ============================================================

def open_beneficiary_overview(
    beneficiary: BeneficiaryListPage,
) -> None:
    open_menu_subsection(
        beneficiary.beneficiarylist,
        beneficiary.beneficiarylist_overview,
    )


def open_beneficiary_approval(
    beneficiary: BeneficiaryListPage,
) -> None:

    open_menu_subsection(
        beneficiary.beneficiarylist,
        beneficiary.benef_list_approval,
    )


# ============================================================
# Payment Navigation
# ============================================================

def open_payment_overview(
    payment: PaymentListPage,
) -> None:

    open_menu_subsection(
        payment.paymentlist,
        payment.paymentlist_overview,
    )


def open_payment_approval(
    payment: PaymentListPage,
) -> None:

    open_menu_subsection(
        payment.paymentlist,
        payment.payment_list_approval,
    )


def open_payment_tracking(
    payment: PaymentListPage,
) -> None:

    open_menu_subsection(
        payment.paymentlist,
        payment.payment_tracking_overview,
    )


# ============================================================
# Sampling Navigation
# ============================================================

def open_sample_overview(
    sampling: SamplingPage,
) -> None:

    open_menu_subsection(
        sampling.sampling,
        sampling.sample_report_overview,
    )


def open_sample_approval(
    sampling: SamplingPage,
) -> None:

    open_menu_subsection(
        sampling.sampling,
        sampling.sample_report_approval,
    )


def open_project_criteria(configuration: ConfigurationPage) -> None:
    open_menu_subsection(
        configuration.configuration,
        configuration.project_criteria_setup,
    )


def open_country_project_mapper(configuration: ConfigurationPage) -> None:
    open_menu_subsection(
        configuration.configuration,
        configuration.country_project_mapper,
    )


def open_menu_subsection(menu, subsection) -> None:
    if not subsection.is_visible():
        menu.click(timeout=10000)
        subsection.wait_for(state="visible", timeout=10000)
    subsection.click(timeout=10000)


# ============================================================
# Page Result Logging
# ============================================================

def log_page_result(
    result: ScanResult,
) -> None:

    report.log(
        f"===== {result.page_name} =====",
        "UI-QUALITY",
    )

    report.log(
        f"URL: {result.url}",
        "UI-QUALITY",
    )

    # --------------------------------------------------------
    # Content / capitalization
    # --------------------------------------------------------

    log_issue_section(
        "CONTENT / CAPITALIZATION",
        result.content_issues,
    )

    # --------------------------------------------------------
    # Spelling / grammar
    # --------------------------------------------------------

    log_issue_section(
        "SPELLING / GRAMMAR",
        result.language_issues,
    )

    # --------------------------------------------------------
    # UI consistency
    # --------------------------------------------------------

    log_issue_section(
        "BUTTON / UI CONSISTENCY",
        result.ui_issues,
    )

    # Accessibility intentionally removed.


# ============================================================
# Issue Section Logging
# ============================================================

def log_issue_section(
    title: str,
    issues: list[dict],
) -> None:

    report.log(
        f"===== {title} =====",
        "UI-QUALITY",
    )

    if not issues:

        report.log(
            "PASS - no issues detected.",
            "UI-QUALITY",
        )

        return

    for issue in issues:

        report.log(
            format_issue(issue),
            "UI-QUALITY",
        )


# ============================================================
# Issue Formatting
# ============================================================

def format_issue(
    issue: dict,
) -> str:

    parts = [
        f"Type: {issue.get('type', 'Issue')}",
    ]

    element = (
        issue.get("element")
        or issue.get("text")
        or "<n/a>"
    )

    parts.append(
        f"Element/Text: {element}"
    )

    if issue.get("message"):

        parts.append(
            issue["message"]
        )

    if issue.get("actual") is not None:

        parts.append(
            f"Actual: {issue['actual']}"
        )

    if issue.get("expected") is not None:

        parts.append(
            f"Expected: {issue['expected']}"
        )

    if issue.get("suggestion"):

        parts.append(
            f"Suggestion: {issue['suggestion']}"
        )

    if issue.get("suggestions"):

        suggestions = issue["suggestions"]

        if isinstance(
            suggestions,
            list,
        ):

            parts.append(
                "Suggestions: "
                + ", ".join(
                    str(item)
                    for item in suggestions
                )
            )

    if issue.get("context"):

        parts.append(
            f"Context: {issue['context']}"
        )

    # Evidence path, when provided by the scanner.

    evidence = (
        issue.get("screenshot")
        or issue.get("evidence")
        or issue.get("evidence_path")
    )

    if evidence:

        parts.append(
            f"Evidence: {evidence}"
        )

    if issue.get("url"):

        parts.append(
            f"URL: {issue['url']}"
        )

    return " | ".join(
        str(part)
        for part in parts
        if part
    )


# ============================================================
# Application Summary
# ============================================================

def log_application_summary(
    page_results: list[ScanResult],
    navigation_errors: list[str],
    total_warnings: int,
) -> None:

    report.log(
        "========================================",
        "UI-QUALITY",
    )

    report.log(
        "CVA UI QUALITY SCAN SUMMARY",
        "UI-QUALITY",
    )

    report.log(
        "========================================",
        "UI-QUALITY",
    )

    report.log(
        f"Pages / Modals scanned: "
        f"{len(page_results)}",
        "UI-QUALITY",
    )

    total_issues = sum(
        result.total_issues
        for result in page_results
    )

    report.log(
        f"Total UI-quality issues: "
        f"{total_issues}",
        "UI-QUALITY",
    )

    report.log(
        f"Scanner warnings: "
        f"{total_warnings}",
        "UI-QUALITY",
    )

    report.log(
        f"Navigation / flow warnings: "
        f"{len(navigation_errors)}",
        "UI-QUALITY",
    )

    # --------------------------------------------------------
    # Per-page summary
    # --------------------------------------------------------

    for result in page_results:

        report.log(
            f"{result.page_name} | "
            f"Issues: {result.total_issues} | "
            f"URL: {result.url}",
            "UI-QUALITY",
        )