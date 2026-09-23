from dataclasses import dataclass
from typing import Any

@dataclass
class Step:
    name: str
    status: str = "INFO"
    details: str = ""
    expected: Any = None
    actual: Any = None
    screenshot: str | None = None
