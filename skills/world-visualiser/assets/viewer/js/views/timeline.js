// timeline.js: Glowing SVG causal timeline with animated dash-flow arcs, era density minimap scrubber,
// milestone callouts, hover causal-chain spotlight, and rich floating hover cards.
(function () {
  'use strict';
  const { el, svg, byId, fmtT, lineage } = WB.util;
  const D = WB.data;
  const SIZE = { 'world-changing': 9.5, major: 7, moderate: 5.2, minor: 3.8 };
  const LABEL_W = 148;
  const ROW = 26;
  const AXIS_H = 54;
  const ERA_TINTS = ['#56B4E9', '#009E73', '#E69F00', '#CC79A7', '#0072B2', '#D55E00'];
  const trunc = (s, n) => (s && s.length > n ? s.slice(0, n - 1) + '…' : (s || ''));

  WB.registerView({
    id: 'timeline', title: 'Timeline', order: 20,
    create(container) {
      container.classList.add('tl');
      const cal = D.calendar;
      const events = D.timeline.events || [];
      const traditions = D.timeline.traditions || [];
      const opts = { lanes: 'type', zoom: 1 };
      const mk = new Map(); // id -> {g, item, laneIdx}
      let arcEls = []; // {p, flow, e}
      let laneLabelEls = []; // {el, idx, ids:Set}
      let order = []; // visible ids in chronological order
      let lastW = 0;
      let totalSvgW = 600;
      let hoverId = null;
      let hoverChain = null; // {id, up:Set, down:Set, mem:Set}
      let currentEvs = [];
      let currentTrs = [];

      // ---- toolbar
      const laneSel = el('select', { 'aria-label': 'Group lanes by' },
        el('option', { value: 'type', text: 'Lanes by event type' }),
        el('option', { value: 'location', text: 'Lanes by location' }));
      laneSel.addEventListener('change', () => { opts.lanes = laneSel.value; draw(); });

      const zoomReadout = el('span', { class: 'tl-zoom-readout', 'aria-live': 'polite', text: '100%' });
      const setZoom = (nextZoom, anchorRatio) => {
        const clamped = Math.min(60, Math.max(1, nextZoom));
        const viewW = Math.max(1, scroll.clientWidth - LABEL_W);
        const ratio = anchorRatio !== undefined
          ? anchorRatio
          : (scroll.scrollLeft + viewW * 0.5) / Math.max(1, totalSvgW);
        opts.zoom = clamped;
        zoomReadout.textContent = Math.round(opts.zoom * 100) + '%';
        draw();
        const targetLeft = ratio * totalSvgW - viewW * 0.5;
        scroll.scrollLeft = Math.max(0, Math.min(Math.max(0, totalSvgW - viewW), targetLeft));
        syncMinimap();
      };
      const zoom = (f) => setZoom(opts.zoom * f);

      const count = el('span', { class: 'muted', id: 'tl-count' });
      const legendPills = el('div', { class: 'tl-legend-pills', 'aria-hidden': 'true' },
        el('span', { class: 'tl-leg-pill' }, el('span', { class: 'tl-leg-swatch', style: 'background:#38bdf8' }), 'Upstream cause'),
        el('span', { class: 'tl-leg-pill' }, el('span', { class: 'tl-leg-swatch', style: 'background:#f59e0b' }), 'Downstream effect'),
        el('span', { class: 'tl-leg-pill' }, el('span', { class: 'tl-leg-swatch', style: 'background:#e879f9;border-top:1px dashed #e879f9' }), 'Memory trace'));

      const bar = el('div', { class: 'tl-bar' },
        laneSel,
        el('div', { class: 'tl-zoom-group' },
          el('button', { type: 'button', class: 'btn', 'aria-label': 'Zoom in', text: '+', onclick: () => zoom(1.5) }),
          zoomReadout,
          el('button', { type: 'button', class: 'btn', 'aria-label': 'Zoom out', text: '−', onclick: () => zoom(1 / 1.5) }),
          el('button', { type: 'button', class: 'btn', text: 'Fit', onclick: () => setZoom(1, 0) })),
        count,
        legendPills);

      const scroll = el('div', { class: 'tl-scroll' });
      const tip = el('div', { class: 'tl-tip', hidden: true, role: 'tooltip' });

      // ---- Era Density Scrubber / Minimap
      const miniRange = el('span', { text: '' });
      const miniSvg = svg('svg', { class: 'tl-mini-svg', preserveAspectRatio: 'none', 'aria-hidden': 'true' });
      const miniHandleL = el('div', { class: 'tl-mini-handle left', title: 'Drag to zoom left edge' });
      const miniHandleR = el('div', { class: 'tl-mini-handle right', title: 'Drag to zoom right edge' });
      const miniVp = el('div', {
        class: 'tl-mini-vp', role: 'slider', tabindex: '0',
        'aria-label': 'Timeline viewport scrubber', 'aria-valuemin': '0', 'aria-valuemax': '100', 'aria-valuenow': '0',
      }, miniHandleL, miniHandleR);
      const miniTrack = el('div', { class: 'tl-mini-track' }, miniSvg, miniVp);
      const minimap = el('div', { class: 'tl-minimap', role: 'region', 'aria-label': 'Era density minimap scrubber' },
        el('div', { class: 'tl-mini-head' },
          el('strong', { text: 'Era Density Scrubber' }),
          miniRange),
        miniTrack);

      const tableWrap = el('div', { class: 'sr-only' });
      container.append(bar, scroll, minimap, tip, tableWrap);

      const sizeOf = (ev) => SIZE[ev.significance] || 5.2;
      const nodeOf = (id) => byId.get(id);

      // Compute causal & memory chain for hover spotlight
      function computeChain(id) {
        if (!id) return null;
        const l = typeof lineage === 'function' ? lineage(id) : { up: new Set(), down: new Set() };
        const mem = new Set();
        WB.edges.forEach((e) => {
          if (!e.memory) return;
          if (e.source === id || l.up.has(e.source) || l.down.has(e.source)) mem.add(e.target);
          if (e.target === id) mem.add(e.source);
        });
        return { id, up: l.up, down: l.down, mem };
      }

      function showTip(id, clientX, clientY) {
        const n = nodeOf(id);
        if (!n) return;
        const ev = events.find((e) => e.id === id);
        const tr = traditions.find((t) => t.id === id);
        const chain = computeChain(id);
        const col = WB.colors.type[n.type] || '#888';
        const kindLabel = ev ? (ev.significance ? ev.significance + ' · ' : '') + (ev.type || 'event')
          : tr ? 'tradition · ' + (tr.kind || 'memory') : n.type;
        const dateStr = (n.date_label || fmtT(n.t)) + (n.era ? ' (' + n.era + ')' : '');

        const stats = [];
        if (chain) {
          if (chain.up.size) stats.push(el('span', { class: 'tl-tip-stat-up', text: '← ' + chain.up.size + ' upstream' }));
          if (chain.down.size) stats.push(el('span', { class: 'tl-tip-stat-down', text: chain.down.size + ' downstream →' }));
          if (chain.mem.size) stats.push(el('span', { class: 'tl-tip-stat-mem', text: '◆ ' + chain.mem.size + ' memory' }));
        }
        if (!stats.length) stats.push(el('span', { class: 'muted', text: 'Click to inspect details' }));

        tip.replaceChildren(
          el('div', { class: 'tl-tip-head' },
            el('span', { class: 'tl-tip-badge', style: 'border-color:' + col },
              el('span', { class: 'dot', style: 'background:' + col, 'aria-hidden': 'true' }),
              kindLabel),
            el('span', { class: 'tl-tip-date', text: dateStr })),
          el('div', { class: 'tl-tip-title', text: n.name }),
          n.summary ? el('p', { class: 'tl-tip-summary', text: trunc(n.summary, 130) }) : null,
          el('div', { class: 'tl-tip-stats' }, stats));

        const r = container.getBoundingClientRect();
        tip.hidden = false;
        const tw = tip.offsetWidth || 276;
        const th = tip.offsetHeight || 110;
        let left = clientX - r.left + 16;
        let top = clientY - r.top + 14;
        if (left + tw > r.width - 10) left = Math.max(8, clientX - r.left - tw - 14);
        if (top + th > r.height - 86) top = Math.max(46, clientY - r.top - th - 12);
        tip.style.left = left + 'px';
        tip.style.top = top + 'px';
      }

      function setHover(id, clientX, clientY) {
        if (hoverId !== id) {
          hoverId = id;
          hoverChain = id ? computeChain(id) : null;
          restyle();
        }
        if (id) showTip(id, clientX, clientY);
        else tip.hidden = true;
      }

      function tickStep(ppy) {
        const steps = [1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000, 2000, 5000];
        return steps.find((s) => s * ppy >= 86) || 5000;
      }

      // ---- Minimap rendering & dragging
      function drawMinimap(evs, trs) {
        const span = Math.max(1e-9, cal.t_max - cal.t_min);
        const MW = 600;
        const MH = 44;
        miniSvg.setAttribute('viewBox', '0 0 ' + MW + ' ' + MH);
        miniSvg.replaceChildren();

        const defs = svg('defs', {});
        const grad = svg('linearGradient', { id: 'tl-mini-area-grad', x1: '0', y1: '0', x2: '0', y2: '1' },
          svg('stop', { offset: '0%', 'stop-color': 'var(--accent)', 'stop-opacity': '0.55' }),
          svg('stop', { offset: '100%', 'stop-color': 'var(--accent)', 'stop-opacity': '0.04' }));
        defs.appendChild(grad);
        miniSvg.appendChild(defs);

        // Era backdrop strips
        (cal.eras || []).forEach((er, i) => {
          const x0 = ((er.t0 - cal.t_min) / span) * MW;
          const x1 = ((er.t1 - cal.t_min) / span) * MW;
          const tint = ERA_TINTS[i % ERA_TINTS.length];
          miniSvg.appendChild(svg('rect', {
            x: x0, y: 0, width: Math.max(1, x1 - x0), height: MH,
            fill: tint, 'fill-opacity': i % 2 ? 0.1 : 0.05,
          }));
          if (x1 - x0 > 26) {
            miniSvg.appendChild(svg('text', {
              x: x0 + 4, y: 11, fill: 'var(--muted)', 'font-size': '9', 'font-weight': '700',
            }, er.prefix || trunc(er.name, 8)));
          }
        });

        // Density sparkline across 60 bins
        const BINS = 60;
        const counts = new Array(BINS).fill(0);
        const allT = evs.map((e) => e.t).concat(trs.map((t) => t.first_attested_t));
        allT.forEach((t) => {
          const idx = Math.max(0, Math.min(BINS - 1, Math.floor(((t - cal.t_min) / span) * BINS)));
          counts[idx] += 1;
        });
        // Gentle 3-tap smoothing so sparkline feels organic
        const smooth = counts.map((v, i) => (counts[Math.max(0, i - 1)] * 0.25 + v * 0.5 + counts[Math.min(BINS - 1, i + 1)] * 0.25));
        const maxC = Math.max(1, ...smooth);
        const pts = smooth.map((v, i) => {
          const px = ((i + 0.5) / BINS) * MW;
          const py = MH - 4 - (v / maxC) * (MH - 16);
          return [px, py];
        });
        if (pts.length) {
          let lineD = 'M' + pts[0][0].toFixed(1) + ',' + pts[0][1].toFixed(1);
          for (let i = 1; i < pts.length; i++) {
            const prev = pts[i - 1];
            const cur = pts[i];
            const mx = ((prev[0] + cur[0]) / 2).toFixed(1);
            lineD += ' Q' + prev[0].toFixed(1) + ',' + prev[1].toFixed(1) + ' ' + mx + ',' + ((prev[1] + cur[1]) / 2).toFixed(1);
          }
          const last = pts[pts.length - 1];
          lineD += ' L' + last[0].toFixed(1) + ',' + last[1].toFixed(1);
          const areaD = lineD + ' L' + MW + ',' + MH + ' L0,' + MH + ' Z';
          miniSvg.appendChild(svg('path', { d: areaD, fill: 'url(#tl-mini-area-grad)' }));
          miniSvg.appendChild(svg('path', { d: lineD, fill: 'none', stroke: 'var(--accent)', 'stroke-width': '1.6' }));
        }

        // Milestone ticks
        evs.filter((e) => e.significance === 'world-changing').forEach((e) => {
          const mx = ((e.t - cal.t_min) / span) * MW;
          miniSvg.appendChild(svg('line', { x1: mx, x2: mx, y1: 12, y2: MH, stroke: '#f59e0b', 'stroke-width': '1.4', 'stroke-opacity': '0.75' }));
        });
        if (cal.present_t !== null && cal.present_t !== undefined) {
          const px = ((cal.present_t - cal.t_min) / span) * MW;
          miniSvg.appendChild(svg('line', { x1: px, x2: px, y1: 0, y2: MH, stroke: 'var(--focus)', 'stroke-width': '2' }));
        }
        syncMinimap();
      }

      function syncMinimap() {
        const viewW = Math.max(1, scroll.clientWidth - LABEL_W);
        const contentW = Math.max(viewW, totalSvgW);
        const leftFrac = Math.max(0, Math.min(1, scroll.scrollLeft / contentW));
        const widthFrac = Math.max(0.03, Math.min(1, viewW / contentW));
        miniVp.style.left = (leftFrac * 100).toFixed(2) + '%';
        miniVp.style.width = (Math.min(1 - leftFrac, widthFrac) * 100).toFixed(2) + '%';
        miniVp.setAttribute('aria-valuenow', String(Math.round(leftFrac * 100)));

        const span = Math.max(1e-9, cal.t_max - cal.t_min);
        const t0 = cal.t_min + leftFrac * span;
        const t1 = cal.t_min + Math.min(1, leftFrac + widthFrac) * span;
        miniRange.textContent = fmtT(t0) + ' — ' + fmtT(t1);
      }

      // Minimap drag / resize / click-to-pan
      let miniDrag = null;
      miniTrack.addEventListener('pointerdown', (ev) => {
        const rect = miniTrack.getBoundingClientRect();
        if (!rect.width) return;
        const viewW = Math.max(1, scroll.clientWidth - LABEL_W);
        const contentW = Math.max(viewW, totalSvgW);
        const startLeft = scroll.scrollLeft / contentW;
        const startWidth = Math.min(1, viewW / contentW);

        if (ev.target === miniHandleL || ev.target === miniHandleR) {
          ev.stopPropagation();
          miniDrag = { mode: ev.target === miniHandleL ? 'left' : 'right', x0: ev.clientX, rect, startLeft, startWidth };
        } else if (ev.target === miniVp) {
          miniDrag = { mode: 'move', x0: ev.clientX, rect, startLeft, startWidth };
        } else {
          // Click on track: centre viewport here
          const clickFrac = Math.max(0, Math.min(1, (ev.clientX - rect.left) / rect.width));
          const targetFrac = Math.max(0, Math.min(1 - startWidth, clickFrac - startWidth / 2));
          scroll.scrollLeft = targetFrac * contentW;
          syncMinimap();
          miniDrag = { mode: 'move', x0: ev.clientX, rect, startLeft: targetFrac, startWidth };
        }
        if (miniTrack.setPointerCapture) {
          try { miniTrack.setPointerCapture(ev.pointerId); } catch (e) { /* ignore */ }
        }
      });
      miniTrack.addEventListener('pointermove', (ev) => {
        if (!miniDrag) return;
        const dxFrac = (ev.clientX - miniDrag.x0) / Math.max(1, miniDrag.rect.width);
        const viewW = Math.max(1, scroll.clientWidth - LABEL_W);
        if (miniDrag.mode === 'move') {
          const contentW = Math.max(viewW, totalSvgW);
          const nextLeft = Math.max(0, Math.min(1 - miniDrag.startWidth, miniDrag.startLeft + dxFrac));
          scroll.scrollLeft = nextLeft * contentW;
          syncMinimap();
        } else {
          const minW = 1 / 60;
          let nextL = miniDrag.startLeft;
          let nextR = miniDrag.startLeft + miniDrag.startWidth;
          if (miniDrag.mode === 'left') nextL = Math.max(0, Math.min(nextR - minW, miniDrag.startLeft + dxFrac));
          else nextR = Math.min(1, Math.max(nextL + minW, miniDrag.startLeft + miniDrag.startWidth + dxFrac));
          const nextWidth = Math.max(minW, nextR - nextL);
          const nextZoom = Math.min(60, Math.max(1, 1 / nextWidth));
          opts.zoom = nextZoom;
          zoomReadout.textContent = Math.round(opts.zoom * 100) + '%';
          draw();
          scroll.scrollLeft = nextL * totalSvgW;
          syncMinimap();
        }
      });
      const endMiniDrag = () => { miniDrag = null; };
      miniTrack.addEventListener('pointerup', endMiniDrag);
      miniTrack.addEventListener('pointercancel', endMiniDrag);
      miniVp.addEventListener('keydown', (ev) => {
        const step = Math.max(40, (scroll.clientWidth - LABEL_W) * 0.2);
        if (ev.key === 'ArrowLeft') { ev.preventDefault(); scroll.scrollLeft = Math.max(0, scroll.scrollLeft - step); syncMinimap(); }
        else if (ev.key === 'ArrowRight') { ev.preventDefault(); scroll.scrollLeft += step; syncMinimap(); }
        else if (ev.key === '+' || ev.key === '=') { ev.preventDefault(); zoom(1.3); }
        else if (ev.key === '-') { ev.preventDefault(); zoom(1 / 1.3); }
      });

      scroll.addEventListener('scroll', syncMinimap, { passive: true });

      function draw() {
        const avail = Math.max(320, scroll.clientWidth - LABEL_W - 24);
        const span = Math.max(1e-9, cal.t_max - cal.t_min);
        const ppy = (avail / span) * opts.zoom;
        const W = Math.ceil(span * ppy) + 80;
        totalSvgW = W;
        lastW = avail;
        const X = (t) => (t - cal.t_min) * ppy + 28;

        const evs = events.filter((e) => e.t !== null && e.t !== undefined && WB.passes(nodeOf(e.id)));
        const trs = traditions.filter((t) => t.first_attested_t !== null && t.first_attested_t !== undefined && WB.passes(nodeOf(t.id)));
        currentEvs = evs;
        currentTrs = trs;

        const laneKey = (e) => {
          if (opts.lanes === 'location') {
            const loc = (e.locations || []).find((l) => byId.has(l));
            return loc ? byId.get(loc).name : '(no location)';
          }
          return e.type || 'other';
        };
        const laneMap = new Map();
        evs.forEach((e) => {
          const k = laneKey(e);
          if (!laneMap.has(k)) laneMap.set(k, []);
          laneMap.get(k).push(e);
        });
        const laneNames = [...laneMap.keys()].sort((a, b) => (/^\(|^other$/.test(a) ? 1 : 0) - (/^\(|^other$/.test(b) ? 1 : 0) || a.localeCompare(b));
        const lanes = laneNames.map((k) => ({
          name: k,
          isTrad: false,
          items: laneMap.get(k).map((e) => ({
            id: e.id, name: e.name, t: e.t, end: e.end_t, r: sizeOf(e),
            kind: 'event', ev: e, milestone: e.significance === 'world-changing',
          })),
        }));
        if (trs.length) {
          lanes.push({
            name: 'traditions (memory)',
            isTrad: true,
            items: trs.map((t) => ({
              id: t.id, name: t.name, t: t.first_attested_t, end: null, r: 6.5,
              kind: 'tradition', ev: null, milestone: false,
            })),
          });
        }

        // Pack each lane into non-overlapping rows
        let y = AXIS_H;
        lanes.forEach((ln) => {
          ln.items.sort((a, b) => a.t - b.t || a.id.localeCompare(b.id));
          const rowsEnd = [];
          ln.items.forEach((it) => {
            it.x = X(it.t);
            const label = trunc(it.name, it.milestone ? 30 : 25);
            it.label = label;
            const w = it.r * 2 + 12 + label.length * (it.milestone ? 6.4 : 5.8);
            let r = rowsEnd.findIndex((end) => it.x - it.r > end + 8);
            if (r < 0) { r = rowsEnd.length; rowsEnd.push(0); }
            rowsEnd[r] = it.x - it.r + w;
            it.row = r;
          });
          ln.top = y;
          ln.h = Math.max(1, rowsEnd.length) * ROW + 18;
          ln.items.forEach((it) => { it.y = ln.top + 12 + it.row * ROW + ROW / 2; });
          y += ln.h;
        });
        const H = Math.max(y + 18, 200);

        const s = svg('svg', {
          class: 'tl-svg', width: W, height: H,
          role: 'group', 'aria-label': 'Timeline of events and traditions',
          viewBox: '0 0 ' + W + ' ' + H,
        });

        // Defs: glow filters, era gradients, arrowheads
        const defs = svg('defs', {});
        const addGlow = (id, std) => {
          const fl = svg('filter', { id, x: '-25%', y: '-25%', width: '150%', height: '150%' },
            svg('feGaussianBlur', { stdDeviation: std, result: 'blur' }),
            svg('feMerge', {},
              svg('feMergeNode', { in: 'blur' }),
              svg('feMergeNode', { in: 'SourceGraphic' })));
          defs.appendChild(fl);
        };
        addGlow('tl-glow-up', '2.6');
        addGlow('tl-glow-down', '2.6');
        addGlow('tl-glow-mem', '2.2');
        addGlow('tl-glow-present', '3.2');

        [['n', 'var(--muted)'], ['up', '#38bdf8'], ['down', '#f59e0b'], ['mem', '#E7298A'], ['mem-lit', '#e879f9']].forEach(([k, c]) => {
          defs.appendChild(svg('marker', {
            id: 'tl-ah-' + k, viewBox: '0 0 8 8', refX: 7, refY: 4, markerWidth: 6.5, markerHeight: 6.5, orient: 'auto',
          }, svg('path', { d: 'M0,1 L8,4 L0,7 z', fill: c })));
        });

        (cal.eras || []).forEach((er, i) => {
          const tint = ERA_TINTS[i % ERA_TINTS.length];
          defs.appendChild(svg('linearGradient', { id: 'tl-era-grad-' + i, x1: '0', y1: '0', x2: '0', y2: '1' },
            svg('stop', { offset: '0%', 'stop-color': tint, 'stop-opacity': i % 2 ? '0.11' : '0.06' }),
            svg('stop', { offset: '35%', 'stop-color': tint, 'stop-opacity': i % 2 ? '0.04' : '0.02' }),
            svg('stop', { offset: '100%', 'stop-color': tint, 'stop-opacity': '0.01' })));
        });
        s.appendChild(defs);

        // Era backdrop bands & header banners
        (cal.eras || []).forEach((er, i) => {
          const x0 = X(er.t0);
          const x1 = X(er.t1);
          const bw = Math.max(0, x1 - x0);
          const eraCount = evs.filter((e) => e.t >= er.t0 && e.t <= er.t1).length;
          s.appendChild(svg('rect', { x: x0, y: 0, width: bw, height: H, fill: 'url(#tl-era-grad-' + i + ')' }));
          s.appendChild(svg('rect', { class: 'era-band-header', x: x0, y: 0, width: bw, height: 24 }));
          s.appendChild(svg('rect', { x: x0, y: 0, width: bw, height: 2.5, fill: ERA_TINTS[i % ERA_TINTS.length], 'fill-opacity': '0.8' }));
          if (i > 0) s.appendChild(svg('line', { class: 'era-divider', x1: x0, x2: x0, y1: 0, y2: H }));
          if (bw > 44) {
            s.appendChild(svg('text', { class: 'era-name', x: x0 + 8, y: 16 }, er.name + ' (' + er.prefix + ')'));
          }
          if (bw > 170) {
            s.appendChild(svg('text', { class: 'era-sub', x: x1 - 8, y: 16, 'text-anchor': 'end' }, eraCount + ' events'));
          }
        });

        // Date ticks
        const step = tickStep(ppy);
        for (let t = Math.ceil(cal.t_min / step) * step; t <= cal.t_max; t += step) {
          const x = X(t);
          s.appendChild(svg('line', { class: 'tick', x1: x, x2: x, y1: 24, y2: H }));
          s.appendChild(svg('text', { class: 'tick-label', x: x + 4, y: 42 }, fmtT(t)));
        }

        // Lane separators
        lanes.forEach((ln) => s.appendChild(svg('line', { class: 'lane-sep', x1: 0, x2: W, y1: ln.top, y2: ln.top })));

        // Present-date glowing laser line
        if (cal.present_t !== null && cal.present_t !== undefined) {
          const px = X(cal.present_t);
          s.appendChild(svg('line', { class: 'present-glow', x1: px, x2: px, y1: 24, y2: H }));
          s.appendChild(svg('line', { class: 'present', x1: px, x2: px, y1: 24, y2: H }));
          s.appendChild(svg('rect', { class: 'present-pill', x: px - 28, y: 26, width: 56, height: 15, rx: 7.5 }));
          s.appendChild(svg('text', { class: 'present-label', x: px, y: 37, 'text-anchor': 'middle' }, 'PRESENT'));
        }

        // Positions & smooth cubic Bézier causal/memory arcs + animated flow overlays
        mk.clear();
        const pos = new Map();
        lanes.forEach((ln, idx) => ln.items.forEach((it) => { it.laneIdx = idx; pos.set(it.id, it); }));
        const arcLayer = svg('g', { 'data-layer': 'arcs' });
        s.appendChild(arcLayer);
        arcEls = [];
        WB.edges.forEach((e) => {
          if (!(e.causal || e.memory)) return;
          const a = pos.get(e.source);
          const b = pos.get(e.target);
          if (!a || !b) return;
          const dx = b.x - a.x;
          const absDx = Math.abs(dx);
          const dir = Math.sign(dx || 1);
          const endX = b.x - dir * (b.r + 4);
          const lift = Math.min(110, 18 + absDx * 0.22);
          const cy = Math.max(AXIS_H - 8, Math.min(a.y, b.y) - lift);
          const c1x = a.x + (endX - a.x) * 0.28;
          const c2x = a.x + (endX - a.x) * 0.72;
          const d = 'M' + a.x.toFixed(1) + ',' + a.y.toFixed(1) +
            ' C' + c1x.toFixed(1) + ',' + cy.toFixed(1) + ' ' +
            c2x.toFixed(1) + ',' + cy.toFixed(1) + ' ' +
            endX.toFixed(1) + ',' + b.y.toFixed(1);
          const p = svg('path', {
            class: 'arc' + (e.memory ? ' memory' : ''),
            d,
            'marker-end': 'url(#tl-ah-' + (e.memory ? 'mem' : 'n') + ')',
          });
          const flow = svg('path', {
            class: 'arc-flow' + (e.memory ? ' memory' : ''),
            d,
          });
          arcLayer.appendChild(p);
          arcLayer.appendChild(flow);
          arcEls.push({ p, flow, e });
        });

        // Markers
        const mkLayer = svg('g', { 'data-layer': 'markers' });
        s.appendChild(mkLayer);
        lanes.forEach((ln) => ln.items.forEach((it) => {
          const col = WB.colors.type[it.kind] || '#D55E00';
          const g = svg('g', {
            class: 'mk' + (it.milestone ? ' milestone' : ''),
            tabindex: '-1', role: 'button', 'data-id': it.id,
            'aria-label': it.name + ', ' + ((byId.get(it.id) || {}).date_label || fmtT(it.t)) + ', ' + it.kind + (it.milestone ? ', world-changing milestone' : ''),
          });
          if (it.end !== null && it.end !== undefined && it.end > it.t) {
            g.appendChild(svg('rect', {
              class: 'dur', x: it.x, y: it.y - 3,
              width: Math.max(3, (it.end - it.t) * ppy), height: 6, rx: 3, fill: col,
            }));
          }
          if (it.milestone) {
            g.appendChild(svg('circle', { class: 'milestone-beacon', cx: it.x, cy: it.y, r: it.r + 5 }));
            g.appendChild(svg('circle', { class: 'milestone-ring', cx: it.x, cy: it.y, r: it.r + 3 }));
            const pillW = Math.max(44, it.label.length * 6.5 + 12);
            g.appendChild(svg('rect', {
              class: 'milestone-pill', x: it.x + it.r + 4, y: it.y - 9, width: pillW, height: 18, rx: 9,
            }));
          }
          if (it.kind === 'tradition') {
            const side = (it.r - 0.8) * 2;
            g.appendChild(svg('rect', {
              class: 'shape', x: it.x - side / 2, y: it.y - side / 2, width: side, height: side,
              rx: 1.5, transform: 'rotate(45 ' + it.x + ' ' + it.y + ')', fill: col,
            }));
          } else {
            g.appendChild(svg('circle', { class: 'shape', cx: it.x, cy: it.y, r: it.r, fill: col }));
          }
          g.appendChild(svg('text', { x: it.x + it.r + (it.milestone ? 10 : 5), y: it.y + 4 }, it.label));
          g.addEventListener('click', () => WB.select(it.id));
          g.addEventListener('keydown', (ev) => { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); WB.select(it.id); } });
          g.addEventListener('mouseenter', (ev) => setHover(it.id, ev.clientX, ev.clientY));
          g.addEventListener('mousemove', (ev) => { if (hoverId === it.id) showTip(it.id, ev.clientX, ev.clientY); });
          g.addEventListener('mouseleave', () => setHover(null));
          g.addEventListener('focus', () => {
            const br = g.getBoundingClientRect();
            setHover(it.id, br.left, br.bottom);
          });
          g.addEventListener('blur', () => setHover(null));
          mkLayer.appendChild(g);
          mk.set(it.id, { g, item: it, laneIdx: it.laneIdx });
        }));
        order = [...pos.values()].sort((a, b) => a.t - b.t || a.id.localeCompare(b.id)).map((i) => i.id);

        laneLabelEls = [];
        const laneNodes = lanes.map((ln, idx) => {
          const rowEl = el('div', {
            class: 'tl-lane-label' + (ln.isTrad ? ' tl-lane-trad' : ''),
            style: 'top:' + ln.top + 'px;height:' + ln.h + 'px',
            title: ln.name + ' (' + ln.items.length + ')',
          },
            el('span', { text: ln.name }),
            el('span', { class: 'tl-lane-cnt', text: String(ln.items.length) }));
          laneLabelEls.push({ el: rowEl, idx, ids: new Set(ln.items.map((i) => i.id)) });
          return rowEl;
        });
        const labels = el('div', {
          class: 'tl-lanes',
          style: 'width:' + LABEL_W + 'px;height:' + H + 'px',
          'aria-hidden': 'true',
        },
          el('div', { class: 'tl-lane-header', style: 'height:' + AXIS_H + 'px', text: opts.lanes === 'location' ? 'Location' : 'Event Lane' }),
          laneNodes);

        const prev = scroll.scrollLeft;
        scroll.replaceChildren(el('div', { class: 'tl-inner' }, labels, s));
        scroll.scrollLeft = prev;
        s.addEventListener('keydown', onKey);
        s.addEventListener('wheel', (ev) => {
          if (!(ev.ctrlKey || ev.metaKey)) return;
          ev.preventDefault();
          const rect = scroll.getBoundingClientRect();
          const anchor = (scroll.scrollLeft + (ev.clientX - rect.left - LABEL_W)) / Math.max(1, totalSvgW);
          setZoom(opts.zoom * (ev.deltaY < 0 ? 1.18 : 1 / 1.18), Math.max(0, Math.min(1, anchor)));
        }, { passive: false });

        count.textContent = evs.length + ' events · ' + trs.length + ' traditions' + (evs.length + trs.length === 0 ? ' (nothing dated matches the filters)' : '');
        drawMinimap(evs, trs);
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
            el('td', { text: e.type || '' }),
            el('td', { text: e.significance || '' }),
            el('td', { text: names(e.caused_by) }),
            el('td', { text: names(e.leads_to) }))))));
      }

      function roving() {
        const sel = WB.state.selected && mk.has(WB.state.selected) ? WB.state.selected : order[0];
        mk.forEach((m, id) => m.g.setAttribute('tabindex', id === sel ? '0' : '-1'));
      }

      function restyle() {
        const wbFocus = WB.focus();
        // Hover spotlight takes priority while hovering; otherwise selected entity or highlight
        const activeChain = hoverChain || (wbFocus.id ? { id: wbFocus.id, up: wbFocus.up, down: wbFocus.down, mem: new Set() } : null);
        const hl = !hoverChain && wbFocus.hl ? wbFocus.hl : null;
        const hasFocus = !!activeChain || !!hl;
        const litIds = new Set();

        mk.forEach((m, id) => {
          let cls = 'mk' + (m.item.milestone ? ' milestone' : '');
          if (activeChain) {
            if (id === activeChain.id) { cls += ' sel'; litIds.add(id); }
            else if (activeChain.up.has(id)) { cls += ' up'; litIds.add(id); }
            else if (activeChain.down.has(id)) { cls += ' down'; litIds.add(id); }
            else if (activeChain.mem && activeChain.mem.has(id)) { cls += ' mem-lit'; litIds.add(id); }
            else cls += ' dim';
          } else if (hl) {
            if (hl.has(id)) { cls += ' sel'; litIds.add(id); }
            else cls += ' dim';
          }
          m.g.setAttribute('class', cls);
        });

        arcEls.forEach(({ p, flow, e }) => {
          let cls = 'arc' + (e.memory ? ' memory' : '');
          let fcls = 'arc-flow' + (e.memory ? ' memory' : '');
          let marker = e.memory ? 'mem' : 'n';
          if (activeChain) {
            const s = e.source;
            const t = e.target;
            const inUp = (s === activeChain.id || activeChain.up.has(s)) && (t === activeChain.id || activeChain.up.has(t));
            const inDown = (s === activeChain.id || activeChain.down.has(s)) && (t === activeChain.id || activeChain.down.has(t));
            const isMemHit = e.memory && (s === activeChain.id || t === activeChain.id || activeChain.up.has(s) || activeChain.down.has(s));
            if (isMemHit) { cls += ' mem-lit'; fcls += ' mem-lit'; marker = 'mem-lit'; }
            else if (inUp) { cls += ' up'; fcls += ' up'; marker = 'up'; }
            else if (inDown) { cls += ' down'; fcls += ' down'; marker = 'down'; }
            else { cls += ' dim'; fcls += ' dim'; }
          } else if (hasFocus) {
            cls += ' dim';
            fcls += ' dim';
          }
          p.setAttribute('class', cls);
          p.setAttribute('marker-end', 'url(#tl-ah-' + marker + ')');
          flow.setAttribute('class', fcls);
        });

        laneLabelEls.forEach(({ el: rowEl, ids }) => {
          if (!hasFocus) {
            rowEl.classList.remove('tl-lane-dim', 'tl-lane-lit');
            return;
          }
          let hit = false;
          ids.forEach((id) => { if (litIds.has(id)) hit = true; });
          rowEl.classList.toggle('tl-lane-lit', hit);
          rowEl.classList.toggle('tl-lane-dim', !hit);
        });
      }

      function scrollTo(id) {
        const m = mk.get(id);
        if (!m) return;
        const x = m.item.x;
        const left = scroll.scrollLeft;
        const view = scroll.clientWidth - LABEL_W;
        if (x < left + 40 || x > left + view - 70) scroll.scrollLeft = Math.max(0, x - view / 2);
        const top = scroll.scrollTop;
        if (m.item.y < top + AXIS_H || m.item.y > top + scroll.clientHeight - 24) scroll.scrollTop = Math.max(0, m.item.y - scroll.clientHeight / 2);
        syncMinimap();
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
      this.activate = () => {
        if (Math.abs(scroll.clientWidth - LABEL_W - 24 - lastW) > 2 || !mk.size) draw();
        else drawMinimap(currentEvs, currentTrs);
        restyle();
      };
      this.resize = () => {
        if (!container.hidden && Math.abs(scroll.clientWidth - LABEL_W - 24 - lastW) > 2) draw();
        else if (!container.hidden) syncMinimap();
      };
      WB.bus.on('highlight', () => restyle());
      draw();
    },
  });
})();
