#!/usr/bin/env python3
"""
Add Unsplash hero photos to every article on euromalin.

Usage:
    UNSPLASH_KEY=xxxxxxxx python3 scripts/add_unsplash_photos.py [--force] [--dry-run]

For each HTML file in articles/, this script:
  1. extracts the page title and a few keywords from the URL slug
  2. queries the Unsplash Search API
  3. downloads the best landscape photo into assets/img/articles/<slug>.jpg
  4. inserts an <img class="article-hero-image"> at the top of the article body
     (idempotent: skips files that already have an .article-hero-image, unless --force)

Requires only the Python standard library. No external dependencies.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARTICLES_DIR = ROOT / "articles"
IMG_DIR = ROOT / "assets" / "img" / "articles"
IMG_DIR.mkdir(parents=True, exist_ok=True)

API_URL = "https://api.unsplash.com/search/photos"
USER_AGENT = "EuroMalinBot/1.0 (+https://euromalin.com)"

# Per-slug keyword overrides — preserves topical accuracy when the title is too abstract.
KEYWORD_OVERRIDES: dict[str, str] = {
    "cashback-cest-quoi": "shopping receipt money",
    "meilleurs-sites-cashback": "online shopping savings",
    "igraal-ou-ebuyclub": "online shopping comparison",
    "widilo-poulpeo-topcashback": "ecommerce shopping",
    "meilleur-cashback-nike": "running shoes sport",
    "meilleur-cashback-amazon": "ecommerce package",
    "meilleur-cashback-booking": "travel hotel suitcase",
    "cashback-aliexpress-shein-temu": "ecommerce delivery boxes",
    "cashback-courses-alimentaires-drive": "grocery shopping cart",
    "cashback-crypto-plutus-binance": "cryptocurrency bitcoin",
    "cashback-voyages-booking-hotels": "hotel lobby travel",
    "forfait-mobile-comparatif-cashback": "smartphone hand mobile",
    "prixtel-cashback-2026": "smartphone signal",
    "gamsgo-abonnements-moins-cher": "streaming netflix tv",
    "gamsgo-avis-2026": "subscription streaming",
    "payer-netflix-spotify-youtube-moins-cher": "streaming subscription",
    "abonnements-inutiles": "subscriptions cancel",
    "economiser-1500-euros-en-39-jours": "saving money piggy bank",
    "economiser-200-euros-par-mois": "wallet euros saving",
    "economiser-voyages-2026": "travel airplane window",
    "courses-moins-cheres": "supermarket aisle groceries",
    "reduire-facture-electricite": "electricity bulb energy",
    "methode-des-enveloppes": "envelopes cash",
    "erreurs-budget": "budget planner desk",
    "gerer-budget-intelligent": "budget spreadsheet finance",
    "banques-en-ligne-primes": "online banking card",
    "meilleures-apps-gagner-argent": "smartphone earning apps",
    "arrondir-ses-fins-de-mois": "side hustle laptop",
    "gagner-argent-en-marchant": "walking sneakers city",
    "gagnez-5-euros-en-vous-inscrivant": "wallet euros bonus",
    "gagnez-7-euros-en-vous-inscrivant": "wallet euros bonus",
    "meilleurs-bons-plans-du-mois": "deals shopping bags",
    "french-week-amazon-mai-2026": "shopping sale tags",
    "guide-achat-aspirateur-balai": "vacuum cleaner home",
    "guide-achat-beaute-cosmetique": "cosmetics beauty",
    "guide-achat-cuisine-electromenager": "kitchen appliances",
    "guide-achat-ecouteurs-sans-fil": "wireless earbuds",
    "guide-achat-machine-cafe-2026": "coffee machine espresso",
    "guide-vpn-2026": "vpn security laptop",
    "quel-air-fryer-choisir": "air fryer kitchen",
    "mexc-bonus-bienvenue-crypto": "cryptocurrency wallet",
}


def extract_title(html: str) -> str:
    m = re.search(r"<title>([^<]+)</title>", html, re.I | re.S)
    return (m.group(1) if m else "").split("•")[0].strip()


def keywords_for(slug: str, title: str) -> str:
    if slug in KEYWORD_OVERRIDES:
        return KEYWORD_OVERRIDES[slug]
    # Fallback: derive from slug
    raw = slug.replace("-", " ")
    raw = re.sub(r"\b(20\d{2}|cest|le|la|les|de|du|des|en|et|ou|pour|sans|sur|avec|comment|que|qui|le)\b", "", raw)
    raw = re.sub(r"\s+", " ", raw).strip()
    return raw or "finance money"


def http_get_json(url: str, headers: dict) -> dict:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def http_download(url: str, dest: Path, headers: dict) -> int:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
    dest.write_bytes(data)
    return len(data)


def search_unsplash(query: str, access_key: str) -> dict | None:
    params = urllib.parse.urlencode({
        "query": query,
        "orientation": "landscape",
        "per_page": 5,
        "content_filter": "high",
    })
    headers = {
        "Authorization": f"Client-ID {access_key}",
        "Accept-Version": "v1",
        "User-Agent": USER_AGENT,
    }
    try:
        data = http_get_json(f"{API_URL}?{params}", headers)
    except Exception as e:
        print(f"  ! search failed: {e}", file=sys.stderr)
        return None
    results = data.get("results") or []
    if not results:
        return None
    return results[0]


def trigger_download_event(download_location: str, access_key: str) -> None:
    """Per Unsplash API guidelines, ping the download endpoint to credit usage."""
    headers = {
        "Authorization": f"Client-ID {access_key}",
        "Accept-Version": "v1",
        "User-Agent": USER_AGENT,
    }
    try:
        http_get_json(download_location, headers)
    except Exception:
        pass


def inject_hero_image(html: str, slug: str, photo: dict) -> str | None:
    """Insert <img class="article-hero-image"> at the start of the article body."""
    img_url = f"assets/img/articles/{slug}.jpg"
    rel_prefix = "../"  # we operate from articles/ subdir
    alt = (photo.get("alt_description") or photo.get("description") or slug).strip()[:140]
    credit_name = (photo.get("user") or {}).get("name") or "Unsplash"
    credit_url = (photo.get("user") or {}).get("links", {}).get("html") or "https://unsplash.com"
    photo_url = (photo.get("links") or {}).get("html") or "https://unsplash.com"

    img_tag = (
        f'<figure class="article-hero">'
        f'<img class="article-hero-image" src="{rel_prefix}{img_url}" '
        f'alt="{html_escape_attr(alt)}" loading="lazy" decoding="async" '
        f'width="1200" height="675"/>'
        f'<figcaption class="article-hero-credit">'
        f'Photo : <a href="{photo_url}?utm_source=euromalin&utm_medium=referral" rel="nofollow noopener">'
        f'{html_escape(credit_name)}</a> sur '
        f'<a href="https://unsplash.com?utm_source=euromalin&utm_medium=referral" rel="nofollow noopener">Unsplash</a>'
        f'</figcaption>'
        f'</figure>'
    )

    # Insert just after the opening <article ...> tag (best match) or
    # otherwise right after the article hero card (.intro paragraph location).
    pattern_article = re.compile(r'(<article\b[^>]*>)', re.I)
    m = pattern_article.search(html)
    if m:
        return html[:m.end()] + img_tag + html[m.end():]
    # Fallback: insert after the breadcrumb/hero card opening
    pattern_hero = re.compile(r'(<div class="hero-card">)', re.I)
    m = pattern_hero.search(html)
    if m:
        return html[:m.end()] + img_tag + html[m.end():]
    return None


def html_escape(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def html_escape_attr(s: str) -> str:
    return html_escape(s).replace('"', "&quot;")


def process_article(path: Path, access_key: str, force: bool, dry_run: bool) -> bool:
    slug = path.stem
    html = path.read_text(encoding="utf-8")
    if "article-hero-image" in html and not force:
        print(f"= {slug}: already has hero image (skip; --force to overwrite)")
        return False

    title = extract_title(html)
    query = keywords_for(slug, title)
    print(f"→ {slug}: query='{query}'")

    if dry_run:
        return False

    photo = search_unsplash(query, access_key)
    if not photo:
        print(f"  ! no photo for '{query}'")
        return False
    urls = photo.get("urls") or {}
    img_url = urls.get("regular") or urls.get("small") or urls.get("full")
    if not img_url:
        print("  ! no usable URL in response")
        return False

    dest = IMG_DIR / f"{slug}.jpg"
    try:
        size = http_download(img_url, dest, {"User-Agent": USER_AGENT})
    except Exception as e:
        print(f"  ! download failed: {e}", file=sys.stderr)
        return False
    print(f"  ↓ {size//1024}KB → {dest.relative_to(ROOT)}")

    # Credit the download per Unsplash terms
    dl_loc = (photo.get("links") or {}).get("download_location")
    if dl_loc:
        trigger_download_event(dl_loc, access_key)

    new_html = inject_hero_image(html, slug, photo)
    if not new_html:
        print("  ! could not find insertion point in HTML")
        return False
    if force and "article-hero-image" in html:
        # Strip existing hero image first
        new_html = re.sub(
            r'<figure class="article-hero">.*?</figure>',
            '', new_html, count=1, flags=re.S,
        )
        # Re-inject
        new_html = inject_hero_image(new_html, slug, photo) or new_html

    path.write_text(new_html, encoding="utf-8")
    print(f"  ✓ injected hero image")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description="Add Unsplash hero photos to all articles")
    ap.add_argument("--force", action="store_true", help="Overwrite existing hero images")
    ap.add_argument("--dry-run", action="store_true", help="Print plan without downloading")
    ap.add_argument("--only", help="Process only this slug")
    args = ap.parse_args()

    access_key = os.environ.get("UNSPLASH_KEY") or os.environ.get("UNSPLASH_ACCESS_KEY")
    if not args.dry_run and not access_key:
        print("error: set UNSPLASH_KEY=<your-access-key> in the environment", file=sys.stderr)
        return 2

    files = sorted(ARTICLES_DIR.glob("*.html"))
    if args.only:
        files = [f for f in files if f.stem == args.only]
        if not files:
            print(f"no article matches slug '{args.only}'", file=sys.stderr)
            return 1
    print(f"Processing {len(files)} articles…")

    changed = 0
    for i, path in enumerate(files, 1):
        try:
            if process_article(path, access_key or "", args.force, args.dry_run):
                changed += 1
        except KeyboardInterrupt:
            print("interrupted", file=sys.stderr)
            return 130
        # Gentle pace to respect rate limit (50/h dev mode)
        if not args.dry_run and i < len(files):
            time.sleep(1.2)

    print(f"\nDone — {changed} article(s) updated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
