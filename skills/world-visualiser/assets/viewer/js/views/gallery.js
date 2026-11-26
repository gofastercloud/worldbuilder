// gallery.js: responsive entity artwork gallery view respecting global search, type and era filters.
(function () {
  'use strict';
  if (typeof WB === 'undefined' || !WB || !WB.registerView) return;
  const { el, safeImageSrc } = WB.util;
  const D = WB.data;

  WB.registerView({
    id: 'gallery', title: 'Gallery', order: 60,
    create(container) {
      container.classList.add('gal');
      const opts = { sort: 'name' };
      const sortSel = el('select', { 'aria-label': 'Sort gallery by' },
        el('option', { value: 'name', text: 'Name (A-Z)' }),
        el('option', { value: 'type', text: 'Entity type' }),
        el('option', { value: 'date', text: 'Date' }));
      sortSel.addEventListener('change', () => { opts.sort = sortSel.value; render(); });

      const countEl = el('span', { class: 'muted', role: 'status' });
      const bar = el('div', { class: 'gal-bar' },
        el('label', {}, 'Sort ', sortSel),
        countEl);
      const scroll = el('div', { class: 'gal-scroll' });
      container.append(bar, scroll);

      const allWithArt = () => D.nodes.filter((n) => !!safeImageSrc(n.image));

      function sortNodes(list) {
        const copy = list.slice();
        if (opts.sort === 'type') {
          copy.sort((a, b) => a.type.localeCompare(b.type) || a.name.localeCompare(b.name));
        } else if (opts.sort === 'date') {
          copy.sort((a, b) => {
            const ta = a.t === null || a.t === undefined ? Infinity : a.t;
            const tb = b.t === null || b.t === undefined ? Infinity : b.t;
            return ta - tb || a.name.localeCompare(b.name);
          });
        } else {
          copy.sort((a, b) => a.name.localeCompare(b.name));
        }
        return copy;
      }

      function render() {
        const totalArt = allWithArt();
        if (!totalArt.length) {
          countEl.textContent = '0 artworks';
          scroll.replaceChildren(
            el('div', { class: 'gal-empty' },
              el('h3', { text: 'No entity artwork yet' }),
              el('p', {}, 'Generate portraits, landscapes, faction emblems and items with the ',
                el('code', { text: 'world-art' }), ' skill, or place images in ',
                el('code', { text: 'output/images/<type>/<slug>.png' }), '.'),
              el('p', {}, 'Rebuild the viewer afterwards with ',
                el('code', { text: 'build_viewer.py' }), ' (add ',
                el('code', { text: '--embed-images' }), ' for a portable single file).')));
          return;
        }

        const shown = sortNodes(totalArt.filter((n) => WB.passes(n)));
        countEl.textContent = shown.length + ' of ' + totalArt.length + (totalArt.length === 1 ? ' artwork' : ' artworks');
        if (!shown.length) {
          scroll.replaceChildren(
            el('div', { class: 'gal-empty' },
              el('h3', { text: 'No matching artwork' }),
              el('p', { text: 'No entities with artwork match the current search, type or era filters.' })));
          return;
        }

        const sel = WB.state.selected;
        const grid = el('div', { class: 'gal-grid', role: 'list', 'aria-label': 'Entity artwork gallery' },
          shown.map((n) => {
            const src = safeImageSrc(n.image);
            const col = WB.colors.type[n.type] || '#888';
            const thumb = el('div', { class: 'gal-thumb' });
            const img = el('img', { src, alt: n.name + ' artwork', loading: 'lazy' });
            img.addEventListener('error', () => {
              thumb.replaceChildren(el('div', { class: 'gal-placeholder', 'aria-hidden': 'true', text: WB.typeGlyph[n.type] || '?' }));
            });
            thumb.appendChild(img);
            const isSel = n.id === sel;
            const card = el('button', {
              type: 'button',
              class: 'gal-card' + (isSel ? ' sel' : ''),
              role: 'listitem',
              'aria-pressed': String(isSel),
              'aria-label': n.name + ' (' + n.type + (n.date_label ? ', ' + n.date_label : '') + ')',
              onclick: () => WB.select(n.id),
              ondblclick: () => WB.openLightbox(n, card),
            },
            thumb,
            el('div', { class: 'gal-body' },
              el('div', { class: 'gal-title', text: n.name }),
              el('div', { class: 'gal-meta' },
                el('span', { class: 'gal-badge', style: 'border-color:' + col },
                  el('span', { class: 'dot', style: 'background:' + col, 'aria-hidden': 'true' }),
                  n.type),
                n.date_label ? el('span', { text: n.date_label }) : null),
              n.summary ? el('p', { class: 'gal-summary', text: n.summary }) : null));
            return card;
          }));
        scroll.replaceChildren(grid);
      }

      this.onSelect = () => render();
      this.onFilter = () => render();
      this.activate = () => render();
      render();
    },
  });
})();
