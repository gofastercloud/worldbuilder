"""Tests for skills/writing/scripts/story_campaign.py."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "writing" / "scripts" / "story_campaign.py"
LATTICE = ROOT / "skills" / "worldbuilding" / "assets" / "example-the-lattice"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_story_anchored_to_event_excludes_future_events_and_includes_ancestry(tmp_path: Path) -> None:
    out = tmp_path / "ai-wars-story.md"
    res = _run(
        "story", str(LATTICE), "--event", "ai-wars", "--words", "4000", "--subgenre", "hard-sf", "--out", str(out)
    )
    assert res.returncode == 0, res.stderr
    text = out.read_text(encoding="utf-8")
    assert "# Short Story Brief — The AI Wars" in text
    assert "MAGIC OFF" in text
    assert "Spoiler Firewall:" in text
    assert "18 future event(s)" in text
    assert "## Causal Ancestry (`why`)" in text
    assert "vaelori-ai-technology-transfer" in text
    assert "~4,000 words" in text
    assert "hard-sf" in text


def test_story_anchored_to_tradition_contrasts_belief_and_origin_events() -> None:
    res = _run("story", str(LATTICE), "--tradition", "the-long-voyage-telling", "--json")
    assert res.returncode == 0, res.stderr
    data = json.loads(res.stdout)
    assert data["anchor"]["kind"] == "tradition"
    assert data["anchor"]["slug"] == "the-long-voyage-telling"
    assert any(a["id"] == "mekvol-homeworld-destruction" for a in data["ancestry"])
    assert "WorldDate(" not in data["anchor"]["date_label"]


def test_story_anchored_to_era_range_and_location(tmp_path: Path) -> None:
    out = tmp_path / "era-story.md"
    res = _run(
        "story",
        str(LATTICE),
        "--era",
        "CE",
        "--start-year",
        "50",
        "--end-year",
        "200",
        "--location",
        "terra-prime",
        "--out",
        str(out),
    )
    assert res.returncode == 0, res.stderr
    text = out.read_text(encoding="utf-8")
    assert "50-200 CE" in text
    assert "Focus Location — Terra Prime" in text
    # Event at CE 250 must be excluded by end-year 200 firewall
    assert "ai-wars" not in text


def test_campaign_dnd5e_magic_off_calibration_and_rumour_table(tmp_path: Path) -> None:
    out = tmp_path / "lattice-campaign.md"
    res = _run(
        "campaign",
        str(LATTICE),
        "--era",
        "CE",
        "--year",
        "250",
        "--level",
        "5-10",
        "--length",
        "short",
        "--location",
        "meridian-station",
        "--tone",
        "paranoid corporate thriller",
        "--out",
        str(out),
    )
    assert res.returncode == 0, res.stderr
    text = out.read_text(encoding="utf-8")
    assert "# D&D 5e Campaign Brief" in text
    assert "Tier 2 — Heroes of the Realm (Levels 5–10)" in text
    assert "CR 3 – CR 10" in text
    assert "5e Low/No-Magic Guidance:" in text
    assert "### Meridian Station" in text
    assert "## Faction Clocks" in text
    assert "## Hub Rumour Table" in text
    assert "3 session(s)" in text


def test_campaign_present_one_shot_json() -> None:
    res = _run("campaign", str(LATTICE), "--present", "--level", "1-4", "--length", "one-shot", "--json")
    assert res.returncode == 0, res.stderr
    data = json.loads(res.stdout)
    assert data["anchor"]["kind"] == "present"
    assert data["future_events_excluded"] == 0
    assert len(data["factions"]) >= 1
    assert len(data["characters"]) >= 1


def test_story_campaign_magic_on_world(tmp_path: Path) -> None:
    # Minimal synthetic magic-on world to verify magic-on 5e rendering
    proj = tmp_path / "magic-world"
    (proj / "world" / "history").mkdir(parents=True)
    (proj / "world" / "events").mkdir(parents=True)
    (proj / "world" / "traditions").mkdir(parents=True)
    (proj / "project.yaml").write_text(
        """title: Glass Spire
present_date: AE 10
world_flags:
  magic:
    present: true
    hardness: hard
    prevalence: rare
    source: starlight prisms
    cost: glass lung
""",
        encoding="utf-8",
    )
    (proj / "world" / "history" / "calendar.yaml").write_text(
        """eras:
  - name: Amber Era
    prefix: AE
    sort_order: 1
    start_year: 1
    end_year: 100
""",
        encoding="utf-8",
    )
    (proj / "world" / "events" / "prism-fall.md").write_text(
        """---
id: prism-fall
name: The Prism Fall
date: AE 5
open_ended: Shards still hum beneath the harbour.
---
A starlight prism shattered over the harbour.
""",
        encoding="utf-8",
    )
    res = _run(
        "campaign", str(proj), "--era", "AE", "--year", "10", "--level", "1-4", "--length", "custom", "--sessions", "5"
    )
    assert res.returncode == 0, res.stderr
    out_file = proj / "output" / "campaigns" / "campaign-ae-10.md"
    assert out_file.is_file()
    text = out_file.read_text(encoding="utf-8")
    assert "MAGIC ON" in text
    assert "5e Low/No-Magic Guidance:" not in text
    assert "5 sessions" in text
    assert "prism-fall" in text


def test_story_campaign_error_handling(tmp_path: Path) -> None:
    # Missing project.yaml
    r1 = _run("story", str(tmp_path), "--present")
    assert r1.returncode == 1
    assert "error:" in r1.stderr

    # Missing anchor
    r2 = _run("story", str(LATTICE))
    assert r2.returncode == 1
    assert "specify one of" in r2.stderr

    # Unknown event
    r3 = _run("story", str(LATTICE), "--event", "nonexistent-event")
    assert r3.returncode == 1
    assert "event not found" in r3.stderr

    # Unknown era
    r4 = _run("campaign", str(LATTICE), "--era", "NOPE")
    assert r4.returncode == 1
    assert "not found in calendar.yaml" in r4.stderr
