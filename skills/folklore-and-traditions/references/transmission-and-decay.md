# Transmission and decay

Fidelity falls with time, falls faster without writing, and is reset or frozen by institutions.

## Rough defaults

| Situation | Typical fidelity | Notes |
|---|---|---|
| Under about 50 years, witnesses alive | accurate to simplified | Reliability `firsthand`. Disputes between witnesses are normal (`conflicting-accounts`). |
| 50 to 150 years, oral | simplified | Core events and names mostly survive; causes and numbers drift. |
| 150 to 300 years, oral | simplified to embellished | Heroes fuse, lessons attach. |
| 300+ years, oral | embellished, conflated, garbled, or invented | `accurate` is not credible; the validator warns on it. |
| 1,000+ years, oral | garbled or invented, with a kernel in a fixed form | Only fixed forms (songs, rituals, oaths, place names) preserve kernels. |
| Written, institutional archive | accurate to simplified, but biased | Accurate about what the institution wanted recorded. Can freeze an error. |
| Ritual | can preserve details unchanged, with the meaning lost | The action survives; the explanation is rebuilt every few generations. |
| Song or rhyme | preserves wording and number, loses context | Rhythm resists change. Mistranslation hits it when the language shifts. |

## What changes the rate

- **Literacy**: scribal records slow drift but allow deliberate rewriting.
- **Institutions**: priesthoods, guilds and states freeze or rewrite. A regime change can reset the version overnight.
- **Language shift or contact**: each crossing is a mistranslation chance.
- **Trauma or shame**: speeds loss (taboo-induced silence).
- **Economic use**: a story that supports a claim or a market is repeated and polished.
- **Isolation**: isolated groups drift independently, so variants multiply.

## Status

- `living`: practised or told now.
- `fading`: carriers dwindling, practised by few; usually followed by a cause (urban drift, language death).
- `forgotten`: no living carriers; survives only in an archive, a ruin or the author's notes. A forgotten tradition is a trace only if something records it.
- `revived`: rediscovered and rebuilt, often differently from the original. Say who revived it and why (nationalism, tourism, scholarship); the revival itself is an event worth recording.
- `suppressed`: banned or hidden by an institution. Needs the suppressing faction and an effect (secret practice, coded form).

## Reliability (event enum used on a tradition)

Use `firsthand`, `well-documented`, `rumored`, `conflicting-accounts`, `legend` or `false-history` for how far the in-world record supports the tradition. `false-history` is for a deliberately falsified account, and should be linked to the faction that falsified it.

## Dates

`first_attested` is the first point at which it is known to exist, not the event date. It must not precede the earliest origin event. A big gap between event and attestation is realistic for oral traditions; say why it was not written down.
