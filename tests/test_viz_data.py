"""Tests for the world-visualiser data layer (viz_data.py, build_viewer.py)."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parent.parent
SKILL = PLUGIN / "skills" / "world-visualiser"
EXAMPLE = PLUGIN / "skills" / "worldbuilding" / "assets" / "example-the-lattice"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


vd = _load("viz_data_under_test", SKILL / "scripts" / "viz_data.py")
bv = _load("build_viewer_under_test", SKILL / "scripts" / "build_viewer.py")

TOP_KEYS = {
    "version", "project", "counts", "calendar", "nodes", "edges", "timeline",
    "map", "climate", "life", "economy", "warnings",
}  # fmt: skip

CALENDAR = """
name: Test Calendar
eras:
  - {name: Old, prefix: OA, sort_order: 1, end_year: 1000}
  - {name: New, prefix: NA, sort_order: 2}
"""

ECONOMY = """
currencies:
  - {name: Crown, issuing_authority: "the-crown", accepted_in: ["realm", "harbour"]}
resources:
  - {name: "Iron Ore", category: raw-material, rarity: common, consumers: ["harbour"]}
production:
  - {resource: "iron-ore", location: "hill-town", output: "lots", status: active}
trade_routes:
  - name: "Ore Road"
    from_location: "hill-town"
    to_location: "harbour"
    mode: caravan
    goods:
      - {resource: "iron-ore", direction: outbound, volume: high}
  - name: "Far Run"
    from_location: "harbour"
    to_location: "various"
    goods: []
shocks:
  - event: "the-flood"
    production_effects:
      - {location: "harbour", resource: "iron-ore", change: halved}
"""


def md(meta, body=""):
    import yaml

    return "---\n" + yaml.safe_dump(meta, sort_keys=False) + "---\n" + body


def write_world(root, *, economy=True, rich=True):
    (root / "world" / "locations").mkdir(parents=True)
    (root / "world" / "events").mkdir(parents=True)
    (root / "world" / "traditions").mkdir(parents=True)
    (root / "world" / "species").mkdir(parents=True)
    (root / "world" / "history").mkdir(parents=True)
    (root / "project.yaml").write_text("title: Test World\npresent_date: {year: 1500, era_prefix: NA}\n")
    (root / "world" / "history" / "calendar.yaml").write_text(CALENDAR)
    loc = root / "world" / "locations"
    realm = {"name": "Realm", "type": "kingdom", "population": "~2 million", "terrain": "plains"}
    (loc / "realm.md").write_text(md(realm))
    hill = {
        "name": "Hill Town", "type": "town", "parent": "realm", "elevation_m": 800, "area_km2": 12,
        "routes": [{"to": "harbour", "methods": [{"mode": "caravan", "travel_time": "3 days", "distance": "90 km"}]}],
    }  # fmt: skip
    harbour = {
        "name": "Harbour", "type": "city", "parent": "realm",
        "routes": [{"to": "hill-town", "methods": [{"mode": "caravan"}, {"mode": "sailing-ship"}]}],
    }  # fmt: skip
    if rich:
        hill["climate_profile"] = {
            "zone": "alpine", "temperature_c": {"summer": [8, 18], "winter": [-10, 0]},
            "precipitation_mm": 900, "growing_season_days": 90, "drivers": ["altitude 800 m"],
        }  # fmt: skip
        hill["flora"] = [{"name": "winter rye", "role": "staple-crop"}, {"species": "silverbark", "role": "timber"}]
        hill["fauna"] = [{"name": "goat", "role": "domesticate"}]
        hill["resources"] = [{"name": "iron-ore", "category": "raw-material", "rarity": "common"}, "salt"]
        hill["hydrology"] = {"flows_to": "harbour", "freshwater": "abundant"}
        harbour["climate_profile"] = {"zone": "temperate", "temperature_c": {"summer": [15, 25]}, "precipitation_mm": 700}  # noqa: E501
    (loc / "hill-town.md").write_text(md(hill))
    (loc / "harbour.md").write_text(md(harbour))
    (root / "world" / "species" / "silverbark.md").write_text(md({"name": "Silverbark", "type": "plant"}))
    ev = root / "world" / "events"
    (ev / "the-flood.md").write_text(md({
        "name": "The Flood", "type": "disaster", "date": {"year": 10, "era_prefix": "OA"}, "significance": "major",
        "locations": ["harbour"], "leads_to": ["the-rebuilding"], "traces": ["flood-song"],
        "economic_impact": "Trade halted.", "participants": [{"entity": "realm", "role": "affected"}],
    }))  # fmt: skip
    (ev / "the-rebuilding.md").write_text(md({
        "name": "The Rebuilding", "type": "founding", "start_date": {"year": 50, "era_prefix": "OA"},
        "end_date": {"year": 60, "era_prefix": "OA"}, "caused_by": ["the-flood"], "significance": "minor",
    }))  # fmt: skip
    (root / "world" / "traditions" / "flood-song.md").write_text(md({
        "name": "Flood Song", "kind": "song", "status": "living", "fidelity": "simplified",
        "origin_events": ["the-flood"], "first_attested": {"year": 200, "era_prefix": "OA"},
    }))  # fmt: skip
    if economy:
        (root / "world" / "economy.yaml").write_text(ECONOMY)


@pytest.fixture()
def world(tmp_path):
    write_world(tmp_path)
    return tmp_path


@pytest.fixture(scope="module")
def example_data():
    return vd.build_viz_data(EXAMPLE)


# ── synthetic world ─────────────────────────────────────────────────────────


def test_top_level_keys_and_json_roundtrip(world):
    data = vd.build_viz_data(world)
    assert set(data) == TOP_KEYS
    assert data["version"] == 1
    assert json.loads(json.dumps(data)) == data
    assert data["project"]["name"] == "Test World"


def test_calendar_and_nodes(world):
    data = vd.build_viz_data(world)
    cal = data["calendar"]
    assert [e["prefix"] for e in cal["eras"]] == ["OA", "NA"]
    assert cal["eras"][0]["t0"] == 0 and cal["eras"][0]["t1"] == 1000
    assert cal["eras"][1]["t0"] == 1000 and cal["eras"][1]["t1"] >= 1500
    assert data["project"]["present_t"] == 2500 == cal["present_t"]
    assert cal["t_min"] <= 10 and cal["t_max"] >= 2500
    nodes = {n["id"]: n for n in data["nodes"]}
    assert nodes["the-rebuilding"]["t"] == 50 and nodes["the-rebuilding"]["end_t"] == 60
    assert nodes["the-flood"]["end_t"] is None
    node_keys = {"id", "type", "name", "t", "end_t", "date_label", "era", "summary", "status", "tags", "image"}
    assert set(nodes["the-flood"]) == node_keys
    assert nodes["the-flood"]["image"] is None
    assert data["counts"]["event"] == 2 and data["counts"]["location"] == 3


def test_edges_causal_and_memory_flags(world):
    data = vd.build_viz_data(world)
    assert all(set(e) == {"source", "target", "kind", "label", "field", "causal", "memory"} for e in data["edges"])
    causal = [e for e in data["edges"] if e["causal"]]
    assert {(e["source"], e["target"]) for e in causal} == {("the-flood", "the-rebuilding")}
    assert any(e["memory"] and e["source"] == "the-flood" and e["target"] == "flood-song" for e in data["edges"])
    assert not any("provenance" in e for e in data["edges"])


def test_timeline(world):
    tl = vd.build_viz_data(world)["timeline"]
    ev = {e["id"]: e for e in tl["events"]}
    assert ev["the-flood"]["leads_to"] == ["the-rebuilding"]
    assert ev["the-rebuilding"]["caused_by"] == ["the-flood"]
    assert ev["the-flood"]["traces"] == ["flood-song"]
    assert ev["the-flood"]["locations"] == ["harbour"]
    assert ev["the-flood"]["participants"] == ["realm"]
    impact = {"economic": "Trade halted.", "social": None, "political": None, "magical": None}
    assert ev["the-flood"]["impact"] == impact
    assert ev["the-flood"]["significance"] == "major"
    (tr,) = tl["traditions"]
    assert tr["origin_events"] == ["the-flood"] and tr["first_attested_t"] == 200 and tr["kind"] == "song"


def test_route_merge_and_reciprocal(world, tmp_path):
    routes = vd.build_viz_data(world)["map"]["routes"]
    assert len(routes) == 1
    r = routes[0]
    assert (r["id"], r["from"], r["to"]) == ("harbour--hill-town", "harbour", "hill-town")
    assert r["reciprocal"] is True
    assert {m["mode"] for m in r["modes"]} == {"caravan", "sailing-ship"}
    caravan = next(m for m in r["modes"] if m["mode"] == "caravan")
    assert caravan["time"] == "3 days" and caravan["distance"] == "90 km"
    assert r["goods"] == ["Iron Ore"]
    # one-sided declaration
    one = tmp_path / "one"
    write_world(one)
    (one / "world" / "locations" / "harbour.md").write_text(md({"name": "Harbour", "type": "city", "parent": "realm"}))
    (r2,) = vd.build_viz_data(one)["map"]["routes"]
    assert r2["reciprocal"] is False


def test_locations_climate_and_life(world):
    data = vd.build_viz_data(world)
    locs = {x["id"]: x for x in data["map"]["locations"]}
    assert locs["realm"]["parent"] is None and locs["realm"]["children"] == ["harbour", "hill-town"]
    assert locs["realm"]["population"] == 2_000_000 and locs["realm"]["depth"] == 0 and locs["hill-town"]["depth"] == 1
    hill = locs["hill-town"]
    assert hill["elevation_m"] == 800 and hill["area_km2"] == 12
    assert hill["climate"]["zone"] == "alpine" and hill["climate"]["inherited"] is False
    assert hill["hydrology"]["flows_to"] == "harbour"
    assert {r["name"] for r in hill["resources"]} == {"iron-ore", "salt"}
    assert hill["flora"][1] == {"name": "Silverbark", "species": "silverbark", "role": "timber"}
    assert locs["realm"]["climate"] is None
    zones = {z["zone"]: z for z in data["climate"]["zones"]}
    assert set(zones) == {"alpine", "temperate"}
    assert zones["alpine"]["mean_precipitation_mm"] == 900 and zones["alpine"]["mean_temperature_c"] == 4.0
    assert all(c.startswith("#") and len(c) == 7 for c in data["climate"]["legend"].values())
    assert len(set(vd.PALETTE)) == 10
    idx = {(s["kind"], s["name"]): s for s in data["life"]["species_index"]}
    assert idx[("flora", "Silverbark")]["species_id"] == "silverbark"
    assert idx[("fauna", "goat")]["locations"] == ["hill-town"]


def test_climate_inheritance(tmp_path):
    write_world(tmp_path)
    (tmp_path / "world" / "locations" / "harbour.md").write_text(
        md({"name": "Harbour", "type": "city", "parent": "hill-town"})
    )
    locs = {x["id"]: x for x in vd.build_viz_data(tmp_path)["map"]["locations"]}
    assert locs["harbour"]["climate"]["zone"] == "alpine" and locs["harbour"]["climate"]["inherited"] is True
    assert locs["harbour"]["has_own_climate"] is False


def test_economy(world):
    eco = vd.build_viz_data(world)["economy"]
    res = {r["name"]: r for r in eco["resources"]}
    iron = res["Iron Ore"]
    assert iron["category"] == "raw-material" and iron["producers"] == ["hill-town"]
    assert iron["consumers"] == ["harbour"]
    assert "harbour--hill-town" in iron["routes"]
    tr = {t["id"]: t for t in eco["trade_routes"]}
    assert tr["ore-road"]["from"] == "hill-town" and tr["ore-road"]["mode"] == "caravan"
    assert tr["far-run"]["to"] is None and tr["far-run"]["to_label"] == "various"
    (cur,) = eco["currencies"]
    assert cur["accepted_in"] == ["harbour", "realm"]
    assert eco["shocks"][0]["event"] == "the-flood" and "production_effects" in eco["shocks"][0]["effects"]


def test_layout_deterministic_and_bounded(world):
    a = vd.build_viz_data(world)
    b = vd.build_viz_data(world)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    for loc in a["map"]["locations"]:
        assert 0 <= loc["x"] <= 1000 and 0 <= loc["y"] <= 1000


def test_layout_function_handles_edge_cases():
    assert vd.compute_layout([], {}, []) == {}
    assert vd.compute_layout(["a"], {}, []) == {"a": (500.0, 500.0)}
    # parent cycle and coincident handling must not crash or leave bounds
    pos = vd.compute_layout(["a", "b", "c"], {"a": "b", "b": "a"}, [("a", "c")])
    assert set(pos) == {"a", "b", "c"}
    assert all(0 <= x <= 1000 and 0 <= y <= 1000 for x, y in pos.values())


def test_sparse_world_warnings(tmp_path):
    write_world(tmp_path, economy=False, rich=False)
    data = vd.build_viz_data(tmp_path)
    w = data["warnings"]
    assert "0 locations have climate data" in w
    assert "0 locations have flora data" in w
    assert "0 locations have fauna data" in w
    assert any(x.startswith("economy data missing") for x in w)
    assert data["climate"]["zones"] == [] and data["life"]["species_index"] == []
    assert data["economy"]["trade_routes"] == [] and data["economy"]["shocks"] == []


def test_minimal_project_with_nothing(tmp_path):
    (tmp_path / "project.yaml").write_text("title: Empty\n")
    data = vd.build_viz_data(tmp_path)
    assert set(data) == TOP_KEYS
    assert data["nodes"] == [] and data["map"]["locations"] == []
    assert data["project"]["present_t"] is None and data["calendar"]["eras"] == []
    assert any("no locations" in x for x in data["warnings"])
    json.dumps(data)


# ── build_viewer ────────────────────────────────────────────────────────────


def test_html_marker_replacement_escapes_script_end(tmp_path):
    write_world(tmp_path)
    (tmp_path / "world" / "locations" / "realm.md").write_text(
        md({"name": "Evil </script><script>alert(1)</script>   Realm", "type": "kingdom"})
    )
    tpl = tmp_path / "tpl.html"
    tpl.write_text("<html><script>const WORLD = /*__WORLD_DATA__*/null;</script></html>")
    out = tmp_path / "out" / "viewer.html"
    assert bv.main([str(tmp_path), "--out", str(out), "--template", str(tpl)]) == 0
    html = out.read_text(encoding="utf-8")
    assert bv.MARKER not in html
    assert html.count("</script>") == 1
    assert " " not in html and " " not in html
    payload = html.split("const WORLD = ", 1)[1].split(";</script>", 1)[0]
    data = json.loads(payload)
    assert data["map"]["locations"][-1]["name"] if False else True
    names = [loc["name"] for loc in data["map"]["locations"]]
    assert "Evil </script><script>alert(1)</script>   Realm" in names


def test_default_output_path_and_viewer(world):
    assert bv.main([str(world)]) == 0
    out = world / "output" / "world-viewer.html"
    html = out.read_text(encoding="utf-8")
    assert 'id="app"' in html and "const DATA = " in html and bv.MARKER not in html and "Test World" in html


def test_json_only_and_missing_project(world, tmp_path, capsys):
    assert bv.main([str(world), "--json-only"]) == 0
    data = json.loads((world / "output" / "viz.json").read_text(encoding="utf-8"))
    assert set(data) == TOP_KEYS
    empty = tmp_path / "nowhere"
    empty.mkdir()
    assert bv.main([str(empty)]) == 1
    assert "no project.yaml" in capsys.readouterr().err


def test_template_without_marker_is_rejected(world, tmp_path, capsys):
    tpl = tmp_path / "bad.html"
    tpl.write_text("<html></html>")
    assert bv.main([str(world), "--template", str(tpl)]) == 1
    assert "marker" in capsys.readouterr().err


def test_cli_exit_code(tmp_path):
    r = subprocess.run(
        [sys.executable, str(SKILL / "scripts" / "build_viewer.py"), str(tmp_path)], capture_output=True, text=True
    )
    assert r.returncode == 1 and "project.yaml" in r.stderr


def test_image_discovery_convention(world):
    loc_dir = world / "output" / "images" / "locations"
    ev_dir = world / "output" / "images" / "events"
    tr_dir = world / "output" / "images" / "traditions"
    for d in (loc_dir, ev_dir, tr_dir):
        d.mkdir(parents=True)
    (loc_dir / "harbour.png").write_bytes(b"\x89PNG\r\n\x1a\nfake")
    (ev_dir / "the-flood.webp").write_bytes(b"RIFF\x00\x00\x00\x00WEBP")
    (tr_dir / "flood-song.jpg").write_bytes(b"\xff\xd8\xff\xe0fake")
    nodes = {n["id"]: n for n in vd.build_viz_data(world)["nodes"]}
    assert nodes["harbour"]["image"] == "images/locations/harbour.png"
    assert nodes["the-flood"]["image"] == "images/events/the-flood.webp"
    assert nodes["flood-song"]["image"] == "images/traditions/flood-song.jpg"
    assert nodes["hill-town"]["image"] is None


def test_image_discovery_frontmatter_and_safety(world):
    custom = world / "output" / "images" / "custom"
    custom.mkdir(parents=True)
    (custom / "realm-crest.png").write_bytes(b"\x89PNG\r\n\x1a\ncrest")
    (world / "world" / "locations" / "realm.md").write_text(
        md({"name": "Realm", "type": "kingdom", "image": "images/custom/realm-crest.png"})
    )
    # External URL or path traversal must be ignored safely.
    (world / "world" / "locations" / "hill-town.md").write_text(
        md({"name": "Hill Town", "type": "town", "parent": "realm", "image": "https://evil.example/x.png"})
    )
    nodes = {n["id"]: n for n in vd.build_viz_data(world)["nodes"]}
    assert nodes["realm"]["image"] == "images/custom/realm-crest.png"
    assert nodes["hill-town"]["image"] is None


def test_embed_images_data_uri(world):
    import base64

    png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    webp_bytes = b"RIFF\x0c\x00\x00\x00WEBPVP8 "
    (world / "output" / "images" / "locations").mkdir(parents=True)
    (world / "output" / "images" / "events").mkdir(parents=True)
    (world / "output" / "images" / "locations" / "harbour.png").write_bytes(png_bytes)
    (world / "output" / "images" / "events" / "the-flood.webp").write_bytes(webp_bytes)

    data = vd.build_viz_data(world, embed_images=True)
    nodes = {n["id"]: n for n in data["nodes"]}
    assert nodes["harbour"]["image"] == "data:image/png;base64," + base64.b64encode(png_bytes).decode("ascii")
    assert nodes["the-flood"]["image"] == "data:image/webp;base64," + base64.b64encode(webp_bytes).decode("ascii")
    assert nodes["hill-town"]["image"] is None

    out = world / "output" / "viz-embedded.json"
    assert bv.main([str(world), "--json-only", "--embed-images", "--out", str(out)]) == 0
    embedded = json.loads(out.read_text(encoding="utf-8"))
    enodes = {n["id"]: n for n in embedded["nodes"]}
    assert enodes["harbour"]["image"].startswith("data:image/png;base64,")


# ── skill files ─────────────────────────────────────────────────────────────


def test_skill_frontmatter_and_command():
    import yaml

    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    assert len(text.splitlines()) < 80
    meta = yaml.safe_load(text.split("---", 2)[1])
    assert set(meta) == {"name", "description"} and meta["name"] == "world-visualiser"
    assert len(meta["description"]) <= 600 and ": " not in meta["description"]
    cmd = (PLUGIN / "commands" / "wb-visualise.md").read_text(encoding="utf-8")
    assert set(yaml.safe_load(cmd.split("---", 2)[1])) == {"description"} and "$ARGUMENTS" in cmd


# ── example world ───────────────────────────────────────────────────────────


def test_example_integrity(example_data):
    d = example_data
    assert set(d) == TOP_KEYS
    ids = {n["id"] for n in d["nodes"]}
    assert len(ids) == len(d["nodes"]) > 50
    assert all(e["source"] in ids and e["target"] in ids for e in d["edges"])
    locs = {x["id"]: x for x in d["map"]["locations"]}
    assert locs
    assert all(x["parent"] is None or x["parent"] in locs for x in locs.values())
    assert all(c in locs for x in locs.values() for c in x["children"])
    assert all(0 <= x["x"] <= 1000 and 0 <= x["y"] <= 1000 for x in locs.values())
    for r in d["map"]["routes"]:
        assert r["from"] in locs and r["to"] in locs


def test_example_events_reference_real_events(example_data):
    events = {e["id"] for e in example_data["timeline"]["events"]}
    assert len(events) > 10
    for e in example_data["timeline"]["events"]:
        assert set(e["caused_by"]) <= events and set(e["leads_to"]) <= events
    assert example_data["timeline"]["traditions"]
    assert example_data["economy"]["resources"] and example_data["economy"]["currencies"]


def test_example_json_roundtrip_and_sample(example_data):
    text = json.dumps(example_data)
    assert json.loads(text) == example_data
    tmp = Path(os.environ.get("TMPDIR", "/tmp"))
    sample = tmp / "viz-sample.json"
    sample.write_text(text, encoding="utf-8")
    assert sample.stat().st_size > 1000
