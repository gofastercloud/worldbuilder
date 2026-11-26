---
name: world-compile
description: Compile a WorldBuilder project's chapters into one manuscript, as Markdown or a single self-contained HTML file. Use when the user asks for a manuscript, a full draft, an export of their book or stories, or a readable copy of the chapters. Chapters come from story/chapters or stories folders, in book and chapter order, with frontmatter removed.
---

# World compile

Join the chapters into one manuscript. Run the script, then tell the user where the file is and how many chapters and words it holds.

## Run

Run [scripts/compile.py](./scripts/compile.py) (resolved relative to this skill's directory):

```
python3 <this-skill-dir>/scripts/compile.py <project> --format md
```

Use `--format html` for a single HTML page, or `--out <file>` to choose the output path. The default output is `<project>/output/manuscript.md` or `.html`. The script needs only Python 3.9+; PyYAML is bundled.

## If it fails

- Exit 1 with "no chapters found": the project has no chapter files with frontmatter. Check that chapters sit in `story/chapters/` or in `stories/<name>/`, and that files starting with `_` are not the only ones.
- A warning about bad frontmatter: that file is skipped. Fix its YAML and run again.
- If `python3` is missing, say so and do not compile by hand.

## Notes

- The title page comes from `project.yaml` (title, subtitle, author).
- Chapter headings are generated from `number` or `chapter_number` and `title` or `name`. A leading heading in the chapter body is dropped to avoid a duplicate.
