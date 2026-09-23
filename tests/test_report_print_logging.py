from bth_qa_reporter.reporter import Reporter


def test_report_logs_print_output():
    reporter = Reporter()
    reporter.start_test("case:print", "print log")

    reporter.log("Username: & Pass: admin 12345", "PRINT")

    assert reporter.results["case:print"]["logs"] == [
        {"level": "PRINT", "message": "Username: & Pass: admin 12345"}
    ]
