# CVA Phase-1 UI Quality Scan

This add-on scans the core CVA pages covered by `tests/test_cva_happyPath.py` without creating or changing business data.

## Core pages scanned

1. Dashboard
2. Beneficiary List Overview
3. Beneficiary List Approval
4. Payment List Overview
5. Payment List Approval
6. Payment Tracking Overview
7. Sample Report Overview
8. Sample Report Approval

Safe, non-submitting popups are also scanned:

- Create New Beneficiary List
- Create New Payment List
- Create New Sample

`Fetch Data` and `Sync Data` are intentionally excluded from Phase-1.

## Checks

- Mixed capitalization, such as `OverView` → `Overview`
- Spelling / grammar through LanguageTool
- Button/UI consistency
- Accessibility through axe-playwright

## Evidence

Every detected application issue gets a full-page PNG evidence screenshot. The screenshot includes an injected evidence header containing:

- Page name
- Full URL
- Issue category
- Issue type
- Element/text
- Finding
- Suggestion, when available

The affected DOM element/text is highlighted in red when it can be located.

The browser address bar itself is not part of Playwright screenshots, so the URL is deliberately printed in the evidence header.

## LanguageTool SSL handling

The LanguageTool checker uses `truststore.inject_into_ssl()` so Python can use the Windows/OS certificate store. This avoids disabling TLS verification on corporate networks that use a trusted inspection CA.

Install dependencies:

```powershell
python -m pip install -r requirements-ui-quality.txt
python -m playwright install chromium
```

Run the scan:

```powershell
pytest -v -s .\tests\test_cva_core_application_ui_quality.py --bth-report-dir=test-reports --headed
```

The generated report is under a timestamped directory inside `test-reports`.
