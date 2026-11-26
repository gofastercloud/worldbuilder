.PHONY: verify lint typecheck test sync

# --inexact keeps optional extras (e.g. all-media) installed; --locked fails if uv.lock is stale
sync:
	uv sync --locked --inexact --extra dev --extra mcp

lint:
	uv run ruff check .

typecheck:
	uv run pyright

test:
	uv run pytest tests/ -q

verify: sync lint typecheck test
