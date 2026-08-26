#!/usr/bin/env python3
"""Apply deterministic SEO hygiene and GamsGo topic-cluster improvements.

The transform deliberately preserves the existing HTML formatting. It can be
rerun after the catalogue or English-site generators without duplicating links
or disclosure markers.
"""

from __future__ import annotations

import html
import json
import posixpath
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
TODAY = "2026-08-26"
AFFILIATE_DOMAINS = ("gamsgo.com", "u7buy.com", "igraal.com", "amazon.fr")
RELATED_START = "<!-- seo-related-gamsgo:begin -->"
RELATED_END = "<!-- seo-related-gamsgo:end -->"
DEAL_PLACEHOLDER = ROOT / "assets" / "img" / "bons-plans" / "euromalin-bon-plan-placeholder.svg"

A_TAG_RE = re.compile(r"<a\b[^>]*>", re.I | re.S)
IMG_TAG_RE = re.compile(r"<img\b[^>]*>", re.I | re.S)
META_TAG_RE = re.compile(r"<meta\b[^>]*>", re.I | re.S)
ATTR_RE_TEMPLATE = r"\b{attribute}\s*=\s*([\"'])(.*?)\1"


def attribute(tag: str, name: str) -> str | None:
    match = re.search(ATTR_RE_TEMPLATE.format(attribute=re.escape(name)), tag, re.I | re.S)
    return html.unescape(match.group(2).strip()) if match else None


def set_attribute(tag: str, name: str, value: str) -> str:
    escaped = html.escape(value, quote=True)
    pattern = re.compile(ATTR_RE_TEMPLATE.format(attribute=re.escape(name)), re.I | re.S)
    if pattern.search(tag):
        return pattern.sub(f'{name}="{escaped}"', tag, count=1)
    closing = "/>" if tag.rstrip().endswith("/>") else ">"
    position = tag.rfind(closing)
    return tag[:position] + f' {name}="{escaped}"' + tag[position:]


def sitemap_files() -> list[Path]:
    tree = ElementTree.parse(ROOT / "sitemap.xml")
    namespace = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    paths: list[Path] = []
    for node in tree.findall(".//s:loc", namespace):
        url_path = unquote(urlsplit((node.text or "").strip()).path)
        path = ROOT / (url_path.lstrip("/") or "index.html")
        if url_path.endswith("/"):
            path /= "index.html"
        if path.is_file():
            paths.append(path)
    return paths


def qualify_affiliate_links(text: str, stats: Counter[str]) -> str:
    def replace(match: re.Match[str]) -> str:
        tag = match.group(0)
        href = attribute(tag, "href") or ""
        host = (urlsplit(href).hostname or "").lower()
        if not any(host == domain or host.endswith(f".{domain}") for domain in AFFILIATE_DOMAINS):
            return tag
        rel_pattern = re.compile(
            r"\s+" + ATTR_RE_TEMPLATE.format(attribute="rel"),
            re.I | re.S,
        )
        rel_matches = list(rel_pattern.finditer(tag))
        values = [value for rel_match in rel_matches for value in rel_match.group(2).split()]
        if "sponsored" not in {value.lower() for value in values}:
            values.insert(0, "sponsored")
            stats["affiliate_links_qualified"] += 1
        if len(rel_matches) > 1:
            stats["affiliate_rel_attributes_deduplicated"] += 1
        values = list(dict.fromkeys(value.lower() for value in values))
        tag = rel_pattern.sub("", tag)
        return set_attribute(tag, "rel", " ".join(values))

    return A_TAG_RE.sub(replace, text)


def local_image_path(page: Path, src: str) -> Path | None:
    parts = urlsplit(src)
    if parts.scheme and parts.scheme not in {"http", "https"}:
        return None
    if parts.netloc and parts.netloc.lower() not in {"euromalin.com", "www.euromalin.com"}:
        return None
    url_path = unquote(parts.path)
    if parts.netloc or url_path.startswith("/"):
        normalized = posixpath.normpath(url_path).lstrip("/")
        candidate = ROOT / normalized
    else:
        candidate = page.parent / url_path
    try:
        candidate = candidate.resolve()
        candidate.relative_to(ROOT.resolve())
    except (OSError, ValueError):
        return None
    return candidate if candidate.is_file() else None


def add_image_dimensions(text: str, page: Path, stats: Counter[str]) -> str:
    og_image_match = re.search(
        r'<meta\b(?=[^>]*\bproperty=["\']og:image["\'])[^>]*\bcontent=(["\'])(.*?)\1[^>]*>',
        text,
        re.I | re.S,
    )
    og_image = html.unescape(og_image_match.group(2)) if og_image_match else ""

    def replace(match: re.Match[str]) -> str:
        tag = match.group(0)
        if attribute(tag, "width") and attribute(tag, "height"):
            return tag
        src = attribute(tag, "src")
        image_path = local_image_path(page, src or og_image)
        if not image_path and not src and DEAL_PLACEHOLDER.is_file():
            image_path = DEAL_PLACEHOLDER.resolve()
        if not image_path:
            return tag
        if image_path.suffix.lower() == ".svg":
            svg = image_path.read_text(encoding="utf-8")
            view_box = re.search(r'\bviewBox=["\']\s*0\s+0\s+([0-9.]+)\s+([0-9.]+)["\']', svg)
            if not view_box:
                return tag
            width, height = (round(float(view_box.group(1))), round(float(view_box.group(2))))
        else:
            try:
                with Image.open(image_path) as image:
                    width, height = image.size
            except (OSError, ValueError):
                return tag
        if not src:
            relative_src = image_path.relative_to(page.parent.resolve(), walk_up=True).as_posix()
            tag = set_attribute(tag, "src", relative_src)
            stats["missing_image_sources_restored"] += 1
        tag = set_attribute(tag, "width", str(width))
        tag = set_attribute(tag, "height", str(height))
        stats["images_dimensioned"] += 1
        return tag

    return IMG_TAG_RE.sub(replace, text)


def replace_meta_values(text: str, values: dict[tuple[str, str], str]) -> str:
    def replace(match: re.Match[str]) -> str:
        tag = match.group(0)
        for selector in ("name", "property"):
            key = (selector, (attribute(tag, selector) or "").lower())
            if key in values:
                return set_attribute(tag, "content", values[key])
        return tag

    return META_TAG_RE.sub(replace, text)


def first_under_limit(candidates: tuple[str, ...], limit: int = 60) -> str:
    for candidate in candidates:
        if len(candidate) <= limit:
            return candidate
    return candidates[-1]


def french_seo(service: str, price: str | None) -> tuple[str, str]:
    if price:
        title = first_under_limit(
            (
                f"{service} moins cher : dès {price} sur GamsGo",
                f"{service} dès {price} sur GamsGo",
                f"{service} {price} | GamsGo",
            )
        )
        description = (
            f"{service} sur GamsGo dès {price}. Prix relevé le 20 août 2026 : "
            "type d’accès, risques et code WPQTU à contrôler avant l’achat."
        )
    else:
        title = first_under_limit(
            (
                f"{service} sur GamsGo : prix et avis 2026",
                f"{service} sur GamsGo : notre avis",
                f"{service} | GamsGo",
            )
        )
        description = (
            f"{service} sur GamsGo avec prix à vérifier. Disponibilité, type d’accès, "
            "risques et code WPQTU à contrôler avant l’achat."
        )
    return title, description


def english_price(price: str) -> str:
    monthly = re.fullmatch(r"([0-9]+(?:,[0-9]+)?)\s*€/mois", price)
    if monthly:
        return f"€{monthly.group(1).replace(',', '.')}/month"
    single = re.fullmatch(r"([0-9]+(?:,[0-9]+)?)\s*€", price)
    if single:
        return f"€{single.group(1).replace(',', '.')}"
    return price.replace(",", ".").replace("€/mois", "€/month")


def english_seo(service: str, price: str | None) -> tuple[str, str]:
    if price:
        price_en = english_price(price)
        title = first_under_limit(
            (
                f"{service} on GamsGo from {price_en} (2026)",
                f"{service} from {price_en} on GamsGo",
                f"{service} {price_en} | GamsGo",
            )
        )
        description = (
            f"{service} on GamsGo from {price_en}. Price checked August 20, 2026: "
            "access type, risks and WPQTU code to verify before buying."
        )
    else:
        title = first_under_limit(
            (
                f"{service} on GamsGo: price and review (2026)",
                f"{service} on GamsGo: our review",
                f"{service} | GamsGo",
            )
        )
        description = (
            f"{service} on GamsGo with price to verify. Check availability, access type, "
            "risks and WPQTU code before buying."
        )
    return title, description


def update_head(text: str, title: str, description: str) -> str:
    text = re.sub(
        r"<title>.*?</title>",
        f"<title>{html.escape(title, quote=False)}</title>",
        text,
        count=1,
        flags=re.I | re.S,
    )
    return replace_meta_values(
        text,
        {
            ("name", "description"): description,
            ("property", "og:title"): title,
            ("property", "og:description"): description,
            ("name", "twitter:title"): title,
            ("name", "twitter:description"): description,
        },
    )


def update_title_only(text: str, title: str) -> str:
    text = re.sub(
        r"<title>.*?</title>",
        f"<title>{html.escape(title, quote=False)}</title>",
        text,
        count=1,
        flags=re.I | re.S,
    )
    return replace_meta_values(
        text,
        {
            ("property", "og:title"): title,
            ("name", "twitter:title"): title,
        },
    )
def related_block(offer: object, offers: list[object], english: bool) -> str:
    peers = sorted(
        (item for item in offers if item.category == offer.category and item.slug != offer.slug),
        key=lambda item: item.service.casefold(),
    )
    insertion = next(
        (index for index, item in enumerate(peers) if item.service.casefold() > offer.service.casefold()),
        len(peers),
    )
    choices = [peers[(insertion - 1) % len(peers)], peers[insertion % len(peers)]]
    if english:
        heading = "Compare similar GamsGo offers"
        links = "".join(
            f'<li><a href="{item.slug}.html">{html.escape(item.service)} on GamsGo: price and checks</a></li>'
            for item in choices
        )
        fixed = (
            '<li><a href="catalogue-gamsgo-complet-offres-code-wpqtu.html">Complete GamsGo catalogue and checked prices</a></li>'
            '<li><a href="gamsgo-avis-2026.html">GamsGo review 2026: reliability and risks</a></li>'
        )
    else:
        heading = "Comparer des offres similaires"
        links = "".join(
            f'<li><a href="{item.slug}.html">{html.escape(item.service)} sur GamsGo : prix et précautions</a></li>'
            for item in choices
        )
        fixed = (
            '<li><a href="catalogue-gamsgo-complet-offres-code-wpqtu.html">Catalogue GamsGo complet et prix relevés</a></li>'
            '<li><a href="gamsgo-avis-2026.html">Avis GamsGo 2026 : fiabilité et risques</a></li>'
        )
    return (
        f'{RELATED_START}\n<section class="related-guides" aria-labelledby="related-gamsgo">'
        f'<h2 id="related-gamsgo">{heading}</h2><ul>{links}{fixed}</ul></section>\n{RELATED_END}'
    )


def insert_related(text: str, block: str, english: bool) -> str:
    marker_pattern = re.compile(re.escape(RELATED_START) + r".*?" + re.escape(RELATED_END), re.S)
    if marker_pattern.search(text):
        return marker_pattern.sub(block, text, count=1)
    if english:
        heading = re.compile(r"(<h2>Frequently asked questions</h2>)", re.I)
    else:
        heading = re.compile(r"(<h2>Questions fréquentes</h2>)", re.I)
    return heading.sub(block + r"\n\1", text, count=1)


def optimize_gamsgo(stats: Counter[str]) -> set[str]:
    sys.path.insert(0, str(ROOT / "scripts"))
    from build_gamsgo_full_catalog import OFFERS  # noqa: PLC0415

    changed_urls: set[str] = set()
    for offer in OFFERS:
        french_path = ROOT / "articles" / f"{offer.slug}.html"
        if not french_path.is_file():
            continue
        french = french_path.read_text(encoding="utf-8")
        title_match = re.search(r"<title>Comment acheter (.+?)</title>", french, re.I | re.S)
        if not title_match:
            continue
        raw = html.unescape(title_match.group(1))
        price_match = re.match(rf"{re.escape(offer.service)} dès (.+?) sur GamsGo \? • EuroMalin$", raw)
        price = price_match.group(1) if price_match else None
        title_fr, description_fr = french_seo(offer.service, price)
        updated = update_head(french, title_fr, description_fr)
        updated = insert_related(updated, related_block(offer, OFFERS, False), False)
        if updated != french:
            french_path.write_text(updated, encoding="utf-8")
            stats["gamsgo_fr_pages_optimized"] += 1
            changed_urls.add(f"https://euromalin.com/articles/{offer.slug}.html")

        english_path = ROOT / "en" / "articles" / f"{offer.slug}.html"
        if not english_path.is_file():
            continue
        english = english_path.read_text(encoding="utf-8")
        title_en, description_en = english_seo(offer.service, price)
        updated = update_head(english, title_en, description_en)
        updated = insert_related(updated, related_block(offer, OFFERS, True), True)
        if offer.slug == "gamsgo-lovable-moins-cher":
            updated = updated.replace("Washable", "Lovable")
        if updated != english:
            english_path.write_text(updated, encoding="utf-8")
            stats["gamsgo_en_pages_optimized"] += 1
            changed_urls.add(f"https://euromalin.com/en/articles/{offer.slug}.html")
    return changed_urls


def fix_english_duplicate_title(stats: Counter[str]) -> set[str]:
    relative = "bons-plans/clinique-even-better-fond-de-teint-31e.html"
    path = ROOT / "en" / relative
    if not path.is_file():
        return set()
    original = path.read_text(encoding="utf-8")
    updated = update_head(
        original,
        "Clinique Even Better foundation SPF 50 at €31.89",
        "Clinique Even Better Clinical foundation SPF 50 at €31.89. Check current availability, price and cashback before ordering.",
    )
    if updated == original:
        return set()
    path.write_text(updated, encoding="utf-8")
    stats["duplicate_titles_fixed"] += 1
    return {f"https://euromalin.com/en/{relative}"}


def optimize_pillar_titles(stats: Counter[str]) -> set[str]:
    titles = {
        "articles/catalogue-gamsgo-complet-offres-code-wpqtu.html": "Catalogue GamsGo 2026 : offres, prix et code WPQTU",
        "en/articles/catalogue-gamsgo-complet-offres-code-wpqtu.html": "GamsGo catalogue 2026: offers, prices and code WPQTU",
        "articles/gamsgo-abonnements-moins-cher.html": "GamsGo 2026 : abonnements moins chers et code WPQTU",
        "articles/gamsgo-guide-abonnements-2026.html": "Guide GamsGo 2026 : abonnements et code WPQTU",
        "articles/gamsgo-ia-streaming-logiciels.html": "GamsGo 2026 : IA, streaming et logiciels",
        "articles/gamsgo-nouveautes-prix-2026.html": "Nouveautés GamsGo 2026 : services et prix",
        "en/articles/gamsgo-avis-2026.html": "GamsGo review 2026: prices, reliability and risks",
        "en/articles/u7buy-vs-gamsgo.html": "U7BUY vs GamsGo 2026: subscriptions and gaming",
    }
    changed_urls: set[str] = set()
    for relative, title in titles.items():
        path = ROOT / relative
        original = path.read_text(encoding="utf-8")
        updated = update_title_only(original, title)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            stats["pillar_titles_optimized"] += 1
        changed_urls.add(f"https://euromalin.com/{relative}")
    return changed_urls


def update_lastmod(urls: set[str]) -> None:
    path = ROOT / "sitemap.xml"
    text = path.read_text(encoding="utf-8")
    for url in urls:
        pattern = rf"(<loc>{re.escape(url)}</loc>\s*<lastmod>)[^<]+(</lastmod>)"
        text = re.sub(pattern, rf"\g<1>{TODAY}\g<2>", text, count=1)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    stats: Counter[str] = Counter()
    for path in sitemap_files():
        original = path.read_text(encoding="utf-8")
        updated = qualify_affiliate_links(original, stats)
        updated = add_image_dimensions(updated, path, stats)
        if path.is_relative_to(ROOT / "en"):
            updated = updated.replace('"message":"Ce site utilise des cookies."', '"message":"This site uses cookies."')
            updated = updated.replace('"link":"En savoir plus"', '"link":"Learn more"')
            if updated != original and "Ce site utilise des cookies." in original:
                stats["english_cookie_banners_translated"] += 1
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            stats["html_files_changed_for_hygiene"] += 1

    lastmod_urls = optimize_gamsgo(stats)
    lastmod_urls.update(fix_english_duplicate_title(stats))
    lastmod_urls.update(optimize_pillar_titles(stats))
    lastmod_urls.update(
        {
            "https://euromalin.com/a-propos.html",
            "https://euromalin.com/en/a-propos.html",
            "https://euromalin.com/calculateur.html",
            "https://euromalin.com/en/calculateur.html",
        }
    )
    update_lastmod(lastmod_urls)
    print(json.dumps(dict(sorted(stats.items())), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
