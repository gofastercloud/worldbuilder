.PHONY: lint test validate-example verify

lint:
	uv run ruff check .

test:
	uv run pytest tests/ -q

validate-example:
	python3 skills/world-validate/scripts/validate.py skills/worldbuilding/assets/example-the-lattice

verify: lint test validate-example
