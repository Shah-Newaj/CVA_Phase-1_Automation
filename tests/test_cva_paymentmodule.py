from pages.dashboard_page import Dashboard
from pages.login_page import LoginPage
from pages.paymentList_page import PaymentListPage


def test_cva_payment_module(page):
    login = LoginPage(page)
    dashboard = Dashboard(page)
    payment = PaymentListPage(page)

    login.load()
    login.login("SuperAdmin", "Welcome@2")

    page.wait_for_timeout(1000)
    dashboard.select_country()
    page.wait_for_timeout(1000)
    dashboard.select_project()

    beneficiary_list_id = "DQBSLG82" # just for test purpose.. real date will auto receive in happy path flow
    payment_list_id = payment.create_payment(beneficiary_list_id)
    print("Payment List ID: ", payment_list_id)
    # payment.approve_payment(payment_list_id)

    # payment_list_id = "31AYQ9PG" #just for test purpose.. real date will auto receive in happy path flow
    # payment.payment_tracking(payment_list_id)