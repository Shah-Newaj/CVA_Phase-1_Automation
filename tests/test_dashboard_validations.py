import re
import time
import os
from urllib.parse import urljoin

from bth_qa_reporter import report
from pages.dashboard_page import Dashboard
from pages.login_page import LoginPage


# Edit these two values when this test file needs a different report heading.
REPORT_TITLE = "CVA_Phase_1_QA_Automation_Report"
REPORT_SUBTITLE = "URL: https://cashapp.savethechildren.net/"
REPORT_TEST_NAME = "Tile_Data_Validation"
REPORT_TEST_FILE_NAME = "Environment: Prod | Country: Niger CVA | Project: BMZ RESA Training | Browser: Chromium"
os.environ["BTH_REPORT_TITLE"] = REPORT_TITLE
os.environ["BTH_REPORT_SUBTITLE"] = REPORT_SUBTITLE

# Application pages and expected dashboard context.
HOUSEHOLD_DATA_URL = "https://cashapp.savethechildren.net/MasterHouseholdData"
BENEFICIARY_OVERVIEW_URL = "https://cashapp.savethechildren.net/BeneficiaryListOverView"
PAYMENT_TRACKING_URL = "https://cashapp.savethechildren.net/PaymentTrackingOverview"
EXPECTED_DOMAIN = "sci-co-niger"
EXPECTED_COUNTRY = "Niger CVA"
EXPECTED_PROJECT = "BMZ RESA Training"

# Record a tile result and attach evidence without stopping later checks.
def _record_tile_check(page, failures, name, expected, actual):
    passed = report.tile_validation(
        name,
        expected=expected,
        actual=actual,
        assert_result=False,
    )
    if not passed:
        failures.append(f"{name}: expected {expected!r}, actual {actual!r}")
        report.attach_screenshot(
            page,
            f"{name}_failure",
            attach_to_failed_step=True,
        )

# Extract the last numeric value displayed inside a dashboard tile.
def _tile_value(page, label: str) -> str:
    label_locator = page.get_by_text(label, exact=False).first
    label_locator.wait_for(state="visible", timeout=60000)
    card = label_locator
    for _ in range(4):
        card = card.locator("xpath=..")
        card_text = card.inner_text()
        values = re.findall(r"-?\d+(?:\.\d+)?", card_text)
        if values:
            return values[-1]
    raise AssertionError(f"No numeric value found for dashboard tile: {label}")

# Wait for an integer tile value after loading overlays disappear.
def _wait_for_tile_value(page, label: str) -> int:
    deadline = time.monotonic() + 60000 / 1000
    while time.monotonic() < deadline:
        loading = page.get_by_text("Loading...", exact=True)
        loading_visible = any(item.is_visible() for item in loading.all())
        if not loading_visible:
            try:
                return int(float(_tile_value(page, label)))
            except (AssertionError, ValueError):
                pass
        page.wait_for_timeout(1000)
    raise AssertionError(f"Timed out waiting for dashboard tile data: {label}")

# Wait for a decimal or negative numeric tile value.
def _wait_for_numeric_tile_value(page, label: str) -> float:
    deadline = time.monotonic() + 120
    while time.monotonic() < deadline:
        loading = page.get_by_text("Loading...", exact=True)
        loading_visible = any(item.is_visible() for item in loading.all())
        if not loading_visible:
            try:
                return float(_tile_value(page, label))
            except (AssertionError, ValueError):
                pass
        page.wait_for_timeout(1000)
    raise AssertionError(f"Timed out waiting for dashboard tile data: {label}")

# Wait for a tile that must contain a non-zero value.
def _wait_for_nonzero_tile_value(page, label: str) -> int:
    deadline = time.monotonic() + 180
    actual_value = ""
    while time.monotonic() < deadline:
        actual_value = _tile_value(page, label)
        if int(float(actual_value)) > 0:
            return int(float(actual_value))
        page.wait_for_timeout(1000)
    raise AssertionError(
        f"Timed out waiting for {label!r} to load a non-zero value; "
        f"last value was {actual_value!r}."
    )

# Read and verify a selected Domain, Country, or Project value.
def _selected_value(page, value: str) -> str:
    selected = page.get_by_text(value, exact=True).last
    selected.wait_for(state="visible", timeout=60000)
    return selected.inner_text().strip()

# Wait until the Payment Tracking Overview table has loaded real headers.
def _payment_tracking_table(page):
    deadline = time.monotonic() + 120
    table = page.locator("table").first
    while time.monotonic() < deadline:
        if table.is_visible():
            headers = " ".join(table.locator("thead").inner_text().split()).lower()
            if "payment list name" in headers:
                return table
        page.wait_for_timeout(2000)
    raise AssertionError(
        "Timed out waiting for the Payment Tracking Overview table data."
    )

# Open a payment detail page and retry when the application leaves its loader active.
def _open_payment_detail(page, detail_url: str, tile_labels: list[str]):
    last_error = None
    for attempt in range(3):
        try:
            page.goto(detail_url, wait_until="domcontentloaded", timeout=120000)
            page.wait_for_load_state("networkidle", timeout=60000)
            page.get_by_text(tile_labels[0], exact=False).first.wait_for(
                state="visible",
                timeout=60000,
            )
            return
        except Exception as exc:
            last_error = exc
            if attempt < 2:
                page.reload(wait_until="domcontentloaded", timeout=120000)
                page.wait_for_timeout(5000)
    raise AssertionError(
        f"Payment detail page did not finish loading after 3 attempts: {detail_url}"
    ) from last_error

# Sum approved Number of households values from the Beneficiary Overview.
def _number_of_households_total(page) -> int:
    table = page.locator("table").filter(has_text="Number of households").first
    table.wait_for(state="visible", timeout=60000)

    headers = [
        " ".join(header.split()).lower()
        for header in table.locator("thead th").all_inner_texts()
    ]
    households_column = next(
        (
            index
            for index, header in enumerate(headers)
            if "number of households" in header
        ),
        None,
    )
    if households_column is None:
        raise AssertionError("The Beneficiary List Overview table has no 'Number of households' column.")
    status_column = next(
        (
            index
            for index, header in enumerate(headers)
            if "beneficiary list status" in header
        ),
        None,
    )
    if status_column is None:
        raise AssertionError(
            "The Beneficiary List Overview table has no 'Beneficiary List Status' column."
        )

    total = 0
    processed_pages = set()

    # Process every table page until there is no enabled Next button.
    while True:
        rows = table.locator("tbody tr")
        deadline = time.monotonic() + 60000 / 1000
        while rows.count() < 50 and time.monotonic() < deadline:
            page.wait_for_timeout(1000)
        if not rows.count():
            raise AssertionError("Beneficiary List Overview contains no data rows.")
        first_row = rows.first.inner_text()
        if first_row in processed_pages:
            raise AssertionError("Beneficiary List Overview pagination did not advance.")
        processed_pages.add(first_row)

        for row_index in range(rows.count()):
            row = rows.nth(row_index)
            cells = row.locator("td")
            if cells.count() <= max(households_column, status_column):
                continue
            status = " ".join(cells.nth(status_column).inner_text().split()).lower()
            if status != "approved":
                continue
            cell = cells.nth(households_column)
            cell_text = cell.inner_text().strip()
            if not cell_text:
                continue
            values = re.findall(r"\d+", cell_text)
            if not values:
                raise AssertionError(
                    f"No numeric value found in 'Number of households' row {row_index + 1}."
                )
            total += int(values[-1])

        next_button = page.locator(
            "button[aria-label*='Next'], button[title*='Next'], "
            "button:has-text('Next'), [role='button'][aria-label*='Next']"
        ).last
        if (
            not next_button.count()
            or not next_button.is_visible()
            or not next_button.is_enabled()
        ):
            break

        next_button.click()
        page.wait_for_load_state("networkidle")

    return total

# Read overview totals and sum matching tiles from every payment detail page.
def _payment_tracking_totals_from_rows(page) -> dict[str, tuple[int, int]]:
    table = _payment_tracking_table(page)
    headers = [
        " ".join(header.split()).lower()
        for header in table.locator("thead th").all_inner_texts()
    ]
    name_column = next(
        (index for index, header in enumerate(headers) if "payment list name" in header),
        None,
    )
    if name_column is None:
        raise AssertionError("Payment Tracking Overview has no 'Payment List Name' column.")

    tile_labels = (
        "NUMBER OF PENDING HOUSEHOLD TRANSFERS",
        "NUMBER OF SUCCESSFUL HOUSEHOLD TRANSFERS",
        "NUMBER OF FAILED HOUSEHOLD TRANSFERS",
        "PLANNED TOTAL TRANSFER",
        "ACTUAL TOTAL TRANSFER",
        "VARIANCE",
    )
    numeric_labels = {
        "PLANNED TOTAL TRANSFER",
        "ACTUAL TOTAL TRANSFER",
        "VARIANCE",
    }
    # Capture overview tile values before navigating to detail pages.
    expected = {}
    for label in tile_labels:
        expected[label] = (
            _wait_for_numeric_tile_value(page, label)
            if label in numeric_labels
            else _wait_for_tile_value(page, label)
        )
    # Accumulate the corresponding value from each payment detail page.
    actual = {label: 0 for label in tile_labels}
    detail_targets = []
    # Collect detail-page links across all overview table pages first.
    while True:
        rows = table.locator("tbody tr")
        rows.first.wait_for(state="visible", timeout=60000)
        loading_deadline = time.monotonic() + 120
        previous_link_count = -1
        stable_link_reads = 0
        while time.monotonic() < loading_deadline:
            rows = table.locator("tbody tr")
            link_count = sum(
                1
                for row in rows.all()
                if row.locator("td").nth(name_column).locator("a").count()
            )
            if link_count == previous_link_count and link_count > 0:
                stable_link_reads += 1
                if stable_link_reads >= 3:
                    break
            else:
                stable_link_reads = 0
                previous_link_count = link_count
            page.wait_for_timeout(2000)
        if stable_link_reads < 3:
            raise AssertionError(
                "Payment Tracking Overview did not finish loading payment links."
            )
        for row_index in range(rows.count()):
            row = rows.nth(row_index)
            row_key = row.inner_text()
            if not row_key.strip():
                raise AssertionError(
                    "Payment Tracking Overview contains an empty data row."
                )
            name_cell = row.locator("td").nth(name_column)
            link = name_cell.locator("a").first
            href = link.get_attribute("href") if link.count() else None
            # The application sometimes leaves one non-data placeholder row.
            if not href and "loading..." in row_key.lower():
                continue
            detail_targets.append(
                (urljoin(PAYMENT_TRACKING_URL, href) if href else None, row_key)
            )

        next_button = page.locator(
            "button[aria-label*='Next'], button[title*='Next'], "
            "button:has-text('Next'), [role='button'][aria-label*='Next']"
        ).last
        if (
            not next_button.count()
            or not next_button.is_visible()
            or not next_button.is_enabled()
        ):
            break
        previous_rows = rows.all_inner_texts()
        next_button.click()
        deadline = time.monotonic() + 120
        while time.monotonic() < deadline:
            page.wait_for_timeout(1000)
            next_rows = table.locator("tbody tr").all_inner_texts()
            if next_rows and next_rows != previous_rows:
                break
        else:
            raise AssertionError(
                "Payment Tracking Overview did not load the next page of rows."
            )
        table = _payment_tracking_table(page)

    # Visit each payment detail page and add all requested tile values.
    for detail_url, row_key in detail_targets:
        if detail_url:
            _open_payment_detail(page, detail_url, tile_labels)
        else:
            raise AssertionError(
                f"Payment row has no detail link after loading: {row_key!r}"
            )
        for label in tile_labels:
            page.get_by_text(label, exact=False).first.wait_for(
                state="visible",
                timeout=60000,
            )
            value = (
                _wait_for_numeric_tile_value(page, label)
                if label in numeric_labels
                else _wait_for_tile_value(page, label)
            )
            actual[label] += value

    return {
        label: (expected[label], actual[label])
        for label in tile_labels
    }

# Log in, select the test context, and run all dashboard validations.
def test_household_management_dashboard_tiles(page):
    login = LoginPage(page)
    dashboard = Dashboard(page)
    failures = []

    # Authenticate using the same login flow as the happy-path test.
    with report.step("Login to CVA application"):
        login.load()
        login.login("SuperAdmin", "Welcome@2")
        report.assert_visible(login.userIcon, "User icon visible after login", timeout=60000)

    # Select and verify the configured Domain, Country, and Project.
    with report.step("Select dashboard context"):
        page.wait_for_timeout(10000)
        report.assert_enabled(dashboard.domain_drp, "Domain dropdown enabled")
        report.assert_enabled(dashboard.country_drp, "Country dropdown enabled")
        dashboard.select_country()
        page.wait_for_timeout(1000)
        report.assert_enabled(dashboard.project_drp, "Project dropdown enabled")
        dashboard.select_project()
        page.wait_for_load_state("networkidle")

        report.validation(
            "Selected domain",
            EXPECTED_DOMAIN,
            _selected_value(page, EXPECTED_DOMAIN),
        )
        report.validation(
            "Selected country",
            EXPECTED_COUNTRY,
            _selected_value(page, EXPECTED_COUNTRY),
        )
        report.validation(
            "Selected project",
            EXPECTED_PROJECT,
            _selected_value(page, EXPECTED_PROJECT),
        )
        expected_households = _wait_for_nonzero_tile_value(
            page, "TOTAL NUMBER OF HOUSEHOLDS"
        )
        expected_beneficiaries = _wait_for_nonzero_tile_value(
            page, "TOTAL NUMBER OF BENEFICIARIES SELECTED"
        )

    # Compare the dashboard household tile with Master Household Data.
    with report.step("Validate household tile against Master Household Data"):
        page.goto(HOUSEHOLD_DATA_URL, wait_until="domcontentloaded")
        page.get_by_text("NUMBER OF HOUSEHOLDS", exact=True).wait_for(
            state="visible",
            timeout=60000,
        )
        _record_tile_check(
            page,
            failures,
            "Total number of households",
            expected_households,
            _wait_for_nonzero_tile_value(page, "NUMBER OF HOUSEHOLDS"),
        )

    # Compare the dashboard beneficiary tile with approved beneficiary rows.
    with report.step("Validate beneficiary tile against Beneficiary List Overview"):
        page.goto(BENEFICIARY_OVERVIEW_URL, wait_until="domcontentloaded")
        page.locator("table").filter(has_text="Number of households").first.wait_for(
            state="visible",
            timeout=60000,
        )
        _record_tile_check(
            page,
            failures,
            "Total number of beneficiaries selected",
            expected_beneficiaries,
            _number_of_households_total(page),
        )

    # Compare all Payment Tracking Overview tiles with detail-page sums.
    with report.step("Validate Payment Tracking Overview data"):
        page.goto(PAYMENT_TRACKING_URL, wait_until="domcontentloaded")
        _payment_tracking_table(page)
        payment_tracking_totals = _payment_tracking_totals_from_rows(page)
        for label, (expected, actual) in payment_tracking_totals.items():
            _record_tile_check(
                page,
                failures,
                f"Validate Payment Tracking Overview data - {label.title()}",
                expected,
                actual,
            )

    # Fail only after every validation and screenshot has been recorded.
    with report.step("Complete dashboard validation checks"):
        if failures:
            raise AssertionError(
                "Dashboard validation failures:\n"
                + "\n".join(f"- {failure}" for failure in failures)
            )
