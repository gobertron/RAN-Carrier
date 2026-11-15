# RAN / HMAS Australis — Sea Power

Alternate-history Royal Australian Navy aircraft carrier development for *Sea Power: Naval Combat in the Missile Age*.

**[Complete Australis version-and-changes table](docs/AUSTRALIS_VERSION_HISTORY.md)** · [CSV](docs/AUSTRALIS_VERSION_HISTORY.csv) · [All saved artifacts](docs/AUSTRALIS_ARTIFACT_INDEX.md)

Documentation reconciled **15 November 2026**. The record covers the early concepts, recovery builds, v0.8.x–v0.10.x evolution and Windows 11 packages through **v1.2.8**. Current operating-system target: **Windows 11**.

| Record | Version / location | Meaning |
|---|---|---|
| Latest documented delivery | v1.2.8 — In-Game Info Sheet | Adds Mod Manager and ship encyclopedia descriptions; updater, not a full carrier archive. |
| Latest source/build tracked in GitHub | [v0.8.5 on the Australis development branch](https://github.com/gobertron/RAN-Carrier/tree/feature/australis-2050-concept) | The later packages are catalogued here but their implementation binaries have not been uploaded by this documentation update. |
| Default branch | Original fleet concepts plus this history | The design files below are historical proposals, not the v1.2.8 game model. |

## Recent Windows deliveries

| Version | What changed | Package scope |
|---|---|---|
| v1.2.8 | In-game carrier info sheet in Mod Manager and ship encyclopedia. | Updater; retains v1.2.7 controller repair. |
| v1.2.7 | Controller startup/preloader timing repair for CIWS6, ICCS and weapon-bay operation. | Repair updater; live mechanism retest not confirmed. |
| v1.2.6 | Catalogue expanded to all stock aircraft categories. | Updater; listing does not prove every aircraft can launch/land. |
| v1.2.5 | Detection fixes for legacy model names, paths and missing runtime inventory. | Archive/update tool. |
| v1.2.4 | Carrier-capable, VTOL and helicopter catalogue expansion. | Archive/update tool. |
| v1.2.3 | Task-lighting correction and archive/update workflow. | Separate lighting patch and updater packages. |
| v1.2.2 | Captures compatibility evidence for the installed game assemblies. | Read-only checker, not a model update. |
| v1.2.1 | Full Restore installer hardening and checks. | Full embedded package; one recorded install stopped before writes on assembly mismatch. |
| v1.2.0 | Restored the complete v0.10.26 requirements baseline. | Full Restore package; night 3D view is a separate preview. |
| v1.1.0 | Flight Deck Stage 1 build from the Basic Shell. | Test package; later notes report landing failure. |
| Basic Shell v1.0 / installer v1.0.1–v1.0.2 | Reduced baseline and Windows bootstrap/installer revisions. | Installer version and model version are separate labels. |

The [full table](docs/AUSTRALIS_VERSION_HISTORY.md) records exact packages, prerequisites, recovered source evidence and history gaps. Historical Linux installers, previews and diagnostics are labelled separately. No live game pass or Steam publication is inferred from installation or offline checks.

## Original fleet design archive

The following preserves the repository's 8 October fleet-design documentation. Its systems, aircraft totals and next steps describe that original design snapshot.

### Royal Australian Navy carrier game design — 8 October 2026

Fourteen original Sea Power carrier **designs** covering every edition in the brief. The models and gameplay figures are proposals for an alternate-history RAN fleet. They are not tested as a playable mod.

| Era | Proposed class | Propulsion | Aircraft | Offensive ECM | Laser |
|---|---|---|---:|---|---|
| 1940s early | Endeavour | Steam | 30 | — | — |
| 1940s late | Sydney | Steam | 30 | — | — |
| 1950s early | Melbourne | Steam | 30 | — | — |
| 1950s late | Melbourne | Steam | 30 | — | — |
| 1960s early | Australia | Steam | 68 | — | — |
| 1960s late | Federation | Nuclear | 68 | — | — |
| 1970s early | Federation | Nuclear | 69 | 1 shipboard | — |
| 1970s late | Canberra | Nuclear | 69 | 1 shipboard | — |
| 1980s early | Commonwealth | Nuclear | 98 | 1 shipboard | — |
| 1980s late | Commonwealth | Nuclear | 98 | 1 shipboard | — |
| 1990s early | Commonwealth | Nuclear | 98 | 1 shipboard | — |
| 2000s early | Southern Cross | Nuclear | 98 | 1 shipboard | — |
| 2000s late | Southern Cross | Nuclear | 98 | 1 shipboard | — |
| 2020s early | Australis | Nuclear | 99 | 1 shipboard | 4 mounts (concept) |

Each edition has a separate design sheet with the proposed air group, dated combat systems and hull dimensions. `design-manifest.json` provides machine-readable values, including a single carrier-mounted offensive ECM module from 1972 onward. ECM uses no aircraft slots and there is no EF-111N-2050 aircraft. The 2023 hull has four visible laser mount studies; beam weapon logic and effects need implementation and testing.

`metre-source-models/` holds the original OBJ/MTL authoring coordinates. `game-scale-models/ships/` holds approximately scaled copies using one observed Sea Power OBJ reference ratio, with the same object groups (Hull, FlightDeck, elevators, catapult markings, ECM and laser mounts). `previews/` are geometry renders, not screenshots. `generate_source_models.py` rebuilds the original metre models from `fleet-source.json` with Python, NumPy and Pillow; `rebuild_game_scale.py` recreates the approximate game-scale OBJ copies from the packaged metre sources. The design manifest remains the editable source of the gameplay proposals.

`draft-ini/` has Sea Power-shaped **reference templates**, including eight original ECM sensor profiles with native-style `Kind=ECM` and `Type=Offensive` fields. The files deliberately end in `.draft.ini`. Do not copy them into the live game's `StreamingAssets/user` tree. They omit engine-required taxi paths, launch/recovery points, collision, animations, damage models, materials, aircraft IDs, weapon mounts, sonar routing and an operational laser. Ship propulsion labels are design requirements; the game's native nuclear-power type remains to be confirmed. Numeric ECM performance is proposed game balance, constrained in practice by jamming and horizon calculations.

The 1944–1959 light fleet series follows British wartime light-carrier design cues. The 1963–1993 hulls draw from US conventional and nuclear supercarrier lineages but have newly authored Australian silhouettes and fittings. The 2002–2023 Southern Cross and Australis hulls have distinct Australian decks, islands and sensor/weapon outlines. No third-party hull geometry, textures or INIs are included. `CREDITS.md` records the provenance of the one external scale reference.

The next native integration step is to inspect the **actual installed** carrier definitions and load order, map source aircraft IDs, then build lift, taxi, launch and recovery routes against each final mesh. The 5.21 GiB carrier-source archive in Drive was not accessible through the connector's 256 MiB download cap at the time this package was built. The smaller review ZIPs requested from that archive can ground donor selection and creator credits. Source design geometry may require reshaping for physically safe deck cycles. No in-game flight, radar, sonar, ECM or laser tests have been claimed.

## Source notes

- Sea Power carrier INI format, navigation fields and ECM key names were checked against the local Project Southern Cross examples supplied earlier in this conversation. They are used as schema reference only.
- The [Project Southern Cross Workshop page](https://steamcommunity.com/sharedfiles/filedetails/?id=3574957049) credits Peter Garrett. Specific third-party models would require their own permission and contributor checks if incorporated later.

