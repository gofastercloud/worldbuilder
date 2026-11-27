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
import http.server
import json
import mimetypes
import re
import sys
import urllib.parse
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


def _load_template(template_arg):
    tpl = Path(template_arg) if template_arg else DEFAULT_TEMPLATE
    if tpl.exists():
        return assemble_template(tpl)
    if template_arg:
        raise FileNotFoundError(f"template not found: {tpl}")
    return PLACEHOLDER


def _is_local_host(host_header):
    if not host_header:
        return True
    host = host_header.strip().lower()
    if host.startswith("["):
        host = host.split("]", 1)[0].lstrip("[")
    else:
        host = host.split(":", 1)[0]
    return host in {"127.0.0.1", "localhost", "::1"}


_RANGE_RE = re.compile(r"^bytes=(\d*)-(\d*)$")


def create_server(project, *, port=8765, template_arg=None, embed_images=False):
    """Create a localhost-only ThreadingHTTPServer serving <project>/output with auto-rebuild on refresh."""
    project_dir = Path(project).resolve()
    output_dir = (project_dir / "output").resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    class _ViewerHandler(http.server.BaseHTTPRequestHandler):
        def log_message(self, format, *args):  # noqa: A002
            pass

        def _reject_bad_host(self):
            if not _is_local_host(self.headers.get("Host")):
                self.send_error(403, "Forbidden: local requests only")
                return True
            return False

        def do_HEAD(self):  # noqa: N802
            self._handle(head_only=True)

        def do_GET(self):  # noqa: N802
            self._handle(head_only=False)

        def _handle(self, *, head_only):
            if self._reject_bad_host():
                return
            req_path = urllib.parse.unquote(urllib.parse.urlsplit(self.path).path)
            if req_path in {"", "/", "/index.html", "/world-viewer.html"}:
                try:
                    data = viz_data.build_viz_data(project_dir, embed_images=embed_images)
                    html = render_html(data, _load_template(template_arg))
                except (FileNotFoundError, ValueError) as exc:
                    self.send_error(500, str(exc))
                    return
                body = html.encode("utf-8")
                (output_dir / "world-viewer.html").write_bytes(body)
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                if not head_only:
                    self.wfile.write(body)
                return

            rel = req_path.lstrip("/")
            try:
                target = (output_dir / rel).resolve()
                target.relative_to(output_dir)
            except ValueError:
                self.send_error(403, "Forbidden")
                return
            if not target.is_file():
                self.send_error(404, "Not found")
                return

            ctype = (
                viz_data.IMAGE_MIME.get(target.suffix.lower())
                or viz_data.AUDIO_MIME.get(target.suffix.lower())
                or mimetypes.guess_type(target.name)[0]
                or "application/octet-stream"
            )
            raw = target.read_bytes()
            total = len(raw)
            rng = self.headers.get("Range")
            if rng:
                m = _RANGE_RE.match(rng.strip())
                if m:
                    s_str, e_str = m.groups()
                    start = int(s_str) if s_str else 0
                    end = int(e_str) if e_str else total - 1
                    end = min(end, total - 1)
                    if 0 <= start <= end < total:
                        chunk = raw[start : end + 1]
                        self.send_response(206)
                        self.send_header("Content-Type", ctype)
                        self.send_header("Accept-Ranges", "bytes")
                        self.send_header("Content-Range", f"bytes {start}-{end}/{total}")
                        self.send_header("Content-Length", str(len(chunk)))
                        self.end_headers()
                        if not head_only:
                            self.wfile.write(chunk)
                        return

            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Length", str(total))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            if not head_only:
                self.wfile.write(raw)

    return http.server.ThreadingHTTPServer(("127.0.0.1", int(port)), _ViewerHandler)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build or serve the world viewer HTML")
    ap.add_argument("project")
    ap.add_argument("--out", help="output file (default: <project>/output/world-viewer.html)")
    ap.add_argument("--json-only", action="store_true", help="write viz.json instead of the HTML page")
    ap.add_argument("--template", help="HTML template path (default: assets/viewer/index.html)")
    ap.add_argument(
        "--embed-images",
        "--embed-media",
        dest="embed_images",
        action="store_true",
        help="base64-encode discovered entity images and audio as data URIs for portability",
    )
    ap.add_argument("--serve", action="store_true", help="serve output/ on 127.0.0.1 with auto-rebuild on refresh")
    ap.add_argument("--port", type=int, default=8765, help="port for --serve (default: 8765, 0 for ephemeral)")
    args = ap.parse_args(argv)

    project = Path(args.project)
    if not (project / "project.yaml").exists():
        print(f"error: no project.yaml in {project}. Pass the project folder.", file=sys.stderr)
        return 1

    if args.serve:
        server = create_server(project, port=args.port, template_arg=args.template, embed_images=args.embed_images)
        bound_port = server.server_address[1]
        print(
            f"Serving {project.resolve().name} at http://127.0.0.1:{bound_port}/world-viewer.html "
            "(auto-rebuilds on refresh; Ctrl+C to stop)",
            flush=True,
        )
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()
        return 0

    data = viz_data.build_viz_data(project, embed_images=args.embed_images)

    if args.json_only:
        out = Path(args.out) if args.out else project / "output" / "viz.json"
        text = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    else:
        out = Path(args.out) if args.out else project / "output" / "world-viewer.html"
        try:
            template_text = _load_template(args.template)
            text = render_html(data, template_text)
        except (FileNotFoundError, ValueError) as exc:
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
