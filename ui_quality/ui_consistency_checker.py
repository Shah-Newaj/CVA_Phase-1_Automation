from __future__ import annotations

from collections import Counter, defaultdict


class UIConsistencyChecker:
    """
    Baseline-free UI consistency checks for the CVA application.

    Important CVA-specific behavior:
      * The normal ``Add New`` control is a real ``button`` containing an
        icon and a ``span``. We count only actual text-node line boxes, so the
        icon/span structure is NOT incorrectly reported as multi-line text.
      * Project Criteria Setup ``Save`` is not a button. It is rendered as
        ``.rf-form-header-action-save > .rf-form-header-action-save-only``.
        It receives a dedicated check instead of the generic button rules.
    """

    BUTTON_SELECTOR = (
        "button, input[type='button'], input[type='submit'], [role='button'], "
        ".rf-form-header-action-save-only"
    )

    SAVE_SELECTOR = ".rf-form-header-action-save-only"

    def __init__(
        self,
        minimum_button_height: float = 30.0,
        minimum_font_size: float = 10.0,
        detect_square_button_outliers: bool = True,
        minimum_horizontal_label_space: float = 20.0,
    ):
        self.minimum_button_height = minimum_button_height
        self.minimum_font_size = minimum_font_size
        self.detect_square_button_outliers = detect_square_button_outliers
        self.minimum_horizontal_label_space = minimum_horizontal_label_space

    def scan_buttons(self, page) -> list[dict]:
        records: list[dict] = []
        issues: list[dict] = []

        buttons = page.locator(self.BUTTON_SELECTOR)

        for index in range(buttons.count()):
            element = buttons.nth(index)

            try:
                if not element.is_visible():
                    continue

                record = element.evaluate(self._collect_record_js())
                if record:
                    records.append(record)

            except Exception as exc:
                records.append(
                    {
                        "text": f"<button #{index + 1}>",
                        "scan_error": str(exc),
                    }
                )

        # ------------------------------------------------------------
        # Generic controls
        # ------------------------------------------------------------
        for record in records:
            if "scan_error" in record:
                issues.append(
                    {
                        "type": "UI Scan Error",
                        "element": record["text"],
                        "message": record["scan_error"],
                    }
                )
                continue

            text = record["text"] or "<Unnamed button>"

            # Project Criteria Save has its own dedicated rule below.
            if record.get("isCustomSave"):
                continue

            if record.get("textLines", 0) > 1:
                issues.append(
                    {
                        "type": "Button Text Wrapping",
                        "element": text,
                        "actual": f"{record['textLines']} lines",
                        "expected": "1 line",
                        "message": f"Button '{text}' wraps onto multiple lines.",
                    }
                )

            if (
                record.get("textWidth", 0) > 0
                and record["width"] < record["textWidth"] + 8
            ):
                expected_width = record["textWidth"] + 8
                issues.append(
                    {
                        "type": "Button Label Fit",
                        "element": text,
                        "actual": f"{record['width']:.1f}px wide",
                        "expected": (
                            f">= {expected_width:.1f}px to fit label "
                            "with horizontal spacing"
                        ),
                        "message": (
                            f"Button '{text}' leaves too little horizontal "
                            "space around its label."
                        ),
                    }
                )

            if record["height"] < self.minimum_button_height:
                issues.append(
                    {
                        "type": "Button Height",
                        "element": text,
                        "actual": f"{record['height']:.1f}px",
                        "expected": f">= {self.minimum_button_height:.0f}px",
                        "message": f"Button '{text}' is unusually short.",
                    }
                )

            font_size = self._px(record["fontSize"])
            if font_size < self.minimum_font_size:
                issues.append(
                    {
                        "type": "Button Font Size",
                        "element": text,
                        "actual": f"{font_size:.1f}px",
                        "expected": f">= {self.minimum_font_size:.0f}px",
                        "message": f"Button '{text}' has unusually small text.",
                    }
                )

        # ------------------------------------------------------------
        # Dedicated CVA Project Criteria Setup Save check
        # ------------------------------------------------------------
        for record in records:
            if not record.get("isCustomSave"):
                continue

            text = (record.get("text") or "").strip()
            if text.casefold() != "save":
                continue

            wrapper_width = float(record.get("saveWrapperWidth") or 0)
            text_width = float(record.get("textWidth") or 0)
            horizontal_space = wrapper_width - text_width
            left_padding = self._px(record.get("savePaddingLeft", "0px"))
            right_padding = self._px(record.get("savePaddingRight", "0px"))

            # The CVA application standard .button-rf uses 10px horizontal
            # padding on each side. A broken Save control renders almost the
            # exact text width (31.5px) with no horizontal space.
            if (
                horizontal_space < self.minimum_horizontal_label_space
                or left_padding < 10
                or right_padding < 10
            ):
                issues.append(
                    {
                        "type": "UI Spacing Anomaly",
                        "element": "Save",
                        "actual": (
                            f"wrapperWidth={wrapper_width:.1f}px, "
                            f"textWidth={text_width:.1f}px, "
                            f"left={left_padding:.1f}px, "
                            f"right={right_padding:.1f}px"
                        ),
                        "expected": (
                            "At least 10px horizontal padding on each side "
                            "of the Save action"
                        ),
                        "message": (
                            "Custom form action 'Save' has reduced horizontal "
                            "spacing around its label."
                        ),
                        "suggestion": (
                            "Review the horizontal padding of the Save action "
                            "against the standard application button spacing."
                        ),
                        "padding_left": left_padding,
                        "padding_right": right_padding,
                        "width": wrapper_width,
                        "textWidth": text_width,
                        "target": record.get("saveTarget"),
                    }
                )

        # ------------------------------------------------------------
        # Shape/style checks for ordinary controls only
        # ------------------------------------------------------------
        normal_records = [
            r for r in records
            if "scan_error" not in r and not r.get("isCustomSave")
        ]

        if self.detect_square_button_outliers:
            radius_values = [self._radius(r) for r in normal_records]
            rounded_count = sum(radius > 0 for radius in radius_values)
            square_count = sum(radius == 0 for radius in radius_values)

            if len(radius_values) >= 3 and rounded_count >= 2 and square_count >= 1:
                for record in normal_records:
                    if self._radius(record) == 0:
                        text = record["text"] or "<Unnamed button>"
                        issues.append(
                            {
                                "type": "Button Shape Outlier",
                                "element": text,
                                "actual": "0px border radius",
                                "expected": (
                                    "Rounded corners consistent with the "
                                    "majority of visible buttons"
                                ),
                                "message": (
                                    f"Button '{text}' has square corners while "
                                    "the majority of visible buttons are rounded."
                                ),
                            }
                        )

        style_groups = defaultdict(list)
        for record in normal_records:
            key = (
                record["backgroundColor"],
                record["borderColor"],
                record["fontSize"],
                record["fontWeight"],
                round(record["height"]),
            )
            style_groups[key].append(record)

        for group in style_groups.values():
            if len(group) < 2:
                continue

            radii = Counter(self._radius(record) for record in group)
            if len(radii) <= 1:
                continue

            common_radius, common_count = radii.most_common(1)[0]
            if common_count < 2 or common_count <= len(group) / 2:
                continue

            for record in group:
                radius = self._radius(record)
                if radius == common_radius:
                    continue

                text = record["text"] or "<Unnamed button>"
                issues.append(
                    {
                        "type": "Button Style Inconsistency",
                        "element": text,
                        "actual": f"{radius:g}px border radius",
                        "expected": (
                            f"{common_radius:g}px, matching "
                            f"{common_count}/{len(group)} similar buttons"
                        ),
                        "message": (
                            f"Button '{text}' is a visual style outlier "
                            "among otherwise similar buttons."
                        ),
                    }
                )

        # Exact duplicate findings are not useful in the report.
        unique: dict[tuple, dict] = {}
        for issue in issues:
            key = (
                issue.get("type"),
                issue.get("element"),
                issue.get("actual"),
            )
            unique[key] = issue

        return list(unique.values())

    @staticmethod
    def _collect_record_js() -> str:
        return r"""
        (el) => {
            const visible = (node) => {
                if (!node) return false;
                for (let current = node; current; current = current.parentElement) {
                    const style = getComputedStyle(current);
                    if (style.display === 'none'
                        || style.visibility === 'hidden'
                        || Number(style.opacity) === 0
                        || current.getAttribute('aria-hidden') === 'true') {
                        return false;
                    }
                }
                const rect = node.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0;
            };

            const isSave = el.matches('.rf-form-header-action-save-only');
            const visual = isSave
                ? (el.closest('.rf-form-header-action-save') || el)
                : el;
            const style = getComputedStyle(visual);
            const rect = visual.getBoundingClientRect();

            const rawText = (
                el.innerText ||
                el.value ||
                el.getAttribute('aria-label') ||
                el.getAttribute('title') ||
                ''
            ).trim();

            // Measure ONLY text nodes. This prevents an icon + text button
            // such as <i>...</i><span>Add New</span> from being counted as
            // multiple text lines.
            const textNodes = [];
            const walker = document.createTreeWalker(
                el,
                NodeFilter.SHOW_TEXT,
                {
                    acceptNode: node => {
                        const value = (node.nodeValue || '').trim();
                        if (!value) return NodeFilter.FILTER_REJECT;
                        if (node.parentElement &&
                            node.parentElement.closest('i, svg, script, style')) {
                            return NodeFilter.FILTER_REJECT;
                        }
                        return visible(node.parentElement)
                            ? NodeFilter.FILTER_ACCEPT
                            : NodeFilter.FILTER_REJECT;
                    }
                }
            );

            let node;
            while ((node = walker.nextNode())) textNodes.push(node);

            const lineYs = [];
            for (const textNode of textNodes) {
                const range = document.createRange();
                range.selectNodeContents(textNode);
                for (const r of range.getClientRects()) {
                    if (r.width <= 0 || r.height <= 0) continue;
                    if (!lineYs.some(y => Math.abs(y - r.top) <= 1.5)) {
                        lineYs.push(r.top);
                    }
                }
            }

            const canvas = document.createElement('canvas');
            const context = canvas.getContext('2d');
            if (context) context.font = style.font;
            const textWidth = context && rawText
                ? context.measureText(rawText).width
                : 0;

            const saveWrapper = isSave
                ? (el.closest('.rf-form-header-action-save') || el)
                : null;
            const saveStyle = saveWrapper ? getComputedStyle(saveWrapper) : null;
            const saveRect = saveWrapper
                ? saveWrapper.getBoundingClientRect()
                : null;

            let saveTarget = null;
            if (isSave) {
                const selector = '.rf-form-header-action-save-only';
                saveTarget = selector;
            }

            return {
                text: rawText,
                tag: el.tagName.toLowerCase(),
                className: typeof el.className === 'string' ? el.className : '',
                width: rect.width,
                height: rect.height,
                x: rect.x,
                y: rect.y,
                borderRadius: style.borderRadius,
                borderTopLeftRadius: style.borderTopLeftRadius,
                borderTopRightRadius: style.borderTopRightRadius,
                borderBottomRightRadius: style.borderBottomRightRadius,
                borderBottomLeftRadius: style.borderBottomLeftRadius,
                fontSize: style.fontSize,
                fontWeight: style.fontWeight,
                paddingLeft: style.paddingLeft,
                paddingRight: style.paddingRight,
                backgroundColor: style.backgroundColor,
                borderColor: style.borderColor,
                display: style.display,
                textLines: Math.max(lineYs.length, rawText ? 1 : 0),
                textWidth,
                isCustomSave: isSave,
                saveWrapperWidth: saveRect ? saveRect.width : 0,
                savePaddingLeft: saveStyle ? saveStyle.paddingLeft : '0px',
                savePaddingRight: saveStyle ? saveStyle.paddingRight : '0px',
                saveTarget,
            };
        }
        """

    @staticmethod
    def _px(value: str | float | int) -> float:
        try:
            return float(str(value).replace('px', '').strip())
        except (ValueError, AttributeError, TypeError):
            return 0.0

    @classmethod
    def _radius(cls, record: dict) -> float:
        values = [
            cls._px(record.get('borderTopLeftRadius', '0px')),
            cls._px(record.get('borderTopRightRadius', '0px')),
            cls._px(record.get('borderBottomRightRadius', '0px')),
            cls._px(record.get('borderBottomLeftRadius', '0px')),
        ]
        return min(values) if values else 0.0
