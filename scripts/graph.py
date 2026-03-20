"""
WorldGraph — graph-based integrity layer for WorldBuilder.

Builds a directed graph from WorldBuilder entities, with typed edges
representing cross-references. Provides validation (dangling refs,
bidirectional symmetry, business rules) and query methods (neighbors,
shortest path, isolated nodes, etc.).

Usage:
    from graph import WorldGraph
    graph = WorldGraph.from_entities(entities, name_index, slugify_fn=slugify)
    issues = graph.validate()
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

import yaml


# ─── Data classes ─────────────────────────────────────────────────────────────


@dataclass
class GraphNode:
    slug: str
    entity_type: str  # "character", "location", etc.
    name: str
    meta: dict  # raw YAML frontmatter
    file_path: Path


@dataclass
class GraphEdge:
    source: str  # slug
    target: str  # slug
    edge_type: str
    edge_subtype: str = ""
    metadata: dict = field(default_factory=dict)
    bidirectional: bool = False  # whether a reverse edge is expected


@dataclass
class ValidationIssue:
    severity: str  # "error" or "warning"
    category: str  # "dangling_ref", "asymmetric_edge", "business_rule", "data_completeness"
    message: str
    source_slug: str = ""
    target_slug: str = ""
    edge_type: str = ""


# ─── Compatibility table for bidirectional symmetry checks ────────────────────

COMPATIBLE_REVERSE: dict[tuple[str, str], tuple[str, str]] = {
    ("family_link", "parent"): ("family_link", "child"),
    ("family_link", "child"): ("family_link", "parent"),
    ("family_link", "spouse"): ("family_link", "spouse"),
    ("family_link", "sibling"): ("family_link", "sibling"),
    ("causality", "caused_by"): ("causality", "leads_to"),
    ("causality", "leads_to"): ("causality", "caused_by"),
    ("language_family", "parent"): ("language_family", "child"),
    ("language_family", "child"): ("language_family", "parent"),
    # Cross-type pairs: character.location ↔ location.notable_characters
    ("location_ref", ""): ("notable_character", ""),
    ("notable_character", ""): ("location_ref", ""),
}


# ─── YAML frontmatter rewriter ────────────────────────────────────────────────


def _parse_entity_file(file_path: Path) -> tuple[dict, str]:
    """Read an entity file and return (frontmatter_dict, markdown_body)."""
    text = file_path.read_text(encoding="utf-8")
    # Split on '---' delimiters — first element is empty (before opening ---)
    parts = text.split("---", 2)
    if len(parts) < 3:
        # Malformed — return empty meta and full text as body
        return {}, text
    meta = yaml.safe_load(parts[1]) or {}
    body = parts[2].lstrip("\n")
    return meta, body


def rewrite_entity_frontmatter(file_path: Path, meta: dict, body: str) -> None:
    """Rewrite an entity file with updated frontmatter, preserving body."""
    yaml_str = yaml.dump(meta, default_flow_style=False, allow_unicode=True, sort_keys=False)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("---\n")
        f.write(yaml_str)
        f.write("---\n\n")
        f.write(body)


# ─── WorldGraph ───────────────────────────────────────────────────────────────


class WorldGraph:
    """Directed multigraph of WorldBuilder entities and their cross-references."""

    def __init__(self) -> None:
        self.nodes: dict[str, GraphNode] = {}
        self.edges: dict[str, list[GraphEdge]] = defaultdict(list)  # source → [edges]
        self.reverse_edges: dict[str, list[GraphEdge]] = defaultdict(list)  # target → [edges]
        self.entity_type_index: dict[str, list[str]] = defaultdict(list)  # type → [slugs]

    # ── Node / edge primitives ────────────────────────────────────────────

    def _add_node(self, slug: str, entity_type: str, name: str,
                  meta: dict, file_path: Path) -> None:
        node = GraphNode(slug=slug, entity_type=entity_type, name=name,
                         meta=meta, file_path=file_path)
        self.nodes[slug] = node
        self.entity_type_index[entity_type].append(slug)

    def _add_edge(self, source: str, target: str, edge_type: str,
                  edge_subtype: str = "", metadata: dict | None = None,
                  bidirectional: bool = False) -> None:
        if not target:
            return
        edge = GraphEdge(
            source=source, target=target, edge_type=edge_type,
            edge_subtype=edge_subtype,
            metadata=metadata or {},
            bidirectional=bidirectional,
        )
        self.edges[source].append(edge)
        self.reverse_edges[target].append(edge)

    # ── Factory ───────────────────────────────────────────────────────────

    _EXTRACTOR_MAP: dict[str, str] = {
        "character": "_extract_character_edges",
        "location": "_extract_location_edges",
        "faction": "_extract_faction_edges",
        "event": "_extract_event_edges",
        "species": "_extract_species_edges",
        "race": "_extract_race_edges",
        "language": "_extract_language_edges",
        "item": "_extract_item_edges",
        "lineage": "_extract_lineage_edges",
        "arc": "_extract_arc_edges",
        "magic-system": "_extract_magic_system_edges",
    }

    @classmethod
    def from_entities(cls, entities: dict, name_index: dict,
                      slugify_fn: Callable[[str], str] | None = None) -> "WorldGraph":
        """Build a WorldGraph from collect_entities() / build_name_index() output.

        *slugify_fn* normalises reference strings to slugs.  If None, a
        simple lowercase-hyphenate fallback is used (prefer passing the real
        ``slugify`` from worldbuilder.py).
        """
        import re

        if slugify_fn is None:
            def slugify_fn(name: str) -> str:
                return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

        graph = cls()
        graph._slugify = slugify_fn

        # Pass 1: create nodes
        for entity_type, ents in entities.items():
            if entity_type == "chapter":
                continue  # chapters are not graph entities
            for slug, data in ents.items():
                meta = data["meta"]
                name = meta.get("name", meta.get("title", slug))
                graph._add_node(slug, entity_type, name, meta, data["file"])

        # Pass 2: extract edges
        for entity_type, ents in entities.items():
            extractor_name = cls._EXTRACTOR_MAP.get(entity_type)
            if not extractor_name:
                continue
            extractor = getattr(graph, extractor_name)
            for slug, data in ents.items():
                extractor(slug, data["meta"])

        return graph

    # ── Helpers ────────────────────────────────────────────────────────────

    def _slug(self, ref: Any) -> str:
        """Normalise a reference to a slug string.  Returns '' for falsy input."""
        if not ref:
            return ""
        if isinstance(ref, dict):
            # common patterns: {entity: "slug"}, {target: "slug"}, {faction: "slug"}
            for key in ("entity", "target", "slug", "faction", "species", "race",
                        "language", "location"):
                if key in ref:
                    return self._slugify(str(ref[key])) if ref[key] else ""
            return ""
        return self._slugify(str(ref))

    # ── Edge extractors ───────────────────────────────────────────────────

    def _extract_character_edges(self, slug: str, meta: dict) -> None:
        # relationships
        for rel in meta.get("relationships", []) or []:
            if isinstance(rel, dict):
                target = self._slug(rel.get("target", ""))
                subtype = rel.get("type", "")
                if target:
                    self._add_edge(slug, target, "relationship",
                                   edge_subtype=subtype, bidirectional=True)
            elif isinstance(rel, str) and rel:
                self._add_edge(slug, self._slug(rel), "relationship",
                               bidirectional=True)

        # location
        loc = self._slug(meta.get("location", ""))
        if loc:
            self._add_edge(slug, loc, "location_ref", bidirectional=True)

        # faction
        faction = self._slug(meta.get("faction", ""))
        if faction:
            self._add_edge(slug, faction, "faction_membership", bidirectional=True)

        # species (not bidirectional — species doesn't list characters)
        species = self._slug(meta.get("species", ""))
        if species:
            self._add_edge(slug, species, "species_ref")

        # race
        race = self._slug(meta.get("race", ""))
        if race:
            self._add_edge(slug, race, "race_ref")

        # family_links
        family = meta.get("family_links", {}) or {}

        lineage = self._slug(family.get("lineage", ""))
        if lineage:
            self._add_edge(slug, lineage, "lineage_membership", bidirectional=True)

        for parent_field in ("father", "mother"):
            parent = self._slug(family.get(parent_field, ""))
            if parent:
                self._add_edge(slug, parent, "family_link",
                               edge_subtype="child", bidirectional=True)

        spouse = self._slug(family.get("spouse", ""))
        if spouse:
            self._add_edge(slug, spouse, "family_link",
                           edge_subtype="spouse", bidirectional=True)

        for child_ref in family.get("children", []) or []:
            child = self._slug(child_ref)
            if child:
                self._add_edge(slug, child, "family_link",
                               edge_subtype="parent", bidirectional=True)

        for sib_ref in family.get("siblings", []) or []:
            sib = self._slug(sib_ref)
            if sib:
                self._add_edge(slug, sib, "family_link",
                               edge_subtype="sibling", bidirectional=True)

        # arc
        arc = self._slug(meta.get("arc", ""))
        if arc:
            self._add_edge(slug, arc, "arc_participant")

    def _extract_location_edges(self, slug: str, meta: dict) -> None:
        # parent hierarchy
        parent = self._slug(meta.get("parent", ""))
        if parent:
            self._add_edge(slug, parent, "location_hierarchy")

        # routes
        for route in meta.get("routes", []) or []:
            if isinstance(route, dict):
                dest = self._slug(route.get("to", "") or route.get("destination", ""))
                if dest:
                    route_meta = {}
                    for key in ("methods", "distance", "route_type",
                                "travel_time"):
                        if key in route:
                            route_meta[key] = route[key]
                    self._add_edge(slug, dest, "route",
                                   metadata=route_meta, bidirectional=True)

        # notable characters
        for char_ref in meta.get("notable_characters", []) or []:
            char = self._slug(char_ref)
            if char:
                self._add_edge(slug, char, "notable_character",
                               bidirectional=True)

        # controlling faction
        faction = self._slug(meta.get("faction", ""))
        if faction:
            self._add_edge(slug, faction, "faction_territory",
                           bidirectional=True)

    def _extract_faction_edges(self, slug: str, meta: dict) -> None:
        # leader
        leader = self._slug(meta.get("leader", ""))
        if leader:
            self._add_edge(slug, leader, "leader")

        # members
        for mem_ref in meta.get("members", []) or []:
            mem = self._slug(mem_ref)
            if mem:
                self._add_edge(slug, mem, "faction_membership",
                               bidirectional=True)

        # headquarters
        hq = self._slug(meta.get("headquarters", ""))
        if hq:
            self._add_edge(slug, hq, "faction_territory", bidirectional=True)

        # allies
        for ally_ref in meta.get("allies", []) or []:
            ally = self._slug(ally_ref)
            if ally:
                self._add_edge(slug, ally, "faction_ally", bidirectional=True)

        # enemies
        for enemy_ref in meta.get("enemies", []) or []:
            enemy = self._slug(enemy_ref)
            if enemy:
                self._add_edge(slug, enemy, "faction_enemy",
                               bidirectional=True)

    def _extract_event_edges(self, slug: str, meta: dict) -> None:
        # participants
        for p in meta.get("participants", []) or []:
            if isinstance(p, dict):
                target = self._slug(p.get("entity", ""))
                if target:
                    self._add_edge(slug, target, "event_participant",
                                   metadata={"role": p.get("role", "")})
            elif isinstance(p, str) and p:
                self._add_edge(slug, self._slug(p), "event_participant")

        # locations
        for loc_ref in meta.get("locations", []) or []:
            loc = self._slug(loc_ref)
            if loc:
                self._add_edge(slug, loc, "event_location")

        # organizations
        for org in meta.get("organizations", []) or []:
            if isinstance(org, dict):
                target = self._slug(org.get("entity", ""))
                if target:
                    self._add_edge(slug, target, "event_organization")
            elif isinstance(org, str) and org:
                self._add_edge(slug, self._slug(org), "event_organization")

        # items
        for item_ref in meta.get("items_involved", []) or []:
            item = self._slug(item_ref)
            if item:
                self._add_edge(slug, item, "event_item")

        # causality
        for cause_ref in meta.get("caused_by", []) or []:
            cause = self._slug(cause_ref)
            if cause:
                self._add_edge(slug, cause, "causality",
                               edge_subtype="caused_by", bidirectional=True)

        for leads_ref in meta.get("leads_to", []) or []:
            leads = self._slug(leads_ref)
            if leads:
                self._add_edge(slug, leads, "causality",
                               edge_subtype="leads_to", bidirectional=True)

    def _extract_species_edges(self, slug: str, meta: dict) -> None:
        # races
        for race_ref in meta.get("races", []) or []:
            race = self._slug(race_ref)
            if race:
                self._add_edge(slug, race, "species_race", bidirectional=True)

        # relationships
        for rel in meta.get("relationships", []) or []:
            if isinstance(rel, dict):
                target = self._slug(rel.get("species", ""))
                if target:
                    self._add_edge(slug, target, "species_relationship",
                                   metadata={"disposition": rel.get("disposition", "")},
                                   bidirectional=True)

    def _extract_race_edges(self, slug: str, meta: dict) -> None:
        # species
        species = self._slug(meta.get("species", ""))
        if species:
            self._add_edge(slug, species, "species_race", bidirectional=True)

        # relationships
        for rel in meta.get("relationships", []) or []:
            if isinstance(rel, dict):
                target = self._slug(rel.get("race", ""))
                if target:
                    self._add_edge(slug, target, "race_relationship",
                                   metadata={"disposition": rel.get("disposition", "")},
                                   bidirectional=True)

        # faction affiliations
        for fac_ref in meta.get("faction_affiliations", []) or []:
            fac = self._slug(fac_ref)
            if fac:
                self._add_edge(slug, fac, "faction_affiliation")

    def _extract_language_edges(self, slug: str, meta: dict) -> None:
        family = meta.get("family", {}) or {}

        # parent language
        parent = self._slug(family.get("parent_language", ""))
        if parent:
            self._add_edge(slug, parent, "language_family",
                           edge_subtype="parent", bidirectional=True)

        # child languages
        for child_ref in family.get("child_languages", []) or []:
            child = self._slug(child_ref)
            if child:
                self._add_edge(slug, child, "language_family",
                               edge_subtype="child", bidirectional=True)

        # intelligibility
        for entry in meta.get("intelligibility", []) or []:
            if isinstance(entry, dict):
                target = self._slug(entry.get("language", ""))
                if not target:
                    continue
                direction = entry.get("direction", "mutual")
                score = entry.get("score", 0.0)
                bidi = direction == "mutual"
                self._add_edge(slug, target, "intelligibility",
                               metadata={"score": score, "direction": direction},
                               bidirectional=bidi)

    def _extract_item_edges(self, slug: str, meta: dict) -> None:
        owner = self._slug(meta.get("owner", ""))
        if owner:
            self._add_edge(slug, owner, "ownership")

        loc = self._slug(meta.get("location", ""))
        if loc:
            self._add_edge(slug, loc, "item_location")

        creator = self._slug(meta.get("creator_ref", "") or meta.get("creator", ""))
        if creator:
            self._add_edge(slug, creator, "item_creator")

    def _extract_lineage_edges(self, slug: str, meta: dict) -> None:
        founder = self._slug(meta.get("founder", ""))
        if founder:
            self._add_edge(slug, founder, "lineage_membership",
                           edge_subtype="founder")

        head = self._slug(meta.get("current_head", ""))
        if head:
            self._add_edge(slug, head, "lineage_membership",
                           edge_subtype="head")

        for mem_ref in meta.get("members", []) or []:
            mem = self._slug(mem_ref)
            if mem:
                self._add_edge(slug, mem, "lineage_membership",
                               bidirectional=True)

        seat = self._slug(meta.get("seat", ""))
        if seat:
            self._add_edge(slug, seat, "lineage_seat")

        faction = self._slug(meta.get("faction", ""))
        if faction:
            self._add_edge(slug, faction, "faction_affiliation")

        for ally_ref in meta.get("allied_lineages", []) or []:
            ally = self._slug(ally_ref)
            if ally:
                self._add_edge(slug, ally, "lineage_ally", bidirectional=True)

        for rival_ref in meta.get("rival_lineages", []) or []:
            rival = self._slug(rival_ref)
            if rival:
                self._add_edge(slug, rival, "lineage_rival",
                               bidirectional=True)

    def _extract_arc_edges(self, slug: str, meta: dict) -> None:
        for list_key in ("protagonists", "antagonists", "supporting",
                         "characters_involved"):
            for ref in meta.get(list_key, []) or []:
                target = self._slug(ref)
                if target:
                    self._add_edge(slug, target, "arc_participant")

        for loc_ref in meta.get("locations", []) or []:
            loc = self._slug(loc_ref)
            if loc:
                self._add_edge(slug, loc, "arc_location")

        for fac_ref in meta.get("factions_involved", []) or []:
            fac = self._slug(fac_ref)
            if fac:
                self._add_edge(slug, fac, "arc_faction")

    def _extract_magic_system_edges(self, slug: str, meta: dict) -> None:
        for p in meta.get("practitioners", []) or []:
            if isinstance(p, dict):
                target = self._slug(p.get("entity", "") or p.get("name", ""))
            else:
                target = self._slug(p)
            if target:
                self._add_edge(slug, target, "magic_practitioner")

        for p in meta.get("famous_practitioners", []) or []:
            target = self._slug(p)
            if target:
                self._add_edge(slug, target, "magic_practitioner")

    # ── Validation ────────────────────────────────────────────────────────

    def check_dangling_references(self) -> list[ValidationIssue]:
        """Find edges whose target slug does not exist as a node."""
        issues: list[ValidationIssue] = []
        for source_slug, edge_list in self.edges.items():
            for edge in edge_list:
                if not edge.target:
                    continue
                if edge.target not in self.nodes:
                    issues.append(ValidationIssue(
                        severity="error",
                        category="dangling_ref",
                        message=(f"{self._node_label(source_slug)}: "
                                 f"{edge.edge_type} reference '{edge.target}' "
                                 f"not found"),
                        source_slug=source_slug,
                        target_slug=edge.target,
                        edge_type=edge.edge_type,
                    ))
        return issues

    def check_bidirectional_symmetry(self) -> list[ValidationIssue]:
        """For every bidirectional edge A→B, verify a compatible B→A exists."""
        issues: list[ValidationIssue] = []
        seen: set[tuple[str, str, str, str]] = set()

        for source_slug, edge_list in self.edges.items():
            for edge in edge_list:
                if not edge.bidirectional:
                    continue
                if edge.target not in self.nodes:
                    continue  # already caught by dangling check

                key = (edge.source, edge.target, edge.edge_type, edge.edge_subtype)
                if key in seen:
                    continue
                seen.add(key)

                if self._has_compatible_reverse(edge):
                    continue

                issues.append(ValidationIssue(
                    severity="error",
                    category="asymmetric_edge",
                    message=(f"{self._node_label(source_slug)}: "
                             f"{edge.edge_type}"
                             f"{'/' + edge.edge_subtype if edge.edge_subtype else ''}"
                             f" → '{edge.target}' has no reciprocal edge"),
                    source_slug=source_slug,
                    target_slug=edge.target,
                    edge_type=edge.edge_type,
                ))
        return issues

    def _has_compatible_reverse(self, edge: GraphEdge) -> bool:
        """Check whether a reverse edge exists for *edge*."""
        reverse_edges = self.edges.get(edge.target, [])

        # Determine what the expected reverse looks like
        expected = COMPATIBLE_REVERSE.get((edge.edge_type, edge.edge_subtype))

        for rev in reverse_edges:
            if rev.target != edge.source:
                continue
            if expected:
                if (rev.edge_type, rev.edge_subtype) == expected:
                    return True
            else:
                # Same edge_type is considered compatible
                if rev.edge_type == edge.edge_type:
                    return True
        return False

    def check_business_rules(self, calendar: dict | None = None) -> list[ValidationIssue]:
        """Domain-specific integrity checks."""
        issues: list[ValidationIssue] = []
        self._rule_min_parent_age(issues)
        self._rule_faction_leader(issues)
        self._rule_dead_character_last_appearance(issues)
        self._rule_image_prompt_completeness(issues)
        self._rule_voice_completeness(issues)
        return issues

    def _rule_min_parent_age(self, issues: list[ValidationIssue]) -> None:
        """Parents must be at least 16 years older than children."""
        for source_slug, edge_list in self.edges.items():
            for edge in edge_list:
                if edge.edge_type != "family_link":
                    continue
                if edge.edge_subtype == "parent":
                    parent_slug = source_slug
                    child_slug = edge.target
                elif edge.edge_subtype == "child":
                    parent_slug = edge.target
                    child_slug = source_slug
                else:
                    continue

                parent_node = self.nodes.get(parent_slug)
                child_node = self.nodes.get(child_slug)
                if not parent_node or not child_node:
                    continue

                parent_age = self._parse_age(parent_node.meta.get("age"))
                child_age = self._parse_age(child_node.meta.get("age"))
                if parent_age is None or child_age is None:
                    continue

                age_diff = parent_age - child_age
                if age_diff < 16:
                    issues.append(ValidationIssue(
                        severity="error",
                        category="business_rule",
                        message=(f"Parent '{parent_node.name}' (age {parent_age}) "
                                 f"is only {age_diff} years older than child "
                                 f"'{child_node.name}' (age {child_age}); "
                                 f"minimum is 16"),
                        source_slug=parent_slug,
                        target_slug=child_slug,
                        edge_type="family_link",
                    ))

    def _rule_faction_leader(self, issues: list[ValidationIssue]) -> None:
        """Each faction should have a leader; living leader if specified."""
        for slug in self.entity_type_index.get("faction", []):
            node = self.nodes[slug]
            leader_ref = node.meta.get("leader", "")

            # Explicitly vacant / empty is fine
            if not leader_ref or str(leader_ref).lower() in ("", "vacant", "none"):
                continue

            leader_slug = self._slug(leader_ref)
            leader_node = self.nodes.get(leader_slug)
            if not leader_node:
                continue  # dangling ref caught elsewhere

            if leader_node.entity_type != "character":
                issues.append(ValidationIssue(
                    severity="error",
                    category="business_rule",
                    message=(f"Faction '{node.name}': leader '{leader_slug}' "
                             f"is a {leader_node.entity_type}, not a character"),
                    source_slug=slug,
                    target_slug=leader_slug,
                    edge_type="leader",
                ))
            elif leader_node.meta.get("status") == "dead":
                issues.append(ValidationIssue(
                    severity="error",
                    category="business_rule",
                    message=(f"Faction '{node.name}': leader "
                             f"'{leader_node.name}' has status 'dead'"),
                    source_slug=slug,
                    target_slug=leader_slug,
                    edge_type="leader",
                ))

    def _rule_dead_character_last_appearance(self, issues: list[ValidationIssue]) -> None:
        """Dead characters should have last_appearance set."""
        for slug in self.entity_type_index.get("character", []):
            node = self.nodes[slug]
            if node.meta.get("status") == "dead":
                if not node.meta.get("last_appearance"):
                    issues.append(ValidationIssue(
                        severity="warning",
                        category="data_completeness",
                        message=(f"Character '{node.name}': status is 'dead' "
                                 f"but last_appearance not set"),
                        source_slug=slug,
                    ))

    def _rule_image_prompt_completeness(self, issues: list[ValidationIssue]) -> None:
        """Major characters and locations should have image_prompt."""
        important_roles = {"major", "protagonist", "antagonist", "supporting"}

        for slug in self.entity_type_index.get("character", []):
            node = self.nodes[slug]
            role = node.meta.get("role", "")
            if role in important_roles:
                descs = node.meta.get("descriptions", {}) or {}
                if not descs.get("image_prompt"):
                    issues.append(ValidationIssue(
                        severity="warning",
                        category="data_completeness",
                        message=(f"Character '{node.name}' (role={role}): "
                                 f"missing descriptions.image_prompt"),
                        source_slug=slug,
                    ))

        for slug in self.entity_type_index.get("location", []):
            node = self.nodes[slug]
            descs = node.meta.get("descriptions", {}) or {}
            if not descs.get("image_prompt"):
                issues.append(ValidationIssue(
                    severity="warning",
                    category="data_completeness",
                    message=(f"Location '{node.name}': "
                             f"missing descriptions.image_prompt"),
                    source_slug=slug,
                ))

    def _rule_voice_completeness(self, issues: list[ValidationIssue]) -> None:
        """Important characters should have voice config for TTS generation."""
        important_roles = {"major", "protagonist", "antagonist", "supporting"}

        for slug in self.entity_type_index.get("character", []):
            node = self.nodes[slug]
            role = node.meta.get("role", "")
            if role not in important_roles:
                continue
            voice = node.meta.get("voice", {}) or {}
            if not voice.get("sample_text"):
                issues.append(ValidationIssue(
                    severity="warning",
                    category="data_completeness",
                    message=(f"Character '{node.name}' (role={role}): "
                             f"missing voice.sample_text for TTS generation"),
                    source_slug=slug,
                ))
            if not voice.get("description"):
                issues.append(ValidationIssue(
                    severity="warning",
                    category="data_completeness",
                    message=(f"Character '{node.name}' (role={role}): "
                             f"missing voice.description for TTS voice design"),
                    source_slug=slug,
                ))
            # Check voice tags gender matches character gender
            tags = voice.get("tags", []) or []
            gender = (node.meta.get("gender", "") or "").lower().strip()
            tag_set = {t.lower().strip() for t in tags}
            if gender and tags:
                gender_tags = tag_set & {"male", "female"}
                if gender_tags:
                    tag_gender = gender_tags.pop()
                    norm_gender = "female" if gender in ("female", "f", "woman") else "male" if gender in ("male", "m", "man") else ""
                    if norm_gender and tag_gender != norm_gender:
                        issues.append(ValidationIssue(
                            severity="error",
                            category="data_consistency",
                            message=(f"Character '{node.name}': gender is '{gender}' "
                                     f"but voice.tags contains '{tag_gender}'"),
                            source_slug=slug,
                        ))

    def validate(self, calendar: dict | None = None) -> list[ValidationIssue]:
        """Run all validation checks and return combined issues."""
        issues: list[ValidationIssue] = []
        issues.extend(self.check_dangling_references())
        issues.extend(self.check_bidirectional_symmetry())
        issues.extend(self.check_business_rules(calendar=calendar))
        return issues

    # ── Query methods ─────────────────────────────────────────────────────

    def neighbors(self, slug: str, edge_type: str | None = None,
                  direction: str = "out") -> list[tuple[str, GraphEdge]]:
        """Return (neighbor_slug, edge) pairs for a node.

        *direction*: "out" (outgoing), "in" (incoming), or "both".
        """
        results: list[tuple[str, GraphEdge]] = []

        if direction in ("out", "both"):
            for edge in self.edges.get(slug, []):
                if edge_type and edge.edge_type != edge_type:
                    continue
                results.append((edge.target, edge))

        if direction in ("in", "both"):
            for edge in self.reverse_edges.get(slug, []):
                if edge_type and edge.edge_type != edge_type:
                    continue
                results.append((edge.source, edge))

        return results

    def nodes_by_type(self, entity_type: str) -> list[GraphNode]:
        """Return all nodes of a given entity type."""
        return [self.nodes[s] for s in self.entity_type_index.get(entity_type, [])
                if s in self.nodes]

    def shortest_path(self, source: str, target: str,
                      edge_types: set[str] | None = None) -> list[str] | None:
        """BFS shortest path from *source* to *target*.

        Returns list of slugs (inclusive) or None if unreachable.
        Optional *edge_types* filter restricts which edges are traversed.
        """
        if source not in self.nodes or target not in self.nodes:
            return None
        if source == target:
            return [source]

        visited: set[str] = {source}
        queue: deque[list[str]] = deque([[source]])

        while queue:
            path = queue.popleft()
            current = path[-1]

            for edge in self.edges.get(current, []):
                if edge_types and edge.edge_type not in edge_types:
                    continue
                nxt = edge.target
                if nxt in visited:
                    continue
                if nxt not in self.nodes:
                    continue
                new_path = path + [nxt]
                if nxt == target:
                    return new_path
                visited.add(nxt)
                queue.append(new_path)

        return None

    def isolated_nodes(self) -> list[GraphNode]:
        """Nodes with no edges in or out."""
        connected: set[str] = set()
        for slug in self.edges:
            if self.edges[slug]:
                connected.add(slug)
        for slug in self.reverse_edges:
            if self.reverse_edges[slug]:
                connected.add(slug)
        return [self.nodes[s] for s in self.nodes if s not in connected]

    def entities_in_faction(self, faction_slug: str) -> list[GraphNode]:
        """All character nodes connected to *faction_slug* via faction_membership."""
        results: list[GraphNode] = []
        for edge in self.edges.get(faction_slug, []):
            if edge.edge_type == "faction_membership":
                node = self.nodes.get(edge.target)
                if node and node.entity_type == "character":
                    results.append(node)
        # Also check reverse — characters with faction_membership → this faction
        for edge in self.reverse_edges.get(faction_slug, []):
            if edge.edge_type == "faction_membership":
                node = self.nodes.get(edge.source)
                if node and node.entity_type == "character":
                    if node not in results:
                        results.append(node)
        return results

    def routes_from(self, location_slug: str) -> list[GraphEdge]:
        """All route edges originating from *location_slug*."""
        return [e for e in self.edges.get(location_slug, [])
                if e.edge_type == "route"]

    def events_involving(self, entity_slug: str) -> list[GraphNode]:
        """All event nodes connected to *entity_slug* (as participant, location, etc.)."""
        event_slugs: set[str] = set()
        # entity is a target of an event edge
        for edge in self.reverse_edges.get(entity_slug, []):
            if edge.edge_type.startswith("event_"):
                event_slugs.add(edge.source)
        return [self.nodes[s] for s in event_slugs if s in self.nodes]

    # ── Internal helpers ──────────────────────────────────────────────────

    def _node_label(self, slug: str) -> str:
        """Human-readable label for error messages."""
        node = self.nodes.get(slug)
        if node:
            return f"{node.entity_type.title()} '{node.name}'"
        return f"'{slug}'"

    @staticmethod
    def _parse_age(age_val: Any) -> int | None:
        """Try to extract a numeric age from an age field (string or int)."""
        if age_val is None:
            return None
        if isinstance(age_val, (int, float)):
            return int(age_val)
        if isinstance(age_val, str):
            # Handle "32", "~30", "early 40s", "25-30", etc.
            import re
            m = re.search(r"(\d+)", str(age_val))
            if m:
                return int(m.group(1))
        return None

    # ── Auto-fix ─────────────────────────────────────────────────────────

    def auto_fix_issues(self, entities: dict, project_dir) -> list[str]:
        """Auto-fix detectable issues. Returns list of fix descriptions.

        Fixes applied:
        1. Faction membership: if character.faction = X, add character to X.members[]
        2. Notable characters: if character.location = X, add character to X.notable_characters[]
        3. Species↔race: if race.species = X, add race to X.races[] and vice versa
        4. Event causality: if A.leads_to includes B, add A to B.caused_by (and vice versa)
        5. Lineage membership: if character.lineage = X, add character to X.members[]
        6. Faction ally/enemy symmetry: if A.allies includes B, add A to B.allies
        """
        fixes: list[str] = []
        notable_roles = {"protagonist", "antagonist", "supporting", "major"}

        # ── Fix 1: Faction membership ────────────────────────────────────
        for char_slug in self.entity_type_index.get("character", []):
            char_node = self.nodes[char_slug]
            faction_edges = [e for e in self.edges.get(char_slug, [])
                             if e.edge_type == "faction_membership"]
            for edge in faction_edges:
                faction_slug = edge.target
                if faction_slug not in self.nodes:
                    continue
                faction_data = entities.get("faction", {}).get(faction_slug)
                if not faction_data:
                    continue
                # Check if faction already lists this character
                members = faction_data["meta"].get("members", []) or []
                member_slugs = set()
                for m in members:
                    ms = self._slug(m)
                    if ms:
                        member_slugs.add(ms)
                if char_slug not in member_slugs:
                    file_path = faction_data["file"]
                    meta, body = _parse_entity_file(file_path)
                    if "members" not in meta or meta["members"] is None:
                        meta["members"] = []
                    meta["members"].append(char_slug)
                    rewrite_entity_frontmatter(file_path, meta, body)
                    fixes.append(
                        f"Faction '{faction_data['meta'].get('name', faction_slug)}': "
                        f"added '{char_node.name}' to members "
                        f"[{file_path.name}]"
                    )

        # ── Fix 2: Notable characters ────────────────────────────────────
        for char_slug in self.entity_type_index.get("character", []):
            char_node = self.nodes[char_slug]
            role = char_node.meta.get("role", "")
            if role not in notable_roles:
                continue
            loc_edges = [e for e in self.edges.get(char_slug, [])
                         if e.edge_type == "location_ref"]
            for edge in loc_edges:
                loc_slug = edge.target
                if loc_slug not in self.nodes:
                    continue
                loc_data = entities.get("location", {}).get(loc_slug)
                if not loc_data:
                    continue
                notables = loc_data["meta"].get("notable_characters", []) or []
                notable_slugs = set()
                for n in notables:
                    ns = self._slug(n)
                    if ns:
                        notable_slugs.add(ns)
                if char_slug not in notable_slugs:
                    file_path = loc_data["file"]
                    meta, body = _parse_entity_file(file_path)
                    if "notable_characters" not in meta or meta["notable_characters"] is None:
                        meta["notable_characters"] = []
                    meta["notable_characters"].append(char_slug)
                    rewrite_entity_frontmatter(file_path, meta, body)
                    fixes.append(
                        f"Location '{loc_data['meta'].get('name', loc_slug)}': "
                        f"added '{char_node.name}' to notable_characters "
                        f"[{file_path.name}]"
                    )

        # ── Fix 3: Species↔race ──────────────────────────────────────────
        # Race→species: ensure species.races[] includes the race
        for race_slug in self.entity_type_index.get("race", []):
            race_node = self.nodes[race_slug]
            sp_edges = [e for e in self.edges.get(race_slug, [])
                        if e.edge_type == "species_race"]
            for edge in sp_edges:
                sp_slug = edge.target
                if sp_slug not in self.nodes:
                    continue
                sp_data = entities.get("species", {}).get(sp_slug)
                if not sp_data:
                    continue
                sp_races = sp_data["meta"].get("races", []) or []
                race_slugs = set()
                for r in sp_races:
                    rs = self._slug(r)
                    if rs:
                        race_slugs.add(rs)
                if race_slug not in race_slugs:
                    file_path = sp_data["file"]
                    meta, body = _parse_entity_file(file_path)
                    if "races" not in meta or meta["races"] is None:
                        meta["races"] = []
                    meta["races"].append(race_slug)
                    rewrite_entity_frontmatter(file_path, meta, body)
                    fixes.append(
                        f"Species '{sp_data['meta'].get('name', sp_slug)}': "
                        f"added '{race_node.name}' to races "
                        f"[{file_path.name}]"
                    )

        # Species→race: ensure each listed race has species pointing back
        for sp_slug in self.entity_type_index.get("species", []):
            sp_node = self.nodes[sp_slug]
            race_edges = [e for e in self.edges.get(sp_slug, [])
                          if e.edge_type == "species_race"]
            for edge in race_edges:
                race_slug = edge.target
                if race_slug not in self.nodes:
                    continue
                race_data = entities.get("race", {}).get(race_slug)
                if not race_data:
                    continue
                existing_sp = self._slug(race_data["meta"].get("species", ""))
                if existing_sp == sp_slug:
                    continue
                # Only fix if species field is empty (don't overwrite a different value)
                if existing_sp:
                    continue
                file_path = race_data["file"]
                meta, body = _parse_entity_file(file_path)
                meta["species"] = sp_slug
                rewrite_entity_frontmatter(file_path, meta, body)
                fixes.append(
                    f"Race '{race_data['meta'].get('name', race_slug)}': "
                    f"set species to '{sp_node.name}' "
                    f"[{file_path.name}]"
                )

        # ── Fix 4: Event causality symmetry ──────────────────────────────
        for evt_slug in self.entity_type_index.get("event", []):
            evt_node = self.nodes[evt_slug]
            for edge in self.edges.get(evt_slug, []):
                if edge.edge_type != "causality":
                    continue
                target_slug = edge.target
                if target_slug not in self.nodes:
                    continue
                target_data = entities.get("event", {}).get(target_slug)
                if not target_data:
                    continue

                if edge.edge_subtype == "leads_to":
                    # Target should have caused_by pointing back
                    caused_by = target_data["meta"].get("caused_by", []) or []
                    caused_slugs = {self._slug(c) for c in caused_by if c}
                    if evt_slug not in caused_slugs:
                        file_path = target_data["file"]
                        meta, body = _parse_entity_file(file_path)
                        if "caused_by" not in meta or meta["caused_by"] is None:
                            meta["caused_by"] = []
                        meta["caused_by"].append(evt_slug)
                        rewrite_entity_frontmatter(file_path, meta, body)
                        fixes.append(
                            f"Event '{target_data['meta'].get('name', target_slug)}': "
                            f"added '{evt_node.name}' to caused_by "
                            f"[{file_path.name}]"
                        )

                elif edge.edge_subtype == "caused_by":
                    # Target should have leads_to pointing back
                    leads_to = target_data["meta"].get("leads_to", []) or []
                    leads_slugs = {self._slug(lt) for lt in leads_to if lt}
                    if evt_slug not in leads_slugs:
                        file_path = target_data["file"]
                        meta, body = _parse_entity_file(file_path)
                        if "leads_to" not in meta or meta["leads_to"] is None:
                            meta["leads_to"] = []
                        meta["leads_to"].append(evt_slug)
                        rewrite_entity_frontmatter(file_path, meta, body)
                        fixes.append(
                            f"Event '{target_data['meta'].get('name', target_slug)}': "
                            f"added '{evt_node.name}' to leads_to "
                            f"[{file_path.name}]"
                        )

        # ── Fix 5: Lineage membership ────────────────────────────────────
        for char_slug in self.entity_type_index.get("character", []):
            char_node = self.nodes[char_slug]
            lineage_edges = [e for e in self.edges.get(char_slug, [])
                             if e.edge_type == "lineage_membership"]
            for edge in lineage_edges:
                lin_slug = edge.target
                if lin_slug not in self.nodes:
                    continue
                lin_data = entities.get("lineage", {}).get(lin_slug)
                if not lin_data:
                    continue
                members = lin_data["meta"].get("members", []) or []
                member_slugs = set()
                for m in members:
                    ms = self._slug(m)
                    if ms:
                        member_slugs.add(ms)
                if char_slug not in member_slugs:
                    file_path = lin_data["file"]
                    meta, body = _parse_entity_file(file_path)
                    if "members" not in meta or meta["members"] is None:
                        meta["members"] = []
                    meta["members"].append(char_slug)
                    rewrite_entity_frontmatter(file_path, meta, body)
                    fixes.append(
                        f"Lineage '{lin_data['meta'].get('name', lin_slug)}': "
                        f"added '{char_node.name}' to members "
                        f"[{file_path.name}]"
                    )

        # ── Fix 6: Faction ally/enemy symmetry ───────────────────────────
        for fac_slug in self.entity_type_index.get("faction", []):
            fac_node = self.nodes[fac_slug]
            for edge in self.edges.get(fac_slug, []):
                if edge.edge_type not in ("faction_ally", "faction_enemy"):
                    continue
                target_slug = edge.target
                if target_slug not in self.nodes:
                    continue
                target_data = entities.get("faction", {}).get(target_slug)
                if not target_data:
                    continue

                if edge.edge_type == "faction_ally":
                    field_name = "allies"
                else:
                    field_name = "enemies"

                existing = target_data["meta"].get(field_name, []) or []
                existing_slugs = {self._slug(x) for x in existing if x}
                if fac_slug not in existing_slugs:
                    file_path = target_data["file"]
                    meta, body = _parse_entity_file(file_path)
                    if field_name not in meta or meta[field_name] is None:
                        meta[field_name] = []
                    meta[field_name].append(fac_slug)
                    rewrite_entity_frontmatter(file_path, meta, body)
                    fixes.append(
                        f"Faction '{target_data['meta'].get('name', target_slug)}': "
                        f"added '{fac_node.name}' to {field_name} "
                        f"[{file_path.name}]"
                    )

        # ── Fix 7: Language family symmetry ──────────────────────────────
        for lang_slug in self.entity_type_index.get("language", []):
            lang_node = self.nodes[lang_slug]
            for edge in self.edges.get(lang_slug, []):
                if edge.edge_type != "language_family":
                    continue
                target_slug = edge.target
                if target_slug not in self.nodes:
                    continue
                target_data = entities.get("language", {}).get(target_slug)
                if not target_data:
                    continue
                family = target_data["meta"].get("family", {}) or {}

                if edge.edge_subtype == "parent":
                    # lang lists target as parent → target should list lang as child
                    children = family.get("child_languages", []) or []
                    child_slugs = {self._slug(c) for c in children if c}
                    if lang_slug not in child_slugs:
                        file_path = target_data["file"]
                        meta, body = _parse_entity_file(file_path)
                        if "family" not in meta or meta["family"] is None:
                            meta["family"] = {}
                        if "child_languages" not in meta["family"] or meta["family"]["child_languages"] is None:
                            meta["family"]["child_languages"] = []
                        meta["family"]["child_languages"].append(lang_slug)
                        rewrite_entity_frontmatter(file_path, meta, body)
                        fixes.append(
                            f"Language '{target_data['meta'].get('name', target_slug)}': "
                            f"added '{lang_node.name}' to child_languages "
                            f"[{file_path.name}]"
                        )

                elif edge.edge_subtype == "child":
                    # lang lists target as child → target should list lang as parent
                    parent = family.get("parent_language", "")
                    if parent and self._slug(parent) == lang_slug:
                        continue  # already correct
                    if parent:
                        continue  # has a different parent, don't overwrite
                    file_path = target_data["file"]
                    meta, body = _parse_entity_file(file_path)
                    if "family" not in meta or meta["family"] is None:
                        meta["family"] = {}
                    meta["family"]["parent_language"] = lang_slug
                    rewrite_entity_frontmatter(file_path, meta, body)
                    fixes.append(
                        f"Language '{target_data['meta'].get('name', target_slug)}': "
                        f"set parent_language to '{lang_node.name}' "
                        f"[{file_path.name}]"
                    )

        return fixes

    # ── Repr ──────────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        edge_count = sum(len(el) for el in self.edges.values())
        return (f"WorldGraph(nodes={len(self.nodes)}, edges={edge_count}, "
                f"types={list(self.entity_type_index.keys())})")
