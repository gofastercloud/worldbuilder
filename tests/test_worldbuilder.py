"""Tests for scripts/worldbuilder.py — core data model and utilities."""

from worldbuilder import (
    WorldDate,
    build_name_index,
    get_event_date,
    parse_frontmatter,
    resolve_ref,
    slugify,
)

# ── slugify ──────────────────────────────────────────────────────────────────

class TestSlugify:
    def test_basic(self):
        assert slugify("Rowan Thornfield") == "rowan-thornfield"

    def test_special_chars(self):
        assert slugify("Elda's Remedy Book") == "elda-s-remedy-book"

    def test_already_slug(self):
        assert slugify("already-a-slug") == "already-a-slug"

    def test_uppercase(self):
        assert slugify("THE BLACK TOWER") == "the-black-tower"

    def test_leading_trailing_junk(self):
        assert slugify("---hello---") == "hello"

    def test_multiple_spaces(self):
        assert slugify("too   many   spaces") == "too-many-spaces"

    def test_empty(self):
        assert slugify("") == ""

    def test_numbers(self):
        assert slugify("Chapter 3: The End") == "chapter-3-the-end"


# ── WorldDate ────────────────────────────────────────────────────────────────

class TestWorldDate:
    def test_from_dict(self):
        d = WorldDate({"year": 312, "era_prefix": "QY"})
        assert d.valid
        assert d.year == 312
        assert d.era_prefix == "QY"

    def test_from_int(self):
        d = WorldDate(500)
        assert d.valid
        assert d.year == 500
        assert d.era_prefix == ""

    def test_from_none(self):
        d = WorldDate(None)
        assert not d.valid

    def test_from_empty_dict(self):
        d = WorldDate({})
        assert not d.valid

    def test_from_empty_string(self):
        d = WorldDate("")
        assert not d.valid

    def test_sort_key(self):
        d = WorldDate({"year": 100, "month": 3, "day": 15, "era_prefix": "AC"})
        assert d.sort_key() == (0, 100, 3, 15)  # era_sort=0 without calendar_config

    def test_sort_key_with_calendar(self, calendar_config):
        d = WorldDate({"year": 100, "era_prefix": "QY"}, calendar_config)
        assert d.sort_key() == (2, 100, 0, 0)

    def test_comparison(self):
        a = WorldDate({"year": 100, "era_prefix": "AC"})
        b = WorldDate({"year": 200, "era_prefix": "AC"})
        assert a < b
        assert b > a
        assert a != b

    def test_comparison_cross_era(self, calendar_config):
        a = WorldDate({"year": 600, "era_prefix": "AC"}, calendar_config)
        b = WorldDate({"year": 1, "era_prefix": "QY"}, calendar_config)
        assert a < b  # AC has sort_order 1, QY has 2

    def test_invalid_comparison(self):
        a = WorldDate(None)
        b = WorldDate({"year": 100})
        assert not (a < b)
        assert not (a > b)
        assert a != b

    def test_equality(self):
        a = WorldDate({"year": 312, "era_prefix": "QY"})
        b = WorldDate({"year": 312, "era_prefix": "QY"})
        assert a == b

    def test_repr_valid(self):
        d = WorldDate({"year": 312, "era_prefix": "QY"})
        assert "312" in repr(d)
        assert "QY" in repr(d)

    def test_repr_invalid(self):
        d = WorldDate(None)
        assert "unknown" in repr(d)

    def test_display_auto_generated(self):
        d = WorldDate({"year": 100, "month": 6, "day": 15, "era_prefix": "AC"})
        assert d.display == "AC 100 m6 d15"

    def test_display_custom(self):
        d = WorldDate({"year": 100, "display": "The Dawn of Time"})
        assert d.display == "The Dawn of Time"


# ── get_event_date ───────────────────────────────────────────────────────────

class TestGetEventDate:
    def test_instant_event(self):
        meta = {"date": {"year": 312, "era_prefix": "QY"}}
        start, end = get_event_date(meta)
        assert start.valid
        assert start == end
        assert start.year == 312

    def test_duration_event(self):
        meta = {
            "start_date": {"year": 100, "era_prefix": "AC"},
            "end_date": {"year": 200, "era_prefix": "AC"},
        }
        start, end = get_event_date(meta)
        assert start.year == 100
        assert end.year == 200

    def test_no_date(self):
        start, end = get_event_date({})
        assert not start.valid
        assert not end.valid

    def test_date_takes_precedence(self):
        meta = {
            "date": {"year": 50},
            "start_date": {"year": 100},
        }
        start, end = get_event_date(meta)
        assert start.year == 50


# ── build_name_index / resolve_ref ───────────────────────────────────────────

class TestNameIndex:
    def test_index_by_slug(self, sample_entities):
        idx = build_name_index(sample_entities)
        assert "rowan-thornfield" in idx
        assert idx["rowan-thornfield"][0] == "character"

    def test_index_by_lowercase_name(self, sample_entities):
        idx = build_name_index(sample_entities)
        assert "rowan thornfield" in idx

    def test_index_by_slugified_name(self, sample_entities):
        idx = build_name_index(sample_entities)
        assert "aldfield-village-council" in idx

    def test_resolve_exact_slug(self, sample_entities):
        idx = build_name_index(sample_entities)
        result = resolve_ref("rowan-thornfield", idx)
        assert result is not None
        assert result[2] == "rowan-thornfield"

    def test_resolve_by_name(self, sample_entities):
        idx = build_name_index(sample_entities)
        result = resolve_ref("Elda Greenhand", idx)
        assert result is not None
        assert result[2] == "elda-greenhand"

    def test_resolve_none(self, sample_entities):
        idx = build_name_index(sample_entities)
        assert resolve_ref(None, idx) is None

    def test_resolve_missing(self, sample_entities):
        idx = build_name_index(sample_entities)
        assert resolve_ref("nonexistent-entity", idx) is None


# ── parse_frontmatter ────────────────────────────────────────────────────────

class TestParseFrontmatter:
    def test_valid_frontmatter(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("---\nname: Test\nrole: protagonist\n---\n\n## Notes\nHello.\n")
        meta, body = parse_frontmatter(f)
        assert meta is not None
        assert meta["name"] == "Test"
        assert meta["role"] == "protagonist"
        assert "Hello" in body

    def test_no_frontmatter(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("# Just a heading\n\nSome text.\n")
        meta, body = parse_frontmatter(f)
        assert meta is None
        assert "Just a heading" in body

    def test_empty_frontmatter(self, tmp_path):
        f = tmp_path / "test.md"
        f.write_text("---\n---\n\nBody text.\n")
        meta, body = parse_frontmatter(f)
        assert meta is None  # yaml.safe_load of empty string returns None
        assert "Body" in body
