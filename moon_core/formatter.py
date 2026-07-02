"""
moon_core/formatter.py
======================
Pre-processor for LLM output before it reaches telegramify-markdown.

Telegram has no native table support. telegramify-markdown renders tables
as <pre> ASCII-art blocks which look ugly on mobile.

This module converts Markdown tables → clean bullet-point Markdown,
which telegramify-markdown then renders correctly as bold/entity text.

Everything else (bold, italic, code, lists, blockquotes) is left untouched
for telegramify-markdown to handle natively.
"""

import re


def _table_to_bullets(match: re.Match) -> str:
    """Convert a single Markdown table block to bullet-point Markdown."""
    raw = match.group(0)
    rows = [r.strip() for r in raw.strip().splitlines() if r.strip()]

    parsed = []
    for row in rows:
        cells = [c.strip() for c in row.strip("|").split("|")]
        # Skip separator rows: | :--- | --- |
        if all(re.match(r'^[:\-\s]+$', c) for c in cells if c):
            continue
        parsed.append(cells)

    if len(parsed) < 2:
        # Not enough rows to make sense — return as-is
        return raw

    headers = parsed[0]
    data_rows = parsed[1:]

    lines = []
    for row in data_rows:
        if len(headers) == 2 and len(row) >= 2:
            # Two-column table → "**Header1:** value | **Header2:** value"
            lines.append(f"**{row[0]}:** {row[1]}")
        else:
            # Multi-column → bullet with label:value pairs
            parts = []
            for i, cell in enumerate(row):
                label = headers[i] if i < len(headers) else f"Col{i+1}"
                parts.append(f"**{label}:** {cell}")
            lines.append("• " + "\n  ".join(parts))

    return "\n".join(lines)


def preprocess_for_telegram(text: str) -> str:
    """
    Sanitize LLM Markdown output before passing to telegramify-markdown.

    Currently handles:
    - Markdown tables → bullet-point Markdown

    telegramify-markdown handles everything else (bold, italic, code, etc.)
    """
    # Match one or more consecutive table rows (lines starting and ending with |)
    text = re.sub(
        r'((?:^[ \t]*\|.+\|[ \t]*\n?)+)',
        _table_to_bullets,
        text,
        flags=re.MULTILINE
    )
    return text
