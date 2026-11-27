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
    '.wbm-river{fill:none;stroke-linecap:round;stroke-linejoin:round;pointer-events:none}.wbm-river-bank{fill:none;stroke-linecap:round;stroke-linejoin:round;pointer-events:none}' +
    '.wbm-orn-mountain{fill:none;stroke:#6b533b;stroke-width:1.15;stroke-linecap:round;stroke-linejoin:round;opacity:.76;pointer-events:none}' +
    '.wbm-orn-mountain-shade{fill:#6b533b;fill-opacity:.24;stroke:none;pointer-events:none}' +
    '.wbm-orn-forest{fill:#5d6e4a;fill-opacity:.34;stroke:#5d4e38;stroke-width:.75;stroke-linecap:round;opacity:.64;pointer-events:none}' +
    '.wbm-region-title{font-family:Georgia,"Times New Roman",serif;font-weight:700;letter-spacing:.26em;text-transform:uppercase;pointer-events:none;paint-order:stroke;stroke-linejoin:round}' +
    '.wbm-scale-bar{pointer-events:none}.wbm-scale-txt{font-size:9.5px;font-weight:600;font-variant-numeric:tabular-nums;pointer-events:none}' +
    '.wbm-route-line{transition:opacity 160ms ease,stroke-width 160ms ease}.wbm-sea-lane{stroke-dasharray:7 5}.wbm-route-dim{opacity:.12 !important}.wbm-route-lit{stroke-opacity:1 !important;filter:url(#wbm-glow)}' +
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
    mode: 'type', sizeBy: 'population', style: 'topographic', halos: true, rivers: true, pulses: true, labels: true,
    res: '', a: null, b: null, route: null, hoverId: null, focusId: null,
    active: false, dirty: true, raf: 0, reduced: false,
  };
  let W, G, root, stage, svg, pz, ui = {}, layers = {}, markers = {}, routeEls = [], pulses = [], modeCol = {}, shapes = {}, typeCol = {};
  const terrainCache = {};
  const terrainFieldCache = {};

  function clamp01(v) { return v < 0 ? 0 : v > 1 ? 1 : v; }
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
  function fbm(x, y, seed, octaves) {
    const oct = octaves || 5;
    let sum = 0, amp = 0.5, freq = 1, norm = 0;
    for (let o = 0; o < oct; o++) {
      sum += amp * vNoise(x * freq, y * freq, seed + o * 97);
      norm += amp;
      freq *= 2.04; amp *= 0.5;
    }
    return sum / (norm || 1);
  }
  function ridgedFbm(x, y, seed, octaves) {
    const oct = octaves || 4;
    let sum = 0, amp = 0.5, freq = 1, weight = 1, norm = 0;
    for (let o = 0; o < oct; o++) {
      let n = 1 - Math.abs(vNoise(x * freq, y * freq, seed + o * 131) * 2 - 1);
      n = n * n * weight;
      weight = Math.min(1, Math.max(0.18, n * 1.65));
      sum += n * amp;
      norm += amp;
      freq *= 2.12; amp *= 0.5;
    }
    return sum / (norm || 1);
  }
  function isMarineLoc(l) {
    if (l.elevation_m != null && l.elevation_m < 0) return true;
    const txt = ((l.type || '') + ' ' + (l.terrain || '') + ' ' + (l.name || '')).toLowerCase();
    return /\b(trench|abyss|ocean|sea|raft|floating|strait|channel|lagoon|reef|pelagic|water|shoal|harbour|harbor|bay)\b/.test(txt);
  }
  function isHighlandLoc(l) {
    if (l.elevation_m != null && l.elevation_m >= 600) return true;
    const txt = ((l.type || '') + ' ' + (l.terrain || '') + ' ' + (l.name || '')).toLowerCase();
    return /\b(mountain|peak|ridge|range|crag|highland|alpine|volcan|spine|summit|sierra|pass|cliff|plateau)\b/.test(txt);
  }
  function isSeaRoute(a, b, mode) {
    if (/\b(sea|ship|sail|boat|ferry|galley|vessel|water|ocean|canal|raft|naval|maritime)\b/i.test(String(mode || ''))) return true;
    return isMarineLoc(a) && isMarineLoc(b);
  }
  function zoneTintRgb(z) {
    const k = String(z || '').toLowerCase();
    if (k === 'arid' || k === 'semi-arid') return [206, 176, 118];
    if (k === 'tropical') return [60, 132, 78];
    if (k === 'polar' || k === 'subarctic' || k === 'alpine') return [184, 198, 208];
    if (k === 'mediterranean') return [150, 164, 96];
    if (k === 'continental') return [102, 138, 90];
    return [108, 146, 98]; // temperate / default
  }
  function zoneMoisture(z, precipMm) {
    const k = String(z || '').toLowerCase();
    let m = 0.56;
    if (k === 'arid') m = 0.14;
    else if (k === 'semi-arid') m = 0.28;
    else if (k === 'mediterranean') m = 0.44;
    else if (k === 'continental') m = 0.54;
    else if (k === 'temperate') m = 0.64;
    else if (k === 'tropical') m = 0.86;
    else if (k === 'polar' || k === 'subarctic') m = 0.34;
    else if (k === 'alpine') m = 0.52;
    if (precipMm != null && !isNaN(precipMm)) {
      const pm = clamp01(precipMm / 1800);
      m = m * 0.45 + pm * 0.55;
    }
    return m;
  }
  function whittakerRgb(temp, moist) {
    if (temp < 0.22) return [192, 204, 214]; // polar tundra / frost
    if (moist < 0.26) return [214, 184, 126]; // desert / rain-shadow sand
    if (moist < 0.40) return [176, 166, 108]; // dry steppe / savannah
    if (temp >= 0.66 && moist >= 0.54) return [52, 126, 74]; // tropical rainforest
    if (temp >= 0.60 && moist < 0.54) return [146, 158, 92]; // mediterranean / scrub
    if (moist >= 0.68) return [72, 134, 82]; // lush temperate woodland
    return [102, 146, 92]; // temperate grassland / mixed forest
  }
  function terrainScopeKey() {
    const parts = [(G.D.project && G.D.project.name) || 'world'];
    G.locs.forEach(function (l) {
      const z = (l.climate && l.climate.zone) || '';
      const p = (l.climate && l.climate.precipitation_mm != null) ? l.climate.precipitation_mm : '';
      parts.push(l.id + '@' + l.x + ',' + l.y + ':' + (l.elevation_m == null ? '' : l.elevation_m) + ':' + z + ':' + p);
    });
    return String(hashSeed(parts.join('|'))) + '_' + G.locs.length;
  }
  function sampleField(tf, arr, wx, wy) {
    if (!tf || !arr) return 0;
    const s = tf.size;
    const fx = clamp01(wx / 1000) * (s - 1);
    const fy = clamp01(wy / 1000) * (s - 1);
    const x0 = Math.floor(fx), y0 = Math.floor(fy);
    const x1 = Math.min(s - 1, x0 + 1), y1 = Math.min(s - 1, y0 + 1);
    const tx = fx - x0, ty = fy - y0;
    const a = arr[y0 * s + x0], b = arr[y0 * s + x1], c = arr[y1 * s + x0], d = arr[y1 * s + x1];
    return a + (b - a) * tx + (c - a) * ty + (a - b - c + d) * tx * ty;
  }
  function computeTerrainField() {
    const scopeKey = terrainScopeKey();
    if (terrainFieldCache[scopeKey]) return terrainFieldCache[scopeKey];
    const size = 420;
    const seed = hashSeed((G.D.project && G.D.project.name) || 'world');
    const highlands = G.locs.filter(isHighlandLoc);
    const seeds = G.locs.map(function (l) {
      const marine = isMarineLoc(l);
      const highland = !marine && isHighlandLoc(l);
      let w = marine ? -0.48 : (highland ? 0.62 : 0.42);
      if (l.elevation_m != null && !isNaN(l.elevation_m)) {
        w = l.elevation_m < 0
          ? -Math.min(0.68, 0.28 + Math.abs(l.elevation_m) / 5500)
          : Math.min(0.84, 0.28 + l.elevation_m / 3200);
      }
      const rad = l.type === 'region' || l.type === 'continent' ? 215 : (marine ? 155 : 145);
      // Orient tectonic ridge strike toward nearest sibling highland, else deterministic hash angle
      let theta = ((hashSeed(l.id) % 360) * Math.PI) / 180;
      if (highland && highlands.length > 1) {
        let bestD = Infinity;
        highlands.forEach(function (other) {
          if (other.id === l.id) return;
          const dist = Math.hypot(other.x - l.x, other.y - l.y);
          if (dist > 10 && dist < 540 && dist < bestD) {
            bestD = dist;
            theta = Math.atan2(other.y - l.y, other.x - l.x);
          }
        });
      }
      const rAlong = highland ? rad * 1.85 : rad;
      const rAcross = highland ? rad * 0.56 : rad;
      const z = l.climate && l.climate.zone;
      const precip = l.climate && l.climate.precipitation_mm;
      return {
        x: l.x, y: l.y, w: w, marine: marine, highland: highland,
        r2: rad * rad, rAlong2: rAlong * rAlong, rAcross2: rAcross * rAcross,
        cosT: Math.cos(theta), sinT: Math.sin(theta),
        maxD2: (rAlong * 2.2) * (rAlong * 2.2),
        rgb: zoneTintRgb(z),
        moist: zoneMoisture(z, precip),
      };
    });

    const nPix = size * size;
    const field = new Float32Array(nPix);
    const moisture = new Float32Array(nPix);
    const temp = new Float32Array(nPix);
    const biomeR = new Float32Array(nPix);
    const biomeG = new Float32Array(nPix);
    const biomeB = new Float32Array(nPix);
    const anchorM = new Float32Array(nPix);
    const anchorW = new Float32Array(nPix);

    // Pass 1: domain-warped fBm + ridged multifractal tectonic chains & archipelagos
    for (let py = 0; py < size; py++) {
      const wy = (py / (size - 1)) * 1000;
      for (let px = 0; px < size; px++) {
        const wx = (px / (size - 1)) * 1000;
        const warpX = (fbm(wx / 260 + 3.1, wy / 260 + 1.7, seed ^ 0x517cc1b7, 3) - 0.5) * 160;
        const warpY = (fbm(wx / 260 + 8.4, wy / 260 + 5.2, seed ^ 0x9e3779b9, 3) - 0.5) * 160;
        const ux = wx + warpX, uy = wy + warpY;

        const cont = fbm(ux / 225, uy / 225, seed, 5);
        const ridge = ridgedFbm(ux / 145 + 5.7, uy / 145 + 2.3, seed ^ 0x7f4a7c15, 4);
        const arch = fbm(ux / 58 + 13.1, uy / 58 + 9.4, seed ^ 0x2c1b3c6d, 3);
        let hVal = (cont - 0.53) * 0.86 + (ridge - 0.42) * 0.25 + (arch - 0.5) * 0.17;

        let br = 108, bg = 146, bb = 98, bw = 0.22;
        let am = 0, aw = 0;
        const swx = wx + warpX * 0.42, swy = wy + warpY * 0.42;
        for (let i = 0; i < seeds.length; i++) {
          const s = seeds[i];
          const dx = swx - s.x, dy = swy - s.y;
          const d2 = dx * dx + dy * dy;
          if (d2 > s.maxD2) continue;
          let gVal;
          if (s.highland) {
            const along = dx * s.cosT + dy * s.sinT;
            const across = -dx * s.sinT + dy * s.cosT;
            const env = Math.exp(-((along * along) / (2 * s.rAlong2) + (across * across) / (2 * s.rAcross2)));
            gVal = env * (0.56 + 0.74 * ridge);
          } else {
            gVal = Math.exp(-d2 / (2 * s.r2)) * (0.82 + 0.36 * arch);
          }
          hVal += s.w * gVal;
          if (!s.marine) {
            br += s.rgb[0] * gVal; bg += s.rgb[1] * gVal; bb += s.rgb[2] * gVal; bw += gVal;
            am += s.moist * gVal; aw += gVal;
          }
        }
        const idx = py * size + px;
        field[idx] = hVal;
        biomeR[idx] = br / bw; biomeG[idx] = bg / bw; biomeB[idx] = bb / bw;
        anchorM[idx] = aw > 0 ? am / aw : 0.54;
        anchorW[idx] = Math.min(0.65, aw * 0.65);
      }
    }

    // Pass 2: latitude temperature lapse + prevailing-wind orographic rain-shadow moisture
    for (let py = 0; py < size; py++) {
      const lat = Math.abs((py / (size - 1)) * 2 - 1);
      const latMoist = 0.58 + 0.20 * Math.cos(lat * Math.PI * 2.1) - 0.16 * Math.exp(-Math.pow((lat - 0.34) / 0.16, 2));
      let airMoist = 0.78;
      let prevH = field[py * size];
      for (let px = 0; px < size; px++) {
        const idx = py * size + px;
        const hVal = field[idx];
        let orog = 0;
        if (hVal < 0) {
          airMoist = Math.min(1, airMoist + 0.042);
        } else {
          const dh = hVal - prevH;
          if (dh > 0 && hVal > 0.04) {
            orog = Math.min(0.38, dh * 8.5);
            airMoist = Math.max(0.06, airMoist - dh * 2.5 - (hVal > 0.32 ? 0.018 : 0.003));
          } else {
            airMoist = Math.max(0.08, airMoist - 0.0025);
          }
        }
        prevH = hVal;
        const physM = clamp01(airMoist * 0.62 + latMoist * 0.38 + orog);
        const wA = anchorW[idx];
        moisture[idx] = clamp01(physM * (1 - wA) + anchorM[idx] * wA);
        temp[idx] = clamp01(1 - lat * 0.76 - Math.max(0, hVal) * 0.52);
      }
    }

    const tf = {
      size: size, seed: seed, scopeKey: scopeKey,
      field: field, moisture: moisture, temp: temp,
      biomeR: biomeR, biomeG: biomeG, biomeB: biomeB,
    };
    terrainFieldCache[scopeKey] = tf;
    return tf;
  }

  function buildProceduralTerrain(style) {
    if (typeof document === 'undefined' || !document.createElement) return null;
    const tf = computeTerrainField();
    const cacheKey = tf.scopeKey + '|' + style;
    if (terrainCache[cacheKey]) return terrainCache[cacheKey];
    const size = tf.size;
    const cvs = document.createElement('canvas');
    cvs.width = size; cvs.height = size;
    const ctx = cvs.getContext && cvs.getContext('2d');
    if (!ctx) return null;

    const img = ctx.createImageData(size, size);
    const d = img.data;
    const field = tf.field, moist = tf.moisture, temp = tf.temp;
    const biomeR = tf.biomeR, biomeG = tf.biomeG, biomeB = tf.biomeB;
    const seed = tf.seed;
    const isParch = style === 'parchment';

    for (let py = 0; py < size; py++) {
      for (let px = 0; px < size; px++) {
        const idx = py * size + px;
        const hVal = field[idx];
        const mVal = moist[idx];
        const tVal = temp[idx];
        const hL = field[py * size + Math.max(0, px - 1)];
        const hR = field[py * size + Math.min(size - 1, px + 1)];
        const hU = field[Math.max(0, py - 1) * size + px];
        const hD = field[Math.min(size - 1, py + 1) * size + px];
        // NW directional hill-shading (315 deg azimuth)
        const shade = Math.max(-0.42, Math.min(0.42, ((hL - hR) * 0.72 + (hU - hD) * 0.72) * 3.1));
        let r, g, b;

        if (isParch) {
          const grain = (vNoise(px * 0.48, py * 0.48, seed + 511) - 0.5) * 14;
          if (hVal < 0) {
            const dCoast = Math.abs(hVal);
            // Double (plus faint third) hand-inked coastline ripples
            const ripple1 = dCoast > 0.013 && dCoast < 0.025;
            const ripple2 = dCoast > 0.044 && dCoast < 0.056;
            const ripple3 = dCoast > 0.080 && dCoast < 0.089;
            if (ripple1 || ripple2) {
              r = 152; g = 136; b = 112;
            } else if (ripple3) {
              r = 176; g = 164; b = 140;
            } else {
              r = 212 - Math.min(30, dCoast * 58);
              g = 203 - Math.min(28, dCoast * 54);
              b = 180 - Math.min(24, dCoast * 46);
            }
          } else {
            const coast = hVal < 0.017;
            const contour = hVal > 0.09 && Math.abs((hVal * 9) % 1 - 0.5) < 0.044;
            if (coast) {
              r = 86; g = 64; b = 42;
            } else if (contour) {
              r = 158; g = 132; b = 96;
            } else {
              // Subtle arid/humid parchment warmth + directional sepia relief
              const dryTint = (1 - mVal) * 10;
              r = 236 + dryTint - hVal * 32 + shade * 48;
              g = 221 + dryTint * 0.4 - hVal * 38 + shade * 42;
              b = 184 - dryTint * 0.6 - hVal * 46 + shade * 32;
            }
          }
          r += grain; g += grain * 0.9; b += grain * 0.7;
        } else {
          // Topographic style: bathymetry shelf contours, turquoise coastal shoals,
          // rain-shadow Whittaker biome tints, NW hill-shading, elevation contours
          if (hVal < 0) {
            const depth = Math.min(1, Math.abs(hVal) * 1.45);
            const shoal = clamp01(1 - Math.abs(hVal) / 0.085);
            const bathy = Math.abs((depth * 8) % 1 - 0.5) < 0.028;
            const shelfEdge = Math.abs(depth - 0.22) < 0.012;
            // Deep abyssal navy -> continental shelf slate-teal -> turquoise coastal shoals
            r = 12 + (1 - depth) * 26 + shoal * 24 + (bathy ? 11 : 0) + (shelfEdge ? 16 : 0);
            g = 34 + (1 - depth) * 78 + shoal * 64 + (bathy ? 16 : 0) + (shelfEdge ? 20 : 0);
            b = 64 + (1 - depth) * 86 + shoal * 36 + (bathy ? 18 : 0) + (shelfEdge ? 22 : 0);
          } else if (hVal < 0.028) {
            // Coastal beach / sandy littoral rim
            r = 204 + shade * 34; g = 192 + shade * 30; b = 150 + shade * 22;
          } else if (hVal < 0.36) {
            const t = (hVal - 0.028) / 0.332;
            const wRgb = whittakerRgb(tVal, mVal);
            const br = wRgb[0] * 0.58 + biomeR[idx] * 0.42;
            const bg = wRgb[1] * 0.58 + biomeG[idx] * 0.42;
            const bb = wRgb[2] * 0.58 + biomeB[idx] * 0.42;
            r = br * (1 - t * 0.24) + 124 * t * 0.24 + shade * 96;
            g = bg * (1 - t * 0.26) + 116 * t * 0.26 + shade * 92;
            b = bb * (1 - t * 0.22) + 100 * t * 0.22 + shade * 82 - Math.max(0, -shade) * 14;
          } else if (hVal < 0.58) {
            const t = (hVal - 0.36) / 0.22;
            r = 128 + t * 54 + shade * 116;
            g = 120 + t * 54 + shade * 110;
            b = 108 + t * 58 + shade * 102;
          } else {
            // Snow-capped alpine peaks
            r = 228 + shade * 62; g = 232 + shade * 62; b = 238 + shade * 58;
          }
          if (hVal > 0.04) {
            const cPhase = (hVal * 12) % 1;
            if (Math.abs(cPhase - 0.5) < 0.026) {
              const idxContour = Math.floor(hVal * 12) % 4 === 0 ? 18 : 11;
              r -= idxContour; g -= idxContour; b -= idxContour * 0.85;
            }
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
    terrainCache[cacheKey] = url;
    return url;
  }

  function smoothPath(pts) {
    if (!pts || pts.length < 2) return '';
    let d = 'M' + pts[0][0].toFixed(1) + ',' + pts[0][1].toFixed(1);
    if (pts.length === 2) return d + 'L' + pts[1][0].toFixed(1) + ',' + pts[1][1].toFixed(1);
    for (let i = 1; i < pts.length - 1; i++) {
      const mx = (pts[i][0] + pts[i + 1][0]) * 0.5;
      const my = (pts[i][1] + pts[i + 1][1]) * 0.5;
      d += 'Q' + pts[i][0].toFixed(1) + ',' + pts[i][1].toFixed(1) + ' ' + mx.toFixed(1) + ',' + my.toFixed(1);
    }
    const last = pts[pts.length - 1];
    return d + 'L' + last[0].toFixed(1) + ',' + last[1].toFixed(1);
  }

  function traceMeander(a, b, seed, tf) {
    const dx = b.x - a.x, dy = b.y - a.y;
    const dist = Math.hypot(dx, dy);
    if (dist < 4) return [[a.x, a.y], [b.x, b.y]];
    const nx = -dy / dist, ny = dx / dist;
    const steps = Math.max(7, Math.min(22, Math.round(dist / 22)));
    const amp = Math.min(22, Math.max(6, dist * 0.085));
    const pts = [];
    for (let i = 0; i <= steps; i++) {
      const t = i / steps;
      const env = Math.sin(Math.PI * t);
      const wave = Math.sin(t * Math.PI * 2.5 + (seed % 17)) * 0.55 + (vNoise(t * 3.8 + (seed % 31), (seed % 19) * 0.3, seed) - 0.5) * 1.1;
      let px = a.x + dx * t + nx * wave * amp * env;
      let py = a.y + dy * t + ny * wave * amp * env;
      // Gentle downhill nudge when terrain field is present
      if (tf && i > 0 && i < steps) {
        const hPlus = sampleField(tf, tf.field, px + nx * 10, py + ny * 10);
        const hMinus = sampleField(tf, tf.field, px - nx * 10, py - ny * 10);
        const pull = Math.max(-7, Math.min(7, (hMinus - hPlus) * 26)) * env;
        px += nx * pull;
        py += ny * pull;
      }
      pts.push([px, py]);
    }
    return pts;
  }

  function traceDownhill(startX, startY, tf) {
    if (!tf) return null;
    const s = tf.size, field = tf.field;
    let cx = clamp01(startX / 1000) * (s - 1);
    let cy = clamp01(startY / 1000) * (s - 1);
    if (field[Math.round(cy) * s + Math.round(cx)] < 0.08) return null;
    const pts = [[(cx / (s - 1)) * 1000, (cy / (s - 1)) * 1000]];
    let vx = 0, vy = 0;
    const dirs = [[2, 0], [-2, 0], [0, 2], [0, -2], [2, 2], [-2, 2], [2, -2], [-2, -2]];
    for (let step = 0; step < 80; step++) {
      const ix = Math.round(cx), iy = Math.round(cy);
      const curH = field[iy * s + ix];
      if (curH < -0.01) break;
      let bestH = curH, bx = 0, by = 0;
      for (let k = 0; k < dirs.length; k++) {
        const nx = ix + dirs[k][0], ny = iy + dirs[k][1];
        if (nx < 1 || nx >= s - 1 || ny < 1 || ny >= s - 1) continue;
        const nh = field[ny * s + nx];
        if (nh < bestH) { bestH = nh; bx = dirs[k][0]; by = dirs[k][1]; }
      }
      if (bx === 0 && by === 0) break;
      vx = vx * 0.35 + bx * 0.65;
      vy = vy * 0.35 + by * 0.65;
      const len = Math.hypot(vx, vy) || 1;
      cx += (vx / len) * 2.2;
      cy += (vy / len) * 2.2;
      if (cx < 2 || cx >= s - 2 || cy < 2 || cy >= s - 2) break;
      if (step % 2 === 0) pts.push([(cx / (s - 1)) * 1000, (cy / (s - 1)) * 1000]);
    }
    if (pts.length < 5) return null;
    const last = pts[pts.length - 1];
    if (Math.hypot(last[0] - pts[0][0], last[1] - pts[0][1]) < 40) return null;
    return pts;
  }

  function drawRivers(vis, tf) {
    clear(layers.river);
    if (!st.rivers) return;
    const isParch = st.style === 'parchment';
    const strokeCol = isParch ? '#4c6d7e' : '#3ca4dc';
    const bankCol = isParch ? '#d9caa8' : '#184b6a';
    const opacity = isParch ? 0.8 : 0.86;
    const hasExplicit = {};
    let autoCount = 0;

    // 1. Explicit hydrology.flows_to rivers
    G.locs.forEach(function (l) {
      const raw = l.hydrology && l.hydrology.flows_to;
      if (!raw) return;
      const targets = Array.isArray(raw) ? raw : [raw];
      targets.forEach(function (tid) {
        const dst = G.L[tid];
        if (!dst || (!vis[l.id] && !vis[dst.id])) return;
        hasExplicit[l.id] = 1;
        const pts = traceMeander(l, dst, hashSeed(l.id + '->' + dst.id), tf);
        const d = smoothPath(pts);
        if (st.style !== 'schematic') {
          layers.river.appendChild(h('svg:path', {
            class: 'wbm-river-bank', d: d, stroke: bankCol, 'stroke-width': 4.2, 'stroke-opacity': isParch ? 0.55 : 0.45,
          }));
        }
        layers.river.appendChild(h('svg:path', {
          class: 'wbm-river', d: d, stroke: strokeCol, 'stroke-width': 2.2, 'stroke-opacity': opacity,
        }, h('svg:title', { text: 'River: ' + l.name + ' → ' + dst.name })));
      });
    });

    // 2. Procedural downhill drainage from high-elevation inland locations toward the coast
    if (tf && st.style !== 'schematic') {
      G.locs.forEach(function (l) {
        if (!vis[l.id] || hasExplicit[l.id] || isMarineLoc(l)) return;
        if (l.elevation_m == null || l.elevation_m < 500) return;
        const pts = traceDownhill(l.x, l.y, tf);
        if (!pts) return;
        autoCount++;
        const d = smoothPath(pts);
        layers.river.appendChild(h('svg:path', {
          class: 'wbm-river-bank', d: d, stroke: bankCol, 'stroke-width': 3.0, 'stroke-opacity': 0.38,
        }));
        layers.river.appendChild(h('svg:path', {
          class: 'wbm-river wbm-river-auto', d: d, stroke: strokeCol, 'stroke-width': 1.45, 'stroke-opacity': opacity * 0.85,
        }));
      });

      // Fallback natural drainage from prominent procedural peaks if no inland high locations drained
      if (autoCount === 0) {
        const s = tf.size, step = Math.floor(s / 6);
        const peaks = [];
        for (let py = step; py < s - step; py += step) {
          for (let px = step; px < s - step; px += step) {
            const hVal = tf.field[py * s + px];
            if (hVal > 0.34) peaks.push({ x: (px / (s - 1)) * 1000, y: (py / (s - 1)) * 1000, h: hVal });
          }
        }
        peaks.sort(function (a, b) { return b.h - a.h; });
        peaks.slice(0, 3).forEach(function (pk) {
          const pts = traceDownhill(pk.x, pk.y, tf);
          if (!pts) return;
          const d = smoothPath(pts);
          layers.river.appendChild(h('svg:path', {
            class: 'wbm-river wbm-river-auto', d: d, stroke: strokeCol, 'stroke-width': 1.35, 'stroke-opacity': opacity * 0.72,
          }));
        });
      }
    }
  }

  function estimateScaleKm() {
    const areas = G.locs.map(function (l) { return l.area_km2; }).filter(function (a) { return a != null && a > 0; });
    let raw = 250;
    if (areas.length) {
      const maxA = Math.max.apply(null, areas);
      raw = Math.max(25, Math.sqrt(maxA) * 0.35);
    }
    const nice = [25, 50, 100, 200, 250, 500, 1000, 2000];
    let best = nice[0], bestDiff = Infinity;
    nice.forEach(function (n) { const diff = Math.abs(n - raw); if (diff < bestDiff) { bestDiff = diff; best = n; } });
    return best;
  }

  function drawOrnaments(vis, tf) {
    clear(layers.ornament);
    const isParch = st.style === 'parchment';
    const isTopo = st.style === 'topographic';

    // 1. Parchment hand-drawn mountain chevrons & woodland clusters
    if (isParch && tf) {
      const locPts = Object.keys(vis).map(function (id) { return vis[id]; });
      const nearLoc = function (x, y) {
        for (let i = 0; i < locPts.length; i++) {
          const dx = locPts[i].x - x, dy = locPts[i].y - y;
          if (dx * dx + dy * dy < 576) return true;
        }
        return false;
      };
      const seed = tf.seed;
      const step = 34;
      for (let gy = 36; gy <= 964; gy += step) {
        for (let gx = 36; gx <= 964; gx += step) {
          const jx = gx + (vNoise(gx * 0.13, gy * 0.13, seed + 701) - 0.5) * 18;
          const jy = gy + (vNoise(gx * 0.13, gy * 0.13, seed + 809) - 0.5) * 18;
          if (nearLoc(jx, jy)) continue;
          const hVal = sampleField(tf, tf.field, jx, jy);
          const mVal = sampleField(tf, tf.moisture, jx, jy);
          const tVal = sampleField(tf, tf.temp, jx, jy);
          if (hVal >= 0.30) {
            const sc = 6.5 + Math.min(7.5, (hVal - 0.30) * 18);
            const w = sc * 1.15, ht = sc * 0.9;
            // Shaded eastern slope + crisp hand-drawn mountain chevron
            layers.ornament.appendChild(h('svg:path', {
              class: 'wbm-orn-mountain-shade',
              d: 'M' + jx.toFixed(1) + ',' + (jy - ht).toFixed(1) + 'L' + (jx + w).toFixed(1) + ',' + (jy + ht).toFixed(1) + 'L' + (jx + w * 0.15).toFixed(1) + ',' + (jy + ht).toFixed(1) + 'Z',
            }));
            layers.ornament.appendChild(h('svg:path', {
              class: 'wbm-orn-mountain',
              d: 'M' + (jx - w).toFixed(1) + ',' + (jy + ht).toFixed(1) + 'L' + jx.toFixed(1) + ',' + (jy - ht).toFixed(1) + 'L' + (jx + w).toFixed(1) + ',' + (jy + ht).toFixed(1),
            }));
          } else if (hVal > 0.04 && hVal < 0.28 && mVal > 0.42 && tVal > 0.24) {
            const roll = vNoise(gx * 0.27, gy * 0.27, seed + 919);
            if (roll > 0.42) {
              const r0 = 3.2 + (roll - 0.42) * 3.2;
              const d = 'M' + (jx - r0 * 1.6).toFixed(1) + ',' + (jy + r0 * 0.6).toFixed(1) +
                'a' + r0.toFixed(1) + ',' + r0.toFixed(1) + ' 0 1,1 ' + (r0 * 1.5).toFixed(1) + ',-' + (r0 * 0.6).toFixed(1) +
                'a' + (r0 * 1.1).toFixed(1) + ',' + (r0 * 1.1).toFixed(1) + ' 0 1,1 ' + (r0 * 1.7).toFixed(1) + ',' + (r0 * 0.6).toFixed(1) + 'Z';
              layers.ornament.appendChild(h('svg:path', { class: 'wbm-orn-forest', d: d }));
            }
          }
        }
      }
    }

    // 2. Styled cartographic region titles for top-level regions
    if (isParch || isTopo) {
      const topRegions = Object.keys(vis).map(function (id) { return vis[id]; }).filter(function (l) {
        return (l.depth === 0 || !l.parent) &&
          (l.type === 'region' || l.type === 'continent' || l.type === 'realm' || (l.children && l.children.length > 0));
      });
      topRegions.forEach(function (reg) {
        const kids = (reg.children || []).map(function (c) { return vis[c]; }).filter(Boolean);
        const pts = [reg].concat(kids);
        const cx = pts.reduce(function (acc, p) { return acc + p.x; }, 0) / pts.length;
        const minY = Math.min.apply(null, pts.map(function (p) { return p.y; }));
        const ty = Math.max(26, Math.min(960, minY - 24));
        layers.ornament.appendChild(h('svg:text', {
          class: 'wbm-region-title',
          x: cx.toFixed(1), y: ty.toFixed(1),
          'text-anchor': 'middle',
          'font-size': 13,
          fill: isParch ? '#4a3420' : '#eef5fb',
          'fill-opacity': isParch ? 0.82 : 0.72,
          stroke: isParch ? '#efe3c6' : '#0f1c2b',
          'stroke-width': 3.2,
          'stroke-opacity': isParch ? 0.78 : 0.65,
          text: reg.name,
        }));
      });
    }

    // 3. Cartographic map scale bar in bottom-left corner
    if (st.style !== 'schematic') {
      const km = estimateScaleKm();
      const segW = 30; // 4 segments = 120 map units
      const ink = isParch ? '#4e3824' : '#e2ecf5';
      const fillAlt = isParch ? '#efe3c8' : '#162436';
      const bgFill = isParch ? 'rgba(239,227,200,0.78)' : 'rgba(15,24,38,0.68)';
      const sg = h('svg:g', { class: 'wbm-scale-bar', transform: 'translate(24, 948)', 'aria-hidden': 'true' },
        h('svg:rect', { x: -8, y: -16, width: segW * 4 + 28, height: 34, rx: 4, fill: bgFill, stroke: ink, 'stroke-opacity': 0.35, 'stroke-width': 0.8 }),
        h('svg:rect', { x: 0, y: 0, width: segW, height: 6, fill: ink, stroke: ink, 'stroke-width': 0.8 }),
        h('svg:rect', { x: segW, y: 0, width: segW, height: 6, fill: fillAlt, stroke: ink, 'stroke-width': 0.8 }),
        h('svg:rect', { x: segW * 2, y: 0, width: segW, height: 6, fill: ink, stroke: ink, 'stroke-width': 0.8 }),
        h('svg:rect', { x: segW * 3, y: 0, width: segW, height: 6, fill: fillAlt, stroke: ink, 'stroke-width': 0.8 }),
        h('svg:text', { class: 'wbm-scale-txt', x: 0, y: -4, fill: ink, text: '0' }),
        h('svg:text', { class: 'wbm-scale-txt', x: segW * 2, y: -4, 'text-anchor': 'middle', fill: ink, text: String(km / 2) }),
        h('svg:text', { class: 'wbm-scale-txt', x: segW * 4, y: -4, 'text-anchor': 'middle', fill: ink, text: km + ' km' }));
      layers.ornament.appendChild(sg);
    }
  }

  function drawTerrain() {
    clear(layers.terrain);
    if (st.style === 'schematic') return null;
    let href = null, tf = null;
    if (st.style === 'painted') {
      const raw = G.D.map && G.D.map.backdrop;
      href = W.util && W.util.safeImageSrc ? W.util.safeImageSrc(raw) : raw;
    } else {
      tf = computeTerrainField();
      href = buildProceduralTerrain(st.style);
    }
    if (href) {
      layers.terrain.appendChild(h('svg:image', {
        x: 0, y: 0, width: 1000, height: 1000,
        href: href, preserveAspectRatio: 'xMidYMid slice',
        opacity: st.style === 'painted' ? 0.94 : 0.94,
        'pointer-events': 'none',
      }));
    }
    return tf;
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
    const tf = drawTerrain();
    markers = {};

    const vis = {};
    G.locs.forEach(function (l) { if (passes(W, l)) vis[l.id] = l; });
    drawOrnaments(vis, tf);
    drawRivers(vis, tf);
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
        const sea = isSeaRoute(a, b, m.mode);
        const bend = (sea ? 0.17 : 0.09) + (i - (modes.length - 1) / 2) * 0.11;
        const c = curve(a, b, bend);
        const col = modeCol[m.mode] || '#888';
        if (onPath[r.id]) {
          layers.path.appendChild(h('svg:path', {
            d: c.d, fill: 'none', stroke: '#FFD400', 'stroke-width': w + 8,
            'stroke-opacity': 0.68, 'stroke-linecap': 'round', filter: 'url(#wbm-glow)',
          }));
        }
        const line = h('svg:path', {
          class: 'wbm-route-line' + (sea ? ' wbm-sea-lane' : ''), d: c.d, fill: 'none', stroke: col,
          'stroke-width': w, 'stroke-opacity': 0.78, 'stroke-linecap': 'round',
          'stroke-dasharray': r.reciprocal === false ? '6 5' : (sea ? '7 5' : null),
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
      ['defs', 'terrain', 'ornament', 'river', 'grid', 'halo', 'hull', 'path', 'route', 'pulse', 'node', 'badge'].forEach(function (k) {
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
        mkToggle('Rivers', 'rivers'),
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
