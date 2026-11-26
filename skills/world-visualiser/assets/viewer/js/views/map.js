/* WorldBuilder viewer: MAP view (SVG renderer; three.js is not needed for a 2D map). */
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
  const CSS = '.wbg-view{display:flex;flex-direction:column;height:100%;min-height:0;font:13px/1.4 system-ui,sans-serif}' +
    '.wbg-bar{display:flex;flex-wrap:wrap;gap:6px 14px;align-items:center;padding:6px 10px;border-bottom:1px solid rgba(128,128,128,.35)}' +
    '.wbg-bar label{display:inline-flex;gap:6px;align-items:center}' +
    '.wbg-body{display:flex;flex:1;min-height:0}.wbg-stage{flex:1 1 auto;min-width:0;position:relative;min-height:320px}' +
    '.wbg-side{width:350px;flex:none;overflow:auto;padding:8px 10px;border-left:1px solid rgba(128,128,128,.35)}' +
    '@media(max-width:820px){.wbg-body{flex-direction:column;overflow:auto}.wbg-side{width:auto;border-left:0;border-top:1px solid rgba(128,128,128,.35)}}' +
    'svg.wbg-svg{width:100%;height:100%;display:block;touch-action:none;cursor:grab;min-height:320px}' +
    '.wbg-sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}' +
    '.wbg-lbl{fill:currentColor;font-size:var(--wbg-fs,12px);paint-order:stroke;stroke:Canvas;stroke-width:3px;stroke-linejoin:round;pointer-events:none}' +
    '.wbg-glyph{font-weight:700;font-size:calc(var(--wbg-fs,12px)*.9);fill:#000;pointer-events:none}' +
    '.wbg-node{cursor:pointer}.wbg-node:focus{outline:none}.wbg-node:focus-visible .wbg-sh{stroke:Highlight;stroke-width:4}' +
    '.wbg-node .wbg-sh{stroke:CanvasText;stroke-width:1.2}.wbg-node.wbg-sel .wbg-sh{stroke:Highlight;stroke-width:4}' +
    '.wbg-node.wbg-dim{opacity:.3}.wbg-node.wbg-hl .wbg-sh{stroke:Highlight;stroke-width:3}' +
    '.wbg-chip,.wbg-btn{font:inherit;color:inherit;background:rgba(128,128,128,.14);border:1px solid rgba(128,128,128,.5);border-radius:11px;padding:1px 8px;margin:1px 3px 1px 0;cursor:pointer}' +
    '.wbg-btn{border-radius:4px;padding:2px 8px}.wbg-chip:hover,.wbg-btn:hover{background:rgba(128,128,128,.3)}' +
    '.wbg-chip:focus-visible,.wbg-btn:focus-visible,.wbg-row:focus-visible{outline:2px solid Highlight;outline-offset:1px}' +
    '.wbg-card h3,.wbg-side h3{margin:10px 0 4px;font-size:13px}.wbg-card dl{display:grid;grid-template-columns:auto 1fr;gap:2px 10px;margin:4px 0}.wbg-card dt{opacity:.7}.wbg-card dd{margin:0}' +
    '.wbg-dim-t{opacity:.7}.wbg-empty{padding:24px;opacity:.85}.wbg-legend{display:flex;flex-wrap:wrap;gap:4px 12px;margin:6px 0}.wbg-legend span{display:inline-flex;gap:4px;align-items:center}' +
    '.wbg-flag{display:inline-block;border-radius:3px;padding:0 5px;margin:1px 3px 1px 0;font-size:11.5px;border:1px solid}' +
    '.wbg-flag.bad{border-color:#D55E00;background:rgba(213,94,0,.2)}.wbg-flag.warn{border-color:#E69F00;background:rgba(230,159,0,.2)}.wbg-flag.note{border-color:rgba(128,128,128,.7);background:rgba(128,128,128,.12)}' +
    '.wbg-side table{width:100%;border-collapse:collapse}.wbg-side th,.wbg-side td{text-align:left;padding:2px 4px;border-bottom:1px solid rgba(128,128,128,.25);vertical-align:top}' +
    '.wbg-row{cursor:pointer}.wbg-row[aria-pressed="true"],.wbg-row.on{background:rgba(0,114,178,.22)}' +
    '.wbg-list{list-style:none;margin:0;padding:0}.wbg-list li{margin:2px 0}.wbg-bar2{display:inline-block;height:8px;background:currentColor;opacity:.55;border-radius:2px;vertical-align:middle}';
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

  const RAMP = ['#440154', '#3b528b', '#21918c', '#5ec962', '#fde725'];
  function lerpHex(a, b, t) {
    const pa = [1, 3, 5].map(function (i) { return parseInt(a.substr(i, 2), 16); }), pb = [1, 3, 5].map(function (i) { return parseInt(b.substr(i, 2), 16); });
    return '#' + pa.map(function (v, i) { return ('0' + Math.round(v + (pb[i] - v) * t).toString(16)).slice(-2); }).join('');
  }
  function ramp(t) { t = Math.max(0, Math.min(1, t)) * (RAMP.length - 1); const i = Math.min(RAMP.length - 2, Math.floor(t)); return lerpHex(RAMP[i], RAMP[i + 1], t - i); }
  // "3-7 days" -> hours (midpoint of a range); null when unparseable
  function parseHours(s) {
    if (!s) return null;
    const m = /(\d+(?:\.\d+)?)(?:\s*(?:-|–|to)\s*(\d+(?:\.\d+)?))?\s*(minutes?|mins?|hours?|hrs?|days?|weeks?|months?|years?|yrs?)/i.exec(String(s));
    if (!m) return null;
    const v = m[2] ? (parseFloat(m[1]) + parseFloat(m[2])) / 2 : parseFloat(m[1]), u = m[3].toLowerCase();
    const k = u.indexOf('min') === 0 ? 1 / 60 : u.indexOf('h') === 0 ? 1 : u.indexOf('d') === 0 ? 24 : u.indexOf('w') === 0 ? 168 : u.indexOf('mo') === 0 ? 720 : 8766;
    return v * k;
  }
  function fmtHours(x) {
    if (x < 1) return Math.round(x * 60) + ' min';
    if (x < 48) return +x.toFixed(1) + ' h';
    if (x < 24 * 90) return +(x / 24).toFixed(1) + ' days';
    return +(x / 8766).toFixed(1) + ' years';
  }
  // time of one route leg = fastest mode with a parseable time; assumed 1 day (flagged) when none parses
  function legTime(r) {
    let best = null;
    (r.modes || []).forEach(function (m) { const t = parseHours(m.time); if (t != null && (best == null || t < best)) best = t; });
    return best == null ? { h: 24, est: true } : { h: best, est: false };
  }
  function shortest(G, a, b) {
    const dist = {}, prev = {}, done = {};
    G.locs.forEach(function (l) { dist[l.id] = Infinity; });
    if (!(a in dist) || !(b in dist)) return null;
    dist[a] = 0;
    for (;;) {
      let u = null;
      for (const id in dist) if (!done[id] && dist[id] < Infinity && (u == null || dist[id] < dist[u])) u = id;
      if (u == null || u === b) break;
      done[u] = 1;
      (G.adj[u] || []).forEach(function (e) { if (!(e.to in dist)) return; const d = dist[u] + legTime(e.r).h; if (d < dist[e.to]) { dist[e.to] = d; prev[e.to] = { from: u, r: e.r }; } });
    }
    if (dist[b] === Infinity) return null;
    const legs = []; let c = b;
    while (c !== a) { legs.unshift(prev[c]); c = prev[c].from; }
    return { total: dist[b], legs: legs, est: legs.some(function (l) { return legTime(l.r).est; }) };
  }

  const st = { mode: 'type', res: '', a: null, b: null, route: null, focusId: null, active: false, dirty: true };
  let W, G, root, svg, pz, ui = {}, layers = {}, markers = {}, modeCol = {}, shapes = {}, typeCol = {};

  function typeColor(t) { return (W.colors && W.colors.type && W.colors.type[t]) || typeCol[t] || '#888'; }
  function resObj() { return ((G.D.economy || {}).resources || []).filter(function (r) { return r.name === st.res; })[0]; }
  function resRole(l) {
    const r = resObj(); if (!r) return { p: false, c: false };
    const k = slug(r.name);
    return { p: (r.producers || []).indexOf(l.id) >= 0 || (l.resources || []).some(function (x) { return slug(x.name) === k; }), c: (r.consumers || []).indexOf(l.id) >= 0 };
  }
  function popRange() {
    const v = G.locs.map(function (l) { return l.population; }).filter(function (x) { return x > 0; }).map(Math.log10);
    return v.length ? [Math.min.apply(null, v), Math.max.apply(null, v)] : [0, 1];
  }
  function colorOf(l, pr) {
    if (st.mode === 'zone') return zoneColor(W, l.climate && l.climate.zone);
    if (st.mode === 'pop') return l.population > 0 ? ramp(pr[1] > pr[0] ? (Math.log10(l.population) - pr[0]) / (pr[1] - pr[0]) : 0.5) : '#BDBDBD';
    if (st.mode === 'res') { const r = resRole(l); return r.p && r.c ? '#CC79A7' : r.p ? '#009E73' : r.c ? '#E69F00' : '#D9D9D9'; }
    return typeColor(l.type || 'place');
  }
  function glyphOf(l) { if (st.mode !== 'res') return ''; const r = resRole(l); return r.p && r.c ? 'PC' : r.p ? 'P' : r.c ? 'C' : ''; }
  function describe(l) {
    const z = l.climate && l.climate.zone;
    return l.name + ', ' + (l.type || 'place') + (l.population != null ? ', population ' + (l.population_label || fmtN(l.population)) : '') + (z ? ', climate ' + z : '');
  }

  // ---------- drawing ----------
  function render() {
    st.dirty = false;
    Object.keys(layers).forEach(function (k) { clear(layers[k]); });
    markers = {};
    const vis = {}; G.locs.forEach(function (l) { if (passes(W, l)) vis[l.id] = l; });
    const pr = popRange(), sel = W.state && W.state.selected;
    // containment hulls: a soft ring around each parent and its visible children
    G.locs.filter(function (l) { return vis[l.id] && (l.children || []).some(function (c) { return vis[c]; }); })
      .sort(function (a, b) { return (a.depth || 0) - (b.depth || 0); }).forEach(function (p) {
        const pts = [p].concat((p.children || []).map(function (c) { return vis[c]; }).filter(Boolean));
        const cx = pts.reduce(function (s, q) { return s + q.x; }, 0) / pts.length, cy = pts.reduce(function (s, q) { return s + q.y; }, 0) / pts.length;
        const r = Math.max.apply(null, pts.map(function (q) { return Math.hypot(q.x - cx, q.y - cy) + rad(q); })) + 18;
        layers.hull.appendChild(h('svg:circle', { cx: cx, cy: cy, r: r, fill: 'currentColor', 'fill-opacity': 0.05, stroke: 'currentColor', 'stroke-opacity': 0.3, 'stroke-dasharray': '2 5' },
          h('svg:title', { text: 'Contains: ' + pts.slice(1).map(function (q) { return q.name; }).join(', ') })));
      });
    // path of the travel ruler
    const path = st.a && st.b ? shortest(G, st.a, st.b) : null;
    const onPath = {}; if (path) path.legs.forEach(function (l) { onPath[l.r.id] = 1; });
    // routes: one curve per mode, width by number of goods, dashed when not reciprocal
    G.routes.forEach(function (r) {
      const a = vis[r.from], b = vis[r.to]; if (!a || !b) return;
      const modes = (r.modes && r.modes.length) ? r.modes : [{ mode: 'unspecified' }], w = 1.2 + Math.min((r.goods || []).length, 6) * 0.9;
      modes.forEach(function (m, i) {
        const c = curve(a, b, 0.08 + (i - (modes.length - 1) / 2) * 0.1);
        if (onPath[r.id]) layers.path.appendChild(h('svg:path', { d: c.d, fill: 'none', stroke: '#FFD400', 'stroke-width': w + 8, 'stroke-opacity': 0.7, 'stroke-linecap': 'round' }));
        layers.route.appendChild(h('svg:path', { d: c.d, fill: 'none', stroke: modeCol[m.mode] || '#888', 'stroke-width': w, 'stroke-opacity': 0.8, 'stroke-dasharray': r.reciprocal === false ? '6 5' : null }));
        layers.route.appendChild(h('svg:path', { d: c.d, fill: 'none', stroke: 'transparent', 'stroke-width': Math.max(w, 12), style: 'cursor:pointer', onclick: function () { if (!pz.wasDrag()) showRoute(r); } },
          h('svg:title', { text: G.name(r.from) + ' ↔ ' + G.name(r.to) + ': ' + modes.map(function (x) { return x.mode + (x.time ? ' (' + x.time + ')' : ''); }).join(', ') + (r.reciprocal === false ? ' [declared on one side only]' : '') })));
      });
    });
    // markers (large first so small ones stay on top)
    Object.keys(vis).map(function (k) { return vis[k]; }).sort(function (a, b) { return rad(b) - rad(a); }).forEach(function (l) {
      const r = rad(l), gl = glyphOf(l);
      const g = h('svg:g', { class: 'wbg-node' + (l.id === sel ? ' wbg-sel' : ''), transform: 'translate(' + l.x + ',' + l.y + ')', role: 'button', tabindex: -1, 'aria-label': describe(l), 'aria-pressed': l.id === sel ? 'true' : 'false', 'data-id': l.id },
        h('svg:title', { text: describe(l) }),
        h('svg:path', { class: 'wbg-sh', d: shapeD(shapes[l.type || 'place'], r), fill: colorOf(l, pr), 'fill-opacity': l.population > 0 ? 1 : 0.75, 'stroke-dasharray': l.population > 0 ? null : '3 2' }),
        gl ? h('svg:text', { class: 'wbg-glyph', 'text-anchor': 'middle', y: 4, text: gl }) : null,
        st.a === l.id || st.b === l.id ? h('svg:text', { class: 'wbg-lbl', 'text-anchor': 'middle', y: -r - 6, style: 'font-weight:700', text: st.a === l.id ? 'A' : 'B' }) : null,
        h('svg:text', { class: 'wbg-lbl', 'text-anchor': 'middle', y: r + 13, text: l.name }));
      g.addEventListener('click', function (ev) { if (pz.wasDrag()) return; activateNode(l.id, ev.shiftKey); });
      g.addEventListener('keydown', function (ev) {
        if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); activateNode(l.id, ev.shiftKey); }
        else if (ev.key.indexOf('Arrow') === 0) { ev.preventDefault(); nav(l, ev.key, vis); }
      });
      g.addEventListener('focus', function () { st.focusId = l.id; });
      layers.node.appendChild(g); markers[l.id] = g;
    });
    const ids = Object.keys(markers), tab = markers[sel] ? sel : st.focusId && markers[st.focusId] ? st.focusId : ids[0];
    if (tab) markers[tab].setAttribute('tabindex', 0);
    if (st.refocus && markers[st.refocus]) { markers[st.refocus].focus(); } st.refocus = null;
    renderLegend(); renderRuler(path); renderCard(); renderSr(vis);
    ui.empty.style.display = G.locs.length ? 'none' : '';
    if (G.locs.length && !ids.length) ui.count.textContent = 'No locations match the current filters.'; else ui.count.textContent = ids.length + ' of ' + G.locs.length + ' locations shown';
  }
  function nav(from, key, vis) {
    const ux = key === 'ArrowRight' ? 1 : key === 'ArrowLeft' ? -1 : 0, uy = key === 'ArrowDown' ? 1 : key === 'ArrowUp' ? -1 : 0;
    let best = null, bs = Infinity;
    Object.keys(vis).forEach(function (id) {
      if (id === from.id) return;
      const dx = vis[id].x - from.x, dy = vis[id].y - from.y, d = Math.hypot(dx, dy) || 1, dot = (dx * ux + dy * uy) / d;
      if (dot > 0.5 && d / dot < bs) { bs = d / dot; best = id; }
    });
    if (best) { markers[from.id].setAttribute('tabindex', -1); markers[best].setAttribute('tabindex', 0); markers[best].focus(); }
  }
  function activateNode(id, shift) {
    st.refocus = id;
    if (shift) { rulerPick(id); return; }
    st.route = null; WB.select(id);
  }
  function rulerPick(id) { if (!st.a || (st.a && st.b)) { st.a = id; st.b = null; } else if (id !== st.a) st.b = id; st.refocus = id; render(); }

  function renderLegend() {
    clear(ui.legend);
    const types = G.types.map(function (t) {
      const sw = h('svg:svg', { width: 16, height: 16, viewBox: '-12 -12 24 24', 'aria-hidden': 'true' }, h('svg:path', { d: shapeD(shapes[t], 7), fill: st.mode === 'type' ? typeColor(t) : '#999', stroke: 'currentColor' }));
      return h('span', null, sw, t);
    });
    ui.legend.appendChild(h('div', null, h('strong', { text: 'Shape = type' }), h('div', { class: 'wbg-legend' }, types)));
    const swatch = function (c, t) { return h('span', null, h('span', { style: 'display:inline-block;width:12px;height:12px;border:1px solid currentColor;background:' + c }), t); };
    let key = null;
    if (st.mode === 'zone') {
      const zs = (G.D.climate && G.D.climate.zones) || [];
      key = zs.length ? zs.map(function (z) { return swatch(zoneColor(W, z.zone), z.zone + ' (' + z.count + ')'); }) : [h('span', { text: 'No climate data yet: use the geography-and-climate skill' })];
      key.push(swatch('#BDBDBD', 'no climate data'));
    } else if (st.mode === 'pop') {
      const pr = popRange(); key = [h('span', { text: 'population (log): ' + fmtN(Math.pow(10, pr[0])) }), h('span', { style: 'display:inline-block;width:90px;height:10px;border:1px solid currentColor;background:linear-gradient(90deg,' + RAMP.join(',') + ')' }), h('span', { text: fmtN(Math.pow(10, pr[1])) }), swatch('#BDBDBD', 'unknown')];
    } else if (st.mode === 'res') {
      key = [swatch('#009E73', 'P produces'), swatch('#E69F00', 'C consumes'), swatch('#CC79A7', 'PC both'), swatch('#D9D9D9', 'neither')];
    } else key = [h('span', { text: 'Colour = type (shape repeats it)' })];
    ui.legend.appendChild(h('div', null, h('strong', { text: 'Colour' }), h('div', { class: 'wbg-legend' }, key)));
    const ms = Object.keys(modeCol).map(function (m) { return h('span', null, h('svg:svg', { width: 26, height: 8, 'aria-hidden': 'true' }, h('svg:line', { x1: 0, y1: 4, x2: 26, y2: 4, stroke: modeCol[m], 'stroke-width': 3 })), m); });
    ui.legend.appendChild(h('div', null, h('strong', { text: 'Routes' }), h('div', { class: 'wbg-legend' }, ms.length ? ms : [h('span', { text: 'no routes' })],
      h('span', null, h('svg:svg', { width: 26, height: 8, 'aria-hidden': 'true' }, h('svg:line', { x1: 0, y1: 4, x2: 26, y2: 4, stroke: 'currentColor', 'stroke-width': 3, 'stroke-dasharray': '6 5' })), 'dashed = declared one side only'),
      h('span', { text: 'width = number of goods' }))));
  }
  function chips(items, titleFn) {
    return items.map(function (x) { return h('button', { type: 'button', class: 'wbg-chip', title: titleFn ? titleFn(x) : 'Show in life view', 'aria-label': 'Focus ' + x.name + ' in life view', onclick: function () { WB.bus.emit('focus-life', x.name); }, text: x.name }); });
  }
  function renderCard() {
    clear(ui.card);
    const l = G.L[W.state && W.state.selected];
    if (st.route) {
      const r = st.route;
      ui.card.appendChild(h('div', null, h('h3', { text: 'Route: ' + G.name(r.from) + ' ↔ ' + G.name(r.to) }),
        h('ul', { class: 'wbg-list' }, (r.modes || []).map(function (m) { return h('li', { text: m.mode + (m.distance ? ', ' + m.distance : '') + (m.time ? ', ' + m.time : '') }); })),
        h('p', { text: 'Goods: ' + ((r.goods || []).join(', ') || 'none recorded') }),
        r.reciprocal === false ? h('p', { class: 'wbg-flag warn', text: 'Declared on one side only (validator warning)' }) : null,
        h('button', { class: 'wbg-btn', type: 'button', onclick: function () { st.route = null; renderCard(); }, text: 'Close' })));
      return;
    }
    if (!l) { ui.card.appendChild(h('p', { class: 'wbg-dim-t', text: G.locs.length ? 'Select a location (click or Enter). Shift-click sets the travel ruler start, then end.' : '' })); return; }
    const c = l.climate, parent = l.parent && G.L[l.parent];
    const rows = [['Type', l.type || 'place'], ['Parent', parent ? h('button', { class: 'wbg-chip', type: 'button', onclick: function () { WB.select(parent.id); }, text: parent.name }) : 'none (top level)'],
      ['Terrain', l.terrain || 'not recorded'], ['Elevation', l.elevation_m != null ? fmtN(l.elevation_m) + ' m' : 'not recorded'], ['Area', l.area_km2 != null ? fmtN(l.area_km2) + ' km²' : 'not recorded'],
      ['Population', l.population_label || (l.population != null ? fmtN(l.population) : 'not recorded')],
      ['Climate zone', c ? (c.zone || 'unspecified') + (c.inherited ? ' (inherited)' : '') : 'not recorded']];
    if (c && c.growing_season_days != null) rows.push(['Growing season', c.growing_season_days + ' days']);
    if (c && c.precipitation_mm != null) rows.push(['Precipitation', c.precipitation_mm + ' mm']);
    const dl = h('dl', null, rows.map(function (r) { return [h('dt', { text: r[0] }), h('dd', null, r[1])]; }));
    const group = function (t, a, tf) { return a && a.length ? [h('h3', { text: t }), h('div', null, chips(a, tf))] : []; };
    ui.card.appendChild(h('div', null, h('h3', { text: l.name }), dl,
      c ? null : h('p', { class: 'wbg-dim-t', text: 'No climate data yet: use the geography-and-climate skill' }),
      group('Resources', l.resources, function (x) { return (x.category || 'resource') + (x.rarity ? ', ' + x.rarity : ''); }),
      group('Flora', l.flora, function (x) { return x.role || 'flora'; }), group('Fauna', l.fauna, function (x) { return x.role || 'fauna'; }),
      h('div', { style: 'margin-top:6px' }, h('button', { class: 'wbg-btn', type: 'button', onclick: function () { st.a = l.id; st.b = null; st.refocus = l.id; render(); }, text: 'Ruler start here' }),
        h('button', { class: 'wbg-btn', type: 'button', onclick: function () { if (st.a && st.a !== l.id) { st.b = l.id; st.refocus = l.id; render(); } }, text: 'Ruler end here' }))));
  }
  function showRoute(r) { st.route = r; renderCard(); }
  function renderRuler(path) {
    clear(ui.ruler);
    if (!st.a) { ui.ruler.appendChild(h('span', { class: 'wbg-dim-t', text: 'Travel ruler: shift-click two locations' })); return; }
    const clr = h('button', { class: 'wbg-btn', type: 'button', onclick: function () { st.a = st.b = null; render(); }, text: 'Clear ruler' });
    if (!st.b) { ui.ruler.appendChild(h('span', null, 'Ruler: from ' + G.name(st.a) + ', pick an end ', clr)); return; }
    if (!path) { ui.ruler.appendChild(h('span', null, 'No route chain between ' + G.name(st.a) + ' and ' + G.name(st.b) + ' ', clr)); return; }
    const chain = [G.name(st.a)]; path.legs.forEach(function (l) { chain.push(G.name(l.r.from === l.from ? l.r.to : l.r.from)); });
    ui.ruler.appendChild(h('span', { role: 'status' }, h('strong', { text: chain.join(' → ') }), ': ' + fmtHours(path.total) + (path.est ? ' (some legs have no parseable time, assumed 1 day)' : '') + ' ', clr));
  }
  function renderSr(vis) {
    clear(ui.sr);
    ui.sr.appendChild(h('table', null, h('caption', { text: 'Locations (text alternative to the map)' }),
      h('thead', null, h('tr', null, ['Name', 'Type', 'Parent', 'Population', 'Climate zone', 'Terrain'].map(function (t) { return h('th', { text: t }); }))),
      h('tbody', null, Object.keys(vis).map(function (id) {
        const l = vis[id];
        return h('tr', null, h('td', null, h('button', { type: 'button', tabindex: -1, onclick: function () { WB.select(id); }, text: l.name })), h('td', { text: l.type || '' }), h('td', { text: l.parent ? G.name(l.parent) : '' }),
          h('td', { text: l.population_label || '' }), h('td', { text: (l.climate && l.climate.zone) || '' }), h('td', { text: l.terrain || '' }));
      }))));
    ui.sr.appendChild(h('ul', null, G.routes.map(function (r) { return h('li', { text: 'Route ' + G.name(r.from) + ' to ' + G.name(r.to) + ': ' + (r.modes || []).map(function (m) { return m.mode + (m.time ? ' ' + m.time : ''); }).join(', ') }); })));
  }
  function syncMode() { ui.resWrap.style.display = st.mode === 'res' ? '' : 'none'; }

  WB.registerView({
    id: 'map', title: 'Map', order: 30,
    create: function (container, wb) {
      W = wb || WB; G = prep(W); injectCss();
      G.types.forEach(function (t, i) { typeCol[t] = PAL[i % PAL.length]; }); shapes = shapeMap(G.types);
      const modes = {}; G.routes.forEach(function (r) { (r.modes || []).forEach(function (m) { modes[m.mode] = 1; }); });
      Object.keys(modes).sort().forEach(function (m, i) { modeCol[m] = PAL[i % PAL.length]; });
      const resources = ((G.D.economy || {}).resources || []).map(function (r) { return r.name; }).sort(); st.res = resources[0] || '';
      svg = mkSvg('Map of locations'); pz = panzoom(svg, function (u) { svg.style.setProperty('--wbg-fs', (12 * u) + 'px'); });
      ['hull', 'path', 'route', 'node'].forEach(function (k) { layers[k] = h('svg:g', { 'data-layer': k }); svg.appendChild(layers[k]); });
      const modeSel = h('select', { id: 'wbg-map-mode', onchange: function (e) { st.mode = e.target.value; syncMode(); render(); } },
        [['type', 'Type'], ['zone', 'Climate zone'], ['res', 'Resource availability'], ['pop', 'Population']].map(function (o) { return h('option', { value: o[0], text: o[1] }); }));
      const resSel = h('select', { id: 'wbg-map-res', 'aria-label': 'Resource', onchange: function (e) { st.res = e.target.value; render(); } },
        resources.length ? resources.map(function (r) { return h('option', { value: r, text: r }); }) : [h('option', { value: '', text: 'No economy data yet' })]);
      ui.resWrap = h('label', null, 'Resource ', resSel); ui.count = h('span', { class: 'wbg-dim-t', role: 'status' });
      ui.ruler = h('span'); ui.legend = h('div'); ui.card = h('div', { class: 'wbg-card', 'aria-live': 'polite' }); ui.sr = h('div', { class: 'wbg-sr' });
      ui.empty = h('div', { class: 'wbg-empty', style: 'display:none', text: 'No locations with map positions yet. ' + ((W.data && W.data.warnings) || []).join('; ') });
      root = h('div', { class: 'wbg-view' },
        h('div', { class: 'wbg-bar' }, h('label', null, 'Colour by ', modeSel), ui.resWrap, zoomBtns(pz), ui.count, ui.ruler),
        h('div', { class: 'wbg-body' }, h('div', { class: 'wbg-stage' }, svg, ui.empty), h('div', { class: 'wbg-side' }, ui.card, ui.legend)), ui.sr);
      container.appendChild(root); syncMode();
      if (W.bus) { W.bus.on('highlight', function (ids) { const s = ids ? new Set(ids) : null; Object.keys(markers).forEach(function (id) { markers[id].classList.toggle('wbg-hl', !!(s && s.has(id))); }); }); }
      render();
    },
    activate: function () { st.active = true; if (st.dirty) render(); else { renderCard(); } },
    deactivate: function () { st.active = false; },
    resize: function () { if (pz) pz.refresh(); },
    onSelect: function () { st.route = null; if (root) render(); else st.dirty = true; },
    onFilter: function () { if (root) render(); else st.dirty = true; }
  });
})();
