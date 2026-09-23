from pages.dashboard_page import Dashboard
from pages.login_page import LoginPage
from pages.paymentList_page import PaymentListPage
from pages.sampling_page import SamplingPage


def test_cva_sampling(page):
    login = LoginPage(page)
    dashboard = Dashboard(page)
    sampling = SamplingPage(page)

    login.load()
    login.login("SuperAdmin", "Welcome@2")

    page.wait_for_timeout(3000)
    dashboard.select_country()
    page.wait_for_timeout(3000)
    dashboard.select_project()
    beneficiary_list_id = "MSQTX2L5" # this is dumy, in happy path it will come from beneficiary module
    sampling.create_sample(beneficiary_list_id)
    login.logout()

    login.login2("shah.ca", "WelcomeCVA@2026")
    sampling.approve_sample()