#!/usr/bin/env python3
"""Generate the U7BUY/GamsGo editorial cluster for EuroMalin.

The generated pages intentionally avoid volatile price promises. They explain
marketplace mechanics, provider-policy risks, refund limits and affiliate
tracking in plain French while keeping the site's existing static HTML style.
"""

from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.parse import quote


ROOT = Path(__file__).resolve().parent.parent
ARTICLES = ROOT / "articles"
TODAY = date(2026, 7, 24).isoformat()
U7_BASE = "https://www.u7buy.com"
U7_REFERRAL = "CzMdAgd4"
U7_CODE = "EURO10"
GAMSGO_URL = "https://www.gamsgo.com/partner/Px5AZ"
GAMSGO_CODE = "WPQTU"


@dataclass(frozen=True)
class Subscription:
    slug: str
    service: str
    plan: str
    u7_path: str
    gamsgo_status: str
    angle: str
    specific_risk: str
    official_url: str
    official_label: str
    cover_query: str

    @property
    def title(self) -> str:
        if self.service == "IPTV":
            return "IPTV sur U7BUY : avis, légalité et vérifications avant achat"
        return f"{self.plan} moins cher en 2026 : U7BUY ou GamsGo ?"

    @property
    def description(self) -> str:
        if self.service == "IPTV":
            return (
                "IPTV sur U7BUY : comment vérifier les droits de diffusion, le vendeur, "
                "la compatibilité et les conditions de remboursement avant de payer."
            )
        return (
            f"{self.plan} moins cher : comparez U7BUY et GamsGo, le code {U7_CODE} "
            "(-5 % sur les commandes éligibles), les formats d’accès et les risques."
        )

    @property
    def u7_url(self) -> str:
        return f"{U7_BASE}{self.u7_path}?referral-code={U7_REFERRAL}"


SUBSCRIPTIONS = [
    Subscription(
        "iptv-u7buy-avis",
        "IPTV",
        "IPTV",
        "/iptv/iptv-accounts",
        "Aucune rubrique IPTV clairement visible dans le catalogue GamsGo consulté.",
        "des bouquets de télévision sur internet dont les droits peuvent varier selon le vendeur",
        "Un prix très bas ou un catalogue mondial ne prouve pas que le vendeur possède les droits de diffusion. Privilégiez les services identifiables et autorisés dans votre pays.",
        "https://www.arcom.fr/television-et-video-la-demande/proteger-la-creation/les-offres-legales",
        "ARCOM — offres légales",
        "legal television streaming remote control",
    ),
    Subscription(
        "payer-chatgpt-plus-moins-cher",
        "ChatGPT",
        "ChatGPT Plus",
        "/chatgpt/chatgpt-accounts",
        "ChatGPT est visible dans la rubrique IA de GamsGo.",
        "des comptes privés, partagés, des upgrades et parfois des sièges d’espace de travail",
        "N’envoyez jamais de documents professionnels, de mots de passe ou de données personnelles dans un compte partagé ou administré par un tiers.",
        "https://chatgpt.com/pricing/",
        "Tarifs officiels ChatGPT",
        "artificial intelligence laptop privacy",
    ),
    Subscription(
        "payer-netflix-premium-moins-cher",
        "Netflix",
        "Netflix Premium",
        "/netflix/netflix-accounts",
        "Netflix est visible dans la marketplace GamsGo.",
        "des profils ou comptes de streaming, privés ou partagés selon l’annonce",
        "Netflix applique des règles de foyer. Un accès vendu hors du foyer peut cesser de fonctionner ou demander une vérification supplémentaire.",
        "https://help.netflix.com/node/123277",
        "Règles Netflix sur le foyer",
        "television streaming living room",
    ),
    Subscription(
        "payer-youtube-premium-moins-cher",
        "YouTube",
        "YouTube Premium",
        "/youtube-premium/youtube-premium-accounts",
        "YouTube est visible dans la rubrique SVOD de GamsGo.",
        "des comptes, invitations ou accès Premium dont la région et la durée varient",
        "Les groupes famille YouTube imposent des conditions de foyer et de pays. Vérifiez le mode d’accès plutôt que de supposer qu’il s’agit d’un abonnement officiel individuel.",
        "https://support.google.com/youtube/answer/7507349?hl=fr",
        "Aide YouTube — forfait famille",
        "video streaming creator laptop",
    ),
    Subscription(
        "payer-nordvpn-moins-cher",
        "NordVPN",
        "NordVPN",
        "/nordvpn/nordvpn-accounts",
        "GamsGo affiche plusieurs VPN, mais NordVPN n’était pas nommé clairement dans le catalogue consulté.",
        "des identifiants VPN fournis par un vendeur, avec durée et contrôle du compte variables",
        "Un VPN protège le transport, pas un compte partagé. Si un tiers contrôle l’e-mail ou le mot de passe, il contrôle aussi votre accès.",
        "https://my.nordaccount.com/legal/terms-of-service/",
        "Conditions officielles NordVPN",
        "cybersecurity vpn laptop lock",
    ),
    Subscription(
        "payer-crunchyroll-moins-cher",
        "Crunchyroll",
        "Crunchyroll Premium",
        "/crunchyroll/crunchyroll-accounts",
        "Crunchyroll est visible dans les rubriques SVOD et marketplace de GamsGo.",
        "des comptes de streaming d’anime avec région, formule et nombre d’écrans variables",
        "Contrôlez la région, les écrans simultanés et la possibilité de modifier le profil sans perturber d’autres utilisateurs.",
        "https://www.crunchyroll.com/terms",
        "Conditions officielles Crunchyroll",
        "anime television streaming",
    ),
    Subscription(
        "payer-amazon-prime-video-moins-cher",
        "Prime Video",
        "Amazon Prime Video",
        "/amazon-prime-video/amazon-prime-video-accounts",
        "Prime Video est visible dans la marketplace GamsGo.",
        "des comptes ou accès vidéo distincts d’un abonnement Amazon Prime personnel",
        "Évitez tout compte rattaché à des moyens de paiement, commandes ou données personnelles d’un tiers. Vérifiez que l’accès est limité à Prime Video.",
        "https://www.primevideo.com/help",
        "Aide officielle Prime Video",
        "home cinema television popcorn",
    ),
    Subscription(
        "payer-gemini-advanced-moins-cher",
        "Gemini",
        "Gemini Advanced",
        "/gemini/accounts",
        "Gemini est visible dans la rubrique IA de GamsGo.",
        "des comptes Google ou accès IA dont le propriétaire, la région et le stockage peuvent varier",
        "Un compte Google peut contenir e-mails, fichiers et données sensibles. Préférez un accès dédié et n’y ajoutez jamais vos moyens de récupération personnels sans en comprendre le contrôle.",
        "https://policies.google.com/terms?hl=fr",
        "Conditions d’utilisation Google",
        "artificial intelligence smartphone laptop",
    ),
    Subscription(
        "payer-xbox-game-pass-moins-cher",
        "Xbox",
        "Xbox Game Pass",
        "/xbox-live/xbox-live-accounts",
        "Xbox est visible dans la rubrique jeux de GamsGo.",
        "des comptes Xbox et accès Game Pass avec région, plateforme et durée variables",
        "Vérifiez si l’accès est un code, un compte complet ou une méthode de partage. Les trois n’offrent pas le même contrôle ni le même niveau de risque.",
        "https://www.microsoft.com/servicesagreement",
        "Contrat de services Microsoft",
        "gaming controller television",
    ),
    Subscription(
        "payer-claude-pro-moins-cher",
        "Claude",
        "Claude Pro",
        "/claude/accounts",
        "Claude est visible dans la marketplace GamsGo.",
        "des comptes IA privés ou partagés dont les limites et la récupération diffèrent",
        "Ne traitez aucune information confidentielle dans un compte vendeur ou partagé. Les conversations et limites d’usage peuvent être visibles ou consommées par d’autres.",
        "https://www.anthropic.com/legal/consumer-terms",
        "Conditions consommateurs Anthropic",
        "artificial intelligence writing laptop",
    ),
    Subscription(
        "payer-perplexity-pro-moins-cher",
        "Perplexity",
        "Perplexity Pro",
        "/perplexity-ai/accounts",
        "Perplexity AI est visible dans les rubriques IA et marketplace de GamsGo.",
        "des comptes de recherche IA privés ou partagés, avec limites et durée variables",
        "Les recherches, fichiers et espaces peuvent contenir des informations privées. Un compte partagé ne convient pas à un usage professionnel sensible.",
        "https://www.perplexity.ai/hub/legal/terms-of-service",
        "Conditions officielles Perplexity",
        "artificial intelligence search research",
    ),
    Subscription(
        "payer-apple-tv-plus-moins-cher",
        "Apple TV+",
        "Apple TV+",
        "/apple-tv/accounts",
        "GamsGo affiche une rubrique Apple ; le produit exact doit être vérifié au moment de l’achat.",
        "des comptes Apple TV+ dont la région, la durée et l’accès à l’identifiant Apple varient",
        "Un identifiant Apple peut donner accès à des données et achats. N’utilisez pas un compte tiers comme compte principal de votre appareil.",
        "https://www.apple.com/legal/internet-services/itunes/fr/terms.html",
        "Conditions des services multimédias Apple",
        "television streaming apple remote",
    ),
    Subscription(
        "payer-apple-one-moins-cher",
        "Apple One",
        "Apple One",
        "/apple-one/accounts",
        "GamsGo affiche une rubrique Apple ; Apple One doit être confirmé dans l’offre.",
        "des accès groupés Apple dont les services inclus et le contrôle du compte varient",
        "Apple One peut regrouper stockage, musique et vidéo. Un compte contrôlé par un tiers augmente le risque de perte d’accès et de confidentialité.",
        "https://www.apple.com/fr/apple-one/",
        "Présentation officielle Apple One",
        "apple devices music television",
    ),
    Subscription(
        "payer-apple-music-moins-cher",
        "Apple Music",
        "Apple Music",
        "/apple-music/accounts",
        "GamsGo affiche Apple dans sa rubrique musique ; vérifiez la formule exacte.",
        "des comptes ou accès musique, individuels ou liés à un groupe selon l’annonce",
        "Ne rattachez pas votre photothèque, vos cartes ou vos sauvegardes à un identifiant Apple fourni par un vendeur.",
        "https://www.apple.com/fr/apple-music/",
        "Présentation officielle Apple Music",
        "headphones music smartphone",
    ),
    Subscription(
        "payer-spotify-premium-moins-cher",
        "Spotify",
        "Spotify Premium",
        "/spotify/spotify-accounts",
        "Spotify n’était pas visible dans le catalogue GamsGo consulté le 24 juillet 2026.",
        "des comptes ou places Premium dont la région, la formule et la récupération varient",
        "Les formules Duo et Famille imposent des conditions d’adresse. Un compte partagé peut aussi exposer l’historique d’écoute et les playlists.",
        "https://www.spotify.com/fr/legal/end-user-agreement/",
        "Conditions d’utilisation Spotify",
        "headphones music listening",
    ),
]


@dataclass(frozen=True)
class ServiceGuide:
    slug: str
    title: str
    u7_path: str
    count: str
    gamsgo: str
    summary: str
    examples: str
    risk: str
    checks: tuple[str, ...]
    cover_query: str

    @property
    def description(self) -> str:
        return (
            f"Guide U7BUY {self.title.lower()} : fonctionnement, comparaison GamsGo, "
            f"code {U7_CODE}, vérifications vendeur, risques et remboursement."
        )

    @property
    def u7_url(self) -> str:
        return f"{U7_BASE}{self.u7_path}?referral-code={U7_REFERRAL}"


SERVICE_GUIDES = [
    ServiceGuide(
        "u7buy-top-up-jeux",
        "Top up et recharges de jeux",
        "/game-top-up",
        "75 catégories affichées",
        "GamsGo propose aussi des recharges de jeux.",
        "acheter directement une recharge pour un identifiant de joueur ou une région donnée",
        "Genshin Impact, Honkai: Star Rail, Pokémon GO, Fortnite, PUBG Mobile ou Roblox",
        "Une recharge livrée sur le mauvais identifiant est généralement difficile à récupérer.",
        (
            "copier l’identifiant joueur sans le retaper",
            "confirmer le serveur et la région",
            "comparer le total avec les boutiques officielles",
            "ne jamais payer hors de la plateforme",
        ),
        "mobile gaming top up smartphone",
    ),
    ServiceGuide(
        "u7buy-objets-jeux-items",
        "Objets et items de jeux",
        "/game-items",
        "131 catégories affichées",
        "GamsGo possède également une rubrique objets.",
        "comparer des annonces vendeur pour des objets échangeables ou livrés en jeu",
        "Roblox, Fortnite, Adopt Me, Blox Fruits, ARC Raiders ou Diablo",
        "La revente contre argent réel peut être limitée par les règles du jeu et exposer le compte à une sanction.",
        (
            "lire la méthode de livraison avant de payer",
            "vérifier la note et les commandes terminées",
            "garder les échanges dans la messagerie de commande",
            "prendre des captures avant de confirmer la réception",
        ),
        "fantasy video game inventory",
    ),
    ServiceGuide(
        "u7buy-comptes-jeux",
        "Comptes de jeux",
        "/game-accounts-for-sale",
        "134 catégories affichées",
        "GamsGo possède une marketplace de comptes de jeux.",
        "acheter un compte existant avec progression, personnages ou inventaire",
        "Fortnite, Roblox, GTA 5, Valorant, Minecraft ou Genshin Impact",
        "Le propriétaire initial peut parfois récupérer un compte. Les règles de nombreux jeux interdisent aussi la vente de comptes.",
        (
            "exiger le contrôle complet de l’e-mail de récupération",
            "vérifier la région et la plateforme",
            "ne pas modifier le compte avant d’avoir contrôlé l’annonce",
            "lire la durée exacte de la garantie vendeur",
        ),
        "gaming account computer setup",
    ),
    ServiceGuide(
        "u7buy-coins-monnaies-jeux",
        "Coins et monnaies de jeux",
        "/game-coins",
        "51 catégories affichées",
        "GamsGo référence aussi plusieurs monnaies de jeux.",
        "recevoir une monnaie via transfert, achat d’objet, échange ou recharge",
        "FC, Roblox, GTA Online, Albion Online ou Path of Exile",
        "Les transferts de monnaie peuvent déclencher des contrôles antifraude ou violer les règles de l’éditeur.",
        (
            "choisir la méthode de livraison la moins intrusive",
            "éviter les volumes anormalement élevés",
            "demander si le risque de sanction a été signalé",
            "conserver les preuves de livraison",
        ),
        "video game coins controller",
    ),
    ServiceGuide(
        "u7buy-boosting-jeux",
        "Boosting et montée de rang",
        "/game-boosting",
        "58 catégories affichées",
        "Le boosting n’était pas une rubrique clairement mise en avant chez GamsGo.",
        "payer un joueur pour atteindre un rang, gagner des matchs ou terminer un objectif",
        "GTA Online, Valorant, FC, Fortnite ou jeux compétitifs",
        "Le boosting implique souvent le partage de compte et peut entraîner une sanction, une perte de rang ou une compromission.",
        (
            "privilégier les prestations sans partage de mot de passe",
            "changer le mot de passe après la prestation",
            "activer l’authentification à deux facteurs",
            "refuser tout logiciel tiers ou automatisation",
        ),
        "esports competitive gaming keyboard",
    ),
    ServiceGuide(
        "u7buy-roblox",
        "Roblox : items, comptes et Robux",
        "/roblox",
        "86 expériences affichées",
        "GamsGo référence également Roblox dans plusieurs rubriques.",
        "chercher des objets, comptes, pass ou monnaies liés à des expériences Roblox",
        "Grow a Garden, Steal a Brainrot, Blox Fruits, Adopt Me ou Pet Simulator",
        "Roblox est très utilisé par des mineurs : évitez les échanges privés, les liens externes et toute demande de mot de passe.",
        (
            "utiliser le contrôle parental si l’acheteur est mineur",
            "ne jamais communiquer de code de connexion",
            "vérifier que l’objet est réellement échangeable",
            "rester dans la commande et la messagerie officielles",
        ),
        "child playing video game colorful",
    ),
    ServiceGuide(
        "u7buy-cartes-cadeaux-cles-jeux",
        "Cartes cadeaux, clés et points",
        "/gift-cards",
        "catalogue variable",
        "GamsGo affiche des cartes cadeaux Apple, Xbox, PlayStation, Nintendo et jeux.",
        "acheter un code numérique ou un crédit à activer sur une boutique",
        "Apple, Xbox, PlayStation, Nintendo eShop, Roblox ou Valorant",
        "Le catalogue U7BUY affichait zéro résultat sur certaines pages lors de notre contrôle. Vérifiez la disponibilité réelle et n’achetez jamais un code d’une mauvaise région.",
        (
            "contrôler la devise et le pays d’activation",
            "vérifier si le code est neuf et non remboursable",
            "filmer ou capturer l’ouverture de la commande",
            "activer rapidement le code sans confirmer avant le test",
        ),
        "gift card gaming controller",
    ),
]


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def json_ld(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def u7_url(path: str = "/") -> str:
    return f"{U7_BASE}{path}?referral-code={U7_REFERRAL}"


def head(title: str, description: str, slug: str, faq: list[tuple[str, str]]) -> str:
    canonical = f"https://euromalin.com/articles/{slug}.html"
    image = f"https://euromalin.com/assets/img/articles/{slug}.jpg"
    article_schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": description,
        "datePublished": TODAY,
        "dateModified": TODAY,
        "author": {"@type": "Organization", "name": "EuroMalin"},
        "publisher": {
            "@type": "Organization",
            "name": "EuroMalin",
            "url": "https://euromalin.com",
        },
        "image": image,
        "mainEntityOfPage": canonical,
    }
    breadcrumb_schema = {
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
                "name": "Articles",
                "item": "https://euromalin.com/articles.html",
            },
            {
                "@type": "ListItem",
                "position": 3,
                "name": title,
                "item": canonical,
            },
        ],
    }
    faq_schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": question,
                "acceptedAnswer": {"@type": "Answer", "text": answer},
            }
            for question, answer in faq
        ],
    }
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{esc(title)} • EuroMalin</title>
<meta name="description" content="{esc(description)}"/>
<meta name="robots" content="index,follow,max-snippet:-1,max-image-preview:large"/>
<meta name="author" content="EuroMalin"/>
<meta name="theme-color" content="#0f2d40" media="(prefers-color-scheme: light)"/>
<meta name="theme-color" content="#0d141c" media="(prefers-color-scheme: dark)"/>
<meta name="color-scheme" content="light dark"/>
<meta property="og:type" content="article"/>
<meta property="og:site_name" content="EuroMalin"/>
<meta property="og:title" content="{esc(title)}"/>
<meta property="og:description" content="{esc(description)}"/>
<meta property="og:url" content="{canonical}"/>
<meta property="og:image" content="{image}"/>
<meta property="og:locale" content="fr_FR"/>
<meta name="twitter:card" content="summary_large_image"/>
<meta name="twitter:title" content="{esc(title)}"/>
<meta name="twitter:description" content="{esc(description)}"/>
<link rel="canonical" href="{canonical}"/>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Manrope:wght@400;500;700;800&display=swap" rel="stylesheet"/>
<link rel="stylesheet" href="../assets/style.css"/>
<link rel="icon" type="image/svg+xml" href="../assets/favicon.svg"/>
<script type="application/ld+json">{json_ld(article_schema)}</script>
<script type="application/ld+json">{json_ld(breadcrumb_schema)}</script>
<script type="application/ld+json">{json_ld(faq_schema)}</script>
<script>(function(){{try{{var t=localStorage.getItem('euromalin-theme');if(t==='light'||t==='dark')document.documentElement.setAttribute('data-theme',t);}}catch(e){{}}}})();</script>
<script defer src="../assets/tracking.js"></script>
</head>"""


def header() -> str:
    return """<body>
<a class="skip-link" href="#main">Aller au contenu</a>
<div class="scroll-progress" data-scroll-progress></div>
<header class="topbar"><div class="container nav">
<a class="brand" href="../index.html"><div class="brand-mark">€</div><div><div class="brand-title">EuroMalin</div><div class="brand-sub">Cashback, économies et budget malin</div></div></a>
<nav class="nav-links"><a href="../index.html">Accueil</a><a href="../articles.html">Articles</a><a href="../bons-plans.html">Bons Plans</a><a href="../cashback.html">Cashback</a><a href="../economies.html">Économies</a><a href="../budget.html">Budget</a><a href="../revenus.html">Revenus</a></nav>
<a class="btn" href="u7buy-vs-gamsgo.html">U7BUY vs GamsGo</a>
</div></header>"""


def footer() -> str:
    return """<footer class="footer"><div class="container footer-grid">
<div><div class="brand-title" style="font-size:1.3rem">EuroMalin</div><p>Des comparatifs clairs, des articles lisibles et des idées simples pour payer moins sans masquer les limites.</p></div>
<div><h3>Guides U7BUY</h3><div class="small-list"><a href="u7buy-vs-gamsgo.html">U7BUY ou GamsGo</a><a href="u7buy-avis-code-promo-euro10.html">Avis U7BUY et code EURO10</a><a href="u7buy-top-up-jeux.html">Recharges de jeux</a><a href="u7buy-comptes-jeux.html">Comptes de jeux</a></div></div>
<div><h3>À parcourir</h3><div class="small-list"><a href="../articles.html">Tous les articles</a><a href="../economies.html">Économies</a><a href="../privacy.html">Confidentialité</a><a href="../a-propos.html">À propos</a></div></div>
</div><div class="footer-bottom container"><span>© 2026 EuroMalin.</span><span>Liens affiliés signalés clairement.</span></div></footer>
<script src="../assets/affiliate-config.js" defer></script><script src="../assets/script.js" defer></script>
</body></html>"""


def disclosure() -> str:
    return (
        '<aside class="affiliate-disclosure">Cette page contient des liens affiliés U7BUY et '
        "GamsGo. EuroMalin peut recevoir une commission si vous achetez via ces liens, sans "
        "surcoût annoncé pour vous. Le classement reste fondé sur les usages, les risques et "
        "les conditions visibles lors de notre contrôle.</aside>"
    )


def dual_cta(u7_href: str, label: str) -> str:
    return f"""<div class="offer-duo">
<div class="platform-card platform-card--u7buy">
<span class="platform-card__eyebrow">U7BUY • code partenaire</span>
<h3>{esc(label)} sur U7BUY</h3>
<p>Comparez plusieurs annonces et saisissez <code>{U7_CODE}</code> pour <strong>5 % de remise supplémentaire</strong> sur les commandes éligibles. Vérifiez la remise avant de payer.</p>
<a class="btn btn-primary" href="{esc(u7_href)}" target="_blank" rel="sponsored noopener noreferrer">Voir les offres U7BUY →</a>
</div>
<div class="platform-card platform-card--gamsgo">
<span class="platform-card__eyebrow">GamsGo • alternative</span>
<h3>Comparer aussi GamsGo</h3>
<p>Le catalogue change selon le pays et la marketplace. Le code <code>{GAMSGO_CODE}</code> peut être testé au panier ; fiez-vous au total réellement affiché.</p>
<a class="btn ghost" href="{GAMSGO_URL}" target="_blank" rel="sponsored noopener noreferrer">Ouvrir GamsGo →</a>
</div>
</div>"""


def subscription_page(item: Subscription) -> str:
    faq = [
        (
            f"Le code {U7_CODE} fonctionne-t-il pour {item.plan} ?",
            f"Le code {U7_CODE} est annoncé par l’affilié comme offrant 5 % supplémentaires. "
            "Son éligibilité peut dépendre du produit, du vendeur ou d’une promotion. Vérifiez "
            "toujours la remise dans le récapitulatif avant paiement.",
        ),
        (
            f"U7BUY ou GamsGo : lequel choisir pour {item.plan} ?",
            "Choisissez l’annonce qui décrit clairement le type d’accès, la région, la durée, "
            "le contrôle de l’e-mail et la garantie. U7BUY est une marketplace très large ; "
            "GamsGo combine offres directes et marketplace selon le produit.",
        ),
        (
            "Un compte partagé est-il sans risque ?",
            "Non. Il peut exposer l’historique, les fichiers ou les limites d’usage à d’autres "
            "personnes et peut ne pas respecter les règles du fournisseur. N’y placez aucune "
            "donnée sensible.",
        ),
        (
            "Comment éviter un litige après achat ?",
            "Conservez l’annonce et les échanges, testez immédiatement l’accès, ne confirmez "
            "pas la réception avant vérification et restez dans la messagerie de la plateforme.",
        ),
    ]
    if item.service == "IPTV":
        verdict = (
            "Nous ne recommandons pas une offre IPTV uniquement parce qu’elle promet des milliers "
            "de chaînes. Vérifiez l’identité du fournisseur et ses droits de diffusion. Sans preuve "
            "claire, préférez une offre légale référencée par l’ARCOM."
        )
    else:
        verdict = (
            f"Pour {item.plan}, U7BUY est utile pour comparer des formats d’accès très différents. "
            "GamsGo mérite une comparaison uniquement si le produit exact et ses conditions sont "
            "visibles. Dans les deux cas, une offre privée avec contrôle de l’e-mail est préférable "
            "à un compte partagé lorsque la confidentialité compte."
        )
    return (
        head(item.title, item.description, item.slug, faq)
        + header()
        + f"""<main id="main">
<section class="hero-mini"><div class="container">
<div class="breadcrumbs"><a href="../index.html">Accueil</a> · <a href="../articles.html">Articles</a> · Abonnements</div>
<div class="hero-card">
<div class="eyebrow">Comparatif 2026 • mis à jour le 24 juillet</div>
<h1>{esc(item.title)}</h1>
<p class="lead">{esc(item.description)}</p>
</div></div></section>
<section class="section"><div class="container page-grid">
<article class="hero-card article">
{disclosure()}
<div class="fact-strip"><div><strong>U7BUY</strong><span>Marketplace, 15 abonnements listés</span></div><div><strong>{U7_CODE}</strong><span>-5 % si la commande est éligible</span></div><div><strong>Prix</strong><span>Variable selon vendeur, durée et région</span></div></div>
<h2>Le verdict en 30 secondes</h2>
<div class="verdict-box"><span class="verdict-box__label">Verdict EuroMalin</span><p>{esc(verdict)}</p></div>
{dual_cta(item.u7_url, item.plan)}
<h2>Ce qu’on achète réellement</h2>
<p>Sur U7BUY, {esc(item.angle)}. Ce n’est pas forcément le même produit que l’abonnement individuel acheté directement chez l’éditeur. L’annonce peut porter sur un compte privé, un compte partagé, une invitation, un upgrade ou un accès administré par un tiers.</p>
<p><strong>État du comparatif GamsGo :</strong> {esc(item.gamsgo_status)}</p>
<div class="responsive-table"><table>
<thead><tr><th>Critère</th><th>U7BUY</th><th>GamsGo</th><th>Officiel</th></tr></thead>
<tbody>
<tr><td>Modèle</td><td>Marketplace multi-vendeurs</td><td>Offres directes + marketplace</td><td>Abonnement de l’éditeur</td></tr>
<tr><td>Choix</td><td>Souvent très large</td><td>Variable selon la rubrique</td><td>Formules standardisées</td></tr>
<tr><td>Contrôle du compte</td><td>Dépend de l’annonce</td><td>Dépend du produit</td><td>Compte personnel</td></tr>
<tr><td>Risque de règle fournisseur</td><td>À vérifier</td><td>À vérifier</td><td>Le plus faible</td></tr>
<tr><td>Prix</td><td>Variable par vendeur</td><td>Variable par offre</td><td>Prix public</td></tr>
</tbody></table></div>
<h2>Code promo U7BUY {U7_CODE} : mode d’emploi</h2>
<ol>
<li>Ouvrez U7BUY via le <a href="{esc(item.u7_url)}" target="_blank" rel="sponsored noopener noreferrer">lien partenaire EuroMalin</a>.</li>
<li>Comparez le type d’accès, la région, la durée, la note et la garantie de plusieurs annonces.</li>
<li>Ajoutez l’offre choisie au panier puis saisissez <code>{U7_CODE}</code>.</li>
<li>Contrôlez que les 5 % supplémentaires apparaissent bien avant de confirmer le paiement.</li>
</ol>
<h2>Les risques à vérifier avant de payer</h2>
<div class="warning-box"><strong>Point spécifique à {esc(item.service)} :</strong> {esc(item.specific_risk)}</div>
<ul class="check-list">
<li><strong>Privé ou partagé :</strong> qui d’autre peut voir l’historique, les fichiers ou les profils ?</li>
<li><strong>Contrôle :</strong> pouvez-vous accéder à l’e-mail, changer le mot de passe et récupérer le compte ?</li>
<li><strong>Région :</strong> l’accès fonctionne-t-il en France ou en Belgique sans contournement ?</li>
<li><strong>Durée :</strong> quand commence-t-elle et que se passe-t-il si l’accès s’arrête avant ?</li>
<li><strong>Garantie :</strong> combien de temps le vendeur remplace-t-il ou rembourse-t-il l’accès ?</li>
<li><strong>Règles de l’éditeur :</strong> la revente, le partage hors foyer ou le transfert de compte sont-ils autorisés ?</li>
</ul>
<blockquote>Le moins cher n’est pas toujours le plus économique : un compte non récupérable ou remplacé plusieurs fois peut coûter plus cher en temps, en données et en stress.</blockquote>
<h2>Notre checklist d’achat</h2>
<ol>
<li>Lire l’annonce entière, y compris les restrictions et la méthode de livraison.</li>
<li>Choisir un vendeur avec historique, avis récents et conditions de garantie explicites.</li>
<li>Faire des captures de l’annonce et du délai annoncé.</li>
<li>Payer et échanger uniquement dans la plateforme.</li>
<li>Tester immédiatement toutes les fonctions importantes.</li>
<li>Ne confirmer la réception qu’après le test.</li>
<li>Ne jamais utiliser un compte partagé pour des données sensibles.</li>
</ol>
<h2>Prix : comparez le coût total, pas seulement le bandeau</h2>
<p>Les prix changent avec la durée, la région, les frais de paiement et le vendeur. EuroMalin ne fige donc pas un tarif qui peut devenir faux demain. Comparez le total après code, la durée réellement couverte, le type d’accès et la garantie. Un mois court est souvent préférable pour tester avant un engagement plus long.</p>
<h2>Questions fréquentes</h2>
<div class="faq">
{''.join(f'<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>' for q, a in faq)}
</div>
<h2>Sources et méthode</h2>
<p>Catalogue contrôlé le 24 juillet 2026. Consultez la <a href="{esc(item.u7_url)}" target="_blank" rel="sponsored noopener noreferrer">rubrique {esc(item.service)} de U7BUY</a>, la <a href="https://www.u7buy.com/help-center/articles/u7buy-trade-protect-for-buyer" target="_blank" rel="noopener noreferrer">protection acheteur U7BUY</a>, le <a href="https://www.gamsgo.com/accounts" target="_blank" rel="noopener noreferrer">catalogue GamsGo</a> et les <a href="{esc(item.official_url)}" target="_blank" rel="noopener noreferrer">{esc(item.official_label)}</a>. Les catalogues et conditions peuvent évoluer.</p>
{dual_cta(item.u7_url, item.plan)}
</article>
<aside class="sidebar">
<div class="sidebar-card"><div class="kicker">Comparatif central</div><h3>U7BUY ou GamsGo ?</h3><p>Abonnements, jeux, codes et risques comparés point par point.</p><a class="btn ghost" href="u7buy-vs-gamsgo.html">Voir le comparatif</a></div>
<div class="sidebar-card"><div class="kicker">Code partenaire</div><h3>{U7_CODE} = -5 %</h3><p>Sur les commandes U7BUY éligibles. Vérifiez la remise au panier.</p><a class="btn ghost" href="u7buy-avis-code-promo-euro10.html">Lire l’avis U7BUY</a></div>
</aside>
</div></section></main>"""
        + footer()
    )


def comparison_page() -> tuple[str, str, str]:
    slug = "u7buy-vs-gamsgo"
    title = "U7BUY ou GamsGo en 2026 : comparatif abonnements et gaming"
    description = (
        "U7BUY vs GamsGo : catalogue, abonnements, comptes, top up, protection acheteur, "
        f"risques et codes promo {U7_CODE} et {GAMSGO_CODE} comparés."
    )
    faq = [
        (
            "U7BUY ou GamsGo : lequel est le moins cher ?",
            "Il n’y a pas de gagnant permanent. Les prix dépendent du vendeur, du pays, du type "
            "d’accès, de la durée et des frais. Comparez le total final et la garantie.",
        ),
        (
            f"Quel est le code promo U7BUY ?",
            f"Le code partenaire {U7_CODE} annonce 5 % supplémentaires sur les commandes éligibles. "
            "Vérifiez son application dans le panier.",
        ),
        (
            "Les comptes vendus sont-ils officiels ?",
            "U7BUY et une partie de GamsGo fonctionnent comme des marketplaces tierces. Un compte "
            "peut être privé, partagé, administré par un vendeur ou fourni sous forme d’invitation. "
            "Ce n’est pas équivalent à un achat direct chez l’éditeur.",
        ),
        (
            "Quelle plateforme choisir pour les jeux ?",
            "U7BUY affiche davantage de catégories historiques, notamment boosting et Roblox. "
            "GamsGo propose aussi top up, comptes, objets, cartes cadeaux et monnaies.",
        ),
    ]
    rows = "".join(
        f"<tr><td><a href=\"{esc(item.slug)}.html\">{esc(item.service)}</a></td>"
        f"<td>Listé</td><td>{esc(item.gamsgo_status)}</td><td>{esc(item.specific_risk)}</td></tr>"
        for item in SUBSCRIPTIONS
    )
    content = (
        head(title, description, slug, faq)
        + header()
        + f"""<main id="main">
<section class="hero-mini"><div class="container"><div class="breadcrumbs"><a href="../index.html">Accueil</a> · <a href="../articles.html">Articles</a> · Comparatifs</div>
<div class="hero-card"><div class="eyebrow">Comparatif indépendant • 24 juillet 2026</div><h1>{esc(title)}</h1><p class="lead">Deux catalogues qui se rapprochent, mais deux expériences différentes. Voici lequel choisir selon l’abonnement ou le service gaming recherché.</p></div></div></section>
<section class="section"><div class="container page-grid">
<article class="hero-card article">
{disclosure()}
<div class="fact-strip"><div><strong>U7BUY</strong><span>Marketplace très large</span></div><div><strong>GamsGo</strong><span>Abonnements + marketplace</span></div><div><strong>{U7_CODE}</strong><span>-5 % si éligible</span></div></div>
<h2>Notre verdict</h2>
<div class="verdict-box"><span class="verdict-box__label">En bref</span><p><strong>U7BUY</strong> convient mieux si vous voulez beaucoup d’annonces, de services gaming ou comparer plusieurs vendeurs. <strong>GamsGo</strong> reste plus lisible pour certaines offres directes d’abonnements, mais sa marketplace s’est fortement élargie. Pour la confidentialité, la simplicité et le respect des règles fournisseur, l’abonnement officiel reste le repère le plus sûr.</p></div>
{dual_cta(u7_url("/"), "Tout le catalogue")}
<h2>U7BUY vs GamsGo : le tableau qui tranche</h2>
<div class="responsive-table"><table><thead><tr><th>Critère</th><th>U7BUY</th><th>GamsGo</th></tr></thead><tbody>
<tr><td>Positionnement</td><td>Marketplace de produits numériques et gaming</td><td>Abonnements, logiciels, IA et marketplace gaming</td></tr>
<tr><td>Abonnements</td><td>15 catégories affichées</td><td>Catalogue plus vaste, mais disponibilité variable par rubrique</td></tr>
<tr><td>Gaming</td><td>Top up, items, comptes, coins, boosting, Roblox</td><td>Top up, comptes, items, cartes cadeaux, coins</td></tr>
<tr><td>Qualité</td><td>Dépend fortement du vendeur et de l’annonce</td><td>Dépend du produit direct ou du vendeur marketplace</td></tr>
<tr><td>Protection</td><td>Litiges et remboursements encadrés ; test immédiat indispensable</td><td>Politique différente selon le type de produit et la garantie</td></tr>
<tr><td>Code EuroMalin</td><td><code>{U7_CODE}</code> : -5 % annoncé sur commandes éligibles</td><td><code>{GAMSGO_CODE}</code> : tester au panier</td></tr>
</tbody></table></div>
<h2>Les 15 abonnements U7BUY, comparés à GamsGo</h2>
<div class="responsive-table"><table><thead><tr><th>Service</th><th>U7BUY</th><th>GamsGo au 24/07/2026</th><th>Point de vigilance</th></tr></thead><tbody>{rows}</tbody></table></div>
<h2>Quand choisir U7BUY</h2>
<ul class="check-list"><li>Vous cherchez une catégorie gaming précise ou un grand choix de vendeurs.</li><li>Vous savez comparer note, volume de commandes, méthode de livraison et garantie.</li><li>Vous voulez tester le code <code>{U7_CODE}</code> pour 5 % supplémentaires sur une commande éligible.</li><li>Vous êtes prêt à contrôler immédiatement le produit avant de confirmer la réception.</li></ul>
<h2>Quand choisir GamsGo</h2>
<ul class="check-list"><li>L’offre est vendue directement par GamsGo et les conditions sont plus simples à lire.</li><li>Le service exact est visible dans la rubrique abonnement, IA ou logiciel.</li><li>La garantie et le mode d’accès sont plus clairs que dans les annonces concurrentes.</li><li>Le total au panier, après éventuel code <code>{GAMSGO_CODE}</code>, est réellement meilleur.</li></ul>
<h2>Les risques communs</h2>
<p>Les deux sites peuvent proposer des comptes partagés, des comptes contrôlés par un tiers, des invitations ou des produits soumis aux règles d’un éditeur. Cela peut entraîner une vérification de région, une perte d’accès, une récupération par le propriétaire initial ou une sanction dans un jeu. Pour les outils IA, e-mails, fichiers et historiques peuvent aussi être visibles par d’autres personnes.</p>
<div class="warning-box"><strong>Règle simple :</strong> aucun document confidentiel sur un compte partagé, aucun paiement hors plateforme, aucune confirmation de réception avant test complet.</div>
<h2>Comment utiliser le code U7BUY {U7_CODE}</h2>
<ol><li>Accédez à U7BUY par le lien affilié EuroMalin.</li><li>Choisissez une annonce et vérifiez ses restrictions.</li><li>Saisissez <code>{U7_CODE}</code> au panier.</li><li>Vérifiez que la remise de 5 % apparaît réellement.</li><li>Si elle n’apparaît pas, comparez sans supposer que le code est universel.</li></ol>
<h2>Questions fréquentes</h2><div class="faq">{''.join(f'<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>' for q, a in faq)}</div>
<h2>Sources</h2>
<p>Comparatif établi à partir des catalogues publics <a href="{u7_url('/')}" target="_blank" rel="sponsored noopener noreferrer">U7BUY</a> et <a href="https://www.gamsgo.com/accounts" target="_blank" rel="noopener noreferrer">GamsGo</a>, de la <a href="https://www.u7buy.com/help-center/articles/u7buy-trade-protect-for-buyer" target="_blank" rel="noopener noreferrer">protection acheteur U7BUY</a> et des <a href="https://www.u7buy.com/refund-promise" target="_blank" rel="noopener noreferrer">conditions de remboursement U7BUY</a>. Vérification : 24 juillet 2026.</p>
</article><aside class="sidebar">
<div class="sidebar-card"><div class="kicker">Code U7BUY</div><h3>{U7_CODE}</h3><p>5 % supplémentaires annoncés sur les commandes éligibles.</p><a class="btn ghost" href="u7buy-avis-code-promo-euro10.html">Voir le guide</a></div>
<div class="sidebar-card"><div class="kicker">Abonnements</div><h3>15 guides détaillés</h3><div class="small-list"><a href="payer-chatgpt-plus-moins-cher.html">ChatGPT Plus</a><a href="payer-netflix-premium-moins-cher.html">Netflix</a><a href="payer-youtube-premium-moins-cher.html">YouTube Premium</a><a href="payer-spotify-premium-moins-cher.html">Spotify</a></div></div>
</aside></div></section></main>"""
        + footer()
    )
    return slug, title, content


def u7_review_page() -> tuple[str, str, str]:
    slug = "u7buy-avis-code-promo-euro10"
    title = "Avis U7BUY 2026 : code promo EURO10, fiabilité et garanties"
    description = (
        f"Avis U7BUY 2026 : fonctionnement de la marketplace, code {U7_CODE} -5 %, "
        "vendeurs, abonnements, gaming, remboursement et précautions."
    )
    faq = [
        (
            "U7BUY est-il une boutique ou une marketplace ?",
            "U7BUY fonctionne principalement comme une marketplace : les annonces et la "
            "livraison dépendent souvent de vendeurs indépendants.",
        ),
        (
            f"Que donne le code {U7_CODE} ?",
            f"Le code partenaire {U7_CODE} annonce 5 % supplémentaires sur les commandes "
            "éligibles. Le panier doit confirmer la remise.",
        ),
        (
            "Quand faut-il ouvrir un litige ?",
            "Dès qu’un produit n’est pas livré ou ne correspond pas à l’annonce. Conservez "
            "les preuves et ne confirmez pas la réception avant le test.",
        ),
        (
            "Peut-on acheter sans risque de sanction dans un jeu ?",
            "Non. Les règles de l’éditeur peuvent interdire la vente de comptes, de monnaie, "
            "d’objets ou le boosting. Vérifiez-les avant achat.",
        ),
    ]
    content = (
        head(title, description, slug, faq)
        + header()
        + f"""<main id="main"><section class="hero-mini"><div class="container"><div class="breadcrumbs"><a href="../index.html">Accueil</a> · <a href="../articles.html">Articles</a> · Avis</div>
<div class="hero-card"><div class="eyebrow">Avis vérifié • catalogue du 24 juillet 2026</div><h1>{esc(title)}</h1><p class="lead">U7BUY offre beaucoup de choix, mais il faut juger chaque annonce comme un achat auprès d’un vendeur indépendant.</p></div></div></section>
<section class="section"><div class="container page-grid"><article class="hero-card article">
{disclosure()}
<div class="fact-strip"><div><strong>15</strong><span>abonnements affichés</span></div><div><strong>75+</strong><span>catégories top up</span></div><div><strong>{U7_CODE}</strong><span>-5 % si éligible</span></div></div>
<h2>Notre avis sur U7BUY</h2>
<div class="verdict-box"><span class="verdict-box__label">7,5/10 pour les comparateurs attentifs</span><p>U7BUY est intéressant pour son choix et la concurrence entre vendeurs. Il est moins adapté à quelqu’un qui veut une garantie simple et uniforme. Le bon réflexe consiste à comparer l’annonce, la note, le volume de commandes, le mode de livraison et la garantie — pas seulement le prix.</p></div>
<h2>Que vend U7BUY ?</h2>
<div class="responsive-table"><table><thead><tr><th>Rubrique</th><th>Catalogue affiché</th><th>Exemples</th></tr></thead><tbody>
<tr><td>Top up</td><td>75 catégories</td><td>Genshin Impact, Fortnite, Pokémon GO</td></tr>
<tr><td>Objets</td><td>131 catégories</td><td>Roblox, Adopt Me, Blox Fruits</td></tr>
<tr><td>Comptes</td><td>134 catégories</td><td>GTA 5, Fortnite, Valorant</td></tr>
<tr><td>Coins</td><td>51 catégories</td><td>FC, Roblox, Albion Online</td></tr>
<tr><td>Boosting</td><td>58 catégories</td><td>Rang, victoires, objectifs</td></tr>
<tr><td>Abonnements</td><td>15 catégories</td><td>Netflix, ChatGPT, Spotify, Apple</td></tr>
<tr><td>Roblox</td><td>86 expériences</td><td>Items, comptes, pass, monnaies</td></tr>
</tbody></table></div>
{dual_cta(u7_url("/"), "U7BUY")}
<h2>Code promo U7BUY {U7_CODE}</h2>
<p>Le code affilié <code>{U7_CODE}</code> est annoncé comme offrant <strong>5 % de remise supplémentaire</strong>. Il peut dépendre de la catégorie, du vendeur, du montant ou d’une promotion en cours. EuroMalin ne présente donc pas cette remise comme universelle : le total du panier fait foi.</p>
<h2>Protection acheteur : ce qu’il faut comprendre</h2>
<p>La protection U7BUY couvre notamment les produits non reçus ou différents de la description. Elle exclut plusieurs cas après confirmation de réception, achat hors plateforme, erreur de l’acheteur ou expiration de la garantie. La page de protection indique également qu’une absence de réclamation rapide peut valoir acceptation.</p>
<ul class="check-list"><li>Tester immédiatement le produit.</li><li>Ne pas confirmer la réception trop tôt.</li><li>Conserver annonce, captures et messages.</li><li>Ne jamais déplacer la transaction vers Discord, Telegram ou un paiement direct.</li><li>Ouvrir le litige depuis la commande avec des preuves lisibles.</li></ul>
<h2>Points forts</h2><ul><li>Catalogue très large.</li><li>Concurrence entre vendeurs et formats.</li><li>Notes, avis et volume de commandes visibles.</li><li>Paiements et messagerie centralisés.</li><li>Code partenaire {U7_CODE} sur les commandes éligibles.</li></ul>
<h2>Points faibles</h2><ul><li>Qualité et support variables d’un vendeur à l’autre.</li><li>Règles de remboursement plus complexes qu’une boutique classique.</li><li>Certains produits peuvent enfreindre les conditions des éditeurs.</li><li>Comptes partagés ou récupérables par un tiers.</li><li>Prix final susceptible d’inclure des frais de paiement.</li></ul>
<h2>Questions fréquentes</h2><div class="faq">{''.join(f'<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>' for q, a in faq)}</div>
<h2>Sources</h2><p>Catalogue <a href="{u7_url('/')}" target="_blank" rel="sponsored noopener noreferrer">U7BUY</a>, <a href="https://www.u7buy.com/help-center/articles/u7buy-trade-protect-for-buyer" target="_blank" rel="noopener noreferrer">Trade Protect</a> et <a href="https://www.u7buy.com/refund-promise" target="_blank" rel="noopener noreferrer">politique de remboursement</a>, consultés le 24 juillet 2026.</p>
</article><aside class="sidebar"><div class="sidebar-card"><div class="kicker">Comparatif</div><h3>U7BUY ou GamsGo ?</h3><a class="btn ghost" href="u7buy-vs-gamsgo.html">Comparer</a></div><div class="sidebar-card"><div class="kicker">À retenir</div><h3>Tester avant de confirmer</h3><p>La preuve et le délai de réclamation comptent autant que le prix.</p></div></aside></div></section></main>"""
        + footer()
    )
    return slug, title, content


def service_page(item: ServiceGuide) -> str:
    faq = [
        (
            f"Le code {U7_CODE} s’applique-t-il à cette rubrique ?",
            f"Le code {U7_CODE} annonce 5 % supplémentaires sur les commandes éligibles. "
            "Vérifiez le panier, car toutes les annonces ne sont pas forcément compatibles.",
        ),
        (
            "U7BUY ou GamsGo : où comparer ?",
            f"{item.gamsgo} Comparez le prix total, le vendeur, la méthode de livraison, "
            "la garantie et les règles du jeu.",
        ),
        (
            "Que faire si la livraison ne correspond pas ?",
            "Ne confirmez pas la réception. Prenez des captures, contactez le vendeur depuis "
            "la commande puis ouvrez un litige U7BUY si nécessaire.",
        ),
    ]
    checks = "".join(f"<li>{esc(check.capitalize())}.</li>" for check in item.checks)
    return (
        head(item.title, item.description, item.slug, faq)
        + header()
        + f"""<main id="main"><section class="hero-mini"><div class="container"><div class="breadcrumbs"><a href="../index.html">Accueil</a> · <a href="../articles.html">Articles</a> · Gaming</div>
<div class="hero-card"><div class="eyebrow">Guide U7BUY • gaming • 2026</div><h1>{esc(item.title)} sur U7BUY : guide et précautions</h1><p class="lead">{esc(item.summary.capitalize())}, avec le code {U7_CODE}, la comparaison GamsGo et les points à vérifier avant paiement.</p></div></div></section>
<section class="section"><div class="container page-grid"><article class="hero-card article">
{disclosure()}
<div class="fact-strip"><div><strong>U7BUY</strong><span>{esc(item.count)}</span></div><div><strong>{U7_CODE}</strong><span>-5 % si éligible</span></div><div><strong>GamsGo</strong><span>Alternative à comparer</span></div></div>
<h2>À quoi sert cette rubrique ?</h2><p>La rubrique permet de {esc(item.summary)}. Le catalogue public met notamment en avant {esc(item.examples)}. Les stocks, vendeurs, prix et délais changent en continu.</p>
<div class="verdict-box"><span class="verdict-box__label">Notre avis</span><p>U7BUY est intéressant si vous comparez plusieurs vendeurs et comprenez la méthode de livraison. {esc(item.gamsgo)} Dans tous les cas, les règles de l’éditeur du jeu restent prioritaires.</p></div>
{dual_cta(item.u7_url, item.title)}
<h2>Le risque principal</h2><div class="warning-box"><strong>À savoir :</strong> {esc(item.risk)}</div>
<h2>Checklist avant achat</h2><ul class="check-list">{checks}</ul>
<h2>Comparer U7BUY et GamsGo</h2>
<div class="responsive-table"><table><thead><tr><th>Critère</th><th>U7BUY</th><th>GamsGo</th></tr></thead><tbody>
<tr><td>Choix</td><td>{esc(item.count)}</td><td>Variable selon la rubrique</td></tr>
<tr><td>Vendeurs</td><td>Plusieurs annonces possibles</td><td>Offre directe ou marketplace</td></tr>
<tr><td>Prix</td><td>À comparer après frais et code</td><td>À comparer au panier</td></tr>
<tr><td>Garantie</td><td>Dépend de l’annonce et de la catégorie</td><td>Dépend du produit et du vendeur</td></tr>
<tr><td>Risque éditeur</td><td>À vérifier dans les règles du jeu</td><td>À vérifier dans les règles du jeu</td></tr>
</tbody></table></div>
<h2>Comment utiliser le code {U7_CODE}</h2><ol><li>Ouvrez la rubrique via le lien partenaire.</li><li>Comparez au moins trois annonces similaires.</li><li>Saisissez <code>{U7_CODE}</code> au panier.</li><li>Vérifiez les 5 % supplémentaires avant paiement.</li><li>Testez la livraison avant de confirmer la réception.</li></ol>
<h2>Questions fréquentes</h2><div class="faq">{''.join(f'<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>' for q, a in faq)}</div>
<h2>Sources</h2><p><a href="{esc(item.u7_url)}" target="_blank" rel="sponsored noopener noreferrer">Catalogue U7BUY</a>, <a href="https://www.u7buy.com/help-center/articles/u7buy-trade-protect-for-buyer" target="_blank" rel="noopener noreferrer">protection acheteur</a>, <a href="https://www.u7buy.com/refund-promise" target="_blank" rel="noopener noreferrer">remboursements U7BUY</a> et <a href="https://www.gamsgo.com/accounts" target="_blank" rel="noopener noreferrer">catalogue GamsGo</a>, consultés le 24 juillet 2026.</p>
</article><aside class="sidebar"><div class="sidebar-card"><div class="kicker">Avis complet</div><h3>U7BUY est-il fiable ?</h3><a class="btn ghost" href="u7buy-avis-code-promo-euro10.html">Lire l’avis</a></div><div class="sidebar-card"><div class="kicker">Comparatif</div><h3>U7BUY ou GamsGo</h3><a class="btn ghost" href="u7buy-vs-gamsgo.html">Voir le duel</a></div></aside></div></section></main>"""
        + footer()
    )


def card(slug: str, title: str, description: str, category: str = "Bons Plans") -> str:
    return f"""<article class="article-card" data-article-card>
<a class="article-thumb" href="articles/{esc(slug)}.html" aria-hidden="true" tabindex="-1"><img src="assets/img/articles/{esc(slug)}.jpg" alt="" loading="lazy" decoding="async" width="600" height="338"/></a>
<div class="article-meta"><span class="category-pill">{esc(category)}</span><span class="read-time">8 min</span></div>
<h3>{esc(title)}</h3><p>{esc(description)}</p><div class="actions"><a class="btn" href="articles/{esc(slug)}.html">Lire le guide →</a></div>
</article>"""


def update_index(generated: list[tuple[str, str, str, str]]) -> None:
    path = ROOT / "articles.html"
    text = path.read_text(encoding="utf-8")
    all_slugs = [slug for slug, _, _, _ in generated]
    for slug in all_slugs:
        text = re.sub(
            rf'<article class="article-card"[^>]*>(?:(?!</article>).)*?href="articles/{re.escape(slug)}\.html"(?:(?!</article>).)*?</article>',
            "",
            text,
            count=1,
            flags=re.S,
        )
    block = (
        "<!-- U7BUY-CONTENT:START -->"
        + disclosure()
        + "".join(card(slug, title, description, category) for slug, title, description, category in generated)
        + "<!-- U7BUY-CONTENT:END -->"
    )
    text = re.sub(
        r"<!-- U7BUY-CONTENT:START -->.*?<!-- U7BUY-CONTENT:END -->",
        "",
        text,
        flags=re.S,
    )
    needle = '<div class="grid-3">'
    if needle not in text:
        raise RuntimeError("articles.html grid marker not found")
    text = text.replace(needle, needle + block, 1)
    total = len(list(ARTICLES.glob("*.html")))
    text = re.sub(r"\d+ articles déjà intégrés", f"{total} articles déjà intégrés", text)
    path.write_text(text, encoding="utf-8")


def update_economies(generated: list[tuple[str, str, str, str]]) -> None:
    path = ROOT / "economies.html"
    text = path.read_text(encoding="utf-8")
    featured = generated[:2] + [
        next(item for item in generated if item[0] == "payer-chatgpt-plus-moins-cher"),
        next(item for item in generated if item[0] == "payer-netflix-premium-moins-cher"),
        next(item for item in generated if item[0] == "u7buy-top-up-jeux"),
        next(item for item in generated if item[0] == "u7buy-comptes-jeux"),
    ]
    block = (
        "<!-- U7BUY-FEATURED:START -->"
        + "".join(card(slug, title, description, category) for slug, title, description, category in featured)
        + "<!-- U7BUY-FEATURED:END -->"
    )
    text = re.sub(
        r"<!-- U7BUY-FEATURED:START -->.*?<!-- U7BUY-FEATURED:END -->",
        "",
        text,
        flags=re.S,
    )
    for slug, _, _, _ in generated:
        text = re.sub(
            rf'<article class="article-card"[^>]*>(?:(?!</article>).)*?href="articles/{re.escape(slug)}\.html"(?:(?!</article>).)*?</article>',
            "",
            text,
            flags=re.S,
        )
    needle = '<div class="grid-3">'
    if needle not in text:
        raise RuntimeError("economies.html grid marker not found")
    text = text.replace(needle, needle + block, 1)
    path.write_text(text, encoding="utf-8")


def update_sitemap(slugs: list[str]) -> None:
    path = ROOT / "sitemap.xml"
    text = path.read_text(encoding="utf-8")
    for slug in slugs:
        loc = f"https://euromalin.com/articles/{slug}.html"
        pattern = rf"(<loc>{re.escape(loc)}</loc>\s*<lastmod>)[^<]+(</lastmod>)"
        if re.search(pattern, text):
            text = re.sub(pattern, rf"\g<1>{TODAY}\g<2>", text)
        elif loc not in text:
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


def write_query_manifest(generated: list[tuple[str, str, str, str]], queries: dict[str, str]) -> None:
    manifest = ROOT / "scripts" / "u7buy_cover_queries.json"
    data = {slug: queries[slug] for slug, _, _, _ in generated if slug in queries}
    manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    ARTICLES.mkdir(exist_ok=True)
    generated: list[tuple[str, str, str, str]] = []
    queries: dict[str, str] = {}

    compare_slug, compare_title, compare_html = comparison_page()
    (ARTICLES / f"{compare_slug}.html").write_text(compare_html, encoding="utf-8")
    generated.append((compare_slug, compare_title, "Le duel complet : abonnements, gaming, garanties, risques et codes promo.", "Comparatif"))
    queries[compare_slug] = "gaming streaming subscriptions comparison"

    review_slug, review_title, review_html = u7_review_page()
    (ARTICLES / f"{review_slug}.html").write_text(review_html, encoding="utf-8")
    generated.append((review_slug, review_title, f"Notre analyse de la marketplace et du code {U7_CODE} : -5 % si éligible.", "Avis"))
    queries[review_slug] = "online marketplace gaming shopping"

    for item in SUBSCRIPTIONS:
        (ARTICLES / f"{item.slug}.html").write_text(subscription_page(item), encoding="utf-8")
        generated.append((item.slug, item.title, item.description, "Abonnements"))
        queries[item.slug] = item.cover_query

    for item in SERVICE_GUIDES:
        (ARTICLES / f"{item.slug}.html").write_text(service_page(item), encoding="utf-8")
        generated.append((item.slug, item.title, item.description, "Gaming"))
        queries[item.slug] = item.cover_query

    update_index(generated)
    update_economies(generated)
    update_sitemap([slug for slug, _, _, _ in generated])
    write_query_manifest(generated, queries)

    print(f"Generated {len(generated)} editorial pages/cards ({len(SUBSCRIPTIONS)} subscriptions).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
