# Australis installable builds

## Current: v0.8.2 — lift lighting

- [Standalone installer](install-ran-australis-v0.8.2-lift-lighting.sh)
- [Game package and editable source ZIP](RAN-Carrier-Australis-v0.8.2-Lift-Lighting.zip)
- [SHA256 checksums](SHA256SUMS-v0.8.2.txt)
- [Current model guide](../australis-2030/README.md) and [test/rollback instructions](../australis-2030/GAME-TEST.md)

This release contains four numbered ships, three catapults, four internal lifts, three helicopter pads, five CIWS and five repair teams. It retains the eight-waterjet prototype, configures **Standard 20 kn / Full 30 kn / Flank 30 kn**, and adds eight position-controlled wall lights per lift. The lights work while each platform is below deck and switch off before it closes flush with the flight deck.

The ZIP includes the independent native mod, the project's AnchorChain controller binary/source, rebuild and validation tools, hydrostatic measurements and the preliminary waterjet review. It does not bundle the game, Unity, AnchorChain, Harmony or Workshop assets. An existing compatible AnchorChain installation and the supported game build are required.

### Install

Download the installer to Downloads, close Sea Power, then run:

```bash
bash "$HOME/Downloads/install-ran-australis-v0.8.2-lift-lighting.sh"
```

For a check without installation, append `--check`. The installer prints percentage stages, validates the package/game/dependencies, creates a verified backup before replacement and verifies the installed files. Keep the printed log and backup directory. It leaves stock, Workshop, RADF, User Data, BepInEx and launch options unchanged.

Enable **RAN Australis Fleet v0.8.2 Lift Lighting**, restart and place a fresh carrier in a new blank mission. Use **Standard** for normal flight operations; Full's emergency designation is an operating convention, not an automatic emergency detector. Existing aircraft eligibility, weather, sea-state and deck-conflict checks remain active.

To restore an older installation, close the game and use the backup path printed by the installer:

```bash
bash "$HOME/Downloads/install-ran-australis-v0.8.2-lift-lighting.sh" --restore "/path/to/verified/backup"
```

`--remove` withdraws this independent mod/controller and retains a verified backup. Saved missions can retain old state, so use a fresh unit after installation or restore.

### Validation status

The exported geometry/native bindings, reference catalogue checks and internal reservations pass. The lift-light policy and reflection-integration fixture passes **193 checks**. The transactional installer passes fresh, repeat, upgrade, backup, restore, removal, incompatible-game rejection, corrupt-backup rejection and injected-failure rollback tests. These are isolated software checks; **the latest in-game flight cycle, combat, lift illumination and rough-sea behavior remain untested**.

The 112,000-tonne wet-boundary geometry includes flooded-duct deductions. Real waterjet performance, cavitation, structures, loading and full stability are unresolved. The 30-knot setting is a game target, not a proven physical result. Read the [engineering review](../WATERJET-ENGINEERING-REVIEW.md) before interpreting the waterjet study.

## Archived prototypes

The following files are retained as historical snapshots. Their counts, layouts and CIWS timings describe those older packages and do not describe v0.8.2. They should not be mixed with the current native files.

| Archive | Historical contents |
|---|---|
| [RAN-Carrier-Australis-2030-2026-10-24.zip](RAN-Carrier-Australis-2030-2026-10-24.zip) | Earlier independent 38-file native mod, installer and SHA256 inventory; source `e04142174e9e3ee41dd5b5dcf85d385133de5cf3`, model revision `64724edac9bc` |
| [RAN-Carrier-Australis-2030-CIWS-2026-10-24.zip](RAN-Carrier-Australis-2030-CIWS-2026-10-24.zip) | Earlier 39-file native engagement-driven CIWS study; 0.4 s opening and 1 s closing after its native idle/rest condition; source `6bd0366bde6667178909198f43b0ed68c24c355f` |
| [RAN-Carrier-Australis-v0.5.1-Five-Repair-Teams.zip](RAN-Carrier-Australis-v0.5.1-Five-Repair-Teams.zip) | Recoverable v0.5.1 five-team source/package baseline used during reconstruction |

These archives passed their recorded static/isolated installer checks when produced; no new in-game testing is implied. The v0.8.2 recovery line reconstructs later requested features from the recoverable source and subsequent instructions. It is not a byte-for-byte restoration of the lost v0.6.0 installer.
