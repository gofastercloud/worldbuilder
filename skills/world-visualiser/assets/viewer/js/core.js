// core.js: data, shared state, event bus, helpers, cinematic lightbox and detail panel with mini causal graph. Defines the global WB.
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
    off(evt, fn) {
      const arr = handlers[evt];
      if (!arr) return;
      const idx = arr.indexOf(fn);
      if (idx >= 0) arr.splice(idx, 1);
    },
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

  const state = {
    selected: null, hover: null, highlight: null, activeView: null,
    filters: { types: new Set(), eras: new Set(), search: '' },
  };

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
  function safeAudioSrc(src) {
    if (typeof src !== 'string') return null;
    const s = src.trim();
    if (!s) return null;
    if (s.startsWith('data:audio/')) return s;
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
  function trunc(str, max) {
    const s = String(str || '');
    return s.length > max ? s.slice(0, max - 1) + '…' : s;
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

  function outOf(id) { return out.get(id); }
  function inOf(id) { return inn.get(id); }

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

  let focusCache = { id: null, up: new Set(), down: new Set(), hl: null };
  function updateFocus() {
    const id = state.selected;
    const l = id ? lineage(id) : { up: new Set(), down: new Set() };
    focusCache = { id, up: l.up, down: l.down, hl: state.highlight };
  }

  // ---- cinematic lightbox with prev/next navigation
  let lbEl = null;
  let lbReturnFocus = null;
  let lbNodes = [];
  let lbIdx = 0;

  function closeLightbox() {
    if (!lbEl || lbEl.hidden) return;
    lbEl.hidden = true;
    lbEl.replaceChildren();
    lbNodes = [];
    if (lbReturnFocus && typeof lbReturnFocus.focus === 'function') lbReturnFocus.focus();
    lbReturnFocus = null;
  }

  function renderLightboxSlide() {
    const node = lbNodes[lbIdx];
    if (!lbEl || !node) return;
    const src = safeImageSrc(node.image);
    if (!src) return;
    const multi = lbNodes.length > 1;
    const col = colors.type[node.type] || '#888';

    const step = (delta) => {
      if (!multi) return;
      lbIdx = (lbIdx + delta + lbNodes.length) % lbNodes.length;
      renderLightboxSlide();
    };

    const closeBtn = el('button', {
      type: 'button', class: 'wb-lightbox-close',
      'aria-label': 'Close artwork preview', onclick: closeLightbox, text: 'Close',
    });
    const inspectBtn = el('button', {
      type: 'button', class: 'btn',
      onclick: () => { const id = node.id; closeLightbox(); WBobj.select(id); },
      text: 'Inspect',
    });
    const prevBtn = multi ? el('button', {
      type: 'button', class: 'wb-lightbox-nav prev',
      'aria-label': 'Previous artwork', onclick: () => step(-1), text: '‹',
    }) : null;
    const nextBtn = multi ? el('button', {
      type: 'button', class: 'wb-lightbox-nav next',
      'aria-label': 'Next artwork', onclick: () => step(1), text: '›',
    }) : null;

    const badge = el('span', { class: 'chip', style: 'border-color:' + col },
      el('span', { class: 'dot', style: 'background:' + col, 'aria-hidden': 'true' }),
      node.type);

    lbEl.setAttribute('aria-label', node.name + ' artwork');
    lbEl.replaceChildren(
      el('div', { class: 'wb-lightbox-dialog' },
        el('div', { class: 'wb-lightbox-stage' },
          prevBtn,
          el('img', { class: 'wb-lightbox-img', src, alt: node.name + ' artwork' }),
          nextBtn),
        el('div', { class: 'wb-lightbox-bar' },
          el('div', { class: 'wb-lightbox-title' },
            el('strong', { text: node.name }),
            badge,
            node.date_label ? el('span', { class: 'muted', text: node.date_label }) : null),
          el('div', { class: 'wb-lightbox-actions' },
            multi ? el('span', { class: 'wb-lightbox-counter', text: (lbIdx + 1) + ' / ' + lbNodes.length }) : null,
            inspectBtn,
            closeBtn))),
    );
    closeBtn.focus();
  }

  function openLightbox(node, triggerEl) {
    const src = node && safeImageSrc(node.image);
    if (!src) return;
    lbReturnFocus = triggerEl || document.activeElement;
    const allArt = data.nodes.filter((n) => !!safeImageSrc(n.image));
    const idx = allArt.findIndex((n) => n.id === node.id);
    lbNodes = idx >= 0 ? allArt : [node];
    lbIdx = idx >= 0 ? idx : 0;

    if (!lbEl) {
      lbEl = el('div', {
        class: 'wb-lightbox', role: 'dialog', 'aria-modal': 'true', hidden: true,
        onclick: (ev) => { if (ev.target === lbEl) closeLightbox(); },
      });
      document.body.appendChild(lbEl);
      document.addEventListener('keydown', (ev) => {
        if (!lbEl || lbEl.hidden) return;
        if (ev.key === 'Escape') { ev.preventDefault(); closeLightbox(); }
        else if (ev.key === 'ArrowLeft' && lbNodes.length > 1) {
          ev.preventDefault();
          lbIdx = (lbIdx - 1 + lbNodes.length) % lbNodes.length;
          renderLightboxSlide();
        } else if (ev.key === 'ArrowRight' && lbNodes.length > 1) {
          ev.preventDefault();
          lbIdx = (lbIdx + 1) % lbNodes.length;
          renderLightboxSlide();
        }
      });
    }
    lbEl.hidden = false;
    renderLightboxSlide();
  }

  // ---- audio engine: looping world soundtrack (auto-ducking) + character voice playback
  const MUSIC_VOL = 0.34;
  const DUCK_VOL = 0.07;
  const themeSrc = safeAudioSrc(data.project && data.project.audio);
  let musicEl = null;
  let musicMuted = false;
  let musicPlaying = false;
  let voiceEl = null;
  let speakingId = null;

  function syncMusicVol() {
    if (!musicEl) return;
    musicEl.volume = speakingId ? DUCK_VOL : MUSIC_VOL;
  }

  function tryStartMusic() {
    if (!musicEl || musicMuted) return;
    const p = musicEl.play();
    if (p && typeof p.then === 'function') {
      p.then(() => {
        musicPlaying = true;
        bus.emit('audio');
      }).catch(() => {
        // Browser autoplay policy blocked unmuted start; start on first user gesture.
        const unlock = () => {
          document.removeEventListener('pointerdown', unlock, true);
          document.removeEventListener('keydown', unlock, true);
          if (!musicMuted && musicEl && musicEl.paused) {
            musicEl.play().then(() => {
              musicPlaying = true;
              bus.emit('audio');
            }).catch(() => {});
          }
        };
        document.addEventListener('pointerdown', unlock, true);
        document.addEventListener('keydown', unlock, true);
      });
    }
  }

  if (themeSrc && typeof Audio !== 'undefined') {
    musicEl = new Audio(themeSrc);
    musicEl.loop = true;
    musicEl.preload = 'auto';
    musicEl.volume = MUSIC_VOL;
    musicEl.addEventListener('pause', () => { musicPlaying = false; bus.emit('audio'); });
    musicEl.addEventListener('play', () => { musicPlaying = true; bus.emit('audio'); });
    tryStartMusic();
  }

  const audio = {
    hasMusic: !!themeSrc,
    isMusicPlaying() { return musicPlaying && !musicMuted; },
    isMuted() { return musicMuted; },
    speakingId() { return speakingId; },
    toggleMusic() {
      if (!musicEl) return;
      if (musicMuted || musicEl.paused) {
        musicMuted = false;
        musicEl.muted = false;
        syncMusicVol();
        musicEl.play().then(() => { musicPlaying = true; bus.emit('audio'); }).catch(() => {});
      } else {
        musicMuted = true;
        musicEl.pause();
        musicPlaying = false;
        bus.emit('audio');
      }
    },
    stopVoice() {
      if (voiceEl) {
        try { voiceEl.pause(); voiceEl.currentTime = 0; } catch (_) {}
      }
      speakingId = null;
      syncMusicVol();
      bus.emit('audio');
    },
    playVoice(node) {
      if (!node) return;
      const src = safeAudioSrc(node.audio);
      if (!src || typeof Audio === 'undefined') return;
      if (speakingId === node.id && voiceEl && !voiceEl.paused) {
        audio.stopVoice();
        return;
      }
      if (!voiceEl) {
        voiceEl = new Audio();
        voiceEl.addEventListener('ended', () => {
          speakingId = null;
          syncMusicVol();
          bus.emit('audio');
        });
        voiceEl.addEventListener('error', () => {
          speakingId = null;
          syncMusicVol();
          bus.emit('audio');
        });
      }
      voiceEl.src = src;
      speakingId = node.id;
      syncMusicVol();
      bus.emit('audio');
      voiceEl.play().catch(() => {
        speakingId = null;
        syncMusicVol();
        bus.emit('audio');
      });
    },
  };

  const WBobj = {
    data, state, colors, bus, typeGlyph, edges, degree, openLightbox, audio,
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
    util: { el, svg, fmtT, tToX, byId, esc, safeImageSrc, safeAudioSrc, lineage, out, inn },
  };

  // ---- inline SVG Mini Causal Neighbourhood Graph
  function buildMiniGraph(n, causedBy, leadsTo, traces, originEvents) {
    const uniq = (arr) => {
      const s = new Set();
      const res = [];
      (arr || []).forEach((id) => {
        if (id && id !== n.id && byId.has(id) && !s.has(id)) { s.add(id); res.push(id); }
      });
      return res;
    };

    const upCausal = uniq([...(causedBy || []), ...(originEvents || [])]);
    const downCausal = uniq(leadsTo || []);
    const downTraces = uniq(traces || []);
    const hasCausal = upCausal.length + downCausal.length + downTraces.length > 0;

    let leftNodes = [];
    let rightNodes = [];
    let modeLabel = 'Causal Neighbourhood';

    if (hasCausal) {
      leftNodes = upCausal.map((id) => ({ id, kind: 'cause', stroke: '#38bdf8', dashed: false }));
      rightNodes = [
        ...downCausal.map((id) => ({ id, kind: 'effect', stroke: '#f59e0b', dashed: false })),
        ...downTraces.map((id) => ({ id, kind: 'trace', stroke: '#a78bfa', dashed: true })),
      ];
    } else {
      modeLabel = 'Linked Neighbourhood';
      const seenStruct = new Set([n.id]);
      (inOf(n.id) || []).forEach((e) => {
        if (byId.has(e.source) && !seenStruct.has(e.source)) {
          seenStruct.add(e.source);
          leftNodes.push({ id: e.source, kind: 'link', stroke: '#8b95a7', dashed: false });
        }
      });
      (outOf(n.id) || []).forEach((e) => {
        if (byId.has(e.target) && !seenStruct.has(e.target)) {
          seenStruct.add(e.target);
          rightNodes.push({ id: e.target, kind: 'link', stroke: '#8b95a7', dashed: false });
        }
      });
    }

    if (!leftNodes.length && !rightNodes.length) return null;

    const MAX_SIDE = 5;
    const extraLeft = Math.max(0, leftNodes.length - MAX_SIDE);
    const extraRight = Math.max(0, rightNodes.length - MAX_SIDE);
    const leftShown = leftNodes.slice(0, MAX_SIDE);
    const rightShown = rightNodes.slice(0, MAX_SIDE);

    const rows = Math.max(leftShown.length, rightShown.length, 1);
    const W = 326;
    const rowH = 30;
    const H = Math.max(86, rows * rowH + 26);
    const cx = W / 2;
    const cy = H / 2;
    const pillW = 94;
    const pillH = 22;
    const centerW = 104;
    const centerH = 28;

    const makeArrow = (id, fill) => svg('marker', {
      id, viewBox: '0 0 8 8', refX: '7', refY: '4', markerWidth: '5', markerHeight: '5', orient: 'auto-start-reverse',
    }, svg('path', { d: 'M0,1 L7,4 L0,7 Z', fill }));

    const defs = svg('defs', {},
      makeArrow('mg-arr-cause', '#38bdf8'),
      makeArrow('mg-arr-effect', '#f59e0b'),
      makeArrow('mg-arr-trace', '#a78bfa'),
      makeArrow('mg-arr-link', '#8b95a7'));

    const edgeLayer = svg('g', { 'aria-hidden': 'true' });
    const nodeLayer = svg('g', {});

    const yFor = (i, total) => {
      if (total <= 1) return cy;
      const spanH = (total - 1) * rowH;
      return cy - spanH / 2 + i * rowH;
    };

    const addSatellite = (item, x, y, isLeft) => {
      const m = byId.get(item.id);
      if (!m) return;
      const mCol = colors.type[m.type] || '#888';
      const x1 = isLeft ? x + pillW : cx + centerW / 2;
      const y1 = isLeft ? y : cy;
      const x2 = isLeft ? cx - centerW / 2 - 2 : x - 2;
      const y2 = isLeft ? cy : y;
      const dx = (x2 - x1) * 0.52;
      const d = `M ${x1} ${y1} C ${x1 + dx} ${y1}, ${x2 - dx} ${y2}, ${x2} ${y2}`;

      edgeLayer.appendChild(svg('path', {
        d, fill: 'none', stroke: item.stroke, 'stroke-width': item.kind === 'link' ? '1.25' : '1.6',
        'stroke-dasharray': item.dashed ? '4 3' : null,
        'stroke-opacity': '0.85',
        'marker-end': 'url(#mg-arr-' + item.kind + ')',
      }));

      const g = svg('g', {
        class: 'mg-node', role: 'button', tabindex: '0',
        'aria-label': 'Navigate to ' + m.name + ' (' + m.type + ')',
        onclick: () => WBobj.select(m.id),
        onkeydown: (ev) => {
          if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); WBobj.select(m.id); }
        },
        onmouseenter: () => WBobj.highlight([m.id]),
        onmouseleave: () => WBobj.highlight(null),
        onfocus: () => WBobj.highlight([m.id]),
        onblur: () => WBobj.highlight(null),
      },
      svg('title', { text: m.name + ' (' + m.type + ')' }),
      svg('rect', {
        class: 'mg-pill', x, y: y - pillH / 2, width: pillW, height: pillH, rx: '11',
        fill: 'var(--panel)', stroke: item.stroke, 'stroke-width': '1', 'stroke-opacity': '0.75',
      }),
      svg('circle', { cx: x + 10, cy: y, r: '3.5', fill: mCol }),
      svg('text', {
        x: x + 18, y: y + 3.5, 'font-size': '10', fill: 'var(--fg)', 'font-weight': '500',
        text: trunc(m.name, 12),
      }));
      nodeLayer.appendChild(g);
    };

    leftShown.forEach((item, i) => addSatellite(item, 4, yFor(i, leftShown.length), true));
    rightShown.forEach((item, i) => addSatellite(item, W - pillW - 4, yFor(i, rightShown.length), false));

    // Centre selected node
    const nCol = colors.type[n.type] || '#56B4E9';
    nodeLayer.appendChild(svg('g', {},
      svg('title', { text: n.name + ' (selected)' }),
      svg('rect', {
        class: 'mg-center-aura', x: cx - centerW / 2 - 4, y: cy - centerH / 2 - 4,
        width: centerW + 8, height: centerH + 8, rx: '16',
        fill: 'none', stroke: nCol, 'stroke-width': '1.5', 'stroke-opacity': '0.45',
      }),
      svg('rect', {
        x: cx - centerW / 2, y: cy - centerH / 2, width: centerW, height: centerH, rx: '14',
        fill: 'var(--panel)', stroke: nCol, 'stroke-width': '2',
      }),
      svg('circle', { cx: cx - centerW / 2 + 12, cy, r: '4', fill: nCol }),
      svg('text', {
        x: cx - centerW / 2 + 21, y: cy + 3.5, 'font-size': '10.5', 'font-weight': '700', fill: 'var(--fg)',
        text: trunc(n.name, 12),
      })));

    const totalExtra = extraLeft + extraRight;
    const svgEl = svg('svg', {
      class: 'detail-minigraph-svg',
      viewBox: `0 0 ${W} ${H}`,
      role: 'img',
      'aria-label': modeLabel + ' for ' + n.name,
    }, defs, edgeLayer, nodeLayer);

    const legendItems = [];
    if (hasCausal) {
      if (upCausal.length) legendItems.push(['Cause', '#38bdf8', false]);
      if (downCausal.length) legendItems.push(['Effect', '#f59e0b', false]);
      if (downTraces.length) legendItems.push(['Trace', '#a78bfa', true]);
    } else {
      legendItems.push(['Structural link', '#8b95a7', false]);
    }

    return el('div', { class: 'detail-minigraph' },
      el('div', { class: 'detail-minigraph-head' },
        el('span', { class: 'detail-minigraph-title', text: modeLabel }),
        totalExtra > 0 ? el('span', { class: 'muted', style: 'font-size:11px', text: '+' + totalExtra + ' more below' }) : null),
      svgEl,
      el('div', { class: 'detail-minigraph-legend' },
        legendItems.map(([label, col, dashed]) => el('span', { class: 'mg-leg-item' },
          el('span', { class: 'mg-leg-swatch' + (dashed ? ' dashed' : ''), style: dashed ? '' : 'background:' + col }),
          label))));
  }

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
      const traces = ev ? ev.traces : (outOf(n.id) || []).filter((e) => e.memory).map((e) => e.target);
      add('Caused by', causedBy);
      add('Leads to', leadsTo);
      add('Traces', traces);
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

      const nCol = colors.type[n.type] || '#888';
      const chip = el('span', { class: 'chip', style: 'border-color:' + nCol },
        el('span', { class: 'dot', style: 'background:' + nCol, 'aria-hidden': 'true' }),
        n.type);

      const dateText = (n.t !== null && n.t !== undefined)
        ? (n.date_label || fmtT(n.t)) + (n.end_t !== null && n.end_t !== undefined ? ' – ' + fmtT(n.end_t) : '')
        : 'undated';

      const headerBlock = el('div', { class: 'detail-header' },
        el('div', { class: 'detail-crest', style: '--crest-col:' + nCol, 'aria-hidden': 'true', text: typeGlyph[n.type] || '?' }),
        el('div', { class: 'detail-head-text' },
          el('h2', { text: n.name }),
          el('div', { class: 'detail-pills' },
            chip,
            n.era ? el('span', { class: 'detail-era-pill', text: n.era }) : null,
            el('span', { class: 'detail-era-pill', text: dateText }),
            n.status ? el('span', { class: 'detail-era-pill', text: n.status }) : null)));

      const miniGraph = buildMiniGraph(n, causedBy, leadsTo, traces, tr ? tr.origin_events : null);

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

      const voiceSrc = safeAudioSrc(n.audio);
      let voiceBtn = null;
      if (voiceSrc) {
        const isSpk = audio.speakingId() === n.id;
        voiceBtn = el('button', {
          type: 'button',
          class: 'wb-voice-btn' + (isSpk ? ' playing' : ''),
          'aria-pressed': String(isSpk),
          'aria-label': isSpk ? 'Stop ' + n.name + ' speaking' : 'Hear ' + n.name + ' speak',
          onclick: () => audio.playVoice(n),
        },
        el('span', { class: 'wb-voice-icon', 'aria-hidden': 'true', text: isSpk ? '⏹' : '🔊' }),
        el('span', { text: isSpk ? 'Stop speaking' : 'Hear ' + n.name + ' speak' }));
      }

      const detailChildren = [
        hero,
        headerBlock,
        voiceBtn,
        n.summary ? el('p', { class: 'detail-summary', text: n.summary }) : null,
        miniGraph,
        facts.length ? el('dl', {}, facts.map(([k, v]) => [el('dt', { text: k }), el('dd', { text: v })])) : null,
        n.tags && n.tags.length ? el('div', { class: 'detail-tags', 'aria-label': 'Tags' },
          n.tags.map((t) => el('span', { class: 'detail-tag', text: '#' + t }))) : null,
        ...(lists.length ? lists.map((l) => el('details', { class: 'detail-group', open: true },
          el('summary', {},
            el('span', { text: l.title }),
            el('span', { class: 'detail-group-count', text: String(l.items.length) })),
          el('div', { class: 'detail-rel-chips' }, l.items.map((id) => {
            const m = byId.get(id);
            const note = l.note && l.note.get ? l.note.get(id) : null;
            return el('button', {
              type: 'button', class: 'detail-rel-chip',
              onclick: () => WBobj.select(id),
              onmouseenter: () => WBobj.highlight([id]),
              onmouseleave: () => WBobj.highlight(null),
              onfocus: () => WBobj.highlight([id]),
              onblur: () => WBobj.highlight(null),
            },
            el('span', { class: 'dot', style: 'background:' + (colors.type[m.type] || '#888'), 'aria-hidden': 'true' }),
            el('span', { class: 'detail-rel-chip-name', text: m.name }),
            note ? el('span', { class: 'detail-rel-chip-note', text: '· ' + note }) : null);
          })))) : [el('p', { class: 'muted', text: 'No linked items in the files.' })]),
      ].filter(Boolean);
      root.replaceChildren(...detailChildren);
    },
  };
  WBobj.detail = detail;
  return WBobj;
})();
window.WB = WB;
