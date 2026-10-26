# Australis v0.8.2 — lift lighting

Current experimental build, 26 October 2026. Four ships: HMSCS Australis 91, Southern Cross 92, Federation 93 and Commonwealth 94.

[Installer](../../../builds/install-ran-australis-v0.8.2-lift-lighting.sh) · [Source/native ZIP](../../../builds/RAN-Carrier-Australis-v0.8.2-Lift-Lighting.zip) · [SHA256 checksums](../../../builds/SHA256SUMS-v0.8.2.txt) · [Test and rollback](../../GAME-TEST.md)

## Changes carried by this release

- Eight recessed warm-white lights per lift shaft, 32 total. Each group reads its actual lift height during day and night, fades from full brightness at 0.60 m below deck, and is off within 0.10 m of the deck-level stop. Downward spots and non-emissive fittings avoid permanent glow above a closed lift.
- Standard 20 kn for normal aviation; Full 30 kn for emergency manoeuvring; Flank 30 kn. The maximum and280,000 hp setting stay unchanged.
- Eight-waterjet broad-stern prototype with real intake/outlet openings and internal wet ducts; four steering nozzles and four fixed boosters. Approximately 900.4 m³ of flooded ducts are included in the 112,000 t net geometric displacement calibration.
- Three catapults (two bow, one waist), four internal lifts, three helicopter pads, five retractable CIWS and five native repair teams. Helicopter pad preference is aft, front, middle.
- Four numbered hulls, naval doors/windows/paint, landing/deck/hangar lights and six-second lift animations. The forward CIWS retains its corrected outboard location.

## Validation and limits

193 lighting-policy/reflection-fixture checks pass. Geometry, native bindings, internal reservations, speed ladder, aircraft routes and transactional installer/rollback checks pass. These are software and geometry checks. In-game lighting, waterline, steering, aircraft and combat trials remain pending.

The power/resistance sensitivity does not establish real 30-knot capability. The waterjets use the game's aggregate conventional propulsion model; individual thrust allocation, booster staging, reverse-bucket actuation and eight physical jet wakes are not simulated. CFD, cavitation, actual machinery weights, full stability and structure remain unverified. [Engineering review](../../../WATERJET-ENGINEERING-REVIEW.md).

The release ZIP and self-contained installer are the exact delivered v0.8.2 artifacts. Branch documentation and metadata may receive corrections without rewriting those archives. Earlier release notes and fleet studies describe their own dated configurations.

![Actual v0.8.2 model](../../previews/australis_2030_current_starboard.png)

![Lift cutaway, illustrative lamp shading](../../previews/Australis-v0.8.2-Lift-Cutaway.png)
