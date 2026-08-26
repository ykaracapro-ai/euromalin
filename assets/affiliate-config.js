/**
 * Configuration centralisée des liens d'affiliation EuroMalin.
 * Source unique de vérité — éditez ici, ça se propage partout via script.js.
 *
 * Convention rel pour les liens affiliés :
 *   target="_blank" rel="sponsored noopener noreferrer"
 */
(function () {
  'use strict';

  window.EUROMALIN_AFFILIATES = Object.freeze({
    U7BUY: {
      url: 'https://www.u7buy.com?referral-code=CzMdAgd4',
      referral: 'CzMdAgd4',
      promo: 'EURO10',
      discount: '5%',
      name: 'U7BUY',
    },
    GAMSGO: {
      url: 'https://www.gamsgo.com/partner/Px5AZ',
      promo: 'WPQTU',
      name: 'GamsGo',
    },
    GAMSGO_SHOWCASE: {
      url: 'https://www.gamsgo.com/showcase/euromalin',
      promo: 'WPQTU',
      name: 'Sélection EuroMalin sur GamsGo',
    },
    GAMSGO_PLAYSTATION: {
      url: 'https://www.gamsgo.com/fr/accounts/playstation/partner/Px5AZ',
      promo: 'WPQTU',
      name: 'GamsGo PlayStation',
    },
    WIDILO: {
      url: 'https://www.widilo.fr/i/YKHR50',
      name: 'Widilo',
    },
    IGRAAL: {
      url: 'https://fr.igraal.com/parrainage?parrain=AG_69131d3a40583&utm_medium=raf&utm_source=refer_friend',
      name: 'iGraal',
    },
  });

  // Au chargement, on patche les ancres data-aff="<KEY>" pour qu'elles
  // pointent vers l'URL centralisée — pratique pour ajouter de nouveaux
  // CTA via attribut HTML sans dupliquer l'URL.
  document.addEventListener('DOMContentLoaded', function () {
    var aff = window.EUROMALIN_AFFILIATES;
    document.querySelectorAll('a[data-aff]').forEach(function (a) {
      var key = a.getAttribute('data-aff');
      var conf = aff[key];
      if (!conf) return;
      var href = conf.url;
      a.setAttribute('href', href);
      a.setAttribute('target', '_blank');
      a.setAttribute('rel', 'sponsored noopener noreferrer');
    });
  });
})();
