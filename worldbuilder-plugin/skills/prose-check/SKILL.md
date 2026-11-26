---
name: prose-check
description: Measure prose readability for worldbuilder chapters, entities and stories using Flesch, Flesch-Kincaid, Gunning Fog, dialogue ratio and style flags. Use when the user asks how hard their writing is to read, whether a chapter or story matches its target audience, or which paragraphs or files stand out. Scores are advisory.
---

# Prose check

Run the stdlib-only readability report on a file or folder:

```
python3 "${CLAUDE_SKILL_DIR}/scripts/readability.py" <path> [--json]
```

Pass a single `.md` file, or a folder (searched recursively, files starting with `_` skipped). Frontmatter is stripped. Use `--json` when you need to inspect the numbers programmatically.

## Reading the scores

- **Flesch reading ease** (higher is easier): 60-70 is standard fiction, 50-60 is literary or dense, below 30 is academic.
- **Flesch-Kincaid grade**: years of schooling. Genre and young-adult fiction usually sits around 6-9, adult literary fiction 9-12. Worldbuilding reference text (rules, histories) often runs higher because of proper nouns and clauses.
- **Gunning Fog** and **Coleman-Liau** are cross-checks; if they disagree wildly with FK, the text likely has many long words or unusual punctuation.
- **Dialogue ratio**: share of words inside quotes. Action-heavy scenes are low, dialogue-driven scenes high. Judge it against the scene's intent.
- **Adverbs and fillers** per 1,000 words, **repeated openers** and **longest sentences**: style flags to look at, not errors.

Compare like with like. A codex entry, a chapter and a dialogue scene should not share one target. Ask the user for the intended audience and prose style before calling a score too hard or too easy.

## Outliers

Paragraphs or files more than 1.5 standard deviations from their average are flagged. These are places to look, not problems to fix. Check whether the outlier is deliberate (a dense worldbuilding passage, a quiet emotional beat) before rewriting.

## Caveats

- Syllables are estimated with a vowel-group heuristic, so scores can differ by a few tenths from textstat-based tools.
- Results are advisory. Never change prose only to hit a number.
