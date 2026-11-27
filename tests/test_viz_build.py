"""Tests for assembling the single-file world viewer (assets/viewer + build_viewer.py)."""

from __future__ import annotations

import importlib.util
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parent.parent
SKILL = PLUGIN / "skills" / "world-visualiser"
VIEWER = SKILL / "assets" / "viewer"
EXAMPLE = PLUGIN / "skills" / "worldbuilding" / "assets" / "example-the-lattice"
INTEGRITY = "sha384-5UGTcMIxVUKFeJH0zOS3lqMAZNBG+fCXJbi3UglUq6ABO4MQJu6rxNa+MPP+qtwq"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


bv = _load("build_viewer_for_viz_build", SKILL / "scripts" / "build_viewer.py")
fixtures = _load("test_viz_data_fixtures", PLUGIN / "tests" / "test_viz_data.py")


def _build(project, tmp_path):
    out = tmp_path / "out" / "viewer.html"
    assert bv.main([str(project), "--out", str(out)]) == 0
    return out.read_text(encoding="utf-8")


def _scripts(html):
    """Inline script bodies (the three.js tag has a src and no body)."""
    return [m.group(1) for m in re.finditer(r"<script>\n(.*?)\n</script>", html, re.S)]


def _build_copy(tmp_path):
    """Build the example-free synthetic world with a scratch copy of the viewer sources; returns (rc, out)."""
    out = tmp_path / "o.html"
    tpl = tmp_path / "viewer" / "index.html"
    return bv.main([str(tmp_path / "w"), "--out", str(out), "--template", str(tpl)]), out


def _check_single_file(html):
    assert html.count(bv.MARKER) == 0
    assert html.count("const DATA = ") == 1
    assert "<!--__CSS__-->" not in html and "<!--__JS__-->" not in html
    assert f'integrity="{INTEGRITY}"' in html
    assert html.count("<style>") == 1
    assert len(_scripts(html)) == 1
    # No other network resources: the only external URL is the three.js CDN script.
    srcs = re.findall(r'(?:src|href)="(https?://[^"]+)"', html)
    assert srcs == ["https://cdn.jsdelivr.net/npm/three@0.158.0/build/three.min.js"]


def test_example_builds_to_one_self_contained_page(tmp_path):
    html = _build(EXAMPLE, tmp_path)
    _check_single_file(html)
    assert "The Lattice" in html
    assert (
        "WB.registerView" in html
        and "'graph'" in html
        and "'timeline'" in html
        and "'gallery'" in html
        and "'content'" in html
    )


def test_content_tab_discovers_stories_and_campaigns_and_escapes_html(tmp_path):
    fixtures.write_world(tmp_path)
    stories_dir = tmp_path / "stories"
    stories_dir.mkdir(parents=True)
    (stories_dir / "harbour-tale.md").write_text(
        "---\ntitle: The Harbour Tale\ndate: 10 AE\n---\n# The Harbour Tale\n\n"
        "A tale set in `harbour` with <script>alert(1)</script> safely escaped.\n\n"
        "> Read-aloud box\n\n| Col A | Col B |\n| --- | --- |\n| 1 | 2 |\n",
        encoding="utf-8",
    )
    camp_dir = tmp_path / "output" / "campaigns"
    camp_dir.mkdir(parents=True)
    (camp_dir / "era-campaign.md").write_text(
        "---\ntitle: Era 5e Campaign\nsystem: D&D 5e\nlevel: 1-4\n---\n# Era 5e Campaign\n\n"
        "Starts at `harbour`.\n",
        encoding="utf-8",
    )
    data = bv.viz_data.build_viz_data(tmp_path)
    assert data["counts"]["content"] == 2
    by_kind = {item["kind"]: item for item in data["content"]}
    assert "story" in by_kind and "campaign" in by_kind
    story_html = by_kind["story"]["html"]
    assert "<script>" not in story_html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in story_html
    assert 'data-entity="harbour"' in story_html
    assert "<blockquote>" in story_html
    assert "<table>" in story_html
    html = _build(tmp_path, tmp_path)
    _check_single_file(html)
    assert "The Harbour Tale" in html and "Era 5e Campaign" in html


def test_map_backdrop_discovery_and_embed_images(tmp_path):
    import base64

    fixtures.write_world(tmp_path)
    png_bytes = b"\x89PNG\r\n\x1a\nworldmap"
    img_dir = tmp_path / "output" / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    (img_dir / "world-map.png").write_bytes(png_bytes)

    data_rel = bv.viz_data.build_viz_data(tmp_path, embed_images=False)
    assert data_rel["map"]["backdrop"] == "images/world-map.png"

    data_emb = bv.viz_data.build_viz_data(tmp_path, embed_images=True)
    expected = "data:image/png;base64," + base64.b64encode(png_bytes).decode("ascii")
    assert data_emb["map"]["backdrop"] == expected

    html = _build(tmp_path, tmp_path)
    _check_single_file(html)
    assert "buildProceduralTerrain" in html and "Painted Map" in html


def test_embed_images_flag_produces_portable_single_file(tmp_path):
    import base64

    fixtures.write_world(tmp_path)
    png_bytes = b"\x89PNG\r\n\x1a\nportable"
    img_dir = tmp_path / "output" / "images" / "locations"
    img_dir.mkdir(parents=True)
    (img_dir / "harbour.png").write_bytes(png_bytes)
    out = tmp_path / "out" / "portable.html"
    assert bv.main([str(tmp_path), "--embed-images", "--out", str(out)]) == 0
    html = out.read_text(encoding="utf-8")
    _check_single_file(html)
    expected = "data:image/png;base64," + base64.b64encode(png_bytes).decode("ascii")
    assert expected in html


def test_synthetic_project_and_script_end_in_name(tmp_path):
    fixtures.write_world(tmp_path)
    evil = "Evil </script><script>alert(1)</script> Realm"
    (tmp_path / "world" / "locations" / "realm.md").write_text(fixtures.md({"name": evil, "type": "kingdom"}))
    html = _build(tmp_path, tmp_path)
    _check_single_file(html)
    assert evil not in html
    assert "\\u003c/script\\u003e" in html
    assert html.count("</script>") == 2  # the CDN tag and the one inline script


def test_missing_view_files_do_not_break_the_build(tmp_path):
    shutil.copytree(VIEWER, tmp_path / "viewer")
    for f in (tmp_path / "viewer" / "js" / "views").glob("*.js"):
        f.unlink()
    fixtures.write_world(tmp_path / "w")
    rc, out = _build_copy(tmp_path)
    assert rc == 0
    html = out.read_text(encoding="utf-8")
    assert "<!--__JS__-->" not in html and "const DATA = " in html


def test_views_are_inlined_in_sorted_order_between_core_and_main(tmp_path):
    shutil.copytree(VIEWER, tmp_path / "viewer")
    views = tmp_path / "viewer" / "js" / "views"
    for f in views.glob("*.js"):
        f.unlink()
    (views / "b.js").write_text("/*VIEW_B*/\n")
    (views / "a.js").write_text("/*VIEW_A*/\n")
    fixtures.write_world(tmp_path / "w")
    rc, out = _build_copy(tmp_path)
    assert rc == 0
    html = out.read_text(encoding="utf-8")
    order = [html.index(x) for x in ("const DATA = ", "/*VIEW_A*/", "/*VIEW_B*/", "// main.js")]
    assert order == sorted(order)


def test_script_end_in_a_source_file_is_rejected(tmp_path, capsys):
    shutil.copytree(VIEWER, tmp_path / "viewer")
    (tmp_path / "viewer" / "js" / "views" / "bad.js").write_text("const s = '</script>';\n")
    fixtures.write_world(tmp_path / "w")
    rc, _ = _build_copy(tmp_path)
    assert rc == 1
    assert "</script" in capsys.readouterr().err


def test_data_marker_lives_once_in_core():
    sources = [p for p in VIEWER.rglob("*") if p.is_file() and p.suffix in {".js", ".html", ".css"}]
    holders = [p.name for p in sources if bv.MARKER in p.read_text(encoding="utf-8")]
    assert holders == ["core.js"]


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_assembled_script_parses(tmp_path):
    html = _build(EXAMPLE, tmp_path)
    script = tmp_path / "viewer.js"
    script.write_text(_scripts(html)[0], encoding="utf-8")
    result = subprocess.run(["node", "--check", str(script)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_tectonic_cartography_rivers_and_ornaments_in_single_file(tmp_path):
    fixtures.write_world(tmp_path)
    html = _build(tmp_path, tmp_path)
    _check_single_file(html)
    for token in (
        "ridgedFbm",
        "computeTerrainField",
        "terrainFieldCache",
        "drawRivers",
        "flows_to",
        "drawOrnaments",
        "wbm-orn-mountain",
        "wbm-orn-forest",
        "wbm-scale-bar",
        "wbm-region-title",
        "wbm-river",
        "wbm-sea-lane",
    ):
        assert token in html, f"expected {token!r} in assembled viewer"


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_map_view_renders_tectonic_terrain_rivers_and_ornaments(tmp_path):
    """Execute map.js in a minimal Node DOM/canvas mock for Topographic and Parchment modes."""
    fixtures.write_world(tmp_path)
    html = _build(tmp_path, tmp_path)
    _check_single_file(html)

    map_js = (VIEWER / "js" / "views" / "map.js").read_text(encoding="utf-8")
    harness = tmp_path / "run_map.js"
    harness.write_text(
        """
const fs = require('fs');
let canvasBuilds = 0;

function mkEl(tag, ns) {
  const el = {
    tagName: tag,
    ns: ns || null,
    attrs: {},
    children: [],
    listeners: {},
    style: { setProperty: function () {} },
    classList: {
      _set: new Set(),
      add: function () { for (const c of arguments) this._set.add(c); },
      remove: function () { for (const c of arguments) this._set.delete(c); },
      toggle: function (c, on) { if (on) this._set.add(c); else this._set.delete(c); },
    },
    setAttribute: function (k, v) { this.attrs[k] = String(v); },
    getAttribute: function (k) { return this.attrs[k]; },
    appendChild: function (c) { this.children.push(c); return c; },
    removeChild: function (c) {
      const i = this.children.indexOf(c);
      if (i >= 0) this.children.splice(i, 1);
      return c;
    },
    addEventListener: function (ev, fn) {
      (this.listeners[ev] = this.listeners[ev] || []).push(fn);
    },
    getBoundingClientRect: function () { return { width: 800, height: 800, left: 0, top: 0 }; },
    focus: function () {},
    get firstChild() { return this.children[0] || null; },
  };
  if (tag === 'canvas') {
    el.getContext = function () {
      canvasBuilds += 1;
      return {
        createImageData: function (w, h) {
          return { width: w, height: h, data: new Uint8ClampedArray(w * h * 4) };
        },
        putImageData: function () {},
      };
    };
    el.toDataURL = function () { return 'data:image/png;base64,MOCK_' + canvasBuilds; };
  }
  return el;
}

function collectByClass(node, cls, out) {
  out = out || [];
  if (!node || typeof node !== 'object') return out;
  const c = (node.attrs && node.attrs.class) || '';
  if (c.split(/\\s+/).indexOf(cls) >= 0) out.push(node);
  (node.children || []).forEach(function (ch) { collectByClass(ch, cls, out); });
  return out;
}

function findById(node, id) {
  if (!node || typeof node !== 'object') return null;
  if (node.attrs && node.attrs.id === id) return node;
  for (const ch of (node.children || [])) {
    const hit = findById(ch, id);
    if (hit) return hit;
  }
  return null;
}

global.window = { matchMedia: function () { return { matches: false }; } };
global.document = {
  head: mkEl('head'),
  body: mkEl('body'),
  getElementById: function () { return null; },
  createElement: function (t) { return mkEl(t); },
  createElementNS: function (ns, t) { return mkEl(t, ns); },
  createTextNode: function (s) { return { text: String(s) }; },
};

let view = null;
global.WB = {
  data: {
    project: { name: 'Tectonic Test World' },
    nodes: [],
    map: {
      locations: [
        {
          id: 'north-realm', name: 'North Realm', type: 'region', depth: 0,
          children: ['high-peak', 'green-vale'], x: 320, y: 320, elevation_m: 350,
          area_km2: 85000, climate: { zone: 'temperate', precipitation_mm: 980 },
        },
        {
          id: 'high-peak', name: 'Ironspine Peak', type: 'landmark', parent: 'north-realm',
          depth: 1, children: [], x: 260, y: 280, elevation_m: 3400,
          terrain: 'alpine mountain ridge', climate: { zone: 'alpine', precipitation_mm: 1200 },
          hydrology: { flows_to: 'green-vale' },
        },
        {
          id: 'green-vale', name: 'Green Vale', type: 'settlement', parent: 'north-realm',
          depth: 1, children: [], x: 460, y: 420, elevation_m: 180,
          terrain: 'forested lowland', population: 42000,
          climate: { zone: 'temperate', precipitation_mm: 1050 },
          hydrology: { flows_to: 'harbour' },
        },
        {
          id: 'dry-basin', name: 'Leeward Wastes', type: 'region', depth: 0, children: [],
          x: 640, y: 360, elevation_m: 420, terrain: 'arid steppe',
          climate: { zone: 'arid', precipitation_mm: 140 },
        },
        {
          id: 'harbour', name: 'Shoal Harbour', type: 'city', depth: 0, children: [],
          x: 780, y: 740, elevation_m: -15, terrain: 'coastal sea harbour',
          population: 90000, climate: { zone: 'mediterranean' },
        },
      ],
      routes: [
        {
          id: 'green-vale--harbour', from: 'green-vale', to: 'harbour',
          modes: [{ mode: 'sea', time: '2 days' }], goods: ['grain'], reciprocal: true,
        },
      ],
    },
    climate: { zones: [], legend: {} },
    economy: { resources: [] },
  },
  state: { filters: {}, selected: null },
  colors: { type: {}, zone: function () { return '#5ec962'; } },
  bus: { on: function () {}, emit: function () {} },
  select: function () {},
  registerView: function (v) { view = v; },
};

eval(fs.readFileSync(process.argv[2], 'utf8'));
if (!view) throw new Error('map view did not register');

const container = mkEl('div');
view.create(container, global.WB);

// Topographic mode renders rivers, sea-lanes, scale bar, region titles, and caches terrain
if (canvasBuilds !== 1) throw new Error('expected 1 initial topographic canvas build, got ' + canvasBuilds);
const topoRivers = collectByClass(container, 'wbm-river');
if (topoRivers.length < 2) throw new Error('expected >=2 river paths, got ' + topoRivers.length);
const seaLanes = collectByClass(container, 'wbm-sea-lane');
if (seaLanes.length < 1) throw new Error('expected sea-lane class on sea route');
const scaleBars = collectByClass(container, 'wbm-scale-bar');
if (scaleBars.length !== 1) throw new Error('expected 1 scale bar, got ' + scaleBars.length);
const regionTitles = collectByClass(container, 'wbm-region-title');
if (regionTitles.length < 1) throw new Error('expected top-level region titles, got ' + regionTitles.length);

// Re-render same style must hit cache (no extra canvas build)
view.onFilter();
if (canvasBuilds !== 1) throw new Error('expected terrain cache hit on re-render, got ' + canvasBuilds);

// Switch to Parchment style: builds parchment canvas once and renders chevrons + woodland clusters
const styleSel = findById(container, 'wbg-map-style');
if (!styleSel) throw new Error('missing style select');
(styleSel.listeners.change || []).forEach(function (fn) { fn({ target: { value: 'parchment' } }); });
if (canvasBuilds !== 2) throw new Error('expected 2nd canvas build for parchment, got ' + canvasBuilds);
const chevrons = collectByClass(container, 'wbm-orn-mountain');
if (chevrons.length < 1) throw new Error('expected mountain chevrons in parchment mode, got ' + chevrons.length);
const forests = collectByClass(container, 'wbm-orn-forest');
if (forests.length < 1) throw new Error('expected woodland clusters in parchment mode, got ' + forests.length);

// Switch back to topographic: must hit cache
(styleSel.listeners.change || []).forEach(function (fn) { fn({ target: { value: 'topographic' } }); });
if (canvasBuilds !== 2) throw new Error('expected cache hit returning to topographic, got ' + canvasBuilds);

// Single-world project must hide the World / Realm switcher
if (findById(container, 'wbg-map-scope')) throw new Error('single-world project should not render wbg-map-scope');
""",
        encoding="utf-8",
    )
    map_src_path = tmp_path / "map_copy.js"
    map_src_path.write_text(map_js, encoding="utf-8")
    result = subprocess.run(["node", str(harness), str(map_src_path)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr + result.stdout


def _write_multi_realm_world(root: Path) -> Path:
    """Create a synthetic multi-realm fantasy world with cross-world portals and one per-scope backdrop."""
    fixtures.write_world(root)
    locs = root / "world" / "locations"
    # Remove default single-world locations so only our two realms exist cleanly
    for existing in locs.glob("*.md"):
        existing.unlink()

    (locs / "aetheria.md").write_text(
        fixtures.md({
            "name": "Aetheria",
            "type": "realm",
            "terrain": "sunlit highlands",
            "climate_profile": {"zone": "temperate", "precipitation_mm": 900},
        }),
        encoding="utf-8",
    )
    (locs / "sunspire.md").write_text(
        fixtures.md({
            "name": "Sunspire",
            "type": "city",
            "parent": "aetheria",
            "population": 120000,
            "elevation_m": 850,
            "routes": [
                {"to": "dawnport", "methods": [{"mode": "road", "travel_time": "2 days"}]},
                {"to": "gloomgate", "methods": [{"mode": "portal", "travel_time": "instant"}]},
            ],
        }),
        encoding="utf-8",
    )
    (locs / "dawnport.md").write_text(
        fixtures.md({
            "name": "Dawnport",
            "type": "city",
            "parent": "aetheria",
            "population": 65000,
            "routes": [
                {"to": "sunspire", "methods": [{"mode": "road", "travel_time": "2 days"}]},
            ],
        }),
        encoding="utf-8",
    )
    (locs / "shadowfen.md").write_text(
        fixtures.md({
            "name": "Shadowfen",
            "type": "realm",
            "terrain": "misty marshlands",
            "climate_profile": {"zone": "subarctic", "precipitation_mm": 1300},
        }),
        encoding="utf-8",
    )
    (locs / "gloomgate.md").write_text(
        fixtures.md({
            "name": "Gloomgate",
            "type": "settlement",
            "parent": "shadowfen",
            "population": 18000,
            "routes": [
                {"to": "sunspire", "methods": [{"mode": "portal", "travel_time": "instant"}]},
                {"to": "mirewatch", "methods": [{"mode": "boat", "travel_time": "1 day"}]},
            ],
        }),
        encoding="utf-8",
    )
    (locs / "mirewatch.md").write_text(
        fixtures.md({
            "name": "Mirewatch",
            "type": "landmark",
            "parent": "shadowfen",
            "elevation_m": 20,
            "routes": [
                {"to": "gloomgate", "methods": [{"mode": "boat", "travel_time": "1 day"}]},
            ],
        }),
        encoding="utf-8",
    )
    # Give Aetheria a per-scope painted backdrop; Shadowfen has none
    maps_dir = root / "output" / "images" / "maps"
    maps_dir.mkdir(parents=True, exist_ok=True)
    (maps_dir / "aetheria.png").write_bytes(b"\x89PNG\r\n\x1a\naetheria-map")
    return root


def test_multi_world_viewer_builds_for_example_and_fantasy_realms(tmp_path):
    # 1. example-the-lattice has multiple planet scopes
    ex_data = bv.viz_data.build_viz_data(EXAMPLE)
    assert len(ex_data["map"]["scopes"]) >= 2
    ex_html = _build(EXAMPLE, tmp_path / "ex")
    _check_single_file(ex_html)
    for token in (
        "wbg-map-scope",
        "Overview (All Worlds)",
        "View Surface Map",
        "wbm-world-node",
        "wbm-cross-route",
        "cross_world_routes",
    ):
        assert token in ex_html, f"expected {token!r} in example-the-lattice viewer"

    # 2. Synthetic multi-realm fantasy world with cross-world portal + per-scope backdrop
    proj = _write_multi_realm_world(tmp_path / "fantasy")
    data = bv.viz_data.build_viz_data(proj)
    scopes = {s["id"]: s for s in data["map"]["scopes"]}
    assert set(scopes) == {"aetheria", "shadowfen"}
    assert scopes["aetheria"]["backdrop"] == "images/maps/aetheria.png"
    assert scopes["shadowfen"]["backdrop"] is None
    assert len(data["map"]["cross_world_routes"]) == 1
    assert data["map"]["cross_world_routes"][0]["cross_world"] is True

    html = _build(proj, tmp_path / "fantasy_out")
    _check_single_file(html)
    assert "Aetheria" in html and "Shadowfen" in html
    assert "images/maps/aetheria.png" in html


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_multi_world_map_switcher_overview_and_per_scope_backdrop(tmp_path):
    """Execute map.js in Node with a multi-realm world to verify switcher, overview, drill-down and backdrops."""
    import json

    proj = _write_multi_realm_world(tmp_path / "fantasy")
    data = bv.viz_data.build_viz_data(proj)
    data_path = tmp_path / "viz.json"
    data_path.write_text(json.dumps(data), encoding="utf-8")

    map_js = (VIEWER / "js" / "views" / "map.js").read_text(encoding="utf-8")
    map_src_path = tmp_path / "map_copy.js"
    map_src_path.write_text(map_js, encoding="utf-8")

    harness = tmp_path / "run_multi_map.js"
    harness.write_text(
        """
const fs = require('fs');
const vizData = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
let canvasBuilds = 0;

function mkEl(tag, ns) {
  const el = {
    tagName: tag,
    ns: ns || null,
    attrs: {},
    children: [],
    listeners: {},
    style: { setProperty: function () {} },
    classList: {
      _set: new Set(),
      add: function () { for (const c of arguments) this._set.add(c); },
      remove: function () { for (const c of arguments) this._set.delete(c); },
      toggle: function (c, on) { if (on) this._set.add(c); else this._set.delete(c); },
    },
    setAttribute: function (k, v) { this.attrs[k] = String(v); },
    getAttribute: function (k) { return this.attrs[k]; },
    appendChild: function (c) { this.children.push(c); return c; },
    removeChild: function (c) {
      const i = this.children.indexOf(c);
      if (i >= 0) this.children.splice(i, 1);
      return c;
    },
    addEventListener: function (ev, fn) {
      (this.listeners[ev] = this.listeners[ev] || []).push(fn);
    },
    getBoundingClientRect: function () { return { width: 800, height: 800, left: 0, top: 0 }; },
    focus: function () {},
    get firstChild() { return this.children[0] || null; },
  };
  if (tag === 'canvas') {
    el.getContext = function () {
      canvasBuilds += 1;
      return {
        createImageData: function (w, h) {
          return { width: w, height: h, data: new Uint8ClampedArray(w * h * 4) };
        },
        putImageData: function () {},
      };
    };
    el.toDataURL = function () { return 'data:image/png;base64,MOCK_' + canvasBuilds; };
  }
  return el;
}

function collectByClass(node, cls, out) {
  out = out || [];
  if (!node || typeof node !== 'object') return out;
  const c = (node.attrs && node.attrs.class) || '';
  if (c.split(/\\s+/).indexOf(cls) >= 0) out.push(node);
  (node.children || []).forEach(function (ch) { collectByClass(ch, cls, out); });
  return out;
}

function collectByTag(node, tag, out) {
  out = out || [];
  if (!node || typeof node !== 'object') return out;
  if (node.tagName === tag) out.push(node);
  (node.children || []).forEach(function (ch) { collectByTag(ch, tag, out); });
  return out;
}

function findById(node, id) {
  if (!node || typeof node !== 'object') return null;
  if (node.attrs && node.attrs.id === id) return node;
  for (const ch of (node.children || [])) {
    const hit = findById(ch, id);
    if (hit) return hit;
  }
  return null;
}

global.window = { matchMedia: function () { return { matches: false }; } };
global.document = {
  head: mkEl('head'),
  body: mkEl('body'),
  getElementById: function () { return null; },
  createElement: function (t) { return mkEl(t); },
  createElementNS: function (ns, t) { return mkEl(t, ns); },
  createTextNode: function (s) { return { text: String(s) }; },
};

let view = null;
global.WB = {
  data: vizData,
  state: { filters: {}, selected: null },
  colors: { type: {}, zone: function () { return '#5ec962'; } },
  bus: { on: function () {}, emit: function () {} },
  select: function (id) { global.WB.state.selected = id; if (view && view.onSelect) view.onSelect(); },
  registerView: function (v) { view = v; },
};

eval(fs.readFileSync(process.argv[2], 'utf8'));
if (!view) throw new Error('map view did not register');

const container = mkEl('div');
view.create(container, global.WB);

// 1. World / Realm switcher renders with Overview + each scope name
const scopeSel = findById(container, 'wbg-map-scope');
if (!scopeSel) throw new Error('missing wbg-map-scope selector for multi-world project');
const optVals = scopeSel.children.map(function (o) { return o.attrs.value; });
const optTexts = scopeSel.children.map(function (o) { return o.textContent; });
if (optVals[0] !== 'overview' || optTexts[0] !== 'Overview (All Worlds)') {
  throw new Error('unexpected overview option: ' + JSON.stringify({ optVals, optTexts }));
}
if (optVals.indexOf('aetheria') < 0 || optVals.indexOf('shadowfen') < 0) {
  throw new Error('missing scope options: ' + JSON.stringify(optVals));
}
if (optTexts.indexOf('Aetheria') < 0 || optTexts.indexOf('Shadowfen') < 0) {
  throw new Error('missing scope labels: ' + JSON.stringify(optTexts));
}

// 2. Overview mode renders world nodes + cross-world portal arc (no surface canvas yet)
if (canvasBuilds !== 0) throw new Error('overview should not build surface terrain canvas, got ' + canvasBuilds);
const worldNodes = collectByClass(container, 'wbm-world-node');
if (worldNodes.length !== 2) throw new Error('expected 2 world nodes in overview, got ' + worldNodes.length);
const crossRoutes = collectByClass(container, 'wbm-cross-route');
if (crossRoutes.length !== 1) throw new Error('expected 1 cross-world route arc, got ' + crossRoutes.length);

// 3. Click Aetheria world node -> side card shows 'View Surface Map' button; clicking it drills in
const aetheriaNode = worldNodes.find(function (n) { return n.attrs['data-id'] === 'aetheria'; });
if (!aetheriaNode) throw new Error('missing aetheria world node');
(aetheriaNode.listeners.click || []).forEach(function (fn) { fn({ shiftKey: false }); });
const drillBtns = collectByClass(container, 'wbm-drill-btn');
if (drillBtns.length !== 1 || drillBtns[0].textContent !== 'View Surface Map') {
  throw new Error('expected View Surface Map button in side card');
}
(drillBtns[0].listeners.click || []).forEach(function (fn) { fn({}); });

// Now inside Aetheria surface map: has Painted Map backdrop option & only Aetheria locations
const styleSel = findById(container, 'wbg-map-style');
const aetheriaStyles = styleSel.children.map(function (o) { return o.attrs.value; });
if (aetheriaStyles.indexOf('painted') < 0) {
  throw new Error('expected Painted Map option for aetheria, got ' + JSON.stringify(aetheriaStyles));
}
const imgs = collectByTag(container, 'image');
if (!imgs.some(function (im) { return im.attrs.href === 'images/maps/aetheria.png'; })) {
  throw new Error('expected aetheria backdrop image to be rendered');
}
const aetheriaMarkers = collectByClass(container, 'wbg-node').map(function (n) { return n.attrs['data-id']; });
if (aetheriaMarkers.indexOf('sunspire') < 0 || aetheriaMarkers.indexOf('gloomgate') >= 0) {
  throw new Error('unexpected markers in aetheria scope: ' + JSON.stringify(aetheriaMarkers));
}

// Switch Aetheria to topographic -> builds 1st procedural terrain canvas
(styleSel.listeners.change || []).forEach(function (fn) { fn({ target: { value: 'topographic' } }); });
if (canvasBuilds !== 1) throw new Error('expected 1st procedural canvas for aetheria, got ' + canvasBuilds);

// 4. Switch to Shadowfen via switcher -> no Painted Map option, builds 2nd procedural terrain canvas
(scopeSel.listeners.change || []).forEach(function (fn) { fn({ target: { value: 'shadowfen' } }); });
const shadowStyles = styleSel.children.map(function (o) { return o.attrs.value; });
if (shadowStyles.indexOf('painted') >= 0) {
  throw new Error('shadowfen has no backdrop; Painted Map option should not appear');
}
if (canvasBuilds !== 2) throw new Error('expected 2nd procedural canvas for shadowfen, got ' + canvasBuilds);
const shadowMarkers = collectByClass(container, 'wbg-node').map(function (n) { return n.attrs['data-id']; });
if (shadowMarkers.indexOf('gloomgate') < 0 || shadowMarkers.indexOf('sunspire') >= 0) {
  throw new Error('unexpected markers in shadowfen scope: ' + JSON.stringify(shadowMarkers));
}

// 5. Return to Overview and double-click Shadowfen node -> drills straight into Shadowfen (and hits terrain cache)
(scopeSel.listeners.change || []).forEach(function (fn) { fn({ target: { value: 'overview' } }); });
const ovNodes = collectByClass(container, 'wbm-world-node');
const shadowNode = ovNodes.find(function (n) { return n.attrs['data-id'] === 'shadowfen'; });
if (!shadowNode) throw new Error('missing shadowfen world node in overview');
(shadowNode.listeners.dblclick || []).forEach(function (fn) { fn({}); });
if (canvasBuilds !== 2) throw new Error('expected terrain cache hit returning to shadowfen, got ' + canvasBuilds);
const afterDblMarkers = collectByClass(container, 'wbg-node').map(function (n) { return n.attrs['data-id']; });
if (afterDblMarkers.indexOf('gloomgate') < 0 || afterDblMarkers.indexOf('sunspire') >= 0) {
  throw new Error('double-click did not drill into shadowfen: ' + JSON.stringify(afterDblMarkers));
}
""",
        encoding="utf-8",
    )
    result = subprocess.run(
        ["node", str(harness), str(map_src_path), str(data_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr + result.stdout




def test_serve_mode_rebuilds_streams_range_and_blocks_non_local_host(tmp_path):
    import http.client
    import threading

    fixtures.write_world(tmp_path)
    audio = tmp_path / "output" / "audio" / "theme.mp3"
    audio.parent.mkdir(parents=True, exist_ok=True)
    audio.write_bytes(b"0123456789ABCDEF")

    server = bv.create_server(tmp_path, port=0)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        # 1. GET /world-viewer.html builds and serves HTML
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        conn.request("GET", "/world-viewer.html")
        resp = conn.getresponse()
        body = resp.read().decode("utf-8")
        assert resp.status == 200
        assert "Test World" in body and "const DATA = " in body
        conn.close()

        # 2. HTTP Range request on audio returns 206 Partial Content
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        conn.request("GET", "/audio/theme.mp3", headers={"Range": "bytes=4-9"})
        resp = conn.getresponse()
        chunk = resp.read()
        assert resp.status == 206
        assert resp.getheader("Content-Type") == "audio/mpeg"
        assert resp.getheader("Content-Range") == "bytes 4-9/16"
        assert chunk == b"456789"
        conn.close()

        # 3. Non-localhost Host header rejected with 403
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        conn.request("GET", "/world-viewer.html", headers={"Host": "evil.example.com"})
        resp = conn.getresponse()
        resp.read()
        assert resp.status == 403
        conn.close()

        # 4. Path traversal outside output/ rejected
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        conn.request("GET", "/../project.yaml")
        resp = conn.getresponse()
        resp.read()
        assert resp.status in (403, 404)
        conn.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
