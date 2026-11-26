"""Tests for the world-compile script."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parent.parent
SCRIPT = PLUGIN / "skills" / "world-compile" / "scripts" / "compile.py"
EXAMPLE = PLUGIN / "skills" / "worldbuilding" / "assets" / "example-the-lattice"

_spec = importlib.util.spec_from_file_location("world_compile", SCRIPT)
assert _spec is not None and _spec.loader is not None
wc = importlib.util.module_from_spec(_spec)
sys.modules["world_compile"] = wc
_spec.loader.exec_module(wc)


def write_project(root: Path, title: str = "Test Book", author: str = "") -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "project.yaml").write_text(f'title: "{title}"\nauthor: "{author}"\n', encoding="utf-8")
    return root


def write_chapter(path: Path, title: str, number: int, body: str, book: int = 1) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f'---\ntitle: "{title}"\nnumber: {number}\nbook: {book}\n---\n\n{body}\n',
        encoding="utf-8",
    )


def test_chapters_ordered_by_book_then_number(tmp_path: Path) -> None:
    proj = write_project(tmp_path / "p")
    chapters = proj / "story" / "chapters"
    write_chapter(chapters / "c-b.md", "Second", 2, "Body two.")
    write_chapter(chapters / "c-a.md", "First", 1, "Body one.")
    write_chapter(chapters / "c-book2.md", "Book Two Opener", 1, "Body b2.", book=2)

    manuscript, _ = wc.build_markdown(wc.load_project_config(proj), wc.load_chapters(proj))

    first = manuscript.index("## Chapter 1: First")
    second = manuscript.index("## Chapter 2: Second")
    other_book = manuscript.index("## Chapter 1: Book Two Opener")
    assert first < second < other_book


def test_stories_folder_chapters_are_included_and_grouped(tmp_path: Path) -> None:
    proj = write_project(tmp_path / "p")
    write_chapter(proj / "stories" / "beta" / "chapter-01.md", "Beta One", 1, "Beta body.")
    write_chapter(proj / "stories" / "alpha" / "chapter-01.md", "Alpha One", 1, "Alpha body.")
    write_chapter(proj / "stories" / "alpha" / "chapter-02.md", "Alpha Two", 2, "Alpha two body.")

    titles = [c["meta"]["title"] for c in wc.load_chapters(proj)]

    assert titles == ["Alpha One", "Alpha Two", "Beta One"]


def test_frontmatter_is_stripped(tmp_path: Path) -> None:
    proj = write_project(tmp_path / "p")
    write_chapter(proj / "story" / "chapters" / "c1.md", "Opening", 1, "The rain began.")

    manuscript, words = wc.build_markdown(wc.load_project_config(proj), wc.load_chapters(proj))

    assert "number: 1" not in manuscript
    assert "---\ntitle" not in manuscript
    assert "The rain began." in manuscript
    assert words == 3


def test_underscore_files_and_files_without_frontmatter_are_skipped(tmp_path: Path) -> None:
    proj = write_project(tmp_path / "p")
    chapters = proj / "story" / "chapters"
    write_chapter(chapters / "_draft.md", "Hidden", 1, "Should not appear.")
    chapters.mkdir(parents=True, exist_ok=True)
    (chapters / "notes.md").write_text("Just notes, no frontmatter.\n", encoding="utf-8")
    write_chapter(chapters / "c1.md", "Real", 1, "Visible text.")

    manuscript, _ = wc.build_markdown(wc.load_project_config(proj), wc.load_chapters(proj))

    assert "Should not appear" not in manuscript
    assert "Just notes" not in manuscript
    assert "Visible text." in manuscript


def test_html_escapes_script_tags(tmp_path: Path) -> None:
    proj = write_project(tmp_path / "p", title="<b>Bold</b> Title")
    write_chapter(proj / "story" / "chapters" / "c1.md", "Trap", 1, "<script>alert('x')</script> & more")

    manuscript, _ = wc.build_markdown(wc.load_project_config(proj), wc.load_chapters(proj))
    page = wc.markdown_to_html(manuscript, "<b>Bold</b> Title")

    assert "<script>" not in page
    assert "&lt;script&gt;alert(&#x27;x&#x27;)&lt;/script&gt; &amp; more" in page
    assert "<title>&lt;b&gt;Bold&lt;/b&gt; Title</title>" in page
    assert page.startswith("<!DOCTYPE html>")


def test_no_chapters_exits_1(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    proj = write_project(tmp_path / "empty")

    code = wc.main([str(proj)])

    assert code == 1
    assert "no chapters found" in capsys.readouterr().err
    assert not (proj / "output").exists()


def test_cli_md_output_written_to_default_path(tmp_path: Path) -> None:
    proj = write_project(tmp_path / "p", title="Lattice", author="A. Writer")
    write_chapter(proj / "story" / "chapters" / "c1.md", "Start", 1, "# Chapter 1: Start\n\nFirst words here.")

    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(proj), "--format", "md"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    out = (proj / "output" / "manuscript.md").read_text(encoding="utf-8")
    assert out.startswith("# Lattice\n")
    assert "*by A. Writer*" in out
    assert "## Chapter 1: Start" in out
    assert "# Chapter 1: Start" not in out.replace("## Chapter 1: Start", "")
    assert "First words here." in out


def test_cli_html_output_is_single_page(tmp_path: Path) -> None:
    proj = write_project(tmp_path / "p")
    write_chapter(proj / "story" / "chapters" / "c1.md", "Start", 1, "Plain & simple.")
    target = tmp_path / "out" / "book.html"

    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(proj), "--format", "html", "--out", str(target)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    html_text = target.read_text(encoding="utf-8")
    assert html_text.count("<html") == 1
    assert "<style>" in html_text
    assert "Plain &amp; simple." in html_text


def test_example_project_compiles() -> None:
    chapters = wc.load_chapters(EXAMPLE)

    assert chapters, "example project should contain chapters under stories/"
    manuscript, words = wc.build_markdown(wc.load_project_config(EXAMPLE), chapters)
    assert "## Chapter 1: Diagnostic" in manuscript
    assert words > 0
