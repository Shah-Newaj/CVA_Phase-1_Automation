import pytest

from bth_qa_reporter.reporter import Reporter


@pytest.fixture
def reporter():
    instance = Reporter()
    instance.start_test("reporter-validations", "Reporter validation functions")
    return instance


def test_validation_records_expected_and_actual_values(reporter):
    assert reporter.validation(
        "Beneficiary list status",
        expected="Approved",
        actual="Approved",
    )

    step = reporter.current_test["steps"][-1]
    assert step["status"] == "PASS"
    assert step["expected"] == "Approved"
    assert step["actual"] == "Approved"


def test_tile_validation_records_dashboard_tile_result(reporter):
    assert reporter.tile_validation(
        "Total beneficiaries",
        expected=125,
        actual=125,
    )

    step = reporter.current_test["steps"][-1]
    assert step["name"] == "Tile: Total beneficiaries"
    assert step["status"] == "PASS"
    assert step["expected"] == 125
    assert step["actual"] == 125


def test_column_validation_records_table_column_result(reporter):
    assert reporter.column_validation(
        "Payment amount",
        expected=5000,
        actual=5000,
    )

    step = reporter.current_test["steps"][-1]
    assert step["name"] == "Column: Payment amount"
    assert step["status"] == "PASS"
    assert step["expected"] == 5000
    assert step["actual"] == 5000


def test_table_validation_records_cell_by_cell_results(reporter):
    expected_rows = [
        {"id": "BL-001", "status": "Approved", "amount": 5000},
        {"id": "BL-002", "status": "Pending", "amount": 2500},
    ]
    actual_rows = [
        {"id": "BL-001", "status": "Approved", "amount": 5000},
        {"id": "BL-002", "status": "Pending", "amount": 2500},
    ]

    assert reporter.table_validation(
        "Beneficiary list table",
        expected=expected_rows,
        actual=actual_rows,
        key="id",
    )

    step = reporter.current_test["steps"][-1]
    assert step["name"] == "Beneficiary list table"
    assert step["status"] == "PASS"
    assert '"status": "PASS"' in step["details"]


def test_assert_validation_raises_for_mismatched_values(reporter):
    with pytest.raises(AssertionError, match="Beneficiary list status validation failed"):
        reporter.assert_validation(
            "Beneficiary list status",
            expected="Approved",
            actual="Pending",
        )

    step = reporter.current_test["steps"][-1]
    assert step["status"] == "FAIL"
    assert step["expected"] == "Approved"
    assert step["actual"] == "Pending"


def test_table_validation_raises_for_mismatched_cells(reporter):
    with pytest.raises(AssertionError, match="Beneficiary list table failed"):
        reporter.table_validation(
            "Beneficiary list table",
            expected=[{"id": "BL-001", "status": "Approved"}],
            actual=[{"id": "BL-001", "status": "Pending"}],
            key="id",
        )

    step = reporter.current_test["steps"][-1]
    assert step["status"] == "FAIL"
    assert '"status": "FAIL"' in step["details"]
