import time

from playwright.sync_api import Page

class LoginPage:
    def __init__(self, page: Page):
        self.page = page
        self.username = page.locator("//input[@placeholder='example@savethechildren.org']")
        self.password = page.locator("//input[@placeholder='************']")
        self.login_btn = page.get_by_role("button", name="Login")
        self.userIcon = page.locator("//div[@class='rf-page-header-action-item-username']")
        self.logout_btn = page.get_by_role("button", name="Logout")
        self.micro_btn = page.get_by_role("button", name="Microsoft")

    def load(self):
        self.page.goto("https://cashapp.savethechildren.net/")
        self.username.is_visible()
        # self.page.wait_for_selector("//label[normalize-space()='Email Address']")

    def login(self, user, pwd):
        self.username.fill(user)
        self.password.fill(pwd)
        self.login_btn.click()

    def login2(self, user, pwd):
        self.username.fill(user)
        self.password.fill(pwd)
        self.login_btn.click()

    def logout(self):
        self.userIcon.click()
        self.logout_btn.click()