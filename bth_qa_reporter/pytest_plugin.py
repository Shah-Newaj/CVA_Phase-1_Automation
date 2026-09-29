from __future__ import annotations

import builtins
import json
import os
from datetime import datetime
from pathlib import Path
import pytest
from .reporter import report

def pytest_addoption(parser):
    group=parser.getgroup("bth-report")
    group.addoption("--bth-report-dir", action="store", default="test-reports", help="BTH QA HTML report output directory.")

def pytest_configure(config):
    run_id=os.environ.get("BTH_REPORT_RUN_ID") or datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")[:-3]
    os.environ["BTH_REPORT_RUN_ID"]=run_id
    report.configure(Path(config.getoption("--bth-report-dir"))/f"BTH_QA_Report_{run_id}")

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_protocol(item,nextitem):
    display_name = getattr(item.module, "REPORT_TEST_NAME", item.name)
    display_file = getattr(item.module, "REPORT_TEST_FILE_NAME", item.nodeid)
    report.start_test(item.nodeid, display_name)
    report.results[item.nodeid]["nodeid"] = display_file
    yield

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    report._current_page=item.funcargs.get("page") if hasattr(item,"funcargs") else None
    original_print=builtins.print
    def bth_print(*args,**kwargs):
        original_print(*args,**kwargs)
        if kwargs.get("file") is None:
            try:
                msg=kwargs.get("sep"," ").join(str(a) for a in args)+kwargs.get("end","\n")
                msg=msg.rstrip("\r\n")
                if msg: report.log(msg,"PRINT")
            except Exception: pass
    builtins.print=bth_print
    try: yield
    finally:
        builtins.print=original_print
        report._current_page=None

def _capture_sections(rep):
    for heading,content in getattr(rep,"sections",[]):
        if not content: continue
        h=heading.lower()
        if h=="captured stdout call": report.log(content.rstrip(),"STDOUT")
        elif h=="captured stderr call": report.log(content.rstrip(),"STDERR")

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item,call):
    outcome=yield
    rep=outcome.get_result()
    if rep.when!="call": return
    result=report.results.get(item.nodeid)
    if not result: return
    _capture_sections(rep)
    result["outcome"]=rep.outcome
    result["duration"]=rep.duration
    page=item.funcargs.get("page") if hasattr(item,"funcargs") else None
    if page:
        try:
            result.setdefault("metadata",{})["Browser"]=page.context.browser.browser_type.name
            result["metadata"]["URL"]=page.url
        except Exception: pass
    if rep.failed:
        result["error"]=str(rep.longrepr)
        if page and not result.get("failure_screenshot"):
            try: report.attach_screenshot(page,f"{item.name}_failure",attach_to_failed_step=True)
            except Exception: pass

@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    """Always finalize the BTH report when pytest reaches session shutdown."""
    root = report.output_dir
    root.mkdir(parents=True, exist_ok=True)

    worker = os.environ.get("PYTEST_XDIST_WORKER")
    if worker:
        report.export_worker(root / "workers" / f"{worker}.json")
        return

    report.export_worker(root / "workers" / "master.json")

    try:
        report_path = _build_html(root)
        # Keep a stable pointer at the user-specified report directory so the
        # report is easy to find even when each run gets its own timestamped
        # subdirectory. The timestamped report remains the canonical file.
        latest_path = root.parent / "latest_report.html"
        relative_report = report_path.relative_to(root.parent).as_posix()
        latest_path.write_text(
            "<!doctype html><html><head>"
            f"<meta http-equiv=\"refresh\" content=\"0; url={relative_report}\">"
            "<title>BTH QA Report</title></head><body>"
            f"<p><a href=\"{relative_report}\">Open latest BTH QA report</a></p>"
            "</body></html>",
            encoding="utf8",
        )
        print(f"\nBTH QA report: {report_path}")
        print(f"BTH QA latest : {latest_path}")
    except Exception as exc:
        # Do not hide the original pytest result because report generation
        # failed. Make the failure visible in the terminal instead.
        print(f"\nWARNING: BTH QA report generation failed: {exc}")

def _build_html(root):
    results = []
    workers_dir = root / "workers"
    workers_dir.mkdir(parents=True, exist_ok=True)

    for path in sorted(workers_dir.glob("*.json")):
        try:
            results.extend(
                json.loads(path.read_text(encoding="utf8"))
            )
        except Exception as exc:
            print(f"WARNING: Could not read report worker file {path}: {exc}")

    template_path = Path(__file__).parent / "templates" / "report.html"
    html = template_path.read_text(encoding="utf8")

    # Escape closing script tags so JSON cannot terminate the report's
    # embedded JavaScript block.
    test_data = json.dumps(
        results,
        default=str,
    ).replace("</", "<\\/")

    html = html.replace("%%TEST_DATA%%", test_data)

    title = os.environ.get(
        "BTH_REPORT_TITLE",
        os.environ.get(
            "CVA_Project_Dashboard_Validation",
            Path.cwd().name,
        ),
    )
    subtitle = os.environ.get(
        "BTH_REPORT_SUBTITLE",
        "Household, Beneficiary, and Payment Tracking Data Checks",
    )

    html = (
        html
        .replace("%%PROJECT%%", title)
        .replace("%%REPORT_TITLE%%", title)
        .replace("%%REPORT_SUBTITLE%%", subtitle)
        .replace("%%RUN_NAME%%", root.name)
    )

    report_path = root / f"{root.name}.html"
    report_path.write_text(html, encoding="utf8")
    return report_path
