from playwright.sync_api import Page
from playwright.sync_api import expect


DOMAIN_NAME = "sci-co-sudan"
COUNTRY_NAME = "Sudan CVA"
PROJECT_NAME = "GFFO Training"


class Dashboard:
    def __init__(self, page: Page):
        self.page = page
        self.domain_drp = page.locator(
            "//span[normalize-space()='Domain:']/following-sibling::div[contains(@class,'select-rf')][1]//div[contains(@class,'select-rf-viewer')]"
        )
        self.domain = page.locator(".select-rf-popper:visible").get_by_text(
            DOMAIN_NAME, exact=True
        )
        self.country_drp = page.locator(
            "//span[normalize-space()='Country:']/following-sibling::div[contains(@class,'select-rf')][1]//div[contains(@class,'select-rf-viewer')]"
        )
        self.search = page.locator(
            ".select-rf-popper:visible input[placeholder='Search...']"
        )
        self.country = page.locator(".select-rf-popper:visible").get_by_text(
            COUNTRY_NAME, exact=True
        )
        self.project_drp = page.locator(
            "//span[normalize-space()='Project:']/following-sibling::div[contains(@class,'select-rf')][1]//div[contains(@class,'select-rf-viewer')]"
        )
        self.project = page.locator(".select-rf-popper:visible").get_by_text(
            PROJECT_NAME, exact=True
        )
        self.login_btn = page.get_by_role("button", name="Login")

    def select_domain(self):
        self.domain_drp.click()
        expect(self.search).to_be_visible(timeout=60000)
        self.search.fill(DOMAIN_NAME)
        expect(self.domain).to_be_visible(timeout=60000)
        self.domain.click()
        expect(self.domain_drp).to_contain_text(DOMAIN_NAME, timeout=60000)
        self.page.wait_for_timeout(2000)

    def select_country(self):
        self.country_drp.click()
        expect(self.search).to_be_visible(timeout=60000)
        self.search.fill(COUNTRY_NAME)
        expect(self.country).to_be_visible(timeout=60000)
        self.country.click()
        expect(self.page.get_by_text(COUNTRY_NAME, exact=True).last).to_be_visible(
            timeout=60000
        )
        self.page.wait_for_timeout(2000)

    def select_project(self):
        self.project_drp.click()
        expect(self.search).to_be_visible(timeout=60000)
        self.search.fill(PROJECT_NAME)
        expect(self.project).to_be_visible(timeout=60000)
        self.project.click()
        expect(self.page.get_by_text(PROJECT_NAME, exact=True).last).to_be_visible(
            timeout=60000
        )
        self.page.wait_for_timeout(5000)