# from playwright.sync_api import Page
#
#
# class ConfigurationPage:
#     def __init__(self, page: Page):
#         self.configuration = page.locator("a.nav-link").filter(
#             has_text="Configuration"
#         ).first
#         self.project_criteria_setup = page.get_by_role("link",name="Project Criteria Setup List",exact=True)
#         self.country_project_mapper = page.get_by_role("link",name="Country Project Mapper List",exact=True)
#         self.add_new = page.get_by_role("button", name="Add New", exact=True)

from __future__ import annotations

from playwright.sync_api import Locator, Page


class ConfigurationPage:
    """
    Page Object for the CVA Configuration section.

    The CVA sidebar is dynamic: Configuration can be collapsed and the
    submenu items are not consistently exposed to Playwright as ARIA links.
    Therefore this page object intentionally uses visible-text fallback
    locators instead of depending only on get_by_role("link").
    """

    PROJECT_CRITERIA_LABEL = "Project Criteria Setup List"
    COUNTRY_PROJECT_MAPPER_LABEL = "Country Project Mapper List"

    def __init__(self, page: Page):
        self.page = page

        # Keep the original locator as the first choice because it matches
        # the existing CVA sidebar implementation used by other page objects.
        self.configuration = page.locator("a.nav-link").filter(
            has_text="Configuration"
        ).first

        # Text-based fallbacks are important because the submenu entries are
        # not always exposed with role="link" by the browser accessibility tree.
        self.configuration_text = page.get_by_text(
            "Configuration", exact=True
        ).first

        self.project_criteria_setup = page.get_by_text(
            self.PROJECT_CRITERIA_LABEL, exact=True
        ).first

        self.country_project_mapper = page.get_by_text(
            self.COUNTRY_PROJECT_MAPPER_LABEL, exact=True
        ).first

        # Backward-compatible Add New locators.
        self.project_criteria_add_new = page.get_by_role(
            "button", name="Add New", exact=True
        )
        self.country_project_mapper_add_new = page.get_by_role(
            "button", name="Add New", exact=True
        )
        self.add_new = self.project_criteria_add_new

    # ------------------------------------------------------------------
    # Sidebar helpers
    # ------------------------------------------------------------------

    def _visible_locator(self, *locators: Locator) -> Locator | None:
        """Return the first currently visible locator."""
        for locator in locators:
            try:
                if locator.count() == 0:
                    continue
                for index in range(locator.count()):
                    candidate = locator.nth(index)
                    if candidate.is_visible():
                        return candidate
            except Exception:
                continue
        return None

    def _click_configuration_menu(self) -> None:
        """Expand Configuration if its submenu is not currently visible."""
        submenu = self._visible_locator(
            self.project_criteria_setup,
            self.country_project_mapper,
        )
        if submenu is not None:
            return

        menu = self._visible_locator(
            self.configuration,
            self.configuration_text,
        )
        if menu is None:
            raise RuntimeError(
                "Configuration menu could not be located as a visible sidebar item."
            )

        menu.scroll_into_view_if_needed()
        menu.click(timeout=15000)

        self.page.wait_for_timeout(500)

        submenu = self._visible_locator(
            self.project_criteria_setup,
            self.country_project_mapper,
        )
        if submenu is None:
            raise RuntimeError(
                "Configuration menu was clicked, but its submenu did not become visible."
            )

    def _open_subsection(self, label: str) -> None:
        """Expand Configuration and click the requested visible subsection."""
        self._click_configuration_menu()

        if label == self.PROJECT_CRITERIA_LABEL:
            target = self._visible_locator(self.project_criteria_setup)
        elif label == self.COUNTRY_PROJECT_MAPPER_LABEL:
            target = self._visible_locator(self.country_project_mapper)
        else:
            target = self._visible_locator(
                self.page.get_by_text(label, exact=True).first
            )

        if target is None:
            raise RuntimeError(
                f"Configuration subsection '{label}' could not be located."
            )

        target.scroll_into_view_if_needed()
        target.click(timeout=15000)

        # Give the Blazor/router navigation time to update the page. Do not
        # require networkidle because CVA can keep background requests alive.
        self.page.wait_for_timeout(1000)

    # ------------------------------------------------------------------
    # Public navigation API
    # ------------------------------------------------------------------

    def open_configuration(self) -> None:
        self._click_configuration_menu()

    def open_project_criteria_setup(self) -> None:
        self._open_subsection(self.PROJECT_CRITERIA_LABEL)

    def open_country_project_mapper(self) -> None:
        self._open_subsection(self.COUNTRY_PROJECT_MAPPER_LABEL)

    # ------------------------------------------------------------------
    # Add New
    # ------------------------------------------------------------------

    def get_visible_add_new(self) -> Locator | None:
        """Return the first visible/enabled Add New button on the current page."""
        buttons = self.page.get_by_role(
            "button", name="Add New", exact=True
        )

        for index in range(buttons.count()):
            button = buttons.nth(index)
            try:
                if button.is_visible() and button.is_enabled():
                    return button
            except Exception:
                continue

        # Some CVA controls are rendered as clickable elements without a
        # button role. Keep a text fallback for those pages.
        text_buttons = self.page.get_by_text("Add New", exact=True)
        for index in range(text_buttons.count()):
            candidate = text_buttons.nth(index)
            try:
                if candidate.is_visible() and candidate.is_enabled():
                    return candidate
            except Exception:
                continue

        return None
