// timeline.js: SVG timeline of events and traditions with era bands, causal arcs and memory links.
(function () {
  'use strict';
  const { el, svg, byId, fmtT } = WB.util;
  const D = WB.data;
  const SIZE = { 'world-changing': 9, major: 7, moderate: 5, minor: 3.5 };
  const LABEL_W = 130;
  const ROW = 22;
  const AXIS_H = 46;
  const trunc = (s, n) => (s.length > n ? s.slice(0, n - 1) + '…' : s);

  WB.registerView({
    id: 'timeline', title: 'Timeline', order: 20,
    create(container) {
      container.classList.add('tl');
      const cal = D.calendar;
      const events = D.timeline.events || [];
      const traditions = D.timeline.traditions || [];
      const opts = { lanes: 'type', zoom: 1 };
      const mk = new Map(); // id -> {g, x, y, item}
      let arcEls = []; // {path, e}
      let order = []; // visible ids in chronological order
      let lastW = 0;

      const laneSel = el('select', { 'aria-label': 'Group lanes by' },
        el('option', { value: 'type', text: 'Lanes by event type' }), el('option', { value: 'location', text: 'Lanes by location' }));
      laneSel.addEventListener('change', () => { opts.lanes = laneSel.value; draw(); });
      const zoom = (f) => { opts.zoom = Math.min(60, Math.max(1, opts.zoom * f)); draw(); };
      const bar = el('div', { class: 'tl-bar' }, laneSel,
        el('button', { type: 'button', class: 'btn', text: 'Zoom in', onclick: () => zoom(1.5) }),
        el('button', { type: 'button', class: 'btn', text: 'Zoom out', onclick: () => zoom(1 / 1.5) }),
        el('button', { type: 'button', class: 'btn', text: 'Fit', onclick: () => { opts.zoom = 1; draw(); } }),
        el('span', { class: 'muted', text: 'Ctrl+wheel zooms. Arrows: left and right by date, up to a cause, down to an effect.' }),
        el('span', { class: 'muted', id: 'tl-count' }));
      const scroll = el('div', { class: 'tl-scroll' });
      const tip = el('div', { class: 'tl-tip', hidden: true });
      const tableWrap = el('div', { class: 'sr-only' });
      container.append(bar, scroll, tip, tableWrap);
      const count = bar.querySelector('#tl-count');

      const sizeOf = (ev) => SIZE[ev.significance] || 5;
      const nodeOf = (id) => byId.get(id);
      const showTip = (id, x, y) => {
        const n = nodeOf(id);
        if (!n) return;
        const r = container.getBoundingClientRect();
        tip.textContent = n.name + ' | ' + (n.date_label || fmtT(n.t)) + (n.era ? ' | ' + n.era : '');
        tip.style.left = Math.max(4, Math.min(x - r.left + 12, r.width - 260)) + 'px';
        tip.style.top = (y - r.top + 14) + 'px';
        tip.hidden = false;
      };

      function tickStep(ppy) {
        const steps = [1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000, 2000, 5000];
        return steps.find((s) => s * ppy >= 80) || 5000;
      }

      function draw() {
        const avail = Math.max(300, scroll.clientWidth - LABEL_W - 24);
        const span = Math.max(1e-9, cal.t_max - cal.t_min);
        const ppy = (avail / span) * opts.zoom;
        const W = Math.ceil(span * ppy) + 60;
        lastW = avail;
        const X = (t) => (t - cal.t_min) * ppy + 20;

        // items
        const evs = events.filter((e) => e.t !== null && e.t !== undefined && WB.passes(nodeOf(e.id)));
        const trs = traditions.filter((t) => t.first_attested_t !== null && t.first_attested_t !== undefined && WB.passes(nodeOf(t.id)));
        const laneKey = (e) => {
          if (opts.lanes === 'location') {
            const loc = (e.locations || []).find((l) => byId.has(l));
            return loc ? byId.get(loc).name : '(no location)';
          }
          return e.type || 'other';
        };
        const laneMap = new Map();
        evs.forEach((e) => { const k = laneKey(e); if (!laneMap.has(k)) laneMap.set(k, []); laneMap.get(k).push(e); });
        const laneNames = [...laneMap.keys()].sort((a, b) => (/^\(|^other$/.test(a) ? 1 : 0) - (/^\(|^other$/.test(b) ? 1 : 0) || a.localeCompare(b));
        const lanes = laneNames.map((k) => ({ name: k, items: laneMap.get(k).map((e) => ({ id: e.id, name: e.name, t: e.t, end: e.end_t, r: sizeOf(e), kind: 'event', ev: e })) }));
        if (trs.length) lanes.push({ name: 'traditions (memory)', items: trs.map((t) => ({ id: t.id, name: t.name, t: t.first_attested_t, end: null, r: 6, kind: 'tradition', ev: null })) });

        // pack each lane into rows
        let y = AXIS_H;
        lanes.forEach((ln) => {
          ln.items.sort((a, b) => a.t - b.t || a.id.localeCompare(b.id));
          const rowsEnd = [];
          ln.items.forEach((it) => {
            it.x = X(it.t);
            const label = trunc(it.name, 26);
            it.label = label;
            const w = it.r * 2 + 6 + label.length * 5.7;
            let r = rowsEnd.findIndex((end) => it.x - it.r > end + 6);
            if (r < 0) { r = rowsEnd.length; rowsEnd.push(0); }
            rowsEnd[r] = it.x - it.r + w;
            it.row = r;
          });
          ln.top = y;
          ln.h = Math.max(1, rowsEnd.length) * ROW + 14;
          ln.items.forEach((it) => { it.y = ln.top + 10 + it.row * ROW + ROW / 2; });
          y += ln.h;
        });
        const H = Math.max(y + 10, 160);

        const s = svg('svg', { width: W, height: H, role: 'group', 'aria-label': 'Timeline of events', viewBox: '0 0 ' + W + ' ' + H });
        // markers for arrowheads
        const defs = svg('defs', {});
        [['n', 'var(--muted)'], ['up', '#56B4E9'], ['down', '#E69F00'], ['mem', '#E7298A']].forEach(([k, c]) => {
          defs.appendChild(svg('marker', { id: 'tl-ah-' + k, viewBox: '0 0 8 8', refX: 7, refY: 4, markerWidth: 7, markerHeight: 7, orient: 'auto' },
            svg('path', { d: 'M0,0 L8,4 L0,8 z', fill: c })));
        });
        s.appendChild(defs);
        // era bands
        (cal.eras || []).forEach((er, i) => {
          const x0 = X(er.t0); const x1 = X(er.t1);
          s.appendChild(svg('rect', { class: i % 2 ? 'band-b' : 'band-a', x: x0, y: 0, width: Math.max(0, x1 - x0), height: H }));
          s.appendChild(svg('text', { class: 'era-name', x: x0 + 6, y: 15 }, er.name + ' (' + er.prefix + ')'));
        });
        // ticks
        const step = tickStep(ppy);
        const firstEra = (cal.eras || [])[0];
        for (let t = Math.ceil(cal.t_min / step) * step; t <= cal.t_max; t += step) {
          const x = X(t);
          s.appendChild(svg('line', { class: 'tick', x1: x, x2: x, y1: 24, y2: H, 'stroke-opacity': 0.35 }));
          s.appendChild(svg('text', { class: 'tick-label', x: x + 3, y: 38 }, fmtT(t + (firstEra ? 0 : 0))));
        }
        lanes.forEach((ln) => s.appendChild(svg('line', { class: 'lane-sep', x1: 0, x2: W, y1: ln.top, y2: ln.top })));
        if (cal.present_t !== null && cal.present_t !== undefined) {
          const x = X(cal.present_t);
          s.appendChild(svg('line', { class: 'present', x1: x, x2: x, y1: 20, y2: H }));
          s.appendChild(svg('text', { class: 'present-label', x: x + 4, y: H - 6 }, 'present'));
        }

        // positions for arcs
        mk.clear();
        const pos = new Map();
        lanes.forEach((ln) => ln.items.forEach((it) => pos.set(it.id, it)));
        const arcLayer = svg('g', {});
        s.appendChild(arcLayer);
        arcEls = [];
        WB.edges.forEach((e) => {
          if (!(e.causal || e.memory)) return;
          const a = pos.get(e.source); const b = pos.get(e.target);
          if (!a || !b) return;
          const dx = Math.abs(b.x - a.x);
          const lift = Math.min(90, 14 + dx * 0.18);
          const top = Math.min(a.y, b.y) - lift;
          const d = 'M' + a.x + ',' + a.y + ' Q' + (a.x + b.x) / 2 + ',' + Math.max(8, top) + ' ' + (b.x - Math.sign(b.x - a.x || 1) * (b.r + 2)) + ',' + b.y;
          const p = svg('path', { class: 'arc' + (e.memory ? ' memory' : ''), d, 'marker-end': 'url(#tl-ah-' + (e.memory ? 'mem' : 'n') + ')' });
          arcLayer.appendChild(p);
          arcEls.push({ p, e });
        });

        // markers
        const mkLayer = svg('g', {});
        s.appendChild(mkLayer);
        order = [];
        lanes.forEach((ln) => ln.items.forEach((it) => {
          const col = WB.colors.type[it.kind];
          const g = svg('g', { class: 'mk', tabindex: '-1', role: 'button', 'data-id': it.id,
            'aria-label': it.name + ', ' + (byId.get(it.id).date_label || fmtT(it.t)) + ', ' + it.kind });
          if (it.end !== null && it.end !== undefined && it.end > it.t) {
            g.appendChild(svg('rect', { class: 'dur', x: it.x, y: it.y - 2.5, width: Math.max(2, (it.end - it.t) * ppy), height: 5, rx: 2, fill: col }));
          }
          g.appendChild(it.kind === 'tradition'
            ? svg('rect', { class: 'shape', x: it.x - it.r + 1, y: it.y - it.r + 1, width: (it.r - 1) * 2, height: (it.r - 1) * 2, transform: 'rotate(45 ' + it.x + ' ' + it.y + ')', fill: col })
            : svg('circle', { class: 'shape', cx: it.x, cy: it.y, r: it.r, fill: col }));
          g.appendChild(svg('text', { x: it.x + it.r + 4, y: it.y + 4 }, it.label));
          g.addEventListener('click', () => WB.select(it.id));
          g.addEventListener('keydown', (ev) => { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); WB.select(it.id); } });
          g.addEventListener('mouseenter', (ev) => showTip(it.id, ev.clientX, ev.clientY));
          g.addEventListener('mousemove', (ev) => showTip(it.id, ev.clientX, ev.clientY));
          g.addEventListener('mouseleave', () => { tip.hidden = true; });
          g.addEventListener('focus', () => showTip(it.id, g.getBoundingClientRect().left, g.getBoundingClientRect().bottom));
          g.addEventListener('blur', () => { tip.hidden = true; });
          mkLayer.appendChild(g);
          mk.set(it.id, { g, item: it });
        }));
        order = [...pos.values()].sort((a, b) => a.t - b.t || a.id.localeCompare(b.id)).map((i) => i.id);

        const labels = el('div', { class: 'tl-lanes', style: 'width:' + LABEL_W + 'px;height:' + H + 'px', 'aria-hidden': 'true' },
          lanes.map((ln) => el('div', { class: 'tl-lane-label', style: 'top:' + ln.top + 'px;height:' + ln.h + 'px', title: ln.name, text: ln.name })));
        const prev = scroll.scrollLeft;
        scroll.replaceChildren(el('div', { class: 'tl-inner' }, labels, s));
        scroll.scrollLeft = prev;
        s.addEventListener('keydown', onKey);
        s.addEventListener('wheel', (ev) => {
          if (!(ev.ctrlKey || ev.metaKey)) return;
          ev.preventDefault();
          zoom(ev.deltaY < 0 ? 1.15 : 1 / 1.15);
        }, { passive: false });

        count.textContent = evs.length + ' events, ' + trs.length + ' traditions' + (evs.length + trs.length === 0 ? ' (nothing dated matches the filters)' : '');
        drawTable(evs);
        restyle();
        roving();
      }

      function drawTable(evs) {
        const rows = evs.slice().sort((a, b) => a.t - b.t || a.id.localeCompare(b.id));
        const names = (ids) => (ids || []).map((i) => (byId.get(i) || { name: i }).name).join(', ');
        tableWrap.replaceChildren(el('table', {},
          el('caption', { text: 'Events in date order' }),
          el('thead', {}, el('tr', {}, ['Date', 'Event', 'Type', 'Significance', 'Caused by', 'Leads to'].map((h) => el('th', { scope: 'col', text: h })))),
          el('tbody', {}, rows.map((e) => el('tr', {},
            el('td', { text: (byId.get(e.id) || {}).date_label || fmtT(e.t) }),
            el('th', { scope: 'row' }, el('button', { type: 'button', text: e.name, onclick: () => WB.select(e.id) })),
            el('td', { text: e.type || '' }), el('td', { text: e.significance || '' }),
            el('td', { text: names(e.caused_by) }), el('td', { text: names(e.leads_to) }))))));
      }

      function roving() {
        const sel = WB.state.selected && mk.has(WB.state.selected) ? WB.state.selected : order[0];
        mk.forEach((m, id) => m.g.setAttribute('tabindex', id === sel ? '0' : '-1'));
      }

      function restyle() {
        const f = WB.focus();
        const active = !!f.id || !!f.hl;
        mk.forEach((m, id) => {
          let cls = 'mk';
          if (f.id) {
            if (id === f.id) cls += ' sel';
            else if (f.up.has(id)) cls += ' up';
            else if (f.down.has(id)) cls += ' down';
            else cls += ' dim';
          }
          if (f.hl && f.hl.has(id)) cls = 'mk sel';
          else if (!f.id && f.hl) cls += ' dim';
          m.g.setAttribute('class', cls);
        });
        arcEls.forEach(({ p, e }) => {
          let cls = 'arc' + (e.memory ? ' memory' : '');
          let marker = e.memory ? 'mem' : 'n';
          if (f.id) {
            const s = e.source; const t = e.target;
            if ((s === f.id || f.up.has(s)) && (t === f.id || f.up.has(t))) { cls += ' up'; marker = 'up'; }
            else if ((s === f.id || f.down.has(s)) && (t === f.id || f.down.has(t))) { cls += ' down'; marker = 'down'; }
            else cls += ' dim';
          } else if (active) cls += ' dim';
          p.setAttribute('class', cls);
          p.setAttribute('marker-end', 'url(#tl-ah-' + marker + ')');
        });
      }

      function scrollTo(id) {
        const m = mk.get(id);
        if (!m) return;
        const x = m.item.x;
        const left = scroll.scrollLeft; const view = scroll.clientWidth - LABEL_W;
        if (x < left + 30 || x > left + view - 60) scroll.scrollLeft = Math.max(0, x - view / 2);
        const top = scroll.scrollTop;
        if (m.item.y < top + AXIS_H || m.item.y > top + scroll.clientHeight - 20) scroll.scrollTop = Math.max(0, m.item.y - scroll.clientHeight / 2);
      }

      function onKey(ev) {
        const cur = WB.state.selected && mk.has(WB.state.selected) ? WB.state.selected : null;
        let next = null;
        if (ev.key === 'ArrowRight' || ev.key === 'ArrowLeft') {
          const i = cur ? order.indexOf(cur) : -1;
          const j = ev.key === 'ArrowRight' ? Math.min(order.length - 1, i + 1) : Math.max(0, i - 1);
          next = order[i < 0 ? 0 : j];
        } else if ((ev.key === 'ArrowUp' || ev.key === 'ArrowDown') && cur) {
          const e = WB.edges.filter((x) => (x.causal || x.memory) && (ev.key === 'ArrowUp' ? x.target === cur : x.source === cur) && mk.has(ev.key === 'ArrowUp' ? x.source : x.target));
          if (e.length) next = ev.key === 'ArrowUp' ? e[0].source : e[0].target;
        } else if (ev.key === 'Home') next = order[0];
        else if (ev.key === 'End') next = order[order.length - 1];
        else return;
        ev.preventDefault();
        if (next) { WB.select(next); const m = mk.get(next); if (m) m.g.focus({ preventScroll: true }); }
      }

      this.onSelect = (id) => { restyle(); roving(); if (id) scrollTo(id); };
      this.onFilter = () => draw();
      this.activate = () => { if (Math.abs(scroll.clientWidth - LABEL_W - 24 - lastW) > 2 || !mk.size) draw(); restyle(); };
      this.resize = () => { if (!container.hidden && Math.abs(scroll.clientWidth - LABEL_W - 24 - lastW) > 2) draw(); };
      WB.bus.on('highlight', () => restyle());
      draw();
    },
  });
})();
