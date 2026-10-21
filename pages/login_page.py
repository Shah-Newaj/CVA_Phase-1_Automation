import time

from playwright.sync_api import Page, expect

class LoginPage:
    def __init__(self, page: Page):
        self.page = page
        self.username = page.locator("//input[@placeholder='example@savethechildren.org']")
        self.password = page.locator("//input[@placeholder='************']")
        self.login_btn = page.get_by_role("button", name="Login")
        self.userIcon = page.locator("//div[@class='rf-page-header-action-item-username']")
        self.logout_btn = page.get_by_role("button", name="Logout")
        self.micro_btn = page.get_by_role("button", name="Microsoft")

    def _wait_for_page_ready(self):
        for selector in (".preloader-rf-backarea", ".preloader-rf-body"):
            expect(self.page.locator(selector)).to_be_hidden(timeout=60000)

    def load(self):
        self.page.goto("https://cashapp.savethechildren.net/")
        self.username.is_visible()
        # self.page.wait_for_selector("//label[normalize-space()='Email Address']")

    def login(self, user, pwd):
        self.username.fill(user)
        self.password.fill(pwd)
        self.login_btn.click()
        expect(self.userIcon).to_be_visible(timeout=60000)
        self._wait_for_page_ready()

    def login2(self, user, pwd):
        self.username.fill(user)
        self.password.fill(pwd)
        self.login_btn.click()
        expect(self.userIcon).to_be_visible(timeout=60000)
        self._wait_for_page_ready()

    def logout(self):
        self._wait_for_page_ready()
        self.userIcon.click()
        expect(self.logout_btn).to_be_visible(timeout=60000)
        self.logout_btn.click()