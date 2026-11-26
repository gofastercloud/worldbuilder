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

from mlx_lock import mlx_lock

logger = logging.getLogger(__name__)

# ── State ──
_model = None
_model_lock = threading.Lock()
_jobs: dict[str, dict] = {}
_job_lock = threading.Lock()
_job_queue: list[tuple[dict, Path]] = []
_queue_lock = threading.Lock()
_worker_started = False
_worker_lock = threading.Lock()

MODEL_ID = "mlx-community/Qwen3-TTS-12Hz-1.7B-VoiceDesign-bf16"

# Request limits
MAX_TEXT_CHARS = 1000         # roughly a minute of speech
MAX_INSTRUCT_CHARS = 1000
MIN_SPEED, MAX_SPEED = 0.5, 2.0
MAX_QUEUED_JOBS = 50          # pending jobs; further submissions are rejected
MAX_FINISHED_JOBS = 200       # finished jobs kept in memory for status polling


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
            from mlx_audio.tts.utils import load_model  # pyright: ignore[reportMissingImports]
            _model = load_model(MODEL_ID)
            logger.info("Qwen3-TTS VoiceDesign loaded.")
        except Exception as e:
            logger.error("Failed to load Qwen3-TTS: %s", e)
            _model = None
    return _model


def preload_model():
    """Pre-load model in background thread (called on webapp startup).

    Holds mlx_lock so this can't load concurrently with the image model (OOM risk).
    """
    def _preload():
        with mlx_lock:
            _get_model()

    t = threading.Thread(target=_preload, daemon=True, name="voicegen-preload")
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


def _worker_loop():
    """Background worker: processes one voice job at a time."""
    while True:
        item = None
        with _queue_lock:
            if _job_queue:
                item = _job_queue.pop(0)

        if item is None:
            time.sleep(0.5)
            continue

        job, project_dir = item
        _update_job(job, status="generating")

        with mlx_lock:
            _run_job(job, project_dir)


def _ensure_worker():
    global _worker_started
    with _worker_lock:
        if _worker_started:
            return
        _worker_started = True
    t = threading.Thread(target=_worker_loop, daemon=True, name="voicegen-worker")
    t.start()


def _update_job(job: dict, **fields) -> None:
    """Mutate a job under _job_lock so pollers never see a half-updated job."""
    with _job_lock:
        job.update(fields)


def _prune_finished_jobs() -> None:
    """Drop the oldest finished jobs beyond MAX_FINISHED_JOBS. Caller must hold _job_lock."""
    finished = [j for j in _jobs.values() if j.get("status") in ("completed", "failed")]
    if len(finished) <= MAX_FINISHED_JOBS:
        return
    finished.sort(key=lambda j: j.get("completed_at") or j.get("created_at") or 0)
    for j in finished[: len(finished) - MAX_FINISHED_JOBS]:
        _jobs.pop(j["job_id"], None)


def validate_request(text: object, speed: object = 1.0, instruct: object = "") -> tuple[str, float]:
    """Validate voice request input. Raises ValueError with a user-facing message."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("text is required")
    if len(text) > MAX_TEXT_CHARS:
        raise ValueError(f"text must be at most {MAX_TEXT_CHARS} characters")
    if not isinstance(instruct, str) or len(instruct) > MAX_INSTRUCT_CHARS:
        raise ValueError(f"instruct must be a string of at most {MAX_INSTRUCT_CHARS} characters")
    if isinstance(speed, bool) or not isinstance(speed, (int, float)):
        raise ValueError("speed must be a number")
    if not MIN_SPEED <= speed <= MAX_SPEED:
        raise ValueError(f"speed must be between {MIN_SPEED} and {MAX_SPEED}")
    return text, float(speed)


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
    """Submit a voice generation job. Returns job dict immediately.

    Raises ValueError if text or speed are invalid (see validate_request).
    """
    text, speed = validate_request(text, speed, instruct)
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

    _ensure_worker()

    job = {
        "job_id": job_id,
        "status": "queued",
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
        "url": None,
        "error": None,
    }

    with _queue_lock:
        if len(_job_queue) >= MAX_QUEUED_JOBS:
            return {"job_id": None, "status": "failed", "error": "Voice queue is full — try again later."}
        with _job_lock:
            _jobs[job_id] = job
            _prune_finished_jobs()
            snapshot = dict(job)
        _job_queue.append((job, project_dir))

    return snapshot


def _run_job(job: dict, project_dir: Path):
    """Execute a voice generation job (called by worker with mlx_lock held)."""
    try:
        model = _get_model()
        if model is None:
            _update_job(job, status="failed", error="TTS model not available (still loading?)",
                        completed_at=time.time())
            return

        import numpy as np  # pyright: ignore[reportMissingImports]
        import soundfile as sf  # pyright: ignore[reportMissingImports]

        logger.debug("Generating voice: instruct=%r text_chars=%d", job["instruct"], len(job["text"]))

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

        _update_job(
            job,
            status="completed",
            filename=filename,
            url=f"/api/project/{job['project_slug']}/voices/{filename}",
            completed_at=time.time(),
        )
        logger.info("Voice generated: %s (%.1fs audio)",
                     filename, len(audio) / sample_rate)

    except Exception as e:
        _update_job(job, status="failed", error=str(e), completed_at=time.time())
        logger.error("Voice generation failed: %s", e)


def get_job(job_id: str) -> dict | None:
    """Return a snapshot of a job (a copy, so callers can't race the worker)."""
    with _job_lock:
        job = _jobs.get(job_id)
        return dict(job) if job is not None else None


def get_all_jobs(project: str | None = None) -> list[dict]:
    with _job_lock:
        jobs = [dict(j) for j in _jobs.values()]
    if project:
        jobs = [j for j in jobs if j.get("project_slug") == project]
    return sorted(jobs, key=lambda j: j.get("created_at", 0), reverse=True)


def get_queue_length() -> int:
    with _queue_lock:
        return len(_job_queue)
