#!/usr/bin/env python3
"""Validate GamsGo price pages, covers, links and index integration."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from build_gamsgo_price_content import PRODUCTS, ROOT
from validate_u7buy_content import PageParser, local_target


ARTICLES = ROOT / "articles"
HUB_SLUGS = [
    "gamsgo-nouveautes-prix-2026",
    "gamsgo-avis-2026",
    "gamsgo-abonnements-moins-cher",
]


def validate_page(path: Path, price_page: bool) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    parser = PageParser()
    parser.feed(text)

    if len(re.findall(r"<title>.*?</title>", text, flags=re.I | re.S)) != 1:
        errors.append(f"{path.name}: expected one title")
    if len(re.findall(r"<h1\b", text, flags=re.I)) != 1:
        errors.append(f"{path.name}: expected one h1")

    descriptions = [
        attrs.get("content", "")
        for tag, attrs in parser.tags
        if tag == "meta" and attrs.get("name") == "description"
    ]
    if len(descriptions) != 1 or not 105 <= len(descriptions[0]) <= 180:
        errors.append(f"{path.name}: invalid meta description")

    expected_canonical = f"https://euromalin.com/articles/{path.stem}.html"
    canonicals = [
        attrs.get("href", "")
        for tag, attrs in parser.tags
        if tag == "link" and attrs.get("rel") == "canonical"
    ]
    if canonicals != [expected_canonical]:
        errors.append(f"{path.name}: canonical mismatch")

    hero_images = [
        attrs.get("src", "")
        for tag, attrs in parser.tags
        if tag == "img" and "article-hero-image" in attrs.get("class", "").split()
    ]
    if len(hero_images) != 1:
        errors.append(f"{path.name}: expected one API cover")

    for tag, attrs in parser.tags:
        if tag not in {"a", "img", "script", "link"}:
            continue
        attr_name = "href" if tag in {"a", "link"} else "src"
        target = local_target(path, attrs.get(attr_name, ""))
        if target is not None and not target.exists():
            errors.append(f"{path.name}: missing local target {attrs.get(attr_name, '')}")

    if len(parser.json_blocks) < 3:
        errors.append(f"{path.name}: structured data is incomplete")

    for tag, attrs in parser.tags:
        if tag != "a" or "gamsgo.com/partner/" not in attrs.get("href", ""):
            continue
        rel = set(attrs.get("rel", "").split())
        if not {"sponsored", "noopener", "noreferrer"}.issubset(rel):
            errors.append(f"{path.name}: GamsGo affiliate rel is incomplete")

    if "affiliate-disclosure" not in text:
        errors.append(f"{path.name}: affiliate disclosure is missing")
    if price_page:
        if "Comment payer environ" not in text:
            errors.append(f"{path.name}: price-led title is missing")
        if "1,1694" not in text or "BCE" not in text:
            errors.append(f"{path.name}: dated EUR conversion is missing")
        if "24 juillet 2026" not in text:
            errors.append(f"{path.name}: observation date is missing")

    forbidden = ["totalement légal", "en toute légalité", "prix garanti", "sans aucun risque"]
    for phrase in forbidden:
        if phrase.casefold() in text.casefold():
            errors.append(f"{path.name}: overstated claim found: {phrase}")
    return errors


def main() -> int:
    price_slugs = [item.slug for item in PRODUCTS]
    expected = price_slugs + HUB_SLUGS
    errors: list[str] = []
    for slug in expected:
        page = ARTICLES / f"{slug}.html"
        cover = ROOT / "assets" / "img" / "articles" / f"{slug}.jpg"
        if not page.exists():
            errors.append(f"missing page: {slug}")
            continue
        if not cover.exists() or cover.stat().st_size < 10_000:
            errors.append(f"missing or too-small cover: {slug}")
        errors.extend(validate_page(page, slug in price_slugs))

    index = (ROOT / "articles.html").read_text(encoding="utf-8")
    sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    for slug in expected:
        href = f"articles/{slug}.html"
        if index.count(href) != 2:
            errors.append(f"articles.html expected one card for {slug}")
        if f"https://euromalin.com/articles/{slug}.html" not in sitemap:
            errors.append(f"sitemap.xml misses {slug}")

    article_total = len(list((ROOT / "articles").glob("*.html")))
    if f"{article_total} articles déjà intégrés" not in index:
        errors.append(f"articles.html count is not {article_total}")
    if "articles/gamsgo-nouveautes-prix-2026.html" not in (
        ROOT / "index.html"
    ).read_text(encoding="utf-8"):
        errors.append("homepage misses the GamsGo catalog feature")

    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors))
        print(f"\nValidation failed with {len(errors)} issue(s).")
        return 1
    print(
        f"Validation passed: {len(expected)} GamsGo pages, covers, price snapshots, "
        "structured data, affiliate links and sitemap entries."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
