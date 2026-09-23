
from datetime import datetime

from playwright.sync_api import Page
import time
from playwright.sync_api import expect

class SamplingPage:
    def __init__(self, page: Page):
        self.page = page
        self.sampling = page.get_by_text("Sampling Management")
        self.sample_report_overview = page.get_by_role("link", name="Sample Report Overview")
        self.sample_report_approval = page.get_by_role("link", name="Sample Report Approval")
        self.create_btn = page.get_by_role("button", name="Create New Sample")
        self.sample_name_text = page.locator("//div[@class='input-group']//div[@class='input-rf']//input[@type='text']")
        self.survey_type_drp = page.locator("//span[normalize-space()='Select Survey Type']")
        self.survey_type = page.locator(".multiselect-rf-popper-items").get_by_text("Baseline", exact=True)
        self.radio_btn = page.locator(".option-rf").get_by_text("All registered households in this project", exact=True)
        self.save_btn = page.get_by_role("button", name="Save")
        self.select_all_checkbox = page.locator("//div[contains(@class,'table-rf-check-holder False')]//i[@class='table-rf-check-icon fa-solid fa-check']")
        self.save_sample_list_btn = page.get_by_role("button", name="Save to Sample List")
        self.input_sample_size_text = page.locator("//input[@type='number']")
        self.input_sample_size_drp = page.locator(".select-rf")
        self.input_sample_size = page.locator("//div[contains(text(),'Percentage (%)')]")
        self.generate_sample_btn = page.get_by_role("button", name="Generate Random Sample")
        self.sendlist_for_approval_btn = page.get_by_role("button", name="Send List for Approval")
        self.sample_search = page.locator("//input[@placeholder='Search']")
        self.approve_btn = page.get_by_role("button", name="Approve")
        self.sample_name = f"Test Sample {datetime.now().strftime('%Y%m%d_%H%M%S')}"


    def create_sample(self, beneficiary_list_id):
        print(f"Received ID: {beneficiary_list_id}")
        self.sampling.click()
        self.page.wait_for_timeout(1000)
        self.sample_report_overview.click()
        self.page.wait_for_timeout(1000)
        self.create_btn.click()
        self.page.wait_for_timeout(3000)
        self.sample_name_text.fill(self.sample_name)
        self.page.wait_for_timeout(3000)
        self.survey_type_drp.click()
        self.page.wait_for_timeout(3000)
        self.survey_type.click()
        self.radio_btn.click()
        self.save_btn.click()
        self.page.wait_for_timeout(3000)
        self.select_all_checkbox.click()
        self.page.wait_for_timeout(3000)
        self.save_sample_list_btn.click()
        self.page.wait_for_timeout(3000)
        self.select_all_checkbox.click()
        self.page.wait_for_timeout(3000)
        self.input_sample_size_text.fill("50")
        self.input_sample_size_drp.click()
        self.page.wait_for_timeout(3000)
        self.input_sample_size.click()
        self.page.wait_for_timeout(3000)
        self.generate_sample_btn.click()
        self.page.wait_for_timeout(3000)
        self.sendlist_for_approval_btn.click()
        self.page.wait_for_timeout(10000)
        self.page.wait_for_url("https://cashapp.savethechildren.net/SampleReportOverView")






    def approve_sample(self):
        self.sampling.click()
        self.sample_report_approval.click()
        self.page.wait_for_timeout(3000)
        self.sample_search.fill(self.sample_name)
        self.sample_search.press("Enter")
        self.page.wait_for_timeout(3000)
        row = self.page.locator("//tbody/tr[1]/td[1]")
        row.wait_for(state="visible")
        row.click()
        self.page.wait_for_timeout(5000)
        self.approve_btn.click()
        self.page.wait_for_url("https://cashapp.savethechildren.net/SampleReportApproval")
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(10000)


