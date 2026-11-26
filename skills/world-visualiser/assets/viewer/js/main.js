// main.js: the page shell (header, tabs, filters, list, detail panel, footer) around the registered views.
(function () {
  'use strict';
  const { el } = WB.util;
  const D = WB.data;
  const app = document.getElementById('app');
  const hasThree = typeof window.THREE !== 'undefined';
  app.replaceChildren();

  const banner = el('div', { class: 'banner', role: 'alert', hidden: hasThree },
    'three.js could not load (needs internet). The 3D views are unavailable; the entity list, detail panel, timeline and gallery still work.');

  // ---- header and filters
  const search = el('input', { type: 'search', placeholder: 'Search names (press /)', 'aria-label': 'Search by name' });
  let timer = null;
  search.addEventListener('input', () => {
    clearTimeout(timer);
    timer = setTimeout(() => { WB.state.filters.search = search.value; WB.setFilter(); }, 120);
  });
  const eraSel = el('select', { 'aria-label': 'Filter by era' }, el('option', { value: '', text: 'All eras' }),
    (D.calendar.eras || []).map((e) => el('option', { value: e.name, text: e.name })));
  eraSel.addEventListener('change', () => {
    const f = WB.state.filters.eras;
    f.clear();
    if (eraSel.value) f.add(eraSel.value);
    WB.setFilter();
  });
  const listBtn = el('button', { type: 'button', class: 'btn', 'aria-expanded': String(!hasThree), 'aria-controls': 'list', text: 'Entity list' });

  const themes = ['system', 'light', 'dark'];
  let themeIdx = 0;
  const themeBtn = el('button', { type: 'button', class: 'btn', 'aria-label': 'Cycle colour theme', text: 'Theme: system' });
  themeBtn.addEventListener('click', () => {
    themeIdx = (themeIdx + 1) % themes.length;
    const mode = themes[themeIdx];
    if (mode === 'system') document.documentElement.removeAttribute('data-theme');
    else document.documentElement.setAttribute('data-theme', mode);
    themeBtn.textContent = 'Theme: ' + mode;
    WB.bus.emit('theme', mode);
  });

  const header = el('header', { class: 'top' },
    el('h1', { text: (D.project && D.project.name) || 'World' }),
    search, eraSel, listBtn,
    el('span', { class: 'header-spacer', 'aria-hidden': 'true' }),
    themeBtn);

  const tablist = el('div', { class: 'tabs', role: 'tablist', 'aria-label': 'Views' });

  const typesPresent = Object.keys(WB.colors.type).filter((t) => D.nodes.some((n) => n.type === t));
  const chipBox = el('div', { class: 'chips', role: 'group', 'aria-label': 'Filter by type (none selected means all)' });
  typesPresent.forEach((t) => {
    const count = D.nodes.filter((n) => n.type === t).length;
    const b = el('button', { type: 'button', class: 'chip', 'aria-pressed': 'false' },
      el('span', { class: 'dot', style: 'background:' + WB.colors.type[t], 'aria-hidden': 'true' }),
      WB.typeGlyph[t] + ' ' + t + ' ' + count);
    b.addEventListener('click', () => {
      const f = WB.state.filters.types;
      if (f.has(t)) f.delete(t); else f.add(t);
      b.setAttribute('aria-pressed', String(f.has(t)));
      WB.setFilter();
    });
    chipBox.appendChild(b);
  });

  // ---- entity list (keyboard accessible, works without WebGL)
  const listBox = el('aside', { id: 'list', 'aria-label': 'Entity list', hidden: hasThree });
  const viewsBox = el('div', { id: 'views' });
  const detailBox = el('aside', { id: 'detail', 'aria-label': 'Details', 'aria-live': 'polite' });
  WB.detail.mount(detailBox);
  const main = el('main', {}, listBox, viewsBox, detailBox);

  const warnBtn = el('button', { type: 'button', class: 'btn', 'aria-expanded': 'false', 'aria-controls': 'warnings' });
  const warnBox = el('div', { id: 'warnings', hidden: true, role: 'region', 'aria-label': 'Data warnings' });
  const warnings = D.warnings || [];
  warnBtn.textContent = warnings.length + (warnings.length === 1 ? ' warning' : ' warnings');
  warnBtn.addEventListener('click', () => {
    const open = warnBox.hidden;
    warnBox.hidden = !open;
    warnBtn.setAttribute('aria-expanded', String(open));
  });
  warnBox.append(el('strong', { text: 'Data warnings' }), el('ul', {},
    warnings.length ? warnings.map((w) => el('li', { text: w })) : el('li', { text: 'None.' })));
  const stats = el('span', { class: 'muted' });
  const footer = el('footer', { class: 'bottom' }, warnBtn, stats);
  app.append(banner, header, tablist, chipBox, main, footer, warnBox);

  listBtn.addEventListener('click', () => {
    listBox.hidden = !listBox.hidden;
    listBtn.setAttribute('aria-expanded', String(!listBox.hidden));
    WB.bus.emit('resize');
  });

  function renderList() {
    const shown = D.nodes.filter((n) => WB.passes(n))
      .sort((a, b) => a.type.localeCompare(b.type) || a.name.localeCompare(b.name));
    const cap = 400;
    stats.textContent = shown.length + ' of ' + D.nodes.length + ' entities match';
    listBox.replaceChildren(el('ul', {}, shown.slice(0, cap).map((n) => el('li', {}, el('button', {
      type: 'button', class: 'link', 'aria-current': WB.state.selected === n.id ? 'true' : null,
      onclick: () => WB.select(n.id),
    }, el('span', { class: 'dot', style: 'background:' + (WB.colors.type[n.type] || '#888'), 'aria-hidden': 'true' }),
    n.name, el('span', { class: 'muted', text: ' ' + (WB.typeGlyph[n.type] || '') }))))),
    shown.length > cap ? el('p', { class: 'muted', text: (shown.length - cap) + ' more; refine the search.' }) : null,
    shown.length === 0 ? el('p', { class: 'muted', text: 'Nothing matches the filters.' }) : null);
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
    const tab = el('button', { type: 'button', role: 'tab', id: 'tab-' + v.id, 'aria-controls': 'view-' + v.id,
      'aria-selected': 'false', tabindex: '-1', text: v.title });
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

  WB.bus.on('select', (id) => {
    WB.views.forEach((v) => call(v, 'onSelect', id));
    renderList();
  });
  WB.bus.on('filter', () => {
    WB.views.forEach((v) => call(v, 'onFilter'));
    renderList();
  });
  WB.bus.on('resize', () => call(WB.views.find((v) => v.id === WB.state.activeView), 'resize'));
  if (typeof ResizeObserver !== 'undefined') new ResizeObserver(() => WB.bus.emit('resize')).observe(viewsBox);
  else window.addEventListener('resize', () => WB.bus.emit('resize'));

  document.addEventListener('keydown', (ev) => {
    const tag = (ev.target && ev.target.tagName) || '';
    if (tag === 'INPUT' || tag === 'SELECT' || tag === 'TEXTAREA') return;
    if (ev.key === '/') { ev.preventDefault(); search.focus(); }
  });

  renderList();
  if (WB.views.length) setView(WB.views[0].id);
  else viewsBox.appendChild(el('p', { class: 'view-msg', text: 'No views are installed.' }));
})();
