"""Tests for assembling the single-file world viewer (assets/viewer + build_viewer.py)."""

from __future__ import annotations

import importlib.util
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parent.parent
SKILL = PLUGIN / "skills" / "world-visualiser"
VIEWER = SKILL / "assets" / "viewer"
EXAMPLE = PLUGIN / "skills" / "worldbuilding" / "assets" / "example-the-lattice"
INTEGRITY = "sha384-5UGTcMIxVUKFeJH0zOS3lqMAZNBG+fCXJbi3UglUq6ABO4MQJu6rxNa+MPP+qtwq"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


bv = _load("build_viewer_for_viz_build", SKILL / "scripts" / "build_viewer.py")
fixtures = _load("test_viz_data_fixtures", PLUGIN / "tests" / "test_viz_data.py")


def _build(project, tmp_path):
    out = tmp_path / "out" / "viewer.html"
    assert bv.main([str(project), "--out", str(out)]) == 0
    return out.read_text(encoding="utf-8")


def _scripts(html):
    """Inline script bodies (the three.js tag has a src and no body)."""
    return [m.group(1) for m in re.finditer(r"<script>\n(.*?)\n</script>", html, re.S)]


def _build_copy(tmp_path):
    """Build the example-free synthetic world with a scratch copy of the viewer sources; returns (rc, out)."""
    out = tmp_path / "o.html"
    tpl = tmp_path / "viewer" / "index.html"
    return bv.main([str(tmp_path / "w"), "--out", str(out), "--template", str(tpl)]), out


def _check_single_file(html):
    assert html.count(bv.MARKER) == 0
    assert html.count("const DATA = ") == 1
    assert "<!--__CSS__-->" not in html and "<!--__JS__-->" not in html
    assert f'integrity="{INTEGRITY}"' in html
    assert html.count("<style>") == 1
    assert len(_scripts(html)) == 1
    # No other network resources: the only external URL is the three.js CDN script.
    srcs = re.findall(r'(?:src|href)="(https?://[^"]+)"', html)
    assert srcs == ["https://cdn.jsdelivr.net/npm/three@0.158.0/build/three.min.js"]


def test_example_builds_to_one_self_contained_page(tmp_path):
    html = _build(EXAMPLE, tmp_path)
    _check_single_file(html)
    assert "The Lattice" in html
    assert (
        "WB.registerView" in html
        and "'graph'" in html
        and "'timeline'" in html
        and "'gallery'" in html
        and "'content'" in html
    )


def test_content_tab_discovers_stories_and_campaigns_and_escapes_html(tmp_path):
    fixtures.write_world(tmp_path)
    stories_dir = tmp_path / "stories"
    stories_dir.mkdir(parents=True)
    (stories_dir / "harbour-tale.md").write_text(
        "---\ntitle: The Harbour Tale\ndate: 10 AE\n---\n# The Harbour Tale\n\n"
        "A tale set in `harbour` with <script>alert(1)</script> safely escaped.\n\n"
        "> Read-aloud box\n\n| Col A | Col B |\n| --- | --- |\n| 1 | 2 |\n",
        encoding="utf-8",
    )
    camp_dir = tmp_path / "output" / "campaigns"
    camp_dir.mkdir(parents=True)
    (camp_dir / "era-campaign.md").write_text(
        "---\ntitle: Era 5e Campaign\nsystem: D&D 5e\nlevel: 1-4\n---\n# Era 5e Campaign\n\n"
        "Starts at `harbour`.\n",
        encoding="utf-8",
    )
    data = bv.viz_data.build_viz_data(tmp_path)
    assert data["counts"]["content"] == 2
    by_kind = {item["kind"]: item for item in data["content"]}
    assert "story" in by_kind and "campaign" in by_kind
    story_html = by_kind["story"]["html"]
    assert "<script>" not in story_html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in story_html
    assert 'data-entity="harbour"' in story_html
    assert "<blockquote>" in story_html
    assert "<table>" in story_html
    html = _build(tmp_path, tmp_path)
    _check_single_file(html)
    assert "The Harbour Tale" in html and "Era 5e Campaign" in html


def test_map_backdrop_discovery_and_embed_images(tmp_path):
    import base64

    fixtures.write_world(tmp_path)
    png_bytes = b"\x89PNG\r\n\x1a\nworldmap"
    img_dir = tmp_path / "output" / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    (img_dir / "world-map.png").write_bytes(png_bytes)

    data_rel = bv.viz_data.build_viz_data(tmp_path, embed_images=False)
    assert data_rel["map"]["backdrop"] == "images/world-map.png"

    data_emb = bv.viz_data.build_viz_data(tmp_path, embed_images=True)
    expected = "data:image/png;base64," + base64.b64encode(png_bytes).decode("ascii")
    assert data_emb["map"]["backdrop"] == expected

    html = _build(tmp_path, tmp_path)
    _check_single_file(html)
    assert "buildProceduralTerrain" in html and "Painted Map" in html


def test_embed_images_flag_produces_portable_single_file(tmp_path):
    import base64

    fixtures.write_world(tmp_path)
    png_bytes = b"\x89PNG\r\n\x1a\nportable"
    img_dir = tmp_path / "output" / "images" / "locations"
    img_dir.mkdir(parents=True)
    (img_dir / "harbour.png").write_bytes(png_bytes)
    out = tmp_path / "out" / "portable.html"
    assert bv.main([str(tmp_path), "--embed-images", "--out", str(out)]) == 0
    html = out.read_text(encoding="utf-8")
    _check_single_file(html)
    expected = "data:image/png;base64," + base64.b64encode(png_bytes).decode("ascii")
    assert expected in html


def test_synthetic_project_and_script_end_in_name(tmp_path):
    fixtures.write_world(tmp_path)
    evil = "Evil </script><script>alert(1)</script> Realm"
    (tmp_path / "world" / "locations" / "realm.md").write_text(fixtures.md({"name": evil, "type": "kingdom"}))
    html = _build(tmp_path, tmp_path)
    _check_single_file(html)
    assert evil not in html
    assert "\\u003c/script\\u003e" in html
    assert html.count("</script>") == 2  # the CDN tag and the one inline script


def test_missing_view_files_do_not_break_the_build(tmp_path):
    shutil.copytree(VIEWER, tmp_path / "viewer")
    for f in (tmp_path / "viewer" / "js" / "views").glob("*.js"):
        f.unlink()
    fixtures.write_world(tmp_path / "w")
    rc, out = _build_copy(tmp_path)
    assert rc == 0
    html = out.read_text(encoding="utf-8")
    assert "<!--__JS__-->" not in html and "const DATA = " in html


def test_views_are_inlined_in_sorted_order_between_core_and_main(tmp_path):
    shutil.copytree(VIEWER, tmp_path / "viewer")
    views = tmp_path / "viewer" / "js" / "views"
    for f in views.glob("*.js"):
        f.unlink()
    (views / "b.js").write_text("/*VIEW_B*/\n")
    (views / "a.js").write_text("/*VIEW_A*/\n")
    fixtures.write_world(tmp_path / "w")
    rc, out = _build_copy(tmp_path)
    assert rc == 0
    html = out.read_text(encoding="utf-8")
    order = [html.index(x) for x in ("const DATA = ", "/*VIEW_A*/", "/*VIEW_B*/", "// main.js")]
    assert order == sorted(order)


def test_script_end_in_a_source_file_is_rejected(tmp_path, capsys):
    shutil.copytree(VIEWER, tmp_path / "viewer")
    (tmp_path / "viewer" / "js" / "views" / "bad.js").write_text("const s = '</script>';\n")
    fixtures.write_world(tmp_path / "w")
    rc, _ = _build_copy(tmp_path)
    assert rc == 1
    assert "</script" in capsys.readouterr().err


def test_data_marker_lives_once_in_core():
    sources = [p for p in VIEWER.rglob("*") if p.is_file() and p.suffix in {".js", ".html", ".css"}]
    holders = [p.name for p in sources if bv.MARKER in p.read_text(encoding="utf-8")]
    assert holders == ["core.js"]


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_assembled_script_parses(tmp_path):
    html = _build(EXAMPLE, tmp_path)
    script = tmp_path / "viewer.js"
    script.write_text(_scripts(html)[0], encoding="utf-8")
    result = subprocess.run(["node", "--check", str(script)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_serve_mode_rebuilds_streams_range_and_blocks_non_local_host(tmp_path):
    import http.client
    import threading

    fixtures.write_world(tmp_path)
    audio = tmp_path / "output" / "audio" / "theme.mp3"
    audio.parent.mkdir(parents=True, exist_ok=True)
    audio.write_bytes(b"0123456789ABCDEF")

    server = bv.create_server(tmp_path, port=0)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        # 1. GET /world-viewer.html builds and serves HTML
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        conn.request("GET", "/world-viewer.html")
        resp = conn.getresponse()
        body = resp.read().decode("utf-8")
        assert resp.status == 200
        assert "Test World" in body and "const DATA = " in body
        conn.close()

        # 2. HTTP Range request on audio returns 206 Partial Content
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        conn.request("GET", "/audio/theme.mp3", headers={"Range": "bytes=4-9"})
        resp = conn.getresponse()
        chunk = resp.read()
        assert resp.status == 206
        assert resp.getheader("Content-Type") == "audio/mpeg"
        assert resp.getheader("Content-Range") == "bytes 4-9/16"
        assert chunk == b"456789"
        conn.close()

        # 3. Non-localhost Host header rejected with 403
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        conn.request("GET", "/world-viewer.html", headers={"Host": "evil.example.com"})
        resp = conn.getresponse()
        resp.read()
        assert resp.status == 403
        conn.close()

        # 4. Path traversal outside output/ rejected
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        conn.request("GET", "/../project.yaml")
        resp = conn.getresponse()
        resp.read()
        assert resp.status in (403, 404)
        conn.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
