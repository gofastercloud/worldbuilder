// main.js: command-centre shell (header, command palette, telemetry HUD, tabs, filters, list, detail panel, footer).
(function () {
  'use strict';
  const { el, svg, safeImageSrc } = WB.util;
  const D = WB.data;
  const app = document.getElementById('app');
  const hasThree = typeof window.THREE !== 'undefined';
  const isMac = typeof navigator !== 'undefined' && /Mac|iPhone|iPad/i.test(navigator.platform || navigator.userAgent || '');
  app.replaceChildren();

  const banner = el('div', { class: 'banner', role: 'alert', hidden: hasThree },
    'three.js could not load (needs internet). The 3D views are unavailable; the entity list, detail panel, timeline and gallery still work.');

  // ---- header controls
  const search = el('input', { type: 'search', placeholder: 'Filter names (/)', 'aria-label': 'Search by name' });
  let timer = null;
  search.addEventListener('input', () => {
    clearTimeout(timer);
    timer = setTimeout(() => { WB.state.filters.search = search.value; WB.setFilter(); }, 120);
  });

  const eraSel = el('select', { 'aria-label': 'Filter by era' },
    el('option', { value: '', text: 'All eras' }),
    (D.calendar.eras || []).map((e) => el('option', { value: e.name, text: e.name })));
  eraSel.addEventListener('change', () => {
    const f = WB.state.filters.eras;
    f.clear();
    if (eraSel.value) f.add(eraSel.value);
    WB.setFilter();
  });

  const cmdBtn = el('button', {
    type: 'button', class: 'btn btn-cmd',
    'aria-label': 'Open Command Palette',
  }, 'Jump', el('kbd', { class: 'wb-kbd', text: isMac ? '⌘K' : 'Ctrl K' }));

  const hudIcon = svg('svg', { width: '14', height: '14', viewBox: '0 0 16 16', 'aria-hidden': 'true' },
    svg('rect', { x: '1', y: '8', width: '3', height: '7', rx: '1', fill: 'currentColor' }),
    svg('rect', { x: '6.5', y: '4', width: '3', height: '11', rx: '1', fill: 'currentColor' }),
    svg('rect', { x: '12', y: '1', width: '3', height: '14', rx: '1', fill: 'currentColor' }));
  const hudBtn = el('button', {
    type: 'button', class: 'btn', 'aria-expanded': 'false', 'aria-controls': 'telemetry-hud',
  }, hudIcon, 'Telemetry');

  const listBtn = el('button', {
    type: 'button', class: 'btn', 'aria-expanded': String(!hasThree), 'aria-controls': 'list', text: 'Entity list',
  });

  const themes = ['system', 'dark', 'light'];
  let themeIdx = 0;
  const themeBtn = el('button', { type: 'button', class: 'btn', 'aria-label': 'Cycle colour theme', text: 'Theme: system' });
  function cycleTheme() {
    themeIdx = (themeIdx + 1) % themes.length;
    const mode = themes[themeIdx];
    if (mode === 'system') document.documentElement.removeAttribute('data-theme');
    else document.documentElement.setAttribute('data-theme', mode);
    themeBtn.textContent = 'Theme: ' + mode;
    WB.bus.emit('theme', mode);
  }
  themeBtn.addEventListener('click', cycleTheme);

  const header = el('header', { class: 'top' },
    el('div', { class: 'brand-wrap' },
      el('span', { class: 'brand-orb', 'aria-hidden': 'true' }),
      el('h1', { text: (D.project && D.project.name) || 'World' })),
    search, eraSel, cmdBtn, hudBtn, listBtn,
    el('span', { class: 'header-spacer', 'aria-hidden': 'true' }),
    themeBtn);

  const tablist = el('div', { class: 'tabs', role: 'tablist', 'aria-label': 'Views' });

  // ---- type filter chips (kept in sync with Telemetry HUD)
  const typesPresent = Object.keys(WB.colors.type).filter((t) => D.nodes.some((n) => n.type === t));
  const typeChipButtons = new Map();
  const chipBox = el('div', { class: 'chips', role: 'group', 'aria-label': 'Filter by type (none selected means all)' });
  function toggleTypeFilter(t) {
    const f = WB.state.filters.types;
    if (f.has(t)) f.delete(t); else f.add(t);
    WB.setFilter();
  }
  typesPresent.forEach((t) => {
    const count = D.nodes.filter((n) => n.type === t).length;
    const b = el('button', { type: 'button', class: 'chip', 'aria-pressed': 'false' },
      el('span', { class: 'dot', style: 'background:' + WB.colors.type[t], 'aria-hidden': 'true' }),
      WB.typeGlyph[t] + ' ' + t + ' ' + count);
    b.addEventListener('click', () => toggleTypeFilter(t));
    typeChipButtons.set(t, b);
    chipBox.appendChild(b);
  });

  // ---- World Telemetry HUD Drawer
  const hudBox = el('section', { id: 'telemetry-hud', class: 'telemetry-hud', hidden: true, 'aria-label': 'World Telemetry' });
  const warnings = D.warnings || [];
  const warnBtn = el('button', { type: 'button', class: 'btn', 'aria-expanded': 'false', 'aria-controls': 'warnings' });
  const warnBox = el('div', { id: 'warnings', hidden: true, role: 'region', 'aria-label': 'Data warnings' });
  warnBtn.textContent = warnings.length + (warnings.length === 1 ? ' warning' : ' warnings');
  function toggleWarnings() {
    const open = warnBox.hidden;
    warnBox.hidden = !open;
    warnBtn.setAttribute('aria-expanded', String(open));
  }
  warnBtn.addEventListener('click', toggleWarnings);
  warnBox.append(el('strong', { text: 'Data warnings' }), el('ul', {},
    warnings.length ? warnings.map((w) => el('li', { text: w })) : el('li', { text: 'None.' })));

  // Precompute causal analytics for HUD
  const causalEdges = WB.edges.filter((e) => e.causal);
  const causalOut = new Map();
  const causalIn = new Map();
  causalEdges.forEach((e) => {
    if (!causalOut.has(e.source)) causalOut.set(e.source, []);
    if (!causalIn.has(e.target)) causalIn.set(e.target, []);
    causalOut.get(e.source).push(e.target);
    causalIn.get(e.target).push(e.source);
  });

  const eventNodes = D.nodes.filter((n) => n.type === 'event');
  const linkedEvents = eventNodes.filter((n) => (causalOut.get(n.id) || []).length > 0 || (causalIn.get(n.id) || []).length > 0);
  const causalPct = eventNodes.length ? Math.round((linkedEvents.length / eventNodes.length) * 100) : 0;

  // Cycle-safe longest causal chain depth (number of nodes in deepest chain)
  const depthMemo = new Map();
  function longestFrom(id, visiting) {
    if (depthMemo.has(id)) return depthMemo.get(id);
    if (visiting.has(id)) return 0;
    visiting.add(id);
    let best = 1;
    (causalOut.get(id) || []).forEach((nxt) => {
      best = Math.max(best, 1 + longestFrom(nxt, visiting));
    });
    visiting.delete(id);
    depthMemo.set(id, best);
    return best;
  }
  let deepestChain = 0;
  if (causalEdges.length) {
    D.nodes.forEach((n) => {
      if ((causalOut.get(n.id) || []).length) {
        deepestChain = Math.max(deepestChain, longestFrom(n.id, new Set()));
      }
    });
  }
  const artCount = D.nodes.filter((n) => !!safeImageSrc(n.image)).length;

  function renderTelemetryHud() {
    const total = D.nodes.length;
    const typeCounts = typesPresent.map((t) => ({
      type: t, count: D.nodes.filter((n) => n.type === t).length, color: WB.colors.type[t] || '#888',
    })).sort((a, b) => b.count - a.count);
    const activeTypes = WB.state.filters.types;

    // 1. Donut + Stacked Bar card
    const r = 24;
    const circ = 2 * Math.PI * r;
    let offset = 0;
    const donutSegs = typeCounts.map((tc) => {
      const frac = total ? tc.count / total : 0;
      const dash = frac * circ;
      const isDim = activeTypes.size > 0 && !activeTypes.has(tc.type);
      const seg = svg('circle', {
        class: 'hud-donut-seg', cx: '33', cy: '33', r: String(r),
        fill: 'none', stroke: tc.color, 'stroke-width': activeTypes.has(tc.type) ? '10' : '8',
        'stroke-dasharray': `${dash} ${Math.max(0, circ - dash)}`,
        'stroke-dashoffset': String(-offset),
        'stroke-opacity': isDim ? '0.28' : '0.95',
        transform: 'rotate(-90 33 33)',
        onclick: () => toggleTypeFilter(tc.type),
      }, svg('title', { text: tc.type + ': ' + tc.count + ' (click to filter)' }));
      offset += dash;
      return seg;
    });
    const donutSvg = svg('svg', {
      class: 'hud-donut', viewBox: '0 0 66 66', role: 'img', 'aria-label': 'Entity type breakdown',
    },
    svg('circle', { cx: '33', cy: '33', r: String(r), fill: 'none', stroke: 'var(--border-subtle)', 'stroke-width': '8' }),
    ...donutSegs,
    svg('text', { x: '33', y: '37', 'text-anchor': 'middle', 'font-size': '14', 'font-weight': '700', fill: 'var(--fg)', text: String(total) }));

    const stackBar = el('div', { class: 'hud-stackbar', role: 'group', 'aria-label': 'Entity proportions' },
      typeCounts.map((tc) => el('button', {
        type: 'button',
        class: 'hud-stack-seg' + (activeTypes.size && !activeTypes.has(tc.type) ? ' dim' : ''),
        style: `flex:${tc.count};background:${tc.color}`,
        title: `${tc.type}: ${tc.count}`,
        'aria-label': `Filter by ${tc.type} (${tc.count})`,
        onclick: () => toggleTypeFilter(tc.type),
      })));

    const typePills = el('div', { class: 'hud-type-pills' },
      typeCounts.map((tc) => el('button', {
        type: 'button', class: 'hud-type-pill', 'aria-pressed': String(activeTypes.has(tc.type)),
        onclick: () => toggleTypeFilter(tc.type),
      },
      el('span', { class: 'dot', style: 'background:' + tc.color, 'aria-hidden': 'true' }),
      tc.type + ' ' + tc.count)));

    const breakdownCard = el('div', { class: 'hud-card' },
      el('div', { class: 'hud-card-head' },
        el('span', { class: 'hud-card-title', text: 'Entity Breakdown' }),
        el('span', { class: 'hud-card-sub', text: typesPresent.length + ' types · click to filter' })),
      el('div', { class: 'hud-breakdown' },
        donutSvg,
        el('div', { class: 'hud-breakdown-right' }, stackBar, typePills)));

    // 2. Era Event Distribution Sparkbar card
    const eras = (D.calendar.eras || []).map((e) => ({
      name: e.name, prefix: e.prefix || e.name.slice(0, 6),
      count: eventNodes.filter((n) => n.era === e.name).length,
    }));
    const undatedCount = eventNodes.filter((n) => !n.era).length;
    if (undatedCount > 0 || !eras.length) eras.push({ name: '', prefix: 'Undated', count: undatedCount });
    const maxEra = Math.max(1, ...eras.map((e) => e.count));
    const sw = 240;
    const sh = 74;
    const padX = 8;
    const barSlot = (sw - padX * 2) / Math.max(1, eras.length);
    const barW = Math.max(12, Math.min(34, barSlot - 8));

    const sparkBars = eras.map((e, i) => {
      const h = Math.max(3, Math.round((e.count / maxEra) * 40));
      const x = padX + i * barSlot + (barSlot - barW) / 2;
      const y = 52 - h;
      const activeEra = WB.state.filters.eras.has(e.name);
      return svg('g', {
        class: 'hud-spark-bar',
        onclick: () => {
          if (!e.name) return;
          const f = WB.state.filters.eras;
          if (f.has(e.name)) { f.clear(); eraSel.value = ''; }
          else { f.clear(); f.add(e.name); eraSel.value = e.name; }
          WB.setFilter();
        },
      },
      svg('title', { text: (e.name || 'Undated') + ': ' + e.count + ' events' }),
      svg('rect', {
        x: String(x), y: String(y), width: String(barW), height: String(h), rx: '3',
        fill: activeEra ? 'var(--accent-2)' : 'var(--accent)',
        'fill-opacity': activeEra ? '1' : '0.82',
      }),
      svg('text', {
        x: String(x + barW / 2), y: String(y - 3), 'text-anchor': 'middle',
        'font-size': '9.5', 'font-weight': '650', fill: 'var(--fg)', text: String(e.count),
      }),
      svg('text', {
        x: String(x + barW / 2), y: '67', 'text-anchor': 'middle',
        'font-size': '9', fill: 'var(--muted)', text: e.prefix.slice(0, 8),
      }));
    });

    const eraCard = el('div', { class: 'hud-card' },
      el('div', { class: 'hud-card-head' },
        el('span', { class: 'hud-card-title', text: 'Era Event Distribution' }),
        el('span', { class: 'hud-card-sub', text: eventNodes.length + ' events' })),
      svg('svg', {
        class: 'hud-spark-svg', viewBox: `0 0 ${sw} ${sh}`, role: 'img', 'aria-label': 'Events per era',
      },
      svg('line', { x1: String(padX), y1: '52', x2: String(sw - padX), y2: '52', stroke: 'var(--border)', 'stroke-width': '1' }),
      ...sparkBars));

    // 3. Causal Connectivity Gauge & World Pulse card
    const gr = 34;
    const semiCirc = Math.PI * gr;
    const filled = (causalPct / 100) * semiCirc;
    const gaugeSvg = svg('svg', {
      class: 'hud-gauge-svg', viewBox: '0 0 92 58', role: 'img',
      'aria-label': causalPct + '% of events linked in causal chains',
    },
    svg('path', {
      d: 'M 12 48 A 34 34 0 0 1 80 48', fill: 'none', stroke: 'var(--border)', 'stroke-width': '8', 'stroke-linecap': 'round',
    }),
    svg('path', {
      d: 'M 12 48 A 34 34 0 0 1 80 48', fill: 'none', stroke: 'var(--accent)', 'stroke-width': '8', 'stroke-linecap': 'round',
      'stroke-dasharray': `${filled} ${semiCirc}`,
    }),
    svg('text', {
      x: '46', y: '44', 'text-anchor': 'middle', 'font-size': '15', 'font-weight': '750', fill: 'var(--fg)',
      text: causalPct + '%',
    }),
    svg('text', {
      x: '46', y: '55', 'text-anchor': 'middle', 'font-size': '8.5', fill: 'var(--muted)', text: 'CAUSAL',
    }));

    const warnPill = el('button', {
      type: 'button',
      class: 'hud-warn-pill ' + (warnings.length ? 'has-warn' : 'is-ok'),
      onclick: toggleWarnings,
      text: warnings.length ? warnings.length + (warnings.length === 1 ? ' warning' : ' warnings') : '0 warnings',
    });

    const pulseCard = el('div', { class: 'hud-card' },
      el('div', { class: 'hud-card-head' },
        el('span', { class: 'hud-card-title', text: 'Causal Connectivity' }),
        warnPill),
      el('div', { class: 'hud-gauge-row' },
        gaugeSvg,
        el('div', { class: 'hud-stats-grid' },
          el('div', { class: 'hud-stat' }, el('strong', { text: String(deepestChain) }), el('span', { text: 'Deepest chain' })),
          el('div', { class: 'hud-stat' }, el('strong', { text: String(causalEdges.length) }), el('span', { text: 'Causal links' })),
          el('div', { class: 'hud-stat' }, el('strong', { text: linkedEvents.length + '/' + eventNodes.length }), el('span', { text: 'Linked events' })),
          el('div', { class: 'hud-stat' }, el('strong', { text: artCount + '/' + total }), el('span', { text: 'Artwork' })))));

    hudBox.replaceChildren(el('div', { class: 'hud-grid' }, breakdownCard, eraCard, pulseCard));
  }

  function toggleTelemetryHud() {
    const opening = hudBox.hidden;
    hudBox.hidden = !opening;
    hudBtn.setAttribute('aria-expanded', String(opening));
    if (opening) renderTelemetryHud();
    WB.bus.emit('resize');
  }
  hudBtn.addEventListener('click', toggleTelemetryHud);

  // ---- entity list, views & detail panel
  const listBox = el('aside', { id: 'list', 'aria-label': 'Entity list', hidden: hasThree });
  const viewsBox = el('div', { id: 'views' });
  const detailBox = el('aside', { id: 'detail', 'aria-label': 'Details', 'aria-live': 'polite' });
  WB.detail.mount(detailBox);
  const main = el('main', {}, listBox, viewsBox, detailBox);

  const stats = el('span', { class: 'muted' });
  const footer = el('footer', { class: 'bottom' }, warnBtn, stats);
  app.append(banner, header, tablist, chipBox, hudBox, main, footer, warnBox);

  function toggleEntityList() {
    listBox.hidden = !listBox.hidden;
    listBtn.setAttribute('aria-expanded', String(!listBox.hidden));
    WB.bus.emit('resize');
  }
  listBtn.addEventListener('click', toggleEntityList);

  function syncFilterControls() {
    typeChipButtons.forEach((btn, t) => btn.setAttribute('aria-pressed', String(WB.state.filters.types.has(t))));
    if (!hudBox.hidden) renderTelemetryHud();
  }

  function renderList() {
    const shown = D.nodes.filter((n) => WB.passes(n))
      .sort((a, b) => a.type.localeCompare(b.type) || a.name.localeCompare(b.name));
    const cap = 400;
    stats.textContent = shown.length + ' of ' + D.nodes.length + ' entities match';
    listBox.replaceChildren(...[
      el('ul', {}, shown.slice(0, cap).map((n) => el('li', {}, el('button', {
        type: 'button', class: 'link', 'aria-current': WB.state.selected === n.id ? 'true' : null,
        onclick: () => WB.select(n.id),
      }, el('span', { class: 'dot', style: 'background:' + (WB.colors.type[n.type] || '#888'), 'aria-hidden': 'true' }),
      n.name, el('span', { class: 'muted', text: ' ' + (WB.typeGlyph[n.type] || '') }))))),
      shown.length > cap ? el('p', { class: 'muted', text: (shown.length - cap) + ' more; refine the search.' }) : null,
      shown.length === 0 ? el('p', { class: 'muted', text: 'Nothing matches the filters.' }) : null,
    ].filter(Boolean));
  }

  // ---- views and tabs
  const made = new Map();
  const tabs = [];
  WB.views.forEach((v) => {
    const panel = el('div', { class: 'view', id: 'view-' + v.id, role: 'tabpanel', 'aria-labelledby': 'tab-' + v.id, hidden: true });
    viewsBox.appendChild(panel);
    try { v.create(panel, WB); } catch (e) {
      console.error('view ' + v.id + ' failed to create', e);
      panel.replaceChildren(el('p', { class: 'view-msg', text: 'The ' + v.title + ' view failed to load: ' + e.message }));
    }
    made.set(v.id, panel);
    const tab = el('button', {
      type: 'button', role: 'tab', id: 'tab-' + v.id, 'aria-controls': 'view-' + v.id,
      'aria-selected': 'false', tabindex: '-1', text: v.title,
    });
    tab.addEventListener('click', () => setView(v.id));
    tab.addEventListener('keydown', (ev) => {
      const i = tabs.indexOf(tab);
      let j = null;
      if (ev.key === 'ArrowRight') j = (i + 1) % tabs.length;
      else if (ev.key === 'ArrowLeft') j = (i - 1 + tabs.length) % tabs.length;
      else if (ev.key === 'Home') j = 0;
      else if (ev.key === 'End') j = tabs.length - 1;
      if (j !== null) { ev.preventDefault(); tabs[j].focus(); setView(WB.views[j].id); }
    });
    tabs.push(tab);
    tablist.appendChild(tab);
  });

  function call(v, name, ...args) {
    if (v && typeof v[name] === 'function') {
      try { v[name](...args); } catch (e) { console.error('view ' + v.id + '.' + name + ' failed', e); }
    }
  }
  function setView(id) {
    const next = WB.views.find((v) => v.id === id);
    if (!next) return;
    const prev = WB.views.find((v) => v.id === WB.state.activeView);
    if (prev && prev !== next) { call(prev, 'deactivate'); made.get(prev.id).hidden = true; }
    made.get(id).hidden = false;
    WB.state.activeView = id;
    tabs.forEach((t, i) => {
      const on = WB.views[i].id === id;
      t.setAttribute('aria-selected', String(on));
      t.tabIndex = on ? 0 : -1;
    });
    call(next, 'activate');
    call(next, 'resize');
    WB.bus.emit('view', id);
  }
  WB.setView = setView;

  // ---- Quick Command Palette (Cmd+K / Ctrl+K)
  let cmdEl = null;
  let cmdInput = null;
  let cmdList = null;
  let cmdReturnFocus = null;
  let cmdResults = [];
  let cmdActiveIdx = 0;

  function fuzzyScore(text, query) {
    if (!query) return { score: 1, ranges: [] };
    const t = text.toLowerCase();
    const q = query.toLowerCase();
    const exact = t.indexOf(q);
    if (exact >= 0) {
      const bonus = exact === 0 ? 120 : (t[exact - 1] === ' ' || t[exact - 1] === '-' ? 95 : 70);
      return { score: bonus - exact * 0.5, ranges: [[exact, exact + q.length]] };
    }
    let qi = 0;
    let score = 0;
    let streak = 0;
    const ranges = [];
    for (let ti = 0; ti < t.length && qi < q.length; ti++) {
      if (t[ti] === q[qi]) {
        streak += 1;
        score += 10 + streak * 5 + (ti === 0 || t[ti - 1] === ' ' ? 12 : 0);
        if (ranges.length && ranges[ranges.length - 1][1] === ti) ranges[ranges.length - 1][1] = ti + 1;
        else ranges.push([ti, ti + 1]);
        qi += 1;
      } else {
        streak = 0;
      }
    }
    return qi === q.length ? { score, ranges } : null;
  }

  function renderHighlighted(text, ranges) {
    if (!ranges || !ranges.length) return [text];
    const outNodes = [];
    let pos = 0;
    ranges.forEach(([s, e]) => {
      if (s > pos) outNodes.push(text.slice(pos, s));
      outNodes.push(el('mark', { text: text.slice(s, e) }));
      pos = e;
    });
    if (pos < text.length) outNodes.push(text.slice(pos));
    return outNodes;
  }

  function getCommandEntries(query) {
    const q = query.trim();
    const actions = [];
    WB.views.forEach((v) => {
      actions.push({
        group: 'Views & Commands',
        label: 'View: ' + v.title,
        keywords: v.title + ' ' + v.id + ' view tab',
        meta: WB.state.activeView === v.id ? 'active' : 'switch',
        run: () => setView(v.id),
      });
    });
    actions.push(
      {
        group: 'Views & Commands', label: 'Toggle World Telemetry HUD',
        keywords: 'telemetry hud stats analytics chart gauge',
        meta: hudBox.hidden ? 'open' : 'close', run: toggleTelemetryHud,
      },
      {
        group: 'Views & Commands', label: 'Cycle Colour Theme',
        keywords: 'theme dark light system obsidian parchment',
        meta: themes[themeIdx], run: cycleTheme,
      },
      {
        group: 'Views & Commands', label: 'Toggle Entity List Sidebar',
        keywords: 'sidebar list entities panel',
        meta: listBox.hidden ? 'show' : 'hide', run: toggleEntityList,
      },
    );
    const hasFilters = WB.state.filters.types.size || WB.state.filters.eras.size || WB.state.filters.search.trim();
    if (hasFilters) {
      actions.push({
        group: 'Views & Commands', label: 'Clear All Active Filters',
        keywords: 'clear reset filters search', meta: 'reset',
        run: () => {
          WB.state.filters.types.clear();
          WB.state.filters.eras.clear();
          WB.state.filters.search = '';
          search.value = '';
          eraSel.value = '';
          WB.setFilter();
        },
      });
    }

    const matchedActions = [];
    actions.forEach((a) => {
      const m = fuzzyScore(a.label, q) || fuzzyScore(a.keywords, q);
      if (m) matchedActions.push({ ...a, score: m.score + (q ? 5 : 0), ranges: fuzzyScore(a.label, q)?.ranges || [] });
    });
    matchedActions.sort((a, b) => b.score - a.score);

    const matchedEntities = [];
    D.nodes.forEach((n) => {
      const mName = fuzzyScore(n.name || n.id, q);
      const mType = !mName && q ? fuzzyScore(n.type + ' ' + (n.era || '') + ' ' + n.id, q) : null;
      const m = mName || mType;
      if (!m) return;
      const causalCount = (causalOut.get(n.id) || []).length + (causalIn.get(n.id) || []).length;
      const totalDeg = WB.degree(n.id);
      matchedEntities.push({
        group: 'Entities',
        node: n,
        label: n.name || n.id,
        causalCount,
        totalDeg,
        score: m.score + (mName ? 20 : 0) + Math.min(totalDeg, 10) * 0.2,
        ranges: mName ? mName.ranges : [],
        run: () => WB.select(n.id),
      });
    });
    matchedEntities.sort((a, b) => b.score - a.score || a.label.localeCompare(b.label));

    return [
      ...matchedActions.slice(0, q ? 6 : 8),
      ...matchedEntities.slice(0, q ? 24 : 16),
    ];
  }

  function closeCmdPalette() {
    if (!cmdEl || cmdEl.hidden) return;
    cmdEl.hidden = true;
    if (cmdReturnFocus && typeof cmdReturnFocus.focus === 'function') cmdReturnFocus.focus();
    cmdReturnFocus = null;
  }

  function renderCmdList() {
    if (!cmdList || !cmdInput) return;
    cmdResults = getCommandEntries(cmdInput.value);
    if (cmdActiveIdx >= cmdResults.length) cmdActiveIdx = 0;
    if (!cmdResults.length) {
      cmdList.replaceChildren(el('li', { class: 'wb-cmdk-empty', text: 'No matching entities or commands.' }));
      return;
    }

    const frag = document.createDocumentFragment();
    let lastGroup = null;
    cmdResults.forEach((item, idx) => {
      if (item.group !== lastGroup) {
        lastGroup = item.group;
        frag.appendChild(el('li', { class: 'wb-cmdk-sec', role: 'presentation', text: item.group }));
      }
      const isAct = idx === cmdActiveIdx;
      const rowChildren = [];
      if (item.node) {
        const col = WB.colors.type[item.node.type] || '#888';
        rowChildren.push(
          el('span', { class: 'wb-cmdk-pill', style: 'border-color:' + col },
            el('span', { class: 'dot', style: 'background:' + col, 'aria-hidden': 'true' }),
            item.node.type),
          el('span', { class: 'wb-cmdk-name' }, ...renderHighlighted(item.label, item.ranges)),
          el('span', { class: 'wb-cmdk-meta' },
            item.node.era ? el('span', { text: item.node.era }) : (item.node.date_label ? el('span', { text: item.node.date_label }) : null),
            item.causalCount > 0 ? el('span', { class: 'wb-cmdk-pill', text: item.causalCount + ' causal' })
              : (item.totalDeg > 0 ? el('span', { text: item.totalDeg + ' links' }) : null)),
        );
      } else {
        rowChildren.push(
          el('span', { class: 'wb-cmdk-name' }, ...renderHighlighted(item.label, item.ranges)),
          item.meta ? el('span', { class: 'wb-cmdk-meta', text: item.meta }) : null,
        );
      }
      const btn = el('button', {
        type: 'button',
        id: 'wb-cmdk-opt-' + idx,
        class: 'wb-cmdk-item',
        role: 'option',
        'aria-selected': String(isAct),
        onmouseenter: () => { cmdActiveIdx = idx; updateCmdSelection(); },
        onclick: () => { closeCmdPalette(); item.run(); },
      }, ...rowChildren);
      frag.appendChild(el('li', { role: 'presentation' }, btn));
    });
    cmdList.replaceChildren(frag);
    updateCmdSelection();
  }

  function updateCmdSelection() {
    if (!cmdList || !cmdInput) return;
    const opts = cmdList.querySelectorAll('.wb-cmdk-item');
    opts.forEach((btn, i) => {
      const active = i === cmdActiveIdx;
      btn.setAttribute('aria-selected', String(active));
      if (active) btn.scrollIntoView({ block: 'nearest' });
    });
    if (opts[cmdActiveIdx]) cmdInput.setAttribute('aria-activedescendant', opts[cmdActiveIdx].id);
    else cmdInput.removeAttribute('aria-activedescendant');
  }

  function openCmdPalette(triggerEl) {
    cmdReturnFocus = triggerEl || document.activeElement;
    if (!cmdEl) {
      cmdInput = el('input', {
        type: 'text', class: 'wb-cmdk-input',
        placeholder: 'Jump to entity, switch view, toggle telemetry or theme…',
        'aria-label': 'Command palette search',
        role: 'combobox', 'aria-expanded': 'true', 'aria-controls': 'wb-cmdk-listbox', 'aria-autocomplete': 'list',
      });
      cmdList = el('ul', { id: 'wb-cmdk-listbox', class: 'wb-cmdk-list', role: 'listbox', 'aria-label': 'Command results' });
      cmdInput.addEventListener('input', () => { cmdActiveIdx = 0; renderCmdList(); });
      cmdInput.addEventListener('keydown', (ev) => {
        if (ev.key === 'ArrowDown') {
          ev.preventDefault();
          if (cmdResults.length) { cmdActiveIdx = (cmdActiveIdx + 1) % cmdResults.length; updateCmdSelection(); }
        } else if (ev.key === 'ArrowUp') {
          ev.preventDefault();
          if (cmdResults.length) { cmdActiveIdx = (cmdActiveIdx - 1 + cmdResults.length) % cmdResults.length; updateCmdSelection(); }
        } else if (ev.key === 'Enter') {
          ev.preventDefault();
          const chosen = cmdResults[cmdActiveIdx];
          if (chosen) { closeCmdPalette(); chosen.run(); }
        } else if (ev.key === 'Escape') {
          ev.preventDefault();
          closeCmdPalette();
        }
      });

      cmdEl = el('div', {
        class: 'wb-cmdk', role: 'dialog', 'aria-modal': 'true', 'aria-label': 'Command palette', hidden: true,
        onclick: (ev) => { if (ev.target === cmdEl) closeCmdPalette(); },
      },
      el('div', { class: 'wb-cmdk-dialog' },
        el('div', { class: 'wb-cmdk-input-row' },
          el('span', { class: 'wb-cmdk-icon', 'aria-hidden': 'true', text: '⌘' }),
          cmdInput,
          el('kbd', { class: 'wb-kbd', text: 'ESC' })),
        cmdList,
        el('div', { class: 'wb-cmdk-foot' },
          el('span', { class: 'wb-cmdk-hints' },
            el('span', {}, el('kbd', { class: 'wb-kbd', text: '↑↓' }), ' navigate'),
            el('span', {}, el('kbd', { class: 'wb-kbd', text: '↵' }), ' select'),
            el('span', {}, el('kbd', { class: 'wb-kbd', text: 'esc' }), ' close')),
          el('span', { text: D.nodes.length + ' entities indexed' }))));
      document.body.appendChild(cmdEl);
    }
    cmdEl.hidden = false;
    cmdInput.value = '';
    cmdActiveIdx = 0;
    renderCmdList();
    cmdInput.focus();
  }
  cmdBtn.addEventListener('click', () => openCmdPalette(cmdBtn));

  // ---- bus wiring & global shortcuts
  WB.bus.on('select', (id) => {
    WB.views.forEach((v) => call(v, 'onSelect', id));
    renderList();
  });
  WB.bus.on('filter', () => {
    syncFilterControls();
    WB.views.forEach((v) => call(v, 'onFilter'));
    renderList();
  });
  WB.bus.on('resize', () => call(WB.views.find((v) => v.id === WB.state.activeView), 'resize'));
  if (typeof ResizeObserver !== 'undefined') new ResizeObserver(() => WB.bus.emit('resize')).observe(viewsBox);
  else window.addEventListener('resize', () => WB.bus.emit('resize'));

  document.addEventListener('keydown', (ev) => {
    if ((ev.metaKey || ev.ctrlKey) && ev.key.toLowerCase() === 'k') {
      ev.preventDefault();
      if (cmdEl && !cmdEl.hidden) closeCmdPalette();
      else openCmdPalette(document.activeElement);
      return;
    }
    if (ev.key === 'Escape' && cmdEl && !cmdEl.hidden) {
      ev.preventDefault();
      closeCmdPalette();
      return;
    }
    const tag = (ev.target && ev.target.tagName) || '';
    if (tag === 'INPUT' || tag === 'SELECT' || tag === 'TEXTAREA') return;
    if (ev.key === '/') { ev.preventDefault(); search.focus(); }
  });

  renderList();
  if (WB.views.length) setView(WB.views[0].id);
  else viewsBox.appendChild(el('p', { class: 'view-msg', text: 'No views are installed.' }));
})();
