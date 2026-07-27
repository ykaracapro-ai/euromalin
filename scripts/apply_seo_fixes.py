#!/usr/bin/env python3
"""Apply reproducible on-page and internal-link SEO fixes to EuroMalin."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
FR_HTML = sorted(
    path
    for path in ROOT.rglob("*.html")
    if "en" not in path.relative_to(ROOT).parts
)

MANUAL_TITLES = {
    "articles.html": "Articles économies et bons plans 2026 • EuroMalin",
    "budget.html": "Budget personnel : méthodes et conseils • EuroMalin",
    "cashback.html": "Cashback 2026 : comparatifs et meilleurs sites • EuroMalin",
    "economies.html": "Économies : payer moins au quotidien • EuroMalin",
    "articles/u7buy-comptes-jeux.html": "Comptes de jeux U7BUY : guide et risques • EuroMalin",
}

IMAGE_RENAMES = {
    "assets/img/bons-plans/bose-soundlink-max.png": "assets/img/bons-plans/bose-soundlink-max.webp",
    "assets/img/bons-plans/papiers-air-fryer-cecotec.png": "assets/img/bons-plans/papiers-air-fryer-cecotec.webp",
    "assets/img/bons-plans/sac-cabine-hayayu.png": "assets/img/bons-plans/sac-cabine-hayayu.webp",
    "assets/img/bons-plans/legrand-greenup-access.png": "assets/img/bons-plans/legrand-greenup-access.webp",
    "assets/img/bons-plans/cuiseur-riz-russell-hobbs.png": "assets/img/bons-plans/cuiseur-riz-russell-hobbs.webp",
    "assets/img/bons-plans/bosch-tassimo-happy.png": "assets/img/bons-plans/bosch-tassimo-happy.webp",
    "assets/img/bons-plans/nespresso-vertuo-pop.png": "assets/img/bons-plans/nespresso-vertuo-pop.webp",
}

STATIC_IMAGE_RENAMES = {
    "assets/img/bons-plans/nordvpn-logo.png": "assets/img/bons-plans/nordvpn-illustration.svg",
}

STOP_WORDS = {
    "et", "de", "des", "les", "la", "le", "du", "à", "au", "aux",
    "avec", "pour", "sur", "en", "un", "une",
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_if_changed(path: Path, text: str) -> bool:
    old = read(path)
    if old == text:
        return False
    path.write_text(text, encoding="utf-8", newline="")
    return True


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def plain_text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", value))).strip()


def shorten_title(title: str) -> str:
    title = re.sub(r"\s+", " ", title).strip()
    if len(title) <= 65:
        return title
    base = re.sub(r"\s*[•|–-]\s*EuroMalin\s*$", "", title, flags=re.I)
    if len(base) > 65:
        candidate = base[:65]
        if " " in candidate:
            candidate = candidate.rsplit(" ", 1)[0]
        if candidate.count("(") > candidate.count(")"):
            candidate = candidate.rsplit("(", 1)[0].rstrip()
        words = candidate.rstrip(" :–—-|,").split()
        while words and words[-1].lower().strip("’'") in STOP_WORDS:
            words.pop()
        base = " ".join(words).rstrip(" :–—-|,")
    suffix = " • EuroMalin"
    if len(base) < 50 and len(base) + len(suffix) <= 65:
        base += suffix
    return base[:65].rstrip(" :–—-|,")


def normalize_description(description: str) -> str:
    description = re.sub(r"\s+", " ", html.unescape(description)).strip()
    if len(description) < 105:
        addition = (
            " Vérifiez les critères, les limites et nos conseils pratiques "
            "avant de choisir ou d’acheter."
        )
        description += addition
    if len(description) > 180:
        candidate = description[:177]
        if " " in candidate:
            candidate = candidate.rsplit(" ", 1)[0]
        description = candidate.rstrip(" ,;:") + "."
    description = re.sub(
        r"\b(?:avant de|avant|avec|pour|sur|de|des|du|et|à)\.$",
        "avant votre choix.",
        description,
        flags=re.I,
    )
    if len(description) > 180:
        candidate = description[:177]
        if " " in candidate:
            candidate = candidate.rsplit(" ", 1)[0]
        description = candidate.rstrip(" ,;:") + "."
    return description


def replace_meta(text: str, key: str, value: str, attr: str = "name") -> str:
    pattern = re.compile(
        rf'(<meta\s+{attr}="{re.escape(key)}"\s+content=")([^"]*)(")',
        flags=re.I,
    )
    return pattern.sub(lambda match: match.group(1) + html.escape(value, quote=True) + match.group(3), text)


def fix_page_metadata(path: Path, text: str) -> str:
    if path.name == "404.html":
        return text
    title_match = re.search(r"<title>(.*?)</title>", text, flags=re.I | re.S)
    if title_match:
        title = MANUAL_TITLES.get(relative(path), shorten_title(plain_text(title_match.group(1))))
        text = text[:title_match.start(1)] + html.escape(title) + text[title_match.end(1):]
        social_title = re.sub(r"\s*•\s*EuroMalin$", "", title)
        text = replace_meta(text, "og:title", social_title, "property")
        text = replace_meta(text, "twitter:title", social_title)

    desc_match = re.search(
        r'<meta\s+name="description"\s+content="([^"]*)"', text, flags=re.I
    )
    if desc_match:
        description = normalize_description(desc_match.group(1))
        text = (
            text[:desc_match.start(1)]
            + html.escape(description, quote=True)
            + text[desc_match.end(1):]
        )
        text = replace_meta(text, "og:description", description, "property")
        text = replace_meta(text, "twitter:description", description)
    return text


def fix_known_links(path: Path, text: str) -> str:
    rel = relative(path)
    if "/" in rel:
        text = text.replace('src="../../assets/tracking.js"', 'src="../assets/tracking.js"')
    else:
        text = text.replace('src="../assets/tracking.js"', 'src="assets/tracking.js"')
    if rel.startswith(("articles/", "bons-plans/")):
        text = text.replace('href="a-propos.html"', 'href="../a-propos.html"')
    if rel == "articles/erreurs-budget.html":
        text = text.replace(
            'href="articles/gagnez-5-euros-en-vous-inscrivant.html"',
            'href="gagnez-5-euros-en-vous-inscrivant.html"',
        )
    if rel == "bons-plans.html":
        text = text.replace('href="../articles/', 'href="articles/')
    return text


def deduplicate_canonical(text: str) -> str:
    pattern = re.compile(r'<link\s+rel="canonical"\s+href="[^"]+"\s*/?>', flags=re.I)
    matches = list(pattern.finditer(text))
    if len(matches) <= 1:
        return text
    for match in reversed(matches[1:]):
        text = text[:match.start()] + text[match.end():]
    return text


def add_breadcrumb_schema(path: Path, text: str) -> str:
    rel = relative(path)
    if not rel.startswith(("articles/", "bons-plans/")) or path.name == "_template.html":
        return text
    if '"@type":"BreadcrumbList"' in text or '"@type": "BreadcrumbList"' in text:
        return text
    canonical = re.search(r'<link\s+rel="canonical"\s+href="([^"]+)"', text, flags=re.I)
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", text, flags=re.I | re.S)
    if not canonical or not h1:
        return text
    section_name = "Articles" if rel.startswith("articles/") else "Bons plans"
    section_url = (
        "https://euromalin.com/articles.html"
        if rel.startswith("articles/")
        else "https://euromalin.com/bons-plans.html"
    )
    payload = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": 1,
                "name": "Accueil",
                "item": "https://euromalin.com/",
            },
            {
                "@type": "ListItem",
                "position": 2,
                "name": section_name,
                "item": section_url,
            },
            {
                "@type": "ListItem",
                "position": 3,
                "name": plain_text(h1.group(1)),
                "item": html.unescape(canonical.group(1)),
            },
        ],
    }
    schema = (
        '\n<script type="application/ld+json">'
        + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        + "</script>\n"
    )
    return text.replace("</head>", schema + "</head>", 1)


def improve_homepage_structure(text: str) -> str:
    if "<!-- HERO -->" in text and "<main" not in text:
        text = text.replace("<!-- HERO -->", '<main id="main">\n<!-- HERO -->', 1)
        text = text.replace("<footer", "</main>\n<footer", 1)
    marker = "<!-- SEO-SITE-IDENTITY -->"
    if marker not in text:
        schemas = [
            {
                "@context": "https://schema.org",
                "@type": "Organization",
                "@id": "https://euromalin.com/#organization",
                "name": "EuroMalin",
                "url": "https://euromalin.com/",
                "logo": "https://euromalin.com/assets/favicon.svg",
            },
            {
                "@context": "https://schema.org",
                "@type": "WebSite",
                "@id": "https://euromalin.com/#website",
                "url": "https://euromalin.com/",
                "name": "EuroMalin",
                "inLanguage": "fr-FR",
                "publisher": {"@id": "https://euromalin.com/#organization"},
            },
        ]
        block = marker + "\n" + "\n".join(
            '<script type="application/ld+json">'
            + json.dumps(schema, ensure_ascii=False, separators=(",", ":"))
            + "</script>"
            for schema in schemas
        ) + "\n"
        text = text.replace("</head>", block + "</head>", 1)
    return text


def noindex_technical_page(text: str) -> str:
    if re.search(r'<meta\s+name="robots"', text, flags=re.I):
        return text
    return text.replace(
        "</head>",
        '<meta name="robots" content="noindex, nofollow, noarchive"/>\n</head>',
        1,
    )


def fix_affiliate_claims(text: str) -> str:
    text = text.replace(
        "GamsGo achète des comptes premium ou des plans familiaux légitimes auprès des éditeurs. "
        "La société répartit ensuite les places disponibles entre utilisateurs vérifiés. "
        "Vous recevez vos identifiants <strong>en moins de 5 minutes</strong>, prêts à utiliser. "
        "Le compte est <strong>dédié</strong> : vous n'interférez avec personne, vos préférences restent privées.",
        "Selon l’offre, la livraison peut prendre la forme d’un compte, d’une invitation ou d’un autre "
        "type d’accès. Vérifiez avant l’achat le mode de livraison, le contrôle du compte et sa conformité "
        "aux conditions du fournisseur. Le délai dépend de l’offre et du traitement de la commande.",
    )
    text = text.replace(
        "quand l'abonnement partagé légal existe ?",
        "quand une offre à prix réduit est disponible ?",
    )
    text = text.replace(
        "un abonnement partagé légal, avec un compte personnel sécurisé,",
        "un accès à prix réduit, dont le type et les conditions doivent être vérifiés avant l’achat,",
    )
    text = re.sub(
        r"Et c'est totalement légal, contrairement aux comptes piratés qu'on voit traîner sur certains sites douteux\.",
        "La conformité dépend du type d’accès livré et des conditions d’utilisation du fournisseur.",
        text,
    )
    text = text.replace(
        "<strong>Garantie :</strong> remplacement instantané si le compte ne fonctionne plus",
        "<strong>Garantie :</strong> remplacement selon les conditions et les délais indiqués par le vendeur",
    )
    text = text.replace(
        "<strong>Recevez vos identifiants par e-mail</strong> en moins de 5 minutes, prêts à utiliser",
        "<strong>Suivez les instructions de livraison</strong> et testez l’accès dès sa réception",
    )
    text = re.sub(
        r'"text":"Instantané\. Vos identifiants [^"]+? arrivent par e-mail en moins de 5 minutes '
        r'après le paiement\. Vous pouvez vous connecter immédiatement\."',
        '"text":"Le délai et le mode de livraison dépendent de l’offre. '
        'Vérifiez les indications affichées avant le paiement."',
        text,
    )
    return text


def extract_title_and_description(path: Path) -> tuple[str, str]:
    text = read(path)
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", text, flags=re.I | re.S)
    title = plain_text(h1.group(1)) if h1 else path.stem.replace("-", " ").title()
    desc = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', text, flags=re.I)
    description = plain_text(desc.group(1)) if desc else "Consultez le détail de ce bon plan."
    if len(description) > 155:
        description = description[:152].rsplit(" ", 1)[0] + "…"
    return title, description


def add_bons_plans_archive(text: str) -> str:
    start = "<!-- SEO-ARCHIVE:START -->"
    end = "<!-- SEO-ARCHIVE:END -->"
    text = re.sub(
        rf"\s*{re.escape(start)}.*?{re.escape(end)}\s*",
        "\n",
        text,
        flags=re.S,
    )
    linked = set(re.findall(r'href="(bons-plans/[^"#?]+\.html)"', text))
    cards = []
    for path in sorted((ROOT / "bons-plans").glob("*.html")):
        if path.name == "_template.html":
            continue
        href = f"bons-plans/{path.name}"
        if href in linked:
            continue
        title, description = extract_title_and_description(path)
        cards.append(
            '<article class="article-card" data-article-card>'
            '<div class="category-pill">Archive bons plans</div>'
            f'<h3><a href="{html.escape(href)}">{html.escape(title)}</a></h3>'
            f"<p>{html.escape(description)}</p>"
            f'<a class="read-more" href="{html.escape(href)}">Voir la fiche →</a>'
            "</article>"
        )
    if not cards:
        return text
    block = (
        f"\n{start}\n"
        '<section class="section"><div class="container">'
        '<div class="section-head"><div><div class="kicker">Toutes les fiches</div>'
        '<h2>Archives des bons plans</h2>'
        "<p>Retrouvez toutes les offres publiées. Les prix et disponibilités peuvent évoluer : "
        "vérifiez toujours la fiche du marchand avant l’achat.</p></div></div>"
        '<div class="grid-3">'
        + "\n".join(cards)
        + "</div></div></section>\n"
        f"{end}\n"
    )
    return text.replace("</main>", block + "</main>", 1)


def add_orphan_article_link(text: str) -> str:
    marker = "<!-- SEO-ORPHAN-LINK -->"
    if marker in text or "gagnez-7-euros-en-vous-inscrivant.html" in text:
        return text
    block = (
        f"\n{marker}\n"
        '<section class="section"><div class="container"><div class="grid-3">'
        '<article class="article-card" data-article-card>'
        '<div class="category-pill">Cashback</div>'
        '<h3><a href="articles/gagnez-7-euros-en-vous-inscrivant.html">'
        "Comment gagner 7 € dès l’inscription</a></h3>"
        "<p>Conditions, étapes et points à vérifier avant de profiter de cette offre de bienvenue.</p>"
        '<a class="read-more" href="articles/gagnez-7-euros-en-vous-inscrivant.html">'
        "Lire l’article →</a></article></div></div></section>\n"
    )
    return text.replace("</main>", block + "</main>", 1)


def convert_large_images() -> None:
    for old_rel, new_rel in IMAGE_RENAMES.items():
        old_path = ROOT / old_rel
        new_path = ROOT / new_rel
        if old_path.exists():
            with Image.open(old_path) as image:
                image.save(new_path, "WEBP", quality=82, method=6)
    for rel in (
        "assets/img/articles/courses-moins-cheres.jpg",
        "assets/img/articles/payer-midjourney-moins-cher.jpg",
    ):
        path = ROOT / rel
        if path.exists():
            with Image.open(path) as image:
                rgb = image.convert("RGB")
                rgb.save(path, "JPEG", quality=82, optimize=True, progressive=True)


def replace_image_references(text: str) -> str:
    for old, new in {**IMAGE_RENAMES, **STATIC_IMAGE_RENAMES}.items():
        text = text.replace(old, new)
        text = text.replace(Path(old).name, Path(new).name)
    return text


def add_image_dimensions(path: Path, text: str) -> str:
    def amend(match: re.Match[str]) -> str:
        tag = match.group(0)
        if re.search(r"\bwidth\s*=", tag, flags=re.I) and re.search(
            r"\bheight\s*=", tag, flags=re.I
        ):
            return tag
        src_match = re.search(r'\bsrc="([^"]+)"', tag, flags=re.I)
        if not src_match:
            return tag
        src = src_match.group(1).split("?", 1)[0]
        if src.startswith(("http://", "https://", "data:")):
            return tag
        image_path = (path.parent / src).resolve()
        try:
            image_path.relative_to(ROOT.resolve())
        except ValueError:
            return tag
        if not image_path.exists():
            return tag
        try:
            with Image.open(image_path) as image:
                width, height = image.size
        except OSError:
            if image_path.suffix.lower() != ".svg":
                return tag
            svg_head = image_path.read_text(encoding="utf-8")[:500]
            width_match = re.search(r'\bwidth="(\d+)"', svg_head)
            height_match = re.search(r'\bheight="(\d+)"', svg_head)
            if not width_match or not height_match:
                return tag
            width, height = int(width_match.group(1)), int(height_match.group(1))
        attrs = ""
        if not re.search(r"\bwidth\s*=", tag, flags=re.I):
            attrs += f' width="{width}"'
        if not re.search(r"\bheight\s*=", tag, flags=re.I):
            attrs += f' height="{height}"'
        return re.sub(r"\s*/?>$", lambda ending: attrs + ending.group(0), tag)

    return re.sub(r"<img\b[^>]*>", amend, text, flags=re.I)


def main() -> None:
    robots = ROOT / "robots.txt"
    if robots.exists():
        write_if_changed(robots, read(robots).replace("Disallow: /assets/\n", ""))

    convert_large_images()
    changed = 0
    for path in FR_HTML:
        text = read(path)
        text = replace_image_references(text)
        text = fix_known_links(path, text)
        text = deduplicate_canonical(text)
        text = fix_affiliate_claims(text)
        text = fix_page_metadata(path, text)
        text = add_breadcrumb_schema(path, text)
        if relative(path) == "index.html":
            text = improve_homepage_structure(text)
        if relative(path) in {"bons-plans/_template.html", "assets/analytics.html"}:
            text = noindex_technical_page(text)
        text = text.replace('"dateModified":"2026-07-24"', '"dateModified":"2026-07-27"')
        text = text.replace('"dateModified": "2026-07-24"', '"dateModified": "2026-07-27"')
        if relative(path) == "bons-plans.html":
            text = add_bons_plans_archive(text)
        if relative(path) == "articles.html":
            text = add_orphan_article_link(text)
        text = add_image_dimensions(path, text)
        changed += write_if_changed(path, text)

    print(f"SEO fixes applied; {changed} French HTML files updated.")
    for old_rel, new_rel in IMAGE_RENAMES.items():
        old_path = ROOT / old_rel
        if old_path.exists() and (ROOT / new_rel).exists():
            old_path.unlink()
    for old_rel, new_rel in STATIC_IMAGE_RENAMES.items():
        old_path = ROOT / old_rel
        if old_path.exists() and (ROOT / new_rel).exists():
            old_path.unlink()


if __name__ == "__main__":
    main()
