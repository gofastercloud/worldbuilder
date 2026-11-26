"""Entity file helpers shared by the CLI, web UI and MCP server.

Keep this module dependency-light (stdlib + PyYAML) so every entry point can import it.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


_FRONTMATTER_RE = re.compile(r"\A---[ \t]*\r?\n(.*?)^---[ \t]*$", re.DOTALL | re.MULTILINE)
_PLACEHOLDER_RE = re.compile(r'"\{\{(?:NAME|TITLE)\}\}"|\{\{(?:NAME|TITLE)\}\}')


def slugify(name: str) -> str:
    """Convert a name to a filename-safe slug."""
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def parse_frontmatter(filepath: str | Path) -> tuple[dict | None, str]:
    """Split a Markdown file into (frontmatter, body).

    Returns (None, full_text) when there is no frontmatter or it isn't valid YAML,
    so one malformed file can't take down a whole project listing. The YAML error
    is logged; `worldbuilder.py validate` reports it to the user.
    """
    with open(filepath) as f:
        content = f.read()

    # Delimiters are whole "---" lines; a "---" inside a value doesn't end the frontmatter
    m = _FRONTMATTER_RE.match(content)
    if not m:
        return None, content

    try:
        meta = yaml.safe_load(m.group(1))
    except yaml.YAMLError as e:
        logger.warning("Invalid YAML frontmatter in %s: %s", filepath, e)
        return None, content
    return meta, content[m.end():]


def fill_name_placeholders(template: str, name: str) -> str:
    """Substitute {{NAME}} / {{TITLE}} in an entity template.

    Quoted placeholders ("{{NAME}}") are replaced with a JSON-escaped string, which is
    also a valid YAML double-quoted scalar, so a name containing quotes or newlines
    can't inject extra frontmatter keys. Any remaining (body) placeholders get the
    name with line breaks collapsed.
    """
    quoted = json.dumps(name, ensure_ascii=False)
    one_line = " ".join(name.split())
    # Single pass: substituted text is never rescanned, so a name containing "{{NAME}}" can't re-trigger
    return _PLACEHOLDER_RE.sub(lambda m: quoted if m.group(0).startswith('"') else one_line, template)
