// core.js: data, shared state, event bus, helpers, lightbox and the detail panel. Defines the global WB.
const DATA = /*__WORLD_DATA__*/null;
const WB = (function () {
  'use strict';
  const empty = {
    version: 1, project: { name: '(no data)', present_t: null },
    calendar: { eras: [], t_min: 0, t_max: 1, present_t: null },
    nodes: [], edges: [], timeline: { events: [], traditions: [] }, map: { locations: [], routes: [] },
    climate: { zones: [], legend: {} }, life: { species_index: [] },
    economy: { resources: [], trade_routes: [], currencies: [], shocks: [] }, warnings: ['no data embedded'],
  };
  const data = Object.assign({}, empty, DATA || {});
  data.calendar = Object.assign({}, empty.calendar, data.calendar || {});
  data.timeline = Object.assign({}, empty.timeline, data.timeline || {});
  data.climate = Object.assign({}, empty.climate, data.climate || {});

  // ---- bus
  const handlers = {};
  const bus = {
    on(evt, fn) { (handlers[evt] = handlers[evt] || []).push(fn); },
    emit(evt, ...args) {
      (handlers[evt] || []).slice().forEach((fn) => {
        try { fn(...args); } catch (e) { console.error('WB handler for ' + evt + ' failed', e); }
      });
    },
  };

  // ---- colours (Okabe-Ito based; the type chip text and node shapes add redundancy)
  const typeColors = {
    character: '#56B4E9', location: '#009E73', faction: '#E69F00', item: '#CC79A7', 'magic-system': '#F0E442',
    arc: '#0072B2', event: '#D55E00', species: '#8C8C8C', race: '#B8860B', language: '#A6CEE3',
    lineage: '#7570B3', tradition: '#E7298A',
  };
  const typeGlyph = {
    character: 'C', location: 'L', faction: 'F', item: 'I', 'magic-system': 'M', arc: 'A', event: 'E',
    species: 'S', race: 'R', language: 'G', lineage: 'Y', tradition: 'T',
  };
  const colors = {
    type: typeColors,
    edge: { causes: '#D55E00', 'leaves-trace': '#E7298A', other: '#8C8C8C' },
    lineage: { selected: '#F0E442', up: '#56B4E9', down: '#E69F00' },
    zone(name) {
      const legend = data.climate.legend || {};
      return legend[name] || '#999999';
    },
  };

  const state = { selected: null, hover: null, highlight: null, activeView: null,
    filters: { types: new Set(), eras: new Set(), search: '' } };

  // ---- util
  function el(tag, attrs, ...children) { return build(document.createElement(tag), attrs, children); }
  function svg(tag, attrs, ...children) {
    return build(document.createElementNS('http://www.w3.org/2000/svg', tag), attrs, children);
  }
  function build(node, attrs, children) {
    for (const [k, v] of Object.entries(attrs || {})) {
      if (v === null || v === undefined || v === false) continue;
      if (k === 'class') node.setAttribute('class', v);
      else if (k === 'text') node.textContent = v;
      else if (k.startsWith('on') && typeof v === 'function') node.addEventListener(k.slice(2), v);
      else node.setAttribute(k, v === true ? '' : String(v));
    }
    const add = (c) => {
      if (c === null || c === undefined || c === false) return;
      if (Array.isArray(c)) c.forEach(add);
      else node.appendChild(c.nodeType ? c : document.createTextNode(String(c)));
    };
    children.forEach(add);
    return node;
  }
  function esc(str) {
    return String(str === null || str === undefined ? '' : str).replace(/[&<>"']/g,
      (ch) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
  }
  function safeImageSrc(src) {
    if (typeof src !== 'string') return null;
    const s = src.trim();
    if (!s) return null;
    if (s.startsWith('data:image/')) return s;
    if (/^[a-zA-Z][a-zA-Z0-9+.-]*:/.test(s) || s.startsWith('//')) return null;
    return s;
  }
  const cal = data.calendar;
  const span = () => Math.max(1e-9, (cal.t_max - cal.t_min));
  function tToX(t, w) { return ((t - cal.t_min) / span()) * w; }
  function fmtT(t) {
    if (t === null || t === undefined || isNaN(t)) return 'undated';
    const eras = cal.eras || [];
    for (let i = eras.length - 1; i >= 0; i--) {
      if (t >= eras[i].t0) return Math.floor(t - eras[i].t0) + ' ' + eras[i].prefix;
    }
    return String(Math.round(t * 10) / 10);
  }

  // ---- graph indexes
  const byId = new Map();
  data.nodes.forEach((n) => byId.set(n.id, n));
  const out = new Map();
  const inn = new Map();
  const edges = data.edges.filter((e) => byId.has(e.source) && byId.has(e.target));
  edges.forEach((e) => {
    if (!out.has(e.source)) out.set(e.source, []);
    if (!inn.has(e.target)) inn.set(e.target, []);
    out.get(e.source).push(e);
    inn.get(e.target).push(e);
  });
  const degree = (id) => (out.get(id) || []).length + (inn.get(id) || []).length;

  // Upstream and downstream along causal and memory edges (source -> target).
  function lineage(id) {
    const walk = (start, next) => {
      const seen = new Set();
      const queue = [start];
      while (queue.length) {
        const cur = queue.pop();
        for (const e of next(cur) || []) {
          if (!(e.causal || e.memory)) continue;
          const other = next === outOf ? e.target : e.source;
          if (!seen.has(other) && other !== start) { seen.add(other); queue.push(other); }
        }
      }
      return seen;
    };
    return { up: walk(id, inOf), down: walk(id, outOf) };
  }
  function outOf(id) { return out.get(id); }
  function inOf(id) { return inn.get(id); }

  let focusCache = { id: null, up: new Set(), down: new Set(), hl: null };
  function updateFocus() {
    const id = state.selected;
    const l = id ? lineage(id) : { up: new Set(), down: new Set() };
    focusCache = { id, up: l.up, down: l.down, hl: state.highlight };
  }

  // ---- lightbox
  let lbEl = null;
  let lbReturnFocus = null;
  function closeLightbox() {
    if (!lbEl || lbEl.hidden) return;
    lbEl.hidden = true;
    lbEl.replaceChildren();
    if (lbReturnFocus && typeof lbReturnFocus.focus === 'function') lbReturnFocus.focus();
    lbReturnFocus = null;
  }
  function openLightbox(node, triggerEl) {
    const src = node && safeImageSrc(node.image);
    if (!src) return;
    lbReturnFocus = triggerEl || document.activeElement;
    if (!lbEl) {
      lbEl = el('div', {
        class: 'wb-lightbox', role: 'dialog', 'aria-modal': 'true', hidden: true,
        onclick: (ev) => { if (ev.target === lbEl) closeLightbox(); },
      });
      document.body.appendChild(lbEl);
      document.addEventListener('keydown', (ev) => {
        if (ev.key === 'Escape' && lbEl && !lbEl.hidden) { ev.preventDefault(); closeLightbox(); }
      });
    }
    const closeBtn = el('button', { type: 'button', class: 'wb-lightbox-close', 'aria-label': 'Close artwork preview', onclick: closeLightbox, text: 'Close' });
    const badge = el('span', { class: 'chip', style: 'border-color:' + (colors.type[node.type] || '#888') },
      el('span', { class: 'dot', style: 'background:' + (colors.type[node.type] || '#888'), 'aria-hidden': 'true' }),
      node.type);
    lbEl.setAttribute('aria-label', node.name + ' artwork');
    lbEl.replaceChildren(
      el('div', { class: 'wb-lightbox-dialog' },
        el('img', { class: 'wb-lightbox-img', src, alt: node.name + ' artwork' }),
        el('div', { class: 'wb-lightbox-bar' },
          el('div', { class: 'wb-lightbox-title' }, el('strong', { text: node.name }), badge,
            node.date_label ? el('span', { class: 'muted', text: node.date_label }) : null),
          closeBtn)),
    );
    lbEl.hidden = false;
    closeBtn.focus();
  }

  const WBobj = {
    data, state, colors, bus, typeGlyph, edges, degree, openLightbox,
    focus() { return focusCache; },
    select(id) {
      const next = id && byId.has(id) ? id : null;
      state.selected = next;
      updateFocus();
      if (next) detail.show(next); else detail.clear();
      bus.emit('select', next);
    },
    highlight(ids) {
      state.highlight = ids && ids.length !== 0 ? new Set(ids) : null;
      updateFocus();
      bus.emit('highlight', ids);
    },
    passes(node) {
      if (!node) return false;
      const f = state.filters;
      if (f.types.size && !f.types.has(node.type)) return false;
      if (f.eras.size && !f.eras.has(node.era)) return false;
      const q = f.search.trim().toLowerCase();
      if (q && !(node.name || '').toLowerCase().includes(q) && !node.id.includes(q)) return false;
      return true;
    },
    setFilter() { bus.emit('filter'); },
    views: [],
    registerView(view) {
      if (!view || !view.id || !view.title || typeof view.create !== 'function') {
        console.error('registerView: id, title and create are required', view);
        return;
      }
      this.views.push(view);
      this.views.sort((a, b) => (a.order || 100) - (b.order || 100));
    },
    util: { el, svg, fmtT, tToX, byId, esc, safeImageSrc, lineage, out, inn },
  };

  // ---- detail panel
  let root = null;
  const detail = {
    mount(node) { root = node; this.clear(); },
    clear() {
      if (!root) return;
      root.replaceChildren(el('p', { class: 'muted', text: 'Select an item to see its details, causes and effects.' }));
    },
    show(nodeOrId) {
      const n = typeof nodeOrId === 'string' ? byId.get(nodeOrId) : nodeOrId;
      if (!root || !n) return;
      const tl = data.timeline;
      const ev = tl.events.find((x) => x.id === n.id) || null;
      const tr = tl.traditions.find((x) => x.id === n.id) || null;
      const seen = new Set([n.id]);
      const lists = [];
      const add = (title, ids, note) => {
        const items = (ids || []).filter((i) => byId.has(i));
        items.forEach((i) => seen.add(i));
        if (items.length) lists.push({ title, items, note });
      };
      const causedBy = ev ? ev.caused_by : (inOf(n.id) || []).filter((e) => e.causal).map((e) => e.source);
      const leadsTo = ev ? ev.leads_to : (outOf(n.id) || []).filter((e) => e.causal).map((e) => e.target);
      add('Caused by', causedBy);
      add('Leads to', leadsTo);
      add('Traces', ev ? ev.traces : (outOf(n.id) || []).filter((e) => e.memory).map((e) => e.target));
      if (tr) add('Left by (origin events)', tr.origin_events);
      if (tr) add('Contradicts', tr.contradicts);
      if (ev) {
        add('Participants', ev.participants);
        add('Locations', ev.locations);
      }
      const relNote = new Map();
      const rel = [];
      [...(outOf(n.id) || []), ...(inOf(n.id) || [])].forEach((e) => {
        const other = e.source === n.id ? e.target : e.source;
        if (seen.has(other) || relNote.has(other)) return;
        relNote.set(other, e.label || e.field || e.kind);
        rel.push(other);
      });
      if (rel.length) lists.push({ title: 'Related', items: rel, note: relNote });

      const imgSrc = safeImageSrc(n.image);
      let hero = null;
      if (imgSrc) {
        const fig = el('figure', { class: 'detail-hero' });
        const img = el('img', { src: imgSrc, alt: n.name + ' artwork', loading: 'lazy' });
        img.addEventListener('error', () => { fig.hidden = true; });
        const btn = el('button', {
          type: 'button', class: 'detail-hero-btn',
          'aria-label': 'Expand artwork for ' + n.name,
          onclick: () => openLightbox(n, btn),
        }, img, el('span', { class: 'detail-hero-hint', 'aria-hidden': 'true', text: 'Expand' }));
        fig.appendChild(btn);
        hero = fig;
      }

      const chip = el('span', { class: 'chip', style: 'border-color:' + (colors.type[n.type] || '#888') },
        el('span', { class: 'dot', style: 'background:' + (colors.type[n.type] || '#888'), 'aria-hidden': 'true' }),
        (typeGlyph[n.type] || '?') + ' ' + n.type);
      const meta = [];
      if (n.t !== null && n.t !== undefined) {
        meta.push(n.date_label || fmtT(n.t));
        if (n.end_t !== null && n.end_t !== undefined) meta.push('to ' + fmtT(n.end_t));
        if (n.era) meta.push(n.era);
      } else meta.push('undated');
      if (n.status) meta.push('status: ' + n.status);
      const facts = [];
      if (ev) {
        if (ev.significance) facts.push(['Significance', ev.significance]);
        if (ev.type) facts.push(['Kind', ev.type]);
        if (ev.open_ended) facts.push(['Effects continue', ev.open_ended]);
        Object.entries(ev.impact || {}).forEach(([k, v]) => { if (v) facts.push(['Impact: ' + k, v]); });
      }
      if (tr) {
        facts.push(['Kind', tr.kind || 'other']);
        if (tr.fidelity) facts.push(['Fidelity', tr.fidelity]);
        if (tr.status) facts.push(['Status', tr.status]);
      }
      root.replaceChildren(
        hero,
        el('h2', { text: n.name }), chip,
        el('p', { class: 'detail-meta', text: meta.join(' · ') }),
        n.summary ? el('p', { class: 'detail-summary', text: n.summary }) : null,
        facts.length ? el('dl', {}, facts.map(([k, v]) => [el('dt', { text: k }), el('dd', { text: v })])) : null,
        n.tags && n.tags.length ? el('div', { class: 'detail-tags', 'aria-label': 'Tags' }, n.tags.map((t) => el('span', { class: 'detail-tag', text: '#' + t }))) : null,
        lists.length ? lists.map((l) => el('section', {},
          el('h3', { text: l.title + ' (' + l.items.length + ')' }),
          el('ul', { class: 'links' }, l.items.map((id) => {
            const m = byId.get(id);
            const note = l.note && l.note.get ? l.note.get(id) : null;
            return el('li', {}, el('button', {
              type: 'button', class: 'link',
              onclick: () => WBobj.select(id),
              onmouseenter: () => WBobj.highlight([id]),
              onmouseleave: () => WBobj.highlight(null),
              onfocus: () => WBobj.highlight([id]),
              onblur: () => WBobj.highlight(null),
            }, el('span', { class: 'dot', style: 'background:' + (colors.type[m.type] || '#888'), 'aria-hidden': 'true' }),
            m.name, el('span', { class: 'muted', text: ' ' + (typeGlyph[m.type] || '') + (note ? ' · ' + note : '') })));
          })))) : el('p', { class: 'muted', text: 'No linked items in the files.' }));
    },
  };
  WBobj.detail = detail;
  return WBobj;
})();
window.WB = WB;
