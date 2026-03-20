#!/usr/bin/env python3
"""
WorldBuilder Image Generation Backend — Z-Image-Turbo via mflux (MLX).

Background job system: submit_job() returns a job_id immediately,
the generation runs in a worker thread, and callers poll job status.

Uses Z-Image-Turbo (Apache 2.0, unrestricted) with GGUF-quantized weights
via mflux's MLX-native engine. LoRA-based style presets for anime,
photorealistic, and cartoon outputs.

Requirements (macOS Apple Silicon only):
    pip install mflux
"""

import hashlib
import os
import random
import re
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Optional

from mlx_lock import mlx_lock

# Eagerly import PreTrainedTokenizer before any other transformers usage.
# transformers 5.x uses lazy imports that race with concurrent model loading
# (voicegen loads Qwen3-TTS in parallel, partially resolving the lazy module
# and blocking mflux's later import of PreTrainedTokenizer).
try:
    from transformers import PreTrainedTokenizer  # noqa: F401
except ImportError:
    pass

# ─── Lazy model import ───────────────────────────────────────────────────────

_models = {}  # style -> loaded model instance
_model_lock = threading.Lock()
_mlx_available = None
_load_error = None

QUANTIZE_BITS = 4             # 4-bit quantization
MODEL_PATH = "filipstrand/Z-Image-Turbo-mflux-4bit"  # Pre-quantized — no on-the-fly quant
DEFAULT_STEPS = 9             # Z-Image-Turbo sweet spot
DEFAULT_WIDTH = 768
DEFAULT_HEIGHT = 768

# ─── Style Presets with LoRAs ────────────────────────────────────────────────
# Each style uses a Z-Image-Turbo base model with an optional LoRA.
# LoRA paths are HuggingFace repo IDs — mflux auto-downloads them.

STYLE_PRESETS = {
    "default": {
        "label": "Default",
        "description": "Z-Image-Turbo base model — versatile general-purpose",
        "lora_paths": [],
        "lora_scales": [],
        "prompt_prefix": "",
        "prompt_suffix": "high quality, detailed",
    },
    "photorealistic": {
        "label": "Photorealistic",
        "description": "Photography-quality realism with cinematic lighting",
        "lora_paths": ["suayptalha/Z-Image-Turbo-Realism-LoRA"],
        "lora_scales": [0.8],
        "prompt_prefix": "",
        "prompt_suffix": "cinematic lighting, sharp focus, high detail",
    },
    "anime": {
        "label": "Anime / Manga",
        "description": "Japanese anime and manga illustration style",
        "lora_paths": ["Haruka041/z-image-anime-lora"],
        "lora_scales": [0.85],
        "prompt_prefix": "anime style, ",
        "prompt_suffix": "vibrant colors, clean linework, cel-shaded",
    },
    "cartoon": {
        "label": "Digital Art / Cartoon",
        "description": "Stylized digital art illustration with vivid colors",
        "lora_paths": ["AiAF/D-ART_Z-Image-Turbo_LoRA"],
        "lora_scales": [0.8],
        "prompt_prefix": "digital art illustration, ",
        "prompt_suffix": "stylized, vivid colors, expressive",
    },
}


def get_style_presets() -> dict:
    """Return available style presets for the frontend."""
    return {
        key: {"label": v["label"], "description": v["description"]}
        for key, v in STYLE_PRESETS.items()
    }


# ─── MLX / mflux checks ────────────────────────────────────────────────────

def _check_mlx() -> bool:
    """Check if MLX is importable (Apple Silicon only)."""
    global _mlx_available, _load_error
    if _mlx_available is not None:
        return _mlx_available
    try:
        import mlx.core  # noqa: F401
        _mlx_available = True
    except ImportError:
        _mlx_available = False
        _load_error = "MLX not installed. Run: pip install mflux"
    return _mlx_available


def _check_mflux() -> bool:
    """Check if mflux is importable."""
    try:
        import mflux  # noqa: F401
        return True
    except ImportError:
        return False


def _load_model(style: str = "default"):
    """Load Z-Image-Turbo model with style-specific LoRA. Thread-safe lazy singleton per style."""
    global _load_error

    with _model_lock:
        if style in _models:
            return _models[style]

        if not _check_mlx():
            return None

        if not _check_mflux():
            _load_error = "mflux not installed. Run: pip install mflux"
            return None

        preset = STYLE_PRESETS.get(style, STYLE_PRESETS["default"])

        try:
            from mflux.models.z_image import ZImageTurbo

            lora_desc = ""
            if preset["lora_paths"]:
                lora_names = [p.split("/")[-1] for p in preset["lora_paths"]]
                lora_desc = f" + LoRA: {', '.join(lora_names)}"

            print(f"[imagegen] Loading Z-Image-Turbo ({QUANTIZE_BITS}-bit) style={style}{lora_desc}...")
            t0 = time.time()

            kwargs = {
                "quantize": QUANTIZE_BITS,
                "model_path": MODEL_PATH,
            }
            if preset["lora_paths"]:
                kwargs["lora_paths"] = preset["lora_paths"]
                kwargs["lora_scales"] = preset["lora_scales"]

            model = ZImageTurbo(**kwargs)

            elapsed = time.time() - t0
            print(f"[imagegen] Model ready ({style}) in {elapsed:.1f}s")
            _models[style] = model
            return model

        except Exception as e:
            _load_error = f"Failed to load model (style={style}): {e}"
            print(f"[imagegen] {_load_error}")
            import traceback
            traceback.print_exc()
            return None


# ─── Prompt Enrichment ───────────────────────────────────────────────────────

def enrich_prompt(
    base_prompt: str,
    entity_meta: Optional[dict] = None,
    project_config: Optional[dict] = None,
    style: str = "default",
) -> str:
    """Build the final prompt from subject description + world context + style layer.

    The image_prompt from the entity should describe the SUBJECT only (what to draw).
    Style/rendering instructions come from the LoRA preset and project config, not
    from the entity data. This keeps entity prompts reusable across styles.

    Prompt structure:
      [style prefix] + [subject from image_prompt] + [world/genre context] + [style suffix]
    """
    preset = STYLE_PRESETS.get(style, STYLE_PRESETS["default"])

    # ── Subject layer (from entity) ──
    subject = base_prompt.strip()

    # Add visual details from machine description if available
    if entity_meta:
        machine_desc = (entity_meta.get("descriptions") or {}).get("machine", "")
        if machine_desc and len(machine_desc) > 20:
            visual_keys = _extract_visual_details(machine_desc)
            if visual_keys:
                subject = f"{subject}, {visual_keys}"

    # ── World layer (from project config) ──
    world_context = ""
    if project_config:
        genre = project_config.get("genre", "")
        genre_hints = {
            "fantasy": "fantasy setting",
            "scifi": "sci-fi setting, futuristic",
            "horror": "dark atmosphere",
            "steampunk": "steampunk aesthetic",
            "post-apocalyptic": "post-apocalyptic setting",
            "cyberpunk": "cyberpunk setting, neon-lit",
        }
        visual_style = project_config.get("visual_style") or project_config.get("style", {}).get("visual", "")
        if isinstance(visual_style, dict):
            hints = [str(v) for k, v in visual_style.items()
                     if k not in ("negative_prompt",) and isinstance(v, str)]
            if hints:
                world_context = ", ".join(hints)
        elif visual_style:
            world_context = str(visual_style)
        elif genre and genre in genre_hints:
            world_context = genre_hints[genre]

    # ── Style layer (from LoRA preset — the dropdown selection) ──
    prefix = preset.get("prompt_prefix", "").rstrip(", ")
    suffix = preset.get("prompt_suffix", "")

    # Assemble: [style prefix], [subject], [world context], [style suffix]
    parts = []
    if prefix:
        parts.append(prefix)
    parts.append(subject)
    if world_context:
        parts.append(world_context)
    if suffix:
        parts.append(suffix)

    return ", ".join(parts)


# Quality guards applied as negative prompt (separate CLIP embedding)
NEGATIVE_PROMPT = "watermark, text, signature, border, logo, blurry, low quality, distorted, deformed, ugly"


def _extract_visual_details(machine_desc: str) -> str:
    """Pull visually relevant details from a machine description."""
    visual_keywords = []
    categories = [
        "appearance", "clothing", "armor", "weapon", "color", "hair",
        "eyes", "skin", "build", "height", "age", "scar", "tattoo",
        "uniform", "outfit", "gear", "equipment", "architecture",
        "material", "terrain", "atmosphere", "weather", "lighting",
    ]
    sentences = machine_desc.replace("\n", ". ").split(". ")
    for sentence in sentences:
        s_lower = sentence.lower().strip()
        if any(cat in s_lower for cat in categories):
            cleaned = sentence.strip().rstrip(".")
            if len(cleaned) > 10:
                visual_keywords.append(cleaned)
    if visual_keywords:
        combined = ". ".join(visual_keywords[:4])
        if len(combined) > 300:
            combined = combined[:300].rsplit(" ", 1)[0]
        return combined
    return ""


# ─── Image cache ─────────────────────────────────────────────────────────────

def _cache_dir(project_dir: Path, subdir: str = "output/images") -> Path:
    cache = project_dir / subdir
    cache.mkdir(parents=True, exist_ok=True)
    return cache


def _prompt_hash(prompt: str) -> str:
    return hashlib.sha256(prompt.encode()).hexdigest()[:16]


def get_cached_image(project_dir: Path, entity_slug: str, prompt: str, subdir: str = "output/images") -> Optional[str]:
    """Check if a cached image exists. Returns filename or None."""
    cache = _cache_dir(project_dir, subdir)
    phash = _prompt_hash(prompt)
    filename = f"{entity_slug}_{phash}.png"
    if (cache / filename).exists():
        return filename
    return None


# ─── Background Job System ───────────────────────────────────────────────────

_jobs = {}
_jobs_lock = threading.Lock()
_job_queue = []
_queue_lock = threading.Lock()
_worker_started = False


def _worker_loop():
    """Background worker: processes one image job at a time."""
    while True:
        job = None
        with _queue_lock:
            if _job_queue:
                job = _job_queue.pop(0)

        if job is None:
            time.sleep(0.5)
            continue

        job_id = job["job_id"]

        with _jobs_lock:
            _jobs[job_id]["status"] = "running"

        with mlx_lock:
            success, result = _generate_sync(
                prompt=job["prompt"],
                project_dir=job["project_dir"],
                entity_slug=job["entity_slug"],
                job_id=job_id,
                seed=job.get("seed"),
                steps=job.get("steps", DEFAULT_STEPS),
                width=job.get("width", DEFAULT_WIDTH),
                height=job.get("height", DEFAULT_HEIGHT),
                style=job.get("style", "default"),
                cache_subdir=job.get("cache_subdir", "output/images"),
            )

        with _jobs_lock:
            _jobs[job_id]["completed_at"] = time.time()
            if success:
                _jobs[job_id]["status"] = "complete"
                _jobs[job_id]["filename"] = result
                _jobs[job_id]["url"] = f"/api/project/{job['project_slug']}/images/{result}"
            else:
                _jobs[job_id]["status"] = "failed"
                _jobs[job_id]["error"] = result


def _ensure_worker():
    global _worker_started
    if _worker_started:
        return
    _worker_started = True
    t = threading.Thread(target=_worker_loop, daemon=True, name="imagegen-worker")
    t.start()


_PREVIEW_DIR = Path(__file__).parent.parent / "logs" / "previews"
_PREVIEW_DIR.mkdir(parents=True, exist_ok=True)


def get_preview_path(job_id: str) -> Optional[Path]:
    """Return the path to the latest step preview image for a job, if it exists."""
    p = _PREVIEW_DIR / f"{job_id}.png"
    return p if p.exists() else None


class _ProgressCallback:
    """Lightweight callback — updates step counter only, no VAE decode."""

    def __init__(self, job_id: str, total_steps: int):
        self._job_id = job_id
        self._total_steps = total_steps
        self._step = 0

    def call_in_loop(self, t, seed, prompt, latents, config, time_steps):
        self._step += 1
        with _jobs_lock:
            job = _jobs.get(self._job_id)
            if job:
                job["current_step"] = self._step
                job["total_steps"] = self._total_steps


class _StepPreviewCallback:
    """Callback that decodes latents at each step and saves a preview image.

    Also updates job progress. The preview is written to a temp file that
    the frontend can poll for live rendering.
    """

    def __init__(self, job_id: str, total_steps: int, model, latent_creator_cls):
        self._job_id = job_id
        self._total_steps = total_steps
        self._step = 0
        self._model = model
        self._latent_creator_cls = latent_creator_cls
        self._preview_path = _PREVIEW_DIR / f"{job_id}.png"

    def call_in_loop(self, t, seed, prompt, latents, config, time_steps):
        self._step += 1
        with _jobs_lock:
            job = _jobs.get(self._job_id)
            if job:
                job["current_step"] = self._step
                job["total_steps"] = self._total_steps
                job["preview_url"] = f"/api/imagegen/preview/{self._job_id}"

        # Decode latents to a preview image
        try:
            from mflux.utils.image_util import ImageUtil
            unpack = self._latent_creator_cls.unpack_latents(
                latents=latents, height=config.height, width=config.width,
            )
            if hasattr(self._model.vae, "decode_packed_latents"):
                decoded = self._model.vae.decode_packed_latents(unpack)
            else:
                decoded = self._model.vae.decode(unpack)
            gen_time = time_steps.format_dict["elapsed"] if time_steps is not None else 0
            img = ImageUtil.to_image(
                decoded_latents=decoded, config=config, seed=seed, prompt=prompt,
                quantization=self._model.bits, lora_paths=self._model.lora_paths,
                lora_scales=self._model.lora_scales, generation_time=gen_time,
            )
            img.save(path=str(self._preview_path), export_json_metadata=False)
        except Exception as e:
            print(f"[imagegen] Preview decode failed at step {self._step}: {e}")

    def cleanup(self):
        """Remove the preview file after generation completes."""
        try:
            self._preview_path.unlink(missing_ok=True)
        except Exception:
            pass


def _generate_sync(
    prompt: str,
    project_dir: Path,
    entity_slug: str,
    job_id: Optional[str] = None,
    seed: Optional[int] = None,
    steps: int = DEFAULT_STEPS,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    style: str = "default",
    cache_subdir: str = "output/images",
):
    """Synchronous image generation. Returns (success, filename_or_error)."""
    if not _check_mlx():
        return False, _load_error or "MLX not available."

    model = _load_model(style)
    if model is None:
        return False, _load_error or "Failed to load model."

    try:
        if seed is None:
            seed = random.randint(0, 2**31 - 1)

        style_label = STYLE_PRESETS.get(style, {}).get("label", style)
        print(f"[imagegen] Generating: {entity_slug} ({steps} steps, {width}x{height}, seed={seed}, style={style_label})")
        t0 = time.time()

        # Progress callback (step counter only — VAE decode preview was OOM-ing)
        progress_cb = None
        if job_id:
            progress_cb = _ProgressCallback(job_id, steps)
            model.callbacks.register(progress_cb)

        image = model.generate_image(
            seed=seed,
            prompt=prompt,
            negative_prompt=NEGATIVE_PROMPT,
            num_inference_steps=steps,
            height=height,
            width=width,
        )

        if progress_cb:
            try:
                model.callbacks.in_loop.remove(progress_cb)
            except ValueError:
                pass

        cache = _cache_dir(project_dir, cache_subdir)
        phash = _prompt_hash(prompt)
        filename = f"{entity_slug}_{phash}.png"
        image.save(path=str(cache / filename))

        elapsed = time.time() - t0
        print(f"[imagegen] Done: {filename} ({elapsed:.1f}s)")
        return True, filename

    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, f"Generation failed: {e}"


# ─── Public API ──────────────────────────────────────────────────────────────

def submit_job(
    prompt: str,
    project_dir: Path,
    project_slug: str,
    entity_slug: str,
    entity_name: str = "",
    entity_type: str = "",
    seed: Optional[int] = None,
    force: bool = False,
    steps: int = DEFAULT_STEPS,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    entity_meta: Optional[dict] = None,
    project_config: Optional[dict] = None,
    style: str = "default",
    cache_subdir: str = "output/images",
) -> dict:
    """Submit an image generation job. Returns immediately with a job_id."""
    # Enrich prompt with style and context
    enriched = enrich_prompt(prompt, entity_meta, project_config, style=style)

    # Check cache (enriched prompt is the cache key)
    if not force:
        cached = get_cached_image(project_dir, entity_slug, enriched, subdir=cache_subdir)
        if cached:
            job_id = str(uuid.uuid4())[:8]
            job = {
                "job_id": job_id,
                "status": "complete",
                "entity_slug": entity_slug,
                "entity_name": entity_name,
                "entity_type": entity_type,
                "prompt": enriched,
                "original_prompt": prompt,
                "filename": cached,
                "url": f"/api/project/{project_slug}/images/{cached}",
                "error": None,
                "started_at": time.time(),
                "completed_at": time.time(),
                "cached": True,
                "style": style,
            }
            with _jobs_lock:
                _jobs[job_id] = job
            return job

    if not _check_mlx():
        return {
            "job_id": None,
            "status": "failed",
            "error": _load_error or "MLX not available.",
        }

    _ensure_worker()

    job_id = str(uuid.uuid4())[:8]
    job = {
        "job_id": job_id,
        "status": "queued",
        "entity_slug": entity_slug,
        "entity_name": entity_name,
        "entity_type": entity_type,
        "prompt": enriched,
        "original_prompt": prompt,
        "filename": None,
        "url": None,
        "error": None,
        "started_at": time.time(),
        "completed_at": None,
        "cached": False,
        "current_step": 0,
        "total_steps": steps,
        "style": style,
        # Worker data
        "project_dir": project_dir,
        "project_slug": project_slug,
        "seed": seed,
        "steps": steps,
        "width": width,
        "height": height,
        "cache_subdir": cache_subdir,
    }

    with _jobs_lock:
        _jobs[job_id] = job

    with _queue_lock:
        _job_queue.append(job)

    return _sanitize_job(job)


def get_job(job_id: str) -> Optional[dict]:
    with _jobs_lock:
        job = _jobs.get(job_id)
    if job is None:
        return None
    return _sanitize_job(job)


def get_all_jobs(project_slug: str = None) -> list:
    with _jobs_lock:
        jobs = list(_jobs.values())
    result = []
    for j in jobs:
        if project_slug and j.get("project_slug") != project_slug:
            continue
        result.append(_sanitize_job(j))
    result.sort(key=lambda x: x.get("started_at", 0), reverse=True)
    return result


def get_pending_completions(since: float) -> list:
    with _jobs_lock:
        jobs = list(_jobs.values())
    result = []
    for j in jobs:
        if j.get("completed_at") and j["completed_at"] > since and j["status"] in ("complete", "failed"):
            result.append(_sanitize_job(j))
    return result


def _sanitize_job(job: dict) -> dict:
    return {
        "job_id": job.get("job_id"),
        "status": job.get("status"),
        "entity_slug": job.get("entity_slug"),
        "entity_name": job.get("entity_name"),
        "entity_type": job.get("entity_type"),
        "prompt": job.get("prompt"),
        "original_prompt": job.get("original_prompt"),
        "filename": job.get("filename"),
        "url": job.get("url"),
        "error": job.get("error"),
        "started_at": job.get("started_at"),
        "completed_at": job.get("completed_at"),
        "cached": job.get("cached", False),
        "current_step": job.get("current_step"),
        "total_steps": job.get("total_steps"),
        "style": job.get("style", "default"),
        "preview_url": job.get("preview_url"),
    }


def get_status() -> dict:
    """Return the current state of the image generation backend."""
    with _queue_lock:
        queue_len = len(_job_queue)
    mflux_ok = _check_mflux() if _check_mlx() else False
    return {
        "backend": "Z-Image-Turbo (mflux)" if mflux_ok else "unavailable",
        "mlx_available": _check_mlx(),
        "mflux_installed": mflux_ok,
        "model_loaded": len(_models) > 0,
        "loaded_styles": list(_models.keys()),
        "error": _load_error,
        "model": "Z-Image-Turbo",
        "quantize": QUANTIZE_BITS,
        "queue_length": queue_len,
        "default_steps": DEFAULT_STEPS,
        "default_size": f"{DEFAULT_WIDTH}x{DEFAULT_HEIGHT}",
        "available_styles": get_style_presets(),
    }


def preload_model():
    """Pre-load the default model in a background thread at app startup."""
    def _preload():
        if not _check_mlx():
            print("[imagegen] MLX not available — skipping preload")
            return

        if not _check_mflux():
            print("[imagegen] mflux not installed — run: pip install mflux")
            return

        # Load the default (no-LoRA) model first — it's the fastest to load
        model = _load_model("default")
        if model is not None:
            print("[imagegen] Default model pre-loaded and ready")
        else:
            print(f"[imagegen] Pre-load failed: {_load_error}")

        _ensure_worker()

    thread = threading.Thread(target=_preload, daemon=True, name="imagegen-preload")
    thread.start()
    print(f"[imagegen] Pre-loading Z-Image-Turbo ({QUANTIZE_BITS}-bit) in background...")
