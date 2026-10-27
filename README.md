# Royal Australian Navy carrier game design

## Current release: Australis v0.8.5 — Naval Details

An original alternate-history carrier prototype for **Sea Power**, supplied as four numbered ships: **HMSCS Australis 91, Southern Cross 92, Federation 93 and Commonwealth 94**. The active build is experimental: geometry, configuration and installer checks pass; the latest version still needs an in-game flight, combat and lighting trial.

[Download the v0.8.5 offline installer](builds/install-ran-australis-v0.8.5-naval-details-offline.sh?raw=1) · [Four-ship 3D viewer](australis-2030/viewer/Australis-v0.8.5-Fleet-3D.html?raw=1) · [Release notes](australis-2030/releases/v0.8.5/README.md) · [Install/test/rollback](australis-2030/GAME-TEST.md)

### Naval details in v0.8.5

Hull numbers **91–94** are enlarged on the flight deck and both main-island sides and aligned to their model surfaces. The shared native class still selects the matching number atlas for each named ship. Both bridge structures receive individual framed naval-style windows, with consistent sill heights and mullions on their actual raked faces. Watertight-style doors use raised coamings, rounded corners, hinges, dogs and handles aligned to the supporting surface.

The deck number panel is **10.8 × 8.8 m**, with an approximately **8.44 × 6.53 m** painted glyph. Both port and starboard main-island panels are **9.6 × 5.6 m**, with approximately **7.69 × 4.20 m** glyphs. The panels follow their actual supporting planes with a small surface offset; the enlarged island markings sit between the lower access doors and bridge glazing.

These fittings are original decorative model geometry; they do not create functioning doors or establish watertight integrity, ballistic protection or naval-design certification. Their appearance, texture orientation and visibility still need an in-game check. The change retains the preceding hull, waterjet, class-list and flight-deck configuration.

**The v0.8.4 class-list correction is retained: one Australis-class entry**, using four native ship variants rather than four separate class definitions. This is intended to remove the extra “2025” submenus shown in the earlier build. The target Mission Editor list is:

| Class | Selectable ship |
|---|---|
| Australis-class | HMSCS Australis 91 |
| Australis-class | HMSCS Southern Cross 92 |
| Australis-class | HMSCS Federation 93 |
| Australis-class | HMSCS Commonwealth 94 |

The variants share the hull and use native per-variant number textures on deck- and island-coloured panels. Hull shape, propulsion settings and the compiled v0.8.2 deck controller are retained. The v0.8.4 lift-home state and taxi-route corrections are retained as described below. **The class-list presentation and number-panel appearance still need confirmation in the live game.**

Older missions that reference the former Southern Cross, Federation or Commonwealth vessel IDs need those ships re-placed from **Australis-class**. The installer retains a verified backup; it does not edit saved missions.

The flight-deck correction sets each lift's idle/home stop to flight-deck level: `StartsLowered=False`, `CloseDoorsAfterTaxi=False`, with the initial platform at **Y=22.002 m**. The native system lowers a lift on demand and returns it to the upper home stop after launch or recovery. The v0.8.3 lower-home setting conflicted with the native post-taxi upper state, which could leave `IsBusy` permanently true and prevent another aircraft cycle.

All four lifts now have fixed-wing routes: **12 lift-to-catapult routes, four arrested-recovery-to-lift routes, three helicopter launch routes and three helicopter recovery routes — 22 taxi routes in total**. The three dedicated pads accept **Helicopter** only; carrier-capable VTOL/STOL aircraft use the catapult and arrested-recovery paths. Native interlocks remain active. Fixed-wing recovery conservatively blocks all six launch points, so conflicting operations queue.

A state simulation derived from the supplied game IL passes **20 launch/recovery cycles on each of four lifts**. This checks the native lift-state transitions; live Sea Power flight cycles and Unity appearance remain to be confirmed. The compiled v0.8.2 deck controller is retained.

The earlier **v0.8.3 stock-catalogue fix is included**. It addresses the installer stopping at 40% with `section '---------- Surface ships ----------' already exists` in Sea Power's stock `systems/sensors.ini`. Earlier attempts stopped before replacement, so they left the old installation in place. The corrected dependency check inventories stock section names, tolerates repeated catalogue dividers and values, and leaves the original game files untouched. Our own mod INIs remain strict; missing actual systems, ammunition and dependencies still stop installation.

Automated installer regression tests pass with the repeated divider at line 624, including replacement of an older fixture installation and verified restore/rollback. Missing required profiles and ammunition still stop before changes. Live installation and in-game confirmation remain pending.

The v0.8.5 viewer uses the current exported OBJ and INI geometry. Hull-number appearance is projected from the same per-variant PNG atlas used by the game. Preview texture sampling and studio shading are approximations; they do not simulate Unity lighting, the Mission Editor or native flight scheduling. All four variants use the common current mesh, with lifts at their 22.002 m upper home stop.

[Download the v0.8.5 offline installer](builds/install-ran-australis-v0.8.5-naval-details-offline.sh?raw=1). It contains the complete verified package and editable source and requires Python 3; no internet connection is needed after download, and no earlier installer is required. The smaller [network installer](builds/install-ran-australis-v0.8.5-naval-details.sh?raw=1) is an alternative that requires an internet connection and reconstructs the same verified release file manifest.

Close Sea Power, download the complete offline installer above into Downloads, then run:

```bash
bash "$HOME/Downloads/install-ran-australis-v0.8.5-naval-details-offline.sh"
```

Alternatively, download the smaller [network installer](builds/install-ran-australis-v0.8.5-naval-details.sh?raw=1); it requires Python 3 and an internet connection:

```bash
bash "$HOME/Downloads/install-ran-australis-v0.8.5-naval-details.sh"
```

Wait for **100%** and `installed package hashes verified`. Enable **AnchorChain** and **RAN Australis Fleet v0.8.5 Naval Details**, disable older Australis entries, restart Sea Power, and place a fresh carrier in a new mission. A `[STOP]` is an unsuccessful installation; retain its printed log.

![Australis v0.8.5 model render](australis-2030/previews/Australis-v0.8.5-Full-Ship.png)

[Open the v0.8.5 four-ship 3D viewer](australis-2030/viewer/Australis-v0.8.5-Fleet-3D.html) · [Current viewer alias](australis-2030/viewer/australis_2030_3d.html). Open the self-contained HTML locally; GitHub's file view does not run the model viewer. The model has an empty air group for user-selected aircraft. Renders show the exported model, not gameplay screenshots.


### Current arrangement

| Feature | Current carrier configuration |
|---|---|
| Overall length / flight-deck width | 370 m / 82 m |
| Waterline length / maximum beam / draft | 362.6 m / 41 m / 11.5 m |
| Displacement | 112,000 t native target; approximately 112,000.07 t net geometric wet-boundary result |
| Aviation | Three catapults: two bow, one port waist; angled arrested recovery |
| Lifts | Four internal 22 × 26 m platforms; all four have fixed-wing routes and idle at flight-deck level |
| Helicopter pads | Three helicopter-only pads; preference aft, front, then middle |
| Air group / personnel | 99-aircraft design target; 5,300 embarked target and 5,800 planning berths |
| Hangar | 280 × 50 × 8 m reservation; 36 folded reference parking slots |
| Defence | Five retractable CIWS, two 30 mm guns, 80 VLS cells and five repair teams |
| Propulsion appearance | Eight waterjets: four outer steering nozzles and four fixed boosters |
| Normal aviation / emergency speed orders | Standard 20 kn / Full 30 kn; Flank also capped at 30 kn |

Carrier-capable aircraft are discovered without a carrier-specific class, size, role or loadout whitelist. The aircraft and its squadron definitions must be correctly installed. Eligibility does not establish swept-clearance compatibility for every add-on. Shared taxi lanes, lifts, recovery corridors and defensive-bay interlocks still govern operations.

The forward CIWS is clear of the bow catapult at the corrected port-side position. The five CIWS and other defensive equipment use covered bays controlled by the bundled AnchorChain add-on: deploy after committed aviation clears in 0.75 simulation seconds, hold for 300 seconds after the last actual shot, then stow over 10 seconds. Aviation remains locked until stowed. The five repair teams use the native damage-control setting.

The current VLS stores include **40 stock RIM-66E SAM proxy rounds and 40 RIM-7M Sea Sparrows**. These retain stock guidance and performance. They are not an SM-6 implementation, and no ballistic-missile interception capability is claimed. Nulka and laser positions remain visual studies; a raised laser demonstration is not an operational laser weapon.

### Lift-wall lighting

Eight recessed warm-white work lights serve each shaft, **32 total**, on its existing outer, forward and aft walls. Each lift's actual platform height controls its own lights, during both day and night. They fade out within the final 0.60 m of upward travel and are fully off within 0.10 m of the deck-level stop. Downward spotlight cones and non-emissive lenses avoid a permanently glowing closed lift.

![Australis v0.8.4 lift-wall lighting cutaway](australis-2030/previews/Australis-v0.8.4-Lift-Cutaway.png)

The cutaway uses actual model geometry with **illustrative lamp shading**, not Unity or in-game rendering. Native lift movement takes six seconds between the lower and flight-deck levels. The controller's 193 lighting-policy and reflection-integration checks pass; an in-game visual check remains necessary.

### Engineering and implementation limits

The eight intake mouths, open transom bores and connected internal wet ducts are actual mesh openings. The hull is recalibrated after deducting approximately **900.40 m³** of flooded duct volume. This is a geometric hydrostatic check using an assumed planning CG, not a complete weight-centre or stability assessment.

Sea Power uses its aggregate conventional propulsion model for this prototype. The eight internal impellers and four steering assemblies have native moving bindings; independent jet thrust, booster staging, reverse-bucket actuation and eight physical jet wakes are not simulated. The existing **280,000 hp (about 208.8 MW)** setting and 30-knot maximum are retained. Real 30-knot capability is unresolved: the preliminary resistance sensitivity spans approximately 99–310 MW under its stated assumptions. CFD, cavitation, actual machinery weights, structural design and full intact/damage stability have not been validated.

See the [current project guide](australis-2030/README.md), [design basis](australis-2030/DESIGN-BASIS.md) and [engineering review](WATERJET-ENGINEERING-REVIEW.md). Geometry/native-reference checks and transactional installer tests cover fresh installation, repeat installation, upgrade, backups, restore, removal, rejected incompatible game versions and failure rollback. These checks do not establish in-game aircraft cycles or seaworthiness.

The installer requires an existing compatible AnchorChain installation and the supported game build. It replaces only the independent Australis mod/controller, retains a verified backup and leaves stock, Workshop, RADF, User Data, BepInEx and launch options unchanged. Close Sea Power before installing; restart and test a fresh carrier in a new mission. [Build history](builds/README.md) separates the current release from archived prototypes.

## Earlier fleet studies

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

Each edition has a separate design sheet with the proposed air group, dated combat systems and hull dimensions. `design-manifest.json` provides machine-readable values, including a single carrier-mounted offensive ECM module from 1972 onward. ECM uses no aircraft slots and there is no carrier-dedicated EF-111N aircraft. The 2023 hull has four visible laser mount studies; beam weapon logic and effects need implementation and testing.

`metre-source-models/` holds the original OBJ/MTL authoring coordinates. `game-scale-models/ships/` holds approximately scaled copies using one observed Sea Power OBJ reference ratio, with the same object groups (Hull, FlightDeck, elevators, catapult markings, ECM and laser mounts). `previews/` are geometry renders, not screenshots. `generate_source_models.py` rebuilds the original metre models from `fleet-source.json` with Python, NumPy and Pillow; `rebuild_game_scale.py` recreates the approximate game-scale OBJ copies from the packaged metre sources. The design manifest remains the editable source of those earlier gameplay proposals. The active Australis 2030 build uses its own source and specification in `australis-2030/`.

`draft-ini/` has Sea Power-shaped **reference templates**, including eight original ECM sensor profiles with native-style `Kind=ECM` and `Type=Offensive` fields. The files deliberately end in `.draft.ini`. Do not copy them into the live game's `StreamingAssets/user` tree. They omit engine-required taxi paths, launch/recovery points, collision, animations, damage models, materials, aircraft IDs, weapon mounts, sonar routing and an operational laser. Ship propulsion labels are design requirements; the game's native nuclear-power type remains to be confirmed. Numeric ECM performance is proposed game balance, constrained in practice by jamming and horizon calculations.

The 1944–1959 light fleet series follows British wartime light-carrier design cues. The 1963–1993 hulls draw from US conventional and nuclear supercarrier lineages but have newly authored Australian silhouettes and fittings. The 2002–2023 Southern Cross and Australis hulls have distinct Australian decks, islands and sensor/weapon outlines. No third-party hull geometry, textures or INIs are included. `CREDITS.md` records the provenance of the one external scale reference.

The Australis editor test uses the supplied smaller reference archives of stock Forrestal/Nimitz and Workshop carrier INIs to map lifts, taxi, launch and recovery sections against the original Australis mesh. The supplied Sea Power copy was used to inspect `Seapower-Scripts.dll` and trace the rudder loading error; game binaries and third-party assets are not included here. The prototype leaves its air group empty for user-selected aircraft and now includes a declared stock-compatible combat trial. Source design geometry may require reshaping for physically safe deck cycles. No in-game flight, radar, sonar, ECM or laser tests have been claimed.

## Source notes

- The current original source, exported native fleet and controller are in `australis-2030/`, `game-mod/RAN-Carrier-Australis-2030/` and `addon/DeckController/`.
- The supplied game assembly was inspected privately to verify native loading, telegraph speeds, aircraft operations and mount behavior. It is not redistributed.
- [CREDITS.md](CREDITS.md) records scale references, third-party runtime dependencies and the distinction between concept art and actual model renders.
