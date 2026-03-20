#!/usr/bin/env python3
"""
WorldBuilder MCP Server — MCP tools for structured worldbuilding.

Provides tools for creating worlds, managing entities, validating consistency,
exploring timelines/geography/families, and generating writing prompts.
Runs via stdio transport for local Claude Code / Cowork integration.
"""

import json
import re
import subprocess
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from mcp.server.fastmcp import FastMCP

# ─── Constants ──────────────────────────────────────────────────────────────

SERVER_ROOT = Path(__file__).parent.parent
ENTITY_TYPES = [
    "character", "location", "faction", "item", "magic-system", "arc",
    "event", "species", "race", "language", "lineage",
]
ENTITY_DIRS = {
    "character": "characters", "location": "locations", "faction": "factions",
    "item": "items", "magic-system": "magic-systems", "arc": "arcs",
    "event": "events", "species": "species", "race": "races",
    "language": "languages", "lineage": "lineages",
}

# Resolve template/editor dirs
if (SERVER_ROOT / "assets" / "templates").exists():
    TEMPLATE_DIR = SERVER_ROOT / "assets" / "templates"
    EDITOR_DIR = SERVER_ROOT / "assets" / "editors"
else:
    TEMPLATE_DIR = SERVER_ROOT / "templates"
    EDITOR_DIR = SERVER_ROOT / "editors"


# ─── Lifespan ───────────────────────────────────────────────────────────────

@asynccontextmanager
async def app_lifespan(server):
    """Discover projects on startup."""
    projects = _discover_projects()
    yield {"projects": projects}


mcp = FastMCP("worldbuilder_mcp", lifespan=app_lifespan)


# ─── Shared Helpers ─────────────────────────────────────────────────────────

def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


WORLDS_DIR = SERVER_ROOT / "worlds"
PROJECT_ROOTS = [WORLDS_DIR, SERVER_ROOT]


def _discover_projects() -> Dict[str, Path]:
    """Find all project dirs containing project.yaml (worlds/ first, then repo root)."""
    projects = {}
    for root in PROJECT_ROOTS:
        if not root.exists():
            continue
        for p in root.iterdir():
            if p.is_dir() and (p / "project.yaml").exists() and p.name not in projects:
                projects[p.name] = p
    return projects


def _resolve_project(project: Optional[str] = None) -> Path:
    """Resolve a project by name or find the only one."""
    projects = _discover_projects()
    if not projects:
        raise ValueError("No WorldBuilder projects found. Use wb_init_project to create one.")
    if project:
        slug = _slugify(project)
        if slug in projects:
            return projects[slug]
        for name, path in projects.items():
            if slug in name:
                return path
        raise ValueError(f"Project '{project}' not found. Available: {', '.join(projects.keys())}")
    if len(projects) == 1:
        return next(iter(projects.values()))
    raise ValueError(f"Multiple projects found. Specify one: {', '.join(projects.keys())}")


def _load_yaml(filepath: Path) -> dict:
    with open(filepath) as f:
        return yaml.safe_load(f) or {}


def _load_entity_file(filepath: Path) -> dict:
    """Parse YAML frontmatter + Markdown."""
    with open(filepath) as f:
        content = f.read()
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            meta = yaml.safe_load(parts[1]) or {}
            body = parts[2].strip()
            return {"meta": meta, "body": body, "path": str(filepath)}
    return {"meta": {}, "body": content, "path": str(filepath)}


def _collect_entities(project_dir: Path) -> Dict[str, Dict[str, dict]]:
    """Collect all entities for a project."""
    world_dir = project_dir / "world"
    entities = {}
    for etype, dirname in ENTITY_DIRS.items():
        edir = world_dir / dirname
        entities[etype] = {}
        if edir.exists():
            for f in sorted(edir.glob("*.md")):
                data = _load_entity_file(f)
                data["slug"] = f.stem
                entities[etype][f.stem] = data
    # Chapters
    ch_dir = project_dir / "chapters"
    entities["chapter"] = {}
    if ch_dir.exists():
        for f in sorted(ch_dir.glob("*.md")):
            data = _load_entity_file(f)
            data["slug"] = f.stem
            entities["chapter"][f.stem] = data
    return entities


def _serialize_date(d) -> str:
    if isinstance(d, dict):
        return d.get("display", f"{d.get('era_prefix', '')} {d.get('year', '?')}")
    return str(d) if d else "?"


def _format_entity_summary(etype: str, slug: str, meta: dict) -> str:
    """Format a one-line entity summary."""
    name = meta.get("name", slug)
    status = meta.get("status", "")
    role = meta.get("role", "")
    species = meta.get("species", "")
    parts = [f"- **{name}** ({slug})"]
    if status:
        parts.append(f"[{status}]")
    if role:
        parts.append(role)
    if species and etype == "character":
        parts.append(f"({species})")
    return " ".join(parts)


def _format_entity_detail(etype: str, slug: str, data: dict) -> str:
    """Format a full entity detail view."""
    meta = data["meta"]
    lines = [f"# {meta.get('name', slug)} ({etype})\n"]

    skip = {"name", "descriptions", "family_links", "relationships", "routes", "heraldry", "intelligibility"}
    for k, v in meta.items():
        if k in skip or v is None or v == "" or v == []:
            continue
        if isinstance(v, dict):
            if "display" in v:
                lines.append(f"**{k}**: {v['display']}")
            else:
                lines.append(f"**{k}**: {json.dumps(v, default=str)}")
        elif isinstance(v, list):
            lines.append(f"**{k}**: {', '.join(str(i) for i in v)}")
        else:
            lines.append(f"**{k}**: {v}")

    descs = meta.get("descriptions", {})
    if descs.get("human"):
        lines.append(f"\n## Description\n{descs['human']}")
    if descs.get("machine"):
        lines.append("\n## Machine Description")
        for k, v in descs["machine"].items():
            if v:
                lines.append(f"- **{k}**: {v}")
    if descs.get("image_prompt"):
        lines.append(f"\n## Image Prompt\n`{descs['image_prompt']}`")

    heraldry = meta.get("heraldry", {})
    if heraldry:
        lines.append("\n## Heraldry")
        if isinstance(heraldry.get("sigil"), dict):
            lines.append(f"- **Sigil**: {heraldry['sigil'].get('description', '')}")
        elif isinstance(heraldry.get("sigil"), str):
            lines.append(f"- **Sigil**: {heraldry['sigil']}")
        if heraldry.get("motto"):
            lines.append(f"- **Motto**: \"{heraldry['motto']}\"")
        if heraldry.get("image_prompt"):
            lines.append(f"- **Image prompt**: `{heraldry['image_prompt']}`")

    rels = meta.get("relationships", [])
    if rels:
        lines.append("\n## Relationships")
        for r in rels:
            target = r.get("entity") or r.get("character") or r.get("name", "?")
            lines.append(f"- {r.get('type', 'related')}: **{target}** {r.get('description', '')}")

    family = meta.get("family_links", {})
    if family:
        lines.append("\n## Family")
        for k, v in family.items():
            if v and k not in ("legitimacy", "title_inherited", "birth_order"):
                people = v if isinstance(v, list) else [v]
                for p in people:
                    if p:
                        lines.append(f"- {k}: **{p}**")

    if data.get("body"):
        lines.append(f"\n## Notes\n{data['body']}")

    lines.append(f"\n---\n*File: `{data.get('path', slug)}`*")
    return "\n".join(lines)


def _get_cli_script() -> Path:
    """Find the worldbuilder CLI script."""
    return SERVER_ROOT / "scripts" / "worldbuilder.py"


# ═══════════════════════════════════════════════════════════════════════════
# TOOLS — flat parameter signatures for native MCP argument passing
# ═══════════════════════════════════════════════════════════════════════════

# ─── Project Management ─────────────────────────────────────────────────────

@mcp.tool(
    name="wb_list_projects",
    annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
)
async def wb_list_projects() -> str:
    """List all WorldBuilder projects in the workspace.

    Returns a list of all projects with their title, genre, and type.
    Use this to discover available projects before other operations.
    """
    projects = _discover_projects()
    if not projects:
        return "No WorldBuilder projects found. Use `wb_init_project` to create one, or `wb_wizard` to auto-generate a world."

    lines = ["# WorldBuilder Projects\n"]
    for slug, path in sorted(projects.items()):
        config = _load_yaml(path / "project.yaml")
        lines.append(f"- **{config.get('title', slug)}** (`{slug}`)")
        lines.append(f"  Genre: {config.get('genre', '?')}, Type: {config.get('type', '?')}")
    return "\n".join(lines)


@mcp.tool(
    name="wb_project_overview",
    annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
)
async def wb_project_overview(project: str = "") -> str:
    """Get a full overview of a WorldBuilder project: config, entity counts, style, world flags.

    Use this to understand a project's scope and current state before working with it.

    Args:
        project: Project name/slug. Omit if only one project exists.
    """
    project_dir = _resolve_project(project or None)
    config = _load_yaml(project_dir / "project.yaml")
    entities = _collect_entities(project_dir)

    lines = [f"# {config.get('title', project_dir.name)}\n"]
    lines.append(f"**Genre**: {config.get('genre', '?')}  |  **Type**: {config.get('type', '?')}")
    lines.append(f"**Target**: {config.get('target_word_count', '?')} words  |  **Chapter target**: {config.get('chapter_target_words', 3000)} words\n")

    style = config.get("style", {})
    prose = style.get("prose", {})
    if prose:
        lines.append(f"**Prose**: {prose.get('preset', '?')} | POV: {prose.get('pov', '?')} | Tense: {prose.get('tense', '?')}")

    visual = style.get("visual", {})
    if visual:
        lines.append(f"**Visual**: {visual.get('preset', '?')} | Lighting: {visual.get('lighting', '?')}\n")

    lines.append("## Entity Counts\n")
    total = 0
    for etype, ents in sorted(entities.items()):
        if ents:
            lines.append(f"- {etype}: **{len(ents)}**")
            total += len(ents)
    lines.append(f"\n**Total: {total} entities**")

    eco_file = project_dir / "world" / "economy.yaml"
    if eco_file.exists():
        eco = _load_yaml(eco_file)
        lines.append(f"\n**Economy**: {len(eco.get('currencies', []))} currencies, {len(eco.get('resources', []))} resources, {len(eco.get('trade_routes', []))} trade routes")

    return "\n".join(lines)


@mcp.tool(
    name="wb_init_project",
    annotations={"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False},
)
async def wb_init_project(
    name: str,
    genre: str = "fantasy",
    project_type: str = "novel",
) -> str:
    """Initialize a new WorldBuilder project with directory structure and templates.

    Args:
        name: Project name (e.g., 'The Shattered Crown').
        genre: Genre preset: fantasy, scifi, modern, horror, post-apocalyptic, steampunk, custom.
        project_type: Project type: novel, series, campaign, game, worldbook.
    """
    slug = _slugify(name)
    project_dir = SERVER_ROOT / slug
    if project_dir.exists():
        return f"Error: Project directory '{slug}' already exists."

    dirs = ["world/" + d for d in ENTITY_DIRS.values()] + [
        "world/transport", "chapters", "output", "output/reviews", "output/writing"
    ]
    for d in dirs:
        (project_dir / d).mkdir(parents=True, exist_ok=True)

    template = TEMPLATE_DIR / "project_template.yaml"
    if template.exists():
        import shutil
        shutil.copy(template, project_dir / "project.yaml")
        config = _load_yaml(project_dir / "project.yaml")
        config["title"] = name
        config["genre"] = genre
        config["type"] = project_type
        with open(project_dir / "project.yaml", "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    else:
        config = {"title": name, "genre": genre, "type": project_type, "version": "0.1.0"}
        with open(project_dir / "project.yaml", "w") as f:
            yaml.dump(config, f, default_flow_style=False)

    preset_file = (SERVER_ROOT / "assets" / "presets" if (SERVER_ROOT / "assets" / "presets").exists()
                   else SERVER_ROOT / "presets") / f"{genre}.yaml"
    if preset_file.exists():
        import shutil
        shutil.copy(preset_file, project_dir / "world" / "world_flags.yaml")

    return f"✓ Project **{name}** initialized at `{slug}/`\n\nDirectories created for all {len(ENTITY_DIRS)} entity types.\nUse `wb_add_entity` to start populating your world, or `wb_wizard` to auto-generate."


# ─── Entity CRUD ────────────────────────────────────────────────────────────

@mcp.tool(
    name="wb_add_entity",
    annotations={"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False},
)
async def wb_add_entity(
    entity_type: str,
    name: str,
    project: str = "",
    fields: dict = None,
) -> str:
    """Add a new entity to a WorldBuilder project by copying the appropriate template.

    Args:
        entity_type: Type of entity: character, location, faction, item, magic-system, arc, event, species, race, language, lineage.
        name: Entity name (e.g., 'Kael Dawnblade').
        project: Project name/slug. Omit if only one project.
        fields: Optional dict of additional YAML fields to set.
    """
    if entity_type not in ENTITY_DIRS:
        return f"Error: Unknown entity type '{entity_type}'. Valid: {', '.join(ENTITY_DIRS.keys())}"

    project_dir = _resolve_project(project or None)
    dirname = ENTITY_DIRS[entity_type]
    slug = _slugify(name)

    target_dir = project_dir / "world" / dirname
    target_dir.mkdir(parents=True, exist_ok=True)
    target_file = target_dir / f"{slug}.md"

    if target_file.exists():
        return f"Error: Entity `{slug}.md` already exists in {dirname}/."

    template_file = TEMPLATE_DIR / dirname / "_template.md"
    if template_file.exists():
        content = template_file.read_text()
        content = content.replace("Entity Name", name)
    else:
        content = f"---\nname: \"{name}\"\ntype: \"{entity_type}\"\nstatus: active\n---\n\n## Description\n\n"

    target_file.write_text(content)
    return f"✓ Created **{name}** (`{dirname}/{slug}.md`)\n\nEdit the file to fill in details. The YAML frontmatter defines structured fields; the Markdown body is for prose notes."


@mcp.tool(
    name="wb_get_entity",
    annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
)
async def wb_get_entity(
    entity_type: str,
    slug: str,
    project: str = "",
) -> str:
    """Get the full details of a specific entity including all metadata, descriptions, and prose.

    Args:
        entity_type: Type of entity: character, location, faction, item, etc.
        slug: Entity slug (kebab-case filename, e.g., 'kael-dawnblade').
        project: Project name/slug.
    """
    project_dir = _resolve_project(project or None)
    entities = _collect_entities(project_dir)

    if entity_type not in entities or slug not in entities[entity_type]:
        for s, data in entities.get(entity_type, {}).items():
            if slug in s or slug.lower() in data["meta"].get("name", "").lower():
                return _format_entity_detail(entity_type, s, data)
        return f"Error: Entity `{slug}` not found in {entity_type}. Use `wb_list_entities` to see available entities."

    data = entities[entity_type][slug]
    return _format_entity_detail(entity_type, slug, data)


@mcp.tool(
    name="wb_list_entities",
    annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
)
async def wb_list_entities(
    entity_type: str = "",
    query: str = "",
    project: str = "",
) -> str:
    """List entities in a project, optionally filtered by type and/or search query.

    Args:
        entity_type: Filter by entity type (e.g., 'character'). Omit for all types.
        query: Search filter string.
        project: Project name/slug.
    """
    project_dir = _resolve_project(project or None)
    entities = _collect_entities(project_dir)
    q = query.lower()

    lines = ["# Entities\n"]
    count = 0

    for etype in sorted(entities.keys()):
        if entity_type and etype != entity_type:
            continue
        ents = entities[etype]
        if not ents:
            continue

        type_lines = []
        for s, data in sorted(ents.items()):
            meta = data["meta"]
            name = meta.get("name", s)
            if q and q not in name.lower() and q not in s and q not in json.dumps(meta, default=str).lower():
                continue
            type_lines.append(_format_entity_summary(etype, s, meta))
            count += 1

        if type_lines:
            lines.append(f"## {etype.capitalize()} ({len(type_lines)})\n")
            lines.extend(type_lines)
            lines.append("")

    if count == 0:
        return "No entities found matching your criteria."
    lines.append(f"\n**Total: {count} entities**")
    return "\n".join(lines)


@mcp.tool(
    name="wb_search",
    annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
)
async def wb_search(query: str, project: str = "") -> str:
    """Search across ALL entity types for a term. Searches names, metadata, and prose bodies.

    Args:
        query: Search term to find across all entities.
        project: Project name/slug.
    """
    project_dir = _resolve_project(project or None)
    entities = _collect_entities(project_dir)
    q = query.lower()

    results = []
    for etype, ents in entities.items():
        for slug, data in ents.items():
            meta = data["meta"]
            name = meta.get("name", slug)
            score = 0
            if q in name.lower():
                score = 100
            elif q in slug:
                score = 80
            elif q in data.get("body", "").lower():
                score = 40
            elif q in json.dumps(meta, default=str).lower():
                score = 20
            if score > 0:
                results.append((score, etype, slug, name))

    results.sort(key=lambda x: -x[0])

    if not results:
        return f"No results found for '{query}'."

    lines = [f"# Search: '{query}'\n"]
    for score, etype, slug, name in results[:20]:
        lines.append(f"- **{name}** ({etype}: `{slug}`) — relevance: {score}")
    if len(results) > 20:
        lines.append(f"\n... and {len(results) - 20} more results")
    return "\n".join(lines)


# ─── Exploration / Visualization ────────────────────────────────────────────

@mcp.tool(
    name="wb_timeline",
    annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
)
async def wb_timeline(project: str = "") -> str:
    """Display the world timeline — all events in chronological order.

    Args:
        project: Project name/slug.
    """
    project_dir = _resolve_project(project or None)
    entities = _collect_entities(project_dir)
    events = entities.get("event", {})

    if not events:
        return "No events found. Use `wb_add_entity` with type 'event' to create timeline events."

    def _sort_key(item):
        m = item[1]["meta"]
        d = m.get("date", m.get("start_date", {}))
        if isinstance(d, dict):
            return (d.get("era_prefix", ""), d.get("year", 0), item[0])
        return (str(d), 0, item[0])

    sorted_events = sorted(events.items(), key=_sort_key)

    lines = ["# World Timeline\n"]
    for slug, data in sorted_events:
        m = data["meta"]
        d = m.get("date", m.get("start_date", "?"))
        date_str = _serialize_date(d)
        sig = m.get("significance", "minor")
        sig_icon = {"world-changing": "🔴", "major": "🟠", "moderate": "🔵", "minor": "⚪", "trivial": "·"}.get(sig, "·")

        lines.append(f"{sig_icon} **[{date_str}]** {m.get('name', slug)} ({m.get('type', '?')})")

        participants = m.get("participants", [])
        if participants:
            pnames = ", ".join(p.get("entity", "?") for p in participants[:5])
            lines.append(f"  Participants: {pnames}")

        leads_to = m.get("leads_to", [])
        if leads_to:
            lines.append(f"  → Leads to: {', '.join(leads_to)}")
        lines.append("")

    return "\n".join(lines)


@mcp.tool(
    name="wb_geography",
    annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
)
async def wb_geography(project: str = "") -> str:
    """Display the spatial hierarchy of locations and transport routes between them.

    Args:
        project: Project name/slug.
    """
    project_dir = _resolve_project(project or None)
    entities = _collect_entities(project_dir)
    locations = entities.get("location", {})

    if not locations:
        return "No locations found."

    lines = ["# Geography & Routes\n"]

    children = {}
    roots = []
    for slug, data in locations.items():
        parent = data["meta"].get("parent", "")
        if parent and _slugify(parent) in locations:
            children.setdefault(_slugify(parent), []).append(slug)
        else:
            roots.append(slug)

    def print_tree(slug, depth=0):
        data = locations[slug]
        meta = data["meta"]
        indent = "  " * depth
        pop = meta.get("population", "")
        pop_str = f" (pop: {pop})" if pop else ""
        lines.append(f"{indent}📍 **{meta.get('name', slug)}** [{meta.get('type', '?')}]{pop_str}")

        for route in meta.get("routes", []):
            dest = route.get("to") or route.get("destination", "?")
            methods = route.get("methods", [])
            rt = route.get("route_type", "minor")
            if methods:
                modes = ", ".join(f"{m.get('mode', '?')} ({m.get('travel_time', '?')})" for m in methods if isinstance(m, dict))
                lines.append(f"{indent}  → {dest} [{rt}]: {modes}")

        for child in children.get(slug, []):
            print_tree(child, depth + 1)

    for root in roots:
        print_tree(root)
        lines.append("")

    return "\n".join(lines)


@mcp.tool(
    name="wb_families",
    annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
)
async def wb_families(project: str = "") -> str:
    """Display lineages/dynasties with their family members, heraldry, and relationships.

    Args:
        project: Project name/slug.
    """
    project_dir = _resolve_project(project or None)
    entities = _collect_entities(project_dir)
    lineages = entities.get("lineage", {})
    characters = entities.get("character", {})

    if not lineages:
        return "No lineages found."

    lines = ["# Lineages & Families\n"]

    for lin_slug, lin_data in lineages.items():
        meta = lin_data["meta"]
        lines.append(f"## 👑 {meta.get('name', lin_slug)}")

        heraldry = meta.get("heraldry", {})
        if heraldry.get("motto"):
            lines.append(f"*\"{heraldry['motto']}\"*")
        if isinstance(heraldry.get("sigil"), str):
            lines.append(f"Sigil: {heraldry['sigil']}")
        elif isinstance(heraldry.get("sigil"), dict):
            lines.append(f"Sigil: {heraldry['sigil'].get('description', '')}")

        members = []
        for char_slug, char_data in characters.items():
            cm = char_data["meta"]
            lin_ref = cm.get("lineage") or (cm.get("family_links") or {}).get("lineage", "")
            if lin_ref and (_slugify(lin_ref) == lin_slug or lin_ref.lower() == meta.get("name", "").lower()):
                status_icon = {"alive": "●", "dead": "✝", "unknown": "?"}.get(cm.get("status", ""), "?")
                members.append(f"  {status_icon} **{cm.get('name', char_slug)}** — {cm.get('role', '')}")

        if members:
            lines.append("\nMembers:")
            lines.extend(members)
        else:
            lines.append("\n*No members linked yet*")
        lines.append("")

    return "\n".join(lines)


@mcp.tool(
    name="wb_languages",
    annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
)
async def wb_languages(project: str = "") -> str:
    """Display language families, status, mutual intelligibility, and speaker info.

    Args:
        project: Project name/slug.
    """
    project_dir = _resolve_project(project or None)
    entities = _collect_entities(project_dir)
    langs = entities.get("language", {})

    if not langs:
        return "No languages found."

    families = {}
    for slug, data in langs.items():
        ft = data["meta"].get("family_tree", {})
        fam = ft.get("family_name", "Unknown")
        families.setdefault(fam, []).append((slug, data))

    lines = ["# Languages\n"]
    for fam, members_list in sorted(families.items()):
        lines.append(f"## 🗣️ {fam}\n")
        for slug, data in members_list:
            meta = data["meta"]
            status = meta.get("status", "living")
            status_icon = {"living": "●", "endangered": "⚠", "dead": "✝", "extinct": "✝"}.get(status, "●")
            special = meta.get("special", {})
            tags = []
            if special.get("lingua_franca"):
                tags.append("lingua franca")
            if special.get("magical_properties"):
                tags.append("magical")
            tag_str = f" [{', '.join(tags)}]" if tags else ""

            lines.append(f"{status_icon} **{meta.get('name', slug)}** ({status}){tag_str}")

            for intel in meta.get("intelligibility", []):
                score = intel.get("score", 0)
                pct = int(score * 100)
                bar = "█" * (pct // 10) + "░" * (10 - pct // 10)
                lines.append(f"  ↔ {intel.get('language', '?')}: {bar} {pct}%")
            lines.append("")

    return "\n".join(lines)


@mcp.tool(
    name="wb_species",
    annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
)
async def wb_species(project: str = "") -> str:
    """Display species and their associated races, biology, and relationships.

    Args:
        project: Project name/slug.
    """
    project_dir = _resolve_project(project or None)
    entities = _collect_entities(project_dir)
    species = entities.get("species", {})
    races = entities.get("race", {})

    if not species:
        return "No species found."

    lines = ["# Species & Races\n"]
    for slug, data in sorted(species.items()):
        meta = data["meta"]
        sentience = meta.get("sentience", "?")
        s_icon = {"sapient": "🧠", "semi-sapient": "🐾", "non-sapient": "🦎", "hive-mind": "🐝"}.get(sentience, "❓")
        bio = meta.get("biology", {})
        lifespan = bio.get("lifespan", {})
        pop = (meta.get("habitat") or {}).get("population_estimate", "?")

        lines.append(f"## {s_icon} {meta.get('name', slug)} ({sentience})\n")
        if lifespan:
            if isinstance(lifespan, dict):
                lines.append(f"Lifespan: {lifespan.get('average', '?')} years | Population: ~{pop}")
            else:
                lines.append(f"Lifespan: {lifespan} | Population: ~{pop}")

        sp_races = [r for r_slug, r in races.items() if _slugify(r["meta"].get("species", "")) == slug]
        if sp_races:
            lines.append(f"\nRaces:")
            for r in sp_races:
                lines.append(f"  - **{r['meta'].get('name', '?')}**")
        lines.append("")

    return "\n".join(lines)


@mcp.tool(
    name="wb_economy",
    annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
)
async def wb_economy(project: str = "") -> str:
    """Display the economic overview: currencies, resources, production, trade routes.

    Args:
        project: Project name/slug.
    """
    project_dir = _resolve_project(project or None)
    eco_file = project_dir / "world" / "economy.yaml"
    if not eco_file.exists():
        return "No economy data found. Create `world/economy.yaml` to define currencies, resources, and trade."

    eco = _load_yaml(eco_file)
    lines = ["# Economy\n"]

    for cur in eco.get("currencies", []):
        denoms = ", ".join(f"{d['name']} ({d['value']})" for d in cur.get("denominations", []))
        lines.append(f"**{cur.get('symbol', '')} {cur.get('name', '?')}**: {denoms}")

    resources = eco.get("resources", [])
    if resources:
        lines.append(f"\n## Resources ({len(resources)})\n")
        for r in resources:
            lines.append(f"- **{r.get('name', '?')}** [{r.get('category', '?')}] — {r.get('rarity', '?')}, base: {r.get('base_value', '?')}")

    routes = eco.get("trade_routes", [])
    if routes:
        lines.append(f"\n## Trade Routes ({len(routes)})\n")
        for rt in routes:
            lines.append(f"- **{rt.get('name', '?')}**: {rt.get('from_location', '?')} ↔ {rt.get('to_location', '?')} ({rt.get('annual_value', '?')}/yr)")
            for g in rt.get("goods", []):
                arrow = {"outbound": "→", "inbound": "←", "both": "↔"}.get(g.get("direction", "both"), "↔")
                lines.append(f"  {arrow} {g.get('resource', '?')}: {g.get('volume', '?')}")

    return "\n".join(lines)


@mcp.tool(
    name="wb_world_flags",
    annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
)
async def wb_world_flags(project: str = "") -> str:
    """Display world flags — the boolean rules that define what's possible in this world.

    Args:
        project: Project name/slug.
    """
    project_dir = _resolve_project(project or None)
    config = _load_yaml(project_dir / "project.yaml")
    flags = config.get("world_flags", {})

    if not flags:
        wf_file = project_dir / "world" / "world_flags.yaml"
        if wf_file.exists():
            flags = _load_yaml(wf_file)

    if not flags:
        return "No world flags set. Define them in project.yaml under `world_flags:` or in `world/world_flags.yaml`."

    lines = ["# World Flags\n"]
    for category, cat_flags in sorted(flags.items()):
        if not isinstance(cat_flags, dict):
            continue
        lines.append(f"## {category.capitalize()}\n")
        for flag_name, flag_data in sorted(cat_flags.items()):
            if isinstance(flag_data, dict):
                val = flag_data.get("value")
                locked = flag_data.get("locked", False)
                lock_icon = "🔒" if locked else "🔓"
                val_icon = "✓" if val else "✗"
                lines.append(f"{lock_icon} {val_icon} **{flag_name}**: {val}")
            else:
                val_icon = "✓" if flag_data else "✗"
                lines.append(f"🔓 {val_icon} **{flag_name}**: {flag_data}")
        lines.append("")

    return "\n".join(lines)


# ─── Image Generation ───────────────────────────────────────────────────────

@mcp.tool(
    name="wb_generate_image",
    annotations={"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False},
)
async def wb_generate_image(
    entity_type: str,
    slug: str,
    project: str = "",
    force: bool = False,
) -> str:
    """Generate an image for an entity using its image_prompt field via MLX Stable Diffusion.

    Requires macOS with Apple Silicon and MLX installed. Images are cached
    in the project's output/images/ directory.

    Args:
        entity_type: Type of entity (character, location, faction, etc.).
        slug: Entity slug (kebab-case filename).
        project: Project name/slug.
        force: If true, regenerate even if cached.
    """
    project_dir = _resolve_project(project or None)
    entities = _collect_entities(project_dir)

    if entity_type not in entities or slug not in entities[entity_type]:
        return f"Error: Entity `{slug}` not found in {entity_type}."

    data = entities[entity_type][slug]
    meta = data["meta"]

    # Find image_prompt
    image_prompt = (meta.get("descriptions") or {}).get("image_prompt")
    if not image_prompt:
        image_prompt = (meta.get("heraldry") or {}).get("image_prompt")
    if not image_prompt:
        return f"No visualization available for **{meta.get('name', slug)}** — no `image_prompt` in YAML frontmatter."

    # Try importing the webapp imagegen module
    try:
        webapp_dir = SERVER_ROOT / "webapp"
        if str(webapp_dir) not in sys.path:
            sys.path.insert(0, str(webapp_dir))
        from imagegen import submit_job, get_job, get_status

        status = get_status()
        if not status["mlx_available"]:
            return (
                f"MLX not available on this system.\n\n"
                f"**Image prompt for {meta.get('name', slug)}:**\n"
                f"`{image_prompt}`\n\n"
                f"To generate locally, install mflux on macOS Apple Silicon:\n"
                f"  pip install mflux"
            )

        job = submit_job(
            prompt=image_prompt,
            project_dir=project_dir,
            project_slug=project_dir.name,
            entity_slug=slug,
            entity_name=meta.get("name", slug),
            entity_type=entity_type,
            force=force,
        )

        if job.get("status") == "complete":
            return f"✓ Image generated for **{meta.get('name', slug)}**: `output/images/{job.get('filename')}`"
        elif job.get("status") == "failed":
            return f"Generation failed: {job.get('error', 'unknown error')}"
        else:
            # Job is queued/running — wait for it (MCP calls are synchronous from client perspective)
            import time
            job_id = job.get("job_id")
            for _ in range(300):  # up to ~5 minutes
                time.sleep(1)
                result = get_job(job_id)
                if result and result.get("status") == "complete":
                    return f"✓ Image generated for **{meta.get('name', slug)}**: `output/images/{result.get('filename')}`"
                elif result and result.get("status") == "failed":
                    return f"Generation failed: {result.get('error', 'unknown error')}"
            return f"Image generation timed out (job {job_id}). Check status via the web UI."

    except ImportError:
        return (
            f"Image generation module not found.\n\n"
            f"**Image prompt for {meta.get('name', slug)}:**\n"
            f"`{image_prompt}`\n\n"
            f"Use this prompt with any text-to-image tool (Draw Things, ComfyUI, etc.)"
        )


# ─── Validation ─────────────────────────────────────────────────────────────

@mcp.tool(
    name="wb_validate",
    annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
)
async def wb_validate(project: str = "") -> str:
    """Validate project consistency: cross-references, timeline, geography, species, world flags.

    Args:
        project: Project name/slug.
    """
    project_dir = _resolve_project(project or None)
    script = _get_cli_script()

    result = subprocess.run(
        [sys.executable, str(script), "validate", "--project", str(project_dir)],
        capture_output=True, text=True, cwd=str(SERVER_ROOT)
    )
    output = result.stdout + result.stderr
    return output if output.strip() else "Validation complete — no output (check if project has entities)."


# ─── Generation / Writing ───────────────────────────────────────────────────

@mcp.tool(
    name="wb_wizard",
    annotations={"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False},
)
async def wb_wizard(
    mode: str = "yolo",
    size: str = "M",
    genre: str = "fantasy",
    seed: str = "",
    tone: str = "epic",
    project_type: str = "novel",
) -> str:
    """Generate a YOLO world-creation prompt from genre, size, and optional creative seed.

    Args:
        mode: 'yolo' for auto-generation, 'interactive' for step-by-step.
        size: World complexity: S (small), M (medium), L (large), XL (epic).
        genre: Genre: fantasy, scifi, modern, horror, post-apocalyptic, steampunk, custom.
        seed: Optional creative seed phrase (e.g., 'dying gods and shattered moons').
        tone: Prose/world tone: literary, pulp, young-adult, dark, gritty, epic.
        project_type: novel, series, campaign, game, worldbook.
    """
    script = _get_cli_script()

    cmd = [sys.executable, str(script), "wizard", mode,
           "--size", size.upper(), "--genre", genre,
           "--tone", tone, "--project-type", project_type]
    if seed:
        cmd.extend(["--seed", seed])

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(SERVER_ROOT))
    return result.stdout if result.stdout.strip() else f"Error: {result.stderr}"


@mcp.tool(
    name="wb_generate_history",
    annotations={"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False},
)
async def wb_generate_history(
    gen_type: str = "mixed",
    years: int = 100,
    project: str = "",
) -> str:
    """Generate a procedural history prompt from current world state.

    Args:
        gen_type: History focus: peaceful, conflict, catastrophe, mixed.
        years: Number of years of history to generate (10–100000).
        project: Project name/slug.
    """
    project_dir = _resolve_project(project or None)
    script = _get_cli_script()

    result = subprocess.run(
        [sys.executable, str(script), "generate", gen_type,
         "--years", str(years), "--project", str(project_dir)],
        capture_output=True, text=True, cwd=str(SERVER_ROOT)
    )
    return result.stdout if result.stdout.strip() else f"Error: {result.stderr}"


@mcp.tool(
    name="wb_write_chapter",
    annotations={"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False},
)
async def wb_write_chapter(
    chapter: int = 0,
    project: str = "",
) -> str:
    """Build a context-aware writing prompt loaded with style, characters, locations, and chapter outlines.

    Args:
        chapter: Chapter number to write. 0 or omit for 'next chapter' mode.
        project: Project name/slug.
    """
    project_dir = _resolve_project(project or None)
    script = _get_cli_script()

    cmd = [sys.executable, str(script), "write", "--project", str(project_dir)]
    if chapter and chapter > 0:
        cmd.extend(["--chapter", str(chapter)])

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(SERVER_ROOT))
    return result.stdout if result.stdout.strip() else f"Error: {result.stderr}"


@mcp.tool(
    name="wb_edit_review",
    annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
)
async def wb_edit_review(
    editor: str,
    project: str = "",
) -> str:
    """Generate an editor review prompt. 9 editors: character, continuity, dialogue, geography, pacing, plot, prose, sensitivity, worldrules.

    Args:
        editor: Editor persona name. Use 'list' to see all available editors.
        project: Project name/slug.
    """
    if editor.lower() == "list":
        if not EDITOR_DIR.exists():
            return "Error: Editor directory not found."
        lines = ["# Editor Personae\n"]
        for f in sorted(EDITOR_DIR.glob("*.yaml")):
            data = _load_yaml(f)
            lines.append(f"- **{f.stem}**: {data.get('focus', data.get('description', ''))}")
        return "\n".join(lines)

    project_dir = _resolve_project(project or None)
    script = _get_cli_script()

    result = subprocess.run(
        [sys.executable, str(script), "edit", editor, "--project", str(project_dir)],
        capture_output=True, text=True, cwd=str(SERVER_ROOT)
    )
    return result.stdout if result.stdout.strip() else f"Error: {result.stderr}"


# ═══════════════════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    mcp.run()
