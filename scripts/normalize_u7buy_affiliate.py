#!/usr/bin/env python3
"""Normalize every U7BUY affiliate link to the owner-approved URL."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXACT = "https://www.u7buy.com?referral-code=CzMdAgd4"
AFFILIATE_URL = re.compile(
    r"https://www\.u7buy\.com(?:/[^\"'\s<>?]*)?\?[^\"'\s<>]*"
    r"referral-code=CzMdAgd4[^\"'\s<>]*",
    re.IGNORECASE,
)


def main() -> int:
    paths = [
        *ROOT.glob("*.html"),
        *ROOT.glob("articles/*.html"),
        *ROOT.glob("bons-plans/*.html"),
        *ROOT.glob("en/*.html"),
        *ROOT.glob("en/articles/*.html"),
        *ROOT.glob("en/bons-plans/*.html"),
    ]
    changed = 0
    replacements = 0
    for path in paths:
        before = path.read_text(encoding="utf-8")
        after, count = AFFILIATE_URL.subn(EXACT, before)
        if count and after != before:
            path.write_text(after, encoding="utf-8")
            changed += 1
            replacements += count
    print(f"Normalized {replacements} U7BUY affiliate links in {changed} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
