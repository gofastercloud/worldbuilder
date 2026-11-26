"""Tests for fal.ai OAuth MCP config, world-art skill, slash command and templates."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "skills" / "world-validate" / "scripts" / "vendor"
if str(VENDOR) not in sys.path:
    sys.path.insert(0, str(VENDOR))

import yaml  # noqa: E402

FAL_MCP_URL = "https://mcp.fal.ai/mcp-relay"

ENTITY_TEMPLATES = [
    "characters",
    "locations",
    "factions",
    "items",
    "species",
    "events",
]


def _split_frontmatter(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{path} must start with YAML frontmatter"
    end = text.index("\n---\n", 4)
    fm_text = text[4:end]
    body = text[end + 5 :]
    data = yaml.safe_load(fm_text)
    assert isinstance(data, dict), f"{path} frontmatter must parse as a mapping"
    return data, body


def test_mcp_config_antigravity():
    path = ROOT / "mcp_config.json"
    assert path.is_file()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data == {"mcpServers": {"fal": {"url": FAL_MCP_URL}}}


def test_mcp_json_claude_code():
    path = ROOT / ".mcp.json"
    assert path.is_file()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data == {"mcpServers": {"fal": {"type": "http", "url": FAL_MCP_URL}}}


def test_world_art_skill_frontmatter_and_constraints():
    path = ROOT / "skills" / "world-art" / "SKILL.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    assert len(lines) < 300, f"SKILL.md must be under 300 lines, got {len(lines)}"

    fm, body = _split_frontmatter(path)
    assert set(fm.keys()) == {"name", "description"}
    assert fm["name"] == "world-art"
    assert isinstance(fm["description"], str) and fm["description"].strip()
    assert ": " not in fm["description"], "SKILL.md description must not contain ': '"

    # Sandbox safety rules from AGENTS.md
    assert "${CLAUDE_SKILL_DIR}" not in text
    assert "!`" not in text
    assert not re.search(r"(?m)^!\s*\S", text)

    # Core functional requirements
    assert FAL_MCP_URL in body
    assert "world_flags" in body
    assert "world_flags.magic.present" in body
    assert "output/images/" in body
    assert "world-visualiser" in body
    assert "descriptions.image_prompt" in body
    assert "style.visual" in body


def test_world_art_style_presets_reference():
    ref_path = ROOT / "skills" / "world-art" / "references" / "style-presets.md"
    assert ref_path.is_file()
    ref_text = ref_path.read_text(encoding="utf-8")

    styles_path = ROOT / "skills" / "worldbuilding" / "assets" / "templates" / "styles.yaml"
    styles_data = yaml.safe_load(styles_path.read_text(encoding="utf-8"))
    presets = styles_data["visual_style"]["preset"]["values"]
    assert len(presets) >= 5
    for preset in presets:
        assert f"`{preset}`" in ref_text, f"Preset {preset!r} missing from style-presets.md"


def test_wb_art_command():
    path = ROOT / "commands" / "wb-art.md"
    assert path.is_file()
    fm, body = _split_frontmatter(path)
    assert "description" in fm and isinstance(fm["description"], str) and fm["description"].strip()
    assert "world-art" in body
    assert "$ARGUMENTS" in body


def test_templates_restore_image_prompt_and_visual_style():
    templates_dir = ROOT / "skills" / "worldbuilding" / "assets" / "templates"

    # project_template.yaml has style.visual
    proj = yaml.safe_load((templates_dir / "project_template.yaml").read_text(encoding="utf-8"))
    assert "visual" in proj["style"]
    assert "preset" in proj["style"]["visual"]

    # styles.yaml has visual_style
    styles = yaml.safe_load((templates_dir / "styles.yaml").read_text(encoding="utf-8"))
    assert "visual_style" in styles
    assert "preset" in styles["visual_style"]

    # descriptions.yaml documents image_prompt
    desc_text = (templates_dir / "descriptions.yaml").read_text(encoding="utf-8")
    assert "image_prompt" in desc_text

    # Entity templates have descriptions.image_prompt
    for etype in ENTITY_TEMPLATES:
        tpl_path = templates_dir / etype / "_template.md"
        fm, _ = _split_frontmatter(tpl_path)
        assert "descriptions" in fm, f"{etype}/_template.md missing descriptions"
        assert "image_prompt" in fm["descriptions"], f"{etype}/_template.md missing descriptions.image_prompt"
