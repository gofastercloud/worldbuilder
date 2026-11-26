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
    assert "WB.registerView" in html and "'graph'" in html and "'timeline'" in html and "'gallery'" in html


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
