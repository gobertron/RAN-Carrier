# Australis 2030 — current design basis

This page describes **v0.8.2 Lift Lighting**. It separates exported geometry and native configuration from planning assumptions and uncompleted in-game or engineering tests. Older releases describe earlier layouts and remain historical records.

## Hull, spaces and people

| Item | Current value or planning target |
|---|---:|
| Overall length | 370 m |
| Main flight-deck width, including internal lifts | 82 m |
| Waterline length / maximum beam | 362.6 m / 41 m |
| Maximum design draft | 11.5 m |
| Native displacement target | 112,000 metric tonnes |
| Net wet-boundary geometric displacement | 112,000.07 t at 1.025 t/m³ reference seawater density |
| Floodable waterjet-duct deduction | 900.40 m³ |
| Hangar length / width / clear height | 280 m / 50 m / 8 m |
| Folded hangar reference boxes | 36: 24 large, eight compact UAV and four folded rotor |
| Proposed flight-deck aircraft allocation | 63, unverified |
| Total aircraft target | 99 |
| Ship's company / air wing / staff | 2,850 / 2,250 / 200 |
| Embarked personnel / planning berths | 5,300 / 5,800 |

The current lifts are internal; the earlier 109 m width including deck-edge lift extensions no longer applies. Room envelopes and folded parking boxes pass sampled geometric containment and reservation-overlap checks. They are not detailed cabins, machinery, evacuation routes, towing paths or a verified 99-aircraft operating cycle.

The wet hull is symmetric about the centreline and includes connected intake ducts rather than treating those flooded spaces as buoyant solid hull. The outer reference envelope is larger than the net wet volume and is not registered as visible geometry. A separate simplified convex collision hull has 108 triangles and bridges the visible openings; it is not a CFD surface.

The planning/game CG is approximately `(0, +7.000, -11.259)` m relative to the design waterline and hull centre. Its longitudinal position is aligned with the wet-boundary geometric centre of buoyancy. Conditional initial transverse GM is approximately **4.361 m for this assumed CG**. No detailed machinery weight-centre survey, full GZ curve, loading range, downflooding, damage stability, structural or seakeeping assessment is complete.

[Exported hydrostatic audit](../game-mod/RAN-Carrier-Australis-2030/naval-hull-hydrostatics.json) · [Internal arrangement](../game-mod/RAN-Carrier-Australis-2030/internal-arrangement.json) · [Internal-fit audit](../game-mod/RAN-Carrier-Australis-2030/internal-fit-validation.json)

## Three-catapult aviation layout

Coordinates below are physical metres: X positive to starboard, Z positive forward; Y is measured above the design waterline.

| Catapult | Launch position X, Z | Heading | Stroke |
|---|---|---:|---:|
| 1, port bow | −23.5, 88 | Ahead | 95 m |
| 2, starboard bow | 2.5, 88 | Ahead | 95 m |
| 3, port waist | −25.0, −1 | 6° to port | 95 m |

There are two bow catapults and one waist catapult. The nine-degree port recovery lane has four perpendicular arresting-wire indications. Launch, recovery, lift and taxi interlocks remain native configuration plus the enclosed-defence controller; a one-second launch delay is a scheduler minimum, not a guarantee of simultaneous launches.

| Internal lift | Centre X, Z | Intended use |
|---|---|---|
| 1 | 27.5, 82 | Fixed wing |
| 2 | 27.5, 54 | Fixed wing |
| 3 | 11.0, −18 | Helicopter / VTOL |
| 4 | 26.0, −50 | Helicopter / VTOL |

Each platform is 22 × 26 m and travels between Y=11.8 m and Y=22.002 m using six-second native animation sequences. The three helicopter pads lie at `(11, 12)`, `(13.6, −79)` and `(20.2, −116)` m, with aft/front/middle selection preference. Separate pads do not eliminate shared lift, taxi and recovery conflicts.

Plane, VTOL and STOL eligibility is configured for rolling launch/recovery. Dedicated vertical points accept helicopters and VTOL aircraft. Installed aircraft must themselves support carrier operations and have valid squadron definitions. No carrier-specific aircraft whitelist is used; eligibility is distinct from proving a particular airframe, rotor or loadout clears the complete route.

## Speed and propulsion

| Native telegraph setting | Knots |
|---|---:|
| Astern / Stop / Creep / Slow | −7 / 0 / 6 / 12 |
| **Standard — normal aviation setting** | **20** |
| **Full — emergency manoeuvring convention** | **30** |
| Flank | 30 |

`Physics.TelegraphVelocities=-7,0,6,12,20,30,30` supplies the supported native ladder. Standard matches the inspected fixed-wing air-operations target. Helicopter sea-state and landing-assistance checks remain active. Full is available to the operator; the controller does not classify or enforce emergencies. Damaged propulsion can reduce achievable speed.

Eight conceptual waterjets share the existing **280,000 mechanical hp, approximately 208.8 MW aggregate** power setting. Four outer steering assemblies use a common native rudder command; four inner outlets represent fixed boosters. The 2.35 m clear outlet bore is a geometry assumption, not a selected manufacturer's pump size. Internal impellers rotate, while raised reverse-bucket shapes remain static. The native game model does not calculate intake flow, independent thrust allocation, booster staging or waterjet reversal.

At 30 knots, the preliminary resistance sensitivity spans approximately **99–310 MW** for its stated arbitrary resistance scenarios. Those scenarios are not measured predictions or confidence limits. Actual resistance and pump/inlet performance can exceed available power; real 30-knot adequacy is unresolved. See the [engineering review](../WATERJET-ENGINEERING-REVIEW.md) and [reproducible screen](../game-mod/RAN-Carrier-Australis-2030/waterjet-engineering-screen.json).

## Lift and night lighting

Each lift has eight recessed warm-white wall fixtures on its existing outer, forward and aft walls, leaving the inboard hangar doorway open. Fixture bodies lie outside the moving platform footprint. Actual platform height independently controls each group, during both day and night:

- Fully off within 0.10 m below the 22.002 m deck stop.
- Smooth fade to full brightness by 0.60 m below deck.
- On at the lower stop; the same fade applies while ascending.

Spotlight cones point inward/downward, with their highest ray below horizontal. The lenses have no permanent emission. Missing, nonfinite or out-of-travel platform data switches the affected group off, and initialization failure disables partially created lamps. Exterior guidance, task and hangar night lamps remain a separate system. These lighting behaviors pass **193 policy and reflection-integration checks** using a Unity-shaped fixture; the checks do not establish in-game brightness or eliminate the need for a visual leakage test.

## Combat configuration and proxies

| Fit | Current implementation |
|---|---|
| CIWS | Five retractable positions: three deck wells and two island roofs |
| 30 mm | Two original moving gun mounts with declared ammunition profile |
| Peripheral VLS | 80 cells: 40 stock RIM-66E proxies and 40 stock RIM-7M rounds |
| ESSM/RAM-form housings | Declared stock Sea Sparrow compatibility proxies; housing does not change guidance |
| Search / surface / air-traffic radar | Declared SPY-1A / SPS-67 / SPN-43 stock profiles |
| ESM / defensive ECM | Declared AN/SLQ-32-family profiles |
| Offensive ECM | One configured shipboard module; no aircraft slot consumed |
| Chaff / towed decoys | Eight SRBOC positions and two Nixie decoys |
| Nulka / lasers | Visual positions; active hovering or laser-weapon behavior unimplemented |
| Damage control | Five native repair teams |
| Aviation reserve | 6,000,000 finite ammunition points; no per-category caps |

RIM-66E retains stock range, guidance and target limits. It is **not SM-6**, and no ballistic-missile interception is claimed. The current native fit and planning allocations are recorded in [combat-fit.json](../game-mod/RAN-Carrier-Australis-2030/combat-fit.json).

The AnchorChain controller clears committed aviation before defensive deployment, opens over 0.75 simulation seconds, holds until 300 seconds after the last actual shot, and stows over 10 seconds. Aviation stays interlocked while the wells are open. Raised deck platforms stop 8 cm above the deck. The forward CIWS has moved outboard of the bow catapult to the corrected port-side position. These are configured/controller behaviors requiring an in-game engagement test.

## Validation boundary

The exported wet boundary, eight inlet/outlet paths, rotor/bore fit, nozzle packaging, native bindings, collision budget and internal reservations are audited. Installer tests cover fresh, repeated and upgrade installation, verified backup, restore, removal, unsupported game versions, corrupt backups and rollback after an injected failure. The package uses original geometry and controller source; stock assets are referenced, not bundled.

These checks support an experimental game build. Actual flight cycles, Unity rendering, weapon engagements, damage response and rough-sea behavior remain pending. Full naval-engineering validation also requires measured or validated resistance/self-propulsion work, supplier pump/inlet matching, cavitation analysis, detailed weights, stability and structures.
