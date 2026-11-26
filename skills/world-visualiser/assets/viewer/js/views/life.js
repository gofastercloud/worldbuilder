/* WorldBuilder viewer: LIFE view — Interactive Biome & Ecological Web pairing a Climate Envelope
 * Chart (SVG temperature ranges & precipitation bars per Paul Tol climate zone) with an Interactive
 * Ecological Network SVG linking Climate Zones <-> Locations <-> Flora/Fauna species. */
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
  const trunc = function (s, n) { return s && s.length > n ? s.slice(0, n - 1) + '…' : (s || ''); };
  function prep(WB) {
    const D = WB.data || {}, M = D.map || {};
    const locs = M.locations || [], routes = M.routes || [];
    const L = {}, N = {};
    locs.forEach(function (l) { L[l.id] = l; });
    (D.nodes || []).forEach(function (n) { N[n.id] = n; });
    return {
      D: D, locs: locs, routes: routes, L: L, N: N,
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

  const LIFE_CSS = '.wbl-main{flex:1 1 auto;min-width:0;overflow:auto;padding:12px 14px;display:grid;gap:14px;align-content:start}' +
    '.wbl-main.split{grid-template-columns:repeat(auto-fit,minmax(420px,1fr))}' +
    '.wbl-main.single{grid-template-columns:minmax(0,1fr)}' +
    '.wbl-panel{background:var(--panel);border:1px solid var(--border);border-radius:var(--radius-md,10px);padding:12px 14px;box-shadow:var(--shadow-sm);min-width:0}' +
    '.wbl-panel-head{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:8px}' +
    '.wbl-panel-title{font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin:0}' +
    '.wbl-panel-sub{font-size:11.5px;color:var(--muted)}' +
    '.wbl-svg{display:block;width:100%;height:auto}' +
    '.wbl-axis{stroke:var(--border);stroke-width:1}.wbl-zero{stroke:#38bdf8;stroke-width:1.2;stroke-dasharray:3 3;stroke-opacity:.7}' +
    '.wbl-tick{fill:var(--muted);font-size:10px;font-variant-numeric:tabular-nums}' +
    '.wbl-zrow{cursor:pointer;transition:opacity 160ms ease}.wbl-zrow:focus{outline:none}.wbl-zrow:focus-visible .wbl-zrow-bg{stroke:var(--focus);stroke-width:1.8}' +
    '.wbl-zrow-bg{fill:transparent;transition:fill 140ms ease}.wbl-zrow:hover .wbl-zrow-bg,.wbl-zrow.active .wbl-zrow-bg{fill:var(--accent-soft)}' +
    '.wbl-zrow.dim{opacity:.26}' +
    '.wbl-zname{fill:var(--fg);font-size:11.5px;font-weight:600}.wbl-zval{fill:var(--muted);font-size:10px;font-variant-numeric:tabular-nums}' +
    '.wbl-net-node{cursor:pointer;transition:opacity 160ms ease}.wbl-net-node:focus{outline:none}.wbl-net-node:focus-visible rect,.wbl-net-node:focus-visible circle{stroke:var(--focus);stroke-width:2.6}' +
    '.wbl-net-node.dim{opacity:.18}.wbl-net-lbl{fill:var(--fg);font-size:11px;font-weight:600;pointer-events:none}.wbl-net-role{fill:var(--muted);font-size:9.5px;pointer-events:none}' +
    '.wbl-net-link{fill:none;stroke-width:1.5;stroke-opacity:.32;transition:stroke-opacity 160ms ease,stroke-width 160ms ease}' +
    '.wbl-net-link.dim{stroke-opacity:.05}.wbl-net-link.lit{stroke-opacity:.92;stroke-width:2.4;filter:url(#wbl-glow)}' +
    '.wbl-col-h{fill:var(--muted);font-size:10.5px;font-weight:700;text-transform:uppercase;letter-spacing:.07em}' +
    '.wbl-role-pill{display:inline-block;padding:1px 7px;border-radius:999px;font-size:11px;font-weight:600;border:1px solid var(--border);background:var(--surface);color:var(--fg);margin:2px 4px 2px 0}';

  const BASE_CSS = '.wbg-view{display:flex;flex-direction:column;height:100%;min-height:0;font:13px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;color:var(--fg,CanvasText)}' +
    '.wbg-bar{display:flex;flex-wrap:wrap;gap:8px 12px;align-items:center;padding:8px 14px;border-bottom:1px solid var(--border,rgba(128,128,128,.35));background:var(--glass,var(--panel,transparent));backdrop-filter:blur(12px)}' +
    '.wbg-bar label{display:inline-flex;gap:6px;align-items:center;color:var(--muted,inherit);font-weight:500;font-size:12.5px}' +
    '.wbg-bar select,.wbg-view input[type=search]{background:var(--surface,Canvas);color:var(--fg,CanvasText);border:1px solid var(--border,rgba(128,128,128,.5));border-radius:var(--radius-sm,6px);padding:4px 8px}' +
    '.wbg-body{display:flex;flex:1;min-height:0}.wbg-side{width:348px;flex:none;overflow:auto;padding:12px 14px;border-left:1px solid var(--border,rgba(128,128,128,.35));background:var(--panel,transparent)}' +
    '@media(max-width:820px){.wbg-body{flex-direction:column;overflow:auto}.wbg-side{width:auto;border-left:0;border-top:1px solid var(--border,rgba(128,128,128,.35))}}' +
    '.wbg-sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}' +
    '.wbg-chip,.wbg-btn{font:inherit;color:var(--fg,inherit);background:var(--surface,rgba(128,128,128,.14));border:1px solid var(--border,rgba(128,128,128,.5));border-radius:999px;padding:3px 10px;margin:2px 4px 2px 0;cursor:pointer;transition:background-color 140ms ease,border-color 140ms ease}' +
    '.wbg-btn{border-radius:var(--radius-sm,6px);padding:4px 9px;font-weight:500;font-size:12.5px}.wbg-chip:hover,.wbg-btn:hover{background:var(--surface-hover,rgba(128,128,128,.28));border-color:var(--accent,Highlight)}' +
    '.wbg-btn[aria-pressed="true"]{background:var(--accent-soft,rgba(0,114,178,.18));border-color:var(--accent,Highlight);box-shadow:inset 0 0 0 1px var(--accent,Highlight)}' +
    '.wbg-side h3{margin:14px 0 6px;font-size:11.5px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--muted,inherit)}' +
    '.wbg-dim-t{color:var(--muted,inherit)}.wbg-empty{padding:24px;color:var(--muted,inherit)}' +
    '.wbg-flag{display:inline-block;border-radius:4px;padding:1px 6px;margin:1px 3px 1px 0;font-size:11.5px;font-weight:600;border:1px solid}' +
    '.wbg-flag.bad{border-color:#D55E00;background:rgba(213,94,0,.18)}.wbg-flag.warn{border-color:#E69F00;background:rgba(230,159,0,.18)}.wbg-flag.note{border-color:var(--border,rgba(128,128,128,.7));background:var(--surface,rgba(128,128,128,.12))}' +
    '.wbg-list{list-style:none;margin:0;padding:0}.wbg-list li{margin:4px 0}';

  function injectCss() {
    try {
      const head = document.head || document.body;
      if (!document.getElementById('wbg-css')) { const s0 = h('style', { id: 'wbg-css' }); s0.textContent = BASE_CSS; head.appendChild(s0); }
      if (!document.getElementById('wbg-life-css')) { const s = h('style', { id: 'wbg-life-css' }); s.textContent = LIFE_CSS; head.appendChild(s); }
    } catch (e) { /* ignore */ }
  }

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
  const HABITAT = /^(artificial|custom|unspecified)$/;
  const EXPLAIN = /mountain|alp|peak|range|highland|plateau|coast|sea|ocean|lake|rift|valley|basin|trench|depth/i;
  const STAPLE = /staple|crop|grain|cereal|food|agric/i;

  const st = { layout: 'split', sel: null, hoverKey: null, q: '', dirty: true, active: false };
  let W, G, SP = [], zones = [], zoneStats = [], findings = [], root, ui = {}, pending = null;
  let envRowEls = [], netNodeEls = [], netLinkEls = [];

  function computeFindings() {
    const out = [], seen = {}, add1 = function (o) { if (out.length < 60) out.push(o); };
    const clim = G.locs.filter(function (l) { return l.climate; });
    const pairs = [];
    G.routes.forEach(function (r) { pairs.push([r.from, r.to]); });
    for (let i = 0; i < clim.length; i++) {
      for (let j = i + 1; j < clim.length; j++) {
        if (Math.hypot(clim[i].x - clim[j].x, clim[i].y - clim[j].y) < 90) pairs.push([clim[i].id, clim[j].id]);
      }
    }
    pairs.forEach(function (p) {
      const a = G.L[p[0]], b = G.L[p[1]], key = [p[0], p[1]].sort().join('|');
      if (!a || !b || !a.climate || !b.climate || seen[key]) return; seen[key] = 1;
      const za = a.climate.zone, zb = b.climate.zone;
      if (!za || !zb || za === zb || HABITAT.test(za) || HABITAT.test(zb) || a.parent === b.id || b.parent === a.id) return;
      const ta = temp(a.climate), tb = temp(b.climate), pa = precip(a.climate), pb = precip(b.climate);
      const dT = ta && tb ? Math.abs(ta.mean - tb.mean) : 0;
      const ratio = pa > 0 && pb > 0 ? Math.max(pa, pb) / Math.min(pa, pb) : 1;
      if (dT < 15 && ratio < 5) return;
      const dE = a.elevation_m != null && b.elevation_m != null ? Math.abs(a.elevation_m - b.elevation_m) : null;
      if ((dE != null && dE >= 1000) || EXPLAIN.test((a.terrain || '') + ' ' + (b.terrain || ''))) return;
      add1({
        k: 'warn', ids: [a.id, b.id],
        text: a.name + ' (' + za + ') borders ' + b.name + ' (' + zb + '): ' + (dT >= 15 ? 'mean temperature differs by ' + dT.toFixed(0) + '°C' : 'rainfall differs ' + ratio.toFixed(1) + '×') + ', with no mountain, coast or elevation difference recorded.',
      });
    });
    clim.forEach(function (l) {
      const c = l.climate, t = temp(c), g = c.growing_season_days;
      if (g > 0 && t && t.max < 0) add1({ k: 'bad', ids: [l.id], text: l.name + ': growing_season_days is ' + g + ' but highest recorded temperature is ' + t.max + '°C.' });
      if (g === 0) (l.flora || []).filter(function (f) { return STAPLE.test(f.role || ''); }).forEach(function (f) { add1({ k: 'bad', ids: [l.id], text: l.name + ': staple flora "' + f.name + '" (' + f.role + ') with 0 growing days.' }); });
    });
    findings = out;
  }

  function buildData() {
    SP = ((G.D.life || {}).species_index || []).slice().sort(function (a, b) { return a.name.localeCompare(b.name); });
    zones = (G.D.climate || {}).zones || [];
    zoneStats = zones.map(function (z) {
      const tMins = [], tMaxs = [];
      (z.locations || []).forEach(function (id) {
        const l = G.L[id];
        const t = l && l.climate ? temp(l.climate) : null;
        if (t) { tMins.push(t.min); tMaxs.push(t.max); }
      });
      const meanT = z.mean_temperature_c;
      const minT = tMins.length ? Math.min.apply(null, tMins) : meanT;
      const maxT = tMaxs.length ? Math.max.apply(null, tMaxs) : meanT;
      return {
        zone: z.zone, count: z.count, locations: z.locations || [],
        meanT: meanT, minT: minT, maxT: maxT, precip: z.mean_precipitation_mm, raw: z,
      };
    });
  }

  function selectItem(sel) { st.sel = sel; if (root) renderAll(); else st.dirty = true; }
  function selSpecies(s) {
    selectItem({ kind: 'species', key: 'sp:' + s.kind + ':' + s.name, label: s.name, ids: s.locations || [], info: s });
    if (s.species_id && G.N[s.species_id]) WB.select(s.species_id);
  }
  function selZone(z) {
    selectItem({ kind: 'zone', key: 'zone:' + z.zone, label: 'Climate zone: ' + z.zone, ids: z.locations || [], info: z });
  }
  function selLoc(id) {
    const l = G.L[id];
    selectItem({ kind: 'location', key: 'loc:' + id, label: G.name(id), ids: [id], info: l });
    if (G.N[id]) WB.select(id);
  }
  function selRes(name) {
    const k = slug(name);
    const ids = G.locs.filter(function (l) { return (l.resources || []).some(function (r) { return slug(r.name) === k; }); }).map(function (l) { return l.id; });
    selectItem({ kind: 'resource', key: 'res:' + k, label: 'Resource: ' + name, ids: ids, info: null });
  }
  function focus(name) {
    const k = slug(name);
    const s = SP.filter(function (x) { return slug(x.name) === k; })[0] || SP.filter(function (x) { return x.species_id && slug(x.species_id) === k; })[0];
    if (s) return selSpecies(s);
    const z = zones.filter(function (x) { return slug(x.zone) === k; })[0];
    if (z) return selZone(z);
    selRes(name);
  }

  function applyWebHighlight(activeKey) {
    const key = activeKey || (st.sel ? st.sel.key : null);
    if (!key) {
      envRowEls.forEach(function (r) { r.el.classList.remove('dim', 'active'); });
      netNodeEls.forEach(function (n) { n.el.classList.remove('dim'); });
      netLinkEls.forEach(function (l) { l.el.classList.remove('dim', 'lit'); });
      return;
    }
    // BFS over ecological graph (zone <-> location <-> species)
    const litNodes = new Set([key]);
    const litLinks = new Set();
    let changed = true;
    while (changed) {
      changed = false;
      netLinkEls.forEach(function (lk, idx) {
        if (litLinks.has(idx)) return;
        if ((lk.from === key || lk.to === key) || (lk.stage === 1 && litNodes.has(lk.from) && key.indexOf('zone:') === 0) || (lk.stage === 0 && litNodes.has(lk.to) && key.indexOf('sp:') === 0)) {
          litLinks.add(idx);
          if (!litNodes.has(lk.from)) { litNodes.add(lk.from); changed = true; }
          if (!litNodes.has(lk.to)) { litNodes.add(lk.to); changed = true; }
        }
      });
    }
    envRowEls.forEach(function (r) {
      const hit = litNodes.has(r.key);
      r.el.classList.toggle('active', r.key === key);
      r.el.classList.toggle('dim', !hit);
    });
    netNodeEls.forEach(function (n) { n.el.classList.toggle('dim', !litNodes.has(n.key)); });
    netLinkEls.forEach(function (l, idx) {
      l.el.classList.toggle('lit', litLinks.has(idx));
      l.el.classList.toggle('dim', !litLinks.has(idx));
    });
  }

  // ---- 1. Climate Envelope Chart (SVG)
  function renderEnvelope() {
    envRowEls = [];
    const panel = h('section', { class: 'wbl-panel', role: 'region', 'aria-label': 'Climate envelope chart' },
      h('div', { class: 'wbl-panel-head' },
        h('h3', { class: 'wbl-panel-title', text: 'Climate Envelope Chart' }),
        h('span', { class: 'wbl-panel-sub', text: 'Temperature range (°C) & precipitation (mm)' })));

    if (!zoneStats.length) {
      panel.appendChild(h('p', { class: 'wbg-empty', text: 'No climate data yet: use the geography-and-climate skill.' }));
      return panel;
    }

    const temps = [];
    zoneStats.forEach(function (z) {
      if (z.minT != null) temps.push(z.minT);
      if (z.maxT != null) temps.push(z.maxT);
      if (z.meanT != null) temps.push(z.meanT);
    });
    const tLo = temps.length ? Math.min(-10, Math.floor(Math.min.apply(null, temps) / 10) * 10) : -20;
    const tHi = temps.length ? Math.max(40, Math.ceil(Math.max.apply(null, temps) / 10) * 10) : 45;
    const tSpan = Math.max(1, tHi - tLo);
    const maxP = Math.max.apply(null, zoneStats.map(function (z) { return z.precip || 0; }).concat([500]));

    const W_SVG = 540, ROW_H = 38, TOP = 32, BOT = 22;
    const H_SVG = TOP + zoneStats.length * ROW_H + BOT;
    const tempX0 = 152, tempX1 = 368, precX0 = 396, precX1 = 516;
    const mapT = function (v) { return tempX0 + ((v - tLo) / tSpan) * (tempX1 - tempX0); };

    const s = h('svg:svg', { class: 'wbl-svg', viewBox: '0 0 ' + W_SVG + ' ' + H_SVG, role: 'group', 'aria-label': 'Temperature ranges and precipitation by climate zone' });
    s.appendChild(h('svg:text', { class: 'wbl-col-h', x: 8, y: 18, text: 'Biome / Zone' }));
    s.appendChild(h('svg:text', { class: 'wbl-col-h', x: (tempX0 + tempX1) / 2, y: 18, 'text-anchor': 'middle', text: 'Temp Envelope (°C)' }));
    s.appendChild(h('svg:text', { class: 'wbl-col-h', x: (precX0 + precX1) / 2, y: 18, 'text-anchor': 'middle', text: 'Rain (mm)' }));

    // Axis ticks & 0°C freezing reference line
    const zeroX = mapT(0);
    if (zeroX >= tempX0 && zeroX <= tempX1) {
      s.appendChild(h('svg:line', { class: 'wbl-zero', x1: zeroX, x2: zeroX, y1: TOP - 4, y2: H_SVG - BOT }));
      s.appendChild(h('svg:text', { class: 'wbl-tick', x: zeroX, y: H_SVG - 6, 'text-anchor': 'middle', style: 'fill:#38bdf8', text: '0°C' }));
    }
    s.appendChild(h('svg:line', { class: 'wbl-axis', x1: tempX0, x2: tempX1, y1: H_SVG - BOT, y2: H_SVG - BOT }));
    s.appendChild(h('svg:text', { class: 'wbl-tick', x: tempX0, y: H_SVG - 6, text: tLo + '°' }));
    s.appendChild(h('svg:text', { class: 'wbl-tick', x: tempX1, y: H_SVG - 6, 'text-anchor': 'end', text: tHi + '°' }));
    s.appendChild(h('svg:line', { class: 'wbl-axis', x1: precX0, x2: precX1, y1: H_SVG - BOT, y2: H_SVG - BOT }));
    s.appendChild(h('svg:text', { class: 'wbl-tick', x: precX0, y: H_SVG - 6, text: '0' }));
    s.appendChild(h('svg:text', { class: 'wbl-tick', x: precX1, y: H_SVG - 6, 'text-anchor': 'end', text: Math.round(maxP) + ' mm' }));

    zoneStats.forEach(function (z, i) {
      const y = TOP + i * ROW_H;
      const cy = y + ROW_H / 2;
      const col = zoneColor(W, z.zone);
      const key = 'zone:' + z.zone;
      const g = h('svg:g', {
        class: 'wbl-zrow', role: 'button', tabindex: 0,
        'aria-label': z.zone + ', ' + z.count + ' locations, mean temperature ' + (z.meanT == null ? 'n/a' : z.meanT + ' C') + ', precipitation ' + (z.precip == null ? 'n/a' : Math.round(z.precip) + ' mm'),
      },
        h('svg:rect', { class: 'wbl-zrow-bg', x: 2, y: y + 2, width: W_SVG - 4, height: ROW_H - 4, rx: 6 }),
        h('svg:rect', { x: 8, y: cy - 6, width: 12, height: 12, rx: 3, fill: col, stroke: 'var(--panel)', 'stroke-width': 1 }),
        h('svg:text', { class: 'wbl-zname', x: 26, y: cy + 4, text: trunc(z.zone, 16) + ' (' + z.count + ')' }));

      // Temperature range bar + mean diamond
      if (z.minT != null && z.maxT != null) {
        const xMin = mapT(z.minT), xMax = mapT(z.maxT), xMean = mapT(z.meanT != null ? z.meanT : (z.minT + z.maxT) / 2);
        const bw = Math.max(4, xMax - xMin);
        g.appendChild(h('svg:rect', { x: xMin, y: cy - 4, width: bw, height: 8, rx: 4, fill: col, 'fill-opacity': 0.45, stroke: col, 'stroke-width': 1 }));
        g.appendChild(h('svg:path', { d: 'M' + xMean.toFixed(1) + ',' + (cy - 6) + ' L' + (xMean + 5).toFixed(1) + ',' + cy + ' L' + xMean.toFixed(1) + ',' + (cy + 6) + ' L' + (xMean - 5).toFixed(1) + ',' + cy + ' Z', fill: col, stroke: 'var(--panel)', 'stroke-width': 1.2 }));
        g.appendChild(h('svg:text', { class: 'wbl-zval', x: Math.min(tempX1 - 2, xMax + 5), y: cy + 3.5, text: (z.meanT != null ? Math.round(z.meanT) + '°' : '') }));
      } else {
        g.appendChild(h('svg:text', { class: 'wbl-zval', x: tempX0 + 4, y: cy + 3.5, text: 'n/a' }));
      }

      // Precipitation bar
      if (z.precip != null) {
        const pw = Math.max(3, (z.precip / maxP) * (precX1 - precX0 - 28));
        g.appendChild(h('svg:rect', { x: precX0, y: cy - 5, width: pw, height: 10, rx: 3, fill: '#38bdf8', 'fill-opacity': 0.62 }));
        g.appendChild(h('svg:text', { class: 'wbl-zval', x: precX0 + pw + 5, y: cy + 3.5, text: String(Math.round(z.precip)) }));
      } else {
        g.appendChild(h('svg:text', { class: 'wbl-zval', x: precX0 + 4, y: cy + 3.5, text: 'n/a' }));
      }

      g.addEventListener('click', function () { selZone(z.raw); });
      g.addEventListener('keydown', function (ev) { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); selZone(z.raw); } });
      g.addEventListener('mouseenter', function () { st.hoverKey = key; applyWebHighlight(key); });
      g.addEventListener('mouseleave', function () { st.hoverKey = null; applyWebHighlight(null); });
      g.addEventListener('focus', function () { st.hoverKey = key; applyWebHighlight(key); });
      g.addEventListener('blur', function () { st.hoverKey = null; applyWebHighlight(null); });
      s.appendChild(g);
      envRowEls.push({ el: g, key: key });
    });

    panel.appendChild(s);
    return panel;
  }

  // ---- 2. Interactive Ecological Network SVG (Zones <-> Locations <-> Flora/Fauna)
  function renderNetwork() {
    netNodeEls = [];
    netLinkEls = [];
    const panel = h('section', { class: 'wbl-panel', role: 'region', 'aria-label': 'Interactive ecological network' },
      h('div', { class: 'wbl-panel-head' },
        h('h3', { class: 'wbl-panel-title', text: 'Interactive Ecological Network' }),
        h('span', { class: 'wbl-panel-sub', text: 'Biomes ↔ Habitats ↔ Flora & Fauna' })));

    const q = st.q.trim().toLowerCase();
    const visSp = SP.filter(function (s) {
      return !q || s.name.toLowerCase().indexOf(q) >= 0 || (s.roles || []).join(' ').toLowerCase().indexOf(q) >= 0;
    });
    const visLocs = G.locs.filter(function (l) {
      if (!passes(W, l)) return false;
      const hasEco = (l.climate && l.climate.zone) || (l.flora && l.flora.length) || (l.fauna && l.fauna.length);
      return hasEco;
    });

    if (!zones.length && !visLocs.length && !visSp.length) {
      panel.appendChild(h('p', { class: 'wbg-empty', text: 'No climate or species links recorded yet.' }));
      return panel;
    }

    const W_SVG = 620;
    const rows = Math.max(zones.length, visLocs.length, visSp.length, 1);
    const H_SVG = Math.max(320, 44 + rows * 28);
    const TOP = 34, BOT = 16;
    const usableH = H_SVG - TOP - BOT;
    const colX = [16, 250, 442];

    const s = h('svg:svg', { class: 'wbl-svg', viewBox: '0 0 ' + W_SVG + ' ' + H_SVG, role: 'group', 'aria-label': 'Ecological network linking climate zones, locations, and species' });
    s.appendChild(h('svg:defs', null,
      h('svg:filter', { id: 'wbl-glow', x: '-25%', y: '-25%', width: '150%', height: '150%' },
        h('svg:feGaussianBlur', { stdDeviation: 2.2, result: 'b' }),
        h('svg:feMerge', null, h('svg:feMergeNode', { in: 'b' }), h('svg:feMergeNode', { in: 'SourceGraphic' })))));

    s.appendChild(h('svg:text', { class: 'wbl-col-h', x: colX[0], y: 18, text: 'Climate Zones (' + zones.length + ')' }));
    s.appendChild(h('svg:text', { class: 'wbl-col-h', x: colX[1], y: 18, text: 'Habitats (' + visLocs.length + ')' }));
    s.appendChild(h('svg:text', { class: 'wbl-col-h', x: colX[2], y: 18, text: 'Flora & Fauna (' + visSp.length + ')' }));

    const linkLayer = h('svg:g', { 'data-layer': 'links' });
    const nodeLayer = h('svg:g', { 'data-layer': 'nodes' });
    s.appendChild(linkLayer); s.appendChild(nodeLayer);

    const pos = {};
    const stepY = function (n, i) { return n <= 1 ? TOP + usableH / 2 : TOP + (i / (n - 1)) * (usableH - 12); };
    zones.forEach(function (z, i) { pos['zone:' + z.zone] = { x: colX[0] + 126, y: stepY(zones.length, i), col: zoneColor(W, z.zone) }; });
    visLocs.forEach(function (l, i) { pos['loc:' + l.id] = { x: colX[1], y: stepY(visLocs.length, i), col: zoneColor(W, l.climate && l.climate.zone) }; });
    visSp.forEach(function (sp, i) { pos['sp:' + sp.kind + ':' + sp.name] = { x: colX[2], y: stepY(visSp.length, i), col: sp.kind === 'flora' ? '#009E73' : '#E69F00' }; });

    const addLink = function (stageIdx, fromKey, toKey, stroke) {
      const a = pos[fromKey], b = pos[toKey];
      if (!a || !b) return;
      const x0 = stageIdx === 0 ? a.x : a.x + 124;
      const x1 = b.x;
      const mx = (x0 + x1) / 2;
      const d = 'M' + x0.toFixed(1) + ',' + a.y.toFixed(1) + ' C' + mx.toFixed(1) + ',' + a.y.toFixed(1) + ' ' + mx.toFixed(1) + ',' + b.y.toFixed(1) + ' ' + x1.toFixed(1) + ',' + b.y.toFixed(1);
      const p = h('svg:path', { class: 'wbl-net-link', d: d, stroke: stroke });
      linkLayer.appendChild(p);
      netLinkEls.push({ el: p, from: fromKey, to: toKey, stage: stageIdx });
    };

    // Zone -> Location links
    visLocs.forEach(function (l) {
      if (l.climate && l.climate.zone) addLink(0, 'zone:' + l.climate.zone, 'loc:' + l.id, zoneColor(W, l.climate.zone));
    });
    // Location -> Species links
    visSp.forEach(function (sp) {
      const spKey = 'sp:' + sp.kind + ':' + sp.name;
      const stroke = sp.kind === 'flora' ? '#009E73' : '#E69F00';
      (sp.locations || []).forEach(function (lid) { addLink(1, 'loc:' + lid, spKey, stroke); });
    });

    const wire = function (g, key, onClick) {
      g.addEventListener('click', onClick);
      g.addEventListener('keydown', function (ev) { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); onClick(); } });
      g.addEventListener('mouseenter', function () { st.hoverKey = key; applyWebHighlight(key); });
      g.addEventListener('mouseleave', function () { st.hoverKey = null; applyWebHighlight(null); });
      g.addEventListener('focus', function () { st.hoverKey = key; applyWebHighlight(key); });
      g.addEventListener('blur', function () { st.hoverKey = null; applyWebHighlight(null); });
      nodeLayer.appendChild(g);
      netNodeEls.push({ el: g, key: key });
    };

    // Zone pills
    zones.forEach(function (z) {
      const key = 'zone:' + z.zone, p = pos[key], col = zoneColor(W, z.zone);
      const g = h('svg:g', { class: 'wbl-net-node', role: 'button', tabindex: 0, 'aria-label': 'Climate zone ' + z.zone },
        h('svg:rect', { x: colX[0], y: p.y - 10, width: 126, height: 20, rx: 10, fill: col, 'fill-opacity': 0.22, stroke: col, 'stroke-width': 1.3 }),
        h('svg:circle', { cx: colX[0] + 10, cy: p.y, r: 4, fill: col }),
        h('svg:text', { class: 'wbl-net-lbl', x: colX[0] + 19, y: p.y + 4, text: trunc(z.zone, 15) }));
      wire(g, key, function () { selZone(z); });
    });

    // Location habitat nodes
    const selId = W.state && W.state.selected;
    visLocs.forEach(function (l) {
      const key = 'loc:' + l.id, p = pos[key], col = p.col;
      const isSel = l.id === selId;
      const g = h('svg:g', { class: 'wbl-net-node', role: 'button', tabindex: 0, 'aria-label': 'Location ' + l.name },
        h('svg:rect', { x: colX[1], y: p.y - 10, width: 124, height: 20, rx: 5, fill: 'var(--surface)', stroke: isSel ? 'var(--focus)' : col, 'stroke-width': isSel ? 2.4 : 1.4 }),
        h('svg:circle', { cx: colX[1] + 10, cy: p.y, r: 4, fill: col }),
        h('svg:text', { class: 'wbl-net-lbl', x: colX[1] + 19, y: p.y + 4, text: trunc(l.name, 14) }));
      wire(g, key, function () { selLoc(l.id); });
    });

    // Flora & Fauna nodes
    visSp.forEach(function (sp) {
      const key = 'sp:' + sp.kind + ':' + sp.name, p = pos[key];
      const col = sp.kind === 'flora' ? '#009E73' : '#E69F00';
      const roleTxt = (sp.roles || []).slice(0, 2).join(', ');
      const g = h('svg:g', { class: 'wbl-net-node', role: 'button', tabindex: 0, 'aria-label': sp.name + ' (' + sp.kind + (roleTxt ? ', ' + roleTxt : '') + ')' },
        h('svg:rect', { x: colX[2], y: p.y - 10, width: 168, height: 20, rx: 10, fill: col, 'fill-opacity': 0.16, stroke: col, 'stroke-width': 1.2 }),
        h('svg:text', { class: 'wbl-net-lbl', x: colX[2] + 9, y: p.y + 3.5, text: (sp.kind === 'flora' ? '❀ ' : '◆ ') + trunc(sp.name, 16) }),
        roleTxt ? h('svg:text', { class: 'wbl-net-role', x: colX[2] + 162, y: p.y + 3.5, 'text-anchor': 'end', text: trunc(roleTxt, 11) }) : null);
      wire(g, key, function () { selSpecies(sp); });
    });

    panel.appendChild(s);
    return panel;
  }

  function renderSide() {
    clear(ui.side);
    const s = st.sel;
    ui.side.appendChild(h('h3', { text: 'Ecological Inspector' }));
    if (!s) {
      ui.side.appendChild(h('p', { class: 'wbg-dim-t', text: 'Hover any biome, habitat, or species to trace its full ecological web. Click to inspect and select in the detail panel.' }));
    } else {
      ui.side.appendChild(h('div', { style: 'display:flex;align-items:center;justify-content:space-between;gap:8px' },
        h('strong', { text: s.label }),
        h('button', { type: 'button', class: 'wbg-btn', onclick: function () { st.sel = null; renderAll(); }, text: 'Clear' })));
      if (s.kind === 'species' && s.info) {
        ui.side.appendChild(h('div', { style: 'margin:6px 0' },
          h('span', { class: 'wbl-role-pill', style: 'border-color:' + (s.info.kind === 'flora' ? '#009E73' : '#E69F00'), text: s.info.kind }),
          (s.info.roles || []).map(function (r) { return h('span', { class: 'wbl-role-pill', text: r }); })));
        if (s.info.species_id && G.N[s.info.species_id]) {
          ui.side.appendChild(h('button', { type: 'button', class: 'wbg-btn', onclick: function () { WB.select(s.info.species_id); }, text: 'Open species entity' }));
        }
      } else if (s.kind === 'zone' && s.info) {
        ui.side.appendChild(h('p', { class: 'wbg-dim-t', text: 'Mean temp: ' + (s.info.mean_temperature_c == null ? 'n/a' : s.info.mean_temperature_c + '°C') + ' · Rain: ' + (s.info.mean_precipitation_mm == null ? 'n/a' : Math.round(s.info.mean_precipitation_mm) + ' mm') }));
      }
      if (s.ids && s.ids.length) {
        ui.side.appendChild(h('h3', { text: 'Habitats (' + s.ids.length + ')' }));
        ui.side.appendChild(h('div', null, s.ids.map(function (id) {
          return h('button', { type: 'button', class: 'wbg-chip', onclick: function () { WB.select(id); }, text: G.name(id) });
        })));
      }
    }

    // Climate Consistency Heuristics
    ui.side.appendChild(h('h3', { text: 'Climate Consistency (Heuristics)' }));
    if (!G.locs.some(function (l) { return l.climate; })) {
      ui.side.appendChild(h('p', { class: 'wbg-dim-t', text: 'No climate data yet: use the geography-and-climate skill.' }));
    } else if (!findings.length) {
      ui.side.appendChild(h('p', { role: 'status', class: 'wbg-dim-t', text: 'No inconsistencies flagged (neighbour contrast, freezing growing season, staple crop with 0 growing days).' }));
    } else {
      ui.side.appendChild(h('ul', { class: 'wbg-list' }, findings.map(function (f) {
        return h('li', null, h('span', { class: 'wbg-flag ' + f.k, text: 'FLAG' }), ' ',
          h('button', {
            type: 'button', class: 'wbg-btn', style: 'text-align:left',
            onclick: function () { selectItem({ kind: 'finding', key: 'loc:' + f.ids[0], label: 'Flagged: ' + f.ids.map(G.name).join(' & '), ids: f.ids, info: null }); },
            text: f.text,
          }));
      })));
    }
  }

  function renderSr() {
    clear(ui.sr);
    ui.sr.appendChild(h('table', null,
      h('caption', { text: 'Flora and fauna by location (text alternative)' }),
      h('tbody', null, SP.map(function (s) {
        return h('tr', null,
          h('th', { text: s.name + ' (' + s.kind + ')' }),
          h('td', { text: (s.roles || []).join(', ') }),
          h('td', { text: (s.locations || []).map(G.name).join(', ') }));
      }))));
  }

  function renderAll() {
    st.dirty = false;
    clear(ui.main);
    ui.main.className = 'wbl-main ' + (st.layout === 'split' ? 'split' : 'single');
    if (st.layout === 'split' || st.layout === 'envelope') ui.main.appendChild(renderEnvelope());
    if (st.layout === 'split' || st.layout === 'network') ui.main.appendChild(renderNetwork());
    renderSide();
    renderSr();
    applyWebHighlight(st.hoverKey);
    ui.empty.style.display = G.locs.length || SP.length || zones.length ? 'none' : '';
  }

  WB.registerView({
    id: 'life', title: 'Life', order: 50,
    create: function (container, wb) {
      W = wb || WB; G = prep(W); injectCss(); buildData(); computeFindings();

      const layoutBtns = [['split', 'Split View'], ['envelope', 'Climate Envelope'], ['network', 'Ecological Web']].map(function (pair) {
        const b = h('button', {
          type: 'button', class: 'wbg-btn', 'aria-pressed': st.layout === pair[0] ? 'true' : 'false', text: pair[1],
          onclick: function () {
            st.layout = pair[0];
            layoutBtns.forEach(function (x, idx) { x.setAttribute('aria-pressed', ['split', 'envelope', 'network'][idx] === st.layout ? 'true' : 'false'); });
            renderAll();
          },
        });
        return b;
      });

      const searchEl = h('input', {
        type: 'search', placeholder: 'Filter flora/fauna or roles…', 'aria-label': 'Filter species',
        oninput: function (e) { st.q = e.target.value; renderAll(); },
      });

      ui.main = h('div', { class: 'wbl-main split' });
      ui.side = h('div', { class: 'wbg-side', role: 'region', 'aria-label': 'Ecological inspector and consistency' });
      ui.sr = h('div', { class: 'wbg-sr' });
      ui.empty = h('div', { class: 'wbg-empty', style: 'display:none', text: 'No climate or ecology data yet: use the geography-and-climate skill.' });

      root = h('div', { class: 'wbg-view' },
        h('div', { class: 'wbg-bar' },
          h('span', { class: 'wbg-dim-t', style: 'font-weight:600', text: 'Layout:' }),
          layoutBtns,
          h('label', null, 'Species ', searchEl),
          h('span', { class: 'wbg-dim-t', style: 'margin-left:auto', text: zones.length + ' climate zones · ' + SP.length + ' species' })),
        ui.empty,
        h('div', { class: 'wbg-body' }, ui.main, ui.side),
        ui.sr);
      container.appendChild(root);

      if (W.bus) W.bus.on('focus-life', function (name) { if (name != null) focus(String(name)); });
      if (pending) { const n = pending; pending = null; focus(n); } else renderAll();
    },
    activate: function () { st.active = true; if (st.dirty) renderAll(); },
    deactivate: function () { st.active = false; },
    resize: function () {},
    onSelect: function () { if (root) renderAll(); else st.dirty = true; },
    onFilter: function () { if (root) renderAll(); else st.dirty = true; },
  });
})();
