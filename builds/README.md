# Australis installable builds

## Current: v0.8.5 — Naval Details

## Naval details in v0.8.5

Hull numbers **91–94** are enlarged on the flight deck and both main-island sides and aligned to their model surfaces. The shared native class still selects the matching number atlas for each named ship. Both bridge structures receive individual framed naval-style windows, with consistent sill heights and mullions on their actual raked faces. Watertight-style doors use raised coamings, rounded corners, hinges, dogs and handles aligned to the supporting surface.

The deck number panel is **10.8 × 8.8 m**, with an approximately **8.44 × 6.53 m** painted glyph. Both port and starboard main-island panels are **9.6 × 5.6 m**, with approximately **7.69 × 4.20 m** glyphs. The panels follow their actual supporting planes with a small surface offset; the enlarged island markings sit between the lower access doors and bridge glazing.

These fittings are original decorative model geometry; they do not create functioning doors or establish watertight integrity, ballistic protection or naval-design certification. Their appearance, texture orientation and visibility still need an in-game check. The change retains the preceding hull, waterjet, class-list and flight-deck configuration.

- [Download the v0.8.5 offline installer](install-ran-australis-v0.8.5-naval-details-offline.sh?raw=1)
- [Download the same source and mod as a ZIP](RAN-Carrier-Australis-v0.8.5-Naval-Details.zip?raw=1) · [SHA256 checksums](SHA256SUMS-v0.8.5.txt)
- [v0.8.5 release notes](../australis-2030/releases/v0.8.5/README.md)
- [Current model guide](../australis-2030/README.md), [four-ship 3D viewer](../australis-2030/viewer/Australis-v0.8.5-Fleet-3D.html) and [test/rollback instructions](../australis-2030/GAME-TEST.md)

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

[Download the v0.8.5 offline installer](install-ran-australis-v0.8.5-naval-details-offline.sh?raw=1). It contains the complete verified package and editable source and requires Python 3; no internet connection is needed after download, and no earlier installer is required. The smaller [network installer](install-ran-australis-v0.8.5-naval-details.sh?raw=1) is an alternative that requires an internet connection and reconstructs the same verified release file manifest.

The earlier **v0.8.3 stock-catalogue fix is included**. It addresses the installer stopping at 40% with `section '---------- Surface ships ----------' already exists` in Sea Power's stock `systems/sensors.ini`. Earlier attempts stopped before replacement, so they left the old installation in place. The corrected dependency check inventories stock section names, tolerates repeated catalogue dividers and values, and leaves the original game files untouched. Our own mod INIs remain strict; missing actual systems, ammunition and dependencies still stop installation.

Automated installer regression tests pass with the repeated divider at line 624, including replacement of an older fixture installation and verified restore/rollback. Missing required profiles and ammunition still stop before changes. Live installation and in-game confirmation remain pending.

The v0.8.5 viewer uses the current exported OBJ and INI geometry. Hull-number appearance is projected from the same per-variant PNG atlas used by the game. Preview texture sampling and studio shading are approximations; they do not simulate Unity lighting, the Mission Editor or native flight scheduling. All four variants use the common current mesh, with lifts at their 22.002 m upper home stop.

This release contains four numbered ships, three catapults, four internal lifts, three helicopter pads, five CIWS and five repair teams. It retains the eight-waterjet prototype, configures **Standard 20 kn / Full 30 kn / Flank 30 kn**, and retains eight position-controlled wall lights per lift. The lights work while each platform is below deck and switch off before it closes flush with the flight deck.

The complete offline release includes the independent native mod, the project's AnchorChain controller binary/source, rebuild and validation tools, hydrostatic measurements and the preliminary waterjet review. It does not bundle the game, Unity, AnchorChain, Harmony or Workshop assets. An existing compatible AnchorChain installation and the supported game build are required.

### Install

Close Sea Power, download the complete offline installer above into Downloads, then run:

```bash
bash "$HOME/Downloads/install-ran-australis-v0.8.5-naval-details-offline.sh"
```

Alternatively, download the smaller [network installer](install-ran-australis-v0.8.5-naval-details.sh?raw=1); it requires Python 3 and an internet connection:

```bash
bash "$HOME/Downloads/install-ran-australis-v0.8.5-naval-details.sh"
```

Confirm **100%** and `installed package hashes verified` before starting the game. For a check without installation, append `--check`. The installer prints percentage stages, validates the package/game/dependencies, creates a verified backup before replacement and verifies the installed files. Keep the printed log and backup directory. It leaves stock, Workshop, RADF, User Data, BepInEx and launch options unchanged.

After verifying the installed hashes, the installer prints `[VERIFIED] RAN Australis Fleet v0.8.5 Naval Details` so you can identify the exact release. It also scans local mod folders and the Sea Power Workshop directory for competing copies of the same carrier vessel definitions. Each match is listed as `[OTHER COPY]` with its folder path; disable older Australis copies in the game mod menu. The diagnostic does not delete or change those copies. An unreadable folder produces a note that the scan was incomplete without invalidating the verified installation.

Enable **AnchorChain** and **RAN Australis Fleet v0.8.5 Naval Details**, disable older Australis entries, restart Sea Power and place a fresh carrier in a new blank mission. Use **Standard** for normal flight operations; Full's emergency designation is an operating convention, not an automatic emergency detector. Existing aircraft eligibility, weather, sea-state and deck-conflict checks remain active.

To restore an older installation, close the game and use the backup path printed by the installer:

```bash
bash "$HOME/Downloads/install-ran-australis-v0.8.5-naval-details-offline.sh" --restore "/path/to/verified/backup"
```

`--remove` withdraws this independent mod/controller and retains a verified backup. Saved missions can retain old state, so use a fresh unit after installation or restore.

### Validation status

The carried-forward geometry/native bindings and internal reservations pass. The stock-catalogue regression cases pass with the exact repeated divider at line 624, duplicate stock values and commented fake headers. Negative tests confirm rejection of missing required profiles/ammunition and duplicate authored INIs. The lift-light policy and reflection-integration fixture passes **193 checks**. The transactional installer passes fresh, repeat, upgrade, backup, restore, removal, incompatible-game rejection, corrupt-backup rejection and injected-failure rollback tests. These are isolated software checks; **the latest in-game flight cycle, combat, lift illumination and rough-sea behavior remain untested**.

The 112,000-tonne wet-boundary geometry includes flooded-duct deductions. Real waterjet performance, cavitation, structures, loading and full stability are unresolved. The 30-knot setting is a game target, not a proven physical result. Read the [engineering review](../WATERJET-ENGINEERING-REVIEW.md) before interpreting the waterjet study.

## Archived prototypes

The following files are retained as historical snapshots. Their counts, layouts and CIWS timings describe those older packages and do not describe the current carrier build. They should not be mixed with the current native files.

| Archive | Historical contents |
|---|---|
| [v0.8.4 release notes](../australis-2030/releases/v0.8.4/README.md) | Consolidated class list and upper-home flight-deck/lift correction, retained in v0.8.5. |
| [v0.8.3 release notes](../australis-2030/releases/v0.8.3/README.md) | Stock-catalogue installer fix; separate vessel definitions retained the extra year submenus. Superseded by v0.8.4. |
| [v0.8.2 ZIP](RAN-Carrier-Australis-v0.8.2-Lift-Lighting.zip) · [installer](install-ran-australis-v0.8.2-lift-lighting.sh) · [checksums](SHA256SUMS-v0.8.2.txt) | Immutable lift-lighting release; its stock-catalogue precheck can stop on repeated divider headings. Use the supplied current offline installer for installation. |
| [RAN-Carrier-Australis-2030-2026-10-24.zip](RAN-Carrier-Australis-2030-2026-10-24.zip) | Earlier independent 38-file native mod, installer and SHA256 inventory; source `e04142174e9e3ee41dd5b5dcf85d385133de5cf3`, model revision `64724edac9bc` |
| [RAN-Carrier-Australis-2030-CIWS-2026-10-24.zip](RAN-Carrier-Australis-2030-CIWS-2026-10-24.zip) | Earlier 39-file native engagement-driven CIWS study; 0.4 s opening and 1 s closing after its native idle/rest condition; source `6bd0366bde6667178909198f43b0ed68c24c355f` |
| [RAN-Carrier-Australis-v0.5.1-Five-Repair-Teams.zip](RAN-Carrier-Australis-v0.5.1-Five-Repair-Teams.zip) | Recoverable v0.5.1 five-team source/package baseline used during reconstruction |

These archives passed their recorded static/isolated installer checks when produced; no new in-game testing is implied. The v0.8.2 recovery line reconstructs later requested features from the recoverable source and subsequent instructions. It is not a byte-for-byte restoration of the lost v0.6.0 installer.
