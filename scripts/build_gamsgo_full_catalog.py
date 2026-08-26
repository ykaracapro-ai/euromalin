#!/usr/bin/env python3
"""Build the missing GamsGo catalogue guides audited on 20 August 2026.

The public catalogue mixes direct subscriptions and marketplace listings. These
pages deliberately avoid undated price promises and tell readers to verify the
seller, access method, region, duration, guarantee and checkout total.
"""

from __future__ import annotations

import html
import json
import re
import textwrap
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from build_u7buy_content import card, footer, head, header


ROOT = Path(__file__).resolve().parents[1]
ARTICLES = ROOT / "articles"
IMAGES = ROOT / "assets" / "img" / "articles"
TODAY = "2026-08-20"
DISPLAY_DATE = "20 août 2026"
GAMSGO_URL = "https://www.gamsgo.com/partner/Px5AZ"
GAMSGO_CODE = "WPQTU"
CATALOG_URL = "https://www.gamsgo.com/fr/accounts"
HUB_SLUG = "catalogue-gamsgo-complet-offres-code-wpqtu"
START = "<!-- GAMSGO-CATALOG-2026:START -->"
END = "<!-- GAMSGO-CATALOG-2026:END -->"
PRICE_SNAPSHOT = ROOT / "scripts" / "gamsgo_catalog_prices.json"


def normalized_service(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


PRICE_RECORDS = json.loads(PRICE_SNAPSHOT.read_text(encoding="utf-8"))
PRICE_BY_SERVICE = {
    normalized_service(str(record["service"])): record for record in PRICE_RECORDS
}
PRICE_ALIASES = {
    "dazn": "dznsports",
    "vixpremium": "vix",
    "shahidvip": "shahid",
    "vikipass": "viki",
    "movistar": "movistarplus",
    "gammaai": "gama",
    "runwayai": "runway",
    "deezerpremium": "deezer",
    "replitcore": "replit",
    "courseraplus": "coursera",
    "playstationplus": "playstation",
    "hedraai": "hedraia",
    "lumaai": "luma",
    "tindergold": "tinder",
    "cursorpro": "cursor",
    "higgsfieldai": "higgsfield",
    "dreaminaai": "dreamina",
    "manusai": "manus",
    "zoompremium": "zoom",
    "discordnitro": "discord",
    "linkedinpremium": "linkedin",
    "telegrampremium": "telegram",
    "figmaprofessional": "figma",
    "plexpass": "plex",
    "anghamiplus": "anghami",
    "deeplpro": "deepl",
    "updfpro": "updf",
}


def format_eur(value: float) -> str:
    return f"{value:.2f}".replace(".", ",")


@dataclass(frozen=True)
class Offer:
    slug: str
    service: str
    category: str
    use_case: str
    specific_check: str
    catalog_name: str | None = None

    @property
    def price_record(self) -> dict | None:
        key = normalized_service(self.catalog_name or self.service)
        return PRICE_BY_SERVICE.get(PRICE_ALIASES.get(key, key))

    @property
    def title(self) -> str:
        record = self.price_record
        if record and record.get("monthly") is not None:
            return (
                f"Comment acheter {self.service} dès "
                f"{format_eur(float(record['monthly']))} €/mois sur GamsGo ?"
            )
        if record and record.get("price") is not None:
            return (
                f"Comment acheter {self.service} dès "
                f"{format_eur(float(record['price']))} € sur GamsGo ?"
            )
        return f"Comment acheter {self.service} sur GamsGo ? Prix à vérifier"

    @property
    def description(self) -> str:
        record = self.price_record
        if record and record.get("monthly") is not None:
            price = f"dès {format_eur(float(record['monthly']))} €/mois"
        elif record and record.get("price") is not None:
            price = f"dès {format_eur(float(record['price']))} €"
        else:
            price = "prix à contrôler"
        return (
            f"Comment acheter {self.service} sur GamsGo {price} : prix relevé le "
            f"{DISPLAY_DATE}, durée, type d’accès, risques, code {GAMSGO_CODE} et lien partenaire."
        )

    @property
    def seo_title(self) -> str:
        record = self.price_record
        if record and record.get("monthly") is not None:
            price = f"{format_eur(float(record['monthly']))} €/mois"
            candidates = (
                f"{self.service} moins cher : dès {price} sur GamsGo",
                f"{self.service} dès {price} sur GamsGo",
                f"{self.service} {price} | GamsGo",
            )
        elif record and record.get("price") is not None:
            price = f"{format_eur(float(record['price']))} €"
            candidates = (
                f"{self.service} moins cher : dès {price} sur GamsGo",
                f"{self.service} dès {price} sur GamsGo",
                f"{self.service} {price} | GamsGo",
            )
        else:
            candidates = (
                f"{self.service} sur GamsGo : prix et avis 2026",
                f"{self.service} sur GamsGo : notre avis",
                f"{self.service} | GamsGo",
            )
        return next((candidate for candidate in candidates if len(candidate) <= 60), candidates[-1])

    @property
    def seo_description(self) -> str:
        record = self.price_record
        if record and record.get("monthly") is not None:
            price = f"dès {format_eur(float(record['monthly']))} €/mois"
        elif record and record.get("price") is not None:
            price = f"dès {format_eur(float(record['price']))} €"
        else:
            price = "avec prix à vérifier"
        return (
            f"{self.service} sur GamsGo {price}. Prix relevé le {DISPLAY_DATE} : "
            f"type d’accès, risques et code {GAMSGO_CODE} à contrôler avant l’achat."
        )


# Missing services from the public subscription catalogue and its expanded
# navigation, compared with the 90 French articles present before this audit.
OFFERS = [
    # Streaming and sport
    Offer("gamsgo-dazn-moins-cher", "DAZN", "Streaming", "suivre le sport en direct et les compétitions disponibles dans votre pays", "les compétitions incluses, les restrictions géographiques et le nombre d’écrans"),
    Offer("gamsgo-vix-premium-moins-cher", "ViX Premium", "Streaming", "regarder des séries, films et sports en espagnol", "la disponibilité de ViX dans votre pays et le type de profil livré"),
    Offer("gamsgo-peacock-tv-moins-cher", "Peacock TV", "Streaming", "accéder aux séries, films et sports proposés par Peacock", "la région du compte et la nécessité éventuelle d’un VPN compatible"),
    Offer("gamsgo-nba-league-pass-moins-cher", "NBA League Pass", "Streaming", "regarder les rencontres NBA en direct ou en replay", "les blackouts locaux, la formule choisie et le nombre d’appareils"),
    Offer("gamsgo-shahid-vip-moins-cher", "Shahid VIP", "Streaming", "regarder des séries, films et chaînes arabophones", "le pays d’utilisation, le bouquet inclus et la langue des contenus"),
    Offer("gamsgo-rtl-plus-moins-cher", "RTL+", "Streaming", "accéder aux programmes RTL+ et à ses contenus audio ou vidéo", "la compatibilité hors Allemagne et le mode de connexion fourni"),
    Offer("gamsgo-viki-pass-moins-cher", "Viki Pass", "Streaming", "regarder des dramas asiatiques avec sous-titres", "la formule Standard ou Plus, les régions et les sous-titres disponibles"),
    Offer("gamsgo-osn-plus-moins-cher", "OSN+", "Streaming", "regarder des films et séries disponibles au Moyen-Orient", "la zone géographique autorisée et les appareils compatibles"),
    Offer("gamsgo-plex-pass-moins-cher", "Plex Pass", "Streaming", "utiliser les fonctions premium de Plex et l’accès distant", "la différence entre Plex Pass et Remote Watch Pass ainsi que le contrôle du compte"),
    Offer("gamsgo-mubi-moins-cher", "MUBI", "Streaming", "regarder une sélection de cinéma d’auteur", "le catalogue régional, la durée et la conservation du même profil"),
    Offer("gamsgo-movistar-plus-moins-cher", "Movistar+", "Streaming", "regarder les chaînes et programmes proposés par Movistar+", "la disponibilité en Espagne, la région du compte et les écrans simultanés"),
    Offer("gamsgo-skyshowtime-moins-cher", "SkyShowtime", "Streaming", "regarder les films et séries du catalogue SkyShowtime", "le pays d’activation, la formule et les règles de foyer"),
    Offer("gamsgo-f1-tv-pro-moins-cher", "F1 TV Pro", "Streaming", "suivre la Formule 1 en direct avec les fonctions F1 TV", "la disponibilité de F1 TV Pro dans votre pays et les restrictions de diffusion"),
    Offer("gamsgo-tennis-tv-moins-cher", "Tennis TV", "Streaming", "suivre les tournois ATP en direct et en replay", "les compétitions réellement incluses et les éventuelles restrictions locales"),
    Offer("gamsgo-mlb-tv-moins-cher", "MLB.TV", "Streaming", "regarder la saison de baseball MLB", "les blackouts, la saison couverte et le renouvellement automatique"),
    Offer("gamsgo-now-tv-moins-cher", "NOW TV", "Streaming", "accéder aux pass divertissement, cinéma ou sport de NOW", "le pass exact, le pays et la qualité vidéo annoncée"),
    # Music
    Offer("gamsgo-qobuz-moins-cher", "Qobuz", "Musique", "écouter et télécharger de la musique en haute résolution", "la qualité Hi-Res, le pays du compte et la formule Studio ou Sublime"),
    Offer("gamsgo-anghami-plus-moins-cher", "Anghami Plus", "Musique", "écouter de la musique arabe et internationale sans publicité", "la région, la formule individuelle ou famille et la migration des playlists"),
    Offer("gamsgo-deezer-premium-moins-cher", "Deezer Premium", "Musique", "écouter de la musique sans publicité et hors connexion", "la formule, la région et la possibilité de conserver vos playlists"),
    Offer("gamsgo-tidal-moins-cher", "TIDAL", "Musique", "écouter de la musique en haute qualité audio", "le niveau de qualité, le pays et le caractère privé du compte"),
    Offer("gamsgo-soundcloud-go-plus-moins-cher", "SoundCloud Go+", "Musique", "écouter SoundCloud sans publicité et hors connexion", "la région, la durée et le contrôle de l’adresse e-mail"),
    # Artificial intelligence
    Offer("gamsgo-gamma-ai-moins-cher", "Gamma AI", "IA", "créer des présentations et documents avec l’IA", "les crédits IA, l’export, le filigrane et l’espace de travail livré"),
    Offer("gamsgo-elevenlabs-moins-cher", "ElevenLabs", "IA", "générer des voix et du contenu audio", "les crédits, les droits commerciaux et l’autorisation d’utiliser une voix clonée"),
    Offer("gamsgo-cursor-pro-moins-cher", "Cursor Pro", "IA", "développer du code avec un éditeur assisté par IA", "le caractère privé du compte et l’absence de dépôt ou secret professionnel sensible"),
    Offer("gamsgo-higgsfield-ai-moins-cher", "Higgsfield AI", "IA", "créer des images et vidéos assistées par IA", "les crédits, la résolution, les droits commerciaux et la politique sur les visages"),
    Offer("gamsgo-runway-ai-moins-cher", "Runway AI", "IA", "générer et monter des vidéos avec l’IA", "les crédits, les modèles disponibles, la résolution et les droits d’export"),
    Offer("gamsgo-dreamina-ai-moins-cher", "Dreamina AI", "IA", "générer des images et créations visuelles", "les crédits, la région, le filigrane et les droits d’utilisation"),
    Offer("gamsgo-manus-ai-moins-cher", "Manus AI", "IA", "exécuter des recherches et tâches avec un agent IA", "les crédits et surtout les autorisations accordées à un compte contrôlé par un tiers"),
    Offer("gamsgo-lovable-moins-cher", "Lovable", "IA", "prototyper des applications web avec l’IA", "les crédits, l’accès au projet, l’export du code et les secrets de déploiement"),
    Offer("gamsgo-ai-api-moins-cher", "AI API", "IA", "utiliser une clé API pour des modèles d’intelligence artificielle", "le fournisseur réel, les quotas, les journaux de requêtes et la révocation de la clé"),
    Offer("gamsgo-google-antigravity-moins-cher", "Google Antigravity", "IA", "tester les fonctions créatives et d’automatisation annoncées", "le produit exact livré, les quotas et le contrôle du compte Google associé"),
    Offer("gamsgo-github-copilot-moins-cher", "GitHub Copilot", "IA", "obtenir une assistance IA dans son éditeur de code", "le mode d’activation et l’accès éventuel à vos dépôts privés"),
    Offer("gamsgo-deepl-pro-moins-cher", "DeepL Pro", "IA", "traduire des textes et documents avec davantage de fonctions", "la confidentialité des documents, les quotas et la formule réellement activée"),
    # Software and marketplace subscriptions
    Offer("gamsgo-expressvpn-moins-cher", "ExpressVPN", "Logiciels", "protéger sa connexion sur des appareils compatibles", "la durée de la clé, la région, le nombre d’appareils et la récupération du compte"),
    Offer("gamsgo-zoom-premium-moins-cher", "Zoom Premium", "Logiciels", "organiser des réunions plus longues avec davantage de fonctions", "le rôle administrateur, la durée et la confidentialité des réunions"),
    Offer("gamsgo-surfshark-vpn-moins-cher", "Surfshark VPN", "Logiciels", "utiliser un VPN sur plusieurs appareils", "la durée de la clé, l’origine de la licence et les conditions de renouvellement"),
    Offer("gamsgo-windows-11-cle-moins-cher", "Windows 11", "Logiciels", "activer une édition compatible de Windows 11", "l’édition Home ou Pro, le type OEM ou Retail et la région de la clé"),
    Offer("gamsgo-tradingview-moins-cher", "TradingView", "Logiciels", "utiliser davantage d’indicateurs, alertes et graphiques", "la formule exacte et l’absence de données financières ou courtier liées à un compte partagé"),
    Offer("gamsgo-proton-vpn-moins-cher", "Proton VPN", "Logiciels", "utiliser les serveurs et fonctions premium de Proton VPN", "le contrôle du compte et l’absence de boîte Proton Mail personnelle associée"),
    Offer("gamsgo-discord-nitro-moins-cher", "Discord Nitro", "Logiciels", "profiter des fonctions Nitro sur Discord", "le mode d’activation, la région et l’absence de demande de mot de passe ou de jeton"),
    Offer("gamsgo-linkedin-premium-moins-cher", "LinkedIn Premium", "Logiciels", "utiliser les fonctions Premium pour l’emploi ou la prospection", "le mode d’activation et la sécurité d’un profil professionnel nominatif"),
    Offer("gamsgo-figma-professional-moins-cher", "Figma Professional", "Logiciels", "collaborer sur des fichiers et bibliothèques de design", "la propriété des fichiers, l’équipe d’accueil et la récupération des projets"),
    Offer("gamsgo-autodesk-moins-cher", "Autodesk", "Logiciels", "utiliser un logiciel Autodesk selon la licence proposée", "le produit exact, la version, la licence commerciale et l’association au compte"),
    Offer("gamsgo-replit-core-moins-cher", "Replit Core", "Logiciels", "développer et héberger des projets avec davantage de ressources", "les crédits, la propriété du workspace et les secrets présents dans les projets"),
    Offer("gamsgo-envato-elements-moins-cher", "Envato Elements", "Logiciels", "télécharger des ressources créatives sous licence", "la licence des éléments déjà téléchargés et l’enregistrement de chaque projet"),
    Offer("gamsgo-cookidoo-moins-cher", "Cookidoo", "Logiciels", "accéder au catalogue de recettes pour Thermomix", "le pays du compte, la compatibilité de l’appareil et la conservation des collections"),
    Offer("gamsgo-magnific-freepik-moins-cher", "Magnific / Freepik", "Logiciels", "améliorer des images et accéder à des ressources créatives", "les crédits, les licences commerciales et l’historique des créations"),
    Offer("gamsgo-zwift-moins-cher", "Zwift", "Logiciels", "s’entraîner à vélo ou en course dans un environnement virtuel", "la région, la compatibilité du matériel et la conservation des données sportives"),
    Offer("gamsgo-similarweb-moins-cher", "Similarweb", "Logiciels", "analyser le trafic et les tendances de sites web", "les limites de données, l’export et l’absence d’informations clients sensibles"),
    Offer("gamsgo-coursera-plus-moins-cher", "Coursera Plus", "Logiciels", "suivre des cours et certificats en ligne", "le nom affiché sur les certificats et l’accès durable à votre progression"),
    Offer("gamsgo-updf-pro-moins-cher", "UPDF Pro", "Logiciels", "éditer, convertir et annoter des documents PDF", "la licence, le nombre d’appareils et la confidentialité des documents importés"),
    Offer("gamsgo-windows-10-cle-moins-cher", "Windows 10", "Logiciels", "activer une édition compatible de Windows 10", "l’édition, le type de licence et la fin de support du système"),
    Offer("gamsgo-telegram-premium-moins-cher", "Telegram Premium", "Logiciels", "débloquer les fonctions Premium de Telegram", "le mode d’activation et l’absence de demande de code de connexion à votre compte"),
    Offer("gamsgo-heygen-moins-cher", "HeyGen", "Logiciels", "créer des vidéos avec avatars et voix synthétiques", "les crédits, le consentement des personnes représentées et les droits commerciaux"),
    Offer("gamsgo-snapchat-plus-moins-cher", "Snapchat+", "Logiciels", "utiliser les fonctions supplémentaires de Snapchat", "le mode d’activation sur un compte personnel et la protection du code de connexion"),
    # Gaming subscriptions
    Offer("gamsgo-playstation-plus-moins-cher", "PlayStation Plus", "Gaming", "jouer en ligne et accéder aux avantages du plan PlayStation choisi", "la région de la carte ou du compte, la formule Essential, Extra ou Premium et l’activation"),
    Offer("gamsgo-ea-play-moins-cher", "EA Play", "Gaming", "accéder au catalogue et aux essais EA sur une plateforme compatible", "la plateforme PC, Xbox ou PlayStation, la région et la durée"),
]

# Services revealed by expanding every public catalogue section on 20 August
# 2026. They were not visible in the initially collapsed category lists.
OFFERS += [
    Offer("gamsgo-bloomberg-moins-cher", "Bloomberg", "Streaming", "lire l’actualité économique et suivre les marchés", "la formule Digital, la région et le caractère privé du compte"),
    Offer("gamsgo-amc-plus-moins-cher", "AMC+", "Streaming", "regarder les séries et films du catalogue AMC+", "la région, le profil livré et les appareils compatibles"),
    Offer("gamsgo-mediaset-infinity-moins-cher", "Mediaset Infinity", "Streaming", "regarder les chaînes et programmes italiens disponibles", "la disponibilité hors d’Italie et le type de profil"),
    Offer("gamsgo-tod-tv-moins-cher", "TOD TV", "Streaming", "suivre les sports et contenus proposés par TOD", "le bouquet All-in, la région et les écrans simultanés"),
    Offer("gamsgo-quillbot-premium-moins-cher", "QuillBot", "IA", "réécrire, corriger et résumer des textes", "les fonctions Premium, la confidentialité des textes et le contrôle du compte"),
    Offer("gamsgo-windows-copilot-pro-moins-cher", "Windows Copilot", "IA", "utiliser les fonctions Copilot Pro pendant la durée annoncée", "le mode d’activation, le compte Microsoft et la durée réelle"),
    Offer("gamsgo-meshy-ai-moins-cher", "Meshy AI", "IA", "générer des modèles et textures 3D avec l’IA", "les crédits, les formats d’export et les droits commerciaux"),
    Offer("gamsgo-leonardo-ai-moins-cher", "Leonardo AI", "IA", "créer des images avec des modèles génératifs", "les jetons, la formule Essential et les droits d’utilisation"),
    Offer("gamsgo-picsart-pro-moins-cher", "PicsArt", "IA", "retoucher et créer des visuels sur mobile ou ordinateur", "le plan Pro, le compte partagé et la conservation des projets"),
    Offer("gamsgo-turnitin-moins-cher", "Turnitin", "Logiciels", "contrôler la similarité de documents", "le rôle Instructor, la confidentialité des travaux et les limites de dépôt"),
    Offer("gamsgo-ipvanish-moins-cher", "IPVanish", "Logiciels", "utiliser un VPN sur des appareils compatibles", "le partage du compte, le nombre d’appareils et la récupération"),
    Offer("gamsgo-blackbox-ai-moins-cher", "BlackBox AI", "IA", "obtenir une assistance IA pour le développement", "les quotas, le compte partagé et l’absence de code confidentiel"),
    Offer("gamsgo-vidiq-max-moins-cher", "vidIQ", "Logiciels", "analyser et optimiser une chaîne YouTube", "la formule Max et l’autorisation d’accès à la chaîne"),
    Offer("gamsgo-jetbrains-pro-moins-cher", "JetBrains", "Logiciels", "utiliser les IDE JetBrains inclus dans la licence", "les produits couverts, l’usage commercial et le compte associé"),
    Offer("gamsgo-invideo-ai-moins-cher", "InVideo AI", "IA", "générer et monter des vidéos assistées par IA", "les minutes, crédits, exports et droits commerciaux"),
    Offer("gamsgo-hailuo-ai-moins-cher", "Hailuo AI", "IA", "générer des vidéos à partir de textes ou d’images", "les crédits, la résolution et les droits sur les médias importés"),
    Offer("gamsgo-storyblocks-moins-cher", "Storyblocks", "Logiciels", "télécharger des vidéos, musiques et ressources créatives", "la licence des téléchargements et l’usage commercial après expiration"),
    Offer("gamsgo-veed-io-pro-moins-cher", "VEED.io", "Logiciels", "monter, sous-titrer et exporter des vidéos en ligne", "le compte partagé, les limites d’export et la confidentialité des médias"),
    Offer("gamsgo-ubersuggest-business-moins-cher", "Ubersuggest", "Logiciels", "analyser des mots-clés et des sites pour le référencement", "la formule Business, les quotas et les exports"),
    Offer("gamsgo-hedra-ai-moins-cher", "Hedra AI", "IA", "créer des personnages et vidéos avec l’IA", "les crédits, le consentement des personnes et les droits d’usage"),
    Offer("gamsgo-luma-ai-moins-cher", "Luma AI", "IA", "générer des images et vidéos avec l’IA", "les crédits, la formule Plus et les droits commerciaux"),
    Offer("gamsgo-moz-pro-moins-cher", "Moz Pro", "Logiciels", "suivre le référencement et les performances de sites", "le plan Standard, les campagnes et les limites d’exploration"),
    Offer("gamsgo-jasper-pro-moins-cher", "Jasper", "IA", "rédiger et adapter des contenus marketing avec l’IA", "le compte privé, les quotas et les données de marque importées"),
    Offer("gamsgo-ideogram-plus-moins-cher", "Ideogram", "IA", "générer des images et du texte intégré aux visuels", "les crédits, le mode privé et les droits commerciaux"),
    Offer("gamsgo-writehuman-ultra-moins-cher", "WriteHuman", "IA", "reformuler des textes avec les outils proposés", "les quotas, la confidentialité et les règles académiques ou professionnelles"),
    Offer("gamsgo-picwish-pro-moins-cher", "PicWish", "IA", "retoucher, détourer et améliorer des images", "les crédits, la résolution et les droits sur les images"),
    Offer("gamsgo-nim-video-moins-cher", "Nim.video", "IA", "générer des vidéos avec les modèles disponibles", "les crédits, les modèles, la résolution et les exports"),
    Offer("gamsgo-renderforest-lite-moins-cher", "Renderforest", "Logiciels", "créer des vidéos, logos et pages visuelles", "le plan Lite, les exports, le filigrane et les droits"),
    Offer("gamsgo-krea-ai-moins-cher", "Krea AI", "IA", "générer et améliorer des créations visuelles", "les crédits, le plan Basic et la confidentialité des créations"),
    Offer("gamsgo-cyberghost-vpn-moins-cher", "CyberGhost VPN", "Logiciels", "protéger sa connexion avec un VPN", "la durée, le profil privé et les appareils autorisés"),
    Offer("gamsgo-motion-array-moins-cher", "Motion Array", "Logiciels", "télécharger des modèles et ressources pour le montage", "le compte partagé et la validité des licences de projet"),
    Offer("gamsgo-strava-premium-moins-cher", "Strava", "Logiciels", "analyser ses activités sportives avec les fonctions Premium", "le compte personnel et la confidentialité des données de localisation"),
    Offer("gamsgo-mcafee-advanced-moins-cher", "McAfee", "Logiciels", "protéger ses appareils avec la suite de sécurité", "le nombre d’appareils, la région et le type de licence"),
    Offer("gamsgo-purevpn-moins-cher", "PureVPN", "Logiciels", "utiliser un VPN pendant la durée annoncée", "la durée, les appareils et le contrôle du compte"),
    Offer("gamsgo-storytel-moins-cher", "Storytel", "Musique", "écouter des livres audio et lire des ebooks", "la région, le catalogue linguistique et le compte personnel"),
    Offer("gamsgo-norton-standard-moins-cher", "Norton", "Logiciels", "protéger un appareil avec Norton", "l’édition Standard, la durée et le renouvellement"),
    Offer("gamsgo-wall-street-journal-moins-cher", "The Wall Street Journal", "Streaming", "lire l’actualité économique du Wall Street Journal", "l’accès Digital, la région et le contrôle du compte"),
    Offer("gamsgo-mobbin-pro-moins-cher", "Mobbin", "Logiciels", "consulter des références d’interfaces pour le design produit", "le compte partagé, les quotas et l’usage en équipe"),
    Offer("gamsgo-adguard-moins-cher", "AdGuard", "Logiciels", "bloquer publicités et traqueurs sur les appareils compatibles", "la formule Individual, les appareils et le type de licence"),
    Offer("gamsgo-miro-business-moins-cher", "Miro", "Logiciels", "collaborer sur des tableaux blancs en ligne", "l’espace Business, la propriété des tableaux et les invités"),
    Offer("gamsgo-exitlag-moins-cher", "ExitLag", "Gaming", "optimiser le routage réseau pour les jeux compatibles", "la durée, le nombre d’appareils et les jeux réellement pris en charge"),
    Offer("gamsgo-1password-moins-cher", "1Password", "Logiciels", "gérer ses mots de passe dans un coffre privé", "la propriété du compte et l’absence totale d’accès du vendeur au coffre"),
    Offer("gamsgo-new-york-times-moins-cher", "The New York Times", "Streaming", "lire les articles et contenus numériques du New York Times", "l’offre Individual, la région et les contenus inclus"),
    Offer("gamsgo-windows-server-cle-moins-cher", "Windows Server", "Logiciels", "activer l’édition Windows Server annoncée", "l’édition, le nombre de cœurs, le type de clé et l’usage commercial"),
    Offer("gamsgo-dropbox-plus-moins-cher", "Dropbox", "Logiciels", "stocker et synchroniser des fichiers en ligne", "le compte privé, l’espace disponible et la récupération des fichiers"),
    Offer("gamsgo-pdfelement-moins-cher", "PDFelement", "Logiciels", "modifier, convertir et signer des documents PDF", "la durée, les appareils et la confidentialité des documents"),
    Offer("gamsgo-tinder-gold-moins-cher", "Tinder Gold", "Logiciels", "activer les fonctions Tinder Gold pendant la durée annoncée", "le mode d’activation et la sécurité du compte personnel"),
    Offer("gamsgo-bitwarden-premium-moins-cher", "Bitwarden", "Logiciels", "utiliser les fonctions Premium d’un gestionnaire de mots de passe", "la propriété du compte et l’absence d’accès du vendeur au coffre"),
    Offer("gamsgo-semrush-moins-cher", "SEMrush", "Logiciels", "analyser des mots-clés, concurrents et campagnes SEO", "le compte partagé, les quotas et l’absence de données client sensibles"),
]


# Current catalogue services already covered by a dedicated EuroMalin page.
EXISTING = {
    "Streaming": {
        "Netflix": "payer-netflix-premium-moins-cher",
        "Prime Video": "payer-amazon-prime-video-moins-cher",
        "Disney+": "payer-disney-plus-moins-cher",
        "YouTube Premium": "payer-youtube-premium-moins-cher",
        "Apple TV+": "payer-apple-tv-plus-moins-cher",
        "Crunchyroll": "payer-crunchyroll-moins-cher",
        "HBO Max": "payer-hbo-max-moins-cher",
        "FOX One": "payer-fox-one-moins-cher",
    },
    "Musique": {
        "Spotify Premium": "payer-spotify-premium-moins-cher",
        "Apple Music": "payer-apple-music-moins-cher",
        "YouTube Premium": "payer-youtube-premium-moins-cher",
    },
    "IA": {
        "ChatGPT Plus": "payer-chatgpt-plus-moins-cher",
        "Gemini": "payer-gemini-advanced-moins-cher",
        "Genspark Plus": "payer-genspark-plus-moins-cher",
        "Suno Pro": "payer-suno-pro-moins-cher",
        "Grok / SuperGrok": "payer-grok-ai-moins-cher",
        "Perplexity Pro": "payer-perplexity-pro-moins-cher",
        "Claude": "payer-claude-pro-moins-cher",
        "Kling AI": "payer-kling-ai-pro-moins-cher",
        "Midjourney": "payer-midjourney-moins-cher",
        "Candy AI": "payer-candy-ai-moins-cher",
        "Poe AI": "payer-poe-ai-moins-cher",
        "Canva Pro": "payer-canva-pro-moins-cher",
        "Adobe / Photoshop": "payer-photoshop-moins-cher",
    },
    "Logiciels": {
        "CapCut Pro": "payer-capcut-pro-moins-cher",
        "Adobe Creative Cloud": "payer-photoshop-moins-cher",
        "Duolingo Super": "payer-duolingo-super-moins-cher",
        "Canva Pro": "payer-canva-pro-moins-cher",
        "Filmora": "payer-filmora-moins-cher",
        "Grammarly Premium": "payer-grammarly-premium-moins-cher",
        "Microsoft 365": "payer-microsoft-365-moins-cher",
        "Notion": "payer-notion-ai-moins-cher",
        "WPS Office": "payer-wps-office-moins-cher",
    },
    "Gaming": {
        "Xbox Game Pass": "payer-xbox-game-pass-moins-cher",
    },
}

# Current catalogue services whose established EuroMalin price guide should be
# kept instead of creating a duplicate URL.
CURRENT_EXISTING = {
    "Netflix": ("payer-netflix-premium-moins-cher", "Streaming"),
    "Prime Video": ("payer-amazon-prime-video-moins-cher", "Streaming"),
    "Disney+": ("payer-disney-plus-moins-cher", "Streaming"),
    "YouTube": ("payer-youtube-premium-moins-cher", "Streaming"),
    "Apple": ("payer-apple-one-moins-cher", "Streaming"),
    "Crunchyroll": ("payer-crunchyroll-moins-cher", "Streaming"),
    "Spotify": ("payer-spotify-premium-moins-cher", "Musique"),
    "Claude": ("payer-claude-pro-moins-cher", "IA"),
    "Gemini": ("payer-gemini-advanced-moins-cher", "IA"),
    "SuperGrok": ("payer-grok-ai-moins-cher", "IA"),
    "Adobe": ("payer-photoshop-moins-cher", "IA"),
    "Perplexity AI": ("payer-perplexity-pro-moins-cher", "IA"),
    "Canva": ("payer-canva-pro-moins-cher", "IA"),
    "Midjourney": ("payer-midjourney-moins-cher", "IA"),
    "kling": ("payer-kling-ai-pro-moins-cher", "IA"),
    "Suno": ("payer-suno-pro-moins-cher", "IA"),
    "Poe": ("payer-poe-ai-moins-cher", "IA"),
    "Microsoft Office": ("payer-microsoft-365-moins-cher", "Logiciels"),
    "Notion": ("payer-notion-ai-moins-cher", "Logiciels"),
    "Xbox": ("payer-xbox-game-pass-moins-cher", "Gaming"),
}


def current_catalog_rows() -> list[tuple[str, str, str, dict]]:
    offer_by_catalog_service: dict[str, Offer] = {}
    for offer in OFFERS:
        record = offer.price_record
        if record:
            offer_by_catalog_service[normalized_service(str(record["service"]))] = offer

    rows: list[tuple[str, str, str, dict]] = []
    missing: list[str] = []
    for record in PRICE_RECORDS:
        service = str(record["service"])
        if service in CURRENT_EXISTING:
            slug, category = CURRENT_EXISTING[service]
        else:
            offer = offer_by_catalog_service.get(normalized_service(service))
            if offer is None:
                missing.append(service)
                continue
            slug, category = offer.slug, offer.category
        rows.append((service, slug, category, record))
    if missing:
        raise RuntimeError(f"Unmapped current GamsGo services: {', '.join(missing)}")
    return rows


CATEGORY_COPY = {
    "Streaming": {
        "format": "un compte, un profil ou une place dans un abonnement proposé directement ou par un vendeur de la marketplace",
        "risk": "Les règles de foyer, la région et les écrans simultanés peuvent rendre un accès inutilisable même si les identifiants fonctionnent.",
        "checks": ("la région et le catalogue accessible", "le nombre d’écrans et le type de profil", "la durée et le maintien du même compte"),
        "color": (71, 208, 168),
    },
    "Musique": {
        "format": "un compte Premium, une place famille ou un accès préactivé dont le format dépend de l’annonce",
        "risk": "Une offre mal adaptée peut faire perdre playlists, favoris ou historique. N’associez pas de moyen de paiement personnel à un compte fourni.",
        "checks": ("la région et la formule exacte", "la migration des playlists", "le caractère privé ou familial de l’accès"),
        "color": (247, 191, 77),
    },
    "IA": {
        "format": "un compte, des crédits ou un accès à un espace de travail IA selon la fiche et le vendeur",
        "risk": "Un compte géré par un tiers n’est pas adapté aux secrets, fichiers clients, données personnelles ou connecteurs professionnels.",
        "checks": ("les modèles et quotas réellement inclus", "le contrôle de l’e-mail et de l’espace de travail", "les droits commerciaux des résultats"),
        "color": (135, 119, 255),
    },
    "Logiciels": {
        "format": "une clé, une invitation, une licence ou un compte préactivé selon l’offre affichée",
        "risk": "Une licence peut être limitée à une version, une région, un appareil ou un usage non commercial. Le libellé exact prime sur le nom du produit.",
        "checks": ("le type et la durée de licence", "les appareils et la région compatibles", "la récupération du compte ou de la clé"),
        "color": (67, 151, 219),
    },
    "Gaming": {
        "format": "une carte, un code, un compte ou un abonnement correspondant à une plateforme et une région précises",
        "risk": "Une mauvaise région ou plateforme peut empêcher l’activation. Les comptes achetés peuvent aussi être récupérés ou contraires aux règles de l’éditeur.",
        "checks": ("la plateforme, l’édition et la région", "le format code, carte ou compte", "la durée et les règles d’activation"),
        "color": (255, 112, 94),
    },
}


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def promo_cta(service: str, compact: bool = False) -> str:
    intro = "Lien partenaire EuroMalin" if not compact else "Avant de payer"
    return f"""<section class="gamsgo-promo" aria-label="Code promo GamsGo">
<div><span class="gamsgo-promo__eyebrow">{intro}</span><strong>Code promo GamsGo : <code>{GAMSGO_CODE}</code></strong><p>Ouvrez GamsGo avec le lien partenaire, saisissez le code si le panier le propose et vérifiez la remise réellement affichée pour {esc(service)}.</p></div>
<a class="btn btn-primary" href="{GAMSGO_URL}" target="_blank" rel="sponsored noopener noreferrer">Voir l’offre sur GamsGo →</a>
</section>"""


def disclosure() -> str:
    return (
        '<aside class="affiliate-disclosure">Cette page contient le lien partenaire '
        "GamsGo d’EuroMalin. Une commission peut être versée si vous achetez via ce lien, "
        "sans surcoût annoncé pour vous. Le code WPQTU est à tester au panier : son "
        "éligibilité et sa remise peuvent évoluer.</aside>"
    )


def hero_figure(offer: Offer) -> str:
    return f"""<figure class="article-hero"><img class="article-hero-image" src="../assets/img/articles/{offer.slug}.jpg" alt="Guide EuroMalin de l’offre {esc(offer.service)} sur GamsGo" loading="eager" decoding="async" width="1200" height="675"/><figcaption class="article-hero-credit">Illustration EuroMalin • catalogue contrôlé le {DISPLAY_DATE}</figcaption></figure>"""


def price_presentation(offer: Offer) -> tuple[str, str, str]:
    record = offer.price_record
    if not record or record.get("price") is None:
        return "Prix indisponible", "offre absente du relevé actuel", ""
    total = format_eur(float(record["price"]))
    months = record.get("months")
    monthly = record.get("monthly")
    if months is not None and monthly is not None:
        duration = "1 mois" if int(months) == 1 else f"{int(months)} mois"
        headline = f"Dès {format_eur(float(monthly))} €/mois"
        detail = f"{total} € pour {duration}"
    else:
        headline = f"Dès {total} €"
        detail = str(record.get("descriptor") or "achat unique ou crédits")
    snapshot = (
        f'<div class="verdict-box"><span class="verdict-box__label">Prix relevé le {DISPLAY_DATE}</span>'
        f'<p><strong>{esc(headline)}</strong> — {esc(detail)}. Il s’agit de l’annonce la moins '
        f'chère repérée parmi les résultats visibles, pas d’un tarif garanti. Comparez la formule, '
        f'le vendeur, la région, la garantie et le total au panier.</p></div>'
    )
    return headline, detail, snapshot


def page(offer: Offer) -> str:
    copy = CATEGORY_COPY[offer.category]
    price_headline, price_detail, price_snapshot = price_presentation(offer)
    available = offer.price_record is not None
    faq = [
        (f"GamsGo propose-t-il actuellement {offer.service} ?", f"{offer.service} {'apparaissait' if available else 'n’apparaissait pas'} dans le relevé complet du catalogue public GamsGo effectué le {DISPLAY_DATE}. La disponibilité, les vendeurs et les formules peuvent changer."),
        (f"Comment utiliser le code {GAMSGO_CODE} pour {offer.service} ?", f"Ouvrez GamsGo avec le lien EuroMalin, choisissez l’offre {offer.service}, saisissez {GAMSGO_CODE} si un champ promo est affiché, puis vérifiez le total avant paiement."),
        ("Le prix affiché est-il garanti ?", "Non. Le prix varie selon la durée, le vendeur, la devise, la région, le type d’accès et les frais éventuels. Seul le total du panier au moment de l’achat fait foi."),
        ("Que faire si l’accès ne correspond pas à la fiche ?", "Conservez la fiche et les échanges, testez immédiatement la livraison et ouvrez une demande dans la commande sans déplacer la discussion hors de GamsGo."),
    ]
    checked = "".join(f"<li>{esc(item.capitalize())}.</li>" for item in copy["checks"])
    checked += f"<li>{esc(offer.specific_check.capitalize())}.</li>"
    title = offer.title
    description = offer.description
    page_head = head(
        title,
        description,
        offer.slug,
        faq,
        seo_title=offer.seo_title,
        seo_description=offer.seo_description,
    ).replace("2026-07-24", TODAY)
    return page_head + header() + f"""<main id="main">
<section class="hero-mini"><div class="container"><div class="breadcrumbs"><a href="../index.html">Accueil</a> · <a href="../articles.html">Articles</a> · GamsGo</div><div class="hero-card"><div class="eyebrow">Catalogue vérifié • {DISPLAY_DATE}</div><h1>{esc(title)}</h1><p class="lead">{esc(description)}</p></div></div></section>
<section class="section"><div class="container page-grid"><article class="hero-card article">
{disclosure()}{hero_figure(offer)}
<div class="fact-strip"><div><strong>{esc(price_headline)}</strong><span>{esc(price_detail)}</span></div><div><strong>{GAMSGO_CODE}</strong><span>code à tester</span></div><div><strong>Prix variable</strong><span>relevé le {DISPLAY_DATE}</span></div></div>
{promo_cta(offer.service)}
<h2>Combien coûte {esc(offer.service)} sur GamsGo ?</h2>{price_snapshot or '<div class="warning-box"><strong>Disponibilité à vérifier :</strong> aucune annonce tarifée n’apparaissait dans le relevé complet du catalogue lors du dernier contrôle. Ne présentez pas un ancien prix comme encore disponible.</div>'}
<h2>L’offre {esc(offer.service)} repérée sur GamsGo</h2>
<div class="verdict-box"><span class="verdict-box__label">Résultat de la comparaison</span><p>{esc(offer.service)} {'figurait bien' if available else 'ne figurait plus'} dans le catalogue public GamsGo lors de notre contrôle. Le prix du titre est introduit par « dès » et daté afin de ne pas transformer une annonce temporaire de marketplace en promesse permanente.</p></div>
<p>L’offre peut intéresser les personnes qui veulent {esc(offer.use_case)}. Selon la fiche sélectionnée, GamsGo peut proposer {esc(str(copy['format']))}. Ce détail change le niveau de contrôle, de confidentialité et de simplicité de renouvellement.</p>
<h2>Ce qu’il faut vérifier avant de commander</h2><ul class="check-list">{checked}<li>Le prix total, les frais et la devise au panier.</li><li>La note du vendeur, le délai de livraison et la protection indiquée.</li></ul>
<div class="warning-box"><strong>Point de vigilance :</strong> {esc(str(copy['risk']))} {esc(offer.specific_check.capitalize())}.</div>
<h2>Compte, invitation, clé ou recharge : ne pas les confondre</h2>
<p>Un compte fourni par un vendeur ne donne pas le même contrôle qu’un abonnement activé sur votre propre compte. Une invitation peut être retirée par l’administrateur. Une clé peut dépendre d’une région ou d’une version. Une recharge personnelle est généralement plus simple pour conserver vos réglages, mais elle exige parfois de transmettre un identifiant ou d’effectuer une procédure précise.</p>
<p>Lisez la section de livraison avant le paiement. N’utilisez jamais un mot de passe déjà employé ailleurs et ne communiquez aucun code de double authentification sauf si la procédure officielle, clairement décrite dans la commande, l’exige et que vous comprenez exactement l’accès accordé.</p>
<h2>Comment comparer correctement l’offre {esc(offer.service)}</h2>
<ol><li>Ouvrez le catalogue avec le lien partenaire EuroMalin.</li><li>Recherchez {esc(offer.service)} et comparez les formules équivalentes.</li><li>Vérifiez le type d’accès, la région, la durée et la garantie.</li><li>Saisissez <code>{GAMSGO_CODE}</code> dans le champ promotionnel s’il est disponible.</li><li>Comparez le total final à l’offre officielle, sans vous fier uniquement au pourcentage annoncé.</li><li>Conservez une capture de la fiche et testez la livraison immédiatement.</li></ol>
<h2>Le code promo GamsGo {GAMSGO_CODE}</h2>
<p>Le code partenaire EuroMalin est <strong><code>{GAMSGO_CODE}</code></strong>. Il doit rester visible avant la validation du paiement, mais EuroMalin n’annonce pas un pourcentage fixe : l’éligibilité peut dépendre du produit, du vendeur, de la période ou du compte client. Si le panier ne montre aucune économie, considérez que le code ne s’applique pas à cette commande.</p>
{promo_cta(offer.service, compact=True)}
{related_guides(offer)}
<h2>Questions fréquentes</h2><div class="faq">{''.join(f'<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>' for q, a in faq)}</div>
<h2>Sources et date de contrôle</h2><p>Comparaison effectuée le {DISPLAY_DATE} à partir du <a href="{CATALOG_URL}" target="_blank" rel="noopener noreferrer">catalogue public GamsGo en français</a>. La disponibilité et les conditions évoluent : relisez toujours la fiche et le panier. Le bouton commercial utilise le <a href="{GAMSGO_URL}" target="_blank" rel="sponsored noopener noreferrer">lien partenaire standard EuroMalin</a>.</p>
</article><aside class="sidebar"><div class="sidebar-card"><div class="kicker">Catalogue complet</div><h3>Toutes les offres GamsGo comparées</h3><a class="btn ghost" href="{HUB_SLUG}.html">Voir le tableau</a></div><div class="sidebar-card"><div class="kicker">Code EuroMalin</div><h3>{GAMSGO_CODE}</h3><p>À tester au panier, puis vérifier sur le total.</p></div></aside></div></section></main>""" + footer()


def related_guides(offer: Offer) -> str:
    peers = sorted(
        (item for item in OFFERS if item.category == offer.category and item.slug != offer.slug),
        key=lambda item: item.service.casefold(),
    )
    if not peers:
        return ""
    insertion = next(
        (index for index, item in enumerate(peers) if item.service.casefold() > offer.service.casefold()),
        len(peers),
    )
    choices = [peers[(insertion - 1) % len(peers)], peers[insertion % len(peers)]]
    links = "".join(
        f'<li><a href="{item.slug}.html">{esc(item.service)} sur GamsGo : prix et précautions</a></li>'
        for item in choices
    )
    return f"""<!-- seo-related-gamsgo:begin -->
<section class="related-guides" aria-labelledby="related-gamsgo"><h2 id="related-gamsgo">Comparer des offres similaires</h2><ul>{links}<li><a href="{HUB_SLUG}.html">Catalogue GamsGo complet et prix relevés</a></li><li><a href="gamsgo-avis-2026.html">Avis GamsGo 2026 : fiabilité et risques</a></li></ul></section>
<!-- seo-related-gamsgo:end -->"""


def hub_page() -> tuple[str, str, str]:
    current_rows = current_catalog_rows()
    new_current_count = sum(1 for _, slug, _, _ in current_rows if slug.startswith("gamsgo-"))
    title = f"Catalogue GamsGo complet : offres présentes et guides avec le code {GAMSGO_CODE}"
    description = f"Comparatif du catalogue GamsGo vérifié le {DISPLAY_DATE} : offres déjà couvertes, nouveaux guides EuroMalin, code {GAMSGO_CODE} et lien partenaire."
    faq = [
        ("Combien d’offres ont été comparées ?", f"Le contrôle couvre {len(current_rows)} familles de services visibles après ouverture de toutes les catégories du catalogue public."),
        ("Toutes les offres ont-elles un prix fixe ?", "Non. Une partie du catalogue relève de la marketplace et varie selon le vendeur, le pays, la durée, la devise et la méthode d’accès."),
        (f"Le code {GAMSGO_CODE} donne-t-il toujours une remise ?", "Non. Il faut le tester au panier et vérifier la réduction réellement appliquée avant de payer."),
        ("Pourquoi certaines offres ont-elles plusieurs pages ?", "Apple, Adobe ou YouTube peuvent apparaître dans plusieurs catégories ou formules. Le tableau renvoie vers le guide EuroMalin le plus proche de l’usage recherché."),
    ]
    groups = []
    for category in ("Streaming", "Musique", "IA", "Logiciels", "Gaming"):
        rows = []
        for service, slug, row_category, record in current_rows:
            if row_category != category:
                continue
            price = (
                f"dès {format_eur(float(record['monthly']))} €/mois"
                if record.get("monthly") is not None
                else f"dès {format_eur(float(record['price']))} €"
            )
            rows.append((service, slug, price))
        rows.sort(key=lambda row: row[0].casefold())
        body = "".join(f'<tr><td><a href="{esc(slug)}.html">{esc(service)}</a></td><td>{esc(price)}</td><td><a href="{esc(slug)}.html">Lire le guide</a></td></tr>' for service, slug, price in rows)
        groups.append(f'<h3>{category} — {len(rows)} offres ou familles</h3><div class="responsive-table"><table><thead><tr><th>Service</th><th>Prix relevé</th><th>Page</th></tr></thead><tbody>{body}</tbody></table></div>')
    page_head = head(
        title,
        description,
        HUB_SLUG,
        faq,
        seo_title=f"Catalogue GamsGo 2026 : offres, prix et code {GAMSGO_CODE}",
        seo_description=(
            f"Catalogue GamsGo vérifié le {DISPLAY_DATE} : prix relevés, guides par service, "
            f"risques à contrôler et code {GAMSGO_CODE} à tester au panier."
        ),
    ).replace("2026-07-24", TODAY)
    content = page_head + header() + f"""<main id="main"><section class="hero-mini"><div class="container"><div class="breadcrumbs"><a href="../index.html">Accueil</a> · <a href="../articles.html">Articles</a> · GamsGo</div><div class="hero-card"><div class="eyebrow">Audit complet • {DISPLAY_DATE}</div><h1>{esc(title)}</h1><p class="lead">{esc(description)}</p></div></div></section>
<section class="section"><div class="container page-grid"><article class="hero-card article">{disclosure()}
<figure class="article-hero"><img class="article-hero-image" src="../assets/img/articles/{HUB_SLUG}.jpg" alt="Catalogue GamsGo comparé par EuroMalin" loading="eager" decoding="async" width="1200" height="675"/><figcaption class="article-hero-credit">Illustration EuroMalin • audit du {DISPLAY_DATE}</figcaption></figure>
<div class="fact-strip"><div><strong>{len(current_rows)}</strong><span>offres ou familles comparées</span></div><div><strong>{new_current_count}</strong><span>guides GamsGo dédiés</span></div><div><strong>{GAMSGO_CODE}</strong><span>code à tester</span></div></div>
{promo_cta("le catalogue complet")}
<h2>Résultat de la comparaison EuroMalin / GamsGo</h2><div class="verdict-box"><span class="verdict-box__label">Catalogue entièrement déplié</span><p>L’audit du {DISPLAY_DATE} couvre {len(current_rows)} familles actuellement visibles, y compris les offres cachées derrière les boutons « Voir plus ». Chaque ligne renvoie vers un guide EuroMalin et affiche un prix « dès » daté, le code {GAMSGO_CODE}, le lien partenaire standard et les contrôles adaptés.</p></div>
<p>Le périmètre comprend les abonnements numériques visibles dans le catalogue et dans sa navigation étendue : streaming, musique, intelligence artificielle, logiciels et abonnements gaming. Les recharges, comptes, objets, cartes cadeaux et monnaies de centaines de jeux restent des inventaires marketplace mouvants ; ils sont traités par familles dans les guides gaming existants plutôt que par une page mince pour chaque annonce vendeur.</p>
<div class="warning-box"><strong>Important :</strong> « présent au catalogue » ne signifie pas « prix garanti ». Les vendeurs, durées, méthodes de partage, régions, délais et garanties changent. Le panier et la fiche de commande font foi.</div>
<h2>Toutes les offres comparées</h2>{''.join(groups)}
<h2>Comment utiliser ce dossier</h2><ol><li>Choisissez une catégorie puis ouvrez le guide du service.</li><li>Vérifiez le format livré et le risque spécifique avant de regarder le prix.</li><li>Accédez à GamsGo avec le lien partenaire EuroMalin.</li><li>Testez le code <code>{GAMSGO_CODE}</code> si le champ est proposé.</li><li>Comparez le total avec l’offre officielle et conservez la fiche avant paiement.</li></ol>
<h2>Questions fréquentes</h2><div class="faq">{''.join(f'<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>' for q, a in faq)}</div>
<h2>Source</h2><p><a href="{CATALOG_URL}" target="_blank" rel="noopener noreferrer">Catalogue public GamsGo en français</a>, navigation des catégories et pages visibles, contrôlés le {DISPLAY_DATE}. Les liens commerciaux utilisent exclusivement <a href="{GAMSGO_URL}" target="_blank" rel="sponsored noopener noreferrer">le lien partenaire standard EuroMalin</a>.</p>{promo_cta("le catalogue complet", compact=True)}
</article><aside class="sidebar"><div class="sidebar-card"><div class="kicker">Transparence</div><h3>Prix variables</h3><p>Nous ne transformons pas un prix temporaire de marketplace en promesse permanente.</p></div><div class="sidebar-card"><div class="kicker">Code partenaire</div><h3>{GAMSGO_CODE}</h3><p>À tester au panier.</p></div></aside></div></section></main>""" + footer()
    return title, description, content


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "arialbd.ttf" if bold else "arial.ttf"
    path = Path("C:/Windows/Fonts") / name
    return ImageFont.truetype(str(path), size=size)


def make_cover(slug: str, service: str, category: str) -> None:
    IMAGES.mkdir(parents=True, exist_ok=True)
    path = IMAGES / f"{slug}.jpg"
    accent = CATEGORY_COPY.get(category, CATEGORY_COPY["Logiciels"])["color"]
    image = Image.new("RGB", (1200, 675), (9, 30, 43))
    draw = ImageDraw.Draw(image)
    for y in range(675):
        ratio = y / 674
        base = tuple(round((1 - ratio) * a + ratio * b) for a, b in zip((9, 30, 43), (18, 62, 65)))
        draw.line((0, y, 1200, y), fill=base)
    draw.ellipse((820, -180, 1320, 320), fill=tuple(min(255, int(c * .65)) for c in accent))
    draw.ellipse((940, 420, 1280, 760), outline=accent, width=8)
    draw.rounded_rectangle((72, 70, 310, 126), radius=28, fill=accent)
    draw.text((100, 83), "GAMSGO", font=font(25, True), fill=(8, 26, 37))
    lines = textwrap.wrap(service, width=22)[:3]
    y = 190
    for line in lines:
        draw.text((72, y), line, font=font(64, True), fill=(250, 252, 252))
        y += 76
    draw.text((76, y + 14), "OFFRE • GUIDE • PRECAUTIONS", font=font(24, True), fill=accent)
    draw.rounded_rectangle((72, 520, 490, 606), radius=18, fill=(255, 205, 82))
    draw.text((103, 541), f"CODE  {GAMSGO_CODE}", font=font(34, True), fill=(19, 42, 52))
    draw.text((930, 605), "EuroMalin", font=font(25, True), fill=(235, 244, 244))
    image.save(path, "JPEG", quality=88, optimize=True, progressive=True)


def remove_cards(text: str, slugs: list[str]) -> str:
    for slug in slugs:
        text = re.sub(rf'<article class="article-card"[^>]*>(?:(?!</article>).)*?href="articles/{re.escape(slug)}\.html"(?:(?!</article>).)*?</article>', "", text, flags=re.S)
    return text


def update_listing(generated: list[tuple[str, str, str, str]]) -> None:
    path = ROOT / "articles.html"
    text = path.read_text(encoding="utf-8")
    text = re.sub(re.escape(START) + r".*?" + re.escape(END), "", text, flags=re.S)
    text = remove_cards(text, [item[0] for item in generated])
    block = START + "".join(card(*item) for item in generated) + END
    text = text.replace('<div class="grid-3">', '<div class="grid-3">' + block, 1)
    total = len(list(ARTICLES.glob("*.html")))
    text = re.sub(r"\d+ articles déjà intégrés", f"{total} articles déjà intégrés", text, count=1)
    path.write_text(text, encoding="utf-8")


def update_feature_pages(hub: tuple[str, str, str, str]) -> None:
    for filename, marker in (("index.html", "GAMSGO-CATALOG-HOME"), ("economies.html", "GAMSGO-CATALOG-ECONOMIES")):
        path = ROOT / filename
        text = path.read_text(encoding="utf-8")
        start = f"<!-- {marker}:START -->"
        end = f"<!-- {marker}:END -->"
        text = re.sub(re.escape(start) + r".*?" + re.escape(end), "", text, flags=re.S)
        text = remove_cards(text, [HUB_SLUG])
        block = start + card(*hub) + end
        text = text.replace('<div class="grid-3">', '<div class="grid-3">' + block, 1)
        path.write_text(text, encoding="utf-8")


def update_sitemap(slugs: list[str]) -> None:
    path = ROOT / "sitemap.xml"
    text = path.read_text(encoding="utf-8")
    for slug in slugs:
        loc = f"https://euromalin.com/articles/{slug}.html"
        pattern = rf"(<loc>{re.escape(loc)}</loc>\s*<lastmod>)[^<]+(</lastmod>)"
        if re.search(pattern, text):
            text = re.sub(pattern, rf"\g<1>{TODAY}\g<2>", text)
        else:
            entry = f"\n  <url>\n    <loc>{loc}</loc>\n    <lastmod>{TODAY}</lastmod>\n    <changefreq>monthly</changefreq>\n    <priority>0.8</priority>\n  </url>\n"
            text = text.replace("</urlset>", entry + "</urlset>")
    path.write_text(text, encoding="utf-8")


def update_thumbnail_manifest(offers: list[Offer]) -> None:
    query_groups = {
        "Streaming": (
            "streaming television cinema living room",
            "news media sports television",
        ),
        "Musique": ("headphones music audio listening",),
        "IA": (
            "artificial intelligence creative workstation",
            "coding software developer laptop",
            "video editing creator studio",
        ),
        "Logiciels": (
            "software productivity laptop desk",
            "cybersecurity privacy laptop",
            "digital design creative workspace",
            "business analytics computer dashboard",
        ),
        "Gaming": ("gaming console controller setup",),
    }
    manifest: dict[str, str] = {}
    counters = {category: 0 for category in query_groups}
    for offer in sorted(offers, key=lambda item: item.slug):
        choices = query_groups[offer.category]
        index = counters[offer.category]
        manifest[offer.slug] = choices[index % len(choices)]
        counters[offer.category] += 1
    manifest[HUB_SLUG] = "streaming software subscriptions laptop"
    path = ROOT / "scripts" / "gamsgo_catalog_thumbnail_queries.json"
    path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    ARTICLES.mkdir(exist_ok=True)
    generated: list[tuple[str, str, str, str]] = []
    for offer in OFFERS:
        (ARTICLES / f"{offer.slug}.html").write_text(page(offer), encoding="utf-8")
        if offer.price_record:
            generated.append((offer.slug, offer.title, offer.description, f"GamsGo • {offer.category}"))

    hub_title, hub_description, hub_html = hub_page()
    (ARTICLES / f"{HUB_SLUG}.html").write_text(hub_html, encoding="utf-8")
    hub = (HUB_SLUG, hub_title, hub_description, "Catalogue GamsGo")
    generated.sort(key=lambda item: (item[3], item[1].casefold()))
    generated.insert(0, hub)
    update_listing(generated)
    update_feature_pages(hub)
    update_sitemap([offer.slug for offer in OFFERS] + [HUB_SLUG])
    update_thumbnail_manifest([offer for offer in OFFERS if offer.price_record])
    print(
        f"Built {len(OFFERS)} GamsGo guides, including {len(generated) - 1} "
        "current priced offers, plus the comparison hub."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
