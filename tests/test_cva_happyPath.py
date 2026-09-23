import time
from os import name
import os
import pytest
from playwright.sync_api import expect

from pages.beneficiaryList_page import BeneficiaryListPage
from pages.dashboard_page import Dashboard
from pages.login_page import LoginPage
from pages.paymentList_page import PaymentListPage
from pages.sampling_page import SamplingPage
from bth_qa_reporter import report

# Edit these two values when this test file needs a different report heading.
REPORT_TITLE = "CVA_Phase_1_QA_Automation_Report"
REPORT_SUBTITLE = "URL: https://cashapp.savethechildren.net/"
REPORT_TEST_NAME = "End-to-End CVA Happy Path Test"
REPORT_TEST_FILE_NAME = "Environment: Prod | Country: Niger CVA | Project: BMZ RESA Training | Browser: Chromium"
os.environ["BTH_REPORT_TITLE"] = REPORT_TITLE
os.environ["BTH_REPORT_SUBTITLE"] = REPORT_SUBTITLE


def test_cva_happy_path(page):

    login = LoginPage(page)
    dashboard = Dashboard(page)
    beneficiary = BeneficiaryListPage(page)
    payment = PaymentListPage(page)
    sampling = SamplingPage(page)

    with report.step("Login"):
        login.load()
        login.login("SuperAdmin", "Welcome@2")
        report.assert_visible(login.userIcon, "User icon visible after login", timeout=15000)
        print("Username: & Pass: ", "admin", "12345")

    with report.step("Verify login with bth_qa_reporter function"):
        expect(page.locator("//div[@class='rf-page-header-action-item-username']")).to_be_visible()

    with report.step("Select Country & Project"):
        page.wait_for_timeout(10000)
        report.assert_enabled(dashboard.country_drp, "Country dropdown enabled")
        dashboard.select_country()
        page.wait_for_timeout(1000)
        dashboard.select_project()
        page.wait_for_load_state("networkidle")

    with report.step("Create Beneficiary List"):
        beneficiary_list_id = beneficiary.create_beneficiary("test")
        print("Beneficiary List ID: ", beneficiary_list_id)
        login.logout()

    with report.step("Approve Beneficiary List"):
        login.login2("shah.ca", "WelcomeCVA@2026")
        beneficiary.approve_beneficiary(beneficiary_list_id)

    with report.step("Create Payment List"):
        payment_list_id = payment.create_payment(beneficiary_list_id)
        print("Payment List ID: ", payment_list_id)
        login.logout()

    with report.step("Approve Payment List"):
        login.login("SuperAdmin", "Welcome@2")
        payment.approve_payment(payment_list_id)

    with report.step("Payment Tracking"):
        payment.payment_tracking(payment_list_id)

    with report.step("Create Sample"):
        sampling.create_sample(beneficiary_list_id)
        login.logout()

    with report.step("Approve Sample"):
        login.login2("shah.ca", "WelcomeCVA@2026")
        sampling.approve_sample()

