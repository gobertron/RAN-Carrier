# Australis v0.8.4 — Class and Flight Deck Fix

27 October 2026.

[Network installer](../../../builds/install-ran-australis-v0.8.4-class-list-fix.sh) · [Install/test/rollback](../../GAME-TEST.md) · [Current source guide](../../README.md)

## Changed

The earlier package defined each ship as a separate vessel type. Sea Power grouped those types beneath the same translated class heading and added a separate “2025” submenu for each one. The current package defines one **Australis-class** vessel with four native variants:

| Variant | Ship |
|---|---|
| 1 | HMSCS Australis 91 |
| 2 | HMSCS Southern Cross 92 |
| 3 | HMSCS Federation 93 |
| 4 | HMSCS Commonwealth 94 |

The intended editor layout places those four ship names directly beneath Australis-class, like the stock Forrestal-class list. The variants share one hull and select native number textures on deck- and island-coloured panels. Live-game grouping and number-panel rendering remain to be confirmed.

The old Southern Cross, Federation and Commonwealth vessel IDs are no longer active editor definitions. Re-place affected ships in older missions from the new class; the installer does not edit saved missions and preserves a verified previous-mod backup.

## Flight-deck correction

The flight-deck correction sets each lift's idle/home stop to flight-deck level: `StartsLowered=False`, `CloseDoorsAfterTaxi=False`, with the initial platform at **Y=22.002 m**. The native system lowers a lift on demand and returns it to the upper home stop after launch or recovery. The v0.8.3 lower-home setting conflicted with the native post-taxi upper state, which could leave `IsBusy` permanently true and prevent another aircraft cycle.

All four lifts now have fixed-wing routes: **12 lift-to-catapult routes, four arrested-recovery-to-lift routes, three helicopter launch routes and three helicopter recovery routes — 22 taxi routes in total**. The three dedicated pads accept **Helicopter** only; carrier-capable VTOL/STOL aircraft use the catapult and arrested-recovery paths. Native interlocks remain active. Fixed-wing recovery conservatively blocks all six launch points, so conflicting operations queue.

A state simulation derived from the supplied game IL passes **20 launch/recovery cycles on each of four lifts**. This checks the native lift-state transitions; live Sea Power flight cycles and Unity appearance remain to be confirmed. The compiled v0.8.2 deck controller is retained.

## Retained

The v0.8.3 duplicate stock-catalogue heading fix is included. Hull shape, eight waterjets, Standard 20 kn / Full 30 kn / Flank 30 kn, three catapults, four lifts, three helicopter pads, five CIWS, five repair teams and 32 position-controlled lift-wall lights retain the preceding configuration. The compiled controller remains v0.8.2.

[v0.8.4 compact fleet viewer](../../viewer/Australis-v0.8.4-Fleet-3D.html) · [Full ship](../../previews/Australis-v0.8.4-Full-Ship.png) · [Lift-lighting cutaway](../../previews/Australis-v0.8.4-Lift-Cutaway.png). The compact v0.8.4 viewer uses the retained v0.8.3 numbered design meshes and shows the new flight-deck-level idle pose. The runtime class uses one shared hull with per-variant number textures. Model renders and illustrative lift lighting do not simulate the Mission Editor hierarchy, native flight scheduling or Unity rendering.

## Install

Close Sea Power, then download and run:

```bash
curl -fL 'https://raw.githubusercontent.com/gobertron/RAN-Carrier/feature/australis-2050-concept/builds/install-ran-australis-v0.8.4-class-list-fix.sh' \
  -o "$HOME/Downloads/install-ran-australis-v0.8.4-class-list-fix.sh" &&
bash "$HOME/Downloads/install-ran-australis-v0.8.4-class-list-fix.sh"
```

The network installer downloads an immutable base archive, verifies its SHA256, applies the embedded current overlay and verifies the resulting target manifest before installation. No earlier installer needs to be run. The full offline installer and ZIP are separate release deliverables.

Wait for **100%** and `installed package hashes verified`. Enable **AnchorChain** and **RAN Australis Fleet v0.8.4 Class and Flight Deck Fix**, disable older Australis copies, restart and place each named variant in a fresh mission.

## Validation boundary

Check the class expands directly to four ship names, each number matches the selected name, and no duplicate old class entry remains enabled. Confirm all four lifts start flush at their upper home stop, then repeat native launch/recovery cycles through every lift. Repeat the steering, lift-lighting and combat checks in [GAME-TEST.md](../../GAME-TEST.md).

The preceding isolated geometry, dependency and installation checks do not establish live UI appearance, Unity rendering, flight/combat behaviour or real naval engineering approval. Waterjet performance, full stability and structural validation remain unresolved.

[v0.8.3 historical notes](../v0.8.3/README.md).
