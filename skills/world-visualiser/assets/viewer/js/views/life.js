/* WorldBuilder viewer: LIFE view (climate zones, flora and fauna, climate consistency heuristics). */
(function () {
  'use strict';
  if (typeof WB === 'undefined' || !WB || !WB.registerView) return;
  // ---- shared helpers (duplicated in map.js, trade.js, life.js; scripts are concatenated, so no shared globals) ----
  const NS = 'http://www.w3.org/2000/svg';
  function add(n, c) {
    if (c == null || c === false) return;
    if (Array.isArray(c)) c.forEach(function (x) { add(n, x); });
    else n.appendChild(typeof c === 'object' ? c : document.createTextNode(String(c)));
  }
  // h('div', {class:'x', onclick:fn, text:'t'}, ...children); tag 'svg:path' makes an SVG element.
  function h(tag, attrs) {
    const isSvg = tag.slice(0, 4) === 'svg:';
    const n = isSvg ? document.createElementNS(NS, tag.slice(4)) : document.createElement(tag);
    if (attrs) {
      for (const k in attrs) {
        const v = attrs[k];
        if (v == null || v === false) continue;
        if (k === 'text') n.textContent = v;
        else if (k.slice(0, 2) === 'on' && typeof v === 'function') n.addEventListener(k.slice(2), v);
        else n.setAttribute(k, v === true ? '' : String(v));
      }
    }
    for (let i = 2; i < arguments.length; i++) add(n, arguments[i]);
    return n;
  }
  function clear(n) { while (n.firstChild) n.removeChild(n.firstChild); }
  const slug = function (s) { return String(s == null ? '' : s).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, ''); };
  function fmtN(n) {
    if (n == null || isNaN(n)) return '?';
    const a = Math.abs(n), u = [[1e12, 'trillion'], [1e9, 'billion'], [1e6, 'million'], [1e3, 'thousand']];
    for (let i = 0; i < u.length; i++) if (a >= u[i][0]) return (+(n / u[i][0]).toFixed(1)) + ' ' + u[i][1];
    return String(+(+n).toFixed(1));
  }
  function prep(WB) {
    const D = WB.data || {}, M = D.map || {};
    const locs = M.locations || [], routes = M.routes || [];
    const L = {}, N = {}, adj = {};
    locs.forEach(function (l) { L[l.id] = l; });
    (D.nodes || []).forEach(function (n) { N[n.id] = n; });
    routes.forEach(function (r) {
      (adj[r.from] = adj[r.from] || []).push({ to: r.to, r: r });
      (adj[r.to] = adj[r.to] || []).push({ to: r.from, r: r });
    });
    const types = Array.from(new Set(locs.map(function (l) { return l.type || 'place'; }))).sort();
    return { D: D, locs: locs, routes: routes, L: L, N: N, adj: adj, types: types,
      name: function (id) { return (L[id] && L[id].name) || (N[id] && N[id].name) || String(id); } };
  }
  // Filter semantics (assumption, see report): empty Set = no filter. A location passes the type filter when the Set
  // contains its location type (planet, station...) or the node type 'location'. Search matches name or id.
  function passes(WB, l) {
    const f = (WB.state && WB.state.filters) || {};
    const t = f.types;
    if (t && t.size && !t.has(l.type) && !t.has('location')) return false;
    const s = String(f.search || '').trim().toLowerCase();
    if (s && (l.name + ' ' + l.id).toLowerCase().indexOf(s) < 0) return false;
    return true;
  }
  function zoneColor(WB, z) {
    if (!z || z === 'unspecified') return '#BDBDBD';
    try { if (WB.colors && typeof WB.colors.zone === 'function') return WB.colors.zone(z) || '#BDBDBD'; } catch (e) { /* fall through */ }
    const lg = (WB.data && WB.data.climate && WB.data.climate.legend) || {};
    return lg[z] || '#BDBDBD';
  }
  const PAL = ['#0072B2', '#D55E00', '#009E73', '#CC79A7', '#56B4E9', '#E69F00', '#882255', '#44AA99'];
  const SHAPES = ['circle', 'square', 'diamond', 'triangle', 'hexagon', 'star', 'plus'];
  const PRESET = { planet: 'circle', moon: 'circle', station: 'square', region: 'hexagon', system: 'star', city: 'diamond',
    settlement: 'diamond', continent: 'hexagon', realm: 'hexagon', building: 'triangle', landmark: 'triangle' };
  function shapeMap(types) {
    const out = {}, used = {};
    types.forEach(function (t) { if (PRESET[t]) { out[t] = PRESET[t]; used[PRESET[t]] = 1; } });
    let i = 0;
    types.forEach(function (t) {
      if (out[t]) return;
      while (i < SHAPES.length && used[SHAPES[i]]) i++;
      out[t] = SHAPES[i % SHAPES.length]; used[out[t]] = 1; i++;
    });
    return out;
  }
  function poly(pts) { return 'M' + pts.map(function (p) { return p[0].toFixed(1) + ',' + p[1].toFixed(1); }).join('L') + 'Z'; }
  function shapeD(kind, r) {
    switch (kind) {
      case 'square': return poly([[-r, -r], [r, -r], [r, r], [-r, r]]);
      case 'diamond': return poly([[0, -r * 1.3], [r * 1.3, 0], [0, r * 1.3], [-r * 1.3, 0]]);
      case 'triangle': return poly([[0, -r * 1.25], [r * 1.15, r * 0.85], [-r * 1.15, r * 0.85]]);
      case 'hexagon': { const p = []; for (let i = 0; i < 6; i++) p.push([r * 1.1 * Math.cos(i * Math.PI / 3), r * 1.1 * Math.sin(i * Math.PI / 3)]); return poly(p); }
      case 'star': { const p = []; for (let i = 0; i < 10; i++) { const rr = i % 2 ? r * 0.55 : r * 1.35, a = -Math.PI / 2 + i * Math.PI / 5; p.push([rr * Math.cos(a), rr * Math.sin(a)]); } return poly(p); }
      case 'plus': { const a = r * 1.3, b = r * 0.45; return poly([[-b, -a], [b, -a], [b, -b], [a, -b], [a, b], [b, b], [b, a], [-b, a], [-b, b], [-a, b], [-a, -b], [-b, -b]]); }
      default: return 'M' + (-r) + ',0a' + r + ',' + r + ' 0 1,0 ' + (2 * r) + ',0a' + r + ',' + r + ' 0 1,0 ' + (-2 * r) + ',0Z';
    }
  }
  // marker radius: log scale on population; unknown population gets a small fixed size
  function rad(l) { return l.population > 0 ? Math.max(5, Math.min(20, 5 + 2.2 * (Math.log10(l.population) - 2))) : 5; }
  function curve(a, b, bend) {
    const mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2, dx = b.x - a.x, dy = b.y - a.y;
    const cx = mx - dy * bend, cy = my + dx * bend;
    return { d: 'M' + a.x + ',' + a.y + 'Q' + cx.toFixed(1) + ',' + cy.toFixed(1) + ' ' + b.x + ',' + b.y,
      at: function (t) { const u = 1 - t; return { x: u * u * a.x + 2 * u * t * cx + t * t * b.x, y: u * u * a.y + 2 * u * t * cy + t * t * b.y,
        tx: 2 * u * (cx - a.x) + 2 * t * (b.x - cx), ty: 2 * u * (cy - a.y) + 2 * t * (b.y - cy) }; } };
  }
  // simple pan (drag) / zoom (wheel, buttons, +/-/0 keys) by rewriting the viewBox
  function panzoom(svg, onChange) {
    const home = { x: -20, y: -20, w: 1040, h: 1040 };
    const vb = { x: home.x, y: home.y, w: home.w, h: home.h };
    let drag = null, moved = 0;
    function upp() { const r = svg.getBoundingClientRect ? svg.getBoundingClientRect() : { width: 800, height: 800 }; return Math.max(vb.w / (r.width || 800), vb.h / (r.height || 800)); }
    function apply() { svg.setAttribute('viewBox', vb.x + ' ' + vb.y + ' ' + vb.w + ' ' + vb.h); if (onChange) onChange(upp()); }
    function toSvg(ev) {
      try { const p = svg.createSVGPoint(); p.x = ev.clientX; p.y = ev.clientY; const q = p.matrixTransform(svg.getScreenCTM().inverse()); return { x: q.x, y: q.y }; }
      catch (e) { return { x: vb.x + vb.w / 2, y: vb.y + vb.h / 2 }; }
    }
    function zoom(f, c) {
      const k = Math.min(2000, Math.max(60, vb.w * f)) / vb.w;
      c = c || { x: vb.x + vb.w / 2, y: vb.y + vb.h / 2 };
      vb.x = c.x - (c.x - vb.x) * k; vb.y = c.y - (c.y - vb.y) * k; vb.w *= k; vb.h *= k; apply();
    }
    svg.addEventListener('wheel', function (ev) { ev.preventDefault(); zoom(Math.pow(1.0015, ev.deltaY), toSvg(ev)); }, { passive: false });
    svg.addEventListener('pointerdown', function (ev) { drag = { cx: ev.clientX, cy: ev.clientY, x: vb.x, y: vb.y }; moved = 0; });
    svg.addEventListener('pointermove', function (ev) {
      if (!drag) return;
      const dx = ev.clientX - drag.cx, dy = ev.clientY - drag.cy; moved = Math.max(moved, Math.abs(dx) + Math.abs(dy));
      if (moved > 4) { const u = upp(); vb.x = drag.x - dx * u; vb.y = drag.y - dy * u; apply(); }
    });
    const end = function () { drag = null; };
    svg.addEventListener('pointerup', end); svg.addEventListener('pointerleave', end);
    svg.addEventListener('keydown', function (ev) {
      if (ev.key === '+' || ev.key === '=') zoom(0.8); else if (ev.key === '-') zoom(1.25);
      else if (ev.key === '0') { Object.assign(vb, home); apply(); }
    });
    apply();
    return { refresh: apply, zoomIn: function () { zoom(0.8); }, zoomOut: function () { zoom(1.25); },
      reset: function () { Object.assign(vb, home); apply(); }, wasDrag: function () { return moved > 4; }, upp: upp };
  }
  const CSS = '.wbg-view{display:flex;flex-direction:column;height:100%;min-height:0;font:13px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;color:var(--fg,CanvasText)}' +
    '.wbg-bar{display:flex;flex-wrap:wrap;gap:8px 14px;align-items:center;padding:8px 14px;border-bottom:1px solid var(--border,rgba(128,128,128,.35));background:var(--panel,transparent)}' +
    '.wbg-bar label{display:inline-flex;gap:6px;align-items:center;color:var(--muted,inherit);font-weight:500}' +
    '.wbg-bar select,.wbg-view input[type=search]{background:var(--surface,Canvas);color:var(--fg,CanvasText);border:1px solid var(--border,rgba(128,128,128,.5));border-radius:var(--radius-sm,6px);padding:3px 8px}' +
    '.wbg-body{display:flex;flex:1;min-height:0}.wbg-stage{flex:1 1 auto;min-width:0;position:relative;min-height:320px;background:var(--bg,Canvas)}' +
    '.wbg-side{width:350px;flex:none;overflow:auto;padding:12px 14px;border-left:1px solid var(--border,rgba(128,128,128,.35));background:var(--panel,transparent)}' +
    '@media(max-width:820px){.wbg-body{flex-direction:column;overflow:auto}.wbg-side{width:auto;border-left:0;border-top:1px solid var(--border,rgba(128,128,128,.35))}}' +
    'svg.wbg-svg{width:100%;height:100%;display:block;touch-action:none;cursor:grab;min-height:320px}' +
    '.wbg-sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}' +
    '.wbg-lbl{fill:var(--fg,currentColor);font-size:var(--wbg-fs,12px);font-weight:500;paint-order:stroke;stroke:var(--bg,Canvas);stroke-width:3.5px;stroke-linejoin:round;pointer-events:none}' +
    '.wbg-glyph{font-weight:700;font-size:calc(var(--wbg-fs,12px)*.9);fill:#000;pointer-events:none}' +
    '.wbg-node{cursor:pointer}.wbg-node:focus{outline:none}.wbg-node:focus-visible .wbg-sh{stroke:var(--focus,Highlight);stroke-width:4}' +
    '.wbg-node .wbg-sh{stroke:var(--panel,Canvas);stroke-width:1.6}.wbg-node.wbg-sel .wbg-sh{stroke:var(--focus,Highlight);stroke-width:4}' +
    '.wbg-node.wbg-dim{opacity:.25}.wbg-node.wbg-hl .wbg-sh{stroke:var(--accent,Highlight);stroke-width:3.5}' +
    '.wbg-chip,.wbg-btn{font:inherit;color:var(--fg,inherit);background:var(--surface,rgba(128,128,128,.14));border:1px solid var(--border,rgba(128,128,128,.5));border-radius:999px;padding:2px 9px;margin:2px 4px 2px 0;cursor:pointer;transition:background-color 140ms ease,border-color 140ms ease}' +
    '.wbg-btn{border-radius:var(--radius-sm,6px);padding:3px 9px;font-weight:500}.wbg-chip:hover,.wbg-btn:hover{background:var(--surface-hover,rgba(128,128,128,.28));border-color:var(--accent,Highlight)}' +
    '.wbg-chip:focus-visible,.wbg-btn:focus-visible,.wbg-row:focus-visible{outline:2px solid var(--focus,Highlight);outline-offset:1px}' +
    '.wbg-card h3,.wbg-side h3{margin:14px 0 6px;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:var(--muted,inherit)}.wbg-card dl{display:grid;grid-template-columns:auto 1fr;gap:4px 12px;margin:6px 0;padding:8px 10px;background:var(--surface,transparent);border:1px solid var(--border-subtle,rgba(128,128,128,.25));border-radius:var(--radius-sm,6px)}.wbg-card dt{color:var(--muted,inherit);font-weight:600}.wbg-card dd{margin:0}' +
    '.wbg-dim-t{color:var(--muted,inherit)}.wbg-empty{padding:24px;color:var(--muted,inherit)}.wbg-legend{display:flex;flex-wrap:wrap;gap:5px 12px;margin:6px 0}.wbg-legend span{display:inline-flex;gap:5px;align-items:center}' +
    '.wbg-flag{display:inline-block;border-radius:4px;padding:1px 6px;margin:1px 3px 1px 0;font-size:11.5px;font-weight:600;border:1px solid}' +
    '.wbg-flag.bad{border-color:#D55E00;background:rgba(213,94,0,.18)}.wbg-flag.warn{border-color:#E69F00;background:rgba(230,159,0,.18)}.wbg-flag.note{border-color:var(--border,rgba(128,128,128,.7));background:var(--surface,rgba(128,128,128,.12))}' +
    '.wbg-side table{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums}.wbg-side th,.wbg-side td{text-align:left;padding:5px 6px;border-bottom:1px solid var(--border-subtle,rgba(128,128,128,.25));vertical-align:top}' +
    '.wbg-side th{font-size:11.5px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted,inherit)}' +
    '.wbg-row{cursor:pointer;transition:background-color 120ms ease}.wbg-row:hover{background:var(--surface,rgba(128,128,128,.12))}.wbg-row[aria-pressed="true"],.wbg-row.on{background:var(--accent-soft,rgba(0,114,178,.22))}' +
    '.wbg-list{list-style:none;margin:0;padding:0}.wbg-list li{margin:3px 0}.wbg-bar2{display:inline-block;height:8px;background:var(--accent,currentColor);opacity:.72;border-radius:3px;vertical-align:middle}';
  function injectCss() {
    try { if (document.getElementById('wbg-css')) return; const s = h('style', { id: 'wbg-css' }); s.textContent = CSS; (document.head || document.body).appendChild(s); } catch (e) { /* no DOM head */ }
  }
  function reducedMotion() { try { return !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches); } catch (e) { return false; } }
  function mkSvg(label) { return h('svg:svg', { class: 'wbg-svg', viewBox: '-20 -20 1040 1040', role: 'group', 'aria-label': label, preserveAspectRatio: 'xMidYMid meet' }); }
  function zoomBtns(pz) {
    return h('span', null, h('button', { class: 'wbg-btn', type: 'button', 'aria-label': 'Zoom in', onclick: pz.zoomIn, text: '+' }),
      h('button', { class: 'wbg-btn', type: 'button', 'aria-label': 'Zoom out', onclick: pz.zoomOut, text: '−' }),
      h('button', { class: 'wbg-btn', type: 'button', 'aria-label': 'Reset view', onclick: pz.reset, text: 'Reset' }));
  }

  const st = { sel: null, q: '', dirty: true, active: false };   // sel = {kind, key, label, ids:[], info}
  let W, G, SP = [], zones = [], findings = [], root, ui = {}, mini, miniNodes = {}, pending = null;

  function nums(v, out) {
    if (v == null) return out;
    if (typeof v === 'number' && isFinite(v)) out.push(v);
    else if (typeof v === 'string' && v.trim() !== '' && isFinite(+v)) out.push(+v);
    else if (Array.isArray(v)) v.forEach(function (x) { nums(x, out); });
    else if (typeof v === 'object') Object.keys(v).forEach(function (k) { nums(v[k], out); });
    return out;
  }
  function temp(c) {
    const a = c ? nums(c.temperature_c, []) : [];
    return a.length ? { mean: a.reduce(function (s, x) { return s + x; }, 0) / a.length, min: Math.min.apply(null, a), max: Math.max.apply(null, a) } : null;
  }
  const precip = function (c) { const a = c ? nums(c.precipitation_mm, []) : []; return a.length ? a.reduce(function (s, x) { return s + x; }, 0) / a.length : null; };
  const HABITAT = /^(artificial|custom|unspecified)$/;     // stations, ships etc.: zone contrast means nothing there
  const EXPLAIN = /mountain|alp|peak|range|highland|plateau|coast|sea|ocean|lake|rift|valley|basin|trench|depth/i;
  const STAPLE = /staple|crop|grain|cereal|food|agric/i;

  // ---- heuristics: computed from the data only, never authoritative ----
  function compute() {
    const out = [], seen = {}, add1 = function (o) { if (out.length < 60) out.push(o); };
    const clim = G.locs.filter(function (l) { return l.climate; });
    // 1. neighbours (linked by a route, or within 90 layout units) with very different climate and nothing explaining it
    const pairs = [];
    G.routes.forEach(function (r) { pairs.push([r.from, r.to]); });
    for (let i = 0; i < clim.length; i++) for (let j = i + 1; j < clim.length; j++) if (Math.hypot(clim[i].x - clim[j].x, clim[i].y - clim[j].y) < 90) pairs.push([clim[i].id, clim[j].id]);
    pairs.forEach(function (p) {
      const a = G.L[p[0]], b = G.L[p[1]], key = [p[0], p[1]].sort().join('|');
      if (!a || !b || !a.climate || !b.climate || seen[key]) return; seen[key] = 1;
      const za = a.climate.zone, zb = b.climate.zone;
      if (!za || !zb || za === zb || HABITAT.test(za) || HABITAT.test(zb) || a.parent === b.id || b.parent === a.id) return;
      const ta = temp(a.climate), tb = temp(b.climate), pa = precip(a.climate), pb = precip(b.climate);
      const dT = ta && tb ? Math.abs(ta.mean - tb.mean) : 0, ratio = pa > 0 && pb > 0 ? Math.max(pa, pb) / Math.min(pa, pb) : 1;
      if (dT < 15 && ratio < 5) return;
      const dE = a.elevation_m != null && b.elevation_m != null ? Math.abs(a.elevation_m - b.elevation_m) : null;
      if ((dE != null && dE >= 1000) || EXPLAIN.test((a.terrain || '') + ' ' + (b.terrain || ''))) return;
      add1({ k: 'warn', ids: [a.id, b.id], text: a.name + ' (' + za + ') borders ' + b.name + ' (' + zb + '): ' + (dT >= 15 ? 'mean temperature differs by ' + dT.toFixed(0) + ' C' : 'rainfall differs ' + ratio.toFixed(1) + 'x') + ', with no mountain, coast or elevation difference recorded.' });
    });
    clim.forEach(function (l) {
      const c = l.climate, t = temp(c), g = c.growing_season_days;
      // 2. growing season but never above freezing
      if (g > 0 && t && t.max < 0) add1({ k: 'bad', ids: [l.id], text: l.name + ': growing_season_days is ' + g + ' but the highest recorded temperature is ' + t.max + ' C (below freezing).' });
      // 3. staple crop flora where there is no growing season
      if (g === 0) (l.flora || []).filter(function (f) { return STAPLE.test(f.role || ''); }).forEach(function (f) { add1({ k: 'bad', ids: [l.id], text: l.name + ': staple flora "' + f.name + '" (' + f.role + ') but growing_season_days is 0.' }); });
    });
    findings = out;
  }

  function buildSpecies() {
    SP = ((G.D.life || {}).species_index || []).slice().sort(function (a, b) { return a.name.localeCompare(b.name); });
    zones = (G.D.climate || {}).zones || [];
  }
  function select(sel) { st.sel = sel; if (root) renderAll(); else st.dirty = true; }
  function selSpecies(s) { select({ kind: 'species', key: s.kind + ':' + s.name, label: s.name, ids: s.locations || [], info: s }); }
  function selZone(z) { select({ kind: 'zone', key: 'zone:' + z.zone, label: 'Climate zone: ' + z.zone, ids: z.locations || [], info: z }); }
  function selRes(name) {
    const k = slug(name), ids = G.locs.filter(function (l) { return (l.resources || []).some(function (r) { return slug(r.name) === k; }); }).map(function (l) { return l.id; });
    select({ kind: 'resource', key: 'res:' + k, label: 'Resource: ' + name, ids: ids, info: null });
  }
  // 'focus-life' from the map: a species, a climate zone, or a resource name
  function focus(name) {
    const k = slug(name);
    const s = SP.filter(function (x) { return slug(x.name) === k; })[0] || SP.filter(function (x) { return x.species_id && slug(x.species_id) === k; })[0];
    if (s) return selSpecies(s);
    const z = zones.filter(function (x) { return slug(x.zone) === k; })[0]; if (z) return selZone(z);
    selRes(name);
  }

  function passVis(id) { const l = G.L[id]; return !l || passes(W, l); }
  function renderMini() {
    clear(ui.mini); miniNodes = {};
    const hl = new Set(st.sel ? st.sel.ids : []), any = hl.size > 0;
    const svg = mkSvg('Mini-map of locations'); mini = svg;
    G.routes.forEach(function (r) { const a = G.L[r.from], b = G.L[r.to]; if (a && b) svg.appendChild(h('svg:line', { x1: a.x, y1: a.y, x2: b.x, y2: b.y, stroke: 'currentColor', 'stroke-opacity': 0.15, 'stroke-width': 1.5 })); });
    const fs = 22;
    G.locs.forEach(function (l) {
      const on = hl.has(l.id), vis = passVis(l.id), sel = W.state && W.state.selected === l.id;
      const g = h('svg:g', { class: 'wbg-node' + (on ? ' wbg-hl' : '') + (sel ? ' wbg-sel' : '') + (!vis || (any && !on) ? ' wbg-dim' : ''), transform: 'translate(' + l.x + ',' + l.y + ')', role: 'button', tabindex: on ? 0 : -1,
        'aria-label': l.name + (on ? ' (highlighted)' : '') + (l.climate && l.climate.zone ? ', ' + l.climate.zone : ''), 'aria-pressed': sel ? 'true' : 'false' },
        h('svg:title', { text: l.name }),
        on ? h('svg:circle', { r: 20, fill: 'none', stroke: 'Highlight', 'stroke-width': 4 }) : null,
        h('svg:path', { class: 'wbg-sh', d: shapeD(on ? 'diamond' : 'circle', on ? 10 : 7), fill: zoneColor(W, l.climate && l.climate.zone) }),
        on ? h('svg:text', { class: 'wbg-lbl', style: 'font-size:' + fs + 'px', 'text-anchor': 'middle', y: 36, text: l.name }) : null);
      const go = function () { WB.select(l.id); };
      g.addEventListener('click', go); g.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); go(); } });
      svg.appendChild(g); miniNodes[l.id] = g;
    });
    ui.mini.appendChild(svg);
    ui.mini.appendChild(h('div', { class: 'wbg-legend' }, h('span', { text: 'Colour = climate zone; large diamond with ring = in selection' })));
  }
  const badge = function (t) { return h('span', { class: 'wbg-flag note', text: t }); };
  function renderZones() {
    clear(ui.zones);
    ui.zones.appendChild(h('h3', { text: 'Climate zones' }));
    if (!zones.length) { ui.zones.appendChild(h('p', { class: 'wbg-empty', text: 'No climate data yet: use the geography-and-climate skill' })); return; }
    const maxP = Math.max.apply(null, zones.map(function (z) { return z.mean_precipitation_mm || 0; }).concat([1]));
    zones.forEach(function (z) {
      const on = st.sel && st.sel.key === 'zone:' + z.zone, tt = z.mean_temperature_c, pp = z.mean_precipitation_mm;
      ui.zones.appendChild(h('button', { type: 'button', class: 'wbg-chip wbg-zone', style: 'display:block;width:100%;text-align:left;border-radius:6px;margin:4px 0;padding:4px 8px;' + (on ? 'outline:2px solid Highlight;' : ''), 'aria-pressed': on ? 'true' : 'false', onclick: function () { selZone(z); } },
        h('span', { style: 'display:inline-block;width:12px;height:12px;margin-right:6px;vertical-align:middle;border:1px solid currentColor;background:' + zoneColor(W, z.zone) }),
        h('strong', { text: z.zone }), ' (' + z.count + ')',
        h('div', null, 'Temp ', h('span', { class: 'wbg-bar2', style: 'width:' + (tt == null ? 0 : Math.max(2, Math.min(100, (tt + 30) / 80 * 100))) + 'px' }), ' ' + (tt == null ? 'n/a' : tt + ' C')),
        h('div', null, 'Rain ', h('span', { class: 'wbg-bar2', style: 'width:' + (pp == null ? 0 : Math.max(2, pp / maxP * 100)) + 'px' }), ' ' + (pp == null ? 'n/a' : Math.round(pp) + ' mm'))));
    });
    const none = G.locs.filter(function (l) { return !l.climate; }).length;
    if (none) ui.zones.appendChild(h('p', { class: 'wbg-dim-t', text: none + ' of ' + G.locs.length + ' locations have no climate data.' }));
  }
  function speciesList(kind, title) {
    const q = st.q.toLowerCase(), list = SP.filter(function (s) { return s.kind === kind && (!q || s.name.toLowerCase().indexOf(q) >= 0 || (s.roles || []).join(' ').toLowerCase().indexOf(q) >= 0); });
    const box = h('div', null, h('h3', { text: title + ' (' + list.length + ')' }));
    if (!list.length) { box.appendChild(h('p', { class: 'wbg-dim-t', text: SP.some(function (s) { return s.kind === kind; }) ? 'No match.' : 'No ' + kind + ' recorded yet: use the geography-and-climate skill.' })); return box; }
    box.appendChild(h('ul', { class: 'wbg-list' }, list.map(function (s) {
      const on = st.sel && st.sel.key === s.kind + ':' + s.name;
      return h('li', null, h('button', { type: 'button', class: 'wbg-chip', style: 'border-radius:6px;' + (on ? 'outline:2px solid Highlight;' : ''), 'aria-pressed': on ? 'true' : 'false', onclick: function () { selSpecies(s); } },
        (kind === 'flora' ? '❀ ' : '◆ ') + s.name + ' ', h('span', { class: 'wbg-dim-t', text: '×' + (s.locations || []).length })), ' ', (s.roles || []).map(badge));
    })));
    return box;
  }
  function renderCentre() {
    clear(ui.centre);
    ui.centre.appendChild(h('label', null, 'Filter species ', h('input', { type: 'search', value: st.q, 'aria-label': 'Filter species', oninput: function (e) { st.q = e.target.value; renderCentre(); } })));
    if (!SP.length) { ui.centre.appendChild(h('p', { class: 'wbg-empty', text: 'No flora or fauna yet: use the geography-and-climate skill.' })); return; }
    ui.centre.appendChild(speciesList('flora', 'Flora')); ui.centre.appendChild(speciesList('fauna', 'Fauna'));
  }
  function renderDetail() {
    clear(ui.detail); const s = st.sel;
    if (!s) { ui.detail.appendChild(h('p', { class: 'wbg-dim-t', text: 'Select a species, a climate zone or a resource to highlight its locations.' })); return; }
    ui.detail.appendChild(h('h3', { text: s.label }));
    if (s.kind === 'species') {
      ui.detail.appendChild(h('p', null, s.info.kind + '; roles: ' + ((s.info.roles || []).join(', ') || 'none'), ' ', s.info.species_id && G.N[s.info.species_id] ? h('button', { type: 'button', class: 'wbg-btn', onclick: function () { WB.select(s.info.species_id); }, text: 'Open species entity' }) : null));
    } else if (s.kind === 'zone') {
      ui.detail.appendChild(h('p', { text: 'Mean temperature ' + (s.info.mean_temperature_c == null ? 'n/a' : s.info.mean_temperature_c + ' C') + ', mean rainfall ' + (s.info.mean_precipitation_mm == null ? 'n/a' : Math.round(s.info.mean_precipitation_mm) + ' mm') }));
    }
    ui.detail.appendChild(s.ids.length ? h('ul', { class: 'wbg-list' }, s.ids.map(function (id) { return h('li', null, h('button', { type: 'button', class: 'wbg-chip', onclick: function () { WB.select(id); }, text: G.name(id) }), passVis(id) ? '' : ' (hidden by filters)'); })) : h('p', { class: 'wbg-dim-t', text: 'No locations recorded.' }));
  }
  function renderFindings() {
    clear(ui.find);
    ui.find.appendChild(h('h3', { text: 'Climate consistency (heuristics)' }));
    ui.find.appendChild(h('p', { class: 'wbg-dim-t', text: 'Quick checks from the data only. They can be wrong: a flag is a prompt to look, not a verdict.' }));
    if (!G.locs.some(function (l) { return l.climate; })) { ui.find.appendChild(h('p', { class: 'wbg-empty', text: 'No climate data yet: use the geography-and-climate skill' })); return; }
    if (!findings.length) { ui.find.appendChild(h('p', { role: 'status', text: 'No inconsistencies flagged by the three heuristics (neighbour contrast, freezing growing season, staple crop with no growing season).' })); return; }
    ui.find.appendChild(h('ul', { class: 'wbg-list' }, findings.map(function (f) {
      return h('li', null, h('span', { class: 'wbg-flag ' + f.k, text: 'FLAG' }), ' ', h('button', { type: 'button', class: 'wbg-btn', style: 'text-align:left', onclick: function () { select({ kind: 'finding', key: 'f:' + f.text, label: 'Flagged: ' + f.ids.map(G.name).join(' and '), ids: f.ids, info: null }); }, text: f.text }));
    })));
  }
  function renderSr() {
    clear(ui.sr);
    ui.sr.appendChild(h('table', null, h('caption', { text: 'Flora and fauna by location (text alternative)' }), h('tbody', null, SP.map(function (s) {
      return h('tr', null, h('th', { text: s.name + ' (' + s.kind + ')' }), h('td', { text: (s.roles || []).join(', ') }), h('td', { text: (s.locations || []).map(G.name).join(', ') }));
    }))));
  }
  function renderAll() {
    st.dirty = false; renderZones(); renderCentre(); renderMini(); renderDetail(); renderFindings(); renderSr();
    ui.empty.style.display = G.locs.length || SP.length || zones.length ? 'none' : '';
  }

  WB.registerView({
    id: 'life', title: 'Life', order: 50,
    create: function (container, wb) {
      W = wb || WB; G = prep(W); injectCss(); buildSpecies(); compute();
      ui.zones = h('div', { class: 'wbg-side', style: 'width:230px;border-left:0;border-right:1px solid rgba(128,128,128,.35)', role: 'region', 'aria-label': 'Climate zones' });
      ui.centre = h('div', { style: 'flex:1 1 260px;overflow:auto;padding:8px 10px;min-width:220px', role: 'region', 'aria-label': 'Species' });
      ui.mini = h('div'); ui.detail = h('div', { 'aria-live': 'polite' }); ui.find = h('div');
      ui.side = h('div', { class: 'wbg-side', style: 'width:380px', role: 'region', 'aria-label': 'Selection and consistency' }, h('div', { style: 'height:300px' }, ui.mini), ui.detail, ui.find);
      ui.sr = h('div', { class: 'wbg-sr' }); ui.empty = h('div', { class: 'wbg-empty', style: 'display:none', text: 'No climate or ecology data yet: use the geography-and-climate skill. ' + ((W.data && W.data.warnings) || []).join('; ') });
      root = h('div', { class: 'wbg-view' }, ui.empty, h('div', { class: 'wbg-body', style: 'flex-wrap:wrap;overflow:auto' }, ui.zones, ui.centre, ui.side), ui.sr);
      container.appendChild(root);
      if (W.bus) W.bus.on('focus-life', function (name) { if (name != null) focus(String(name)); });
      if (pending) { const n = pending; pending = null; focus(n); } else renderAll();
    },
    activate: function () { st.active = true; if (st.dirty) renderAll(); },
    deactivate: function () { st.active = false; },
    resize: function () {},
    onSelect: function () { if (root) { renderMini(); } else st.dirty = true; },
    onFilter: function () { if (root) { renderMini(); renderDetail(); } else st.dirty = true; }
  });
})();
