/* WorldBuilder viewer: TRADE view — Interactive Economic Flow Sankey Diagram & Spatial Route Map,
 * animated glowing cargo flow particles, interactive Resource Filter Chips, and elevated Currency
 * & Economic Shock Impact Cards linking to the shared detail panel. */
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
  function poly(pts) { return 'M' + pts.map(function (p) { return p[0].toFixed(1) + ',' + p[1].toFixed(1); }).join('L') + 'Z'; }
  function shapeD(kind, r) {
    if (kind === 'triangle') return poly([[0, -r * 1.25], [r * 1.15, r * 0.85], [-r * 1.15, r * 0.85]]);
    if (kind === 'square') return poly([[-r, -r], [r, -r], [r, r], [-r, r]]);
    return 'M' + (-r) + ',0a' + r + ',' + r + ' 0 1,0 ' + (2 * r) + ',0a' + r + ',' + r + ' 0 1,0 ' + (-2 * r) + ',0Z';
  }
  function rad(l) { return l.population > 0 ? Math.max(6, Math.min(20, 6 + 2.1 * (Math.log10(l.population) - 2))) : 6.5; }
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
  function cubicAt(x0, y0, cx1, cy1, cx2, cy2, x1, y1, t) {
    const u = 1 - t;
    const uu = u * u, uuu = uu * u, tt = t * t, ttt = tt * t;
    return {
      x: uuu * x0 + 3 * uu * t * cx1 + 3 * u * tt * cx2 + ttt * x1,
      y: uuu * y0 + 3 * uu * t * cy1 + 3 * u * tt * cy2 + ttt * y1,
    };
  }
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
      const k = Math.min(2000, Math.max(80, vb.w * f)) / vb.w;
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
    apply();
    return { refresh: apply, zoomIn: function () { zoom(0.8); }, zoomOut: function () { zoom(1.25); }, reset: function () { Object.assign(vb, home); apply(); }, wasDrag: function () { return moved > 4; } };
  }

  const TRADE_CSS = '.wbt-chips-bar{display:flex;align-items:center;gap:6px;padding:7px 14px;border-bottom:1px solid var(--border);background:var(--surface);overflow-x:auto;flex:none}' +
    '.wbt-chips-bar input[type=search]{flex:none;width:155px;padding:3px 8px;font-size:12px;border-radius:999px;border:1px solid var(--border);background:var(--panel);color:var(--fg)}' +
    '.wbt-chip-strip{display:flex;gap:5px;align-items:center;flex-wrap:nowrap}' +
    '.wbt-rchip{flex:none;display:inline-flex;align-items:center;gap:5px;padding:3px 10px;border-radius:999px;border:1px solid var(--border);background:var(--panel);color:var(--fg);font-size:12px;font-weight:500;cursor:pointer;white-space:nowrap;transition:background-color 140ms ease,border-color 140ms ease,box-shadow 140ms ease}' +
    '.wbt-rchip:hover{border-color:var(--accent);background:var(--surface-hover)}' +
    '.wbt-rchip[aria-pressed="true"]{background:var(--accent);color:#0e1117;border-color:var(--accent);font-weight:700;box-shadow:0 0 10px color-mix(in srgb,var(--accent) 35%,transparent)}' +
    '.wbt-rchip .wbt-dot{width:7px;height:7px;border-radius:50%;flex:none}' +
    '.wbt-sankey-wrap{width:100%;height:100%;overflow:auto;padding:12px 16px}' +
    '.wbt-sankey-svg{display:block;width:100%;min-width:620px;height:auto}' +
    '.wbt-col-title{fill:var(--muted);font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase}' +
    '.wbt-sk-node{cursor:pointer;transition:opacity 160ms ease}.wbt-sk-node:focus{outline:none}.wbt-sk-node:focus-visible rect{stroke:var(--focus);stroke-width:2.5}' +
    '.wbt-sk-node.dim{opacity:.2}.wbt-sk-lbl{fill:var(--fg);font-size:11.5px;font-weight:600;pointer-events:none}.wbt-sk-sub{fill:var(--muted);font-size:10px;pointer-events:none}' +
    '.wbt-sk-link{fill:none;transition:opacity 160ms ease,stroke-opacity 160ms ease;cursor:pointer}.wbt-sk-link.dim{stroke-opacity:.06 !important}.wbt-sk-link.lit{stroke-opacity:.82 !important;filter:url(#wbt-glow)}' +
    '.wbt-card-grid{display:flex;flex-direction:column;gap:8px;margin-top:6px}' +
    '.wbt-ecard{position:relative;padding:10px 12px 10px 15px;border-radius:var(--radius-md,10px);background:var(--surface);border:1px solid var(--border);box-shadow:var(--shadow-sm);overflow:hidden}' +
    '.wbt-ecard::before{content:"";position:absolute;left:0;top:0;bottom:0;width:4px;background:var(--accent)}' +
    '.wbt-ecard.currency::before{background:linear-gradient(180deg,#f59e0b,#eab308)}' +
    '.wbt-ecard.shock::before{background:linear-gradient(180deg,#ef4444,#f97316)}' +
    '.wbt-ecard.route::before{background:linear-gradient(180deg,#38bdf8,#0072B2)}' +
    '.wbt-ecard-head{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:5px}' +
    '.wbt-ecard-title{font-weight:700;font-size:13px;color:var(--fg)}' +
    '.wbt-ecard-meta{font-size:11.5px;color:var(--muted);margin-bottom:5px}' +
    '.wbt-ecard-chips{display:flex;flex-wrap:wrap;gap:4px;align-items:center}' +
    '.wbt-shock-btn{display:inline-flex;align-items:center;gap:5px;padding:3px 9px;border-radius:999px;border:1px solid #D55E00;background:rgba(213,94,0,.14);color:var(--fg);font-weight:700;font-size:12px;cursor:pointer}' +
    '.wbt-shock-btn:hover{background:rgba(213,94,0,.28)}' +
    '@media(prefers-reduced-motion:reduce){.wbt-particle{display:none}}';

  const BASE_CSS = '.wbg-view{display:flex;flex-direction:column;height:100%;min-height:0;font:13px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;color:var(--fg,CanvasText)}' +
    '.wbg-bar{display:flex;flex-wrap:wrap;gap:8px 12px;align-items:center;padding:8px 14px;border-bottom:1px solid var(--border,rgba(128,128,128,.35));background:var(--glass,var(--panel,transparent));backdrop-filter:blur(12px)}' +
    '.wbg-bar label{display:inline-flex;gap:6px;align-items:center;color:var(--muted,inherit);font-weight:500;font-size:12.5px}' +
    '.wbg-bar select,.wbg-view input[type=search]{background:var(--surface,Canvas);color:var(--fg,CanvasText);border:1px solid var(--border,rgba(128,128,128,.5));border-radius:var(--radius-sm,6px);padding:4px 8px}' +
    '.wbg-body{display:flex;flex:1;min-height:0}.wbg-stage{flex:1 1 auto;min-width:0;position:relative;min-height:320px;background:var(--bg,Canvas);overflow:hidden}' +
    '.wbg-side{width:348px;flex:none;overflow:auto;padding:12px 14px;border-left:1px solid var(--border,rgba(128,128,128,.35));background:var(--panel,transparent)}' +
    '@media(max-width:820px){.wbg-body{flex-direction:column;overflow:auto}.wbg-side{width:auto;border-left:0;border-top:1px solid var(--border,rgba(128,128,128,.35))}}' +
    'svg.wbg-svg{width:100%;height:100%;display:block;touch-action:none;cursor:grab;min-height:320px}' +
    '.wbg-sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}' +
    '.wbg-lbl{fill:var(--fg,currentColor);font-size:var(--wbg-fs,12px);font-weight:600;paint-order:stroke;stroke:var(--bg,Canvas);stroke-width:3.6px;stroke-linejoin:round;pointer-events:none}' +
    '.wbg-glyph{font-weight:700;font-size:calc(var(--wbg-fs,12px)*.88);fill:#0e1117;pointer-events:none}' +
    '.wbg-node{cursor:pointer}.wbg-node:focus{outline:none}.wbg-node .wbg-sh{stroke:var(--panel,Canvas);stroke-width:1.8}.wbg-node.wbg-sel .wbg-sh{stroke:var(--focus,Highlight);stroke-width:3.8}' +
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
      if (!document.getElementById('wbg-trade-css')) { const s = h('style', { id: 'wbg-trade-css' }); s.textContent = TRADE_CSS; head.appendChild(s); }
    } catch (e) { /* ignore */ }
  }
  function reducedMotion() { try { return !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches); } catch (e) { return false; } }

  const st = { mode: 'sankey', res: '', resSearch: '', hoverKey: null, active: false, dirty: true, raf: 0, reduced: false };
  let W, G, E, root, stage, mapSvg, pz, ui = {}, mapLayers = {}, particles = [], flags = null, comp = {};

  const FOOD_CAT = /food|agri|crop|grain|farm|fish|livestock|harvest/i;
  const FOOD_NAME = /food|grain|crop|fish|meat|produce|harvest|ration|livestock/i;
  function isFood(r) { return FOOD_CAT.test(r.category || '') || FOOD_NAME.test(r.name || ''); }
  function components() {
    const par = {};
    const find = function (x) { while (par[x] !== x) { par[x] = par[par[x]]; x = par[x]; } return x; };
    G.locs.forEach(function (l) { par[l.id] = l.id; });
    const un = function (a, b) { if (a in par && b in par) par[find(a)] = find(b); };
    G.routes.forEach(function (r) { un(r.from, r.to); });
    G.locs.forEach(function (l) { if (l.parent) un(l.id, l.parent); });
    const c = {}; G.locs.forEach(function (l) { c[l.id] = find(l.id); }); return c;
  }
  function computeFlags() {
    comp = components();
    const res = {}, food = (E.resources || []).filter(isFood);
    (E.resources || []).forEach(function (r) {
      const f = [], P = r.producers || [], C = r.consumers || [];
      if (C.length && !P.length) f.push({ k: 'bad', t: 'Consumed, no producer' });
      if (P.length && C.length && !P.some(function (p) { return C.some(function (c) { return comp[p] && comp[p] === comp[c]; }); })) f.push({ k: 'warn', t: 'No route to consumer' });
      if (P.length && !C.length) f.push({ k: 'note', t: 'No consumer recorded' });
      res[r.name] = f;
    });
    const unfed = [];
    if (food.length) {
      const fedComp = {}; food.forEach(function (r) { (r.producers || []).forEach(function (p) { if (comp[p]) fedComp[comp[p]] = 1; }); });
      G.locs.forEach(function (l) { if (l.population > 0 && !fedComp[comp[l.id]]) unfed.push(l.id); });
    }
    const missing = [];
    (E.trade_routes || []).forEach(function (t) {
      (t.map_route_ids || []).forEach(function (id) { if (!G.routes.some(function (r) { return r.id === id; })) missing.push({ t: t, id: id }); });
    });
    flags = { res: res, unfed: unfed, noFood: !food.length, missing: missing };
  }
  function carrying(r) {
    const k = slug(r.name), out = {};
    (r.routes || []).forEach(function (id) {
      if (id.indexOf('trade:') === 0) {
        const t = (E.trade_routes || []).filter(function (x) { return x.id === id.slice(6); })[0];
        if (t) (t.map_route_ids || []).forEach(function (m) { out[m] = 1; });
      } else out[id] = 1;
    });
    G.routes.forEach(function (rt) { if ((rt.goods || []).some(function (g) { return slug(g) === k; })) out[rt.id] = 1; });
    return out;
  }
  function volWeight(v) {
    const s = String(v || '').toLowerCase();
    if (s.indexOf('very high') >= 0) return 4;
    if (s.indexOf('high') >= 0) return 3;
    if (s.indexOf('med') >= 0) return 2;
    return 1.2;
  }
  const cur = function () { return (E.resources || []).filter(function (r) { return r.name === st.res; })[0]; };
  const nm = function (id) { return G.name(id); };

  function stopAnim() { if (st.raf) { try { cancelAnimationFrame(st.raf); } catch (e) { /* ignore */ } } st.raf = 0; }
  function startAnim() {
    stopAnim();
    if (!st.active || st.reduced || !particles.length || typeof requestAnimationFrame !== 'function') return;
    const tick = function () {
      if (!st.active) { st.raf = 0; return; }
      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];
        p.t = (p.t + p.speed) % 1;
        const q = p.at(p.t);
        p.el.setAttribute('cx', q.x.toFixed(1));
        p.el.setAttribute('cy', q.y.toFixed(1));
      }
      st.raf = requestAnimationFrame(tick);
    };
    st.raf = requestAnimationFrame(tick);
  }

  // ---- Build Sankey flow model: Producer Locations -> Trade Routes / Hubs -> Consumer Locations
  function buildSankeyModel(vis) {
    const rSel = cur();
    const resources = rSel ? [rSel] : (E.resources || []);
    const tradeRoutes = E.trade_routes || [];
    const prodMap = new Map(); // id -> {id, name, weight, resources:Set}
    const midMap = new Map();  // key -> {key, id, name, sub, weight, kind, tr, resources:Set}
    const consMap = new Map(); // id -> {id, name, weight, resources:Set}
    const links = []; // {fromCol, fromKey, toKey, weight, label, color, resNames:Set}

    const addNode = function (map, key, obj) {
      if (!map.has(key)) map.set(key, Object.assign({ weight: 0, resources: new Set() }, obj));
      return map.get(key);
    };
    const linkAcc = new Map();
    const addLink = function (stageIdx, fromKey, toKey, weight, resName, color) {
      const k = stageIdx + '|' + fromKey + '|' + toKey;
      if (!linkAcc.has(k)) linkAcc.set(k, { stage: stageIdx, from: fromKey, to: toKey, weight: 0, resNames: new Set(), color: color });
      const l = linkAcc.get(k);
      l.weight += weight;
      if (resName) l.resNames.add(resName);
    };

    // 1. Named trade routes first
    tradeRoutes.forEach(function (tr) {
      const goods = tr.goods || [];
      const matchingGoods = rSel
        ? goods.filter(function (g) { return slug(g.resource || g) === slug(rSel.name); })
        : goods;
      if (rSel && !matchingGoods.length) return;
      const fromId = tr.from || tr.from_label || ('origin:' + tr.id);
      const toId = tr.to || tr.to_label || ('dest:' + tr.id);
      if (G.L[fromId] && !vis[fromId] && G.L[toId] && !vis[toId]) return;

      const totalW = matchingGoods.length
        ? matchingGoods.reduce(function (s, g) { return s + volWeight(g.volume); }, 0)
        : 2;
      const midKey = 'tr:' + tr.id;
      const pNode = addNode(prodMap, fromId, { id: fromId, name: nm(fromId), isLoc: !!G.L[fromId] });
      const mNode = addNode(midMap, midKey, {
        id: tr.id, name: tr.name, sub: (tr.annual_value ? tr.annual_value : (tr.mode || 'trade corridor')),
        kind: 'route', tr: tr,
      });
      const cNode = addNode(consMap, toId, { id: toId, name: nm(toId), isLoc: !!G.L[toId] });
      pNode.weight += totalW; mNode.weight += totalW; cNode.weight += totalW;
      matchingGoods.forEach(function (g) {
        const rn = g.resource || String(g);
        pNode.resources.add(rn); mNode.resources.add(rn); cNode.resources.add(rn);
      });
      const sampleRes = matchingGoods.length ? (matchingGoods[0].resource || '') : tr.name;
      addLink(0, fromId, midKey, totalW, sampleRes, '#009E73');
      addLink(1, midKey, toId, totalW, sampleRes, '#0072B2');
    });

    // 2. Resource-level producer -> resource hub -> consumer links (when isolating a resource, or when no trade routes exist)
    if (rSel || !midMap.size) {
      const subset = rSel ? [rSel] : resources.filter(function (r) { return (r.producers || []).length && (r.consumers || []).length; }).slice(0, 14);
      subset.forEach(function (r) {
        const P = (r.producers || []).filter(function (id) { return !G.L[id] || vis[id]; });
        const C = (r.consumers || []).filter(function (id) { return !G.L[id] || vis[id]; });
        if (!P.length && !C.length) return;
        const midKey = 'res:' + slug(r.name);
        const mNode = addNode(midMap, midKey, { id: r.name, name: r.name, sub: r.category || 'resource', kind: 'resource', tr: null });
        P.forEach(function (pid) {
          const pNode = addNode(prodMap, pid, { id: pid, name: nm(pid), isLoc: !!G.L[pid] });
          pNode.weight += 1.5; mNode.weight += 1.5; pNode.resources.add(r.name); mNode.resources.add(r.name);
          addLink(0, pid, midKey, 1.5, r.name, '#009E73');
        });
        C.forEach(function (cid) {
          const cNode = addNode(consMap, cid, { id: cid, name: nm(cid), isLoc: !!G.L[cid] });
          cNode.weight += 1.5; mNode.weight += 1.5; cNode.resources.add(r.name); mNode.resources.add(r.name);
          addLink(1, midKey, cid, 1.5, r.name, '#E69F00');
        });
      });
    }

    linkAcc.forEach(function (v) { links.push(v); });
    return {
      prods: Array.from(prodMap.entries()).map(function (e) { return Object.assign({ key: e[0] }, e[1]); }).sort(function (a, b) { return b.weight - a.weight || a.name.localeCompare(b.name); }),
      mids: Array.from(midMap.entries()).map(function (e) { return Object.assign({ key: e[0] }, e[1]); }).sort(function (a, b) { return b.weight - a.weight || a.name.localeCompare(b.name); }),
      conss: Array.from(consMap.entries()).map(function (e) { return Object.assign({ key: e[0] }, e[1]); }).sort(function (a, b) { return b.weight - a.weight || a.name.localeCompare(b.name); }),
      links: links,
    };
  }

  function renderSankey(vis) {
    const model = buildSankeyModel(vis);
    const wrap = h('div', { class: 'wbt-sankey-wrap' });
    if (!model.mids.length && !model.prods.length) {
      wrap.appendChild(h('p', { class: 'wbg-empty', text: st.res ? 'No trade routes or producer/consumer flows recorded for "' + st.res + '".' : 'No trade flow data recorded yet in world/economy.yaml.' }));
      clear(stage);
      stage.appendChild(wrap);
      return;
    }

    const W_SVG = 860;
    const NODE_W = 16;
    const PAD_TOP = 42, PAD_BOT = 24, GAP = 14;
    const colX = [170, 422, 674];
    const maxColCount = Math.max(model.prods.length, model.mids.length, model.conss.length, 1);
    const H_SVG = Math.max(380, PAD_TOP + PAD_BOT + maxColCount * 46);
    const usableH = H_SVG - PAD_TOP - PAD_BOT;

    function layoutCol(list, x) {
      const totalW = list.reduce(function (s, n) { return s + Math.max(1, n.weight); }, 0) || 1;
      const totalGap = Math.max(0, list.length - 1) * GAP;
      const avail = Math.max(40, usableH - totalGap);
      let y = PAD_TOP;
      const map = {};
      list.forEach(function (n) {
        const nh = Math.max(22, (Math.max(1, n.weight) / totalW) * avail);
        n.x = x; n.y = y; n.h = nh; n.outOff = 0; n.inOff = 0;
        map[n.key] = n;
        y += nh + GAP;
      });
      return map;
    }
    const pPos = layoutCol(model.prods, colX[0]);
    const mPos = layoutCol(model.mids, colX[1]);
    const cPos = layoutCol(model.conss, colX[2]);

    const s = h('svg:svg', {
      class: 'wbt-sankey-svg', viewBox: '0 0 ' + W_SVG + ' ' + H_SVG,
      role: 'group', 'aria-label': 'Economic flow Sankey diagram connecting producers, trade routes, and consumers',
    });
    const defs = h('svg:defs', null,
      h('svg:filter', { id: 'wbt-glow', x: '-25%', y: '-25%', width: '150%', height: '150%' },
        h('svg:feGaussianBlur', { stdDeviation: 2.6, result: 'b' }),
        h('svg:feMerge', null, h('svg:feMergeNode', { in: 'b' }), h('svg:feMergeNode', { in: 'SourceGraphic' }))),
      h('svg:linearGradient', { id: 'wbt-grad-0', x1: '0', y1: '0', x2: '1', y2: '0' },
        h('svg:stop', { offset: '0%', 'stop-color': '#009E73' }),
        h('svg:stop', { offset: '100%', 'stop-color': '#38bdf8' })),
      h('svg:linearGradient', { id: 'wbt-grad-1', x1: '0', y1: '0', x2: '1', y2: '0' },
        h('svg:stop', { offset: '0%', 'stop-color': '#38bdf8' }),
        h('svg:stop', { offset: '100%', 'stop-color': '#E69F00' })));
    s.appendChild(defs);

    // Column headers
    s.appendChild(h('svg:text', { class: 'wbt-col-title', x: colX[0] + NODE_W / 2, y: 22, 'text-anchor': 'middle', text: 'Producers (' + model.prods.length + ')' }));
    s.appendChild(h('svg:text', { class: 'wbt-col-title', x: colX[1] + NODE_W / 2, y: 22, 'text-anchor': 'middle', text: 'Trade Routes & Flows (' + model.mids.length + ')' }));
    s.appendChild(h('svg:text', { class: 'wbt-col-title', x: colX[2] + NODE_W / 2, y: 22, 'text-anchor': 'middle', text: 'Consumers (' + model.conss.length + ')' }));

    const linkLayer = h('svg:g', { 'data-layer': 'links' });
    const particleLayer = h('svg:g', { 'data-layer': 'particles' });
    const nodeLayer = h('svg:g', { 'data-layer': 'nodes' });
    s.appendChild(linkLayer); s.appendChild(particleLayer); s.appendChild(nodeLayer);

    const linkEls = [];
    const nodeEls = [];

    model.links.forEach(function (lk) {
      const a = lk.stage === 0 ? pPos[lk.from] : mPos[lk.from];
      const b = lk.stage === 0 ? mPos[lk.to] : cPos[lk.to];
      if (!a || !b) return;
      const strokeW = Math.max(3, Math.min(26, (lk.weight / Math.max(1, a.weight)) * a.h * 0.72));
      const y0 = a.y + Math.min(a.h - strokeW / 2, a.outOff + strokeW / 2);
      const y1 = b.y + Math.min(b.h - strokeW / 2, b.inOff + strokeW / 2);
      a.outOff += strokeW * 0.85;
      b.inOff += strokeW * 0.85;
      const x0 = a.x + NODE_W;
      const x1 = b.x;
      const mx = (x0 + x1) / 2;
      const d = 'M' + x0.toFixed(1) + ',' + y0.toFixed(1) +
        ' C' + mx.toFixed(1) + ',' + y0.toFixed(1) + ' ' +
        mx.toFixed(1) + ',' + y1.toFixed(1) + ' ' +
        x1.toFixed(1) + ',' + y1.toFixed(1);
      const path = h('svg:path', {
        class: 'wbt-sk-link', d: d,
        stroke: lk.stage === 0 ? 'url(#wbt-grad-0)' : 'url(#wbt-grad-1)',
        'stroke-width': strokeW.toFixed(1), 'stroke-opacity': 0.34,
      }, h('svg:title', { text: a.name + ' → ' + b.name + (lk.resNames.size ? ' (' + Array.from(lk.resNames).join(', ') + ')' : '') }));
      linkLayer.appendChild(path);
      linkEls.push({ el: path, from: lk.from, to: lk.to, stage: lk.stage });

      if (!st.reduced) {
        const count = Math.min(4, Math.max(1, Math.round(lk.weight)));
        for (let k = 0; k < count; k++) {
          const dot = h('svg:circle', {
            class: 'wbt-particle', r: Math.min(4.2, 2.2 + strokeW * 0.12).toFixed(1),
            fill: '#ffffff', stroke: lk.stage === 0 ? '#38bdf8' : '#f59e0b',
            'stroke-width': 1.5, filter: 'url(#wbt-glow)', 'pointer-events': 'none', 'aria-hidden': 'true',
          });
          particleLayer.appendChild(dot);
          particles.push({
            el: dot, t: k / count, speed: 0.0028 + (lk.weight * 0.0003),
            at: function (t) { return cubicAt(x0, y0, mx, y0, mx, y1, x1, y1, t); },
          });
        }
      }
    });

    function spotlight(key) {
      if (!key) {
        linkEls.forEach(function (x) { x.el.classList.remove('dim', 'lit'); });
        nodeEls.forEach(function (x) { x.el.classList.remove('dim'); });
        return;
      }
      const litNodes = new Set([key]);
      const litLinks = new Set();
      // Walk forward and backward one hop across the 3 columns
      linkEls.forEach(function (lk, idx) {
        if (lk.from === key || lk.to === key) { litLinks.add(idx); litNodes.add(lk.from); litNodes.add(lk.to); }
      });
      linkEls.forEach(function (lk, idx) {
        if (litNodes.has(lk.from) && litNodes.has(lk.to)) litLinks.add(idx);
      });
      linkEls.forEach(function (lk, idx) {
        lk.el.classList.toggle('lit', litLinks.has(idx));
        lk.el.classList.toggle('dim', !litLinks.has(idx));
      });
      nodeEls.forEach(function (nd) { nd.el.classList.toggle('dim', !litNodes.has(nd.key)); });
    }

    function drawColNodes(list, colIdx, fill, align) {
      const sel = W.state && W.state.selected;
      list.forEach(function (n) {
        const isSel = n.id === sel;
        const g = h('svg:g', {
          class: 'wbt-sk-node', role: 'button', tabindex: 0,
          'aria-label': n.name + (n.sub ? ', ' + n.sub : '') + ', ' + n.resources.size + ' resources',
        },
          h('svg:rect', {
            x: n.x, y: n.y, width: NODE_W, height: n.h, rx: 4, fill: fill,
            stroke: isSel ? 'var(--focus)' : 'var(--panel)', 'stroke-width': isSel ? 2.8 : 1.4,
          }),
          h('svg:text', {
            class: 'wbt-sk-lbl',
            x: align === 'left' ? n.x - 8 : align === 'right' ? n.x + NODE_W + 8 : n.x + NODE_W / 2,
            y: align === 'mid' ? n.y - 5 : n.y + n.h / 2 + (n.sub ? -1 : 4),
            'text-anchor': align === 'left' ? 'end' : align === 'right' ? 'start' : 'middle',
            text: trunc(n.name, 22),
          }),
          n.sub || n.resources.size ? h('svg:text', {
            class: 'wbt-sk-sub',
            x: align === 'left' ? n.x - 8 : align === 'right' ? n.x + NODE_W + 8 : n.x + NODE_W / 2,
            y: align === 'mid' ? n.y + n.h + 11 : n.y + n.h / 2 + 12,
            'text-anchor': align === 'left' ? 'end' : align === 'right' ? 'start' : 'middle',
            text: trunc(n.sub || (n.resources.size + ' resource' + (n.resources.size === 1 ? '' : 's')), 24),
          }) : null);

        const activate = function () {
          if (n.isLoc && G.N[n.id]) WB.select(n.id);
          else if (n.kind === 'resource') pick(n.id);
          else if (n.tr && n.tr.controlled_by && G.N[n.tr.controlled_by]) WB.select(n.tr.controlled_by);
        };
        g.addEventListener('click', activate);
        g.addEventListener('keydown', function (ev) { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); activate(); } });
        g.addEventListener('mouseenter', function () { spotlight(n.key); });
        g.addEventListener('mouseleave', function () { spotlight(null); });
        g.addEventListener('focus', function () { spotlight(n.key); });
        g.addEventListener('blur', function () { spotlight(null); });
        nodeLayer.appendChild(g);
        nodeEls.push({ el: g, key: n.key });
      });
    }

    drawColNodes(model.prods, 0, '#009E73', 'left');
    drawColNodes(model.mids, 1, '#0072B2', 'mid');
    drawColNodes(model.conss, 2, '#E69F00', 'right');

    wrap.appendChild(s);
    clear(stage);
    stage.appendChild(wrap);
  }

  // ---- Spatial Map Flow Mode
  function renderSpatial(vis) {
    clear(stage);
    stage.appendChild(mapSvg);
    stage.appendChild(ui.empty);
    Object.keys(mapLayers).forEach(function (k) { clear(mapLayers[k]); });
    const r = cur(), carry = r ? carrying(r) : null;
    const P = r ? r.producers || [] : [], C = r ? r.consumers || [] : [];
    const sel = W.state && W.state.selected;

    G.routes.forEach(function (rt) {
      const a = vis[rt.from], b = vis[rt.to]; if (!a || !b) return;
      const on = !carry || carry[rt.id];
      const w = on ? 1.8 + Math.min((rt.goods || []).length, 6) * 0.9 + (carry ? 2 : 0) : 1;
      const c = curve(a, b, 0.1);
      mapLayers.route.appendChild(h('svg:path', {
        d: c.d, fill: 'none', stroke: on ? (carry ? '#38bdf8' : '#888') : '#999',
        'stroke-width': w, 'stroke-opacity': on ? 0.85 : 0.18,
        'stroke-dasharray': rt.reciprocal === false ? '6 5' : null,
      }, h('svg:title', { text: G.name(rt.from) + ' ↔ ' + G.name(rt.to) + ': ' + ((rt.goods || []).join(', ') || 'no goods recorded') })));
      if (on && (carry || (rt.goods && rt.goods.length))) {
        const fwd = !(P.indexOf(rt.to) >= 0 && P.indexOf(rt.from) < 0);
        const cc = fwd ? c : curve(b, a, -0.1);
        const q = cc.at(0.6), ang = Math.atan2(q.ty, q.tx) * 180 / Math.PI;
        mapLayers.route.appendChild(h('svg:path', {
          d: 'M-6,-5L6,0L-6,5Z',
          transform: 'translate(' + q.x.toFixed(1) + ',' + q.y.toFixed(1) + ') rotate(' + ang.toFixed(0) + ')',
          fill: '#38bdf8', stroke: 'var(--panel)',
        }));
        if (!st.reduced) {
          for (let i = 0; i < 3; i++) {
            const dot = h('svg:circle', { class: 'wbt-particle', r: 3.6, fill: '#fff', stroke: '#38bdf8', 'stroke-width': 1.6, 'aria-hidden': 'true' });
            mapLayers.flow.appendChild(dot);
            particles.push({ el: dot, t: i / 3, speed: 0.0038, at: cc.at });
          }
        }
      }
    });

    Object.keys(vis).map(function (k) { return vis[k]; }).sort(function (a, b) { return rad(b) - rad(a); }).forEach(function (l) {
      const rr = rad(l), p = P.indexOf(l.id) >= 0, c = C.indexOf(l.id) >= 0, unfed = flags.unfed.indexOf(l.id) >= 0;
      const gl = r ? (p && c ? 'PC' : p ? 'P' : c ? 'C' : '') : '';
      const fill = !r ? '#94a3b8' : p && c ? '#CC79A7' : p ? '#009E73' : c ? '#E69F00' : '#94a3b8';
      const lab = l.name + (r ? (p ? ', produces ' + r.name : '') + (c ? ', consumes ' + r.name : '') : '');
      const g = h('svg:g', {
        class: 'wbg-node' + (l.id === sel ? ' wbg-sel' : ''),
        transform: 'translate(' + l.x + ',' + l.y + ')', role: 'button', tabindex: 0, 'aria-label': lab,
      },
        h('svg:title', { text: lab }),
        unfed ? h('svg:circle', { r: rr + 6, fill: 'none', stroke: '#D55E00', 'stroke-width': 2.5, 'stroke-dasharray': '4 3' }) : null,
        h('svg:path', { class: 'wbg-sh', d: shapeD(p ? 'triangle' : c ? 'square' : 'circle', rr), fill: fill, 'fill-opacity': r && !p && !c ? 0.45 : 1 }),
        gl ? h('svg:text', { class: 'wbg-glyph', 'text-anchor': 'middle', y: 4, text: gl }) : null,
        h('svg:text', { class: 'wbg-lbl', 'text-anchor': 'middle', y: rr + 14, text: l.name }));
      g.addEventListener('click', function () { if (!pz.wasDrag()) WB.select(l.id); });
      g.addEventListener('keydown', function (ev) { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); WB.select(l.id); } });
      mapLayers.node.appendChild(g);
    });
    ui.empty.style.display = G.locs.length ? 'none' : '';
  }

  function renderChips() {
    clear(ui.chipStrip);
    const rs = (E.resources || []).slice().sort(function (a, b) {
      const aw = (a.producers || []).length + (a.consumers || []).length;
      const bw = (b.producers || []).length + (b.consumers || []).length;
      return bw - aw || a.name.localeCompare(b.name);
    });
    const q = st.resSearch.trim().toLowerCase();
    const filtered = q ? rs.filter(function (r) { return (r.name + ' ' + (r.category || '')).toLowerCase().indexOf(q) >= 0; }) : rs;

    ui.chipStrip.appendChild(h('button', {
      type: 'button', class: 'wbt-rchip', 'aria-pressed': st.res === '' ? 'true' : 'false',
      onclick: function () { pick(''); }, text: 'All Resources (' + rs.length + ')',
    }));
    filtered.forEach(function (r) {
      const f = flags.res[r.name] || [];
      const hasBad = f.some(function (x) { return x.k === 'bad'; });
      const hasWarn = f.some(function (x) { return x.k === 'warn'; });
      const dotCol = hasBad ? '#D55E00' : hasWarn ? '#E69F00' : '#009E73';
      ui.chipStrip.appendChild(h('button', {
        type: 'button', class: 'wbt-rchip', 'aria-pressed': st.res === r.name ? 'true' : 'false',
        title: r.name + (r.category ? ' (' + r.category + ')' : '') + ' · ' + (r.producers || []).length + 'P / ' + (r.consumers || []).length + 'C',
        onclick: function () { pick(st.res === r.name ? '' : r.name); },
      }, h('span', { class: 'wbt-dot', style: 'background:' + dotCol, 'aria-hidden': 'true' }), r.name));
    });
  }

  function locChip(id) {
    return h('button', { type: 'button', class: 'wbg-chip', onclick: function () { WB.select(id); }, text: nm(id) });
  }
  const flagEl = function (f) { return h('span', { class: 'wbg-flag ' + f.k, text: f.t }); };

  function renderSide() {
    clear(ui.side);
    const rs = E.resources || [];
    const trs = E.trade_routes || [];
    const curs = E.currencies || [];
    const shocks = E.shocks || [];
    if (!rs.length && !curs.length && !shocks.length && !trs.length) {
      ui.side.appendChild(h('p', { class: 'wbg-empty', text: 'No economy data yet: add world/economy.yaml (resources, trade routes, currencies, shocks).' }));
      return;
    }

    // Active resource summary card
    const rSel = cur();
    if (rSel) {
      ui.side.appendChild(h('div', { class: 'wbt-ecard' },
        h('div', { class: 'wbt-ecard-head' },
          h('span', { class: 'wbt-ecard-title', text: rSel.name }),
          h('button', { type: 'button', class: 'wbg-btn', onclick: function () { pick(''); }, text: 'Reset' })),
        h('div', { class: 'wbt-ecard-meta', text: (rSel.category || 'resource') + (rSel.rarity ? ' · ' + rSel.rarity : '') }),
        (flags.res[rSel.name] || []).length ? h('div', { style: 'margin-bottom:6px' }, flags.res[rSel.name].map(flagEl)) : null,
        (rSel.producers || []).length ? h('div', { class: 'wbt-ecard-meta' }, 'Producers: ', h('div', { class: 'wbt-ecard-chips' }, rSel.producers.map(locChip))) : null,
        (rSel.consumers || []).length ? h('div', { class: 'wbt-ecard-meta' }, 'Consumers: ', h('div', { class: 'wbt-ecard-chips' }, rSel.consumers.map(locChip))) : null));
    }

    // Economic Shock Impact Cards (elevated, linking directly to causing events)
    ui.side.appendChild(h('h3', { text: 'Economic Shock Impact Cards (' + shocks.length + ')' }));
    if (shocks.length) {
      ui.side.appendChild(h('div', { class: 'wbt-card-grid' }, shocks.map(function (s) {
        const evNode = G.N[s.event];
        const fx = s.effects || {};
        const fxPills = Object.keys(fx).map(function (k) {
          let v = typeof fx[k] === 'string' ? fx[k] : JSON.stringify(fx[k]);
          if (v && v.length > 120) v = v.slice(0, 117) + '…';
          return h('div', { class: 'wbt-ecard-meta', text: k.replace(/_/g, ' ') + ': ' + v });
        });
        return h('div', { class: 'wbt-ecard shock' },
          h('div', { class: 'wbt-ecard-head' },
            evNode
              ? h('button', { type: 'button', class: 'wbt-shock-btn', onclick: function () { WB.select(s.event); }, text: '⚡ ' + evNode.name })
              : h('span', { class: 'wbt-ecard-title', text: '⚡ ' + String(s.event) }),
            h('span', { class: 'wbg-flag bad', text: 'Shock' })),
          fxPills);
      })));
    } else {
      ui.side.appendChild(h('p', { class: 'wbg-dim-t', text: 'No economic shocks recorded yet (add shocks: in world/economy.yaml).' }));
    }

    // Elevated Currency Cards
    ui.side.appendChild(h('h3', { text: 'Currencies (' + curs.length + ')' }));
    if (curs.length) {
      ui.side.appendChild(h('div', { class: 'wbt-card-grid' }, curs.map(function (c) {
        return h('div', { class: 'wbt-ecard currency' },
          h('div', { class: 'wbt-ecard-head' },
            h('span', { class: 'wbt-ecard-title', text: c.name }),
            c.issuer && G.N[c.issuer] ? locChip(c.issuer) : h('span', { class: 'wbg-dim-t', text: String(c.issuer || 'unissued') })),
          h('div', { class: 'wbt-ecard-meta', text: 'Accepted in:' }),
          h('div', { class: 'wbt-ecard-chips' },
            (c.accepted_in || []).length
              ? c.accepted_in.map(function (id) { return G.N[id] ? locChip(id) : h('span', { class: 'wbg-flag note', text: String(id) }); })
              : [h('span', { class: 'wbg-dim-t', text: 'not recorded' })]));
      })));
    } else {
      ui.side.appendChild(h('p', { class: 'wbg-dim-t', text: 'No currencies recorded.' }));
    }

    // Trade Corridors
    if (trs.length) {
      ui.side.appendChild(h('h3', { text: 'Major Trade Corridors (' + trs.length + ')' }));
      ui.side.appendChild(h('div', { class: 'wbt-card-grid' }, trs.map(function (t) {
        return h('div', { class: 'wbt-ecard route' },
          h('div', { class: 'wbt-ecard-head' },
            h('span', { class: 'wbt-ecard-title', text: t.name }),
            t.annual_value ? h('span', { class: 'wbg-flag note', text: t.annual_value }) : null),
          h('div', { class: 'wbt-ecard-meta', text: (t.from ? nm(t.from) : t.from_label || '?') + ' → ' + (t.to ? nm(t.to) : t.to_label || '?') + (t.status ? ' · ' + t.status : '') }),
          t.controlled_by && G.N[t.controlled_by] ? h('div', { class: 'wbt-ecard-chips' }, h('span', { class: 'wbg-dim-t', text: 'Controlled by ' }), locChip(t.controlled_by)) : null);
      })));
    }

    // Consistency audit summary
    const nflag = rs.filter(function (r) { return flags.res[r.name].some(function (f) { return f.k !== 'note'; }); }).length;
    ui.side.appendChild(h('h3', { text: 'Economy Consistency Check' }));
    ui.side.appendChild(h('p', { class: 'wbg-dim-t', role: 'status', text: nflag + ' of ' + rs.length + ' resources flagged · ' + flags.unfed.length + ' populated locations without food.' }));
    if (flags.unfed.length) {
      ui.side.appendChild(h('div', { class: 'wbt-ecard-chips' }, flags.unfed.map(function (id) { return [h('span', { class: 'wbg-flag bad', text: 'Unfed' }), locChip(id)]; })));
    }
  }

  function render() {
    st.dirty = false;
    stopAnim();
    particles = [];
    const vis = {};
    G.locs.forEach(function (l) { if (passes(W, l)) vis[l.id] = l; });
    renderChips();
    if (st.mode === 'sankey') renderSankey(vis);
    else renderSpatial(vis);
    if (ui.zoomWrap) ui.zoomWrap.style.display = st.mode === 'spatial' ? '' : 'none';
    renderSide();
    startAnim();
  }

  function pick(name) { st.res = name; render(); }

  WB.registerView({
    id: 'trade', title: 'Trade', order: 40,
    create: function (container, wb) {
      W = wb || WB; G = prep(W); E = G.D.economy || {}; injectCss(); st.reduced = reducedMotion(); computeFlags();
      mapSvg = h('svg:svg', { class: 'wbg-svg', viewBox: '-20 -20 1040 1040', role: 'group', 'aria-label': 'Spatial trade route flow map', preserveAspectRatio: 'xMidYMid meet' });
      pz = panzoom(mapSvg, function (u) { mapSvg.style.setProperty('--wbg-fs', (12 * u) + 'px'); });
      ['route', 'flow', 'node'].forEach(function (k) { mapLayers[k] = h('svg:g'); mapSvg.appendChild(mapLayers[k]); });

      const btnSankey = h('button', { type: 'button', class: 'wbg-btn', 'aria-pressed': 'true', text: 'Sankey Flow', onclick: function () { st.mode = 'sankey'; btnSankey.setAttribute('aria-pressed', 'true'); btnMap.setAttribute('aria-pressed', 'false'); render(); } });
      const btnMap = h('button', { type: 'button', class: 'wbg-btn', 'aria-pressed': 'false', text: 'Spatial Map', onclick: function () { st.mode = 'spatial'; btnMap.setAttribute('aria-pressed', 'true'); btnSankey.setAttribute('aria-pressed', 'false'); render(); } });
      ui.zoomWrap = h('span', { style: 'display:none' },
        h('button', { class: 'wbg-btn', type: 'button', 'aria-label': 'Zoom in', onclick: pz.zoomIn, text: '+' }),
        h('button', { class: 'wbg-btn', type: 'button', 'aria-label': 'Zoom out', onclick: pz.zoomOut, text: '−' }),
        h('button', { class: 'wbg-btn', type: 'button', 'aria-label': 'Reset view', onclick: pz.reset, text: 'Fit' }));

      const searchInput = h('input', {
        type: 'search', placeholder: 'Filter resources…', 'aria-label': 'Filter resource chips',
        oninput: function (e) { st.resSearch = e.target.value; renderChips(); },
      });
      ui.chipStrip = h('div', { class: 'wbt-chip-strip', role: 'group', 'aria-label': 'Resource filter chips' });
      const chipsBar = h('div', { class: 'wbt-chips-bar' }, searchInput, ui.chipStrip);

      stage = h('div', { class: 'wbg-stage' });
      ui.side = h('div', { class: 'wbg-side' });
      ui.empty = h('div', { class: 'wbg-empty', style: 'display:none', text: 'No locations with map positions yet.' });
      ui.sr = h('div', { class: 'wbg-sr' }, h('table', null,
        h('caption', { text: 'Resources, producers, consumers, and consistency flags' }),
        h('tbody', null, (E.resources || []).map(function (r) {
          return h('tr', null,
            h('th', { text: r.name }),
            h('td', { text: 'producers: ' + ((r.producers || []).map(nm).join(', ') || 'none') }),
            h('td', { text: 'consumers: ' + ((r.consumers || []).map(nm).join(', ') || 'none') }),
            h('td', { text: (flags.res[r.name] || []).map(function (f) { return f.t; }).join('; ') }));
        }))));

      root = h('div', { class: 'wbg-view' },
        h('div', { class: 'wbg-bar' },
          h('span', { class: 'wbg-dim-t', style: 'font-weight:600', text: 'Diagram:' }),
          btnSankey, btnMap, ui.zoomWrap,
          h('span', { class: 'wbg-dim-t', style: 'margin-left:auto', text: (E.resources || []).length + ' resources · ' + (E.trade_routes || []).length + ' trade routes · ' + (E.currencies || []).length + ' currencies' })),
        chipsBar,
        h('div', { class: 'wbg-body' }, stage, ui.side),
        ui.sr);
      container.appendChild(root);
      render();
    },
    activate: function () { st.active = true; st.reduced = reducedMotion(); if (st.dirty) render(); else startAnim(); },
    deactivate: function () { st.active = false; stopAnim(); },
    resize: function () { if (pz && st.mode === 'spatial') pz.refresh(); },
    onSelect: function () { if (root) render(); else st.dirty = true; },
    onFilter: function () { if (root) render(); else st.dirty = true; },
  });
})();
