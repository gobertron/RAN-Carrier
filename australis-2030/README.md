# Australis 2030 — original RAN carrier design study

This is the first ship in the newest-to-oldest Australis sequence. The original
mesh draws broad design cues from U.S. aircraft carriers and modern faceted
warship superstructures, with two RAN concept islands and a continuous carrier
flight deck. No third-party meshes, textures, or vessel definitions are copied.

The deck has been narrowed from 104 m to **88 m**, while the maximum waterline
beam is approximately **44 m**. High continuous topsides connect the deck's
entire perimeter to a narrower waterline; the bow below the deck tapers to a
fine immersed stem. The hull has a proposed 11.5 m draft and a 370 m overall
length. Its crude enclosed-volume estimate is 117,064 m³, or about 119,991
tonnes in seawater at 1.025 tonnes/m³; the corresponding approximate block
coefficient is 0.637. This arithmetic only checks that the blockout has a
plausible order of magnitude. It does not demonstrate actual
loading, intact or damaged stability, trim, resistance, seakeeping, structural
strength, propulsion or safe flight operations. The angular shapes are a
visual design choice and do not establish a radar signature.

| Design target | Value |
|---|---:|
| Type and propulsion | CVN, nuclear concept |
| Overall length / maximum deck beam | 370 m / 88 m |
| Maximum waterline beam / draft | 44 m / 11.5 m, approximate |
| Air group | 99 aircraft, capacity target only |
| Catapult tracks / blast deflector panels | 3 / 3, indicated |
| Deck-edge lifts | 4, with the forward starboard lift amidships |
| Aft VTOL / helicopter spots | 4, offset toward the smaller aft island in a fore-to-aft line |
| Recovery lane | Angled, with landing threshold and four arresting cables indicated |
| Islands | 2; larger central command island, smaller aft aviation island |
| Side-mounted radar faces / offensive ECM | 7 indicative panels / 1 visual module |
| Defensive lasers | 4 flush hatches; separate raised visual state |

The four H markings have the requested 12-degree tilt. Their centers lie at
x=6 m, 29 m apart, alongside the aft island. The landing lane is offset to
port. Hook-equipped aircraft would engage **arresting cables on the deck**;
the hooks themselves belong to aircraft and are not carrier fittings. Vertical
operations and fixed-wing recovery are intended as separate deck modes.
The right-hand catapult launches forward and avoids the lifts in plan view.
The builder checks sampled spot outlines and minimum two-dimensional gaps
from islands, lifts and catapult routes. The smallest reported spot-edge gap
is 8 m; the smallest sampled catapult-to-island/lift plan gap is 16.4 m.
These checks do not cover rotor disks, parked aircraft, jet blast, wings,
elevator cycling, simultaneous operations or actual approach geometry.

Radar faces are placed on the command and aviation island sides rather than
carried above them on exposed rotating frames. The four laser hatches are
closed nearly flush to the flight deck in the default OBJ. In the viewer,
**Deploy four lasers** opens the hatches and raises simplified turrets; the
reverse control lowers them. This animation is a visual demonstration, not
game logic, a working directed-energy weapon, or a verified below-deck
installation. The small forward sonar fairing and ECM panel are also
unimplemented visual cues.

Open [the offline 3D viewer](viewer/australis_2030_3d.html) to rotate the model,
switch among deck, bow, side and perspective views, and test the laser states.
The [deck plan](previews/australis_2030_deck_plan.png),
[perspective](previews/australis_2030_perspective.png) and
[bow view](previews/australis_2030_bow.png) are renders of this geometry.
`model/source/ran_cvn_australis_2030.obj` has metre coordinates. The
`model/source/ran_cvn_australis_2030_deployed_lasers.obj` file is a **laser
overlay only** for aligning on top of the closed-state hull in a 3D editor;
hide the four closed hatch objects while inspecting that state. The
`model/game-scale/` OBJ is an approximate scale copy for later integration.
Run `python3 build.py` here to regenerate all geometry, previews and viewer.

**Status:** The components form individually closed geometry, but this is
concept art, not a seaworthy naval architecture package or an installable Sea
Power mod. No vessel INI is enabled or shipped here. Mission Editor loading,
materials, collision, aircraft launch and recovery, radar, ECM and lasers
have not been integrated or tested. Nothing in this milestone modifies RADF,
the Workshop, the original game or the earlier Melbourne prototype.

## Design references

- [U.S. Navy aircraft carrier dimensions](https://www.airpac.navy.mil/Organization/Distinguished-Visitors/Important-Links-and-Info/) informed the difference between a carrier's waterline beam and broader flight deck. Australis uses its own dimensions and hull shape.
- [NAVAIR Advanced Arresting Gear](https://www.navair.navy.mil/product/advanced-arresting-gear-aag) informed the recovery lane and cable indications; none of its engineering is implemented here.
- [NAVSEA on Ford flight-deck design](https://www.navsea.navy.mil/Media/News/Article-View/Article/2596302/uss-gerald-r-ford-closes-out-evolutionary-18-month-pdtt-for-first-in-class-airc/) informed the outboard island and carrier equipment layout.
- [NAVSEA on Zumwalt's faceted superstructure](https://www.navsea.navy.mil/Media/News/Article-View/Article/777551/us-navy-accepts-delivery-of-future-uss-zumwalt-ddg-1000/) informed the visual treatment of tower surfaces; its destroyer hull design has not been transferred to this carrier.
