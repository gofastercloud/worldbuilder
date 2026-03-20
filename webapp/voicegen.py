"""Voice generation backend using Qwen3-TTS VoiceDesign via mlx-audio.

Qwen3-TTS VoiceDesign generates distinct voices from natural language
descriptions (the 'instruct' parameter). Each character gets a unique
voice based on their voice.description, tags, accent, dialect, and
regional defaults from their home location.
"""

import hashlib
import logging
import re
import threading
import time
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

# ── State ──
_model = None
_model_lock = threading.Lock()
_jobs: dict[str, dict] = {}
_job_lock = threading.Lock()

MODEL_ID = "mlx-community/Qwen3-TTS-12Hz-1.7B-VoiceDesign-bf16"


def build_voice_instruct(
    voice_config: dict,
    character_meta: dict,
    location_meta: dict | None = None,
) -> str:
    """Build a VoiceDesign instruct string from character + location data.

    Inheritance chain (first non-empty wins for accent/dialect):
      1. voice_config.instruct (manual override — returned verbatim)
      2. Character-level voice fields (description, tags, accent, dialect)
      3. Location regional_defaults (accent, dialect, tags)

    The instruct string is free-form natural language that Qwen3-TTS uses
    to design a unique voice. It should describe gender, age, vocal quality,
    accent, and speaking style.
    """
    # Manual override — bypass all auto-generation
    manual = (voice_config.get("instruct") or "").strip()
    if manual:
        return manual

    parts = []

    # ── Gender ──
    gender = (character_meta.get("gender") or "").strip().lower()
    if gender in ("male", "m", "man"):
        parts.append("male")
    elif gender in ("female", "f", "woman"):
        parts.append("female")

    # ── Age ──
    age_raw = str(character_meta.get("age") or "").strip()
    if age_raw:
        age_match = re.match(r"(\d+)", age_raw)
        if age_match:
            age_num = int(age_match.group(1))
            if age_num < 20:
                parts.append("young, teenage")
            elif age_num < 35:
                parts.append("young adult")
            elif age_num < 50:
                parts.append("middle-aged")
            elif age_num < 65:
                parts.append("mature")
            else:
                parts.append("elderly")

    # ── Voice description (richest source) ──
    desc = (voice_config.get("description") or "").strip()
    if desc:
        parts.append(desc)

    # ── Voice tags as supplementary texture ──
    tags = voice_config.get("tags") or []
    texture_tags = [t for t in tags if t.lower() not in ("male", "female")]
    if texture_tags:
        parts.append(f"Voice qualities: {', '.join(texture_tags)}")

    # ── Accent (character > location regional_defaults) ──
    accent = (voice_config.get("accent") or "").strip()
    if not accent and location_meta:
        rd = location_meta.get("regional_defaults") or {}
        accent = ((rd.get("voice") or {}).get("accent") or "").strip()
    if accent:
        parts.append(f"Speaking with a {accent} accent")

    # ── Dialect (character > location regional_defaults) ──
    dialect = (voice_config.get("dialect") or "").strip()
    if not dialect and location_meta:
        rd = location_meta.get("regional_defaults") or {}
        dialect = ((rd.get("voice") or {}).get("dialect") or "").strip()
    if dialect:
        parts.append(f"Speech register: {dialect}")

    instruct = ". ".join(parts)
    if not instruct:
        instruct = "A neutral, clear speaking voice."
    return instruct


def _get_model():
    """Lazy-load the Qwen3-TTS VoiceDesign model."""
    global _model
    if _model is not None:
        return _model
    with _model_lock:
        if _model is not None:
            return _model
        logger.info("Loading Qwen3-TTS VoiceDesign (%s)...", MODEL_ID)
        try:
            from mlx_audio.tts.utils import load_model
            _model = load_model(MODEL_ID)
            logger.info("Qwen3-TTS VoiceDesign loaded.")
        except Exception as e:
            logger.error("Failed to load Qwen3-TTS: %s", e)
            _model = None
    return _model


def preload_model():
    """Pre-load model in background thread (called on webapp startup)."""
    t = threading.Thread(target=_get_model, daemon=True)
    t.start()


def get_status() -> dict:
    """Check if TTS backend is available."""
    return {
        "available": _model is not None,
        "model": "Qwen3-TTS VoiceDesign (1.7B)",
        "loading": _model_lock.locked(),
    }


def _cache_path(project_dir: Path, entity_slug: str) -> Path:
    """Get the cache directory for voice samples."""
    cache_dir = project_dir / "output" / "voices"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def get_cached_voice(project_dir: Path, entity_slug: str, text: str, instruct: str) -> str | None:
    """Check if a cached voice sample exists. Returns filename or None."""
    cache_dir = _cache_path(project_dir, entity_slug)
    cache_key = hashlib.sha256(f"{entity_slug}:{instruct}:{text}".encode()).hexdigest()[:16]
    filename = f"{entity_slug}_{cache_key}.mp3"
    if (cache_dir / filename).exists():
        return filename
    return None


def submit_job(
    text: str,
    instruct: str,
    project_dir: Path,
    project_slug: str,
    entity_slug: str,
    entity_name: str,
    entity_type: str,
    speed: float = 1.0,
    force: bool = False,
    language: str = "English",
) -> dict:
    """Submit a voice generation job. Returns job dict immediately."""
    job_id = str(uuid.uuid4())[:8]

    # Check cache first
    if not force:
        cached = get_cached_voice(project_dir, entity_slug, text, instruct)
        if cached:
            return {
                "job_id": job_id,
                "status": "completed",
                "entity_slug": entity_slug,
                "filename": cached,
                "url": f"/api/project/{project_slug}/voices/{cached}",
                "cached": True,
            }

    job = {
        "job_id": job_id,
        "status": "pending",
        "entity_slug": entity_slug,
        "entity_name": entity_name,
        "entity_type": entity_type,
        "project_slug": project_slug,
        "instruct": instruct,
        "text": text,
        "speed": speed,
        "language": language,
        "created_at": time.time(),
        "completed_at": None,
        "filename": None,
        "error": None,
    }

    with _job_lock:
        _jobs[job_id] = job

    thread = threading.Thread(target=_run_job, args=(job, project_dir), daemon=True)
    thread.start()

    return job


def _run_job(job: dict, project_dir: Path):
    """Execute a voice generation job in background."""
    try:
        job["status"] = "generating"

        model = _get_model()
        if model is None:
            job["status"] = "failed"
            job["error"] = "TTS model not available (still loading?)"
            return

        import numpy as np
        import soundfile as sf

        logger.debug("Generating voice: instruct=%r text=%r", job["instruct"], job["text"])

        results = list(model.generate(
            text=job["text"],
            instruct=job["instruct"],
            language=job.get("language", "English"),
        ))

        # Concatenate audio chunks
        audio_parts = []
        sample_rate = 24000
        for r in results:
            audio_np = np.array(r.audio, dtype=np.float32)
            audio_parts.append(audio_np)
            sample_rate = r.sample_rate

        audio = np.concatenate(audio_parts)

        # Save to cache
        cache_dir = _cache_path(project_dir, job["entity_slug"])
        cache_key = hashlib.sha256(
            f"{job['entity_slug']}:{job['instruct']}:{job['text']}".encode()
        ).hexdigest()[:16]
        filename = f"{job['entity_slug']}_{cache_key}.mp3"
        output_path = cache_dir / filename

        sf.write(str(output_path), audio, sample_rate)

        job["status"] = "completed"
        job["filename"] = filename
        job["completed_at"] = time.time()
        logger.info("Voice generated: %s (%.1fs audio)",
                     filename, len(audio) / sample_rate)

    except Exception as e:
        job["status"] = "failed"
        job["error"] = str(e)
        logger.error("Voice generation failed: %s", e)


def get_job(job_id: str) -> dict | None:
    return _jobs.get(job_id)


def get_all_jobs(project: str | None = None) -> list[dict]:
    with _job_lock:
        jobs = list(_jobs.values())
    if project:
        jobs = [j for j in jobs if j.get("project_slug") == project]
    return sorted(jobs, key=lambda j: j.get("created_at", 0), reverse=True)
