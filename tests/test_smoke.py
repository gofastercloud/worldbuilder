"""Smoke tests: every read-only CLI command and every GET API route runs against the example project.

These catch crashes and regressions in the large command/route bodies that the unit tests don't reach.
"""

import shutil
import subprocess
import sys
from pathlib import Path

import app as webapp
import pytest

ROOT = Path(__file__).parent.parent
EXAMPLE = ROOT / "assets" / "example" / "the-lattice"
CLI = ROOT / "scripts" / "worldbuilder.py"
EXAMPLE_CHARACTER = sorted(p.stem for p in (EXAMPLE / "world" / "characters").glob("[!_]*.md"))[0]


@pytest.fixture(scope="module")
def example_copy(tmp_path_factory):
    """A throwaway copy of the example project, so commands can't modify the real one."""
    dest = tmp_path_factory.mktemp("projects") / "the-lattice"
    shutil.copytree(EXAMPLE, dest)
    return dest


def run_cli(*args, cwd):
    return subprocess.run(
        [sys.executable, str(CLI), *args], capture_output=True, text=True, cwd=cwd, timeout=60
    )


# ── CLI ──────────────────────────────────────────────────────────────────────

READ_ONLY_COMMANDS = [
    ["stats"], ["timeline"], ["graph"], ["list", "character"], ["list", "event"], ["query", "lattice"],
    ["history", EXAMPLE_CHARACTER], ["crossref", EXAMPLE_CHARACTER], ["flags"], ["geography"],
    ["family", "house-meridian"], ["languages"], ["peoples"], ["economy"],
]


@pytest.mark.parametrize("cmd", READ_ONLY_COMMANDS, ids=lambda c: " ".join(c))
def test_cli_read_only_command(example_copy, cmd):
    result = run_cli(*cmd, "--project", str(example_copy), cwd=example_copy.parent)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip()
    assert "Traceback" not in result.stderr


def test_cli_validate_example_is_clean(example_copy):
    result = run_cli("validate", "--project", str(example_copy), cwd=example_copy.parent)
    assert result.returncode == 0, result.stderr
    assert "No issues found" in result.stdout


@pytest.mark.parametrize("fmt", ["md", "html"])
def test_cli_compile(example_copy, fmt):
    result = run_cli("compile", "--project", str(example_copy), "--format", fmt, cwd=example_copy.parent)
    assert result.returncode == 0, result.stderr
    assert "Traceback" not in result.stderr


def test_cli_wizard_yolo_writes_prompt(tmp_path):
    result = run_cli("wizard", "yolo", "--size", "S", "--genre", "fantasy", cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    prompts = list(tmp_path.glob("wizard-*.md"))
    assert len(prompts) == 1
    assert "Generate a complete fantasy world" in prompts[0].read_text()


def test_cli_validate_reports_bad_reference(example_copy, tmp_path):
    proj = tmp_path / "broken"
    shutil.copytree(example_copy, proj)
    char = proj / "world" / "characters" / "aelindra-velkaan.md"
    text = char.read_text()
    assert 'faction: "vaelori-concord"' in text
    char.write_text(text.replace('faction: "vaelori-concord"', 'faction: "no-such-faction-xyz"'))
    result = run_cli("validate", "--project", str(proj), cwd=tmp_path)
    assert "no-such-faction-xyz" in result.stdout + result.stderr


# ── Web routes ───────────────────────────────────────────────────────────────

@pytest.fixture
def client(example_copy, monkeypatch):
    monkeypatch.setattr(webapp, "PROJECTS_ROOTS", [example_copy.parent])
    webapp.app.config["TESTING"] = True
    return webapp.app.test_client()


PROJECT_ROUTES = [
    "", "/timeline", "/geography", "/families", "/relationships", "/languages",
    "/species", "/economy", "/flags", "/search?q=a",
]


@pytest.mark.parametrize("route", PROJECT_ROUTES)
def test_project_get_routes(client, route):
    res = client.get(f"/api/project/the-lattice{route}")
    assert res.status_code == 200, res.get_data(as_text=True)[:300]
    assert res.is_json


@pytest.mark.parametrize("route", [
    "/api/projects", "/api/imagegen/status", "/api/imagegen/styles", "/api/imagegen/jobs",
    "/api/imagegen/completions", "/api/genqueue/status", "/api/voicegen/status",
    "/api/voicegen/voices", "/api/wizard/sizes",
])
def test_global_get_routes(client, route):
    res = client.get(route)
    assert res.status_code == 200, res.get_data(as_text=True)[:300]


def test_index_page(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"app.js" in res.data


def test_every_entity_renders(client):
    """Open every entity of every type — exercises the per-type detail code paths."""
    stats = client.get("/api/project/the-lattice").get_json()["stats"]
    seen = 0
    for etype, count in stats.items():
        if not count:
            continue
        for ent in client.get(f"/api/project/the-lattice/entities/{etype}").get_json():
            res = client.get(f"/api/project/the-lattice/entity/{etype}/{ent['slug']}")
            assert res.status_code == 200, (etype, ent["slug"])
            seen += 1
    assert seen > 100
