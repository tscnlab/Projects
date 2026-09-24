/* Progressive enhancement: all opportunities and links work without JavaScript. */
(() => {
  'use strict';
  const search = document.querySelector('#project-search');
  if (!search) return;
  const location = document.querySelector('#location-filter');
  const cards = [...document.querySelectorAll('.project-card')];
  const count = document.querySelector('#result-count');
  const empty = document.querySelector('#no-results');
  const normalise = value => value.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/muenchen|munchen/g, 'munich').replace(/tuebingen/g, 'tubingen').replace(/master[’']s/g, 'masters');
  const index = cards.map(card => normalise(card.dataset.search));
  const params = new URLSearchParams(window.location.search);
  search.value = params.get('q') || '';
  if ([...location.options].some(option => option.value === params.get('location'))) location.value = params.get('location');
  function filter(updateUrl = true) {
    const words = normalise(search.value.trim()).split(/\s+/).filter(Boolean);
    let shown = 0;
    cards.forEach((card, i) => {
      const match = words.every(word => index[i].includes(word)) && (!location.value || card.dataset.locations.split('|').includes(location.value));
      card.hidden = !match;
      if (match) shown++;
    });
    count.textContent = `${shown} ${shown === 1 ? 'project' : 'projects'}${shown < cards.length ? ` of ${cards.length}` : ''}`;
    empty.hidden = shown !== 0;
    if (updateUrl) {
      const url = new URL(window.location.href);
      search.value.trim() ? url.searchParams.set('q', search.value.trim()) : url.searchParams.delete('q');
      location.value ? url.searchParams.set('location', location.value) : url.searchParams.delete('location');
      window.history.replaceState(null, '', url);
    }
  }
  search.addEventListener('input', () => filter());
  location.addEventListener('change', () => filter());
  document.querySelector('#reset-search').addEventListener('click', () => {search.value = ''; location.value = ''; filter(); search.focus();});
  window.addEventListener('pageshow', () => filter(false));
  filter(false);
})();
