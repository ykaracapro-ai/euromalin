#!/usr/bin/env python3
"""Build the dated GamsGo price guides and current-catalog hubs."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from build_u7buy_content import (
    ARTICLES,
    ECB_USD_PER_EUR,
    GAMSGO_CODE,
    GAMSGO_URL,
    ROOT,
    TODAY,
    U7_CODE,
    card,
    disclosure,
    esc,
    footer,
    head,
    header,
    json_ld,
    write_article_preserving_hero,
)


GAMSGO_CATALOG = "https://www.gamsgo.com/accounts"
GAMSGO_PROTECTION = (
    "https://help.gamsgo.com/en/article/"
    "rules-for-sellers-of-digital-subscription-products-1muaxb9/"
)
ECB_SOURCE = (
    "https://www.ecb.europa.eu/stats/policy_and_exchange_rates/"
    "euro_reference_exchange_rates/html/eurofxref-graph-usd.fr.html"
)
U7_AFFILIATE = "https://www.u7buy.com?referral-code=CzMdAgd4"


@dataclass(frozen=True)
class GamsGoProduct:
    slug: str
    service: str
    plan: str
    price_usd: float
    official_usd: float | None
    product_url: str
    category: str
    access_method: str
    use_case: str
    risk: str
    checks: tuple[str, ...]
    official_url: str
    official_label: str
    cover_query: str

    @property
    def price_eur(self) -> str:
        return f"{self.price_usd / ECB_USD_PER_EUR:.2f}".replace(".", ",")

    @property
    def title(self) -> str:
        return f"Comment payer environ {self.price_eur} € pour {self.plan} ?"

    @property
    def description(self) -> str:
        return (
            f"{self.plan} à environ {self.price_eur} € sur GamsGo : prix relevé, "
            "conversion en euros, type d’accès, limites, risques et vérifications avant achat."
        )


PRODUCTS = [
    GamsGoProduct(
        "payer-genspark-plus-moins-cher",
        "Genspark",
        "Genspark Plus",
        16.99,
        24.99,
        "https://www.gamsgo.com/details/genspark",
        "IA",
        "un compte Plus privé préactivé avec crédits et modèles avancés",
        "recherche, présentations, génération multimédia et automatisation de tâches",
        "Le compte peut être administré par un tiers. Ne lui confiez aucun connecteur, document ou secret professionnel avant d’avoir vérifié qui contrôle l’e-mail de récupération.",
        (
            "le nombre de crédits réellement inclus",
            "le caractère privé du compte",
            "l’accès aux modèles annoncés",
            "la durée de la garantie",
        ),
        "https://www.genspark.ai/pricing",
        "tarifs officiels Genspark",
        "artificial intelligence research laptop",
    ),
    GamsGoProduct(
        "payer-suno-pro-moins-cher",
        "Suno",
        "Suno Pro",
        4.99,
        10.00,
        "https://www.gamsgo.com/details/suno",
        "IA créative",
        "un compte Suno Pro fourni après paiement",
        "créer des chansons, maquettes, jingles ou bandes-son avec davantage de crédits",
        "Les droits commerciaux dépendent du plan actif au moment de la création. Archivez les conditions et n’utilisez pas de voix, paroles ou œuvres protégées sans autorisation.",
        (
            "les crédits mensuels",
            "les droits commerciaux des créations",
            "le contrôle de l’e-mail",
            "la version du modèle accessible",
        ),
        "https://suno.com/pricing",
        "tarifs officiels Suno",
        "music production studio headphones",
    ),
    GamsGoProduct(
        "payer-grok-ai-moins-cher",
        "Grok",
        "Grok AI",
        18.99,
        30.00,
        "https://www.gamsgo.com/details/grok",
        "IA",
        "un compte donnant accès au plan et aux quotas Grok indiqués dans l’offre",
        "conversation IA, recherche en temps réel et génération de contenu",
        "La disponibilité des modèles, les quotas et le lien éventuel avec un compte X peuvent changer. Évitez de rattacher un profil social personnel à des identifiants contrôlés par un vendeur.",
        (
            "la formule exacte",
            "les limites quotidiennes",
            "la nécessité d’un compte X",
            "la récupération du compte",
        ),
        "https://help.x.com/en/using-x/about-x-premium",
        "aide officielle X Premium",
        "artificial intelligence smartphone laptop",
    ),
    GamsGoProduct(
        "payer-kling-ai-pro-moins-cher",
        "Kling AI",
        "Kling AI Pro",
        7.99,
        28.99,
        "https://www.gamsgo.com/details/kling-ai",
        "Vidéo IA",
        "un compte ou un accès mensuel avec crédits de génération vidéo",
        "transformer du texte ou des images en séquences vidéo",
        "Les crédits peuvent être consommés très vite selon la résolution et la durée. Vérifiez aussi les droits d’utilisation des visages, images et musiques importés.",
        (
            "le nombre de crédits",
            "la résolution maximale",
            "la présence d’un filigrane",
            "les droits d’usage commercial",
        ),
        "https://klingai.com/global/membership/membership-plan",
        "formules officielles Kling AI",
        "video editing creative workstation",
    ),
    GamsGoProduct(
        "payer-candy-ai-moins-cher",
        "Candy AI",
        "Candy AI Premium",
        9.99,
        13.99,
        "https://www.gamsgo.com/details/candy-ai",
        "IA conversationnelle",
        "un compte Premium donnant accès aux fonctions et quotas décrits",
        "conversation, génération d’images et personnalisation de personnages virtuels",
        "Ce service peut traiter des données intimes. N’envoyez aucune photo identifiable, information sensible ou donnée d’un tiers sans son consentement.",
        (
            "les règles d’âge du service",
            "la confidentialité des conversations",
            "les quotas d’images ou messages",
            "la suppression des données",
        ),
        "https://candy.ai/",
        "site officiel Candy AI",
        "smartphone artificial intelligence privacy",
    ),
    GamsGoProduct(
        "payer-poe-ai-moins-cher",
        "Poe",
        "Poe AI Plus",
        4.17,
        None,
        "https://www.gamsgo.com/details/poe",
        "IA",
        "un compte avec points de calcul et accès à plusieurs modèles",
        "tester plusieurs assistants IA depuis une seule interface",
        "Les modèles, points et limites changent régulièrement. Un accès vendu par un tiers ne doit pas servir à traiter des documents confidentiels.",
        (
            "les points de calcul inclus",
            "les modèles réellement accessibles",
            "la durée exacte",
            "le contrôle de l’e-mail",
        ),
        "https://poe.com/subscriptions",
        "abonnements officiels Poe",
        "artificial intelligence chat laptop",
    ),
    GamsGoProduct(
        "payer-filmora-moins-cher",
        "Filmora",
        "Filmora",
        4.50,
        9.99,
        "https://www.gamsgo.com/details/filmora",
        "Logiciel",
        "un compte ou une licence Filmora selon la fiche choisie",
        "montage vidéo, effets, sous-titres et outils assistés par IA",
        "Une licence peut être liée à un appareil, une région ou un compte vendeur. Vérifiez si les crédits IA, mises à jour et export sans filigrane sont réellement inclus.",
        (
            "Windows, macOS ou mobile",
            "le nombre d’appareils",
            "l’export sans filigrane",
            "les crédits IA inclus",
        ),
        "https://filmora.wondershare.com/shop/buy/buy-video-editor.html",
        "tarifs officiels Filmora",
        "video editing workstation",
    ),
    GamsGoProduct(
        "payer-wps-office-moins-cher",
        "WPS Office",
        "WPS Office",
        2.99,
        None,
        "https://www.gamsgo.com/details/wps",
        "Logiciel",
        "un abonnement WPS Office fourni sous la forme précisée dans l’offre",
        "éditer des documents, feuilles de calcul, présentations et PDF",
        "Un compte partagé n’est pas adapté aux documents confidentiels. Vérifiez aussi le stockage cloud, le nombre d’appareils et les fonctions PDF incluses.",
        (
            "le nombre d’appareils",
            "le stockage cloud",
            "les outils PDF",
            "le caractère privé du compte",
        ),
        "https://www.wps.com/pricing/",
        "tarifs officiels WPS Office",
        "office documents laptop desk",
    ),
    GamsGoProduct(
        "payer-hbo-max-moins-cher",
        "HBO Max",
        "HBO Max",
        4.25,
        6.92,
        "https://www.gamsgo.com/details/max",
        "Streaming",
        "un profil ou compte de streaming selon la formule affichée",
        "regarder les séries et films du catalogue Max sur plusieurs appareils",
        "Les catalogues et règles de foyer varient par pays. Un profil partagé peut perdre l’accès, demander une vérification ou être limité à un appareil.",
        (
            "le pays du compte",
            "la qualité vidéo",
            "le nombre d’appareils",
            "le profil privé ou partagé",
        ),
        "https://help.max.com/",
        "aide officielle Max",
        "streaming television cinema living room",
    ),
    GamsGoProduct(
        "payer-fox-one-moins-cher",
        "FOX One",
        "FOX One",
        6.92,
        19.99,
        "https://www.gamsgo.com/details/fox-one",
        "Streaming",
        "un accès mensuel au service indiqué dans la fiche",
        "regarder des chaînes et programmes FOX disponibles dans la région couverte",
        "FOX One n’est pas disponible partout et son catalogue dépend du pays. Confirmez la zone d’utilisation et la compatibilité avant paiement.",
        (
            "la disponibilité en France ou Belgique",
            "les chaînes réellement incluses",
            "les appareils compatibles",
            "les restrictions géographiques",
        ),
        "https://www.fox.com/",
        "site officiel FOX",
        "television sports streaming remote",
    ),
    GamsGoProduct(
        "payer-midjourney-moins-cher",
        "Midjourney",
        "Midjourney",
        7.99,
        10.00,
        "https://www.gamsgo.com/details/midjourney",
        "IA créative",
        "un compte ou accès à une formule Midjourney selon la fiche",
        "générer des images et explorer rapidement des directions visuelles",
        "Le mode d’accès, la confidentialité des créations et les droits commerciaux dépendent du plan. Ne supposez pas qu’un accès tiers équivaut à votre propre abonnement officiel.",
        (
            "le nombre d’heures rapides",
            "le mode privé ou public",
            "les droits commerciaux",
            "le contrôle du compte",
        ),
        "https://docs.midjourney.com/docs/plans",
        "formules officielles Midjourney",
        "ai generated art abstract",
    ),
    GamsGoProduct(
        "payer-capcut-pro-moins-cher",
        "CapCut",
        "CapCut Pro",
        7.99,
        None,
        "https://www.gamsgo.com/details/capcut",
        "Logiciel",
        "un compte CapCut Pro, une recharge ou un accès selon la fiche",
        "monter des vidéos, utiliser des modèles, sous-titres et fonctions IA",
        "Les fonctions et tarifs CapCut diffèrent selon la région, la plateforme et l’appareil. Vérifiez que l’accès fonctionne sur votre propre appareil et sans partager vos projets.",
        (
            "ordinateur ou mobile",
            "la région du compte",
            "le stockage cloud",
            "les crédits et fonctions IA",
        ),
        "https://www.capcut.com/pricing",
        "tarifs officiels CapCut",
        "video editing creator",
    ),
    GamsGoProduct(
        "payer-canva-pro-moins-cher",
        "Canva",
        "Canva Pro",
        9.99,
        20.00,
        "https://www.gamsgo.com/details/cannva",
        "Logiciel",
        "un compte, une invitation d’équipe ou un accès Pro selon l’offre",
        "créer des visuels, présentations, vidéos et contenus de marque",
        "Une place d’équipe peut être retirée par son administrateur. N’y stockez pas de kit de marque, fichiers clients ou créations confidentielles sans contrôle durable du compte.",
        (
            "compte privé ou siège d’équipe",
            "la propriété des créations",
            "le stockage inclus",
            "la possibilité d’exporter avant la fin",
        ),
        "https://www.canva.com/pricing/",
        "tarifs officiels Canva",
        "graphic design workspace laptop",
    ),
    GamsGoProduct(
        "payer-disney-plus-moins-cher",
        "Disney+",
        "Disney+",
        4.99,
        12.99,
        "https://www.gamsgo.com/details/disneyplus",
        "Streaming",
        "un compte ou profil Disney+ fourni pour la durée choisie",
        "regarder Disney, Pixar, Marvel, Star Wars et les autres catalogues disponibles",
        "Un profil partagé peut être limité par les règles de foyer, le nombre d’écrans et la région. Ne réutilisez jamais un mot de passe personnel sur ce compte.",
        (
            "la région",
            "la qualité 4K ou Full HD",
            "le nombre d’appareils",
            "le renouvellement du même compte",
        ),
        "https://www.disneyplus.com/",
        "site officiel Disney+",
        "cinema popcorn movie",
    ),
]


def affiliate_cta(product: GamsGoProduct) -> str:
    return f"""<div class="offer-duo">
<div class="platform-card platform-card--gamsgo">
<span class="platform-card__eyebrow">GamsGo • lien partenaire</span>
<h3>{esc(product.plan)} à comparer</h3>
<p>Le prix relevé était de <strong>{product.price_usd:.2f} $</strong>. Testez le code <code>{GAMSGO_CODE}</code> au panier et fiez-vous au total affiché.</p>
<a class="btn btn-primary" href="{GAMSGO_URL}" target="_blank" rel="sponsored noopener noreferrer">Voir GamsGo →</a>
</div>
<div class="platform-card platform-card--u7buy">
<span class="platform-card__eyebrow">Alternative marketplace</span>
<h3>Comparer aussi U7BUY</h3>
<p>U7BUY peut proposer plusieurs vendeurs. Le code <code>{U7_CODE}</code> annonce 5 % de remise supplémentaire sur les commandes éligibles.</p>
<a class="btn ghost" href="{U7_AFFILIATE}" target="_blank" rel="sponsored noopener noreferrer">Ouvrir U7BUY →</a>
</div>
</div>"""


def product_page(product: GamsGoProduct) -> str:
    official = (
        f"{product.official_usd:.2f} $"
        if product.official_usd is not None
        else "selon la formule officielle"
    )
    savings = ""
    if product.official_usd:
        percent = round((1 - product.price_usd / product.official_usd) * 100)
        savings = f", soit environ {percent} % sous le repère officiel affiché"
    faq = [
        (
            f"Peut-on réellement payer {product.price_eur} € pour {product.plan} ?",
            f"Le 24 juillet 2026, GamsGo affichait {product.price_usd:.2f} $. "
            "La conversion donne ce montant indicatif, mais le plan, la devise, la durée, "
            "les frais et le pays peuvent modifier le total.",
        ),
        (
            f"Que reçoit-on pour {product.plan} sur GamsGo ?",
            f"La fiche décrit {product.access_method}. Il faut relire le mode de livraison, "
            "le contrôle du compte et la durée exacte avant de payer.",
        ),
        (
            f"Le code {GAMSGO_CODE} fonctionne-t-il ?",
            f"Le code {GAMSGO_CODE} peut être testé au panier. EuroMalin ne l’intègre pas "
            "au prix du titre car son éligibilité et son effet peuvent changer.",
        ),
        (
            "Quelle protection s’applique si l’accès cesse de fonctionner ?",
            "GamsGo indique une protection DealShield de 5 à 90 jours pour les produits "
            "d’abonnement numérique, selon la durée du produit. Vérifiez la période de la fiche.",
        ),
    ]
    checks = "".join(f"<li>{esc(check.capitalize())}.</li>" for check in product.checks)
    return (
        head(product.title, product.description, product.slug, faq)
        + header()
        + f"""<main id="main">
<section class="hero-mini"><div class="container">
<div class="breadcrumbs"><a href="../index.html">Accueil</a> · <a href="../articles.html">Articles</a> · GamsGo</div>
<div class="hero-card"><div class="eyebrow">Prix contrôlé • 24 juillet 2026</div>
<h1>{esc(product.title)}</h1><p class="lead">{esc(product.description)}</p></div>
</div></section>
<section class="section"><div class="container page-grid">
<article class="hero-card article">
{disclosure()}
<div class="fact-strip"><div><strong>{product.price_eur} €</strong><span>conversion indicative</span></div><div><strong>{product.price_usd:.2f} $</strong><span>prix GamsGo relevé</span></div><div><strong>{esc(product.category)}</strong><span>{esc(product.service)}</span></div></div>
<h2>Le prix en une phrase</h2>
<div class="verdict-box"><span class="verdict-box__label">Repère EuroMalin</span><p>GamsGo affichait {product.plan} à <strong>{product.price_usd:.2f} $</strong>, soit environ <strong>{product.price_eur} €</strong> au taux BCE du jour{savings}. Ce montant reste un instantané, pas une garantie permanente.</p></div>
<h2>Comment obtient-on environ {product.price_eur} € ?</h2>
<p>La conversion utilise 1 € pour 1,1694 $, taux de référence BCE du 24 juillet 2026. Elle n’inclut ni éventuels frais de paiement ni code promotionnel. Le panier peut donc différer de quelques centimes ou davantage selon la devise et la formule choisie.</p>
<div class="responsive-table"><table><thead><tr><th>Repère</th><th>Montant</th><th>Ce qu’il faut comprendre</th></tr></thead><tbody>
<tr><td>Prix GamsGo relevé</td><td>{product.price_usd:.2f} $</td><td>Prix public affiché sur la page produit</td></tr>
<tr><td>Conversion indicative</td><td>{product.price_eur} €</td><td>Avant frais et code promo</td></tr>
<tr><td>Repère officiel</td><td>{official}</td><td>Peut varier selon pays, mensualité ou engagement</td></tr>
</tbody></table></div>
{affiliate_cta(product)}
<h2>Ce que vous achetez réellement</h2>
<p>La fiche GamsGo décrit {esc(product.access_method)}. L’usage principal est de {esc(product.use_case)}. Selon le produit, la livraison peut prendre la forme d’identifiants, d’une invitation, d’un compte préactivé ou d’une recharge appliquée à votre propre compte.</p>
<p>Ces formats ne donnent pas tous le même contrôle. Un abonnement officiel souscrit directement reste le plus simple pour la récupération, la confidentialité et la conformité aux règles du fournisseur. Un prix inférieur peut être intéressant si la fiche explique clairement les restrictions et si elles conviennent à votre usage.</p>
<h2>Le risque principal pour {esc(product.service)}</h2>
<div class="warning-box"><strong>À vérifier :</strong> {esc(product.risk)}</div>
<p>Un prix bas ne compense pas une mauvaise région, un compte partagé inadapté ou une garantie trop courte. Prenez une capture de la fiche et de la durée de protection avant le paiement. Si la livraison ne correspond pas, restez dans la messagerie et le système de litige de la plateforme.</p>
<h2>Checklist avant de payer</h2>
<ul class="check-list">{checks}<li>Le montant final dans votre devise.</li><li>La durée DealShield réellement indiquée.</li><li>L’absence de paiement ou de discussion déplacés hors plateforme.</li></ul>
<h2>Comment acheter sans se fier uniquement au prix</h2>
<ol><li>Ouvrez la page produit et identifiez le plan, la durée et le type d’accès.</li><li>Comparez le prix de {product.price_usd:.2f} $ au panier et à l’offre officielle.</li><li>Testez le code <code>{GAMSGO_CODE}</code> sans supposer qu’il est universel.</li><li>Vérifiez les frais, la devise et la protection avant paiement.</li><li>Testez immédiatement l’accès livré et conservez les preuves.</li></ol>
<h2>GamsGo ou U7BUY ?</h2>
<p>GamsGo est généralement plus lisible quand le produit est vendu directement avec un prix et un mode d’accès précis. U7BUY peut être utile pour comparer plusieurs vendeurs ou chercher un autre format. Le bon choix dépend moins du bandeau promotionnel que du contrôle du compte, de la région, de la garantie et du total réellement payé.</p>
<h2>Questions fréquentes</h2><div class="faq">{''.join(f'<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>' for q, a in faq)}</div>
<h2>Sources et méthode</h2>
<p>Prix relevé sur la <a href="{esc(product.product_url)}" target="_blank" rel="noopener noreferrer">page {esc(product.plan)} de GamsGo</a> le 24 juillet 2026. Conversion avec le <a href="{ECB_SOURCE}" target="_blank" rel="noopener noreferrer">taux euro/dollar de la BCE</a>. Vérifiez aussi les <a href="{GAMSGO_PROTECTION}" target="_blank" rel="noopener noreferrer">règles DealShield pour abonnements numériques</a> et les <a href="{esc(product.official_url)}" target="_blank" rel="noopener noreferrer">{esc(product.official_label)}</a>.</p>
{affiliate_cta(product)}
</article><aside class="sidebar">
<div class="sidebar-card"><div class="kicker">Nouveautés</div><h3>Le catalogue GamsGo 2026</h3><a class="btn ghost" href="gamsgo-nouveautes-prix-2026.html">Voir les nouveautés</a></div>
<div class="sidebar-card"><div class="kicker">Comparatif</div><h3>U7BUY ou GamsGo ?</h3><a class="btn ghost" href="u7buy-vs-gamsgo.html">Comparer les plateformes</a></div>
</aside></div></section></main>"""
        + footer()
    )


def hub_page() -> tuple[str, str, str]:
    slug = "gamsgo-nouveautes-prix-2026"
    title = "Nouveautés GamsGo 2026 : services et prix vérifiés"
    description = (
        "Les nouveautés GamsGo vérifiées en juillet 2026 : streaming, IA, logiciels, "
        "marketplace et gaming, avec prix datés, conversions en euros et guides détaillés."
    )
    faq = [
        (
            "Quelles sont les principales nouveautés GamsGo ?",
            "Le catalogue visible inclut désormais davantage d’outils IA, notamment Genspark, "
            "Suno, Grok, Kling AI, Runway, Poe et plusieurs services vidéo, ainsi qu’une "
            "marketplace et des rubriques gaming élargies.",
        ),
        (
            "Les prix en euros sont-ils garantis ?",
            "Non. Ils sont convertis depuis les prix en dollars relevés le 24 juillet 2026 "
            "avec le taux BCE du jour. Le panier, les frais, la devise et le plan peuvent varier.",
        ),
        (
            "GamsGo vend-il uniquement des abonnements partagés ?",
            "Non. Le catalogue mélange offres directes, comptes, invitations, recharges, "
            "marketplace et produits gaming. Le format exact doit être lu sur chaque fiche.",
        ),
        (
            "Quelle est la différence avec U7BUY ?",
            "GamsGo met en avant davantage d’offres directes et une marketplace en croissance. "
            "U7BUY reste très large sur les vendeurs et les services gaming.",
        ),
    ]
    rows = "".join(
        f'<tr><td><a href="{esc(item.slug)}.html">{esc(item.plan)}</a></td>'
        f"<td>{item.price_usd:.2f} $</td><td>{item.price_eur} €</td>"
        f"<td>{esc(item.category)}</td></tr>"
        for item in PRODUCTS
    )
    return (
        slug,
        title,
        head(title, description, slug, faq)
        + header()
        + f"""<main id="main">
<section class="hero-mini"><div class="container"><div class="breadcrumbs"><a href="../index.html">Accueil</a> · <a href="../articles.html">Articles</a> · GamsGo</div>
<div class="hero-card"><div class="eyebrow">Veille catalogue • 24 juillet 2026</div><h1>{esc(title)}</h1><p class="lead">{esc(description)}</p></div></div></section>
<section class="section"><div class="container page-grid"><article class="hero-card article">
{disclosure()}
<div class="fact-strip"><div><strong>SVOD</strong><span>YouTube, Crunchyroll, FOX One</span></div><div><strong>IA</strong><span>14 services visibles</span></div><div><strong>Gaming</strong><span>recharges, comptes, cartes, coins et items</span></div></div>
<h2>Ce qui a changé chez GamsGo</h2>
<div class="verdict-box"><span class="verdict-box__label">Mise à jour</span><p>GamsGo n’est plus seulement une vitrine de streaming partagé. Le catalogue public regroupe maintenant abonnements directs, IA générative, logiciels, marketplace de comptes et six grandes familles gaming.</p></div>
<p>Les ajouts les plus visibles sont les outils IA spécialisés : Genspark pour la recherche et les agents, Suno pour la musique, Grok, Cursor, Kling AI, Runway, Midjourney, Dreamina, Candy AI et Poe. Côté marketplace figurent notamment Claude, SuperGrok, Microsoft Office, Adobe, Proton VPN, TradingView, Zoom, Lovable, Manus, LinkedIn, Telegram, Antigravity, HeyGen, Snapchat et Figma.</p>
<h2>Prix vérifiés et guides EuroMalin</h2>
<div class="responsive-table"><table><thead><tr><th>Service</th><th>Prix relevé</th><th>Environ en euros</th><th>Catégorie</th></tr></thead><tbody>{rows}</tbody></table></div>
<div class="warning-box"><strong>Lecture correcte :</strong> les montants sont des instantanés. Ils peuvent correspondre à une durée, un compte ou une méthode de livraison particulière. Cliquez sur le guide avant de comparer.</div>
<h2>Les autres offres désormais visibles</h2>
<h3>Streaming et abonnements</h3><p>YouTube Premium, Crunchyroll, FOX One, Netflix, Disney+, HBO Max, Spotify et Prime Video apparaissent via offre directe ou marketplace selon le produit.</p>
<h3>IA et logiciels</h3><p>ChatGPT, Gemini, Genspark, Suno, Grok, Perplexity, Cursor, Kling AI, Runway, Midjourney, Poe, CapCut, Canva, Filmora, UPDF et WPS couvrent désormais une grande partie des usages créatifs et professionnels.</p>
<h3>Gaming</h3><p>GamsGo affiche des recharges, comptes, objets, cartes cadeaux et monnaies pour Pokémon GO, Genshin Impact, Fortnite, Roblox, Valorant, EA Sports FC, PUBG Mobile et de nombreux autres jeux.</p>
<h2>Comment nous vérifions un prix</h2><ol><li>Lecture de la page publique du produit.</li><li>Conservation du prix d’origine en dollars.</li><li>Conversion au taux BCE du 24 juillet 2026.</li><li>Exclusion du code promo et des frais du titre.</li><li>Contrôle du mode d’accès et des conditions de protection.</li></ol>
<h2>Questions fréquentes</h2><div class="faq">{''.join(f'<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>' for q, a in faq)}</div>
<h2>Sources</h2><p>Veille réalisée à partir du <a href="{GAMSGO_CATALOG}" target="_blank" rel="noopener noreferrer">catalogue GamsGo</a>, du <a href="https://www.gamsgo.com/top-up" target="_blank" rel="noopener noreferrer">centre de recharges et de ses menus publics</a>, des <a href="{GAMSGO_PROTECTION}" target="_blank" rel="noopener noreferrer">règles vendeurs et DealShield</a>, et du <a href="{ECB_SOURCE}" target="_blank" rel="noopener noreferrer">taux BCE</a>.</p>
<div class="platform-card platform-card--gamsgo"><span class="platform-card__eyebrow">Lien partenaire</span><h3>Vérifier le catalogue actuel</h3><p>Testez le code <code>{GAMSGO_CODE}</code>, puis comparez toujours le total et la protection.</p><a class="btn btn-primary" href="{GAMSGO_URL}" target="_blank" rel="sponsored noopener noreferrer">Ouvrir GamsGo →</a></div>
</article><aside class="sidebar"><div class="sidebar-card"><div class="kicker">Avis</div><h3>GamsGo est-il fiable ?</h3><a class="btn ghost" href="gamsgo-avis-2026.html">Lire l’avis actualisé</a></div><div class="sidebar-card"><div class="kicker">Comparatif</div><h3>U7BUY ou GamsGo ?</h3><a class="btn ghost" href="u7buy-vs-gamsgo.html">Voir le comparatif</a></div></aside></div></section></main>"""
        + footer(),
    )


def review_page() -> tuple[str, str, str]:
    slug = "gamsgo-avis-2026"
    title = "Avis GamsGo 2026 : prix, nouveautés, fiabilité et risques"
    description = (
        "Notre avis GamsGo actualisé en juillet 2026 : nouveaux abonnements, IA, logiciels, "
        "marketplace, prix vérifiés, DealShield, limites et précautions avant achat."
    )
    faq = [
        ("GamsGo est-il une boutique classique ?", "Pas entièrement. Le site combine produits directs et marketplace, avec des vendeurs et garanties qui peuvent différer."),
        ("Les comptes partagés sont-ils sans risque ?", "Non. Ils peuvent être limités par les règles du fournisseur, la région, le foyer ou le contrôle de l’e-mail."),
        ("Quelle garantie est annoncée ?", "Les règles vendeurs indiquent une protection DealShield de 5 à 90 jours pour les abonnements numériques selon leur durée."),
        (f"Faut-il utiliser le code {GAMSGO_CODE} ?", "Vous pouvez le tester au panier, mais vérifiez la remise et le total plutôt que de supposer un pourcentage fixe."),
    ]
    return (
        slug,
        title,
        head(title, description, slug, faq)
        + header()
        + f"""<main id="main"><section class="hero-mini"><div class="container"><div class="breadcrumbs"><a href="../index.html">Accueil</a> · <a href="../articles.html">Articles</a> · Avis</div><div class="hero-card"><div class="eyebrow">Avis actualisé • 24 juillet 2026</div><h1>{esc(title)}</h1><p class="lead">{esc(description)}</p></div></div></section>
<section class="section"><div class="container page-grid"><article class="hero-card article">{disclosure()}
<div class="fact-strip"><div><strong>Direct + marketplace</strong><span>deux modes d’achat</span></div><div><strong>5 à 90 jours</strong><span>DealShield selon produit</span></div><div><strong>{GAMSGO_CODE}</strong><span>à tester au panier</span></div></div>
<h2>Notre avis en bref</h2><div class="verdict-box"><span class="verdict-box__label">Verdict</span><p>GamsGo est devenu un catalogue très large et peut proposer de vrais écarts de prix. Son intérêt dépend toutefois du produit : une offre directe bien décrite est plus simple à évaluer qu’un compte marketplace. Pour les données sensibles ou un usage professionnel, l’abonnement officiel personnel reste le meilleur repère.</p></div>
<h2>Les points forts</h2><ul class="check-list"><li>Catalogue actuel couvrant streaming, IA, logiciels et gaming.</li><li>Prix publics visibles sur plusieurs pages directes.</li><li>Protection et messagerie centralisées.</li><li>Formats variés : recharge, invitation, compte, profil ou marketplace.</li><li>Support et règles vendeurs publiés.</li></ul>
<h2>Les limites</h2><ul><li>Le format d’accès change selon le produit.</li><li>Les prix peuvent varier par pays, durée et devise.</li><li>Un compte partagé peut enfreindre les règles du fournisseur.</li><li>La protection n’est pas identique pour toutes les commandes.</li><li>Un vendeur peut conserver le contrôle de l’e-mail ou du compte.</li></ul>
<h2>Exemples de prix vérifiés</h2><div class="responsive-table"><table><thead><tr><th>Produit</th><th>Prix GamsGo</th><th>Environ en euros</th></tr></thead><tbody>{''.join(f'<tr><td><a href="{p.slug}.html">{esc(p.plan)}</a></td><td>{p.price_usd:.2f} $</td><td>{p.price_eur} €</td></tr>' for p in PRODUCTS[:10])}</tbody></table></div>
<h2>Ce que DealShield couvre</h2><p>Les règles publiques destinées aux vendeurs d’abonnements numériques annoncent une période de protection de 5 à 90 jours selon la durée d’usage. Un compte devenu inutilisable, annulé ou récupéré pendant cette période peut donner lieu à annulation et remboursement. La fiche de la commande reste toutefois la référence concrète.</p>
<h2>Notre méthode avant achat</h2><ol><li>Identifier si GamsGo vend directement ou héberge un vendeur.</li><li>Vérifier région, durée, plan et contrôle du compte.</li><li>Comparer le prix final avec l’offre officielle et U7BUY.</li><li>Conserver la fiche et les échanges.</li><li>Tester immédiatement sans confirmer trop tôt.</li></ol>
<h2>Questions fréquentes</h2><div class="faq">{''.join(f'<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>' for q, a in faq)}</div>
<h2>Sources</h2><p><a href="{GAMSGO_CATALOG}" target="_blank" rel="noopener noreferrer">Catalogue GamsGo</a>, <a href="{GAMSGO_PROTECTION}" target="_blank" rel="noopener noreferrer">règles vendeurs et DealShield</a>, et pages produit contrôlées le 24 juillet 2026.</p>
<div class="platform-card platform-card--gamsgo"><span class="platform-card__eyebrow">Lien partenaire</span><h3>Comparer le panier</h3><p>Testez le code <code>{GAMSGO_CODE}</code> sans supposer qu’il s’applique partout.</p><a class="btn btn-primary" href="{GAMSGO_URL}" target="_blank" rel="sponsored noopener noreferrer">Voir GamsGo →</a></div>
</article><aside class="sidebar"><div class="sidebar-card"><div class="kicker">Nouveautés</div><h3>Prix et nouveaux services</h3><a class="btn ghost" href="gamsgo-nouveautes-prix-2026.html">Voir le dossier</a></div></aside></div></section></main>"""
        + footer(),
    )


def subscriptions_page() -> tuple[str, str, str]:
    slug = "gamsgo-abonnements-moins-cher"
    title = "Comment payer ses abonnements moins cher avec GamsGo en 2026 ?"
    description = (
        "Guide GamsGo 2026 pour payer moins cher streaming, IA et logiciels : prix datés, "
        "méthodes d’accès, code WPQTU, DealShield et checklist avant commande."
    )
    faq = [
        ("Quel abonnement tester en premier ?", "Choisissez un service non sensible, sur une courte durée, avec une méthode d’accès et une protection clairement décrites."),
        ("Faut-il choisir le prix le plus bas ?", "Non. Comparez la durée, le plan, la région, le contrôle du compte et la garantie avant le montant."),
        ("Peut-on utiliser son propre compte ?", "Certaines offres fonctionnent par recharge ou invitation, d’autres livrent de nouveaux identifiants. La fiche doit le préciser."),
        ("Comment limiter les risques ?", "N’utilisez aucun mot de passe réemployé, aucune donnée confidentielle et conservez toutes les preuves dans la plateforme."),
    ]
    groups = {
        "Streaming": [p for p in PRODUCTS if p.category == "Streaming"],
        "IA et création": [p for p in PRODUCTS if "IA" in p.category or p.category == "Vidéo IA"],
        "Logiciels": [p for p in PRODUCTS if p.category == "Logiciel"],
    }
    group_html = "".join(
        f"<h3>{esc(label)}</h3><ul>"
        + "".join(f'<li><a href="{p.slug}.html">{esc(p.plan)}</a> : environ {p.price_eur} €</li>' for p in items)
        + "</ul>"
        for label, items in groups.items()
    )
    return (
        slug,
        title,
        head(title, description, slug, faq)
        + header()
        + f"""<main id="main"><section class="hero-mini"><div class="container"><div class="breadcrumbs"><a href="../index.html">Accueil</a> · <a href="../articles.html">Articles</a> · Économies</div><div class="hero-card"><div class="eyebrow">Guide pratique • juillet 2026</div><h1>{esc(title)}</h1><p class="lead">{esc(description)}</p></div></div></section>
<section class="section"><div class="container page-grid"><article class="hero-card article">{disclosure()}
<h2>La méthode EuroMalin</h2><div class="verdict-box"><span class="verdict-box__label">En bref</span><p>Commencez par une courte durée, un service sans données sensibles et une fiche qui précise clairement ce qui est livré. Le prix vient ensuite : un accès mal décrit n’est pas une économie.</p></div>
<h2>Les guides avec prix actualisés</h2>{group_html}
<h2>Comment payer moins sans acheter le mauvais produit</h2><ol><li>Décidez si vous acceptez un profil partagé, une invitation ou seulement un compte privé.</li><li>Ouvrez le guide EuroMalin correspondant et lisez le risque spécifique.</li><li>Comparez le tarif GamsGo au prix officiel et à U7BUY.</li><li>Testez le code <code>{GAMSGO_CODE}</code> au panier.</li><li>Contrôlez les frais, la devise et DealShield.</li><li>Testez l’accès immédiatement et conservez les preuves.</li></ol>
<h2>Les erreurs coûteuses</h2><ul><li>Confondre prix mensuel et prix total d’une durée différente.</li><li>Utiliser un compte partagé pour des fichiers clients ou des e-mails.</li><li>Ignorer la région et les règles de foyer.</li><li>Payer en dehors de la plateforme.</li><li>Confirmer avant d’avoir testé toutes les fonctions importantes.</li></ul>
<div class="warning-box"><strong>À retenir :</strong> les prix affichés dans les titres sont des conversions datées. Le panier reste la seule référence pour le montant réellement débité.</div>
<h2>Questions fréquentes</h2><div class="faq">{''.join(f'<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>' for q, a in faq)}</div>
<h2>Sources</h2><p><a href="{GAMSGO_CATALOG}" target="_blank" rel="noopener noreferrer">Catalogue GamsGo</a>, pages produit, <a href="{GAMSGO_PROTECTION}" target="_blank" rel="noopener noreferrer">règles DealShield</a> et <a href="{ECB_SOURCE}" target="_blank" rel="noopener noreferrer">taux BCE</a>, contrôlés le 24 juillet 2026.</p>
<div class="platform-card platform-card--gamsgo"><span class="platform-card__eyebrow">Lien partenaire</span><h3>Vérifier les prix actuels</h3><a class="btn btn-primary" href="{GAMSGO_URL}" target="_blank" rel="sponsored noopener noreferrer">Ouvrir GamsGo →</a></div>
</article><aside class="sidebar"><div class="sidebar-card"><div class="kicker">Veille</div><h3>Nouveautés GamsGo</h3><a class="btn ghost" href="gamsgo-nouveautes-prix-2026.html">Voir le catalogue</a></div></aside></div></section></main>"""
        + footer(),
    )


def remove_cards(text: str, slugs: list[str]) -> str:
    for slug in slugs:
        text = re.sub(
            rf'<article class="article-card"[^>]*>(?:(?!</article>).)*?href="articles/{re.escape(slug)}\.html"(?:(?!</article>).)*?</article>',
            "",
            text,
            flags=re.S,
        )
    return text


def update_indexes(generated: list[tuple[str, str, str, str]]) -> None:
    slugs = [slug for slug, _, _, _ in generated]
    index_path = ROOT / "articles.html"
    text = index_path.read_text(encoding="utf-8")
    text = re.sub(r"<!-- GAMSGO-PRICES:START -->.*?<!-- GAMSGO-PRICES:END -->", "", text, flags=re.S)
    text = remove_cards(text, slugs)
    block = (
        "<!-- GAMSGO-PRICES:START -->"
        + "".join(card(slug, title, description, category) for slug, title, description, category in generated)
        + "<!-- GAMSGO-PRICES:END -->"
    )
    text = text.replace('<div class="grid-3">', '<div class="grid-3">' + block, 1)
    total = len(list(ARTICLES.glob("*.html")))
    text = re.sub(r"\d+ articles déjà intégrés", f"{total} articles déjà intégrés", text)
    index_path.write_text(text, encoding="utf-8")

    economy_path = ROOT / "economies.html"
    text = economy_path.read_text(encoding="utf-8")
    text = re.sub(r"<!-- GAMSGO-PRICES:START -->.*?<!-- GAMSGO-PRICES:END -->", "", text, flags=re.S)
    text = remove_cards(text, slugs)
    featured = generated[:1] + [
        next(item for item in generated if item[0] == "payer-genspark-plus-moins-cher"),
        next(item for item in generated if item[0] == "payer-suno-pro-moins-cher"),
        next(item for item in generated if item[0] == "payer-hbo-max-moins-cher"),
    ]
    block = (
        "<!-- GAMSGO-PRICES:START -->"
        + "".join(card(slug, title, description, category) for slug, title, description, category in featured)
        + "<!-- GAMSGO-PRICES:END -->"
    )
    text = text.replace('<div class="grid-3">', '<div class="grid-3">' + block, 1)
    economy_path.write_text(text, encoding="utf-8")


def update_sitemap(slugs: list[str]) -> None:
    path = ROOT / "sitemap.xml"
    text = path.read_text(encoding="utf-8")
    for slug in slugs:
        loc = f"https://euromalin.com/articles/{slug}.html"
        pattern = rf"(<loc>{re.escape(loc)}</loc>\s*<lastmod>)[^<]+(</lastmod>)"
        if re.search(pattern, text):
            text = re.sub(pattern, rf"\g<1>{TODAY}\g<2>", text)
        else:
            entry = (
                "\n  <url>\n"
                f"    <loc>{loc}</loc>\n"
                f"    <lastmod>{TODAY}</lastmod>\n"
                "    <changefreq>monthly</changefreq>\n"
                "    <priority>0.8</priority>\n"
                "  </url>\n"
            )
            text = text.replace("</urlset>", entry + "</urlset>")
    path.write_text(text, encoding="utf-8")


def write_manifest(generated: list[tuple[str, str, str, str]]) -> None:
    queries = {item.slug: item.cover_query for item in PRODUCTS}
    queries["gamsgo-nouveautes-prix-2026"] = "streaming subscriptions artificial intelligence"
    manifest = ROOT / "scripts" / "gamsgo_cover_queries.json"
    manifest.write_text(json.dumps(queries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    generated: list[tuple[str, str, str, str]] = []
    for item in PRODUCTS:
        write_article_preserving_hero(ARTICLES / f"{item.slug}.html", product_page(item))
        generated.append((item.slug, item.title, item.description, "Prix GamsGo"))

    for builder, category in [
        (hub_page, "Nouveautés"),
        (review_page, "Avis"),
        (subscriptions_page, "Économies"),
    ]:
        slug, title, content = builder()
        write_article_preserving_hero(ARTICLES / f"{slug}.html", content)
        description = re.search(r'<meta name="description" content="([^"]+)"', content).group(1)
        generated.append((slug, title, description, category))

    # Put the catalog hub first in listings.
    generated.sort(key=lambda item: (item[0] != "gamsgo-nouveautes-prix-2026", item[0]))
    update_indexes(generated)
    update_sitemap([slug for slug, _, _, _ in generated])
    write_manifest(generated)
    print(f"Generated {len(generated)} GamsGo price and catalog pages.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
