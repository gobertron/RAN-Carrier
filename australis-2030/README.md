# Australis 2030 — original Australian CATOBAR carrier

The current concept uses the supplied Ford flight-deck reference with our
original faceted hull and two islands. It has **five 95 m steam catapults**:
three at the bow and two angled on the port waist, plus an arrested-recovery lane,
four helicopter/VTOL spots ahead of the islands and four 22 × 26 m lifts. A broader bow flight
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
| Steam CATOBAR tracks | Five, each 95 m; IDs 1/2/3 bow and 4/5 port waist |
| Waist launch heading | 6 degrees to port; launch positions staggered 21 m |
| Deck-edge lifts | Four, each 22 × 26 m, bow-facing parking |
| Recovery | 9° to port, four perpendicular cable indications; aircraft carries the hook |
| Islands | Larger command island; reduced aft island with wraparound bridge glazing |
| Aviation ammunition | 6,000,000 finite supply points, no per-category caps |

[DESIGN-BASIS.md](DESIGN-BASIS.md) provides the crew and mass budget, space
allowances, references and complete modern-target/stock-proxy equipment table.
The dimensions and staffing are project estimates, not certified naval
architecture. Folded-aircraft parking, stability, blast clearance and the full
99-aircraft cycle remain unvalidated.

The combat layout includes 80 peripheral VLS cells, two self-defence missile
mounts, two 21-position RAM-form mounts, three Phalanx mounts, two 30 mm guns,
radars, ESM, defensive ECM, one offensive ECM, eight SRBOC positions and two
Nixie decoys. The current native package uses declared stock-compatible
proxies. All missile stores now use stock Sea Sparrows as defensive proxies;
changing their housing does not implement RIM-116/ESSM performance. Four
Nulka positions and four laser hatches are visual studies. RIM-66E and
RGM-109 have been removed. Four VLS banks and four missile housings occupy
the marked main-deck edge areas, with no-parking zones. Guns have original
moving yaw/elevation meshes; missile housings and hatches remain static.

Bow catapults 1/3 can operate as a pair; centre bow lane 2 interlocks with both.
Waist catapults 4/5 interlock with all bow lanes and with each other because
their departure/taxi areas are shared. The one-second minimum interval remains
subject to the game scheduler. All five catapults and arrested recovery accept
Plane, VTOL and STOL types; vertical spots accept Helicopter and VTOL types.
Automatic discovery has no carrier-specific class whitelist or size, role or
loadout exclusions. Aircraft must be correctly installed and carrier-capable,
including their squadron definitions. The air group remains empty for user
selection, without an aircraft-pack dependency.

The outer waist catapult starts at physical (-20.2, -1) m, 6.2 m inboard of its
earlier position. All five lanes are checked at staging and their aligned
20 m approach using A-7E (11.8 × 14.06 m), F-14A (19.545 × 19.1 m) and a
25 × 30 m reference footprint, with span listed before length. These checks
cover deck, lift and island footprints; they do not validate every add-on,
swept taxi turns, rotor clearance or a mixed deck cycle.

The starboard forward lift is moved to z=54 m; the port
lift remains abreast of the aft part of the main island at z=-32 m. Four
12-degree H markings form two pairs ahead of the islands. All vertical launch
spots 6–9 interlock bidirectionally with waist lanes 4/5, leaving bow launch
points available during vertical launches. Every recovery point explicitly
blocks launch points 1–9.

The 30 mm normal-gun sections now use the engine-required NumberOfGuns/Gun1
keys and registered barrels, correcting the null reference in AlignTurret.
Taxi/launch contact points match the deck surface, removing the former
16 cm height offset. Lifts now sit within 2 mm of the main deck rather than
20.5 cm higher; helicopter circles use a 2 mm painted surface rather than
an 8 cm platform. Native contact positions match those exported surfaces.
Deck paint, closed laser covers and stowed deflectors also sit close to or
flush with the deck. Cable and shuttle details retain small raised profiles.
Stock aircraft magazines remain intact; the carrier reserve increases to
6,000,000 points for repeated armed sorties. The new gun and wheel-contact
corrections still need an in-game firing and aircraft check.

The three-bow/two-waist arrangement is our requested Australis adaptation of
the bow-and-waist carrier layout, not a claim that an American class has this
exact five-catapult arrangement. Tracks, deflector panels, taxi approaches and
native launch headings share the same axes; the waist tracks turn to port.
The waist tracks now use a shallow 6-degree heading, port-side positioning and
a 21 m fore-and-aft stagger. Small launch shuttles, flush metal troughs/dark
slots, white guides and segmented stowed deflectors give them a more credible
appearance. Those details are static; deflector deployment and shuttle motion
are not animated. The chosen angle is an Australis design value.

The [deck plan](previews/australis_2030_deck_plan.png),
[perspective](previews/australis_2030_perspective.png) and
[bow view](previews/australis_2030_bow.png) are geometry renders. Open the
[offline viewer](viewer/australis_2030_3d.html) to rotate and inspect the model.
The [port-waist view](previews/australis_2030_port_waist.png) and the viewer's
**Port waist** preset show the shallow, staggered tracks from their outboard side.
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
