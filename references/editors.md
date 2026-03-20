# Editors Reference

9 specialized Claude personas that review and validate content. Each focuses on one aspect of quality.

## Editor Overview

| Persona | Codename | Icon | Focus | Severity |
|---------|----------|------|-------|----------|
| Character Editor | The Psychologist | 🎭 | Character consistency, voice, arcs | Info/Warning |
| Continuity Editor | The Archivist | 📜 | Timeline, contradictions, facts | Error/Warning/Info |
| Dialogue Editor | The Linguist | 💬 | Speech patterns, period language | Warning/Info |
| Geography Editor | The Cartographer | 🗺️ | Spatial logic, travel, terrain | Error/Warning/Info |
| Pacing Editor | The Conductor | 🎵 | Story rhythm, tension, structure | Warning/Info |
| Plot Editor | The Detective | 🔍 | Logic, holes, threads, causality | Error/Warning/Info |
| Prose Editor | The Wordsmith | ✒️ | Line-level writing quality | Info |
| Sensitivity Editor | The Guardian | 🛡️ | Representation, tropes, safety | Warning/Info |
| World Rules Editor | The Lawkeeper | ⚖️ | World flags, magic costs, tech | Error/Warning |

## Character Editor — The Psychologist

**Focus:** Character consistency, motivation, arc progression

**Key Checks:**

| Check | Severity | What It Catches | Method |
|-------|----------|-----------------|--------|
| out-of-character | warning | Character acts against established traits | Compare actions vs traits |
| voice-drift | warning | Speech patterns change unexpectedly | Compare dialogue style |
| arc-stall | info | Arc stalls for several chapters | Track arc beats |
| forgotten-trait | info | Established trait not shown/referenced | Check trait list mentions |
| unearned-change | warning | Character changes without buildup | Track development |
| relationship-drift | info | Dynamic shifts without scene justification | Track relationship changes |
| motivation-gap | warning | Actions don't serve established goals | Cross-reference goals |
| knowledge-violation | error | Character acts on unknown info | Track character knowledge |

**Output:** Per-character arc status, voice consistency rating, specific issues with chapters/scenes

**Example output:**
```
## Character Report — Ch 1-5

#### Kael Dawnblade
- **Arc status:** Discovery (35%)
- **Voice consistency:** 9/10
- **Issues:**
  - **[KNOWLEDGE]** Ch 3: Kael knows about the prophecy but was never present or told
```

---

## Continuity Editor — The Archivist

**Focus:** Factual consistency, timeline integrity, world rules

**Key Checks:**

| Check | Severity | What It Catches | Method |
|-------|----------|-----------------|--------|
| dead-character-active | error | Dead character appears in story | Cross-ref deaths vs prose |
| timeline-contradiction | error | Events contradict established timeline | Compare dates in prose vs events |
| location-contradiction | error | Character in two places at once | Track locations per chapter |
| fact-drift | warning | Early fact (eye color, weapon) changes | Track stated facts |
| age-inconsistency | warning | Stated age doesn't match birth date | Calculate from timeline |
| relationship-contradiction | warning | Prose contradicts character file | Compare prose vs metadata |
| missing-event | info | Major event has no event file | Scan for undocumented events |
| season-weather-mismatch | info | Weather contradicts calendar position | Cross-ref dates with seasons |

**Output:** Continuity report with error list, fact tracker, timeline review

**Example output:**
```
## Continuity Report — Ch 1-10

### Errors (must fix)
- **[DEAD-ACTIVE]** Ch 5, p2: Morwen appears but died in "The Siege" (Year 14)
- **[TIMELINE]** Ch 8: References "last winter" but it's currently summer per calendar

### Warnings (should fix)
- **[FACT-DRIFT]** Ch 3: Kael's sword described as "plain steel" in Ch 1, now "silvered blade"
```

**Most critical editor.** Runs first in validation pipeline.

---

## Dialogue Editor — The Linguist

**Focus:** Speech patterns, period-appropriate language, character voices

**Key Checks:**

| Check | Severity | What It Catches | Method |
|-------|----------|-----------------|--------|
| voice-sameness | warning | Two+ characters speak identically | Compare dialogue patterns |
| period-language | warning | Modern language in non-modern setting | Flag modern slang/idioms |
| talking-heads | info | Long dialogue with no action beats | Flag 6+ line dialogue runs |
| voice-break | warning | Character's speech suddenly changes | Compare formality/vocab across scenes |
| info-dump-dialogue | warning | Unnatural exposition disguised as speech | Flag "As you know, Bob" patterns |
| missing-dialect | info | Character missing established dialect | Cross-ref origin vs voice notes |

**Output:** Voice distinctiveness matrix, issue list with specific quotes

**Example output:**
```
### Voice Distinctiveness Matrix:
|        | Kael | Morwen | Vexis |
|--------|------|--------|-------|
| Kael   |  —   | 7/10   | 9/10  |
| Morwen | 7/10 |   —    | 8/10  |

### Issues:
- **[PERIOD]** Ch 4: "That's literally crazy" — modern intensifier in medieval setting
- **[SAMENESS]** Ch 6: Kael and Vexis dialogue nearly interchangeable
```

---

## Geography Editor — The Cartographer

**Focus:** Spatial logic, terrain consistency, travel feasibility

**Key Checks:**

| Check | Severity | What It Catches | Method |
|-------|----------|-----------------|--------|
| impossible-travel | error | Character travels too fast | Calculate time vs route |
| transport-anachronism | error | Transport mode doesn't exist per flags | Check against defined systems |
| route-not-defined | warning | Travel route undefined | Verify routes exist |
| direction-contradiction | warning | Cardinal directions inconsistent | Track all directional references |
| location-description-drift | warning | Prose doesn't match location file | Compare descriptions |
| terrain-impossibility | error | Adjacent terrain geologically wrong | Check terrain adjacency rules |
| geology-contradiction | warning | Geology contradicts terrain/climate | Cross-check features |
| missing-journey | info | Character teleports to new location | Track location changes |
| climate-inconsistency | info | Weather doesn't match location | Cross-ref prose vs climate data |
| scale-violation | warning | Distances contradict geography | Check against route distances |
| hierarchy-gap | info | Location outside spatial hierarchy | Check location nesting |
| unreachable-location | warning | Location has no routes | Verify connectivity |

**Output:** Spatial hierarchy tree, travel log, terrain issue list, transport validation

**Example output:**
```
### Travel Log:
| Chapter | Character | From | To | Method | Time Stated | Time Per Route | Issue? |
|---------|-----------|------|----|--------|-------------|----------------|--------|
| 3       | Kael      | Valdris | Library | Horse | "2 days" | 5 days minimum | IMPOSSIBLE |

### Terrain Issues:
- **[TERRAIN]** Block 5: Desert adjacent to Glacier — invalid transition
```

---

## Pacing Editor — The Conductor

**Focus:** Story rhythm, tension curves, structural balance

**Key Checks:**

| Check | Severity | What It Catches | Method |
|-------|----------|-----------------|--------|
| chapter-length-imbalance | info | Chapter too long/short vs average | Compare word counts |
| tension-plateau | warning | Multiple chapters same tension level | Analyze scene types |
| arc-stall | warning | Arc beat missing for too many chapters | Track beat appearances |
| missing-breather | info | High intensity chapters with no cooldown | Track scene intensity |
| premature-climax | warning | Climax too early in structure | Check vs act structure |
| saggy-middle | info | Act 2 less dense than Acts 1 & 3 | Compare event density |
| unresolved-setup | warning | Foreshadowing not paid off | Cross-ref setup vs payoff |

**Output:** Tension curve visualization, arc tracking, setup/payoff analysis

**Example output:**
```
### Tension Curve:
Ch1  ████░░░░░░ Setup
Ch2  ██████░░░░ Rising
Ch3  ████████░░ Confrontation
Ch4  ███░░░░░░░ Breather ← good
Ch5  █████████░ Crisis

### Issues:
- **[PLATEAU]** Ch 6-8: 3 chapters of similar intensity (action-action-action)
- **[SETUP]** "The Prophecy" (Ch 1) still unresolved by Ch 10
```

---

## Plot Editor — The Detective

**Focus:** Logic, holes, causality, thread resolution

**Key Checks:**

| Check | Severity | What It Catches | Method |
|-------|----------|-----------------|--------|
| plot-hole | error | Logical gap breaking story logic | Follow cause-effect chains |
| unresolved-thread | warning | Subplot introduced but never resolved | Track arc foreshadowing |
| chekhovs-gun | warning | Significant item never used | Track significant items |
| deus-ex-machina | warning | Problem solved by unestablished element | Check solution introduction timeline |
| idiot-ball | info | Character makes obviously wrong choice | Evaluate vs intelligence |
| coincidence-overuse | info | Random chance drives plot too much | Track agency vs chance |
| broken-causality | error | Event cause doesn't lead to effect | Walk causality chains |
| power-inconsistency | warning | Character inexplicably stronger/weaker | Track power demonstrations |

**Output:** Thread tracker table, causality analysis, specific plot issues

**Example output:**
```
### Thread Tracker:
| Thread | Introduced | Status | Last Referenced |
|--------|-----------|--------|-----------------|
| The Prophecy | Ch 1 | Open | Ch 8 |
| Crown Fragments | Ch 3 | Partially resolved | Ch 12 |

### Issues:
- **[HOLE]** Ch 9: How did Kael escape the locked tower? Never explained.
- **[DEUS-EX]** Ch 15: The sword appears to save the day but was never mentioned before
```

---

## Prose Editor — The Wordsmith

**Focus:** Line-level writing quality, clarity, impact

**Key Checks:**

| Check | Severity | What It Catches | Method |
|-------|----------|-----------------|--------|
| purple-prose | info | Overly ornate writing obscuring meaning | Flag excessive adjectives/metaphors |
| weak-verbs | info | Over-reliance on "was", "had", "said" | Track verb frequency |
| adverb-excess | info | Too many -ly adverbs, especially in dialogue tags | Count adverbs per chapter |
| repetition | warning | Same word/phrase used too frequently | Track word frequency in windows |
| tell-not-show | info | Emotional state told not shown | Flag "he felt X" patterns |
| passive-voice | info | Excessive passive voice | Track passive vs active ratio |
| filter-words | info | Unnecessary distance-creating words | Flag "he saw", "she heard" |
| sentence-monotony | info | Consecutive sentences same structure/length | Analyze sentence variety |

**Output:** Chapter metrics, specific prose issues with quotes, readability analysis

**Example output:**
```
### Chapter Metrics:
| Chapter | Words | Avg Sentence | Passive % | Adverb/1000w | Readability |
|---------|-------|-------------|-----------|--------------|-------------|
| 1       | 3,200 | 18 words    | 12%       | 8.5          | Good        |
| 2       | 2,800 | 16 words    | 14%       | 6.2          | Good        |

### Issues:
- **[REPEAT]** Ch 3: "darkness" appears 12 times in 1500 words
- **[TELL]** Ch 5: "He felt angry" — show through action instead
```

---

## Sensitivity Editor — The Guardian

**Focus:** Representation, stereotypes, harmful tropes, content appropriateness

**Key Checks:**

| Check | Severity | What It Catches | Method |
|-------|----------|-----------------|--------|
| stereotype | warning | Character/culture relies on real-world stereotypes | Check against cultural_inspiration flags |
| harmful-trope | warning | Known harmful trope without subversion | Flag: bury-your-gays, magical-negro, noble-savage, etc. |
| representation-gap | info | Lack of diversity where world supports it | Analyze character demographics |
| power-dynamic | info | Problematic power dynamics uncritical | Flag slavery, colonialism, subjugation |
| content-rating-violation | warning | Content exceeds project rating | Check violence/sexual/language content |

**Output:** Issue list with context and alternatives, topic assessment

**Example output:**
```
### Issues:
- **[TROPE]** Ch 7: "Magical Negro" trope — wise mentor exists only to help white protagonist.
  Consider: Give mentor their own goals/agency not tied to protagonist's arc.
- **[STEREOTYPE]** Ch 12: The "tribal savages" read as real-world indigenous stereotypes.
  Suggestion: Add cultural complexity, distinct governance, conflict with other factions.

### Notes (not necessarily problems):
- **[TOPIC]** Ch 9: Handles slavery critically. Current approach: characters oppose it.
```

---

## World Rules Editor — The Lawkeeper

**Focus:** World flags, technology anachronisms, magic costs, physics

**Key Checks:**

| Check | Severity | What It Catches | Method |
|-------|----------|-----------------|--------|
| tech-anachronism | error | Technology exists that shouldn't per flags | Scan for tech keywords vs flags |
| magic-rule-violation | error | Magic used against system rules | Cross-ref usage vs limitations |
| magic-cost-skip | warning | Magic used without established cost | Check cost payment |
| physics-violation | warning | Physical impossibility not justified | Check against world_flags.physics |
| social-anachronism | info | Social norms don't match world flags | Check vs society flags |
| flag-contradiction | error | Manuscript contradicts locked world flag | Compare prose assertions |

**Tech Keywords tracked:**
- gunpowder: gun, cannon, ammunition, etc.
- printing: newspaper, pamphlet, printed, etc.
- electricity: electric, battery, wire, lightbulb, etc.
- steam_power: steam engine, locomotive, piston, etc.
- computing: computer, algorithm, data, etc.
- spaceflight: rocket, orbit, thruster, etc.

**Output:** World flags summary, violation list by type, context

**Example output:**
```
### World Flags Checked:
- Technology: medieval
- Gunpowder: false
- Magic: true
- Magic cost: life-force

### Violations:
- **[TECH]** Ch 6: "The musket roared" — world_flags.technology.gunpowder = false
- **[MAGIC]** Ch 8: Vexis casts spell without mentioned life-force cost
- **[PHYSICS]** Ch 12: Character jumps 50 feet vertically (not justified by magic)
```

---

## Editor Execution Order

During validation, editors run sequentially. **Order matters:**

1. **worldrules** ← Must pass first (foundation)
2. **geography** ← Spatial integrity
3. **continuity** ← Timeline integrity
4. **lore** ← Internal consistency
5. **characterization** ← Character level
6. **sensitivity** ← Final content review

Prose/dialogue/pacing/plot editors run during editorial passes (not validation), or on-demand.

---

## Severity Levels

| Level | Meaning | Action |
|-------|---------|--------|
| error | Story-breaking issue, must fix | Blocks validation, requires fix |
| warning | Significant issue, should fix | Noted, human reviews |
| info | Informational, can ignore | Noted, mostly harmless |

---

## When Each Editor Runs

**Post-generation validation (automatic):**
- worldrules, geography, continuity, lore, characterization, sensitivity
- All 6 must pass for world to be considered valid

**Editorial passes (on-demand, during manuscript work):**
- All 9 editors
- Used to improve existing manuscript
- Can run individually or as full pass

**Example:**
```
# Generate world
claude-code --wizard --genre fantasy --size M

# World validation runs automatically
> worldrules: PASS
> geography: PASS
> continuity: PASS
> lore: PASS
> characterization: PASS
> sensitivity: PASS

# Later, during manuscript editing
# User runs full editorial pass
claude-code --edit chapters/ --full-pass

# Runs all 9 editors
> character editor...
> continuity editor...
> dialogue editor...
> geography editor...
> pacing editor...
> plot editor...
> prose editor...
> sensitivity editor...
> worldrules editor...
```

---

## Quick Reference: Which Editor to Run

| Problem | Use |
|---------|-----|
| Character seems out of character | Character Editor |
| Timeline/facts don't match | Continuity Editor |
| Dialogue feels samey | Dialogue Editor |
| Travel times impossible | Geography Editor |
| Story feels draggy or rushed | Pacing Editor |
| Plot hole found | Plot Editor |
| Prose feels clunky | Prose Editor |
| Worried about representation | Sensitivity Editor |
| Tech/magic violates rules | World Rules Editor |
