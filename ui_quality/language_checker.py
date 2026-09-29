from __future__ import annotations

import os
import re
from typing import Iterable

import requests

from .content_checker import DEFAULT_IGNORED_WORDS

try:
    import truststore
except ImportError:
    truststore = None

# Use the Windows/OS trust store when available. This is important on corporate
# networks where HTTPS inspection may install a trusted corporate CA that is not
# present in certifi's bundle.
if truststore is not None:
    truststore.inject_into_ssl()


class LanguageToolChecker:
    """LanguageTool HTTP API client with OS certificate-store support."""

    DEFAULT_URL = "https://api.languagetool.org/v2/check"

    def __init__(
        self,
        api_url: str | None = None,
        ignored_words: Iterable[str] | None = None,
        timeout: int = 30,
    ):
        self.api_url = api_url or os.getenv("LANGUAGE_TOOL_URL", self.DEFAULT_URL)
        self.timeout = timeout
        self.ignored_words = {
            word.strip().lower()
            for word in (ignored_words or DEFAULT_IGNORED_WORDS)
            if word and word.strip()
        }

    def check(self, text: str, language: str = "en-US") -> list[dict]:
        if not text.strip():
            return []

        response = requests.post(
            self.api_url,
            data={"text": text, "language": language},
            timeout=self.timeout,
        )
        response.raise_for_status()

        matches = response.json().get("matches", [])
        issues: list[dict] = []

        for match in matches:
            context = match.get("context", {})
            context_text = context.get("text", "")
            matched_text = self._matched_text(match, context_text)

            if (
                not matched_text.strip()
                or not matched_text.strip(".… ")
                or self._is_domain_label(context_text, matched_text)
                or self._contains_ignored_word(matched_text)
                or self._is_person_metadata(context_text)
            ):
                continue

            replacements = [
                replacement.get("value")
                for replacement in match.get("replacements", [])[:5]
                if replacement.get("value")
            ]

            issues.append(
                {
                    "type": "Spelling / Grammar",
                    "text": matched_text,
                    "actual": matched_text,
                    "message": match.get("message", "Language issue detected."),
                    "suggestions": replacements,
                    "context": context_text,
                    "offset": match.get("offset"),
                    "length": match.get("length"),
                    "rule": match.get("rule", {}).get("id"),
                    "category": match.get("rule", {}).get("category", {}).get("id"),
                }
            )

        unique_issues = {}
        for issue in issues:
            if not issue["text"].strip():
                continue
            key = (
                issue["text"].casefold(),
                issue["message"],
                tuple(issue["suggestions"]),
            )
            unique_issues.setdefault(key, issue)

        return list(unique_issues.values())

    def _contains_ignored_word(self, text: str) -> bool:
        if not self.ignored_words:
            return False

        tokens = {
            token.lower()
            for token in re.findall(r"[A-Za-z][A-Za-z0-9_-]*", text)
        }
        return bool(tokens & self.ignored_words)

    @staticmethod
    def _is_domain_label(context: str, matched_text: str) -> bool:
        match = re.search(
            r"current\s+domain\s*:\s*([a-z0-9][a-z0-9.-]*)",
            context,
            flags=re.IGNORECASE,
        )
        return bool(match and matched_text.casefold() == match.group(1).casefold())

    @staticmethod
    def _is_person_metadata(context: str) -> bool:
        return bool(
            re.search(
                r"\b(?:submitted|approved|created|updated)\s+by\s*:",
                context,
                flags=re.IGNORECASE,
            )
        )

    @staticmethod
    def _matched_text(match: dict, context_text: str) -> str:
        context = match.get("context", {})
        offset = context.get("offset")
        if offset is None:
            offset = match.get("offsetInContext")
        if offset is None:
            return ""

        length = match.get("length")

        if (
            isinstance(offset, int)
            and isinstance(length, int)
            and 0 <= offset < len(context_text)
        ):
            return context_text[offset : offset + length]

        return ""
