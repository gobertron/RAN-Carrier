# Australis v0.8.5 — Naval Details

27 October 2026. This release enlarges the four ships' hull numbers and replaces the window and door detailing with original naval-style fittings aligned to the actual model surfaces.

## Changed

- Enlarged **91, 92, 93 and 94** markings retain native per-variant number textures on the shared Australis-class hull.
- Individual framed windows follow both the main bridge and aft aviation bridge faces, with consistent sills and mullions.
- Watertight-style doors have rounded coamings, hinges, dogs and handles placed against their supporting island or hull face.
- Current 3D views use the exported game geometry and the same number PNG atlases as the installed variants. Texture sampling and studio shading are preview approximations, not Unity rendering.

The fittings are decorative geometry. They do not add operational door animations, actual watertight closures, protected glazing or naval-design certification. The class list, number textures and live-game appearance remain trial checks.

The deck number panel is **10.8 × 8.8 m**, with an approximately **8.44 × 6.53 m** painted glyph. Both port and starboard main-island panels are **9.6 × 5.6 m**, with approximately **7.69 × 4.20 m** glyphs. The panels follow their actual supporting planes with a small surface offset; the enlarged island markings sit between the lower access doors and bridge glazing.

## Retained

One **Australis-class** entry contains HMSCS Australis 91, Southern Cross 92, Federation 93 and Commonwealth 94. All four lifts idle at **22.002 m** and use the native lower-on-demand/return-upper cycle. They have fixed-wing routes to all three catapults; the three rear pads are **helicopter-only**. The 22 taxi routes, five repair teams, eight-waterjet hull, Standard 20 kn / Full 30 kn speed profile and 32 lift-wall lights are retained. The compiled deck controller remains v0.8.2.

The repeated stock catalogue heading correction is included. Missing actual dependencies still stop installation, and authored INIs remain strictly checked. Older missions that reference the retired Southern Cross, Federation or Commonwealth vessel IDs need those ships re-placed from the consolidated class. Saved missions are not rewritten.

## Install and inspect

[Download the v0.8.5 offline installer](../../../builds/install-ran-australis-v0.8.5-naval-details-offline.sh?raw=1), save it in Downloads, close Sea Power and run:

```bash
bash "$HOME/Downloads/install-ran-australis-v0.8.5-naval-details-offline.sh"
```

The complete offline installer requires Python 3 and verifies its embedded package. Alternatively, download the smaller [network installer](../../../builds/install-ran-australis-v0.8.5-naval-details.sh?raw=1); it requires an internet connection and reconstructs the same verified release:

```bash
bash "$HOME/Downloads/install-ran-australis-v0.8.5-naval-details.sh"
```

Wait for **100%** and `installed package hashes verified`. Enable **AnchorChain** and **RAN Australis Fleet v0.8.5 Naval Details**, disable older Australis entries, restart and place a fresh carrier. The installer retains a verified previous-build backup and supports `--check`, `--restore BACKUP_DIRECTORY` and `--remove`.

[Full-ship render](../../previews/Australis-v0.8.5-Full-Ship.png) · [Naval-detail close-up](../../previews/Australis-v0.8.5-Naval-Details.png) · [Numbering views](../../previews/Australis-v0.8.5-Hull-Numbers.png) · [Four-ship 3D viewer](../../viewer/Australis-v0.8.5-Fleet-3D.html) · [Install/test/rollback](../../GAME-TEST.md)

Download and open the self-contained HTML locally to rotate the model. Preview number appearance is projected from the same per-variant PNG atlas as the game, with approximate texture sampling. Inspect all four variants in daylight and at night, check the window/door alignment from both sides, then repeat the lift and aircraft-cycle checks.

## Visual references

The fittings use original geometry; reference photographs are not redistributed. Style references are the U.S. Navy's [Nimitz watertight-door installation photograph](https://www.dvidshub.net/image/8496398/sailor-installs-watertight-door) and [Gerald R. Ford exterior photograph](https://www.dvidshub.net/image/9253915/uss-gerald-r-ford-cvn-78-conducts-fueling-sea). They inform appearance rather than certifying this fictional ship's construction.

[Previous class and flight-deck fix](../v0.8.4/README.md) · [Current design basis](../../DESIGN-BASIS.md)
