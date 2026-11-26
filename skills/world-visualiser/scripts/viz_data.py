#!/usr/bin/env python3
"""Build the JSON payload for the world visualiser.

Usage:
    viz_data.py <project-dir> [--out FILE]

`build_viz_data(project_dir)` returns a JSON-serialisable dict (schema: references/data-format.md).
It reuses the loader, calendar and graph code of the world-validate skill (graph.py / validate.py)
and adds the timeline, map, climate, life and economy views. Absent data stays absent: nothing is
invented, and sparse areas are reported in the `warnings` list.

Python 3.9+, standard library only (PyYAML is vendored with validate.py).
"""

from __future__ import annotations

import argparse
import base64
import importlib.util
import json
import math
import os
import re
import sys
from pathlib import Path

_VALIDATE_DIR = Path(__file__).resolve().parents[2] / "world-validate" / "scripts"
if str(_VALIDATE_DIR) not in sys.path:
    sys.path.insert(0, str(_VALIDATE_DIR))

_spec = importlib.util.spec_from_file_location("wb_viz_graph", _VALIDATE_DIR / "graph.py")
assert _spec is not None and _spec.loader is not None
_g = importlib.util.module_from_spec(_spec)
sys.modules["wb_viz_graph"] = _g
_spec.loader.exec_module(_g)
_v = _g._v
yaml = _v.yaml

VERSION = 1
LAYOUT_SIZE = 1000.0
LAYOUT_ITERATIONS = 80
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp")
IMAGE_MIME = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}

# Paul Tol "muted" qualitative palette (colour-blind safe), 10 colours.
PALETTE = [
    "#CC6677", "#332288", "#DDCC77", "#117733", "#88CCEE",
    "#882255", "#44AA99", "#999933", "#AA4499", "#DDDDDD",
]  # fmt: skip
STANDARD_ZONES = [
    "tropical", "arid", "semi-arid", "mediterranean", "temperate",
    "continental", "subarctic", "polar", "alpine", "custom",
]  # fmt: skip
UNSPECIFIED_ZONE = "unspecified"


# ── small helpers ───────────────────────────────────────────────────────────


def _clean(v):
    """Make a YAML value JSON-safe (dates and other objects become strings, NaN becomes null)."""
    if isinstance(v, dict):
        return {str(k): _clean(x) for k, x in v.items()}
    if isinstance(v, (list, tuple, set)):
        return [_clean(x) for x in v]
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    if v is None or isinstance(v, (str, int, float, bool)):
        return v
    return str(v)


def _num(v):
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return None if isinstance(v, float) and (math.isnan(v) or math.isinf(v)) else v
    if isinstance(v, str):
        try:
            return float(v.strip().replace(",", ""))
        except ValueError:
            return None
    return None


_POP_RE = re.compile(r"^\s*~?\s*(\d[\d,]*(?:\.\d+)?)\s*(trillion|billion|million|thousand|k|m|bn)?\b", re.I)
_POP_MULT = {"trillion": 1e12, "billion": 1e9, "bn": 1e9, "million": 1e6, "m": 1e6, "thousand": 1e3, "k": 1e3}


def _population(v):
    """Leading number of a population value (`~45 million permanent` -> 45000000), else None."""
    n = _num(v) if not isinstance(v, str) else None
    if n is not None:
        return n
    if not isinstance(v, str):
        return None
    m = _POP_RE.match(v)
    if not m:
        return None
    val = float(m.group(1).replace(",", "")) * _POP_MULT.get((m.group(2) or "").lower(), 1)
    return int(val) if val == int(val) else val


def _str(v):
    return v if isinstance(v, str) and v.strip() else None


def _strs(v):
    if isinstance(v, str):
        return [v] if v.strip() else []
    if isinstance(v, (list, tuple)):
        return [str(x) for x in v if isinstance(x, (str, int, float)) and str(x).strip()]
    return []


def _ref_values(value):
    """Every string that may be a reference inside a (possibly nested) list/dict field."""
    out = []
    if isinstance(value, str):
        out.append(value)
    elif isinstance(value, (list, tuple)):
        for x in value:
            out.extend(_ref_values(x))
    elif isinstance(value, dict):
        for key in ("entity", "character", "faction", "location", "slug", "id", "name"):
            if isinstance(value.get(key), str):
                out.append(value[key])
                break
    return out


def _load_yaml(path):
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError):
        return None, "unreadable"
    return (data, None) if isinstance(data, dict) else (None, "not a mapping")


# ── deterministic layout ────────────────────────────────────────────────────


def compute_layout(ids, parents, edges):
    """Deterministic 2D layout in [0, 1000]^2. See references/data-format.md for the algorithm.

    ids: sorted location ids; parents: id -> parent id or None; edges: list of (a, b) route pairs.
    Returns {id: (x, y)} rounded to one decimal place.
    """
    ids = sorted(ids)
    if not ids:
        return {}
    kids = {i: [] for i in ids}
    roots = []
    for i in ids:
        p = parents.get(i)
        (kids[p] if p in kids else roots).append(i)
    centre = LAYOUT_SIZE / 2
    pos = {}
    angle_of = {}

    def place_children(parent, depth):
        children = sorted(kids[parent])
        if not children:
            return
        radius = max(24.0, 120.0 * (0.55 ** (depth - 1)))
        base = angle_of.get(parent, 0.0)
        # first child offset by half a step so children do not sit exactly on the outward axis
        for k, c in enumerate(children):
            a = base + (k + 0.5) * 2 * math.pi / len(children)
            angle_of[c] = a
            pos[c] = (pos[parent][0] + radius * math.cos(a), pos[parent][1] + radius * math.sin(a))
            place_children(c, depth + 1)

    if len(roots) == 1:
        pos[roots[0]] = (centre, centre)
        angle_of[roots[0]] = 0.0
        place_children(roots[0], 1)
    else:
        ring = 340.0
        for k, r in enumerate(roots):
            a = -math.pi / 2 + k * 2 * math.pi / len(roots)
            angle_of[r] = a
            pos[r] = (centre + ring * math.cos(a), centre + ring * math.sin(a))
            place_children(r, 1)
    # Any id missed (parent cycle): put on an outer ring in id order.
    missing = [i for i in ids if i not in pos]
    for k, i in enumerate(missing):
        a = k * 2 * math.pi / max(1, len(missing))
        pos[i] = (centre + 450 * math.cos(a), centre + 450 * math.sin(a))

    # Fixed-iteration force relaxation: pairwise repulsion, route springs, parent springs.
    n = len(ids)
    index = {i: k for k, i in enumerate(ids)}
    xs = [pos[i][0] for i in ids]
    ys = [pos[i][1] for i in ids]
    springs = [(index[a], index[b], 130.0, 0.04) for a, b in edges if a in index and b in index and a != b]
    springs += [(index[i], index[parents[i]], 60.0, 0.08) for i in ids if parents.get(i) in index]
    iterations = LAYOUT_ITERATIONS if n <= 300 else 25
    for it in range(iterations):
        cool = 1.0 - it / float(iterations)
        fx = [0.0] * n
        fy = [0.0] * n
        for a in range(n):
            for b in range(a + 1, n):
                dx = xs[a] - xs[b]
                dy = ys[a] - ys[b]
                d2 = dx * dx + dy * dy
                if d2 < 1e-6:  # coincident: deterministic nudge by index
                    dx, dy, d2 = 0.01 * (a + 1), 0.01 * (b + 1), 1e-4 * ((a + 1) ** 2 + (b + 1) ** 2)
                if d2 > 150.0 ** 2:
                    continue
                d = math.sqrt(d2)
                f = 900.0 / d2
                fx[a] += f * dx / d
                fy[a] += f * dy / d
                fx[b] -= f * dx / d
                fy[b] -= f * dy / d
        for a, b, rest, k in springs:
            dx = xs[b] - xs[a]
            dy = ys[b] - ys[a]
            d = math.sqrt(dx * dx + dy * dy) or 1e-6
            f = k * (d - rest)
            fx[a] += f * dx / d
            fy[a] += f * dy / d
            fx[b] -= f * dx / d
            fy[b] -= f * dy / d
        step = 4.0 * cool
        for a in range(n):
            mx = max(-20.0, min(20.0, fx[a] * step))
            my = max(-20.0, min(20.0, fy[a] * step))
            xs[a] = min(LAYOUT_SIZE - 20, max(20.0, xs[a] + mx))
            ys[a] = min(LAYOUT_SIZE - 20, max(20.0, ys[a] + my))
    return {i: (round(xs[index[i]], 1), round(ys[index[i]], 1)) for i in ids}


# ── builders ────────────────────────────────────────────────────────────────


def _meta(g, slug):
    for ents in g._entities.values():
        if slug in ents:
            return ents[slug]["meta"]
    return {}


def _resolve(g, ref, etype=None):
    if not isinstance(ref, str) or not ref.strip():
        return None
    slug = g.resolve_slug(ref)
    if slug is None or (etype and g.nodes[slug]["type"] != etype):
        return None
    return slug


def _resolve_all(g, value, etype=None):
    out = []
    for ref in _ref_values(value):
        s = _resolve(g, ref, etype)
        if s and s not in out:
            out.append(s)
    return out


def _calendar(g, node_ts, present_t):
    eras = []
    for e in g._eras:
        off = g._era_offsets.get(e.get("prefix"), 0)
        end = e.get("end_year")
        eras.append({
            "prefix": e.get("prefix"),
            "name": e.get("name"),
            "t0": off,
            "t1": off + int(end) if end else None,
            "sort_order": e.get("sort_order"),
        })  # fmt: skip
    pts = [t for t in node_ts if t is not None]
    if present_t is not None:
        pts.append(present_t)
    pts += [e["t0"] for e in eras] + [e["t1"] for e in eras if e["t1"] is not None]
    t_min = min(pts) if pts else 0
    t_max = max(pts) if pts else 0
    for e in eras:
        if e["t1"] is None:
            e["t1"] = max(t_max, e["t0"])
    return {"eras": eras, "t_min": t_min, "t_max": t_max, "present_t": present_t}


def _present_t(g):
    for src in (g.config, g.calendar):
        if not isinstance(src, dict):
            continue
        for key in ("present_date", "current_date"):
            wd = _v.WorldDate(src.get(key), g.calendar)
            if wd.valid:
                t = g._date_t(wd)
                if t is not None:
                    return t
    return None


def _end_t(g, slug, node):
    meta = _meta(g, slug)
    if node["type"] == "event":
        _, end = _v.get_event_date(meta, g.calendar)
    else:
        end = _v.WorldDate(meta.get("end_date"), g.calendar)
    if end is None or not getattr(end, "valid", False):
        return None
    t = g._date_t(end)
    return None if t is None or t == node["t"] else t


def _is_within(path, root):
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _find_image_file(project, ntype, slug, meta):
    """Locate an entity's image inside <project> (frontmatter `image:` first, then output/images/<dir>/<slug>)."""
    output_dir = project / "output"
    raw = _str(meta.get("image"))
    if raw and not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", raw):
        for base in (output_dir, project):
            cand = (base / raw).resolve()
            if cand.suffix.lower() in IMAGE_MIME and _is_within(cand, project) and cand.is_file():
                return cand
    type_dir = _v.ENTITY_DIRS.get(ntype)
    if type_dir:
        folder = output_dir / "images" / type_dir
        for ext in IMAGE_EXTS:
            cand = folder / f"{slug}{ext}"
            if cand.is_file():
                return cand
    return None


def _node_image(project, ntype, slug, meta, *, embed=False):
    """Return relative path from output/world-viewer.html, a data: URI when embed=True, or None."""
    raw = _str(meta.get("image"))
    if raw and raw.startswith("data:image/"):
        return raw
    path = _find_image_file(project, ntype, slug, meta)
    if path is None:
        return None
    if embed:
        mime = IMAGE_MIME.get(path.suffix.lower())
        if not mime:
            return None
        b64 = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:{mime};base64,{b64}"
    rel = os.path.relpath(path.resolve(), (project / "output").resolve())
    return Path(rel).as_posix()


def _nodes(g, project, *, embed_images=False):
    nodes = []
    for slug in sorted(g.nodes):
        n = g.nodes[slug]
        meta = _meta(g, slug)
        nodes.append({
            "id": slug,
            "type": n["type"],
            "name": n["name"],
            "t": n["t"],
            "end_t": _end_t(g, slug, n),
            "date_label": n["date"],
            "era": n["era"],
            "summary": n["summary"],
            "status": _str(meta.get("status")),
            "tags": _strs(meta.get("tags")),
            "image": _node_image(project, n["type"], slug, meta, embed=embed_images),
        })  # fmt: skip
    return nodes


def _edges(g):
    out = []
    for e in g.edges:
        out.append({
            "source": e["source"],
            "target": e["target"],
            "kind": e["kind"],
            "label": e["label"],
            "field": e["field"],
            "causal": e["kind"] == _g.CAUSES,
            "memory": e["kind"] == _g.TRACE,
        })  # fmt: skip
    out.sort(key=lambda e: (e["source"], e["target"], e["kind"], e["field"]))
    return out


def _timeline(g, nodes_by_id):
    events = []
    for slug in sorted(g.nodes):
        n = g.nodes[slug]
        if n["type"] != "event":
            continue
        meta = _meta(g, slug)
        nd = nodes_by_id[slug]

        def evs(ids):
            return sorted({i for i in ids if i in g.nodes and g.nodes[i]["type"] == "event"})

        caused_by = evs(e["source"] for e in g.in_edges(slug, _g.CAUSES))
        leads_to = evs(e["target"] for e in g.out_edges(slug, _g.CAUSES))
        traces = sorted({e["target"] for e in g.out_edges(slug, _g.TRACE)})
        participants = _resolve_all(g, [meta.get("participants"), meta.get("primary_characters"),
                                        meta.get("organizations"), meta.get("primary_factions")])  # fmt: skip
        events.append({
            "id": slug,
            "name": n["name"],
            "t": nd["t"],
            "end_t": nd["end_t"],
            "significance": _str(meta.get("significance")),
            "type": _str(meta.get("type")),
            "era": n["era"],
            "caused_by": caused_by,
            "leads_to": leads_to,
            "traces": traces,
            "participants": participants,
            "locations": _resolve_all(g, meta.get("locations"), "location"),
            "impact": {k: _str(meta.get(k + "_impact")) for k in ("economic", "social", "political", "magical")},
            "open_ended": _str(meta.get("open_ended")),
        })  # fmt: skip
    traditions = []
    for slug in sorted(g.nodes):
        n = g.nodes[slug]
        if n["type"] != "tradition":
            continue
        meta = _meta(g, slug)
        traditions.append({
            "id": slug,
            "name": n["name"],
            "kind": _str(meta.get("kind")),
            "status": _str(meta.get("status")),
            "fidelity": _str(meta.get("fidelity")),
            "first_attested_t": n["t"],
            "origin_events": _resolve_all(g, meta.get("origin_events"), "event"),
            "contradicts": _resolve_all(g, meta.get("contradicts"), "tradition"),
        })  # fmt: skip
    return {"events": events, "traditions": traditions}


def _organisms(g, value):
    out = []
    if not isinstance(value, list):
        return out
    for item in value:
        if isinstance(item, str):
            item = {"name": item}
        if not isinstance(item, dict):
            continue
        sp_ref = _str(item.get("species"))
        sp = _resolve(g, sp_ref, "species") if sp_ref else None
        name = _str(item.get("name")) or (g.nodes[sp]["name"] if sp else sp_ref)
        if not name:
            continue
        out.append({"name": name, "species": sp or sp_ref, "role": _str(item.get("role"))})
    return out


def _resource_entries(value):
    out = []
    if not isinstance(value, list):
        return out
    for item in value:
        if isinstance(item, str) and item.strip():
            out.append({"name": item.strip(), "category": None, "rarity": None})
        elif isinstance(item, dict) and _str(item.get("name")):
            out.append({"name": item["name"].strip(), "category": _str(item.get("category")),
                        "rarity": _str(item.get("rarity"))})  # fmt: skip
    return out


def _effective_climate(g, slug, cache):
    """(profile dict | None, inherited bool). A child overrides only the keys it states."""
    if slug in cache:
        return cache[slug]
    cache[slug] = (None, False)  # cycle guard
    own = _meta(g, slug).get("climate_profile")
    own = own if isinstance(own, dict) and own else None
    parent = _str(_meta(g, slug).get("parent"))
    pslug = _resolve(g, parent, "location") if parent else None
    inherited = None
    if pslug and pslug != slug:
        inherited = _effective_climate(g, pslug, cache)[0]
    if own is None and inherited is None:
        res = (None, False)
    elif own is None:
        res = (inherited, True)
    else:
        merged = dict(inherited or {})
        merged.update(own)
        res = (merged, False)
    cache[slug] = res
    return res


def _climate_out(profile, inherited):
    if profile is None:
        return None
    notes = _str(profile.get("notes"))
    if notes is None:
        drivers = _strs(profile.get("drivers"))
        notes = "; ".join(drivers) if drivers else None
    return {
        "zone": _str(profile.get("zone")),
        "temperature_c": _clean(profile.get("temperature_c")),
        "precipitation_mm": _num(profile.get("precipitation_mm")),
        "growing_season_days": _num(profile.get("growing_season_days")),
        "seasons": _clean(profile.get("seasons")) if isinstance(profile.get("seasons"), list) else [],
        "hazards": _clean(profile.get("hazards")) if isinstance(profile.get("hazards"), list) else [],
        "notes": notes,
        "inherited": inherited,
    }


def _mean_temp(t):
    """Mean of all numbers in a temperature_c value (scalar, [lo, hi] or {season: [lo, hi]})."""
    nums = []

    def walk(v):
        if isinstance(v, (list, tuple)):
            for x in v:
                walk(x)
        elif isinstance(v, dict):
            for x in v.values():
                walk(x)
        else:
            n = _num(v)
            if n is not None:
                nums.append(n)

    walk(t)
    return sum(nums) / len(nums) if nums else None


def _mean(vals):
    vals = [v for v in vals if v is not None]
    return round(sum(vals) / len(vals), 1) if vals else None


def _map(g, economy_routes_by_pair):
    loc_ids = sorted(s for s, n in g.nodes.items() if n["type"] == "location")
    parents, route_acc = {}, {}
    for slug in loc_ids:
        meta = _meta(g, slug)
        p = _resolve(g, _str(meta.get("parent")), "location")
        parents[slug] = p if p != slug else None
        for r in meta.get("routes") or []:
            if not isinstance(r, dict):
                continue
            to = _resolve(g, _str(r.get("to")), "location")
            if not to or to == slug:
                continue
            key = tuple(sorted((slug, to)))
            acc = route_acc.setdefault(key, {"modes": {}, "sides": set()})
            acc["sides"].add(slug)
            methods = r.get("methods") if isinstance(r.get("methods"), list) else []
            for m in methods:
                if isinstance(m, dict) and _str(m.get("mode")):
                    cur = acc["modes"].setdefault(m["mode"], {"mode": m["mode"], "distance": None, "time": None})
                    cur["distance"] = cur["distance"] or _str(m.get("distance"))
                    cur["time"] = cur["time"] or _str(m.get("travel_time"))
    routes = []
    for (a, b), acc in sorted(route_acc.items()):
        rid = f"{a}--{b}"
        routes.append({
            "id": rid,
            "from": a,
            "to": b,
            "modes": [acc["modes"][k] for k in sorted(acc["modes"])],
            "goods": sorted(economy_routes_by_pair.get((a, b), [])),
            "reciprocal": len(acc["sides"]) == 2,
        })  # fmt: skip
    # tree depth (cycle-safe)
    depth = {}
    for s in loc_ids:
        d, cur, seen = 0, parents.get(s), {s}
        while cur and cur not in seen:
            d += 1
            seen.add(cur)
            cur = parents.get(cur)
        depth[s] = d
    children = {s: [] for s in loc_ids}
    for s in loc_ids:
        if parents.get(s) in children:
            children[parents[s]].append(s)
    layout = compute_layout(loc_ids, parents, [(r["from"], r["to"]) for r in routes])
    cache = {}
    locations = []
    for s in loc_ids:
        meta = _meta(g, s)
        profile, inherited = _effective_climate(g, s, cache)
        hydro = meta.get("hydrology")
        pop = meta.get("population")
        locations.append({
            "id": s,
            "name": g.nodes[s]["name"],
            "type": _str(meta.get("type")),
            "parent": parents.get(s),
            "children": sorted(children[s]),
            "depth": depth[s],
            "x": layout[s][0],
            "y": layout[s][1],
            "terrain": _str(meta.get("terrain")),
            "elevation_m": _num(meta.get("elevation_m")),
            "area_km2": _num(meta.get("area_km2")),
            "population": _population(pop),
            "population_label": str(pop) if isinstance(pop, (str, int, float)) and not isinstance(pop, bool) else None,
            "climate": _climate_out(profile, inherited),
            "hydrology": _clean(hydro) if isinstance(hydro, dict) and hydro else None,
            "flora": _organisms(g, meta.get("flora")),
            "fauna": _organisms(g, meta.get("fauna")),
            "resources": _resource_entries(meta.get("resources")),
            "has_own_climate": isinstance(meta.get("climate_profile"), dict) and bool(meta.get("climate_profile")),
        })  # fmt: skip
    return {"locations": locations, "routes": routes}


def _zone_colour_map(zones):
    names = list(STANDARD_ZONES)
    for z in sorted(zones):
        if z not in names:
            names.append(z)
    return {z: PALETTE[i % len(PALETTE)] for i, z in enumerate(names)}


def _climate(locations):
    by_zone = {}
    for loc in locations:
        c = loc["climate"]
        if c is None:
            continue
        by_zone.setdefault(c["zone"] or UNSPECIFIED_ZONE, []).append(loc)
    zones = []
    for z in sorted(by_zone):
        locs = by_zone[z]
        zones.append({
            "zone": z,
            "count": len(locs),
            "locations": sorted(loc["id"] for loc in locs),
            "mean_temperature_c": _mean(_mean_temp(loc["climate"]["temperature_c"]) for loc in locs),
            "mean_precipitation_mm": _mean(loc["climate"]["precipitation_mm"] for loc in locs),
        })  # fmt: skip
    return {"zones": zones, "legend": _zone_colour_map(by_zone.keys())}


def _life(locations):
    acc = {}
    for loc in locations:
        for kind in ("flora", "fauna"):
            for o in loc[kind]:
                key = (kind, o["species"] or o["name"].lower())
                e = acc.setdefault(key, {"name": o["name"], "kind": kind, "species_id": None,
                                         "roles": set(), "locations": set(), "_sp": o["species"]})  # fmt: skip
                if o["role"]:
                    e["roles"].add(o["role"])
                e["locations"].add(loc["id"])
    return sorted(
        ({"name": e["name"], "kind": e["kind"], "species_id": e["_sp"], "roles": sorted(e["roles"]),
          "locations": sorted(e["locations"])} for e in acc.values()),
        key=lambda e: (e["kind"], e["name"].lower()),
    )  # fmt: skip


def _load_economy(project):
    path = project / "world" / "economy.yaml"
    if not path.exists():
        return None, "no world/economy.yaml"
    data, err = _load_yaml(path)
    return (data, None) if data is not None else (None, f"world/economy.yaml is {err}")


def _economy_trade_routes(g, eco):
    routes = []
    seen = set()
    for i, r in enumerate(eco.get("trade_routes") or []):
        if not isinstance(r, dict):
            continue
        name = _str(r.get("name")) or f"trade-route-{i + 1}"
        rid = _v.slugify(name) or f"trade-route-{i + 1}"
        while rid in seen:
            rid += "-x"
        seen.add(rid)
        frm, to = _str(r.get("from_location")), _str(r.get("to_location"))
        goods = []
        for gd in r.get("goods") or []:
            if isinstance(gd, str):
                gd = {"resource": gd}
            if isinstance(gd, dict) and _str(gd.get("resource")):
                goods.append({"resource": _v.slugify(gd["resource"]), "direction": _str(gd.get("direction")),
                              "volume": _str(gd.get("volume"))})  # fmt: skip
        routes.append({
            "id": rid,
            "name": name,
            "from": _resolve(g, frm, "location"),
            "to": _resolve(g, to, "location"),
            "from_label": frm,
            "to_label": to,
            "via": _resolve_all(g, r.get("via"), "location"),
            "mode": _str(r.get("mode")),
            "goods": goods,
            "annual_value": _str(r.get("annual_value")),
            "controlled_by": _str(r.get("controlled_by")),
            "status": _str(r.get("status")),
        })  # fmt: skip
    return routes


def _route_legs(tr):
    stops = [s for s in [tr["from"]] + tr["via"] + [tr["to"]] if s]
    return ["--".join(sorted((a, b))) for a, b in zip(stops, stops[1:]) if a != b]


def _goods_by_pair(eco, trade_routes):
    names = {}
    for r in (eco or {}).get("resources") or []:
        if isinstance(r, dict) and _str(r.get("name")):
            names[_v.slugify(r["name"])] = r["name"]
    pairs = {}
    for tr in trade_routes:
        tr["map_route_ids"] = _route_legs(tr)
        for gd in tr["goods"]:
            for rid in tr["map_route_ids"]:
                a, b = rid.split("--")
                pairs.setdefault((a, b), set()).add(names.get(gd["resource"], gd["resource"]))
    return pairs


def _economy(g, eco, locations, trade_routes):
    loc_ids = {loc["id"] for loc in locations}
    res = {}

    def entry(name):
        key = _v.slugify(name)
        return res.setdefault(key, {"key": key, "name": name, "category": None, "rarity": None,
                                    "producers": set(), "consumers": set(), "routes": set()})  # fmt: skip

    if eco:
        for r in eco.get("resources") or []:
            if isinstance(r, dict) and _str(r.get("name")):
                e = entry(r["name"])
                e["category"], e["rarity"] = _str(r.get("category")), _str(r.get("rarity"))
                e["consumers"].update(s for s in _resolve_all(g, r.get("consumers"), "location"))
                e["producers"].update(s for s in _resolve_all(g, r.get("sources"), "location"))
        for p in eco.get("production") or []:
            if isinstance(p, dict) and _str(p.get("resource")):
                loc = _resolve(g, _str(p.get("location")), "location")
                e = res.get(_v.slugify(p["resource"])) or entry(p["resource"])
                if loc:
                    e["producers"].add(loc)
    for loc in locations:
        for r in loc["resources"]:
            e = entry(r["name"])
            e["category"] = e["category"] or r["category"]
            e["rarity"] = e["rarity"] or r["rarity"]
            e["producers"].add(loc["id"])
    for tr in trade_routes:
        for gd in tr["goods"]:
            e = res.get(gd["resource"])
            if e is not None:
                e["routes"].update(tr["map_route_ids"])
                e["routes"].add("trade:" + tr["id"])
    currencies = []
    for c in (eco or {}).get("currencies") or []:
        if isinstance(c, dict) and _str(c.get("name")):
            issuer = _str(c.get("issuing_authority"))
            currencies.append({
                "name": c["name"],
                "issuer": _resolve(g, issuer) or issuer,
                "accepted_in": sorted(set(_resolve_all(g, c.get("accepted_in")))),
            })  # fmt: skip
    shocks = []
    for s in (eco or {}).get("shocks") or []:
        if isinstance(s, dict) and s.get("event") is not None:
            ev = _str(s.get("event"))
            shocks.append({"event": _resolve(g, ev, "event") or ev,
                           "effects": {k: _clean(v) for k, v in s.items() if k != "event"}})  # fmt: skip
    resources = [
        {
            "name": e["name"],
            "category": e["category"],
            "rarity": e["rarity"],
            "producers": sorted(e["producers"] & loc_ids),
            "consumers": sorted(e["consumers"] & loc_ids),
            "routes": sorted(e["routes"]),
        }
        for _, e in sorted(res.items())
    ]  # fmt: skip
    return {"resources": resources, "trade_routes": trade_routes, "currencies": currencies, "shocks": shocks}


def _warnings(project_name, locations, routes, eco_err, economy, nodes, events, cal):
    w = []
    nloc = len(locations)

    def share(label, n):
        if nloc == 0:
            return
        if n == 0:
            w.append(f"0 locations have {label} data")
        elif n < nloc:
            w.append(f"{n} of {nloc} locations have {label} data")

    if nloc == 0:
        w.append("no locations found: the map, climate and life views will be empty")
    share("climate", sum(1 for loc in locations if loc["climate"]))
    share("flora", sum(1 for loc in locations if loc["flora"]))
    share("fauna", sum(1 for loc in locations if loc["fauna"]))
    share("resource", sum(1 for loc in locations if loc["resources"]))
    share("terrain or elevation", sum(1 for loc in locations if loc["terrain"] or loc["elevation_m"] is not None))
    if nloc and not routes:
        w.append("no routes declared between locations")
    if eco_err:
        w.append(f"economy data missing: {eco_err}")
    elif not economy["trade_routes"]:
        w.append("world/economy.yaml declares no trade_routes")
    if not events:
        w.append("no events found: the timeline will be empty")
    else:
        undated = sum(1 for e in events if e["t"] is None)
        if undated:
            w.append(f"{undated} of {len(events)} events have no usable date and are not placed on the timeline")
    if not cal["eras"]:
        w.append("no calendar eras defined (world/history/calendar.yaml): dates are plain years")
    if cal["present_t"] is None:
        w.append("no present_date set in project.yaml or calendar.yaml")
    unresolved = sum(1 for t in economy["trade_routes"] if not (t["from"] and t["to"]))
    if unresolved:
        w.append(f"{unresolved} trade routes have an endpoint that is not a known location")
    return w


def build_viz_data(project_dir, *, embed_images=False):
    """Return the visualiser payload for a project directory (see references/data-format.md)."""
    project = Path(project_dir).resolve()
    g = _g.WorldGraph.from_project(project)
    nodes = _nodes(g, project, embed_images=embed_images)
    nodes_by_id = {n["id"]: n for n in nodes}
    present_t = _present_t(g)
    cal = _calendar(g, [x for n in nodes for x in (n["t"], n["end_t"])], present_t)
    timeline = _timeline(g, nodes_by_id)

    eco, eco_err = _load_economy(project)
    trade_routes = _economy_trade_routes(g, eco) if eco else []
    mp = _map(g, _goods_by_pair(eco, trade_routes))
    locations = mp["locations"]
    economy = _economy(g, eco, locations, trade_routes)
    known_routes = {r["id"] for r in mp["routes"]}
    for r in economy["resources"]:
        r["routes"] = [x for x in r["routes"] if x in known_routes or x.startswith("trade:")]
    climate = _climate(locations)

    counts = {"nodes": len(nodes), "edges": len(g.edges)}
    for n in nodes:
        counts[n["type"]] = counts.get(n["type"], 0) + 1
    counts.update(routes=len(mp["routes"]), resources=len(economy["resources"]),
                  trade_routes=len(trade_routes), species_index=0)  # fmt: skip
    life = _life(locations)
    counts["species_index"] = len(life)

    return {
        "version": VERSION,
        "project": {"name": str(g.config.get("title") or project.name), "present_t": present_t},
        "counts": counts,
        "calendar": cal,
        "nodes": nodes,
        "edges": _edges(g),
        "timeline": timeline,
        "map": mp,
        "climate": climate,
        "life": {"species_index": life},
        "economy": economy,
        "warnings": _warnings(project.name, locations, mp["routes"], eco_err, economy, nodes,
                              timeline["events"], cal),  # fmt: skip
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Write the world visualiser JSON payload")
    ap.add_argument("project")
    ap.add_argument("--out", help="write here instead of stdout")
    ap.add_argument("--embed-images", action="store_true", help="base64-encode discovered entity images as data URIs")
    args = ap.parse_args(argv)
    if not (Path(args.project) / "project.yaml").exists():
        print(f"error: no project.yaml in {args.project}", file=sys.stderr)
        return 1
    payload = build_viz_data(args.project, embed_images=args.embed_images)
    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
