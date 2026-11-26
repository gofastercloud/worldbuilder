---
name: magic-systems
description: Design, check or reject magic, spells, psionics, mana, divine power, the supernatural, magic users, magical creatures, curses and enchantment in a worldbuilding project, keeping it consistent with geography, economy, history and peoples. Use for any magic question, including "does my world have magic?". Always starts with the yes/no gate on world_flags.magic in project.yaml; if magic is off it creates no magic and offers technology, psychology or fraud explanations instead.
---

# Magic systems

Magic is a fact about physics, so it changes everything downstream. A good system has a source, a price, limits, users, institutions and a visible footprint on history, economy and geography. This skill follows the contract in the `worldbuilding` skill (`references/causality.md`): internal consistency first, causal chains, consequence sweep.

## Step 0: the yes/no gate (never skip)

Read `world_flags.magic` in `project.yaml` before anything else.

| State | Action |
|-------|--------|
| `present: false`, or `prevalence: none` | The world is non-magical. Do NOT create magic-system entities, magical effects, spells, curses that work, or magical creatures. Explain this to the user and offer (a) or (b) below. |
| `present` unset | Ask the user a direct yes or no. Do not guess. Record the answer in `project.yaml` (`present`, plus `prevalence`; if yes also `hardness`, `source`, `cost`, `heritability`) and then continue. |
| `present: true` | Proceed to design. Check `prevalence`, `hardness`, `source`, `cost`, `heritability`, `public_knowledge`, `divine_intervention` and any `locked: true` entries; every system you write must agree with them. |

**(a) Apparent magic, honouring the flag.** The world may contain things that look magical but have a mundane explanation that the files record: technology (a faction's engineers, hidden infrastructure), psychology (belief, suggestion, grief, ritual placebo), fraud (stage conjurors, oracles with informants), or natural phenomena (bioluminescence, aurora, toxic gas, mineral properties). Characters may believe it is magic; the machine description states the real cause. An entity of `type: technological` in `world/magic-systems/` is allowed under a no-magic flag (the-lattice does this for FTL travel).

**(b) Change the flag deliberately.** Only the user can decide this. Before editing `project.yaml`, run an impact sweep of everything written so far (history, peoples, religion, economy, language, existing events) and list what would need to change. Make the change only after the user agrees, then rewrite the affected files.

A world with `present: false` should read as a world where the question "why is there no magic here?" is not interesting. Do not smuggle magic in through "mysterious energies", curses that come true, or prophecies that work.

## Procedure for designing a system

Read `project.yaml`, `world/overview.md` and `rules.md` if present, existing magic systems, and the locations, peoples, events and economy the system will touch (see `worldbuilding` step 1). Then work through each section, recording the answer in the entity file.

1. **Source.** Where does the power come from, physically or metaphysically (ley lines, gods, a mineral, a field, minds, an exhausted prior civilisation)? A power with no origin is an orphan. Record `source` and, if it began at a point in time, `origin_event`.
2. **Users and heritability.** Who can use it: anyone trained, a bloodline, a species, divine selection, random gift? What fraction of the population? This must match `world_flags.magic.heritability` and `prevalence`. If heritable, link lineages and species.
3. **Cost (no free lunch).** Every effect must be paid for with something conserved: energy, time, health, materials, memory, favour, years of life. Record `cost.type`, `cost.amount` and side effects. If cost is `none` the world is trivially solved; say what then constrains it (scarcity of users, risk, social taboo).
4. **Limits and failure modes.** Write `limitations` and `cannot_do` as hard rules, and `failure_modes` (backlash, madness, burnout, mis-cast). A system that cannot fail is not dramatic and not credible.
5. **Scaling laws.** How does effect scale with cost, skill and numbers? Does ten times the effect cost ten times or a hundred times? What stops one master doing the work of an army? Record `scaling`.
6. **Learning and training.** How long does mastery take, who teaches, what does it cost? Ties to `learning_difficulty`, `ranks`.
7. **Institutions.** Whoever controls scarce knowledge or users forms a body: schools, guilds, churches, licensing, secret societies, black markets, inquisitions. Create or link factions; record `institutions`.
8. **Geography and climate.** Do places of power exist (ley lines, springs, high ground, a ruin)? Does climate or terrain feed or block it? Link `places_of_power` to location slugs and edit those locations too. Hand to `geography-and-climate`.
9. **Economy.** What does magic make cheap, what does it make valuable and scarce (users, reagents, anti-magic goods, certification)? Why has it not replaced all labour and technology? If it truly does, the economy must be rebuilt around it. Hand to `economy-and-trade`.
10. **History.** What events did it cause or change (wars, plagues cured, collapse of an empire, a catastrophe that set the rules)? Why is the world not Earth plus fireballs? Link `events` and write the causal chains. Hand to `history-and-events`.
11. **Peoples.** Species affinity or inability, languages with ritual forms, naming, religion. Hand to `peoples`.
12. **What it cannot do.** List explicit exclusions. These do more for coherence than the abilities.

## Hardness (Sanderson-style test questions)

`hardness` controls how much explanation the story owes the reader. Match `world_flags.magic.hardness`.

- **soft**: mysterious, unexplained; wonder over rules. Powers need not be systematised, but costs and consequences must still be consistent in the story. Never use it to solve a plot problem.
- **medium**: some rules known, some mysterious. The reader may be surprised by a limit but never by an unearned rescue.
- **hard**: strict rules, costs and limits the reader knows. The plot may be solved with the rules, never against them.
- **scientific**: fully systematic and quantified; treat as an engineering discipline.

Ask for every use of magic in a scene:
1. Could the reader have predicted this was possible?
2. Who paid for it, and with what?
3. Why did the characters not do this earlier, or more?
4. If it worked, what else would have been trivial? Is that consistently so everywhere?
5. What limit or failure mode is on display?
6. Does the result match the stated rules, or did the rules bend for the plot?

The harder the system, the more of these must be answered on the page. Soft systems still owe 2, 3 and 4.

## Second-order effects checklist

For each, write one line in `second_order_effects` (or say why it does not apply):
- **Communication**: can messages cross distance? Why is there still a postal service?
- **Medicine**: can it heal or harm? Plague, lifespan, birth rate, who gets treated.
- **Warfare**: tactics, armour, sieges, logistics, who holds the monopoly on violence, counters.
- **Agriculture**: yields, weather control, famine, land value.
- **Law**: licensing, liability, evidence (can magic detect lies?), jurisdiction, treason.
- **Crime**: theft, fraud, assassination, policing, forbidden uses.
- **Religion**: is it miracle or technique? Who claims authority? Heresy, divine intervention flag.
- **Also**: transport, construction, education, class, gender and inheritance rules if heritable.

## Anti-patterns

- Magic as a cure-all that never changes society.
- No cost, or a cost that is never paid.
- No institutions: a thousand users and no school, guild, law or church.
- Society identical to our history with spells pasted on.
- Rules that change for plot convenience, or a limit that appears only when needed.
- Powers with no origin, or an origin that contradicts the flag.
- Magic everywhere but no effect on prices, medicine, war or language.
- Every culture using it the same way.

## Myths of magic

Stories about magic are beliefs (`folklore-and-traditions`): when magic is present, check them against the system's rules; when magic is absent, they are allowed only as beliefs with `claims_supernatural: true` and never cause real effects.

## Consequence sweep

After writing or changing a system, update the affected files now:
- `history-and-events`: origin and turning-point events, wars, disasters; `magical_impact` on events.
- `geography-and-climate`: places of power, resource effects, terrain scarring.
- `economy-and-trade`: prices, scarce reagents, labour displaced, licensing, trade goods.
- `peoples`: species affinity, lineages, languages, religion, customs.
- Factions (institutions), characters (users, costs paid), items (enchanted or power-source fields).
Add reverse links on every referenced entity.

## Worked example (invented, illustrative only)

Flag: `present: true, prevalence: rare, hardness: hard, source: natural, cost: "body heat", heritability: "bloodline"`.

System **Thermal Binding** (`world/magic-systems/thermal-binding.md`, `type: elemental`):
- Source: geothermal ley lines under the Ashfall Range (`places_of_power: [ashfall-range]`); binders draw heat from the ground through a conductive stone circle.
- Cost: the user's body heat; a large working risks hypothermia. Limit: cannot create heat, only move it; useless in cold seas.
- Users: a bloodline in the Karrow lineage (about 1 in 500). Institution: the Hearthwardens, who license binders.
- Second-order: no one can heat a city, so wood and coal remain valuable; binders are scarce so they warm hospitals and kilns, not homes; it did not replace labour because each working needs a circle and a user.
- History: the Great Freeze (event) made binders indispensable and gave the Hearthwardens political power.

## Checklist

- [ ] Gate passed: `world_flags.magic.present` read; unset answered and recorded; off means no magic entities
- [ ] Source, users/heritability, cost, limits, failure modes, scaling, training all recorded
- [ ] Hardness matches the flag; no rule bends for plot
- [ ] Institutions created and linked
- [ ] Places of power linked to locations; both sides edited
- [ ] Events linked; causal chains recorded; economy and peoples updated
- [ ] Second-order effects written for each domain
- [ ] Consequence sweep done across the four sibling skills
- [ ] Run the `world-validate` skill and fix every error and warning before reporting done
