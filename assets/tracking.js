/**
 * EuroMalin - Affiliate Click Tracking
 * Envoie les événements à GA4 + DataLayer (prêt pour GTM)
 * 
 * Installation : GTM container à créer sur tagmanager.google.com
 * GTM ID à configurer : Remplacer GTM-XXXXXXX dans le <head>
 * 
 * Événements trackés :
 * - affiliate_click : clic sur lien iGraal, Amazon, GamsGo, eBuyClub
 * - cta_click : clic sur CTA interne (article, bon plan)
 * - page_view : vue de page (déjà géré par GA4)
 */

(function() {
  'use strict';

  // === CONFIG ===
  const TRACKING = {
    ga4Enabled: typeof gtag === 'function',
    debug: false  // Passe à true pour voir les logs en console
  };

  function log(...args) {
    if (TRACKING.debug) console.log('[Tracking]', ...args);
  }

  /**
   * Identifie le type de lien affilié à partir de l'URL
   */
  function getAffiliateData(url) {
    if (!url) return null;

    if (url.includes('fr.igraal.com')) {
      return { merchant: 'igraal', type: 'cashback', label: 'iGraal' };
    }
    if (url.includes('amazon.fr')) {
      return { merchant: 'amazon', type: 'product', label: 'Amazon' };
    }
    if (url.includes('gamsgo.com')) {
      return { merchant: 'gamsgo', type: 'subscription', label: 'GamsGo' };
    }
    if (url.includes('ebuyclub.com')) {
      return { merchant: 'ebuyclub', type: 'cashback', label: 'eBuyClub' };
    }
    return null;
  }

  /**
   * Extrait le slug de l'article depuis l'URL courante
   */
  function getArticleSlug() {
    const path = window.location.pathname;
    const match = path.match(/articles\/(.+)\.html/);
    return match ? match[1] : 'homepage';
  }

  /**
   * Envoie l'événement à GA4 + DataLayer
   */
  function trackEvent(eventName, params) {
    log('Event:', eventName, params);
    
    // 1. DataLayer (prêt pour GTM)
    if (window.dataLayer) {
      window.dataLayer.push({
        event: eventName,
        ...params
      });
    }

    // 2. GA4 direct (si gtag chargé)
    if (TRACKING.ga4Enabled) {
      gtag('event', eventName, params);
    }
  }

  /**
   * Intercepte les clics sur les liens affiliés
   */
  function setupClickTracking() {
    document.addEventListener('click', function(e) {
      const link = e.target.closest('a');
      if (!link || !link.href) return;

      const affiliate = getAffiliateData(link.href);
      const articleSlug = getArticleSlug();

      // CTA position dans la page
      const rect = link.getBoundingClientRect();
      const viewportMid = window.innerHeight / 2;
      const ctaPosition = rect.top < viewportMid ? 'above-fold' : 'below-fold';

      // Texte du bouton
      const buttonText = link.textContent.trim().substring(0, 60);

      if (affiliate) {
        // Clic sur lien affilié
        trackEvent('affiliate_click', {
          merchant_name: affiliate.merchant,
          merchant_label: affiliate.label,
          offer_type: affiliate.type,
          article_slug: articleSlug,
          cta_position: ctaPosition,
          button_text: buttonText,
          link_url: link.href.substring(0, 200),
          page_url: window.location.href
        });
        log(`🔗 Clic affilié: ${affiliate.label} depuis ${articleSlug}`);
      } else if (link.href.includes(window.location.hostname) && 
                 link.href.includes('/bons-plans/')) {
        // Clic vers une fiche bon plan interne
        trackEvent('cta_click', {
          cta_type: 'bon-plan',
          article_slug: articleSlug,
          cta_position: ctaPosition,
          button_text: buttonText,
          target_url: link.href
        });
        log(`📄 Clic bon plan: ${buttonText} depuis ${articleSlug}`);
      }
    }, true); // capture phase pour intercepter avant navigation
  }

  // === INIT ===
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupClickTracking);
  } else {
    setupClickTracking();
  }

  log('✅ Tracking initialisé. Article:', getArticleSlug());
})();
