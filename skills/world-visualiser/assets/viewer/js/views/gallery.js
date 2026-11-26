// gallery.js: 3D-tilt perspective artwork & holographic entity card gallery respecting global filters.
(function () {
  'use strict';
  if (typeof WB === 'undefined' || !WB || !WB.registerView) return;
  const { el, svg, safeImageSrc } = WB.util;
  const D = WB.data;

  function hashStr(str) {
    let h = 2166136261;
    const s = String(str || '');
    for (let i = 0; i < s.length; i++) {
      h ^= s.charCodeAt(i);
      h = Math.imul(h, 16777619);
    }
    return h >>> 0;
  }

  function buildProceduralCrest(node, col) {
    const h = hashStr(node.id || node.name);
    const sides = 5 + (h % 4); // 5..8 sided sigil
    const rot = (h >> 4) % 360;
    const ticks = 8 + ((h >> 9) % 9);
    const pts = [];
    for (let i = 0; i < sides; i++) {
      const a = ((i * 2 * Math.PI) / sides) - Math.PI / 2;
      const rad = i % 2 === 0 ? 40 : (24 + ((h >> 13) % 14));
      pts.push((60 + Math.cos(a) * rad).toFixed(1) + ',' + (60 + Math.sin(a) * rad).toFixed(1));
    }
    const tickEls = [];
    for (let i = 0; i < ticks; i++) {
      const a = (i * 2 * Math.PI) / ticks;
      const x1 = (60 + Math.cos(a) * 48).toFixed(1);
      const y1 = (60 + Math.sin(a) * 48).toFixed(1);
      const x2 = (60 + Math.cos(a) * 53).toFixed(1);
      const y2 = (60 + Math.sin(a) * 53).toFixed(1);
      tickEls.push(svg('line', { x1, y1, x2, y2, stroke: col, 'stroke-width': '1.2', 'stroke-opacity': '0.55' }));
    }
    const glyph = WB.typeGlyph[node.type] || '?';
    return svg('svg', {
      class: 'gal-holo-svg', viewBox: '0 0 120 120', 'aria-hidden': 'true',
    },
    svg('circle', { cx: '60', cy: '60', r: '52', fill: 'none', stroke: col, 'stroke-width': '0.8', 'stroke-dasharray': '3 4', 'stroke-opacity': '0.5' }),
    svg('circle', { cx: '60', cy: '60', r: '44', fill: 'none', stroke: col, 'stroke-width': '1', 'stroke-opacity': '0.35' }),
    ...tickEls,
    svg('polygon', {
      points: pts.join(' '), fill: col, 'fill-opacity': '0.12',
      stroke: col, 'stroke-width': '1.4', 'stroke-opacity': '0.78',
      transform: `rotate(${rot} 60 60)`,
    }),
    svg('circle', { cx: '60', cy: '60', r: '19', fill: 'var(--panel)', stroke: col, 'stroke-width': '1.8' }),
    svg('text', {
      x: '60', y: '67', 'text-anchor': 'middle', 'font-size': '20', 'font-weight': '800', fill: col,
      text: glyph,
    }));
  }

  function attachTilt(card) {
    if (typeof window.matchMedia === 'function' && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    card.addEventListener('pointermove', (ev) => {
      if (ev.pointerType === 'touch') return;
      const r = card.getBoundingClientRect();
      if (!r.width || !r.height) return;
      const px = (ev.clientX - r.left) / r.width;
      const py = (ev.clientY - r.top) / r.height;
      const rx = ((0.5 - py) * 11).toFixed(2) + 'deg';
      const ry = ((px - 0.5) * 11).toFixed(2) + 'deg';
      card.classList.add('tilting');
      card.style.setProperty('--rx', rx);
      card.style.setProperty('--ry', ry);
      card.style.setProperty('--mx', Math.round(px * 100) + '%');
      card.style.setProperty('--my', Math.round(py * 100) + '%');
    });
    card.addEventListener('pointerleave', () => {
      card.classList.remove('tilting');
      card.style.setProperty('--rx', '0deg');
      card.style.setProperty('--ry', '0deg');
    });
  }

  WB.registerView({
    id: 'gallery', title: 'Gallery', order: 60,
    create(container) {
      container.classList.add('gal');
      const allWithArt = () => D.nodes.filter((n) => !!safeImageSrc(n.image));
      const opts = {
        sort: 'name',
        mode: allWithArt().length > 0 ? 'art' : 'all',
      };

      const artModeBtn = el('button', { type: 'button', class: 'gal-seg-btn', 'aria-pressed': String(opts.mode === 'art'), text: 'Artwork Only' });
      const allModeBtn = el('button', { type: 'button', class: 'gal-seg-btn', 'aria-pressed': String(opts.mode === 'all'), text: 'All Entities (Holographic)' });
      const setMode = (m) => {
        opts.mode = m;
        artModeBtn.setAttribute('aria-pressed', String(m === 'art'));
        allModeBtn.setAttribute('aria-pressed', String(m === 'all'));
        render();
      };
      artModeBtn.addEventListener('click', () => setMode('art'));
      allModeBtn.addEventListener('click', () => setMode('all'));

      const sortSel = el('select', { 'aria-label': 'Sort gallery by' },
        el('option', { value: 'name', text: 'Name (A-Z)' }),
        el('option', { value: 'type', text: 'Entity type' }),
        el('option', { value: 'date', text: 'Date' }),
        el('option', { value: 'links', text: 'Most linked' }));
      sortSel.addEventListener('change', () => { opts.sort = sortSel.value; render(); });

      const countEl = el('span', { class: 'muted', role: 'status' });
      const bar = el('div', { class: 'gal-bar' },
        el('div', { class: 'gal-seg', role: 'group', 'aria-label': 'Gallery display mode' }, artModeBtn, allModeBtn),
        el('label', {}, 'Sort ', sortSel),
        countEl);
      const scroll = el('div', { class: 'gal-scroll' });
      container.append(bar, scroll);

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
        } else if (opts.sort === 'links') {
          copy.sort((a, b) => WB.degree(b.id) - WB.degree(a.id) || a.name.localeCompare(b.name));
        } else {
          copy.sort((a, b) => a.name.localeCompare(b.name));
        }
        return copy;
      }

      function render() {
        const totalArt = allWithArt();
        artModeBtn.textContent = 'Artwork Only (' + totalArt.length + ')';
        allModeBtn.textContent = 'All Entities (' + D.nodes.length + ')';

        if (opts.mode === 'art' && !totalArt.length) {
          countEl.textContent = '0 artworks';
          scroll.replaceChildren(
            el('div', { class: 'gal-empty' },
              el('h3', { text: 'No entity artwork yet' }),
              el('p', {}, 'Generate portraits, landscapes, faction emblems and items with the ',
                el('code', { text: 'world-art' }), ' skill, or place images in ',
                el('code', { text: 'output/images/<type>/<slug>.png' }), '.'),
              el('p', {}, 'Rebuild the viewer afterwards with ',
                el('code', { text: 'build_viewer.py' }), ' (add ',
                el('code', { text: '--embed-images' }), ' for a portable single file), or switch to ',
                el('strong', { text: 'All Entities' }), ' to browse holographic cards.')));
          return;
        }

        const pool = opts.mode === 'art' ? totalArt : D.nodes;
        const shown = sortNodes(pool.filter((n) => WB.passes(n)));
        const unit = opts.mode === 'art' ? (pool.length === 1 ? 'artwork' : 'artworks') : 'entities';
        countEl.textContent = shown.length + ' of ' + pool.length + ' ' + unit;

        if (!shown.length) {
          scroll.replaceChildren(
            el('div', { class: 'gal-empty' },
              el('h3', { text: opts.mode === 'art' ? 'No matching artwork' : 'No matching entities' }),
              el('p', { text: 'Nothing matches the current search, type or era filters.' })));
          return;
        }

        const artBanner = opts.mode === 'all' && totalArt.length === 0 ? el('div', { class: 'gal-art-banner' },
          el('span', {}, 'Showing procedural holographic cards. Run the ',
            el('code', { text: 'world-art' }), ' skill to generate portraits, landscapes, faction emblems and scenes.')) : null;

        const sel = WB.state.selected;
        const grid = el('div', { class: 'gal-grid', role: 'list', 'aria-label': 'Entity gallery' },
          shown.map((n) => {
            const src = safeImageSrc(n.image);
            const col = WB.colors.type[n.type] || '#888';
            const deg = WB.degree(n.id);
            const thumb = el('div', { class: 'gal-thumb' });

            if (src) {
              const img = el('img', { src, alt: n.name + ' artwork', loading: 'lazy' });
              img.addEventListener('error', () => {
                thumb.replaceChildren(el('div', { class: 'gal-holo' }, buildProceduralCrest(n, col)));
              });
              thumb.appendChild(img);
              thumb.appendChild(el('span', { class: 'gal-expand-pill', 'aria-hidden': 'true', text: 'Double-click to expand' }));
            } else {
              thumb.appendChild(el('div', { class: 'gal-holo' },
                buildProceduralCrest(n, col),
                el('span', { class: 'gal-holo-tag', 'aria-hidden': 'true', text: 'Hologram' })));
            }

            const isSel = n.id === sel;
            const card = el('button', {
              type: 'button',
              class: 'gal-card' + (isSel ? ' sel' : ''),
              style: '--card-col:' + col,
              role: 'listitem',
              'aria-pressed': String(isSel),
              'aria-label': n.name + ' (' + n.type + (n.date_label ? ', ' + n.date_label : '') + ')',
              onclick: () => WB.select(n.id),
              ondblclick: src ? () => WB.openLightbox(n, card) : null,
            },
            el('span', { class: 'gal-sheen', 'aria-hidden': 'true' }),
            thumb,
            el('div', { class: 'gal-body' },
              el('div', { class: 'gal-title', text: n.name }),
              el('div', { class: 'gal-meta' },
                el('span', { class: 'gal-badge', style: 'border-color:' + col },
                  el('span', { class: 'dot', style: 'background:' + col, 'aria-hidden': 'true' }),
                  n.type),
                n.date_label ? el('span', { text: n.date_label }) : (n.era ? el('span', { text: n.era }) : null),
                deg > 0 ? el('span', { class: 'gal-links-pill', text: deg + (deg === 1 ? ' link' : ' links') }) : null),
              n.summary ? el('p', { class: 'gal-summary', text: n.summary }) : null));

            attachTilt(card);
            return el('div', { class: 'gal-card-wrap' }, card);
          }));

        scroll.replaceChildren(...[artBanner, grid].filter(Boolean));
      }

      this.onSelect = () => render();
      this.onFilter = () => render();
      this.activate = () => render();
      render();
    },
  });
})();
