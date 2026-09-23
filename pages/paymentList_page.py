from playwright.sync_api import Page
import time
from playwright.sync_api import expect

class PaymentListPage:
    def __init__(self, page: Page):
        self.page = page
        self.paymentlist = page.get_by_text("Payment List Management")
        self.paymentlist_overview = page.get_by_role("link", name="Payment List Overview")
        self.create_btn = page.get_by_role("button", name="Create New Payment List")
        self.location3_drp = page.locator("//div[@class='select-rf-viewer False']//span[contains(text(),'Select')]")
        # self.location3 = page.locator(".select-rf-popper").get_by_text("Bosso", exact=True) #change Location name here if required
        self.location3 = page.locator("//div[@class='select-rf-popper True']//div[2]//div[1]")
        self.beneficiarylist_drop = page.locator("//div[@class='multiselect-rf-viewer False']//span[contains(text(),'Select')]")
        # self.beneficiarylist = page.locator(".select-rf-popper").get_by_text("AdminUAT1/UN OC/Test Location 2/09Jul20/C1SPDRUC", exact=True) #change Beneficiary name here if required
        self.beneficiarylist = page.locator("//div[contains(text(),'AdminUAT1/UN OC/Test Location 2/09Jul20/C1SPDRUC')]")
        self.save_btn = page.get_by_role("button", name="Save")
        self.assign_pymnt_btn = page.get_by_role("button", name="Assign Payments")

        self.cva_type_drp = page.locator("div[id$='-SetTransferDetailsComponent-CVAType']")
        # self.cva_type = page.locator("//div[contains(text(),'mpca')]")
        self.cva_type = page.locator("(//div[@class='select-rf-popper-item-text'])[1]")
        self.currency_transfer_drp = page.locator("div[id$='-SetTransferDetailsComponent-CurrencyOfTransfer']")
        # self.currency_transfer = page.locator("//div[contains(text(),'US Dollar')]")
        self.currency_transfer = page.locator("(//div[@class='select-rf-popper-item-text'])[1]")
        self.financial_service_drp = page.locator("div[id$='-SetTransferDetailsComponent-FinancialServiceProvider']")
        # self.financial_service = page.locator("//div[contains(text(),'Test Bank')]")
        self.financial_service = page.locator("(//div[@class='select-rf-popper-item-text'])[1]")
        self.delivery_mecha_drp = page.locator("div[id$='-SetTransferDetailsComponent-PaymentModality']")
        # self.delivery_mecha = page.locator("//div[contains(text(),'Mobile money')]")
        self.delivery_mecha = page.locator("(//div[@class='select-rf-popper-item-text'])[1]")
        self.exp_transfer_date_picker = page.locator("//div[text()='Expected Transfer Date']/following-sibling::div[contains(@class,'datepicker-rf')]")
        self.exp_transfer_date = page.locator("//div[contains(@class,'datepicker-rf')]//input[contains(@type,'text')]")
        self.transfer_value_text = page.locator("//div[text()='Transfer Value']/following-sibling::div[contains(@class,'input-rf')]//input")

        self.select_all_checkbox = page.locator("//div[contains(@class,'table-rf-check-holder False')]//i[@class='table-rf-check-icon fa-solid fa-check']")
        self.apply_to_selected_btn = page.get_by_role("button", name="Apply to Selected")
        self.sendlist_for_approval_btn = page.get_by_role("button", name="Send List for Approval")

        self.payment_list_approval = page.get_by_role("link", name="Payment List Approval")
        self.view_payments_btn = page.get_by_role("button", name="View Payments")
        self.payment_search = page.locator("//input[@placeholder='Search']")
        self.benef_search = page.locator("//input[contains(@class,'multiselect-rf-popper-input rf-control')]")
        self.approve_btn = page.get_by_role("button", name="Approve")

        self.payment_tracking_overview = page.get_by_role("link", name="Payment Tracking Overview")
        self.update_payment_status_drp = page.locator("//span[normalize-space()='Select']")
        self.update_payment_status = page.locator("//div[contains(text(),'Successful')]")
        self.save_record_transfer_btn = page.get_by_role("button", name="Save & Record Transfer")
        self.receive_transfer_amount = page.locator("//div[contains(text(),'Yes')]")
        self.transfer_made_date_picker = page.locator("//div[text()='What date was the transfer made']/following-sibling::div[contains(@class,'datepicker-rf')]")
        self.transfer_made_date = page.locator("//div[contains(@class,'datepicker-rf')]//input[contains(@type,'text')]")


    def create_payment(self, beneficiary_list_id):
        print(f"Received ID: {beneficiary_list_id}")
        self.paymentlist.click()
        self.paymentlist_overview.click()
        self.create_btn.click()
        self.page.wait_for_timeout(5000) #under 5 seconds it's not working
        self.location3_drp.click()
        self.page.wait_for_timeout(3000)
        self.location3.click()
        self.page.wait_for_timeout(3000)
        self.beneficiarylist_drop.click()
        self.page.wait_for_timeout(3000)
        self.benef_search.fill(beneficiary_list_id)
        self.benef_search.press("Enter")
        self.page.locator(f"//div[contains(text(),'{beneficiary_list_id}')]").click()
        self.page.wait_for_timeout(1000)
        self.save_btn.click()
        self.page.wait_for_timeout(5000)
        self.page.wait_for_load_state("networkidle")
        self.assign_pymnt_btn.click()
        self.page.wait_for_timeout(5000)
        payment_list_id = self.page.locator("//div[normalize-space()='PAYMENT LIST ID']/following-sibling::div[contains(@class,'summary-value')]").inner_text().strip()
        print(payment_list_id)
        self.cva_type_drp.click()
        self.cva_type.click()
        self.page.wait_for_timeout(3000)
        self.currency_transfer_drp.click()
        self.currency_transfer.click()
        self.page.wait_for_timeout(3000)
        self.financial_service_drp.click()
        self.financial_service.click()
        self.page.wait_for_timeout(3000)
        self.delivery_mecha_drp.click()
        self.delivery_mecha.click()
        self.page.wait_for_timeout(3000)
        self.exp_transfer_date_picker.click()
        self.page.locator(".datepicker-popup-rf tbody td").get_by_text("25", exact=True).click()
        self.transfer_value_text.fill("150")
        self.page.wait_for_timeout(3000)
        self.select_all_checkbox.click()
        self.page.wait_for_timeout(3000)
        self.apply_to_selected_btn.click()
        self.page.wait_for_timeout(10000) #otherwise it's not working
        self.page.wait_for_load_state("networkidle")
        self.sendlist_for_approval_btn.click()
        self.page.wait_for_timeout(5000)
        self.page.wait_for_url("https://cashapp.savethechildren.net/PaymentListOverView")
        return payment_list_id


    def approve_payment(self, payment_list_id):
        print(f"Received ID: {payment_list_id}")
        self.paymentlist.click()
        self.payment_list_approval.click()
        self.page.wait_for_timeout(5000)
        self.payment_search.fill(payment_list_id)
        self.payment_search.press("Enter")
        self.page.wait_for_timeout(3000)
        row = self.page.locator("//tbody//tr//td[2]")
        row.wait_for(state="visible")
        row.click()
        self.page.wait_for_load_state("networkidle")
        self.view_payments_btn.click()
        self.approve_btn.click()
        self.page.wait_for_url("https://cashapp.savethechildren.net/PaymentListApproval")
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(10000)


    def payment_tracking(self, payment_list_id):
        print(f"Received ID: {payment_list_id}")
        self.paymentlist.click()
        self.payment_tracking_overview.click()
        self.page.wait_for_timeout(5000)
        self.payment_search.fill(payment_list_id)
        self.payment_search.press("Enter")
        self.page.wait_for_timeout(3000)
        row = self.page.locator("//tbody//tr//td[3]")
        row.wait_for(state="visible")
        row.click()

        self.select_all_checkbox.click()
        self.page.wait_for_timeout(3000)
        self.update_payment_status_drp.click()
        self.page.wait_for_timeout(2000)
        self.update_payment_status.click()
        self.page.wait_for_timeout(2000)
        self.transfer_made_date_picker.click()
        self.page.wait_for_timeout(2000)
        self.page.locator(".datepicker-popup-rf tbody td").get_by_text("20", exact=True).click()
        self.page.wait_for_timeout(2000)
        self.update_payment_status_drp.click()
        self.page.wait_for_timeout(2000)
        self.receive_transfer_amount.click()
        self.page.wait_for_timeout(2000)
        self.apply_to_selected_btn.click()
        self.page.wait_for_timeout(10000)
        self.save_record_transfer_btn.click()
        self.page.wait_for_timeout(10000)
        self.page.wait_for_url("https://cashapp.savethechildren.net/PaymentTrackingOverview")





