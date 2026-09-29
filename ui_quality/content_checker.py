from __future__ import annotations

import re
from typing import Iterable

# Application/domain words that should not be reported as spelling/mixed-case issues.
DEFAULT_IGNORED_WORDS = {
    "CVA",
    "SCI",
    "BMZ",
    "PDM",
    "Kobo",
    "API",
    "URL",
    "ID",
    "IDs",
    "UI",
    "UX",
    "HTML",
    "CSS",
    "JavaScript",
    "Playwright",
    "GitHub",
    "PowerPoint",
    "SaveTheChildren",
    "BeneficiaryID",
    "PaymentID",
    "AdminSuper",
    "AfN",
    "Habib",
    "Saffat",
    "Saffa",
    "Shah",
    "Newaj",
    "Asma",
    "Ul",
    "Husna",
    "Binte",
    "Sharif",
    "Simin",
    "Sadia",
    "Chowd",
    "Super",
    "sci-co-niger",
}


class ContentChecker:
    """Detect simple content-quality problems without requiring a baseline."""

    def __init__(self, ignored_words: Iterable[str] | None = None):
        self.ignored_words = {
            word.strip().casefold()
            for word in (ignored_words or DEFAULT_IGNORED_WORDS)
            if word and word.strip()
        }

    def find_mixed_capitalization(self, text: str) -> list[dict]:
        """
        Find words such as 'OverView' where a lowercase letter is
        immediately followed by an uppercase letter.

        This is intentionally a heuristic. Known product/technical terms
        are excluded to reduce false positives.
        """
        pattern = re.compile(r"\b[A-Za-z]+[a-z][A-Z][A-Za-z]*\b")
        issues: list[dict] = []

        for word in dict.fromkeys(pattern.findall(text)):
            if word.casefold() in self.ignored_words:
                continue

            issues.append(
                {
                    "type": "Mixed Capitalization",
                    "text": word,
                    "actual": word,
                    "message": (
                        f"Possible incorrect capitalization in '{word}'. "
                        "Check whether the word should use normal title/sentence casing."
                    ),
                    "suggestion": self._simple_suggestion(word),
                    "expected": self._simple_suggestion(word),
                }
            )

        return issues

    @staticmethod
    def _simple_suggestion(word: str) -> str:
        """
        Conservative suggestion for UI labels.

        We do not try to rewrite arbitrary camelCase technical terms here.
        For labels such as OverView this produces Overview.
        """
        if not word:
            return word

        # Preserve the first character and lowercase the rest.
        return word[0] + word[1:].lower()
