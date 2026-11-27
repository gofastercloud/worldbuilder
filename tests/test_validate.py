"""Tests for the world-validate script."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parent.parent
SCRIPT = PLUGIN / "skills" / "world-validate" / "scripts" / "validate.py"
EXAMPLE = PLUGIN / "skills" / "worldbuilding" / "assets" / "example-the-lattice"

_spec = importlib.util.spec_from_file_location("world_validate", SCRIPT)
assert _spec is not None and _spec.loader is not None
wv = importlib.util.module_from_spec(_spec)
sys.modules["world_validate"] = wv
_spec.loader.exec_module(wv)

CALENDAR = """
eras:
  - {name: Old, prefix: OA, sort_order: 1}
  - {name: New, prefix: NA, sort_order: 2}
"""

PROJECT = """
title: Test World
world_flags:
  technology:
    steam_power: false
    gunpowder: {value: false}
  peoples:
    cross_species_breeding: false
"""


def fm(**meta) -> str:
    import yaml

    return "---\n" + yaml.safe_dump(meta, sort_keys=False) + "---\n\nBody.\n"


def d(year, era="NA", **kw):
    return {"year": year, "era_prefix": era, **kw}


def make_project(root: Path, files: dict, project: str = PROJECT) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "project.yaml").write_text(project)
    (root / "world" / "history").mkdir(parents=True, exist_ok=True)
    (root / "world" / "history" / "calendar.yaml").write_text(CALENDAR)
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    return root


def run(root: Path):
    report, _ = wv.validate(root)
    return report.issues


def find(issues, check, severity=None, contains=""):
    return [
        i
        for i in issues
        if i["check"] == check and (severity is None or i["severity"] == severity) and contains in i["message"]
    ]


def event(name, date=None, **kw):
    meta = {
        "name": name,
        "type": "milestone",
        "date": date or d(100),
        "immediate_consequences": ["x"],
        "long_term_consequences": ["y"],
        "caused_by": [],
        "leads_to": [],
        "root_causes": ["start"],
        **kw,
    }
    return fm(**meta)


# ── the example world ────────────────────────────────────────────────────────


def test_example_world_has_no_errors():
    issues = run(EXAMPLE)
    errors = [i for i in issues if i["severity"] == "error"]
    assert errors == [], errors


def test_example_world_is_fully_clean():
    assert run(EXAMPLE) == []


def test_cli_exit_codes_and_json(tmp_path):
    warn_root = make_project(
        tmp_path / "warn",
        {"world/events/lonely.md": fm(name="Lonely", type="milestone", date=d(5), importance="major")},
    )
    ok = subprocess.run([sys.executable, "-B", str(SCRIPT), str(warn_root), "--json"], capture_output=True, text=True)
    assert ok.returncode == 0, ok.stderr
    data = json.loads(ok.stdout)
    assert data["errors"] == 0 and data["warnings"] > 0
    assert {"severity", "check", "file", "field", "message", "hint"} <= set(data["issues"][0])

    only_errors = subprocess.run(
        [sys.executable, "-B", str(SCRIPT), str(warn_root), "--json", "--severity", "error"],
        capture_output=True,
        text=True,
    )
    assert json.loads(only_errors.stdout)["issues"] == []

    root = make_project(
        tmp_path, {"world/events/a.md": event("A", caused_by=["nonexistent"], type="death", participants=["ghost"])}
    )
    bad = subprocess.run([sys.executable, "-B", str(SCRIPT), str(root)], capture_output=True, text=True)
    assert bad.returncode == 1
    assert "ERRORS" in bad.stdout and "fix:" in bad.stdout

    missing = subprocess.run(
        [sys.executable, "-B", str(SCRIPT), str(tmp_path / "nope")], capture_output=True, text=True
    )
    assert missing.returncode == 2


# ── original checks ──────────────────────────────────────────────────────────


def test_frontmatter_parse_error(tmp_path):
    root = make_project(tmp_path, {"world/characters/bad.md": "---\nname: [unclosed\n---\nbody\n"})
    assert find(run(root), "frontmatter", "error", "parse error")


def test_dangling_ref(tmp_path):
    root = make_project(
        tmp_path,
        {
            "world/characters/a.md": fm(
                name="Alice", status="alive", relationships=[{"target": "nobody", "type": "x"}]
            ),
        },
    )
    hits = find(run(root), "dangling-ref", "error", "nobody")
    assert hits and hits[0]["file"].endswith("a.md") and hits[0]["field"] == "relationships"


def test_missing_reverse_link_family(tmp_path):
    root = make_project(
        tmp_path,
        {
            "world/characters/parent.md": fm(name="Parent", status="alive", age=50, family_links={"children": ["kid"]}),
            "world/characters/kid.md": fm(name="Kid", status="alive", age=10, family_links={}),
        },
    )
    issues = run(root)
    assert find(issues, "symmetry", "error", "child's father/mother doesn't reference back")
    assert not find(issues, "min-parent-age")  # 40 years apart is fine


def test_min_parent_age(tmp_path):
    root = make_project(
        tmp_path,
        {
            "world/characters/parent.md": fm(name="Parent", status="alive", age=20, family_links={"children": ["kid"]}),
            "world/characters/kid.md": fm(name="Kid", status="alive", age=10, family_links={"father": "parent"}),
        },
    )
    assert find(run(root), "min-parent-age", "error", "less than 16")


def test_faction_leader_dead_and_not_member(tmp_path):
    root = make_project(
        tmp_path,
        {
            "world/characters/boss.md": fm(name="Boss", status="dead", last_appearance="ch1", faction="guild"),
            "world/factions/guild.md": fm(name="Guild", leader="boss", members=["boss"]),
            "world/factions/other.md": fm(name="Other", leader="boss", members=[]),
        },
    )
    issues = run(root)
    assert find(issues, "faction-leader", "error", "has status 'dead'")
    assert find(issues, "faction-leader", "warning", "not a member")


def test_world_flag_transport_and_keywords(tmp_path):
    root = make_project(
        tmp_path,
        {
            "world/locations/a.md": fm(name="A", type="city", routes=[{"to": "b", "method": "railway"}]),
            "world/locations/b.md": fm(name="B", type="city", routes=[{"to": "a", "method": "road"}]),
            "story/chapters/ch1.md": "---\ntitle: One\n---\nHe raised the rifle and fired.\n",
        },
    )
    issues = run(root)
    assert find(issues, "world-flag", "error", "railway")
    assert find(issues, "world-flag", "warning", "'rifle'")


def test_cross_species_breeding_and_hierarchy(tmp_path):
    root = make_project(
        tmp_path,
        {
            "world/species/elf.md": fm(name="Elf", races=["wood-elf"]),
            "world/species/orc.md": fm(name="Orc", races=[]),
            "world/races/wood-elf.md": fm(name="Wood Elf", species="elf"),
            "world/characters/mum.md": fm(name="Mum", species="elf", status="alive"),
            "world/characters/dad.md": fm(name="Dad", species="orc", status="alive"),
            "world/characters/odd.md": fm(name="Odd", species="orc", race="wood-elf", status="alive"),
            "world/events/birth.md": event("Birth", type="birth", parents=["mum", "dad"]),
        },
    )
    issues = run(root)
    assert find(issues, "world-flag", "error", "cross_species_breeding is not enabled")
    assert find(issues, "hierarchy", "error", "belongs to species")


def test_location_cycle(tmp_path):
    root = make_project(
        tmp_path,
        {
            "world/locations/a.md": fm(name="A", type="city", parent="b"),
            "world/locations/b.md": fm(name="B", type="city", parent="c"),
            "world/locations/c.md": fm(name="C", type="city", parent="a"),
            "world/locations/d.md": fm(name="D", type="city", parent="a"),
        },
    )
    cycles = find(run(root), "location-cycle", "error")
    assert len(cycles) == 1  # one issue for the cycle, none for the branch leading into it


# ── causal consistency ───────────────────────────────────────────────────────


def test_cause_later_than_effect(tmp_path):
    root = make_project(
        tmp_path,
        {
            "world/events/cause.md": event("Cause", d(200), leads_to=["effect"]),
            "world/events/effect.md": event("Effect", d(100), caused_by=["cause"]),
        },
    )
    issues = run(root)
    assert find(issues, "causal-chronology", "error", "AFTER")
    assert not find(issues, "causal-reciprocity")


def test_cause_earlier_era_is_fine_and_cross_era_ordering(tmp_path):
    root = make_project(
        tmp_path,
        {
            "world/events/cause.md": event("Cause", d(900, "OA"), leads_to=["effect"]),
            "world/events/effect.md": event("Effect", d(5, "NA"), caused_by=["cause"]),
        },
    )
    assert not find(run(root), "causal-chronology")


def test_causal_reciprocity_warning(tmp_path):
    root = make_project(
        tmp_path,
        {
            "world/events/a.md": event("A", d(1), leads_to=["b"]),
            "world/events/b.md": event("B", d(2)),
        },
    )
    assert find(run(root), "causal-reciprocity", "warning")


def test_causal_cycle(tmp_path):
    root = make_project(
        tmp_path,
        {
            "world/events/a.md": event("A", d(1), caused_by=["c"], leads_to=["b"]),
            "world/events/b.md": event("B", d(1), caused_by=["a"], leads_to=["c"]),
            "world/events/c.md": event("C", d(1), caused_by=["b"], leads_to=["a"]),
        },
    )
    cyc = find(run(root), "causal-cycle", "error")
    assert len(cyc) == 1 and "a" in cyc[0]["message"]


def test_orphan_and_missing_consequences(tmp_path):
    root = make_project(
        tmp_path,
        {
            "world/events/lonely.md": fm(name="Lonely", type="milestone", date=d(5), importance="major"),
            "world/events/linked-a.md": event("Linked A", d(1), leads_to=["linked-b"]),
            "world/events/linked-b.md": event("Linked B", d(2), caused_by=["linked-a"]),
        },
    )
    issues = run(root)
    orphans = find(issues, "orphan-event", "warning")
    assert len(orphans) == 1 and "Lonely" in orphans[0]["message"]
    assert find(issues, "missing-consequences", "warning", "Lonely")
    assert not find(issues, "missing-consequences", contains="Linked")


def test_open_ended_waives_only_with_reason_and_consequences(tmp_path):
    def project(**extra):
        return make_project(
            tmp_path,
            {
                "world/events/a.md": fm(
                    name="Big",
                    type="milestone",
                    date=d(1),
                    significance="major",
                    root_causes=["start"],
                    **extra,
                ),
            },
        )

    base = dict(immediate_consequences=["x"], long_term_consequences=["y"])
    assert not find(run(project(open_ended="still unfolding", **base)), "orphan-event", "warning", "leads to nothing")
    assert find(run(project(open_ended="", **base)), "orphan-event", "warning", "leads to nothing")
    assert find(run(project(open_ended="still unfolding")), "orphan-event", "warning", "leads to nothing")


def test_orphan_significant_without_cause(tmp_path):
    root = make_project(
        tmp_path,
        {
            "world/events/a.md": fm(
                name="Big",
                type="milestone",
                date=d(1),
                significance="world-changing",
                leads_to=["b"],
                immediate_consequences=["x"],
                long_term_consequences=["y"],
            ),
            "world/events/b.md": event("B", d(2), caused_by=["a"]),
        },
    )
    assert find(run(root), "orphan-event", "warning", "has no cause")


def test_dead_character_appears_after_death(tmp_path):
    root = make_project(
        tmp_path,
        {
            "world/characters/vic.md": fm(name="Vic", status="dead", last_appearance="ch1", died=d(50)),
            "world/events/after.md": event("After", d(60), participants=[{"entity": "vic", "role": "attendee"}]),
            "world/events/memorial.md": event("Memorial", d(70), participants=[{"entity": "vic", "role": "deceased"}]),
            "world/events/before.md": event("Before", d(40), participants=[{"entity": "vic", "role": "guest"}]),
        },
    )
    hits = find(run(root), "lifespan", "error", "after dying")
    assert len(hits) == 1 and "After" in hits[0]["message"]


def test_character_acts_before_birth_via_birth_event(tmp_path):
    root = make_project(
        tmp_path,
        {
            "world/characters/kid.md": fm(name="Kid", status="alive"),
            "world/events/kid-born.md": event("Kid Born", d(100), type="birth", person="kid"),
            "world/events/early.md": event("Early", d(90), participants=[{"entity": "kid", "role": "guest"}]),
        },
    )
    issues = run(root)
    assert find(issues, "lifespan", "error", "before being born")
    assert not find(issues, "lifespan", contains="Kid Born")


def test_entity_did_not_exist_yet(tmp_path):
    root = make_project(
        tmp_path,
        {
            "world/factions/guild.md": fm(name="Guild", leader="vacant", founding_date=d(100)),
            "world/locations/town.md": fm(name="Town", type="town", founded=d(100)),
            "world/events/early.md": event("Early", d(50), organizations=[{"entity": "guild"}], locations=["town"]),
        },
    )
    hits = find(run(root), "existence", "warning", "did not exist yet")
    assert len(hits) == 2


# ── dates ────────────────────────────────────────────────────────────────────


def test_worlddate_precision_and_eras():
    cal = {"eras": [{"prefix": "A", "sort_order": 1}, {"prefix": "B", "sort_order": 2}]}
    year_only = wv.WorldDate({"year": 5, "era_prefix": "A"}, cal)
    dated = wv.WorldDate({"year": 5, "month": 3, "era_prefix": "A"}, cal)
    assert year_only.cmp(dated) == 0  # not comparable below year precision
    assert wv.WorldDate("A 4", cal).cmp(wv.WorldDate("B 1", cal)) == -1
    assert wv.WorldDate({"year": 1, "era_prefix": "ZZ"}, cal).cmp(wv.WorldDate("A 4", cal)) is None


@pytest.mark.parametrize("bad", [None, "", {}, {"year": 0}, True])
def test_worlddate_invalid(bad):
    assert not wv.WorldDate(bad).valid


# ── magic yes/no gate ───────────────────────────────────────────────────────

NO_MAGIC = "title: T\nworld_flags:\n  magic:\n    present: false\n    prevalence: none\n"
YES_MAGIC = "title: T\nworld_flags:\n  magic:\n    present: true\n    hardness: hard\n"


def msys(**kw):
    return fm(**{"name": "Weave", "type": "arcane", **kw})


def test_magic_absent_system_is_error(tmp_path):
    root = make_project(tmp_path, {"world/magic-systems/weave.md": msys()}, NO_MAGIC)
    assert find(run(root), "magic-flag", "error", "no magic")


def test_magic_prevalence_none_counts_as_absent(tmp_path):
    p = "title: T\nworld_flags:\n  magic:\n    prevalence: none\n"
    root = make_project(tmp_path, {"world/magic-systems/weave.md": msys()}, p)
    assert find(run(root), "magic-flag", "error")


def test_magic_absent_technology_system_allowed(tmp_path):
    root = make_project(tmp_path, {"world/magic-systems/drive.md": msys(type="technology")}, NO_MAGIC)
    assert not find(run(root), "magic-flag")


def test_magic_absent_reference_is_error(tmp_path):
    root = make_project(
        tmp_path,
        {
            "world/characters/a.md": fm(name="A", type="npc", magic_system="weave"),
            "world/characters/b.md": fm(name="B", type="npc", abilities=["weave"]),
        },
        NO_MAGIC,
    )
    # b refers to a slug that has no magic-system file, so only a is flagged
    errs = find(run(root), "magic-flag", "error")
    assert len(errs) == 1 and errs[0]["file"].endswith("a.md")


def test_magic_absent_slug_reference_is_error(tmp_path):
    root = make_project(
        tmp_path,
        {
            "world/magic-systems/weave.md": msys(),
            "world/characters/b.md": fm(name="B", type="npc", abilities=["weave"]),
        },
        NO_MAGIC,
    )
    assert any(i["file"].endswith("b.md") for i in find(run(root), "magic-flag", "error"))


def test_magic_absent_keyword_warning_and_exceptions(tmp_path):
    ent = fm(name="Tower", type="city", descriptions={"machine": "A wizard casts a spell here."})
    root = make_project(tmp_path, {"world/locations/tower.md": ent}, NO_MAGIC)
    issues = run(root)
    assert find(issues, "magic-flag", "warning", "'wizard'")
    assert not find(issues, "magic-flag", "error")
    p = NO_MAGIC + "    exceptions: [wizard, spell]\n"
    assert not find(run(make_project(tmp_path / "x", {"world/locations/tower.md": ent}, p)), "magic-flag")
    p = NO_MAGIC.replace("prevalence: none", "prevalence: {value: none, notes: stage wizard and spell are theatre}")
    assert not find(run(make_project(tmp_path / "y", {"world/locations/tower.md": ent}, p)), "magic-flag")


def test_magic_unset_is_silent(tmp_path):
    ent = fm(name="Tower", type="city", descriptions={"machine": "A wizard casts a spell here."})
    root = make_project(tmp_path, {"world/magic-systems/weave.md": msys(), "world/locations/tower.md": ent})
    assert not find(run(root), "magic-flag") and not find(run(root), "magic-system")


def test_magic_present_incomplete_system_warns(tmp_path):
    root = make_project(tmp_path, {"world/magic-systems/weave.md": msys()}, YES_MAGIC)
    msgs = " ".join(i["message"] for i in find(run(root), "magic-system", "warning"))
    assert "no source" in msgs and "who can use" in msgs and "no cost" in msgs and "no limits" in msgs
    assert not find(run(root), "magic-flag")


def test_magic_present_complete_system_clean_and_soft_skips_cost(tmp_path):
    full = msys(source="ley lines", cost="fatigue", limitations=["no healing"], heritability="bloodline")
    root = make_project(tmp_path, {"world/magic-systems/weave.md": full}, YES_MAGIC)
    assert not find(run(root), "magic-system")
    soft = YES_MAGIC.replace("hard", "soft")
    bare = msys(source="gods", practitioners=[])
    msgs = [i["message"] for i in find(run(make_project(tmp_path / "s", {"world/magic-systems/w.md": bare}, soft)),
                                       "magic-system", "warning")]
    assert not any("no cost" in m or "no limits" in m for m in msgs)
    assert any("who can use" in m for m in msgs)


# ── significance vocabulary ──────────────────────────────────────────────────


@pytest.mark.parametrize("level,warns", [("important", True), ("crucial", True), ("major", True), ("notable", False)])
def test_significance_vocabulary(tmp_path, level, warns):
    root = make_project(
        tmp_path,
        {
            "world/events/a.md": fm(
                name="Big",
                type="milestone",
                date=d(1),
                significance=level,
                leads_to=["b"],
                immediate_consequences=["x"],
                long_term_consequences=["y"],
            ),
            "world/events/b.md": event("B", d(2), caused_by=["a"]),
        },
    )
    assert bool(find(run(root), "orphan-event", "warning", "has no cause")) is warns


# ── calendar eras ────────────────────────────────────────────────────────────


def test_unknown_era_warns_only_with_calendar(tmp_path):
    files = {"world/events/a.md": event("A", d(5, era="ZZ"))}
    root = make_project(tmp_path / "with", files)
    assert find(run(root), "unknown-era", "warning", "'ZZ'")
    assert not find(run(make_project(tmp_path / "ok", {"world/events/a.md": event("A", d(5))})), "unknown-era")
    nocal = make_project(tmp_path / "none", files)
    (nocal / "world" / "history" / "calendar.yaml").unlink()
    assert not find(run(nocal), "unknown-era")


# ── physical geography ───────────────────────────────────────────────────────


def loc(name, **kw):
    return fm(name=name, type="region", **kw)


def test_geography_dangling_species_and_flows_to(tmp_path):
    root = make_project(
        tmp_path,
        {
            "world/species/ridge-wolf.md": fm(name="Ridge Wolf", type="animal"),
            "world/locations/vale.md": loc(
                "Vale",
                flora=[{"name": "winter rye"}, "moss", {"species": "ghost-pine"}],
                fauna=[{"species": "ridge-wolf"}, {"species": "ghost-owl"}],
                hydrology={"flows_to": "nowhere-sea"},
                climate_profile={"zone": "alpine", "drivers": ["altitude", {"entity": "missing-range"}]},
            ),
        },
    )
    issues = run(root)
    assert find(issues, "dangling-ref", "warning", "flora species 'ghost-pine'")
    assert find(issues, "dangling-ref", "warning", "fauna species 'ghost-owl'")
    assert not find(issues, "dangling-ref", contains="ridge-wolf")
    assert not find(issues, "dangling-ref", contains="winter rye")
    assert find(issues, "dangling-ref", "warning", "flows_to 'nowhere-sea'")
    assert find(issues, "dangling-ref", "warning", "missing-range")


def test_river_cycle_is_error_and_uphill_warns(tmp_path):
    root = make_project(
        tmp_path,
        {
            "world/locations/a.md": loc("A", hydrology={"flows_to": "b"}, elevation_m=100),
            "world/locations/b.md": loc("B", hydrology={"flows_to": "a"}, elevation_m=200),
            "world/locations/c.md": loc("C", hydrology={"flows_to": "d"}, elevation_m=50),
            "world/locations/d.md": loc("D", elevation_m=80),
            "world/locations/e.md": loc("E", hydrology={"flows_to": "d"}),
        },
    )
    issues = run(root)
    assert len(find(issues, "river-cycle", "error")) == 1
    up = find(issues, "river-elevation", "warning")
    assert any("'C'" in i["message"] for i in up)
    assert not any("'E'" in i["message"] for i in up)


# ── magical transport ────────────────────────────────────────────────────────


def route_loc(method):
    return loc("Gate", routes=[{"to": "gate", "method": method}])


@pytest.mark.parametrize("method", ["teleportation", "ley-line", "portal", "magic carpet"])
def test_magical_transport_error_when_magic_absent(tmp_path, method):
    root = make_project(tmp_path, {"world/locations/gate.md": route_loc(method)}, NO_MAGIC)
    assert find(run(root), "world-flag", "error", "magical transport")


def test_magical_transport_silent_when_magic_present_or_unset(tmp_path):
    files = {"world/locations/gate.md": route_loc("portal")}
    assert not find(run(make_project(tmp_path / "y", files, YES_MAGIC)), "world-flag")
    assert not find(run(make_project(tmp_path / "u", files)), "world-flag", contains="magical")


def test_tech_transport_unchanged(tmp_path):
    root = make_project(tmp_path, {"world/locations/gate.md": route_loc("train")})
    assert find(run(root), "world-flag", "error", "steam_power")


# ── magic keyword scan covers all text fields ────────────────────────────────


@pytest.mark.parametrize(
    "etype,field,value",
    [
        ("characters", "abilities", ["casts a spell"]),
        ("locations", "magical_impact", "Mana pools here"),
        ("locations", "flora", [{"name": "moss", "notes": "faintly magical"}]),
        ("items", "properties", {"effect": "an enchanted blade"}),
        ("species", "traits", ["innate sorcery"]),
        ("events", "immediate_consequences", ["the wizard fell"]),
    ],
)
def test_magic_scan_covers_all_fields(tmp_path, etype, field, value):
    ent = fm(name="Thing", type="x", date=d(1), **{field: value})
    root = make_project(tmp_path, {f"world/{etype}/thing.md": ent}, NO_MAGIC)
    hits = find(run(root), "magic-flag", "warning")
    assert any(i["field"] == field for i in hits), hits
    assert not find(run(root), "magic-flag", "error")


def test_magic_scan_ignores_body_and_names(tmp_path):
    ent = "---\nname: Magic Hill\ntype: hill\ntags: [magic]\n---\n\nNo magic exists; no wizard ever lived here.\n"
    root = make_project(tmp_path, {"world/locations/hill.md": ent}, NO_MAGIC)
    assert not find(run(root), "magic-flag")


# ── traditions (memory chain) and event traces ──────────────────────────────


def trad(name="Lantern Night", **kw):
    meta = {"name": name, "kind": "festival", "origin_events": ["flood"], **kw}
    return fm(**meta)


def flood(**kw):
    return event("Flood", d(10), traces=["lantern-night"], **kw)


def tproject(tmp_path, files=None, project=PROJECT):
    base = {"world/events/flood.md": flood(), "world/traditions/lantern-night.md": trad()}
    base.update(files or {})
    return make_project(tmp_path, base, project)


def test_tradition_clean_world_has_no_issues(tmp_path):
    assert run(tproject(tmp_path)) == []


def test_tradition_directory_is_loaded(tmp_path):
    _, entities = wv.validate(tproject(tmp_path))
    assert "lantern-night" in entities["tradition"]
    assert wv.ENTITY_DIRS["tradition"] == "traditions"


def test_origin_event_missing_is_error(tmp_path):
    root = tproject(tmp_path, {"world/traditions/lantern-night.md": trad(origin_events=["ghost"])})
    assert find(run(root), "dangling-ref", "error", "origin event 'ghost'")


def test_origin_event_wrong_type_is_error(tmp_path):
    files = {"world/locations/hill.md": fm(name="Hill", type="hill")}
    files["world/traditions/lantern-night.md"] = trad(origin_events=["hill"])
    assert find(run(tproject(tmp_path, files)), "wrong-ref-type", "error", "not an event")


def test_tradition_soft_refs_warn(tmp_path):
    t = trad(held_by=["nobody"], regions=["nowhere"], places=["noplace"], language="nolang", related=["notrad"])
    issues = run(tproject(tmp_path, {"world/traditions/lantern-night.md": t}))
    for fld in ("held_by", "regions", "places", "language", "related"):
        assert any(i["field"] == fld and i["severity"] == "warning" for i in issues), fld
    assert not [i for i in issues if i["severity"] == "error"]


def test_trace_reciprocity_both_directions(tmp_path):
    # event traces the tradition, tradition does not name the event
    files = {"world/traditions/lantern-night.md": trad(origin_events=[], origin_unknown="lost with the archive")}
    assert find(run(tproject(tmp_path / "a", files)), "trace-reciprocity", "warning", "doesn't reference back")
    # tradition names the event, event does not trace it
    files = {"world/events/flood.md": event("Flood", d(10))}
    assert find(run(tproject(tmp_path / "b", files)), "trace-reciprocity", "warning", "doesn't list it in traces")


def test_event_trace_missing_target_warns(tmp_path):
    files = {"world/events/flood.md": event("Flood", d(10), traces=["gone"])}
    issues = run(tproject(tmp_path, files))
    assert find(issues, "dangling-ref", "warning", "trace 'gone'")


def test_contradicts_must_be_reciprocal(tmp_path):
    files = {
        "world/traditions/lantern-night.md": trad(contradicts=["dark-night"]),
        "world/traditions/dark-night.md": trad("Dark Night", origin_events=["flood"]),
        "world/events/flood.md": event("Flood", d(10), traces=["lantern-night", "dark-night"]),
    }
    assert find(run(tproject(tmp_path / "a", files)), "symmetry", "warning", "contradicts")
    files["world/traditions/dark-night.md"] = trad("Dark Night", contradicts=["lantern-night"])
    assert not find(run(tproject(tmp_path / "b", files)), "symmetry")


def test_orphan_tradition(tmp_path):
    t = trad(origin_events=[])
    root = tproject(tmp_path / "a", {"world/traditions/lantern-night.md": t, "world/events/flood.md": event("F", d(1))})
    assert find(run(root), "orphan-tradition", "warning")
    t = trad(origin_events=[], origin_unknown="the founders burned their records")
    root = tproject(tmp_path / "b", {"world/traditions/lantern-night.md": t, "world/events/flood.md": event("F", d(1))})
    assert not find(run(root), "orphan-tradition")


def test_tradition_before_origin_is_error(tmp_path):
    early = {"world/traditions/lantern-night.md": trad(first_attested=d(5))}
    late = {"world/traditions/lantern-night.md": trad(first_attested=d(20))}
    assert find(run(tproject(tmp_path / "a", early)), "tradition-before-origin", "error")
    assert not find(run(tproject(tmp_path / "b", late)), "tradition-before-origin")


def test_tradition_before_earliest_of_several_origins(tmp_path):
    files = {
        "world/events/flood.md": flood(),
        "world/events/war.md": event("War", d(50), traces=["lantern-night"]),
        "world/traditions/lantern-night.md": trad(origin_events=["flood", "war"], first_attested=d(30)),
    }
    assert not find(run(tproject(tmp_path, files)), "tradition-before-origin")


def test_tradition_before_origin_skipped_when_undatable(tmp_path):
    # different eras with no way to order them (calendar eras lack end_year): cannot compare
    files = {"world/traditions/lantern-night.md": trad(first_attested={"year": 1, "era_prefix": "ZZ"})}
    assert not find(run(tproject(tmp_path / "a", files)), "tradition-before-origin")
    files = {"world/events/flood.md": flood(), "world/traditions/lantern-night.md": trad()}
    assert not find(run(tproject(tmp_path / "b", files)), "tradition-before-origin")  # no first_attested


PRESENT = PROJECT + "present_date: {year: 400, era_prefix: NA}\n"


def test_implausible_fidelity_oral_accurate_over_300_years(tmp_path):
    t = trad(transmission="oral", fidelity="accurate")
    root = tproject(tmp_path, {"world/traditions/lantern-night.md": t}, PRESENT)
    assert find(run(root), "implausible-fidelity", "warning", "390 years")


def test_implausible_fidelity_not_raised_when_it_should_not(tmp_path):
    oral = trad(transmission="oral", fidelity="accurate")
    # no present date: skipped
    assert not find(run(tproject(tmp_path / "a", {"world/traditions/lantern-night.md": oral})), "implausible-fidelity")
    # written, or not 'accurate': fine
    for i, kw in enumerate(({"transmission": "written", "fidelity": "accurate"},
                            {"transmission": "oral", "fidelity": "embellished"})):
        root = tproject(tmp_path / f"b{i}", {"world/traditions/lantern-night.md": trad(**kw)}, PRESENT)
        assert not find(run(root), "implausible-fidelity")
    # under the threshold
    near = "title: T\npresent_date: {year: 200, era_prefix: NA}\n"
    root = tproject(tmp_path / "c", {"world/traditions/lantern-night.md": oral}, near)
    assert not find(run(root), "implausible-fidelity")


def test_trace_waives_leads_to_nothing(tmp_path):
    def world(**extra):
        ev = fm(name="Big", type="milestone", date=d(1), significance="crucial", root_causes=["start"],
                immediate_consequences=["x"], long_term_consequences=["y"], **extra)
        return make_project(tmp_path / f"w{len(extra)}", {"world/events/big.md": ev})

    assert find(run(world()), "orphan-event", "warning", "leads to nothing")
    assert not find(run(world(traces=["somewhere"])), "orphan-event", "warning", "leads to nothing")


def test_tradition_exempt_from_magic_keyword_scan(tmp_path):
    t = trad(distortions=["the flood is told as a wizard's spell"], descriptions={"human": "Magic lanterns."})
    files = {"world/traditions/lantern-night.md": t, "world/locations/hill.md": fm(name="Hill", type="hill",
             description="a magical hill")}
    issues = run(tproject(tmp_path, files, NO_MAGIC))
    flagged = [i["file"] for i in find(issues, "magic-flag")]
    assert flagged == ["world/locations/hill.md"]  # the location is still scanned, the tradition is not


def test_tradition_referencing_magic_system_still_error_when_absent(tmp_path):
    files = {
        "world/magic-systems/weave.md": msys(type="technology"),
        "world/traditions/lantern-night.md": trad(related=["weave"]),
    }
    assert not find(run(tproject(tmp_path / "a", files, NO_MAGIC)), "magic-flag", "error")  # tech system
    files["world/magic-systems/weave.md"] = msys()
    errs = find(run(tproject(tmp_path / "b", files, NO_MAGIC)), "magic-flag", "error")
    assert any(i["file"].endswith("lantern-night.md") for i in errs)


# ── location coordinates ─────────────────────────────────────────────────────


def test_valid_location_coordinates(tmp_path):
    root = make_project(
        tmp_path,
        {
            "world/locations/list-loc.md": fm(name="List Loc", type="city", coordinates=[0, 1000]),
            "world/locations/dict-loc.md": fm(name="Dict Loc", type="city", coordinates={"x": 250.5, "y": 750.25}),
            "world/locations/empty-loc.md": fm(name="Empty Loc", type="city", coordinates={}),
            "world/locations/plain-loc.md": fm(name="Plain Loc", type="city"),
        },
    )
    assert not find(run(root), "coordinates")


@pytest.mark.parametrize(
    "bad_coords",
    [
        [-1, 500],
        [500, 1001],
        {"x": -0.1, "y": 500},
        {"x": 500, "y": 1000.1},
        [100],
        [100, 200, 300],
        [],
        {"x": 100},
        {"x": 100, "y": 200, "z": 300},
        ["100", "200"],
        [True, 200],
        [float("nan"), 100],
        [float("inf"), 100],
        "100, 200",
    ],
)
def test_invalid_location_coordinates_emit_error(tmp_path, bad_coords):
    root = make_project(
        tmp_path,
        {"world/locations/bad.md": fm(name="Bad", type="city", coordinates=bad_coords)},
    )
    errs = find(run(root), "coordinates", "error")
    assert len(errs) == 1
    assert errs[0]["field"] == "coordinates"
