# Australis 2050 — original RAN carrier concept

The first new design in the newest-to-oldest Australis sequence. This 2050
study has a straight-edged flight deck, hard-chine hull, a larger integrated
command island amidships, a smaller aviation island aft, flush radar faces,
and four enclosed deck-edge laser positions. Surfaces use
long aligned planes to give a clean, radar-conscious silhouette. This is a
visual design choice, not a measured radar signature or a claim of stealth.

| Design target | Value |
|---|---:|
| Type and propulsion | CVN, nuclear concept |
| Overall length | 370 m |
| Maximum flight-deck beam | 104 m |
| Air-group capacity | 99 aircraft, target only |
| Catapult tracks / deck-edge lifts | 3 / 4, indicated on the model |
| Aft vertical-operation spots | 4, staggered with angled H markings; VTOL or helicopters |
| Islands | 2; larger midship command island, smaller aft aviation island |
| Shipboard offensive ECM | 1 integrated module, represented by two panels |
| Laser positions | 4 enclosed mounts, visual study only |

The deck has two bow catapults, one waist catapult, an angled recovery lane,
four arresting-wire indications and four marked aft VTOL/helicopter spots.
The spots sit farther apart in staggered rows on the aft deck, and their H
markings are angled by 12 degrees. Vertical operations and fixed-wing
recovery are proposed as separate deck modes; simultaneous use is not claimed.
One lift is on the forward port side and another on the starboard edge ahead
of the aft spots; this leaves space for the smaller rear island.
Flight operations, equipment locations, and deck clearances still need an
in-game engineering pass. The aircraft
capacity is the requested design target and is not a demonstrated 99-aircraft
simulation. Air-group IDs and combat values are deliberately unassigned.

`model/source/ran_cvn_australis_2050.obj` uses metres. `model/game-scale/`
contains an approximate scale copy for later integration. The OBJ groups are
named so deck, island, panels, lifts and mounts can be refined independently.
The PNG previews show rendered geometry and a deck-layout study; they are not
Sea Power screenshots. `build.py` regenerates the OBJ/MTL and preview images
from original geometry using NumPy and Pillow.

**Status:** Concept art and watertight component mesh, not an installable Sea
Power mod. No vessel INI is enabled or shipped here. Mission Editor loading,
native materials, collision, launch and recovery, ECM, radar and lasers have
not been tested. This milestone does not alter RADF, the Workshop, the game or
the earlier Melbourne prototype. The next edition in this sequence will be a
less futuristic Australis after this silhouette is reviewed.

All geometry and materials in this folder are authored for this project.
