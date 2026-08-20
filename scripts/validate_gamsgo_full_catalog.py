#!/usr/bin/env python3
"""Validate the full GamsGo catalogue additions and affiliate invariants."""

from __future__ import annotations

import re
from pathlib import Path

from bs4 import BeautifulSoup

from build_gamsgo_full_catalog import GAMSGO_CODE, GAMSGO_URL, HUB_SLUG, OFFERS, ROOT


REQUIRED_REL = {"sponsored", "noopener", "noreferrer"}


def main() -> int:
    errors: list[str] = []
    slugs = [HUB_SLUG] + [offer.slug for offer in OFFERS]
    current_slugs = [HUB_SLUG] + [offer.slug for offer in OFFERS if offer.price_record]
    for locale in ("", "en"):
        base = ROOT / locale if locale else ROOT
        for slug in slugs:
            path = base / "articles" / f"{slug}.html"
            if not path.exists():
                errors.append(f"missing {path}")
                continue
            text = path.read_text(encoding="utf-8")
            soup = BeautifulSoup(text, "html.parser")
            if len(soup.find_all("h1")) != 1:
                errors.append(f"{path}: expected one h1")
            if GAMSGO_CODE not in text:
                errors.append(f"{path}: promo code missing")
            links = soup.find_all("a", href=GAMSGO_URL)
            if len(links) < 2:
                errors.append(f"{path}: expected at least two standard affiliate links")
            for link in links:
                if link.get("target") != "_blank" or not REQUIRED_REL <= set(link.get("rel") or []):
                    errors.append(f"{path}: incomplete affiliate attributes")
            canonical = soup.find("link", rel="canonical")
            expected = f"https://euromalin.com/{'en/' if locale else ''}articles/{slug}.html"
            if not canonical or canonical.get("href") != expected:
                errors.append(f"{path}: canonical mismatch")
            if not soup.find("img", class_="article-hero-image"):
                errors.append(f"{path}: hero image missing")
            if slug in current_slugs:
                title = soup.title.get_text(" ", strip=True) if soup.title else ""
                if slug != HUB_SLUG and "dès" not in title.casefold() and "from" not in title.casefold():
                    errors.append(f"{path}: current offer title has no dated starting price")
                if not any("unsplash.com" in str(link.get("href")) for link in soup.find_all("a", href=True)):
                    errors.append(f"{path}: API thumbnail attribution missing")
            if re.search(r"WPQTU.{0,40}(?:7\s*%|remise garantie)", text, re.I | re.S):
                errors.append(f"{path}: unsupported fixed promo claim")

    listing = (ROOT / "articles.html").read_text(encoding="utf-8")
    sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    for slug in current_slugs:
        if listing.count(f"articles/{slug}.html") != 2:
            errors.append(f"articles.html: bad card count for {slug}")
    for slug in slugs:
        for prefix in ("", "en/"):
            if f"https://euromalin.com/{prefix}articles/{slug}.html" not in sitemap:
                errors.append(f"sitemap.xml: missing {prefix}{slug}")
        image = ROOT / "assets" / "img" / "articles" / f"{slug}.jpg"
        if not image.exists() or image.stat().st_size < 20_000:
            errors.append(f"missing or too-small cover: {slug}")

    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors))
        return 1
    print(f"Validated {len(slugs)} GamsGo catalogue pages in French and English.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
