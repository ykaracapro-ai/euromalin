#!/usr/bin/env python3
"""Validate the generated U7BUY/GamsGo editorial cluster."""

from __future__ import annotations

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parent.parent
ARTICLES = ROOT / "articles"
MANIFEST = ROOT / "scripts" / "u7buy_cover_queries.json"


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags: list[tuple[str, dict[str, str]]] = []
        self.json_blocks: list[str] = []
        self._json = False
        self._buffer: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        self.tags.append((tag, values))
        if tag == "script" and values.get("type") == "application/ld+json":
            self._json = True
            self._buffer = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._json:
            self.json_blocks.append("".join(self._buffer).strip())
            self._json = False

    def handle_data(self, data: str) -> None:
        if self._json:
            self._buffer.append(data)


def local_target(page: Path, value: str) -> Path | None:
    if not value or value.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
        return None
    parsed = urlparse(value)
    if parsed.scheme or parsed.netloc:
        return None
    clean = unquote(parsed.path)
    if not clean:
        return None
    target = (page.parent / clean).resolve()
    if clean.endswith("/"):
        target /= "index.html"
    return target


def validate_page(path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    parser = PageParser()
    parser.feed(text)
    tags = parser.tags

    titles = re.findall(r"<title>.*?</title>", text, flags=re.I | re.S)
    h1s = re.findall(r"<h1\b", text, flags=re.I)
    if len(titles) != 1:
        errors.append(f"{path.name}: expected one title, found {len(titles)}")
    if len(h1s) != 1:
        errors.append(f"{path.name}: expected one h1, found {len(h1s)}")

    descriptions = [
        attrs.get("content", "")
        for tag, attrs in tags
        if tag == "meta" and attrs.get("name") == "description"
    ]
    if len(descriptions) != 1:
        errors.append(f"{path.name}: missing or duplicate meta description")
    elif not 105 <= len(descriptions[0]) <= 180:
        errors.append(
            f"{path.name}: meta description length {len(descriptions[0])}, expected 105..180"
        )

    canonicals = [
        attrs.get("href", "")
        for tag, attrs in tags
        if tag == "link" and attrs.get("rel") == "canonical"
    ]
    expected_canonical = f"https://euromalin.com/articles/{path.stem}.html"
    if canonicals != [expected_canonical]:
        errors.append(f"{path.name}: canonical mismatch")

    hero_images = [
        attrs.get("src", "")
        for tag, attrs in tags
        if tag == "img" and "article-hero-image" in attrs.get("class", "").split()
    ]
    if len(hero_images) != 1:
        errors.append(f"{path.name}: expected one article hero image, found {len(hero_images)}")

    for tag, attrs in tags:
        if tag not in {"a", "img", "script", "link"}:
            continue
        attr_name = "href" if tag in {"a", "link"} else "src"
        target = local_target(path, attrs.get(attr_name, ""))
        if target is not None and not target.exists():
            errors.append(
                f"{path.name}: missing local target {attrs.get(attr_name, '')}"
            )

    for block in parser.json_blocks:
        try:
            json.loads(block)
        except json.JSONDecodeError as error:
            errors.append(f"{path.name}: invalid JSON-LD ({error})")
    if len(parser.json_blocks) < 3:
        errors.append(f"{path.name}: expected Article, Breadcrumb and FAQ JSON-LD")

    for tag, attrs in tags:
        if tag != "a":
            continue
        href = attrs.get("href", "")
        rel = set(attrs.get("rel", "").split())
        if "u7buy.com" in href:
            u7_path = urlparse(href).path
            is_reference = (
                u7_path.startswith("/help-center/")
                or u7_path.startswith("/refund-promise")
                or u7_path.startswith("/terms")
            )
            if not is_reference:
                if "referral-code=CzMdAgd4" not in href:
                    errors.append(f"{path.name}: U7BUY link misses referral code")
                if not {"sponsored", "noopener", "noreferrer"}.issubset(rel):
                    errors.append(f"{path.name}: U7BUY affiliate rel is incomplete")
        if "gamsgo.com/partner/" in href:
            if not {"sponsored", "noopener", "noreferrer"}.issubset(rel):
                errors.append(f"{path.name}: GamsGo affiliate rel is incomplete")

    forbidden = [
        "totalement légal",
        "en toute légalité",
        "garantie instantanée",
        "livraison instantanée",
        "moins de 5 minutes",
    ]
    lowered = text.casefold()
    for phrase in forbidden:
        if phrase.casefold() in lowered:
            errors.append(f"{path.name}: stale/overstated claim found: {phrase}")

    if "EURO10" not in text:
        errors.append(f"{path.name}: EURO10 is missing")
    if "affiliate-disclosure" not in text:
        errors.append(f"{path.name}: affiliate disclosure is missing")
    return errors


def main() -> int:
    queries = json.loads(MANIFEST.read_text(encoding="utf-8"))
    expected = sorted(queries)
    errors: list[str] = []

    for slug in expected:
        page = ARTICLES / f"{slug}.html"
        cover = ROOT / "assets" / "img" / "articles" / f"{slug}.jpg"
        if not page.exists():
            errors.append(f"missing page: {page}")
            continue
        if not cover.exists() or cover.stat().st_size < 10_000:
            errors.append(f"missing or too-small cover: {cover}")
        errors.extend(validate_page(page))

    articles_index = (ROOT / "articles.html").read_text(encoding="utf-8")
    economies_index = (ROOT / "economies.html").read_text(encoding="utf-8")
    homepage = (ROOT / "index.html").read_text(encoding="utf-8")
    sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    for slug in expected:
        article_href = f"articles/{slug}.html"
        if article_href not in articles_index:
            errors.append(f"articles.html misses card/link for {slug}")
        if articles_index.count(article_href) != 2:
            errors.append(
                f"articles.html expected two card links for {slug}, "
                f"found {articles_index.count(article_href)}"
            )
        if economies_index.count(article_href) > 2:
            errors.append(f"economies.html contains duplicate cards for {slug}")
        if f"https://euromalin.com/articles/{slug}.html" not in sitemap:
            errors.append(f"sitemap.xml misses {slug}")

    if "articles/u7buy-vs-gamsgo.html" not in homepage:
        errors.append("homepage misses the U7BUY vs GamsGo feature")

    if ".claude/settings.local.json" in {
        str(path.relative_to(ROOT)).replace("\\", "/")
        for path in ROOT.rglob("*")
        if path.is_file()
    }:
        errors.append("tracked/local settings file with credentials is still present")

    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors))
        print(f"\nValidation failed with {len(errors)} issue(s).")
        return 1
    print(
        f"Validation passed: {len(expected)} pages, covers, structured data, "
        "affiliate links, internal links and sitemap entries."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
