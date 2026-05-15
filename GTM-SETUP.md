# Configuration Google Tag Manager pour EuroMalin

## 1. Créer le compte GTM

1. Va sur https://tagmanager.google.com
2. Connecte-toi avec `outoftouch280@gmail.com` (le même compte Google que Analytics)
3. Clique **"Créer un compte"**
4. Nom du compte : `EuroMalin`
5. Pays : France
6. Conteneur : `euromalin.com`
7. Type : Web
8. Accepte les CGU → clic **"Créer"**

## 2. Copier le GTM ID

Le GTM ID ressemble à `GTM-XXXXXXX`. Il faut le copier-coller dans le fichier :

Modifie `/home/yusuf/.openclaw/workspace/euromalin-repo/assets/tracking.js` :
- Remplace `GTM-XXXXXXX` par le vrai ID

Puis relance le script pour mettre à jour toutes les pages :
```bash
cd /home/yusuf/.openclaw/workspace/euromalin-repo
python3 -c "
import os
GTM = 'GTM-TONREELID'
for root, dirs, files in os.walk('.'):
    if '.git' in root: continue
    for f in files:
        if f.endswith('.html'):
            fp = os.path.join(root, f)
            html = open(fp).read()
            html = html.replace('GTM-XXXXXXX', GTM)
            open(fp, 'w').write(html)
print('✅ GTM ID mis à jour')
"
git add -A && git commit -m "chore: activer GTM ID réel" && git push
```

## 3. Tags à créer dans GTM

### Tag 1 : GA4 - Page View (si pas déjà fait)
- Type : **Google Analytics : GA4 Event**
- Measurement ID : `G-DXH0N60DDB`
- Event Name : `page_view`
- Trigger : **All Pages**

### Tag 2 : GA4 - Affiliate Click
- Type : **Google Analytics : GA4 Event**
- Measurement ID : `G-DXH0N60DDB`
- Event Name : `affiliate_click`
- Parameters :
  - `merchant_name` = `{{DLV - merchant_name}}`
  - `merchant_label` = `{{DLV - merchant_label}}`
  - `offer_type` = `{{DLV - offer_type}}`
  - `article_slug` = `{{DLV - article_slug}}`
  - `cta_position` = `{{DLV - cta_position}}`
  - `button_text` = `{{DLV - button_text}}`
- Trigger : **Custom Event** → `affiliate_click`

### Tag 3 : GA4 - CTA Click
- Type : **Google Analytics : GA4 Event**
- Measurement ID : `G-DXH0N60DDB`
- Event Name : `cta_click`
- Parameters :
  - `cta_type` = `{{DLV - cta_type}}`
  - `article_slug` = `{{DLV - article_slug}}`
- Trigger : **Custom Event** → `cta_click`

### 🔧 Variables (Data Layer)
Créer ces **Variables de la couche de données** :
- `DLV - merchant_name` → Data Layer Variable Name : `merchant_name`
- `DLV - merchant_label` → Data Layer Variable Name : `merchant_label`
- `DLV - offer_type` → Data Layer Variable Name : `offer_type`
- `DLV - article_slug` → Data Layer Variable Name : `article_slug`
- `DLV - cta_position` → Data Layer Variable Name : `cta_position`
- `DLV - button_text` → Data Layer Variable Name : `button_text`
- `DLV - cta_type` → Data Layer Variable Name : `cta_type`

### Étape 4 : Publier
1. Clique **"Soumettre"** en haut à droite
2. Nom de la version : `V1 - EuroMalin tracking events`
3. Publier

## 4. Vérification
- Ouvre euromalin.com en navigation privée
- Active l'extension **Tag Assistant** (Google) ou `gtm_preview` dans l'URL
- Clique sur un lien iGraal ou Amazon
- Vérifie que l'événement `affiliate_click` apparaît dans la Preview GTM

## 5. Rapports GA4
Dans Google Analytics, les événements seront visibles dans :
- **Rapports → Engagement → Événements**
- Tu verras : `affiliate_click`, `cta_click`
- Tu peux créer des **Explorations** pour voir quels articles génèrent le plus de clics
