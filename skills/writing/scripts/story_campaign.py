#!/usr/bin/env python3
"""Deterministic dated brief generator for in-universe short stories and D&D 5e campaigns.

Zero runtime dependencies: Python 3.9+ stdlib plus the shared WorldGraph and vendored
PyYAML from `skills/world-validate/scripts/`.

Usage:
    story_campaign.py story <project> (--event SLUG | --tradition SLUG | --era PREFIX [--start-year Y] | --present)
    story_campaign.py campaign <project> (--era PREFIX [--year Y] | --event SLUG | --tradition SLUG | --present)
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

_VALIDATE_DIR = Path(__file__).resolve().parents[2] / "world-validate" / "scripts"
if str(_VALIDATE_DIR) not in sys.path:
    sys.path.insert(0, str(_VALIDATE_DIR))

_spec = importlib.util.spec_from_file_location("wb_writing_graph", _VALIDATE_DIR / "graph.py")
assert _spec is not None and _spec.loader is not None
_g = importlib.util.module_from_spec(_spec)
sys.modules["wb_writing_graph"] = _g
_spec.loader.exec_module(_g)
_v = _g._v
yaml = _v.yaml


# ── helpers ─────────────────────────────────────────────────────────────────


def _meta(g: Any, slug: str) -> dict[str, Any]:
    for ents in g._entities.values():
        if slug in ents:
            m = ents[slug].get("meta")
            return m if isinstance(m, dict) else {}
    return {}


def _present_t(g: Any) -> tuple[float | None, str]:
    for src in (g.config, g.calendar):
        if not isinstance(src, dict):
            continue
        for key in ("present_date", "current_date"):
            raw = src.get(key)
            wd = _v.WorldDate(raw, g.calendar)
            if wd.valid:
                t = g._date_t(wd)
                if t is not None:
                    return t, wd.display
    return None, "present day"


def _era_info(g: Any, prefix: str) -> dict[str, Any] | None:
    p = prefix.strip().lower()
    for e in g._eras:
        if str(e.get("prefix", "")).strip().lower() == p or str(e.get("name", "")).strip().lower() == p:
            return e
    return None


def _resolve_anchor(
    g: Any,
    *,
    event: str | None = None,
    tradition: str | None = None,
    era: str | None = None,
    year: int | None = None,
    end_year: int | None = None,
    present: bool = False,
) -> dict[str, Any]:
    """Resolve the story/campaign anchor into a deterministic dict with numeric `t` and label."""
    if event:
        slug = g.resolve_slug(event)
        if not slug or g.nodes[slug]["type"] != "event":
            raise ValueError(f"event not found: {event}")
        node = g.nodes[slug]
        return {
            "kind": "event",
            "slug": slug,
            "title": node["name"],
            "t": node["t"],
            "end_t": None,
            "date_label": node["date"] or "undated",
            "era": node["era"] or "",
        }

    if tradition:
        slug = g.resolve_slug(tradition)
        if not slug or g.nodes[slug]["type"] != "tradition":
            raise ValueError(f"tradition not found: {tradition}")
        node = g.nodes[slug]
        meta = _meta(g, slug)
        pt, plabel = _present_t(g)
        t = pt if pt is not None else node["t"]
        label = plabel if pt is not None else (node["date"] or "undated")
        origins = [g.resolve_slug(o) for o in (meta.get("origin_events") or []) if isinstance(o, str)]
        origins = [o for o in origins if o and o in g.nodes]
        return {
            "kind": "tradition",
            "slug": slug,
            "title": node["name"],
            "t": t,
            "end_t": None,
            "date_label": label,
            "era": node["era"] or "",
            "origin_events": origins,
        }

    if era:
        info = _era_info(g, era)
        if not info:
            valid = ", ".join(str(e.get("prefix")) for e in g._eras) or "(none)"
            raise ValueError(f"era '{era}' not found in calendar.yaml (available: {valid})")
        prefix = str(info.get("prefix"))
        era_name = str(info.get("name") or prefix)
        y = year if year is not None else int(info.get("start_year") or 1)
        wd = _v.WorldDate({"year": y, "era_prefix": prefix}, g.calendar)
        t = g._date_t(wd)
        end_t = None
        label = f"{y} {prefix} ({era_name})"
        if end_year is not None:
            wd_end = _v.WorldDate({"year": end_year, "era_prefix": prefix}, g.calendar)
            end_t = g._date_t(wd_end)
            label = f"{y}-{end_year} {prefix} ({era_name})"
        slug = _v.slugify(f"{prefix}-{y}" + (f"-to-{end_year}" if end_year is not None else ""))
        return {
            "kind": "era",
            "slug": slug,
            "title": f"{era_name} ({label})",
            "t": t,
            "end_t": end_t,
            "date_label": label,
            "era": era_name,
        }

    if present:
        pt, plabel = _present_t(g)
        if pt is None:
            dated = [n["t"] for n in g.nodes.values() if n["t"] is not None]
            pt = max(dated) if dated else 0.0
            plabel = "present day"
        return {
            "kind": "present",
            "slug": "present-day",
            "title": f"Present Day ({plabel})",
            "t": pt,
            "end_t": None,
            "date_label": plabel,
            "era": "",
        }

    raise ValueError("specify one of --event, --tradition, --era, or --present")


def _is_alive_at(g: Any, slug: str, anchor_t: float | None) -> bool:
    if anchor_t is None:
        return True
    meta = _meta(g, slug)
    birth = _v.WorldDate(meta.get("birth_date"), g.calendar)
    if birth.valid:
        bt = g._date_t(birth)
        if bt is not None and bt > anchor_t:
            return False
    death = _v.WorldDate(meta.get("death_date"), g.calendar)
    if death.valid:
        dt_val = g._date_t(death)
        if dt_val is not None and dt_val < anchor_t:
            return False
    return True


def _load_economy(project: Path) -> dict[str, Any]:
    eco_path = project / "world" / "economy.yaml"
    if not eco_path.is_file():
        return {}
    raw = yaml.safe_load(eco_path.read_text(encoding="utf-8"))
    return raw if isinstance(raw, dict) else {}


def _magic_summary(config: dict[str, Any]) -> tuple[bool, str]:
    wf = config.get("world_flags") if isinstance(config.get("world_flags"), dict) else {}
    magic = wf.get("magic") if isinstance(wf.get("magic"), dict) else {}
    present = bool(magic.get("present", False))
    if not present:
        return (
            False,
            "MAGIC OFF (`world_flags.magic.present: false`) — strictly mundane; "
            "no real spells or supernatural effects.",
        )
    parts = [
        f"MAGIC ON (hardness: {magic.get('hardness', 'unspecified')}",
        f"prevalence: {magic.get('prevalence', 'unspecified')})",
    ]
    if magic.get("source"):
        parts.append(f"source: {magic['source']}")
    if magic.get("cost"):
        parts.append(f"cost: {magic['cost']}")
    return True, " — ".join(parts)


def _dnd5e_tier(level_range: str) -> dict[str, str]:
    try:
        low = int(str(level_range).split("-")[0].strip())
    except ValueError:
        low = 1
    if low <= 4:
        return {
            "tier": "Tier 1 — Local Heroes (Levels 1–4)",
            "prof_bonus": "+2",
            "dc_band": "Easy 10 · Moderate 13 · Hard 15 · Very Hard 18",
            "cr_band": "CR 1/4 – CR 4",
        }
    if low <= 10:
        return {
            "tier": "Tier 2 — Heroes of the Realm (Levels 5–10)",
            "prof_bonus": "+3 to +4",
            "dc_band": "Easy 12 · Moderate 15 · Hard 18 · Very Hard 20",
            "cr_band": "CR 3 – CR 10",
        }
    if low <= 16:
        return {
            "tier": "Tier 3 — Masters of the Realm (Levels 11–16)",
            "prof_bonus": "+4 to +5",
            "dc_band": "Easy 13 · Moderate 16 · Hard 19 · Very Hard 22",
            "cr_band": "CR 8 – CR 16",
        }
    return {
        "tier": "Tier 4 — Masters of the World (Levels 17–20)",
        "prof_bonus": "+6",
        "dc_band": "Easy 15 · Moderate 18 · Hard 21 · Very Hard 25",
        "cr_band": "CR 15 – CR 24+",
    }


def _collect_dated_context(
    project: Path,
    g: Any,
    anchor: dict[str, Any],
    *,
    location_slug: str | None = None,
) -> dict[str, Any]:
    """Build spoiler-free dated world context at `anchor['t']`."""
    t_cut = anchor["end_t"] if anchor.get("end_t") is not None else anchor["t"]

    past_events = []
    future_count = 0
    for slug, n in sorted(g.nodes.items()):
        if n["type"] != "event":
            continue
        et = n["t"]
        if t_cut is not None and et is not None and et > t_cut:
            future_count += 1
            continue
        meta = _meta(g, slug)
        past_events.append({
            "id": slug,
            "name": n["name"],
            "t": et,
            "date": n["date"] or "undated",
            "era": n["era"] or "",
            "significance": meta.get("significance") or "",
            "summary": n["summary"] or "",
            "caused_by": meta.get("caused_by") or [],
            "open_ended": meta.get("open_ended") or "",
            "traces": meta.get("traces") or [],
        })
    past_events.sort(key=lambda e: (e["t"] is None, e["t"] if e["t"] is not None else 0, e["id"]))

    # Traditions attested by anchor date
    traditions = []
    for slug, n in sorted(g.nodes.items()):
        if n["type"] != "tradition":
            continue
        meta = _meta(g, slug)
        fa = _v.WorldDate(meta.get("first_attested"), g.calendar)
        if fa.valid and t_cut is not None:
            fat = g._date_t(fa)
            if fat is not None and fat > t_cut:
                continue
        traditions.append({
            "id": slug,
            "name": n["name"],
            "kind": meta.get("kind") or "tradition",
            "fidelity": meta.get("fidelity") or "unknown",
            "origin_events": meta.get("origin_events") or [],
            "distortions": meta.get("distortions") or [],
            "drives": meta.get("drives") or [],
            "summary": n["summary"] or "",
        })

    # Characters alive at anchor date
    characters = []
    for slug, n in sorted(g.nodes.items()):
        if n["type"] != "character":
            continue
        if not _is_alive_at(g, slug, t_cut):
            continue
        meta = _meta(g, slug)
        voice = meta.get("voice") if isinstance(meta.get("voice"), dict) else {}
        characters.append({
            "id": slug,
            "name": n["name"],
            "role": meta.get("role") or "",
            "faction": meta.get("faction") or "",
            "location": meta.get("location") or "",
            "summary": n["summary"] or "",
            "voice": voice.get("description") or "",
        })

    # Locations & routes
    locations = []
    for slug, n in sorted(g.nodes.items()):
        if n["type"] != "location":
            continue
        meta = _meta(g, slug)
        cp = meta.get("climate_profile") if isinstance(meta.get("climate_profile"), dict) else {}
        routes = []
        for r in meta.get("routes") or []:
            if isinstance(r, dict) and r.get("to"):
                methods = [
                    f"{m.get('mode', '?')} ({m.get('travel_time', '?')})"
                    for m in (r.get("methods") or [])
                    if isinstance(m, dict)
                ]
                routes.append(f"→ `{r['to']}` via {', '.join(methods) or 'route'}")
        locations.append({
            "id": slug,
            "name": n["name"],
            "type": meta.get("type") or "",
            "terrain": meta.get("terrain") or "",
            "climate": cp.get("zone") or meta.get("climate") or "",
            "hazards": [h.get("name") for h in (cp.get("hazards") or []) if isinstance(h, dict) and h.get("name")],
            "routes": routes,
            "summary": n["summary"] or "",
        })

    # Factions & goals
    factions = []
    for slug, n in sorted(g.nodes.items()):
        if n["type"] != "faction":
            continue
        meta = _meta(g, slug)
        factions.append({
            "id": slug,
            "name": n["name"],
            "leader": meta.get("leader") or "",
            "headquarters": meta.get("headquarters") or "",
            "goals": meta.get("goals") or [],
            "enemies": meta.get("enemies") or [],
            "summary": n["summary"] or "",
        })

    # Causal ancestry for event/tradition anchors
    ancestry: list[dict[str, Any]] = []
    if anchor["kind"] in {"event", "tradition"}:
        tree = g.ancestors(anchor["slug"])
        seen_anc: set[str] = {anchor["slug"]}

        def _walk(node: dict[str, Any]) -> None:
            for ch in node.get("children") or []:
                cid = ch.get("slug")
                if not cid or cid in seen_anc or cid not in g.nodes:
                    continue
                seen_anc.add(cid)
                cn = g.nodes[cid]
                ancestry.append({
                    "id": cid,
                    "name": cn["name"],
                    "date": cn["date"] or "undated",
                    "relation": ch.get("link") or "causes",
                })
                _walk(ch)

        _walk(tree)

    focus_loc = None
    if location_slug:
        r_loc = g.resolve_slug(location_slug)
        if not r_loc or g.nodes[r_loc]["type"] != "location":
            raise ValueError(f"location not found: {location_slug}")
        focus_loc = next((loc for loc in locations if loc["id"] == r_loc), None)

    return {
        "world_title": str(g.config.get("title") or project.name),
        "anchor": anchor,
        "future_events_excluded": future_count,
        "magic": _magic_summary(g.config),
        "style": g.config.get("style") or {},
        "economy": _load_economy(project),
        "ancestry": ancestry,
        "events": past_events,
        "traditions": traditions,
        "characters": characters,
        "locations": locations,
        "focus_location": focus_loc,
        "factions": factions,
    }


# ── Markdown brief renderers ────────────────────────────────────────────────


def render_story_brief(
    ctx: dict[str, Any],
    *,
    protagonist: str = "generate",
    words: int = 3500,
    tone: str | None = None,
    subgenre: str | None = None,
) -> str:
    a = ctx["anchor"]
    magic_on, magic_line = ctx["magic"]
    lines = [
        f"# Short Story Brief — {a['title']}",
        "",
        f"- **World:** {ctx['world_title']}",
        f"- **Anchor:** `{a['kind']}` · `{a['slug']}` ({a['date_label']})",
        f"- **Target Length:** ~{words:,} words",
        f"- **Protagonist:** `{protagonist}`",
    ]
    if tone:
        lines.append(f"- **Tone Override:** {tone}")
    if subgenre:
        lines.append(f"- **Subgenre:** {subgenre}")
    lines += [
        f"- **Magic Gate:** {magic_line}",
        (
            f"- **Spoiler Firewall:** {ctx['future_events_excluded']} future event(s) "
            f"after `{a['date_label']}` strictly excluded."
        ),
        "",
    ]

    if a["kind"] == "tradition":
        tr = next((t for t in ctx["traditions"] if t["id"] == a["slug"]), None)
        if tr:
            lines += [
                "## Centred Myth / Tradition (Truth vs. Memory Engine)",
                f"- **Tradition:** {tr['name']} (`{tr['kind']}`, fidelity: `{tr['fidelity']}`)",
                f"- **What people believe:** {tr['summary']}",
                f"- **Distortions:** {', '.join(tr['distortions']) or 'None recorded'}",
                f"- **Present-day behaviour driven:** {', '.join(tr['drives']) or 'None recorded'}",
                f"- **Real Origin Event(s):** {', '.join(f'`{o}`' for o in tr['origin_events']) or 'Unknown mystery'}",
                "",
            ]

    if ctx["ancestry"]:
        lines += ["## Causal Ancestry (`why`)", ""]
        for step in ctx["ancestry"][:12]:
            label = step.get("name") or step.get("id")
            date = step.get("date") or ""
            rel = step.get("relation") or step.get("via") or ""
            lines.append(f"- `{step.get('id')}` — **{label}** ({date}) {f'[{rel}]' if rel else ''}".rstrip())
        lines.append("")

    if ctx["focus_location"]:
        loc = ctx["focus_location"]
        lines += [
            f"## Focus Location — {loc['name']}",
            f"- **Terrain & Climate:** {loc['terrain'] or 'unspecified'} ({loc['climate'] or 'unspecified'})",
            f"- **Hazards:** {', '.join(loc['hazards']) or 'none listed'}",
            f"- **Summary:** {loc['summary']}",
            "",
        ]

    lines += ["## Recent & Relevant History (At or Before Anchor)", ""]
    for ev in ctx["events"][-10:]:
        oe = f" *(open-ended: {ev['open_ended']})*" if ev["open_ended"] else ""
        lines.append(f"- **{ev['date']} — {ev['name']}** (`{ev['id']}`): {ev['summary']}{oe}")
    if not ctx["events"]:
        lines.append("- *(No dated events before anchor.)*")
    lines.append("")

    lines += ["## Characters Alive at Anchor Date", ""]
    for c in ctx["characters"]:
        v = f" · Voice: {c['voice']}" if c["voice"] else ""
        lines.append(
            f"- **{c['name']}** (`{c['id']}`, {c['role'] or 'character'}, faction: `{c['faction'] or 'none'}`, "
            f"at `{c['location'] or '?'}`): {c['summary']}{v}"
        )
    if not ctx["characters"]:
        lines.append("- *(No characters confirmed alive at anchor date — generate period-appropriate POV.)*")
    lines.append("")

    lines += ["## Surviving Traditions & Rumours Known in Period", ""]
    for tr in ctx["traditions"]:
        lines.append(f"- **{tr['name']}** (`{tr['kind']}`, fidelity: `{tr['fidelity']}`): {tr['summary']}")
    lines.append("")

    lines += [
        "## Writing & Write-Back Checklist",
        "1. Honour `world_flags` and the magic gate above (no anachronisms; no future-event leaks).",
        "2. Use the gap between the **true causal chain** and **remembered traditions** as dramatic irony.",
        "3. After drafting, write any new canon characters, items, or events back into `world/` and run `validate.py`.",
    ]
    return "\n".join(lines) + "\n"


def render_campaign_brief(
    ctx: dict[str, Any],
    *,
    level: str = "1-4",
    length: str = "one-shot",
    sessions: int = 1,
    tone: str | None = None,
    themes: str | None = None,
) -> str:
    a = ctx["anchor"]
    magic_on, magic_line = ctx["magic"]
    tier = _dnd5e_tier(level)
    sess_count = 1 if length == "one-shot" else (3 if length == "short" else max(1, sessions))

    lines = [
        f"# D&D 5e Campaign Brief — {ctx['world_title']}: {a['title']}",
        "",
        "## Campaign Frame & 5e Calibration",
        "- **System:** D&D 5th Edition (5e)",
        f"- **Anchor:** `{a['kind']}` · `{a['slug']}` ({a['date_label']})",
        f"- **Length:** `{length}` ({sess_count} session{'s' if sess_count != 1 else ''})",
        f"- **Party Tier:** {tier['tier']} (Proficiency {tier['prof_bonus']}, {tier['cr_band']})",
        f"- **5e Check DCs:** {tier['dc_band']}",
        f"- **Magic Gate (5e Rules):** {magic_line}",
    ]
    if not magic_on:
        lines.append(
            "- **5e Low/No-Magic Guidance:** Restrict or reflavour spellcasting classes as mundane tactics, "
            "alchemical/herbal craft, or social exploits; no real magical monsters."
        )
    if tone:
        lines.append(f"- **Tone:** {tone}")
    if themes:
        lines.append(f"- **Themes:** {themes}")
    lines += [
        f"- **Spoiler Firewall:** {ctx['future_events_excluded']} future event(s) after `{a['date_label']}` excluded.",
        "",
    ]

    # Hubs & Routes
    hubs = [ctx["focus_location"]] if ctx["focus_location"] else ctx["locations"][:6]
    lines += ["## Starting Hub & Connected Routes", ""]
    for loc in hubs:
        if not loc:
            continue
        lines.append(f"### {loc['name']} (`{loc['id']}`, {loc['type'] or 'location'})")
        terrain = loc["terrain"] or "unspecified"
        climate = loc["climate"] or "unspecified"
        lines.append(f"- **Terrain & Climate:** {terrain} · Zone: `{climate}`")
        if loc["hazards"]:
            lines.append(f"- **Environmental Hazards (5e CON/DEX/Survival checks):** {', '.join(loc['hazards'])}")
        if loc["routes"]:
            lines.append(f"- **Routes:** {'; '.join(loc['routes'])}")
        lines.append(f"- **Overview:** {loc['summary']}")
        lines.append("")

    # Faction Clocks
    lines += ["## Faction Clocks (Advance Between Sessions If Ignored)", ""]
    for f in ctx["factions"]:
        goals = "; ".join(f["goals"][:3]) if f["goals"] else "consolidate influence"
        lines.append(
            f"- **{f['name']}** (`{f['id']}`, HQ: `{f['headquarters'] or '?'}`, Leader: `{f['leader'] or '?'}`): "
            f"Clock `[0/6]` → *{goals}*"
        )
    lines.append("")

    # NPC Roster
    lines += ["## Active NPCs (Alive at Anchor Date)", ""]
    for c in ctx["characters"]:
        v = f" · Voice: {c['voice']}" if c["voice"] else ""
        lines.append(
            f"- **{c['name']}** (`{c['id']}`, {c['role'] or 'NPC'}, `{c['faction'] or 'independent'}`, "
            f"at `{c['location'] or '?'}`): {c['summary']}{v}"
        )
    lines.append("")

    # d6/d8 Rumour Table from real Traditions & Open-Ended Events
    rumours: list[str] = []
    for tr in ctx["traditions"]:
        tag = "TRUE" if tr["fidelity"] == "accurate" else f"DISTORTED ({tr['fidelity']})"
        dist = f" — *GM truth: {', '.join(tr['distortions'])}*" if tr["distortions"] else ""
        rumours.append(f"[{tag}] **{tr['name']}** (`{tr['id']}`): {tr['summary']}{dist}")
    for ev in ctx["events"]:
        if ev["open_ended"]:
            rumours.append(f"[TRUE / LIVE HOOK] **{ev['name']}** (`{ev['id']}`): {ev['open_ended']}")

    die = "d8" if len(rumours) >= 7 else "d6"
    lines += [f"## Hub Rumour Table ({die})", ""]
    for idx, r in enumerate(rumours[:8], 1):
        lines.append(f"{idx}. {r}")
    if not rumours:
        lines.append("1. *(Add traditions or open-ended events to populate rumours.)*")
    lines.append("")

    # Economy & Shocks
    eco = ctx["economy"]
    if eco:
        lines += ["## Economy & Scarcity Hooks", ""]
        for cur in eco.get("currencies") or []:
            if isinstance(cur, dict):
                lines.append(f"- **Currency:** {cur.get('name')} (issued by `{cur.get('issuer', '?')}`)")
        for tr in eco.get("trade_routes") or []:
            if isinstance(tr, dict):
                frm = tr.get("from_location") or tr.get("from") or "?"
                to = tr.get("to_location") or tr.get("to") or "?"
                status = tr.get("status", "active")
                lines.append(f"- **Trade Route:** {tr.get('name')} (`{frm}` → `{to}`, status: `{status}`)")
        for sh in eco.get("shocks") or []:
            if isinstance(sh, dict):
                eff = sh.get("price_effects") or sh.get("trade_effects") or ""
                lines.append(f"- **Economic Shock (`{sh.get('event')}`):** {eff}")
        lines.append("")

    # Session Structure & Consequence Tracking
    lines += [
        "## Session Outline & Consequence Write-Back",
        (
            f"- Plan **{sess_count} session(s)** mixing social, exploration, "
            f"and combat/hazard encounters tuned to **{tier['cr_band']}**."
        ),
        (
            "- After each session, record player-driven outcomes as new events in `world/events/` "
            "with `caused_by`, update faction clocks and NPC statuses, and re-run `validate.py`."
        ),
    ]
    return "\n".join(lines) + "\n"


# ── CLI ─────────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Generate dated short story or D&D 5e campaign briefs from a world project."
    )
    sub = ap.add_subparsers(dest="mode", required=True)

    def add_common(p: argparse.ArgumentParser) -> None:
        p.add_argument("project", type=Path, help="World project folder containing project.yaml")
        p.add_argument("--event", help="Anchor to an event slug")
        p.add_argument("--tradition", help="Anchor to a myth/legend/tradition slug")
        p.add_argument("--era", help="Anchor to an era prefix (from world/history/calendar.yaml)")
        p.add_argument("--present", action="store_true", help="Anchor to the world's present date")
        p.add_argument("--location", help="Focus on a specific location slug")
        p.add_argument("--tone", help="Tone override")
        p.add_argument("--out", type=Path, help="Output file path")
        p.add_argument("--json", action="store_true", help="Print assembled dated context as JSON")

    p_story = sub.add_parser("story", help="Generate a dated short story brief")
    add_common(p_story)
    p_story.add_argument("--start-year", type=int, help="Start year (with --era)")
    p_story.add_argument("--end-year", type=int, help="Optional end year (with --era)")
    p_story.add_argument("--protagonist", default="generate", help="Character slug or 'generate'")
    p_story.add_argument("--subgenre", help="Subgenre (e.g. noir, heist, hard-sf, gothic)")
    p_story.add_argument("--words", type=int, default=3500, help="Target word count (default: 3500)")

    p_camp = sub.add_parser("campaign", help="Generate a D&D 5e-compatible campaign brief")
    add_common(p_camp)
    p_camp.add_argument("--year", type=int, help="Specific year (with --era)")
    p_camp.add_argument("--level", default="1-4", help="5e party level range (default: 1-4)")
    p_camp.add_argument("--length", choices=["one-shot", "short", "custom"], default="one-shot")
    p_camp.add_argument("--sessions", type=int, default=1, help="Session count (for --length custom)")
    p_camp.add_argument("--themes", help="Comma-separated themes")

    args = ap.parse_args(argv)
    project = args.project.resolve()
    if not (project / "project.yaml").is_file():
        print(f"error: no project.yaml in {project}", file=sys.stderr)
        return 1

    g = _g.WorldGraph.from_project(project)
    year_arg = args.start_year if args.mode == "story" else args.year
    end_year_arg = args.end_year if args.mode == "story" else None

    try:
        anchor = _resolve_anchor(
            g,
            event=args.event,
            tradition=args.tradition,
            era=args.era,
            year=year_arg,
            end_year=end_year_arg,
            present=args.present,
        )
        ctx = _collect_dated_context(project, g, anchor, location_slug=args.location)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(ctx, indent=2, default=str))
        return 0

    if args.mode == "story":
        md = render_story_brief(
            ctx,
            protagonist=args.protagonist,
            words=args.words,
            tone=args.tone,
            subgenre=args.subgenre,
        )
        default_out = project / "output" / "stories" / f"story-{anchor['slug']}.md"
    else:
        md = render_campaign_brief(
            ctx,
            level=args.level,
            length=args.length,
            sessions=args.sessions,
            tone=args.tone,
            themes=args.themes,
        )
        default_out = project / "output" / "campaigns" / f"campaign-{anchor['slug']}.md"

    out = args.out if args.out else default_out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")
    print(f"wrote {out} ({len(md.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
