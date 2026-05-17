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
    GAMSGO: {
      url: 'https://www.gamsgo.com/partner/Px5AZ',
      promo: 'WPQTU',
      name: 'GamsGo',
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
      a.setAttribute('href', conf.url);
      a.setAttribute('target', '_blank');
      a.setAttribute('rel', 'sponsored noopener noreferrer');
    });
  });
})();
