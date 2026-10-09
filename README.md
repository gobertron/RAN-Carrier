# Royal Australian Navy carrier game design — 8 October 2026

Fourteen original Sea Power carrier **designs** covering every edition in the brief. The models and gameplay figures are proposals for an alternate-history RAN fleet. One independent 1959 prototype is now packaged for an in-game registration and deck test; its appearance and flight operations have not yet been verified in Sea Power.

## Original Melbourne 1959 integration milestone

`game-mod/RAN-Carrier-Original-1959/` is a separate local mod with our own carrier OBJ, authored material textures, vessel INI, variants and name entry. It has **no RADF or other Workshop dependency**. It uses only Sea Power's built-in Australian flag and visual optics. The unique game unit ID is `ran_cv_melbourne_1959`; the editor name is **Melbourne 1959 RAN design → Melbourne R21 Original** under **Australia → Light Carrier**.

The prototype defines a 30-aircraft capacity, two lift positions, two bow launch lanes, a helicopter spot, an angled recovery lane, taxi routes and physical colliders. Its air group is intentionally empty while we identify suitable game-native 1950s aircraft. The deck routes, model appearance, combat systems and launch/recovery have not passed in-game QA. The visible radar, AA and sonar fittings on the model are geometry; only basic visual optics are enabled as a sensor in this milestone.

### 9 October rudder-mount correction

The first installed prototype was enabled when the Mission Editor stopped with `SeaPower.VesselRudderSystem.init()` and a `NullReferenceException`. RADF had loaded the editor successfully before our prototype was added, so our carrier is the leading suspect; the stack trace does not name the ship and cannot prove the exact cause. A review of this package against working carrier examples found that our rudder and propellers were listed twice in `[Submodels]`. The corrected package lists each only under `MainSystems`, gives each a local-origin mesh and an explicit pivot. This change is format-checked locally but **has not been confirmed in Sea Power**.

For Aram's installed first release, download the standalone `tools/fix_ran_carrier_original_1959.py` to `~/Downloads` and run `python3 ~/Downloads/fix_ran_carrier_original_1959.py` with Sea Power closed. It carries the three corrected files inside the script; no ZIP or extra package is needed. It verifies the exact original 25-file installation, makes a verified backup in `~/Downloads/RAN-Carrier-Original-1959-backups`, and changes only our mod. It is safe to run again; unknown edits are refused. After it reports 100%, leave RADF enabled as before and restart the game.

Alternatively, from an updated repository checkout, run `python3 tools/install_original_melbourne_1959.py --upgrade` with Sea Power closed. It has the same exact-release check and backup protection. Keep the previously working RADF setup as it was, leave the old Melbourne Test disabled, and enable the corrected prototype. Fully restart the game and open a new blank mission in the editor. If it still fails, disable **only our prototype**, restart, and confirm the editor works with RADF as before. Capture the current game log if our prototype causes a repeatable failure.

To install from a repository checkout or extracted ZIP on Aram's CachyOS machine:

1. Close Sea Power. Undo the earlier registration bridge with `python3 ~/Downloads/bridge-ran-melbourne-1959.py --undo`. This restores User Data from its backup and leaves RADF untouched.
2. From the repository root, run `python3 tools/install_original_melbourne_1959.py` for the first install, or add `--upgrade` for the exact first release. The installer copies the self-contained `game-mod/RAN-Carrier-Original-1959` folder directly under the game's `Sea Power_Data/StreamingAssets` directory. It refuses to replace an unrecognised or edited folder.
3. Enable **RAN Carrier Original 1959 Prototype** in the Mod Manager and leave **RAN Melbourne 1959 Carrier Test** disabled. Keep the previously working RADF setting as it was; the new carrier does not reference its files. Accept changes and fully restart Sea Power.
4. In the Mission Editor, set Australia and open Light Carrier with Hide Anachronistic off. Report whether **Melbourne 1959 RAN design** appears. If it does, place **Melbourne R21 Original** and inspect its appearance. Flight operations are the next milestone.

`python3 tools/build_melbourne_1959_mod.py` regenerates the package from the original game-scale design OBJ. It renames the authoring mesh `FlightDeck` to `Deck` to avoid colliding with the `[FlightDeck]` gameplay section, adds original propeller/rudder primitives and generates simple self-authored material textures. `python3 tools/validate_melbourne_1959_mod.py` checks references and INI structure locally. Neither script reads or writes any Workshop installation.

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

The next native integration step is to confirm that the first original prototype appears in the editor, inspect its placement and deck geometry, then assign source-verified game-native aircraft IDs and test launch and recovery. Source design geometry may require reshaping for physically safe deck cycles. No in-game flight, radar, sonar, ECM or laser tests have been claimed.

## Source notes

- Sea Power carrier INI format, navigation fields and ECM key names were checked against the local Project Southern Cross examples supplied earlier in this conversation. They are used as schema reference only.
- The [Project Southern Cross Workshop page](https://steamcommunity.com/sharedfiles/filedetails/?id=3574957049) credits Peter Garrett. Specific third-party models would require their own permission and contributor checks if incorporated later.
