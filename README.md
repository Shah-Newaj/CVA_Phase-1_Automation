# CVA_Phase-1_Automation
CVA(Cash & Voucher Activities)_Phase-1 Automation using Pytest, Python and Playwright


# Cash Voucher Activities (CVA) Automation Framework
International Live Project of Save the children international (SCI). 
A robust end-to-end test automation framework for the Cash Voucher Activities (CVA) 
application developed using Python, Playwright, and Pytest. The framework follows 
the Page Object Model (POM) architecture to ensure maintainability, scalability, and 
reusable test components.

# Key Features
## Functional Automation
End-to-end automation of CVA business workflows
* Page Object Model (POM) architecture
* Pytest-based test execution
* Data-driven testing using Excel
* Dynamic test data management
* Reusable page objects and utility methods
* Reliable Playwright locator strategy

## User Creation Automation
* Automated user creation using Excel test data
* Supports multiple user records through data-driven execution
* Reduces manual effort and simplifies test maintenance

## Reporting
* BTH QA Report (custom reusable HTML report)
* Fresh timestamped report generated for every test run
* Automatic screenshot capture on failures
* Detailed step-by-step execution status
* Expected vs Actual validation support
* Tile, column, and table validation support
* Browser and URL execution metadata
* Professional execution summary dashboard

Each execution is stored separately using a timestamped folder, for example:

```text
test-reports/
└── BTH_QA_Report_2026-09-15_15-30-45-123/
    ├── BTH_QA_Report_2026-09-15_15-30-45-123.html
    ├── screenshots/
    └── workers/
```

This prevents a new execution from replacing any previous report.

## Running Tests
Run the tests normally with:

```powershell
pytest -v -s .\tests\test_cva_happyPath.py --bth-report-dir=test-reports
```

After execution, open the timestamped HTML file inside the newly created `test-reports/BTH_QA_Report_<date-time>/` folder.

## Technology Stack
* Python
* Playwright
* Pytest
* HTML5
* CSS3
* OpenPyXL (Excel data handling)
* Page Object Model (POM)

## Framework Highlights
* Data-driven testing with Excel
* Modular Page Object Model architecture
* Reusable and maintainable framework
* Enterprise-ready automation structure
* Easy CI/CD integration

## Future Enhancements
* API automation integration
* Database validation
* Cross-browser execution
* Parallel test execution
* Performance trend comparison across executions
* Automatic PDF report generation
* CI/CD pipeline integration

### Command to run the project...

    pytest -v -s .\tests\test_cva_happyPath.py .\tests\test_dashboard_validations.py --headed

### Command to run the project - happy path...

    pytest -v -s .\tests\test_cva_happyPath.py --headed

### Command to run the project - data validation check...

    pytest -v -s .\tests\test_dashboard_validations.py --headed


### Used Packages in this Project...

pip	26.0.1

pkginfo	1.12.1.2	

platformdirs	4.9.6	

playwright	1.58.0	

pluggy	1.6.0

poetry	1.8.4	

poetry-core	1.9.1	

poetry-plugin-export	1.8.0	

ptyprocess	0.7.0	

pyee	13.0.1	

pygments	2.20.0	

pyproject-hooks	1.2.0

pytest	9.0.3

pytest-base-url	2.1.0

pytest-playwright	0.7.2

python-slugify	8.0.4

pywin32-ctypes	0.2.3

rapidfuzz	3.14.5

requests	2.33.1

requests-toolbelt	1.0.0

shellingham	1.5.4

text-unidecode	1.3

tomlkit	0.14.0

trove-classifiers	2026.1.14.14

typing-extensions	4.15.0

urllib3	2.6.3

virtualenv	20.39.1

wheel	0.46.3


## BTH QA HTML Report

This project now includes a reusable `bth_qa_reporter` package for Python + Playwright + Pytest.

Run:

```bash
pytest
```

or:

```bash
pytest --bth-report-dir=test-reports
```

Open:

```text
test-reports/index.html
```

The same `bth_qa_reporter` folder can be copied/package-installed into other Python + Playwright + Pytest projects.

### Reporting API

```python
from bth_qa_reporter import report

report.step("Login")
report.pass_step("Login successful")

report.validation(
    "Status",
    expected="Approved",
    actual="Approved"
)

report.tile_validation(
    "Total Beneficiaries",
    expected=125,
    actual=125
)

report.column_validation(
    "Payment Amount",
    expected=5000,
    actual=5000
)

report.table_validation(
    "Payment Table Validation",
    expected=expected_rows,
    actual=actual_rows
)

# Playwright assertion example
with report.step("Dashboard check"):
    report.assert_visible(login.userIcon, "User icon visible after login")
    report.assert_enabled(dashboard.domain_drp, "Country selector enabled")
```

These methods use Playwright's `expect(locator)` internally and record PASS/FAIL entries in the BTH report.

## BTH QA Reporter - Version 2

The reusable reporter now supports:

* Expected vs Actual validation
* `assert_validation()` for validations that should fail the Pytest test
* Dashboard tile validation with `tile_validation()`
* Single column validation with `column_validation()`
* Table/list-of-dictionaries validation with `table_validation()`
* Automatic failure screenshots through the Pytest plugin
* Browser and current URL metadata in the report when the Playwright `page` fixture is available

Examples:

```python
from bth_qa_reporter import report

report.assert_validation(
    "Beneficiary List Status",
    expected="Approved",
    actual=actual_status,
)

report.tile_validation(
    "Total Beneficiaries",
    expected=125,
    actual=actual_total,
)

report.column_validation(
    "Payment Amount",
    expected=5000,
    actual=actual_amount,
)

report.table_validation(
    "Payment List Validation",
    expected=expected_rows,
    actual=actual_rows,
)
```

`table_validation()` produces a cell-by-cell Expected/Actual comparison in the HTML report. By default it raises an `AssertionError` when any cell differs, so the Pytest test is marked failed as well.


## Automatic PASS/FAIL steps

Use the context-manager form for execution steps:

```python
with report.step("Login"):
    login.load()
    login.login(username, password)

with report.step("Select Country & Project"):
    dashboard.select_country()
    dashboard.select_project()
```

A successful block is automatically marked PASS. If an exception occurs, the
step is automatically marked FAIL, the failure screenshot is attached to that
step when a Playwright page is available, and the original exception is
re-raised so pytest still reports the test as failed.

Manual `report.pass_step()` and `report.fail_step()` remain available for
backward compatibility.


## Console / Print Output

Pytest captures `print()`/stdout and stderr during the test and the BTH report
shows it under **Console / Print Output**.

Example:

```python
print("Beneficiary List ID:", beneficiary_list_id)
print("Payment List ID:", payment_list_id)
```

## Playwright Assertions

Wrap Playwright assertions in a BTH execution step:

```python
from playwright.sync_api import expect

with report.step("Verify Beneficiary List"):
    expect(page.get_by_text("Approved")).to_be_visible()
```

The step is automatically PASS when the assertion succeeds. If the assertion
fails, the step becomes FAIL, the exception is recorded, a failure screenshot
is attempted, and the original exception is re-raised so pytest still fails.

Normal Playwright `expect()` behavior is preserved; no monkey-patching is used.
