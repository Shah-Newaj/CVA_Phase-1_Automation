from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .content_checker import (
    ContentChecker,
    DEFAULT_IGNORED_WORDS,
)
from .language_checker import LanguageToolChecker
from .ui_consistency_checker import UIConsistencyChecker


@dataclass
class ScanResult:
    """
    Result returned by UIQualityScanner.

    Accessibility issues are intentionally excluded.
    """

    page_name: str
    url: str

    content_issues: list[dict[str, Any]] = field(default_factory=list)
    language_issues: list[dict[str, Any]] = field(default_factory=list)
    ui_issues: list[dict[str, Any]] = field(default_factory=list)
    scanner_warnings: list[dict[str, Any]] = field(default_factory=list)

    @property
    def total_issues(self) -> int:
        return (
            len(self.content_issues)
            + len(self.language_issues)
            + len(self.ui_issues)
        )


class UIQualityScanner:
    """
    Main UI Quality Scanner for the CVA application.

    Checks:

        1. Content / capitalization
        2. Spelling / grammar
        3. Button / UI consistency

    Accessibility checking is intentionally disabled.

    The scanner enriches detected issues with:
        - page URL
        - page name
        - issue category
        - suggested correction

    Screenshot generation/highlighting is handled by the test/reporting
    layer. Non-fatal checker outages are recorded as warnings.
    """

    def __init__(
        self,
        language: str | None = None,
        enable_language_tool: bool = True,
        ignored_words: set[str] | None = None,
    ):
        self.language = language or "en-US"
        self.enable_language_tool = enable_language_tool

        # ============================================================
        # Ignored application terminology
        # ============================================================

        ignored = set(DEFAULT_IGNORED_WORDS)

        if ignored_words:
            ignored.update(
                word.strip().lower()
                for word in ignored_words
                if word and word.strip()
            )

        # ============================================================
        # Checkers
        # ============================================================

        self.content_checker = ContentChecker(
            ignored_words=ignored
        )

        self.language_checker = LanguageToolChecker(
            ignored_words=ignored
        )

        self.ui_checker = UIConsistencyChecker()

    # =================================================================
    # MAIN SCAN
    # =================================================================

    def scan(
            self,
            page,
            page_name: str,
            enable_accessibility: bool = False,
            scan_root=None,
    ) -> ScanResult:
        """
        Scan the currently displayed page.

        enable_accessibility is retained only for backward compatibility
        with older test files.

        Accessibility scanning is NOT performed.
        """

        result = ScanResult(
            page_name=page_name,
            url=page.url,
        )

        # ============================================================
        # Get visible page text
        # ============================================================

        try:
            text = self._page_text(page)

        except Exception as exc:

            result.content_issues.append(
                {
                    "type": "Scanner Error",
                    "element": "",
                    "text": "",
                    "message": (
                        f"Unable to read page text: {exc}"
                    ),
                    "page_name": page_name,
                    "url": page.url,
                }
            )

            return result

        # ============================================================
        # 1. CONTENT / CAPITALIZATION
        # ============================================================

        try:

            result.content_issues = (
                self.content_checker.find_mixed_capitalization(
                    text
                )
            )

        except AttributeError:

            # Compatibility with an older ContentChecker.

            if hasattr(
                self.content_checker,
                "check",
            ):
                result.content_issues = (
                    self.content_checker.check(text)
                )
            else:
                result.content_issues = []

        except Exception as exc:

            result.content_issues = [
                {
                    "type": "Content Scanner Error",
                    "element": "",
                    "text": "",
                    "message": str(exc),
                    "page_name": page_name,
                    "url": page.url,
                }
            ]

        result.content_issues = self._normalize_issues(
            result.content_issues,
            page_name,
            page.url,
            category="CONTENT / CAPITALIZATION",
        )
        for issue in result.content_issues:
            if issue.get("type") == "Mixed Capitalization":
                issue.setdefault("expected", issue.get("suggestion"))

        # ============================================================
        # 2. SPELLING / GRAMMAR
        # ============================================================

        if self.enable_language_tool:

            try:

                result.language_issues = (
                    self.language_checker.check(
                        text,
                        language=self.language,
                    )
                )

            except Exception as exc:

                # LanguageTool failure must NOT stop the complete
                # CVA UI quality scan.

                result.scanner_warnings.append(
                    {
                        "type": "LanguageTool Warning",
                        "message": (
                            "LanguageTool could not be reached: "
                            f"{exc}"
                        ),
                        "page_name": page_name,
                        "url": page.url,
                    }
                )

        else:

            result.language_issues = []

        result.language_issues = self._normalize_issues(
            result.language_issues,
            page_name,
            page.url,
            category="SPELLING / GRAMMAR",
        )
        content_findings = {
            str(issue.get("text", "")).casefold()
            for issue in result.content_issues
        }
        result.language_issues = [
            issue
            for issue in result.language_issues
            if str(issue.get("text", "")).casefold() not in content_findings
        ]
        for issue in result.language_issues:
            suggestions = issue.get("suggestions")
            if suggestions and isinstance(suggestions, list):
                issue.setdefault("expected", suggestions[0])

        # ============================================================
        # 3. UI CONSISTENCY
        # ============================================================

        try:

            result.ui_issues = (
                self.ui_checker.scan_buttons(page)
            )

        except AttributeError:

            # Compatibility with older UIConsistencyChecker.

            if hasattr(
                self.ui_checker,
                "check",
            ):

                result.ui_issues = (
                    self.ui_checker.check(page)
                )

            else:

                result.ui_issues = []

        except Exception as exc:

            result.ui_issues = [
                {
                    "type": "UI Scanner Error",
                    "element": "",
                    "text": "",
                    "message": str(exc),
                    "page_name": page_name,
                    "url": page.url,
                }
            ]

        result.ui_issues = self._normalize_issues(
            result.ui_issues,
            page_name,
            page.url,
            category="BUTTON / UI CONSISTENCY",
        )

        result.scanner_warnings = self._normalize_issues(
            result.scanner_warnings,
            page_name,
            page.url,
            category="SCANNER WARNING",
        )

        # ============================================================
        # ACCESSIBILITY
        # ============================================================
        #
        # Intentionally NOT executed.
        #
        # No AccessibilityChecker is used here.
        #
        # ============================================================

        return result

    @staticmethod
    def _page_text(page) -> str:
        if not hasattr(page, "evaluate"):
            return page.locator("body").inner_text(timeout=10000)

        return page.evaluate(
            """
            () => {
                const visible = element => {
                    for (let current = element; current; current = current.parentElement) {
                        const style = getComputedStyle(current);
                        if (style.display === 'none'
                            || style.visibility === 'hidden'
                            || Number(style.opacity) === 0
                            || current.getAttribute('aria-hidden') === 'true'
                            || current.hasAttribute('inert')) {
                            return false;
                        }
                    }
                    return element.getClientRects().length > 0;
                };
                document.querySelectorAll('[data-bth-quality-scan-root]')
                    .forEach(element => element.removeAttribute('data-bth-quality-scan-root'));
                const close = Array.from(
                    document.querySelectorAll("i.fa-xmark")
                ).find(visible);
                let root = document.body;

                if (close) {
                    for (let element = close.parentElement;
                         element && element !== document.body;
                         element = element.parentElement) {
                        const rect = element.getBoundingClientRect();
                        const dialogLike =
                            element.matches('[role="dialog"], [aria-modal="true"]');
                        const panelSized =
                            rect.width >= innerWidth * 0.3
                            && rect.height >= innerHeight * 0.25
                            && rect.width < innerWidth * 0.98
                            && rect.height < innerHeight * 0.98;
                        if (visible(element) && (dialogLike || panelSized)) {
                            root = element;
                            break;
                        }
                    }
                }
                root.setAttribute('data-bth-quality-scan-root', '1');

                const excluded = [
                    'script', 'style', 'noscript', 'tbody', 'tr',
                    '[role="grid"]', '[role="row"]', '.table-rf-row',
                    'input', 'textarea', 'select', '[contenteditable="true"]'
                ].join(',');
                const walker = document.createTreeWalker(
                    root,
                    NodeFilter.SHOW_TEXT,
                    {
                        acceptNode: node => {
                            const element = node.parentElement;
                            if (!element || !visible(element)
                                || element.closest(excluded)
                                || element.closest(
                                    'nav, aside, [role="navigation"], a.nav-link'
                                )) {
                                return NodeFilter.FILTER_REJECT;
                            }
                            const parentText = (element.parentElement?.innerText || '').trim();
                            if (/^Current Domain\\s*:/i.test(parentText)) {
                                return NodeFilter.FILTER_REJECT;
                            }
                            const value = (node.nodeValue || '').trim();
                            return value
                                ? NodeFilter.FILTER_ACCEPT
                                : NodeFilter.FILTER_REJECT;
                        }
                    }
                );
                const parts = [];
                let node;
                while ((node = walker.nextNode())) {
                    parts.push(node.nodeValue.trim());
                }
                return parts.join(' ');
            }
            """
        )

    # =================================================================
    # ISSUE NORMALIZATION
    # =================================================================

    @staticmethod
    def _normalize_issues(
        issues: list[dict[str, Any]] | None,
        page_name: str,
        url: str,
        category: str,
    ) -> list[dict[str, Any]]:
        """
        Normalize issues returned by individual checkers so the
        reporting layer receives a consistent structure.
        """

        if not issues:
            return []

        normalized: list[dict[str, Any]] = []

        for issue in issues:

            if not isinstance(issue, dict):
                continue

            item = dict(issue)

            # --------------------------------------------------------
            # Page information
            # --------------------------------------------------------

            item.setdefault(
                "page_name",
                page_name,
            )

            item.setdefault(
                "url",
                url,
            )

            item.setdefault(
                "category",
                category,
            )

            # --------------------------------------------------------
            # Issue type
            # --------------------------------------------------------

            item.setdefault(
                "type",
                category,
            )

            # --------------------------------------------------------
            # Element / text
            # --------------------------------------------------------

            if "element" not in item:

                item["element"] = (
                    item.get("text")
                    or item.get("matched_text")
                    or ""
                )

            if "text" not in item:

                item["text"] = (
                    item.get("element")
                    or ""
                )

            # --------------------------------------------------------
            # Message
            # --------------------------------------------------------

            if "message" not in item:

                item["message"] = (
                    "UI quality issue detected."
                )

            # --------------------------------------------------------
            # Suggestion
            # --------------------------------------------------------

            if (
                "suggestion" not in item
                and item.get("suggestions")
            ):

                suggestions = item["suggestions"]

                if (
                    isinstance(
                        suggestions,
                        list,
                    )
                    and suggestions
                ):

                    item["suggestion"] = (
                        suggestions[0]
                    )

            normalized.append(item)

        return normalized

    # =================================================================
    # ISSUE COUNT
    # =================================================================

    @staticmethod
    def count_issues(
        result: ScanResult,
    ) -> dict[str, int]:
        """
        Return issue counts by category.
        """

        return {
            "content": len(
                result.content_issues
            ),
            "language": len(
                result.language_issues
            ),
            "ui": len(
                result.ui_issues
            ),
            "total": result.total_issues,
        }