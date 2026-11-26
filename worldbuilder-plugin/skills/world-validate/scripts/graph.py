#!/usr/bin/env python3
"""WorldBuilder in-memory graph layer (plugin edition).

Usage:
    graph.py <project-dir> <command> [args] [--json]

Commands:
    stats                      counts by type / edge kind, components, causal depth
    why <slug>                 upstream causal ancestry down to root causes
    impact <slug> [--depth N]  downstream: causal effects, then structural dependents
    path <a> <b>               shortest path (undirected) with edge kinds
    neighbors <slug>           incoming and outgoing edges
    unrooted                   events with no causal ancestry / root_causes; traditions with no
                               origin event; edgeless entities
    export [--out FILE]        JSON for a visualiser (see WorldGraph.to_dict)

The loader, reference resolver and WorldDate code are reused from validate.py
(same directory). Python 3.9+, standard library only (PyYAML is vendored).

Export schema (version 1):
    {"version": 1, "project": {"title", "path"}, "calendar": {"name", "eras": [...]},
     "nodes": [{"id", "slug", "type", "name", "date", "end_date", "era", "t", "summary"}],
     "edges": [{"source", "target", "kind", "field", "label", "provenance": [{"file", "field"}]}]}
    `t` is a number sortable along the world timeline (era offset + year + month/day
    fraction), or null for undated nodes (a tradition's t comes from first_attested).
    Causal edges (kind "causes") go cause -> effect
    and satisfy t(source) <= t(target) whenever both are dated and comparable.
    Edges of kind "leaves-trace" go event -> tradition (or other entity) and mean "this event left
    that present-day mark"; they are the memory link between the truth chain and the memory chain.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import deque
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate as _v  # noqa: E402

CAUSES = "causes"
# Memory chain: event -> tradition/entity that carries a present-day mark of it.
# Derived from event.traces and tradition.origin_events; one edge per pair, provenance kept.
TRACE = "leaves-trace"

# Fields never scanned for references (free text, labels, or names that may collide with entities).
SKIP_KEYS = {
    "name",
    "aliases",
    "tags",
    "type",
    "title",
    "description",
    "descriptions",
    "role",
    "impact",
    "notes",
    "examples",
    "naming_conventions",
    "family_name",
    "remembered_as",
    "root_causes",
    "immediate_trigger",
    "immediate_consequences",
    "long_term_consequences",
    "drives",
    "distortions",
    "distortion_causes",
    "origin_unknown",
}
# Keys that merely wrap the reference inside a dict item; the kind comes from the key before them.
WRAPPER_KEYS = {
    "entity",
    "target",
    "to",
    "slug",
    "id",
    "character",
    "faction",
    "location",
    "species",
    "race",
    "language",
}
MAX_REF_LEN = 80

KIND_BY_FIELD = {
    "participants": "participant",
    "organizations": "participant",
    "primary_characters": "participant",
    "primary_factions": "participant",
    "locations": "location",
    "primary_location": "location",
    "location": "location",
    "members": "member",
    "allies": "ally",
    "enemies": "enemy",
    "routes": "route",
    "connections": "route",
    "relationships": "relationship",
    "characters_involved": "involved",
    "notable_characters": "notable_character",
    "practitioners": "practitioner",
    "races": "has_race",
    "current_territories": "territory",
    "faction_affiliations": "affiliated",
    "literacy": "literate_in",
    "native": "native_language",
    "spoken": "speaks",
    "rival_lineages": "rival",
    "current_head": "head",
}
KIND_BY_TYPE_FIELD = {
    ("character", "faction"): "member_of",
    ("lineage", "faction"): "member_of",
    ("location", "faction"): "controlled_by",
    ("faction", "faction"): "member_of",
    ("character", "arc"): "arc",
}
# Structural dependency: edge source depends on edge target (so target's impact reaches source).
DEPENDENT_IN = {
    "parent",
    "member_of",
    "location",
    "headquarters",
    "seat",
    "controlled_by",
    "owner",
    "species",
    "race",
    "homeland",
    "territory",
}
# Edge source "contains/owns" target (so source's impact reaches target).
DEPENDENT_OUT = {"member", "notable_character", "practitioner", "has_race"}
UNDIRECTED_STRUCTURAL = {"route"}
SUMMARY_LEN = 160
DATE_FIELDS = ("date", "start_date", "founded", "founding_date", "birth_date", "born", "created", "first_attested")


def _first_text(value):
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        for v in value.values():
            t = _first_text(v)
            if t:
                return t
    return ""


def _summary(meta):
    desc = meta.get("descriptions")
    text = ""
    if isinstance(desc, dict):
        text = _first_text(desc.get("machine")) or _first_text(desc.get("human"))
    text = text or _first_text(meta.get("remembered_as")) or _first_text(meta.get("summary"))
    text = " ".join(text.split())
    return text if len(text) <= SUMMARY_LEN else text[: SUMMARY_LEN - 1].rstrip() + "…"


class WorldGraph:
    """Typed, directed multigraph of a project's entities."""

    def __init__(self, project_dir, config=None, calendar=None):
        self.project_dir = Path(project_dir)
        self.config = config or {}
        self.calendar = calendar or {}
        self.nodes = {}  # slug -> node dict
        self.edges = []  # edge dicts
        self._edge_keys = {}
        self._out = {}
        self._in = {}
        self._entities = {}
        self._eras = []
        self._era_offsets = {}

    # ── construction ────────────────────────────────────────────────────────

    @classmethod
    def from_project(cls, path):
        project_dir = Path(path).resolve()
        config_file = project_dir / "project.yaml"
        if not config_file.exists():
            raise FileNotFoundError(f"no project.yaml in {project_dir}")
        report = _v.Report(project_dir)
        config = _v.load_yaml_file(config_file, report, "project.yaml")
        calendar = _v.load_yaml_file(project_dir / "world" / "history" / "calendar.yaml", report, "calendar.yaml")
        entities = _v.collect_entities(project_dir, report)
        cx = _v.Ctx(entities, _v.build_name_index(entities), config, calendar, report)
        g = cls(project_dir, config, calendar)
        g._build(cx)
        return g

    def _build(self, cx):
        self._entities = cx.entities
        self._compute_era_offsets()
        for etype, ents in cx.entities.items():
            for slug, ent in ents.items():
                if slug not in self.nodes:
                    self.nodes[slug] = self._make_node(slug, etype, ent)
        for etype, ents in cx.entities.items():
            for slug, ent in ents.items():
                if self.nodes[slug]["type"] != etype:
                    continue
                self._derive_edges(cx, slug, etype, ent)

    def _compute_era_offsets(self):
        eras = [e for e in (self.calendar.get("eras") or []) if isinstance(e, dict)]
        eras.sort(key=lambda e: e.get("sort_order", 0) or 0)
        self._eras = eras
        offset = 0
        for e in eras:
            self._era_offsets[e.get("prefix")] = offset
            offset += int(e.get("end_year") or 0)

    def _date_t(self, wd):
        if not wd.valid:
            return None
        if self._eras:
            if wd.era_prefix not in self._era_offsets:
                return None
            base = self._era_offsets[wd.era_prefix]
        else:
            base = 0
        frac = 0.0
        if wd.month:
            frac += (wd.month - 1) / 12.0
            if wd.day:
                frac += (wd.day - 1) / 365.0
        return round(base + wd.year + frac, 4)

    def _make_node(self, slug, etype, ent):
        meta = ent["meta"]
        cal = self.calendar
        start = end = None
        wd = None
        if etype == "event":
            start, end = _v.get_event_date(meta, cal)
            wd = start if start.valid else None
        else:
            for f in DATE_FIELDS:
                cand = _v.WorldDate(meta.get(f), cal)
                if cand.valid:
                    wd, end = cand, _v.WorldDate(meta.get("end_date"), cal)
                    break
        era = meta.get("era") if isinstance(meta.get("era"), str) else ""
        if not era and wd is not None and wd.era_prefix:
            for e in self._eras:
                if e.get("prefix") == wd.era_prefix:
                    era = e.get("name", "")
        return {
            "id": slug,
            "slug": slug,
            "type": etype,
            "name": str(meta.get("name", meta.get("title", slug))),
            "date": wd.display if wd is not None else None,
            "end_date": end.display if end is not None and end.valid and end is not wd else None,
            "era": era or None,
            "t": self._date_t(wd) if wd is not None else None,
            "summary": _summary(meta),
            "file": ent.get("rel", ""),
        }

    def _add_edge(self, src, tgt, kind, field, file, label=""):
        key = (src, tgt, kind) if kind in (CAUSES, TRACE) else (src, tgt, kind, field)
        prov = {"file": file, "field": field}
        existing = self._edge_keys.get(key)
        if existing is not None:
            if prov not in existing["provenance"]:
                existing["provenance"].append(prov)
            if label and not existing["label"]:
                existing["label"] = label
            return
        edge = {"source": src, "target": tgt, "kind": kind, "field": field, "label": label, "provenance": [prov]}
        self._edge_keys[key] = edge
        self.edges.append(edge)
        self._out.setdefault(src, []).append(edge)
        self._in.setdefault(tgt, []).append(edge)

    def _derive_edges(self, cx, slug, etype, ent):
        file = ent.get("rel", "")

        def emit(ref, path, label):
            r = cx.resolve(ref)
            if not r or r[2] == slug or r[2] not in self.nodes:
                return
            target = r[2]
            keys = [k for k in path if k not in WRAPPER_KEYS] or path[:1]
            field = ".".join(path)
            leaf = keys[-1]
            if path[0] in ("caused_by", "leads_to"):
                if path[0] == "caused_by":
                    self._add_edge(target, slug, CAUSES, path[0], file)
                else:
                    self._add_edge(slug, target, CAUSES, path[0], file)
                return
            if etype == "event" and path[0] == "traces":
                self._add_edge(slug, target, TRACE, "traces", file)
                return
            if etype == "tradition" and path[0] == "origin_events":
                if self.nodes[target]["type"] == "event":
                    self._add_edge(target, slug, TRACE, "origin_events", file)
                return
            kind = KIND_BY_TYPE_FIELD.get((etype, leaf)) or KIND_BY_FIELD.get(leaf) or leaf
            self._add_edge(slug, target, kind, field, file, label)

        def walk(value, path, label):
            if isinstance(value, dict):
                lab = _first_text(value.get("role")) or _first_text(value.get("type")) or label
                for k, v in value.items():
                    if k in SKIP_KEYS:
                        continue
                    walk(v, path + [str(k)], lab if path else "")
            elif isinstance(value, (list, tuple)):
                for v in value:
                    walk(v, path, label)
            elif isinstance(value, str) and path and len(value) <= MAX_REF_LEN:
                emit(value, path, label)

        walk(ent["meta"], [], "")

    # ── queries ─────────────────────────────────────────────────────────────

    def has(self, slug):
        return slug in self.nodes

    def resolve_slug(self, ref):
        """Accept a slug, a name, or a slugified name; return the node slug or None."""
        if ref in self.nodes:
            return ref
        s = _v.slugify(ref)
        if s in self.nodes:
            return s
        low = str(ref).lower()
        for slug, n in self.nodes.items():
            if n["name"].lower() == low:
                return slug
        return None

    def out_edges(self, slug, kind=None):
        return [e for e in self._out.get(slug, []) if kind is None or e["kind"] == kind]

    def in_edges(self, slug, kind=None):
        return [e for e in self._in.get(slug, []) if kind is None or e["kind"] == kind]

    def neighbors(self, slug):
        """List of {"slug", "direction": "out"|"in", "kind", "field", "label"} for adjacent nodes."""
        res = []
        for e in self._out.get(slug, []):
            res.append(
                {"slug": e["target"], "direction": "out", "kind": e["kind"], "field": e["field"], "label": e["label"]}
            )
        for e in self._in.get(slug, []):
            res.append(
                {"slug": e["source"], "direction": "in", "kind": e["kind"], "field": e["field"], "label": e["label"]}
            )
        return res

    def memory_parents(self, slug):
        """Events whose present-day trace this tradition is (the memory link)."""
        if self.nodes[slug]["type"] != "tradition":
            return []
        return [
            e["source"]
            for e in self._in.get(slug, [])
            if e["kind"] == TRACE and self.nodes[e["source"]]["type"] == "event"
        ]

    def _why_parents(self, slug):
        return self.causal_parents(slug) + self.memory_parents(slug)

    def causal_parents(self, slug):
        return [e["source"] for e in self._in.get(slug, []) if e["kind"] == CAUSES]

    def causal_children(self, slug):
        return [e["target"] for e in self._out.get(slug, []) if e["kind"] == CAUSES]

    def ancestors(self, slug):
        """Causal ancestry as a tree: {"slug", "children": [...], "seen": bool}.

        Shared ancestors are expanded once (later occurrences have seen=True and no children).
        Also returns the root causes list via roots()."""
        expanded = set()

        def build(s, stack):
            node = {"slug": s, "children": [], "seen": False}
            if s in expanded:
                node["seen"] = bool(self._why_parents(s))
                return node
            expanded.add(s)
            memory = set(self.memory_parents(s))
            for p in self._why_parents(s):
                if p in stack:  # cycle guard
                    node["children"].append({"slug": p, "children": [], "seen": True, "cycle": True})
                    continue
                child = build(p, stack | {s})
                if p in memory:
                    child["link"] = "memory"  # the tradition is a trace of this event, not caused by it
                node["children"].append(child)
            return node

        return build(slug, frozenset())

    def root_causes(self, slug):
        """Ancestors with no causal parents (or [slug] itself if it has none), in discovery order."""
        seen, order, q = {slug}, [], deque([slug])
        roots = []
        while q:
            s = q.popleft()
            order.append(s)
            ps = self._why_parents(s)
            if not ps and s != slug:
                roots.append(s)
            for p in ps:
                if p not in seen:
                    seen.add(p)
                    q.append(p)
        return roots

    def descendants(self, slug, depth=None):
        """Causal effects: list of {"slug", "depth", "via"} (BFS, nearest first)."""
        res, seen, q = [], {slug}, deque([(slug, 0, None)])
        while q:
            s, d, via = q.popleft()
            if depth is not None and d >= depth:
                continue
            for c in self.causal_children(s):
                if c not in seen:
                    seen.add(c)
                    res.append({"slug": c, "depth": d + 1, "via": s})
                    q.append((c, d + 1, s))
        return res

    def _structural_steps(self, slug):
        """Yield (dependent_slug, edge, how) pairs that depend structurally on slug."""
        for e in self._in.get(slug, []):
            if e["kind"] in DEPENDENT_IN:
                yield e["source"], e
        for e in self._out.get(slug, []):
            if e["kind"] in DEPENDENT_OUT:
                yield e["target"], e
        for e in self._out.get(slug, []):
            if e["kind"] in UNDIRECTED_STRUCTURAL:
                yield e["target"], e
        for e in self._in.get(slug, []):
            if e["kind"] in UNDIRECTED_STRUCTURAL:
                yield e["source"], e

    def impact(self, slug, depth=None):
        """Everything downstream of slug.

        Returns {"slug", "effects": [...], "dependents": [...], "traces": [...]}. Each effect is
        {"slug", "depth", "path": [step]}; each dependent likewise. A step is
        {"from", "to", "kind", "field"}. Causal effects come from "causes" edges; dependents are
        reached through structural edges (contained locations, members, things located there,
        routes through it, owned items, ...)."""
        effects = []
        seen = {slug}
        q = deque([(slug, [])])
        while q:
            s, path = q.popleft()
            if depth is not None and len(path) >= depth:
                continue
            for e in self.out_edges(s, CAUSES):
                t = e["target"]
                if t in seen:
                    continue
                seen.add(t)
                p = path + [{"from": s, "to": t, "kind": CAUSES, "direction": "out", "field": e["field"]}]
                effects.append({"slug": t, "depth": len(p), "path": p})
                q.append((t, p))
        dependents = []
        dseen = {slug}
        q = deque([(slug, [])])
        while q:
            s, path = q.popleft()
            if depth is not None and len(path) >= depth:
                continue
            for t, e in self._structural_steps(s):
                if t in dseen:
                    continue
                dseen.add(t)
                d = "out" if e["source"] == s else "in"
                p = path + [{"from": s, "to": t, "kind": e["kind"], "direction": d, "field": e["field"]}]
                dependents.append({"slug": t, "depth": len(p), "path": p})
                q.append((t, p))
        traces = []
        for e in self.out_edges(slug, TRACE):
            t = e["target"]
            meta = self._entities.get(self.nodes[t]["type"], {}).get(t, {}).get("meta", {})
            status = meta.get("status")
            traces.append(
                {"slug": t, "type": self.nodes[t]["type"], "status": status if isinstance(status, str) else None}
            )
        return {"slug": slug, "effects": effects, "dependents": dependents, "traces": traces}

    def shortest_path(self, a, b):
        """Undirected shortest path as a list of steps {"from","to","kind","direction","field"};
        [] if a == b; None if unreachable."""
        if a not in self.nodes or b not in self.nodes:
            return None
        if a == b:
            return []
        prev: dict = {a: None}
        q = deque([a])
        while q:
            s = q.popleft()
            for e in self._out.get(s, []):
                if e["target"] not in prev:
                    prev[e["target"]] = (s, e, "out")
                    q.append(e["target"])
            for e in self._in.get(s, []):
                if e["source"] not in prev:
                    prev[e["source"]] = (s, e, "in")
                    q.append(e["source"])
            if b in prev:
                break
        if b not in prev:
            return None
        steps, cur = [], b
        while prev[cur] is not None:
            s, e, d = prev[cur]
            steps.append({"from": s, "to": cur, "kind": e["kind"], "direction": d, "field": e["field"]})
            cur = s
        steps.reverse()
        return steps

    def components(self):
        seen, comps = set(), []
        for start in self.nodes:
            if start in seen:
                continue
            comp, q = [], deque([start])
            seen.add(start)
            while q:
                s = q.popleft()
                comp.append(s)
                for n in self.neighbors(s):
                    if n["slug"] not in seen:
                        seen.add(n["slug"])
                        q.append(n["slug"])
            comps.append(comp)
        comps.sort(key=len, reverse=True)
        return comps

    def causal_depth(self):
        """Longest causal chain (in edges). Cycles are broken at the back edge."""
        memo, state = {}, {}

        def depth(s):
            if s in memo:
                return memo[s]
            state[s] = 1
            best = 0
            for c in self.causal_children(s):
                if state.get(c) == 1:
                    continue
                best = max(best, 1 + depth(c))
            state[s] = 2
            memo[s] = best
            return best

        sys.setrecursionlimit(max(sys.getrecursionlimit(), 10000))
        return max((depth(s) for s in self.nodes), default=0)

    def stats(self):
        by_type, by_kind = {}, {}
        for n in self.nodes.values():
            by_type[n["type"]] = by_type.get(n["type"], 0) + 1
        for e in self.edges:
            by_kind[e["kind"]] = by_kind.get(e["kind"], 0) + 1
        comps = self.components()
        return {
            "nodes": len(self.nodes),
            "edges": len(self.edges),
            "by_type": dict(sorted(by_type.items())),
            "by_kind": dict(sorted(by_kind.items(), key=lambda kv: (-kv[1], kv[0]))),
            "components": len(comps),
            "largest_component": len(comps[0]) if comps else 0,
            "isolated": sum(1 for c in comps if len(c) == 1),
            "causal_depth": self.causal_depth(),
        }

    def unrooted(self):
        events, edgeless, traditions = [], [], []
        for slug, n in self.nodes.items():
            if n["type"] == "tradition" and not self.memory_parents(slug):
                traditions.append(slug)
            if n["type"] == "event":
                meta = self._entities["event"][slug]["meta"]
                has_root_text = any(_first_text(x) for x in _v.listify(meta.get("root_causes")))
                if not self.causal_parents(slug) and not has_root_text:
                    events.append(slug)
            if not self._out.get(slug) and not self._in.get(slug):
                edgeless.append(slug)
        return {"events": events, "traditions": traditions, "edgeless": edgeless}

    def root_cause_text(self, slug):
        meta = self._entities.get(self.nodes[slug]["type"], {}).get(slug, {}).get("meta", {})
        return [" ".join(str(x).split()) for x in _v.listify(meta.get("root_causes")) if _first_text(x)]

    def to_dict(self):
        eras = [
            {
                "name": e.get("name"),
                "prefix": e.get("prefix"),
                "sort_order": e.get("sort_order"),
                "offset": self._era_offsets.get(e.get("prefix"), 0),
            }
            for e in self._eras
        ]
        title = self.config.get("title") or self.project_dir.name
        nodes = []
        for n in self.nodes.values():
            d = {k: v for k, v in n.items() if k != "file"}
            nodes.append(d)
        return {
            "version": 1,
            "project": {"title": str(title), "path": self.project_dir.name},
            "calendar": {"name": self.calendar.get("name"), "eras": eras},
            "nodes": nodes,
            "edges": [dict(e) for e in self.edges],
        }

    # ── text helpers ────────────────────────────────────────────────────────

    def label(self, slug, with_date=True):
        n = self.nodes[slug]
        s = f"{slug} ({n['type']})"
        if with_date and n["date"]:
            s += f" [{n['date']}]"
        return s


# ═════════════════════════════════════════════════════════════════════════════
# Rendering
# ═════════════════════════════════════════════════════════════════════════════


def _step_text(steps):
    return " ".join(
        (f"-{s['kind']}-> {s['to']}" if s.get("direction", "out") == "out" else f"<-{s['kind']}- {s['to']}")
        for s in steps
    )


def _render_why(g, slug, tree, roots):
    lines = [f"WHY {g.label(slug)} {g.nodes[slug]['name']!r}"]
    if not tree["children"]:
        if g.nodes[slug]["type"] == "tradition":
            unknown = _v.listify(g._entities["tradition"][slug]["meta"].get("origin_unknown"))
            lines.append("  (no origin events)" + (f"; origin_unknown: {unknown[0]}" if unknown else ""))
        else:
            lines.append("  (no causal ancestors)")

    def rec(node, prefix, last, top=False):
        for i, ch in enumerate(node["children"]):
            is_last = i == len(node["children"]) - 1
            tag = " (cycle)" if ch.get("cycle") else " (see above)" if ch["seen"] else ""
            mem = " [memory link: origin of tradition]" if ch.get("link") == "memory" else ""
            lines.append(f"{prefix}{'└─ ' if is_last else '├─ '}{g.label(ch['slug'])}{mem}{tag}")
            rec(ch, prefix + ("   " if is_last else "│  "), is_last)

    rec(tree, "  ", True, True)
    own = g.root_cause_text(slug)
    targets = roots or ([slug] if not tree["children"] else [])
    lines.append("ROOT CAUSES")
    for r in targets:
        lines.append(f"  {g.label(r)}")
        for t in g.root_cause_text(r) or []:
            lines.append(f"    - {t}")
        if not g.root_cause_text(r):
            lines.append("    (no root_causes text)")
    if own and slug not in targets:
        lines.append(f"ROOT CAUSES OF {slug} (own field)")
        lines.extend(f"    - {t}" for t in own)
    return "\n".join(lines)


def _render_impact(g, res):
    lines = [f"IMPACT of {g.label(res['slug'])} {g.nodes[res['slug']]['name']!r}"]
    lines.append(f"Causal effects ({len(res['effects'])})")
    for x in res["effects"]:
        lines.append(f"  {g.label(x['slug'])}  via {res['slug']} {_step_text(x['path'])}")
    lines.append(f"Traces in the present ({len(res['traces'])})")
    for x in res["traces"]:
        lines.append(f"  {x['slug']} ({x['type']})" + (f" [{x['status']}]" if x["status"] else ""))
    lines.append(f"Structural dependents ({len(res['dependents'])})")
    for x in res["dependents"]:
        lines.append(f"  {g.label(x['slug'], with_date=False)}  via {res['slug']} {_step_text(x['path'])}")
    return "\n".join(lines)


def _render_path(g, a, b, steps):
    if steps is None:
        return f"NO PATH between {a} and {b}"
    out = [f"PATH {a} -> {b} ({len(steps)} hops)"]
    parts = [a]
    for s in steps:
        arrow = f"-{s['kind']}->" if s["direction"] == "out" else f"<-{s['kind']}-"
        parts.append(arrow)
        parts.append(s["to"])
    out.append("  " + " ".join(parts))
    return "\n".join(out)


def _render_stats(st):
    lines = [
        f"nodes {st['nodes']}  edges {st['edges']}  components {st['components']} "
        f"(largest {st['largest_component']}, isolated {st['isolated']})  causal depth {st['causal_depth']}",
        "types: " + ", ".join(f"{k} {v}" for k, v in st["by_type"].items()),
        "edge kinds: " + ", ".join(f"{k} {v}" for k, v in st["by_kind"].items()),
    ]
    return "\n".join(lines)


# ═════════════════════════════════════════════════════════════════════════════
# CLI
# ═════════════════════════════════════════════════════════════════════════════


def _emit(args, data, text):
    print(json.dumps(data, indent=2, ensure_ascii=False) if args.json else text)


def main(argv=None):
    ap = argparse.ArgumentParser(description="WorldBuilder graph queries")
    ap.add_argument("project", help="project directory (contains project.yaml)")
    ap.add_argument("command", choices=["stats", "why", "impact", "path", "neighbors", "unrooted", "export"])
    ap.add_argument("args", nargs="*", help="slug(s) for why/impact/neighbors/path")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--depth", type=int, default=None, help="impact: maximum hops")
    ap.add_argument("--out", default=None, help="export: write to this file instead of stdout")
    args = ap.parse_args(argv)

    try:
        g = WorldGraph.from_project(args.project)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    need = {"why": 1, "impact": 1, "neighbors": 1, "path": 2}.get(args.command, 0)
    if len(args.args) != need:
        print(f"error: '{args.command}' takes {need} slug argument(s)", file=sys.stderr)
        return 2
    slugs = []
    for ref in args.args:
        s = g.resolve_slug(ref)
        if s is None:
            print(f"error: no entity '{ref}'", file=sys.stderr)
            return 2
        slugs.append(s)

    cmd = args.command
    if cmd == "stats":
        st = g.stats()
        _emit(args, st, _render_stats(st))
    elif cmd == "why":
        tree = g.ancestors(slugs[0])
        roots = g.root_causes(slugs[0])
        data = {
            "slug": slugs[0],
            "tree": tree,
            "roots": [{"slug": r, "date": g.nodes[r]["date"], "root_causes": g.root_cause_text(r)} for r in roots],
        }
        _emit(args, data, _render_why(g, slugs[0], tree, roots))
    elif cmd == "impact":
        res = g.impact(slugs[0], args.depth)
        _emit(args, res, _render_impact(g, res))
    elif cmd == "path":
        steps = g.shortest_path(slugs[0], slugs[1])
        _emit(args, {"from": slugs[0], "to": slugs[1], "path": steps}, _render_path(g, slugs[0], slugs[1], steps))
    elif cmd == "neighbors":
        ns = g.neighbors(slugs[0])
        lines = [f"NEIGHBORS of {g.label(slugs[0])} ({len(ns)})"]
        for n in ns:
            arrow = f"-{n['kind']}->" if n["direction"] == "out" else f"<-{n['kind']}-"
            lab = f"  ({n['label']})" if n["label"] else ""
            lines.append(f"  {arrow} {g.label(n['slug'], with_date=False)}{lab}")
        _emit(args, {"slug": slugs[0], "neighbors": ns}, "\n".join(lines))
    elif cmd == "unrooted":
        u = g.unrooted()
        lines = [f"Events with no causal ancestry and no root_causes ({len(u['events'])})"]
        lines += [f"  {g.label(s)}" for s in u["events"]]
        lines.append(f"Traditions with no origin event ({len(u['traditions'])})")
        lines += [f"  {g.label(s)}" for s in u["traditions"]]
        lines.append(f"Entities with no edges ({len(u['edgeless'])})")
        lines += [f"  {g.label(s, with_date=False)}" for s in u["edgeless"]]
        _emit(args, u, "\n".join(lines))
    elif cmd == "export":
        text = json.dumps(g.to_dict(), indent=2, ensure_ascii=False)
        if args.out:
            Path(args.out).write_text(text + "\n", encoding="utf-8")
            print(f"wrote {args.out} ({len(g.nodes)} nodes, {len(g.edges)} edges)")
        else:
            print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
