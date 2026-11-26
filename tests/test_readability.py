"""Tests for the prose-check readability script (stdlib only)."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parent.parent
SCRIPT = PLUGIN / "skills" / "prose-check" / "scripts" / "readability.py"

_spec = importlib.util.spec_from_file_location("prose_readability", SCRIPT)
assert _spec is not None and _spec.loader is not None
rd = importlib.util.module_from_spec(_spec)
sys.modules["prose_readability"] = rd
_spec.loader.exec_module(rd)

TWO_SENTENCES = "The cat sat on the mat. The dog ran to the big red barn."
LONG_PROSE = " ".join(["The quick fox jumps over the lazy dog today."] * 6)


@pytest.mark.parametrize(
    ("word", "expected"),
    [
        ("cat", 1),
        ("table", 2),
        ("make", 1),
        ("beautiful", 3),
        ("education", 4),
        ("walked", 1),
        ("wanted", 2),
        ("the", 1),
        ("tree", 1),
        ("played", 1),
        ("needed", 2),
    ],
)
def test_syllable_counts(word: str, expected: int) -> None:
    assert rd.count_syllables(word) == expected


def test_flesch_and_fk_on_fixed_sentences() -> None:
    # 14 words, 2 sentences, 14 one-syllable words.
    # ASL = 7, ASW = 1: ease = 206.835 - 7.105 - 84.6 = 115.13; FK = 2.73 + 11.8 - 15.59 = -1.06
    m = rd.compute_metrics(TWO_SENTENCES)
    assert m is not None
    assert m["word_count"] == 14
    assert m["sentence_count"] == 2
    assert m["reading_ease"] == pytest.approx(115.13, abs=0.01)
    assert m["fk_grade"] == pytest.approx(-1.06, abs=0.01)


def test_short_text_returns_none() -> None:
    assert rd.compute_metrics("Too short.") is None


def test_frontmatter_is_stripped(tmp_path: Path) -> None:
    f = tmp_path / "ch.md"
    f.write_text("---\ntitle: Secret Title\nnumber: 1\n---\n" + TWO_SENTENCES + "\n", encoding="utf-8")
    prose = rd.prose_from_file(f)
    assert "Secret" not in prose
    assert "title" not in prose
    assert prose.startswith("The cat sat")


def test_frontmatter_stripping_leaves_plain_text_alone() -> None:
    text = "A line with --- inside.\nNo fence here."
    assert rd.strip_frontmatter(text) == text


def test_directory_aggregate_and_skips(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text("---\ntitle: A\n---\n" + LONG_PROSE, encoding="utf-8")
    (tmp_path / "b.md").write_text(TWO_SENTENCES, encoding="utf-8")
    (tmp_path / "_index.md").write_text(LONG_PROSE, encoding="utf-8")
    (tmp_path / "tiny.md").write_text("Hi.", encoding="utf-8")
    report = rd.analyse(tmp_path)
    agg = report["aggregate"]
    assert "_index.md" not in " ".join(f["path"] for f in report["files"])
    assert agg["files_analysed"] == 2
    assert [Path(p).name for p in agg["files_skipped"]] == ["tiny.md"]
    assert agg["metrics"] is not None
    assert agg["metrics"]["word_count"] == 14 + 6 * 9


def test_json_schema(tmp_path: Path) -> None:
    (tmp_path / "a.md").write_text(LONG_PROSE, encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), str(tmp_path), "--json"],
        capture_output=True, text=True, check=True,
    )
    data = json.loads(proc.stdout)
    assert set(data) == {"tool", "advisory", "target", "files", "aggregate"}
    assert data["advisory"] is True
    assert set(data["aggregate"]) == {"files_analysed", "files_skipped", "metrics", "file_outliers"}
    metrics = data["files"][0]["metrics"]
    for key in (
        "word_count", "sentence_count", "paragraph_count", "avg_sentence_len", "reading_ease",
        "reading_ease_label", "fk_grade", "gunning_fog", "coleman_liau", "dialogue_ratio",
        "repeated_openers", "longest_sentences",
    ):
        assert key in metrics
    assert set(data["files"][0]) == {"path", "metrics", "paragraph_outliers"}


def test_missing_path_exits_nonzero(tmp_path: Path) -> None:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), str(tmp_path / "nope")], capture_output=True, text=True
    )
    assert proc.returncode == 2
