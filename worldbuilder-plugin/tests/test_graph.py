"""Tests for the world-validate graph layer (graph.py)."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parent.parent
SCRIPTS = PLUGIN / "skills" / "world-validate" / "scripts"
EXAMPLE = PLUGIN / "skills" / "worldbuilding" / "assets" / "example-the-lattice"

_spec = importlib.util.spec_from_file_location("world_graph", SCRIPTS / "graph.py")
assert _spec is not None and _spec.loader is not None
wg = importlib.util.module_from_spec(_spec)
sys.modules["world_graph"] = wg
_spec.loader.exec_module(wg)

CALENDAR = """
name: Test Calendar
eras:
  - {name: Old, prefix: OA, sort_order: 1, end_year: 1000}
  - {name: New, prefix: NA, sort_order: 2}
"""


def _write(base: Path, rel: str, front: str) -> None:
    p = base / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(f"---\n{front.strip()}\n---\n\nBody.\n", encoding="utf-8")


def make_world(tmp_path: Path, files: dict) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "project.yaml").write_text("title: Test World\n", encoding="utf-8")
    cal = tmp_path / "world" / "history"
    cal.mkdir(parents=True, exist_ok=True)
    (cal / "calendar.yaml").write_text(CALENDAR, encoding="utf-8")
    for rel, front in files.items():
        _write(tmp_path, rel, front)
    return tmp_path


@pytest.fixture()
def chain(tmp_path):
    return make_world(
        tmp_path / "chain",
        {
            # a -> b -> c, declared in mixed directions; a<->b declared on both sides.
            "world/events/a.md": "name: A\ntype: war\ndate: {year: 900, era_prefix: OA}\n"
            "leads_to: [b]\nroot_causes: [The sky fell]",
            "world/events/b.md": "name: B\ntype: war\ndate: {year: 10, era_prefix: NA}\ncaused_by: [a]",
            "world/events/c.md": "name: C\ntype: war\ndate: {year: 20, era_prefix: NA}\ncaused_by: [b]",
            "world/events/lonely.md": "name: Lonely\ntype: war\ndate: {year: 5, era_prefix: NA}",
        },
    )


@pytest.fixture()
def structure(tmp_path):
    return make_world(
        tmp_path / "structure",
        {
            "world/locations/realm.md": "name: Realm\ntype: kingdom",
            "world/locations/city.md": "name: City\ntype: city\nparent: realm\n"
            "routes:\n  - {to: port, route_type: major}",
            "world/locations/port.md": "name: Port\ntype: city\nparent: realm",
            "world/locations/farm.md": "name: Farm\ntype: village",
            "world/factions/guild.md": "name: Guild\ntype: guild\nheadquarters: city\nmembers: [ann]",
            "world/characters/ann.md": "name: Ann\ntype: character\nlocation: city\nfaction: guild",
            "world/characters/bob.md": "name: Bob\ntype: character\nlocation: farm\n"
            "relationships:\n  - {entity: ann, type: ally}",
            "world/events/fire.md": "name: Fire\ntype: catastrophe\ndate: {year: 3, era_prefix: NA}\n"
            "locations: [city]\nparticipants:\n  - {entity: guild, role: victim}",
        },
    )


def edges(g, kind=None):
    return [(e["source"], e["target"], e["kind"]) for e in g.edges if kind is None or e["kind"] == kind]


# ── edge derivation ─────────────────────────────────────────────────────────


def test_causal_edges_normalised_and_deduplicated(chain):
    g = wg.WorldGraph.from_project(chain)
    assert sorted(edges(g, "causes")) == [("a", "b", "causes"), ("b", "c", "causes")]
    ab = next(e for e in g.edges if (e["source"], e["target"]) == ("a", "b"))
    assert {p["field"] for p in ab["provenance"]} == {"leads_to", "caused_by"}  # both declarations kept
    assert all(p["file"].endswith(".md") for p in ab["provenance"])


def test_generic_kinds_and_nested_fields(structure):
    g = wg.WorldGraph.from_project(structure)
    ks = set(edges(g))
    assert ("city", "realm", "parent") in ks
    assert ("city", "port", "route") in ks
    assert ("ann", "guild", "member_of") in ks
    assert ("guild", "ann", "member") in ks
    assert ("guild", "city", "headquarters") in ks
    assert ("ann", "city", "location") in ks
    assert ("fire", "guild", "participant") in ks
    assert ("fire", "city", "location") in ks
    rel = next(e for e in g.edges if e["kind"] == "relationship")
    assert (rel["source"], rel["target"], rel["label"]) == ("bob", "ann", "ally")


def test_no_self_edges_or_name_field_matches(tmp_path):
    root = make_world(tmp_path, {"world/factions/x.md": "name: X\ntype: guild\ntags: [x]\nallies: [x]"})
    g = wg.WorldGraph.from_project(root)
    assert g.edges == []


# ── queries ─────────────────────────────────────────────────────────────────


def test_why_three_event_chain(chain):
    g = wg.WorldGraph.from_project(chain)
    tree = g.ancestors("c")
    assert tree["slug"] == "c"
    assert tree["children"][0]["slug"] == "b"
    assert tree["children"][0]["children"][0]["slug"] == "a"
    assert g.root_causes("c") == ["a"]
    assert g.root_cause_text("a") == ["The sky fell"]
    assert g.causal_depth() == 2


def test_why_cli_text_and_json(chain):
    out = subprocess.run(
        [sys.executable, str(SCRIPTS / "graph.py"), str(chain), "why", "c"], capture_output=True, text=True, check=True
    ).stdout
    assert "b (event)" in out and "a (event)" in out and "The sky fell" in out
    data = json.loads(
        subprocess.run(
            [sys.executable, str(SCRIPTS / "graph.py"), str(chain), "why", "c", "--json"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    )
    assert data["roots"][0]["slug"] == "a"


def test_impact_causal_and_structural(structure, chain):
    g = wg.WorldGraph.from_project(chain)
    res = g.impact("a")
    assert [x["slug"] for x in res["effects"]] == ["b", "c"]
    assert [x["slug"] for x in g.impact("a", depth=1)["effects"]] == ["b"]

    g = wg.WorldGraph.from_project(structure)
    dep = {x["slug"]: x for x in g.impact("realm")["dependents"]}
    assert {"city", "port"} <= set(dep)  # locations contained in it
    assert "ann" in dep and "guild" in dep and "fire" in dep  # located / HQ'd / happened there
    assert "farm" not in dep and "bob" not in dep
    assert dep["city"]["path"][0]["kind"] == "parent"
    assert len(dep["ann"]["path"]) >= 2  # edge path is recorded
    # faction members and routes
    guild = {x["slug"] for x in g.impact("guild")["dependents"]}
    assert "ann" in guild
    assert "port" in {x["slug"] for x in g.impact("city")["dependents"]}  # route / parent sibling via route
    assert g.impact("realm", depth=1)["dependents"] and all(
        len(x["path"]) == 1 for x in g.impact("realm", depth=1)["dependents"]
    )


def test_shortest_path_and_neighbors(structure):
    g = wg.WorldGraph.from_project(structure)
    steps = g.shortest_path("bob", "guild")
    assert [s["to"] for s in steps] == ["ann", "guild"]
    assert steps[0]["kind"] == "relationship" and steps[1]["kind"] in ("member_of", "member")
    assert g.shortest_path("bob", "bob") == []
    assert g.shortest_path("bob", "nonexistent") is None
    assert g.shortest_path("farm", "realm") is not None  # farm - bob - ann - city - realm
    assert {n["slug"] for n in g.neighbors("city")} >= {"realm", "port", "ann", "guild", "fire"}


def test_unrooted(chain, structure):
    g = wg.WorldGraph.from_project(chain)
    u = g.unrooted()
    assert "lonely" in u["events"] and "lonely" in u["edgeless"]
    assert "a" not in u["events"]  # has root_causes text
    assert "b" not in u["events"] and "c" not in u["events"]


def test_unreachable_path_is_none(tmp_path):
    root = make_world(
        tmp_path, {"world/locations/a.md": "name: A\ntype: city", "world/locations/b.md": "name: B\ntype: city"}
    )
    g = wg.WorldGraph.from_project(root)
    assert g.shortest_path("a", "b") is None
    assert len(g.components()) == 2


def test_cycle_does_not_hang(tmp_path):
    root = make_world(
        tmp_path,
        {
            "world/events/x.md": "name: X\ntype: war\ncaused_by: [y]",
            "world/events/y.md": "name: Y\ntype: war\ncaused_by: [x]",
        },
    )
    g = wg.WorldGraph.from_project(root)
    g.ancestors("x")
    g.impact("x")
    assert g.causal_depth() >= 1


# ── export ──────────────────────────────────────────────────────────────────


def test_export_schema_and_timeline(chain):
    d = wg.WorldGraph.from_project(chain).to_dict()
    assert set(d) == {"version", "project", "calendar", "nodes", "edges"}
    assert d["version"] == 1 and d["project"]["title"] == "Test World"
    assert [e["prefix"] for e in d["calendar"]["eras"]] == ["OA", "NA"]
    n = {x["id"]: x for x in d["nodes"]}
    assert {"id", "slug", "type", "name", "date", "era", "t", "summary"} <= set(n["a"])
    assert n["a"]["t"] < n["b"]["t"] < n["c"]["t"]  # era offsets: OA 900 < NA 10 < NA 20
    assert n["a"]["era"] == "Old"
    json.dumps(d)  # serialisable
    assert all({"source", "target", "kind"} <= set(e) for e in d["edges"])


def test_export_cli_writes_file(chain, tmp_path):
    out = tmp_path / "g.json"
    subprocess.run(
        [sys.executable, str(SCRIPTS / "graph.py"), str(chain), "export", "--out", str(out)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(out.read_text())["nodes"]


def test_cli_errors(chain):
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "graph.py"), str(chain), "why", "nope"], capture_output=True, text=True
    )
    assert r.returncode == 2 and "no entity" in r.stderr
    r = subprocess.run(
        [sys.executable, str(SCRIPTS / "graph.py"), str(chain / "world"), "stats"], capture_output=True, text=True
    )
    assert r.returncode == 2


# ── the-lattice example ─────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def lattice():
    return wg.WorldGraph.from_project(EXAMPLE)


def test_lattice_node_count_matches_validator(lattice):
    sys.path.insert(0, str(SCRIPTS))
    import validate

    _, entities = validate.validate(EXAMPLE)
    assert len(lattice.nodes) == sum(len(v) for v in entities.values()) == 130  # 122 + 8 example traditions


def test_lattice_edges_reference_existing_nodes(lattice):
    ids = set(lattice.nodes)
    assert lattice.edges
    assert all(e["source"] in ids and e["target"] in ids for e in lattice.edges)
    assert all(e["provenance"] for e in lattice.edges)


def test_lattice_why_reaches_roots(lattice):
    roots = lattice.root_causes("kethvol-discovers-anomalies")
    assert "humans-achieve-spaceflight" in roots
    assert all(not lattice.causal_parents(r) for r in roots)
    assert lattice.causal_depth() >= 10


def test_lattice_export_t_follows_causality(lattice):
    d = lattice.to_dict()
    n = {x["id"]: x for x in d["nodes"]}
    assert len(n) == 130  # 122 + 8 example traditions (world/traditions/)
    causes = [e for e in d["edges"] if e["kind"] == "causes"]
    assert causes
    checked = 0
    for e in causes:
        a, b = n[e["source"]]["t"], n[e["target"]]["t"]
        if a is not None and b is not None:
            assert a <= b, (e["source"], e["target"])
            checked += 1
    assert checked >= 30
    assert all(isinstance(x["t"], (int, float)) for x in n.values() if x["type"] == "event" and x["date"])


def test_lattice_impact_and_path(lattice):
    dep = {x["slug"] for x in lattice.impact("sol-system")["dependents"]}
    assert {"meridian-station", "terra-prime"} <= dep
    steps = lattice.shortest_path("seren-voss", "dresh-mining-guilds")
    assert steps and len(steps) <= 3
    st = lattice.stats()
    # 122 + 8 example traditions
    assert st["nodes"] == 130 and st["components"] >= 1


# ── traditions and the memory chain ──────────────────────────────────────────


@pytest.fixture()
def memory(tmp_path):
    return make_world(
        tmp_path / "memory",
        {
            "world/events/drought.md": "name: Drought\ntype: natural_disaster\ndate: {year: 5, era_prefix: NA}\n"
            "root_causes: [Monsoon failed]\nleads_to: [flood]",
            "world/events/flood.md": "name: Flood\ntype: natural_disaster\ndate: {year: 10, era_prefix: NA}\n"
            "caused_by: [drought]\ntraces: [lantern-night, old-ford]",
            "world/locations/old-ford.md": "name: Old Ford\ntype: ford",
            "world/traditions/lantern-night.md": "name: Lantern Night\nkind: festival\nstatus: fading\n"
            "origin_events: [flood]\nfirst_attested: {year: 40, era_prefix: NA}\ndrives: [old-ford]\n"
            "related: [drowned-bell]",
            "world/traditions/drowned-bell.md": "name: Drowned Bell\nkind: legend\norigin_unknown: lost",
            "world/traditions/folk-rhyme.md": "name: Folk Rhyme\nkind: song\norigin_events: [drought]",
        },
    )


def test_tradition_node_and_t_from_first_attested(memory):
    g = wg.WorldGraph.from_project(memory)
    assert g.nodes["lantern-night"]["type"] == "tradition"
    assert g.nodes["lantern-night"]["t"] is not None
    assert g.nodes["drowned-bell"]["t"] is None
    assert g.nodes["lantern-night"]["t"] > g.nodes["flood"]["t"]


def test_leaves_trace_edges_deduplicated_with_provenance(memory):
    g = wg.WorldGraph.from_project(memory)
    es = [e for e in g.edges if e["kind"] == "leaves-trace" and e["target"] == "lantern-night"]
    assert len(es) == 1 and es[0]["source"] == "flood"
    assert {p["field"] for p in es[0]["provenance"]} == {"traces", "origin_events"}
    # traces on non-tradition entities and tradition-only origin both yield edges event -> target
    assert any(e["kind"] == "leaves-trace" and (e["source"], e["target"]) == ("flood", "old-ford") for e in g.edges)
    assert any(e["kind"] == "leaves-trace" and (e["source"], e["target"]) == ("drought", "folk-rhyme") for e in g.edges)
    # the memory link is not a causal edge, and drives text did not become an edge
    assert not any(e["kind"] == "causes" and "lantern-night" in (e["source"], e["target"]) for e in g.edges)
    assert not any(e["source"] == "lantern-night" and e["target"] == "old-ford" for e in g.edges)


def test_why_tradition_shows_origin_then_causal_ancestry(memory):
    g = wg.WorldGraph.from_project(memory)
    tree = g.ancestors("lantern-night")
    flood = tree["children"][0]
    assert flood["slug"] == "flood" and flood["link"] == "memory"
    drought = flood["children"][0]
    assert drought["slug"] == "drought" and "link" not in drought
    assert g.root_causes("lantern-night") == ["drought"]
    text = wg._render_why(g, "lantern-night", tree, g.root_causes("lantern-night"))
    assert "[memory link: origin of tradition]" in text.split("drought")[0]
    assert text.count("memory link") == 1  # only the first hop is the memory link


def test_why_tradition_without_origin(memory):
    g = wg.WorldGraph.from_project(memory)
    text = wg._render_why(g, "drowned-bell", g.ancestors("drowned-bell"), g.root_causes("drowned-bell"))
    assert "no origin events" in text and "origin_unknown: lost" in text


def test_impact_traces_in_the_present(memory):
    g = wg.WorldGraph.from_project(memory)
    res = g.impact("flood")
    traces = {t["slug"]: t for t in res["traces"]}
    assert traces["lantern-night"]["status"] == "fading" and traces["lantern-night"]["type"] == "tradition"
    assert traces["old-ford"]["status"] is None
    text = wg._render_impact(g, res)
    assert "Traces in the present (2)" in text and "lantern-night (tradition) [fading]" in text
    # tradition does not leak into causal effects
    assert all(x["slug"] != "lantern-night" for x in res["effects"])


def test_unrooted_flags_traditions_without_origin(memory):
    u = wg.WorldGraph.from_project(memory).unrooted()
    assert u["traditions"] == ["drowned-bell"]


def test_export_includes_tradition_and_leaves_trace(memory):
    data = wg.WorldGraph.from_project(memory).to_dict()
    assert any(n["type"] == "tradition" for n in data["nodes"])
    assert any(e["kind"] == "leaves-trace" for e in data["edges"])
    json.dumps(data)


def test_cli_why_and_impact_on_tradition_world(memory):
    out = subprocess.run(
        [sys.executable, str(SCRIPTS / "graph.py"), str(memory), "why", "lantern-night"],
        capture_output=True, text=True, check=True,
    ).stdout
    assert "flood" in out and "drought" in out
