#!/usr/bin/env python3
"""Validate brand-exclusive articles and the approved affiliate URLs."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
U7 = "https://www.u7buy.com?referral-code=CzMdAgd4"
GAMSGO = "https://www.gamsgo.com/partner/Px5AZ"
PAGES = {
    "u7buy-guide-achat-securise-2026": ("gamsgo", U7, "EURO10"),
    "u7buy-comptes-items-top-up-guide": ("gamsgo", U7, "EURO10"),
    "gamsgo-guide-abonnements-2026": ("u7buy", GAMSGO, "WPQTU"),
    "gamsgo-ia-streaming-logiciels": ("u7buy", GAMSGO, "WPQTU"),
}


def main() -> int:
    for locale_prefix in ("", "en/"):
        for slug, (forbidden, affiliate, code) in PAGES.items():
            path = ROOT / locale_prefix / "articles" / f"{slug}.html"
            assert path.exists(), path
            source = path.read_text(encoding="utf-8")
            assert forbidden not in source.casefold(), f"{path}: mentions {forbidden}"
            assert affiliate in source, f"{path}: missing approved affiliate"
            assert code in source, f"{path}: missing code"
            assert source.count("<h1>") == 1, f"{path}: invalid H1"
            assert "application/ld+json" in source, f"{path}: missing structured data"

    bad_u7: list[tuple[Path, str]] = []
    checked = 0
    public_pages = [
        *ROOT.glob("*.html"),
        *ROOT.glob("articles/*.html"),
        *ROOT.glob("bons-plans/*.html"),
        *ROOT.glob("en/*.html"),
        *ROOT.glob("en/articles/*.html"),
        *ROOT.glob("en/bons-plans/*.html"),
    ]
    for path in public_pages:
        source = path.read_text(encoding="utf-8")
        for url in re.findall(r"""href=["'](https://www\.u7buy\.com[^"']*)["']""", source, re.I):
            if "referral-code=" in url.casefold():
                checked += 1
                if url != U7:
                    bad_u7.append((path, url))
    assert not bad_u7, f"Unapproved U7BUY links: {bad_u7[:10]}"

    listing = (ROOT / "articles.html").read_text(encoding="utf-8")
    english_listing = (ROOT / "en" / "articles.html").read_text(encoding="utf-8")
    assert "89 articles déjà intégrés" in listing
    assert "89 articles already integrated" in english_listing
    for slug in PAGES:
        assert f"articles/{slug}.html" in listing
        assert f"articles/{slug}.html" in english_listing
        image = ROOT / "assets" / "img" / "articles" / f"{slug}.jpg"
        assert image.exists() and image.stat().st_size > 50_000, image

    print(
        "Validated 8 exclusive pages, 4 covers, 89 listed articles, "
        f"and {checked} exact U7BUY affiliate links."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
