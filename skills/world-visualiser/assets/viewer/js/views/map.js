/* WorldBuilder viewer: MAP view — Interactive Zoomable & Pannable Cartographic Atlas
 * with procedural climate biome halos, topographic contour rings, parent->child tether arcs,
 * animated travel/trade pulses, display toggles, hover spotlight, and travel ruler. */
(function () {
  'use strict';
  if (typeof WB === 'undefined' || !WB || !WB.registerView) return;
  const NS = 'http://www.w3.org/2000/svg';
  function add(n, c) {
    if (c == null || c === false) return;
    if (Array.isArray(c)) c.forEach(function (x) { add(n, x); });
    else n.appendChild(typeof c === 'object' ? c : document.createTextNode(String(c)));
  }
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
    return {
      D: D, locs: locs, routes: routes, L: L, N: N, adj: adj, types: types,
      name: function (id) { return (L[id] && L[id].name) || (N[id] && N[id].name) || String(id); },
    };
  }
  function passes(WB, l) {
    const f = (WB.state && WB.state.filters) || {};
    const t = f.types;
    if (t && t.size && !t.has(l.type) && !t.has('location')) return false;
    const s = String(f.search || '').trim().toLowerCase();
    if (s && (l.name + ' ' + l.id).toLowerCase().indexOf(s) < 0) return false;
    return true;
  }
  function zoneColor(WB, z) {
    if (!z || z === 'unspecified') return '#94a3b8';
    try { if (WB.colors && typeof WB.colors.zone === 'function') return WB.colors.zone(z) || '#94a3b8'; } catch (e) { /* fall through */ }
    const lg = (WB.data && WB.data.climate && WB.data.climate.legend) || {};
    return lg[z] || '#94a3b8';
  }
  const PAL = ['#0072B2', '#D55E00', '#009E73', '#CC79A7', '#56B4E9', '#E69F00', '#882255', '#44AA99'];
  const SHAPES = ['circle', 'square', 'diamond', 'triangle', 'hexagon', 'star', 'plus'];
  const PRESET = {
    planet: 'circle', moon: 'circle', station: 'square', region: 'hexagon', system: 'star', city: 'diamond',
    settlement: 'diamond', continent: 'hexagon', realm: 'hexagon', building: 'triangle', landmark: 'triangle',
  };
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
  function curve(a, b, bend) {
    const mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2, dx = b.x - a.x, dy = b.y - a.y;
    const cx = mx - dy * bend, cy = my + dx * bend;
    return {
      d: 'M' + a.x + ',' + a.y + 'Q' + cx.toFixed(1) + ',' + cy.toFixed(1) + ' ' + b.x + ',' + b.y,
      at: function (t) {
        const u = 1 - t;
        return {
          x: u * u * a.x + 2 * u * t * cx + t * t * b.x,
          y: u * u * a.y + 2 * u * t * cy + t * t * b.y,
          tx: 2 * u * (cx - a.x) + 2 * t * (b.x - cx),
          ty: 2 * u * (cy - a.y) + 2 * t * (b.y - cy),
        };
      },
    };
  }
  function panzoom(svg, onChange) {
    const home = { x: -40, y: -40, w: 1080, h: 1080 };
    const vb = { x: home.x, y: home.y, w: home.w, h: home.h };
    let drag = null, moved = 0;
    function upp() { const r = svg.getBoundingClientRect ? svg.getBoundingClientRect() : { width: 800, height: 800 }; return Math.max(vb.w / (r.width || 800), vb.h / (r.height || 800)); }
    function zoomPct() { return Math.round((home.w / vb.w) * 100); }
    function apply() { svg.setAttribute('viewBox', vb.x.toFixed(1) + ' ' + vb.y.toFixed(1) + ' ' + vb.w.toFixed(1) + ' ' + vb.h.toFixed(1)); if (onChange) onChange(upp(), zoomPct()); }
    function toSvg(ev) {
      try { const p = svg.createSVGPoint(); p.x = ev.clientX; p.y = ev.clientY; const q = p.matrixTransform(svg.getScreenCTM().inverse()); return { x: q.x, y: q.y }; }
      catch (e) { return { x: vb.x + vb.w / 2, y: vb.y + vb.h / 2 }; }
    }
    function zoom(f, c) {
      const k = Math.min(2200, Math.max(80, vb.w * f)) / vb.w;
      c = c || { x: vb.x + vb.w / 2, y: vb.y + vb.h / 2 };
      vb.x = c.x - (c.x - vb.x) * k; vb.y = c.y - (c.y - vb.y) * k; vb.w *= k; vb.h *= k; apply();
    }
    svg.addEventListener('wheel', function (ev) { ev.preventDefault(); zoom(Math.pow(1.0015, ev.deltaY), toSvg(ev)); }, { passive: false });
    svg.addEventListener('pointerdown', function (ev) { drag = { cx: ev.clientX, cy: ev.clientY, x: vb.x, y: vb.y }; moved = 0; svg.style.cursor = 'grabbing'; });
    svg.addEventListener('pointermove', function (ev) {
      if (!drag) return;
      const dx = ev.clientX - drag.cx, dy = ev.clientY - drag.cy; moved = Math.max(moved, Math.abs(dx) + Math.abs(dy));
      if (moved > 4) { const u = upp(); vb.x = drag.x - dx * u; vb.y = drag.y - dy * u; apply(); }
    });
    const end = function () { drag = null; svg.style.cursor = 'grab'; };
    svg.addEventListener('pointerup', end); svg.addEventListener('pointerleave', end); svg.addEventListener('pointercancel', end);
    svg.addEventListener('keydown', function (ev) {
      if (ev.key === '+' || ev.key === '=') zoom(0.8);
      else if (ev.key === '-') zoom(1.25);
      else if (ev.key === '0') { Object.assign(vb, home); apply(); }
    });
    apply();
    return {
      refresh: apply,
      zoomIn: function () { zoom(0.78); },
      zoomOut: function () { zoom(1.28); },
      reset: function () { Object.assign(vb, home); apply(); },
      wasDrag: function () { return moved > 4; },
      upp: upp,
      zoomPct: zoomPct,
    };
  }

  const BASE_CSS = '.wbg-view{display:flex;flex-direction:column;height:100%;min-height:0;font:13px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;color:var(--fg,CanvasText)}' +
    '.wbg-bar{display:flex;flex-wrap:wrap;gap:8px 12px;align-items:center;padding:8px 14px;border-bottom:1px solid var(--border,rgba(128,128,128,.35));background:var(--glass,var(--panel,transparent));backdrop-filter:blur(12px)}' +
    '.wbg-bar label{display:inline-flex;gap:6px;align-items:center;color:var(--muted,inherit);font-weight:500;font-size:12.5px}' +
    '.wbg-bar select,.wbg-view input[type=search]{background:var(--surface,Canvas);color:var(--fg,CanvasText);border:1px solid var(--border,rgba(128,128,128,.5));border-radius:var(--radius-sm,6px);padding:4px 8px}' +
    '.wbg-body{display:flex;flex:1;min-height:0}.wbg-stage{flex:1 1 auto;min-width:0;position:relative;min-height:320px;background:var(--bg,Canvas);overflow:hidden}' +
    '.wbg-side{width:348px;flex:none;overflow:auto;padding:12px 14px;border-left:1px solid var(--border,rgba(128,128,128,.35));background:var(--panel,transparent)}' +
    '@media(max-width:820px){.wbg-body{flex-direction:column;overflow:auto}.wbg-side{width:auto;border-left:0;border-top:1px solid var(--border,rgba(128,128,128,.35))}}' +
    'svg.wbg-svg{width:100%;height:100%;display:block;touch-action:none;cursor:grab;min-height:320px}' +
    '.wbg-sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}' +
    '.wbg-lbl{fill:var(--fg,currentColor);font-size:var(--wbg-fs,12px);font-weight:600;paint-order:stroke;stroke:var(--bg,Canvas);stroke-width:3.6px;stroke-linejoin:round;pointer-events:none;transition:opacity 160ms ease}' +
    '.wbg-glyph{font-weight:700;font-size:calc(var(--wbg-fs,12px)*.88);fill:#0e1117;pointer-events:none}' +
    '.wbg-node{cursor:pointer;transition:opacity 160ms ease}.wbg-node:focus{outline:none}.wbg-node:focus-visible .wbg-sh{stroke:var(--focus,Highlight);stroke-width:4}' +
    '.wbg-node .wbg-sh{stroke:var(--panel,Canvas);stroke-width:1.8;transition:stroke-width 140ms ease}.wbg-node.wbg-sel .wbg-sh{stroke:var(--focus,Highlight);stroke-width:3.8}' +
    '.wbg-node.wbg-dim{opacity:.18}.wbg-node.wbg-hl .wbg-sh{stroke:var(--accent,Highlight);stroke-width:3.5}' +
    '.wbg-chip,.wbg-btn{font:inherit;color:var(--fg,inherit);background:var(--surface,rgba(128,128,128,.14));border:1px solid var(--border,rgba(128,128,128,.5));border-radius:999px;padding:3px 10px;margin:2px 4px 2px 0;cursor:pointer;transition:background-color 140ms ease,border-color 140ms ease,box-shadow 140ms ease}' +
    '.wbg-btn{border-radius:var(--radius-sm,6px);padding:4px 9px;font-weight:500;font-size:12.5px}.wbg-chip:hover,.wbg-btn:hover{background:var(--surface-hover,rgba(128,128,128,.28));border-color:var(--accent,Highlight)}' +
    '.wbg-btn[aria-pressed="true"],.wbg-chip[aria-pressed="true"]{background:var(--accent-soft,rgba(0,114,178,.18));border-color:var(--accent,Highlight);box-shadow:inset 0 0 0 1px var(--accent,Highlight)}' +
    '.wbg-chip:focus-visible,.wbg-btn:focus-visible,.wbg-row:focus-visible{outline:2px solid var(--focus,Highlight);outline-offset:1px}' +
    '.wbg-card h3,.wbg-side h3{margin:14px 0 6px;font-size:11.5px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--muted,inherit)}' +
    '.wbg-card dl{display:grid;grid-template-columns:auto 1fr;gap:5px 12px;margin:6px 0;padding:10px 12px;background:var(--surface,transparent);border:1px solid var(--border-subtle,rgba(128,128,128,.25));border-radius:var(--radius-md,8px)}' +
    '.wbg-card dt{color:var(--muted,inherit);font-weight:600;font-size:12px}.wbg-card dd{margin:0}' +
    '.wbg-dim-t{color:var(--muted,inherit)}.wbg-empty{padding:24px;color:var(--muted,inherit)}.wbg-legend{display:flex;flex-wrap:wrap;gap:5px 12px;margin:6px 0}.wbg-legend span{display:inline-flex;gap:5px;align-items:center}' +
    '.wbg-flag{display:inline-block;border-radius:4px;padding:1px 6px;margin:1px 3px 1px 0;font-size:11.5px;font-weight:600;border:1px solid}' +
    '.wbg-flag.bad{border-color:#D55E00;background:rgba(213,94,0,.18)}.wbg-flag.warn{border-color:#E69F00;background:rgba(230,159,0,.18)}.wbg-flag.note{border-color:var(--border,rgba(128,128,128,.7));background:var(--surface,rgba(128,128,128,.12))}' +
    '.wbg-side table{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums}.wbg-side th,.wbg-side td{text-align:left;padding:5px 6px;border-bottom:1px solid var(--border-subtle,rgba(128,128,128,.25));vertical-align:top}' +
    '.wbg-side th{font-size:11.5px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted,inherit)}' +
    '.wbg-row{cursor:pointer;transition:background-color 120ms ease}.wbg-row:hover{background:var(--surface,rgba(128,128,128,.12))}.wbg-row[aria-pressed="true"],.wbg-row.on{background:var(--accent-soft,rgba(0,114,178,.22))}' +
    '.wbg-list{list-style:none;margin:0;padding:0}.wbg-list li{margin:4px 0}.wbg-bar2{display:inline-block;height:8px;background:var(--accent,currentColor);opacity:.72;border-radius:3px;vertical-align:middle}';

  const MAP_CSS = '.wbm-toggles{display:inline-flex;flex-wrap:wrap;gap:5px;align-items:center}' +
    '.wbm-hud{position:absolute;right:14px;bottom:14px;z-index:8;display:flex;align-items:center;gap:4px;padding:5px 7px;border-radius:var(--radius-md,10px);background:var(--glass,var(--panel));backdrop-filter:blur(12px);border:1px solid var(--border);box-shadow:var(--shadow-md)}' +
    '.wbm-hud-pct{min-width:42px;text-align:center;font-size:11.5px;font-weight:700;font-variant-numeric:tabular-nums;color:var(--muted)}' +
    '.wbm-tip{position:absolute;z-index:12;pointer-events:none;max-width:250px;padding:9px 12px;border-radius:var(--radius-md,10px);background:var(--glass,var(--panel));backdrop-filter:blur(14px);border:1px solid color-mix(in srgb,var(--accent) 45%,var(--border));box-shadow:var(--shadow-lg);font-size:12px;line-height:1.45}' +
    '.wbm-tip[hidden]{display:none}.wbm-tip-title{font-weight:700;font-size:13px;margin-bottom:3px}.wbm-tip-sub{color:var(--muted);font-size:11.5px;margin-bottom:4px}.wbm-tip-routes{border-top:1px solid var(--border-subtle);padding-top:4px;margin-top:4px;font-size:11px;color:var(--muted)}' +
    '.wbm-grid-minor{stroke:var(--border);stroke-opacity:.22;stroke-width:.7}.wbm-grid-major{stroke:var(--border);stroke-opacity:.48;stroke-width:1.1}' +
    '.wbm-coord{fill:var(--muted);font-size:10px;opacity:.65;font-variant-numeric:tabular-nums;pointer-events:none}' +
    '.wbm-tether{fill:none;stroke:var(--muted);stroke-opacity:.35;stroke-width:1.2;stroke-dasharray:3 5;pointer-events:none}' +
    '.wbm-contour{fill:none;stroke:var(--fg);stroke-opacity:.18;stroke-width:1;pointer-events:none}' +
    '.wbm-route-line{transition:opacity 160ms ease,stroke-width 160ms ease}.wbm-route-dim{opacity:.12 !important}.wbm-route-lit{stroke-opacity:1 !important;filter:url(#wbm-glow)}' +
    '.wbm-route-badge-bg{fill:var(--panel);fill-opacity:.9;stroke:var(--accent);stroke-width:1}.wbm-route-badge-txt{fill:var(--fg);font-size:calc(var(--wbg-fs,12px)*.82);font-weight:600;pointer-events:none}' +
    '@media(prefers-reduced-motion:reduce){.wbm-pulse{display:none}}';

  function injectCss() {
    try {
      const head = document.head || document.body;
      if (!document.getElementById('wbg-css')) { const s = h('style', { id: 'wbg-css' }); s.textContent = BASE_CSS; head.appendChild(s); }
      if (!document.getElementById('wbg-map-css')) { const s2 = h('style', { id: 'wbg-map-css' }); s2.textContent = MAP_CSS; head.appendChild(s2); }
    } catch (e) { /* no DOM head */ }
  }
  function reducedMotion() { try { return !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches); } catch (e) { return false; } }
  function mkSvg(label) { return h('svg:svg', { class: 'wbg-svg', viewBox: '-40 -40 1080 1080', role: 'group', 'aria-label': label, preserveAspectRatio: 'xMidYMid meet' }); }

  const RAMP = ['#440154', '#3b528b', '#21918c', '#5ec962', '#fde725'];
  function lerpHex(a, b, t) {
    const pa = [1, 3, 5].map(function (i) { return parseInt(a.substr(i, 2), 16); }), pb = [1, 3, 5].map(function (i) { return parseInt(b.substr(i, 2), 16); });
    return '#' + pa.map(function (v, i) { return ('0' + Math.round(v + (pb[i] - v) * t).toString(16)).slice(-2); }).join('');
  }
  function ramp(t) { t = Math.max(0, Math.min(1, t)) * (RAMP.length - 1); const i = Math.min(RAMP.length - 2, Math.floor(t)); return lerpHex(RAMP[i], RAMP[i + 1], t - i); }
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

  const st = {
    mode: 'type', sizeBy: 'population', style: 'topographic', halos: true, pulses: true, labels: true,
    res: '', a: null, b: null, route: null, hoverId: null, focusId: null,
    active: false, dirty: true, raf: 0, reduced: false,
  };
  let W, G, root, stage, svg, pz, ui = {}, layers = {}, markers = {}, routeEls = [], pulses = [], modeCol = {}, shapes = {}, typeCol = {};
  const terrainCache = {};

  function hashSeed(str) {
    let h0 = 2166136261;
    const s = String(str || 'world');
    for (let i = 0; i < s.length; i++) { h0 ^= s.charCodeAt(i); h0 = Math.imul(h0, 16777619); }
    return h0 >>> 0;
  }
  function vNoise(x, y, seed) {
    const xi = Math.floor(x), yi = Math.floor(y);
    const xf = x - xi, yf = y - yi;
    const u = xf * xf * (3 - 2 * xf), v = yf * yf * (3 - 2 * yf);
    function h2(ix, iy) {
      let n = Math.imul(ix, 374761393) ^ Math.imul(iy, 668265263) ^ Math.imul(seed, 1442695041);
      n = Math.imul(n ^ (n >>> 13), 1274126177);
      return ((n ^ (n >>> 16)) >>> 0) / 4294967295;
    }
    const a = h2(xi, yi), b = h2(xi + 1, yi), c = h2(xi, yi + 1), d = h2(xi + 1, yi + 1);
    return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v;
  }
  function fbm(x, y, seed) {
    let sum = 0, amp = 0.5, freq = 1;
    for (let o = 0; o < 5; o++) {
      sum += amp * vNoise(x * freq, y * freq, seed + o * 97);
      freq *= 2.04; amp *= 0.5;
    }
    return sum;
  }
  function isMarineLoc(l) {
    if (l.elevation_m != null && l.elevation_m < 0) return true;
    const txt = ((l.type || '') + ' ' + (l.terrain || '') + ' ' + (l.name || '')).toLowerCase();
    return /\b(trench|abyss|ocean|sea|raft|floating|strait|channel|lagoon|reef|pelagic|water)\b/.test(txt);
  }
  function zoneTintRgb(z) {
    const k = String(z || '').toLowerCase();
    if (k === 'arid' || k === 'semi-arid') return [204, 174, 118];
    if (k === 'tropical') return [68, 134, 82];
    if (k === 'polar' || k === 'subarctic' || k === 'alpine') return [176, 190, 200];
    if (k === 'mediterranean') return [152, 166, 98];
    if (k === 'continental') return [104, 140, 92];
    return [112, 148, 102]; // temperate / default
  }
  function buildProceduralTerrain(style) {
    if (terrainCache[style]) return terrainCache[style];
    if (typeof document === 'undefined' || !document.createElement) return null;
    const size = 420;
    const cvs = document.createElement('canvas');
    cvs.width = size; cvs.height = size;
    const ctx = cvs.getContext && cvs.getContext('2d');
    if (!ctx) return null;
    const seed = hashSeed((G.D.project && G.D.project.name) || 'world');
    const seeds = G.locs.map(function (l) {
      const marine = isMarineLoc(l);
      let w = marine ? -0.46 : 0.44;
      if (l.elevation_m != null && !isNaN(l.elevation_m)) {
        w = l.elevation_m < 0 ? -Math.min(0.65, 0.28 + Math.abs(l.elevation_m) / 6000) : Math.min(0.75, 0.3 + l.elevation_m / 3500);
      }
      const rad = l.type === 'region' || l.type === 'continent' ? 210 : (marine ? 155 : 145);
      return { x: l.x, y: l.y, w: w, r2: rad * rad, rgb: zoneTintRgb(l.climate && l.climate.zone) };
    });

    const field = new Float32Array(size * size);
    const biomeR = new Float32Array(size * size);
    const biomeG = new Float32Array(size * size);
    const biomeB = new Float32Array(size * size);

    for (let py = 0; py < size; py++) {
      const wy = (py / (size - 1)) * 1000;
      for (let px = 0; px < size; px++) {
        const wx = (px / (size - 1)) * 1000;
        const n = fbm(wx / 210, wy / 210, seed);
        const detail = fbm(wx / 70 + 11.3, wy / 70 + 7.1, seed ^ 0x9e3779b9);
        let hVal = (n - 0.52) * 0.85 + (detail - 0.5) * 0.26;
        let br = 112, bg = 148, bb = 102, bw = 0.25;
        for (let i = 0; i < seeds.length; i++) {
          const s = seeds[i];
          const dx = wx - s.x, dy = wy - s.y;
          const d2 = dx * dx + dy * dy;
          if (d2 > s.r2 * 4.5) continue;
          const gVal = Math.exp(-d2 / (2 * s.r2));
          hVal += s.w * gVal;
          if (s.w > 0) { br += s.rgb[0] * gVal; bg += s.rgb[1] * gVal; bb += s.rgb[2] * gVal; bw += gVal; }
        }
        const idx = py * size + px;
        field[idx] = hVal;
        biomeR[idx] = br / bw; biomeG[idx] = bg / bw; biomeB[idx] = bb / bw;
      }
    }

    const img = ctx.createImageData(size, size);
    const d = img.data;
    const isParch = style === 'parchment';

    for (let py = 0; py < size; py++) {
      for (let px = 0; px < size; px++) {
        const idx = py * size + px;
        const hVal = field[idx];
        const hL = field[py * size + Math.max(0, px - 1)];
        const hR = field[py * size + Math.min(size - 1, px + 1)];
        const hU = field[Math.max(0, py - 1) * size + px];
        const hD = field[Math.min(size - 1, py + 1) * size + px];
        const shade = Math.max(-0.35, Math.min(0.35, ((hL - hR) + (hU - hD)) * 2.2));
        let r, g, b;

        if (isParch) {
          const grain = (vNoise(px * 0.45, py * 0.45, seed + 511) - 0.5) * 14;
          if (hVal < 0) {
            const dCoast = Math.abs(hVal);
            const ripple = (dCoast > 0.015 && dCoast < 0.032) || (dCoast > 0.05 && dCoast < 0.064);
            r = ripple ? 168 : 210 - Math.min(28, dCoast * 55);
            g = ripple ? 156 : 202 - Math.min(26, dCoast * 52);
            b = ripple ? 132 : 180 - Math.min(22, dCoast * 44);
          } else {
            const coast = hVal < 0.018;
            const contour = hVal > 0.14 && Math.abs((hVal * 10) % 1 - 0.5) < 0.055;
            if (coast) { r = 92; g = 70; b = 46; }
            else if (contour) { r = 162; g = 138; b = 104; }
            else {
              r = 236 - hVal * 34 + shade * 45;
              g = 220 - hVal * 40 + shade * 40;
              b = 184 - hVal * 46 + shade * 32;
            }
          }
          r += grain; g += grain * 0.9; b += grain * 0.7;
        } else {
          // Topographic / satellite hypsometric tint + directional hill-shading
          if (hVal < 0) {
            const depth = Math.min(1, Math.abs(hVal) * 1.45);
            const bathy = Math.abs((depth * 7) % 1 - 0.5) < 0.035;
            r = 16 + (1 - depth) * 34 + (bathy ? 12 : 0);
            g = 38 + (1 - depth) * 76 + (bathy ? 14 : 0);
            b = 68 + (1 - depth) * 92 + (bathy ? 16 : 0);
          } else if (hVal < 0.035) {
            // Coastal beach / shoal rim
            r = 198 + shade * 35; g = 186 + shade * 32; b = 148 + shade * 24;
          } else if (hVal < 0.38) {
            const t = (hVal - 0.035) / 0.345;
            r = biomeR[idx] * (1 - t * 0.25) + 122 * t * 0.25 + shade * 90;
            g = biomeG[idx] * (1 - t * 0.28) + 114 * t * 0.28 + shade * 86;
            b = biomeB[idx] * (1 - t * 0.22) + 98 * t * 0.22 + shade * 78;
          } else if (hVal < 0.62) {
            const t = (hVal - 0.38) / 0.24;
            r = 128 + t * 48 + shade * 110;
            g = 118 + t * 48 + shade * 105;
            b = 104 + t * 52 + shade * 100;
          } else {
            r = 224 + shade * 65; g = 228 + shade * 65; b = 234 + shade * 65;
          }
          if (hVal > 0.04 && Math.abs((hVal * 12) % 1 - 0.5) < 0.03) {
            r -= 14; g -= 14; b -= 12;
          }
        }
        const o = idx * 4;
        d[o] = Math.max(0, Math.min(255, Math.round(r)));
        d[o + 1] = Math.max(0, Math.min(255, Math.round(g)));
        d[o + 2] = Math.max(0, Math.min(255, Math.round(b)));
        d[o + 3] = 255;
      }
    }
    ctx.putImageData(img, 0, 0);
    const url = cvs.toDataURL('image/png');
    terrainCache[style] = url;
    return url;
  }

  function drawTerrain() {
    clear(layers.terrain);
    if (st.style === 'schematic') return;
    let href = null;
    if (st.style === 'painted') {
      const raw = G.D.map && G.D.map.backdrop;
      href = W.util && W.util.safeImageSrc ? W.util.safeImageSrc(raw) : raw;
    } else {
      href = buildProceduralTerrain(st.style);
    }
    if (!href) return;
    layers.terrain.appendChild(h('svg:image', {
      x: 0, y: 0, width: 1000, height: 1000,
      href: href, preserveAspectRatio: 'xMidYMid slice',
      opacity: st.style === 'painted' ? 0.94 : 0.92,
      'pointer-events': 'none',
    }));
  }

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
  function elevRange() {
    const v = G.locs.map(function (l) { return l.elevation_m; }).filter(function (x) { return x != null && !isNaN(x); });
    return v.length ? [Math.min.apply(null, v), Math.max.apply(null, v)] : [0, 1000];
  }
  function rad(l, er) {
    if (st.sizeBy === 'uniform') return 9;
    if (st.sizeBy === 'elevation') {
      if (l.elevation_m == null || isNaN(l.elevation_m)) return 6.5;
      const span = Math.max(1, er[1] - er[0]);
      return 6 + Math.max(0, Math.min(1, (l.elevation_m - er[0]) / span)) * 13;
    }
    return l.population > 0 ? Math.max(6, Math.min(20, 6 + 2.1 * (Math.log10(l.population) - 2))) : 6.5;
  }
  function colorOf(l, pr) {
    if (st.mode === 'zone') return zoneColor(W, l.climate && l.climate.zone);
    if (st.mode === 'pop') return l.population > 0 ? ramp(pr[1] > pr[0] ? (Math.log10(l.population) - pr[0]) / (pr[1] - pr[0]) : 0.5) : '#94a3b8';
    if (st.mode === 'res') { const r = resRole(l); return r.p && r.c ? '#CC79A7' : r.p ? '#009E73' : r.c ? '#E69F00' : '#94a3b8'; }
    return typeColor(l.type || 'place');
  }
  function glyphOf(l) { if (st.mode !== 'res') return ''; const r = resRole(l); return r.p && r.c ? 'PC' : r.p ? 'P' : r.c ? 'C' : ''; }
  function describe(l) {
    const z = l.climate && l.climate.zone;
    return l.name + ', ' + (l.type || 'place') + (l.population != null ? ', population ' + (l.population_label || fmtN(l.population)) : '') + (z ? ', climate ' + z : '');
  }

  function stopAnim() { if (st.raf) { try { cancelAnimationFrame(st.raf); } catch (e) { /* ignore */ } } st.raf = 0; }
  function startAnim() {
    stopAnim();
    if (!st.active || st.reduced || !st.pulses || !pulses.length || typeof requestAnimationFrame !== 'function') return;
    const tick = function () {
      if (!st.active || !st.pulses) { st.raf = 0; return; }
      for (let i = 0; i < pulses.length; i++) {
        const p = pulses[i];
        p.t = (p.t + p.speed) % 1;
        const q = p.c.at(p.t);
        p.el.setAttribute('cx', q.x.toFixed(1));
        p.el.setAttribute('cy', q.y.toFixed(1));
      }
      st.raf = requestAnimationFrame(tick);
    };
    st.raf = requestAnimationFrame(tick);
  }

  function drawGrid() {
    clear(layers.grid);
    // Cartographic graticule (0..1000 in steps of 100 minor, 200 major)
    for (let v = 0; v <= 1000; v += 100) {
      const major = v % 200 === 0;
      const cls = major ? 'wbm-grid-major' : 'wbm-grid-minor';
      layers.grid.appendChild(h('svg:line', { class: cls, x1: v, y1: 0, x2: v, y2: 1000 }));
      layers.grid.appendChild(h('svg:line', { class: cls, x1: 0, y1: v, x2: 1000, y2: v }));
      if (major) {
        layers.grid.appendChild(h('svg:text', { class: 'wbm-coord', x: v + 4, y: -8, text: v + '°E' }));
        layers.grid.appendChild(h('svg:text', { class: 'wbm-coord', x: -34, y: v + 3, text: v + '°N' }));
      }
    }
    // Outer atlas border frame
    layers.grid.appendChild(h('svg:rect', { x: 0, y: 0, width: 1000, height: 1000, fill: 'none', stroke: 'var(--border)', 'stroke-width': 1.5, 'stroke-opacity': 0.7 }));
    // Subtle compass rose in top-right corner
    const cg = h('svg:g', { transform: 'translate(952, 48)', opacity: 0.55, 'aria-hidden': 'true' },
      h('svg:circle', { r: 22, fill: 'none', stroke: 'var(--muted)', 'stroke-width': 1, 'stroke-dasharray': '2 3' }),
      h('svg:path', { d: 'M0,-24 L5,-5 L24,0 L5,5 L0,24 L-5,5 L-24,0 L-5,-5 Z', fill: 'none', stroke: 'var(--muted)', 'stroke-width': 1 }),
      h('svg:path', { d: 'M0,-24 L4,-4 L0,0 L-4,-4 Z', fill: 'var(--accent)' }),
      h('svg:text', { x: 0, y: -28, 'text-anchor': 'middle', class: 'wbm-coord', style: 'font-weight:700', text: 'N' }));
    layers.grid.appendChild(cg);
  }

  function applySpotlight() {
    clear(layers.badge);
    const hid = st.hoverId;
    if (!hid) {
      Object.keys(markers).forEach(function (id) { markers[id].classList.remove('wbg-dim'); });
      routeEls.forEach(function (re) { re.el.classList.remove('wbm-route-dim', 'wbm-route-lit'); });
      return;
    }
    const nbrs = new Set([hid]);
    (G.adj[hid] || []).forEach(function (e) { nbrs.add(e.to); });
    Object.keys(markers).forEach(function (id) {
      markers[id].classList.toggle('wbg-dim', !nbrs.has(id));
    });
    routeEls.forEach(function (re) {
      const hit = re.r.from === hid || re.r.to === hid;
      re.el.classList.toggle('wbm-route-dim', !hit);
      re.el.classList.toggle('wbm-route-lit', hit);
      if (hit) {
        const mid = re.c.at(0.5);
        const label = re.m.mode + (re.m.time ? ' · ' + re.m.time : '');
        const bw = Math.max(46, label.length * 6.4 + 12);
        layers.badge.appendChild(h('svg:g', { transform: 'translate(' + mid.x.toFixed(1) + ',' + mid.y.toFixed(1) + ')' },
          h('svg:rect', { class: 'wbm-route-badge-bg', x: -bw / 2, y: -9, width: bw, height: 18, rx: 9 }),
          h('svg:text', { class: 'wbm-route-badge-txt', 'text-anchor': 'middle', y: 4, text: label })));
      }
    });
  }

  function showTip(l, ev) {
    if (!l || !ui.tip) return;
    const z = l.climate && l.climate.zone ? l.climate.zone : null;
    const adj = G.adj[l.id] || [];
    const subParts = [l.type || 'location'];
    if (l.population_label || l.population != null) subParts.push('Pop ' + (l.population_label || fmtN(l.population)));
    if (l.elevation_m != null) subParts.push(fmtN(l.elevation_m) + ' m');
    if (z) subParts.push(z);
    const routeSummary = adj.length
      ? adj.length + ' connected route' + (adj.length === 1 ? '' : 's') + ': ' + adj.slice(0, 3).map(function (x) { return G.name(x.to); }).join(', ') + (adj.length > 3 ? '…' : '')
      : 'No direct travel routes';
    clear(ui.tip);
    ui.tip.appendChild(h('div', { class: 'wbm-tip-title', text: l.name }));
    ui.tip.appendChild(h('div', { class: 'wbm-tip-sub', text: subParts.join(' · ') }));
    ui.tip.appendChild(h('div', { class: 'wbm-tip-routes', text: routeSummary }));
    ui.tip.hidden = false;
    const sr = stage.getBoundingClientRect();
    let left = ev.clientX - sr.left + 16;
    let top = ev.clientY - sr.top + 14;
    const tw = ui.tip.offsetWidth || 230, th = ui.tip.offsetHeight || 82;
    if (left + tw > sr.width - 10) left = Math.max(8, ev.clientX - sr.left - tw - 14);
    if (top + th > sr.height - 54) top = Math.max(8, ev.clientY - sr.top - th - 12);
    ui.tip.style.left = left + 'px';
    ui.tip.style.top = top + 'px';
  }

  function render() {
    st.dirty = false;
    stopAnim();
    pulses = [];
    routeEls = [];
    Object.keys(layers).forEach(function (k) { if (k !== 'grid' && k !== 'terrain') clear(layers[k]); });
    drawTerrain();
    markers = {};

    const vis = {};
    G.locs.forEach(function (l) { if (passes(W, l)) vis[l.id] = l; });
    const pr = popRange(), er = elevRange(), sel = W.state && W.state.selected;

    // SVG defs: glow filter + procedural radial gradients per climate zone
    clear(layers.defs);
    layers.defs.appendChild(h('svg:filter', { id: 'wbm-glow', x: '-30%', y: '-30%', width: '160%', height: '160%' },
      h('svg:feGaussianBlur', { stdDeviation: 2.5, result: 'b' }),
      h('svg:feMerge', null, h('svg:feMergeNode', { in: 'b' }), h('svg:feMergeNode', { in: 'SourceGraphic' }))));
    const seenZones = {};
    Object.keys(vis).forEach(function (id) {
      const z = vis[id].climate && vis[id].climate.zone;
      if (!z || seenZones[z]) return;
      seenZones[z] = true;
      const col = zoneColor(W, z);
      layers.defs.appendChild(h('svg:radialGradient', { id: 'wbm-halo-' + slug(z), cx: '50%', cy: '50%', r: '50%' },
        h('svg:stop', { offset: '0%', 'stop-color': col, 'stop-opacity': 0.36 }),
        h('svg:stop', { offset: '55%', 'stop-color': col, 'stop-opacity': 0.14 }),
        h('svg:stop', { offset: '100%', 'stop-color': col, 'stop-opacity': 0 })));
    });

    // Procedural climate biome halos & topographic contour rings
    Object.keys(vis).forEach(function (id) {
      const l = vis[id];
      const r = rad(l, er);
      if (st.halos && l.climate && l.climate.zone) {
        const haloR = Math.max(46, r * 4.8);
        layers.halo.appendChild(h('svg:circle', {
          cx: l.x, cy: l.y, r: haloR,
          fill: 'url(#wbm-halo-' + slug(l.climate.zone) + ')',
          'pointer-events': 'none',
        }));
      }
      if (l.elevation_m != null && l.elevation_m >= 500) {
        const rings = Math.min(4, Math.max(2, Math.floor(l.elevation_m / 600) + 1));
        for (let i = 1; i <= rings; i++) {
          layers.halo.appendChild(h('svg:circle', {
            class: 'wbm-contour', cx: l.x, cy: l.y, r: r + i * 7.5,
            'stroke-dasharray': i % 2 ? '4 3' : null,
          }));
        }
      }
    });

    // Containment hulls + hierarchical parent -> child tether arcs
    G.locs.filter(function (l) { return vis[l.id] && (l.children || []).some(function (c) { return vis[c]; }); })
      .sort(function (a, b) { return (a.depth || 0) - (b.depth || 0); })
      .forEach(function (p) {
        const kids = (p.children || []).map(function (c) { return vis[c]; }).filter(Boolean);
        const pts = [p].concat(kids);
        const cx = pts.reduce(function (s, q) { return s + q.x; }, 0) / pts.length;
        const cy = pts.reduce(function (s, q) { return s + q.y; }, 0) / pts.length;
        const hr = Math.max.apply(null, pts.map(function (q) { return Math.hypot(q.x - cx, q.y - cy) + rad(q, er); })) + 20;
        layers.hull.appendChild(h('svg:circle', {
          cx: cx, cy: cy, r: hr, fill: 'var(--accent)', 'fill-opacity': 0.035,
          stroke: 'var(--border)', 'stroke-opacity': 0.55, 'stroke-dasharray': '3 6',
        }, h('svg:title', { text: p.name + ' contains: ' + kids.map(function (q) { return q.name; }).join(', ') })));
        kids.forEach(function (k) {
          const tc = curve(p, k, 0.12);
          layers.hull.appendChild(h('svg:path', { class: 'wbm-tether', d: tc.d }));
        });
      });

    // Travel ruler shortest path
    const path = st.a && st.b ? shortest(G, st.a, st.b) : null;
    const onPath = {};
    if (path) path.legs.forEach(function (l) { onPath[l.r.id] = 1; });

    // Routes + animated travel/trade pulses
    G.routes.forEach(function (r) {
      const a = vis[r.from], b = vis[r.to];
      if (!a || !b) return;
      const modes = (r.modes && r.modes.length) ? r.modes : [{ mode: 'unspecified' }];
      const w = 1.4 + Math.min((r.goods || []).length, 6) * 0.85;
      modes.forEach(function (m, i) {
        const c = curve(a, b, 0.09 + (i - (modes.length - 1) / 2) * 0.11);
        const col = modeCol[m.mode] || '#888';
        if (onPath[r.id]) {
          layers.path.appendChild(h('svg:path', {
            d: c.d, fill: 'none', stroke: '#FFD400', 'stroke-width': w + 8,
            'stroke-opacity': 0.68, 'stroke-linecap': 'round', filter: 'url(#wbm-glow)',
          }));
        }
        const line = h('svg:path', {
          class: 'wbm-route-line', d: c.d, fill: 'none', stroke: col,
          'stroke-width': w, 'stroke-opacity': 0.78, 'stroke-linecap': 'round',
          'stroke-dasharray': r.reciprocal === false ? '6 5' : null,
        });
        layers.route.appendChild(line);
        routeEls.push({ el: line, r: r, m: m, c: c });
        layers.route.appendChild(h('svg:path', {
          d: c.d, fill: 'none', stroke: 'transparent', 'stroke-width': Math.max(w, 14),
          style: 'cursor:pointer', onclick: function () { if (!pz.wasDrag()) showRoute(r); },
        }, h('svg:title', {
          text: G.name(r.from) + ' ↔ ' + G.name(r.to) + ': ' +
            modes.map(function (x) { return x.mode + (x.time ? ' (' + x.time + ')' : ''); }).join(', ') +
            (r.reciprocal === false ? ' [declared on one side only]' : ''),
        })));
        if (st.pulses && !st.reduced) {
          const count = Math.min(3, Math.max(1, Math.ceil(((r.goods || []).length + 1) / 2)));
          for (let k = 0; k < count; k++) {
            const dot = h('svg:circle', {
              class: 'wbm-pulse', r: 3.1, fill: '#ffffff', stroke: col,
              'stroke-width': 1.8, filter: 'url(#wbm-glow)', 'pointer-events': 'none', 'aria-hidden': 'true',
            });
            layers.pulse.appendChild(dot);
            pulses.push({ el: dot, c: c, t: (k / count + i * 0.17) % 1, speed: 0.0022 + (k % 2) * 0.0005 });
          }
        }
      });
    });

    // Location markers (larger first so smaller ones remain clickable on top)
    Object.keys(vis).map(function (k) { return vis[k]; }).sort(function (a, b) { return rad(b, er) - rad(a, er); }).forEach(function (l) {
      const r = rad(l, er), gl = glyphOf(l);
      const isSel = l.id === sel;
      const g = h('svg:g', {
        class: 'wbg-node' + (isSel ? ' wbg-sel' : ''),
        transform: 'translate(' + l.x + ',' + l.y + ')',
        role: 'button', tabindex: -1, 'aria-label': describe(l), 'aria-pressed': isSel ? 'true' : 'false', 'data-id': l.id,
      },
        h('svg:title', { text: describe(l) }),
        isSel ? h('svg:circle', { r: r + 7, fill: 'none', stroke: 'var(--focus)', 'stroke-width': 2, 'stroke-opacity': 0.7, filter: 'url(#wbm-glow)' }) : null,
        h('svg:path', {
          class: 'wbg-sh', d: shapeD(shapes[l.type || 'place'], r),
          fill: colorOf(l, pr), 'fill-opacity': l.population > 0 ? 1 : 0.82,
          'stroke-dasharray': l.population > 0 ? null : '3 2',
        }),
        gl ? h('svg:text', { class: 'wbg-glyph', 'text-anchor': 'middle', y: 4, text: gl }) : null,
        st.a === l.id || st.b === l.id ? h('svg:text', { class: 'wbg-lbl', 'text-anchor': 'middle', y: -r - 7, style: 'font-weight:800;fill:var(--focus)', text: st.a === l.id ? 'START A' : 'END B' }) : null,
        st.labels ? h('svg:text', { class: 'wbg-lbl', 'text-anchor': 'middle', y: r + 14, text: l.name }) : null);

      g.addEventListener('click', function (ev) { if (pz.wasDrag()) return; activateNode(l.id, ev.shiftKey); });
      g.addEventListener('keydown', function (ev) {
        if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); activateNode(l.id, ev.shiftKey); }
        else if (ev.key.indexOf('Arrow') === 0) { ev.preventDefault(); nav(l, ev.key, vis); }
      });
      g.addEventListener('mouseenter', function (ev) { st.hoverId = l.id; applySpotlight(); showTip(l, ev); });
      g.addEventListener('mousemove', function (ev) { if (st.hoverId === l.id) showTip(l, ev); });
      g.addEventListener('mouseleave', function () { st.hoverId = null; applySpotlight(); if (ui.tip) ui.tip.hidden = true; });
      g.addEventListener('focus', function () { st.focusId = l.id; st.hoverId = l.id; applySpotlight(); });
      g.addEventListener('blur', function () { if (st.hoverId === l.id) { st.hoverId = null; applySpotlight(); } });
      layers.node.appendChild(g);
      markers[l.id] = g;
    });

    const ids = Object.keys(markers);
    const tab = markers[sel] ? sel : st.focusId && markers[st.focusId] ? st.focusId : ids[0];
    if (tab) markers[tab].setAttribute('tabindex', 0);
    if (st.refocus && markers[st.refocus]) markers[st.refocus].focus();
    st.refocus = null;

    applySpotlight();
    renderLegend(); renderRuler(path); renderCard(); renderSr(vis);
    ui.empty.style.display = G.locs.length ? 'none' : '';
    ui.count.textContent = G.locs.length && !ids.length
      ? 'No locations match the current filters.'
      : ids.length + ' of ' + G.locs.length + ' locations · ' + G.routes.length + ' routes';
    startAnim();
  }

  function nav(from, key, vis) {
    const ux = key === 'ArrowRight' ? 1 : key === 'ArrowLeft' ? -1 : 0;
    const uy = key === 'ArrowDown' ? 1 : key === 'ArrowUp' ? -1 : 0;
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
      const sw = h('svg:svg', { width: 16, height: 16, viewBox: '-12 -12 24 24', 'aria-hidden': 'true' },
        h('svg:path', { d: shapeD(shapes[t], 7), fill: st.mode === 'type' ? typeColor(t) : '#999', stroke: 'currentColor' }));
      return h('span', null, sw, t);
    });
    ui.legend.appendChild(h('div', null, h('h3', { text: 'Shape = location type' }), h('div', { class: 'wbg-legend' }, types)));
    const swatch = function (c, t) { return h('span', null, h('span', { style: 'display:inline-block;width:12px;height:12px;border-radius:3px;border:1px solid currentColor;background:' + c }), t); };
    let key = null;
    if (st.mode === 'zone') {
      const zs = (G.D.climate && G.D.climate.zones) || [];
      key = zs.length ? zs.map(function (z) { return swatch(zoneColor(W, z.zone), z.zone + ' (' + z.count + ')'); }) : [h('span', { text: 'No climate data yet' })];
      key.push(swatch('#94a3b8', 'no climate data'));
    } else if (st.mode === 'pop') {
      const pr = popRange();
      key = [h('span', { text: fmtN(Math.pow(10, pr[0])) }), h('span', { style: 'display:inline-block;width:88px;height:10px;border-radius:3px;border:1px solid currentColor;background:linear-gradient(90deg,' + RAMP.join(',') + ')' }), h('span', { text: fmtN(Math.pow(10, pr[1])) }), swatch('#94a3b8', 'unknown')];
    } else if (st.mode === 'res') {
      key = [swatch('#009E73', 'P produces'), swatch('#E69F00', 'C consumes'), swatch('#CC79A7', 'PC both'), swatch('#94a3b8', 'neither')];
    } else {
      key = [h('span', { class: 'wbg-dim-t', text: 'Colour matches location type · Biome halos show climate zones' })];
    }
    ui.legend.appendChild(h('div', null, h('h3', { text: 'Colour key' }), h('div', { class: 'wbg-legend' }, key)));
    const ms = Object.keys(modeCol).map(function (m) {
      return h('span', null, h('svg:svg', { width: 22, height: 8, 'aria-hidden': 'true' },
        h('svg:line', { x1: 0, y1: 4, x2: 22, y2: 4, stroke: modeCol[m], 'stroke-width': 3, 'stroke-linecap': 'round' })), m);
    });
    ui.legend.appendChild(h('div', null, h('h3', { text: 'Routes & contours' }), h('div', { class: 'wbg-legend' },
      ms.length ? ms : [h('span', { text: 'no routes' })],
      h('span', { class: 'wbg-dim-t', text: 'Dashed = one-sided · Rings = elevation >= 500 m' }))));
  }

  function chips(items, titleFn) {
    return items.map(function (x) {
      return h('button', {
        type: 'button', class: 'wbg-chip', title: titleFn ? titleFn(x) : 'Show in life view',
        'aria-label': 'Focus ' + x.name + ' in life view',
        onclick: function () { WB.bus.emit('focus-life', x.name); }, text: x.name,
      });
    });
  }
  function renderCard() {
    clear(ui.card);
    const l = G.L[W.state && W.state.selected];
    if (st.route) {
      const r = st.route;
      ui.card.appendChild(h('div', null,
        h('h3', { text: 'Route: ' + G.name(r.from) + ' ↔ ' + G.name(r.to) }),
        h('ul', { class: 'wbg-list' }, (r.modes || []).map(function (m) { return h('li', { text: m.mode + (m.distance ? ', ' + m.distance : '') + (m.time ? ', ' + m.time : '') }); })),
        h('p', { text: 'Goods: ' + ((r.goods || []).join(', ') || 'none recorded') }),
        r.reciprocal === false ? h('p', { class: 'wbg-flag warn', text: 'Declared on one side only (validator warning)' }) : null,
        h('button', { class: 'wbg-btn', type: 'button', onclick: function () { st.route = null; renderCard(); }, text: 'Close' })));
      return;
    }
    if (!l) {
      ui.card.appendChild(h('p', { class: 'wbg-dim-t', text: G.locs.length ? 'Hover any location to spotlight its routes. Click to inspect, or Shift+click two locations for the travel ruler.' : '' }));
      return;
    }
    const c = l.climate, parent = l.parent && G.L[l.parent];
    const rows = [
      ['Type', l.type || 'place'],
      ['Parent', parent ? h('button', { class: 'wbg-chip', type: 'button', onclick: function () { WB.select(parent.id); }, text: parent.name }) : 'none (top level)'],
      ['Terrain', l.terrain || 'not recorded'],
      ['Elevation', l.elevation_m != null ? fmtN(l.elevation_m) + ' m' : 'not recorded'],
      ['Area', l.area_km2 != null ? fmtN(l.area_km2) + ' km²' : 'not recorded'],
      ['Population', l.population_label || (l.population != null ? fmtN(l.population) : 'not recorded')],
      ['Climate zone', c ? (c.zone || 'unspecified') + (c.inherited ? ' (inherited)' : '') : 'not recorded'],
    ];
    if (c && c.growing_season_days != null) rows.push(['Growing season', c.growing_season_days + ' days']);
    if (c && c.precipitation_mm != null) rows.push(['Precipitation', c.precipitation_mm + ' mm']);
    const dl = h('dl', null, rows.map(function (r) { return [h('dt', { text: r[0] }), h('dd', null, r[1])]; }));
    const group = function (t, a, tf) { return a && a.length ? [h('h3', { text: t }), h('div', null, chips(a, tf))] : []; };
    ui.card.appendChild(h('div', null,
      h('h3', { text: l.name }), dl,
      c ? null : h('p', { class: 'wbg-dim-t', text: 'No climate data yet: use the geography-and-climate skill' }),
      group('Resources', l.resources, function (x) { return (x.category || 'resource') + (x.rarity ? ', ' + x.rarity : ''); }),
      group('Flora', l.flora, function (x) { return x.role || 'flora'; }),
      group('Fauna', l.fauna, function (x) { return x.role || 'fauna'; }),
      h('div', { style: 'margin-top:8px;display:flex;gap:6px;flex-wrap:wrap' },
        h('button', { class: 'wbg-btn', type: 'button', onclick: function () { st.a = l.id; st.b = null; st.refocus = l.id; render(); }, text: 'Ruler start here' }),
        h('button', { class: 'wbg-btn', type: 'button', onclick: function () { if (st.a && st.a !== l.id) { st.b = l.id; st.refocus = l.id; render(); } }, text: 'Ruler end here' }))));
  }
  function showRoute(r) { st.route = r; renderCard(); }
  function renderRuler(path) {
    clear(ui.ruler);
    if (!st.a) { ui.ruler.appendChild(h('span', { class: 'wbg-dim-t', text: 'Ruler: Shift+click two locations' })); return; }
    const clr = h('button', { class: 'wbg-btn', type: 'button', onclick: function () { st.a = st.b = null; render(); }, text: 'Clear ruler' });
    if (!st.b) { ui.ruler.appendChild(h('span', null, 'Ruler from ' + G.name(st.a) + ' → pick end ', clr)); return; }
    if (!path) { ui.ruler.appendChild(h('span', null, 'No route chain between ' + G.name(st.a) + ' and ' + G.name(st.b) + ' ', clr)); return; }
    const chain = [G.name(st.a)]; path.legs.forEach(function (l) { chain.push(G.name(l.r.from === l.from ? l.r.to : l.r.from)); });
    ui.ruler.appendChild(h('span', { role: 'status' }, h('strong', { text: chain.join(' → ') }), ': ' + fmtHours(path.total) + (path.est ? ' (est.)' : '') + ' ', clr));
  }
  function renderSr(vis) {
    clear(ui.sr);
    ui.sr.appendChild(h('table', null, h('caption', { text: 'Locations (text alternative to the map)' }),
      h('thead', null, h('tr', null, ['Name', 'Type', 'Parent', 'Population', 'Climate zone', 'Terrain'].map(function (t) { return h('th', { text: t }); }))),
      h('tbody', null, Object.keys(vis).map(function (id) {
        const l = vis[id];
        return h('tr', null,
          h('td', null, h('button', { type: 'button', tabindex: -1, onclick: function () { WB.select(id); }, text: l.name })),
          h('td', { text: l.type || '' }), h('td', { text: l.parent ? G.name(l.parent) : '' }),
          h('td', { text: l.population_label || '' }), h('td', { text: (l.climate && l.climate.zone) || '' }), h('td', { text: l.terrain || '' }));
      }))));
    ui.sr.appendChild(h('ul', null, G.routes.map(function (r) {
      return h('li', { text: 'Route ' + G.name(r.from) + ' to ' + G.name(r.to) + ': ' + (r.modes || []).map(function (m) { return m.mode + (m.time ? ' ' + m.time : ''); }).join(', ') });
    })));
  }
  function syncMode() { ui.resWrap.style.display = st.mode === 'res' ? '' : 'none'; }

  WB.registerView({
    id: 'map', title: 'Map', order: 30,
    create: function (container, wb) {
      W = wb || WB; G = prep(W); injectCss(); st.reduced = reducedMotion();
      G.types.forEach(function (t, i) { typeCol[t] = PAL[i % PAL.length]; }); shapes = shapeMap(G.types);
      const modes = {}; G.routes.forEach(function (r) { (r.modes || []).forEach(function (m) { modes[m.mode] = 1; }); });
      Object.keys(modes).sort().forEach(function (m, i) { modeCol[m] = PAL[i % PAL.length]; });
      const resources = ((G.D.economy || {}).resources || []).map(function (r) { return r.name; }).sort();
      st.res = resources[0] || '';

      const hasBackdrop = !!(G.D.map && G.D.map.backdrop);
      st.style = hasBackdrop ? 'painted' : 'topographic';

      ui.hudPct = h('span', { class: 'wbm-hud-pct', text: '100%' });
      svg = mkSvg('Interactive cartographic atlas of locations');
      pz = panzoom(svg, function (u, pct) {
        svg.style.setProperty('--wbg-fs', (12 * u) + 'px');
        if (ui.hudPct) ui.hudPct.textContent = pct + '%';
      });
      ['defs', 'terrain', 'grid', 'halo', 'hull', 'path', 'route', 'pulse', 'node', 'badge'].forEach(function (k) {
        layers[k] = k === 'defs' ? h('svg:defs') : h('svg:g', { 'data-layer': k });
        svg.appendChild(layers[k]);
      });
      drawGrid();

      const styleOpts = [];
      if (hasBackdrop) styleOpts.push(['painted', 'Painted Map']);
      styleOpts.push(['topographic', 'Topographic'], ['parchment', 'Parchment'], ['schematic', 'Schematic']);
      const styleSel = h('select', { id: 'wbg-map-style', 'aria-label': 'Map terrain style', onchange: function (e) { st.style = e.target.value; render(); } },
        styleOpts.map(function (o) { return h('option', { value: o[0], text: o[1], selected: o[0] === st.style ? true : null }); }));
      const modeSel = h('select', { id: 'wbg-map-mode', onchange: function (e) { st.mode = e.target.value; syncMode(); render(); } },
        [['type', 'Type'], ['zone', 'Climate zone'], ['res', 'Resource availability'], ['pop', 'Population']].map(function (o) { return h('option', { value: o[0], text: o[1] }); }));
      const sizeSel = h('select', { id: 'wbg-map-size', 'aria-label': 'Bubble sizing', onchange: function (e) { st.sizeBy = e.target.value; render(); } },
        [['population', 'Population'], ['uniform', 'Uniform'], ['elevation', 'Elevation']].map(function (o) { return h('option', { value: o[0], text: o[1] }); }));
      const resSel = h('select', { id: 'wbg-map-res', 'aria-label': 'Resource', onchange: function (e) { st.res = e.target.value; render(); } },
        resources.length ? resources.map(function (r) { return h('option', { value: r, text: r }); }) : [h('option', { value: '', text: 'No economy data yet' })]);

      const mkToggle = function (label, key) {
        const b = h('button', {
          type: 'button', class: 'wbg-btn', 'aria-pressed': st[key] ? 'true' : 'false', text: label,
          onclick: function () { st[key] = !st[key]; b.setAttribute('aria-pressed', st[key] ? 'true' : 'false'); render(); },
        });
        return b;
      };
      const toggles = h('div', { class: 'wbm-toggles' },
        mkToggle('Biome Halos', 'halos'),
        mkToggle('Route Pulses', 'pulses'),
        mkToggle('Labels', 'labels'));

      const hud = h('div', { class: 'wbm-hud', role: 'group', 'aria-label': 'Atlas zoom controls' },
        h('button', { class: 'wbg-btn', type: 'button', 'aria-label': 'Zoom in', onclick: pz.zoomIn, text: '+' }),
        ui.hudPct,
        h('button', { class: 'wbg-btn', type: 'button', 'aria-label': 'Zoom out', onclick: pz.zoomOut, text: '−' }),
        h('button', { class: 'wbg-btn', type: 'button', 'aria-label': 'Fit atlas to view', onclick: pz.reset, text: 'Fit' }));

      ui.resWrap = h('label', null, 'Resource ', resSel);
      ui.count = h('span', { class: 'wbg-dim-t', role: 'status' });
      ui.ruler = h('span');
      ui.legend = h('div');
      ui.card = h('div', { class: 'wbg-card', 'aria-live': 'polite' });
      ui.sr = h('div', { class: 'wbg-sr' });
      ui.tip = h('div', { class: 'wbm-tip', hidden: true, role: 'tooltip' });
      ui.empty = h('div', { class: 'wbg-empty', style: 'display:none', text: 'No locations with map positions yet. ' + ((W.data && W.data.warnings) || []).join('; ') });

      stage = h('div', { class: 'wbg-stage' }, svg, hud, ui.tip, ui.empty);
      root = h('div', { class: 'wbg-view' },
        h('div', { class: 'wbg-bar' },
          h('label', null, 'Terrain ', styleSel),
          h('label', null, 'Colour ', modeSel),
          h('label', null, 'Size ', sizeSel),
          ui.resWrap, toggles, ui.count, ui.ruler),
        h('div', { class: 'wbg-body' }, stage, h('div', { class: 'wbg-side' }, ui.card, ui.legend)),
        ui.sr);
      container.appendChild(root);
      syncMode();
      if (W.bus) {
        W.bus.on('highlight', function (ids) {
          const s = ids ? new Set(ids) : null;
          Object.keys(markers).forEach(function (id) { markers[id].classList.toggle('wbg-hl', !!(s && s.has(id))); });
        });
      }
      render();
    },
    activate: function () { st.active = true; st.reduced = reducedMotion(); if (st.dirty) render(); else { renderCard(); startAnim(); } },
    deactivate: function () { st.active = false; stopAnim(); },
    resize: function () { if (pz) pz.refresh(); },
    onSelect: function () { st.route = null; if (root) render(); else st.dirty = true; },
    onFilter: function () { if (root) render(); else st.dirty = true; },
  });
})();
