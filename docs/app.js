(() => {
  'use strict';

  // ---- Subtle interactive starfield backdrop
  const canvas = document.getElementById('starfield');
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (canvas && canvas.getContext) {
    const ctx = canvas.getContext('2d');
    let w = 0;
    let h = 0;
    const stars = Array.from({ length: 90 }, (_, i) => ({
      x: ((i * 73.13) % 100) / 100,
      y: ((i * 37.91) % 100) / 100,
      r: 0.6 + (i % 4) * 0.45,
      s: 0.00004 + (i % 5) * 0.000025,
      hue: i % 3 === 0 ? '#38bdf8' : i % 3 === 1 ? '#a78bfa' : '#f8fafc',
      a: 0.25 + (i % 5) * 0.12,
    }));
    const resize = () => {
      w = canvas.width = window.innerWidth;
      h = canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener('resize', resize);
    const draw = () => {
      ctx.clearRect(0, 0, w, h);
      for (const st of stars) {
        if (!reduced) {
          st.y -= st.s;
          if (st.y < 0) st.y = 1;
        }
        ctx.globalAlpha = st.a;
        ctx.fillStyle = st.hue;
        ctx.beginPath();
        ctx.arc(st.x * w, st.y * h, st.r, 0, Math.PI * 2);
        ctx.fill();
      }
      if (!reduced) requestAnimationFrame(draw);
    };
    draw();
  }

  // ---- Hero interactive video switcher
  const DEMOS = {
    '3d': {
      src: 'assets/demos/demo-3d-universe.mp4',
      poster: 'assets/demos/demo-3d-universe.png',
      caption: '<strong>3D Causal Universe</strong> — Morph between Constellation, Chronos Helix, Causal Strata, and Orbital Sphere with streaming causal particle FX and radar navigation.',
    },
    dataviz: {
      src: 'assets/demos/demo-dataviz.mp4',
      poster: 'assets/demos/demo-dataviz.png',
      caption: '<strong>Timeline, Map, Trade &amp; Life</strong> — Animated Bézier causal arcs, Era Density Scrubber, biome halo atlas, 3-column Trade Sankey, and Ecological Web.',
    },
    gallery: {
      src: 'assets/demos/demo-command-gallery.mp4',
      poster: 'assets/demos/demo-command-gallery.png',
      hasAudio: true,
      caption: '<strong>🔊 Gallery, Soundtrack &amp; Voices</strong> — Click <em>Unmute</em> to hear the looping Lyria ambient score and voiced characters (<em>Selene</em> &amp; <em>Lyra</em>) across 20 fal.ai artworks, Lightbox, and Telemetry HUD.',
    },
  };

  const demoVideo = document.getElementById('demo-video');
  const demoCaption = document.getElementById('demo-caption');
  const unmuteBtn = document.getElementById('stage-unmute');
  function syncUnmuteBtn() {
    if (!unmuteBtn || !demoVideo) return;
    const muted = demoVideo.muted;
    unmuteBtn.textContent = muted ? '🔇 Unmute Audio' : '🔊 Sound On';
    unmuteBtn.classList.toggle('unmuted', !muted);
  }
  unmuteBtn?.addEventListener('click', () => {
    if (!demoVideo) return;
    demoVideo.muted = !demoVideo.muted;
    if (!demoVideo.muted) demoVideo.play().catch(() => {});
    syncUnmuteBtn();
  });
  demoVideo?.addEventListener('volumechange', syncUnmuteBtn);

  document.querySelectorAll('.stage-tab').forEach((btn) => {
    btn.addEventListener('click', () => {
      const key = btn.dataset.demo;
      const d = DEMOS[key];
      if (!d || !demoVideo) return;
      document.querySelectorAll('.stage-tab').forEach((b) => {
        const on = b === btn;
        b.classList.toggle('active', on);
        b.setAttribute('aria-selected', String(on));
      });
      if (unmuteBtn) unmuteBtn.hidden = !d.hasAudio;
      if (!d.hasAudio) demoVideo.muted = true;
      demoVideo.poster = d.poster;
      const srcEl = demoVideo.querySelector('source');
      if (srcEl) srcEl.src = d.src;
      demoVideo.load();
      demoVideo.play().catch(() => {});
      syncUnmuteBtn();
      if (demoCaption) demoCaption.innerHTML = d.caption;
    });
  });

  // ---- Multi-agent install switcher
  const AGENTS = {
    agy: {
      title: 'Antigravity (Gemini) — Native Plugin + OAuth MCP',
      desc: 'Symlink or clone WorldBuilder into your plugins folder. Antigravity automatically discovers plugin.json, all 15 skills, and mcp_config.json (fal.ai browser OAuth — no API key needed).',
      code: `git clone https://github.com/gofastercloud/worldbuilder.git ~/worldbuilder\nln -s ~/worldbuilder ~/.gemini/config/plugins/worldbuilder`,
      note: 'Open Customizations → WorldBuilder to sign in to fal.ai via OAuth, then ask Antigravity to start a world or illustrate an entity.',
    },
    claude: {
      title: 'Claude Code & Cowork — Plugin + Slash Commands',
      desc: 'Load directly in Claude Code or upload as a Cowork plugin. Includes 11 /wb-* slash commands and .mcp.json wired to fal.ai OAuth.',
      code: `git clone https://github.com/gofastercloud/worldbuilder.git ~/worldbuilder\nclaude --plugin-dir ~/worldbuilder`,
      note: 'In Cowork: Customize → Plugins → upload the repo zip or add as a marketplace. Try /wb-wizard, /wb-visualise, or /wb-art.',
    },
    codex: {
      title: 'Codex / ChatGPT — Portable Skills Bundle',
      desc: 'Copy or symlink all 15 skill folders together into your Codex skills directory so compile, visualiser, and usage scripts share the vendored PyYAML library.',
      code: `git clone https://github.com/gofastercloud/worldbuilder.git ~/worldbuilder\nmkdir -p ~/.codex/skills\nln -s ~/worldbuilder/skills/* ~/.codex/skills/`,
      note: 'For artwork generation, add the remote Streamable HTTP MCP server https://mcp.fal.ai/mcp-relay with OAuth.',
    },
  };

  const agentPanel = document.getElementById('agent-panel');
  function renderAgent(key) {
    const a = AGENTS[key];
    if (!a || !agentPanel) return;
    agentPanel.innerHTML = '';
    const h3 = document.createElement('h3');
    h3.textContent = a.title;
    const p = document.createElement('p');
    p.textContent = a.desc;
    const wrap = document.createElement('div');
    wrap.className = 'code-wrap';
    const pre = document.createElement('pre');
    pre.className = 'code-block';
    const code = document.createElement('code');
    code.textContent = a.code;
    pre.appendChild(code);
    const copy = document.createElement('button');
    copy.type = 'button';
    copy.className = 'copy-btn';
    copy.textContent = 'Copy';
    copy.addEventListener('click', () => {
      navigator.clipboard?.writeText(a.code).then(() => {
        copy.textContent = 'Copied!';
        setTimeout(() => { copy.textContent = 'Copy'; }, 1400);
      });
    });
    wrap.append(pre, copy);
    const note = document.createElement('p');
    note.style.marginTop = '12px';
    note.style.marginBottom = '0';
    note.style.fontSize = '13.5px';
    note.textContent = a.note;
    agentPanel.append(h3, p, wrap, note);
  }

  document.querySelectorAll('.agent-tab').forEach((btn) => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.agent-tab').forEach((b) => {
        const on = b === btn;
        b.classList.toggle('active', on);
        b.setAttribute('aria-selected', String(on));
      });
      renderAgent(btn.dataset.agent);
    });
  });
  renderAgent('agy');

  // ---- 15 Skills Grid
  const SKILLS = [
    ['worldbuilding', 'Core contract, causal procedure, routing table & magic gate'],
    ['world-wizard', 'Guided or YOLO world creation, validated stage by stage'],
    ['geography-and-climate', 'Continents, terrain, biomes, climate profiles, flora & fauna'],
    ['economy-and-trade', 'Resources, currencies, trade routes, guilds & economic shocks'],
    ['peoples', 'Species, races, languages, lineages, factions & characters'],
    ['magic-systems', 'Hard/soft magic rules gated strictly by world_flags.magic'],
    ['history-and-events', 'Calendars, eras, timelines, causes, consequences & traces'],
    ['folklore-and-traditions', 'Myths, customs & taboos derived from real distorted events'],
    ['world-validate', 'Deterministic graph checker: links, lifespans, flags & causality'],
    ['world-visualiser', 'Single-file (or --serve) 3D Graph, Timeline, Terrain Map, Trade, Life, Gallery & Content Reader'],
    ['world-art', 'fal.ai OAuth MCP artwork, painted maps, soundtracks & character voices + cost ledger'],
    ['writing', 'Context-loaded chapters, dated short stories (event/myth/era) & D&D 5e campaigns'],
    ['world-review', '9 editorial personas (continuity, worldrules, pacing, prose…)'],
    ['prose-check', 'Stdlib Flesch-Kincaid, Gunning Fog, dialogue ratio & outliers'],
    ['world-compile', 'Export chapters into clean Markdown or single-file HTML manuscripts'],
  ];

  const skillsGrid = document.getElementById('skills-grid');
  if (skillsGrid) {
    SKILLS.forEach(([name, desc]) => {
      const card = document.createElement('div');
      card.className = 'skill-pill';
      const st = document.createElement('strong');
      st.textContent = name;
      const sp = document.createElement('span');
      sp.textContent = desc;
      card.append(st, sp);
      skillsGrid.appendChild(card);
    });
  }

  // ---- Artwork Lightbox
  const lb = document.getElementById('lightbox');
  const lbImg = document.getElementById('lb-img');
  const lbTitle = document.getElementById('lb-title');
  const lbSub = document.getElementById('lb-sub');
  const lbClose = document.getElementById('lb-close');

  function closeLb() {
    if (lb) lb.hidden = true;
  }
  document.querySelectorAll('.art-card').forEach((card) => {
    card.addEventListener('click', () => {
      if (!lb || !lbImg) return;
      lbImg.src = card.dataset.full || '';
      lbImg.alt = card.dataset.title || '';
      if (lbTitle) lbTitle.textContent = card.dataset.title || '';
      if (lbSub) lbSub.textContent = card.dataset.meta || '';
      lb.hidden = false;
    });
  });
  lbClose?.addEventListener('click', closeLb);
  lb?.addEventListener('click', (e) => { if (e.target === lb) closeLb(); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeLb(); });
})();
