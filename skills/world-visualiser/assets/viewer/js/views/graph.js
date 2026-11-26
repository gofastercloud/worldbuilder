// graph.js: 3D Causal Universe — WebGL visualiser with sculpted entity geometries,
// flowing causal/memory particle streams, 4 morphing 3D layouts, spring-damped camera,
// causal tour playback, keyboard surfing, and live 2D radar minimap. Three.js r158 global.
(function () {
  'use strict';
  const { el, byId, out, inn, fmtT, tToX } = WB.util;
  const D = WB.data;

  // Map timeline event metadata (significance, etc.) by id.
  const eventMeta = new Map();
  ((D.timeline && D.timeline.events) || []).forEach((ev) => {
    if (ev && ev.id) eventMeta.set(ev.id, ev);
  });

  function rng(seed) { // deterministic mulberry32 PRNG
    let a = seed >>> 0;
    return function () {
      a = (a + 0x6D2B79F5) >>> 0;
      let t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  function isMajorEvent(node) {
    if (!node || node.type !== 'event') return false;
    const ev = eventMeta.get(node.id);
    const sig = String((ev && ev.significance) || node.significance || '').toLowerCase();
    return sig === 'world-changing' || sig === 'crucial' || sig === 'major';
  }

  function isWorldChanging(node) {
    if (!node || node.type !== 'event') return false;
    const ev = eventMeta.get(node.id);
    const sig = String((ev && ev.significance) || node.significance || '').toLowerCase();
    return sig === 'world-changing' || sig === 'crucial';
  }

  function normT(t) {
    if (t === null || t === undefined || isNaN(t)) return null;
    const x = tToX(t, 1);
    return isNaN(x) ? 0.5 : Math.max(0, Math.min(1, x));
  }

  // ---- 4 Deterministic 3D Layout Algorithms ----
  function layoutConstellation(nodes, links) {
    const n = nodes.length;
    const pos = new Float32Array(n * 3);
    if (!n) return pos;
    const idx = new Map(nodes.map((nd, i) => [nd.id, i]));
    const rand = rng(20240607);
    const k = 22;
    const R = k * Math.cbrt(n) * 1.25;
    for (let i = 0; i < n; i++) {
      pos[i * 3] = (rand() - 0.5) * R * 2;
      pos[i * 3 + 1] = (rand() - 0.5) * R * 2;
      pos[i * 3 + 2] = (rand() - 0.5) * R * 2;
    }
    const L = links
      .map((e) => [idx.get(e.source), idx.get(e.target), e.causal || e.memory ? 1.0 : 0.35])
      .filter((l) => l[0] !== undefined && l[1] !== undefined && l[0] !== l[1]);
    const iters = n <= 260 ? 260 : n <= 550 ? 160 : 90;
    const disp = new Float32Array(n * 3);
    for (let it = 0; it < iters; it++) {
      const temp = k * (1 - it / iters) + 0.4;
      disp.fill(0);
      for (let i = 0; i < n; i++) {
        for (let j = i + 1; j < n; j++) {
          let dx = pos[i * 3] - pos[j * 3];
          let dy = pos[i * 3 + 1] - pos[j * 3 + 1];
          let dz = pos[i * 3 + 2] - pos[j * 3 + 2];
          let d2 = dx * dx + dy * dy + dz * dz;
          if (d2 < 0.01) { dx = rand() - 0.5; dy = rand() - 0.5; dz = rand() - 0.5; d2 = 0.5; }
          const f = (k * k) / d2;
          disp[i * 3] += dx * f; disp[i * 3 + 1] += dy * f; disp[i * 3 + 2] += dz * f;
          disp[j * 3] -= dx * f; disp[j * 3 + 1] -= dy * f; disp[j * 3 + 2] -= dz * f;
        }
      }
      for (const [a, b, w] of L) {
        const dx = pos[a * 3] - pos[b * 3];
        const dy = pos[a * 3 + 1] - pos[b * 3 + 1];
        const dz = pos[a * 3 + 2] - pos[b * 3 + 2];
        const d = Math.sqrt(dx * dx + dy * dy + dz * dz) + 0.01;
        const f = (d / k) * w;
        disp[a * 3] -= dx * f; disp[a * 3 + 1] -= dy * f; disp[a * 3 + 2] -= dz * f;
        disp[b * 3] += dx * f; disp[b * 3 + 1] += dy * f; disp[b * 3 + 2] += dz * f;
      }
      for (let i = 0; i < n; i++) {
        for (let c = 0; c < 3; c++) disp[i * 3 + c] -= pos[i * 3 + c] * 0.038;
        const m = Math.sqrt(disp[i * 3] ** 2 + disp[i * 3 + 1] ** 2 + disp[i * 3 + 2] ** 2) + 1e-6;
        const s = Math.min(m, temp) / m;
        for (let c = 0; c < 3; c++) pos[i * 3 + c] += disp[i * 3 + c] * s;
      }
    }
    return pos;
  }

  // Chronos Helix: 3D spiral timeline where angle/height tracks WorldDate t and radius reflects significance.
  function layoutHelix(nodes) {
    const n = nodes.length;
    const pos = new Float32Array(n * 3);
    if (!n) return pos;
    const rand = rng(9001337);
    const height = Math.max(150, Math.min(340, n * 4.5));
    const turns = Math.max(2.2, Math.min(5.0, n / 14));
    const baseR = Math.max(48, Math.min(110, 26 + n * 1.1));
    const dated = [];
    const undated = [];
    nodes.forEach((nd, i) => {
      const nt = normT(nd.t);
      if (nt !== null) dated.push({ nd, i, nt });
      else undated.push({ nd, i });
    });
    dated.sort((a, b) => a.nt - b.nt || a.nd.id.localeCompare(b.nd.id));
    dated.forEach((item, rank) => {
      const u = dated.length > 1 ? item.nt * 0.72 + (rank / (dated.length - 1)) * 0.28 : 0.5;
      const angle = u * turns * Math.PI * 2;
      const deg = WB.degree(item.nd.id);
      const sigBoost = isWorldChanging(item.nd) ? 1.25 : isMajorEvent(item.nd) ? 1.1 : 0.85;
      const rad = baseR * sigBoost + Math.min(26, Math.sqrt(deg) * 5) + (item.nd.type === 'tradition' ? 18 : 0);
      const y = (u - 0.5) * height;
      pos[item.i * 3] = Math.cos(angle) * rad;
      pos[item.i * 3 + 1] = y;
      pos[item.i * 3 + 2] = Math.sin(angle) * rad;
    });
    // Place undated entities on an outer ethereal halo ring.
    const outerR = baseR * 1.55 + 24;
    undated.forEach((item, idx) => {
      const angle = (idx / Math.max(1, undated.length)) * Math.PI * 2;
      const y = (rand() - 0.5) * height * 0.45;
      pos[item.i * 3] = Math.cos(angle) * outerR;
      pos[item.i * 3 + 1] = y;
      pos[item.i * 3 + 2] = Math.sin(angle) * outerR;
    });
    return pos;
  }

  // Causal Strata: stacked translucent 3D era planes with nodes arranged on their era disc.
  function computeEraBuckets(nodes) {
    const calEras = (D.calendar && D.calendar.eras) || [];
    const eraOrder = [];
    const seen = new Set();
    calEras.forEach((e) => {
      if (e && e.name && !seen.has(e.name)) { seen.add(e.name); eraOrder.push(e.name); }
    });
    nodes.forEach((nd) => {
      if (nd.era && !seen.has(nd.era)) { seen.add(nd.era); eraOrder.push(nd.era); }
    });
    const hasUndated = nodes.some((nd) => !nd.era);
    if (hasUndated || !eraOrder.length) eraOrder.push('Timeless / Undated');
    return eraOrder;
  }

  function layoutStrata(nodes) {
    const n = nodes.length;
    const pos = new Float32Array(n * 3);
    if (!n) return { pos, planes: [] };
    const eraNames = computeEraBuckets(nodes);
    const gapY = Math.max(44, Math.min(72, 260 / Math.max(1, eraNames.length)));
    const totalH = (eraNames.length - 1) * gapY;
    const byEra = new Map(eraNames.map((name) => [name, []]));
    nodes.forEach((nd, i) => {
      const key = nd.era && byEra.has(nd.era) ? nd.era : eraNames[eraNames.length - 1];
      byEra.get(key).push({ nd, i });
    });
    const planes = [];
    const golden = Math.PI * (3 - Math.sqrt(5));
    eraNames.forEach((name, ei) => {
      const y = ei * gapY - totalH / 2;
      const list = byEra.get(name) || [];
      list.sort((a, b) => WB.degree(b.nd.id) - WB.degree(a.nd.id) || (a.nd.t || 0) - (b.nd.t || 0));
      let maxR = 46;
      list.forEach((item, k) => {
        const rad = list.length <= 1 ? 0 : 16 + 18 * Math.sqrt(k + 0.5);
        const angle = k * golden + ei * 1.1;
        const x = Math.cos(angle) * rad;
        const z = Math.sin(angle) * rad;
        pos[item.i * 3] = x;
        pos[item.i * 3 + 1] = y + (item.nd.type === 'tradition' ? 6 : 0);
        pos[item.i * 3 + 2] = z;
        maxR = Math.max(maxR, rad + 18);
      });
      planes.push({ name, y, radius: maxR, count: list.length });
    });
    return { pos, planes };
  }

  // Orbital Sphere: concentric 3D shells grouped by entity type with high-centrality hubs near the core.
  function layoutOrbital(nodes) {
    const n = nodes.length;
    const pos = new Float32Array(n * 3);
    if (!n) return pos;
    const typeOrder = Object.keys(WB.colors.type);
    const groups = new Map();
    nodes.forEach((nd, i) => {
      const t = nd.type || 'other';
      if (!groups.has(t)) groups.set(t, []);
      groups.get(t).push({ nd, i, deg: WB.degree(nd.id) });
    });
    const sortedTypes = [...groups.keys()].sort((a, b) => {
      if (a === 'event') return -1;
      if (b === 'event') return 1;
      return (typeOrder.indexOf(a) + 99) - (typeOrder.indexOf(b) + 99);
    });
    const maxDeg = Math.max(1, ...nodes.map((nd) => WB.degree(nd.id)));
    const golden = Math.PI * (3 - Math.sqrt(5));
    sortedTypes.forEach((type, shellIdx) => {
      const list = groups.get(type);
      list.sort((a, b) => b.deg - a.deg || a.nd.id.localeCompare(b.nd.id));
      const baseShellR = 38 + shellIdx * 34;
      const m = list.length;
      list.forEach((item, k) => {
        const yNorm = m === 1 ? 0 : 1 - (k / (m - 1)) * 2;
        const ringR = Math.sqrt(Math.max(0, 1 - yNorm * yNorm));
        const theta = golden * k + shellIdx * 0.9;
        // High-centrality hubs pull closer to the radiant core.
        const centrality = item.deg / maxDeg;
        const r = Math.max(16, baseShellR * (1.12 - centrality * 0.42));
        pos[item.i * 3] = Math.cos(theta) * ringR * r;
        pos[item.i * 3 + 1] = yNorm * r;
        pos[item.i * 3 + 2] = Math.sin(theta) * ringR * r;
      });
    });
    return pos;
  }

  // ---- Procedural Canvas Glow Textures (zero network dependencies) ----
  function makeGlowTexture(T, stops) {
    const size = 128;
    const c = document.createElement('canvas');
    c.width = size;
    c.height = size;
    const ctx = c.getContext('2d');
    const g = ctx.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
    stops.forEach(([off, col]) => g.addColorStop(off, col));
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, size, size);
    const tex = new T.CanvasTexture(c);
    tex.needsUpdate = true;
    return tex;
  }

  WB.registerView({
    id: 'graph',
    title: 'Causal graph',
    order: 10,
    create(container) {
      container.classList.add('gv');
      const stage = el('div', {
        class: 'gv-stage',
        tabindex: '0',
        role: 'application',
        'aria-label': '3D causal universe. Drag to orbit, right-drag to pan, scroll to zoom, 1-4 switch layouts, arrows or WASD surf neighbours, F flies to selected, R resets camera, Space plays causal tour.',
      });
      container.appendChild(stage);

      if (typeof window.THREE === 'undefined') {
        stage.replaceChildren(el('p', {
          class: 'view-msg',
          text: 'The 3D graph needs three.js, which could not load (needs internet). Use the entity list and the timeline instead.',
        }));
        return;
      }

      const T = window.THREE;
      let renderer;
      try {
        renderer = new T.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
      } catch (e) {
        stage.replaceChildren(el('p', {
          class: 'view-msg',
          text: 'WebGL is not available in this browser, so the 3D graph cannot be drawn: ' + e.message,
        }));
        return;
      }
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
      stage.appendChild(renderer.domElement);

      // ---- Reduced Motion Support ----
      const rmq = window.matchMedia ? window.matchMedia('(prefers-reduced-motion: reduce)') : null;
      let reducedMotion = !!(rmq && rmq.matches);
      if (rmq && rmq.addEventListener) {
        rmq.addEventListener('change', (ev) => {
          reducedMotion = !!ev.matches;
          if (reducedMotion) {
            opts.autoOrbit = false;
            syncHudState();
          }
          dirty = true;
        });
      }

      // ---- State & Options ----
      const opts = {
        layout: 'constellation', // constellation | helix | strata | orbital
        scope: 'chain',          // chain | all
        edges: 'causal',         // causal | all
        traditions: true,
        eraPlanes: false,
        autoOrbit: !reducedMotion,
        fxIntensity: 1.0,        // 0..2
      };

      // ---- Floating Glassmorphic HUD ----
      const layoutButtons = new Map();
      const layoutPills = el('div', { class: 'gv-pills', role: 'group', 'aria-label': '3D Layout' },
        [
          ['constellation', '1', 'Constellation'],
          ['helix', '2', 'Helix'],
          ['strata', '3', 'Strata'],
          ['orbital', '4', 'Orbital'],
        ].map(([id, key, label]) => {
          const btn = el('button', {
            type: 'button',
            class: 'gv-pill',
            'aria-pressed': String(opts.layout === id),
            onclick: () => setLayout(id),
          }, el('span', { class: 'gv-kbd', text: key }), label);
          layoutButtons.set(id, btn);
          return btn;
        }));

      const scopeBtn = el('button', {
        type: 'button', class: 'gv-hud-btn', 'aria-pressed': 'false',
        title: 'Toggle between Causal Chain and All Entities',
        onclick: () => {
          opts.scope = opts.scope === 'chain' ? 'all' : 'chain';
          opts.edges = opts.scope === 'all' ? 'all' : 'causal';
          syncHudState();
          rebuildGraph();
        },
      });
      const tradBtn = el('button', {
        type: 'button', class: 'gv-hud-btn', 'aria-pressed': String(opts.traditions),
        title: 'Show or hide folklore and traditions',
        onclick: () => {
          opts.traditions = !opts.traditions;
          syncHudState();
          rebuildGraph();
        },
      }, 'Traditions');
      const eraBtn = el('button', {
        type: 'button', class: 'gv-hud-btn', 'aria-pressed': String(opts.eraPlanes),
        title: 'Show translucent 3D era planes',
        onclick: () => {
          opts.eraPlanes = !opts.eraPlanes;
          syncHudState();
          updateEraPlanesVisibility();
          dirty = true;
        },
      }, 'Era Planes');
      const orbitBtn = el('button', {
        type: 'button', class: 'gv-hud-btn', 'aria-pressed': String(opts.autoOrbit),
        title: 'Toggle gentle cosmic auto-orbit',
        onclick: () => {
          if (reducedMotion) return;
          opts.autoOrbit = !opts.autoOrbit;
          syncHudState();
          dirty = true;
        },
      }, 'Orbit');
      const fxSlider = el('input', {
        type: 'range', class: 'gv-slider', min: '0', max: '200', step: '10',
        value: String(Math.round(opts.fxIntensity * 100)),
        'aria-label': 'Particle FX intensity',
        oninput: () => {
          opts.fxIntensity = Number(fxSlider.value) / 100;
          if (particleSystem) particleSystem.visible = opts.fxIntensity > 0;
          dirty = true;
        },
      });
      const tourBtn = el('button', {
        type: 'button', class: 'gv-hud-btn', 'aria-pressed': 'false',
        title: 'Play/Pause Causal Tour (Space)',
        onclick: () => toggleTour(),
      }, '▶ Tour');
      const isoBtn = el('button', {
        type: 'button', class: 'gv-hud-btn', title: 'Isometric angle',
        onclick: () => setCameraPreset('iso'),
      }, 'Iso');
      const topBtn = el('button', {
        type: 'button', class: 'gv-hud-btn', title: 'Top-down angle',
        onclick: () => setCameraPreset('top'),
      }, 'Top');
      const resetBtn = el('button', {
        type: 'button', class: 'gv-hud-btn', title: 'Reset camera (R)',
        onclick: () => fit(true),
      }, 'Reset');
      const flyBtn = el('button', {
        type: 'button', class: 'gv-hud-btn', title: 'Fly to selected node (F)',
        onclick: () => { if (WB.state.selected) flyToNode(WB.state.selected); },
      }, 'Fly-To');
      const countEl = el('span', { class: 'gv-count', id: 'gv-count' });

      const hudTop = el('div', { class: 'gv-hud-top' },
        el('div', { class: 'gv-hud-group' },
          layoutPills,
          el('span', { class: 'gv-sep', 'aria-hidden': 'true' }),
          scopeBtn, tradBtn, eraBtn),
        el('div', { class: 'gv-hud-group' },
          tourBtn, orbitBtn,
          el('label', { class: 'gv-slider-wrap' }, 'FX', fxSlider),
          el('span', { class: 'gv-sep', 'aria-hidden': 'true' }),
          isoBtn, topBtn, resetBtn, flyBtn,
          el('span', { class: 'gv-sep', 'aria-hidden': 'true' }),
          countEl));

      const labelBox = el('div', { class: 'gv-labels' });
      const tip = el('div', { class: 'gv-tip', hidden: true });
      const legend = el('div', { class: 'gv-legend' });

      // Live 2D Canvas Radar Minimap
      const radarCanvas = el('canvas', { class: 'gv-radar', width: '276', height: '276', 'aria-label': '3D Radar Minimap (click a node to fly to it)' });
      const radarCtx = radarCanvas.getContext('2d');
      const radarWrap = el('div', { class: 'gv-radar-wrap' },
        el('div', { class: 'gv-radar-head' }, el('span', { text: 'Radar' }), el('span', { text: 'XZ' })),
        radarCanvas);

      // Cinematic Causal Tour Bar
      const tourStepEl = el('span', { class: 'gv-tour-step' });
      const tourNameEl = el('div', { class: 'gv-tour-name' });
      const tourMetaEl = el('div', { class: 'gv-tour-meta' });
      const tourSummaryEl = el('p', { class: 'gv-tour-summary' });
      const tourPlayPauseBtn = el('button', { type: 'button', class: 'gv-hud-btn', onclick: () => toggleTourPause() }, 'Pause');
      const tourBar = el('div', { class: 'gv-tour-bar', hidden: true, role: 'status', 'aria-live': 'polite' },
        el('div', { class: 'gv-tour-top' },
          tourStepEl,
          el('div', { class: 'gv-tour-controls' },
            el('button', { type: 'button', class: 'gv-hud-btn', onclick: () => stepTour(-1), 'aria-label': 'Previous step' }, '◀'),
            tourPlayPauseBtn,
            el('button', { type: 'button', class: 'gv-hud-btn', onclick: () => stepTour(1), 'aria-label': 'Next step' }, '▶'),
            el('button', { type: 'button', class: 'gv-hud-btn', onclick: () => stopTour(), 'aria-label': 'Close tour' }, '✕'))),
        tourNameEl, tourMetaEl, tourSummaryEl);

      stage.append(hudTop, labelBox, tip, radarWrap, legend, tourBar);

      function syncHudState() {
        layoutButtons.forEach((btn, id) => btn.setAttribute('aria-pressed', String(opts.layout === id)));
        scopeBtn.textContent = opts.scope === 'all' ? 'All Entities' : 'Causal Chain';
        scopeBtn.setAttribute('aria-pressed', String(opts.scope === 'all'));
        tradBtn.setAttribute('aria-pressed', String(opts.traditions));
        eraBtn.setAttribute('aria-pressed', String(opts.eraPlanes || opts.layout === 'strata'));
        orbitBtn.setAttribute('aria-pressed', String(opts.autoOrbit));
        tourBtn.classList.toggle('gv-tour-active', tour.active);
        tourBtn.setAttribute('aria-pressed', String(tour.active));
        tourBtn.textContent = tour.active ? (tour.paused ? '▶ Resume' : '⏸ Tour') : '▶ Tour';
        tourPlayPauseBtn.textContent = tour.paused ? 'Resume' : 'Pause';
      }

      // ---- Three.js Scene, Lighting & Procedural Textures ----
      const scene = new T.Scene();
      const ambientLight = new T.AmbientLight(0xdbeafe, 1.15);
      scene.add(ambientLight);
      const keyLight = new T.DirectionalLight(0xffffff, 1.45);
      keyLight.position.set(180, 260, 200);
      scene.add(keyLight);
      const rimLight = new T.DirectionalLight(0x7dd3fc, 0.9);
      rimLight.position.set(-220, -140, -180);
      scene.add(rimLight);
      const warmLight = new T.PointLight(0xf59e0b, 0.85, 900);
      warmLight.position.set(140, -160, 120);
      scene.add(warmLight);

      const camera = new T.PerspectiveCamera(48, 1, 0.5, 6500);
      const cam = { theta: 0.65, phi: 1.18, dist: 215, target: new T.Vector3() };
      const camGoal = { theta: 0.65, phi: 1.18, dist: 215, target: new T.Vector3() };

      const glowTex = makeGlowTexture(T, [
        [0.0, 'rgba(255,255,255,1)'],
        [0.22, 'rgba(255,255,255,0.75)'],
        [0.52, 'rgba(255,255,255,0.22)'],
        [1.0, 'rgba(255,255,255,0)'],
      ]);
      const nebulaTex = makeGlowTexture(T, [
        [0.0, 'rgba(255,255,255,0.22)'],
        [0.4, 'rgba(255,255,255,0.08)'],
        [1.0, 'rgba(255,255,255,0)'],
      ]);
      const sparkTex = makeGlowTexture(T, [
        [0.0, 'rgba(255,255,255,1)'],
        [0.35, 'rgba(255,255,255,0.85)'],
        [0.7, 'rgba(255,255,255,0.25)'],
        [1.0, 'rgba(255,255,255,0)'],
      ]);

      // ---- Procedural Starfield + Nebula / Light-Mode Atmospheric Motes ----
      const backdropGroup = new T.Group();
      scene.add(backdropGroup);
      let starPoints = null;
      let nebulaPoints = null;

      function buildBackdrop() {
        const rand = rng(777123);
        // Starfield / dust motes
        const starCount = 1100;
        const sPos = new Float32Array(starCount * 3);
        const sCol = new Float32Array(starCount * 3);
        const starPalette = [
          new T.Color('#e0f2fe'), new T.Color('#fef3c7'), new T.Color('#ddd6fe'), new T.Color('#ffffff'),
        ];
        for (let i = 0; i < starCount; i++) {
          const rad = 520 + rand() * 1400;
          const th = rand() * Math.PI * 2;
          const ph = Math.acos(2 * rand() - 1);
          sPos[i * 3] = rad * Math.sin(ph) * Math.cos(th);
          sPos[i * 3 + 1] = rad * Math.cos(ph);
          sPos[i * 3 + 2] = rad * Math.sin(ph) * Math.sin(th);
          const c = starPalette[Math.floor(rand() * starPalette.length)];
          sCol[i * 3] = c.r; sCol[i * 3 + 1] = c.g; sCol[i * 3 + 2] = c.b;
        }
        const sGeo = new T.BufferGeometry();
        sGeo.setAttribute('position', new T.BufferAttribute(sPos, 3));
        sGeo.setAttribute('color', new T.BufferAttribute(sCol, 3));
        starPoints = new T.Points(sGeo, new T.PointsMaterial({
          size: 7.5,
          map: glowTex,
          vertexColors: true,
          transparent: true,
          opacity: 0.78,
          depthWrite: false,
          blending: T.AdditiveBlending,
          sizeAttenuation: true,
        }));
        backdropGroup.add(starPoints);

        // Soft Nebula Dust Cloud
        const nebCount = 95;
        const nPos = new Float32Array(nebCount * 3);
        const nCol = new Float32Array(nebCount * 3);
        const nebPalette = [
          new T.Color('#38bdf8'), new T.Color('#818cf8'), new T.Color('#e879f9'), new T.Color('#f59e0b'),
        ];
        for (let i = 0; i < nebCount; i++) {
          const rad = 260 + rand() * 640;
          const th = rand() * Math.PI * 2;
          const y = (rand() - 0.5) * 420;
          nPos[i * 3] = Math.cos(th) * rad;
          nPos[i * 3 + 1] = y;
          nPos[i * 3 + 2] = Math.sin(th) * rad;
          const c = nebPalette[Math.floor(rand() * nebPalette.length)];
          nCol[i * 3] = c.r; nCol[i * 3 + 1] = c.g; nCol[i * 3 + 2] = c.b;
        }
        const nGeo = new T.BufferGeometry();
        nGeo.setAttribute('position', new T.BufferAttribute(nPos, 3));
        nGeo.setAttribute('color', new T.BufferAttribute(nCol, 3));
        nebulaPoints = new T.Points(nGeo, new T.PointsMaterial({
          size: 170,
          map: nebulaTex,
          vertexColors: true,
          transparent: true,
          opacity: 0.34,
          depthWrite: false,
          blending: T.AdditiveBlending,
          sizeAttenuation: true,
        }));
        backdropGroup.add(nebulaPoints);
      }
      buildBackdrop();

      // ---- Theme Detection & Dynamic Backdrop Styling ----
      let bg = new T.Color('#0e1117');
      let isDark = true;

      function themeBg() {
        const v = getComputedStyle(document.documentElement).getPropertyValue('--bg').trim() || '#0e1117';
        bg = new T.Color(v);
        const hsl = { h: 0, s: 0, l: 0 };
        bg.getHSL(hsl);
        isDark = hsl.l < 0.45;
        renderer.setClearColor(bg, 1);
        scene.fog = new T.FogExp2(bg, isDark ? 0.00075 : 0.00065);
        ambientLight.intensity = isDark ? 0.72 : 0.95;
        keyLight.intensity = isDark ? 0.95 : 0.85;
        if (starPoints) {
          const sm = starPoints.material;
          sm.blending = isDark ? T.AdditiveBlending : T.NormalBlending;
          sm.opacity = isDark ? 0.8 : 0.32;
          sm.size = isDark ? 7.5 : 9.0;
          sm.color.set(isDark ? '#ffffff' : '#64748b');
          sm.needsUpdate = true;
        }
        if (nebulaPoints) {
          const nm = nebulaPoints.material;
          nm.blending = isDark ? T.AdditiveBlending : T.NormalBlending;
          nm.opacity = isDark ? 0.34 : 0.14;
          nm.color.set(isDark ? '#ffffff' : '#94a3b8');
          nm.needsUpdate = true;
        }
        nodeObjs.forEach((o) => {
          if (o.halo) {
            o.halo.material.blending = isDark ? T.AdditiveBlending : T.NormalBlending;
            o.halo.material.needsUpdate = true;
          }
        });
        if (particleSystem) {
          particleSystem.material.blending = isDark ? T.AdditiveBlending : T.NormalBlending;
          particleSystem.material.needsUpdate = true;
        }
        dirty = true;
      }

      // ---- Distinct Sculpted 3D Geometries per Entity Type ----
      const geoms = {
        event: new T.IcosahedronGeometry(1.18, 0),
        character: new T.OctahedronGeometry(1.28, 0),
        location: new T.SphereGeometry(1.02, 22, 16),
        faction: new T.TorusKnotGeometry(0.72, 0.24, 48, 8, 2, 3),
        item: new T.OctahedronGeometry(1.05, 0),
        tradition: new T.DodecahedronGeometry(1.16, 0),
        'magic-system': new T.TorusGeometry(0.95, 0.28, 12, 28),
        arc: new T.IcosahedronGeometry(1.12, 1),
        species: new T.DodecahedronGeometry(1.08, 0),
        race: new T.CylinderGeometry(0.76, 1.04, 1.45, 6),
        language: new T.TorusGeometry(0.9, 0.22, 10, 24),
        lineage: new T.ConeGeometry(1.0, 1.85, 6),
      };
      const locRingGeom = new T.TorusGeometry(1.56, 0.07, 8, 32);
      const orbitRingGeomA = new T.TorusGeometry(1.85, 0.045, 8, 40);
      const orbitRingGeomB = new T.TorusGeometry(2.25, 0.035, 8, 44);
      const arrowCone = new T.ConeGeometry(0.85, 2.5, 8);
      const shockRingGeom = new T.RingGeometry(0.86, 1.0, 48);

      // ---- Scene Groups & Data Structures ----
      const nodeGroup = new T.Group();
      const edgeGroup = new T.Group();
      const eraGroup = new T.Group();
      const fxGroup = new T.Group();
      scene.add(eraGroup, edgeGroup, nodeGroup, fxGroup);

      let nodeObjs = [];       // { node, group, mesh, halo, orbitRings, r, fromPos, toPos }
      let nodeById = new Map();
      let pickables = [];
      let posOf = new Map();   // id -> group.position
      let edgeCache = [];      // { e, a, b, ctrl, isCausal, isMemory, role }
      let solidLines = null;
      let memoryLines = null;
      let arrows = null;
      let eraPlanesData = [];  // { name, y, radius, labelPos }
      let morphT = 1;
      const MORPH_DURATION = 0.85;
      const layoutCache = new Map();

      // ---- Shockwave Pool ----
      const shockwaves = [];
      function spawnShockwave(pos, hexColor) {
        if (reducedMotion || !pos) return;
        const color = new T.Color(hexColor || '#F0E442');
        for (let k = 0; k < 2; k++) {
          const mat = new T.MeshBasicMaterial({
            color,
            side: T.DoubleSide,
            transparent: true,
            opacity: 0.88,
            blending: isDark ? T.AdditiveBlending : T.NormalBlending,
            depthWrite: false,
          });
          const ring = new T.Mesh(shockRingGeom, mat);
          ring.position.copy(pos);
          if (k === 0) ring.rotation.x = Math.PI / 2;
          else { ring.rotation.x = Math.PI / 3; ring.rotation.y = Math.PI / 4; }
          fxGroup.add(ring);
          shockwaves.push({ mesh: ring, age: k * -0.14, duration: 1.15, maxScale: 18 + k * 5 });
        }
      }

      // ---- Flowing Edge Energy Particle System ----
      const MAX_PARTICLES = 1500;
      const pPositions = new Float32Array(MAX_PARTICLES * 3);
      const pColors = new Float32Array(MAX_PARTICLES * 3);
      const pMeta = []; // { edgeIdx, u, speed, phase, isMemory }
      const pGeo = new T.BufferGeometry();
      pGeo.setAttribute('position', new T.BufferAttribute(pPositions, 3));
      pGeo.setAttribute('color', new T.BufferAttribute(pColors, 3));
      const pMat = new T.PointsMaterial({
        size: 5.2,
        map: sparkTex,
        vertexColors: true,
        transparent: true,
        opacity: 0.92,
        depthWrite: false,
        blending: T.AdditiveBlending,
        sizeAttenuation: true,
      });
      const particleSystem = new T.Points(pGeo, pMat);
      particleSystem.frustumCulled = false;
      fxGroup.add(particleSystem);
      let activeParticleCount = 0;

      function seedParticles() {
        pMeta.length = 0;
        const rand = rng(424242);
        const streamEdges = [];
        edgeCache.forEach((ec, i) => {
          if (ec.isCausal || ec.isMemory) streamEdges.push(i);
        });
        if (!streamEdges.length) {
          activeParticleCount = 0;
          pGeo.setDrawRange(0, 0);
          return;
        }
        const perEdge = Math.max(2, Math.min(12, Math.floor(MAX_PARTICLES / streamEdges.length)));
        let count = 0;
        for (let s = 0; s < streamEdges.length && count < MAX_PARTICLES; s++) {
          const edgeIdx = streamEdges[s];
          const ec = edgeCache[edgeIdx];
          for (let k = 0; k < perEdge && count < MAX_PARTICLES; k++) {
            pMeta.push({
              edgeIdx,
              u: (k / perEdge + rand() * 0.15) % 1,
              speed: (ec.isMemory ? 0.18 : 0.28) + rand() * 0.16,
              phase: rand() * Math.PI * 2,
              isMemory: ec.isMemory,
            });
            count++;
          }
        }
        activeParticleCount = count;
        pGeo.setDrawRange(0, activeParticleCount);
        updateParticles(0, 0);
      }

      const _tmpC1 = new T.Color('#38bdf8'); // electric cyan upstream
      const _tmpC2 = new T.Color('#fb923c'); // molten amber downstream
      const _tmpCCausal = new T.Color(WB.colors.edge.causes);
      const _tmpCMemory = new T.Color(WB.colors.edge['leaves-trace']);
      const _tmpCDim = new T.Color('#334155');

      function updateParticles(dt, elapsed) {
        if (!activeParticleCount || !particleSystem.visible) return;
        const f = WB.focus();
        const active = !!f.id;
        const speedMult = reducedMotion ? 0 : (0.35 + opts.fxIntensity * 0.95);
        for (let i = 0; i < activeParticleCount; i++) {
          const pm = pMeta[i];
          const ec = edgeCache[pm.edgeIdx];
          if (!ec) {
            pPositions[i * 3] = 1e6; pPositions[i * 3 + 1] = 1e6; pPositions[i * 3 + 2] = 1e6;
            continue;
          }
          const role = ec.role; // 'up' | 'down' | 'dim' | 'normal'
          if (active && role === 'dim') {
            pPositions[i * 3] = 1e6; pPositions[i * 3 + 1] = 1e6; pPositions[i * 3 + 2] = 1e6;
            continue;
          }
          const surge = (role === 'up' || role === 'down') ? 2.1 : 1.0;
          pm.u = (pm.u + pm.speed * dt * speedMult * surge) % 1;
          const u = pm.u;
          const inv = 1 - u;
          const a = ec.a;
          const b = ec.b;
          const c = ec.ctrl;
          let x = inv * inv * a.x + 2 * inv * u * c.x + u * u * b.x;
          let y = inv * inv * a.y + 2 * inv * u * c.y + u * u * b.y;
          let z = inv * inv * a.z + 2 * inv * u * c.z + u * u * b.z;
          if (pm.isMemory && !reducedMotion) {
            const wisp = Math.sin(elapsed * 3.2 + pm.phase + u * 8.0) * 1.4;
            y += wisp;
          }
          pPositions[i * 3] = x;
          pPositions[i * 3 + 1] = y;
          pPositions[i * 3 + 2] = z;

          let col;
          if (role === 'up') col = _tmpC1;
          else if (role === 'down') col = _tmpC2;
          else if (active) col = _tmpCDim;
          else col = pm.isMemory ? _tmpCMemory : _tmpCCausal;
          const pulse = 0.78 + 0.22 * Math.sin(u * Math.PI);
          pColors[i * 3] = Math.min(1, col.r * pulse + (role === 'up' || role === 'down' ? 0.12 : 0));
          pColors[i * 3 + 1] = Math.min(1, col.g * pulse + (role === 'up' || role === 'down' ? 0.12 : 0));
          pColors[i * 3 + 2] = Math.min(1, col.b * pulse + (role === 'up' || role === 'down' ? 0.12 : 0));
        }
        pGeo.attributes.position.needsUpdate = true;
        pGeo.attributes.color.needsUpdate = true;
      }

      // ---- Era Planes (3D Translucent Discs) ----
      function buildEraPlanes(planes) {
        eraGroup.children.slice().forEach((c) => {
          eraGroup.remove(c);
          if (c.geometry) c.geometry.dispose();
          if (c.material) c.material.dispose();
        });
        eraPlanesData = [];
        planes.forEach((pl, idx) => {
          const discR = Math.max(54, pl.radius + 10);
          const hue = (0.56 + idx * 0.11) % 1;
          const col = new T.Color().setHSL(hue, 0.65, isDark ? 0.58 : 0.42);
          const disc = new T.Mesh(
            new T.CircleGeometry(discR, 56),
            new T.MeshBasicMaterial({
              color: col,
              transparent: true,
              opacity: isDark ? 0.065 : 0.08,
              side: T.DoubleSide,
              depthWrite: false,
            })
          );
          disc.rotation.x = -Math.PI / 2;
          disc.position.y = pl.y - 2.5;
          eraGroup.add(disc);

          const rim = new T.Mesh(
            new T.RingGeometry(discR - 0.9, discR, 64),
            new T.MeshBasicMaterial({
              color: col,
              transparent: true,
              opacity: isDark ? 0.36 : 0.42,
              side: T.DoubleSide,
              depthWrite: false,
            })
          );
          rim.rotation.x = -Math.PI / 2;
          rim.position.y = pl.y - 2.4;
          eraGroup.add(rim);

          const innerRim = new T.Mesh(
            new T.RingGeometry(discR * 0.5 - 0.4, discR * 0.5, 48),
            new T.MeshBasicMaterial({
              color: col,
              transparent: true,
              opacity: isDark ? 0.14 : 0.18,
              side: T.DoubleSide,
              depthWrite: false,
            })
          );
          innerRim.rotation.x = -Math.PI / 2;
          innerRim.position.y = pl.y - 2.4;
          eraGroup.add(innerRim);

          eraPlanesData.push({
            name: pl.name,
            y: pl.y,
            radius: discR,
            labelPos: new T.Vector3(discR + 6, pl.y, 0),
          });
        });
        updateEraPlanesVisibility();
      }

      function updateEraPlanesVisibility() {
        eraGroup.visible = opts.eraPlanes || opts.layout === 'strata';
      }

      // ---- Node & Edge Construction ----
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

      function getLayoutPositions(layoutName, nodes, links) {
        const key = [layoutName, opts.scope, opts.edges, opts.traditions, nodes.length].join('|');
        const cached = layoutCache.get(key);
        if (cached) return cached;
        let result;
        if (layoutName === 'helix') {
          result = { pos: layoutHelix(nodes), planes: null };
        } else if (layoutName === 'strata') {
          result = layoutStrata(nodes);
        } else if (layoutName === 'orbital') {
          result = { pos: layoutOrbital(nodes), planes: null };
        } else {
          result = { pos: layoutConstellation(nodes, links), planes: null };
        }
        layoutCache.set(key, result);
        return result;
      }

      function setLayout(name) {
        if (opts.layout === name) return;
        opts.layout = name;
        syncHudState();
        const nodes = nodeObjs.map((o) => o.node);
        const ids = new Set(nodes.map((n) => n.id));
        const links = WB.edges.filter((e) => ids.has(e.source) && ids.has(e.target) && edgeVisible(e));
        const laid = getLayoutPositions(name, nodes, links);
        if (laid.planes) buildEraPlanes(laid.planes);
        else if (!eraPlanesData.length) buildEraPlanes(layoutStrata(nodes).planes);
        updateEraPlanesVisibility();

        nodeObjs.forEach((o, i) => {
          o.fromPos.copy(o.group.position);
          o.toPos.set(laid.pos[i * 3], laid.pos[i * 3 + 1], laid.pos[i * 3 + 2]);
          if (reducedMotion) o.group.position.copy(o.toPos);
        });
        morphT = reducedMotion ? 1 : 0;
        if (reducedMotion) {
          syncEdgesToNodePositions();
          fit(false);
        } else {
          fitTargetBounds(laid.pos);
        }
        dirty = true;
      }

      function rebuildGraph() {
        const nodes = visibleNodeSet();
        const ids = new Set(nodes.map((n) => n.id));
        const links = WB.edges.filter((e) => ids.has(e.source) && ids.has(e.target) && edgeVisible(e));
        const laid = getLayoutPositions(opts.layout, nodes, links);
        const strataPlanes = laid.planes || layoutStrata(nodes).planes;
        buildEraPlanes(strataPlanes);

        // Dispose previous nodes
        nodeObjs.forEach((o) => {
          nodeGroup.remove(o.group);
          o.mesh.material.dispose();
          if (o.halo) o.halo.material.dispose();
          if (o.locRing) o.locRing.material.dispose();
          o.orbitRings.forEach((r) => r.material.dispose());
        });
        nodeObjs = [];
        nodeById = new Map();
        pickables = [];
        posOf = new Map();

        nodes.forEach((n, i) => {
          const deg = WB.degree(n.id);
          const baseR = Math.min(5.2, 1.55 + 0.52 * Math.sqrt(deg) + (isWorldChanging(n) ? 0.85 : 0));
          const grp = new T.Group();
          grp.position.set(laid.pos[i * 3], laid.pos[i * 3 + 1], laid.pos[i * 3 + 2]);

          const mat = new T.MeshPhongMaterial({
            color: 0xffffff,
            emissive: 0x000000,
            emissiveIntensity: 0.55,
            specular: 0xf8fafc,
            shininess: 95,
            transparent: true,
            opacity: 1,
          });
          const geom = geoms[n.type] || geoms.event;
          const mesh = new T.Mesh(geom, mat);
          if (n.type === 'item') mesh.scale.set(0.85 * baseR, 1.55 * baseR, 0.85 * baseR);
          else mesh.scale.setScalar(baseR);
          mesh.userData.id = n.id;
          grp.add(mesh);

          // Additive billboard glow halo
          const haloMat = new T.SpriteMaterial({
            map: glowTex,
            color: WB.colors.type[n.type] || '#888888',
            transparent: true,
            opacity: 0.68,
            blending: isDark ? T.AdditiveBlending : T.NormalBlending,
            depthWrite: false,
          });
          const halo = new T.Sprite(haloMat);
          halo.scale.setScalar(baseR * 5.2);
          grp.add(halo);

          // Planetary ring for locations
          let locRing = null;
          if (n.type === 'location') {
            locRing = new T.Mesh(locRingGeom, new T.MeshBasicMaterial({
              color: WB.colors.type.location,
              transparent: true,
              opacity: 0.55,
            }));
            locRing.scale.setScalar(baseR);
            locRing.rotation.x = Math.PI * 0.36;
            locRing.rotation.y = 0.3;
            grp.add(locRing);
          }

          // Pulsing orbital rings for world-changing / crucial events
          const orbitRings = [];
          if (isWorldChanging(n)) {
            const ringA = new T.Mesh(orbitRingGeomA, new T.MeshBasicMaterial({
              color: '#facc15',
              transparent: true,
              opacity: 0.65,
              blending: isDark ? T.AdditiveBlending : T.NormalBlending,
              depthWrite: false,
            }));
            ringA.scale.setScalar(baseR);
            ringA.rotation.x = Math.PI * 0.42;
            grp.add(ringA);
            orbitRings.push(ringA);

            const ringB = new T.Mesh(orbitRingGeomB, new T.MeshBasicMaterial({
              color: '#38bdf8',
              transparent: true,
              opacity: 0.48,
              blending: isDark ? T.AdditiveBlending : T.NormalBlending,
              depthWrite: false,
            }));
            ringB.scale.setScalar(baseR);
            ringB.rotation.x = -Math.PI * 0.28;
            ringB.rotation.y = Math.PI * 0.35;
            grp.add(ringB);
            orbitRings.push(ringB);
          }

          nodeGroup.add(grp);
          const obj = {
            node: n,
            group: grp,
            mesh,
            halo,
            locRing,
            orbitRings,
            r: baseR,
            fromPos: grp.position.clone(),
            toPos: grp.position.clone(),
          };
          nodeObjs.push(obj);
          nodeById.set(n.id, obj);
          pickables.push(mesh);
          posOf.set(n.id, grp.position);
        });

        morphT = 1;
        applyVisibility();
        fit(false);
      }

      const shown = (n) => WB.passes(n);

      function applyVisibility() {
        let visNodes = 0;
        nodeObjs.forEach((o) => {
          const v = shown(o.node);
          o.group.visible = v;
          if (v) visNodes++;
        });
        buildEdges();
        restyle();
        countEl.textContent = visNodes + ' nodes · ' + edgeCache.length + ' edges';
      }

      const CURVE_SEGS = 6;
      const _mid = new T.Vector3();
      const _dir = new T.Vector3();
      const _perp = new T.Vector3();
      const _up = new T.Vector3(0, 1, 0);

      function computeEdgeCtrl(ec) {
        const a = ec.a;
        const b = ec.b;
        _mid.addVectors(a, b).multiplyScalar(0.5);
        _dir.subVectors(b, a);
        const len = _dir.length() || 1;
        // Subtle curve arc; flatter in Strata so vertical causal beams pierce cleanly.
        const bend = opts.layout === 'strata' ? Math.min(8, len * 0.06) : Math.min(18, len * 0.14);
        _perp.crossVectors(_dir, _up);
        if (_perp.lengthSq() < 0.01) _perp.set(1, 0, 0);
        _perp.normalize();
        ec.ctrl.copy(_mid).addScaledVector(_perp, bend * (ec.isMemory ? -1.1 : 0.75));
        ec.ctrl.y += bend * 0.35;
      }

      function buildEdges() {
        edgeGroup.children.slice().forEach((c) => {
          edgeGroup.remove(c);
          c.geometry.dispose();
          c.material.dispose();
        });
        solidLines = null;
        memoryLines = null;
        if (arrows) {
          scene.remove(arrows);
          arrows.material.dispose();
          arrows = null;
        }

        const visibleEdges = WB.edges.filter((e) =>
          edgeVisible(e) && posOf.has(e.source) && posOf.has(e.target) &&
          shown(byId.get(e.source)) && shown(byId.get(e.target)));

        edgeCache = visibleEdges.map((e) => ({
          e,
          a: posOf.get(e.source),
          b: posOf.get(e.target),
          ctrl: new T.Vector3(),
          isCausal: !!e.causal,
          isMemory: !!e.memory,
          role: 'normal',
        }));

        const solidList = [];
        const memoryList = [];
        const causalList = [];
        edgeCache.forEach((ec) => {
          computeEdgeCtrl(ec);
          if (ec.isMemory) memoryList.push(ec);
          else solidList.push(ec);
          if (ec.isCausal) causalList.push(ec);
        });

        const makeCurveLines = (list, dashed) => {
          const vertsPerEdge = CURVE_SEGS * 2;
          const g = new T.BufferGeometry();
          g.setAttribute('position', new T.BufferAttribute(new Float32Array(list.length * vertsPerEdge * 3), 3));
          g.setAttribute('color', new T.BufferAttribute(new Float32Array(list.length * vertsPerEdge * 3), 3));
          const m = dashed
            ? new T.LineDashedMaterial({ vertexColors: true, dashSize: 3.0, gapSize: 2.2, transparent: true, opacity: 0.85 })
            : new T.LineBasicMaterial({ vertexColors: true, transparent: true, opacity: 0.78 });
          const lines = new T.LineSegments(g, m);
          lines.userData.list = list;
          lines.userData.dashed = dashed;
          edgeGroup.add(lines);
          return lines;
        };

        solidLines = makeCurveLines(solidList, false);
        memoryLines = makeCurveLines(memoryList, true);

        arrows = new T.InstancedMesh(
          arrowCone,
          new T.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.92 }),
          Math.max(1, causalList.length)
        );
        arrows.count = causalList.length;
        arrows.userData.list = causalList;
        scene.add(arrows);

        syncEdgesToNodePositions();
        seedParticles();
      }

      const _m4 = new T.Matrix4();
      const _q = new T.Quaternion();
      const _pt = new T.Vector3();
      const _tan = new T.Vector3();
      const _sc = new T.Vector3(0.95, 0.95, 0.95);

      function syncEdgesToNodePositions() {
        edgeCache.forEach((ec) => computeEdgeCtrl(ec));
        [solidLines, memoryLines].forEach((lines) => {
          if (!lines) return;
          const list = lines.userData.list;
          const arr = lines.geometry.attributes.position.array;
          let ptr = 0;
          for (let i = 0; i < list.length; i++) {
            const ec = list[i];
            const a = ec.a; const b = ec.b; const c = ec.ctrl;
            let px = a.x; let py = a.y; let pz = a.z;
            for (let s = 1; s <= CURVE_SEGS; s++) {
              const u = s / CURVE_SEGS;
              const inv = 1 - u;
              const nx = inv * inv * a.x + 2 * inv * u * c.x + u * u * b.x;
              const ny = inv * inv * a.y + 2 * inv * u * c.y + u * u * b.y;
              const nz = inv * inv * a.z + 2 * inv * u * c.z + u * u * b.z;
              arr[ptr++] = px; arr[ptr++] = py; arr[ptr++] = pz;
              arr[ptr++] = nx; arr[ptr++] = ny; arr[ptr++] = nz;
              px = nx; py = ny; pz = nz;
            }
          }
          lines.geometry.attributes.position.needsUpdate = true;
          if (lines.userData.dashed) lines.computeLineDistances();
        });

        if (arrows && arrows.count > 0) {
          const list = arrows.userData.list;
          for (let i = 0; i < list.length; i++) {
            const ec = list[i];
            const targetObj = nodeById.get(ec.e.target);
            // Tangent at u = 1 of quadratic Bezier is 2*(B - C)
            _tan.subVectors(ec.b, ec.ctrl);
            if (_tan.lengthSq() < 1e-4) _tan.subVectors(ec.b, ec.a);
            _tan.normalize();
            _pt.copy(ec.b).addScaledVector(_tan, -((targetObj ? targetObj.r : 2) + 1.5));
            _q.setFromUnitVectors(_up, _tan);
            _m4.compose(_pt, _q, _sc);
            arrows.setMatrixAt(i, _m4);
          }
          arrows.instanceMatrix.needsUpdate = true;
        }
      }

      // ---- Styling & Lineage Highlighting ----
      function dimmed(hex, amount) { return new T.Color(hex).lerp(bg, amount); }

      function restyle() {
        const f = WB.focus();
        const active = !!f.id && nodeById.has(f.id);
        const hl = f.hl;
        const inUp = (id) => f.up.has(id);
        const inDown = (id) => f.down.has(id);

        nodeObjs.forEach((o) => {
          const id = o.node.id;
          let c;
          let scaleMult = 1;
          let em = 0.58;
          let opacity = 1.0;
          let haloOpacity = isDark ? 0.78 : 0.42;

          if (active && id === f.id) {
            c = new T.Color(WB.colors.lineage.selected);
            scaleMult = 1.48;
            em = 0.85;
            haloOpacity = isDark ? 1.0 : 0.75;
          } else if (active && inUp(id)) {
            c = new T.Color('#38bdf8');
            scaleMult = 1.18;
            em = 0.68;
            haloOpacity = isDark ? 0.88 : 0.55;
          } else if (active && inDown(id)) {
            c = new T.Color('#fb923c');
            scaleMult = 1.18;
            em = 0.68;
            haloOpacity = isDark ? 0.88 : 0.55;
          } else if (active) {
            c = dimmed(WB.colors.type[o.node.type] || '#888888', 0.65);
            opacity = 0.28;
            em = 0.08;
            haloOpacity = 0.08;
          } else {
            c = new T.Color(WB.colors.type[o.node.type] || '#888888');
          }

          if (hl && hl.has(id)) {
            c = new T.Color('#ffffff');
            scaleMult = 1.42;
            em = 0.88;
            opacity = 1.0;
            haloOpacity = 1.0;
          }

          o.mesh.material.color.copy(c);
          o.mesh.material.emissive.copy(c);
          o.mesh.material.emissiveIntensity = em;
          o.mesh.material.opacity = opacity;
          if (o.node.type === 'item') {
            o.mesh.scale.set(0.85 * o.r * scaleMult, 1.55 * o.r * scaleMult, 0.85 * o.r * scaleMult);
          } else {
            o.mesh.scale.setScalar(o.r * scaleMult);
          }
          if (o.halo) {
            o.halo.material.color.copy(c);
            o.halo.material.opacity = haloOpacity;
            o.halo.scale.setScalar(o.r * scaleMult * 5.4);
          }
          if (o.locRing) {
            o.locRing.material.color.copy(c);
            o.locRing.material.opacity = opacity * 0.55;
            o.locRing.scale.setScalar(o.r * scaleMult);
          }
          o.orbitRings.forEach((ring) => {
            ring.material.opacity = opacity * 0.62;
            ring.scale.setScalar(o.r * scaleMult);
          });
        });

        const edgeColour = (ec) => {
          const s = ec.e.source;
          const t = ec.e.target;
          if (active) {
            const upSide = (s === f.id || inUp(s)) && (t === f.id || inUp(t));
            const downSide = (s === f.id || inDown(s)) && (t === f.id || inDown(t));
            if (upSide) { ec.role = 'up'; return new T.Color('#38bdf8'); }
            if (downSide) { ec.role = 'down'; return new T.Color('#fb923c'); }
            ec.role = 'dim';
            return dimmed(ec.isCausal ? WB.colors.edge.causes : ec.isMemory ? WB.colors.edge['leaves-trace'] : WB.colors.edge.other, 0.88);
          }
          ec.role = 'normal';
          if (ec.isCausal) return new T.Color(WB.colors.edge.causes).lerp(new T.Color('#ffffff'), isDark ? 0.28 : 0.05);
          if (ec.isMemory) return new T.Color(WB.colors.edge['leaves-trace']);
          return dimmed(WB.colors.edge.other, 0.55);
        };

        const vertsPerEdge = CURVE_SEGS * 2;
        [solidLines, memoryLines].forEach((lines) => {
          if (!lines) return;
          const list = lines.userData.list;
          const arr = lines.geometry.attributes.color.array;
          for (let i = 0; i < list.length; i++) {
            const c = edgeColour(list[i]);
            let ptr = i * vertsPerEdge * 3;
            for (let v = 0; v < vertsPerEdge; v++) {
              arr[ptr++] = c.r; arr[ptr++] = c.g; arr[ptr++] = c.b;
            }
          }
          lines.geometry.attributes.color.needsUpdate = true;
        });

        if (arrows && arrows.count > 0) {
          arrows.userData.list.forEach((ec, i) => arrows.setColorAt(i, edgeColour(ec)));
          if (arrows.instanceColor) arrows.instanceColor.needsUpdate = true;
        }

        legend.replaceChildren(...(active ? [
          el('div', {}, el('span', { class: 'sw', style: 'border-color:' + WB.colors.lineage.selected }), 'Selected node'),
          el('div', {}, el('span', { class: 'sw', style: 'border-color:#38bdf8' }), 'Upstream surge (causes, origins)'),
          el('div', {}, el('span', { class: 'sw', style: 'border-color:#fb923c' }), 'Downstream ignition (effects, traces)'),
          el('div', { class: 'gv-legend-keys', text: 'Keys: ←/→ or A/D neighbours · ↑/↓ or W/S up/down · F fly · Space tour · 1-4 layouts' }),
        ] : [
          el('div', {}, el('span', { class: 'sw', style: 'border-color:' + WB.colors.edge.causes }), 'Causal stream (arrow = effect)'),
          el('div', {}, el('span', { class: 'sw dash', style: 'border-color:' + WB.colors.edge['leaves-trace'] }), 'Memory wisp (event → tradition)'),
          el('div', { class: 'gv-legend-keys', text: 'Double-click to fly · 1-4 layouts · Space tour · R reset' }),
        ]));
        dirty = true;
      }

      // ---- Damped Spring-Physics Camera & Presets ----
      function applyCameraInstant() {
        cam.theta = camGoal.theta;
        cam.phi = camGoal.phi;
        cam.dist = camGoal.dist;
        cam.target.copy(camGoal.target);
      }

      function placeCamera() {
        const sp = Math.sin(cam.phi);
        camera.position.set(
          cam.target.x + cam.dist * sp * Math.sin(cam.theta),
          cam.target.y + cam.dist * Math.cos(cam.phi),
          cam.target.z + cam.dist * sp * Math.cos(cam.theta)
        );
        camera.lookAt(cam.target);
        camera.updateMatrixWorld();
      }

      function fitTargetBounds(flatPos) {
        const c = new T.Vector3();
        const n = flatPos.length / 3;
        if (!n) return;
        for (let i = 0; i < n; i++) {
          c.x += flatPos[i * 3];
          c.y += flatPos[i * 3 + 1];
          c.z += flatPos[i * 3 + 2];
        }
        c.divideScalar(n);
        let rad = 24;
        const p = new T.Vector3();
        for (let i = 0; i < n; i++) {
          p.set(flatPos[i * 3], flatPos[i * 3 + 1], flatPos[i * 3 + 2]);
          rad = Math.max(rad, p.distanceTo(c));
        }
        camGoal.target.copy(c);
        camGoal.dist = Math.min(2600, Math.max(45, (rad * 1.22) / Math.tan((camera.fov * Math.PI) / 360)));
        if (reducedMotion) applyCameraInstant();
        dirty = true;
      }

      function fit(animate) {
        const pts = nodeObjs.filter((o) => o.group.visible).map((o) => o.group.position);
        const c = new T.Vector3();
        pts.forEach((p) => c.add(p));
        if (pts.length) c.divideScalar(pts.length);
        let rad = 24;
        pts.forEach((p) => { rad = Math.max(rad, p.distanceTo(c)); });
        camGoal.target.copy(c);
        camGoal.dist = Math.min(2600, Math.max(45, (rad * 1.22) / Math.tan((camera.fov * Math.PI) / 360)));
        if (!animate || reducedMotion) applyCameraInstant();
        dirty = true;
      }

      function setCameraPreset(preset) {
        if (preset === 'iso') {
          camGoal.theta = 0.72;
          camGoal.phi = 1.08;
        } else if (preset === 'top') {
          camGoal.theta = 0;
          camGoal.phi = 0.14;
        }
        if (reducedMotion) applyCameraInstant();
        dirty = true;
      }

      function flyToNode(id) {
        const obj = nodeById.get(id);
        if (!obj || !obj.group.visible) return;
        camGoal.target.copy(obj.group.position);
        camGoal.dist = Math.max(36, Math.min(72, obj.r * 13));
        camGoal.phi = Math.max(0.55, Math.min(1.45, camGoal.phi));
        if (reducedMotion) applyCameraInstant();
        dirty = true;
      }

      function size() {
        const w = Math.max(50, stage.clientWidth);
        const h = Math.max(50, stage.clientHeight);
        renderer.setSize(w, h, false);
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
        dirty = true;
      }

      // ---- Causal Tour / Playback Mode ----
      const tour = { active: false, paused: false, list: [], index: 0, timer: 0, interval: 4.4 };

      function buildTourList() {
        const f = WB.focus();
        let ids = [];
        if (f.id && posOf.has(f.id)) {
          ids = [...f.up, f.id, ...f.down].filter((id) => {
            const o = nodeById.get(id);
            return o && o.group.visible;
          });
        }
        if (ids.length < 2) {
          // Fall back to world-changing / major events or top-degree visible events chronologically
          const vis = nodeObjs.filter((o) => o.group.visible).map((o) => o.node);
          const majors = vis.filter((n) => isMajorEvent(n));
          const pool = majors.length >= 2 ? majors : vis.filter((n) => n.type === 'event');
          const chosen = pool.length ? pool : vis;
          ids = chosen
            .slice()
            .sort((a, b) => WB.degree(b.id) - WB.degree(a.id))
            .slice(0, 14)
            .map((n) => n.id);
        }
        ids.sort((a, b) => {
          const na = byId.get(a); const nb = byId.get(b);
          const ta = na && na.t !== null && na.t !== undefined ? na.t : 1e15;
          const tb = nb && nb.t !== null && nb.t !== undefined ? nb.t : 1e15;
          return ta - tb || a.localeCompare(b);
        });
        return ids;
      }

      function renderTourStep() {
        if (!tour.active || !tour.list.length) return;
        const id = tour.list[tour.index];
        const n = byId.get(id);
        if (!n) return;
        tour.timer = 0;
        WB.select(id);
        flyToNode(id);
        tourStepEl.textContent = 'Causal Tour · Step ' + (tour.index + 1) + ' / ' + tour.list.length;
        tourNameEl.textContent = n.name;
        const metaParts = [n.type];
        if (n.date_label) metaParts.push(n.date_label);
        else if (n.t !== null && n.t !== undefined) metaParts.push(fmtT(n.t));
        if (n.era) metaParts.push(n.era);
        tourMetaEl.textContent = metaParts.join(' · ');
        tourSummaryEl.textContent = n.summary || 'A key moment along this world’s causal web.';
        tourBar.hidden = false;
        syncHudState();
      }

      function startTour() {
        const list = buildTourList();
        if (!list.length) return;
        tour.list = list;
        const curIdx = WB.state.selected ? list.indexOf(WB.state.selected) : 0;
        tour.index = curIdx >= 0 ? curIdx : 0;
        tour.active = true;
        tour.paused = false;
        tour.timer = 0;
        renderTourStep();
      }

      function toggleTour() {
        if (!tour.active) startTour();
        else toggleTourPause();
      }

      function toggleTourPause() {
        if (!tour.active) return;
        tour.paused = !tour.paused;
        tour.timer = 0;
        syncHudState();
      }

      function stepTour(delta) {
        if (!tour.active || !tour.list.length) return;
        tour.index = (tour.index + delta + tour.list.length) % tour.list.length;
        renderTourStep();
      }

      function stopTour() {
        tour.active = false;
        tour.paused = false;
        tourBar.hidden = true;
        syncHudState();
      }

      // ---- Keyboard Graph Surfing ----
      function surfGraph(direction) {
        const cur = WB.state.selected;
        if (!cur || !nodeById.has(cur)) {
          // Pick highest-degree visible node
          const top = nodeObjs.filter((o) => o.group.visible)
            .sort((a, b) => WB.degree(b.node.id) - WB.degree(a.node.id))[0];
          if (top) { WB.select(top.node.id); flyToNode(top.node.id); }
          return;
        }
        const incoming = (inn.get(cur) || [])
          .filter((e) => edgeVisible(e) && nodeById.has(e.source) && nodeById.get(e.source).group.visible)
          .map((e) => e.source);
        const outgoing = (out.get(cur) || [])
          .filter((e) => edgeVisible(e) && nodeById.has(e.target) && nodeById.get(e.target).group.visible)
          .map((e) => e.target);

        let targetId = null;
        if (direction === 'up' && incoming.length) {
          targetId = incoming[0];
        } else if (direction === 'down' && outgoing.length) {
          targetId = outgoing[0];
        } else {
          // Cycle neighbours (left/right)
          const allNbrs = [...new Set([...incoming, ...outgoing])];
          if (allNbrs.length) {
            const idx = allNbrs.indexOf(surfGraph.lastNbr);
            const nextIdx = direction === 'left'
              ? (idx <= 0 ? allNbrs.length - 1 : idx - 1)
              : (idx + 1) % allNbrs.length;
            targetId = allNbrs[nextIdx];
            surfGraph.lastNbr = cur;
          }
        }
        if (targetId) {
          WB.select(targetId);
          flyToNode(targetId);
        }
      }
      surfGraph.lastNbr = null;

      // ---- Pointer Controls & Raycasting ----
      const ptrs = new Map();
      let drag = null;
      const dom = renderer.domElement;
      const pinchDist = () => {
        const p = [...ptrs.values()];
        return p.length > 1 ? Math.hypot(p[0].x - p[1].x, p[0].y - p[1].y) : null;
      };

      dom.addEventListener('contextmenu', (e) => e.preventDefault());
      dom.addEventListener('pointerdown', (e) => {
        dom.setPointerCapture(e.pointerId);
        ptrs.set(e.pointerId, { x: e.clientX, y: e.clientY });
        drag = {
          x: e.clientX,
          y: e.clientY,
          moved: 0,
          pan: e.button === 2 || e.button === 1 || e.shiftKey,
          pinch: ptrs.size > 1 ? pinchDist() : null,
        };
        stage.focus({ preventScroll: true });
      });

      dom.addEventListener('pointermove', (e) => {
        if (ptrs.has(e.pointerId)) ptrs.set(e.pointerId, { x: e.clientX, y: e.clientY });
        if (drag && ptrs.size > 1) {
          const d = pinchDist();
          if (drag.pinch && d) {
            camGoal.dist = Math.min(3400, Math.max(12, camGoal.dist * (drag.pinch / d)));
            if (reducedMotion) applyCameraInstant();
            drag.pinch = d;
            drag.moved = 99;
            dirty = true;
          }
          return;
        }
        if (drag) {
          const dx = e.clientX - drag.x;
          const dy = e.clientY - drag.y;
          drag.moved += Math.abs(dx) + Math.abs(dy);
          drag.x = e.clientX;
          drag.y = e.clientY;
          if (drag.pan) {
            const k = (cam.dist * Math.tan((camera.fov * Math.PI) / 360) * 2) / Math.max(1, stage.clientHeight);
            const right = new T.Vector3().setFromMatrixColumn(camera.matrixWorld, 0);
            const upv = new T.Vector3().setFromMatrixColumn(camera.matrixWorld, 1);
            camGoal.target.addScaledVector(right, -dx * k).addScaledVector(upv, dy * k);
          } else {
            camGoal.theta -= dx * 0.0075;
            camGoal.phi = Math.min(Math.PI - 0.06, Math.max(0.06, camGoal.phi - dy * 0.0075));
          }
          if (reducedMotion) applyCameraInstant();
          dirty = true;
        } else {
          setHover(pick(e));
        }
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
      dom.addEventListener('dblclick', (e) => {
        const hit = pick(e);
        if (hit) {
          WB.select(hit);
          flyToNode(hit);
        }
      });
      dom.addEventListener('wheel', (e) => {
        e.preventDefault();
        camGoal.dist = Math.min(3400, Math.max(12, camGoal.dist * Math.exp(e.deltaY * 0.0012)));
        if (reducedMotion) applyCameraInstant();
        dirty = true;
      }, { passive: false });

      stage.addEventListener('keydown', (e) => {
        const tag = (e.target && e.target.tagName) || '';
        if (tag === 'INPUT' || tag === 'SELECT' || tag === 'TEXTAREA') return;
        const k = e.key;
        if (k === '1') setLayout('constellation');
        else if (k === '2') setLayout('helix');
        else if (k === '3') setLayout('strata');
        else if (k === '4') setLayout('orbital');
        else if (k === 'r' || k === 'R' || k === '0') fit(true);
        else if (k === 'f' || k === 'F') { if (WB.state.selected) flyToNode(WB.state.selected); }
        else if (k === ' ') toggleTour();
        else if (k === 'Escape') { if (tour.active) stopTour(); else WB.select(null); }
        else if (k === 'ArrowLeft' || k === 'a' || k === 'A') surfGraph('left');
        else if (k === 'ArrowRight' || k === 'd' || k === 'D') surfGraph('right');
        else if (k === 'ArrowUp' || k === 'w' || k === 'W') surfGraph('up');
        else if (k === 'ArrowDown' || k === 's' || k === 'S') surfGraph('down');
        else if (k === '+' || k === '=') { camGoal.dist = Math.max(12, camGoal.dist * 0.84); if (reducedMotion) applyCameraInstant(); }
        else if (k === '-') { camGoal.dist = Math.min(3400, camGoal.dist / 0.84); if (reducedMotion) applyCameraInstant(); }
        else return;
        e.preventDefault();
        dirty = true;
      });

      const ray = new T.Raycaster();
      let hover = null;

      function pick(e) {
        const r = dom.getBoundingClientRect();
        const v = new T.Vector2(
          ((e.clientX - r.left) / r.width) * 2 - 1,
          -((e.clientY - r.top) / r.height) * 2 + 1
        );
        ray.setFromCamera(v, camera);
        const visiblePickables = pickables.filter((m) => m.parent && m.parent.visible);
        const hit = ray.intersectObjects(visiblePickables, false)[0];
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
        if (n) {
          const col = WB.colors.type[n.type] || '#888888';
          const upCount = (inn.get(n.id) || []).filter((e) => e.causal || e.memory).length;
          const downCount = (out.get(n.id) || []).filter((e) => e.causal || e.memory).length;
          const meta = [];
          if (n.date_label) meta.push(n.date_label);
          else if (n.t !== null && n.t !== undefined) meta.push(fmtT(n.t));
          if (n.era) meta.push(n.era);
          tip.replaceChildren(
            el('div', { class: 'gv-tip-head' },
              el('span', { class: 'gv-tip-badge', style: 'color:' + col, text: (WB.typeGlyph[n.type] || '?') + ' ' + n.type }),
              el('span', { class: 'gv-tip-title', text: n.name })),
            meta.length ? el('div', { class: 'gv-tip-meta', text: meta.join(' · ') }) : null,
            n.summary ? el('p', { class: 'gv-tip-summary', text: n.summary }) : null,
            el('div', { class: 'gv-tip-stats' },
              el('span', { class: 'gv-tip-up', text: '↑ ' + upCount + ' causes' }),
              el('span', { class: 'gv-tip-down', text: '↓ ' + downCount + ' effects' }))
          );
          moveTip();
        }
        dirty = true;
      }

      function moveTip() {
        const p = pick.last || { x: 0, y: 0 };
        const maxLeft = Math.max(12, stage.clientWidth - 280);
        const maxTop = Math.max(12, stage.clientHeight - 150);
        tip.style.left = Math.min(p.x + 16, maxLeft) + 'px';
        tip.style.top = Math.min(p.y + 16, maxTop) + 'px';
      }

      // ---- Live 2D Canvas 3D-Projected Radar Minimap ----
      let radarDots = [];

      function drawRadar() {
        if (!radarCtx || radarWrap.offsetParent === null) return;
        const sizePx = 276;
        const cx = sizePx / 2;
        const cy = sizePx / 2;
        const rad = sizePx / 2 - 10;
        radarCtx.clearRect(0, 0, sizePx, sizePx);

        // Background disc
        radarCtx.save();
        radarCtx.beginPath();
        radarCtx.arc(cx, cy, rad, 0, Math.PI * 2);
        radarCtx.fillStyle = isDark ? 'rgba(10, 14, 24, 0.72)' : 'rgba(241, 245, 249, 0.82)';
        radarCtx.fill();
        radarCtx.clip();

        // Concentric radar rings & crosshair
        radarCtx.strokeStyle = isDark ? 'rgba(148, 163, 184, 0.18)' : 'rgba(71, 85, 105, 0.2)';
        radarCtx.lineWidth = 1.5;
        [0.33, 0.66, 1.0].forEach((f) => {
          radarCtx.beginPath();
          radarCtx.arc(cx, cy, rad * f, 0, Math.PI * 2);
          radarCtx.stroke();
        });
        radarCtx.beginPath();
        radarCtx.moveTo(cx - rad, cy); radarCtx.lineTo(cx + rad, cy);
        radarCtx.moveTo(cx, cy - rad); radarCtx.lineTo(cx, cy + rad);
        radarCtx.stroke();

        // Compute XZ bounds of visible nodes
        let maxExtent = 40;
        let meanX = 0; let meanZ = 0; let visCount = 0;
        nodeObjs.forEach((o) => {
          if (!o.group.visible) return;
          meanX += o.group.position.x;
          meanZ += o.group.position.z;
          visCount++;
        });
        if (visCount) { meanX /= visCount; meanZ /= visCount; }
        nodeObjs.forEach((o) => {
          if (!o.group.visible) return;
          const dx = o.group.position.x - meanX;
          const dz = o.group.position.z - meanZ;
          maxExtent = Math.max(maxExtent, Math.hypot(dx, dz) * 1.15);
        });
        const scale = (rad - 12) / maxExtent;
        const toRx = (x) => cx + (x - meanX) * scale;
        const toRy = (z) => cy + (z - meanZ) * scale;

        // Camera frustum cone
        const camRx = toRx(camera.position.x);
        const camRy = toRy(camera.position.z);
        const tgtRx = toRx(cam.target.x);
        const tgtRy = toRy(cam.target.z);
        const ang = Math.atan2(tgtRy - camRy, tgtRx - camRx);
        const fovHalf = 0.44;
        radarCtx.beginPath();
        radarCtx.moveTo(camRx, camRy);
        radarCtx.arc(camRx, camRy, 68, ang - fovHalf, ang + fovHalf);
        radarCtx.closePath();
        radarCtx.fillStyle = isDark ? 'rgba(56, 189, 248, 0.16)' : 'rgba(0, 114, 178, 0.15)';
        radarCtx.fill();

        // Faint edges
        radarCtx.strokeStyle = isDark ? 'rgba(148, 163, 184, 0.18)' : 'rgba(71, 85, 105, 0.2)';
        radarCtx.lineWidth = 1;
        radarCtx.beginPath();
        for (let i = 0; i < edgeCache.length; i++) {
          const ec = edgeCache[i];
          if (!ec.isCausal) continue;
          radarCtx.moveTo(toRx(ec.a.x), toRy(ec.a.z));
          radarCtx.lineTo(toRx(ec.b.x), toRy(ec.b.z));
        }
        radarCtx.stroke();

        // Nodes
        const f = WB.focus();
        radarDots = [];
        nodeObjs.forEach((o) => {
          if (!o.group.visible) return;
          const rx = toRx(o.group.position.x);
          const ry = toRy(o.group.position.z);
          const id = o.node.id;
          let dotR = 3.2;
          let col = WB.colors.type[o.node.type] || '#94a3b8';
          if (f.id === id) { dotR = 6.2; col = WB.colors.lineage.selected; }
          else if (f.up.has(id)) { dotR = 4.6; col = '#38bdf8'; }
          else if (f.down.has(id)) { dotR = 4.6; col = '#fb923c'; }
          else if (f.id) { dotR = 2.4; col = isDark ? 'rgba(148,163,184,0.35)' : 'rgba(100,116,139,0.35)'; }
          radarCtx.beginPath();
          radarCtx.arc(rx, ry, dotR, 0, Math.PI * 2);
          radarCtx.fillStyle = col;
          radarCtx.fill();
          radarDots.push({ id, x: rx / 2, y: ry / 2 });
        });

        // Camera dot
        radarCtx.beginPath();
        radarCtx.arc(camRx, camRy, 4.5, 0, Math.PI * 2);
        radarCtx.fillStyle = '#38bdf8';
        radarCtx.fill();
        radarCtx.restore();
      }

      radarCanvas.addEventListener('click', (e) => {
        const r = radarCanvas.getBoundingClientRect();
        const mx = e.clientX - r.left;
        const my = e.clientY - r.top;
        let best = null;
        let bestD = 16;
        radarDots.forEach((d) => {
          const dist = Math.hypot(d.x - mx, d.y - my);
          if (dist < bestD) { bestD = dist; best = d.id; }
        });
        if (best) {
          WB.select(best);
          flyToNode(best);
        }
      });

      // ---- 3D Projected Labels ----
      const labelPool = [];
      const _vProj = new T.Vector3();

      function updateLabels() {
        const f = WB.focus();
        const w = stage.clientWidth;
        const h = stage.clientHeight;
        const wanted = [];
        const add = (id, cls) => {
          if (id && posOf.has(id) && !wanted.some((x) => x.id === id)) wanted.push({ id, cls });
        };
        add(f.id, 'sel');
        add(hover, 'sel');
        if (f.hl) f.hl.forEach((id) => add(id, 'sel'));
        if (f.id) {
          [...f.up].slice(0, 12).forEach((id) => add(id, 'up'));
          [...f.down].slice(0, 12).forEach((id) => add(id, 'down'));
        } else {
          nodeObjs
            .filter((o) => o.group.visible)
            .sort((a, b) => WB.degree(b.node.id) - WB.degree(a.node.id))
            .slice(0, 12)
            .forEach((o) => add(o.node.id, ''));
        }

        const boxes = [];
        let used = 0;
        wanted.forEach((wnt) => {
          const o = nodeById.get(wnt.id);
          if (!o || !o.group.visible) return;
          _vProj.copy(o.group.position).project(camera);
          if (_vProj.z > 1 || Math.abs(_vProj.x) > 0.98 || Math.abs(_vProj.y) > 0.96) return;
          const x = (_vProj.x * 0.5 + 0.5) * w;
          const y = (-_vProj.y * 0.5 + 0.5) * h + o.r * 2 + 6;
          const text = (wnt.cls === 'up' ? '↑ ' : wnt.cls === 'down' ? '↓ ' : '') + o.node.name;
          const bw = text.length * 6.4 + 14;
          const box = { x0: x - bw / 2, x1: x + bw / 2, y0: y, y1: y + 18 };
          const forced = wnt.cls === 'sel';
          if (!forced && boxes.some((b) => box.x0 < b.x1 && box.x1 > b.x0 && box.y0 < b.y1 && box.y1 > b.y0)) return;
          boxes.push(box);
          let d = labelPool[used];
          if (!d) { d = el('div', { class: 'gv-label' }); labelBox.appendChild(d); labelPool.push(d); }
          d.hidden = false;
          d.textContent = text;
          d.className = 'gv-label' + (wnt.id === f.id ? ' sel' : wnt.cls ? ' ' + wnt.cls : '');
          d.style.left = x + 'px';
          d.style.top = y + 'px';
          used++;
        });

        // Era plane floating badges when era planes are visible
        if (eraGroup.visible) {
          eraPlanesData.forEach((pl) => {
            _vProj.copy(pl.labelPos).project(camera);
            if (_vProj.z > 1 || Math.abs(_vProj.x) > 0.96 || Math.abs(_vProj.y) > 0.94) return;
            const x = (_vProj.x * 0.5 + 0.5) * w;
            const y = (-_vProj.y * 0.5 + 0.5) * h - 9;
            let d = labelPool[used];
            if (!d) { d = el('div', { class: 'gv-label' }); labelBox.appendChild(d); labelPool.push(d); }
            d.hidden = false;
            d.textContent = pl.name;
            d.className = 'gv-label era';
            d.style.left = x + 'px';
            d.style.top = y + 'px';
            used++;
          });
        }

        for (let i = used; i < labelPool.length; i++) labelPool[i].hidden = true;
      }

      // ---- Main Animation Loop ----
      let dirty = true;
      let raf = 0;
      let lastTime = performance.now();
      let elapsed = 0;

      function frame(now) {
        raf = requestAnimationFrame(frame);
        if (!container.isConnected || container.hidden) return;
        const dt = Math.min(0.05, Math.max(0.001, ((now || performance.now()) - lastTime) / 1000));
        lastTime = now || performance.now();
        elapsed += dt;

        let needsRender = dirty;

        // Causal tour auto-advance
        if (tour.active && !tour.paused && tour.list.length > 1) {
          tour.timer += dt;
          if (tour.timer >= tour.interval) stepTour(1);
        }

        if (!reducedMotion) {
          // Gentle auto-orbit when idle
          if (opts.autoOrbit && !drag) {
            camGoal.theta += dt * 0.085;
            needsRender = true;
          }
          // Spring-damped camera smoothing
          const damp = 1 - Math.exp(-9.5 * dt);
          const dTheta = camGoal.theta - cam.theta;
          const dPhi = camGoal.phi - cam.phi;
          const dDist = camGoal.dist - cam.dist;
          const dTgt = camGoal.target.distanceTo(cam.target);
          if (Math.abs(dTheta) > 1e-4 || Math.abs(dPhi) > 1e-4 || Math.abs(dDist) > 1e-2 || dTgt > 1e-2) {
            cam.theta += dTheta * damp;
            cam.phi += dPhi * damp;
            cam.dist += dDist * damp;
            cam.target.lerp(camGoal.target, damp);
            needsRender = true;
          }
          // Smooth 3D layout morphing
          if (morphT < 1) {
            morphT = Math.min(1, morphT + dt / MORPH_DURATION);
            const ease = 1 - Math.pow(1 - morphT, 3);
            nodeObjs.forEach((o) => {
              o.group.position.lerpVectors(o.fromPos, o.toPos, ease);
            });
            syncEdgesToNodePositions();
            needsRender = true;
          }
          // Ambient cosmic drift, node ring spins, and particle flow
          if (starPoints) starPoints.rotation.y += dt * 0.008;
          if (nebulaPoints) nebulaPoints.rotation.y -= dt * 0.012;
          nodeObjs.forEach((o, i) => {
            if (!o.group.visible) return;
            o.mesh.rotation.y += dt * 0.25;
            if (o.orbitRings.length) {
              o.orbitRings[0].rotation.z += dt * 0.85;
              if (o.orbitRings[1]) o.orbitRings[1].rotation.z -= dt * 0.62;
            }
            if (o.halo && WB.state.selected === o.node.id) {
              const pulse = 1 + 0.14 * Math.sin(elapsed * 4.5 + i);
              o.halo.scale.setScalar(o.r * 1.48 * 4.4 * pulse);
            }
          });
          // Expanding 3D shockwaves
          for (let i = shockwaves.length - 1; i >= 0; i--) {
            const sw = shockwaves[i];
            sw.age += dt;
            if (sw.age < 0) { sw.mesh.visible = false; continue; }
            sw.mesh.visible = true;
            const p = sw.age / sw.duration;
            if (p >= 1) {
              fxGroup.remove(sw.mesh);
              sw.mesh.material.dispose();
              shockwaves.splice(i, 1);
            } else {
              const e = 1 - Math.pow(1 - p, 2.5);
              sw.mesh.scale.setScalar(2 + e * sw.maxScale);
              sw.mesh.material.opacity = (1 - p) * 0.82;
            }
          }
          if (opts.fxIntensity > 0 && activeParticleCount > 0) {
            updateParticles(dt, elapsed);
            needsRender = true;
          }
          needsRender = true;
        }

        if (!needsRender) return;
        dirty = false;
        placeCamera();
        renderer.render(scene, camera);
        updateLabels();
        drawRadar();
      }

      // ---- Theme & WB Lifecycle Hooks ----
      const mq = window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : null;
      if (mq && mq.addEventListener) mq.addEventListener('change', () => { themeBg(); restyle(); });
      WB.bus.on('theme', () => { themeBg(); restyle(); });
      WB.bus.on('highlight', () => restyle());

      this.onSelect = (id) => {
        restyle();
        if (id && posOf.has(id)) {
          spawnShockwave(posOf.get(id), WB.colors.lineage.selected);
          const v = posOf.get(id).clone().project(camera);
          if (Math.abs(v.x) > 0.88 || Math.abs(v.y) > 0.88) {
            camGoal.target.copy(posOf.get(id));
            if (reducedMotion) applyCameraInstant();
          }
        }
        dirty = true;
      };
      this.onFilter = () => { applyVisibility(); };
      this.activate = () => {
        size();
        dirty = true;
        lastTime = performance.now();
        if (!raf) raf = requestAnimationFrame(frame);
      };
      this.deactivate = () => {
        if (tour.active) stopTour();
      };
      this.resize = () => { if (!container.hidden) size(); };

      themeBg();
      syncHudState();
      rebuildGraph();
      size();
      raf = requestAnimationFrame(frame);
    },
  });
})();
