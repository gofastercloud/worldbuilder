# Society, family, politics, religion, customs

## Kin and settlement
- Pastoral or foraging bands: small kin groups, patrilineal or matrilineal descent tied to herd or territory ownership, strong hospitality law, councils of elders, war-leaders by merit.
- Settled farming: household and village, inheritance of land is the central question (primogeniture keeps farms whole, partible inheritance splits them and drives migration or fragmentation), landlords and tenants, taxes in kind.
- Trade and port societies: guilds, merchant houses, contracts, oaths on written or witnessed terms, mixed neighbourhoods and several languages.
- Extractive or fortress societies (mines, holds): kin-based claims on fixed deposits, clan-guild structures, strict internal arbitration.
- High-lifespan species: few children, long apprenticeships, authority accumulates in elders, so succession is slow and rare; revolts and reforms come from the young and are slowed by seniority; long memories make feuds persistent. Account for how power turns over (voluntary retirement, ritual rotation, regencies, ritual death).
- Short-lifespan species: early marriage, large families, rapid turnover of leaders, oral history decays within a few generations unless written.

## Family forms
Choose and record: marriage (monogamy, polygyny, polyandry, group, none) and descent (patrilineal, matrilineal, bilateral, clan). Reason from resources and sex ratio, warfare, labour needs, bride wealth or dowry, and species reproduction (egg-clutch, hive, budding, constructed). Children's names, residence (patrilocal, matrilocal), fosterage and adoption all follow. Record in race `culture.social_structure` and in `family_links` of characters.

## Inheritance rules versus lineage
- Primogeniture/ultimogeniture: single heir keeps estate whole; younger siblings need other careers (clergy, army, migration, colonies), which feeds factions and exiles.
- Partible: splits estates, produces many small holders and frequent disputes.
- Elective or meritocratic: needs an electorate and a body that can verify merit (council, trial, contest); record who votes.
- Divine selection or combat: requires an authority or contest that exists in the world.
- Matrilineal rules require clear maternity; patrilineal rules can still run through adoption and claimed legitimacy.
Every lineage's `succession.rule` must be compatible with the race's inheritance custom and the species' reproduction. A succession history whose heirs do not fit the rule is an error.

## Politics and faction formation
Triggers: resource scarcity, border or tax disputes, religious schism, conquest and its aftermath, famine, migration, technological change, a succession crisis. Each faction has: cause, constituency (who benefits), leadership, resources, enemies who lose from it. Governance follows scale and economy: bands (consensus), chiefdoms (a leader with redistribution duties), city-states (councils and magistrates), tribute empires (a core with garrisons), merchant republics (guild boards).

## Religion
Forms: animist (local spirits tied to places), ancestor (tied to lineage and land), polytheist (specialised powers matching livelihoods), monotheist or philosophical (often follows empire, writing and urbanisation), mineral or memory religions (see Dresh Stone Memory), none (state it). Priests exist where surplus supports them. Holy texts require writing; if oral, say who memorises and the rate of drift. Taboos must be explainable by environment or events.

## Customs checklist
Greeting and hospitality, food rules, funerary rite, marriage rite, coming of age (use `maturity_age`), calendar and festivals (use the project's calendar and seasons), craft and trade ethics, law and punishment, naming ceremony. Tie each to a cause or drop it.

## Population and demographics
Record estimates with a year. Sanity: population growth, famine or plague losses and recovery time (slow breeders recover slowly), migration. Age structure: a short-lived species has a young population; a long-lived species has many adults per child. Army size is at most a few percent of population in pre-industrial settings (about 1 to 3 percent sustained, more briefly). Urban share is low in farming societies without surplus.
