"""Tests for scripts/entity_io.py and the entry points that share it."""

import asyncio

import app as webapp
import pytest
import worldbuilder_mcp as mcp_server
import yaml
from entity_io import fill_name_placeholders, parse_frontmatter, slugify

# ── parse_frontmatter ────────────────────────────────────────────────────────

class TestParseFrontmatterTolerance:
    def test_invalid_yaml_returns_none(self, tmp_path):
        f = tmp_path / "bad.md"
        f.write_text("---\nname: [unclosed\n---\nBody\n")
        meta, body = parse_frontmatter(f)
        assert meta is None
        assert body.startswith("---")

    def test_webapp_lists_project_with_one_bad_file(self, tmp_project, monkeypatch):
        """One malformed entity must not take down the whole entity listing."""
        (tmp_project / "world" / "characters" / "broken.md").write_text("---\nname: [unclosed\n---\n")
        monkeypatch.setattr(webapp, "PROJECTS_ROOTS", [tmp_project.parent])
        entities = webapp.collect_entities("test-project")
        assert set(entities["character"]) == {"broken", "test-hero"}
        assert entities["character"]["broken"]["meta"] == {}

    def test_mcp_loader_tolerates_bad_file(self, tmp_path):
        f = tmp_path / "broken.md"
        f.write_text("---\n: : :\n  - [\n---\nprose\n")
        assert mcp_server._load_entity_file(f)["meta"] == {}

    def test_shared_slugify_is_used_everywhere(self):
        assert webapp.slugify is slugify
        assert mcp_server._slugify is slugify


# ── fill_name_placeholders ───────────────────────────────────────────────────

class TestFillNamePlaceholders:
    TEMPLATE = '---\nname: "{{NAME}}"\nstatus: alive\n---\n\n# {{NAME}}\n'

    def test_plain_name(self):
        out = fill_name_placeholders(self.TEMPLATE, "Kael Dawnblade")
        assert out == '---\nname: "Kael Dawnblade"\nstatus: alive\n---\n\n# Kael Dawnblade\n'

    def test_unicode_kept(self):
        assert 'name: "Æthelrÿd"' in fill_name_placeholders(self.TEMPLATE, "Æthelrÿd")

    @pytest.mark.parametrize("name", [
        'Evil"\nstatus: dead\nrole: "x',  # quote + newline: tries to add/override keys
        'Back\\slash "quoted"',
    ])
    def test_name_cannot_inject_frontmatter(self, name):
        out = fill_name_placeholders(self.TEMPLATE, name)
        meta = yaml.safe_load(out.split("---")[1])
        assert meta == {"name": name, "status": "alive"}

    def test_title_placeholder(self):
        assert fill_name_placeholders('title: "{{TITLE}}"', 'A "B"') == 'title: "A \\"B\\""'


# ── MCP server input handling ────────────────────────────────────────────────

class TestMcpInputs:
    @pytest.mark.parametrize("genre", ["../../etc/x", "fantasy/../../x", "sci fi", ""])
    def test_init_rejects_bad_genre(self, genre):
        out = asyncio.run(mcp_server.wb_init_project(name="Anything", genre=genre))
        assert out.startswith("Error: Invalid genre")

    def test_add_entity_escapes_name(self, tmp_project, monkeypatch):
        monkeypatch.setattr(mcp_server, "PROJECT_ROOTS", [tmp_project.parent])
        name = 'Mallory"\nstatus: dead'
        asyncio.run(mcp_server.wb_add_entity(entity_type="character", name=name, project="test-project"))
        created = tmp_project / "world" / "characters" / f"{slugify(name)}.md"
        meta, _ = parse_frontmatter(created)
        assert meta is not None
        assert meta["name"] == name
        assert meta["status"] == "alive"  # template default, not the injected value

    def test_cli_timeout_reported(self, monkeypatch):
        monkeypatch.setattr(mcp_server, "CLI_TIMEOUT_SECONDS", 0.2)
        result = asyncio.run(mcp_server._run_cli(["sleep", "5"]))
        assert result.returncode == -1
        assert "timed out" in result.stderr


class TestPlaceholderReentry:
    """A name containing a placeholder must not be substituted a second time (quote breakout)."""

    TEMPLATE = '---\nname: "{{NAME}}"\ntitle: "{{TITLE}}"\nstatus: alive\n---\n\n# {{NAME}}\n'

    @pytest.mark.parametrize("name", ['{{NAME}}" #', '{{TITLE}}" ---', '{{NAME}}{{TITLE}}"\n---\nx: 1'])
    def test_placeholder_in_name(self, name, tmp_path):
        f = tmp_path / "e.md"
        f.write_text(fill_name_placeholders(self.TEMPLATE, name))
        meta, body = parse_frontmatter(f)
        assert meta == {"name": name, "title": name, "status": "alive"}
        assert body.strip().startswith("#")


class TestFrontmatterDelimiters:
    def test_dashes_inside_value_do_not_end_frontmatter(self, tmp_path):
        f = tmp_path / "e.md"
        f.write_text('---\nname: "A --- B"\nmotto: x---y\n---\n\nBody --- text\n')
        meta, body = parse_frontmatter(f)
        assert meta == {"name": "A --- B", "motto": "x---y"}
        assert body == "\n\nBody --- text\n"

    def test_body_matches_previous_behaviour(self, tmp_path):
        f = tmp_path / "e.md"
        f.write_text("---\nname: Test\n---\n\n## Notes\nHello.\n")
        assert parse_frontmatter(f) == ({"name": "Test"}, "\n\n## Notes\nHello.\n")

    def test_empty_frontmatter(self, tmp_path):
        f = tmp_path / "e.md"
        f.write_text("---\n---\nBody\n")
        assert parse_frontmatter(f) == (None, "\nBody\n")
