import pytest
import allure

from utils.excel_utils import ExcelUtils
from pages.login_page import LoginPage
from pages.userRole_page import UserRolePage
from bth_qa_reporter import report


test_data = ExcelUtils.get_data(
    "data/users.xlsx",
    "Sheet1"
)


@pytest.mark.parametrize(
    "full_name, username, email, phone, role, image",
    test_data
)

@allure.feature("CVA User Role")
@allure.story("Create User Role")
@allure.severity(allure.severity_level.CRITICAL)
def test_cva_userCreation(page, full_name, username, email, phone, role, image):

    allure.dynamic.title(f"Create User: {full_name}")
    report.step(f"Create User: {full_name}")

    login = LoginPage(page)
    user_role = UserRolePage(page)

    with allure.step("Open application"):
        report.step("Open application")
        login.load()
        report.pass_step("Application opened")

    with allure.step("Login as SuperAdmin"):
        report.step("Login as SuperAdmin")
        login.login("SuperAdmin", "12345")
        report.pass_step("Login successful")

    with allure.step(f"Create user: {full_name}"):

        user_role.profile(
            full_name, username, email, phone, image
        )
        report.pass_step(f"Profile created: {full_name}")

    with allure.step("Assign role"):
        user_role.role(role)
        report.pass_step(f"Role assigned: {role}")

    with allure.step("Set permissions"):
        user_role.permission()
        report.pass_step("Permissions configured")

    with allure.step("Select GEO details"):
        user_role.geo()
        report.pass_step("GEO details selected")

    with allure.step("Complete summary"):
        user_role.summary()
        report.pass_step("Summary completed")

    with allure.step("Validate dashboard data"):
        user_role.dashboard(full_name)