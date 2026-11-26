#!/usr/bin/env python3
"""Readability report for worldbuilder prose. Stdlib only.

Port of the `worldbuilder.py readability` command (textstat-based). Syllables are
estimated with a vowel-group heuristic instead of textstat's dictionary, so scores
differ slightly from the original. Results are advisory.

Usage: readability.py <file-or-dir> [--json]
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

MIN_WORDS = 10
WORDS_PER_PAGE = 250
OUTLIER_Z = 1.5

FRONTMATTER = re.compile(r"\A﻿?---[ \t]*\r?\n.*?\r?\n---[ \t]*(?:\r?\n|\Z)", re.DOTALL)
VOWEL_GROUP = re.compile(r"[aeiouy]+")
SENTENCE_END = re.compile(r"(?<=[.!?])[\"'”’)\]]*\s+|\n+")
DIALOGUE = re.compile(r'"[^"]*"|“[^”]*”')

# Style flags (not in the original command; advisory only).
ADVERB_EXCLUDE = {
    "family",
    "only",
    "early",
    "ugly",
    "holy",
    "lily",
    "jelly",
    "belly",
    "rally",
    "reply",
    "supply",
    "apply",
    "fly",
    "italy",
    "july",
    "daily",
    "silly",
    "likely",
}
FILLERS = {
    "just",
    "really",
    "very",
    "quite",
    "actually",
    "basically",
    "literally",
    "rather",
    "somewhat",
    "perhaps",
    "almost",
}


# ── Text handling ────────────────────────────────────────────────────────────


def strip_frontmatter(text: str) -> str:
    """Remove a leading ---fenced frontmatter block. No YAML parsing needed."""
    return FRONTMATTER.sub("", text, count=1)


def strip_markdown(text: str) -> str:
    """Reduce markdown to plain prose (ported from the original _strip_markdown)."""
    text = re.sub(r"^#{1,6}\s+.*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"---+", "", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"__(.+?)__", r"\1", text)
    text = re.sub(r"_(.+?)_", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"`[^`]+`", "", text)
    text = re.sub(r"^>\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^[-*+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\d+\.\s+", "", text, flags=re.MULTILINE)
    return text.strip()


def split_paragraphs(text: str) -> List[str]:
    """Split on blank lines, dropping empty, heading and rule-only blocks."""
    paragraphs = []
    for p in re.split(r"\n\s*\n", text):
        p = p.strip()
        if not p or re.match(r"^#{1,6}\s+", p) or p == "---":
            continue
        paragraphs.append(p)
    return paragraphs


def split_pages(text: str, words_per_page: int = WORDS_PER_PAGE) -> List[str]:
    words = text.split()
    pages = [" ".join(words[i : i + words_per_page]) for i in range(0, len(words), words_per_page)]
    return [p for p in pages if p.strip()]


def split_sentences(text: str) -> List[str]:
    return [s.strip() for s in SENTENCE_END.split(text) if s and s.strip()]


# ── Metrics ──────────────────────────────────────────────────────────────────


def count_syllables(word: str) -> int:
    """Estimate syllables in one word: vowel groups, minus silent e and -ed endings."""
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        return 0
    if len(w) <= 3:
        return 1
    n = len(VOWEL_GROUP.findall(w))
    if w.endswith("e") and not w.endswith("le") and n > 1:
        n -= 1
    if w.endswith("ed") and not w.endswith(("ted", "ded")) and n > 1:
        n -= 1
    return max(n, 1)


def reading_ease_label(score: float) -> str:
    if score >= 90:
        return "Very easy (5th grade)"
    if score >= 80:
        return "Easy (6th grade)"
    if score >= 70:
        return "Fairly easy (7th grade)"
    if score >= 60:
        return "Standard (8th-9th grade)"
    if score >= 50:
        return "Fairly difficult (10th-12th grade)"
    if score >= 30:
        return "Difficult (college)"
    return "Very difficult (graduate/professional)"


def target_audience(grade: float) -> str:
    if grade <= 6:
        return "Middle grade / children"
    if grade <= 8:
        return "Young adult / general"
    if grade <= 10:
        return "Adult general / genre fiction"
    if grade <= 13:
        return "Adult literary / advanced"
    return "Academic / professional"


def compute_metrics(text: str) -> Optional[Dict[str, Any]]:
    """Readability metrics for plain prose. None if the text is too short."""
    words = text.split()
    if len(words) < MIN_WORDS:
        return None
    sentences = split_sentences(text)
    if not sentences:
        return None

    n_words = len(words)
    n_sents = len(sentences)
    syllables = sum(count_syllables(w) for w in words)
    letters = sum(len(re.sub(r"[^A-Za-z]", "", w)) for w in words)
    complex_words = sum(1 for w in words if count_syllables(w) >= 3)

    asl = n_words / n_sents
    asw = syllables / n_words
    reading_ease = 206.835 - 1.015 * asl - 84.6 * asw
    fk_grade = 0.39 * asl + 11.8 * asw - 15.59
    gunning_fog = 0.4 * (asl + 100.0 * complex_words / n_words)
    coleman_liau = 0.0588 * (letters / n_words * 100) - 0.296 * (n_sents / n_words * 100) - 15.8

    # Style flags (advisory, not in the original command)
    dialogue_words = sum(len(m.split()) for m in DIALOGUE.findall(text))
    lowered = [re.sub(r"[^a-z']", "", w.lower()) for w in words]
    adverbs = sum(1 for w in lowered if len(w) > 4 and w.endswith("ly") and w not in ADVERB_EXCLUDE)
    fillers = sum(1 for w in lowered if w in FILLERS)

    openers = Counter()
    for s in sentences:
        parts = s.split()
        if parts:
            openers[re.sub(r"[^a-z]", "", parts[0].lower())] += 1
    repeated = [
        {"word": w, "count": c, "share": round(c / n_sents, 3)}
        for w, c in openers.most_common()
        if w and c >= 3 and c / n_sents >= 0.10
    ][:5]

    longest = sorted(sentences, key=lambda s: len(s.split()), reverse=True)[:3]

    return {
        "word_count": n_words,
        "sentence_count": n_sents,
        "paragraph_count": len(split_paragraphs(text)),
        "avg_sentence_len": round(asl, 2),
        "avg_word_len": round(letters / n_words, 2),
        "avg_syllables": round(asw, 2),
        "reading_ease": round(reading_ease, 2),
        "reading_ease_label": reading_ease_label(reading_ease),
        "fk_grade": round(fk_grade, 2),
        "gunning_fog": round(gunning_fog, 2),
        "coleman_liau": round(coleman_liau, 2),
        "target_audience": target_audience(fk_grade),
        "reading_time_min": round(n_words / 250, 1),
        "dialogue_ratio": round(dialogue_words / n_words, 3),
        "adverb_count": adverbs,
        "adverbs_per_1000": round(adverbs / n_words * 1000, 1),
        "filler_count": fillers,
        "filler_per_1000": round(fillers / n_words * 1000, 1),
        "repeated_openers": repeated,
        "longest_sentences": [
            {"words": len(s.split()), "text": s if len(s) <= 120 else s[:117] + "..."} for s in longest
        ],
    }


def find_outliers(values: List[float], threshold: float = OUTLIER_Z) -> List[Tuple[int, float, float, float, str]]:
    """Indices whose value sits more than `threshold` standard deviations from the mean."""
    if len(values) < 3:
        return []
    mu = statistics.mean(values)
    sd = statistics.stdev(values)
    if sd == 0:
        return []
    out = []
    for i, v in enumerate(values):
        z = (v - mu) / sd
        if z > threshold:
            out.append((i, v, mu, sd, "harder"))
        elif z < -threshold:
            out.append((i, v, mu, sd, "easier"))
    return out


# ── File handling ────────────────────────────────────────────────────────────


def prose_from_file(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    return strip_markdown(strip_frontmatter(text))


def collect_files(target: Path) -> List[Path]:
    if target.is_file():
        return [target]
    return sorted(p for p in target.rglob("*.md") if not p.name.startswith("_"))


def analyse_file(path: Path) -> Dict[str, Any]:
    prose = prose_from_file(path)
    metrics = compute_metrics(prose)
    para_outliers: List[Dict[str, Any]] = []
    if metrics:
        pieces = []
        for idx, p in enumerate(split_paragraphs(prose), start=1):
            pm = compute_metrics(strip_markdown(p))
            pieces.append((idx, pm["fk_grade"] if pm else None))
        valid = [(i, g) for i, g in pieces if g is not None]
        if len(valid) >= 3:
            for oi, val, mu, sd, label in find_outliers([g for _, g in valid]):
                para_outliers.append(
                    {
                        "paragraph": valid[oi][0],
                        "fk_grade": round(val, 2),
                        "direction": label,
                        "mean": round(mu, 2),
                        "sd": round(sd, 2),
                    }
                )
    return {"path": str(path), "prose": prose, "metrics": metrics, "paragraph_outliers": para_outliers}


def analyse(target: Path) -> Dict[str, Any]:
    results = [analyse_file(p) for p in collect_files(target)]
    analysed = [r for r in results if r["metrics"]]
    skipped = [r["path"] for r in results if not r["metrics"]]

    files_out = [
        {"path": r["path"], "metrics": r["metrics"], "paragraph_outliers": r["paragraph_outliers"]} for r in results
    ]

    aggregate_metrics = None
    file_outliers: List[Dict[str, Any]] = []
    if analysed:
        combined = "\n\n".join(r["prose"] for r in analysed)
        aggregate_metrics = compute_metrics(combined)
    if len(analysed) >= 3:
        grades = [r["metrics"]["fk_grade"] for r in analysed]
        for oi, val, mu, sd, label in find_outliers(grades):
            file_outliers.append(
                {
                    "path": analysed[oi]["path"],
                    "fk_grade": round(val, 2),
                    "direction": label,
                    "mean": round(mu, 2),
                    "sd": round(sd, 2),
                }
            )

    return {
        "tool": "prose-check/readability",
        "advisory": True,
        "target": str(target),
        "files": files_out,
        "aggregate": {
            "files_analysed": len(analysed),
            "files_skipped": skipped,
            "metrics": aggregate_metrics,
            "file_outliers": file_outliers,
        },
    }


# ── Output ───────────────────────────────────────────────────────────────────


def print_metrics(m: Dict[str, Any], indent: str = "  ") -> None:
    print(
        f"{indent}Words: {m['word_count']:,}  Sentences: {m['sentence_count']}  "
        f"Paragraphs: {m['paragraph_count']}  (~{m['reading_time_min']} min read)"
    )
    print(f"{indent}Flesch-Kincaid Grade:  {m['fk_grade']:.1f}")
    print(f"{indent}Flesch Reading Ease:   {m['reading_ease']:.1f}  ({m['reading_ease_label']})")
    print(f"{indent}Gunning Fog:           {m['gunning_fog']:.1f}")
    print(f"{indent}Coleman-Liau:          {m['coleman_liau']:.1f}")
    print(f"{indent}Avg sentence length:   {m['avg_sentence_len']:.1f} words")
    print(f"{indent}Avg word length:       {m['avg_word_len']:.1f} chars")
    print(f"{indent}Dialogue ratio:        {m['dialogue_ratio'] * 100:.1f}% of words")
    print(f"{indent}Adverbs / filler:      {m['adverbs_per_1000']:.1f} / {m['filler_per_1000']:.1f} per 1,000 words")
    if m["repeated_openers"]:
        opens = ", ".join(f"'{o['word']}' ({o['count']})" for o in m["repeated_openers"])
        print(f"{indent}Repeated openers:      {opens}")
    for s in m["longest_sentences"]:
        print(f"{indent}Long sentence ({s['words']} words): {s['text']}")


def print_report(report: Dict[str, Any]) -> None:
    print(f"\nReadability (advisory) — {report['target']}\n")
    for f in report["files"]:
        print(f"{f['path']}")
        if not f["metrics"]:
            print("  too short to analyse\n")
            continue
        print_metrics(f["metrics"])
        for o in f["paragraph_outliers"]:
            print(
                f"  ⚠ Paragraph {o['paragraph']} (grade {o['fk_grade']:.1f}): "
                f"{o['direction']} than file average ({o['mean']:.1f} ± {o['sd']:.1f})"
            )
        print()

    agg = report["aggregate"]
    print(f"═══ Aggregate ({agg['files_analysed']} analysed, {len(agg['files_skipped'])} skipped)")
    if agg["metrics"]:
        print_metrics(agg["metrics"])
        print(f"  Target audience:       {agg['metrics']['target_audience']}")
    for o in agg["file_outliers"]:
        print(
            f"  ⚠ {o['path']} (grade {o['fk_grade']:.1f}): {o['direction']} than average "
            f"({o['mean']:.1f} ± {o['sd']:.1f})"
        )
    print()


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Readability report for worldbuilder prose (advisory).")
    parser.add_argument("target", help="A markdown file or a directory (searched recursively)")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    args = parser.parse_args(argv)

    target = Path(args.target).expanduser()
    if not target.exists():
        print(f"Error: {target} does not exist", file=sys.stderr)
        return 2
    report = analyse(target)
    if not report["files"]:
        print(f"Error: no .md files found under {target}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_report(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
