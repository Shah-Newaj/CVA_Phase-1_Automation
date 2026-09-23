from playwright.sync_api import Page
import time
from playwright.sync_api import expect

class BeneficiaryListPage:
    def __init__(self, page: Page):
        self.page = page
        self.beneficiarylist = page.get_by_text("Beneficiary List Management")
        self.beneficiarylist_overview = page.get_by_role("link", name="Beneficiary List Overview")
        self.create_btn = page.get_by_role("button", name="Create New Beneficiary List")
        self.location3_text = page.locator("(//input[contains(@type,'text')])[5]")
        self.save_btn = page.get_by_role("button", name="Save")
        self.select_all_checkbox = page.locator("//div[contains(@class,'table-rf-check-holder False')]//i[@class='table-rf-check-icon fa-solid fa-check']")
        self.savetobeneficiarylist_btn = page.get_by_role("button", name="Save to Beneficiary List")
        self.sendlistforapproval_btn = page.get_by_role("button", name="Send List for Approval")

        self.benef_list_approval = page.get_by_role("link", name="Beneficiary List Approval")
        self.benef_search = page.locator("//input[@placeholder='Search']")
        self.approve_btn = page.locator("//button[normalize-space()='Approve']")

    def create_beneficiary(self, location_text):
        self.beneficiarylist.click()
        self.beneficiarylist_overview.click()
        self.create_btn.click()
        self.location3_text.fill(location_text)
        beneficiary_list_id = self.page.locator("(//input[@type='text'])[7]").input_value()
        self.save_btn.click()
        self.select_all_checkbox.click()
        self.savetobeneficiarylist_btn.click()
        self.page.wait_for_load_state("networkidle")
        self.sendlistforapproval_btn.click()
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(10000)

        return beneficiary_list_id



    def approve_beneficiary(self, beneficiary_list_id):
        print(f"Received ID: {beneficiary_list_id}")
        self.beneficiarylist.click()
        self.benef_list_approval.click()
        self.page.wait_for_timeout(3000)
        self.benef_search.fill(beneficiary_list_id)
        self.benef_search.press("Enter")
        self.page.wait_for_timeout(3000)
        row = self.page.locator("//tbody//tr//td[2]")
        row.wait_for(state="visible")
        row.click()

        self.page.wait_for_timeout(5000)
        self.approve_btn.click()
        self.page.wait_for_url("https://cashapp.savethechildren.net/BeneficiaryListApproval")
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(10000)

