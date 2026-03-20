#!/usr/bin/env python3
"""
WorldBuilder CLI — A structured worldbuilding and book-writing tool.

Usage:
    python worldbuilder.py init <name> [--genre fantasy|scifi|modern|campaign] [--type novel|series|campaign|game]
    python worldbuilder.py add <entity_type> <name> [--project <path>]
    python worldbuilder.py validate [--project <path>]
    python worldbuilder.py compile [--project <path>] [--format md|html]
    python worldbuilder.py stats [--project <path>]
    python worldbuilder.py timeline [--project <path>] [--era <era>] [--filter <entity>]
    python worldbuilder.py graph [--project <path>]
    python worldbuilder.py query <question> [--project <path>]
    python worldbuilder.py list <entity_type> [--project <path>]
    python worldbuilder.py history <entity_name> [--project <path>]
    python worldbuilder.py crossref <entity_name> [--project <path>]
    python worldbuilder.py flags [--project <path>]
    python worldbuilder.py edit <editor_name> [--chapter <range>] [--project <path>]
    python worldbuilder.py geography [--project <path>]
"""

import argparse
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

import yaml

# Where are the templates?
TOOL_DIR = Path(__file__).parent
SKILL_ROOT = TOOL_DIR.parent
# Support both skill layout (assets/templates) and legacy layout (templates)
if (SKILL_ROOT / "assets" / "templates").exists():
    TEMPLATE_DIR = SKILL_ROOT / "assets" / "templates"
    PRESET_DIR = SKILL_ROOT / "assets" / "presets"
    EDITOR_DIR = SKILL_ROOT / "assets" / "editors"
elif (SKILL_ROOT / "templates").exists():
    TEMPLATE_DIR = SKILL_ROOT / "templates"
    PRESET_DIR = SKILL_ROOT / "presets"
    EDITOR_DIR = SKILL_ROOT / "editors"
else:
    TEMPLATE_DIR = TOOL_DIR.parent / "templates"
    PRESET_DIR = TOOL_DIR.parent / "presets"
    EDITOR_DIR = TOOL_DIR.parent / "editors"

ENTITY_TYPES = [
    "character", "location", "faction", "item", "magic-system", "arc", "event",
    "species", "race", "language", "lineage",
]
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
}


def find_project(start_path=None):
    """Walk up from start_path (or cwd) to find project.yaml."""
    p = Path(start_path) if start_path else Path.cwd()
    for parent in [p] + list(p.parents):
        if (parent / "project.yaml").exists():
            return parent
    return None


def load_project(project_path):
    """Load and return project config."""
    config_file = project_path / "project.yaml"
    with open(config_file, "r") as f:
        return yaml.safe_load(f)


def slugify(name):
    """Convert a name to a filename-safe slug."""
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


# ═══════════════════════════════════════════════════════════════════════════════
# WORLDDATE — in-world calendar date handling
# ═══════════════════════════════════════════════════════════════════════════════

class WorldDate:
    """Represents a date in the world's calendar. Comparable and sortable."""

    def __init__(self, data, calendar_config=None):
        """
        data can be:
          - dict: {year: 1247, month: 3, day: 15, era_prefix: "3A", display: "...", approximate: false}
          - None: represents "unknown date"
        """
        if data is None or data == "" or (isinstance(data, dict) and not data.get("year")):
            self.valid = False
            self.year = 0
            self.month = 0
            self.day = 0
            self.era_prefix = ""
            self.era_sort = 0
            self.display = ""
            self.approximate = False
            return

        self.valid = True
        if isinstance(data, (int, float)):
            # Shorthand: just a year number
            self.year = int(data)
            self.month = 0
            self.day = 0
            self.era_prefix = ""
            self.display = str(self.year)
            self.approximate = False
        elif isinstance(data, dict):
            self.year = int(data.get("year", 0))
            self.month = int(data.get("month", 0))
            self.day = int(data.get("day", 0))
            self.era_prefix = str(data.get("era_prefix", ""))
            self.display = data.get("display", "")
            self.approximate = bool(data.get("approximate", False))
        else:
            # Try to parse as string "year" or "era_prefix year"
            self.valid = False
            self.year = 0
            self.month = 0
            self.day = 0
            self.era_prefix = ""
            self.display = str(data)
            self.approximate = False
            return

        # Resolve era sort order from calendar config
        self.era_sort = 0
        if calendar_config and self.era_prefix:
            for era in calendar_config.get("eras", []):
                if era.get("prefix") == self.era_prefix:
                    self.era_sort = era.get("sort_order", 0)
                    break

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

    def sort_key(self):
        """Return a tuple for chronological sorting."""
        return (self.era_sort, self.year, self.month, self.day)

    def __lt__(self, other):
        if not self.valid or not other.valid:
            return False
        return self.sort_key() < other.sort_key()

    def __le__(self, other):
        if not self.valid or not other.valid:
            return False
        return self.sort_key() <= other.sort_key()

    def __gt__(self, other):
        if not self.valid or not other.valid:
            return False
        return self.sort_key() > other.sort_key()

    def __ge__(self, other):
        if not self.valid or not other.valid:
            return False
        return self.sort_key() >= other.sort_key()

    def __eq__(self, other):
        if not isinstance(other, WorldDate):
            return False
        if not self.valid or not other.valid:
            return False
        return self.sort_key() == other.sort_key()

    def __repr__(self):
        if not self.valid:
            return "WorldDate(unknown)"
        return f"WorldDate({self.display})"


def parse_worlddate(data, calendar_config=None):
    """Parse a worlddate from YAML data."""
    return WorldDate(data, calendar_config)


def get_event_date(meta, calendar_config=None):
    """Extract the primary date from an event's metadata.
    Returns (start_date, end_date) as WorldDate objects.
    For instant events, end_date == start_date."""
    date = parse_worlddate(meta.get("date"), calendar_config)
    start = parse_worlddate(meta.get("start_date"), calendar_config)
    end = parse_worlddate(meta.get("end_date"), calendar_config)

    # Instant event: use 'date'
    if date.valid:
        return date, date
    # Duration event: use start/end
    if start.valid:
        return start, end if end.valid else start
    return WorldDate(None), WorldDate(None)


# ═══════════════════════════════════════════════════════════════════════════════
# ENTITY COLLECTION & PARSING
# ═══════════════════════════════════════════════════════════════════════════════

def parse_frontmatter(filepath):
    """Extract YAML frontmatter from a markdown file."""
    with open(filepath, "r") as f:
        content = f.read()

    if not content.startswith("---"):
        return None, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return None, content

    try:
        meta = yaml.safe_load(parts[1])
        body = parts[2]
        return meta, body
    except yaml.YAMLError:
        return None, content


def collect_entities(project_dir):
    """Collect all entity files and their metadata."""
    entities = {}
    world_dir = project_dir / "world"
    story_dir = project_dir / "story"

    for entity_type, dirname in ENTITY_DIRS.items():
        if entity_type == "arc":
            search_dir = story_dir / "arcs"
        elif entity_type == "event":
            search_dir = world_dir / "events"
        else:
            search_dir = world_dir / dirname

        if not search_dir.exists():
            continue

        entities[entity_type] = {}
        for f in search_dir.glob("*.md"):
            if f.name.startswith("_"):
                continue
            meta, body = parse_frontmatter(f)
            if meta:
                entities[entity_type][f.stem] = {"meta": meta, "body": body, "file": f}

        # Also handle yaml files (arcs, etc.)
        for f in search_dir.glob("*.yaml"):
            if f.name.startswith("_"):
                continue
            with open(f) as fh:
                try:
                    meta = yaml.safe_load(fh)
                    entities.setdefault(entity_type, {})[f.stem] = {"meta": meta, "body": "", "file": f}
                except yaml.YAMLError:
                    pass

    # Chapters
    entities["chapter"] = {}
    chapters_dir = story_dir / "chapters"
    if chapters_dir.exists():
        for f in chapters_dir.glob("*.md"):
            if f.name.startswith("_"):
                continue
            meta, body = parse_frontmatter(f)
            if meta:
                entities["chapter"][f.stem] = {"meta": meta, "body": body, "file": f}

    return entities


def build_name_index(entities):
    """Build a lookup index: slug → (type, name, slug) and lowercase name → same."""
    index = {}
    for etype, ents in entities.items():
        for slug, data in ents.items():
            name = data["meta"].get("name", data["meta"].get("title", slug))
            entry = (etype, name, slug)
            index[slug] = entry
            index[name.lower()] = entry
            # Also index by slugified name
            index[slugify(name)] = entry
    return index


def resolve_ref(ref_str, name_index):
    """Resolve a reference string to (type, name, slug) or None."""
    if not ref_str:
        return None
    # Try exact slug
    if ref_str in name_index:
        return name_index[ref_str]
    # Try slugified
    s = slugify(ref_str)
    if s in name_index:
        return name_index[s]
    # Try lowercase
    if ref_str.lower() in name_index:
        return name_index[ref_str.lower()]
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# TEMPORAL CONTEXT — time-windowed world state for story/campaign generation
# ═══════════════════════════════════════════════════════════════════════════════

def gather_temporal_context(entities, calendar, anchor_type, anchor_value, config):
    """
    Filter world state to a specific time window.

    anchor_type: "event" | "period" | "present"
    anchor_value:
      - for "event": event slug string
      - for "period": dict with keys "era", "start_year", "end_year"
      - for "present": None

    Returns dict with keys:
      anchor_event, time_window, events_before, events_during, events_after,
      active_characters, active_factions, all_locations, all_species, all_races,
      all_languages, magic_systems, items, world_flags, style, calendar, economy
    """
    # Separate entities by type
    characters = entities.get("character", {})
    locations = entities.get("location", {})
    factions = entities.get("faction", {})
    events = entities.get("event", {})
    species = entities.get("species", {})
    races = entities.get("race", {})
    languages = entities.get("language", {})
    items_ents = entities.get("item", {})
    magic_systems = entities.get("magic-system", {})
    lineages = entities.get("lineage", {})
    arcs = entities.get("arc", {})

    # Parse and sort all events chronologically
    dated_events = []
    for slug, data in events.items():
        meta = data["meta"]
        start, end = get_event_date(meta, calendar)
        if start.valid:
            dated_events.append((start, end, slug, data))
    dated_events.sort(key=lambda x: x[0].sort_key())

    # Determine time window
    window_start = None
    window_end = None
    anchor_event = None

    if anchor_type == "event":
        event_data = events.get(anchor_value)
        if event_data:
            anchor_event = event_data
            meta = event_data["meta"]
            ws, we = get_event_date(meta, calendar)
            window_start = ws
            window_end = we
    elif anchor_type == "period":
        era = anchor_value.get("era", "")
        start_year = anchor_value.get("start_year", 0)
        end_year = anchor_value.get("end_year", start_year)
        window_start = WorldDate({"year": start_year, "era_prefix": era}, calendar)
        window_end = WorldDate({"year": end_year, "era_prefix": era}, calendar)
    elif anchor_type == "present":
        if dated_events:
            last_end = dated_events[-1][1]
            window_start = last_end
        else:
            window_start = WorldDate(None)
        window_end = None  # open-ended

    # Partition events into before/during/after
    events_before = []
    events_during = []
    events_after = []
    for start, end, slug, data in dated_events:
        if window_start and window_start.valid and end.valid and end < window_start:
            events_before.append((start, end, slug, data))
        elif window_end and window_end.valid and start.valid and start > window_end:
            events_after.append((start, end, slug, data))
        elif anchor_type == "present" and window_start and window_start.valid:
            if start.valid and start < window_start:
                events_before.append((start, end, slug, data))
            else:
                events_during.append((start, end, slug, data))
        else:
            events_during.append((start, end, slug, data))

    # Build sets of death/birth events for character filtering
    death_events = {}  # char slug -> earliest death date
    birth_events = {}  # char slug -> birth date
    for start, end, slug, data in dated_events:
        meta = data["meta"]
        etype = meta.get("type", "")
        participants = meta.get("participants", []) or []
        primary_chars = meta.get("primary_characters", []) or []
        all_char_refs = list(primary_chars)
        for p in participants:
            if isinstance(p, dict):
                all_char_refs.append(p.get("entity", ""))
            else:
                all_char_refs.append(str(p))
        for cref in all_char_refs:
            cs = slugify(str(cref)) if cref else ""
            if not cs:
                continue
            if etype == "death":
                if cs not in death_events or start < death_events[cs]:
                    death_events[cs] = start
            elif etype == "birth":
                if cs not in birth_events or start < birth_events[cs]:
                    birth_events[cs] = start

    # Filter characters
    active_characters = {}
    for cslug, cdata in characters.items():
        include = True
        if cslug in death_events and window_start and window_start.valid:
            if death_events[cslug] < window_start:
                include = False
        if cslug in birth_events and window_end and window_end.valid:
            if birth_events[cslug] > window_end:
                include = False
        if include:
            active_characters[cslug] = cdata

    # Filter factions
    active_factions = {}
    for fslug, fdata in factions.items():
        meta = fdata["meta"]
        include = True
        diss = meta.get("dissolution_date")
        if diss and window_start and window_start.valid:
            diss_date = parse_worlddate(diss, calendar)
            if diss_date.valid and diss_date < window_start:
                include = False
        found = meta.get("founding_date")
        if found and window_end and window_end.valid:
            found_date = parse_worlddate(found, calendar)
            if found_date.valid and found_date > window_end:
                include = False
        if include:
            active_factions[fslug] = fdata

    # Load economy
    project_dir = None
    for etype_key in entities:
        for slug_key, edata in entities[etype_key].items():
            if "file" in edata:
                project_dir = edata["file"].parent
                while project_dir and not (project_dir / "project.yaml").exists():
                    project_dir = project_dir.parent
                break
        if project_dir:
            break
    economy = {}
    if project_dir:
        eco_file = project_dir / "world" / "economy.yaml"
        if eco_file.exists():
            with open(eco_file) as f:
                economy = yaml.safe_load(f) or {}

    return {
        "anchor_event": anchor_event,
        "time_window": (window_start, window_end),
        "events_before": events_before,
        "events_during": events_during,
        "events_after": events_after,
        "active_characters": active_characters,
        "active_factions": active_factions,
        "all_locations": locations,
        "all_species": species,
        "all_races": races,
        "all_languages": languages,
        "magic_systems": magic_systems,
        "items": items_ents,
        "world_flags": config.get("world_flags", {}),
        "style": config.get("style", {}),
        "calendar": calendar,
        "economy": economy,
    }


def format_world_context_block(ctx):
    """Format temporal context into prompt sections. Returns list of lines."""
    lines = []

    # 1. World Rules
    world_flags = ctx.get("world_flags", {})
    if world_flags:
        lines.append("## World Rules (MUST follow)\n")
        for category, flags in world_flags.items():
            if isinstance(flags, dict):
                for flag_name, flag_val in flags.items():
                    if flag_val is False:
                        lines.append(f"- NO {flag_name}")
                    elif flag_val is True:
                        lines.append(f"- HAS {flag_name}")
                    elif isinstance(flag_val, str) and flag_val not in ("n/a", ""):
                        lines.append(f"- {flag_name}: {flag_val}")
        lines.append("")

    # 2. Calendar & Eras
    calendar = ctx.get("calendar", {})
    eras = calendar.get("eras", [])
    if eras:
        lines.append("## Calendar & Eras\n")
        lines.append(f"Calendar: {calendar.get('name', 'unknown')}")
        for era in eras:
            end_yr = era.get("end_year", "present")
            lines.append(f"- {era.get('prefix', '?')}: {era.get('name', '?')} (year {era.get('start_year', '?')} — {end_yr})")
            desc = era.get("description", "")
            if desc:
                lines.append(f"  {desc}")
        lines.append("")

    # 3. Species
    species = ctx.get("all_species", {})
    if species:
        lines.append(f"## Species ({len(species)})\n")
        for slug, data in species.items():
            m = data["meta"]
            bio = m.get("biology", {}) or {}
            culture = m.get("culture", {}) or {}
            lines.append(f"### {m.get('name', slug)}")
            lines.append(f"Sentience: {m.get('sentience', '?')}")
            if bio:
                lines.append(f"Biology: {bio.get('classification', '?')}, size {bio.get('size', '?')}, lifespan {bio.get('lifespan', '?')}")
            if culture:
                lines.append(f"Culture: {culture.get('social_structure', '?')}, tech {culture.get('technology_level', '?')}")
            lines.append("")

    # 4. Races
    races = ctx.get("all_races", {})
    if races:
        lines.append(f"## Races ({len(races)})\n")
        for slug, data in races.items():
            m = data["meta"]
            var = m.get("variation", {}) or {}
            lines.append(f"- **{m.get('name', slug)}** (species: {m.get('species', '?')})")
            traits = var.get("distinguishing_traits", "")
            if traits:
                lines.append(f"  Traits: {traits}")
        lines.append("")

    # 5. Languages
    languages = ctx.get("all_languages", {})
    if languages:
        lines.append(f"## Languages ({len(languages)})\n")
        for slug, data in languages.items():
            m = data["meta"]
            speakers = m.get("speakers", {}) or {}
            script = m.get("script", {}) or {}
            lines.append(f"- **{m.get('name', slug)}**: status {m.get('status', '?')}, speakers: {speakers.get('total_speakers', '?')}, script: {script.get('name', '?')}")
        lines.append("")

    # 6. Active Factions
    factions = ctx.get("active_factions", {})
    if factions:
        lines.append(f"## Active Factions ({len(factions)})\n")
        for slug, data in factions.items():
            m = data["meta"]
            lines.append(f"### {m.get('name', slug)}")
            lines.append(f"Type: {m.get('type', '?')}, Status: {m.get('status', '?')}")
            if m.get("leader"):
                lines.append(f"Leader: {m['leader']}")
            if m.get("headquarters"):
                lines.append(f"HQ: {m['headquarters']}")
            goals = m.get("goals", [])
            if goals:
                lines.append(f"Goals: {', '.join(str(g) for g in goals[:5])}")
            heraldry = m.get("heraldry", {}) or {}
            if heraldry.get("motto"):
                lines.append(f"Motto: \"{heraldry['motto']}\"")
            lines.append("")

    # 7. Active Locations — spatial hierarchy
    locations = ctx.get("all_locations", {})
    if locations:
        lines.append(f"## Locations ({len(locations)})\n")
        # Build parent-child tree
        children = {}
        roots = []
        for slug, data in locations.items():
            parent = data["meta"].get("parent", "")
            parent_slug = slugify(str(parent)) if parent else ""
            if parent_slug and parent_slug in locations:
                children.setdefault(parent_slug, []).append(slug)
            else:
                roots.append(slug)

        def _format_loc(slug, indent=0):
            data = locations[slug]
            m = data["meta"]
            prefix = "  " * indent + "- "
            lines.append(f"{prefix}**{m.get('name', slug)}** [{m.get('type', '?')}] pop: {m.get('population', '?')}")
            for child in sorted(children.get(slug, [])):
                _format_loc(child, indent + 1)

        for root in sorted(roots):
            _format_loc(root)
        lines.append("")

    # 8. Active Characters
    characters = ctx.get("active_characters", {})
    if characters:
        lines.append(f"## Active Characters ({len(characters)})\n")
        for slug, data in characters.items():
            m = data["meta"]
            lines.append(f"### {m.get('name', slug)}")
            parts = []
            if m.get("role"):
                parts.append(f"Role: {m['role']}")
            if m.get("species"):
                parts.append(f"Species: {m['species']}")
            if m.get("race"):
                parts.append(f"Race: {m['race']}")
            if m.get("faction"):
                parts.append(f"Faction: {m['faction']}")
            if m.get("location"):
                parts.append(f"Location: {m['location']}")
            if parts:
                lines.append(", ".join(parts))
            traits = m.get("traits", [])
            if traits:
                lines.append(f"Traits: {', '.join(str(t) for t in traits)}")
            descs = m.get("descriptions", {}) or {}
            machine = descs.get("machine", {}) or {}
            if machine:
                for key, val in machine.items():
                    if val:
                        lines.append(f"**{key}**: {val}")
            lines.append("")

    # 9. Items
    items = ctx.get("items", {})
    if items:
        lines.append(f"## Items ({len(items)})\n")
        for slug, data in items.items():
            m = data["meta"]
            lines.append(f"- **{m.get('name', slug)}** [{m.get('type', '?')}]: significance {m.get('significance', '?')}, owner: {m.get('owner', '?')}, location: {m.get('location', '?')}")
        lines.append("")

    # 10. Magic/Tech Systems
    msys = ctx.get("magic_systems", {})
    if msys:
        lines.append(f"## Magic/Tech Systems ({len(msys)})\n")
        for slug, data in msys.items():
            m = data["meta"]
            lines.append(f"### {m.get('name', slug)}")
            lines.append(f"Type: {m.get('type', '?')}")
            rules = m.get("rules", [])
            if rules:
                lines.append(f"Rules: {'; '.join(str(r) for r in rules[:5])}")
            lines.append("")

    # 11. Economy
    economy = ctx.get("economy", {})
    if economy:
        lines.append("## Economy\n")
        currencies = economy.get("currencies", [])
        if currencies:
            lines.append("Currencies:")
            for c in currencies:
                if isinstance(c, dict):
                    lines.append(f"- {c.get('name', '?')}: {c.get('description', '')}")
                else:
                    lines.append(f"- {c}")
        resources = economy.get("resources", [])
        if resources:
            lines.append("Key Resources:")
            for r in resources[:10]:
                if isinstance(r, dict):
                    lines.append(f"- {r.get('name', '?')} [{r.get('category', '?')}]: rarity {r.get('rarity', '?')}")
                else:
                    lines.append(f"- {r}")
        trade_routes = economy.get("trade_routes", [])
        if trade_routes:
            lines.append("Trade Routes:")
            for tr in trade_routes[:10]:
                if isinstance(tr, dict):
                    lines.append(f"- {tr.get('name', '?')}: {tr.get('endpoints', '?')}")
                else:
                    lines.append(f"- {tr}")
        lines.append("")

    # 12. Timeline Context
    events_before = ctx.get("events_before", [])
    events_during = ctx.get("events_during", [])
    events_after = ctx.get("events_after", [])

    lines.append("## Timeline Context\n")

    if events_before:
        lines.append("### What Came Before\n")
        for start, end, slug, data in events_before[-15:]:
            m = data["meta"]
            lines.append(f"- [{start.display}] **{m.get('name', slug)}** — {m.get('type', '?')}")
            descs = m.get("descriptions", {}) or {}
            machine = descs.get("machine", {}) or {}
            scene = machine.get("scene", "")
            if scene:
                lines.append(f"  {scene[:120]}...")
        lines.append("")

    if events_during:
        lines.append("### What Is Happening Now\n")
        for start, end, slug, data in events_during:
            m = data["meta"]
            lines.append(f"#### [{start.display}] {m.get('name', slug)}")
            lines.append(f"Type: {m.get('type', '?')}, Significance: {m.get('significance', '?')}, Scope: {m.get('scope', '?')}")
            descs = m.get("descriptions", {}) or {}
            machine = descs.get("machine", {}) or {}
            scene = machine.get("scene", "")
            if scene:
                lines.append(f"Scene: {scene}")
            body = data.get("body", "").strip()
            if body:
                lines.append(f"\n{body}\n")
        lines.append("")

    if events_after:
        lines.append("### What Comes After (for dramatic irony)\n")
        for start, end, slug, data in events_after[:10]:
            m = data["meta"]
            lines.append(f"- [{start.display}] **{m.get('name', slug)}** — {m.get('type', '?')}")
            descs = m.get("descriptions", {}) or {}
            machine = descs.get("machine", {}) or {}
            scene = machine.get("scene", "")
            if scene:
                lines.append(f"  {scene[:120]}...")
        lines.append("")

    return lines


# ═══════════════════════════════════════════════════════════════════════════════
# INIT
# ═══════════════════════════════════════════════════════════════════════════════

def cmd_init(args):
    """Initialize a new WorldBuilder project."""
    name = args.name
    genre = args.genre or "fantasy"
    proj_type = args.type or "novel"
    slug = slugify(name)

    # Create projects under worlds/ subdirectory by default
    repo_root = Path(__file__).resolve().parent.parent
    worlds_dir = repo_root / "worlds"
    worlds_dir.mkdir(exist_ok=True)
    project_dir = worlds_dir / slug
    if project_dir.exists():
        print(f"Error: Directory 'worlds/{slug}' already exists.")
        sys.exit(1)

    # Create directory structure
    dirs = [
        "world/characters",
        "world/locations",
        "world/factions",
        "world/items",
        "world/magic-systems",
        "world/events",
        "world/history",
        "world/species",
        "world/races",
        "world/languages",
        "world/lineages",
        "story/arcs",
        "story/chapters",
        "story/notes",
        "output",
    ]
    if proj_type == "series":
        dirs.append("series")
    if proj_type == "campaign":
        dirs.extend(["campaign/sessions", "campaign/encounters", "campaign/quests"])

    for d in dirs:
        (project_dir / d).mkdir(parents=True, exist_ok=True)

    # Copy schemas into world dirs
    for entity, dirname in ENTITY_DIRS.items():
        if entity == "arc":
            continue
        schema_src = TEMPLATE_DIR / dirname / "_schema.yaml"
        if schema_src.exists():
            shutil.copy2(schema_src, project_dir / "world" / dirname / "_schema.yaml")

    # Create project.yaml from template
    template_file = TEMPLATE_DIR / "project_template.yaml"
    with open(template_file, "r") as f:
        content = f.read()

    content = content.replace("{{TITLE}}", name)
    content = content.replace("genre: fantasy", f"genre: {genre}")
    content = content.replace("type: novel", f"type: {proj_type}")
    content = content.replace("preset: fantasy", f"preset: {genre}")
    content = content.replace('created: ""', f'created: "{datetime.now().isoformat()}"')
    content = content.replace('last_modified: ""', f'last_modified: "{datetime.now().isoformat()}"')

    with open(project_dir / "project.yaml", "w") as f:
        f.write(content)

    # Create world overview
    with open(project_dir / "world" / "overview.md", "w") as f:
        f.write(f"# {name} — World Overview\n\n")
        f.write(f"**Genre:** {genre}\n\n")
        f.write("## Summary\n\n\n")
        f.write("## Tone & Themes\n\n\n")
        f.write("## Core Conceits\n<!-- What makes this world unique? What rules does it follow? -->\n\n\n")
        f.write("## Key Conflicts\n\n\n")

    # Create world rules
    with open(project_dir / "world" / "rules.md", "w") as f:
        f.write(f"# {name} — World Rules\n\n")
        f.write("## Hard Rules\n<!-- These MUST be consistent. Never break these. -->\n\n\n")
        f.write("## Soft Rules\n<!-- Generally true, but can be bent for story purposes. -->\n\n\n")
        f.write("## Genre Conventions\n<!-- What genre expectations are we following or subverting? -->\n\n\n")

    # Create story outline
    with open(project_dir / "story" / "outline.yaml", "w") as f:
        outline = {
            "title": name,
            "structure": "three-act",
            "acts": [
                {"name": "Act 1 — Setup", "chapters": [], "summary": ""},
                {"name": "Act 2 — Confrontation", "chapters": [], "summary": ""},
                {"name": "Act 3 — Resolution", "chapters": [], "summary": ""},
            ],
        }
        yaml.dump(outline, f, default_flow_style=False, sort_keys=False)

    # Create calendar config (replaces old timeline.yaml)
    calendar = {
        "name": "",
        "eras": [
            {"name": "First Era", "prefix": "1E", "sort_order": 1, "start_year": 1, "end_year": None, "description": ""}
        ],
        "months": [],
        "days_per_year": 365,
        "date_format": "{era} {year}",
        "week": [],
    }
    with open(project_dir / "world" / "history" / "calendar.yaml", "w") as f:
        f.write("# World Calendar Definition\n")
        f.write("# Edit this to define your world's eras, months, and date format.\n")
        f.write("# Events reference dates using this calendar.\n\n")
        yaml.dump(calendar, f, default_flow_style=False, sort_keys=False)

    # Series metadata if needed
    if proj_type == "series":
        with open(project_dir / "series" / "series.yaml", "w") as f:
            series_meta = {
                "name": name,
                "books": [{"number": 1, "title": "", "status": "in-progress"}],
                "overarching_arcs": [],
                "cliffhangers": [],
                "recurring_themes": [],
            }
            yaml.dump(series_meta, f, default_flow_style=False, sort_keys=False)

    print(f"✓ Created project '{name}' at worlds/{slug}/")
    print(f"  Genre: {genre} | Type: {proj_type}")
    print(f"  Next: cd {slug} && python {TOOL_DIR}/worldbuilder.py add character 'Your Hero'")


# ═══════════════════════════════════════════════════════════════════════════════
# ADD
# ═══════════════════════════════════════════════════════════════════════════════

def cmd_add(args):
    """Add a new entity to the project."""
    entity_type = args.entity_type
    name = args.name

    if entity_type not in ENTITY_TYPES:
        print(f"Error: Unknown entity type '{entity_type}'. Choose from: {', '.join(ENTITY_TYPES)}")
        sys.exit(1)

    project_dir = find_project(args.project)
    if not project_dir:
        print("Error: No project.yaml found. Run 'init' first or specify --project.")
        sys.exit(1)

    # Determine target directory
    if entity_type == "arc":
        target_dir = project_dir / "story" / "arcs"
    elif entity_type == "event":
        target_dir = project_dir / "world" / "events"
    else:
        target_dir = project_dir / "world" / ENTITY_DIRS[entity_type]

    target_dir.mkdir(parents=True, exist_ok=True)
    slug = slugify(name)

    # Choose template
    if entity_type == "arc":
        template_file = TEMPLATE_DIR / "arcs" / "_template.yaml"
        output_file = target_dir / f"{slug}.yaml"
    else:
        template_file = TEMPLATE_DIR / ENTITY_DIRS[entity_type] / "_template.md"
        output_file = target_dir / f"{slug}.md"

    if output_file.exists():
        print(f"Error: {output_file.name} already exists.")
        sys.exit(1)

    with open(template_file, "r") as f:
        content = f.read()

    content = content.replace("{{NAME}}", name)
    if "{{TITLE}}" in content:
        content = content.replace("{{TITLE}}", name)

    with open(output_file, "w") as f:
        f.write(content)

    print(f"✓ Created {entity_type}: {output_file.relative_to(project_dir)}")


def cmd_add_chapter(project_dir, name, number=None):
    """Add a chapter (special case of add)."""
    chapters_dir = project_dir / "story" / "chapters"
    chapters_dir.mkdir(parents=True, exist_ok=True)

    if number is None:
        existing = list(chapters_dir.glob("*.md"))
        existing = [f for f in existing if not f.name.startswith("_")]
        number = len(existing) + 1

    slug = f"ch-{number:03d}-{slugify(name)}"
    output_file = chapters_dir / f"{slug}.md"

    template_file = TEMPLATE_DIR / "chapters" / "_template.md"
    with open(template_file, "r") as f:
        content = f.read()

    content = content.replace("{{TITLE}}", name)
    content = content.replace("number: 1", f"number: {number}")

    with open(output_file, "w") as f:
        f.write(content)

    print(f"✓ Created chapter {number}: {output_file.relative_to(project_dir)}")


# ═══════════════════════════════════════════════════════════════════════════════
# VALIDATE — with temporal consistency checks
# ═══════════════════════════════════════════════════════════════════════════════

def load_calendar(project_dir):
    """Load calendar config from project."""
    cal_file = project_dir / "world" / "history" / "calendar.yaml"
    if cal_file.exists():
        with open(cal_file) as f:
            return yaml.safe_load(f) or {}
    return {}


def cmd_validate(args):
    """Validate project consistency — references, temporal logic, cross-refs."""
    project_dir = find_project(args.project)
    if not project_dir:
        print("Error: No project.yaml found.")
        sys.exit(1)

    config = load_project(project_dir)
    entities = collect_entities(project_dir)
    calendar = load_calendar(project_dir)
    name_index = build_name_index(entities)
    issues = []
    warnings = []

    # ── Reference validation ──────────────────────────────────────────────────

    # Check character references
    for slug, data in entities.get("character", {}).items():
        meta = data["meta"]
        name = meta.get("name", slug)

        for rel in meta.get("relationships", []) or []:
            if isinstance(rel, dict):
                target = rel.get("target", "")
                if target and not resolve_ref(target, name_index):
                    issues.append(f"Character '{name}': relationship target '{target}' not found")

        loc = meta.get("location", "")
        if loc and not resolve_ref(loc, name_index):
            warnings.append(f"Character '{name}': location '{loc}' not found")

        faction = meta.get("faction", "")
        if faction and not resolve_ref(faction, name_index):
            warnings.append(f"Character '{name}': faction '{faction}' not found")

    # Check for dead characters without death info
    for slug, data in entities.get("character", {}).items():
        meta = data["meta"]
        if meta.get("status") == "dead" and not meta.get("last_appearance"):
            warnings.append(f"Character '{meta.get('name', slug)}': status is 'dead' but last_appearance not set")

    # Check chapter references
    for slug, data in entities.get("chapter", {}).items():
        meta = data["meta"]
        title = meta.get("title", slug)

        pov = meta.get("pov", "")
        if pov and not resolve_ref(pov, name_index):
            issues.append(f"Chapter '{title}': POV character '{pov}' not found")

        for char in meta.get("characters_present", []) or []:
            if not resolve_ref(char, name_index):
                warnings.append(f"Chapter '{title}': character '{char}' not found")

    # Check location parent references
    for slug, data in entities.get("location", {}).items():
        meta = data["meta"]
        parent = meta.get("parent", "")
        if parent and not resolve_ref(parent, name_index):
            warnings.append(f"Location '{meta.get('name', slug)}': parent '{parent}' not found")

    # ── Event validation ──────────────────────────────────────────────────────

    events = entities.get("event", {})
    for slug, data in events.items():
        meta = data["meta"]
        name = meta.get("name", slug)
        evt_type = meta.get("type", "milestone")

        # Check all cross-references in events
        for participant in meta.get("participants", []) or []:
            if isinstance(participant, dict):
                ref = participant.get("entity", "")
                if ref and not resolve_ref(ref, name_index):
                    issues.append(f"Event '{name}': participant '{ref}' not found")
            elif isinstance(participant, str) and participant:
                if not resolve_ref(participant, name_index):
                    issues.append(f"Event '{name}': participant '{participant}' not found")

        for loc_ref in meta.get("locations", []) or []:
            if loc_ref and not resolve_ref(loc_ref, name_index):
                warnings.append(f"Event '{name}': location '{loc_ref}' not found")

        for org in meta.get("organizations", []) or []:
            if isinstance(org, dict):
                ref = org.get("entity", "")
                if ref and not resolve_ref(ref, name_index):
                    warnings.append(f"Event '{name}': organization '{ref}' not found")
            elif isinstance(org, str) and org:
                if not resolve_ref(org, name_index):
                    warnings.append(f"Event '{name}': organization '{org}' not found")

        for item_ref in meta.get("items_involved", []) or []:
            if item_ref and not resolve_ref(item_ref, name_index):
                warnings.append(f"Event '{name}': item '{item_ref}' not found")

        # Check causality references (must be other events)
        for caused in meta.get("caused_by", []) or []:
            if caused:
                resolved = resolve_ref(caused, name_index)
                if not resolved:
                    warnings.append(f"Event '{name}': caused_by '{caused}' not found")
                elif resolved[0] != "event":
                    issues.append(f"Event '{name}': caused_by '{caused}' is a {resolved[0]}, not an event")

        for leads in meta.get("leads_to", []) or []:
            if leads:
                resolved = resolve_ref(leads, name_index)
                if not resolved:
                    warnings.append(f"Event '{name}': leads_to '{leads}' not found")
                elif resolved[0] != "event":
                    issues.append(f"Event '{name}': leads_to '{leads}' is a {resolved[0]}, not an event")

        # ── Temporal consistency ──────────────────────────────────────────────
        start, end = get_event_date(meta, calendar)

        # Duration event: end must be after start
        if start.valid and end.valid and end < start:
            issues.append(f"Event '{name}': end_date ({end.display}) is before start_date ({start.display})")

        # Check causality is chronological
        for caused_slug in meta.get("caused_by", []) or []:
            resolved = resolve_ref(caused_slug, name_index)
            if resolved and resolved[0] == "event":
                cause_data = events.get(resolved[2])
                if cause_data:
                    cause_start, _ = get_event_date(cause_data["meta"], calendar)
                    if cause_start.valid and start.valid and cause_start > start:
                        issues.append(
                            f"Event '{name}' ({start.display}): caused_by '{cause_data['meta'].get('name', caused_slug)}' "
                            f"({cause_start.display}) which happens AFTER it"
                        )

        # Death event: check person status consistency
        if evt_type == "death":
            person_ref = meta.get("person") or ""
            # Also check extra_fields patterns
            for p in meta.get("participants", []) or []:
                if isinstance(p, dict) and p.get("role", "").lower() in ("deceased", "victim", "died"):
                    person_ref = person_ref or p.get("entity", "")
            if person_ref:
                resolved = resolve_ref(person_ref, name_index)
                if resolved and resolved[0] == "character":
                    char_data = entities.get("character", {}).get(resolved[2])
                    if char_data and char_data["meta"].get("status") != "dead":
                        warnings.append(
                            f"Event '{name}': death event for '{resolved[1]}' but character status is "
                            f"'{char_data['meta'].get('status', '?')}', not 'dead'"
                        )

        # Birth event: check character exists
        if evt_type == "birth":
            person_ref = meta.get("person") or ""
            if person_ref:
                resolved = resolve_ref(person_ref, name_index)
                if resolved and resolved[0] == "character":
                    char_data = entities.get("character", {}).get(resolved[2])
                    if char_data:
                        # Check birth is before death
                        char_death_events = [
                            e for e in events.values()
                            if e["meta"].get("type") == "death"
                            and resolve_ref(e["meta"].get("person", ""), name_index)
                            and resolve_ref(e["meta"].get("person", ""), name_index)[2] == resolved[2]
                        ]
                        for death_evt in char_death_events:
                            death_start, _ = get_event_date(death_evt["meta"], calendar)
                            if start.valid and death_start.valid and start > death_start:
                                issues.append(
                                    f"Character '{resolved[1]}': birth ({start.display}) is after "
                                    f"death ({death_start.display})"
                                )

    # ── Cross-reference symmetry checks ───────────────────────────────────────

    # Check that causality chains are bidirectional (warn if not)
    for slug, data in events.items():
        meta = data["meta"]
        name = meta.get("name", slug)
        for leads in meta.get("leads_to", []) or []:
            resolved = resolve_ref(leads, name_index)
            if resolved and resolved[0] == "event":
                target_data = events.get(resolved[2])
                if target_data:
                    target_causes = target_data["meta"].get("caused_by", []) or []
                    target_cause_slugs = [slugify(c) if isinstance(c, str) else c for c in target_causes]
                    if slug not in target_cause_slugs and slugify(name) not in target_cause_slugs:
                        warnings.append(
                            f"Event '{name}' leads_to '{resolved[1]}', but that event's "
                            f"caused_by doesn't reference back"
                        )

    # ── Species / Race / Language validation ──────────────────────────────────
    validate_peoples(entities, name_index, config, issues, warnings)

    # ── Geography / route validation ─────────────────────────────────────────
    validate_geography(entities, name_index, config, issues, warnings)

    # ── Bidirectional reference symmetry ──────────────────────────────────────
    validate_bidirectional_refs(entities, name_index, issues, warnings)

    # ── Business rules ────────────────────────────────────────────────────────
    validate_business_rules(entities, name_index, calendar, issues, warnings)

    # ── World Flags validation (tech keyword scanning) ──────────────────────
    world_flags = config.get("world_flags", {})
    tech_flags = world_flags.get("technology", {})

    # Load tech_keywords from worldrules editor persona
    worldrules_file = EDITOR_DIR / "worldrules.yaml"
    tech_keywords = {}
    if worldrules_file.exists():
        with open(worldrules_file) as f:
            wr = yaml.safe_load(f) or {}
            tech_keywords = wr.get("tech_keywords", {})

    # Scan chapter prose for tech anachronisms
    for slug, data in entities.get("chapter", {}).items():
        ch_title = data["meta"].get("title", slug)
        body = data.get("body", "").lower()
        if not body:
            continue

        for flag_name, keywords in tech_keywords.items():
            # Check if this tech flag is explicitly false
            flag_val = tech_flags.get(flag_name, {})
            if isinstance(flag_val, dict):
                val = flag_val.get("value")
            else:
                val = flag_val

            if val is False or val == "false" or val == "none":
                for kw in keywords:
                    pattern = r'\b' + re.escape(kw.lower()) + r'\b'
                    matches = list(re.finditer(pattern, body))
                    for m in matches:
                        # Get surrounding context (40 chars)
                        start = max(0, m.start() - 20)
                        end = min(len(body), m.end() + 20)
                        context = body[start:end].replace("\n", " ").strip()
                        warnings.append(
                            f"Chapter '{ch_title}': tech anachronism — '{kw}' found "
                            f"but {flag_name} = false. Context: '...{context}...'"
                        )

    # ── Report ────────────────────────────────────────────────────────────────
    event_count = len(events)
    print(f"\nValidated {sum(len(v) for v in entities.values())} entities ({event_count} events)")

    if not issues and not warnings:
        print("✓ No issues found.")
    else:
        if issues:
            print(f"\n✗ {len(issues)} error(s):")
            for i in issues:
                print(f"  ERROR: {i}")
        if warnings:
            print(f"\n⚠ {len(warnings)} warning(s):")
            for w in warnings:
                print(f"  WARN:  {w}")

    # ── Auto-fix ─────────────────────────────────────────────────────────────
    if not getattr(args, 'no_fix', False) and (issues or warnings):
        from graph import WorldGraph
        graph = WorldGraph.from_entities(entities, name_index, slugify_fn=slugify)
        fixes = graph.auto_fix_issues(entities, project_dir)
        if fixes:
            print(f"\n🔧 Auto-fixed {len(fixes)} issue(s):")
            for fix in fixes:
                print(f"  ✓ {fix}")

    return len(issues)


# ═══════════════════════════════════════════════════════════════════════════════
# FIX — standalone auto-fix command
# ═══════════════════════════════════════════════════════════════════════════════


def cmd_fix(args):
    """Auto-fix detectable consistency issues."""
    project_dir = find_project(args.project)
    if not project_dir:
        print("Error: No project found.")
        sys.exit(1)

    config = load_project(project_dir)
    entities = collect_entities(project_dir)
    calendar = load_calendar(project_dir)
    name_index = build_name_index(entities)

    # Import graph
    from graph import WorldGraph

    graph = WorldGraph.from_entities(entities, name_index, slugify_fn=slugify)
    fixes = graph.auto_fix_issues(entities, project_dir)

    if fixes:
        print(f"\n🔧 Applied {len(fixes)} fix(es):\n")
        for fix in fixes:
            print(f"  ✓ {fix}")

        # Re-validate to confirm
        print(f"\n{'=' * 60}")
        print("Re-validating after fixes...\n")
        # Re-collect entities after fixes
        entities = collect_entities(project_dir)
        name_index = build_name_index(entities)
        graph2 = WorldGraph.from_entities(entities, name_index, slugify_fn=slugify)
        remaining = (graph2.check_dangling_references() +
                     graph2.check_bidirectional_symmetry() +
                     graph2.check_business_rules())
        if remaining:
            print(f"⚠ {len(remaining)} issue(s) remain (not auto-fixable):")
            for issue in remaining:
                print(f"  {issue.severity.upper()}: {issue.message}")
        else:
            print("✓ All issues resolved!")
    else:
        print("✓ No fixable issues found.")


# ═══════════════════════════════════════════════════════════════════════════════
# COMPILE
# ═══════════════════════════════════════════════════════════════════════════════

def cmd_compile(args):
    """Compile chapters into a manuscript."""
    project_dir = find_project(args.project)
    if not project_dir:
        print("Error: No project.yaml found.")
        sys.exit(1)

    config = load_project(project_dir)
    chapters_dir = project_dir / "story" / "chapters"
    output_dir = project_dir / "output"
    output_dir.mkdir(exist_ok=True)

    chapters = []
    for f in chapters_dir.glob("*.md"):
        if f.name.startswith("_"):
            continue
        meta, body = parse_frontmatter(f)
        if meta:
            chapters.append({"meta": meta, "body": body, "file": f})

    chapters.sort(key=lambda c: (c["meta"].get("book", 1), c["meta"].get("number", 0)))

    if not chapters:
        print("No chapters found to compile.")
        return

    title = config.get("title", "Untitled")
    author = config.get("author", "")
    lines = [f"# {title}\n"]
    if author:
        lines.append(f"*by {author}*\n")
    lines.append("---\n")

    total_words = 0
    for ch in chapters:
        meta = ch["meta"]
        ch_title = meta.get("title", "Untitled Chapter")
        ch_num = meta.get("number", "?")
        lines.append(f"\n## Chapter {ch_num}: {ch_title}\n")
        body = ch["body"].strip()
        lines.append(body + "\n")
        total_words += len(body.split())

    manuscript = "\n".join(lines)

    md_path = output_dir / "manuscript.md"
    with open(md_path, "w") as f:
        f.write(manuscript)
    print(f"✓ Compiled {len(chapters)} chapters → {md_path.relative_to(project_dir)}")
    print(f"  Total words: {total_words:,}")

    fmt = args.format or "md"
    if fmt == "html" or fmt == "all":
        html = markdown_to_html(manuscript, title, author)
        html_path = output_dir / "manuscript.html"
        with open(html_path, "w") as f:
            f.write(html)
        print(f"✓ HTML version → {html_path.relative_to(project_dir)}")


def markdown_to_html(md_content, title, author):
    """Simple markdown to HTML conversion."""
    lines = md_content.split("\n")
    html_lines = []
    for line in lines:
        line = line.rstrip()
        if line.startswith("# "):
            html_lines.append(f"<h1>{line[2:]}</h1>")
        elif line.startswith("## "):
            html_lines.append(f"<h2>{line[3:]}</h2>")
        elif line.startswith("### "):
            html_lines.append(f"<h3>{line[4:]}</h3>")
        elif line.startswith("---"):
            html_lines.append("<hr>")
        elif line.startswith("*") and line.endswith("*"):
            html_lines.append(f"<p><em>{line.strip('*')}</em></p>")
        elif line == "":
            html_lines.append("")
        else:
            html_lines.append(f"<p>{line}</p>")

    body = "\n".join(html_lines)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: 'Georgia', 'Times New Roman', serif; max-width: 700px; margin: 2em auto; padding: 0 1em; line-height: 1.7; color: #2c2c2c; background: #fefefe; }}
        h1 {{ font-size: 2.2em; text-align: center; margin-bottom: 0.2em; }}
        h2 {{ font-size: 1.5em; margin-top: 2em; border-bottom: 1px solid #ddd; padding-bottom: 0.3em; }}
        h3 {{ font-size: 1.2em; }}
        p {{ margin: 0.8em 0; text-indent: 1.5em; }}
        p:first-of-type {{ text-indent: 0; }}
        hr {{ border: none; border-top: 1px solid #ccc; margin: 2em 0; }}
        em {{ font-style: italic; }}
    </style>
</head>
<body>
{body}
</body>
</html>"""


# ═══════════════════════════════════════════════════════════════════════════════
# STATS
# ═══════════════════════════════════════════════════════════════════════════════

def cmd_stats(args):
    """Show project statistics."""
    project_dir = find_project(args.project)
    if not project_dir:
        print("Error: No project.yaml found.")
        sys.exit(1)

    config = load_project(project_dir)
    entities = collect_entities(project_dir)

    print(f"\n📊 {config.get('title', 'Untitled')} — Stats\n")
    print(f"  Genre: {config.get('genre', '?')}  |  Type: {config.get('type', '?')}")
    print()

    # Entity counts
    for etype in ["character", "location", "faction", "item", "magic-system", "event", "species", "race", "language", "lineage", "chapter"]:
        count = len(entities.get(etype, {}))
        # Handle plurals correctly
        if etype.endswith("s"):
            plural = etype.capitalize() + "es"
        else:
            plural = etype.capitalize() + "s"
        print(f"  {plural + ':':<20} {count}")

    # Event type breakdown
    events = entities.get("event", {})
    if events:
        evt_types = {}
        for slug, data in events.items():
            et = data["meta"].get("type", "milestone")
            evt_types[et] = evt_types.get(et, 0) + 1
        print(f"\n  Event types:")
        for et, count in sorted(evt_types.items(), key=lambda x: -x[1]):
            print(f"    {et:<20} {count}")

    # Word counts for chapters
    total_words = 0
    chapter_words = []
    for slug, data in sorted(entities.get("chapter", {}).items(),
                              key=lambda x: x[1]["meta"].get("number", 0)):
        meta = data["meta"]
        body = data["body"].strip()
        wc = len(body.split())
        total_words += wc
        status = meta.get("status", "?")
        title = meta.get("title", slug)
        num = meta.get("number", "?")
        chapter_words.append((num, title, wc, status))

    print(f"\n  Total words:        {total_words:,}")
    target = config.get("target_word_count", 0)
    if target:
        pct = (total_words / target) * 100
        print(f"  Target:             {target:,} ({pct:.1f}%)")

    if chapter_words:
        print(f"\n  Chapter breakdown:")
        for num, title, wc, status in chapter_words:
            bar = "█" * min(int(wc / 200), 30)
            print(f"    Ch {num:>2}: {title:<30} {wc:>6,}w [{status}] {bar}")

    # Character role breakdown
    chars = entities.get("character", {})
    if chars:
        roles = {}
        for slug, data in chars.items():
            role = data["meta"].get("role", "unknown")
            roles[role] = roles.get(role, 0) + 1
        print(f"\n  Character roles:")
        for role, count in sorted(roles.items()):
            print(f"    {role:<20} {count}")

    print()


# ═══════════════════════════════════════════════════════════════════════════════
# TIMELINE — built from event entities
# ═══════════════════════════════════════════════════════════════════════════════

def cmd_timeline(args):
    """Display chronological timeline built from event entities."""
    project_dir = find_project(args.project)
    if not project_dir:
        print("Error: No project.yaml found.")
        sys.exit(1)

    entities = collect_entities(project_dir)
    calendar = load_calendar(project_dir)
    events = entities.get("event", {})

    if not events:
        print("No events found. Add events with: worldbuilder.py add event 'Event Name'")
        return

    # Parse dates and sort
    dated_events = []
    undated_events = []
    for slug, data in events.items():
        meta = data["meta"]
        start, end = get_event_date(meta, calendar)
        if start.valid:
            dated_events.append((start, end, slug, meta))
        else:
            undated_events.append((slug, meta))

    dated_events.sort(key=lambda x: x[0].sort_key())

    # Optional filters
    era_filter = getattr(args, "era", None)
    entity_filter = getattr(args, "filter", None)

    # Print calendar info
    if calendar.get("eras"):
        print("\n📅 Eras:")
        for era in calendar["eras"]:
            end_yr = era.get("end_year", "present")
            print(f"  {era.get('prefix', '?')}: {era.get('name', '?')} "
                  f"(year {era.get('start_year', '?')} — {end_yr})")

    # Print timeline
    sig_markers = {
        "trivial": "·", "minor": "·", "moderate": "○", "major": "●", "world-changing": "★"
    }
    scope_colors = {
        "personal": "  ", "local": "  ", "regional": " ◈", "national": " ◆",
        "continental": " ◆◆", "global": " ◆◆◆", "cosmic": " ✦"
    }

    print(f"\n📅 Timeline ({len(dated_events)} dated, {len(undated_events)} undated):\n")

    current_era = None
    for start, end, slug, meta in dated_events:
        # Era filter
        if era_filter and start.era_prefix != era_filter:
            continue

        # Entity filter — check if entity appears in participants/locations/organizations
        if entity_filter:
            all_refs = []
            for p in meta.get("participants", []) or []:
                all_refs.append(p.get("entity", p) if isinstance(p, dict) else p)
            all_refs.extend(meta.get("locations", []) or [])
            for o in meta.get("organizations", []) or []:
                all_refs.append(o.get("entity", o) if isinstance(o, dict) else o)
            all_refs_lower = [str(r).lower() for r in all_refs]
            all_refs_slugs = [slugify(str(r)) for r in all_refs]
            ef_lower = entity_filter.lower()
            ef_slug = slugify(entity_filter)
            if ef_lower not in all_refs_lower and ef_slug not in all_refs_slugs:
                continue

        # Era separator
        if start.era_prefix and start.era_prefix != current_era:
            current_era = start.era_prefix
            era_name = current_era
            for era in calendar.get("eras", []):
                if era.get("prefix") == current_era:
                    era_name = f"{current_era} — {era.get('name', '')}"
                    break
            print(f"  ━━━ {era_name} ━━━")

        sig = meta.get("significance", "minor")
        scope = meta.get("scope", "local")
        marker = sig_markers.get(sig, "·")
        scope_mark = scope_colors.get(scope, "")
        name = meta.get("name", slug)
        evt_type = meta.get("type", "?")

        # Date display
        if end.valid and end != start:
            date_str = f"{start.display} — {end.display}"
        else:
            date_str = start.display

        print(f"  {marker} [{date_str}] {name} ({evt_type}){scope_mark}")

        # Participants
        participants = meta.get("participants", []) or []
        if participants:
            p_strs = []
            for p in participants:
                if isinstance(p, dict):
                    p_strs.append(f"{p.get('entity', '?')} ({p.get('role', '?')})")
                else:
                    p_strs.append(str(p))
            print(f"      Participants: {', '.join(p_strs)}")

        # Locations
        locs = meta.get("locations", []) or []
        if locs:
            print(f"      Locations: {', '.join(str(l) for l in locs)}")

        # Causality
        leads = meta.get("leads_to", []) or []
        if leads:
            print(f"      → Leads to: {', '.join(str(l) for l in leads)}")

    if undated_events:
        print(f"\n  ━━━ Undated Events ━━━")
        for slug, meta in undated_events:
            name = meta.get("name", slug)
            evt_type = meta.get("type", "?")
            print(f"  ? [{evt_type}] {name}")

    print()


# ═══════════════════════════════════════════════════════════════════════════════
# HISTORY — show an entity's event history
# ═══════════════════════════════════════════════════════════════════════════════

def cmd_history(args):
    """Show all events related to a specific entity."""
    project_dir = find_project(args.project)
    if not project_dir:
        print("Error: No project.yaml found.")
        sys.exit(1)

    entities = collect_entities(project_dir)
    calendar = load_calendar(project_dir)
    name_index = build_name_index(entities)

    # Find the entity
    target = args.entity_name
    resolved = resolve_ref(target, name_index)
    if not resolved:
        print(f"Entity '{target}' not found.")
        return

    etype, ename, eslug = resolved
    print(f"\n📜 History of {ename} ({etype}):\n")

    # Find all events that reference this entity
    events = entities.get("event", {})
    related = []

    for slug, data in events.items():
        meta = data["meta"]
        refs = set()

        # Collect all references in this event
        for p in meta.get("participants", []) or []:
            if isinstance(p, dict):
                refs.add(slugify(str(p.get("entity", ""))))
            else:
                refs.add(slugify(str(p)))

        for loc in meta.get("locations", []) or []:
            refs.add(slugify(str(loc)))

        for org in meta.get("organizations", []) or []:
            if isinstance(org, dict):
                refs.add(slugify(str(org.get("entity", ""))))
            else:
                refs.add(slugify(str(org)))

        for item_ref in meta.get("items_involved", []) or []:
            refs.add(slugify(str(item_ref)))

        # Type-specific references
        for field in ["person", "ruler", "victor", "founder", "discoverer", "inventor",
                       "prophet", "killer", "besieged", "besieger", "founded_entity",
                       "dissolved_entity"]:
            val = meta.get(field, "")
            if val:
                refs.add(slugify(str(val)))

        # List-type specific references
        for field in ["belligerents", "signatories", "partners", "parents",
                       "regions_affected", "parties"]:
            for item in meta.get(field, []) or []:
                if isinstance(item, dict):
                    for v in item.values():
                        if isinstance(v, str):
                            refs.add(slugify(v))
                elif isinstance(item, str):
                    refs.add(slugify(item))

        if eslug in refs:
            start, end = get_event_date(meta, calendar)
            related.append((start, end, slug, meta))

    if not related:
        print("  No events found for this entity.")
        print(f"  Add events that reference '{eslug}' in their participants/locations/organizations fields.")
        return

    # Sort by date
    dated = [(s, e, sl, m) for s, e, sl, m in related if s.valid]
    undated = [(s, e, sl, m) for s, e, sl, m in related if not s.valid]
    dated.sort(key=lambda x: x[0].sort_key())

    sig_markers = {"trivial": "·", "minor": "·", "moderate": "○", "major": "●", "world-changing": "★"}

    for start, end, slug, meta in dated:
        sig = meta.get("significance", "minor")
        marker = sig_markers.get(sig, "·")
        name = meta.get("name", slug)
        evt_type = meta.get("type", "?")
        date_str = f"{start.display} — {end.display}" if end.valid and end != start else start.display

        # What role did the target entity play?
        role = ""
        for p in meta.get("participants", []) or []:
            if isinstance(p, dict) and slugify(str(p.get("entity", ""))) == eslug:
                role = f" — {p.get('role', '')}"

        print(f"  {marker} [{date_str}] {name} ({evt_type}){role}")

    for start, end, slug, meta in undated:
        name = meta.get("name", slug)
        evt_type = meta.get("type", "?")
        print(f"  ? {name} ({evt_type})")

    print(f"\n  Total: {len(related)} events")
    print()


# ═══════════════════════════════════════════════════════════════════════════════
# CROSSREF — show what entities an event links to (or all links for any entity)
# ═══════════════════════════════════════════════════════════════════════════════

def cmd_crossref(args):
    """Show all cross-references for an entity."""
    project_dir = find_project(args.project)
    if not project_dir:
        print("Error: No project.yaml found.")
        sys.exit(1)

    entities = collect_entities(project_dir)
    name_index = build_name_index(entities)

    target = args.entity_name
    resolved = resolve_ref(target, name_index)
    if not resolved:
        print(f"Entity '{target}' not found.")
        return

    etype, ename, eslug = resolved
    print(f"\n🔗 Cross-references for {ename} ({etype}):\n")

    # Search ALL entities for references to this one
    refs_to = []    # entities that reference our target
    refs_from = []  # entities our target references

    target_data = None
    for et, ents in entities.items():
        if eslug in ents:
            target_data = ents[eslug]
            break

    # Check what our target references
    if target_data:
        meta = target_data["meta"]
        meta_str = str(meta)
        # Scan all known entities to see if they're mentioned
        for other_slug, other_entry in name_index.items():
            if other_slug == eslug:
                continue
            if len(other_slug) < 3:  # skip very short slugs to avoid false matches
                continue
            ot, oname, oslug = other_entry
            if oslug in meta_str or oname.lower() in meta_str.lower():
                if (ot, oname, oslug) not in refs_from:
                    refs_from.append((ot, oname, oslug))

    # Check what references our target
    for et, ents in entities.items():
        for slug, data in ents.items():
            if slug == eslug:
                continue
            meta_str = str(data["meta"])
            if eslug in meta_str or ename.lower() in meta_str.lower():
                name = data["meta"].get("name", data["meta"].get("title", slug))
                refs_to.append((et, name, slug))

    if refs_from:
        print(f"  References (this entity mentions):")
        for rt, rn, rs in sorted(set(refs_from)):
            print(f"    → [{rt}] {rn}")

    if refs_to:
        print(f"\n  Referenced by (other entities mention this one):")
        for rt, rn, rs in sorted(set(refs_to)):
            print(f"    ← [{rt}] {rn}")

    if not refs_from and not refs_to:
        print("  No cross-references found. This entity is isolated.")

    print(f"\n  Outgoing: {len(set(refs_from))} | Incoming: {len(set(refs_to))}")
    print()


# ═══════════════════════════════════════════════════════════════════════════════
# GRAPH
# ═══════════════════════════════════════════════════════════════════════════════

def cmd_graph(args):
    """Generate a Mermaid character relationship graph."""
    project_dir = find_project(args.project)
    if not project_dir:
        print("Error: No project.yaml found.")
        sys.exit(1)

    entities = collect_entities(project_dir)
    chars = entities.get("character", {})

    if not chars:
        print("No characters found.")
        return

    print("```mermaid")
    print("graph LR")

    role_styles = {
        "protagonist": ":::protagonist",
        "antagonist": ":::antagonist",
        "supporting": "", "minor": "", "mentioned": "",
    }

    seen_edges = set()
    for slug, data in chars.items():
        meta = data["meta"]
        name = meta.get("name", slug)
        role = meta.get("role", "")
        style = role_styles.get(role, "")
        safe_name = name.replace('"', "'")
        print(f'    {slug}["{safe_name}"]{style}')

        for rel in meta.get("relationships", []) or []:
            if isinstance(rel, dict):
                target = rel.get("target", "")
                rel_type = rel.get("type", "?")
                target_slug = slugify(target)
                edge_key = tuple(sorted([slug, target_slug]))
                if edge_key not in seen_edges and target_slug in chars:
                    seen_edges.add(edge_key)
                    arrow = {"ally": "---", "enemy": "-.-", "family": "===", "romantic": "-..-"}.get(rel_type, "---")
                    print(f"    {slug} {arrow}|{rel_type}| {target_slug}")

    print()
    print("    classDef protagonist fill:#4a9,stroke:#2a7,color:#fff")
    print("    classDef antagonist fill:#c44,stroke:#a22,color:#fff")
    print("```")


# ═══════════════════════════════════════════════════════════════════════════════
# LIST
# ═══════════════════════════════════════════════════════════════════════════════

def cmd_list(args):
    """List all entities of a given type."""
    project_dir = find_project(args.project)
    if not project_dir:
        print("Error: No project.yaml found.")
        sys.exit(1)

    entities = collect_entities(project_dir)
    calendar = load_calendar(project_dir)
    etype = args.entity_type.rstrip("s")

    # Handle plurals
    if etype not in entities:
        for k in entities:
            if k.rstrip("s") == etype or k == etype + "s":
                etype = k
                break

    items = entities.get(etype, {})
    if not items:
        print(f"No {etype}s found.")
        return

    print(f"\n{etype.capitalize()}s ({len(items)}):\n")
    for slug, data in sorted(items.items()):
        meta = data["meta"]
        name = meta.get("name", slug)
        extra = ""
        if etype == "character":
            role = meta.get("role", "")
            status = meta.get("status", "")
            extra = f"  [{role}, {status}]"
        elif etype == "location":
            loc_type = meta.get("type", "")
            extra = f"  [{loc_type}]"
        elif etype == "event":
            evt_type = meta.get("type", "?")
            start, end = get_event_date(meta, calendar)
            date_str = start.display if start.valid else "undated"
            sig = meta.get("significance", "?")
            extra = f"  [{evt_type}, {date_str}, {sig}]"
        elif etype == "faction":
            status = meta.get("status", "")
            extra = f"  [{status}]" if status else ""
        print(f"  • {name}{extra}")
    print()


# ═══════════════════════════════════════════════════════════════════════════════
# QUERY
# ═══════════════════════════════════════════════════════════════════════════════

def cmd_query(args):
    """Simple keyword query across project data."""
    project_dir = find_project(args.project)
    if not project_dir:
        print("Error: No project.yaml found.")
        sys.exit(1)

    query = args.question.lower()
    entities = collect_entities(project_dir)
    results = []

    for etype, items in entities.items():
        for slug, data in items.items():
            meta = data["meta"]
            body = data.get("body", "")
            searchable = f"{slug} {body} {str(meta)}".lower()
            if query in searchable:
                name = meta.get("name", meta.get("title", slug))
                results.append((etype, name, data["file"]))

    if results:
        print(f"\nFound {len(results)} match(es) for '{args.question}':\n")
        for etype, name, filepath in results:
            print(f"  [{etype}] {name}")
            print(f"    → {filepath.relative_to(project_dir)}")
    else:
        print(f"No matches for '{args.question}'.")
    print()


# ═══════════════════════════════════════════════════════════════════════════════
# FLAGS — display and manage world flags
# ═══════════════════════════════════════════════════════════════════════════════

def cmd_flags(args):
    """Display current world flags from project.yaml."""
    project_dir = find_project(args.project)
    if not project_dir:
        print("Error: No project.yaml found.")
        sys.exit(1)

    config = load_project(project_dir)
    world_flags = config.get("world_flags", {})

    if not world_flags:
        print("\n⚠ No world_flags defined in project.yaml")
        print("  Run 'worldbuilder init' with a genre to populate defaults.")
        return

    title = config.get("title", "Untitled")
    genre = config.get("genre", "?")
    print(f"\n🏴 World Flags — {title} ({genre})\n")

    for section_name, section in world_flags.items():
        if not isinstance(section, dict):
            continue
        print(f"  ┌─ {section_name.upper()} ─────────────────────────────────")
        for flag_name, flag_data in section.items():
            if isinstance(flag_data, dict):
                val = flag_data.get("value", "?")
                desc = flag_data.get("description", "")
                locked = flag_data.get("locked", False)
                lock_icon = "🔒" if locked else "  "
                # Color-code booleans
                if val is True:
                    val_str = "✓ yes"
                elif val is False:
                    val_str = "✗ no"
                else:
                    val_str = str(val)
                print(f"  │ {lock_icon} {flag_name:<22} {val_str:<12} {desc}")
            else:
                print(f"  │    {flag_name:<22} {flag_data}")
        print(f"  └{'─' * 52}")
    print()


# ═══════════════════════════════════════════════════════════════════════════════
# EDIT — run editor personae against chapters
# ═══════════════════════════════════════════════════════════════════════════════

# EDITOR_DIR is set at top of file (supports both skill and legacy layouts)

def list_editors():
    """List available editor personae."""
    editors = {}
    if EDITOR_DIR.exists():
        for f in EDITOR_DIR.glob("*.yaml"):
            with open(f) as fh:
                data = yaml.safe_load(fh) or {}
                editors[f.stem] = data
    return editors


def cmd_edit(args):
    """Run an editor persona against chapters — generates a review prompt/report."""
    project_dir = find_project(args.project)
    if not project_dir:
        print("Error: No project.yaml found.")
        sys.exit(1)

    editor_name = args.editor_name
    editors = list_editors()

    if editor_name == "list":
        print("\n📝 Available Editor Personae:\n")
        for name, data in sorted(editors.items()):
            icon = data.get("icon", "")
            codename = data.get("codename", "")
            role_line = data.get("role", "").strip().split("\n")[0][:70]
            checks = data.get("checks", [])
            print(f"  {icon} {name:<16} ({codename})")
            print(f"    {role_line}")
            print(f"    Checks: {len(checks)}")
            print()
        return

    if editor_name not in editors:
        print(f"Error: Unknown editor '{editor_name}'. Use 'edit list' to see available editors.")
        sys.exit(1)

    editor = editors[editor_name]
    config = load_project(project_dir)
    entities = collect_entities(project_dir)

    # Parse chapter range
    chapter_range = args.chapter if hasattr(args, 'chapter') and args.chapter else "all"
    chapters = entities.get("chapter", {})

    if chapter_range != "all":
        # Support "1-3" or "5" formats
        if "-" in chapter_range:
            start, end = chapter_range.split("-", 1)
            ch_nums = range(int(start), int(end) + 1)
        else:
            ch_nums = [int(chapter_range)]
        chapters = {
            s: d for s, d in chapters.items()
            if d["meta"].get("number") in ch_nums
        }

    if not chapters:
        print(f"No chapters found to edit (range: {chapter_range}).")
        return

    # Gather required context files
    context_req = editor.get("context_requirements", [])
    context_files = {}
    for req in context_req:
        req = req.split("#")[0].strip()  # Strip comments
        if "*" in req:
            # Glob pattern
            for match in project_dir.glob(req):
                if match.is_file():
                    context_files[str(match.relative_to(project_dir))] = match
        else:
            full_path = project_dir / req
            if full_path.exists():
                context_files[req] = full_path

    # Build the review prompt
    icon = editor.get("icon", "")
    codename = editor.get("codename", "")
    name = editor.get("name", editor_name)
    role = editor.get("role", "").strip()
    personality = editor.get("personality", "").strip()
    checks = editor.get("checks", [])
    output_fmt = editor.get("output_format", "")

    print(f"\n{icon} {name} ({codename}) — Reviewing {len(chapters)} chapter(s)\n")
    print("=" * 60)

    # Print the assembled prompt for use with Claude
    prompt_lines = []
    prompt_lines.append(f"# Editor Persona: {name} ({codename})")
    prompt_lines.append(f"\n## Role\n{role}")
    prompt_lines.append(f"\n## Personality\n{personality}")

    prompt_lines.append("\n## Checks to Perform")
    for check in checks:
        sev = check.get("severity", "info").upper()
        prompt_lines.append(f"- [{sev}] {check.get('id', '?')}: {check.get('description', '')}")
        if check.get("method"):
            prompt_lines.append(f"  Method: {check['method']}")

    prompt_lines.append(f"\n## Output Format\n```\n{output_fmt}\n```")

    # Context summary
    prompt_lines.append("\n## Context Files Loaded")
    for rel_path, full_path in sorted(context_files.items()):
        size = full_path.stat().st_size
        prompt_lines.append(f"- {rel_path} ({size:,} bytes)")

    # Chapter content summary
    prompt_lines.append(f"\n## Chapters to Review (range: {chapter_range})")
    for slug, data in sorted(chapters.items(), key=lambda x: x[1]["meta"].get("number", 0)):
        meta = data["meta"]
        body = data.get("body", "").strip()
        wc = len(body.split())
        prompt_lines.append(f"- Ch {meta.get('number', '?')}: {meta.get('title', slug)} ({wc:,} words)")

    full_prompt = "\n".join(prompt_lines)

    # Save the prompt to a review file
    review_dir = project_dir / "output" / "reviews"
    review_dir.mkdir(parents=True, exist_ok=True)
    review_file = review_dir / f"review-{editor_name}-{chapter_range}.md"
    with open(review_file, "w") as f:
        f.write(full_prompt)

    print(full_prompt)
    print(f"\n{'=' * 60}")
    print(f"✓ Review prompt saved to: {review_file.relative_to(project_dir)}")
    print(f"\nTo execute: Feed this prompt + the context files to Claude with the")
    print(f"chapter text to get a detailed {name} review.")


# ═══════════════════════════════════════════════════════════════════════════════
# GEOGRAPHY — spatial hierarchy and transport validation
# ═══════════════════════════════════════════════════════════════════════════════

def build_location_hierarchy(entities):
    """Build a tree of locations from parent references."""
    locations = entities.get("location", {})
    tree = {}   # slug -> { name, parent, children, routes }
    for slug, data in locations.items():
        meta = data["meta"]
        tree[slug] = {
            "name": meta.get("name", slug),
            "parent": meta.get("parent", ""),
            "type": meta.get("type", "place"),
            "children": [],
            "routes": meta.get("routes", []) or [],
            "coordinates": meta.get("coordinates", {}),
        }

    # Wire parent→child links
    for slug, node in tree.items():
        parent_slug = slugify(node["parent"]) if node["parent"] else ""
        if parent_slug and parent_slug in tree:
            tree[parent_slug]["children"].append(slug)

    return tree


def cmd_geography(args):
    """Display spatial hierarchy and transport routes."""
    project_dir = find_project(args.project)
    if not project_dir:
        print("Error: No project.yaml found.")
        sys.exit(1)

    entities = collect_entities(project_dir)
    config = load_project(project_dir)
    tree = build_location_hierarchy(entities)

    title = config.get("title", "Untitled")
    print(f"\n🗺️  Geography — {title}\n")

    # Find root nodes (no parent or parent not in tree)
    roots = []
    for slug, node in tree.items():
        parent_slug = slugify(node["parent"]) if node["parent"] else ""
        if not parent_slug or parent_slug not in tree:
            roots.append(slug)

    if not roots:
        print("  No locations found.")
        return

    def print_tree(slug, depth=0):
        node = tree[slug]
        indent = "  │ " * depth + "  ├─ " if depth > 0 else "  "
        type_badge = f"[{node['type']}]"
        print(f"{indent}{node['name']} {type_badge}")
        # Show routes (support both old single-method and new multi-method format)
        for route in node.get("routes", []):
            if isinstance(route, dict):
                dest = route.get("to", "?")
                route_type = route.get("route_type", "")
                rt_badge = f" [{route_type}]" if route_type else ""
                methods = route.get("methods", [])
                if methods:
                    r_indent = "  │ " * (depth + 1) + "  "
                    modes = ", ".join(m.get("mode", "?") for m in methods if isinstance(m, dict))
                    # Show first method's distance as representative
                    dist = methods[0].get("distance", "?") if methods else "?"
                    print(f"{r_indent}→ {dest}{rt_badge}: {modes} ({dist})")
                else:
                    # Fallback to old format
                    method = route.get("method", "?")
                    distance = route.get("distance", "?")
                    time = route.get("travel_time", "?")
                    r_indent = "  │ " * (depth + 1) + "  "
                    print(f"{r_indent}→ {dest} via {method} ({distance}, ~{time})")
            elif isinstance(route, str):
                r_indent = "  │ " * (depth + 1) + "  "
                print(f"{r_indent}→ {route}")
        for child in sorted(node["children"]):
            print_tree(child, depth + 1)

    for root in sorted(roots, key=lambda s: tree[s]["name"]):
        print_tree(root)

    # Summary
    total = len(tree)
    routes_count = sum(len(n.get("routes", [])) for n in tree.values())
    print(f"\n  {total} locations, {routes_count} transport routes\n")


def validate_peoples(entities, name_index, config, issues, warnings):
    """Validate species/race/language consistency and interbreeding rules."""
    species_data = entities.get("species", {})
    races_data = entities.get("race", {})
    langs_data = entities.get("language", {})
    characters = entities.get("character", {})
    world_flags = config.get("world_flags", {})
    peoples_flags = world_flags.get("peoples", {})

    # Check if cross-species breeding is allowed
    csb_flag = peoples_flags.get("cross_species_breeding", {})
    if isinstance(csb_flag, dict):
        cross_species_ok = csb_flag.get("value", False)
    else:
        cross_species_ok = bool(csb_flag)

    # ── Race→Species reference validation ─────────────────────────────────────
    for slug, data in races_data.items():
        meta = data["meta"]
        name = meta.get("name", slug)
        sp_ref = meta.get("species", "")
        if sp_ref:
            resolved = resolve_ref(sp_ref, name_index)
            if not resolved:
                issues.append(f"Race '{name}': species '{sp_ref}' not found")
            elif resolved[0] != "species":
                issues.append(f"Race '{name}': species '{sp_ref}' is a {resolved[0]}, not a species")
        else:
            warnings.append(f"Race '{name}': no species set")

        # Check language refs
        lang_ref = (meta.get("culture") or {}).get("language", "")
        if lang_ref and not resolve_ref(lang_ref, name_index):
            warnings.append(f"Race '{name}': language '{lang_ref}' not found")

    # ── Species relationship validation ───────────────────────────────────────
    for slug, data in species_data.items():
        meta = data["meta"]
        name = meta.get("name", slug)

        for rel in meta.get("relationships", []) or []:
            if isinstance(rel, dict):
                sp_ref = rel.get("species", "")
                if sp_ref and not resolve_ref(sp_ref, name_index):
                    warnings.append(f"Species '{name}': relationship target '{sp_ref}' not found")

                # Check interbreeding flag consistency
                if rel.get("can_interbreed") and not cross_species_ok:
                    warnings.append(
                        f"Species '{name}': can_interbreed with '{sp_ref}' is true, "
                        f"but world_flags.peoples.cross_species_breeding is false/unset"
                    )

        # Check race refs
        for race_ref in meta.get("races", []) or []:
            if race_ref and not resolve_ref(race_ref, name_index):
                warnings.append(f"Species '{name}': race '{race_ref}' not found")

        # Check language refs
        culture = meta.get("culture") or {}
        for lang_ref in culture.get("languages", []) or []:
            if lang_ref and not resolve_ref(lang_ref, name_index):
                warnings.append(f"Species '{name}': language '{lang_ref}' not found")

    # ── Language family tree validation ────────────────────────────────────────
    for slug, data in langs_data.items():
        meta = data["meta"]
        name = meta.get("name", slug)
        family = meta.get("family") or {}

        parent = family.get("parent_language", "")
        if parent and not resolve_ref(parent, name_index):
            warnings.append(f"Language '{name}': parent_language '{parent}' not found")

        for child in family.get("child_languages", []) or []:
            if child and not resolve_ref(child, name_index):
                warnings.append(f"Language '{name}': child_language '{child}' not found")

        # Check intelligibility refs
        for entry in meta.get("intelligibility", []) or []:
            if isinstance(entry, dict):
                lang_ref = entry.get("language", "")
                if lang_ref and not resolve_ref(lang_ref, name_index):
                    warnings.append(f"Language '{name}': intelligibility target '{lang_ref}' not found")
                score = entry.get("score", 0)
                if isinstance(score, (int, float)) and (score < 0 or score > 1):
                    issues.append(f"Language '{name}': intelligibility score {score} out of range [0.0, 1.0]")

    # ── Character species/race validation ─────────────────────────────────────
    for slug, data in characters.items():
        meta = data["meta"]
        name = meta.get("name", slug)
        sp = meta.get("species", "")
        race = meta.get("race", "")

        # If a character has a race, check it belongs to their species
        if sp and race and species_data and races_data:
            sp_resolved = resolve_ref(sp, name_index)
            race_resolved = resolve_ref(race, name_index)
            if sp_resolved and race_resolved:
                race_data = races_data.get(race_resolved[2])
                if race_data:
                    race_species = race_data["meta"].get("species", "")
                    if race_species:
                        race_sp_resolved = resolve_ref(race_species, name_index)
                        if race_sp_resolved and race_sp_resolved[2] != sp_resolved[2]:
                            issues.append(
                                f"Character '{name}': race '{race}' belongs to species "
                                f"'{race_species}', but character's species is '{sp}'"
                            )

    # ── Character interbreeding validation ────────────────────────────────────
    # Check birth events: if parents are different species, validate interbreeding rules
    events = entities.get("event", {})
    for slug, data in events.items():
        meta = data["meta"]
        if meta.get("type") != "birth":
            continue
        parents = meta.get("parents", []) or []
        if len(parents) < 2:
            continue

        parent_species = []
        for p_ref in parents:
            resolved = resolve_ref(p_ref, name_index)
            if resolved and resolved[0] == "character":
                char = characters.get(resolved[2])
                if char:
                    parent_species.append((resolved[1], char["meta"].get("species", "human")))

        if len(parent_species) >= 2:
            sp1 = parent_species[0][1]
            sp2 = parent_species[1][1]
            if sp1 and sp2 and slugify(sp1) != slugify(sp2):
                if not cross_species_ok:
                    issues.append(
                        f"Birth event '{meta.get('name', slug)}': parents {parent_species[0][0]} "
                        f"({sp1}) and {parent_species[1][0]} ({sp2}) are different species, "
                        f"but cross_species_breeding is not enabled"
                    )
                else:
                    # Check if the specific pair is allowed
                    sp1_data = species_data.get(slugify(sp1))
                    if sp1_data:
                        allowed = False
                        for rel in sp1_data["meta"].get("relationships", []) or []:
                            if isinstance(rel, dict):
                                rel_sp = rel.get("species", "")
                                if slugify(rel_sp) == slugify(sp2) and rel.get("can_interbreed"):
                                    allowed = True
                                    break
                        if not allowed:
                            issues.append(
                                f"Birth event '{meta.get('name', slug)}': cross-species "
                                f"breeding between {sp1} and {sp2} not defined in species relationships"
                            )


def validate_geography(entities, name_index, config, issues, warnings):
    """Validate spatial consistency: hierarchy, routes, travel times."""
    tree = build_location_hierarchy(entities)
    world_flags = config.get("world_flags", {})
    tech_flags = world_flags.get("technology", {})

    # Transport methods that require tech flags
    tech_transport = {
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

    for slug, node in tree.items():
        # Check parent exists
        parent_ref = node["parent"]
        if parent_ref:
            parent_slug = slugify(parent_ref)
            if parent_slug not in tree:
                if not resolve_ref(parent_ref, name_index):
                    warnings.append(
                        f"Location '{node['name']}': parent '{parent_ref}' not found"
                    )

        # Check route destinations exist
        for route in node.get("routes", []):
            if isinstance(route, dict):
                dest = route.get("to", "")
                if dest and not resolve_ref(dest, name_index):
                    warnings.append(
                        f"Location '{node['name']}': route destination '{dest}' not found"
                    )

                # Check transport method is valid for tech level
                method = route.get("method", "").lower()
                for transport, required_flag in tech_transport.items():
                    if transport in method:
                        flag_val = tech_flags.get(required_flag, {})
                        if isinstance(flag_val, dict):
                            val = flag_val.get("value")
                        else:
                            val = flag_val
                        if val is False or val == "false" or val == "none":
                            issues.append(
                                f"Location '{node['name']}': route uses '{method}' "
                                f"but {required_flag} = false"
                            )

    # Check for circular hierarchy
    for slug in tree:
        visited = set()
        current = slug
        while current:
            if current in visited:
                issues.append(f"Location '{tree[slug]['name']}': circular parent hierarchy detected")
                break
            visited.add(current)
            parent_ref = tree.get(current, {}).get("parent", "")
            current = slugify(parent_ref) if parent_ref else ""
            if current and current not in tree:
                break


def validate_bidirectional_refs(entities, name_index, issues, warnings):
    """Validate bidirectional reference symmetry across entity types."""
    characters = entities.get("character", {})
    factions = entities.get("faction", {})
    locations = entities.get("location", {})
    species_data = entities.get("species", {})
    races_data = entities.get("race", {})
    events = entities.get("event", {})
    lineages = entities.get("lineage", {})

    # ── Character relationship symmetry (WARNING) ────────────────────────────
    for slug, data in characters.items():
        meta = data["meta"]
        name = meta.get("name", slug)
        for rel in meta.get("relationships", []) or []:
            if not isinstance(rel, dict):
                continue
            target = rel.get("target", "")
            if not target:
                continue
            resolved = resolve_ref(target, name_index)
            if not resolved or resolved[0] != "character":
                continue
            target_data = characters.get(resolved[2])
            if not target_data:
                continue
            target_rels = target_data["meta"].get("relationships", []) or []
            has_backref = False
            for tr in target_rels:
                if not isinstance(tr, dict):
                    continue
                tr_target = tr.get("target", "")
                if not tr_target:
                    continue
                tr_resolved = resolve_ref(tr_target, name_index)
                if tr_resolved and tr_resolved[2] == slug:
                    has_backref = True
                    break
            if not has_backref:
                warnings.append(
                    f"Character '{name}': has relationship to '{resolved[1]}' "
                    f"but no reciprocal relationship found"
                )

    # ── Family links symmetry (ERROR) ────────────────────────────────────────
    for slug, data in characters.items():
        meta = data["meta"]
        name = meta.get("name", slug)
        fl = meta.get("family_links", {}) or {}

        # Children ↔ father/mother
        for child_ref in fl.get("children", []) or []:
            if not child_ref:
                continue
            resolved = resolve_ref(child_ref, name_index)
            if not resolved or resolved[0] != "character":
                continue
            child_data = characters.get(resolved[2])
            if not child_data:
                continue
            child_fl = child_data["meta"].get("family_links", {}) or {}
            father = child_fl.get("father", "")
            mother = child_fl.get("mother", "")
            father_resolved = resolve_ref(father, name_index) if father else None
            mother_resolved = resolve_ref(mother, name_index) if mother else None
            parent_match = (
                (father_resolved and father_resolved[2] == slug)
                or (mother_resolved and mother_resolved[2] == slug)
            )
            if not parent_match:
                issues.append(
                    f"Character '{name}': lists '{resolved[1]}' as child, "
                    f"but child's father/mother doesn't reference back"
                )

        # Father/mother → children
        for parent_field in ("father", "mother"):
            parent_ref = fl.get(parent_field, "")
            if not parent_ref:
                continue
            resolved = resolve_ref(parent_ref, name_index)
            if not resolved or resolved[0] != "character":
                continue
            parent_data = characters.get(resolved[2])
            if not parent_data:
                continue
            parent_fl = parent_data["meta"].get("family_links", {}) or {}
            parent_children = parent_fl.get("children", []) or []
            child_slugs = []
            for c in parent_children:
                if c:
                    cr = resolve_ref(c, name_index)
                    if cr:
                        child_slugs.append(cr[2])
            if slug not in child_slugs:
                issues.append(
                    f"Character '{name}': lists '{resolved[1]}' as {parent_field}, "
                    f"but parent's children list doesn't include '{name}'"
                )

        # Spouse symmetry
        for spouse_ref in fl.get("spouse", []) or [] if isinstance(fl.get("spouse"), list) else ([fl.get("spouse")] if fl.get("spouse") else []):
            if not spouse_ref:
                continue
            resolved = resolve_ref(spouse_ref, name_index)
            if not resolved or resolved[0] != "character":
                continue
            spouse_data = characters.get(resolved[2])
            if not spouse_data:
                continue
            spouse_fl = spouse_data["meta"].get("family_links", {}) or {}
            spouse_spouses = spouse_fl.get("spouse", []) or [] if isinstance(spouse_fl.get("spouse"), list) else ([spouse_fl.get("spouse")] if spouse_fl.get("spouse") else [])
            spouse_slugs = []
            for s in spouse_spouses:
                if s:
                    sr = resolve_ref(s, name_index)
                    if sr:
                        spouse_slugs.append(sr[2])
            if slug not in spouse_slugs:
                issues.append(
                    f"Character '{name}': lists '{resolved[1]}' as spouse, "
                    f"but spouse doesn't list '{name}' back"
                )

        # Sibling symmetry
        for sib_ref in fl.get("siblings", []) or []:
            if not sib_ref:
                continue
            resolved = resolve_ref(sib_ref, name_index)
            if not resolved or resolved[0] != "character":
                continue
            sib_data = characters.get(resolved[2])
            if not sib_data:
                continue
            sib_fl = sib_data["meta"].get("family_links", {}) or {}
            sib_siblings = sib_fl.get("siblings", []) or []
            sib_slugs = []
            for s in sib_siblings:
                if s:
                    sr = resolve_ref(s, name_index)
                    if sr:
                        sib_slugs.append(sr[2])
            if slug not in sib_slugs:
                issues.append(
                    f"Character '{name}': lists '{resolved[1]}' as sibling, "
                    f"but sibling doesn't list '{name}' back"
                )

    # ── Faction membership symmetry (WARNING) ────────────────────────────────
    # Character→faction: faction should list character as member
    for slug, data in characters.items():
        meta = data["meta"]
        name = meta.get("name", slug)
        faction_ref = meta.get("faction", "")
        if not faction_ref:
            continue
        resolved = resolve_ref(faction_ref, name_index)
        if not resolved or resolved[0] != "faction":
            continue
        faction_data = factions.get(resolved[2])
        if not faction_data:
            continue
        members = faction_data["meta"].get("members", []) or []
        member_slugs = []
        for m in members:
            if isinstance(m, dict):
                mr = resolve_ref(m.get("character", m.get("entity", "")), name_index)
            elif isinstance(m, str):
                mr = resolve_ref(m, name_index)
            else:
                mr = None
            if mr:
                member_slugs.append(mr[2])
        if slug not in member_slugs:
            warnings.append(
                f"Character '{name}': faction is '{resolved[1]}', "
                f"but faction's members list doesn't include them"
            )

    # Faction→members: member should have faction set
    for slug, data in factions.items():
        meta = data["meta"]
        fname = meta.get("name", slug)
        for m in meta.get("members", []) or []:
            if isinstance(m, dict):
                m_ref = m.get("character", m.get("entity", ""))
            elif isinstance(m, str):
                m_ref = m
            else:
                continue
            if not m_ref:
                continue
            resolved = resolve_ref(m_ref, name_index)
            if not resolved or resolved[0] != "character":
                continue
            char_data = characters.get(resolved[2])
            if not char_data:
                continue
            char_faction = char_data["meta"].get("faction", "")
            if char_faction:
                char_faction_resolved = resolve_ref(char_faction, name_index)
                if char_faction_resolved and char_faction_resolved[2] == slug:
                    continue
            warnings.append(
                f"Faction '{fname}': lists '{resolved[1]}' as member, "
                f"but character's faction doesn't match"
            )

    # ── Location notable_characters symmetry (WARNING) ───────────────────────
    notable_roles = {"protagonist", "antagonist", "supporting", "major"}

    # Character→location: location should list notable characters
    for slug, data in characters.items():
        meta = data["meta"]
        name = meta.get("name", slug)
        role = meta.get("role", "")
        if role not in notable_roles:
            continue
        loc_ref = meta.get("location", "")
        if not loc_ref:
            continue
        resolved = resolve_ref(loc_ref, name_index)
        if not resolved or resolved[0] != "location":
            continue
        loc_data = locations.get(resolved[2])
        if not loc_data:
            continue
        notables = loc_data["meta"].get("notable_characters", []) or []
        notable_slugs = []
        for n in notables:
            if n:
                nr = resolve_ref(n, name_index)
                if nr:
                    notable_slugs.append(nr[2])
        if slug not in notable_slugs:
            warnings.append(
                f"Character '{name}' (role={role}): location is '{resolved[1]}', "
                f"but location's notable_characters doesn't include them"
            )

    # Location→notable_characters: character's location should match
    # (also accepts descendants — if char is at a child/grandchild location)
    def _is_ancestor_location(ancestor_slug, descendant_slug, locs, ni, _depth=0):
        """Walk up parent chain from descendant to see if ancestor is found."""
        if _depth > 20:
            return False
        cur = descendant_slug
        while cur and _depth < 20:
            if cur == ancestor_slug:
                return True
            loc = locs.get(cur)
            if not loc:
                break
            parent_ref = loc["meta"].get("parent", "")
            if not parent_ref:
                break
            pr = resolve_ref(parent_ref, ni)
            if not pr or pr[0] != "location":
                break
            cur = pr[2]
            _depth += 1
        return False

    for slug, data in locations.items():
        meta = data["meta"]
        lname = meta.get("name", slug)
        for nc in meta.get("notable_characters", []) or []:
            if not nc:
                continue
            resolved = resolve_ref(nc, name_index)
            if not resolved or resolved[0] != "character":
                continue
            char_data = characters.get(resolved[2])
            if not char_data:
                continue
            char_loc = char_data["meta"].get("location", "")
            if char_loc:
                char_loc_resolved = resolve_ref(char_loc, name_index)
                if char_loc_resolved and _is_ancestor_location(slug, char_loc_resolved[2], locations, name_index):
                    continue
            warnings.append(
                f"Location '{lname}': lists '{resolved[1]}' as notable character, "
                f"but character's location doesn't match"
            )

    # ── Species↔race back-references (ERROR) ─────────────────────────────────
    # Species.races → race.species must point back
    for slug, data in species_data.items():
        meta = data["meta"]
        sname = meta.get("name", slug)
        for race_ref in meta.get("races", []) or []:
            if not race_ref:
                continue
            resolved = resolve_ref(race_ref, name_index)
            if not resolved or resolved[0] != "race":
                continue
            race_data_entry = races_data.get(resolved[2])
            if not race_data_entry:
                continue
            race_species = race_data_entry["meta"].get("species", "")
            if race_species:
                rs_resolved = resolve_ref(race_species, name_index)
                if rs_resolved and rs_resolved[2] == slug:
                    continue
            issues.append(
                f"Species '{sname}': lists race '{resolved[1]}', "
                f"but race's species doesn't point back"
            )

    # Race.species → species.races must include the race
    for slug, data in races_data.items():
        meta = data["meta"]
        rname = meta.get("name", slug)
        sp_ref = meta.get("species", "")
        if not sp_ref:
            continue
        resolved = resolve_ref(sp_ref, name_index)
        if not resolved or resolved[0] != "species":
            continue
        sp_data = species_data.get(resolved[2])
        if not sp_data:
            continue
        sp_races = sp_data["meta"].get("races", []) or []
        race_slugs = []
        for r in sp_races:
            if r:
                rr = resolve_ref(r, name_index)
                if rr:
                    race_slugs.append(rr[2])
        if slug not in race_slugs:
            issues.append(
                f"Race '{rname}': species is '{resolved[1]}', "
                f"but species' races list doesn't include this race"
            )

    # ── Event causality both directions (WARNING) ────────────────────────────
    # caused_by → leads_to backref (extends existing leads_to→caused_by check)
    for slug, data in events.items():
        meta = data["meta"]
        ename = meta.get("name", slug)
        for caused_ref in meta.get("caused_by", []) or []:
            if not caused_ref:
                continue
            resolved = resolve_ref(caused_ref, name_index)
            if not resolved or resolved[0] != "event":
                continue
            cause_data = events.get(resolved[2])
            if not cause_data:
                continue
            leads_to = cause_data["meta"].get("leads_to", []) or []
            leads_slugs = []
            for lt in leads_to:
                if lt:
                    lr = resolve_ref(lt, name_index)
                    if lr:
                        leads_slugs.append(lr[2])
            if slug not in leads_slugs:
                warnings.append(
                    f"Event '{ename}': caused_by '{resolved[1]}', "
                    f"but that event's leads_to doesn't reference back"
                )

    # ── Lineage membership symmetry (ERROR) ──────────────────────────────────
    # Character→lineage: lineage should list character as member
    for slug, data in characters.items():
        meta = data["meta"]
        name = meta.get("name", slug)
        fl = meta.get("family_links", {}) or {}
        lineage_ref = fl.get("lineage", "")
        if not lineage_ref:
            continue
        resolved = resolve_ref(lineage_ref, name_index)
        if not resolved or resolved[0] != "lineage":
            continue
        lineage_data = lineages.get(resolved[2])
        if not lineage_data:
            continue
        members = lineage_data["meta"].get("members", []) or []
        member_slugs = []
        for m in members:
            if m:
                mr = resolve_ref(m, name_index)
                if mr:
                    member_slugs.append(mr[2])
        if slug not in member_slugs:
            issues.append(
                f"Character '{name}': lineage is '{resolved[1]}', "
                f"but lineage's members list doesn't include them"
            )

    # Lineage→members: member should have lineage set
    for slug, data in lineages.items():
        meta = data["meta"]
        lname = meta.get("name", slug)
        for m_ref in meta.get("members", []) or []:
            if not m_ref:
                continue
            resolved = resolve_ref(m_ref, name_index)
            if not resolved or resolved[0] != "character":
                continue
            char_data = characters.get(resolved[2])
            if not char_data:
                continue
            char_fl = char_data["meta"].get("family_links", {}) or {}
            char_lineage = char_fl.get("lineage", "")
            if char_lineage:
                cl_resolved = resolve_ref(char_lineage, name_index)
                if cl_resolved and cl_resolved[2] == slug:
                    continue
            issues.append(
                f"Lineage '{lname}': lists '{resolved[1]}' as member, "
                f"but character's family_links.lineage doesn't match"
            )


def validate_business_rules(entities, name_index, calendar, issues, warnings):
    """Validate business rules: parent age, faction leaders, image prompts."""
    characters = entities.get("character", {})
    factions = entities.get("faction", {})
    events = entities.get("event", {})

    # ── Helper: parse age as integer from age string ─────────────────────────
    def parse_age(age_val):
        """Extract first integer from an age value. Returns int or None."""
        if age_val is None:
            return None
        if isinstance(age_val, (int, float)):
            return int(age_val)
        if isinstance(age_val, str):
            m = re.search(r'\d+', age_val)
            return int(m.group()) if m else None
        return None

    # ── Minimum parent age 16 (ERROR) ────────────────────────────────────────
    for slug, data in characters.items():
        meta = data["meta"]
        name = meta.get("name", slug)
        fl = meta.get("family_links", {}) or {}
        children = fl.get("children", []) or []
        if not children:
            continue

        parent_age = parse_age(meta.get("age"))
        if parent_age is None:
            continue

        for child_ref in children:
            if not child_ref:
                continue
            resolved = resolve_ref(child_ref, name_index)
            if not resolved or resolved[0] != "character":
                continue
            child_data = characters.get(resolved[2])
            if not child_data:
                continue
            child_age = parse_age(child_data["meta"].get("age"))
            if child_age is None:
                continue

            # parent_birth = current_year - parent_age
            # child_birth = current_year - child_age
            # parent_birth + 16 <= child_birth
            # (current_year - parent_age) + 16 <= (current_year - child_age)
            # Simplifies to: parent_age - child_age >= 16
            age_diff = parent_age - child_age
            if age_diff < 16:
                issues.append(
                    f"Character '{name}' (age {parent_age}): child '{resolved[1]}' "
                    f"(age {child_age}) — age difference {age_diff} is less than 16"
                )

    # ── Faction leader validity ──────────────────────────────────────────────
    for slug, data in factions.items():
        meta = data["meta"]
        fname = meta.get("name", slug)
        leader = meta.get("leader", "")
        if not leader:
            warnings.append(f"Faction '{fname}': no leader set")
            continue
        resolved = resolve_ref(leader, name_index)
        if not resolved:
            continue
        if resolved[0] != "character":
            continue
        char_data = characters.get(resolved[2])
        if not char_data:
            continue
        if char_data["meta"].get("status") == "dead":
            issues.append(
                f"Faction '{fname}': leader '{resolved[1]}' has status 'dead'"
            )

    # ── Image prompt completeness (WARNING) ──────────────────────────────────
    # Characters with notable roles
    notable_roles = {"protagonist", "antagonist", "supporting", "major"}
    for slug, data in characters.items():
        meta = data["meta"]
        if meta.get("role", "") not in notable_roles:
            continue
        descs = meta.get("descriptions", {}) or {}
        if not descs.get("image_prompt"):
            warnings.append(
                f"Character '{meta.get('name', slug)}' (role={meta.get('role')}): "
                f"missing descriptions.image_prompt"
            )

    # Locations: cities and towns
    city_types = {"city", "town"}
    for slug, data in entities.get("location", {}).items():
        meta = data["meta"]
        if meta.get("type", "") not in city_types:
            continue
        descs = meta.get("descriptions", {}) or {}
        if not descs.get("image_prompt"):
            warnings.append(
                f"Location '{meta.get('name', slug)}' (type={meta.get('type')}): "
                f"missing descriptions.image_prompt"
            )

    # Factions with specific types need heraldry.image_prompt
    heraldry_types = {"government", "military", "religious", "religious-guild", "military-scholarly"}
    for slug, data in factions.items():
        meta = data["meta"]
        if meta.get("type", "") not in heraldry_types:
            continue
        heraldry = meta.get("heraldry", {}) or {}
        if not heraldry.get("image_prompt"):
            warnings.append(
                f"Faction '{meta.get('name', slug)}' (type={meta.get('type')}): "
                f"missing heraldry.image_prompt"
            )

    # Species, races, items: all need descriptions.image_prompt
    for etype in ("species", "race", "item"):
        for slug, data in entities.get(etype, {}).items():
            meta = data["meta"]
            descs = meta.get("descriptions", {}) or {}
            if not descs.get("image_prompt"):
                warnings.append(
                    f"{etype.capitalize()} '{meta.get('name', slug)}': "
                    f"missing descriptions.image_prompt"
                )

    # ── Voice completeness (WARNING) ──────────────────────────────────────────
    for slug, data in characters.items():
        meta = data["meta"]
        if meta.get("role", "") not in notable_roles:
            continue
        voice = meta.get("voice", {}) or {}
        if not voice.get("sample_text"):
            warnings.append(
                f"Character '{meta.get('name', slug)}' (role={meta.get('role')}): "
                f"missing voice.sample_text for TTS generation"
            )
        if not voice.get("description"):
            warnings.append(
                f"Character '{meta.get('name', slug)}' (role={meta.get('role')}): "
                f"missing voice.description for TTS voice design"
            )


# ═══════════════════════════════════════════════════════════════════════════════
# FAMILY — build and display family trees from character family_links
# ═══════════════════════════════════════════════════════════════════════════════

def cmd_family(args):
    """Display a family tree for a lineage or character."""
    project_dir = find_project(args.project)
    if not project_dir:
        print("Error: No project.yaml found.")
        sys.exit(1)

    entities = collect_entities(project_dir)
    characters = entities.get("character", {})
    lineages = entities.get("lineage", {})
    target = args.name

    # Try to find as lineage first, then character
    target_slug = slugify(target)
    lineage = lineages.get(target_slug)

    if lineage:
        # Show full lineage tree
        meta = lineage["meta"]
        print(f"\n👑 {meta.get('name', target)} — Family Tree")
        if meta.get("heraldry", {}).get("motto"):
            print(f"   \"{meta['heraldry']['motto']}\"")
        print()

        members = meta.get("members", []) or []
        member_slugs = {slugify(m) for m in members}
    else:
        # Find character and build tree from their family_links
        char = characters.get(target_slug)
        if not char:
            # Try name match
            for s, d in characters.items():
                if d["meta"].get("name", "").lower() == target.lower():
                    char = d
                    target_slug = s
                    break
        if not char:
            print(f"Error: No lineage or character named '{target}' found.")
            sys.exit(1)

        # Collect all family members by walking links
        member_slugs = set()
        to_visit = [target_slug]
        while to_visit:
            current = to_visit.pop()
            if current in member_slugs or current not in characters:
                continue
            member_slugs.add(current)
            fl = characters[current]["meta"].get("family_links", {}) or {}
            for link_type in ["father", "mother"]:
                ref = fl.get(link_type, "")
                if ref:
                    to_visit.append(slugify(ref))
            for link_type in ["children", "siblings", "spouse"]:
                for ref in fl.get(link_type, []) or []:
                    if ref:
                        to_visit.append(slugify(ref))

        print(f"\n🌳 Family Tree — {char['meta'].get('name', target)}\n")

    # Build adjacency from family_links
    family_graph = {}  # slug → { name, father, mother, children, spouse, status, species }
    for slug in member_slugs:
        char = characters.get(slug)
        if not char:
            continue
        meta = char["meta"]
        fl = meta.get("family_links", {}) or {}
        family_graph[slug] = {
            "name": meta.get("name", slug),
            "father": slugify(fl.get("father", "")) if fl.get("father") else "",
            "mother": slugify(fl.get("mother", "")) if fl.get("mother") else "",
            "children": [slugify(c) for c in (fl.get("children", []) or []) if c],
            "spouse": [slugify(s) for s in (fl.get("spouse", []) or []) if s],
            "status": meta.get("status", "alive"),
            "species": meta.get("species", ""),
            "gender": meta.get("gender", ""),
            "birth_order": fl.get("birth_order", 0),
            "legitimacy": fl.get("legitimacy", "legitimate"),
        }

    # Find roots (people with no parents in the graph)
    roots = [s for s, g in family_graph.items()
             if not g["father"] or g["father"] not in family_graph]
    # De-duplicate: if someone is a root and also a child of a root, prefer the parent
    root_set = set(roots)
    for slug in list(root_set):
        g = family_graph[slug]
        if g["father"] in root_set or g["mother"] in root_set:
            if g["father"] in root_set:
                root_set.discard(slug)

    if not roots:
        roots = list(family_graph.keys())[:1]

    def status_icon(status):
        return {"alive": "●", "dead": "✝", "unknown": "?", "missing": "◌"}.get(status, "○")

    def print_person(slug, depth=0, seen=None):
        if seen is None:
            seen = set()
        if slug in seen or slug not in family_graph:
            return
        seen.add(slug)
        g = family_graph[slug]
        indent = "  │ " * depth
        icon = status_icon(g["status"])
        legit = "" if g["legitimacy"] == "legitimate" else f" ({g['legitimacy']})"
        spouse_str = ""
        for sp in g["spouse"]:
            if sp in family_graph:
                sp_name = family_graph[sp]["name"]
                spouse_str = f" ⚭ {sp_name}"
                break
        print(f"{indent}  {icon} {g['name']}{legit}{spouse_str}")
        for child in sorted(g["children"], key=lambda c: family_graph.get(c, {}).get("birth_order", 0)):
            print_person(child, depth + 1, seen)

    seen = set()
    for root in sorted(root_set, key=lambda s: family_graph[s]["name"]):
        print_person(root, 0, seen)

    print(f"\n  {len(family_graph)} family member(s)\n")


# ═══════════════════════════════════════════════════════════════════════════════
# LANGUAGES — display language family tree
# ═══════════════════════════════════════════════════════════════════════════════

def cmd_languages(args):
    """Display language families and intelligibility map."""
    project_dir = find_project(args.project)
    if not project_dir:
        print("Error: No project.yaml found.")
        sys.exit(1)

    entities = collect_entities(project_dir)
    langs = entities.get("language", {})

    if not langs:
        print("\nNo languages defined yet.")
        return

    config = load_project(project_dir)
    print(f"\n🗣️  Languages — {config.get('title', 'Untitled')}\n")

    # Group by family
    families = {}
    orphans = []
    for slug, data in langs.items():
        meta = data["meta"]
        family_info = meta.get("family") or {}
        fam_name = family_info.get("family_name", "")
        if fam_name:
            families.setdefault(fam_name, []).append((slug, meta))
        else:
            orphans.append((slug, meta))

    # Build parent→child trees within each family
    for fam_name, members in sorted(families.items()):
        print(f"  ┌─ {fam_name} Family ─────────────────────")

        # Find roots (no parent_language or parent not in family)
        member_slugs = {s for s, _ in members}
        roots = []
        for slug, meta in members:
            parent = (meta.get("family") or {}).get("parent_language", "")
            if not parent or slugify(parent) not in member_slugs:
                roots.append((slug, meta))

        def print_lang(slug, meta, depth=0):
            indent = "  │ " + "  " * depth
            name = meta.get("name", slug)
            status = meta.get("status", "living")
            speakers = (meta.get("speakers") or {}).get("total_speakers", "")
            sp_str = f" ({speakers})" if speakers else ""
            status_icon = {"living": "●", "endangered": "⚠", "dead": "✝", "extinct": "✗", "proto": "◇", "ancient": "◈", "constructed": "⚙", "divine": "★"}.get(status, "○")
            print(f"{indent}{status_icon} {name}{sp_str} [{status}]")

            # Print intelligibility
            for entry in meta.get("intelligibility", []) or []:
                if isinstance(entry, dict):
                    target = entry.get("language", "?")
                    score = entry.get("score", 0)
                    bar = "█" * int(score * 10) + "░" * (10 - int(score * 10))
                    print(f"{indent}  ↔ {target}: {bar} {score:.1f}")

            # Find children
            children = (meta.get("family") or {}).get("child_languages", []) or []
            for child_ref in children:
                child_slug = slugify(child_ref)
                for s, m in members:
                    if s == child_slug:
                        print_lang(s, m, depth + 1)

        for slug, meta in sorted(roots, key=lambda x: x[1].get("name", "")):
            print_lang(slug, meta, 0)
        print(f"  └{'─' * 42}")

    if orphans:
        print(f"\n  ┌─ Unaffiliated Languages ────────────────")
        for slug, meta in orphans:
            name = meta.get("name", slug)
            status = meta.get("status", "living")
            print(f"  │ ○ {name} [{status}]")
        print(f"  └{'─' * 42}")

    print(f"\n  {len(langs)} language(s) total\n")


# ═══════════════════════════════════════════════════════════════════════════════
# PEOPLES — display species and race summary
# ═══════════════════════════════════════════════════════════════════════════════

def cmd_peoples(args):
    """Display species, races, and their relationships."""
    project_dir = find_project(args.project)
    if not project_dir:
        print("Error: No project.yaml found.")
        sys.exit(1)

    entities = collect_entities(project_dir)
    species_data = entities.get("species", {})
    races_data = entities.get("race", {})

    if not species_data:
        print("\nNo species defined yet.")
        return

    config = load_project(project_dir)
    print(f"\n🧬 Peoples — {config.get('title', 'Untitled')}\n")

    for slug, data in sorted(species_data.items(), key=lambda x: x[1]["meta"].get("name", "")):
        meta = data["meta"]
        name = meta.get("name", slug)
        sentience = meta.get("sentience", "?")
        bio = meta.get("biology") or {}
        classification = bio.get("classification", "?")
        lifespan = bio.get("lifespan", "?")
        habitat = meta.get("habitat") or {}
        pop = habitat.get("population_estimate", "?")
        trend = habitat.get("population_trend", "?")

        sent_icon = {"sapient": "🧠", "semi-sapient": "🐵", "non-sapient": "🐾", "hive-mind": "🐝", "artificial": "⚙️", "unknown": "❓"}.get(sentience, "?")
        print(f"  {sent_icon} {name} [{classification}]")
        print(f"    Sentience: {sentience} | Lifespan: {lifespan} | Pop: {pop} ({trend})")

        # Show races
        races = meta.get("races", []) or []
        race_names = []
        for race_ref in races:
            race_slug = slugify(race_ref)
            race_data = races_data.get(race_slug)
            if race_data:
                race_names.append(race_data["meta"].get("name", race_ref))
            else:
                race_names.append(race_ref)
        if race_names:
            print(f"    Races: {', '.join(race_names)}")

        # Show languages
        culture = meta.get("culture") or {}
        langs = culture.get("languages", [])
        if langs:
            print(f"    Languages: {', '.join(langs)}")

        # Show relationships
        rels = meta.get("relationships", []) or []
        for rel in rels:
            if isinstance(rel, dict):
                target = rel.get("species", "?")
                disp = rel.get("disposition", "neutral")
                interbreed = " [can interbreed]" if rel.get("can_interbreed") else ""
                print(f"    → {target}: {disp}{interbreed}")

        print()


# ═══════════════════════════════════════════════════════════════════════════════
# ECONOMY — display economic overview
# ═══════════════════════════════════════════════════════════════════════════════

def cmd_economy(args):
    """Display economic overview: resources, trade routes, production."""
    project_dir = find_project(args.project)
    if not project_dir:
        print("Error: No project.yaml found.")
        sys.exit(1)

    eco_file = project_dir / "world" / "economy.yaml"
    if not eco_file.exists():
        print("\n⚠ No economy.yaml found in world/")
        print("  Copy from templates/economy/_template.yaml to get started.")
        return

    with open(eco_file) as f:
        eco = yaml.safe_load(f) or {}

    config = load_project(project_dir)
    title = config.get("title", "Untitled")

    print(f"\n💰 Economy — {title}\n")

    # Currencies
    currencies = eco.get("currencies", [])
    if currencies:
        print("  ┌─ CURRENCIES ─────────────────────────────")
        for cur in currencies:
            name = cur.get("name", "?")
            symbol = cur.get("symbol", "")
            denoms = cur.get("denominations", [])
            denom_str = ", ".join(f"{d['name']} ({d['value']})" for d in denoms)
            print(f"  │ {symbol} {name}: {denom_str}")
        print(f"  └{'─' * 46}")

    # Resources
    resources = eco.get("resources", [])
    if resources:
        print(f"\n  ┌─ RESOURCES ({len(resources)}) ────────────────────────")
        for res in resources:
            name = res.get("name", "?")
            cat = res.get("category", "?")
            rarity = res.get("rarity", "?")
            value = res.get("base_value", "?")
            rarity_icon = {"abundant": "●●●", "common": "●●", "uncommon": "●", "rare": "◆", "very-rare": "◆◆", "unique": "★"}.get(rarity, "?")
            print(f"  │ {rarity_icon} {name:<22} [{cat}] {value}")
        print(f"  └{'─' * 46}")

    # Production
    production = eco.get("production", [])
    if production:
        print(f"\n  ┌─ PRODUCTION ({len(production)}) ──────────────────────")
        for prod in production:
            res = prod.get("resource", "?")
            loc = prod.get("location", "?")
            output = prod.get("output", "?")
            status = prod.get("status", "active")
            quality = prod.get("quality", "standard")
            s_icon = "✓" if status == "active" else "✗"
            print(f"  │ {s_icon} {loc}: {res} → {output} [{quality}]")
        print(f"  └{'─' * 46}")

    # Trade routes
    routes = eco.get("trade_routes", [])
    if routes:
        print(f"\n  ┌─ TRADE ROUTES ({len(routes)}) ────────────────────")
        for route in routes:
            name = route.get("name", "?")
            frm = route.get("from_location", "?")
            to = route.get("to_location", "?")
            value = route.get("annual_value", "?")
            status = route.get("status", "active")
            goods = route.get("goods", [])
            s_icon = "✓" if status == "active" else "✗"
            print(f"  │ {s_icon} {name}")
            print(f"  │   {frm} ↔ {to}  ({value}/year)")
            for g in goods:
                res = g.get("resource", "?")
                direction = g.get("direction", "both")
                vol = g.get("volume", "?")
                arrow = {"outbound": "→", "inbound": "←", "both": "↔"}.get(direction, "↔")
                print(f"  │   {arrow} {res}: {vol}")
            risks = route.get("risks", [])
            if risks:
                print(f"  │   ⚠ Risks: {', '.join(risks)}")
        print(f"  └{'─' * 46}")

    # Rules summary
    rules = eco.get("rules", {})
    if rules:
        print(f"\n  Economic rules:")
        print(f"    Currency: {rules.get('primary_currency', '?')}")
        print(f"    Barter: {'yes' if rules.get('barter_common') else 'no'}")
        print(f"    Banking: {'yes' if rules.get('banking_exists') else 'no'}")
        print(f"    Guilds: {'yes' if rules.get('guild_system') else 'no'}")
        print(f"    Black market: {'yes' if rules.get('black_market') else 'no'}")
    print()


# ═══════════════════════════════════════════════════════════════════════════════
# GENERATE — procedural history generation prompt builder
# ═══════════════════════════════════════════════════════════════════════════════

def cmd_generate(args):
    """Generate a procedural history prompt from world state."""
    project_dir = find_project(args.project)
    if not project_dir:
        print("Error: No project.yaml found.")
        sys.exit(1)

    config = load_project(project_dir)
    entities = collect_entities(project_dir)
    calendar = load_calendar(project_dir)

    gen_type = args.gen_type
    years = int(args.years) if hasattr(args, 'years') and args.years else 100

    # Gather world state for the prompt
    species_data = entities.get("species", {})
    factions = entities.get("faction", {})
    locations = entities.get("location", {})
    events = entities.get("event", {})
    world_flags = config.get("world_flags", {})
    style = config.get("style", {})

    # Load economy if present
    eco_file = project_dir / "world" / "economy.yaml"
    economy = {}
    if eco_file.exists():
        with open(eco_file) as f:
            economy = yaml.safe_load(f) or {}

    lines = []
    lines.append(f"# Procedural History Generation — {config.get('title', 'Untitled')}")
    lines.append(f"## Task: Generate {years} years of history\n")

    lines.append("## World State\n")
    lines.append(f"Genre: {config.get('genre', '?')}")
    lines.append(f"Calendar: {calendar.get('name', 'unknown')}")

    # Eras
    eras = calendar.get("eras", [])
    if eras:
        lines.append(f"\nEras: {', '.join(e.get('name', '?') + ' (' + e.get('prefix', '?') + ')' for e in eras)}")

    # Species summary
    if species_data:
        lines.append(f"\n### Species ({len(species_data)})")
        for slug, data in species_data.items():
            m = data["meta"]
            pop = (m.get("habitat") or {}).get("population_estimate", "?")
            lines.append(f"- {m.get('name', slug)}: {m.get('sentience', '?')}, pop ~{pop}")

    # Factions
    if factions:
        lines.append(f"\n### Factions ({len(factions)})")
        for slug, data in factions.items():
            m = data["meta"]
            lines.append(f"- {m.get('name', slug)}: {m.get('status', '?')}")
            goals = m.get("goals", [])
            if goals:
                lines.append(f"  Goals: {', '.join(goals[:3])}")

    # Locations
    if locations:
        lines.append(f"\n### Locations ({len(locations)})")
        for slug, data in locations.items():
            m = data["meta"]
            lines.append(f"- {m.get('name', slug)} [{m.get('type', '?')}]: pop {m.get('population', '?')}")

    # Economy summary
    if economy:
        resources = economy.get("resources", [])
        if resources:
            lines.append(f"\n### Resources ({len(resources)})")
            for res in resources:
                lines.append(f"- {res.get('name', '?')} [{res.get('category', '?')}]: {res.get('rarity', '?')}")

    # Existing timeline (last N events for context)
    if events:
        def _event_sort_key(item):
            m = item[1]["meta"]
            d = m.get("date", m.get("start_date", ""))
            if isinstance(d, dict):
                return (d.get("era_prefix", ""), d.get("year", 0), item[0])
            return (str(d), 0, item[0])
        sorted_events = sorted(events.items(), key=_event_sort_key)
        last_events = sorted_events[-10:]
        lines.append(f"\n### Existing Timeline (last {len(last_events)} events)")
        for slug, data in last_events:
            m = data["meta"]
            d = m.get("date", m.get("start_date", "?"))
            date_str = d.get("display", str(d)) if isinstance(d, dict) else str(d)
            lines.append(f"- [{date_str}] {m.get('name', slug)} ({m.get('type', '?')})")

    # World flags summary
    lines.append("\n### World Constraints")
    if world_flags:
        tech = world_flags.get("technology", {})
        for flag_name, flag_data in tech.items():
            if isinstance(flag_data, dict):
                val = flag_data.get("value")
                if val is False:
                    lines.append(f"- NO {flag_name}")
                elif val is True:
                    lines.append(f"- HAS {flag_name}")

    # Generation instructions
    lines.append(f"\n## Generation Instructions")
    lines.append(f"Generate {years} years of history for this world.")
    lines.append("Output as a sequence of event YAML frontmatter blocks.\n")

    if gen_type == "peaceful":
        lines.append("Focus on: discoveries, foundings, cultural developments, trade, population growth, alliances.")
    elif gen_type == "conflict":
        lines.append("Focus on: wars, rebellions, sieges, betrayals, power struggles, resource conflicts.")
    elif gen_type == "catastrophe":
        lines.append("Focus on: plagues, natural disasters, magical cataclysms, economic collapses, extinctions.")
    elif gen_type == "mixed":
        lines.append("Mix of: wars, discoveries, foundings, plagues, trade developments, cultural shifts. Realistic ebb and flow.")
    else:
        lines.append("Generate a realistic mix of events. History has periods of peace and conflict, growth and decline.")

    lines.append("""
For each event, output:
```yaml
---
name: "Event Name"
type: war|battle|birth|death|founding|discovery|plague|cataclysm|trade_agreement|coronation|rebellion|treaty|milestone
date: "ERA YEAR"                    # or start_date/end_date for duration events
significance: trivial|minor|moderate|major|world-changing
scope: personal|local|regional|national|continental|global
participants:
  - entity: "entity-slug"
    role: "description"
locations: ["location-slug"]
caused_by: ["previous-event-slug"]
leads_to: ["next-event-slug"]
economic_impact:
  production_effects: []
  trade_effects: []
---
Brief description of the event and its consequences.
```

Rules:
- Events must be chronologically ordered
- Causality chains must be logical (cause precedes effect)
- Respect ALL world flags (no gunpowder tech if flag is false, etc.)
- Dead characters cannot participate in later events
- Reference existing entities by their slugs
- You may create NEW entities (characters, factions, locations) as needed
- Economic impacts should cascade realistically
""")

    prompt = "\n".join(lines)

    # Save the generation prompt
    output_dir = project_dir / "output"
    output_dir.mkdir(exist_ok=True)
    gen_file = output_dir / f"generate-history-{gen_type}-{years}y.md"
    with open(gen_file, "w") as f:
        f.write(prompt)

    print(f"\n🎲 History Generation Prompt — {years} years ({gen_type})\n")
    print(prompt)
    print(f"\n{'=' * 60}")
    print(f"✓ Prompt saved to: {gen_file.relative_to(project_dir)}")
    print(f"\nFeed this prompt to Claude to generate history events.")
    print(f"Then save the output as .md files in world/events/")


# ═══════════════════════════════════════════════════════════════════════════════
# WRITE — Claude context-aware writing integration
# ═══════════════════════════════════════════════════════════════════════════════

def cmd_write(args):
    """Build a context-loaded writing prompt for Claude."""
    project_dir = find_project(args.project)
    if not project_dir:
        print("Error: No project.yaml found.")
        sys.exit(1)

    config = load_project(project_dir)
    entities = collect_entities(project_dir)
    style = config.get("style", {})
    prose_style = style.get("prose", {})

    chapter_num = int(args.chapter) if hasattr(args, 'chapter') and args.chapter else None

    # Determine what we're writing
    if chapter_num:
        # Find the chapter
        chapters = entities.get("chapter", {})
        target_ch = None
        for slug, data in chapters.items():
            if data["meta"].get("number") == chapter_num:
                target_ch = data
                break
        if not target_ch:
            print(f"Chapter {chapter_num} not found. Use 'add chapter' first.")
            sys.exit(1)
        ch_meta = target_ch["meta"]
        ch_body = target_ch.get("body", "").strip()
    else:
        ch_meta = {}
        ch_body = ""

    lines = []
    lines.append(f"# Writing Session — {config.get('title', 'Untitled')}")
    if chapter_num:
        lines.append(f"## Chapter {chapter_num}: {ch_meta.get('title', 'Untitled')}\n")

    # ── STYLE DIRECTIVES ──────────────────────────────────────────────────────
    lines.append("## Style Directives\n")
    lines.append(f"Prose preset: **{prose_style.get('preset', 'literary')}**")
    lines.append(f"POV: {prose_style.get('pov', 'third-limited')}")
    lines.append(f"Tense: {prose_style.get('tense', 'past')}")
    lines.append(f"Formality: {prose_style.get('formality', 'neutral')}")
    lines.append(f"Vocabulary: {prose_style.get('vocabulary', 'moderate')}")
    lines.append(f"Profanity: {prose_style.get('profanity', 'invented-only')}")
    lines.append(f"Content rating: {prose_style.get('content_rating', 'adult')}")
    lines.append(f"Sensory emphasis: {', '.join(prose_style.get('sensory_emphasis', ['sight', 'sound', 'smell']))}")
    lines.append(f"Target length: {config.get('chapter_target_words', 3000)} words\n")

    # ── WORLD FLAGS (compressed) ──────────────────────────────────────────────
    world_flags = config.get("world_flags", {})
    if world_flags:
        lines.append("## World Rules (MUST follow)\n")
        tech = world_flags.get("technology", {})
        for flag_name, flag_data in tech.items():
            if isinstance(flag_data, dict):
                val = flag_data.get("value")
                if val is False:
                    lines.append(f"- ✗ NO {flag_name}")
                elif val is True:
                    lines.append(f"- ✓ HAS {flag_name}")

    # ── CHARACTER SHEETS (machine descriptions) ──────────────────────────────
    characters_present = ch_meta.get("characters_present", []) if ch_meta else []
    pov_char = ch_meta.get("pov", "") if ch_meta else ""
    relevant_chars = set(characters_present)
    if pov_char:
        relevant_chars.add(pov_char)

    # If no chapter metadata, include all characters
    if not relevant_chars:
        relevant_chars = set(entities.get("character", {}).keys())

    chars = entities.get("character", {})
    if relevant_chars and chars:
        lines.append("\n## Characters in Scene\n")
        for slug in relevant_chars:
            char = chars.get(slugify(slug))
            if not char:
                # Try name match
                for s, d in chars.items():
                    if d["meta"].get("name", "").lower() == slug.lower():
                        char = d
                        break
            if char:
                meta = char["meta"]
                name = meta.get("name", slug)
                is_pov = " ← POV" if slugify(slug) == slugify(pov_char) else ""
                lines.append(f"### {name}{is_pov}\n")

                # Use machine description if available
                descs = meta.get("descriptions", {})
                machine = descs.get("machine", {})
                if machine:
                    for key, val in machine.items():
                        if val:
                            lines.append(f"**{key}**: {val}")
                else:
                    # Fallback to basic fields
                    lines.append(f"Species: {meta.get('species', '?')}, Age: {meta.get('age', '?')}")
                    lines.append(f"Traits: {', '.join(meta.get('traits', []))}")

                # Voice for dialogue
                voice = machine.get("voice", "")
                if voice:
                    lines.append(f"\n**Dialogue voice**: {voice}")

                lines.append("")

    # ── LOCATION CONTEXT ──────────────────────────────────────────────────────
    ch_locations = ch_meta.get("locations", []) if ch_meta else []
    locs = entities.get("location", {})
    if ch_locations and locs:
        lines.append("## Locations in Scene\n")
        for loc_ref in ch_locations:
            loc = locs.get(slugify(loc_ref))
            if loc:
                meta = loc["meta"]
                descs = meta.get("descriptions", {})
                machine = descs.get("machine", {})
                lines.append(f"### {meta.get('name', loc_ref)}\n")
                if machine:
                    for key, val in machine.items():
                        if val:
                            lines.append(f"**{key}**: {val}")
                else:
                    lines.append(f"Type: {meta.get('type', '?')}, Climate: {meta.get('climate', '?')}")
                lines.append("")

    # ── TIMELINE CONTEXT ──────────────────────────────────────────────────────
    events = entities.get("event", {})
    if events:
        lines.append("## Recent Timeline Context\n")
        def _evt_sort(item):
            m = item[1]["meta"]
            d = m.get("date", m.get("start_date", ""))
            if isinstance(d, dict):
                return (d.get("era_prefix", ""), d.get("year", 0), item[0])
            return (str(d), 0, item[0])
        sorted_events = sorted(events.items(), key=_evt_sort)
        for slug, data in sorted_events[-8:]:
            m = data["meta"]
            d = m.get("date", m.get("start_date", "?"))
            date_str = d.get("display", str(d)) if isinstance(d, dict) else str(d)
            lines.append(f"- [{date_str}] {m.get('name', slug)}")
        lines.append("")

    # ── PREVIOUS CHAPTER SUMMARY ──────────────────────────────────────────────
    if chapter_num and chapter_num > 1:
        chapters = entities.get("chapter", {})
        prev_chs = [(s, d) for s, d in chapters.items()
                     if d["meta"].get("number", 0) < chapter_num]
        prev_chs.sort(key=lambda x: x[1]["meta"].get("number", 0))
        if prev_chs:
            lines.append("## Previous Chapter(s)\n")
            for slug, data in prev_chs[-3:]:  # Last 3 chapters
                m = data["meta"]
                body = data.get("body", "").strip()
                wc = len(body.split())
                lines.append(f"### Ch {m.get('number', '?')}: {m.get('title', slug)} ({wc}w)\n")
                if body and len(body) > 200:
                    lines.append(f"*(Provide full text when executing)*\n")
                elif body:
                    lines.append(body + "\n")

    # ── CHAPTER OUTLINE / EXISTING CONTENT ────────────────────────────────────
    if ch_meta:
        lines.append("## Chapter Plan\n")
        summary = ch_meta.get("summary", "")
        if summary:
            lines.append(f"Summary: {summary}")
        scene_list = ch_meta.get("scenes", [])
        if scene_list:
            lines.append("Scenes:")
            for scene in scene_list:
                lines.append(f"  - {scene}")
        if ch_body:
            lines.append(f"\n## Existing Draft ({len(ch_body.split())} words)\n")
            lines.append(ch_body)

    # ── WRITING INSTRUCTIONS ──────────────────────────────────────────────────
    lines.append("\n## Instructions\n")
    lines.append(f"Write {'Chapter ' + str(chapter_num) if chapter_num else 'the next chapter'} following these rules:")
    lines.append(f"1. Match the **{prose_style.get('preset', 'literary')}** prose style exactly")
    lines.append(f"2. Stay in **{prose_style.get('pov', 'third-limited')}** POV, **{prose_style.get('tense', 'past')}** tense")
    lines.append("3. Use character machine_descriptions for physical/behavioral consistency")
    lines.append("4. Respect ALL world flags — no anachronisms")
    lines.append("5. Characters use their established voice patterns for dialogue")
    lines.append(f"6. Profanity: {prose_style.get('profanity', 'invented-only')} (use in-world oaths)")
    lines.append(f"7. Target: {config.get('chapter_target_words', 3000)} words")
    lines.append("8. End with a hook that drives the reader to the next chapter")

    prompt = "\n".join(lines)

    # Save
    output_dir = project_dir / "output" / "writing"
    output_dir.mkdir(parents=True, exist_ok=True)
    ch_label = f"ch-{chapter_num:03d}" if chapter_num else "next"
    write_file = output_dir / f"write-{ch_label}.md"
    with open(write_file, "w") as f:
        f.write(prompt)

    print(f"\n✍️  Writing Prompt — {config.get('title', 'Untitled')}")
    if chapter_num:
        print(f"   Chapter {chapter_num}: {ch_meta.get('title', '?')}")
    print(f"\n{'=' * 60}")
    print(prompt[:2000])
    if len(prompt) > 2000:
        print(f"\n... ({len(prompt)} chars total, truncated in terminal)")
    print(f"\n{'=' * 60}")
    print(f"✓ Full prompt saved to: {write_file.relative_to(project_dir)}")
    print(f"  Context size: {len(prompt):,} chars")
    print(f"\nFeed this prompt to Claude (ideally with 1M context) to write.")


# ═══════════════════════════════════════════════════════════════════════════════
# STORY — In-universe short story generator
# ═══════════════════════════════════════════════════════════════════════════════

def cmd_story(args):
    project_dir = find_project(args.project)
    if not project_dir:
        print("Error: No project.yaml found.")
        sys.exit(1)

    config = load_project(project_dir)
    entities = collect_entities(project_dir)
    calendar = load_calendar(project_dir)
    name_index = build_name_index(entities)

    # Validate arguments
    has_event = hasattr(args, "event") and args.event
    has_era = hasattr(args, "era") and args.era
    has_start_year = hasattr(args, "start_year") and args.start_year is not None

    if not has_event and not (has_era and has_start_year):
        print("Error: Must specify either --event or (--era and --start-year).")
        sys.exit(1)

    # Resolve anchor
    if has_event:
        ref = resolve_ref(args.event, name_index)
        if not ref:
            print(f"Error: Event '{args.event}' not found.")
            sys.exit(1)
        anchor_type = "event"
        anchor_value = ref[2]  # slug
        anchor_label = ref[1]  # display name
    else:
        anchor_type = "period"
        end_year = args.end_year if hasattr(args, "end_year") and args.end_year is not None else args.start_year
        anchor_value = {"era": args.era, "start_year": args.start_year, "end_year": end_year}
        anchor_label = f"{args.era} {args.start_year}–{end_year}"

    # Resolve protagonist
    protagonist_slug = None
    protagonist_name = "generate"
    protagonist_data = None
    if hasattr(args, "protagonist") and args.protagonist and args.protagonist != "generate":
        ref = resolve_ref(args.protagonist, name_index)
        if not ref:
            print(f"Error: Character '{args.protagonist}' not found.")
            sys.exit(1)
        protagonist_slug = ref[2]
        protagonist_name = ref[1]
        protagonist_data = entities.get("character", {}).get(protagonist_slug)

    # Gather temporal context
    ctx = gather_temporal_context(entities, calendar, anchor_type, anchor_value, config)

    # Warn if protagonist is not in active characters
    if protagonist_slug and protagonist_slug not in ctx["active_characters"]:
        print(f"Warning: Protagonist '{protagonist_name}' may not be alive during this time period.")

    # Build prompt
    chapters = args.chapters if hasattr(args, "chapters") else 12
    words = args.words if hasattr(args, "words") else 30000
    tone = args.tone if hasattr(args, "tone") and args.tone else None
    style = config.get("style", {})
    prose_style = style.get("prose", {})

    if not tone:
        tones = config.get("tone", [])
        tone = ", ".join(tones) if isinstance(tones, list) else str(tones) if tones else "epic"

    lines = []
    lines.append(f"# In-Universe Short Story — {config.get('title', 'Untitled')}")
    lines.append(f"\n## Story Parameters\n")
    lines.append(f"- Anchor: {anchor_label}")
    lines.append(f"- Target: {chapters} chapters, ~{words} words")
    lines.append(f"- Protagonist: {protagonist_name if protagonist_slug else 'Generate a new character'}")
    lines.append(f"- Tone: {tone}")

    subgenre = getattr(args, "subgenre", None)
    rating = getattr(args, "rating", None)
    if subgenre:
        lines.append(f"- Subgenre: {subgenre}")
    if rating:
        lines.append(f"- Content Rating: {rating}")

    # Style directives
    lines.append(f"\n## Style Directives\n")
    lines.append(f"Prose preset: **{prose_style.get('preset', 'literary')}**")
    lines.append(f"POV: {prose_style.get('pov', 'third-limited')}")
    lines.append(f"Tense: {prose_style.get('tense', 'past')}")
    lines.append(f"Formality: {prose_style.get('formality', 'neutral')}")
    lines.append(f"Vocabulary: {prose_style.get('vocabulary', 'moderate')}")
    lines.append(f"Profanity: {prose_style.get('profanity', 'invented-only')}")
    effective_rating = rating or prose_style.get('content_rating', 'adult')
    lines.append(f"Content rating: {effective_rating}")
    if subgenre:
        lines.append(f"Subgenre: {subgenre}")
    lines.append(f"Sensory emphasis: {', '.join(prose_style.get('sensory_emphasis', ['sight', 'sound', 'smell']))}")
    visual = style.get("visual", {})
    if visual:
        lines.append(f"Visual style: {visual.get('preset', '?')}, lighting: {visual.get('lighting', '?')}, mood: {visual.get('mood', '?')}")

    # World context
    lines.append(f"\n## World Context\n")
    lines.extend(format_world_context_block(ctx))

    # Protagonist section
    lines.append("## Protagonist\n")
    if protagonist_data:
        meta = protagonist_data["meta"]
        descs = meta.get("descriptions", {}) or {}
        machine = descs.get("machine", {}) or {}
        if machine:
            for key, val in machine.items():
                if val:
                    lines.append(f"**{key}**: {val}")
        else:
            lines.append(f"Name: {meta.get('name', protagonist_slug)}")
            lines.append(f"Species: {meta.get('species', '?')}, Age: {meta.get('age', '?')}")
        rels = meta.get("relationships", [])
        if rels:
            lines.append(f"Relationships:")
            for r in rels:
                if isinstance(r, dict):
                    lines.append(f"  - {r.get('type', '?')}: {r.get('character', r.get('name', '?'))}")
                else:
                    lines.append(f"  - {r}")
        if meta.get("faction"):
            lines.append(f"Faction: {meta['faction']}")
        if meta.get("location"):
            lines.append(f"Location: {meta['location']}")
        voice = meta.get("voice", {}) or {}
        if voice:
            lines.append(f"Voice: {voice.get('description', '')}")
        traits = meta.get("traits", [])
        if traits:
            lines.append(f"Personality: {', '.join(str(t) for t in traits)}")
        skills = meta.get("skills", [])
        if skills:
            lines.append(f"Skills: {', '.join(str(s) for s in skills)}")
    else:
        lines.append("Generate a new character appropriate for this time period.")
        lines.append("Consider the active species, factions, and locations when designing the protagonist.")
        lines.append("Give them a compelling personal stake in the anchor event or time period.")
    lines.append("")

    # Story anchor
    lines.append("## Story Anchor\n")
    if anchor_type == "event" and ctx.get("anchor_event"):
        ae = ctx["anchor_event"]
        meta = ae["meta"]
        start, end = get_event_date(meta, calendar)
        lines.append(f"**{meta.get('name', anchor_value)}**")
        lines.append(f"Date: {start.display}" + (f" — {end.display}" if end.display != start.display else ""))
        lines.append(f"Type: {meta.get('type', '?')}, Significance: {meta.get('significance', '?')}")
        participants = meta.get("participants", [])
        if participants:
            lines.append(f"Participants: {', '.join(str(p.get('entity', p) if isinstance(p, dict) else p) for p in participants)}")
        caused_by = meta.get("caused_by", [])
        if caused_by:
            lines.append(f"Caused by: {', '.join(str(c) for c in caused_by)}")
        leads_to = meta.get("leads_to", [])
        if leads_to:
            lines.append(f"Leads to: {', '.join(str(l) for l in leads_to)}")
        descs = meta.get("descriptions", {}) or {}
        machine = descs.get("machine", {}) or {}
        if machine:
            for key, val in machine.items():
                if val:
                    lines.append(f"**{key}**: {val}")
        body = ae.get("body", "").strip()
        if body:
            lines.append(f"\n{body}")
    else:
        lines.append(f"Time period: {anchor_label}")
        lines.append("Write a story set during this era, drawing on the events and tensions of the time.")
    lines.append("")

    # Writing instructions
    words_per_ch = words // chapters if chapters else words
    lines.append("## Writing Instructions\n")
    lines.append(f"You are writing a self-contained short story set in the world of {config.get('title', 'Untitled')}.\n")
    lines.append("**Structure:**")
    lines.append(f"- {chapters} chapters, approximately {words} words total")
    lines.append(f"- Each chapter: ~{words_per_ch} words, with a clear scene or narrative beat")
    lines.append("- Complete narrative arc: setup, rising action, climax, falling action, resolution\n")
    lines.append("**Constraints:**")
    lines.append("- All world rules (world flags) must be respected — see World Rules section")
    lines.append("- Technology, species, factions, and locations must match the established world")
    lines.append("- If using existing characters, their personality, voice, and appearance must match their descriptions")
    lines.append("- The story must be internally consistent with the world timeline")
    lines.append("- Events in this story should feel like they COULD be canon — they don't contradict established history\n")
    lines.append(f"**Tone:** {tone}\n")
    lines.append("**Output format:**")
    lines.append("For each chapter, output:")
    lines.append("```")
    lines.append("---")
    lines.append('name: "Chapter Title"')
    lines.append("chapter_number: N")
    lines.append('pov_character: "character-slug"')
    lines.append('location: "location-slug"')
    lines.append('summary: "One-sentence summary"')
    lines.append("---")
    lines.append("{Chapter prose}")
    lines.append("```")

    prompt = "\n".join(lines)

    # Save
    slug = slugify(anchor_label)
    output_dir = project_dir / "output" / "stories"
    output_dir.mkdir(parents=True, exist_ok=True)
    story_file = output_dir / f"story-{slug}.md"
    with open(story_file, "w") as f:
        f.write(prompt)

    print(f"\n📖 Story Prompt — {config.get('title', 'Untitled')}")
    print(f"   Anchor: {anchor_label}")
    print(f"   Protagonist: {protagonist_name if protagonist_slug else 'generate'}")
    print(f"   Target: {chapters} chapters, ~{words} words")
    print(f"\n{'=' * 60}")
    print(f"  Characters: {len(ctx['active_characters'])}")
    print(f"  Factions:   {len(ctx['active_factions'])}")
    print(f"  Locations:  {len(ctx['all_locations'])}")
    print(f"  Events:     {len(ctx['events_before'])} before / {len(ctx['events_during'])} during / {len(ctx['events_after'])} after")
    print(f"\n  Context size: {len(prompt):,} chars")
    print(f"  Saved to: {story_file.relative_to(project_dir)}")
    print(f"\nFeed this prompt to Claude to generate the story.")


# ═══════════════════════════════════════════════════════════════════════════════
# CAMPAIGN — D&D campaign/one-shot generator
# ═══════════════════════════════════════════════════════════════════════════════

def cmd_campaign(args):
    project_dir = find_project(args.project)
    if not project_dir:
        print("Error: No project.yaml found.")
        sys.exit(1)

    config = load_project(project_dir)
    entities = collect_entities(project_dir)
    calendar = load_calendar(project_dir)
    name_index = build_name_index(entities)

    # Validate arguments — must have exactly one anchor
    has_event = hasattr(args, "event") and args.event
    has_era = hasattr(args, "era") and args.era
    has_year = hasattr(args, "year") and args.year is not None
    has_present = hasattr(args, "present") and args.present

    anchor_count = sum([bool(has_event), bool(has_era and has_year), bool(has_present)])
    if anchor_count == 0:
        print("Error: Must specify one of --event, (--era and --year), or --present.")
        sys.exit(1)
    if anchor_count > 1:
        print("Error: Specify only one of --event, (--era and --year), or --present.")
        sys.exit(1)

    # Resolve location if given
    location_data = None
    location_name = None
    if hasattr(args, "location") and args.location:
        ref = resolve_ref(args.location, name_index)
        if not ref:
            print(f"Error: Location '{args.location}' not found.")
            sys.exit(1)
        location_data = entities.get("location", {}).get(ref[2])
        location_name = ref[1]

    # Map length
    length = args.length if hasattr(args, "length") else "one-shot"
    if length == "one-shot":
        sessions = 1
    elif length == "short":
        sessions = 3
    elif length == "custom":
        sessions = args.sessions if hasattr(args, "sessions") and args.sessions else 1
        if sessions < 1:
            sessions = 1
    else:
        sessions = 1

    if length == "custom" and sessions == 1:
        print("Warning: --length custom without --sessions defaults to 1 session.")

    # Determine anchor
    if has_event:
        ref = resolve_ref(args.event, name_index)
        if not ref:
            print(f"Error: Event '{args.event}' not found.")
            sys.exit(1)
        anchor_type = "event"
        anchor_value = ref[2]
        anchor_label = ref[1]
    elif has_era and has_year:
        anchor_type = "period"
        anchor_value = {"era": args.era, "start_year": args.year, "end_year": args.year}
        anchor_label = f"{args.era} {args.year}"
    else:
        anchor_type = "present"
        anchor_value = None
        anchor_label = "Present Day"

    # Gather temporal context
    ctx = gather_temporal_context(entities, calendar, anchor_type, anchor_value, config)

    level = args.level if hasattr(args, "level") else "1-4"
    tone = args.tone if hasattr(args, "tone") and args.tone else None
    themes = args.themes if hasattr(args, "themes") and args.themes else None

    if not tone:
        tones = config.get("tone", [])
        tone = ", ".join(tones) if isinstance(tones, list) else str(tones) if tones else "adventure"

    themes_list = [t.strip() for t in themes.split(",")] if themes else config.get("themes", [])

    # Build prompt
    lines = []
    lines.append(f"# D&D Campaign — {config.get('title', 'Untitled')}")
    lines.append(f"\n## Campaign Parameters\n")
    lines.append(f"- Setting: {anchor_label}")
    lines.append(f"- Length: {length} ({sessions} session(s))")
    lines.append(f"- Party Level: {level}")
    lines.append(f"- Tone: {tone}")
    lines.append(f"- Themes: {', '.join(str(t) for t in themes_list)}")
    lines.append(f"- Central Location: {location_name or 'DM choice'}")

    # World context
    lines.append(f"\n## World Context\n")
    lines.extend(format_world_context_block(ctx))

    # Location Focus
    lines.append("## Location Focus\n")
    if location_data:
        meta = location_data["meta"]
        lines.append(f"### {meta.get('name', args.location)}\n")
        descs = meta.get("descriptions", {}) or {}
        machine = descs.get("machine", {}) or {}
        if machine:
            for key, val in machine.items():
                if val:
                    lines.append(f"**{key}**: {val}")
        lines.append(f"Type: {meta.get('type', '?')}")
        if meta.get("parent"):
            lines.append(f"Parent: {meta['parent']}")
        if meta.get("population"):
            lines.append(f"Population: {meta['population']}")
        if meta.get("faction"):
            lines.append(f"Controlling faction: {meta['faction']}")
        routes = meta.get("routes", [])
        if routes:
            lines.append(f"Routes: {len(routes)} connections")
        resources = meta.get("resources", [])
        if resources:
            lines.append(f"Resources: {', '.join(str(r) for r in resources)}")
        dangers = meta.get("dangers", [])
        if dangers:
            lines.append(f"Dangers: {', '.join(str(d) for d in dangers)}")
        notable = meta.get("notable_characters", [])
        if notable:
            lines.append(f"Notable characters: {', '.join(str(n) for n in notable)}")
        body = location_data.get("body", "").strip()
        if body:
            lines.append(f"\n{body}")
    else:
        # Suggest top locations
        locs = ctx.get("all_locations", {})
        loc_list = list(locs.items())[:5]
        if loc_list:
            lines.append("Suggested locations for this time period:\n")
            for slug, data in loc_list:
                m = data["meta"]
                lines.append(f"- **{m.get('name', slug)}** [{m.get('type', '?')}]: {m.get('population', '?')}")
                descs = m.get("descriptions", {}) or {}
                human = descs.get("human", "")
                if human:
                    lines.append(f"  {str(human)[:150]}...")
        else:
            lines.append("No locations defined. DM should choose an appropriate setting.")
    lines.append("")

    # Available NPCs
    active_chars = ctx.get("active_characters", {})
    if active_chars:
        lines.append(f"## Available NPCs ({len(active_chars)})\n")
        for slug, data in active_chars.items():
            m = data["meta"]
            role_suggestion = m.get("role", "supporting")
            faction = m.get("faction", "")
            traits = m.get("traits", [])
            lines.append(f"- **{m.get('name', slug)}** ({m.get('species', '?')})")
            lines.append(f"  Role suggestion: {role_suggestion}")
            if traits:
                lines.append(f"  Traits: {', '.join(str(t) for t in traits[:5])}")
            if faction:
                lines.append(f"  Faction: {faction}")
        lines.append("")

    # Factions in play
    active_factions = ctx.get("active_factions", {})
    if active_factions:
        lines.append(f"## Factions In Play ({len(active_factions)})\n")
        for slug, data in active_factions.items():
            m = data["meta"]
            lines.append(f"### {m.get('name', slug)}")
            lines.append(f"Type: {m.get('type', '?')}, Status: {m.get('status', '?')}")
            goals = m.get("goals", [])
            if goals:
                lines.append(f"Goals: {', '.join(str(g) for g in goals)}")
            ideology = m.get("ideology", "")
            if ideology:
                lines.append(f"Ideology: {ideology}")
            rels = m.get("relationships", [])
            if rels:
                for r in rels:
                    if isinstance(r, dict):
                        lines.append(f"  - {r.get('relationship_type', '?')} with {r.get('faction', '?')}")
            lines.append("")

    # Campaign generation instructions
    lines.append("## Campaign Generation Instructions\n")
    lines.append(f"Generate a complete D&D 5e campaign module for {sessions} session(s), party level {level}.\n")

    lines.append("### Required Output — Campaign Overview\n")
    lines.append("- Campaign title and hook (1-2 paragraphs)")
    lines.append(f"- Central conflict tied to {anchor_label}")
    lines.append("- Faction dynamics and how they affect the adventure")
    lines.append("- Overall story arc across all sessions\n")

    lines.append("### Required Output — Per Session\n")
    lines.append(f"For each of the {sessions} sessions, provide:\n")
    for i in range(1, sessions + 1):
        lines.append(f"**Session {i}: {{Title}}**")
    lines.append("")
    lines.append("Each session must include:")
    lines.append("1. **Opening Scene** — how the session starts, read-aloud text")
    lines.append("2. **Key NPCs** — stat blocks (use 5e format), personality notes, voice/mannerism tips")
    lines.append("   - Draw from existing world characters where appropriate")
    lines.append("   - Generate new NPCs as needed, consistent with world species/races/factions")
    lines.append("3. **Encounters** (3-5 per session, mix of):")
    lines.append("   - Combat encounters with CR-appropriate stat blocks")
    lines.append("   - Social encounters with skill DCs and NPC motivations")
    lines.append("   - Exploration/puzzle encounters with mechanics")
    lines.append("4. **Locations** — descriptions matching world data, tactical maps (text description)")
    lines.append("5. **Rewards** — level-appropriate loot, items from world where relevant")
    lines.append("6. **Session End** — cliffhanger or transition to next session\n")

    lines.append("### Required Output — Appendices\n")
    lines.append("- Random encounter table (d20) for the campaign area")
    lines.append("- NPC quick-reference (name, species, faction, disposition, 1-line description)")
    lines.append("- Treasure table (level-appropriate)")
    lines.append("- Player handouts (letters, maps, documents — formatted as in-world text)")
    lines.append("- Magic item descriptions (if any world items are included)\n")

    # Constraints
    world_flags = ctx.get("world_flags", {})
    key_flags = []
    tech = world_flags.get("technology", {})
    if isinstance(tech, dict):
        for fn, fv in tech.items():
            if fv is True:
                key_flags.append(f"HAS {fn}")
            elif fv is False:
                key_flags.append(f"NO {fn}")
    magic = world_flags.get("magic", {})
    if isinstance(magic, dict):
        if magic.get("present") is True:
            key_flags.append("HAS magic")
        elif magic.get("present") is False:
            key_flags.append("NO magic")

    lines.append("### Constraints\n")
    lines.append(f"- Respect ALL world flags — {', '.join(key_flags[:10]) if key_flags else 'see World Rules section'}")
    lines.append("- Species and races must match world biology and culture")
    lines.append("- Locations must match established descriptions")
    lines.append("- Technology must be appropriate to the time period")
    lines.append("- Factions must behave consistently with their goals and ideology")
    lines.append("- Any existing characters used as NPCs must match their personality and voice")
    lines.append(f"- Combat balance: use 5e CR guidelines for party of 4 at level {level}")

    prompt = "\n".join(lines)

    # Save
    slug = slugify(anchor_label)
    output_dir = project_dir / "output" / "campaigns"
    output_dir.mkdir(parents=True, exist_ok=True)
    campaign_file = output_dir / f"campaign-{slug}-{length}.md"
    with open(campaign_file, "w") as f:
        f.write(prompt)

    print(f"\n🎲 Campaign Prompt — {config.get('title', 'Untitled')}")
    print(f"   Setting: {anchor_label}")
    print(f"   Length: {length} ({sessions} sessions)")
    print(f"   Level: {level}")
    if location_name:
        print(f"   Location: {location_name}")
    print(f"\n{'=' * 60}")
    print(f"  Characters: {len(ctx['active_characters'])}")
    print(f"  Factions:   {len(ctx['active_factions'])}")
    print(f"  Locations:  {len(ctx['all_locations'])}")
    print(f"  Events:     {len(ctx['events_before'])} before / {len(ctx['events_during'])} during / {len(ctx['events_after'])} after")
    print(f"\n  Context size: {len(prompt):,} chars")
    print(f"  Saved to: {campaign_file.relative_to(project_dir)}")
    print(f"\nFeed this prompt to Claude to generate the campaign module.")


# ═══════════════════════════════════════════════════════════════════════════════
# WIZARD — Interactive world creation & YOLO mode
# ═══════════════════════════════════════════════════════════════════════════════

TSHIRT_SIZES = {
    "S": {
        "label": "Small — Short Story / One-Shot",
        "species": (1, 3), "races": (1, 4), "languages": (1, 3),
        "characters": (3, 8), "locations": (2, 6), "factions": (1, 3),
        "items": (0, 3), "events": (3, 10), "lineages": (0, 2),
        "arcs": (1, 2), "magic_systems": (0, 1),
        "eras": (1, 2), "history_years": (50, 500),
        "currencies": (1, 1), "resources": (2, 5), "trade_routes": (0, 2),
        "generation_passes": 1,
    },
    "M": {
        "label": "Medium — Novel / Short Campaign",
        "species": (2, 5), "races": (3, 10), "languages": (2, 6),
        "characters": (8, 20), "locations": (5, 15), "factions": (2, 6),
        "items": (2, 8), "events": (10, 30), "lineages": (1, 4),
        "arcs": (2, 4), "magic_systems": (1, 2),
        "eras": (2, 3), "history_years": (200, 2000),
        "currencies": (1, 3), "resources": (4, 10), "trade_routes": (1, 5),
        "generation_passes": 2,
    },
    "L": {
        "label": "Large — Book Series / Full Campaign",
        "species": (4, 10), "races": (6, 20), "languages": (4, 12),
        "characters": (20, 50), "locations": (12, 35), "factions": (4, 12),
        "items": (5, 15), "events": (25, 80), "lineages": (3, 8),
        "arcs": (3, 8), "magic_systems": (1, 3),
        "eras": (3, 5), "history_years": (1000, 10000),
        "currencies": (2, 5), "resources": (8, 20), "trade_routes": (3, 10),
        "generation_passes": 3,
    },
    "XL": {
        "label": "Extra Large — Epic Universe / Sandbox",
        "species": (8, 20), "races": (12, 40), "languages": (8, 25),
        "characters": (40, 100), "locations": (25, 80), "factions": (8, 25),
        "items": (10, 30), "events": (50, 200), "lineages": (5, 15),
        "arcs": (5, 15), "magic_systems": (2, 5),
        "eras": (4, 8), "history_years": (5000, 50000),
        "currencies": (3, 10), "resources": (12, 40), "trade_routes": (5, 25),
        "generation_passes": 5,
    },
}

WIZARD_STEPS = [
    ("basics", "Project Basics", [
        ("title", "What is the name of your world or project?", None, True),
        ("genre", "Genre?", ["fantasy", "scifi", "modern", "horror", "post-apocalyptic", "steampunk", "custom"], False),
        ("project_type", "Project type?", ["novel", "series", "campaign", "game", "worldbook"], False),
        ("size", "World complexity?", ["S", "M", "L", "XL"], False),
        ("tone", "Tone / prose style?", ["literary", "pulp", "young-adult", "dark", "gritty", "epic", "litrpg", "cozy", "horror", "hard-sf", "space-opera", "noir", "fairy-tale"], False),
    ]),
    ("cosmology", "Cosmology & Physics", [
        ("creation_myth", "Brief creation myth or origin?", None, False),
        ("magic_exists", "Does magic exist?", ["yes", "no", "ambiguous"], False),
        ("calendar_name", "Name of the world's calendar?", None, False),
    ]),
    ("geography", "Geography & Climate", [
        ("world_name", "Name of the primary world/planet/realm?", None, True),
        ("notable_regions", "Key regions/continents (comma-separated)?", None, False),
        ("climate_variety", "Climate range?", ["uniform", "moderate-variety", "extreme-variety"], False),
    ]),
    ("peoples", "Species & Peoples", [
        ("species_approach", "Species approach?", ["humans-only", "few-species", "many-species", "cosmic-zoo"], False),
        ("species_hints", "Specific species to include (comma-separated)?", None, False),
        ("interbreeding", "Cross-species breeding?", ["yes", "no", "rare-exceptions"], False),
    ]),
    ("politics", "Power & Factions", [
        ("political_structure", "Dominant political structure?", ["monarchy", "republic", "tribal", "theocracy", "empire", "fragmented", "corporate", "mixed"], False),
        ("conflict_level", "Current geopolitical tension?", ["peaceful", "simmering", "active-conflict", "total-war", "post-war"], False),
        ("faction_hints", "Key factions (comma-separated)?", None, False),
    ]),
    ("history", "History & Timeline", [
        ("history_depth", "How deep is recorded history?", ["shallow", "moderate", "deep", "ancient"], False),
        ("pivotal_events", "Pivotal historical events (comma-separated)?", None, False),
    ]),
    ("protagonist", "Central Characters", [
        ("protagonist_name", "Protagonist name?", None, False),
        ("protagonist_archetype", "Protagonist archetype?", ["reluctant-hero", "chosen-one", "anti-hero", "everyman", "scholar", "outcast", "soldier", "trickster", "generate"], False),
        ("antagonist_type", "Antagonist type?", ["dark-lord", "political-rival", "nature", "cosmic-force", "self", "organization", "mystery", "generate"], False),
    ]),
]

VALIDATION_EDITORS = ["worldrules", "continuity", "geography", "characterization", "lore", "sensitivity"]


def cmd_wizard(args):
    """World Creation Wizard — interactive or YOLO mode."""
    mode = args.mode if hasattr(args, 'mode') and args.mode else "interactive"
    size = args.size.upper() if hasattr(args, 'size') and args.size else "M"
    genre = args.genre if hasattr(args, 'genre') and args.genre else "fantasy"
    seed = args.seed if hasattr(args, 'seed') and args.seed else ""
    tone = args.tone if hasattr(args, 'tone') and args.tone else "epic"
    project_type = args.project_type if hasattr(args, 'project_type') and args.project_type else "novel"

    if size not in TSHIRT_SIZES:
        print(f"Error: Invalid size '{size}'. Use S, M, L, or XL.")
        sys.exit(1)

    sz = TSHIRT_SIZES[size]

    lines = []
    lines.append(f"# 🧙 World Creation Wizard — {sz['label']}\n")

    if mode == "yolo":
        lines.append("## Mode: YOLO (Full Auto-Generation)\n")
        lines.append(f"Genre: **{genre}**")
        lines.append(f"Size: **{size}** — {sz['label']}")
        lines.append(f"Tone: **{tone}**")
        lines.append(f"Type: **{project_type}**")
        if seed:
            lines.append(f"Seed: **{seed}**")
        lines.append("")
    else:
        lines.append("## Mode: Interactive Wizard\n")
        lines.append("Walk through each step below. For each field, provide your answer")
        lines.append("or type 'generate' to let Claude decide.\n")
        for step_id, step_title, prompts in WIZARD_STEPS:
            lines.append(f"\n### Step: {step_title}\n")
            for field, question, choices, required in prompts:
                req_tag = " *(required)*" if required else ""
                if choices:
                    lines.append(f"**{field}**: {question}{req_tag}")
                    lines.append(f"  Options: {', '.join(choices)}")
                    lines.append(f"  Answer: _________________")
                else:
                    lines.append(f"**{field}**: {question}{req_tag}")
                    lines.append(f"  Answer: _________________")
            lines.append("")

    # ── GENERATION TARGETS ─────────────────────────────────────────────────────
    lines.append("\n## Generation Targets\n")
    lines.append(f"Size **{size}** means generating within these ranges:\n")
    lines.append(f"| Entity Type     | Min | Max |")
    lines.append(f"|-----------------|-----|-----|")
    entity_keys = ["species", "races", "languages", "characters", "locations",
                   "factions", "items", "events", "lineages", "arcs", "magic_systems"]
    for key in entity_keys:
        mn, mx = sz.get(key, (0, 0))
        lines.append(f"| {key:<15} | {mn:>3} | {mx:>3} |")

    lines.append(f"\n| History         |     |     |")
    mn_e, mx_e = sz.get("eras", (1, 1))
    mn_y, mx_y = sz.get("history_years", (100, 100))
    lines.append(f"| Eras            | {mn_e:>3} | {mx_e:>3} |")
    lines.append(f"| History (years) | {mn_y:>3} | {mx_y:>3} |")
    lines.append(f"| Gen passes      | {sz.get('generation_passes', 1):>3} |     |")

    lines.append(f"\n| Economy         |     |     |")
    for key in ["currencies", "resources", "trade_routes"]:
        mn, mx = sz.get(key, (0, 0))
        lines.append(f"| {key:<15} | {mn:>3} | {mx:>3} |")

    # ── GENERATION INSTRUCTIONS ────────────────────────────────────────────────
    lines.append("\n\n## Generation Instructions\n")

    if mode == "yolo":
        lines.append(f"""Generate a complete {genre} world for a {project_type} with {tone} tone.
{f'Creative seed: "{seed}"' if seed else 'Use your creativity freely.'}

Generate ALL entities within the ranges above. For each entity, output valid
YAML frontmatter + Markdown body matching the WorldBuilder schemas.

**REQUIRED: Triple Descriptions & Image Prompts**
Every visual entity MUST include a `descriptions` block with `machine`, `human`, and `image_prompt` fields:
- **Characters** (major/protagonist/antagonist/supporting): physical description, attire, voice, demeanor + image_prompt
- **Locations** (all): architecture, atmosphere, notable features + image_prompt
- **Factions** (all): `heraldry` block with sigil, colors, motto, and `heraldry.image_prompt` PLUS `descriptions` block with visual_identity, atmosphere, and `descriptions.image_prompt`
- **Species** (all): physical appearance, distinctive features + image_prompt of representative individual
- **Races** (all): physical appearance, distinguishing traits + image_prompt of representative individual
- **Items** (all): appearance, properties + image_prompt
- **Magic Systems** (all): visual manifestation, sensory effects + image_prompt of magic in use
- **Lineages** (all): `heraldry` block with sigil, colors, motto, and `heraldry.image_prompt`
- **Events** (major/world-changing only): scene description + image_prompt

Image prompts should describe the SUBJECT ONLY — what to draw, not how to render it. Include physical details, composition, pose, setting, and mood. Do NOT include style/rendering instructions (e.g., "photorealistic", "anime style", "8k", "DSLR", "cinematic lighting") — the rendering style is applied separately via LoRA presets. Do NOT include negative prompts — quality guards (no watermarks, no text, etc.) are injected automatically by the backend.

**REQUIRED: Character Voice Profiles**
Every character with role protagonist/antagonist/supporting/major MUST include a `voice` block:
```yaml
voice:
  description: "how they sound — personality, energy, vocal quality (this is the primary TTS input)"
  tags: [gender, pitch, texture, pace]  # e.g. [female, deep, raspy, calm]
  accent: "accent for TTS rendering"    # e.g. "Scottish", "Brooklyn", "received pronunciation"
  dialect: "speech register"            # e.g. "formal court speech", "street slang"
  sample_text: "A characteristic line of dialogue for this character"
```
Available voice tags: male, female, deep, high, warm, cold, raspy, smooth, young, old, authoritative, casual, energetic, calm, soft, loud, professional, sultry, resonant, formal, mature.
The sample_text should be 1-2 sentences that capture the character's personality and speech patterns.
The voice.description is the most important field — it directly drives the TTS voice design. Be vivid and specific.
Characters from the same location should share accent/dialect unless there's a narrative reason to differ.

**REQUIRED: Location Regional Defaults**
Locations of type city/town/village/region/kingdom SHOULD include a `regional_defaults` block:
```yaml
regional_defaults:
  ethnicity: "cultural background of inhabitants"
  appearance:
    skin_tone: ""
    hair: ""
    build: ""
    distinguishing: ""
  voice:
    accent: "regional accent"
    dialect: "speech register"
    tags: []
```
Characters from this location inherit these appearance and voice traits unless they override them. This ensures people from the same region sound and look consistent.

**Generation order:**
1. Calendar & eras
2. World flags (technology, magic, social rules)
3. Species & races
4. Languages & language families
5. Geography (locations, spatial hierarchy, routes)
6. Factions & organizations
7. Lineages & dynasties
8. Economy (currencies, resources, production, trade routes)
9. Characters (with full family_links, triple descriptions)
10. Historical events (causality chains, {sz.get('generation_passes', 1)} passes)
11. Story arcs
12. Items of significance
13. Magic systems (if applicable)

**After each generation pass:**
Run ALL validation editors in order: {', '.join(VALIDATION_EDITORS)}
Fix any issues before proceeding to the next entity type.
""")
    else:
        lines.append("""Use the wizard answers above to generate entities.
Where the user answered 'generate', use creative judgment within the genre.
Where the user gave specific answers, honor them exactly.

Follow the same generation order and validation process as YOLO mode.
""")

    # ── OUTPUT FORMAT ──────────────────────────────────────────────────────────
    lines.append("## Output Format\n")
    lines.append("""For each entity, output as a separate file block:

```
=== FILE: world/{entity_type}/{slug}.md ===
---
(YAML frontmatter matching the entity schema)
---

(Markdown body with descriptions, notes, etc.)
```

Entity filenames must be kebab-case slugs.
All cross-references must use slugs that match actual generated entities.
Relationships must be bidirectional (if A references B, B must reference A).
All visual entities MUST include descriptions.image_prompt (see requirements above).
Factions and lineages MUST include heraldry.image_prompt.
Minimum parent age is 16 — no character may have a child born before they were 16.
Every faction MUST have a leader (a living character) or explicit vacancy marker.
Every faction's members[] MUST include ALL characters whose faction field references it.

After all entities are generated, output:
1. `project.yaml` with all settings, style, and world_flags
2. `world/calendar.yaml` with eras and months
3. `world/economy.yaml` with full economic data

## Post-Generation Validation\n""")

    lines.append(f"""After ALL entities are generated, run these validation checks:

| Pass | Editor          | Checks                                          |
|------|-----------------|--------------------------------------------------|
| 1    | worldrules      | World flag compliance, tech anachronisms          |
| 2    | geography       | Spatial hierarchy, route validity, terrain logic   |
| 3    | continuity      | Timeline order, causality chains, alive/dead       |
| 4    | lore            | Internal consistency, cross-references valid        |
| 5    | characterization| Voice consistency, trait alignment, relationships  |
| 6    | sensitivity     | Content rating compliance, appropriateness         |

On failure: fix the issue and re-validate. Max 3 retries per entity.
Flag unresolvable issues for human review.
""")

    prompt = "\n".join(lines)

    # Save the wizard prompt
    template_dir = Path(__file__).resolve().parent.parent / "templates" / "wizard"
    output_dir = Path.cwd()

    # If we have a project context, save there; otherwise save to cwd
    if hasattr(args, 'project') and args.project:
        project_dir = find_project(args.project)
        if project_dir:
            output_dir = project_dir / "output"
            output_dir.mkdir(exist_ok=True)

    wizard_file = output_dir / f"wizard-{mode}-{size}.md"
    with open(wizard_file, "w") as f:
        f.write(prompt)

    # Display summary
    print(f"\n🧙 World Creation Wizard — {mode.upper()} mode, size {size}\n")
    print(f"  {sz['label']}")
    print(f"  Genre: {genre}  |  Tone: {tone}  |  Type: {project_type}")
    if seed:
        print(f"  Seed: \"{seed}\"")
    print()

    # Entity count summary
    total_min = sum(sz.get(k, (0, 0))[0] for k in entity_keys)
    total_max = sum(sz.get(k, (0, 0))[1] for k in entity_keys)
    print(f"  📊 Entity budget: {total_min}–{total_max} entities")
    print(f"  📜 History: {sz.get('eras', (1,1))[0]}–{sz.get('eras', (1,1))[1]} eras, "
          f"{sz.get('history_years', (100,100))[0]:,}–{sz.get('history_years', (100,100))[1]:,} years")
    print(f"  🔄 Generation passes: {sz.get('generation_passes', 1)}")
    print(f"  ✅ Post-gen validation: {len(VALIDATION_EDITORS)} editors")
    print()

    print(f"{'=' * 60}")
    print(f"✓ Wizard prompt saved to: {wizard_file}")
    print(f"  Prompt size: {len(prompt):,} chars")
    print(f"\nFeed this to Claude to {'auto-generate your world' if mode == 'yolo' else 'walk through world creation'}.")
    if mode == "yolo":
        print(f"  Recommended: use Opus with 1M context for best results.")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="WorldBuilder CLI — Structured worldbuilding & book writing")
    subparsers = parser.add_subparsers(dest="command")

    # init
    p_init = subparsers.add_parser("init", help="Initialize a new project")
    p_init.add_argument("name", help="Project name")
    p_init.add_argument("--genre", choices=["fantasy", "scifi", "modern", "campaign", "custom"], default="fantasy")
    p_init.add_argument("--type", choices=["novel", "series", "campaign", "game", "worldbook"], default="novel")

    # add
    p_add = subparsers.add_parser("add", help="Add a new entity")
    p_add.add_argument("entity_type", choices=ENTITY_TYPES + ["chapter"])
    p_add.add_argument("name", help="Entity name")
    p_add.add_argument("--project", help="Project path", default=None)

    # validate
    p_val = subparsers.add_parser("validate", help="Check project consistency")
    p_val.add_argument("--project", help="Project path", default=None)
    p_val.add_argument("--no-fix", action="store_true", help="Skip auto-fix of detectable issues")

    # compile
    p_comp = subparsers.add_parser("compile", help="Compile manuscript")
    p_comp.add_argument("--project", help="Project path", default=None)
    p_comp.add_argument("--format", choices=["md", "html", "all"], default="md")

    # stats
    p_stats = subparsers.add_parser("stats", help="Show project statistics")
    p_stats.add_argument("--project", help="Project path", default=None)

    # timeline
    p_tl = subparsers.add_parser("timeline", help="Display world timeline from events")
    p_tl.add_argument("--project", help="Project path", default=None)
    p_tl.add_argument("--era", help="Filter by era prefix", default=None)
    p_tl.add_argument("--filter", help="Filter events involving this entity", default=None)

    # graph
    p_graph = subparsers.add_parser("graph", help="Generate character relationship graph (Mermaid)")
    p_graph.add_argument("--project", help="Project path", default=None)

    # list
    p_list = subparsers.add_parser("list", help="List entities")
    p_list.add_argument("entity_type", help="Type of entity to list")
    p_list.add_argument("--project", help="Project path", default=None)

    # query
    p_query = subparsers.add_parser("query", help="Search project data")
    p_query.add_argument("question", help="Search term")
    p_query.add_argument("--project", help="Project path", default=None)

    # history
    p_hist = subparsers.add_parser("history", help="Show event history for an entity")
    p_hist.add_argument("entity_name", help="Entity name or slug")
    p_hist.add_argument("--project", help="Project path", default=None)

    # crossref
    p_xref = subparsers.add_parser("crossref", help="Show cross-references for an entity")
    p_xref.add_argument("entity_name", help="Entity name or slug")
    p_xref.add_argument("--project", help="Project path", default=None)

    # flags
    p_flags = subparsers.add_parser("flags", help="Display world flags")
    p_flags.add_argument("--project", help="Project path", default=None)

    # edit
    p_edit = subparsers.add_parser("edit", help="Run an editor persona against chapters")
    p_edit.add_argument("editor_name", help="Editor name (or 'list' to show all)")
    p_edit.add_argument("--chapter", help="Chapter range (e.g. '1-3' or 'all')", default="all")
    p_edit.add_argument("--project", help="Project path", default=None)

    # geography
    p_geo = subparsers.add_parser("geography", help="Display spatial hierarchy and routes")
    p_geo.add_argument("--project", help="Project path", default=None)

    # family
    p_family = subparsers.add_parser("family", help="Display family tree for a lineage or character")
    p_family.add_argument("name", help="Lineage or character name")
    p_family.add_argument("--project", help="Project path", default=None)

    # languages
    p_langs = subparsers.add_parser("languages", help="Display language families and intelligibility")
    p_langs.add_argument("--project", help="Project path", default=None)

    # peoples
    p_peoples = subparsers.add_parser("peoples", help="Display species and races")
    p_peoples.add_argument("--project", help="Project path", default=None)

    # economy
    p_eco = subparsers.add_parser("economy", help="Display economic overview")
    p_eco.add_argument("--project", help="Project path", default=None)

    # generate
    p_gen = subparsers.add_parser("generate", help="Generate procedural history prompt")
    p_gen.add_argument("gen_type", choices=["peaceful", "conflict", "catastrophe", "mixed"], default="mixed", nargs="?")
    p_gen.add_argument("--years", help="Years of history to generate", default="100")
    p_gen.add_argument("--project", help="Project path", default=None)

    # write
    p_write = subparsers.add_parser("write", help="Build context-aware writing prompt")
    p_write.add_argument("--chapter", help="Chapter number to write", default=None)
    p_write.add_argument("--project", help="Project path", default=None)

    # story
    p_story = subparsers.add_parser("story", help="Generate in-universe short story prompt")
    p_story.add_argument("--event", help="Event slug to anchor story to")
    p_story.add_argument("--era", help="Era prefix for time period anchor")
    p_story.add_argument("--start-year", type=int, help="Start year (with --era)")
    p_story.add_argument("--end-year", type=int, help="End year (with --era)")
    p_story.add_argument("--protagonist", default="generate", help="Character slug or 'generate'")
    p_story.add_argument("--tone", help="Tone override")
    p_story.add_argument("--subgenre", help="Subgenre (e.g. hard-sf, space-opera, cyberpunk, military-sf, noir)")
    p_story.add_argument("--rating", choices=["young-adult", "adult", "mature"], default=None, help="Content rating override")
    p_story.add_argument("--chapters", type=int, default=12, help="Target chapter count")
    p_story.add_argument("--words", type=int, default=30000, help="Target word count")
    p_story.add_argument("--project", help="Project path")

    # campaign
    p_campaign = subparsers.add_parser("campaign", help="Generate D&D campaign prompt")
    p_campaign.add_argument("--event", help="Event slug to set campaign during")
    p_campaign.add_argument("--era", help="Era prefix for time period")
    p_campaign.add_argument("--year", type=int, help="Specific year (with --era)")
    p_campaign.add_argument("--present", action="store_true", help="Set in present day")
    p_campaign.add_argument("--length", choices=["one-shot", "short", "custom"], default="one-shot", help="Campaign length")
    p_campaign.add_argument("--sessions", type=int, default=1, help="Session count (with --length custom)")
    p_campaign.add_argument("--level", default="1-4", help="Party level range")
    p_campaign.add_argument("--tone", help="Campaign tone override")
    p_campaign.add_argument("--themes", help="Comma-separated themes")
    p_campaign.add_argument("--location", help="Center on this location slug")
    p_campaign.add_argument("--project", help="Project path")

    # wizard
    p_wizard = subparsers.add_parser("wizard", help="World Creation Wizard (interactive or YOLO)")
    p_wizard.add_argument("mode", choices=["interactive", "yolo"], default="interactive", nargs="?",
                          help="Wizard mode: interactive (guided) or yolo (full auto)")
    p_wizard.add_argument("--size", choices=["S", "M", "L", "XL", "s", "m", "l", "xl"],
                          default="M", help="T-shirt size for world complexity")
    p_wizard.add_argument("--genre", choices=["fantasy", "scifi", "modern", "horror",
                          "post-apocalyptic", "steampunk", "custom"], default="fantasy")
    p_wizard.add_argument("--tone", default="epic", help="Prose/world tone")
    p_wizard.add_argument("--seed", default="", help="Creative seed phrase for YOLO mode")
    p_wizard.add_argument("--project-type", dest="project_type",
                          choices=["novel", "series", "campaign", "game", "worldbook"],
                          default="novel")
    p_wizard.add_argument("--project", help="Project path (for output)", default=None)

    # fix
    p_fix = subparsers.add_parser("fix", help="Auto-fix consistency issues")
    p_fix.add_argument("--project", "-p", help="Project path", default=None)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    commands = {
        "init": cmd_init,
        "validate": cmd_validate,
        "compile": cmd_compile,
        "stats": cmd_stats,
        "timeline": cmd_timeline,
        "graph": cmd_graph,
        "list": cmd_list,
        "query": cmd_query,
        "history": cmd_history,
        "crossref": cmd_crossref,
        "flags": cmd_flags,
        "edit": cmd_edit,
        "geography": cmd_geography,
        "family": cmd_family,
        "languages": cmd_languages,
        "peoples": cmd_peoples,
        "economy": cmd_economy,
        "generate": cmd_generate,
        "write": cmd_write,
        "story": cmd_story,
        "campaign": cmd_campaign,
        "wizard": cmd_wizard,
        "fix": cmd_fix,
    }

    if args.command == "add":
        if args.entity_type == "chapter":
            project_dir = find_project(args.project)
            if not project_dir:
                print("Error: No project.yaml found.")
                sys.exit(1)
            cmd_add_chapter(project_dir, args.name)
        else:
            cmd_add(args)
    elif args.command in commands:
        commands[args.command](args)


if __name__ == "__main__":
    main()
