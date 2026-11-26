#!/usr/bin/env python3
"""Build world-viewer.html (a single self-contained page) for a worldbuilding project.

Usage:
    build_viewer.py <project-dir> [--out FILE] [--json-only] [--template PATH] [--embed-images]

Reads assets/viewer/index.html (or --template), inlines the css/*.css files (sorted) at
`<!--__CSS__-->` and the scripts at `<!--__JS__-->` (js/core.js, then js/views/*.js sorted, then
js/main.js), and replaces the single marker `/*__WORLD_DATA__*/null` with the JSON payload from
viz_data.build_viz_data(). The css and js folders are looked up next to the template. If assets/viewer
is absent, a minimal page that dumps the JSON is used. `--json-only` writes viz.json instead.
Exit code 1 if there is no project.yaml.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import viz_data  # noqa: E402

MARKER = "/*__WORLD_DATA__*/null"
CSS_MARKER = "<!--__CSS__-->"
JS_MARKER = "<!--__JS__-->"
DEFAULT_TEMPLATE = Path(__file__).resolve().parents[1] / "assets" / "viewer" / "index.html"
PLACEHOLDER = (
    '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
    '<meta name="viewport" content="width=device-width, initial-scale=1">'
    "<title>World viewer (placeholder)</title></head><body>"
    "<p>The viewer template (assets/viewer.html) is not installed; showing the raw data.</p>"
    '<pre id="dump"></pre>\n<script>\nconst WORLD = ' + MARKER + ';\n'
    'document.getElementById("dump").textContent = JSON.stringify(WORLD, null, 2);\n</script>\n</body></html>\n'
)


def to_script_json(data):
    """JSON safe to embed inside a <script> element."""
    text = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return (
        text.replace("<", "\\u003c")  # covers </script> and <!--
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
        .replace(" ", "\\u2028")
        .replace(" ", "\\u2029")
    )


def _read_all(files):
    return "\n".join(f.read_text(encoding="utf-8") for f in files)


def assemble_template(template_path):
    """Read the shell and inline its css and js (found beside it). Missing files are skipped."""
    text = template_path.read_text(encoding="utf-8")
    base = template_path.parent
    if CSS_MARKER in text:
        css = _read_all(sorted((base / "css").glob("*.css")))
        if "</style" in css.lower():
            raise ValueError("css must not contain </style")
        text = text.replace(CSS_MARKER, ("<style>\n" + css + "\n</style>"))
    if JS_MARKER in text:
        files = []
        if (base / "js" / "core.js").exists():
            files.append(base / "js" / "core.js")
        files += sorted((base / "js" / "views").glob("*.js"))
        if (base / "js" / "main.js").exists():
            files.append(base / "js" / "main.js")
        js = _read_all(files)
        if "</script" in js.lower():
            raise ValueError("js must not contain </script")
        text = text.replace(JS_MARKER, ("<script>\n" + js + "\n</script>"))
    return text



def render_html(data, template_text):
    if template_text.count(MARKER) != 1:
        raise ValueError(f"template must contain the marker {MARKER!r} exactly once")
    return template_text.replace(MARKER, to_script_json(data))


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build the world viewer HTML")
    ap.add_argument("project")
    ap.add_argument("--out", help="output file (default: <project>/output/world-viewer.html)")
    ap.add_argument("--json-only", action="store_true", help="write viz.json instead of the HTML page")
    ap.add_argument("--template", help="HTML template path (default: assets/viewer/index.html)")
    ap.add_argument(
        "--embed-images", action="store_true", help="base64-encode entity images as data URIs for portability"
    )
    args = ap.parse_args(argv)

    project = Path(args.project)
    if not (project / "project.yaml").exists():
        print(f"error: no project.yaml in {project}. Pass the project folder.", file=sys.stderr)
        return 1
    data = viz_data.build_viz_data(project, embed_images=args.embed_images)

    if args.json_only:
        out = Path(args.out) if args.out else project / "output" / "viz.json"
        text = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    else:
        out = Path(args.out) if args.out else project / "output" / "world-viewer.html"
        tpl = Path(args.template) if args.template else DEFAULT_TEMPLATE
        if tpl.exists():
            try:
                template_text = assemble_template(tpl)
            except ValueError as exc:
                print(f"error: {exc}", file=sys.stderr)
                return 1
        elif args.template:
            print(f"error: template not found: {tpl}", file=sys.stderr)
            return 1
        else:
            template_text = PLACEHOLDER
        try:
            text = render_html(data, template_text)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"wrote {out} ({len(text) // 1024} KB)")
    for w in data["warnings"]:
        print(f"note: {w}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
