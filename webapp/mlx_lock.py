"""Shared MLX generation lock.

Apple Silicon uses unified memory for CPU and GPU. Running both image
generation (mflux ~5.5GB) and voice generation (Qwen3-TTS ~3.4GB)
simultaneously can exhaust memory and cause an OOM kill with no
traceback.

Both imagegen and voicegen workers acquire this lock before running
their respective models, ensuring only one MLX model is active at
a time.
"""

import threading

mlx_lock = threading.Lock()
