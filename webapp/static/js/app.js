/* ═══════════════════════════════════════════════════════════════════════════
   WorldBuilder Web App — Frontend
   ═══════════════════════════════════════════════════════════════════════════ */

// ─── Lightweight Markdown → HTML ──────────────────────────────────────────

function renderMarkdown(src) {
  if (!src) return "";
  // Escape HTML entities to prevent XSS
  let text = src
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  // Ensure headings are always their own block by inserting blank lines
  // before and after any line starting with #
  text = text.replace(/([^\n])\n(#{1,6}\s)/g, "$1\n\n$2");  // blank line before
  text = text.replace(/(^#{1,6}\s.+)\n(?!#|\n)/gm, "$1\n\n");  // blank line after

  // Split into blocks by double-newline (paragraphs)
  const blocks = text.split(/\n{2,}/);
  const out = [];

  for (let block of blocks) {
    block = block.trim();
    if (!block) continue;

    // Headings (## … )
    const hMatch = block.match(/^(#{1,6})\s+(.*)$/);
    if (hMatch) {
      const level = hMatch[1].length;
      // Use h5/h6 in the panel to avoid clashing with panel section h4s
      const tag = `h${Math.min(level + 3, 6)}`;
      out.push(`<${tag}>${inlineMarkdown(hMatch[2])}</${tag}>`);
      continue;
    }

    // Unordered list (lines starting with - or *)
    if (/^[\-\*]\s/.test(block)) {
      const items = block.split(/\n/).map(line =>
        `<li>${inlineMarkdown(line.replace(/^[\-\*]\s+/, ""))}</li>`
      ).join("");
      out.push(`<ul>${items}</ul>`);
      continue;
    }

    // Ordered list (lines starting with 1. 2. etc.)
    if (/^\d+\.\s/.test(block)) {
      const items = block.split(/\n/).map(line =>
        `<li>${inlineMarkdown(line.replace(/^\d+\.\s+/, ""))}</li>`
      ).join("");
      out.push(`<ol>${items}</ol>`);
      continue;
    }

    // Regular paragraph — join soft line breaks within a block
    const paragraph = block.split(/\n/).join(" ");
    out.push(`<p>${inlineMarkdown(paragraph)}</p>`);
  }

  return out.join("\n");
}

function inlineMarkdown(text) {
  return text
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")        // **bold**
    .replace(/\*(.+?)\*/g, "<em>$1</em>")                     // *italic*
    .replace(/_(.+?)_/g, "<em>$1</em>")                        // _italic_
    .replace(/`(.+?)`/g, "<code>$1</code>")                    // `code`
    .replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2">$1</a>');   // [link](url)
}

// ─── State ────────────────────────────────────────────────────────────────
let currentProject = null;
let projectConfig = null;
let projectStats = null;
let currentEntityType = "all";
let currentEntities = [];
let allEntities = {};

const ENTITY_ICONS = {
  character: "👤", location: "📍", faction: "⚔️", item: "🔮",
  "magic-system": "✨", arc: "📖", event: "📅", species: "🧬",
  race: "👥", language: "🗣️", lineage: "👑", chapter: "📄",
};

// Image generation state
let imagegenAvailable = null; // null = unknown, true/false after check
let activeJobs = {};  // job_id -> {entityType, entitySlug, entityName}
let lastCompletionCheck = Date.now() / 1000;
let completionPollInterval = null;

const SIGNIFICANCE_COLORS = {
  "world-changing": "#f85149", major: "#d29922", moderate: "#58a6ff",
  minor: "#8b949e", trivial: "#484f58",
};

// ─── Init ─────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  loadProjects();
  setupSearch();
  setupSizePicker();
  checkImagegenStatus();
});

// ─── Navigation ───────────────────────────────────────────────────────────
function showPage(id) {
  document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
  document.getElementById(`page-${id}`).classList.add("active");
}

function showWelcome() {
  currentProject = null;
  showPage("welcome");
  document.getElementById("nav-project").style.display = "none";
  document.getElementById("nav-search").style.display = "none";
  closePanel();
  loadProjects();
}

// ─── Projects ─────────────────────────────────────────────────────────────
async function loadProjects() {
  const res = await fetch("/api/projects");
  const projects = await res.json();
  const grid = document.getElementById("project-list");

  if (projects.length === 0) {
    grid.innerHTML = `<div class="card" style="text-align:center; padding:40px; color:var(--text-2)">
      <p>No projects yet. Use the wizard or YOLO mode to create one!</p>
    </div>`;
    return;
  }

  grid.innerHTML = projects.map(p => `
    <div class="project-card" onclick="openProject('${p.slug}')">
      <h3>${p.title}</h3>
      <div class="meta">
        <span class="badge">${p.genre}</span>
        <span class="badge badge-outline">${p.type}</span>
      </div>
    </div>
  `).join("");
}

async function openProject(slug) {
  currentProject = slug;
  const res = await fetch(`/api/project/${slug}`);
  const data = await res.json();
  projectConfig = data.config;
  projectStats = data.stats;

  // Update nav
  document.getElementById("nav-project").style.display = "flex";
  document.getElementById("nav-project-name").textContent = projectConfig.title || slug;
  document.getElementById("nav-project-genre").textContent = projectConfig.genre || "";
  document.getElementById("nav-search").style.display = "block";

  // Update dashboard header
  document.getElementById("dash-title").textContent = projectConfig.title || slug;
  document.getElementById("dash-genre").textContent = projectConfig.genre || "";
  document.getElementById("dash-type").textContent = projectConfig.type || "";

  const totalEntities = Object.values(data.stats).reduce((a, b) => a + b, 0);
  document.getElementById("dash-entity-count").textContent = `${totalEntities} entities`;

  // Build entity nav
  buildEntityNav(data.stats);

  // Load all entities
  await loadAllEntities();

  showPage("dashboard");
  setEntityType("all");
}

function buildEntityNav(stats) {
  const nav = document.getElementById("entity-nav");
  const total = Object.values(stats).reduce((a, b) => a + b, 0);

  let html = `<button class="entity-nav-btn active" onclick="setEntityType('all')">
    All <span class="count">${total}</span></button>`;

  for (const [type, count] of Object.entries(stats)) {
    const icon = ENTITY_ICONS[type] || "📦";
    html += `<button class="entity-nav-btn" data-type="${type}" onclick="setEntityType('${type}')">
      ${icon} ${type} <span class="count">${count}</span></button>`;
  }
  nav.innerHTML = html;
}

async function loadAllEntities() {
  allEntities = {};
  currentEntities = [];

  for (const etype of Object.keys(projectStats)) {
    const res = await fetch(`/api/project/${currentProject}/entities/${etype}`);
    const ents = await res.json();
    allEntities[etype] = ents;
    currentEntities.push(...ents);
  }
}

function setEntityType(type) {
  currentEntityType = type;

  // Update nav buttons
  document.querySelectorAll(".entity-nav-btn").forEach(btn => {
    btn.classList.toggle("active", (btn.dataset.type || "all") === type ||
      (!btn.dataset.type && type === "all"));
  });

  // Filter entities
  let ents;
  if (type === "all") {
    ents = currentEntities;
  } else {
    ents = allEntities[type] || [];
  }

  renderEntityGrid(ents);
}

// ─── Entity Grid ──────────────────────────────────────────────────────────
function renderEntityGrid(entities) {
  const grid = document.getElementById("entity-grid");
  const filter = document.getElementById("entity-filter").value.toLowerCase();

  let filtered = entities;
  if (filter) {
    filtered = entities.filter(e =>
      e.name.toLowerCase().includes(filter) ||
      e.slug.toLowerCase().includes(filter) ||
      (e.type || "").toLowerCase().includes(filter)
    );
  }

  // Sort
  const sortBy = document.getElementById("entity-sort").value;
  filtered.sort((a, b) => {
    if (sortBy === "type") return (a.type || "").localeCompare(b.type || "");
    if (sortBy === "status") return (a.meta?.status || "").localeCompare(b.meta?.status || "");
    return (a.name || "").localeCompare(b.name || "");
  });

  if (filtered.length === 0) {
    grid.innerHTML = `<div style="grid-column:1/-1; text-align:center; padding:40px; color:var(--text-2)">
      No entities found</div>`;
    return;
  }

  grid.innerHTML = filtered.map(e => {
    const icon = ENTITY_ICONS[e.type] || "📦";
    const status = e.meta?.status || "";
    const statusBadge = status ? `<span class="badge ${status === 'dead' ? 'badge-red' : status === 'alive' ? 'badge-green' : 'badge-muted'}">${status}</span>` : "";
    const species = e.meta?.species ? `<span>${e.meta.species}</span>` : "";
    const metaLine = [species, e.meta?.role, e.meta?.type].filter(Boolean).join(" · ");

    const cardImage = e.image_url
      ? `<div class="entity-card-image" style="background-image:url('${e.image_url}');background-size:cover;background-position:center"></div>`
      : `<div class="entity-card-image">${icon}</div>`;

    return `<div class="entity-card" onclick="openEntity('${e.type}', '${e.slug}')">
      ${cardImage}
      <div class="entity-card-info">
        <h3>${e.name}</h3>
        <div class="entity-card-meta">
          <span class="badge badge-muted">${e.type}</span>
          ${statusBadge}
        </div>
        ${metaLine ? `<div class="entity-card-meta" style="margin-top:4px">${metaLine}</div>` : ""}
      </div>
    </div>`;
  }).join("");
}

function filterEntities() { setEntityType(currentEntityType); }
function sortEntities() { setEntityType(currentEntityType); }

// ─── Entity Detail Panel ──────────────────────────────────────────────────
async function openEntity(type, slug) {
  const res = await fetch(`/api/project/${currentProject}/entity/${type}/${slug}`);
  const data = await res.json();

  document.getElementById("panel-name").textContent = data.name;
  document.getElementById("panel-type").textContent = type;
  document.getElementById("panel-type").className = `badge`;

  // Build content
  const content = document.getElementById("panel-content");
  const meta = data.meta || {};
  let html = "";

  // ── Image generation section (top of panel) ──
  html += buildImageSection(type, slug, meta);

  // ── Voice player section (characters only, below image) ──
  html += buildVoiceSection(type, slug);

  // Key fields
  const skipFields = ["name", "descriptions", "family_links", "relationships", "routes", "heraldry"];
  const fields = Object.entries(meta).filter(([k]) => !skipFields.includes(k));

  if (fields.length) {
    html += `<div class="panel-section"><h4>Properties</h4>`;
    for (const [key, val] of fields) {
      if (val === null || val === undefined || val === "") continue;
      let display = val;
      if (typeof val === "object") {
        if (val.display) display = val.display;
        else if (Array.isArray(val)) display = val.join(", ");
        else display = JSON.stringify(val, null, 1);
      }
      html += `<div class="field"><span class="field-label">${key}</span><span class="field-value">${display}</span></div>`;
    }
    html += `</div>`;
  }

  // Descriptions (triple)
  const descs = meta.descriptions || {};
  if (descs.human) {
    html += `<div class="panel-section"><h4>Description</h4>
      <div class="panel-body">${renderMarkdown(descs.human)}</div></div>`;
  }
  if (descs.machine) {
    html += `<div class="panel-section"><h4>Machine Description</h4>`;
    for (const [k, v] of Object.entries(descs.machine)) {
      if (v) html += `<div class="field"><span class="field-label">${k}</span><span class="field-value">${v}</span></div>`;
    }
    html += `</div>`;
  }

  // Heraldry
  const heraldry = meta.heraldry || {};
  if (heraldry.sigil || heraldry.motto) {
    html += `<div class="panel-section"><h4>Heraldry</h4>`;
    if (heraldry.sigil?.description) html += `<div class="field"><span class="field-label">Sigil</span><span class="field-value">${heraldry.sigil.description}</span></div>`;
    if (heraldry.sigil?.blazon) html += `<div class="field"><span class="field-label">Blazon</span><span class="field-value">${heraldry.sigil.blazon}</span></div>`;
    if (heraldry.motto) html += `<div class="field"><span class="field-label">Motto</span><span class="field-value">"${heraldry.motto}"</span></div>`;
    if (heraldry.image_prompt) {
      html += `<div class="field"><span class="field-label">Heraldry Prompt</span><span class="field-value" style="font-family:var(--font-mono);font-size:12px">${heraldry.image_prompt}</span></div>`;
    }
    html += `</div>`;
  }

  // Relationships
  const rels = meta.relationships || [];
  if (rels.length) {
    html += `<div class="panel-section"><h4>Relationships</h4>`;
    for (const r of rels) {
      const target = r.entity || r.character || r.name || "?";
      html += `<div class="field">
        <span class="field-label">${r.type || "related"}</span>
        <span class="field-value"><span class="panel-link" onclick="navigateToEntity('${target}')">${target}</span> ${r.description || ""}</span>
      </div>`;
    }
    html += `</div>`;
  }

  // Family links
  const family = meta.family_links || {};
  if (Object.keys(family).length) {
    html += `<div class="panel-section"><h4>Family</h4>`;
    for (const [rel, val] of Object.entries(family)) {
      const people = Array.isArray(val) ? val : [val];
      for (const p of people.filter(Boolean)) {
        html += `<div class="field">
          <span class="field-label">${rel}</span>
          <span class="field-value"><span class="panel-link" onclick="navigateToEntity('${p}')">${p}</span></span>
        </div>`;
      }
    }
    html += `</div>`;
  }

  // Body / prose
  if (data.body) {
    html += `<div class="panel-section"><h4>Notes</h4>
      <div class="panel-body">${renderMarkdown(data.body)}</div></div>`;
  }

  content.innerHTML = html;

  // Check for cached image and load it
  checkEntityImage(type, slug);

  // Check for voice data (characters only)
  checkEntityVoice(type, slug);

  // Cross-reference links at bottom
  const links = document.getElementById("panel-links");
  const refs = findCrossRefs(meta);
  links.innerHTML = refs.map(r =>
    `<span class="panel-link" onclick="navigateToEntity('${r}')">${r}</span>`
  ).join("");

  // Open panel
  document.getElementById("entity-panel").classList.add("open");
}

function closePanel() {
  document.getElementById("entity-panel").classList.remove("open");
}

function navigateToEntity(nameOrSlug) {
  const slug = nameOrSlug.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  // Find the entity across all types
  for (const [type, ents] of Object.entries(allEntities)) {
    const found = ents.find(e => e.slug === slug || e.name.toLowerCase() === nameOrSlug.toLowerCase());
    if (found) {
      openEntity(type, found.slug);
      return;
    }
  }
  // Try search
  console.log("Entity not found:", nameOrSlug);
}

function findCrossRefs(meta) {
  const refs = new Set();
  const walk = (obj) => {
    if (typeof obj === "string" && /^[a-z0-9-]+$/.test(obj) && obj.includes("-")) {
      // Looks like a slug reference
      for (const ents of Object.values(allEntities)) {
        if (ents.some(e => e.slug === obj)) { refs.add(obj); break; }
      }
    } else if (Array.isArray(obj)) {
      obj.forEach(walk);
    } else if (obj && typeof obj === "object") {
      Object.values(obj).forEach(walk);
    }
  };
  walk(meta);
  return [...refs];
}

// ─── View Switching ───────────────────────────────────────────────────────
function setView(view) {
  document.querySelectorAll(".view-tab").forEach(t =>
    t.classList.toggle("active", t.dataset.view === view));
  document.querySelectorAll(".view-content").forEach(v =>
    v.classList.toggle("active", v.id === `view-${view}`));

  if (view === "timeline") loadTimeline();
  else if (view === "map") loadGeography();
  else if (view === "relationships") loadRelationships();
  else if (view === "families") loadFamilies();
  else if (view === "languages") loadLanguages();
}

// ─── Timeline Visualization ───────────────────────────────────────────────
async function loadTimeline() {
  const res = await fetch(`/api/project/${currentProject}/timeline`);
  const events = await res.json();
  if (!events.length) return;

  const svg = d3.select("#timeline-svg");
  svg.selectAll("*").remove();

  const container = svg.node().parentElement;
  const width = container.clientWidth;
  const height = Math.max(500, events.length * 60 + 80);
  svg.attr("width", width).attr("height", height);

  const margin = { top: 40, right: 40, bottom: 40, left: 200 };
  const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);

  // Y scale — one row per event
  const y = d3.scaleBand()
    .domain(events.map(e => e.slug))
    .range([0, height - margin.top - margin.bottom])
    .padding(0.3);

  // Event type colors
  const typeColors = {
    war: "#f85149", battle: "#f85149", death: "#8b949e",
    birth: "#3fb950", founding: "#58a6ff", discovery: "#bc8cff",
    coronation: "#e3b341", rebellion: "#d29922", plague: "#da3633",
    cataclysm: "#da3633", treaty: "#56d4dd", marriage: "#f778ba",
    default: "#484f58",
  };

  // Draw events
  const barWidth = width - margin.left - margin.right - 120;

  events.forEach(evt => {
    const row = g.append("g")
      .attr("class", "timeline-event")
      .attr("transform", `translate(0, ${y(evt.slug)})`)
      .on("click", () => openEntity("event", evt.slug));

    const color = typeColors[evt.type] || typeColors.default;
    const sigWidth = { "world-changing": barWidth, major: barWidth * 0.75,
      moderate: barWidth * 0.5, minor: barWidth * 0.3, trivial: barWidth * 0.15 }[evt.significance] || barWidth * 0.3;

    row.append("rect")
      .attr("x", 0).attr("y", 0)
      .attr("width", sigWidth).attr("height", y.bandwidth())
      .attr("fill", color).attr("opacity", 0.6)
      .attr("rx", 4);

    row.append("text")
      .attr("x", 8).attr("y", y.bandwidth() / 2)
      .attr("dy", "0.35em")
      .text(`${evt.date} — ${evt.name}`)
      .attr("fill", "#e6edf3").attr("font-size", "13px");

    // Significance badge
    row.append("text")
      .attr("x", sigWidth + 8).attr("y", y.bandwidth() / 2)
      .attr("dy", "0.35em")
      .text(evt.significance)
      .attr("fill", "#8b949e").attr("font-size", "11px");
  });

  // Causality arrows
  const eventMap = {};
  events.forEach((e, i) => eventMap[e.slug] = i);

  events.forEach(evt => {
    (evt.leads_to || []).forEach(target => {
      if (eventMap[target] !== undefined) {
        const y1 = y(evt.slug) + y.bandwidth();
        const y2 = y(target);
        g.append("line")
          .attr("x1", 20).attr("y1", y1)
          .attr("x2", 20).attr("y2", y2)
          .attr("stroke", "#58a6ff").attr("stroke-width", 1.5)
          .attr("stroke-dasharray", "4,4")
          .attr("opacity", 0.5);
        g.append("polygon")
          .attr("points", `15,${y2} 25,${y2} 20,${y2 + 6}`)
          .attr("fill", "#58a6ff").attr("opacity", 0.5);
      }
    });
  });
}

// ─── Geography Visualization ──────────────────────────────────────────────
async function loadGeography() {
  const res = await fetch(`/api/project/${currentProject}/geography`);
  const data = await res.json();
  if (!data.nodes.length) return;

  const svg = d3.select("#geography-svg");
  svg.selectAll("*").remove();

  const container = svg.node().parentElement;
  const width = container.clientWidth;
  const height = 600;
  svg.attr("width", width).attr("height", height);

  // Force simulation
  const nodeMap = {};
  data.nodes.forEach(n => nodeMap[n.slug] = n);

  const links = data.links
    .filter(l => nodeMap[l.source] && nodeMap[l.target])
    .map(l => ({ ...l, source: l.source, target: l.target }));

  const typeRadius = {
    city: 20, capital: 24, town: 16, village: 12, continent: 30,
    region: 25, building: 10, dungeon: 14, default: 16,
  };
  const typeColors = {
    city: "#58a6ff", capital: "#e3b341", town: "#56d4dd", village: "#3fb950",
    continent: "#bc8cff", region: "#8b949e", building: "#d29922",
    dungeon: "#f85149", default: "#484f58",
  };

  const simulation = d3.forceSimulation(data.nodes)
    .force("link", d3.forceLink(links).id(d => d.slug).distance(120))
    .force("charge", d3.forceManyBody().strength(-300))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("collision", d3.forceCollide().radius(d => (typeRadius[d.type] || typeRadius.default) + 10));

  const g = svg.append("g");

  // Zoom
  svg.call(d3.zoom().scaleExtent([0.3, 3]).on("zoom", (event) => {
    g.attr("transform", event.transform);
  }));

  // Draw links
  const link = g.selectAll(".link")
    .data(links).enter().append("g");

  link.append("line")
    .attr("class", "link")
    .attr("stroke-width", d => d.route_type === "major" ? 3 : 1.5);

  link.append("text")
    .attr("class", "link-label")
    .text(d => d.modes ? d.modes.join(", ") : "");

  // Draw nodes
  const node = g.selectAll(".node")
    .data(data.nodes).enter().append("g")
    .attr("class", "node")
    .call(d3.drag()
      .on("start", (event, d) => { if (!event.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
      .on("drag", (event, d) => { d.fx = event.x; d.fy = event.y; })
      .on("end", (event, d) => { if (!event.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; })
    )
    .on("click", (event, d) => openEntity("location", d.slug));

  node.append("circle")
    .attr("r", d => typeRadius[d.type] || typeRadius.default)
    .attr("fill", d => typeColors[d.type] || typeColors.default)
    .attr("stroke", "#30363d").attr("stroke-width", 2);

  node.append("text")
    .attr("dy", d => (typeRadius[d.type] || typeRadius.default) + 14)
    .attr("text-anchor", "middle")
    .text(d => d.name);

  // Image placeholder icon on nodes
  node.append("text")
    .attr("text-anchor", "middle").attr("dy", "0.35em")
    .attr("font-size", d => (typeRadius[d.type] || typeRadius.default) * 0.8)
    .text(d => d.type === "dungeon" ? "🏛️" : d.type === "city" || d.type === "capital" ? "🏰" : d.type === "village" ? "🏘️" : "📍")
    .attr("pointer-events", "none");

  simulation.on("tick", () => {
    link.select("line")
      .attr("x1", d => d.source.x).attr("y1", d => d.source.y)
      .attr("x2", d => d.target.x).attr("y2", d => d.target.y);
    link.select("text")
      .attr("x", d => (d.source.x + d.target.x) / 2)
      .attr("y", d => (d.source.y + d.target.y) / 2);
    node.attr("transform", d => `translate(${d.x},${d.y})`);
  });
}

// ─── Relationship Graph ───────────────────────────────────────────────────
async function loadRelationships() {
  const res = await fetch(`/api/project/${currentProject}/relationships`);
  const data = await res.json();
  if (!data.nodes.length) return;

  const svg = d3.select("#relationships-svg");
  svg.selectAll("*").remove();

  const container = svg.node().parentElement;
  const width = container.clientWidth;
  const height = 600;
  svg.attr("width", width).attr("height", height);

  const nodeMap = {};
  data.nodes.forEach(n => nodeMap[n.slug] = n);

  const validLinks = data.links.filter(l => nodeMap[l.source] && nodeMap[l.target]);

  const relColors = {
    mentor: "#58a6ff", student: "#58a6ff", ally: "#3fb950",
    enemy: "#f85149", rival: "#d29922", lover: "#f778ba",
    parent: "#bc8cff", child: "#bc8cff", spouse: "#f778ba",
    friend: "#3fb950", default: "#8b949e",
  };

  const simulation = d3.forceSimulation(data.nodes)
    .force("link", d3.forceLink(validLinks).id(d => d.slug).distance(100))
    .force("charge", d3.forceManyBody().strength(-250))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("collision", d3.forceCollide().radius(30));

  const g = svg.append("g");
  svg.call(d3.zoom().scaleExtent([0.3, 3]).on("zoom", (event) => {
    g.attr("transform", event.transform);
  }));

  // Links
  const link = g.selectAll(".link")
    .data(validLinks).enter().append("g");

  link.append("line")
    .attr("class", "link")
    .attr("stroke", d => relColors[d.type] || relColors.default)
    .attr("stroke-width", 1.5);

  link.append("text")
    .attr("class", "link-label")
    .text(d => d.type)
    .attr("fill", d => relColors[d.type] || relColors.default);

  // Nodes
  const node = g.selectAll(".node")
    .data(data.nodes).enter().append("g")
    .attr("class", "node")
    .call(d3.drag()
      .on("start", (event, d) => { if (!event.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
      .on("drag", (event, d) => { d.fx = event.x; d.fy = event.y; })
      .on("end", (event, d) => { if (!event.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; })
    )
    .on("click", (event, d) => openEntity("character", d.slug));

  node.append("circle")
    .attr("r", 20)
    .attr("fill", d => d.status === "dead" ? "#484f58" : "#58a6ff")
    .attr("stroke", d => d.status === "dead" ? "#8b949e" : "#79c0ff")
    .attr("stroke-width", 2)
    .attr("stroke-dasharray", d => d.status === "dead" ? "4,4" : "none");

  node.append("text")
    .attr("dy", 34).attr("text-anchor", "middle")
    .text(d => d.name).attr("font-size", "12px");

  node.append("text")
    .attr("text-anchor", "middle").attr("dy", "0.35em")
    .text("👤").attr("font-size", "16px")
    .attr("pointer-events", "none");

  simulation.on("tick", () => {
    link.select("line")
      .attr("x1", d => d.source.x).attr("y1", d => d.source.y)
      .attr("x2", d => d.target.x).attr("y2", d => d.target.y);
    link.select("text")
      .attr("x", d => (d.source.x + d.target.x) / 2)
      .attr("y", d => (d.source.y + d.target.y) / 2);
    node.attr("transform", d => `translate(${d.x},${d.y})`);
  });
}

// ─── Families View ────────────────────────────────────────────────────────
async function loadFamilies() {
  const res = await fetch(`/api/project/${currentProject}/families`);
  const families = await res.json();
  const container = document.getElementById("families-container");

  if (!families.length) {
    container.innerHTML = `<div style="text-align:center;padding:40px;color:var(--text-2)">No lineages defined</div>`;
    return;
  }

  container.innerHTML = families.map(fam => {
    const heraldry = fam.heraldry || {};
    const heraldryLine = heraldry.motto ? `"${heraldry.motto}"` :
      (heraldry.sigil?.description || "");

    const membersHtml = fam.members.map(m => {
      const isDead = m.status === "dead";
      const icon = isDead ? "✝" : "●";
      return `<span class="family-member ${isDead ? 'dead' : ''}" onclick="openEntity('character','${m.slug}')">
        ${icon} ${m.name} <span style="font-size:11px;color:var(--text-2)">${m.role || ""}</span>
      </span>`;
    }).join("");

    return `<div class="family-tree-card">
      <h3>👑 ${fam.lineage_name}</h3>
      ${heraldryLine ? `<div class="family-heraldry">${heraldryLine}</div>` : ""}
      <div style="margin-bottom:8px">
        <button class="btn btn-ghost btn-sm" onclick="event.stopPropagation(); openEntity('lineage','${fam.lineage_slug}')">🖼️ View & Generate Image</button>
      </div>
      <div>${membersHtml || '<span style="color:var(--text-2)">No members linked</span>'}</div>
    </div>`;
  }).join("");
}

// ─── Languages View ───────────────────────────────────────────────────────
async function loadLanguages() {
  const res = await fetch(`/api/project/${currentProject}/languages`);
  const langs = await res.json();
  const container = document.getElementById("languages-container");

  if (!langs.length) {
    container.innerHTML = `<div style="text-align:center;padding:40px;color:var(--text-2)">No languages defined</div>`;
    return;
  }

  // Group by family
  const families = {};
  langs.forEach(l => {
    const fam = l.family_name || "Unknown";
    if (!families[fam]) families[fam] = [];
    families[fam].push(l);
  });

  container.innerHTML = Object.entries(families).map(([fam, members]) => {
    const membersHtml = members.map(l => {
      const statusClass = l.status || "living";
      const statusIcon = { living: "●", endangered: "⚠", dead: "✝", extinct: "✝", proto: "◯" }[l.status] || "●";

      // Intelligibility bars
      const intellHtml = (l.intelligibility || []).map(i => {
        const score = i.score || 0;
        const pct = Math.round(score * 100);
        return `<div style="display:flex;align-items:center;gap:6px;font-size:12px;margin-top:4px">
          <span style="color:var(--text-2);min-width:80px">${i.language}</span>
          <div class="intelligibility-bar"><div class="intelligibility-fill" style="width:${pct}%"></div></div>
          <span style="color:var(--text-2)">${pct}%</span>
        </div>`;
      }).join("");

      return `<div class="lang-node" onclick="openEntity('language','${l.slug}')" style="display:block;margin:8px 0">
        <div style="display:flex;align-items:center;gap:6px">
          <span class="lang-status ${statusClass}">${statusIcon}</span>
          <strong>${l.name}</strong>
          ${l.special?.lingua_franca ? '<span class="badge badge-muted" style="font-size:10px">lingua franca</span>' : ''}
          ${l.special?.magical_properties ? '<span class="badge badge-purple" style="font-size:10px">magical</span>' : ''}
        </div>
        ${intellHtml}
      </div>`;
    }).join("");

    return `<div class="lang-family">
      <h3>🗣️ ${fam}</h3>
      ${membersHtml}
    </div>`;
  }).join("");
}

// ─── Search ───────────────────────────────────────────────────────────────
function setupSearch() {
  const input = document.getElementById("global-search");
  const dropdown = document.getElementById("search-results");
  let debounce;

  input.addEventListener("input", () => {
    clearTimeout(debounce);
    debounce = setTimeout(async () => {
      const q = input.value.trim();
      if (q.length < 2 || !currentProject) {
        dropdown.classList.remove("active");
        return;
      }
      const res = await fetch(`/api/project/${currentProject}/search?q=${encodeURIComponent(q)}`);
      const results = await res.json();
      if (results.length === 0) {
        dropdown.innerHTML = `<div class="search-item" style="color:var(--text-2)">No results</div>`;
      } else {
        dropdown.innerHTML = results.slice(0, 10).map(r => `
          <div class="search-item" onclick="openEntity('${r.type}','${r.slug}'); document.getElementById('search-results').classList.remove('active')">
            <span>${ENTITY_ICONS[r.type] || '📦'} ${r.name}</span>
            <span class="badge badge-muted">${r.type}</span>
          </div>
        `).join("");
      }
      dropdown.classList.add("active");
    }, 300);
  });

  input.addEventListener("blur", () => {
    setTimeout(() => dropdown.classList.remove("active"), 200);
  });
}

// ─── Size Picker ──────────────────────────────────────────────────────────
function setupSizePicker() {
  document.querySelectorAll(".size-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      btn.parentElement.querySelectorAll(".size-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
    });
  });
}

// ─── Wizard ───────────────────────────────────────────────────────────────
const wizardSteps = [
  {
    title: "Project Basics",
    fields: [
      { id: "wiz-title", label: "World / Project Name", type: "text", placeholder: "The Shattered Crown", required: true },
      { id: "wiz-genre", label: "Genre", type: "choice", options: ["fantasy", "scifi", "modern", "horror", "post-apocalyptic", "steampunk"] },
      { id: "wiz-type", label: "Project Type", type: "choice", options: ["novel", "series", "campaign", "game", "worldbook"] },
      { id: "wiz-size", label: "World Complexity", type: "choice", options: ["S — Small", "M — Medium", "L — Large", "XL — Epic"] },
      { id: "wiz-tone", label: "Tone", type: "choice", options: ["literary", "pulp", "young-adult", "dark", "gritty", "epic", "litrpg", "cozy"] },
    ]
  },
  {
    title: "Cosmology & Physics",
    fields: [
      { id: "wiz-creation", label: "Creation Myth (brief)", type: "text", placeholder: "The world was forged from the dreams of sleeping gods..." },
      { id: "wiz-magic", label: "Does Magic Exist?", type: "choice", options: ["yes", "no", "ambiguous"] },
      { id: "wiz-calendar", label: "Calendar Name", type: "text", placeholder: "Common Reckoning" },
    ]
  },
  {
    title: "Geography & Climate",
    fields: [
      { id: "wiz-world", label: "World / Planet Name", type: "text", placeholder: "Aerthys", required: true },
      { id: "wiz-regions", label: "Key Regions (comma-separated)", type: "text", placeholder: "The Northern Wastes, Sunlit Kingdoms, The Deep Marches" },
      { id: "wiz-climate", label: "Climate Range", type: "choice", options: ["uniform", "moderate-variety", "extreme-variety"] },
    ]
  },
  {
    title: "Species & Peoples",
    fields: [
      { id: "wiz-species", label: "Species Approach", type: "choice", options: ["humans-only", "few-species", "many-species", "cosmic-zoo"] },
      { id: "wiz-species-list", label: "Specific Species", type: "text", placeholder: "Humans, Elves, Dwarves..." },
      { id: "wiz-interbreed", label: "Cross-Species Breeding?", type: "choice", options: ["yes", "no", "rare-exceptions"] },
    ]
  },
  {
    title: "Power & Factions",
    fields: [
      { id: "wiz-politics", label: "Political Structure", type: "choice", options: ["monarchy", "republic", "tribal", "theocracy", "empire", "fragmented", "corporate", "mixed"] },
      { id: "wiz-conflict", label: "Geopolitical Tension", type: "choice", options: ["peaceful", "simmering", "active-conflict", "total-war", "post-war"] },
      { id: "wiz-factions", label: "Key Factions", type: "text", placeholder: "The Silver Order, The Black Market Guild..." },
    ]
  },
  {
    title: "History & Timeline",
    fields: [
      { id: "wiz-history", label: "History Depth", type: "choice", options: ["shallow (decades)", "moderate (centuries)", "deep (millennia)", "ancient (ages)"] },
      { id: "wiz-events", label: "Pivotal Events", type: "text", placeholder: "The Sundering, The War of Broken Crowns..." },
    ]
  },
  {
    title: "Central Characters",
    fields: [
      { id: "wiz-protag", label: "Protagonist Name", type: "text", placeholder: "Leave blank to generate" },
      { id: "wiz-archetype", label: "Protagonist Archetype", type: "choice", options: ["reluctant-hero", "chosen-one", "anti-hero", "everyman", "scholar", "outcast", "soldier", "trickster", "generate"] },
      { id: "wiz-antag", label: "Antagonist Type", type: "choice", options: ["dark-lord", "political-rival", "nature", "cosmic-force", "self", "organization", "mystery", "generate"] },
    ]
  },
];

let wizardStep = 0;
const wizardData = {};

function showWizard() {
  wizardStep = 0;
  showPage("wizard");
  renderWizardStep();
}

function renderWizardStep() {
  const step = wizardSteps[wizardStep];
  const fill = ((wizardStep + 1) / wizardSteps.length * 100).toFixed(0);
  document.getElementById("wizard-progress-fill").style.width = fill + "%";
  document.getElementById("wizard-step-label").textContent = `Step ${wizardStep + 1} of ${wizardSteps.length} — ${step.title}`;

  let html = `<h2>${step.title}</h2>`;
  step.fields.forEach(f => {
    const val = wizardData[f.id] || "";
    if (f.type === "text") {
      html += `<div class="form-group">
        <label>${f.label}${f.required ? ' *' : ''}</label>
        <input type="text" id="${f.id}" value="${val}" placeholder="${f.placeholder || ''}">
      </div>`;
    } else if (f.type === "choice") {
      html += `<div class="form-group">
        <label>${f.label}</label>
        <div class="wizard-choice-grid">
          ${f.options.map(o => `<div class="wizard-choice ${val === o ? 'selected' : ''}"
            onclick="selectWizardChoice('${f.id}', '${o}', this)">${o}</div>`).join("")}
        </div>
      </div>`;
    }
  });

  document.getElementById("wizard-content").innerHTML = html;
  document.getElementById("wizard-back").style.visibility = wizardStep > 0 ? "visible" : "hidden";
  document.getElementById("wizard-next").textContent = wizardStep === wizardSteps.length - 1 ? "Generate World 🚀" : "Next →";
}

function selectWizardChoice(fieldId, value, el) {
  wizardData[fieldId] = value;
  el.parentElement.querySelectorAll(".wizard-choice").forEach(c => c.classList.remove("selected"));
  el.classList.add("selected");
}

function wizardNext() {
  // Save text fields
  const step = wizardSteps[wizardStep];
  step.fields.forEach(f => {
    if (f.type === "text") {
      const el = document.getElementById(f.id);
      if (el) wizardData[f.id] = el.value;
    }
  });

  if (wizardStep < wizardSteps.length - 1) {
    wizardStep++;
    renderWizardStep();
  } else {
    finishWizard();
  }
}

function wizardBack() {
  if (wizardStep > 0) {
    wizardStep--;
    renderWizardStep();
  }
}

function finishWizard() {
  // Show a summary modal / generate prompt
  const summary = Object.entries(wizardData)
    .filter(([k, v]) => v)
    .map(([k, v]) => `${k.replace("wiz-", "")}: ${v}`)
    .join("\n");

  alert(`Wizard complete! Your world configuration:\n\n${summary}\n\nRun the CLI wizard with these settings to generate entity files.`);
  showWelcome();
}

// ─── YOLO Mode ────────────────────────────────────────────────────────────
function launchYolo() {
  const genre = document.getElementById("yolo-genre").value;
  const sizeBtn = document.querySelector("#yolo-size-picker .size-btn.active");
  const size = sizeBtn ? sizeBtn.dataset.size : "M";
  const seed = document.getElementById("yolo-seed").value;

  const cmd = `python scripts/worldbuilder.py wizard yolo --size ${size} --genre ${genre}${seed ? ` --seed "${seed}"` : ""} --tone epic`;

  alert(`YOLO mode ready!\n\nRun this command:\n${cmd}\n\nThen feed the output prompt to Claude to generate your world.`);
}

// ─── Image Generation ────────────────────────────────────────────────────

async function checkImagegenStatus() {
  try {
    const res = await fetch("/api/imagegen/status");
    const status = await res.json();
    imagegenAvailable = status.mlx_available;
    console.log("[imagegen]", status.backend, status.model_loaded ? "(loaded)" : "(not loaded yet)");
  } catch {
    imagegenAvailable = false;
  }
}

function buildImageSection(entityType, entitySlug, meta) {
  // Check if entity has an image_prompt
  const descs = meta.descriptions || {};
  const imagePrompt = descs.image_prompt || (meta.heraldry || {}).image_prompt;

  let html = `<div class="panel-section" id="panel-image-section">`;
  html += `<h4>Visualization</h4>`;

  // Image display area
  html += `<div id="entity-image-container" class="entity-image-container">
    <div id="entity-image-placeholder" class="entity-image-placeholder">
      <span style="font-size:48px; opacity:0.3">${ENTITY_ICONS[entityType] || '📦'}</span>
    </div>
    <img id="entity-image" class="entity-image" style="display:none" />
  </div>`;

  if (!imagePrompt) {
    html += `<div class="image-status image-status-warn">
      No visualization available — add an <code>image_prompt</code> to this entity's descriptions in the YAML frontmatter.
    </div>`;
  } else {
    // Show the prompt
    html += `<div class="image-prompt-preview">
      <span class="field-label">Prompt</span>
      <span class="field-value" style="font-family:var(--font-mono); font-size:11px">${imagePrompt}</span>
    </div>`;

    // Generate button
    if (imagegenAvailable === false) {
      html += `<div class="image-actions">
        <button class="btn btn-primary btn-sm" disabled title="Backend not available">
          🖼️ Generate Image (unavailable)
        </button>
        <span class="image-status image-status-info">
          Backend not configured — check IMAGEGEN_BACKEND setting
        </span>
      </div>`;
    } else {
      // Style selector for entity images
      html += `<div class="entity-style-selector">
        <select id="entity-image-style" class="pg-input-sm" title="Image style">
          <option value="photorealistic">📷 Photorealistic</option>
          <option value="anime">🎌 Anime</option>
          <option value="cartoon">🖍️ Cartoon</option>
          <option value="default">⚙️ Default</option>
        </select>
      </div>`;
      html += `<div class="image-actions">
        <button class="btn btn-primary btn-sm" id="btn-generate-image"
          onclick="generateEntityImage('${entityType}', '${entitySlug}')">
          🖼️ Generate Image
        </button>
        <button class="btn btn-ghost btn-sm" id="btn-regenerate-image" style="display:none"
          onclick="generateEntityImage('${entityType}', '${entitySlug}', true)">
          🔄 Regenerate
        </button>
        <span id="image-gen-status" class="image-status"></span>
      </div>`;
    }
  }

  html += `</div>`;
  return html;
}

// ─── Voice Player ─────────────────────────────────────────────────────────

function buildVoiceSection(entityType, entitySlug) {
  if (entityType !== "character") return "";
  // Return a placeholder container; populated async after panel renders
  return `<div id="voice-player-section" data-entity-type="${entityType}" data-entity-slug="${entitySlug}"></div>`;
}

async function checkEntityVoice(entityType, entitySlug) {
  if (entityType !== "character" || !currentProject) return;
  const container = document.getElementById("voice-player-section");
  if (!container) return;

  try {
    const res = await fetch(`/api/project/${currentProject}/entity/character/${entitySlug}/voice/check`);
    const data = await res.json();
    if (!data.has_voice) {
      container.innerHTML = "";
      return;
    }
    renderVoicePlayer(container, entitySlug, data);
  } catch {
    // Silent fail — no voice section
  }
}

function renderVoicePlayer(container, entitySlug, voiceData) {
  const sampleText = voiceData.sample_text || "";
  const cached = voiceData.cached || false;
  const audioUrl = voiceData.url || "";

  let html = `<div class="panel-section"><h4>Voice</h4><div class="voice-player">`;

  // Editable text area — users can type custom lines or use the default
  html += `<textarea class="voice-text-input" id="voice-text-input" rows="3" placeholder="Enter a line of dialogue...">${sampleText}</textarea>`;
  html += `<div class="voice-actions">`;

  if (cached && audioUrl) {
    html += `<button class="voice-play-btn" id="voice-play-btn" onclick="playVoice('${entitySlug}', '${audioUrl}')">&#9654; Play Voice</button>`;
  } else {
    html += `<button class="voice-play-btn" id="voice-play-btn" onclick="generateAndPlayVoice('${entitySlug}')">&#9654; Play Voice</button>`;
  }

  html += `<span id="voice-status" class="voice-status"></span>`;
  html += `</div>`;
  html += `<audio id="voice-audio" style="display:none"></audio>`;
  html += `</div></div>`;

  container.innerHTML = html;

  // When user edits text, switch button to generate mode (new text = uncached)
  const textarea = document.getElementById("voice-text-input");
  if (textarea) {
    textarea.addEventListener("input", () => {
      const btn = document.getElementById("voice-play-btn");
      if (btn) {
        btn.setAttribute("onclick", `generateAndPlayVoice('${entitySlug}')`);
        btn.innerHTML = "&#9654; Generate & Play";
      }
    });
  }
}

let currentVoiceAudio = null;

function playVoice(entitySlug, url) {
  const btn = document.getElementById("voice-play-btn");
  const audio = document.getElementById("voice-audio");
  if (!audio || !btn) return;

  // If already playing, pause
  if (currentVoiceAudio && !currentVoiceAudio.paused) {
    currentVoiceAudio.pause();
    btn.innerHTML = "&#9654; Play Voice";
    currentVoiceAudio = null;
    return;
  }

  audio.src = url;
  audio.play().then(() => {
    btn.innerHTML = "&#10074;&#10074; Pause";
    currentVoiceAudio = audio;
  }).catch(e => {
    const status = document.getElementById("voice-status");
    if (status) status.textContent = "Playback failed: " + e.message;
  });

  audio.onended = () => {
    btn.innerHTML = "&#9654; Play Voice";
    currentVoiceAudio = null;
  };
}

async function generateAndPlayVoice(entitySlug) {
  const btn = document.getElementById("voice-play-btn");
  const statusEl = document.getElementById("voice-status");
  const textarea = document.getElementById("voice-text-input");
  if (!btn) return;

  // Get text from the editable textarea
  const customText = textarea ? textarea.value.trim() : "";

  btn.disabled = true;
  btn.innerHTML = "&#9654; Play Voice";
  if (statusEl) {
    statusEl.innerHTML = "";
    statusEl.className = "voice-loading";
    statusEl.textContent = "Generating voice...";
  }

  try {
    const body = {};
    if (customText) body.text = customText;

    const res = await fetch(
      `/api/project/${currentProject}/entity/character/${entitySlug}/voice`,
      { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }
    );
    const data = await res.json();

    if (data.error) {
      if (statusEl) { statusEl.className = "voice-status"; statusEl.textContent = data.error; }
      btn.disabled = false;
      return;
    }

    // If immediately complete (cached hit)
    if (data.status === "completed" && data.url) {
      if (statusEl) { statusEl.className = "voice-status"; statusEl.textContent = ""; }
      btn.disabled = false;
      btn.setAttribute("onclick", `playVoice('${entitySlug}', '${data.url}')`);
      playVoice(entitySlug, data.url);
      return;
    }

    // Poll for completion
    const jobId = data.job_id;
    if (!jobId) {
      if (statusEl) { statusEl.className = "voice-status"; statusEl.textContent = "Failed to submit voice job"; }
      btn.disabled = false;
      return;
    }

    pollVoiceJob(jobId, entitySlug);

  } catch (e) {
    if (statusEl) { statusEl.className = "voice-status"; statusEl.textContent = "Error: " + e.message; }
    btn.disabled = false;
  }
}

function pollVoiceJob(jobId, entitySlug) {
  const interval = setInterval(async () => {
    const btn = document.getElementById("voice-play-btn");
    const statusEl = document.getElementById("voice-status");
    try {
      const res = await fetch(`/api/voicegen/job/${jobId}`);
      const data = await res.json();

      if (data.status === "completed" && data.filename) {
        clearInterval(interval);
        const url = `/api/project/${currentProject}/voices/${data.filename}`;
        if (statusEl) { statusEl.className = "voice-status"; statusEl.textContent = ""; }
        if (btn) {
          btn.disabled = false;
          btn.setAttribute("onclick", `playVoice('${entitySlug}', '${url}')`);
        }
        playVoice(entitySlug, url);
      } else if (data.status === "failed") {
        clearInterval(interval);
        if (statusEl) { statusEl.className = "voice-status"; statusEl.textContent = data.error || "Generation failed"; }
        if (btn) btn.disabled = false;
      }
      // Otherwise keep polling
    } catch {
      clearInterval(interval);
      if (statusEl) { statusEl.className = "voice-status"; statusEl.textContent = "Polling failed"; }
      if (btn) btn.disabled = false;
    }
  }, 2000);
}

async function checkEntityImage(entityType, entitySlug) {
  if (!currentProject) return;
  try {
    const res = await fetch(`/api/project/${currentProject}/entity/${entityType}/${entitySlug}/image/check`);
    const data = await res.json();
    if (data.cached && data.url) {
      showEntityImage(data.url);
    }
  } catch {
    // Silent fail — just don't show an image
  }
}

function showEntityImage(url) {
  const img = document.getElementById("entity-image");
  const placeholder = document.getElementById("entity-image-placeholder");
  const regenBtn = document.getElementById("btn-regenerate-image");
  const genBtn = document.getElementById("btn-generate-image");

  if (img && placeholder) {
    img.src = url;
    img.style.display = "block";
    placeholder.style.display = "none";
    img.onerror = () => {
      img.style.display = "none";
      placeholder.style.display = "flex";
    };
  }
  if (regenBtn) regenBtn.style.display = "inline-block";
  if (genBtn) genBtn.textContent = "🖼️ Generate Image";
}

async function generateEntityImage(entityType, entitySlug, force = false) {
  const btn = document.getElementById("btn-generate-image");
  const status = document.getElementById("image-gen-status");

  if (btn) {
    btn.disabled = true;
    btn.textContent = "⏳ Submitting...";
  }
  if (status) {
    status.textContent = "Submitting generation job...";
    status.className = "image-status image-status-info";
  }

  try {
    const res = await fetch(
      `/api/project/${currentProject}/entity/${entityType}/${entitySlug}/image`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ force, style: (document.getElementById("entity-image-style") || {}).value || "photorealistic" }),
      }
    );
    const data = await res.json();

    if (data.error) {
      if (status) {
        status.textContent = data.error;
        status.className = "image-status image-status-warn";
      }
      if (btn) { btn.disabled = false; btn.textContent = "🖼️ Generate Image"; }
      return;
    }

    // If already complete (cached hit), show immediately
    if (data.status === "complete" && data.url) {
      showEntityImage(data.url);
      if (status) {
        status.textContent = data.cached ? "Loaded from cache" : "Image generated";
        status.className = "image-status image-status-ok";
      }
      if (btn) { btn.disabled = false; btn.textContent = "🖼️ Generate Image"; }
      return;
    }

    // Job is queued/running — track it and start polling
    const jobId = data.job_id;
    if (!jobId) {
      if (status) { status.textContent = "Failed to submit job"; status.className = "image-status image-status-warn"; }
      if (btn) { btn.disabled = false; btn.textContent = "🖼️ Generate Image"; }
      return;
    }

    activeJobs[jobId] = {
      entityType, entitySlug,
      entityName: data.entity_name || entitySlug,
    };
    ensureCompletionPolling();

    if (status) {
      status.textContent = `Queued (job ${jobId}) — you can navigate away; you'll be notified when done.`;
      status.className = "image-status image-status-info";
    }
    if (btn) {
      btn.disabled = true;
      btn.textContent = "⏳ Generating...";
    }

    // Also poll this specific job for the currently-open panel
    pollJobForPanel(jobId, entityType, entitySlug);

  } catch (e) {
    if (status) {
      status.textContent = `Error: ${e.message}`;
      status.className = "image-status image-status-warn";
    }
    if (btn) { btn.disabled = false; btn.textContent = "🖼️ Generate Image"; }
  }
}

async function pollJobForPanel(jobId, entityType, entitySlug) {
  // Poll the specific job while user is still on this entity's panel
  const interval = setInterval(async () => {
    try {
      const res = await fetch(`/api/imagegen/job/${jobId}`);
      if (res.status === 404) {
        clearInterval(interval);
        delete activeJobs[jobId];
        const btn = document.getElementById("btn-generate-image");
        const status = document.getElementById("image-gen-status");
        if (btn) { btn.disabled = false; btn.textContent = "🖼️ Generate Image"; }
        if (status) { status.textContent = "Job lost (server restarted) — try again"; status.className = "image-status image-status-warn"; }
        return;
      }
      const job = await res.json();

      if (job.status === "complete") {
        clearInterval(interval);
        delete activeJobs[jobId];

        // If user is still viewing this entity, update the panel
        const btn = document.getElementById("btn-generate-image");
        const status = document.getElementById("image-gen-status");
        if (btn && status && job.url) {
          const img = document.getElementById("entity-image");
          if (img) img.style.opacity = "1";
          showEntityImage(job.url);
          status.textContent = "Image generated successfully";
          status.className = "image-status image-status-ok";
          btn.disabled = false;
          btn.textContent = "🖼️ Generate Image";
        }
      } else if (job.status === "failed") {
        clearInterval(interval);
        delete activeJobs[jobId];

        const btn = document.getElementById("btn-generate-image");
        const status = document.getElementById("image-gen-status");
        if (btn && status) {
          status.textContent = job.error || "Generation failed";
          status.className = "image-status image-status-warn";
          btn.disabled = false;
          btn.textContent = "🖼️ Generate Image";
        }
      } else {
        // Still running — update status with step progress + live preview
        const status = document.getElementById("image-gen-status");
        if (status) {
          const current = job.current_step || 0;
          const total = job.total_steps || 0;
          const stepInfo = total > 0 ? ` — step ${current}/${total}` : "";
          const pct = total > 0 ? Math.round((current / total) * 100) : 0;
          status.innerHTML = `${job.status === "running" ? "Generating" : "Queued"}${stepInfo}`
            + (total > 0 ? `<div class="pg-progress-bar" style="margin:6px 0 0"><div class="pg-progress-fill" style="width:${pct}%"></div></div>` : "");
          status.className = "image-status image-status-info";
        }
        // Show live step preview in the entity image area
        if (job.preview_url && job.current_step > 0) {
          const img = document.getElementById("entity-image");
          const placeholder = document.getElementById("entity-image-placeholder");
          if (img && placeholder) {
            img.src = job.preview_url + "?t=" + Date.now();
            img.style.display = "block";
            img.style.opacity = "0.7";
            placeholder.style.display = "none";
          }
        }
      }
    } catch { /* silent */ }
  }, 2000);
}

// ─── Toast Notification System ────────────────────────────────────────────

function ensureToastContainer() {
  if (!document.getElementById("toast-container")) {
    const container = document.createElement("div");
    container.id = "toast-container";
    document.body.appendChild(container);
  }
}

function showToast(message, type = "info", duration = 6000) {
  ensureToastContainer();
  const container = document.getElementById("toast-container");
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.innerHTML = message;
  container.appendChild(toast);
  // Trigger reflow for animation
  requestAnimationFrame(() => toast.classList.add("show"));
  setTimeout(() => {
    toast.classList.remove("show");
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

function showImageToast(job) {
  const name = job.entity_name || job.entity_slug;
  const icon = ENTITY_ICONS[job.entity_type] || "📦";
  if (job.status === "complete") {
    const thumb = job.url ? `<img src="${job.url}" class="toast-thumb" />` : "";
    showToast(
      `<div class="toast-img-row">${thumb}<div>${icon} <strong>${name}</strong><br><span class="toast-sub">Image ready — click to view</span></div></div>`,
      "success", 8000
    );
  } else if (job.status === "failed") {
    showToast(
      `${icon} <strong>${name}</strong> — image generation failed: ${job.error || "unknown error"}`,
      "error", 8000
    );
  }
}

// ─── Background Completion Polling ────────────────────────────────────────

function ensureCompletionPolling() {
  if (completionPollInterval) return;
  completionPollInterval = setInterval(pollCompletions, 3000);
}

async function pollCompletions() {
  // If no active jobs and no recent submissions, stop polling
  if (Object.keys(activeJobs).length === 0) {
    clearInterval(completionPollInterval);
    completionPollInterval = null;
    return;
  }

  try {
    const res = await fetch(`/api/imagegen/completions?since=${lastCompletionCheck}`);
    const completed = await res.json();
    lastCompletionCheck = Date.now() / 1000;

    for (const job of completed) {
      if (activeJobs[job.job_id]) {
        showImageToast(job);
        delete activeJobs[job.job_id];
      }
    }
  } catch { /* silent */ }
}


// ─── Image Playground ─────────────────────────────────────────────────────

let pgHistory = [];
let pgCurrentJob = null;
let pgSelectedStyle = "photorealistic";

function pgSelectStyle(btn) {
  document.querySelectorAll(".pg-style-card").forEach(c => c.classList.remove("active"));
  btn.classList.add("active");
  pgSelectedStyle = btn.dataset.style;
}

function showPlayground() {
  showPage("playground");
  closePanel();
  // Update status indicator
  pgUpdateStatus();
}

async function pgUpdateStatus() {
  const el = document.getElementById("playground-status");
  try {
    const res = await fetch("/api/imagegen/status");
    const s = await res.json();
    const backendType = s.backend_type || s.backend || "unknown";
    const model = s.model || "unknown";
    if (s.model_loaded || s.comfyui_available) {
      el.innerHTML = `<span class="badge badge-success">✓ ${backendType} — ${model}</span>`;
    } else if (s.mlx_available || s.diffusers_available) {
      el.innerHTML = `<span class="badge badge-warning">Model loading…</span>`;
    } else {
      el.innerHTML = `<span class="badge badge-error">Unavailable: ${s.error || "Backend not configured"}</span>`;
    }
  } catch {
    el.innerHTML = `<span class="badge badge-error">Backend offline</span>`;
  }
}

async function pgGenerate() {
  const prompt = document.getElementById("pg-prompt").value.trim();
  if (!prompt) return;

  const steps = parseInt(document.getElementById("pg-steps").value) || 9;
  const width = parseInt(document.getElementById("pg-width").value) || 1024;
  const height = parseInt(document.getElementById("pg-height").value) || 1024;
  const seedVal = document.getElementById("pg-seed").value.trim();
  const seed = seedVal ? parseInt(seedVal) : null;

  const btn = document.getElementById("pg-generate-btn");
  btn.disabled = true;
  btn.textContent = "Generating…";

  const area = document.getElementById("pg-image-area");
  area.innerHTML = `<div class="pg-placeholder"><span class="placeholder-icon">⏳</span><p>Generating image…</p></div>`;

  try {
    const res = await fetch("/api/imagegen/playground", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt, steps, width, height, seed, force: false, style: pgSelectedStyle }),
    });
    const job = await res.json();

    if (job.error) {
      area.innerHTML = `<div class="pg-placeholder"><span class="placeholder-icon">❌</span><p>${job.error}</p></div>`;
      btn.disabled = false;
      btn.textContent = "Generate";
      return;
    }

    // If cached, show immediately
    if (job.status === "complete" && job.url) {
      pgShowResult(job);
      btn.disabled = false;
      btn.textContent = "Generate";
      return;
    }

    // Poll for completion
    pgCurrentJob = job.job_id;
    pgPollJob(job.job_id, btn);

  } catch (e) {
    area.innerHTML = `<div class="pg-placeholder"><span class="placeholder-icon">❌</span><p>Request failed: ${e.message}</p></div>`;
    btn.disabled = false;
    btn.textContent = "Generate";
  }
}

function pgPollJob(jobId, btn) {
  const interval = setInterval(async () => {
    try {
      const res = await fetch(`/api/imagegen/job/${jobId}`);
      if (res.status === 404) {
        clearInterval(interval);
        const area = document.getElementById("pg-image-area");
        area.innerHTML = `<div class="pg-placeholder"><span class="placeholder-icon">⚠️</span><p>Job lost (server restarted) — try again</p></div>`;
        btn.disabled = false;
        btn.textContent = "Generate";
        return;
      }
      const job = await res.json();

      if (job.status === "complete") {
        clearInterval(interval);
        pgShowResult(job);
        btn.disabled = false;
        btn.textContent = "Generate";
      } else if (job.status === "failed") {
        clearInterval(interval);
        const area = document.getElementById("pg-image-area");
        area.innerHTML = `<div class="pg-placeholder"><span class="placeholder-icon">❌</span><p>${job.error || "Generation failed"}</p></div>`;
        btn.disabled = false;
        btn.textContent = "Generate";
      } else {
        // Update progress bar
        pgUpdateProgress(job);
      }
    } catch {
      clearInterval(interval);
      btn.disabled = false;
      btn.textContent = "Generate";
    }
  }, 2000);
}

function pgUpdateProgress(job) {
  const area = document.getElementById("pg-image-area");
  const current = job.current_step || 0;
  const total = job.total_steps || 0;
  const pct = total > 0 ? Math.round((current / total) * 100) : 0;
  const label = total > 0 ? `Step ${current} / ${total}` : "Starting…";
  const previewImg = job.preview_url && current > 0
    ? `<img src="${job.preview_url}?t=${Date.now()}" class="pg-result-img" style="opacity:0.7" />`
    : `<span class="placeholder-icon">⏳</span>`;
  area.innerHTML = `
    <div class="pg-placeholder" style="position:relative">
      ${previewImg}
      <div style="position:absolute;bottom:8px;left:8px;right:8px;background:rgba(0,0,0,0.6);padding:6px 10px;border-radius:6px">
        <p style="margin:0;color:#fff;font-size:13px">${label}</p>
        <div class="pg-progress-bar" style="margin:4px 0 0">
          <div class="pg-progress-fill" style="width:${pct}%"></div>
        </div>
      </div>
    </div>`;
}

function pgShowResult(job) {
  const area = document.getElementById("pg-image-area");
  // The playground images use _playground project slug, so URL is /api/project/_playground/images/...
  const url = job.url;
  area.innerHTML = `<img src="${url}" class="pg-result-img" onclick="window.open('${url}', '_blank')" title="Click to open full size" />`;

  const info = document.getElementById("pg-image-info");
  info.style.display = "block";
  info.innerHTML = `<span class="hint">Seed: ${job.seed || "?"} · ${job.cached ? "Cached" : "Generated"}</span>`;

  // Add to history
  pgHistory.unshift({ url, prompt: job.prompt, seed: job.seed, style: job.style || pgSelectedStyle });
  pgRenderHistory();
}

function pgRenderHistory() {
  const container = document.getElementById("pg-history");
  if (pgHistory.length === 0) {
    container.style.display = "none";
    return;
  }
  container.style.display = "block";
  const grid = document.getElementById("pg-history-grid");
  const styleIcons = { photorealistic: "📷", anime: "🎌", cartoon: "🖍️", default: "⚙️" };
  grid.innerHTML = pgHistory.map(h => {
    const icon = styleIcons[h.style] || "⚙️";
    return `
    <div class="pg-history-item" onclick="window.open('${h.url}', '_blank')" title="${(h.prompt || '').substring(0, 80)}">
      <img src="${h.url}" />
      <span class="pg-history-badge">${icon}</span>
    </div>`;
  }).join("");
}

function pgClearHistory() {
  pgHistory = [];
  pgRenderHistory();
}
