# Australis 2030 — v0.8.2 lift lighting

Australis is an original alternate-history carrier for Sea Power. The current experimental build includes eight waterjets, a three-catapult flight deck, four internal aircraft lifts and lift-wall lighting that switches off as each platform reaches the flight deck. Four numbered ships share this design: **HMSCS Australis 91, Southern Cross 92, Federation 93 and Commonwealth 94**.

The model, native configuration and controller checks pass. **v0.8.2 has not completed an in-game play test**, and the waterjet arrangement is a propulsion study rather than an engineering-approved design.

![Current Australis model](previews/australis_2030_current_starboard.png)

[Model photos and rotatable 3D viewer](viewer/australis_2030_3d.html) · [Design basis](DESIGN-BASIS.md) · [Install, test and rollback](GAME-TEST.md) · [Build history](../builds/README.md)

Download the self-contained HTML viewer to rotate the model offline. It shows the exported game geometry; studio renders and illustrative lighting are not gameplay screenshots.

## Install the current build

Download [install-ran-australis-v0.8.2-lift-lighting.sh](../builds/install-ran-australis-v0.8.2-lift-lighting.sh), close Sea Power, then run:

```bash
bash "$HOME/Downloads/install-ran-australis-v0.8.2-lift-lighting.sh"
```

Enable **AnchorChain** and **RAN Australis Fleet v0.8.2 Lift Lighting**, restart, and place a fresh carrier in a new mission. The installer checks the supported game version and existing AnchorChain installation, verifies the package and backs up an existing Australis installation before replacement. It supports `--check`, `--remove` and `--restore BACKUP_DIRECTORY`.

[Source and native package ZIP](../builds/RAN-Carrier-Australis-v0.8.2-Lift-Lighting.zip) · [Download checksums](../builds/SHA256SUMS-v0.8.2.txt)

## Current configuration

| Item | v0.8.2 configuration or design target |
|---|---|
| Overall length / main flight-deck width | 370 m / 82 m |
| Waterline length / beam / maximum draft | 362.6 m / 41 m / 11.5 m |
| Net geometric wet-hull displacement | Approximately 112,000 t, including flooded-duct deductions |
| Aircraft / embarked personnel / berths | 99 / 5,300 / 5,800 planning targets |
| Hangar | 280 × 50 × 8 m; 36 folded reference parking boxes |
| Steam catapults | Three 95 m tracks: two bow and one port waist |
| Lifts | Four internal 22 × 26 m platforms; six-second native travel |
| Helicopter pads | Three; preference aft, then front, then middle |
| Operating speeds | **Standard 20 kn**, **Full 30 kn**, Flank 30 kn |
| Repair teams | Five native damage-control teams |
| CIWS | Five retractable mounts: three deck wells and one on each island |
| VLS stores | 40 stock RIM-66E proxies and 40 stock RIM-7M rounds |

The forward CIWS sits outboard of the bow catapult at the corrected port-side position. The flight deck retains its nine-degree port recovery axis, four arresting-wire indications, deck markings, tyre streaks, bridge panes, naval doors and painted hull numbers.

## Aviation at Standard power

**Standard is 20 knots** for normal aircraft and helicopter operations; Full reaches the existing 30-knot ceiling for emergency manoeuvring. This is an operating convention, not an automatic emergency detector. The native speed ladder is `-7,0,6,12,20,30,30` for Astern, Stop, Creep, Slow, Standard, Full and Flank. Maximum speed and the 280,000-horsepower power setting are unchanged.

Lifts 1–2 serve fixed-wing operations; lifts 3–4 serve helicopters and VTOL aircraft. Installed carrier-capable aircraft are discovered without a carrier-specific class whitelist or size, role or loadout exclusion. This includes correctly configured F-111N add-ons; it does not establish physical clearance for every aircraft or loadout. The air group starts empty for user selection.

The three helicopter pads can operate independently when their native routes are free. Shared lifts and taxi/recovery lanes still queue, and recovery retains its configured conflicts. The full 99-aircraft parking and operating cycle remains unverified.

## Lift-wall lighting

Each shaft has eight recessed warm-white wall lights, **32 in total**, on its outer, forward and aft walls. The inboard hangar doorway stays open. Each group follows its actual platform height and operates during the day and at night:

- At the lower stop, 11.8 m, the shaft lights remain on.
- Lights fade as the platform approaches the 22.002 m flight-deck stop.
- They are fully off within 0.10 m of deck level and reach full brightness at 0.60 m below it.

The fixtures stay outside the platform sweep. Their spotlights point inward and downward; the lenses have no permanent emission. Missing or invalid platform data switches the affected group off. Exterior night lighting remains controlled separately.

![Lift lowered and flush with the deck](previews/Australis-v0.8.2-Lift-Cutaway.png)

The cutaway uses actual geometry with illustrative lamp shading. In-game brightness, appearance and light leakage still need a visual check.

## Waterjets and defensive systems

Eight real underside intake openings connect through internal wet ducts to eight open transom outlets. Four outer nozzle assemblies steer together through native rudder pivots; the four inner outlets are fixed booster representations. Sea Power uses its aggregate vessel-propulsion model: independent jet thrust, booster staging, reverse-bucket actuation and eight separate wakes are not simulated.

The [engineering review](../WATERJET-ENGINEERING-REVIEW.md) records the geometric hydrostatics and power sensitivity. Approximately 900.4 m³ of floodable ducts are deducted in the net wet-hull calculation. Actual resistance, pump selection, cavitation, machinery weights, full stability, structures and real 30-knot performance remain unresolved.

The 80 VLS cells use declared stock compatibility proxies. RIM-66E retains its stock guidance and target limits; it is **not SM-6**, and no ballistic-missile defence capability is claimed. The ESSM/RAM-form launchers also use declared stock proxies. Nulka and laser positions remain visual studies.

The AnchorChain deck controller waits for committed aviation to clear before opening the defensive wells, deploys over 0.75 simulation seconds, holds for 300 seconds after the last actual shot, and stows over 10 seconds. Aviation stays interlocked until stowage completes. Actual combat and mixed deck operations require in-game testing.

## Source and checks

The current source is rebuilt from the recoverable v0.5.1 base and subsequent design changes; it is not a byte-for-byte restoration of the lost v0.6.0 installer. The current driver is:

```bash
python3 tools/rebuild_recovery.py
python3 tools/validate_recovery.py
```

Source generation uses NumPy, Pillow, Shapely and SciPy; preview plots also use Matplotlib. Recompiling the controller requires an external .NET SDK and official AnchorChain/Harmony development references; see [GAME-TEST.md](GAME-TEST.md). The delivered installer uses Python's standard library only. Game binaries and third-party asset bytes are not redistributed.

Checks cover exported hull topology and openings, native bindings, internal reservations, aircraft routes, lift animations, the speed ladder, 193 lighting policy/reflection checks and transactional installation/rollback. These establish geometry and software integrity, not completed Unity rendering, flight, combat or naval-engineering validation. Historical release notes remain under [releases](releases/) and [builds](../builds/README.md).
