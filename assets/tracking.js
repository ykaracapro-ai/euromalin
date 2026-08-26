/**
 * EuroMalin - suivi des conversions affiliées.
 *
 * Charge GA4 sur les pages qui ne possèdent pas encore le tag de base, puis
 * mesure les clics commerciaux et les étapes fortes du parcours. Le garde-fou
 * global permet de charger ce fichier depuis le HTML ou depuis script.js sans
 * créer de double écouteur.
 */
(function () {
  'use strict';

  if (window.__euromalinTrackingReady) return;
  window.__euromalinTrackingReady = true;

  var MEASUREMENT_ID = 'G-DXH0N60DDB';
  var DEBUG = false;

  function log() {
    if (!DEBUG || !window.console) return;
    var args = Array.prototype.slice.call(arguments);
    args.unshift('[EuroMalin tracking]');
    console.log.apply(console, args);
  }

  function ensureGa4() {
    window.dataLayer = window.dataLayer || [];
    window.gtag = window.gtag || function () { window.dataLayer.push(arguments); };

    var selector = 'script[src*="googletagmanager.com/gtag/js?id=' + MEASUREMENT_ID + '"]';
    if (document.querySelector(selector)) return;

    var script = document.createElement('script');
    script.async = true;
    script.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(MEASUREMENT_ID);
    document.head.appendChild(script);

    window.gtag('js', new Date());
    window.gtag('config', MEASUREMENT_ID);
  }

  function getAffiliateData(rawUrl) {
    if (!rawUrl) return null;
    var url = rawUrl.toLowerCase();

    if (url.indexOf('fr.igraal.com') !== -1) {
      return { merchant: 'igraal', offerType: 'cashback', destinationType: 'referral' };
    }
    if (url.indexOf('amazon.fr') !== -1) {
      return { merchant: 'amazon', offerType: 'product', destinationType: 'product' };
    }
    if (url.indexOf('gamsgo.com/showcase/') !== -1) {
      return { merchant: 'gamsgo', offerType: 'subscription', destinationType: 'showcase' };
    }
    if (url.indexOf('gamsgo.com') !== -1) {
      return { merchant: 'gamsgo', offerType: 'subscription', destinationType: 'store' };
    }
    if (url.indexOf('u7buy.com') !== -1) {
      return { merchant: 'u7buy', offerType: 'marketplace', destinationType: 'store' };
    }
    if (url.indexOf('ebuyclub.com') !== -1) {
      return { merchant: 'ebuyclub', offerType: 'cashback', destinationType: 'referral' };
    }
    if (url.indexOf('widilo.fr') !== -1) {
      return { merchant: 'widilo', offerType: 'cashback', destinationType: 'referral' };
    }
    return null;
  }

  function getPageKey() {
    var path = window.location.pathname || '/';
    if (path === '/' || path === '/index.html') return 'homepage';
    return path.replace(/^\//, '').replace(/\.html$/, '') || 'homepage';
  }

  function normaliseLabel(value) {
    return (value || '')
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9à-ÿ]+/g, '-')
      .replace(/^-+|-+$/g, '')
      .substring(0, 60) || 'link';
  }

  function getCtaPosition(link) {
    if (link.closest('[data-conversion-panel]')) return 'conversion-panel';
    if (link.closest('.hero, .hero-mini')) return 'hero';
    if (link.closest('.gamsgo-promo, .affiliate-cta')) return 'inline-offer';
    if (link.closest('.site-header, .topbar, header')) return 'navigation';
    if (link.closest('footer')) return 'footer';
    return 'content';
  }

  function getDestinationPath(rawUrl) {
    try {
      var url = new URL(rawUrl);
      return (url.hostname + url.pathname).substring(0, 160);
    } catch (e) {
      return String(rawUrl || '').substring(0, 160);
    }
  }

  function trackEvent(eventName, params) {
    ensureGa4();
    window.gtag('event', eventName, params || {});
    log(eventName, params);
  }

  function setupClickTracking() {
    document.addEventListener('click', function (event) {
      var link = event.target && event.target.closest ? event.target.closest('a') : null;
      if (!link || !link.href) return;

      var affiliate = getAffiliateData(link.href);
      var buttonText = (link.textContent || '').trim().replace(/\s+/g, ' ').substring(0, 80);
      var ctaId = link.getAttribute('data-cta-id') || normaliseLabel(buttonText);
      var common = {
        page_key: getPageKey(),
        page_path: window.location.pathname,
        language: document.documentElement.lang || 'fr',
        cta_id: ctaId,
        cta_position: getCtaPosition(link),
        button_text: buttonText
      };

      if (affiliate) {
        trackEvent('affiliate_click', Object.assign({}, common, {
          merchant_name: affiliate.merchant,
          offer_type: affiliate.offerType,
          destination_type: affiliate.destinationType,
          destination_path: getDestinationPath(link.href)
        }));
        return;
      }

      var destination;
      try { destination = new URL(link.href); } catch (e) { return; }
      var isInternal = destination.hostname === window.location.hostname;
      var isTrackedCta = link.matches('[data-track="cta"], .btn') || !!link.closest('.hero-cta, .calc-ctas');
      if (isInternal && isTrackedCta) {
        trackEvent('cta_click', Object.assign({}, common, {
          destination_path: destination.pathname
        }));
      }
    }, true);
  }

  function setupCalculatorTracking() {
    var input = document.getElementById('indexCalcInput');
    if (!input) return;

    input.addEventListener('change', function () {
      var result = document.getElementById('indexLostAmount');
      trackEvent('calculator_complete', {
        page_key: getPageKey(),
        monthly_spend: Number(input.value) || 0,
        estimated_annual_savings: result ? Number((result.textContent || '').replace(/[^0-9]/g, '')) || 0 : 0
      });
    });
  }

  function init() {
    ensureGa4();
    setupClickTracking();
    setupCalculatorTracking();
  }

  window.euromalinTrack = trackEvent;

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
  } else {
    init();
  }
})();
