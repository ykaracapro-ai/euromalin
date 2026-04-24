
document.addEventListener('DOMContentLoaded', () => {
  const search = document.querySelector('[data-search]');
  if (!search) return;
  const cards = Array.from(document.querySelectorAll('[data-article-card]'));
  search.addEventListener('input', () => {
    const q = search.value.trim().toLowerCase();
    cards.forEach(card => {
      const text = card.innerText.toLowerCase();
      card.style.display = text.includes(q) ? '' : 'none';
    });
  });
});
