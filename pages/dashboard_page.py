from playwright.sync_api import Page
from playwright.sync_api import expect

class Dashboard:
    def __init__(self, page: Page):
        self.page = page
        self.domain_drp = page.locator(
            "//span[normalize-space()='Domain:']/following::span[normalize-space()='Select'][1]"
        )
        self.domain = page.locator(".select-rf-popper:visible").get_by_text("sci-co-niger", exact=True)
        self.country_drp = page.locator(
            "//span[normalize-space()='Country:']/following::span[normalize-space()='Select'][1]"
        )
        self.country = page.locator(".select-rf-popper:visible").get_by_text("Niger CVA", exact=True)
        self.project_drp = page.locator(
            "//span[normalize-space()='Project:']/following::span[normalize-space()='Select'][1]"
        )
        self.project = page.locator(".select-rf-popper:visible").get_by_text("BMZ RESA Training", exact=True)
        self.login_btn = page.get_by_role("button", name="Login")

    def select_country(self):
        self.country_drp.click()
        expect(self.country).to_be_visible(timeout=60000)
        self.country.click()
        expect(self.page.get_by_text("Niger CVA", exact=True).last).to_be_visible(timeout=60000)
        self.page.wait_for_timeout(2000)

    def select_project(self):
        self.project_drp.click()
        expect(self.project).to_be_visible(timeout=60000)
        self.project.click()
        expect(self.page.get_by_text("BMZ RESA Training", exact=True).last).to_be_visible(timeout=60000)
        self.page.wait_for_timeout(5000)