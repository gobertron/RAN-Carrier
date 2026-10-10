# Australis 2030: first Sea Power editor test

This opt-in package is an independent RAN carrier prototype. The packaged
mesh, basic textures and vessel INI are original to this project. It uses a
stock Sea Power Nimitz resource name as a fallback, without copying game
files. It has no RADF, Workshop or F-111N dependency.

The previous Melbourne prototypes caused a Mission Editor load exception.
Close Sea Power before installing, and disable both Melbourne prototypes in
Mod Manager for this isolated test. Leave RADF as it was before.

## Install from the draft branch

In a terminal on the Sea Power computer, run:

```bash
git clone --branch feature/australis-2050-concept \
  https://github.com/gobertron/RAN-Carrier.git "$HOME/Downloads/RAN-Carrier-Australis-test"
python3 "$HOME/Downloads/RAN-Carrier-Australis-test/deliverables/RAN-Carrier-Game-Design/tools/install_australis_2030.py"
```

If the checkout already exists, run
`git -C "$HOME/Downloads/RAN-Carrier-Australis-test" pull --ff-only` before
running the installer. The installer only creates
`Sea Power_Data/StreamingAssets/RAN-Carrier-Australis-2030` and verifies its
files. If that folder already contains different data, it stops safely. To
withdraw the old folder while retaining a verified copy under
`~/Downloads/RAN-Carrier-Australis-2030-backups/`, run:

```bash
python3 "$HOME/Downloads/RAN-Carrier-Australis-test/deliverables/RAN-Carrier-Game-Design/tools/install_australis_2030.py" --remove
```

Then run the first install command again. Do not merge the mod files into
`StreamingAssets/user` or the RADF folder.

## First editor check

1. In Mod Manager enable **RAN Australis 2030 Editor Prototype**. Disable
   **RAN Carrier Original 1959 Prototype** and **RAN Melbourne 1959 Carrier
   Test** if present. Restart Sea Power.
2. Open Mission Editor with a **new blank mission**. Select Australia and the
   carrier/CVN category, with **Hide Anachronistic** off. Search **Australis**.
3. Place one **Australis Test** on the sea. Save and reload the mission. Look
   for the original faceted hull, two islands, offset four H spots, three
   catapult lanes and angled arresting cables.
4. If it loads, test one stock, game-compatible fixed-wing aircraft on a
   catapult and one helicopter on a vertical spot separately. Record whether
   spawn, taxi, launch and recovery work. The air group starts empty.

If the editor hangs or throws an exception, close the game, withdraw this mod
with `--remove`, and provide the latest `Player.log` plus the name of the
section or stack trace. This is the first runtime gate; the static validator
cannot prove that the game accepts every key, geometry or reference.

The 99-aircraft capacity, aircraft deck cycle, working radars, long-range
offensive ECM and retracting laser weapons are later milestones. The offline
3D viewer has a visual laser deployment control, but the game package only
contains closed hatch geometry. Its flag resource remains a stock placeholder
for this editor test.

## Rebuild and check package locally

Building the original mesh requires Python, NumPy and Pillow. Installing the
already built package requires only Python's standard library.

```bash
python3 deliverables/RAN-Carrier-Game-Design/tools/build_australis_2030_mod.py
python3 deliverables/RAN-Carrier-Game-Design/tools/validate_australis_2030_mod.py
```
