#!/usr/bin/env python3
"""WorldBuilder Web App — Local dev server with API endpoints."""

import logging
import os
import sys
import json
import re
from logging.handlers import RotatingFileHandler
from pathlib import Path
from flask import Flask, jsonify, request, render_template, send_from_directory

# Add parent dir so we can import worldbuilder helpers
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import yaml

# ─── Image backend ───────────────────────────────────────────────────────────
# Z-Image-Turbo via mflux (MLX-native, Apple Silicon)

from imagegen import (
    get_status as imagegen_status, get_cached_image,
    submit_job, get_job, get_all_jobs, get_pending_completions,
    preload_model, enrich_prompt, get_style_presets,
    DEFAULT_STEPS, DEFAULT_WIDTH, DEFAULT_HEIGHT,
    get_preview_path,
)

from voicegen import (
    get_status as voicegen_status, get_cached_voice, build_voice_instruct,
    submit_job as voice_submit_job, get_job as voice_get_job,
    get_all_jobs as voice_get_all_jobs,
    preload_model as voice_preload_model,
    get_queue_length as voice_queue_length,
)

app = Flask(__name__, static_folder="static", template_folder="templates")

# ─── Helpers ────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).parent.parent
WORLDS_DIR = REPO_ROOT / "worlds"
PLAYGROUND_DIR = Path.home() / ".worldbuilder" / "images"
# Search both repo root (legacy) and worlds/ subdirectory
PROJECTS_ROOTS = [WORLDS_DIR, REPO_ROOT]

def find_projects():
    """Find all projects (dirs containing project.yaml) in worlds/ and repo root."""
    projects = []
    seen = set()
    for root in PROJECTS_ROOTS:
        if not root.exists():
            continue
        for p in sorted(root.iterdir()):
            if p.is_dir() and (p / "project.yaml").exists() and p.name not in seen:
                seen.add(p.name)
                with open(p / "project.yaml") as f:
                    config = yaml.safe_load(f) or {}
                projects.append({
                    "slug": p.name,
                    "title": config.get("title", p.name),
                    "genre": config.get("genre", "unknown"),
                    "type": config.get("type", "unknown"),
                    "path": str(p),
                    "location": "worlds" if root == WORLDS_DIR else "root",
                })
    return projects


def resolve_project_dir(slug):
    """Find the actual directory for a project slug, checking worlds/ first."""
    for root in PROJECTS_ROOTS:
        p = root / slug
        if p.is_dir() and (p / "project.yaml").exists():
            return p
    return None


def load_project(slug):
    """Load a project's config."""
    p = resolve_project_dir(slug)
    if not p:
        return None
    with open(p / "project.yaml") as f:
        return yaml.safe_load(f) or {}


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


ENTITY_DIRS = {
    "character": "characters", "location": "locations", "faction": "factions",
    "item": "items", "magic-system": "magic-systems", "arc": "arcs",
    "event": "events", "species": "species", "race": "races",
    "language": "languages", "lineage": "lineages",
}


def load_entity_file(filepath):
    """Parse a YAML frontmatter + Markdown file."""
    with open(filepath) as f:
        content = f.read()
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            meta = yaml.safe_load(parts[1]) or {}
            body = parts[2].strip()
            return {"meta": meta, "body": body, "file": str(filepath)}
    return {"meta": {}, "body": content, "file": str(filepath)}


def _resolve_location_meta(entities: dict, character_meta: dict) -> dict | None:
    """Look up a character's location and return its metadata (for regional defaults).

    Walks up the location parent chain until regional_defaults is found.
    """
    locations = entities.get("location", {})
    loc_slug = (character_meta.get("location") or "").strip()
    visited = set()
    while loc_slug and loc_slug not in visited:
        visited.add(loc_slug)
        loc_data = locations.get(loc_slug)
        if not loc_data:
            return None
        loc_meta = loc_data.get("meta", {})
        if loc_meta.get("regional_defaults"):
            return loc_meta
        loc_slug = (loc_meta.get("parent") or "").strip()
    return None


def collect_entities(project_slug):
    """Collect all entities for a project."""
    project_dir = resolve_project_dir(project_slug)
    world_dir = project_dir / "world"
    entities = {}
    for etype, dirname in ENTITY_DIRS.items():
        edir = world_dir / dirname
        entities[etype] = {}
        if edir.exists():
            for f in sorted(edir.glob("*.md")):
                data = load_entity_file(f)
                data["slug"] = f.stem
                data["entity_type"] = etype
                entities[etype][f.stem] = data
    # Also collect chapters
    ch_dir = project_dir / "chapters"
    entities["chapter"] = {}
    if ch_dir.exists():
        for f in sorted(ch_dir.glob("*.md")):
            data = load_entity_file(f)
            data["slug"] = f.stem
            data["entity_type"] = "chapter"
            entities["chapter"][f.stem] = data
    return entities


def load_calendar(project_slug):
    """Load calendar.yaml if present."""
    p = resolve_project_dir(project_slug)
    if not p:
        return {}
    cal_file = p / "world" / "calendar.yaml"
    if cal_file.exists():
        with open(cal_file) as f:
            return yaml.safe_load(f) or {}
    return {}


def load_economy(project_slug):
    """Load economy.yaml if present."""
    p = resolve_project_dir(project_slug)
    if not p:
        return {}
    eco_file = p / "world" / "economy.yaml"
    if eco_file.exists():
        with open(eco_file) as f:
            return yaml.safe_load(f) or {}
    return {}


def serialize_date(d):
    """Convert a WorldDate (dict or string) to display string."""
    if isinstance(d, dict):
        return d.get("display", f"{d.get('era_prefix', '')} {d.get('year', '?')}")
    return str(d) if d else "?"


# ─── Page Routes ────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ─── API Routes ─────────────────────────────────────────────────────────────

@app.route("/api/projects")
def api_projects():
    return jsonify(find_projects())


@app.route("/api/project/<slug>")
def api_project(slug):
    config = load_project(slug)
    if not config:
        return jsonify({"error": "Project not found"}), 404
    entities = collect_entities(slug)
    calendar = load_calendar(slug)
    economy = load_economy(slug)

    # Build stats
    stats = {}
    for etype, ents in entities.items():
        if ents:
            stats[etype] = len(ents)

    return jsonify({
        "config": config,
        "stats": stats,
        "calendar": calendar,
        "has_economy": bool(economy),
    })


@app.route("/api/project/<slug>/entities/<etype>")
def api_entities(slug, etype):
    entities = collect_entities(slug)
    if etype not in entities:
        return jsonify({"error": f"Unknown entity type: {etype}"}), 404

    q = request.args.get("q", "").lower()
    project_dir = resolve_project_dir(slug)
    project_config = load_project(slug)
    results = []
    for s, data in entities[etype].items():
        meta = data["meta"]
        name = meta.get("name", s)
        if q and q not in name.lower() and q not in s.lower():
            # Also search in body and meta values
            body_match = q in data.get("body", "").lower()
            meta_match = q in json.dumps(meta, default=str).lower()
            if not body_match and not meta_match:
                continue
        # Check for cached image
        image_prompt = (meta.get("descriptions") or {}).get("image_prompt") or (meta.get("heraldry") or {}).get("image_prompt")
        image_url = None
        if image_prompt:
            for style in ("photorealistic", "default", "anime", "cartoon"):
                cached = get_cached_image(project_dir, s, enrich_prompt(image_prompt, entity_meta=meta, project_config=project_config, style=style))
                if cached:
                    image_url = f"/api/project/{slug}/images/{cached}"
                    break

        results.append({
            "slug": s,
            "name": name,
            "type": etype,
            "meta": _clean_meta(meta),
            "image_url": image_url,
        })
    return jsonify(results)


@app.route("/api/project/<slug>/entity/<etype>/<entity_slug>")
def api_entity(slug, etype, entity_slug):
    entities = collect_entities(slug)
    if etype not in entities or entity_slug not in entities[etype]:
        return jsonify({"error": "Entity not found"}), 404
    data = entities[etype][entity_slug]
    return jsonify({
        "slug": entity_slug,
        "name": data["meta"].get("name", entity_slug),
        "type": etype,
        "meta": _clean_meta(data["meta"]),
        "body": data.get("body", ""),
    })


@app.route("/api/project/<slug>/timeline")
def api_timeline(slug):
    entities = collect_entities(slug)
    events = entities.get("event", {})
    timeline = []
    for s, data in events.items():
        m = data["meta"]
        d = m.get("date", m.get("start_date", {}))
        end_d = m.get("end_date")
        timeline.append({
            "slug": s,
            "name": m.get("name", s),
            "date": serialize_date(d),
            "end_date": serialize_date(end_d) if end_d else None,
            "type": m.get("type", "unknown"),
            "significance": m.get("significance", "minor"),
            "scope": m.get("scope", "local"),
            "sort_key": _date_sort_key(d),
            "participants": m.get("participants", []),
            "locations": m.get("locations", []),
            "caused_by": m.get("caused_by", []),
            "leads_to": m.get("leads_to", []),
        })
    timeline.sort(key=lambda x: x["sort_key"])
    return jsonify(timeline)


@app.route("/api/project/<slug>/geography")
def api_geography(slug):
    entities = collect_entities(slug)
    locations = entities.get("location", {})

    # Build hierarchy
    nodes = []
    links = []
    for s, data in locations.items():
        m = data["meta"]
        nodes.append({
            "slug": s,
            "name": m.get("name", s),
            "type": m.get("type", "unknown"),
            "parent": m.get("parent"),
            "population": m.get("population"),
            "climate": m.get("climate"),
            "description": (m.get("descriptions", {}).get("human", "") or "")[:200],
        })
        # Routes
        for route in m.get("routes", []):
            dest = route.get("to") or route.get("destination")
            if dest:
                methods = route.get("methods", [])
                modes = [md.get("mode", "?") for md in methods if isinstance(md, dict)] if methods else [route.get("method", "?")]
                links.append({
                    "source": s,
                    "target": dest,
                    "modes": modes,
                    "route_type": route.get("route_type", "minor"),
                })
    return jsonify({"nodes": nodes, "links": links})


@app.route("/api/project/<slug>/families")
def api_families(slug):
    entities = collect_entities(slug)
    characters = entities.get("character", {})
    lineages = entities.get("lineage", {})

    family_data = []
    for lin_slug, lin_data in lineages.items():
        members = []
        for char_slug, char_data in characters.items():
            m = char_data["meta"]
            lin_ref = m.get("lineage") or (m.get("family_links") or {}).get("lineage", "")
            if lin_ref and (slugify(lin_ref) == lin_slug or lin_ref.lower() == lin_data["meta"].get("name", "").lower()):
                family_links = m.get("family_links", {})
                members.append({
                    "slug": char_slug,
                    "name": m.get("name", char_slug),
                    "status": m.get("status", "unknown"),
                    "role": m.get("role", ""),
                    "parents": family_links.get("parents", []),
                    "spouse": family_links.get("spouse"),
                    "children": family_links.get("children", []),
                })
        family_data.append({
            "lineage_slug": lin_slug,
            "lineage_name": lin_data["meta"].get("name", lin_slug),
            "heraldry": lin_data["meta"].get("heraldry", {}),
            "members": members,
        })
    return jsonify(family_data)


@app.route("/api/project/<slug>/relationships")
def api_relationships(slug):
    entities = collect_entities(slug)
    characters = entities.get("character", {})

    nodes = []
    links = []
    for s, data in characters.items():
        m = data["meta"]
        nodes.append({
            "slug": s,
            "name": m.get("name", s),
            "status": m.get("status", "unknown"),
            "species": m.get("species", ""),
            "role": m.get("role", ""),
            "faction": m.get("faction"),
        })
        for rel in m.get("relationships", []):
            target = rel.get("entity") or rel.get("character") or rel.get("name", "")
            links.append({
                "source": s,
                "target": slugify(target) if target else "",
                "type": rel.get("type", "knows"),
                "description": rel.get("description", ""),
            })
    return jsonify({"nodes": nodes, "links": links})


@app.route("/api/project/<slug>/languages")
def api_languages(slug):
    entities = collect_entities(slug)
    langs = entities.get("language", {})

    result = []
    for s, data in langs.items():
        m = data["meta"]
        ft = m.get("family_tree", {})
        result.append({
            "slug": s,
            "name": m.get("name", s),
            "status": m.get("status", "living"),
            "family_name": ft.get("family_name", "Unknown"),
            "parent_language": ft.get("parent_language"),
            "child_languages": ft.get("child_languages", []),
            "intelligibility": m.get("intelligibility", []),
            "speakers": m.get("speakers", {}),
            "special": m.get("special", {}),
        })
    return jsonify(result)


@app.route("/api/project/<slug>/species")
def api_species(slug):
    entities = collect_entities(slug)
    species = entities.get("species", {})
    races = entities.get("race", {})

    result = []
    for s, data in species.items():
        m = data["meta"]
        sp_races = []
        for r_slug, r_data in races.items():
            if r_data["meta"].get("species") and slugify(r_data["meta"]["species"]) == s:
                sp_races.append({
                    "slug": r_slug,
                    "name": r_data["meta"].get("name", r_slug),
                })
        result.append({
            "slug": s,
            "name": m.get("name", s),
            "sentience": m.get("sentience", "unknown"),
            "biology": m.get("biology", {}),
            "habitat": m.get("habitat", {}),
            "races": sp_races,
            "description": (m.get("descriptions", {}).get("human", "") or "")[:300],
        })
    return jsonify(result)


@app.route("/api/project/<slug>/economy")
def api_economy(slug):
    economy = load_economy(slug)
    return jsonify(economy)


@app.route("/api/project/<slug>/flags")
def api_flags(slug):
    config = load_project(slug)
    return jsonify(config.get("world_flags", {}))


@app.route("/api/project/<slug>/search")
def api_search(slug):
    q = request.args.get("q", "").lower()
    if not q:
        return jsonify([])

    entities = collect_entities(slug)
    results = []
    for etype, ents in entities.items():
        for s, data in ents.items():
            meta = data["meta"]
            name = meta.get("name", s)
            score = 0
            if q in name.lower():
                score = 100
            elif q in s:
                score = 80
            elif q in data.get("body", "").lower():
                score = 40
            elif q in json.dumps(meta, default=str).lower():
                score = 20
            if score > 0:
                results.append({
                    "slug": s,
                    "name": name,
                    "type": etype,
                    "score": score,
                    "snippet": _get_snippet(data, q),
                })
    results.sort(key=lambda x: -x["score"])
    return jsonify(results[:50])


# ─── Image Generation (Background Jobs) ─────────────────────────────────────

@app.route("/api/imagegen/status")
def api_imagegen_status():
    """Check if the image generation backend is available."""
    status = imagegen_status()
    return jsonify(status)


@app.route("/api/imagegen/styles")
def api_imagegen_styles():
    """Return available image generation style presets."""
    return jsonify(get_style_presets())


@app.route("/api/project/<slug>/entity/<etype>/<entity_slug>/image", methods=["POST"])
def api_generate_entity_image(slug, etype, entity_slug):
    """Submit a background image generation job for an entity.

    Returns a job_id immediately. Poll /api/imagegen/job/<job_id> for status.
    """
    entities = collect_entities(slug)
    if etype not in entities or entity_slug not in entities[etype]:
        return jsonify({"error": "Entity not found"}), 404

    data = entities[etype][entity_slug]
    meta = data["meta"]

    # Find the image_prompt
    image_prompt = (meta.get("descriptions") or {}).get("image_prompt")
    if not image_prompt:
        image_prompt = (meta.get("heraldry") or {}).get("image_prompt")

    if not image_prompt:
        return jsonify({
            "error": "No visualization available for this entity — missing image_prompt in YAML frontmatter."
        }), 400

    body = request.get_json(silent=True) or {}

    project_config = load_project(slug)

    # Resolve style: explicit request > project visual_style > default
    style = body.get("style")
    if not style and project_config:
        style = project_config.get("visual_style") or project_config.get("style", {}).get("visual", "")

    job = submit_job(
        prompt=image_prompt,
        project_dir=resolve_project_dir(slug),
        project_slug=slug,
        entity_slug=entity_slug,
        entity_name=meta.get("name", entity_slug),
        entity_type=etype,
        seed=body.get("seed"),
        force=body.get("force", False),
        steps=body.get("steps", DEFAULT_STEPS),
        width=body.get("width", DEFAULT_WIDTH),
        height=body.get("height", DEFAULT_HEIGHT),
        entity_meta=meta,
        project_config=project_config,
        style=style or "photorealistic",
    )

    return jsonify(job)


@app.route("/api/imagegen/playground", methods=["POST"])
def api_playground_generate():
    """Submit a free-form image generation job (not tied to any entity).

    Expects JSON: {prompt, seed?, steps?, width?, height?}
    Images are saved to a shared playground cache directory.
    """
    body = request.get_json(silent=True) or {}
    prompt = (body.get("prompt") or "").strip()
    if not prompt:
        return jsonify({"error": "prompt is required"}), 400

    # Use ~/.worldbuilder/images/ for playground images
    PLAYGROUND_DIR.mkdir(parents=True, exist_ok=True)

    # Build a slug from the prompt (first few words)
    slug = re.sub(r"[^a-z0-9]+", "-", prompt[:40].lower()).strip("-") or "image"

    job = submit_job(
        prompt=prompt,
        project_dir=PLAYGROUND_DIR.parent,
        project_slug="_playground",
        entity_slug=slug,
        entity_name=prompt[:60],
        entity_type="playground",
        seed=body.get("seed"),
        force=body.get("force", False),
        steps=body.get("steps", DEFAULT_STEPS),
        width=body.get("width", DEFAULT_WIDTH),
        height=body.get("height", DEFAULT_HEIGHT),
        style=body.get("style", "photorealistic"),
        cache_subdir="images",
    )

    return jsonify(job)


@app.route("/api/imagegen/playground/images/<filename>")
def api_serve_playground_image(filename):
    """Serve a playground-generated image."""
    if not (PLAYGROUND_DIR / filename).exists():
        return jsonify({"error": "Image not found"}), 404
    return send_from_directory(str(PLAYGROUND_DIR), filename, mimetype="image/png")


@app.route("/api/imagegen/job/<job_id>")
def api_job_status(job_id):
    """Poll a specific job's status."""
    job = get_job(job_id)
    if job is None:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job)


@app.route("/api/imagegen/preview/<job_id>")
def api_imagegen_preview(job_id):
    """Serve the latest step preview image for an in-progress job."""
    preview = get_preview_path(job_id)
    if preview is None:
        return "", 204
    return send_from_directory(str(preview.parent), preview.name, mimetype="image/png")


@app.route("/api/imagegen/jobs")
def api_all_jobs():
    """List all image generation jobs, optionally filtered by project."""
    project = request.args.get("project")
    return jsonify(get_all_jobs(project))


@app.route("/api/imagegen/completions")
def api_completions():
    """Get jobs completed since a timestamp. Used for notification polling."""
    since = float(request.args.get("since", 0))
    return jsonify(get_pending_completions(since))


@app.route("/api/project/<slug>/entity/<etype>/<entity_slug>/image/check")
def api_check_entity_image(slug, etype, entity_slug):
    """Check if a cached image exists for this entity."""
    entities = collect_entities(slug)
    if etype not in entities or entity_slug not in entities[etype]:
        return jsonify({"cached": False})

    data = entities[etype][entity_slug]
    meta = data["meta"]

    image_prompt = (meta.get("descriptions") or {}).get("image_prompt")
    if not image_prompt:
        image_prompt = (meta.get("heraldry") or {}).get("image_prompt")

    if not image_prompt:
        return jsonify({"cached": False, "has_prompt": False})

    # Enrich prompt the same way the generate endpoint does, so the cache
    # key matches.  Check the most common style first (photorealistic),
    # then fall back to default.
    project_config = load_project(slug)
    project_dir = resolve_project_dir(slug)

    for style in ("photorealistic", "default", "anime", "cartoon"):
        enriched = enrich_prompt(image_prompt, meta, project_config, style=style)
        cached = get_cached_image(project_dir, entity_slug, enriched)
        if cached:
            return jsonify({
                "cached": True,
                "has_prompt": True,
                "url": f"/api/project/{slug}/images/{cached}",
                "prompt": image_prompt,
            })

    return jsonify({
        "cached": False,
        "has_prompt": True,
        "url": None,
        "prompt": image_prompt,
    })


@app.route("/api/project/<slug>/images/<filename>")
def api_serve_image(slug, filename):
    """Serve a generated image from the project's image cache."""
    if slug == "_playground":
        image_dir = PLAYGROUND_DIR
    else:
        proj = resolve_project_dir(slug)
        image_dir = proj / "output" / "images" if proj else Path("/dev/null")
    if not (image_dir / filename).exists():
        return jsonify({"error": "Image not found"}), 404
    return send_from_directory(str(image_dir), filename, mimetype="image/png")


# ─── Unified Generation Status ──────────────────────────────────────────────

@app.route("/api/genqueue/status")
def api_genqueue_status():
    """Return whether any generation (image or voice) is currently active."""
    from mlx_lock import mlx_lock
    img_status = imagegen_status()
    busy = mlx_lock.locked()
    img_queued = img_status.get("queue_length", 0)
    voice_queued = voice_queue_length()
    return jsonify({
        "busy": busy,
        "image_queue": img_queued,
        "voice_queue": voice_queued,
        "total_queued": img_queued + voice_queued,
    })


# ─── Voice Generation ────────────────────────────────────────────────────────

@app.route("/api/voicegen/status")
def api_voicegen_status():
    return jsonify(voicegen_status())

@app.route("/api/voicegen/voices")
def api_voicegen_voices():
    return jsonify({"note": "Qwen3-TTS VoiceDesign uses free-form instruct strings, not presets"})

@app.route("/api/project/<slug>/entity/<etype>/<entity_slug>/voice", methods=["POST"])
def api_generate_entity_voice(slug, etype, entity_slug):
    """Submit a voice sample generation job for a character."""
    entities = collect_entities(slug)
    if etype not in entities or entity_slug not in entities[etype]:
        return jsonify({"error": "Entity not found"}), 404

    data = entities[etype][entity_slug]
    meta = data["meta"]

    # Get voice config
    voice_config = meta.get("voice", {}) or {}
    sample_text = voice_config.get("sample_text", "")

    body = request.get_json(silent=True) or {}

    # Allow custom text from request body, fall back to sample_text
    text_to_speak = body.get("text", "").strip() or sample_text

    if not text_to_speak:
        return jsonify({"error": "No text provided and no sample_text in voice config"}), 400

    # Resolve character's location for regional voice defaults
    location_meta = _resolve_location_meta(entities, meta)

    # Build voice instruct (or use manual override from request body)
    instruct = body.get("instruct", "").strip()
    if not instruct:
        instruct = build_voice_instruct(voice_config, meta, location_meta)

    job = voice_submit_job(
        text=text_to_speak,
        instruct=instruct,
        project_dir=resolve_project_dir(slug),
        project_slug=slug,
        entity_slug=entity_slug,
        entity_name=meta.get("name", entity_slug),
        entity_type=etype,
        speed=body.get("speed", 1.0),
        force=body.get("force", False),
    )
    return jsonify(job)

@app.route("/api/voicegen/job/<job_id>")
def api_voice_job_status(job_id):
    job = voice_get_job(job_id)
    if job is None:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job)

@app.route("/api/project/<slug>/entity/<etype>/<entity_slug>/voice/check")
def api_check_entity_voice(slug, etype, entity_slug):
    """Check if a cached voice sample exists."""
    entities = collect_entities(slug)
    if etype not in entities or entity_slug not in entities[etype]:
        return jsonify({"cached": False})

    data = entities[etype][entity_slug]
    meta = data["meta"]
    voice_config = meta.get("voice", {}) or {}
    sample_text = voice_config.get("sample_text", "")

    if not sample_text:
        return jsonify({"cached": False, "has_voice": False})

    location_meta = _resolve_location_meta(entities, meta)
    instruct = build_voice_instruct(voice_config, meta, location_meta)

    project_dir = resolve_project_dir(slug)
    cached = get_cached_voice(project_dir, entity_slug, sample_text, instruct)

    return jsonify({
        "cached": cached is not None,
        "has_voice": True,
        "url": f"/api/project/{slug}/voices/{cached}" if cached else None,
        "instruct": instruct,
        "sample_text": sample_text,
    })

@app.route("/api/project/<slug>/voices/generate-all", methods=["POST"])
def api_generate_all_voices(slug):
    """Batch-generate voice samples for all characters with voice config.

    Skips characters that already have cached samples (unless force=true).
    Returns list of jobs submitted.
    """
    entities = collect_entities(slug)
    characters = entities.get("character", {})
    project_dir = resolve_project_dir(slug)
    if not project_dir:
        return jsonify({"error": "Project not found"}), 404

    body = request.get_json(silent=True) or {}
    force = body.get("force", False)

    jobs = []
    skipped = 0
    no_voice = 0

    for char_slug, data in characters.items():
        meta = data["meta"]
        voice_config = meta.get("voice", {}) or {}
        sample_text = voice_config.get("sample_text", "")
        if not sample_text:
            no_voice += 1
            continue

        location_meta = _resolve_location_meta(entities, meta)
        instruct = build_voice_instruct(voice_config, meta, location_meta)

        # Check cache
        if not force:
            cached = get_cached_voice(project_dir, char_slug, sample_text, instruct)
            if cached:
                skipped += 1
                continue

        job = voice_submit_job(
            text=sample_text,
            instruct=instruct,
            project_dir=project_dir,
            project_slug=slug,
            entity_slug=char_slug,
            entity_name=meta.get("name", char_slug),
            entity_type="character",
            speed=body.get("speed", 1.0),
            force=force,
        )
        jobs.append(job)

    return jsonify({
        "submitted": len(jobs),
        "skipped_cached": skipped,
        "skipped_no_voice": no_voice,
        "jobs": jobs,
    })


@app.route("/api/project/<slug>/voices/<filename>")
def api_serve_voice(slug, filename):
    """Serve a generated voice sample."""
    voice_dir = resolve_project_dir(slug) / "output" / "voices"
    if not (voice_dir / filename).exists():
        return jsonify({"error": "Voice not found"}), 404
    mimetype = "audio/mpeg" if filename.endswith(".mp3") else "audio/wav"
    return send_from_directory(str(voice_dir), filename, mimetype=mimetype)


# ─── Wizard / YOLO ──────────────────────────────────────────────────────────

TSHIRT_SIZES = {
    "S": {"label": "Small — Short Story / One-Shot", "entities": "13–45", "eras": "1–2", "history": "50–500y"},
    "M": {"label": "Medium — Novel / Short Campaign", "entities": "30–90", "eras": "2–3", "history": "200–2,000y"},
    "L": {"label": "Large — Book Series / Full Campaign", "entities": "87–253", "eras": "3–5", "history": "1K–10Ky"},
    "XL": {"label": "Extra Large — Epic Universe", "entities": "173–555", "eras": "4–8", "history": "5K–50Ky"},
}

@app.route("/api/wizard/sizes")
def api_wizard_sizes():
    return jsonify(TSHIRT_SIZES)


# ─── Helpers ────────────────────────────────────────────────────────────────

def _clean_meta(meta):
    """Make meta JSON-serializable."""
    def _convert(obj):
        if isinstance(obj, Path):
            return str(obj)
        if isinstance(obj, (set, frozenset)):
            return list(obj)
        return obj
    return json.loads(json.dumps(meta, default=_convert))


def _date_sort_key(d):
    if isinstance(d, dict):
        era = d.get("era_prefix", "")
        year = d.get("year", 0)
        return f"{era}:{year:010d}"
    return str(d) if d else ""


def _get_snippet(data, q):
    body = data.get("body", "")
    idx = body.lower().find(q)
    if idx >= 0:
        start = max(0, idx - 40)
        end = min(len(body), idx + len(q) + 40)
        return "..." + body[start:end] + "..."
    return ""


def _setup_logging():
    """Configure file + console logging to logs/ in the project root."""
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)

    fmt = logging.Formatter(
        "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Main app log — rotates at 5 MB, keeps 3 backups
    app_handler = RotatingFileHandler(
        log_dir / "webapp.log", maxBytes=5_000_000, backupCount=3
    )
    app_handler.setFormatter(fmt)
    app_handler.setLevel(logging.DEBUG)

    # Separate error log for quick triage
    err_handler = RotatingFileHandler(
        log_dir / "webapp-error.log", maxBytes=2_000_000, backupCount=2
    )
    err_handler.setFormatter(fmt)
    err_handler.setLevel(logging.WARNING)

    # Wire up Flask's logger + the root logger (catches imagegen, werkzeug, etc.)
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(app_handler)
    root.addHandler(err_handler)

    # Also keep console output for interactive use
    console = logging.StreamHandler()
    console.setFormatter(fmt)
    console.setLevel(logging.INFO)
    root.addHandler(console)

    # Quiet down noisy libraries
    logging.getLogger("werkzeug").setLevel(logging.INFO)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    logging.info("Logging to %s", log_dir)


if __name__ == "__main__":
    _setup_logging()

    port = int(sys.argv[1].rstrip(".,;")) if len(sys.argv) > 1 else 5000
    logging.info("WorldBuilder Web — http://localhost:%d", port)

    preload_model()
    voice_preload_model()

    app.run(host="127.0.0.1", port=port, debug=False)
