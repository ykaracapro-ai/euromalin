#!/usr/bin/env python3
"""Normalize the public GamsGo affiliate offer without promising a fixed discount."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GAMSGO_URL = "https://www.gamsgo.com/partner/Px5AZ"


LITERAL_REPLACEMENTS = {
    "Code promo WPQTU pour 7 % supplémentaires.": (
        "Code promo WPQTU à tester au panier ; vérifiez la remise et le total affiché."
    ),
    "Code promo <code>WPQTU</code> pour 7 % supplémentaires.": (
        "Code promo <code>WPQTU</code> à tester au panier ; vérifiez la remise et le total affiché."
    ),
    "Avec le code promo WPQTU vous obtenez 7 % supplémentaires.": (
        "Testez le code promo WPQTU au panier, puis vérifiez la remise et le total affiché."
    ),
    (
        "Et avec le code promo <code>WPQTU</code>, vous obtenez encore "
        "7 % de plus sur le panier."
    ): (
        "Testez aussi le code promo <code>WPQTU</code> au panier, puis fiez-vous "
        "à la remise et au total affichés."
    ),
    (
        "<li><strong>Saisissez le code promo <code>WPQTU</code></strong> "
        "au moment du paiement pour 7 % supplémentaires</li>"
    ): (
        "<li><strong>Saisissez le code promo <code>WPQTU</code></strong> "
        "au moment du paiement, puis vérifiez la remise et le total affiché</li>"
    ),
    (
        "<span>Code promo <code>WPQTU</code> = 7 % supplémentaires offerts. "
        "Inscription en moins de 5 minutes.</span>"
    ): (
        "<span>Code promo <code>WPQTU</code> à tester au panier. Vérifiez la "
        "remise et le total affiché avant de payer.</span>"
    ),
    (
        "Mais le code promo <code>WPQTU</code> vous donne déjà 7 % "
        "supplémentaires sur le panier, qui se cumule avec les promotions "
        "GamsGo en cours."
    ): (
        "Testez le code promo <code>WPQTU</code> au panier et vérifiez si la "
        "remise affichée se cumule avec la promotion GamsGo en cours."
    ),
    (
        "Code <strong>WPQTU</strong> pour 7% de réduction supplémentaire."
    ): (
        "Code <strong>WPQTU</strong> à tester au panier ; vérifie la remise "
        "et le total affiché."
    ),
    "(code <strong>WPQTU</strong> pour -7%)": (
        "(code <strong>WPQTU</strong> à tester au panier)"
    ),
    (
        "Jusqu'à -33% sur Netflix, -50% sur YouTube Premium, -7% sur le "
        "forfait GamsGo avec le code <strong>WPQTU</strong>."
    ): (
        "Compare les tarifs Netflix et YouTube Premium, puis teste le code "
        "<strong>WPQTU</strong> au panier GamsGo et vérifie le total affiché."
    ),
    "GamsGo : -7% avec code WPQTU": (
        "GamsGo : code WPQTU à tester au panier"
    ),
    (
        "Netflix, Spotify, YouTube à -70% via GamsGo. Code "
        "<strong>WPQTU</strong> = -7%."
    ): (
        "Compare Netflix, Spotify et YouTube via GamsGo. Teste le code "
        "<strong>WPQTU</strong> au panier et vérifie le total."
    ),
    "Lien GamsGo (+ code WPQTU -7%) + quels abos choisir": (
        "Lien GamsGo (+ code WPQTU à tester au panier) + quels abos choisir"
    ),
}


def public_html_files() -> list[Path]:
    paths = list(ROOT.glob("*.html"))
    paths += list((ROOT / "articles").glob("*.html"))
    paths += list((ROOT / "bons-plans").glob("*.html"))
    return sorted(paths)


def update_file(path: Path) -> bool:
    source = path.read_text(encoding="utf-8")
    updated = source

    updated = re.sub(
        r"https://www\.gamsgo\.com/partner/[A-Za-z0-9_-]+",
        GAMSGO_URL,
        updated,
    )
    for old, new in LITERAL_REPLACEMENTS.items():
        updated = updated.replace(old, new)

    updated = re.sub(
        r"<span>(\d+)% d'économies \+ 7 % avec code "
        r"<code>WPQTU</code>\. Livraison instantanée, garantie GamsGo\.</span>",
        (
            r"<span>\1% d'économies sur le prix comparé. Code "
            r"<code>WPQTU</code> à tester au panier.</span>"
        ),
        updated,
    )

    if updated == source:
        return False
    path.write_text(updated, encoding="utf-8", newline="\n")
    return True


def validate(paths: list[Path]) -> None:
    fixed_claim = re.compile(
        r"(?is)(?:"
        r"WPQTU.{0,55}(?:pour|=|offre|donne|avec).{0,30}(?:-?7\s*%)"
        r"|(?:\+|-)\s*7\s*%\s+(?:avec|code).{0,30}WPQTU"
        r")"
    )
    errors: list[str] = []

    for path in paths:
        source = path.read_text(encoding="utf-8")
        if re.search(r"https://www\.gamsgo\.com/partner/(?!Px5AZ)", source):
            errors.append(f"{path.relative_to(ROOT)}: unexpected partner URL")
        if fixed_claim.search(source):
            errors.append(f"{path.relative_to(ROOT)}: fixed WPQTU discount claim")
        if GAMSGO_URL in source and "WPQTU" not in source:
            errors.append(f"{path.relative_to(ROOT)}: partner link without WPQTU")

    if errors:
        raise SystemExit("\n".join(errors))


def main() -> None:
    paths = public_html_files()
    changed = [path for path in paths if update_file(path)]
    validate(paths)
    print(f"Updated {len(changed)} GamsGo pages; validated {len(paths)} public pages.")


if __name__ == "__main__":
    main()
