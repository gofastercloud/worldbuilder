/* WorldBuilder viewer: TRADE view (SVG flow diagram on the map layout). */
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

  const st = { res: '', active: false, dirty: true, raf: 0, refocus: null, reduced: false };
  let W, G, E, root, svg, pz, ui = {}, layers = {}, markers = {}, particles = [], flags = null, comp = {};

  // ---- consistency rules (computed from data only; heuristics) ----
  // Reachability graph: declared map routes PLUS parent/child containment (a system and the planets inside it
  // share an economy), so "reachable" = same connected component of that graph.
  // Food rule: a resource is "food" when its category matches /food|agri|crop|grain|farm|fish|livestock|harvest/
  // or its name matches /food|grain|crop|fish|meat|produce|harvest|ration|livestock/. A location with a known
  // population is "fed" when it produces a food resource, or sits in the same component as a food producer
  // (it can import). If no food resource exists in the data at all, the food check is skipped, not failed.
  const FOOD_CAT = /food|agri|crop|grain|farm|fish|livestock|harvest/i, FOOD_NAME = /food|grain|crop|fish|meat|produce|harvest|ration|livestock/i;
  function isFood(r) { return FOOD_CAT.test(r.category || '') || FOOD_NAME.test(r.name || ''); }
  function components() {
    const par = {}; const find = function (x) { while (par[x] !== x) { par[x] = par[par[x]]; x = par[x]; } return x; };
    G.locs.forEach(function (l) { par[l.id] = l.id; });
    const un = function (a, b) { if (a in par && b in par) par[find(a)] = find(b); };
    G.routes.forEach(function (r) { un(r.from, r.to); }); G.locs.forEach(function (l) { if (l.parent) un(l.id, l.parent); });
    const c = {}; G.locs.forEach(function (l) { c[l.id] = find(l.id); }); return c;
  }
  function computeFlags() {
    comp = components();
    const res = {}, food = (E.resources || []).filter(isFood);
    (E.resources || []).forEach(function (r) {
      const f = [], P = r.producers || [], C = r.consumers || [];
      if (C.length && !P.length) f.push({ k: 'bad', t: 'Consumed, no producer' });
      if (P.length && C.length && !P.some(function (p) { return C.some(function (c) { return comp[p] && comp[p] === comp[c]; }); })) f.push({ k: 'warn', t: 'Produced, no route to any consumer' });
      if (P.length && !C.length) f.push({ k: 'note', t: 'No consumer recorded' });
      res[r.name] = f;
    });
    const unfed = [];
    if (food.length) {
      const fedComp = {}; food.forEach(function (r) { (r.producers || []).forEach(function (p) { if (comp[p]) fedComp[comp[p]] = 1; }); });
      G.locs.forEach(function (l) { if (l.population > 0 && !fedComp[comp[l.id]]) unfed.push(l.id); });
    }
    const missing = [];
    (E.trade_routes || []).forEach(function (t) { (t.map_route_ids || []).forEach(function (id) { if (!G.routes.some(function (r) { return r.id === id; })) missing.push({ t: t, id: id }); }); });
    flags = { res: res, unfed: unfed, noFood: !food.length, missing: missing };
  }
  function carrying(r) {
    const k = slug(r.name), out = {};
    (r.routes || []).forEach(function (id) {
      if (id.indexOf('trade:') === 0) { const t = (E.trade_routes || []).filter(function (x) { return x.id === id.slice(6); })[0]; if (t) (t.map_route_ids || []).forEach(function (m) { out[m] = 1; }); }
      else out[id] = 1;
    });
    G.routes.forEach(function (rt) { if ((rt.goods || []).some(function (g) { return slug(g) === k; })) out[rt.id] = 1; });
    return out;
  }
  const cur = function () { return (E.resources || []).filter(function (r) { return r.name === st.res; })[0]; };

  function stopAnim() { if (st.raf) { try { cancelAnimationFrame(st.raf); } catch (e) { /* none */ } } st.raf = 0; }
  function startAnim() {
    stopAnim(); if (!st.active || st.reduced || !particles.length || typeof requestAnimationFrame !== 'function') return;
    const tick = function () {
      if (!st.active) { st.raf = 0; return; }
      particles.forEach(function (p) { p.t = (p.t + 0.004) % 1; const q = p.c.at(p.t); p.el.setAttribute('cx', q.x.toFixed(1)); p.el.setAttribute('cy', q.y.toFixed(1)); });
      st.raf = requestAnimationFrame(tick);
    };
    st.raf = requestAnimationFrame(tick);
  }

  function render() {
    st.dirty = false; stopAnim(); particles = [];
    Object.keys(layers).forEach(function (k) { clear(layers[k]); }); markers = {};
    const vis = {}; G.locs.forEach(function (l) { if (passes(W, l)) vis[l.id] = l; });
    const r = cur(), carry = r ? carrying(r) : null, P = r ? r.producers || [] : [], C = r ? r.consumers || [] : [], sel = W.state && W.state.selected;
    G.routes.forEach(function (rt) {
      const a = vis[rt.from], b = vis[rt.to]; if (!a || !b) return;
      const on = !carry || carry[rt.id], w = on ? 1.5 + Math.min((rt.goods || []).length, 6) * 0.9 + (carry ? 2 : 0) : 1;
      const c = curve(a, b, 0.1);
      layers.route.appendChild(h('svg:path', { d: c.d, fill: 'none', stroke: on ? (carry ? '#0072B2' : '#888') : '#999', 'stroke-width': w, 'stroke-opacity': on ? 0.85 : 0.2, 'stroke-dasharray': rt.reciprocal === false ? '6 5' : null },
        h('svg:title', { text: G.name(rt.from) + ' ↔ ' + G.name(rt.to) + ': ' + ((rt.goods || []).join(', ') || 'no goods recorded') })));
      if (carry && on) {
        // direction arrow (static, always shown) from a producer end when known, else from -> to
        const fwd = !(P.indexOf(rt.to) >= 0 && P.indexOf(rt.from) < 0), cc = fwd ? c : curve(b, a, -0.1);
        const q = cc.at(0.6), ang = Math.atan2(q.ty, q.tx) * 180 / Math.PI;
        layers.route.appendChild(h('svg:path', { d: 'M-6,-5L6,0L-6,5Z', transform: 'translate(' + q.x.toFixed(1) + ',' + q.y.toFixed(1) + ') rotate(' + ang.toFixed(0) + ')', fill: '#0072B2', stroke: 'Canvas' }));
        if (!st.reduced) for (let i = 0; i < 3; i++) { const el = h('svg:circle', { r: 3.5, fill: '#fff', stroke: '#0072B2', 'stroke-width': 1.5, 'aria-hidden': 'true' }); layers.flow.appendChild(el); particles.push({ el: el, c: cc, t: i / 3 }); }
      }
    });
    Object.keys(vis).map(function (k) { return vis[k]; }).sort(function (a, b) { return rad(b) - rad(a); }).forEach(function (l) {
      const rr = rad(l), p = P.indexOf(l.id) >= 0, c = C.indexOf(l.id) >= 0, unfed = flags.unfed.indexOf(l.id) >= 0;
      const gl = r ? (p && c ? 'PC' : p ? 'P' : c ? 'C' : '') : '';
      const fill = !r ? '#D9D9D9' : p && c ? '#CC79A7' : p ? '#009E73' : c ? '#E69F00' : '#D9D9D9';
      const lab = l.name + (r ? (p ? ', produces ' + r.name : '') + (c ? ', consumes ' + r.name : '') : '') + (unfed ? ', FLAG: population but no food produced or reachable' : '');
      const g = h('svg:g', { class: 'wbg-node' + (l.id === sel ? ' wbg-sel' : ''), transform: 'translate(' + l.x + ',' + l.y + ')', role: 'button', tabindex: -1, 'aria-label': lab, 'aria-pressed': l.id === sel ? 'true' : 'false' },
        h('svg:title', { text: lab }),
        unfed ? h('svg:circle', { r: rr + 6, fill: 'none', stroke: '#D55E00', 'stroke-width': 2.5, 'stroke-dasharray': '4 3' }) : null,
        h('svg:path', { class: 'wbg-sh', d: shapeD(p ? 'triangle' : c ? 'square' : 'circle', rr), fill: fill, 'fill-opacity': r && !p && !c ? 0.6 : 1 }),
        gl ? h('svg:text', { class: 'wbg-glyph', 'text-anchor': 'middle', y: 4, text: gl }) : null,
        unfed ? h('svg:text', { class: 'wbg-lbl', 'text-anchor': 'middle', x: rr + 8, y: -rr, style: 'font-weight:700;fill:#D55E00', text: '!' }) : null,
        h('svg:text', { class: 'wbg-lbl', 'text-anchor': 'middle', y: rr + 13, text: l.name }));
      const act = function () { st.refocus = l.id; WB.select(l.id); };
      g.addEventListener('click', function () { if (!pz.wasDrag()) act(); });
      g.addEventListener('keydown', function (ev) {
        if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); act(); }
        else if (ev.key.indexOf('Arrow') === 0) { ev.preventDefault(); nav(l, ev.key, vis); }
      });
      layers.node.appendChild(g); markers[l.id] = g;
    });
    const ids = Object.keys(markers), tab = markers[sel] ? sel : ids[0];
    if (tab) markers[tab].setAttribute('tabindex', 0);
    if (st.refocus && markers[st.refocus]) markers[st.refocus].focus(); st.refocus = null;
    ui.empty.style.display = G.locs.length ? 'none' : '';
    renderSide(vis); startAnim();
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
  const flagEl = function (f) { return h('span', { class: 'wbg-flag ' + f.k, text: (f.k === 'note' ? 'Note: ' : 'FLAG: ') + f.t }); };
  const nm = function (id) { return G.name(id); };
  function locBtn(id) { return h('button', { type: 'button', class: 'wbg-chip', onclick: function () { WB.select(id); }, text: nm(id) }); }

  function renderSide(vis) {
    clear(ui.side);
    const rs = E.resources || [];
    if (!rs.length && !(E.currencies || []).length && !(E.shocks || []).length) {
      ui.side.appendChild(h('p', { class: 'wbg-empty', text: 'No economy data yet: add world/economy.yaml (resources, trade routes, currencies). ' + ((W.data && W.data.warnings) || []).filter(function (w) { return /econom/i.test(w); }).join('; ') })); return;
    }
    const nflag = rs.filter(function (r) { return flags.res[r.name].some(function (f) { return f.k !== 'note'; }); }).length;
    ui.side.appendChild(h('div', { role: 'status', text: nflag + ' of ' + rs.length + ' resources flagged; ' + flags.unfed.length + ' populated locations without food' + (flags.missing.length ? '; ' + flags.missing.length + ' trade-route legs not declared as map routes' : '') + '.' }));
    ui.side.appendChild(h('div', { class: 'wbg-legend' }, h('span', null, h('span', { style: 'color:#009E73', text: '▲ ' }), 'P producer (green triangle)'), h('span', null, h('span', { style: 'color:#E69F00', text: '■ ' }), 'C consumer (amber square)'),
      h('span', null, h('span', { style: 'color:#D55E00', text: '! ' }), 'no food (dashed ring)'), h('span', { text: st.reduced ? 'Flow particles off (reduced motion); arrows show direction' : 'Dots = flow' })));
    ui.side.appendChild(h('h3', { text: 'Resources' }));
    ui.side.appendChild(h('table', null, h('thead', null, h('tr', null, ['Resource', 'P', 'C', 'Flags'].map(function (t) { return h('th', { text: t, title: t === 'P' ? 'producers' : t === 'C' ? 'consumers' : null }); }))),
      h('tbody', null, rs.map(function (r) {
        const on = r.name === st.res;
        return h('tr', { class: 'wbg-row' + (on ? ' on' : ''), tabindex: 0, role: 'button', 'aria-pressed': on ? 'true' : 'false', 'aria-label': 'Select resource ' + r.name,
          onclick: function () { pick(r.name); }, onkeydown: function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); pick(r.name); } } },
          h('td', { text: r.name + (r.category ? ' (' + r.category + ')' : '') }), h('td', { text: (r.producers || []).length }), h('td', { text: (r.consumers || []).length }), h('td', null, flags.res[r.name].map(flagEl)));
      }))));
    ui.side.appendChild(h('h3', { text: 'Populated locations with no food' }));
    ui.side.appendChild(flags.noFood ? h('p', { class: 'wbg-dim-t', text: 'Check skipped: no food-category resource is defined (rule: category or name matches food, grain, crop, fish...).' })
      : flags.unfed.length ? h('div', null, flags.unfed.map(function (id) { return [flagEl({ k: 'bad', t: '' }), locBtn(id)]; })) : h('p', { text: 'None.' }));
    if (flags.missing.length) {
      ui.side.appendChild(h('h3', { text: 'Trade-route legs with no declared map route' }));
      ui.side.appendChild(h('ul', { class: 'wbg-list' }, flags.missing.map(function (m) { return h('li', null, flagEl({ k: 'warn', t: '' }), m.t.name + ': ' + m.id); })));
    }
    ui.side.appendChild(h('h3', { text: 'Currencies' }));
    ui.side.appendChild((E.currencies || []).length ? h('ul', { class: 'wbg-list' }, E.currencies.map(function (c) {
      return h('li', null, h('strong', { text: c.name }), ' issued by ', G.N[c.issuer] ? locBtn2(c.issuer) : String(c.issuer || 'unknown'), '; accepted in: ', (c.accepted_in || []).length ? (c.accepted_in || []).map(function (id) { return G.N[id] ? locBtn2(id) : id + ' '; }) : 'not recorded');
    })) : h('p', { class: 'wbg-dim-t', text: 'No currencies recorded.' }));
    ui.side.appendChild(h('h3', { text: 'Economic shocks' }));
    ui.side.appendChild((E.shocks || []).length ? h('ul', { class: 'wbg-list' }, E.shocks.map(function (s) {
      const fx = s.effects || {}, txt = Object.keys(fx).map(function (k) { let v = typeof fx[k] === 'string' ? fx[k] : JSON.stringify(fx[k]); if (v && v.length > 140) v = v.slice(0, 137) + '...'; return k.replace(/_/g, ' ') + ': ' + v; }).join(' | ');
      return h('li', null, G.N[s.event] ? h('button', { type: 'button', class: 'wbg-chip', onclick: function () { WB.select(s.event); }, text: G.N[s.event].name }) : h('strong', { text: String(s.event) }), h('div', { class: 'wbg-dim-t', text: txt }));
    })) : h('p', { class: 'wbg-dim-t', text: 'No shocks recorded (shocks: in world/economy.yaml).' }));
  }
  function locBtn2(id) { return h('button', { type: 'button', class: 'wbg-chip', onclick: function () { WB.select(id); }, text: nm(id) }); }
  function pick(name) { st.res = name; if (ui.sel) ui.sel.value = name; render(); }

  WB.registerView({
    id: 'trade', title: 'Trade', order: 40,
    create: function (container, wb) {
      W = wb || WB; G = prep(W); E = G.D.economy || {}; injectCss(); st.reduced = reducedMotion(); computeFlags();
      svg = mkSvg('Trade flow diagram'); pz = panzoom(svg, function (u) { svg.style.setProperty('--wbg-fs', (12 * u) + 'px'); });
      ['route', 'flow', 'node'].forEach(function (k) { layers[k] = h('svg:g'); svg.appendChild(layers[k]); });
      const names = (E.resources || []).map(function (r) { return r.name; }).sort();
      ui.sel = h('select', { 'aria-label': 'Resource', onchange: function (e) { st.res = e.target.value; render(); } }, h('option', { value: '', text: 'All routes (no resource)' }), names.map(function (n) { return h('option', { value: n, text: n }); }));
      ui.side = h('div', { class: 'wbg-side' }); ui.empty = h('div', { class: 'wbg-empty', style: 'display:none', text: 'No locations with map positions yet.' });
      // screen-reader alternative: per-resource producers, consumers and flags
      ui.sr = h('div', { class: 'wbg-sr' }, h('table', null, h('caption', { text: 'Resources (text alternative to the flow diagram)' }),
        h('tbody', null, (E.resources || []).map(function (r) {
          return h('tr', null, h('th', { text: r.name }), h('td', { text: 'producers: ' + ((r.producers || []).map(nm).join(', ') || 'none') }), h('td', { text: 'consumers: ' + ((r.consumers || []).map(nm).join(', ') || 'none') }),
            h('td', { text: flags.res[r.name].map(function (f) { return f.t; }).join('; ') }));
        }))));
      root = h('div', { class: 'wbg-view' }, h('div', { class: 'wbg-bar' }, h('label', null, 'Resource ', ui.sel), zoomBtns(pz)),
        h('div', { class: 'wbg-body' }, h('div', { class: 'wbg-stage' }, svg, ui.empty), ui.side), ui.sr);
      container.appendChild(root); render();
    },
    activate: function () { st.active = true; st.reduced = reducedMotion(); if (st.dirty) render(); else startAnim(); },
    deactivate: function () { st.active = false; stopAnim(); },
    resize: function () { if (pz) pz.refresh(); },
    onSelect: function () { if (root) render(); else st.dirty = true; },
    onFilter: function () { if (root) render(); else st.dirty = true; }
  });
})();
