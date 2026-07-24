#!/usr/bin/env python3
"""Build a static, indexable English mirror of EuroMalin under /en/."""

from __future__ import annotations

import html
import json
import os
import posixpath
import re
import time
from pathlib import Path, PurePosixPath
from typing import Any, Iterable
from urllib.parse import unquote, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup, Comment, Doctype, NavigableString


ROOT = Path(__file__).resolve().parents[1]
EN_ROOT = ROOT / "en"
CACHE_PATH = ROOT / "scripts" / "translation_cache_fr_en.json"
SITE_URL = "https://euromalin.com"
BUILD_DATE = "2026-07-24"
TRANSLATE_ENDPOINT = "https://translate.googleapis.com/translate_a/single"
MAX_BATCH_CHARS = 4_200
MAX_RETRY_BATCH_CHARS = 850

SKIP_TEXT_PARENTS = {"script", "style", "code", "pre", "kbd", "samp", "svg"}
TRANSLATABLE_ATTRIBUTES = {"alt", "aria-label", "placeholder", "title"}
TRANSLATABLE_JSON_KEYS = {
    "name",
    "headline",
    "description",
    "text",
    "articleSection",
    "keywords",
}
META_SELECTORS = (
    ("name", {"description", "keywords", "twitter:title", "twitter:description"}),
    ("property", {"og:title", "og:description"}),
)
STATIC_SCRIPT_TRANSLATIONS = {
    "Ce site utilise des cookies pour améliorer ton expérience et mesurer l'audience.": (
        "This site uses cookies to improve your experience and measure its audience."
    ),
    "OK, j'accepte": "OK, I agree",
    "En savoir plus": "Learn more",
}
MANUAL_TRANSLATIONS = {
    "EuroMalin — le site qui te rend ton argent": (
        "EuroMalin — the site that puts money back in your pocket"
    ),
    "EuroMalin — le site qui te rend ton argent • EuroMalin": (
        "EuroMalin — the site that puts money back in your pocket • EuroMalin"
    ),
    (
        "Cashback, astuces, comparatifs. EuroMalin te file les bons plans pour "
        "payer moins et récupérer de l'argent tous les mois."
    ): (
        "Cashback, money-saving tips and comparisons. EuroMalin helps you pay "
        "less and get money back every month."
    ),
    "Comment payer ses abonnements moins cher avec GamsGo en 2026 ?": (
        "How to pay less for your subscriptions with GamsGo in 2026"
    ),
    "Comment payer ses abonnements moins cher avec GamsGo en 2026 ? • EuroMalin": (
        "How to pay less for subscriptions with GamsGo in 2026 • EuroMalin"
    ),
    (
        "Guide GamsGo 2026 pour payer moins cher streaming, IA et logiciels : "
        "prix datés, méthodes d’accès, code WPQTU, DealShield et checklist avant commande."
    ): (
        "2026 GamsGo guide to cheaper streaming, AI and software: dated prices, "
        "access methods, WPQTU code, DealShield and a pre-order checklist."
    ),
    "IA": "AI",
    "Bons plans": "Deals",
    "Bons Plans EuroMalin": "EuroMalin Deals",
    (
        "50% besoins, 30% envies, 20% épargne — c'est la base. Mais si ton loyer "
        "bouffe 40% de ton salaire, cette règle ne tient pas."
    ): (
        "50% needs, 30% wants, 20% savings — that is the baseline. But if rent "
        "eats up 40% of your income, the rule no longer works."
    ),
    ": marcher 30 minutes par jour est plus rentable que de longues marches irrégulières.": (
        ": walking 30 minutes a day pays better than long, irregular walks."
    ),
    (
        "Crunchyroll est proposé directement et dans la marketplace GamsGo ; "
        "la page directe affichait 3,13 $ par mois."
    ): (
        "Crunchyroll is offered both directly and through the GamsGo marketplace; "
        "the direct page showed $3.13 per month."
    ),
    (
        "Echo Spot nouvelle génération à 59,99€ au lieu de 94,99€ sur Amazon. "
        "Réveil connecté avec écran, Alexa, son riche."
    ): (
        "The latest Echo Spot costs €59.99 instead of €94.99 on Amazon. It is a "
        "connected alarm clock with a screen, Alexa and rich sound."
    ),
    "Est-ce que mon compte officiel actuel sera affecté ?": (
        "Will my current official account be affected?"
    ),
    (
        "Fais tes courses en drive une fois par semaine au lieu d'aller en magasin. "
        "Pourquoi ?"
    ): "Shop for groceries online once a week instead of going to the store. Why?",
    (
        "Il répond à 5 questions : combien j'ai, combien je dépense, où je dépense, "
        "ce qui est obligatoire, ce qui me rapproche de mes objectifs."
    ): (
        "It answers five questions: how much I have, how much I spend, where I "
        "spend it, what is essential, and what moves me closer to my goals."
    ),
    (
        "Le compte peut être administré par un tiers. Ne lui confiez aucun "
        "connecteur, document ou secret professionnel avant d’avoir vérifié qui "
        "contrôle l’e-mail de récupération."
    ): (
        "The account may be administered by a third party. Do not give it access "
        "to any connector, document or professional secret until you have verified "
        "who controls the recovery email."
    ),
}
FRENCH_MARKERS = re.compile(
    r"(?i)\b(?:"
    r"accueil|achat|acheter|abonnement|abonnements|argent|"
    r"astuce|astuces|avec|avis|bons|cher|choisir|"
    r"comparatif|conseil|conseils|des|du|economiser|economie|economies|"
    r"gagner|les|"
    r"meilleur|meilleurs|moins|nouveau|nouveaux|offre|offres|payer|"
    r"pour|prix|reduction|reductions|une|votre|vos|vous|cette|cet|ces|"
    r"dans|est|sont|sur|que|qui|quoi|sans|peut|avant|apres|puis|aussi"
    r")\b"
)


def public_paths() -> list[Path]:
    paths = list(ROOT.glob("*.html"))
    paths += list((ROOT / "articles").glob("*.html"))
    paths += list((ROOT / "bons-plans").glob("*.html"))
    return sorted(path for path in paths if not path.name.startswith("_"))


def source_rel(path: Path) -> PurePosixPath:
    return PurePosixPath(path.relative_to(ROOT).as_posix())


def french_url(rel: PurePosixPath) -> str:
    if rel == PurePosixPath("index.html"):
        return f"{SITE_URL}/"
    return f"{SITE_URL}/{rel.as_posix()}"


def english_url(rel: PurePosixPath) -> str:
    if rel == PurePosixPath("index.html"):
        return f"{SITE_URL}/en/"
    return f"{SITE_URL}/en/{rel.as_posix()}"


def english_path_fragment(rel: PurePosixPath) -> str:
    if rel == PurePosixPath("index.html"):
        return "/en/"
    return f"/en/{rel.as_posix()}"


def french_path_fragment(rel: PurePosixPath) -> str:
    if rel == PurePosixPath("index.html"):
        return "/"
    return f"/{rel.as_posix()}"


def ensure_french_bilingual_metadata(path: Path) -> None:
    rel = source_rel(path)
    source = path.read_text(encoding="utf-8")
    source = re.sub(
        r"\n?\s*<!-- euromalin-bilingual:begin -->.*?"
        r"<!-- euromalin-bilingual:end -->\s*\n?",
        "\n",
        source,
        flags=re.DOTALL,
    )
    source = re.sub(
        r"\s*<a\b[^>]*class=[\"'][^\"']*\blanguage-switcher\b[^\"']*[\"']"
        r"[^>]*>.*?</a>",
        "",
        source,
        flags=re.DOTALL | re.IGNORECASE,
    )
    source = re.sub(
        r'(<link\s+rel="canonical"\s+href=")[^"]*(")',
        rf"\g<1>{french_url(rel)}\2",
        source,
        count=1,
    )
    source = re.sub(
        r'(<meta\s+property="og:url"\s+content=")[^"]*(")',
        rf"\g<1>{french_url(rel)}\2",
        source,
        count=1,
    )

    alternates = (
        "\n  <!-- euromalin-bilingual:begin -->\n"
        f'  <link rel="alternate" hreflang="fr" href="{french_url(rel)}" />\n'
        f'  <link rel="alternate" hreflang="en" href="{english_url(rel)}" />\n'
        f'  <link rel="alternate" hreflang="x-default" href="{french_url(rel)}" />\n'
        "  <!-- euromalin-bilingual:end -->\n"
    )
    source = source.replace("</head>", f"{alternates}</head>", 1)

    switcher = (
        f'\n      <a class="language-switcher" href="{english_path_fragment(rel)}" '
        'lang="en" hreflang="en" aria-label="Read this page in English">EN</a>\n'
    )
    source = source.replace("</nav>", f"{switcher}    </nav>", 1)
    source = re.sub(r"[ \t]+(?=\n|$)", "", source)
    path.write_text(source, encoding="utf-8", newline="\n")


def load_cache() -> dict[str, str]:
    if not CACHE_PATH.exists():
        return {}
    try:
        data = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return {str(key): str(value) for key, value in data.items()}


def save_cache(cache: dict[str, str]) -> None:
    CACHE_PATH.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def normalized_text(value: str) -> str:
    return value.strip()


def should_translate(value: str) -> bool:
    value = normalized_text(value)
    if not value or len(value) == 1:
        return False
    if value.startswith(("http://", "https://", "mailto:", "tel:", "data:")):
        return False
    if re.fullmatch(r"[\W\d_]+", value, flags=re.UNICODE):
        return False
    if re.fullmatch(r"[A-Z0-9_./+\-]{2,}", value):
        return False
    return True


def translated_response(session: requests.Session, text: str) -> str:
    params = {"client": "gtx", "sl": "fr", "tl": "en", "dt": "t"}
    last_error: Exception | None = None
    for attempt in range(5):
        try:
            response = session.post(
                TRANSLATE_ENDPOINT,
                params=params,
                data={"q": text},
                timeout=45,
            )
            response.raise_for_status()
            data = response.json()
            translated = "".join(part[0] for part in data[0] if part and part[0])
            if translated:
                return translated
            raise RuntimeError("empty translation response")
        except (requests.RequestException, ValueError, RuntimeError) as exc:
            last_error = exc
            time.sleep(min(2**attempt, 12))
    raise RuntimeError(f"translation failed after retries: {last_error}")


def batched(
    values: list[str],
    max_batch_chars: int = MAX_BATCH_CHARS,
) -> Iterable[list[str]]:
    current: list[str] = []
    current_size = 0
    for value in values:
        separator_size = 24 if current else 0
        if current and current_size + separator_size + len(value) > max_batch_chars:
            yield current
            current = []
            current_size = 0
        current.append(value)
        current_size += separator_size + len(value)
    if current:
        yield current


def translate_missing(values: set[str], cache: dict[str, str]) -> None:
    pending = sorted(value for value in values if value not in cache)
    if not pending:
        print(f"Translation cache already covers {len(values)} strings.", flush=True)
        return

    session = requests.Session()
    session.headers["User-Agent"] = "EuroMalin bilingual static-site builder/1.0"
    batches = list(batched(pending))
    print(
        f"Translating {len(pending)} new strings in {len(batches)} batches...",
        flush=True,
    )

    for batch_index, batch in enumerate(batches, start=1):
        separators = [f"__EMSEP_{index:04d}__" for index in range(1, len(batch))]
        payload_parts: list[str] = []
        for index, value in enumerate(batch):
            if index:
                payload_parts.append(f"\n{separators[index - 1]}\n")
            payload_parts.append(value)
        translated = translated_response(session, "".join(payload_parts))

        if separators:
            separator_pattern = (
                r"\s*(?:"
                + "|".join(re.escape(separator) for separator in separators)
                + r")\s*"
            )
            parts = re.split(separator_pattern, translated)
        else:
            parts = [translated]

        if len(parts) != len(batch):
            parts = [translated_response(session, value) for value in batch]

        for original, result in zip(batch, parts, strict=True):
            cache[original] = result.strip()

        if batch_index % 10 == 0 or batch_index == len(batches):
            save_cache(cache)
            print(
                f"  translated batch {batch_index}/{len(batches)}",
                flush=True,
            )


def folded_french_text(value: str) -> str:
    return (
        value.casefold()
        .replace("é", "e")
        .replace("è", "e")
        .replace("ê", "e")
        .replace("ë", "e")
        .replace("à", "a")
        .replace("â", "a")
        .replace("î", "i")
        .replace("ï", "i")
        .replace("ô", "o")
        .replace("ù", "u")
        .replace("û", "u")
        .replace("ü", "u")
        .replace("ç", "c")
        .replace("œ", "oe")
    )


def looks_french(value: str) -> bool:
    return bool(FRENCH_MARKERS.search(folded_french_text(value)))


def translation_still_looks_french(value: str) -> bool:
    score = len(FRENCH_MARKERS.findall(folded_french_text(value)))
    has_french_accent = bool(re.search(r"[àâçéèêëîïôùûüœ]", value.casefold()))
    return score >= 2 or (has_french_accent and score >= 1)


def retry_untranslated_french(values: set[str], cache: dict[str, str]) -> None:
    pending = sorted(
        value
        for value in values
        if value in cache
        and looks_french(value)
        and (
            cache[value].strip().casefold() == value.strip().casefold()
            or translation_still_looks_french(cache[value])
        )
    )
    if not pending:
        return

    try:
        from argostranslate.translate import translate as local_translate
    except ImportError:
        local_translate = None

    session = requests.Session()
    session.headers["User-Agent"] = "EuroMalin bilingual static-site builder/1.0"
    batches = list(batched(pending, MAX_RETRY_BATCH_CHARS))
    engine = "local model" if local_translate else "smaller online batches"
    print(
        f"Retrying {len(pending)} untranslated French strings in "
        f"{len(batches)} batches with {engine}...",
        flush=True,
    )

    for batch_index, batch in enumerate(batches, start=1):
        if local_translate:
            parts = [local_translate(value, "fr", "en") for value in batch]
        else:
            separators = [
                f"__EMRETRY_{index:04d}__" for index in range(1, len(batch))
            ]
            payload_parts: list[str] = []
            for index, value in enumerate(batch):
                if index:
                    payload_parts.append(f"\n{separators[index - 1]}\n")
                payload_parts.append(value)
            translated = translated_response(session, "".join(payload_parts))
            if separators:
                pattern = (
                    r"\s*(?:"
                    + "|".join(re.escape(separator) for separator in separators)
                    + r")\s*"
                )
                parts = re.split(pattern, translated)
            else:
                parts = [translated]
            if len(parts) != len(batch):
                parts = [translated_response(session, value) for value in batch]

        for original, result in zip(batch, parts, strict=True):
            cache[original] = result.strip()
        if batch_index % 5 == 0 or batch_index == len(batches):
            save_cache(cache)
            print(
                f"  retried batch {batch_index}/{len(batches)}",
                flush=True,
            )


def meta_attribute_is_translatable(tag: Any) -> bool:
    if tag.name != "meta" or not tag.get("content"):
        return False
    for attribute, accepted_values in META_SELECTORS:
        if tag.get(attribute) in accepted_values:
            return True
    return False


def json_strings(value: Any, key: str | None = None) -> Iterable[str]:
    if isinstance(value, dict):
        for nested_key, nested_value in value.items():
            yield from json_strings(nested_value, nested_key)
    elif isinstance(value, list):
        for nested_value in value:
            yield from json_strings(nested_value, key)
    elif isinstance(value, str) and key in TRANSLATABLE_JSON_KEYS:
        if should_translate(value):
            yield normalized_text(value)


def collect_candidates(soup: BeautifulSoup) -> set[str]:
    candidates: set[str] = set()

    for node in soup.find_all(string=True):
        if isinstance(node, (Comment, Doctype)):
            continue
        parent_name = node.parent.name if node.parent else ""
        if parent_name in SKIP_TEXT_PARENTS:
            continue
        value = normalized_text(str(node))
        if should_translate(value):
            candidates.add(value)

    for tag in soup.find_all(True):
        for attribute in TRANSLATABLE_ATTRIBUTES:
            value = tag.get(attribute)
            if isinstance(value, str) and should_translate(value):
                candidates.add(normalized_text(value))
        if (
            tag.name == "input"
            and tag.get("type") in {"button", "reset", "submit"}
            and isinstance(tag.get("value"), str)
            and should_translate(tag["value"])
        ):
            candidates.add(normalized_text(tag["value"]))
        if meta_attribute_is_translatable(tag):
            value = normalized_text(tag["content"])
            if should_translate(value):
                candidates.add(value)

    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        if not script.string:
            continue
        try:
            data = json.loads(script.string)
        except json.JSONDecodeError:
            continue
        candidates.update(json_strings(data))

    return candidates


def apply_translation_to_text(value: str, cache: dict[str, str]) -> str:
    stripped = normalized_text(value)
    if stripped not in cache:
        return value
    leading = value[: len(value) - len(value.lstrip())]
    trailing = value[len(value.rstrip()) :]
    return f"{leading}{cache[stripped]}{trailing}"


def rewrite_absolute_site_url(value: str, known_pages: set[PurePosixPath]) -> str:
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or parsed.netloc not in {
        "euromalin.com",
        "www.euromalin.com",
    }:
        return value
    target = PurePosixPath(unquote(parsed.path).lstrip("/") or "index.html")
    if target not in known_pages:
        return value
    new_path = "/en/" if target == PurePosixPath("index.html") else f"/en/{target}"
    return urlunsplit(("https", "euromalin.com", new_path, parsed.query, parsed.fragment))


def rewrite_json(
    value: Any,
    cache: dict[str, str],
    known_pages: set[PurePosixPath],
    key: str | None = None,
) -> Any:
    if isinstance(value, dict):
        return {
            nested_key: rewrite_json(
                nested_value,
                cache,
                known_pages,
                nested_key,
            )
            for nested_key, nested_value in value.items()
        }
    if isinstance(value, list):
        return [rewrite_json(item, cache, known_pages, key) for item in value]
    if isinstance(value, str):
        rewritten = rewrite_absolute_site_url(value, known_pages)
        if key in TRANSLATABLE_JSON_KEYS:
            stripped = normalized_text(rewritten)
            return cache.get(stripped, rewritten)
        return rewritten
    return value


def replace_text_and_attributes(soup: BeautifulSoup, cache: dict[str, str]) -> None:
    for node in list(soup.find_all(string=True)):
        if isinstance(node, (Comment, Doctype)):
            continue
        parent_name = node.parent.name if node.parent else ""
        if parent_name in SKIP_TEXT_PARENTS:
            continue
        translated = apply_translation_to_text(str(node), cache)
        if translated != str(node):
            node.replace_with(NavigableString(translated))

    for tag in soup.find_all(True):
        for attribute in TRANSLATABLE_ATTRIBUTES:
            value = tag.get(attribute)
            if isinstance(value, str):
                stripped = normalized_text(value)
                if stripped in cache:
                    tag[attribute] = cache[stripped]
        if (
            tag.name == "input"
            and tag.get("type") in {"button", "reset", "submit"}
            and isinstance(tag.get("value"), str)
        ):
            stripped = normalized_text(tag["value"])
            if stripped in cache:
                tag["value"] = cache[stripped]
        if meta_attribute_is_translatable(tag):
            stripped = normalized_text(tag["content"])
            if stripped in cache:
                tag["content"] = cache[stripped]


def normalized_target(source: PurePosixPath, path: str) -> PurePosixPath | None:
    joined = posixpath.normpath(
        posixpath.join(source.parent.as_posix(), unquote(path))
    )
    if joined == ".." or joined.startswith("../"):
        return None
    return PurePosixPath(joined)


def relative_reference(from_parent: PurePosixPath, to_path: PurePosixPath) -> str:
    return posixpath.relpath(to_path.as_posix(), from_parent.as_posix())


def rewrite_reference(
    value: str,
    rel: PurePosixPath,
    known_pages: set[PurePosixPath],
) -> str:
    if not value or value.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
        return value

    parsed = urlsplit(value)
    if parsed.netloc and parsed.netloc not in {"euromalin.com", "www.euromalin.com"}:
        return value
    if parsed.scheme and parsed.scheme not in {"http", "https"}:
        return value
    if parsed.scheme in {"http", "https"}:
        return rewrite_absolute_site_url(value, known_pages)

    path = parsed.path
    if not path:
        return value

    if path.startswith("/"):
        target = PurePosixPath(unquote(path).lstrip("/") or "index.html")
        if target in known_pages:
            rewritten_path = (
                "/en/" if target == PurePosixPath("index.html") else f"/en/{target}"
            )
            return urlunsplit(("", "", rewritten_path, parsed.query, parsed.fragment))
        return value

    target = normalized_target(rel, path)
    if target is None:
        return value

    output_parent = PurePosixPath("en") / rel.parent
    if target not in known_pages:
        root_relative_candidate = PurePosixPath(unquote(path))
        if root_relative_candidate in known_pages:
            target = root_relative_candidate
    if target in known_pages:
        destination = PurePosixPath("en") / target
    else:
        local_target = ROOT / Path(target.as_posix())
        if not local_target.exists():
            return value
        destination = target

    rewritten_path = relative_reference(output_parent, destination)
    return urlunsplit(("", "", rewritten_path, parsed.query, parsed.fragment))


def rewrite_srcset(
    value: str,
    rel: PurePosixPath,
    known_pages: set[PurePosixPath],
) -> str:
    items: list[str] = []
    for item in value.split(","):
        bits = item.strip().split(maxsplit=1)
        if not bits:
            continue
        rewritten = rewrite_reference(bits[0], rel, known_pages)
        items.append(rewritten if len(bits) == 1 else f"{rewritten} {bits[1]}")
    return ", ".join(items)


def rewrite_document_references(
    soup: BeautifulSoup,
    rel: PurePosixPath,
    known_pages: set[PurePosixPath],
) -> None:
    for tag in soup.find_all(True):
        for attribute in ("href", "src", "poster"):
            value = tag.get(attribute)
            if isinstance(value, str):
                tag[attribute] = rewrite_reference(value, rel, known_pages)
        if isinstance(tag.get("srcset"), str):
            tag["srcset"] = rewrite_srcset(tag["srcset"], rel, known_pages)


def set_english_metadata(soup: BeautifulSoup, rel: PurePosixPath) -> None:
    if soup.html:
        soup.html["lang"] = "en"

    for link in list(soup.find_all("link")):
        if link.attrs is None:
            continue
        rel_values = link.get("rel") or []
        if "alternate" in rel_values and link.get("hreflang"):
            link.decompose()

    canonical = soup.find("link", rel=lambda value: value and "canonical" in value)
    if canonical is None:
        canonical = soup.new_tag("link", rel="canonical")
        soup.head.append(canonical)
    canonical["href"] = english_url(rel)

    for language, url in (
        ("fr", french_url(rel)),
        ("en", english_url(rel)),
        ("x-default", french_url(rel)),
    ):
        alternate = soup.new_tag("link", rel="alternate", hreflang=language, href=url)
        canonical.insert_after(alternate)

    og_url = soup.find("meta", attrs={"property": "og:url"})
    if og_url:
        og_url["content"] = english_url(rel)

    og_locale = soup.find("meta", attrs={"property": "og:locale"})
    if og_locale:
        og_locale["content"] = "en_US"
        alternate_locale = soup.new_tag("meta")
        alternate_locale["property"] = "og:locale:alternate"
        alternate_locale["content"] = "fr_FR"
        og_locale.insert_after(alternate_locale)

    switcher = soup.find("a", class_="language-switcher")
    if switcher:
        switcher["href"] = french_path_fragment(rel)
        switcher["lang"] = "fr"
        switcher["hreflang"] = "fr"
        switcher["aria-label"] = "Read this page in French"
        switcher.string = "FR"


def translate_json_scripts(
    soup: BeautifulSoup,
    cache: dict[str, str],
    known_pages: set[PurePosixPath],
) -> int:
    failures = 0
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        if not script.string:
            continue
        try:
            data = json.loads(script.string)
        except json.JSONDecodeError:
            failures += 1
            continue
        translated = rewrite_json(data, cache, known_pages)
        script.string.replace_with(
            NavigableString(json.dumps(translated, ensure_ascii=False, indent=2))
        )
    return failures


def translate_static_script_strings(soup: BeautifulSoup) -> None:
    for script in soup.find_all("script"):
        if script.get("type") == "application/ld+json" or not script.string:
            continue
        updated = str(script.string)
        for french, english in STATIC_SCRIPT_TRANSLATIONS.items():
            updated = updated.replace(french, english)
        if updated != str(script.string):
            script.string.replace_with(NavigableString(updated))


def write_sitemap(rels: list[PurePosixPath]) -> None:
    included = [rel for rel in rels if rel != PurePosixPath("404.html")]
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        (
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
            'xmlns:xhtml="http://www.w3.org/1999/xhtml">'
        ),
    ]
    for rel in included:
        fr = french_url(rel)
        en = english_url(rel)
        priority = "1.0" if rel == PurePosixPath("index.html") else (
            "0.9" if len(rel.parts) == 1 else "0.7"
        )
        for loc in (fr, en):
            lines.extend(
                [
                    "  <url>",
                    f"    <loc>{html.escape(loc)}</loc>",
                    f"    <lastmod>{BUILD_DATE}</lastmod>",
                    "    <changefreq>weekly</changefreq>",
                    f"    <priority>{priority}</priority>",
                    (
                        '    <xhtml:link rel="alternate" hreflang="fr" '
                        f'href="{html.escape(fr)}" />'
                    ),
                    (
                        '    <xhtml:link rel="alternate" hreflang="en" '
                        f'href="{html.escape(en)}" />'
                    ),
                    (
                        '    <xhtml:link rel="alternate" hreflang="x-default" '
                        f'href="{html.escape(fr)}" />'
                    ),
                    "  </url>",
                ]
            )
    lines.append("</urlset>")
    (ROOT / "sitemap.xml").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main() -> None:
    paths = public_paths()
    for template in (ROOT / "bons-plans").glob("_*.html"):
        source = template.read_text(encoding="utf-8")
        source = re.sub(
            r"\n?\s*<!-- euromalin-bilingual:begin -->.*?"
            r"<!-- euromalin-bilingual:end -->\s*\n?",
            "\n",
            source,
            flags=re.DOTALL,
        )
        source = re.sub(
            r"\s*<a\b[^>]*class=[\"'][^\"']*\blanguage-switcher\b[^\"']*[\"']"
            r"[^>]*>.*?</a>",
            "",
            source,
            flags=re.DOTALL | re.IGNORECASE,
        )
        source = re.sub(r"[ \t]+(?=\n|$)", "", source)
        template.write_text(source, encoding="utf-8", newline="\n")
        generated_template = EN_ROOT / "bons-plans" / template.name
        if generated_template.exists():
            generated_template.unlink()

    for path in paths:
        ensure_french_bilingual_metadata(path)

    documents: list[tuple[Path, PurePosixPath, BeautifulSoup]] = []
    candidates: set[str] = set()
    for path in paths:
        rel = source_rel(path)
        soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
        documents.append((path, rel, soup))
        candidates.update(collect_candidates(soup))

    cache = load_cache()
    cache.update(MANUAL_TRANSLATIONS)
    translate_missing(candidates, cache)
    retry_untranslated_french(candidates, cache)
    cache.update(MANUAL_TRANSLATIONS)
    save_cache(cache)

    known_pages = {rel for _, rel, _ in documents}
    json_failures = 0
    for _, rel, soup in documents:
        replace_text_and_attributes(soup, cache)
        json_failures += translate_json_scripts(soup, cache, known_pages)
        translate_static_script_strings(soup)
        rewrite_document_references(soup, rel, known_pages)
        set_english_metadata(soup, rel)

        output_path = EN_ROOT / Path(rel.as_posix())
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            soup.decode(formatter="minimal"),
            encoding="utf-8",
            newline="\n",
        )

    write_sitemap(sorted(known_pages))
    print(
        f"Built {len(documents)} English pages with {len(candidates)} translated "
        f"strings; JSON-LD parse failures: {json_failures}.",
        flush=True,
    )


if __name__ == "__main__":
    main()
