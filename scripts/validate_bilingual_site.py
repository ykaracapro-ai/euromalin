#!/usr/bin/env python3
"""Validate EuroMalin's French/English static pages and affiliate invariants."""

from __future__ import annotations

import posixpath
import re
import xml.etree.ElementTree as ET
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
SITE_URL = "https://euromalin.com"
GAMSGO_URL = "https://www.gamsgo.com/partner/Px5AZ"
REQUIRED_REL = {"sponsored", "noopener", "noreferrer"}
FIXED_CODE_CLAIM = re.compile(
    r"(?is)(?:"
    r"WPQTU.{0,55}(?:pour|for|=|offre|offers?|donne|gives?|avec|with)"
    r".{0,30}(?:-?7\s*%)"
    r"|(?:\+|-)\s*7\s*%\s+(?:avec|with|code).{0,30}WPQTU"
    r")"
)


def public_paths() -> list[Path]:
    paths = list(ROOT.glob("*.html"))
    paths += list((ROOT / "articles").glob("*.html"))
    paths += list((ROOT / "bons-plans").glob("*.html"))
    return sorted(path for path in paths if not path.name.startswith("_"))


def rel_path(path: Path) -> PurePosixPath:
    return PurePosixPath(path.relative_to(ROOT).as_posix())


def fr_url(rel: PurePosixPath) -> str:
    return f"{SITE_URL}/" if rel == PurePosixPath("index.html") else f"{SITE_URL}/{rel}"


def en_url(rel: PurePosixPath) -> str:
    return (
        f"{SITE_URL}/en/"
        if rel == PurePosixPath("index.html")
        else f"{SITE_URL}/en/{rel}"
    )


def hreflang_map(soup: BeautifulSoup) -> dict[str, str]:
    return {
        str(link.get("hreflang")): str(link.get("href"))
        for link in soup.find_all("link", rel=lambda value: value and "alternate" in value)
        if link.get("hreflang") and link.get("href")
    }


def validate_affiliate(path: Path, soup: BeautifulSoup, errors: list[str]) -> None:
    source = path.read_text(encoding="utf-8")
    links = [
        link
        for link in soup.find_all("a", href=True)
        if "gamsgo.com/partner/" in str(link.get("href"))
    ]
    for link in links:
        rel_values = set(link.get("rel") or [])
        if link.get("href") != GAMSGO_URL:
            errors.append(f"{path}: unexpected GamsGo partner URL")
        if link.get("target") != "_blank" or not REQUIRED_REL <= rel_values:
            errors.append(f"{path}: incomplete GamsGo affiliate attributes")
    if links and "WPQTU" not in source:
        errors.append(f"{path}: GamsGo partner link without WPQTU")
    if FIXED_CODE_CLAIM.search(source):
        errors.append(f"{path}: fixed 7% claim tied to WPQTU")


def local_target(
    value: str,
    page_path: Path,
    switcher: bool,
) -> Path | None:
    if not value or value.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
        return None
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc:
        return None
    raw_path = unquote(parsed.path)
    if (
        not raw_path
        or "{{" in raw_path
        or raw_path.lower().endswith((".xml", ".rss", ".atom"))
    ):
        return None

    if raw_path.startswith("/"):
        if switcher and not raw_path.startswith("/en/"):
            return None
        target = ROOT / raw_path.lstrip("/")
        if raw_path.endswith("/"):
            target = target / "index.html"
        return target
    target = (page_path.parent / raw_path).resolve()
    return target


def validate_local_references(
    path: Path,
    soup: BeautifulSoup,
    errors: list[str],
) -> None:
    for tag in soup.find_all(True):
        is_switcher = "language-switcher" in (tag.get("class") or [])
        for attribute in ("href", "src", "poster"):
            value = tag.get(attribute)
            if not isinstance(value, str):
                continue
            target = local_target(value, path, is_switcher)
            if target is not None and not target.exists():
                errors.append(f"{path}: broken {attribute}={value}")


def validate_page_pair(
    french_path: Path,
    english_path: Path,
    rel: PurePosixPath,
    errors: list[str],
) -> None:
    if not english_path.exists():
        errors.append(f"{english_path}: missing English mirror")
        return

    fr_soup = BeautifulSoup(french_path.read_text(encoding="utf-8"), "html.parser")
    en_soup = BeautifulSoup(english_path.read_text(encoding="utf-8"), "html.parser")

    if not fr_soup.html or fr_soup.html.get("lang") != "fr":
        errors.append(f"{french_path}: expected lang=fr")
    if not en_soup.html or en_soup.html.get("lang") != "en":
        errors.append(f"{english_path}: expected lang=en")

    for path, soup, canonical_url in (
        (french_path, fr_soup, fr_url(rel)),
        (english_path, en_soup, en_url(rel)),
    ):
        canonical = soup.find("link", rel=lambda value: value and "canonical" in value)
        if not canonical or canonical.get("href") != canonical_url:
            errors.append(f"{path}: unexpected canonical URL")
        expected_hreflang = {
            "fr": fr_url(rel),
            "en": en_url(rel),
            "x-default": fr_url(rel),
        }
        if hreflang_map(soup) != expected_hreflang:
            errors.append(f"{path}: incomplete hreflang map")
        validate_affiliate(path, soup, errors)

    fr_switch = fr_soup.select_one("a.language-switcher")
    expected_en_path = "/en/" if rel == PurePosixPath("index.html") else f"/en/{rel}"
    if (
        not fr_switch
        or fr_switch.get_text(strip=True) != "EN"
        or fr_switch.get("href") != expected_en_path
    ):
        errors.append(f"{french_path}: invalid English language switch")

    en_switch = en_soup.select_one("a.language-switcher")
    expected_fr_path = "/" if rel == PurePosixPath("index.html") else f"/{rel}"
    if (
        not en_switch
        or en_switch.get_text(strip=True) != "FR"
        or en_switch.get("href") != expected_fr_path
    ):
        errors.append(f"{english_path}: invalid French language switch")

    validate_local_references(english_path, en_soup, errors)


def validate_sitemap(rels: list[PurePosixPath], errors: list[str]) -> None:
    sitemap_path = ROOT / "sitemap.xml"
    tree = ET.parse(sitemap_path)
    namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locations = {
        element.text
        for element in tree.findall(".//sm:loc", namespace)
        if element.text
    }
    included = [rel for rel in rels if rel != PurePosixPath("404.html")]
    expected = {fr_url(rel) for rel in included} | {en_url(rel) for rel in included}
    if locations != expected:
        missing = sorted(expected - locations)
        extra = sorted(locations - expected)
        errors.append(
            f"{sitemap_path}: URL mismatch, missing={missing[:3]}, extra={extra[:3]}"
        )


def main() -> None:
    paths = public_paths()
    rels = [rel_path(path) for path in paths]
    errors: list[str] = []

    for path, rel in zip(paths, rels, strict=True):
        validate_page_pair(path, ROOT / "en" / Path(rel.as_posix()), rel, errors)
    validate_sitemap(rels, errors)

    english_pages = list((ROOT / "en").rglob("*.html"))
    if len(english_pages) != len(paths):
        errors.append(
            f"{ROOT / 'en'}: expected {len(paths)} pages, found {len(english_pages)}"
        )

    if errors:
        print("\n".join(errors))
        raise SystemExit(f"Validation failed with {len(errors)} error(s).")

    print(
        f"Validated {len(paths)} French/English page pairs, "
        f"{len(paths) * 2 - 2} sitemap URLs, and all GamsGo affiliate links."
    )


if __name__ == "__main__":
    main()
