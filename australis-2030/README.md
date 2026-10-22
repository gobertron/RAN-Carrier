# Australis 2030 — original Australian CATOBAR carrier

The current concept uses the supplied Ford flight-deck reference with our
original faceted hull and two islands. It has **five 95 m steam catapults**:
three in the middle and two outboard, plus an angled arrested-recovery lane,
four aft helicopter/VTOL spots and four 22 × 26 m lifts. A broader bow flight
deck sits above the fine immersed stem. The main flight deck remains 82 m
wide; the maximum width including the lift extensions is 109 m.

| Design target | Value |
|---|---:|
| Overall length | 370 m |
| Main flight deck / waterline beam | 82 m / approximately 41 m |
| Draft / full-load displacement | 11.5 m / 112,000 metric tonnes |
| Simplified hull-volume displacement estimate | 112,402 tonnes |
| Embarked personnel / berths | 5,300 / 5,800 |
| Aircraft target | 99 |
| Proposed hangar / deck allocation | 36 / 63, parking unverified |
| Steam CATOBAR tracks | Five, each 95 m; IDs 2/3/4 middle and 1/5 outboard |
| Deck-edge lifts | Four, each 22 × 26 m, bow-facing parking |
| Recovery | Angled lane, four cable indications; hook belongs to aircraft |
| Islands | Larger command island and smaller aft aviation island |

[DESIGN-BASIS.md](DESIGN-BASIS.md) provides the crew and mass budget, space
allowances, references and complete modern-target/stock-proxy equipment table.
The dimensions and staffing are project estimates, not certified naval
architecture. Folded-aircraft parking, stability, blast clearance and the full
99-aircraft cycle remain unvalidated.

The combat layout includes 80 peripheral VLS cells, two self-defence missile
mounts, two 21-position RAM-form mounts, three Phalanx mounts, two 30 mm guns,
radars, ESM, defensive ECM, one offensive ECM, eight SRBOC positions and two
Nixie decoys. The current native package uses declared stock-compatible
proxies. In particular its ESSM/RAM-form mounts fire stock Sea Sparrows;
changing their housing does not implement RIM-116/ESSM performance. Four
Nulka positions and four laser hatches are visual studies. Turrets/hatches
are not animated in the game prototype.

Adjacent catapult lanes interlock. Alternate sets 1/3/5 or 2/4 can prepare
independently; the one-second minimum interval remains subject to the game
scheduler. Outboard lanes are restricted to the stock A-7E pending other
footprint checks. The middle lanes use a checked 25 m span × 30 m length
reference envelope. The starboard forward lift is moved to z=54 m; the port
lift remains abreast of the main island. Four 12-degree H markings remain
29 m apart near the aft island. Recovery blocks launches.

The [deck plan](previews/australis_2030_deck_plan.png),
[perspective](previews/australis_2030_perspective.png) and
[bow view](previews/australis_2030_bow.png) are geometry renders. Open the
[offline viewer](viewer/australis_2030_3d.html) to rotate and inspect the model.
Its laser deployment control is a visual demonstration, not game weapon logic.

`model/source/` contains metre OBJ/MTL files. The deployed-laser OBJ is an
overlay for the base hull; `model/game-scale/` contains an approximate Sea
Power scale copy. Rebuild from the repository root:

```bash
python3 australis-2030/build.py
python3 tools/build_australis_2030_mod.py
python3 tools/validate_australis_2030_mod.py
```

The user confirmed original hull loading on 22 October 2026 after the missing
Foam configuration was added. The new CATOBAR/combat fit needs an in-game
check using [GAME-TEST.md](GAME-TEST.md). Geometry is original; stock profile
and resource references do not bundle stock or Workshop asset bytes. The
installer changes only the standalone Australis mod folder.
