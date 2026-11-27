#!/usr/bin/env python3
"""WorldBuilder project validator (plugin edition).

Usage:
    validate.py <project-dir> [--json] [--severity error|warning]

Ported from scripts/worldbuilder.py (cmd_validate and helpers) and
scripts/graph.py, minus the media (image_prompt / voice) completeness rules,
plus new causal-consistency checks for events.

Exit code: 1 if any ERROR was found, otherwise 0 (2 for usage / project errors).
Python 3.9+, standard library only, except PyYAML which is vendored in
./vendor/yaml.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import yaml  # noqa: E402  (vendored PyYAML)

# ═════════════════════════════════════════════════════════════════════════════
# Constants
# ═════════════════════════════════════════════════════════════════════════════

ENTITY_DIRS = {
    "character": "characters",
    "location": "locations",
    "faction": "factions",
    "item": "items",
    "magic-system": "magic-systems",
    "arc": "arcs",
    "event": "events",
    "species": "species",
    "race": "races",
    "language": "languages",
    "lineage": "lineages",
    "tradition": "traditions",
}

# A purely oral tradition that claims to be accurate after this many years is implausible.
ORAL_DRIFT_YEARS = 300
TRADITION_REF_FIELDS = ("held_by", "regions", "places", "language", "related")

# From assets/editors/worldrules.yaml (tech_keywords), embedded so this script
# stays standalone.
TECH_KEYWORDS = {
    "gunpowder": [
        "gun",
        "musket",
        "rifle",
        "pistol",
        "cannon",
        "artillery",
        "explosive",
        "bomb",
        "grenade",
        "ammunition",
        "bullet",
        "shot",
        "powder-horn",
        "cartridge",
    ],
    "printing": ["newspaper", "pamphlet", "printed", "press", "typeset", "broadsheet", "gazette"],
    "electricity": ["electric", "battery", "wire", "lightbulb", "circuit", "generator", "voltage", "outlet", "plug"],
    "steam_power": ["steam engine", "locomotive", "boiler", "piston", "steam-powered", "steamship"],
    "computing": ["computer", "program", "algorithm", "digital", "processor", "data", "binary", "server"],
    "spaceflight": ["rocket", "spacecraft", "orbit", "launch", "zero-g", "airlock", "thruster"],
}

# Transport method keyword -> required technology flag (from validate_geography)
TECH_TRANSPORT = {
    "train": "steam_power",
    "railway": "steam_power",
    "locomotive": "steam_power",
    "steamship": "steam_power",
    "car": "combustion",
    "automobile": "combustion",
    "airplane": "flight",
    "spaceship": "spaceflight",
    "starship": "spaceflight",
    "wormhole": "spaceflight",
    "teleporter": "teleportation",
}
# Transport modes that need magic. Routes using these are an error when
# world_flags.magic.present is false (or prevalence is none).
MAGIC_TRANSPORT = [
    "teleportation",
    "teleport",
    "ley-line",
    "ley line",
    "leyline",
    "portal",
    "magic carpet",
    "flying carpet",
    "broomstick",
    "waygate",
    "planeshift",
    "dimension door",
]
# The original looks up flags under exactly these names; real projects often use
# a longer name (e.g. internal_combustion), so accept known aliases too.
FLAG_ALIASES = {
    "combustion": ["combustion", "internal_combustion"],
    "flight": ["flight", "aviation", "aerospace"],
}

# Canonical significance values come from events/_schema.yaml
# (trivial|minor|notable|important|crucial|world-changing); "major" and "critical"
# are legacy spellings that older projects use, tolerated rather than flagged.
SIGNIFICANT = {"important", "crucial", "world-changing", "major", "critical"}
NOTABLE_ROLES = {"protagonist", "antagonist", "supporting", "major"}
POSTHUMOUS_ROLES = {
    "deceased",
    "victim",
    "died",
    "honoured",
    "honored",
    "commemorated",
    "namesake",
    "subject",
    "memorialised",
    "memorialized",
    "legacy",
    "remembered",
}


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", str(name).lower()).strip("-")


# ═════════════════════════════════════════════════════════════════════════════
# WorldDate
# ═════════════════════════════════════════════════════════════════════════════

_DATE_RE = re.compile(
    r"^\s*(?:(?P<pre>[A-Za-z][A-Za-z.]*)\s*)?(?P<year>-?\d+)"
    r"(?:\s*(?P<post>[A-Za-z][A-Za-z.]*))?"
    r"(?:\s*m(?:onth)?\.?\s*(?P<month>\d+))?(?:\s*d(?:ay)?\.?\s*(?P<day>\d+))?\s*$"
)


class WorldDate:
    """A date in the world's calendar (port of scripts/worldbuilder.py WorldDate).

    Extensions over the original: bare strings such as "CE 250" / "250 CE" are
    parsed, and comparison stops at the coarsest precision both dates share
    (a year-only date is not "earlier" than a dated month in the same year).
    """

    def __init__(self, data, calendar_config=None):
        self.valid = False
        self.year = self.month = self.day = 0
        self.era_prefix = ""
        self.era_sort = 0
        self.display = ""
        self.approximate = False
        self.era_known = True

        if isinstance(data, bool) or data is None or data == "":
            return
        if isinstance(data, dict):
            if not data.get("year"):
                return
            try:
                self.year = int(data.get("year", 0))
                self.month = int(data.get("month", 0) or 0)
                self.day = int(data.get("day", 0) or 0)
            except (TypeError, ValueError):
                return
            self.era_prefix = str(data.get("era_prefix", "") or "")
            self.display = data.get("display", "") or ""
            self.approximate = bool(data.get("approximate", False))
        elif isinstance(data, (int, float)):
            self.year = int(data)
        elif isinstance(data, str):
            m = _DATE_RE.match(data)
            if not m:
                self.display = data
                return
            self.year = int(m.group("year"))
            self.month = int(m.group("month") or 0)
            self.day = int(m.group("day") or 0)
            self.era_prefix = m.group("pre") or m.group("post") or ""
        else:
            return

        self.valid = True
        if calendar_config and self.era_prefix:
            self.era_known = False
            for era in calendar_config.get("eras", []) or []:
                if isinstance(era, dict) and era.get("prefix") == self.era_prefix:
                    self.era_sort = era.get("sort_order", 0) or 0
                    self.era_known = True
                    break
        elif self.era_prefix:
            self.era_known = False  # no calendar to order eras by
        if not self.display:
            parts = []
            if self.era_prefix:
                parts.append(self.era_prefix)
            parts.append(str(self.year))
            if self.month:
                parts.append(f"m{self.month}")
            if self.day:
                parts.append(f"d{self.day}")
            self.display = " ".join(parts)

    def cmp(self, other):
        """-1/0/1, or None when the dates cannot be compared reliably."""
        if not self.valid or not other.valid:
            return None
        if self.era_prefix != other.era_prefix:
            if not (self.era_known and other.era_known):
                return None
            if self.era_sort == other.era_sort:
                return None
        a = [self.era_sort, self.year]
        b = [other.era_sort, other.year]
        if self.month and other.month:
            a.append(self.month)
            b.append(other.month)
            if self.day and other.day:
                a.append(self.day)
                b.append(other.day)
        return (a > b) - (a < b)

    def __repr__(self):
        return f"WorldDate({self.display})" if self.valid else "WorldDate(unknown)"


def get_event_date(meta, calendar):
    """(start, end) for an event (port of get_event_date)."""
    date = WorldDate(meta.get("date"), calendar)
    start = WorldDate(meta.get("start_date"), calendar)
    end = WorldDate(meta.get("end_date"), calendar)
    if date.valid:
        return date, date
    if start.valid:
        return start, end if end.valid else start
    return WorldDate(None), WorldDate(None)


# ═════════════════════════════════════════════════════════════════════════════
# Issues
# ═════════════════════════════════════════════════════════════════════════════


class Report:
    def __init__(self, project_dir):
        self.project_dir = project_dir
        self.issues = []
        self._seen = set()

    def add(self, severity, code, where, field, message, hint=""):
        """where: an entity dict (with 'rel'), a path string, or None."""
        file = where.get("rel", "") if isinstance(where, dict) else (where or "")
        key = (severity, code, file, field, message)
        if key in self._seen:
            return
        self._seen.add(key)
        self.issues.append(
            {"severity": severity, "check": code, "file": file, "field": field, "message": message, "hint": hint}
        )

    def error(self, code, where, field, message, hint=""):
        self.add("error", code, where, field, message, hint)

    def warn(self, code, where, field, message, hint=""):
        self.add("warning", code, where, field, message, hint)


# ═════════════════════════════════════════════════════════════════════════════
# Loading
# ═════════════════════════════════════════════════════════════════════════════


def read_frontmatter(path):
    """Return (meta, body, error). Mirrors parse_frontmatter but reports problems."""
    content = path.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return None, content, "no-frontmatter"
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None, content, "unclosed-frontmatter"
    try:
        meta = yaml.safe_load(parts[1])
    except yaml.YAMLError as exc:
        first = str(exc).strip().splitlines()
        return None, content, "yaml: " + " ".join(s.strip() for s in first[:3])
    if meta is None:
        return None, parts[2], "empty-frontmatter"
    if not isinstance(meta, dict):
        return None, parts[2], "frontmatter is a %s, not a mapping" % type(meta).__name__
    return meta, parts[2], None


def collect_entities(project_dir, report):
    entities = {}
    world_dir = project_dir / "world"
    story_dir = project_dir / "story"

    def rel(p):
        return str(p.relative_to(project_dir))

    def load_md(f, bucket):
        try:
            meta, body, err = read_frontmatter(f)
        except (OSError, UnicodeDecodeError) as exc:
            report.error("frontmatter", rel(f), "", f"cannot read file: {exc}", "Check the file is readable UTF-8.")
            return
        if err:
            if err == "no-frontmatter":
                report.warn(
                    "frontmatter",
                    rel(f),
                    "",
                    "no YAML frontmatter (file does not start with '---')",
                    "Add a frontmatter block, or rename the file with a leading '_' to exclude it.",
                )
            elif err == "unclosed-frontmatter":
                report.error(
                    "frontmatter",
                    rel(f),
                    "",
                    "frontmatter is not closed (missing second '---')",
                    "Add a closing '---' line after the YAML block.",
                )
            elif err == "empty-frontmatter":
                report.warn("frontmatter", rel(f), "", "frontmatter block is empty", "Fill in at least name and type.")
            else:
                report.error(
                    "frontmatter",
                    rel(f),
                    "",
                    f"frontmatter parse error: {err}",
                    "Fix the YAML syntax (quote strings containing ':' or '#', check indentation).",
                )
            return
        bucket[f.stem] = {"meta": meta, "body": body, "file": f, "rel": rel(f)}

    for etype, dirname in ENTITY_DIRS.items():
        if etype == "arc":
            search_dir = story_dir / "arcs"
        elif etype == "event":
            search_dir = world_dir / "events"
        else:
            search_dir = world_dir / dirname
        if not search_dir.exists():
            continue
        bucket = entities.setdefault(etype, {})
        for f in sorted(search_dir.glob("*.md")):
            if f.name.startswith("_"):
                continue
            load_md(f, bucket)
        for f in sorted(search_dir.glob("*.yaml")):
            if f.name.startswith("_"):
                continue
            try:
                meta = yaml.safe_load(f.read_text(encoding="utf-8"))
            except yaml.YAMLError as exc:
                report.error(
                    "frontmatter",
                    rel(f),
                    "",
                    "YAML parse error: " + " ".join(str(exc).split())[:200],
                    "Fix the YAML syntax.",
                )
                continue
            if isinstance(meta, dict):
                bucket[f.stem] = {"meta": meta, "body": "", "file": f, "rel": rel(f)}
            elif meta is not None:
                report.error(
                    "frontmatter",
                    rel(f),
                    "",
                    "top level of the YAML file is not a mapping",
                    "The file must be a key: value mapping.",
                )

    chapters = entities.setdefault("chapter", {})
    chapters_dir = story_dir / "chapters"
    if chapters_dir.exists():
        for f in sorted(chapters_dir.glob("*.md")):
            if not f.name.startswith("_"):
                load_md(f, chapters)
    return entities


def load_yaml_file(path, report, label):
    if not path.exists():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        report.error(
            "config", str(path), "", f"{label} parse error: " + " ".join(str(exc).split())[:200], "Fix the YAML syntax."
        )
        return {}
    return data if isinstance(data, dict) else {}


def build_name_index(entities):
    index = {}
    for etype, ents in entities.items():
        for slug, data in ents.items():
            name = str(data["meta"].get("name", data["meta"].get("title", slug)))
            entry = (etype, name, slug)
            index[slug] = entry
            index[name.lower()] = entry
            index[slugify(name)] = entry
    return index


def ref_str(ref):
    """Reference value -> string (accepts the dict forms used in templates)."""
    if isinstance(ref, dict):
        for key in ("entity", "target", "slug", "character", "faction", "species", "race", "language", "location"):
            if ref.get(key):
                return str(ref[key])
        return ""
    if ref is None or ref is False:
        return ""
    return str(ref)


def listify(value):
    if value is None or value == "":
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


class Ctx:
    """Everything a check needs."""

    def __init__(self, entities, name_index, config, calendar, report):
        self.entities = entities
        self.index = name_index
        self.config = config
        self.calendar = calendar
        self.report = report

    def resolve(self, ref):
        ref = ref_str(ref)
        if not ref:
            return None
        idx = self.index
        if ref in idx:
            return idx[ref]
        s = slugify(ref)
        if s in idx:
            return idx[s]
        if ref.lower() in idx:
            return idx[ref.lower()]
        return None

    def ents(self, etype):
        return self.entities.get(etype, {})

    def get(self, resolved):
        if not resolved:
            return None
        return self.entities.get(resolved[0], {}).get(resolved[2])

    def flag(self, group, name, aliases=None):
        flags = (self.config.get("world_flags") or {}).get(group) or {}
        if not isinstance(flags, dict):
            return None
        for key in aliases or [name]:
            if key in flags:
                v = flags[key]
                return v.get("value") if isinstance(v, dict) else v
        return None


def flag_is_false(val):
    return val is False or val == "false" or val == "none"


# ═════════════════════════════════════════════════════════════════════════════
# Original checks: references (cmd_validate)
# ═════════════════════════════════════════════════════════════════════════════


def check_references(cx):
    R = cx.report
    for slug, ent in cx.ents("character").items():
        meta = ent["meta"]
        name = meta.get("name", slug)
        for rel in listify(meta.get("relationships")):
            if isinstance(rel, dict):
                target = ref_str(rel.get("target") or rel.get("entity"))
                if target and not cx.resolve(target):
                    R.error(
                        "dangling-ref",
                        ent,
                        "relationships",
                        f"Character '{name}': relationship target '{target}' not found",
                        "Create the entity file or correct the slug in the relationship.",
                    )
        loc = ref_str(meta.get("location"))
        if loc and not cx.resolve(loc):
            R.warn(
                "dangling-ref",
                ent,
                "location",
                f"Character '{name}': location '{loc}' not found",
                "Create the location file or correct the slug.",
            )
        faction = ref_str(meta.get("faction"))
        if faction and not cx.resolve(faction):
            R.warn(
                "dangling-ref",
                ent,
                "faction",
                f"Character '{name}': faction '{faction}' not found",
                "Create the faction file or correct the slug.",
            )
        if meta.get("status") == "dead" and not meta.get("last_appearance"):
            R.warn(
                "dead-last-appearance",
                ent,
                "last_appearance",
                f"Character '{meta.get('name', slug)}': status is 'dead' but last_appearance not set",
                "Set last_appearance to the chapter/scene where the character last appears.",
            )

    for slug, ent in cx.ents("chapter").items():
        meta = ent["meta"]
        title = meta.get("title", slug)
        pov = ref_str(meta.get("pov"))
        if pov and not cx.resolve(pov):
            R.error(
                "dangling-ref",
                ent,
                "pov",
                f"Chapter '{title}': POV character '{pov}' not found",
                "Create the character file or correct the slug.",
            )
        for char in listify(meta.get("characters_present")):
            if ref_str(char) and not cx.resolve(char):
                R.warn(
                    "dangling-ref",
                    ent,
                    "characters_present",
                    f"Chapter '{title}': character '{ref_str(char)}' not found",
                    "Create the character file or correct the slug.",
                )

    for slug, ent in cx.ents("location").items():
        meta = ent["meta"]
        parent = ref_str(meta.get("parent"))
        if parent and not cx.resolve(parent):
            R.warn(
                "dangling-ref",
                ent,
                "parent",
                f"Location '{meta.get('name', slug)}': parent '{parent}' not found",
                "Create the parent location or correct the slug.",
            )


# ═════════════════════════════════════════════════════════════════════════════
# Original checks: events (cmd_validate), minus the causal ones that are
# re-done in check_causality
# ═════════════════════════════════════════════════════════════════════════════


def check_event_refs(cx):
    R = cx.report
    for slug, ent in cx.ents("event").items():
        meta = ent["meta"]
        name = meta.get("name", slug)
        evt_type = meta.get("type", "milestone")

        for p in listify(meta.get("participants")):
            ref = ref_str(p)
            if ref and not cx.resolve(ref):
                R.error(
                    "dangling-ref",
                    ent,
                    "participants",
                    f"Event '{name}': participant '{ref}' not found",
                    "Create the entity file or correct the slug.",
                )
        for loc_ref in listify(meta.get("locations")):
            if ref_str(loc_ref) and not cx.resolve(loc_ref):
                R.warn(
                    "dangling-ref",
                    ent,
                    "locations",
                    f"Event '{name}': location '{ref_str(loc_ref)}' not found",
                    "Create the location file or correct the slug.",
                )
        for org in listify(meta.get("organizations")):
            if ref_str(org) and not cx.resolve(org):
                R.warn(
                    "dangling-ref",
                    ent,
                    "organizations",
                    f"Event '{name}': organization '{ref_str(org)}' not found",
                    "Create the faction file or correct the slug.",
                )
        for item_ref in listify(meta.get("items_involved")):
            if ref_str(item_ref) and not cx.resolve(item_ref):
                R.warn(
                    "dangling-ref",
                    ent,
                    "items_involved",
                    f"Event '{name}': item '{ref_str(item_ref)}' not found",
                    "Create the item file or correct the slug.",
                )

        for fieldname in ("caused_by", "leads_to"):
            for ref in listify(meta.get(fieldname)):
                if not ref_str(ref):
                    continue
                resolved = cx.resolve(ref)
                if not resolved:
                    R.warn(
                        "dangling-ref",
                        ent,
                        fieldname,
                        f"Event '{name}': {fieldname} '{ref_str(ref)}' not found",
                        "Create the event file or correct the slug.",
                    )
                elif resolved[0] != "event":
                    R.error(
                        "wrong-ref-type",
                        ent,
                        fieldname,
                        f"Event '{name}': {fieldname} '{ref_str(ref)}' is a {resolved[0]}, not an event",
                        "Causal links must name other events; record non-event causes in the event text.",
                    )

        start, end = get_event_date(meta, cx.calendar)
        if start.valid and end.valid and end.cmp(start) == -1:
            R.error(
                "date-order",
                ent,
                "end_date",
                f"Event '{name}': end_date ({end.display}) is before start_date ({start.display})",
                "Swap or correct the dates.",
            )

        if evt_type == "death":
            person_ref = ref_str(meta.get("person"))
            for p in listify(meta.get("participants")):
                if isinstance(p, dict) and str(p.get("role", "")).lower() in ("deceased", "victim", "died"):
                    person_ref = person_ref or ref_str(p)
            resolved = cx.resolve(person_ref) if person_ref else None
            if resolved and resolved[0] == "character":
                char = cx.ents("character").get(resolved[2])
                if char and char["meta"].get("status") != "dead":
                    R.warn(
                        "death-status",
                        ent,
                        "type",
                        f"Event '{name}': death event for '{resolved[1]}' but character status is "
                        f"'{char['meta'].get('status', '?')}', not 'dead'",
                        "Set status: dead on the character, or fix the event type.",
                    )


# ═════════════════════════════════════════════════════════════════════════════
# Traditions (the memory chain) and event traces (the truth chain's marks)
# ═════════════════════════════════════════════════════════════════════════════


def _abs_year(wd, calendar):
    """A date as a single year number on the world timeline, or None if it cannot be placed."""
    if not wd.valid:
        return None
    eras = [e for e in listify(calendar.get("eras") if isinstance(calendar, dict) else None) if isinstance(e, dict)]
    if not eras:
        return None if wd.era_prefix else wd.year
    eras.sort(key=lambda e: e.get("sort_order", 0) or 0)
    offset = 0
    for e in eras:
        if e.get("prefix") == wd.era_prefix:
            return offset + wd.year
        if not e.get("end_year"):
            return None  # an earlier era of unknown length: the year cannot be placed
        offset += int(e["end_year"])
    return None


def present_date(cx):
    """The project's present date (WorldDate) if declared, else None.
    Read from present_date / current_date in project.yaml, then in calendar.yaml."""
    for src in (cx.config, cx.calendar):
        if not isinstance(src, dict):
            continue
        for key in ("present_date", "current_date"):
            wd = WorldDate(src.get(key), cx.calendar)
            if wd.valid:
                return wd
    return None


def _resolved_slugs(cx, refs):
    return [r[2] for r in (cx.resolve(x) for x in listify(refs) if ref_str(x)) if r]


def check_traditions(cx):
    R = cx.report
    events = cx.ents("event")
    traditions = cx.ents("tradition")

    # Event.traces: dangling (warning) and reciprocity with origin_events.
    for slug, ent in events.items():
        name = ent["meta"].get("name", slug)
        for ref in listify(ent["meta"].get("traces")):
            if not ref_str(ref):
                continue
            r = cx.resolve(ref)
            if not r:
                R.warn("dangling-ref", ent, "traces", f"Event '{name}': trace '{ref_str(ref)}' not found",
                       "Create the entity file or correct the slug.")
            elif r[0] == "tradition":
                t = traditions.get(r[2])
                back = _resolved_slugs(cx, t["meta"].get("origin_events"))
                if slug not in back:
                    R.warn("trace-reciprocity", ent, "traces",
                           f"Event '{name}': traces tradition '{r[1]}', but that tradition's origin_events "
                           "doesn't reference back",
                           f"Add '{slug}' to origin_events in {t['rel']}, or remove it from traces here.")

    present = present_date(cx)
    for slug, ent in traditions.items():
        meta = ent["meta"]
        name = meta.get("name", slug)

        origin_dates = []
        n_origin = 0
        for ref in listify(meta.get("origin_events")):
            if not ref_str(ref):
                continue
            n_origin += 1
            r = cx.resolve(ref)
            if not r:
                R.error("dangling-ref", ent, "origin_events",
                        f"Tradition '{name}': origin event '{ref_str(ref)}' not found",
                        "Create the event file or correct the slug. A tradition must descend from a real event.")
                continue
            if r[0] != "event":
                R.error("wrong-ref-type", ent, "origin_events",
                        f"Tradition '{name}': origin_events '{ref_str(ref)}' is a {r[0]}, not an event",
                        "origin_events must name events; use held_by, regions or places for other entities.")
                continue
            ev = events[r[2]]
            start, _ = get_event_date(ev["meta"], cx.calendar)
            if start.valid:
                origin_dates.append(start)
            back = _resolved_slugs(cx, ev["meta"].get("traces"))
            if slug not in back:
                R.warn("trace-reciprocity", ent, "origin_events",
                       f"Tradition '{name}': origin event '{r[1]}' doesn't list it in traces",
                       f"Add '{slug}' to traces in {ev['rel']}, or remove it from origin_events here.")

        for fld in TRADITION_REF_FIELDS:
            for ref in listify(meta.get(fld)):
                if ref_str(ref) and not cx.resolve(ref):
                    R.warn("dangling-ref", ent, fld, f"Tradition '{name}': {fld} '{ref_str(ref)}' not found",
                           "Create the entity file or correct the slug.")
        for fld in ("contradicts",):
            for ref in listify(meta.get(fld)):
                if not ref_str(ref):
                    continue
                r = cx.resolve(ref)
                if not r:
                    R.warn("dangling-ref", ent, fld, f"Tradition '{name}': {fld} '{ref_str(ref)}' not found",
                           "Create the entity file or correct the slug.")
                elif r[0] == "tradition" and r[2] != slug:
                    other = traditions[r[2]]
                    back = _resolved_slugs(cx, other["meta"].get(fld))
                    if slug not in back:
                        R.warn("symmetry", ent, fld,
                               f"Tradition '{name}': {fld} '{r[1]}' has no reciprocal entry",
                               f"Add '{slug}' to {fld} in {other['rel']}, or remove it here.")

        if n_origin == 0 and not _nonempty(meta.get("origin_unknown")):
            R.warn("orphan-tradition", ent, "origin_events",
                   f"Tradition '{name}' has no origin_events and no origin_unknown",
                   "Trace it to the real event(s) it descends from, or, if the origin is a deliberate mystery, "
                   "say so and why in origin_unknown.")

        if not origin_dates:
            continue
        earliest = origin_dates[0]
        for dt in origin_dates[1:]:
            if dt.cmp(earliest) == -1:
                earliest = dt
        attested = WorldDate(meta.get("first_attested"), cx.calendar)
        if attested.valid and attested.cmp(earliest) == -1:
            R.error("tradition-before-origin", ent, "first_attested",
                    f"Tradition '{name}': first_attested ({attested.display}) is before its earliest origin "
                    f"event ({earliest.display})",
                    "A tradition cannot predate what it descends from. Fix the date or the origin_events.")

        if (str(meta.get("transmission") or "").lower() == "oral"
                and str(meta.get("fidelity") or "").lower() == "accurate" and present is not None):
            if earliest.era_prefix == present.era_prefix:
                y0, y1 = earliest.year, present.year
            else:
                y0, y1 = _abs_year(earliest, cx.calendar), _abs_year(present, cx.calendar)
            if y0 is not None and y1 is not None and y1 - y0 >= ORAL_DRIFT_YEARS:
                R.warn("implausible-fidelity", ent, "fidelity",
                       f"Tradition '{name}': purely oral and 'accurate' after {y1 - y0} years "
                       f"(threshold {ORAL_DRIFT_YEARS})",
                       "Oral memory drifts: lower the fidelity and record distortions and distortion_causes, "
                       "or change the transmission to written, ritual, art or mixed.")


# ═════════════════════════════════════════════════════════════════════════════
# Causal consistency (original chronology/symmetry checks + new checks a-g)
# ═════════════════════════════════════════════════════════════════════════════


def _event_links(cx):
    """Return (links, edges): links[slug] = (caused, leads) resolved event slugs;
    edges = {(cause, effect): declared_on_field_of_effect or 'leads_to'}."""
    events = cx.ents("event")
    links = {}
    edges = {}
    for slug, ent in events.items():
        caused, leads = [], []
        for ref in listify(ent["meta"].get("caused_by")):
            r = cx.resolve(ref)
            if r and r[0] == "event":
                caused.append(r[2])
                edges.setdefault((r[2], slug), "caused_by")
        for ref in listify(ent["meta"].get("leads_to")):
            r = cx.resolve(ref)
            if r and r[0] == "event":
                leads.append(r[2])
                edges.setdefault((slug, r[2]), "leads_to")
        links[slug] = (caused, leads)
    return links, edges


def _tarjan(nodes, adj):
    index, low, onstack, stack, out = {}, {}, set(), [], []
    counter = [0]
    sys.setrecursionlimit(max(sys.getrecursionlimit(), 10000))

    def strong(v):
        index[v] = low[v] = counter[0]
        counter[0] += 1
        stack.append(v)
        onstack.add(v)
        for w in adj.get(v, ()):
            if w not in index:
                strong(w)
                low[v] = min(low[v], low[w])
            elif w in onstack:
                low[v] = min(low[v], index[w])
        if low[v] == index[v]:
            comp = []
            while True:
                w = stack.pop()
                onstack.discard(w)
                comp.append(w)
                if w == v:
                    break
            out.append(comp)

    for n in nodes:
        if n not in index:
            strong(n)
    return out


def check_causality(cx):
    R = cx.report
    events = cx.ents("event")
    if not events:
        return
    links, edges = _event_links(cx)

    def ename(slug):
        return events[slug]["meta"].get("name", slug)

    # (a) reciprocity: original semantics, warnings, both directions.
    for slug, (caused, leads) in links.items():
        ent = events[slug]
        for target in leads:
            if slug not in links[target][0]:
                R.warn(
                    "causal-reciprocity",
                    ent,
                    "leads_to",
                    f"Event '{ename(slug)}' leads_to '{ename(target)}', but that event's caused_by doesn't "
                    f"reference back",
                    f"Add '{slug}' to caused_by in {events[target]['rel']}, or remove it from leads_to here.",
                )
        for cause in caused:
            if slug not in links[cause][1]:
                R.warn(
                    "causal-reciprocity",
                    ent,
                    "caused_by",
                    f"Event '{ename(slug)}': caused_by '{ename(cause)}', but that event's leads_to doesn't "
                    f"reference back",
                    f"Add '{slug}' to leads_to in {events[cause]['rel']}, or remove it from caused_by here.",
                )

    # (b) a cause must not be later than its effect (original: ERROR).
    for (cause, effect), declared in sorted(edges.items()):
        if cause == effect:
            continue
        cs, _ = get_event_date(events[cause]["meta"], cx.calendar)
        es, _ = get_event_date(events[effect]["meta"], cx.calendar)
        if cs.cmp(es) == 1:
            host, fld = (events[effect], "caused_by") if declared == "caused_by" else (events[cause], "leads_to")
            R.error(
                "causal-chronology",
                host,
                fld,
                f"Event '{ename(effect)}' ({es.display}): caused_by '{ename(cause)}' ({cs.display}) "
                f"which happens AFTER it",
                "Fix the dates, or reverse/remove the causal link (a cause cannot postdate its effect).",
            )

    # (c) cycles
    adj = {}
    for c, e in edges:
        adj.setdefault(c, []).append(e)
    for comp in _tarjan(sorted(events), adj):
        selfloop = len(comp) == 1 and comp[0] in adj.get(comp[0], ())
        if len(comp) > 1 or selfloop:
            comp = sorted(comp)
            R.error(
                "causal-cycle",
                events[comp[0]],
                "caused_by/leads_to",
                "Causal cycle between events: " + " -> ".join(comp + [comp[0]]),
                "Break the loop: an event cannot be its own ancestor. Remove one caused_by/leads_to link.",
            )

    # (d) orphan / uncaused significant events
    for slug, ent in events.items():
        meta = ent["meta"]
        caused, leads = links[slug]
        sig = (
            str(meta.get("importance") or "").lower() in SIGNIFICANT
            or str(meta.get("significance") or "").lower() in SIGNIFICANT
        )
        has_cause = bool(caused or listify(meta.get("caused_by")) or _nonempty(meta.get("root_causes")))
        has_effect = bool(leads or listify(meta.get("leads_to")))
        n = ename(slug)
        if not has_cause and not has_effect:
            R.warn(
                "orphan-event",
                ent,
                "caused_by",
                f"Event '{n}' is isolated: caused_by, leads_to and root_causes are all empty"
                + (" (significant event)" if sig else ""),
                "Link it to its causes (caused_by / root_causes) and effects (leads_to).",
            )
        elif sig:
            if not has_cause:
                R.warn(
                    "orphan-event",
                    ent,
                    "caused_by",
                    f"Significant event '{n}' has no cause (caused_by and root_causes empty)",
                    "Add caused_by events or root_causes explaining why this happened.",
                )
            # An event may declare itself open-ended (still unfolding, or its aftermath is unwritten),
            # but only with a stated reason and recorded consequences, so the waiver cannot hide a gap.
            open_ended = (
                isinstance(meta.get("open_ended"), str)
                and meta["open_ended"].strip() != ""
                and (_nonempty(meta.get("immediate_consequences")) or _nonempty(meta.get("long_term_consequences")))
            )
            # A trace is a concrete present-day effect, so it also waives 'leads to nothing'.
            has_trace = _nonempty(meta.get("traces"))
            if not has_effect and not open_ended and not has_trace:
                R.warn(
                    "orphan-event",
                    ent,
                    "leads_to",
                    f"Significant event '{n}' leads to nothing (leads_to empty)",
                    "Add leads_to events, or record the effects in the consequences fields.",
                )

    # (e) consequences
    for slug, ent in events.items():
        meta = ent["meta"]
        missing = [f for f in ("immediate_consequences", "long_term_consequences") if not _nonempty(meta.get(f))]
        if missing:
            R.warn(
                "missing-consequences",
                ent,
                ", ".join(missing),
                f"Event '{ename(slug)}': {' and '.join(missing)} empty",
                "Record what changed afterwards (people, places, factions, economy).",
            )

    check_event_existence(cx, events)


def _nonempty(v):
    if v is None or v == "":
        return False
    if isinstance(v, (list, tuple, dict)):
        return any(_nonempty(x) for x in (v.values() if isinstance(v, dict) else v))
    return True


# ── existence / lifespan (f, g) ──────────────────────────────────────────────

CREATION_FIELDS = {
    "character": ("born", "birth_date", "birth", "date_of_birth"),
    "faction": ("founding_date", "founded", "created", "formed"),
    "location": ("founded", "founding_date", "created", "creation_date", "established"),
    "item": ("creation_date", "created"),
    "lineage": ("founded", "founding_date"),
}
END_FIELDS = {
    "character": ("died", "death_date", "death", "date_of_death"),
    "faction": ("dissolution_date", "dissolved"),
}


def _field_date(meta, names, calendar):
    for n in names:
        if n in meta:
            d = WorldDate(meta[n], calendar)
            if d.valid:
                return d
    return None


def check_event_existence(cx, events):
    R = cx.report
    chars = cx.ents("character")

    # Birth and death dates for characters, from fields then birth/death events.
    born, died = {}, {}
    for slug, ent in chars.items():
        b = _field_date(ent["meta"], CREATION_FIELDS["character"], cx.calendar)
        d = _field_date(ent["meta"], END_FIELDS["character"], cx.calendar)
        if b:
            born[slug] = b
        if d:
            died[slug] = d
    own_events = {}  # (char, event) pairs that are the character's own birth/death
    for eslug, ent in events.items():
        meta = ent["meta"]
        etype = meta.get("type")
        if etype not in ("birth", "death"):
            continue
        refs = [ref_str(meta.get("person"))]
        for p in listify(meta.get("participants")):
            if isinstance(p, dict) and str(p.get("role", "")).lower() in (
                ("born", "child", "newborn", "subject") if etype == "birth" else ("deceased", "victim", "died")
            ):
                refs.append(ref_str(p))
        start, _ = get_event_date(meta, cx.calendar)
        for ref in refs:
            r = cx.resolve(ref) if ref else None
            if r and r[0] == "character":
                own_events.setdefault(r[2], set()).add(eslug)
                if start.valid:
                    (born if etype == "birth" else died).setdefault(r[2], start)

    # birth after death
    for slug in chars:
        if slug in born and slug in died and born[slug].cmp(died[slug]) == 1:
            R.error(
                "lifespan",
                chars[slug],
                "born/died",
                f"Character '{chars[slug]['meta'].get('name', slug)}': birth ({born[slug].display}) is after "
                f"death ({died[slug].display})",
                "Correct the birth or death date.",
            )

    for eslug, ent in events.items():
        meta = ent["meta"]
        ename = meta.get("name", eslug)
        start, _ = get_event_date(meta, cx.calendar)
        if not start.valid:
            continue

        # who is in this event
        actors = []
        for p in listify(meta.get("participants")) + listify(meta.get("primary_characters")):
            r = cx.resolve(p)
            if r:
                role = str(p.get("role", "")).lower() if isinstance(p, dict) else ""
                actors.append((r, role, "participants"))
        for o in listify(meta.get("organizations")) + listify(meta.get("primary_factions")):
            r = cx.resolve(o)
            if r:
                actors.append((r, "", "organizations"))
        for loc in listify(meta.get("locations")) + listify(meta.get("primary_location")):
            r = cx.resolve(loc)
            if r:
                actors.append((r, "", "locations"))
        for it in listify(meta.get("items_involved")):
            r = cx.resolve(it)
            if r:
                actors.append((r, "", "items_involved"))

        seen = set()
        for (etype, nm, slug), role, fld in actors:
            if (etype, slug) in seen:
                continue
            seen.add((etype, slug))
            if etype == "character":
                if eslug in own_events.get(slug, ()):
                    continue
                if slug in born and start.cmp(born[slug]) == -1:
                    R.error(
                        "lifespan",
                        ent,
                        fld,
                        f"Event '{ename}' ({start.display}): '{nm}' takes part before being born "
                        f"({born[slug].display})",
                        "Fix the event date, the participant, or the character's birth date.",
                    )
                if slug in died and start.cmp(died[slug]) == 1 and role not in POSTHUMOUS_ROLES:
                    R.error(
                        "lifespan",
                        ent,
                        fld,
                        f"Event '{ename}' ({start.display}): '{nm}' takes part after dying ({died[slug].display})",
                        "Fix the event date, remove the participant, or give them a posthumous role (e.g. 'deceased').",
                    )
            elif etype in CREATION_FIELDS:
                target = cx.ents(etype).get(slug)
                if not target:
                    continue
                created = _field_date(target["meta"], CREATION_FIELDS[etype], cx.calendar)
                if created and start.cmp(created) == -1:
                    R.warn(
                        "existence",
                        ent,
                        fld,
                        f"Event '{ename}' ({start.display}): {etype} '{nm}' did not exist yet "
                        f"(created/founded {created.display})",
                        "Fix the event date or the founding/creation date, or remove the reference.",
                    )
                ended = _field_date(target["meta"], END_FIELDS.get(etype, ()), cx.calendar)
                if ended and start.cmp(ended) == 1:
                    R.warn(
                        "existence",
                        ent,
                        fld,
                        f"Event '{ename}' ({start.display}): {etype} '{nm}' no longer existed "
                        f"(dissolved {ended.display})",
                        "Fix the event date or the dissolution date, or remove the reference.",
                    )


# ═════════════════════════════════════════════════════════════════════════════
# Original checks: species / race / language (validate_peoples)
# ═════════════════════════════════════════════════════════════════════════════


def check_peoples(cx):
    R = cx.report
    species_data, races_data = cx.ents("species"), cx.ents("race")
    langs, chars, events = cx.ents("language"), cx.ents("character"), cx.ents("event")
    cross_ok = bool(cx.flag("peoples", "cross_species_breeding"))

    for slug, ent in races_data.items():
        meta = ent["meta"]
        name = meta.get("name", slug)
        sp_ref = ref_str(meta.get("species"))
        if sp_ref:
            resolved = cx.resolve(sp_ref)
            if not resolved:
                R.error(
                    "dangling-ref",
                    ent,
                    "species",
                    f"Race '{name}': species '{sp_ref}' not found",
                    "Create the species file or correct the slug.",
                )
            elif resolved[0] != "species":
                R.error(
                    "wrong-ref-type",
                    ent,
                    "species",
                    f"Race '{name}': species '{sp_ref}' is a {resolved[0]}, not a species",
                    "A race's species must be a species entity.",
                )
        else:
            R.warn(
                "hierarchy", ent, "species", f"Race '{name}': no species set", "Set species to the parent species slug."
            )
        lang_ref = ref_str((meta.get("culture") or {}).get("language")) if isinstance(meta.get("culture"), dict) else ""
        if lang_ref and not cx.resolve(lang_ref):
            R.warn(
                "dangling-ref",
                ent,
                "culture.language",
                f"Race '{name}': language '{lang_ref}' not found",
                "Create the language file or correct the slug.",
            )

    for slug, ent in species_data.items():
        meta = ent["meta"]
        name = meta.get("name", slug)
        for rel in listify(meta.get("relationships")):
            if isinstance(rel, dict):
                sp_ref = ref_str(rel.get("species"))
                if sp_ref and not cx.resolve(sp_ref):
                    R.warn(
                        "dangling-ref",
                        ent,
                        "relationships",
                        f"Species '{name}': relationship target '{sp_ref}' not found",
                        "Create the species file or correct the slug.",
                    )
                if rel.get("can_interbreed") and not cross_ok:
                    R.warn(
                        "world-flag",
                        ent,
                        "relationships",
                        f"Species '{name}': can_interbreed with '{sp_ref}' is true, but "
                        f"world_flags.peoples.cross_species_breeding is false/unset",
                        "Enable world_flags.peoples.cross_species_breeding or set can_interbreed: false.",
                    )
        for race_ref in listify(meta.get("races")):
            if ref_str(race_ref) and not cx.resolve(race_ref):
                R.warn(
                    "dangling-ref",
                    ent,
                    "races",
                    f"Species '{name}': race '{ref_str(race_ref)}' not found",
                    "Create the race file or correct the slug.",
                )
        culture = meta.get("culture") if isinstance(meta.get("culture"), dict) else {}
        for lang_ref in listify(culture.get("languages")):
            if ref_str(lang_ref) and not cx.resolve(lang_ref):
                R.warn(
                    "dangling-ref",
                    ent,
                    "culture.languages",
                    f"Species '{name}': language '{ref_str(lang_ref)}' not found",
                    "Create the language file or correct the slug.",
                )

    for slug, ent in langs.items():
        meta = ent["meta"]
        name = meta.get("name", slug)
        family = meta.get("family") if isinstance(meta.get("family"), dict) else {}
        parent = ref_str(family.get("parent_language"))
        if parent and not cx.resolve(parent):
            R.warn(
                "dangling-ref",
                ent,
                "family.parent_language",
                f"Language '{name}': parent_language '{parent}' not found",
                "Create the language file or correct the slug.",
            )
        for child in listify(family.get("child_languages")):
            if ref_str(child) and not cx.resolve(child):
                R.warn(
                    "dangling-ref",
                    ent,
                    "family.child_languages",
                    f"Language '{name}': child_language '{ref_str(child)}' not found",
                    "Create the language file or correct the slug.",
                )
        for entry in listify(meta.get("intelligibility")):
            if isinstance(entry, dict):
                lang_ref = ref_str(entry.get("language"))
                if lang_ref and not cx.resolve(lang_ref):
                    R.warn(
                        "dangling-ref",
                        ent,
                        "intelligibility",
                        f"Language '{name}': intelligibility target '{lang_ref}' not found",
                        "Create the language file or correct the slug.",
                    )
                score = entry.get("score", 0)
                if isinstance(score, (int, float)) and not isinstance(score, bool) and (score < 0 or score > 1):
                    R.error(
                        "range",
                        ent,
                        "intelligibility",
                        f"Language '{name}': intelligibility score {score} out of range [0.0, 1.0]",
                        "Use a score between 0.0 and 1.0.",
                    )

    # Character species/race hierarchy
    for slug, ent in chars.items():
        meta = ent["meta"]
        name = meta.get("name", slug)
        sp, race = ref_str(meta.get("species")), ref_str(meta.get("race"))
        if sp and race and species_data and races_data:
            sp_r, race_r = cx.resolve(sp), cx.resolve(race)
            if sp_r and race_r:
                race_ent = races_data.get(race_r[2])
                if race_ent:
                    race_species = ref_str(race_ent["meta"].get("species"))
                    rs = cx.resolve(race_species) if race_species else None
                    if rs and rs[2] != sp_r[2]:
                        R.error(
                            "hierarchy",
                            ent,
                            "race",
                            f"Character '{name}': race '{race}' belongs to species '{race_species}', "
                            f"but character's species is '{sp}'",
                            "Change the character's race or species so they agree.",
                        )

    # Interbreeding on birth events
    for slug, ent in events.items():
        meta = ent["meta"]
        if meta.get("type") != "birth":
            continue
        parents = listify(meta.get("parents"))
        if len(parents) < 2:
            continue
        ps = []
        for p_ref in parents:
            r = cx.resolve(p_ref)
            if r and r[0] == "character":
                ch = chars.get(r[2])
                if ch:
                    ps.append((r[1], str(ch["meta"].get("species", "human"))))
        if len(ps) >= 2:
            sp1, sp2 = ps[0][1], ps[1][1]
            if sp1 and sp2 and slugify(sp1) != slugify(sp2):
                ename = meta.get("name", slug)
                if not cross_ok:
                    R.error(
                        "world-flag",
                        ent,
                        "parents",
                        f"Birth event '{ename}': parents {ps[0][0]} ({sp1}) and {ps[1][0]} ({sp2}) are "
                        f"different species, but cross_species_breeding is not enabled",
                        "Enable world_flags.peoples.cross_species_breeding, or change a parent.",
                    )
                else:
                    sp1_data = species_data.get(slugify(sp1))
                    if sp1_data:
                        allowed = any(
                            isinstance(rel, dict)
                            and slugify(ref_str(rel.get("species"))) == slugify(sp2)
                            and rel.get("can_interbreed")
                            for rel in listify(sp1_data["meta"].get("relationships"))
                        )
                        if not allowed:
                            R.error(
                                "world-flag",
                                ent,
                                "parents",
                                f"Birth event '{ename}': cross-species breeding between {sp1} and {sp2} "
                                f"not defined in species relationships",
                                f"Add a relationship with can_interbreed: true to the {sp1} species file.",
                            )


# ═════════════════════════════════════════════════════════════════════════════
# Original checks: geography (validate_geography)
# ═════════════════════════════════════════════════════════════════════════════


def parse_coordinates(raw):
    """Parse optional location coordinates.

    Accepts [x, y] or {x: N, y: M} with finite numbers in [0, 1000].
    None or empty mapping {} means unset and returns (None, None).
    Returns ((x, y), None) if valid, or (None, reason) if malformed/out of bounds.
    """
    if raw is None or (isinstance(raw, dict) and not raw):
        return None, None
    if isinstance(raw, (list, tuple)):
        if len(raw) != 2:
            return None, f"expected 2 numbers [x, y], got {len(raw)}"
        rx, ry = raw[0], raw[1]
    elif isinstance(raw, dict):
        if set(raw.keys()) != {"x", "y"}:
            return None, "mapping must have exactly 'x' and 'y' keys"
        rx, ry = raw["x"], raw["y"]
    else:
        return None, f"expected [x, y] or {{x, y}}, got {type(raw).__name__}"
    if (
        isinstance(rx, bool)
        or isinstance(ry, bool)
        or not isinstance(rx, (int, float))
        or not isinstance(ry, (int, float))
    ):
        return None, "x and y must be finite numbers"
    fx, fy = float(rx), float(ry)
    if not (math.isfinite(fx) and math.isfinite(fy)):
        return None, "x and y must be finite numbers"
    if not (0.0 <= fx <= 1000.0 and 0.0 <= fy <= 1000.0):
        return None, f"coordinates ({fx}, {fy}) out of bounds [0, 1000]"
    return (fx, fy), None


def check_geography(cx):
    R = cx.report
    locs = cx.ents("location")
    tree = {}
    for slug, ent in locs.items():
        meta = ent["meta"]
        tree[slug] = {
            "name": meta.get("name", slug),
            "parent": ref_str(meta.get("parent")),
            "routes": [r for r in listify(meta.get("routes"))],
            "ent": ent,
        }

    for slug, node in tree.items():
        ent = node["ent"]
        _, coord_err = parse_coordinates(ent["meta"].get("coordinates"))
        if coord_err:
            R.error(
                "coordinates",
                ent,
                "coordinates",
                f"Location '{node['name']}': invalid coordinates ({coord_err})",
                "Use coordinates: [x, y] or coordinates: {x: N, y: M} with finite numbers in [0, 1000].",
            )
        parent_ref = node["parent"]
        if parent_ref and slugify(parent_ref) not in tree and not cx.resolve(parent_ref):
            R.warn(
                "dangling-ref",
                ent,
                "parent",
                f"Location '{node['name']}': parent '{parent_ref}' not found",
                "Create the parent location or correct the slug.",
            )
        for route in node["routes"]:
            if not isinstance(route, dict):
                continue
            dest = ref_str(route.get("to") or route.get("destination"))
            if dest and not cx.resolve(dest):
                R.warn(
                    "dangling-ref",
                    ent,
                    "routes",
                    f"Location '{node['name']}': route destination '{dest}' not found",
                    "Create the destination location or correct the slug.",
                )
            method = str(route.get("method", "") or "").lower()
            methods = [method] + [str(m).lower() for m in listify(route.get("methods"))]
            for m in [x for x in methods if x]:
                for transport, required in TECH_TRANSPORT.items():
                    if re.search(r"\b" + re.escape(transport) + r"\b", m) or (transport in m and len(transport) > 4):
                        val = cx.flag("technology", required, FLAG_ALIASES.get(required))
                        if flag_is_false(val):
                            R.error(
                                "world-flag",
                                ent,
                                "routes",
                                f"Location '{node['name']}': route uses '{m}' but {required} = false",
                                f"Change the transport method or set world_flags.technology.{required}.",
                            )
                if magic_flags(cx) == "absent":
                    for mt in MAGIC_TRANSPORT:
                        if re.search(r"\b" + re.escape(mt) + r"\b", m) or (mt in m and len(mt) > 4):
                            R.error(
                                "world-flag",
                                ent,
                                "routes",
                                f"Location '{node['name']}': route uses magical transport '{m}' but "
                                "world_flags.magic says there is no magic",
                                "Change the transport method, or enable magic deliberately in world_flags.magic.",
                            )
                            break

    # Ancestor cycles: report each cycle once, on its members only.
    def parent_slug(slug):
        p = tree[slug]["parent"]
        if not p:
            return ""
        s = slugify(p)
        if s in tree:
            return s
        r = cx.resolve(p)
        return r[2] if r and r[0] == "location" else ""

    reported = set()
    for slug in tree:
        path, cur = [], slug
        while cur and cur not in path:
            path.append(cur)
            cur = parent_slug(cur)
        if cur and cur in path:
            cyc = path[path.index(cur) :]
            key = frozenset(cyc)
            if key in reported:
                continue
            reported.add(key)
            R.error(
                "location-cycle",
                tree[cyc[0]]["ent"],
                "parent",
                "Location '%s': circular parent hierarchy detected (%s)"
                % (tree[cyc[0]]["name"], " -> ".join(cyc + [cyc[0]])),
                "Break the loop by clearing or correcting one parent.",
            )


def _num(v):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def check_physical_geography(cx):
    """climate_profile / hydrology / flora / fauna references, and river flow."""
    R = cx.report
    locs = cx.ents("location")

    flows = {}  # slug -> resolved location slug
    for slug, ent in locs.items():
        meta = ent["meta"]
        name = meta.get("name", slug)

        cp = meta.get("climate_profile")
        if isinstance(cp, str):
            cp_refs = [cp]
            cp_label = "climate_profile"
        elif isinstance(cp, dict):
            # drivers are free text; only entries written as references are resolved.
            cp_refs = [ref_str(x) for x in listify(cp.get("drivers")) if isinstance(x, dict)]
            cp_label = "climate_profile.drivers"
        else:
            cp_refs, cp_label = [], ""
        for ref in cp_refs:
            if ref and not cx.resolve(ref):
                R.warn(
                    "dangling-ref",
                    ent,
                    cp_label,
                    f"Location '{name}': {cp_label} reference '{ref}' not found",
                    "Create the entity file or correct the slug.",
                )

        for fld in ("flora", "fauna"):
            for entry in listify(meta.get(fld)):
                if not isinstance(entry, dict):
                    continue  # plain named entries have nothing to resolve
                ref = ref_str(entry.get("species"))
                if ref and not cx.resolve(ref):
                    R.warn(
                        "dangling-ref",
                        ent,
                        fld,
                        f"Location '{name}': {fld} species '{ref}' not found",
                        "Create the species file, correct the slug, or use name: for a plain entry.",
                    )

        hydro = meta.get("hydrology")
        target = ref_str(hydro.get("flows_to")) if isinstance(hydro, dict) else ""
        if not target:
            continue
        res = cx.resolve(target)
        if not res:
            R.warn(
                "dangling-ref",
                ent,
                "hydrology.flows_to",
                f"Location '{name}': flows_to '{target}' not found",
                "Create the river, lake or sea location, or correct the slug.",
            )
            continue
        if res[0] != "location":
            continue
        flows[slug] = res[2]
        src_elev, dst_elev = _num(meta.get("elevation_m")), None
        dst = locs.get(res[2])
        if dst:
            dst_elev = _num(dst["meta"].get("elevation_m"))
        if src_elev is not None and dst_elev is not None and dst_elev > src_elev and res[2] != slug:
            R.warn(
                "river-elevation",
                ent,
                "hydrology.flows_to",
                f"Location '{name}' ({src_elev} m) flows to '{res[1]}' ({dst_elev} m), which is higher: "
                "water does not run uphill",
                "Check both elevation_m values, or change flows_to.",
            )

    reported = set()
    for start in flows:
        path, cur = [], start
        while cur in flows and cur not in path:
            path.append(cur)
            cur = flows[cur]
        if cur in path:
            cyc = path[path.index(cur) :]
            key = frozenset(cyc)
            if key in reported:
                continue
            reported.add(key)
            R.error(
                "river-cycle",
                locs[cyc[0]],
                "hydrology.flows_to",
                "Location '%s': flows_to forms a cycle (%s)"
                % (locs[cyc[0]]["meta"].get("name", cyc[0]), " -> ".join(cyc + [cyc[0]])),
                "Water must end somewhere: break the loop at the sea, a lake or an endorheic basin.",
            )


def check_event_eras(cx):
    """Warn when an event date uses an era prefix the calendar does not define."""
    eras = cx.calendar.get("eras") if isinstance(cx.calendar, dict) else None
    prefixes = {str(e.get("prefix")) for e in listify(eras) if isinstance(e, dict) and e.get("prefix")}
    if not prefixes:
        return
    for slug, ent in cx.ents("event").items():
        for fld in ("date", "start_date", "end_date"):
            d = WorldDate(ent["meta"].get(fld), cx.calendar)
            if d.valid and d.era_prefix and d.era_prefix not in prefixes:
                cx.report.warn(
                    "unknown-era",
                    ent,
                    fld,
                    f"Event '{ent['meta'].get('name', slug)}': era prefix '{d.era_prefix}' is not defined in "
                    f"world/history/calendar.yaml (known: {', '.join(sorted(prefixes))})",
                    "Use one of the calendar's era prefixes, or add the era to the calendar.",
                )


# ═════════════════════════════════════════════════════════════════════════════
# Original checks: bidirectional symmetry (validate_bidirectional_refs + graph)
# ═════════════════════════════════════════════════════════════════════════════


def _slugs(cx, refs):
    out = []
    for r in listify(refs):
        res = cx.resolve(r)
        if res:
            out.append(res[2])
    return out


def _spouses(fl):
    sp = fl.get("spouse")
    return sp if isinstance(sp, list) else ([sp] if sp else [])


def check_symmetry(cx):
    R = cx.report
    chars, factions, locations = cx.ents("character"), cx.ents("faction"), cx.ents("location")
    species_data, races_data, lineages = cx.ents("species"), cx.ents("race"), cx.ents("lineage")

    # Character relationships (warning)
    for slug, ent in chars.items():
        meta = ent["meta"]
        name = meta.get("name", slug)
        for rel in listify(meta.get("relationships")):
            if not isinstance(rel, dict):
                continue
            target = ref_str(rel.get("target") or rel.get("entity"))
            resolved = cx.resolve(target) if target else None
            if not resolved or resolved[0] != "character":
                continue
            tdata = chars.get(resolved[2])
            if not tdata:
                continue
            back = False
            for tr in listify(tdata["meta"].get("relationships")):
                if isinstance(tr, dict):
                    t2 = cx.resolve(ref_str(tr.get("target") or tr.get("entity")))
                    if t2 and t2[2] == slug:
                        back = True
                        break
            if not back:
                R.warn(
                    "symmetry",
                    ent,
                    "relationships",
                    f"Character '{name}': has relationship to '{resolved[1]}' but no reciprocal relationship found",
                    f"Add a relationship back to '{slug}' in {tdata['rel']}.",
                )

    # Family links (error)
    for slug, ent in chars.items():
        meta = ent["meta"]
        name = meta.get("name", slug)
        fl = meta.get("family_links") if isinstance(meta.get("family_links"), dict) else {}

        for child_ref in listify(fl.get("children")):
            resolved = cx.resolve(child_ref) if child_ref else None
            if not resolved or resolved[0] != "character":
                continue
            cdata = chars.get(resolved[2])
            if not cdata:
                continue
            cfl = cdata["meta"].get("family_links") if isinstance(cdata["meta"].get("family_links"), dict) else {}
            if slug not in _slugs(cx, [cfl.get("father"), cfl.get("mother")]):
                R.error(
                    "symmetry",
                    ent,
                    "family_links.children",
                    f"Character '{name}': lists '{resolved[1]}' as child, but child's father/mother doesn't "
                    f"reference back",
                    f"Set family_links.father or mother to '{slug}' in {cdata['rel']}.",
                )

        for pf in ("father", "mother"):
            parent_ref = fl.get(pf)
            resolved = cx.resolve(parent_ref) if parent_ref else None
            if not resolved or resolved[0] != "character":
                continue
            pdata = chars.get(resolved[2])
            if not pdata:
                continue
            pfl = pdata["meta"].get("family_links") if isinstance(pdata["meta"].get("family_links"), dict) else {}
            if slug not in _slugs(cx, pfl.get("children")):
                R.error(
                    "symmetry",
                    ent,
                    f"family_links.{pf}",
                    f"Character '{name}': lists '{resolved[1]}' as {pf}, but parent's children list doesn't "
                    f"include '{name}'",
                    f"Add '{slug}' to family_links.children in {pdata['rel']}.",
                )

        for fieldname, label in (("spouse", "spouse"), ("siblings", "sibling")):
            refs = _spouses(fl) if fieldname == "spouse" else listify(fl.get("siblings"))
            for ref in refs:
                resolved = cx.resolve(ref) if ref else None
                if not resolved or resolved[0] != "character":
                    continue
                odata = chars.get(resolved[2])
                if not odata:
                    continue
                ofl = odata["meta"].get("family_links") if isinstance(odata["meta"].get("family_links"), dict) else {}
                back = _spouses(ofl) if fieldname == "spouse" else listify(ofl.get("siblings"))
                if slug not in _slugs(cx, back):
                    R.error(
                        "symmetry",
                        ent,
                        f"family_links.{fieldname}",
                        f"Character '{name}': lists '{resolved[1]}' as {label}, but {label} doesn't list '{name}' back",
                        f"Add '{slug}' to family_links.{fieldname} in {odata['rel']}.",
                    )

    # Faction membership (warning)
    for slug, ent in chars.items():
        meta = ent["meta"]
        resolved = cx.resolve(meta.get("faction")) if meta.get("faction") else None
        if not resolved or resolved[0] != "faction":
            continue
        fdata = factions.get(resolved[2])
        if not fdata:
            continue
        if slug not in _slugs(cx, [ref_str(m) for m in listify(fdata["meta"].get("members"))]):
            R.warn(
                "symmetry",
                ent,
                "faction",
                f"Character '{meta.get('name', slug)}': faction is '{resolved[1]}', but faction's members list "
                f"doesn't include them",
                f"Add '{slug}' to members in {fdata['rel']}, or change the character's faction.",
            )
    for slug, ent in factions.items():
        fname = ent["meta"].get("name", slug)
        for m in listify(ent["meta"].get("members")):
            resolved = cx.resolve(m) if ref_str(m) else None
            if not resolved or resolved[0] != "character":
                continue
            cdata = chars.get(resolved[2])
            if not cdata:
                continue
            cf = cx.resolve(cdata["meta"].get("faction")) if cdata["meta"].get("faction") else None
            if cf and cf[2] == slug:
                continue
            R.warn(
                "symmetry",
                ent,
                "members",
                f"Faction '{fname}': lists '{resolved[1]}' as member, but character's faction doesn't match",
                f"Set faction: {slug} in {cdata['rel']}, or remove the member.",
            )

    # Location notable_characters (warning)
    for slug, ent in chars.items():
        meta = ent["meta"]
        role = meta.get("role", "")
        if role not in NOTABLE_ROLES:
            continue
        resolved = cx.resolve(meta.get("location")) if meta.get("location") else None
        if not resolved or resolved[0] != "location":
            continue
        ldata = locations.get(resolved[2])
        if ldata and slug not in _slugs(cx, ldata["meta"].get("notable_characters")):
            R.warn(
                "symmetry",
                ent,
                "location",
                f"Character '{meta.get('name', slug)}' (role={role}): location is '{resolved[1]}', but "
                f"location's notable_characters doesn't include them",
                f"Add '{slug}' to notable_characters in {ldata['rel']}.",
            )

    def is_ancestor(anc, desc):
        cur, depth = desc, 0
        while cur and depth < 20:
            if cur == anc:
                return True
            loc = locations.get(cur)
            if not loc:
                break
            pr = cx.resolve(loc["meta"].get("parent")) if loc["meta"].get("parent") else None
            if not pr or pr[0] != "location":
                break
            cur = pr[2]
            depth += 1
        return False

    for slug, ent in locations.items():
        lname = ent["meta"].get("name", slug)
        for nc in listify(ent["meta"].get("notable_characters")):
            resolved = cx.resolve(nc) if nc else None
            if not resolved or resolved[0] != "character":
                continue
            cdata = chars.get(resolved[2])
            if not cdata:
                continue
            cl = cx.resolve(cdata["meta"].get("location")) if cdata["meta"].get("location") else None
            if cl and is_ancestor(slug, cl[2]):
                continue
            R.warn(
                "symmetry",
                ent,
                "notable_characters",
                f"Location '{lname}': lists '{resolved[1]}' as notable character, but character's location "
                f"doesn't match",
                f"Set location: {slug} (or a child location) in {cdata['rel']}, or remove the entry.",
            )

    # Species <-> race (error)
    for slug, ent in species_data.items():
        sname = ent["meta"].get("name", slug)
        for race_ref in listify(ent["meta"].get("races")):
            resolved = cx.resolve(race_ref) if race_ref else None
            if not resolved or resolved[0] != "race":
                continue
            rdata = races_data.get(resolved[2])
            if not rdata:
                continue
            rs = cx.resolve(rdata["meta"].get("species")) if rdata["meta"].get("species") else None
            if rs and rs[2] == slug:
                continue
            R.error(
                "symmetry",
                ent,
                "races",
                f"Species '{sname}': lists race '{resolved[1]}', but race's species doesn't point back",
                f"Set species: {slug} in {rdata['rel']}.",
            )
    for slug, ent in races_data.items():
        rname = ent["meta"].get("name", slug)
        resolved = cx.resolve(ent["meta"].get("species")) if ent["meta"].get("species") else None
        if not resolved or resolved[0] != "species":
            continue
        sdata = species_data.get(resolved[2])
        if sdata and slug not in _slugs(cx, sdata["meta"].get("races")):
            R.error(
                "symmetry",
                ent,
                "species",
                f"Race '{rname}': species is '{resolved[1]}', but species' races list doesn't include this race",
                f"Add '{slug}' to races in {sdata['rel']}.",
            )

    # Lineage membership (error)
    for slug, ent in chars.items():
        meta = ent["meta"]
        fl = meta.get("family_links") if isinstance(meta.get("family_links"), dict) else {}
        resolved = cx.resolve(fl.get("lineage")) if fl.get("lineage") else None
        if not resolved or resolved[0] != "lineage":
            continue
        ldata = lineages.get(resolved[2])
        if ldata and slug not in _slugs(cx, ldata["meta"].get("members")):
            R.error(
                "symmetry",
                ent,
                "family_links.lineage",
                f"Character '{meta.get('name', slug)}': lineage is '{resolved[1]}', but lineage's members list "
                f"doesn't include them",
                f"Add '{slug}' to members in {ldata['rel']}.",
            )
    for slug, ent in lineages.items():
        lname = ent["meta"].get("name", slug)
        for m_ref in listify(ent["meta"].get("members")):
            resolved = cx.resolve(m_ref) if m_ref else None
            if not resolved or resolved[0] != "character":
                continue
            cdata = chars.get(resolved[2])
            if not cdata:
                continue
            cfl = cdata["meta"].get("family_links") if isinstance(cdata["meta"].get("family_links"), dict) else {}
            cl = cx.resolve(cfl.get("lineage")) if cfl.get("lineage") else None
            if cl and cl[2] == slug:
                continue
            R.error(
                "symmetry",
                ent,
                "members",
                f"Lineage '{lname}': lists '{resolved[1]}' as member, but character's family_links.lineage "
                f"doesn't match",
                f"Set family_links.lineage: {slug} in {cdata['rel']}.",
            )

    check_graph_extras(cx)


def check_graph_extras(cx):
    """Edge types that only scripts/graph.py checks: faction allies/enemies,
    route endpoints, species/race relationships, language families, lineage
    allies/rivals, plus dangling refs on those and on item/arc/lineage fields.
    The original reports these as errors; the originals in cmd_validate treat
    comparable refs as warnings, so we use warnings here (see report notes)."""
    R = cx.report

    def dangling(ent, fld, refs, label):
        for r in listify(refs):
            ref = ref_str(r)
            if ref and not cx.resolve(ref):
                R.warn(
                    "dangling-ref",
                    ent,
                    fld,
                    f"{label} '{ent['meta'].get('name', ent['rel'])}': {fld} reference '{ref}' not found",
                    "Create the entity file or correct the slug.",
                )

    def mutual(ent_type, field_name, label, key=None):
        ents = cx.ents(ent_type)
        for slug, ent in ents.items():
            for r in listify(ent["meta"].get(field_name)):
                ref = r.get(key) if (key and isinstance(r, dict)) else r
                res = cx.resolve(ref) if ref_str(ref) else None
                if not res or res[0] != ent_type or res[2] == slug:
                    continue
                other = ents.get(res[2])
                if not other:
                    continue
                back = []
                for rr in listify(other["meta"].get(field_name)):
                    x = rr.get(key) if (key and isinstance(rr, dict)) else rr
                    b = cx.resolve(x) if ref_str(x) else None
                    if b:
                        back.append(b[2])
                if slug not in back:
                    R.warn(
                        "symmetry",
                        ent,
                        field_name,
                        f"{label} '{ent['meta'].get('name', slug)}': {field_name} '{res[1]}' has no reciprocal entry",
                        f"Add '{slug}' to {field_name} in {other['rel']}, or remove it here.",
                    )

    for slug, ent in cx.ents("faction").items():
        meta = ent["meta"]
        dangling(ent, "leader", meta.get("leader"), "Faction")
        dangling(ent, "members", meta.get("members"), "Faction")
        dangling(ent, "headquarters", meta.get("headquarters"), "Faction")
        dangling(ent, "allies", meta.get("allies"), "Faction")
        dangling(ent, "enemies", meta.get("enemies"), "Faction")
    mutual("faction", "allies", "Faction")
    mutual("faction", "enemies", "Faction")
    mutual("species", "relationships", "Species", key="species")
    mutual("race", "relationships", "Race", key="race")
    mutual("lineage", "allied_lineages", "Lineage")
    mutual("lineage", "rival_lineages", "Lineage")

    for slug, ent in cx.ents("character").items():
        meta = ent["meta"]
        for fld in ("species", "race", "arc"):
            dangling(ent, fld, meta.get(fld), "Character")
        fl = meta.get("family_links") if isinstance(meta.get("family_links"), dict) else {}
        for fld in ("father", "mother", "spouse", "children", "siblings", "lineage"):
            dangling(ent, f"family_links.{fld}", fl.get(fld), "Character")
    for slug, ent in cx.ents("item").items():
        for fld in ("owner", "location", "creator_ref", "creator"):
            dangling(ent, fld, ent["meta"].get(fld), "Item")
    for slug, ent in cx.ents("lineage").items():
        for fld in ("founder", "current_head", "members", "seat", "faction", "allied_lineages", "rival_lineages"):
            dangling(ent, fld, ent["meta"].get(fld), "Lineage")
    for slug, ent in cx.ents("arc").items():
        for fld in (
            "protagonists",
            "antagonists",
            "supporting",
            "characters_involved",
            "locations",
            "factions_involved",
        ):
            dangling(ent, fld, ent["meta"].get(fld), "Arc")
    for slug, ent in cx.ents("location").items():
        dangling(ent, "notable_characters", ent["meta"].get("notable_characters"), "Location")
        dangling(ent, "faction", ent["meta"].get("faction"), "Location")
    for slug, ent in cx.ents("magic-system").items():
        for fld in ("practitioners", "famous_practitioners", "places_of_power", "events"):
            dangling(ent, fld, ent["meta"].get(fld), "Magic system")
    for slug, ent in cx.ents("language").items():
        fam = ent["meta"].get("family") if isinstance(ent["meta"].get("family"), dict) else {}
        # language_family: parent <-> child must agree
        p = cx.resolve(fam.get("parent_language")) if fam.get("parent_language") else None
        if p and p[0] == "language":
            pent = cx.ents("language").get(p[2])
            if pent:
                pfam = pent["meta"].get("family") if isinstance(pent["meta"].get("family"), dict) else {}
                if slug not in _slugs(cx, pfam.get("child_languages")):
                    R.warn(
                        "symmetry",
                        ent,
                        "family.parent_language",
                        f"Language '{ent['meta'].get('name', slug)}': parent_language '{p[1]}' does not list it "
                        f"in child_languages",
                        f"Add '{slug}' to family.child_languages in {pent['rel']}.",
                    )
    # route endpoints
    locs = cx.ents("location")
    for slug, ent in locs.items():
        for route in listify(ent["meta"].get("routes")):
            if not isinstance(route, dict):
                continue
            res = cx.resolve(route.get("to") or route.get("destination"))
            if not res or res[0] != "location" or res[2] == slug:
                continue
            other = locs.get(res[2])
            if not other:
                continue
            back = [
                cx.resolve(r.get("to") or r.get("destination"))
                for r in listify(other["meta"].get("routes"))
                if isinstance(r, dict)
            ]
            if slug not in [b[2] for b in back if b]:
                R.warn(
                    "symmetry",
                    ent,
                    "routes",
                    f"Location '{ent['meta'].get('name', slug)}': route to '{res[1]}' has no reciprocal route",
                    f"Add a route to '{slug}' in {other['rel']}.",
                )


# ═════════════════════════════════════════════════════════════════════════════
# Original checks: business rules (validate_business_rules + graph rules)
# ═════════════════════════════════════════════════════════════════════════════


def parse_age(val):
    if val is None or isinstance(val, bool):
        return None
    if isinstance(val, (int, float)):
        return int(val)
    if isinstance(val, str):
        m = re.search(r"\d+", val)
        return int(m.group()) if m else None
    return None


def check_business_rules(cx):
    R = cx.report
    chars, factions = cx.ents("character"), cx.ents("faction")

    # Minimum parent age 16 (error). Covers both children lists and father/mother.
    pairs = {}
    for slug, ent in chars.items():
        fl = ent["meta"].get("family_links") if isinstance(ent["meta"].get("family_links"), dict) else {}
        for c in listify(fl.get("children")):
            r = cx.resolve(c) if c else None
            if r and r[0] == "character":
                pairs.setdefault((slug, r[2]), ent)
        for pf in ("father", "mother"):
            r = cx.resolve(fl.get(pf)) if fl.get(pf) else None
            if r and r[0] == "character":
                pairs.setdefault((r[2], slug), ent)
    for pslug, cslug in sorted(pairs):
        p, c = chars.get(pslug), chars.get(cslug)
        if not p or not c:
            continue
        pa, ca = parse_age(p["meta"].get("age")), parse_age(c["meta"].get("age"))
        if pa is None or ca is None:
            continue
        diff = pa - ca
        if diff < 16:
            R.error(
                "min-parent-age",
                p,
                "family_links.children",
                f"Character '{p['meta'].get('name', pslug)}' (age {pa}): child '{c['meta'].get('name', cslug)}' "
                f"(age {ca}) — age difference {diff} is less than 16",
                "Correct the ages or the parent/child link (parents must be at least 16 years older).",
            )

    # Faction leader
    for slug, ent in factions.items():
        meta = ent["meta"]
        fname = meta.get("name", slug)
        leader = ref_str(meta.get("leader"))
        if not leader:
            R.warn(
                "faction-leader",
                ent,
                "leader",
                f"Faction '{fname}': no leader set",
                "Set leader to a character slug (or 'vacant' if intentionally leaderless).",
            )
            continue
        if leader.lower() in ("vacant", "none"):
            continue
        resolved = cx.resolve(leader)
        if not resolved:
            continue
        if resolved[0] != "character":
            R.error(
                "faction-leader",
                ent,
                "leader",
                f"Faction '{fname}': leader '{leader}' is a {resolved[0]}, not a character",
                "The leader must be a character.",
            )
            continue
        char = chars.get(resolved[2])
        if not char:
            continue
        if char["meta"].get("status") == "dead":
            R.error(
                "faction-leader",
                ent,
                "leader",
                f"Faction '{fname}': leader '{resolved[1]}' has status 'dead'",
                "Name a living leader, or set leader to 'vacant'.",
            )
        # Leader should be a member (new rule from the task brief).
        members = _slugs(cx, [ref_str(m) for m in listify(meta.get("members"))])
        cf = cx.resolve(char["meta"].get("faction")) if char["meta"].get("faction") else None
        if resolved[2] not in members and not (cf and cf[2] == slug):
            R.warn(
                "faction-leader",
                ent,
                "leader",
                f"Faction '{fname}': leader '{resolved[1]}' is not a member of the faction",
                f"Add '{resolved[2]}' to members, or set faction: {slug} on the leader.",
            )


# ═════════════════════════════════════════════════════════════════════════════
# World flags: tech keyword scan of chapter prose
# ═════════════════════════════════════════════════════════════════════════════


def check_tech_keywords(cx):
    R = cx.report
    tech_flags = (cx.config.get("world_flags") or {}).get("technology") or {}
    if not isinstance(tech_flags, dict):
        return
    for slug, ent in cx.ents("chapter").items():
        title = ent["meta"].get("title", slug)
        body = (ent.get("body") or "").lower()
        if not body:
            continue
        for flag_name, keywords in TECH_KEYWORDS.items():
            fv = tech_flags.get(flag_name, {})
            val = fv.get("value") if isinstance(fv, dict) else fv
            if not flag_is_false(val):
                continue
            for kw in keywords:
                for m in re.finditer(r"\b" + re.escape(kw.lower()) + r"\b", body):
                    ctx = body[max(0, m.start() - 20) : min(len(body), m.end() + 20)].replace("\n", " ").strip()
                    R.warn(
                        "world-flag",
                        ent,
                        "body",
                        f"Chapter '{title}': tech anachronism — '{kw}' found but {flag_name} = false. "
                        f"Context: '...{ctx}...'",
                        f"Remove or rephrase the reference, or set world_flags.technology.{flag_name} to true.",
                    )


# ═════════════════════════════════════════════════════════════════════════════
# World flags: magic yes/no gate and magic-system completeness
# ═════════════════════════════════════════════════════════════════════════════

MAGIC_KEYWORDS = [
    "spell",
    "spells",
    "spellcasting",
    "mana",
    "sorcery",
    "sorcerer",
    "sorceress",
    "enchant",
    "enchanted",
    "enchantment",
    "wizard",
    "wizardry",
    "witchcraft",
    "warlock",
    "necromancy",
    "incantation",
    "magic",
    "magical",
    "magically",
]

# Systems of these types are technology in disguise, not magic (see the-lattice).
NON_MAGIC_SYSTEM_TYPES = {"technology", "technological", "tech"}


# Frontmatter keys that hold identifiers or classification, not descriptive text.
MAGIC_SCAN_SKIP_KEYS = {"name", "title", "aliases", "tags", "type", "id", "slug"}


def magic_flags(cx):
    """Return (state, flags) where state is 'absent', 'present' or 'unset'."""
    present = cx.flag("magic", "present")
    prevalence = cx.flag("magic", "prevalence")
    if flag_is_false(present) or (isinstance(prevalence, str) and prevalence.strip().lower() == "none"):
        return "absent"
    if present is True or present == "true":
        return "present"
    return "unset"


def _walk_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from _walk_strings(v)
    elif isinstance(value, (list, tuple)):
        for v in value:
            yield from _walk_strings(v)


def _is_magic_entity(ent):
    return str(ent["meta"].get("type", "")).strip().lower() not in NON_MAGIC_SYSTEM_TYPES


def check_magic_flag(cx):
    R = cx.report
    state = magic_flags(cx)
    if state == "unset":
        return
    systems = cx.ents("magic-system")
    if state == "present":
        hardness = str(cx.flag("magic", "hardness") or "").strip().lower()
        for slug, ent in systems.items():
            m = ent["meta"]
            nm = m.get("name", slug)
            if not _nonempty(m.get("source")):
                R.warn("magic-system", ent, "source", f"Magic system '{nm}' has no source of power.",
                       "Record where the power comes from.")
            has_users = any(_nonempty(m.get(k)) for k in ("practitioners", "users", "heritability"))
            if not has_users:
                R.warn("magic-system", ent, "practitioners",
                       f"Magic system '{nm}' says nothing about who can use it (practitioners/users/heritability).",
                       "Record who can use it and why.")
            if hardness in ("medium", "hard", "scientific"):
                if not _nonempty(m.get("cost")):
                    R.warn("magic-system", ent, "cost",
                           f"Magic system '{nm}' has no cost but world_flags.magic.hardness is {hardness}.",
                           "Add a cost: power without a price breaks conservation.")
                if not any(_nonempty(m.get(k)) for k in ("limitations", "limits", "cannot_do")):
                    R.warn("magic-system", ent, "limitations",
                           f"Magic system '{nm}' has no limits but world_flags.magic.hardness is {hardness}.",
                           "Add limitations or cannot_do.")
        return

    # absent: the world is non-magical
    hint = (
        "World flag magic is false/none: remove the entity, recast it as technology (type: technology), "
        "or change world_flags.magic deliberately and sweep everything written so far."
    )
    for slug, ent in systems.items():
        if _is_magic_entity(ent):
            R.error("magic-flag", ent, "type",
                    f"Magic system '{ent['meta'].get('name', slug)}' exists but world_flags.magic says "
                    "there is no magic.", hint)
    magic_slugs = {s for s, e in systems.items() if _is_magic_entity(e)}
    for etype, bucket in cx.entities.items():
        if etype == "magic-system":
            continue
        for slug, ent in bucket.items():
            meta = ent["meta"]
            for key, val in meta.items():
                is_key = str(key).lower() in ("magic_system", "magic_systems", "magic-system", "magic-systems")
                if is_key and _nonempty(val):
                    R.error("magic-flag", ent, key,
                            f"'{meta.get('name', slug)}' references a magic system but world_flags.magic "
                            "says there is no magic.", hint)
                    continue
                if key == "descriptions":
                    continue
                for text in _walk_strings(val):
                    r = cx.resolve(text) if len(text) < 80 else None
                    if r and r[0] == "magic-system" and r[2] in magic_slugs:
                        R.error("magic-flag", ent, key,
                                f"'{meta.get('name', slug)}' references magic system '{text}' but "
                                "world_flags.magic says there is no magic.", hint)
    # keyword scan of every frontmatter text field
    flags = (cx.config.get("world_flags") or {}).get("magic") or {}
    exceptions = set()
    notes = ""
    if isinstance(flags, dict):
        ex = flags.get("exceptions")
        if isinstance(ex, dict):
            ex = ex.get("value")
        exceptions = {str(x).lower() for x in listify(ex)}
        if isinstance(flags.get("notes"), str):
            notes += " " + flags["notes"].lower()
        for k, v in flags.items():
            if isinstance(v, dict) and isinstance(v.get("notes"), str):
                notes += " " + v["notes"].lower()
    for etype, bucket in cx.entities.items():
        # Traditions are beliefs, not facts about the world: a myth may speak of magic in a
        # world without it. (Structured references to magic-system entities stay errors, above.)
        if etype in ("chapter", "magic-system", "tradition"):
            continue
        for slug, ent in bucket.items():
            # Every text field in the frontmatter, but not the Markdown body (prose may
            # discuss the absence of magic) and not identifiers such as names and tags.
            for key, val in ent["meta"].items():
                if str(key).lower() in MAGIC_SCAN_SKIP_KEYS:
                    continue
                text = " ".join(_walk_strings(val)).lower()
                if not text:
                    continue
                for kw in MAGIC_KEYWORDS:
                    if kw in exceptions or re.search(r"\b" + re.escape(kw) + r"\b", notes):
                        continue
                    m = re.search(r"\b" + re.escape(kw) + r"\b", text)
                    if m:
                        ctx = text[max(0, m.start() - 20) : m.end() + 20].replace("\n", " ").strip()
                        R.warn("magic-flag", ent, str(key),
                               f"'{ent['meta'].get('name', slug)}': magic term '{kw}' in {key} but "
                               f"world_flags.magic says there is no magic. Context: '...{ctx}...'",
                               "Rephrase as technology/natural phenomenon, or list it in "
                               "world_flags.magic.exceptions.")


# ═════════════════════════════════════════════════════════════════════════════
# Driver
# ═════════════════════════════════════════════════════════════════════════════


def validate(project_dir):
    project_dir = Path(project_dir).resolve()
    report = Report(project_dir)
    config_file = project_dir / "project.yaml"
    if not config_file.exists():
        raise FileNotFoundError(f"no project.yaml in {project_dir}")
    config = load_yaml_file(config_file, report, "project.yaml")
    calendar = load_yaml_file(project_dir / "world" / "history" / "calendar.yaml", report, "calendar.yaml")
    entities = collect_entities(project_dir, report)
    cx = Ctx(entities, build_name_index(entities), config, calendar, report)

    check_references(cx)
    check_event_refs(cx)
    check_causality(cx)
    check_traditions(cx)
    check_peoples(cx)
    check_geography(cx)
    check_physical_geography(cx)
    check_event_eras(cx)
    check_symmetry(cx)
    check_business_rules(cx)
    check_tech_keywords(cx)
    check_magic_flag(cx)
    return report, entities


def format_text(report, entities, min_severity):
    issues = [i for i in report.issues if min_severity == "warning" or i["severity"] == "error"]
    n_ent = sum(len(v) for v in entities.values())
    n_err = sum(1 for i in report.issues if i["severity"] == "error")
    n_warn = len(report.issues) - n_err
    lines = [f"Validated {n_ent} entities ({len(entities.get('event', {}))} events) in {report.project_dir}", ""]
    for sev, title in (("error", "ERRORS"), ("warning", "WARNINGS")):
        group = [i for i in issues if i["severity"] == sev]
        if not group:
            continue
        lines.append(f"{title} ({len(group)})")
        for i in sorted(group, key=lambda x: (x["file"], x["field"], x["message"])):
            loc = i["file"] + (f" [{i['field']}]" if i["field"] else "")
            lines.append(f"  {loc or '(project)'}  ({i['check']})")
            lines.append(f"    {i['message']}")
            if i["hint"]:
                lines.append(f"    fix: {i['hint']}")
        lines.append("")
    lines.append(f"{n_err} error(s), {n_warn} warning(s)" if report.issues else "No issues found.")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Validate a WorldBuilder project for internal consistency.")
    ap.add_argument("project", help="project directory (contains project.yaml)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument(
        "--severity",
        choices=("error", "warning"),
        default="warning",
        help="minimum severity to show (default: warning = errors and warnings)",
    )
    args = ap.parse_args(argv)
    try:
        report, entities = validate(args.project)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    n_err = sum(1 for i in report.issues if i["severity"] == "error")
    if args.json:
        shown = [i for i in report.issues if args.severity == "warning" or i["severity"] == "error"]
        shown.sort(key=lambda x: (x["severity"] != "error", x["file"], x["field"], x["message"]))
        print(
            json.dumps(
                {
                    "project": str(report.project_dir),
                    "entities": sum(len(v) for v in entities.values()),
                    "errors": n_err,
                    "warnings": len(report.issues) - n_err,
                    "issues": shown,
                },
                indent=2,
            )
        )
    else:
        print(format_text(report, entities, args.severity))
    return 1 if n_err else 0


if __name__ == "__main__":
    sys.exit(main())
