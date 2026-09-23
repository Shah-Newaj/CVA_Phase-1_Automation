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
def pytest_sessionfinish(session,exitstatus):
    root=report.output_dir; root.mkdir(parents=True,exist_ok=True)
    worker=os.environ.get("PYTEST_XDIST_WORKER")
    if worker:
        report.export_worker(root/"workers"/f"{worker}.json"); return
    report.export_worker(root/"workers"/"master.json"); _build_html(root)

def _build_html(root):
    results=[]
    for path in sorted((root/"workers").glob("*.json")):
        try: results.extend(json.loads(path.read_text(encoding="utf8")))
        except Exception: pass
    html=(Path(__file__).parent/"templates"/"report.html").read_text(encoding="utf8")
    html=html.replace("%%TEST_DATA%%",json.dumps(results,default=str).replace("</","<\/"))
    title=os.environ.get("BTH_REPORT_TITLE",os.environ.get("CVA_Project_Dashboard_Validation",Path.cwd().name))
    subtitle=os.environ.get(
        "BTH_REPORT_SUBTITLE",
        "Household, Beneficiary, and Payment Tracking Data Checks",
    )
    html=(
        html.replace("%%PROJECT%%",title)
        .replace("%%REPORT_TITLE%%",title)
        .replace("%%REPORT_SUBTITLE%%",subtitle)
        .replace("%%RUN_NAME%%",root.name)
    )
    (root/f"{root.name}.html").write_text(html,encoding="utf8")
