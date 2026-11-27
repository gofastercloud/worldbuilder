#!/usr/bin/env python3
"""groundhog-agency cross-project knowledge base ("second brain") with BM25 search.

Stores structured Markdown notes with YAML frontmatter in `~/.agency-kb/` (or
`$AGENCY_KB_DIR`) so learnings from post-build retros, proven patterns, good
libraries, and pitfalls are searchable offline across all projects and AI vendors.

Stdlib only (Python 3.9+), zero vector DB or API keys required.

Subcommands:
  add     Write a new learning note (pattern, library, pitfall, or retro)
  search  Rank notes by Okapi BM25 relevance (with title + tag boosts)
  list    List recent notes, optionally filtered by kind or project
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

KINDS = ("pattern", "library", "pitfall", "retro")
TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9._-]*")
SLUG_RE = re.compile(r"[^a-z0-9]+")


def kb_root(override: str | None = None) -> Path:
    raw = override or os.environ.get("AGENCY_KB_DIR")
    return Path(raw).expanduser() if raw else (Path.home() / ".agency-kb")


def tokenize(text: str) -> list[str]:
    return [t for t in TOKEN_RE.findall(text.lower()) if len(t) > 1]


def slugify(text: str) -> str:
    return SLUG_RE.sub("-", text.lower()).strip("-")[:60] or "note"


@dataclass(frozen=True)
class Note:
    path: Path
    kind: str
    title: str
    tags: tuple[str, ...]
    project: str
    created: str
    body: str


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    parts = text.split("---\n", 2)
    if len(parts) < 3:
        return {}, text
    meta: dict[str, str] = {}
    for line in parts[1].splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"').strip("'")
    return meta, parts[2].strip()


def load_notes(root: Path) -> list[Note]:
    if not root.is_dir():
        return []
    notes: list[Note] = []
    for path in sorted(root.rglob("*.md")):
        if path.name.startswith("."):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        meta, body = _parse_frontmatter(text)
        raw_tags = meta.get("tags", "").strip("[]")
        tags = tuple(t.strip().strip('"').strip("'") for t in raw_tags.split(",") if t.strip())
        notes.append(
            Note(
                path=path,
                kind=meta.get("kind") or path.parent.name.rstrip("s") or "pattern",
                title=meta.get("title") or path.stem,
                tags=tags,
                project=meta.get("project", ""),
                created=meta.get("created", ""),
                body=body,
            )
        )
    return notes


def add_note(
    root: Path,
    *,
    kind: str,
    title: str,
    body: str,
    tags: list[str] | None = None,
    project: str = "",
) -> Path:
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {', '.join(KINDS)}, got {kind!r}")
    folder = root / f"{kind}s"
    folder.mkdir(parents=True, exist_ok=True)
    now = datetime.now()
    stamp = now.strftime("%Y-%m-%d")
    clean_tags = [t.strip().lower() for t in (tags or []) if t.strip()]
    filename = f"{stamp}-{slugify(title)}.md"
    dst = folder / filename
    counter = 2
    while dst.exists():
        dst = folder / f"{stamp}-{slugify(title)}-{counter}.md"
        counter += 1
    safe_title = title.replace('"', "'").replace("\n", " ").strip()
    safe_proj = project.replace('"', "'").replace("\n", " ").strip()
    tag_str = ", ".join(clean_tags)
    content = (
        "---\n"
        f'title: "{safe_title}"\n'
        f"kind: {kind}\n"
        f"tags: [{tag_str}]\n"
        f'project: "{safe_proj}"\n'
        f"created: {now.isoformat(timespec='seconds')}\n"
        "---\n\n"
        f"{body.strip()}\n"
    )
    dst.write_text(content, encoding="utf-8")
    return dst


def search_notes(
    notes: list[Note],
    query: str,
    *,
    kind: str | None = None,
    tag: str | None = None,
    top: int = 5,
) -> list[tuple[float, Note]]:
    """Rank notes with Okapi BM25 (with 3x title and 2x tag weighting)."""
    filtered = [
        n
        for n in notes
        if (not kind or n.kind == kind) and (not tag or tag.lower() in {t.lower() for t in n.tags})
    ]
    q_terms = tokenize(query)
    if not filtered or not q_terms:
        return [(0.0, n) for n in filtered[:top]]

    docs: list[list[str]] = []
    for n in filtered:
        # Weight title (3x) and tags (2x) higher than body text.
        toks = tokenize(n.title) * 3 + tokenize(" ".join(n.tags)) * 2 + tokenize(n.body)
        docs.append(toks)

    n_docs = len(docs)
    avgdl = sum(len(d) for d in docs) / max(n_docs, 1)
    df: Counter[str] = Counter()
    for d in docs:
        for term in set(d):
            df[term] += 1

    k1 = 1.5
    b = 0.75
    scored: list[tuple[float, Note]] = []
    for note, doc in zip(filtered, docs):
        tf = Counter(doc)
        dl = len(doc)
        score = 0.0
        for term in q_terms:
            freq = tf.get(term, 0)
            if freq == 0:
                continue
            idf = math.log(1.0 + (n_docs - df[term] + 0.5) / (df[term] + 0.5))
            denom = freq + k1 * (1.0 - b + b * dl / max(avgdl, 1.0))
            score += idf * (freq * (k1 + 1.0)) / denom
        if score > 0:
            scored.append((round(score, 4), note))

    scored.sort(key=lambda pair: (-pair[0], pair[1].created), reverse=False)
    return scored[:top]


def cmd_add(args: argparse.Namespace) -> int:
    body = args.body
    if body == "-":
        body = sys.stdin.read()
    tags = [t.strip() for t in (args.tags or "").split(",") if t.strip()]
    path = add_note(
        kb_root(args.kb_dir),
        kind=args.kind,
        title=args.title,
        body=body,
        tags=tags,
        project=args.project or "",
    )
    print(path)
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    notes = load_notes(kb_root(args.kb_dir))
    hits = search_notes(notes, args.query, kind=args.kind, tag=args.tag, top=args.top)
    if args.as_json:
        payload = [
            {
                "score": score,
                "kind": n.kind,
                "title": n.title,
                "tags": list(n.tags),
                "project": n.project,
                "path": str(n.path),
                "excerpt": n.body[:400],
            }
            for score, n in hits
        ]
        print(json.dumps(payload, indent=2))
        return 0
    if not hits:
        print("No matching knowledge base notes.")
        return 0
    for score, n in hits:
        tag_s = f" [{', '.join(n.tags)}]" if n.tags else ""
        proj_s = f" ({n.project})" if n.project else ""
        print(f"[{n.kind}] {n.title}{proj_s}{tag_s}  (score {score:.2f})")
        first_line = next((ln.strip() for ln in n.body.splitlines() if ln.strip()), "")
        if first_line:
            print(f"  {first_line[:120]}")
        print(f"  {n.path}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    notes = load_notes(kb_root(args.kb_dir))
    filtered = [
        n
        for n in notes
        if (not args.kind or n.kind == args.kind)
        and (not args.project or n.project.lower() == args.project.lower())
    ]
    filtered.sort(key=lambda n: n.created, reverse=True)
    for n in filtered[: args.limit]:
        tag_s = f" [{', '.join(n.tags)}]" if n.tags else ""
        print(f"{n.created[:10]:<10} [{n.kind:<7}] {n.title}{tag_s}  ({n.project or '-'})")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="kb", description="groundhog-agency cross-project knowledge base")
    p.add_argument("--kb-dir", help="KB directory (default: $AGENCY_KB_DIR or ~/.agency-kb)")
    sub = p.add_subparsers(dest="cmd", required=True)

    pa = sub.add_parser("add", help="Add a learning note to the knowledge base")
    pa.add_argument("--kind", choices=list(KINDS), required=True)
    pa.add_argument("--title", required=True)
    pa.add_argument("--tags", default="", help="Comma-separated tags")
    pa.add_argument("--project", default="", help="Origin project name")
    pa.add_argument("--body", required=True, help="Markdown body (or '-' to read stdin)")
    pa.set_defaults(fn=cmd_add)

    ps = sub.add_parser("search", help="Search the knowledge base using BM25")
    ps.add_argument("query")
    ps.add_argument("--kind", choices=list(KINDS))
    ps.add_argument("--tag")
    ps.add_argument("--top", type=int, default=5)
    ps.add_argument("--json", action="store_true", dest="as_json")
    ps.set_defaults(fn=cmd_search)

    pl = sub.add_parser("list", help="List recent notes")
    pl.add_argument("--kind", choices=list(KINDS))
    pl.add_argument("--project")
    pl.add_argument("--limit", type=int, default=20)
    pl.set_defaults(fn=cmd_list)

    args = p.parse_args(argv)
    return int(args.fn(args))


if __name__ == "__main__":
    sys.exit(main())
