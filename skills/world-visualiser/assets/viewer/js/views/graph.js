// graph.js: 3D force-directed graph of the causal (truth) and memory (tradition) chains. three.js r158 global.
(function () {
  'use strict';
  const { el, byId } = WB.util;
  const D = WB.data;

  const SHAPES = {
    event: 'sphere', tradition: 'octa', location: 'box', faction: 'tetra', character: 'dodeca',
    item: 'cyl', arc: 'icosa', 'magic-system': 'octa', species: 'cyl', race: 'cyl', language: 'dodeca', lineage: 'dodeca',
  };

  function rng(seed) { // mulberry32
    let a = seed >>> 0;
    return function () {
      a = (a + 0x6D2B79F5) >>> 0;
      let t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  // Deterministic force layout. Returns Float32Array of x,y,z per node (same order as `nodes`).
  function layout(nodes, links, pinned) {
    const n = nodes.length;
    const pos = new Float32Array(n * 3);
    if (!n) return pos;
    const idx = new Map(nodes.map((nd, i) => [nd.id, i]));
    const rand = rng(20240607);
    const k = 18;
    const R = k * Math.cbrt(n) * 1.2;
    const span = Math.max(240, k * Math.sqrt(n) * 3);
    const fixedX = new Array(n).fill(null);
    for (let i = 0; i < n; i++) {
      pos[i * 3] = (rand() - 0.5) * R * 2; pos[i * 3 + 1] = (rand() - 0.5) * R * 2; pos[i * 3 + 2] = (rand() - 0.5) * R * 2;
      if (pinned && nodes[i].t !== null && nodes[i].t !== undefined) {
        fixedX[i] = (WB.util.tToX(nodes[i].t, 1) - 0.5) * span;
        pos[i * 3] = fixedX[i];
      }
    }
    const L = links.map((e) => [idx.get(e.source), idx.get(e.target), e.causal || e.memory ? 1 : 0.35])
      .filter((l) => l[0] !== undefined && l[1] !== undefined && l[0] !== l[1]);
    const iters = n <= 300 ? 300 : n <= 600 ? 180 : 100;
    const disp = new Float32Array(n * 3);
    for (let it = 0; it < iters; it++) {
      const temp = k * (1 - it / iters) + 0.4;
      disp.fill(0);
      for (let i = 0; i < n; i++) {
        for (let j = i + 1; j < n; j++) {
          let dx = pos[i * 3] - pos[j * 3]; let dy = pos[i * 3 + 1] - pos[j * 3 + 1]; let dz = pos[i * 3 + 2] - pos[j * 3 + 2];
          let d2 = dx * dx + dy * dy + dz * dz;
          if (d2 < 0.01) { dx = rand() - 0.5; dy = rand() - 0.5; dz = rand() - 0.5; d2 = 0.5; }
          const f = (k * k) / d2; // repulsion magnitude per unit distance
          disp[i * 3] += dx * f; disp[i * 3 + 1] += dy * f; disp[i * 3 + 2] += dz * f;
          disp[j * 3] -= dx * f; disp[j * 3 + 1] -= dy * f; disp[j * 3 + 2] -= dz * f;
        }
      }
      for (const [a, b, w] of L) {
        const dx = pos[a * 3] - pos[b * 3]; const dy = pos[a * 3 + 1] - pos[b * 3 + 1]; const dz = pos[a * 3 + 2] - pos[b * 3 + 2];
        const d = Math.sqrt(dx * dx + dy * dy + dz * dz) + 0.01;
        const f = (d / k) * w;
        disp[a * 3] -= dx * f; disp[a * 3 + 1] -= dy * f; disp[a * 3 + 2] -= dz * f;
        disp[b * 3] += dx * f; disp[b * 3 + 1] += dy * f; disp[b * 3 + 2] += dz * f;
      }
      for (let i = 0; i < n; i++) {
        for (let c = 0; c < 3; c++) disp[i * 3 + c] -= pos[i * 3 + c] * 0.04; // gravity
        if (fixedX[i] !== null) disp[i * 3] = 0;
        const m = Math.sqrt(disp[i * 3] ** 2 + disp[i * 3 + 1] ** 2 + disp[i * 3 + 2] ** 2) + 1e-6;
        const s = Math.min(m, temp) / m;
        for (let c = 0; c < 3; c++) pos[i * 3 + c] += disp[i * 3 + c] * s;
      }
    }
    return pos;
  }

  WB.registerView({
    id: 'graph', title: 'Causal graph', order: 10,
    create(container) {
      container.classList.add('gv');
      const opts = { scope: 'chain', edges: 'causal', traditions: true, pin: false };
      const mkSel = (key, items) => {
        const s = el('select', { 'aria-label': key }, items.map(([v, t]) => el('option', { value: v, text: t })));
        s.value = opts[key];
        s.addEventListener('change', () => { opts[key] = s.value; relayout(); });
        return s;
      };
      const mkChk = (key, text) => {
        const c = el('input', { type: 'checkbox' });
        c.checked = opts[key];
        c.addEventListener('change', () => { opts[key] = c.checked; relayout(); });
        return el('label', {}, c, text);
      };
      const bar = el('div', { class: 'gv-bar' },
        el('label', {}, 'Nodes ', mkSel('scope', [['chain', 'Causal chain (events)'], ['all', 'All entities']])),
        el('label', {}, 'Edges ', mkSel('edges', [['causal', 'Causal only'], ['all', 'All kinds']])),
        mkChk('traditions', 'Show traditions'), mkChk('pin', 'Pin time axis (x = date)'),
        el('button', { type: 'button', class: 'btn', text: 'Reset layout', onclick: () => { relayout(); fit(); } }),
        el('button', { type: 'button', class: 'btn', text: 'Reset camera', onclick: () => fit() }),
        el('span', { class: 'muted', id: 'gv-count' }));
      const stage = el('div', { class: 'gv-stage', tabindex: '0', role: 'application',
        'aria-label': '3D causal graph. Arrow keys rotate, plus and minus zoom, 0 resets. Use the entity list or timeline for keyboard selection.' });
      container.append(bar, stage);
      const count = bar.querySelector('#gv-count');

      if (typeof window.THREE === 'undefined') {
        stage.replaceChildren(el('p', { class: 'view-msg', text: 'The 3D graph needs three.js, which could not load (needs internet). Use the entity list and the timeline instead.' }));
        return;
      }
      const T = window.THREE;
      let renderer;
      try {
        renderer = new T.WebGLRenderer({ antialias: true });
      } catch (e) {
        stage.replaceChildren(el('p', { class: 'view-msg', text: 'WebGL is not available in this browser, so the 3D graph cannot be drawn: ' + e.message }));
        return;
      }
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
      stage.appendChild(renderer.domElement);
      const labelBox = el('div', { class: 'gv-labels' });
      const tip = el('div', { class: 'gv-tip', hidden: true });
      const legend = el('div', { class: 'gv-legend' });
      stage.append(labelBox, tip, legend);
      const scene = new T.Scene();
      const camera = new T.PerspectiveCamera(50, 1, 0.5, 5000);
      const cam = { theta: 0.6, phi: 1.2, dist: 300, target: new T.Vector3() };
      let bg = new T.Color('#14161a');
      let nodeObjs = []; // {node, mesh, r}
      let pickables = [];
      let posOf = new Map();
      let edgeGroup = new T.Group();
      scene.add(edgeGroup);
      let edgeData = [];
      let arrows = null;
      let dirty = true;
      let hover = null;
      const layoutCache = new Map();
      const geoms = {
        sphere: new T.SphereGeometry(1, 16, 12), octa: new T.OctahedronGeometry(1.25), box: new T.BoxGeometry(1.6, 1.6, 1.6),
        tetra: new T.TetrahedronGeometry(1.4), dodeca: new T.DodecahedronGeometry(1.15), cyl: new T.CylinderGeometry(1, 1, 1.5, 12),
        icosa: new T.IcosahedronGeometry(1.1, 0),
      };
      const cone = new T.ConeGeometry(1, 2.6, 8);

      function themeBg() {
        const v = getComputedStyle(document.documentElement).getPropertyValue('--bg').trim() || '#14161a';
        bg = new T.Color(v);
        renderer.setClearColor(bg, 1);
      }
      themeBg();
      const mq = window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : null;
      if (mq && mq.addEventListener) mq.addEventListener('change', () => { themeBg(); restyle(); });

      const visibleNodeSet = () => {
        const set = [];
        D.nodes.forEach((n) => {
          if (opts.scope === 'all') set.push(n);
          else if (n.type === 'event' || (opts.traditions && n.type === 'tradition')) set.push(n);
        });
        return set.filter((n) => opts.traditions || n.type !== 'tradition');
      };
      const edgeVisible = (e) => {
        if (e.causal) return true;
        if (e.memory) return opts.traditions;
        return opts.edges === 'all';
      };

      function relayout() {
        const nodes = visibleNodeSet();
        const ids = new Set(nodes.map((n) => n.id));
        const links = WB.edges.filter((e) => ids.has(e.source) && ids.has(e.target) && edgeVisible(e));
        const key = [opts.scope, opts.edges, opts.traditions, opts.pin].join('|');
        let pos = layoutCache.get(key);
        if (!pos) { pos = layout(nodes, links, opts.pin); layoutCache.set(key, pos); }
        // dispose old
        nodeObjs.forEach((o) => { scene.remove(o.mesh); o.mesh.material.dispose(); });
        nodeObjs = []; pickables = []; posOf = new Map();
        nodes.forEach((n, i) => {
          const r = Math.min(5, 1.4 + 0.5 * Math.sqrt(WB.degree(n.id)));
          const mesh = new T.Mesh(geoms[SHAPES[n.type] || 'sphere'], new T.MeshBasicMaterial({ color: 0xffffff }));
          mesh.scale.setScalar(r);
          mesh.position.set(pos[i * 3], pos[i * 3 + 1], pos[i * 3 + 2]);
          mesh.userData.id = n.id;
          scene.add(mesh);
          nodeObjs.push({ node: n, mesh, r });
          pickables.push(mesh);
          posOf.set(n.id, mesh.position);
        });
        count.textContent = nodes.length + ' nodes';
        applyVisibility();
        fit();
      }

      const shown = (n) => WB.passes(n);
      function applyVisibility() {
        nodeObjs.forEach((o) => { o.mesh.visible = shown(o.node); });
        buildEdges();
        restyle();
      }

      function buildEdges() {
        edgeGroup.children.slice().forEach((c) => { edgeGroup.remove(c); c.geometry.dispose(); c.material.dispose(); });
        edgeData = WB.edges.filter((e) => edgeVisible(e) && posOf.has(e.source) && posOf.has(e.target)
          && shown(byId.get(e.source)) && shown(byId.get(e.target)));
        const groups = { solid: [], memory: [] };
        edgeData.forEach((e) => (e.memory ? groups.memory : groups.solid).push(e));
        const make = (list, dashed) => {
          const g = new T.BufferGeometry();
          g.setAttribute('position', new T.BufferAttribute(new Float32Array(list.length * 6), 3));
          g.setAttribute('color', new T.BufferAttribute(new Float32Array(list.length * 6), 3));
          list.forEach((e, i) => {
            const a = posOf.get(e.source); const b = posOf.get(e.target);
            const p = g.attributes.position.array;
            p.set([a.x, a.y, a.z, b.x, b.y, b.z], i * 6);
          });
          const m = dashed ? new T.LineDashedMaterial({ vertexColors: true, dashSize: 2.5, gapSize: 2 }) : new T.LineBasicMaterial({ vertexColors: true });
          const lines = new T.LineSegments(g, m);
          if (dashed) lines.computeLineDistances();
          lines.userData.list = list;
          edgeGroup.add(lines);
        };
        make(groups.solid, false);
        make(groups.memory, true);
        // arrowheads on causal edges
        const causal = edgeData.filter((e) => e.causal);
        if (arrows) { scene.remove(arrows); arrows.material.dispose(); }
        arrows = new T.InstancedMesh(cone, new T.MeshBasicMaterial({ color: 0xffffff }), Math.max(1, causal.length));
        arrows.count = causal.length;
        arrows.userData.list = causal;
        const up = new T.Vector3(0, 1, 0);
        const m4 = new T.Matrix4(); const q = new T.Quaternion(); const dir = new T.Vector3(); const pt = new T.Vector3();
        const sc = new T.Vector3(0.9, 0.9, 0.9);
        causal.forEach((e, i) => {
          const a = posOf.get(e.source); const b = posOf.get(e.target);
          const rb = nodeObjs.find((o) => o.node.id === e.target);
          dir.subVectors(b, a); const len = dir.length() || 1; dir.divideScalar(len);
          pt.copy(b).addScaledVector(dir, -((rb ? rb.r : 2) + 1.4));
          q.setFromUnitVectors(up, dir);
          m4.compose(pt, q, sc);
          arrows.setMatrixAt(i, m4);
        });
        arrows.instanceMatrix.needsUpdate = true;
        scene.add(arrows);
      }

      function dimmed(hex, amount) { return new T.Color(hex).lerp(bg, amount); }
      function restyle() {
        const f = WB.focus();
        const active = !!f.id;
        const hl = f.hl;
        const inUp = (id) => f.up.has(id);
        const inDown = (id) => f.down.has(id);
        nodeObjs.forEach((o) => {
          const id = o.node.id;
          let c; let s = o.r;
          if (active && id === f.id) { c = new T.Color(WB.colors.lineage.selected); s = o.r * 1.5; }
          else if (active && inUp(id)) c = new T.Color(WB.colors.lineage.up);
          else if (active && inDown(id)) c = new T.Color(WB.colors.lineage.down);
          else if (active) c = dimmed(WB.colors.type[o.node.type], 0.82);
          else c = new T.Color(WB.colors.type[o.node.type] || '#888888');
          if (hl && hl.has(id)) { c = new T.Color('#ffffff'); s = o.r * 1.4; }
          o.mesh.material.color.copy(c);
          o.mesh.scale.setScalar(s);
        });
        const edgeColour = (e) => {
          const s = e.source; const t = e.target;
          if (active) {
            const upSide = (s === f.id || inUp(s)) && (t === f.id || inUp(t));
            const downSide = (s === f.id || inDown(s)) && (t === f.id || inDown(t));
            if (upSide) return new T.Color(WB.colors.lineage.up);
            if (downSide) return new T.Color(WB.colors.lineage.down);
            return dimmed(e.causal ? WB.colors.edge.causes : e.memory ? WB.colors.edge['leaves-trace'] : WB.colors.edge.other, 0.88);
          }
          if (e.causal) return new T.Color(WB.colors.edge.causes).lerp(new T.Color('#ffffff'), 0.25);
          if (e.memory) return new T.Color(WB.colors.edge['leaves-trace']);
          return dimmed(WB.colors.edge.other, 0.55);
        };
        edgeGroup.children.forEach((lines) => {
          const arr = lines.geometry.attributes.color.array;
          lines.userData.list.forEach((e, i) => {
            const c = edgeColour(e);
            arr.set([c.r, c.g, c.b, c.r, c.g, c.b], i * 6);
          });
          lines.geometry.attributes.color.needsUpdate = true;
        });
        if (arrows) {
          arrows.userData.list.forEach((e, i) => arrows.setColorAt(i, edgeColour(e)));
          if (arrows.instanceColor) arrows.instanceColor.needsUpdate = true;
        }
        legend.replaceChildren(...(active ? [
          el('div', {}, el('span', { class: 'sw', style: 'border-color:' + WB.colors.lineage.selected }), 'selected'),
          el('div', {}, el('span', { class: 'sw', style: 'border-color:' + WB.colors.lineage.up }), 'upstream (causes, origins)'),
          el('div', {}, el('span', { class: 'sw', style: 'border-color:' + WB.colors.lineage.down }), 'downstream (effects, traces)'),
        ] : [
          el('div', {}, el('span', { class: 'sw', style: 'border-color:' + WB.colors.edge.causes }), 'causal link (arrow = effect)'),
          el('div', {}, el('span', { class: 'sw dash', style: 'border-color:' + WB.colors.edge['leaves-trace'] }), 'memory link (event to tradition)'),
          el('div', { class: 'muted', text: 'Shapes: sphere event, octahedron tradition, cube location' }),
        ]));
        dirty = true;
      }

      // ---- camera
      function placeCamera() {
        const sp = Math.sin(cam.phi);
        camera.position.set(cam.target.x + cam.dist * sp * Math.sin(cam.theta), cam.target.y + cam.dist * Math.cos(cam.phi),
          cam.target.z + cam.dist * sp * Math.cos(cam.theta));
        camera.lookAt(cam.target);
        camera.updateMatrixWorld();
      }
      function fit() {
        const pts = nodeObjs.filter((o) => o.mesh.visible).map((o) => o.mesh.position);
        const c = new T.Vector3();
        pts.forEach((p) => c.add(p));
        if (pts.length) c.divideScalar(pts.length);
        let rad = 20;
        pts.forEach((p) => { rad = Math.max(rad, p.distanceTo(c)); });
        cam.target.copy(c);
        cam.dist = (rad * 1.15) / Math.tan((camera.fov * Math.PI) / 360);
        dirty = true;
      }
      function size() {
        const w = Math.max(50, stage.clientWidth); const h = Math.max(50, stage.clientHeight);
        renderer.setSize(w, h, false);
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
        dirty = true;
      }

      // ---- pointer controls
      const ptrs = new Map();
      let drag = null;
      const dom = renderer.domElement;
      dom.addEventListener('contextmenu', (e) => e.preventDefault());
      dom.addEventListener('pointerdown', (e) => {
        dom.setPointerCapture(e.pointerId);
        ptrs.set(e.pointerId, { x: e.clientX, y: e.clientY });
        drag = { x: e.clientX, y: e.clientY, moved: 0, pan: e.button === 2 || e.button === 1 || e.shiftKey, pinch: ptrs.size > 1 ? pinchDist() : null };
        stage.focus({ preventScroll: true });
      });
      const pinchDist = () => { const p = [...ptrs.values()]; return p.length > 1 ? Math.hypot(p[0].x - p[1].x, p[0].y - p[1].y) : null; };
      dom.addEventListener('pointermove', (e) => {
        if (ptrs.has(e.pointerId)) ptrs.set(e.pointerId, { x: e.clientX, y: e.clientY });
        if (drag && ptrs.size > 1) {
          const d = pinchDist();
          if (drag.pinch && d) { cam.dist = Math.min(3000, Math.max(8, cam.dist * (drag.pinch / d))); drag.pinch = d; drag.moved = 99; dirty = true; }
          return;
        }
        if (drag) {
          const dx = e.clientX - drag.x; const dy = e.clientY - drag.y;
          drag.moved += Math.abs(dx) + Math.abs(dy);
          drag.x = e.clientX; drag.y = e.clientY;
          if (drag.pan) {
            const k = (cam.dist * Math.tan((camera.fov * Math.PI) / 360) * 2) / Math.max(1, stage.clientHeight);
            const right = new T.Vector3().setFromMatrixColumn(camera.matrixWorld, 0);
            const upv = new T.Vector3().setFromMatrixColumn(camera.matrixWorld, 1);
            cam.target.addScaledVector(right, -dx * k).addScaledVector(upv, dy * k);
          } else {
            cam.theta -= dx * 0.008;
            cam.phi = Math.min(Math.PI - 0.05, Math.max(0.05, cam.phi - dy * 0.008));
          }
          dirty = true;
        } else setHover(pick(e));
      });
      dom.addEventListener('pointerup', (e) => {
        ptrs.delete(e.pointerId);
        if (drag && drag.moved < 5 && ptrs.size === 0) {
          const hit = pick(e);
          WB.select(hit);
        }
        if (!ptrs.size) drag = null;
      });
      dom.addEventListener('pointercancel', (e) => { ptrs.delete(e.pointerId); drag = null; });
      dom.addEventListener('pointerleave', () => { if (!drag) setHover(null); });
      dom.addEventListener('wheel', (e) => {
        e.preventDefault();
        cam.dist = Math.min(3000, Math.max(8, cam.dist * Math.exp(e.deltaY * 0.0012)));
        dirty = true;
      }, { passive: false });
      stage.addEventListener('keydown', (e) => {
        const step = 0.12;
        if (e.key === 'ArrowLeft') cam.theta -= step;
        else if (e.key === 'ArrowRight') cam.theta += step;
        else if (e.key === 'ArrowUp') cam.phi = Math.max(0.05, cam.phi - step);
        else if (e.key === 'ArrowDown') cam.phi = Math.min(Math.PI - 0.05, cam.phi + step);
        else if (e.key === '+' || e.key === '=') cam.dist *= 0.85;
        else if (e.key === '-') cam.dist /= 0.85;
        else if (e.key === '0') fit();
        else return;
        e.preventDefault();
        dirty = true;
      });

      const ray = new T.Raycaster();
      function pick(e) {
        const r = dom.getBoundingClientRect();
        const v = new T.Vector2(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
        ray.setFromCamera(v, camera);
        const hit = ray.intersectObjects(pickables.filter((m) => m.visible), false)[0];
        pick.last = { x: e.clientX - r.left, y: e.clientY - r.top };
        return hit ? hit.object.userData.id : null;
      }
      function setHover(id) {
        if (id === hover) { if (id) moveTip(); return; }
        hover = id;
        WB.state.hover = id;
        dom.style.cursor = id ? 'pointer' : 'default';
        const n = id ? byId.get(id) : null;
        tip.hidden = !n;
        if (n) { tip.textContent = n.name + ' (' + n.type + (n.date_label ? ', ' + n.date_label : '') + ')'; moveTip(); }
        dirty = true;
      }
      function moveTip() {
        const p = pick.last || { x: 0, y: 0 };
        tip.style.left = Math.min(p.x + 14, stage.clientWidth - 200) + 'px';
        tip.style.top = (p.y + 14) + 'px';
      }

      // ---- labels
      const labelPool = [];
      function updateLabels() {
        const f = WB.focus();
        const w = stage.clientWidth; const h = stage.clientHeight;
        const wanted = [];
        const add = (id, cls) => { if (id && posOf.has(id) && !wanted.some((x) => x.id === id)) wanted.push({ id, cls }); };
        add(f.id, 'sel'); add(hover, 'sel');
        if (f.hl) f.hl.forEach((id) => add(id, 'sel'));
        if (f.id) {
          [...f.up].slice(0, 14).forEach((id) => add(id, 'up'));
          [...f.down].slice(0, 14).forEach((id) => add(id, 'down'));
        } else {
          nodeObjs.filter((o) => o.mesh.visible).sort((a, b) => WB.degree(b.node.id) - WB.degree(a.node.id))
            .slice(0, 12).forEach((o) => add(o.node.id, ''));
        }
        const boxes = [];
        const v = new T.Vector3();
        let used = 0;
        wanted.forEach((wnt) => {
          const o = nodeObjs.find((x) => x.node.id === wnt.id);
          if (!o || !o.mesh.visible) return;
          v.copy(o.mesh.position).project(camera);
          if (v.z > 1 || Math.abs(v.x) > 1 || Math.abs(v.y) > 1) return;
          const x = (v.x * 0.5 + 0.5) * w; const y = (-v.y * 0.5 + 0.5) * h + o.r * 2 + 4;
          const text = (wnt.cls === 'up' ? '↑ ' : wnt.cls === 'down' ? '↓ ' : '') + o.node.name;
          const bw = text.length * 6.6 + 8;
          const box = { x0: x - bw / 2, x1: x + bw / 2, y0: y, y1: y + 16 };
          const forced = wnt.cls === 'sel';
          if (!forced && boxes.some((b) => box.x0 < b.x1 && box.x1 > b.x0 && box.y0 < b.y1 && box.y1 > b.y0)) return;
          boxes.push(box);
          let d = labelPool[used];
          if (!d) { d = el('div', { class: 'gv-label' }); labelBox.appendChild(d); labelPool.push(d); }
          d.hidden = false; d.textContent = text;
          d.className = 'gv-label ' + (wnt.id === f.id ? 'sel' : '');
          d.style.left = x + 'px'; d.style.top = y + 'px';
          used++;
        });
        for (let i = used; i < labelPool.length; i++) labelPool[i].hidden = true;
      }

      let raf = 0;
      function frame() {
        raf = requestAnimationFrame(frame);
        if (!dirty || !container.isConnected || container.hidden) return;
        dirty = false;
        placeCamera();
        renderer.render(scene, camera);
        updateLabels();
      }

      this.onSelect = (id) => {
        restyle();
        if (id && posOf.has(id)) {
          const v = posOf.get(id).clone().project(camera);
          if (Math.abs(v.x) > 0.9 || Math.abs(v.y) > 0.9) { cam.target.copy(posOf.get(id)); }
        }
      };
      this.onFilter = () => { applyVisibility(); };
      this.activate = () => { size(); dirty = true; if (!raf) frame(); };
      this.deactivate = () => { };
      this.resize = () => { if (!container.hidden) size(); };
      WB.bus.on('highlight', () => restyle());
      relayout();
      size();
      frame();
    },
  });
})();
