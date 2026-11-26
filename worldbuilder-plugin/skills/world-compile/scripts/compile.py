#!/usr/bin/env python3
"""WorldBuilder manuscript compiler (plugin edition).

Usage:
    compile.py <project-dir> [--format md|html] [--out FILE]

Joins a project's chapters into one manuscript: a title page from project.yaml,
then each chapter in reading order, with its YAML frontmatter stripped. Output is
Markdown, or a single self-contained HTML file.

Chapters are read from:
    story/chapters/*.md            (CLI layout)
    stories/<name>/*.md            (one folder per story, as in the example project)

Files starting with "_" are skipped, as are files without frontmatter. Chapters
sort by book, then story folder, then chapter number, then file name.

Ported from scripts/worldbuilder.py (cmd_compile, markdown_to_html). Python 3.9+,
standard library only, except PyYAML which is vendored in world-validate.

Exit code: 0 on success, 1 on any error (missing project, no chapters, bad YAML
in project.yaml).
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

_VENDOR = Path(__file__).resolve().parents[2] / "world-validate" / "scripts" / "vendor"
if _VENDOR.is_dir():
    sys.path.insert(0, str(_VENDOR))
try:
    import yaml  # noqa: E402  (vendored PyYAML, or an installed copy as fallback)
except ImportError:
    sys.stderr.write("error: PyYAML not found. The vendored copy is missing and no installed yaml is available.\n")
    sys.exit(1)

CSS = """
        body { font-family: 'Georgia', 'Times New Roman', serif; max-width: 700px; margin: 2em auto;
               padding: 0 1em; line-height: 1.7; color: #2c2c2c; background: #fefefe; }
        h1 { font-size: 2.2em; text-align: center; margin-bottom: 0.2em; }
        h2 { font-size: 1.5em; margin-top: 2em; border-bottom: 1px solid #ddd; padding-bottom: 0.3em; }
        h3 { font-size: 1.2em; }
        p { margin: 0.8em 0; text-indent: 1.5em; }
        hr { border: none; border-top: 1px solid #ccc; margin: 2em 0; }
        em { font-style: italic; }
"""

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>__TITLE__</title>
    <style>__CSS__    </style>
</head>
<body>
__BODY__
</body>
</html>
"""


# ═════════════════════════════════════════════════════════════════════════════
# Reading
# ═════════════════════════════════════════════════════════════════════════════


def split_frontmatter(text: str) -> tuple[dict | None, str]:
    """Return (metadata, body). metadata is None when there is no usable frontmatter.

    Raises yaml.YAMLError when the frontmatter block is present but not valid YAML.
    """
    text = text.replace("\r\n", "\n")
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return None, text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            meta = yaml.safe_load("\n".join(lines[1:i])) or {}
            body = "\n".join(lines[i + 1 :])
            return (meta if isinstance(meta, dict) else None), body
    return None, text


def _as_int(value: object, default: int) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def chapter_files(project_dir: Path) -> list[tuple[str, Path]]:
    """Return (story group, path) for every candidate chapter file, unsorted."""
    found: list[tuple[str, Path]] = []
    chapters_dir = project_dir / "story" / "chapters"
    if chapters_dir.is_dir():
        found.extend(("", f) for f in sorted(chapters_dir.glob("*.md")))
    stories_dir = project_dir / "stories"
    if stories_dir.is_dir():
        for story in sorted(p for p in stories_dir.iterdir() if p.is_dir()):
            found.extend((story.name, f) for f in sorted(story.glob("*.md")))
    return [(group, f) for group, f in found if not f.name.startswith("_")]


def load_chapters(project_dir: Path) -> list[dict]:
    """Read and order chapters. Each item: meta, body, group, file."""
    chapters: list[dict] = []
    for group, path in chapter_files(project_dir):
        try:
            text = path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeDecodeError) as exc:
            sys.stderr.write(f"warning: skipping {path}: cannot read ({exc})\n")
            continue
        try:
            meta, body = split_frontmatter(text)
        except yaml.YAMLError as exc:
            sys.stderr.write(f"warning: skipping {path}: bad frontmatter ({exc})\n")
            continue
        if meta is None:
            continue
        chapters.append({"meta": meta, "body": body, "group": group, "file": path})

    chapters.sort(
        key=lambda c: (
            _as_int(c["meta"].get("book", 1), 1),
            c["group"],
            _as_int(c["meta"].get("number", c["meta"].get("chapter_number", 0)), 0),
            c["file"].name,
        )
    )
    return chapters


def load_project_config(project_dir: Path) -> dict:
    config_file = project_dir / "project.yaml"
    if not config_file.exists():
        raise FileNotFoundError(f"no project.yaml in {project_dir}")
    data = yaml.safe_load(config_file.read_text(encoding="utf-8-sig"))
    return data if isinstance(data, dict) else {}


# ═════════════════════════════════════════════════════════════════════════════
# Assembling
# ═════════════════════════════════════════════════════════════════════════════


def _chapter_body(body: str) -> str:
    """Drop a leading heading from the chapter body; the compiler writes its own."""
    lines = body.strip().split("\n")
    if lines and re.match(r"^#{1,2} ", lines[0]):
        lines = lines[1:]
    return "\n".join(lines).strip()


def build_markdown(config: dict, chapters: list[dict]) -> tuple[str, int]:
    """Return (manuscript markdown, total word count)."""
    title = str(config.get("title") or "Untitled")
    subtitle = str(config.get("subtitle") or "").strip()
    author = str(config.get("author") or "").strip()

    parts = [f"# {title}", ""]
    if subtitle:
        parts += [f"*{subtitle}*", ""]
    if author:
        parts += [f"*by {author}*", ""]
    parts += ["---", ""]

    words = 0
    for ch in chapters:
        meta = ch["meta"]
        ch_title = str(meta.get("title") or meta.get("name") or "Untitled Chapter")
        number = meta.get("number", meta.get("chapter_number"))
        heading = f"Chapter {number}: {ch_title}" if number not in (None, "") else ch_title
        body = _chapter_body(ch["body"])
        words += len(body.split())
        parts += [f"## {heading}", "", body, ""]

    return "\n".join(parts).rstrip() + "\n", words


def markdown_to_html(md_content: str, title: str) -> str:
    """Convert the compiler's Markdown subset to one self-contained HTML page.

    Handles #, ##, ### headings, horizontal rules, whole-line *emphasis* and
    paragraphs. All text is HTML-escaped.
    """
    out: list[str] = []
    paragraph: list[str] = []

    def flush() -> None:
        if paragraph:
            out.append(f"<p>{html.escape(' '.join(paragraph), quote=True)}</p>")
            paragraph.clear()

    for raw in md_content.split("\n"):
        line = raw.strip()
        if not line:
            flush()
        elif line.startswith("### "):
            flush()
            out.append(f"<h3>{html.escape(line[4:], quote=True)}</h3>")
        elif line.startswith("## "):
            flush()
            out.append(f"<h2>{html.escape(line[3:], quote=True)}</h2>")
        elif line.startswith("# "):
            flush()
            out.append(f"<h1>{html.escape(line[2:], quote=True)}</h1>")
        elif re.fullmatch(r"-{3,}", line):
            flush()
            out.append("<hr>")
        elif len(line) > 2 and line.startswith("*") and line.endswith("*"):
            flush()
            out.append(f"<p><em>{html.escape(line.strip('*'), quote=True)}</em></p>")
        else:
            paragraph.append(line)
    flush()

    return (
        HTML_TEMPLATE.replace("__TITLE__", html.escape(title, quote=True))
        .replace("__CSS__", CSS)
        .replace("__BODY__", "\n".join(out))
    )


# ═════════════════════════════════════════════════════════════════════════════
# CLI
# ═════════════════════════════════════════════════════════════════════════════


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Compile a WorldBuilder project's chapters into one manuscript.")
    ap.add_argument("project", help="project directory (contains project.yaml)")
    ap.add_argument("--format", choices=["md", "html"], default="md", help="output format (default: md)")
    ap.add_argument("--out", help="output file (default: <project>/output/manuscript.<format>)")
    args = ap.parse_args(argv)

    project_dir = Path(args.project).expanduser().resolve()
    if not project_dir.is_dir():
        sys.stderr.write(f"error: {project_dir} is not a directory\n")
        return 1
    try:
        config = load_project_config(project_dir)
    except (FileNotFoundError, yaml.YAMLError) as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 1

    chapters = load_chapters(project_dir)
    if not chapters:
        sys.stderr.write(
            f"error: no chapters found in {project_dir}. Looked for story/chapters/*.md and "
            "stories/*/*.md with YAML frontmatter.\n"
        )
        return 1

    manuscript, words = build_markdown(config, chapters)
    if args.format == "html":
        content = markdown_to_html(manuscript, str(config.get("title") or "Untitled"))
    else:
        content = manuscript

    out_path = Path(args.out).expanduser() if args.out else project_dir / "output" / f"manuscript.{args.format}"
    out_path = out_path.resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8")

    print(f"Compiled {len(chapters)} chapter(s), {words:,} words -> {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
