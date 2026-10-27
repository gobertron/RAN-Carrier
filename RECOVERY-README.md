# Australis v0.8.5 — Naval Details

## Naval details in v0.8.5

Hull numbers **91–94** are enlarged on the flight deck and both main-island sides and aligned to their model surfaces. The shared native class still selects the matching number atlas for each named ship. Both bridge structures receive individual framed naval-style windows, with consistent sill heights and mullions on their actual raked faces. Watertight-style doors use raised coamings, rounded corners, hinges, dogs and handles aligned to the supporting surface.

The deck number panel is **10.8 × 8.8 m**, with an approximately **8.44 × 6.53 m** painted glyph. Both port and starboard main-island panels are **9.6 × 5.6 m**, with approximately **7.69 × 4.20 m** glyphs. The panels follow their actual supporting planes with a small surface offset; the enlarged island markings sit between the lower access doors and bridge glazing.

These fittings are original decorative model geometry; they do not create functioning doors or establish watertight integrity, ballistic protection or naval-design certification. Their appearance, texture orientation and visibility still need an in-game check. The change retains the preceding hull, waterjet, class-list and flight-deck configuration.

**The v0.8.4 class-list correction is retained: one Australis-class entry**, using four native ship variants rather than four separate class definitions. This is intended to remove the extra “2025” submenus shown in the earlier build. The target Mission Editor list is:

| Class | Selectable ship |
|---|---|
| Australis-class | HMSCS Australis 91 |
| Australis-class | HMSCS Southern Cross 92 |
| Australis-class | HMSCS Federation 93 |
| Australis-class | HMSCS Commonwealth 94 |

The variants share the hull and use native per-variant number textures on deck- and island-coloured panels. Hull shape, propulsion settings and the compiled v0.8.2 deck controller are retained. The v0.8.4 lift-home state and taxi-route corrections are retained as described below. **The class-list presentation and number-panel appearance still need confirmation in the live game.**

Older missions that reference the former Southern Cross, Federation or Commonwealth vessel IDs need those ships re-placed from **Australis-class**. The installer retains a verified backup; it does not edit saved missions.

The flight-deck correction sets each lift's idle/home stop to flight-deck level: `StartsLowered=False`, `CloseDoorsAfterTaxi=False`, with the initial platform at **Y=22.002 m**. The native system lowers a lift on demand and returns it to the upper home stop after launch or recovery. The v0.8.3 lower-home setting conflicted with the native post-taxi upper state, which could leave `IsBusy` permanently true and prevent another aircraft cycle.

All four lifts now have fixed-wing routes: **12 lift-to-catapult routes, four arrested-recovery-to-lift routes, three helicopter launch routes and three helicopter recovery routes — 22 taxi routes in total**. The three dedicated pads accept **Helicopter** only; carrier-capable VTOL/STOL aircraft use the catapult and arrested-recovery paths. Native interlocks remain active. Fixed-wing recovery conservatively blocks all six launch points, so conflicting operations queue.

A state simulation derived from the supplied game IL passes **20 launch/recovery cycles on each of four lifts**. This checks the native lift-state transitions; live Sea Power flight cycles and Unity appearance remain to be confirmed. The compiled v0.8.2 deck controller is retained.

The included v0.8.3 stock-catalogue correction fixes the installer stopping at 40% with `section '---------- Surface ships ----------' already exists` in Sea Power's stock `systems/sensors.ini`. The dependency check now inventories stock section names and tolerates repeated category dividers and values. It does not edit or rewrite the original game files. Strict validation remains enabled for our own mod INIs; missing actual stock systems, ammunition and other dependencies still stop installation.

The class and flight-deck corrections retain the waterjet hull, Standard 20 / Full 30 speed profile and lift-wall lighting. The native fleet now has one vessel definition and four variants, with native hull-number textures. The compiled deck controller remains v0.8.2. Earlier failed attempts stopped before replacement, so the previous installed carrier remains in place until this corrected installer succeeds. A verified backup is made before an existing carrier is replaced.


v0.8.2 adds eight recessed warm-white work lights to each lift shaft (32 total), placed in the existing outer, forward and aft walls. The inboard hangar doorway stays open. The lights follow each actual LiftPlatform transform independently, rather than an animation timer or the exterior night-light schedule. They work during the day and at night while the lift is below deck.

Lift illumination is fully off within 0.10 m of the 22.002 m deck-level stop, fades smoothly, and reaches full brightness at 0.60 m below deck. It remains lit at the lower stop and fades out while returning upward. Missing, invalid or out-of-travel platform data switches that shaft's lights off; initialization faults switch off partially created lights without disabling the aviation controller. The downward spotlight cones have no upward rays, and the lens materials have no permanent emission, so a closed lift does not leave lower-deck glow on the flight deck. Recessed fixture bodies stay outside the platform sweep.

The lighting tests use the actual controller with a minimal Unity-shaped fixture and check independent lifts, top-stop darkness, fading and failure cleanup. They do not replace an in-game visual check. Test one lift down/up during daylight and darkness, then park it flush and confirm no light leaks around the platform. The previous Standard 20 kn / Full 30 kn speed profile remains active.


v0.8.2 configures the native Physics.TelegraphVelocities ladder: Astern −7 kn, Stop 0, Creep 6, Slow 12, **Standard 20**, **Full 30**, Flank 30. Standard is the normal aviation setting, matching Sea Power's fixed-wing PerformingAirOps 20-knot demand. Full remains available for emergency manoeuvring; this is an operating convention, not a restriction that detects or enforces emergencies. Both Full and Flank use the existing 30-knot ceiling.

The supplied game loader reads seven knots values directly, so no new runtime speed patch or increase to maximum speed/horsepower is needed. Native helicopter sea-state/landing-assistance checks, deck conflicts and aircraft eligibility remain active. There is no general helicopter absolute ship-speed cap in the inspected landing path. These settings enable the intended native operating speed; specific aircraft/loadouts, wind, sea state and actual flight cycles still require in-game testing. Damaged propulsion can reduce achievable speed.


This separate build follows the v0.7.0 recovery release. It is an experimental Sea Power implementation with a reproducible preliminary engineering screen, not an engineering-approved carrier propulsion design. The eight-jet concept image has been replaced with actual exported game geometry.

A broader symmetric stern accommodates eight 2.35 m conceptual outlet bores, eight genuinely cut underside intakes and internal connecting wet ducts. Four outer nozzle sleeves steer using native rudder pivots; four inner outlets are fixed boosters visually. Eight internal impellers rotate independently as native propulsion meshes. External shafts, propellers and blade rudders have been removed. The rounded bilges, fine bow and bilge keels remain. The working sizes are packaging assumptions, not selected commercial pumps.

The hull is recalibrated using its **closed wet boundary including the flooded ducts** to approximately 112,000 tonnes at a reference seawater density of 1.025 t/m³. Gross envelope displacement is larger; duct flooding deductions are recorded separately. Maximum waterline beam remains 41 m and maximum draft 11.5 m. The planning/game CG stays at X=0, Y=+7 m above waterline, while its assumed longitudinal position is replanned to the measured wet centre of buoyancy. This is not a machinery weight-centre calculation. The separate closed outer reference envelope is an audit asset and is not registered for rendering, so it cannot seal the visible mouths. The simplified native convex collision mesh deliberately bridges openings and remains below 255 triangles.

The native 30-knot target and 280,000-horsepower setting are retained. Eight equal power shares imply approximately 26.1 MW per train, but no supplier pump match or real 30-knot capability is established. `WATERJET-ENGINEERING-REVIEW.md` and `waterjet-engineering-screen.json` contain the resistance/power sensitivity, explicit assumptions and remaining work. At this stage, actual resistance, intake losses, cavitation, machinery loads, structural strength, full intact/damage stability and seakeeping remain unresolved.

Sea Power uses conventional aggregate vessel propulsion. Eight mounts do not multiply thrust: the shared power plant still supplies the vessel. The four steering units follow the same native rudder command. Independent thrust allocation, booster staging, bucket animation, eight individual wakes and physical waterjet flow are not simulated. The raised reverse-bucket shapes are static. Native astern operation is a game approximation. The original Foam section is retained because native rudder initialization requires its stern trail.

The flight-deck geometry, forward CIWS position and lift locations are retained. Lift-home configuration and aircraft routes are corrected; the compiled deck controller is unchanged. All geometry/software checks reported here apply to this exported prototype; no in-game play test has been completed.

Four native ship variants: HMSCS Australis 91, Southern Cross 92, Federation 93 and Commonwealth 94. Three catapults (two bow, one port waist), four 22 × 26 m internal lifts and three helicopter-only pads are retained. Fixed-wing routes connect all four lifts to all three catapults and the arrested-recovery lane. VTOL/STOL aircraft use those rolling paths. Helicopters prefer aft, front, middle through their native lift/pad routes; shared lifts and taxi/recovery corridors still queue. Fixed-wing recovery blocks all six launch points conservatively.

Five repair teams; 280 × 50 × 8 m hangar and 36 folded reference parking spaces; 5,800 planning berths. The layout is checked by sampled geometric containment and reservation-overlap checks; the current internal-arrangement audit records the final room count. Aircraft turns, 63 deck-parked aircraft, the complete 99-aircraft cycle and naval stability have not been verified.

Five retractable CIWS: three deck wells and one on each tower. Deck platform bases stop 8 cm above the deck. Dedicated VLS launch bases point upward. Defensive stores include 40 **stock RIM-66E long-range SAM proxy rounds** and 40 Sea Sparrows; these are not the missing original SM-6-inspired profile. RIM-66E retains stock guidance, range and target limits. No ballistic-missile interception capability is claimed. Other launcher proxies and original EW configuration are retained.

Original naval paint, small bridge panes, watertight doors, deck tyre marks, painted ship numbers, landing-light lenses, subdued deck guidance fixtures, brighter downward-facing hangar lamps. The controller creates night lamps when the game's sun intensity drops below its night threshold. Lamps have no shadows. Six-second native lift sequences move the platforms between the hangar and flight deck; native embark parenting carries aircraft with them. The design waterline stays at model Y=0; the preceding conservative drag and turning-heel settings are retained. Actual night appearance, lift cycles and rough-sea behaviour need an in-game check.

## Install

Use the supplied complete offline installer for this release. It contains the current game package and editable source, verifies its embedded archive and file manifest, and needs Python 3. No earlier installer is required. GitHub publication of v0.8.5 is pending; do not assume a raw GitHub download of this version is available.

Close Sea Power. Save the supplied v0.8.5 offline installer in Downloads, then run:

```bash
bash "$HOME/Downloads/install-ran-australis-v0.8.5-naval-details-offline.sh"
```

The offline installer verifies its embedded current package before running pre-install checks: your previously supplied game-DLL version, existing AnchorChain installation and current package integrity must pass before replacement. It finds the preloader under **BepInEx/plugins**, including nested folders. It installs our controller inside the enabled carrier mod. Backups are verified before replacing the existing Australis folder. A legacy controller directly under StreamingAssets is backed up and withdrawn to avoid duplicate loading. It does not modify stock, Workshop, RADF, User Data, BepInEx, or your launch options.

After verifying the installed hashes, the installer prints `[VERIFIED] RAN Australis Fleet v0.8.5 Naval Details` so you can identify the exact release. It also scans local mod folders and the Sea Power Workshop directory for competing copies of the same carrier vessel definitions. Each match is listed as `[OTHER COPY]` with its folder path; disable older Australis copies in the game mod menu. The diagnostic does not delete or change those copies. An unreadable folder produces a note that the scan was incomplete without invalidating the verified installation.

Retain your working Steam Proton launch option:

```text
WINEDLLOVERRIDES="winhttp.dll=n,b" %command%
```

Enable AnchorChain and RAN Australis Fleet v0.8.5 Naval Details, disable older Australis entries, restart, then open Australis-class and place a fresh variant in a new blank mission. Ready both aircraft groups before testing. Test repeated fixed-wing launch/recovery through all four lifts, the helicopter routes and pad priority, native lift down/up return to its upper home stop, CIWS deployment, vertical deck VLS firing, five damage-control teams, dusk/night and Standard carrier power. The first combat request waits for committed aviation to clear; aviation remains interlocked while defensive wells are open.

After placing a fresh carrier, check static waterline/trim, ahead and astern, steering both directions, nozzle motion, propulsion damage, and the existing aircraft operations. Compare against v0.7.0. Save logs if the hull sits incorrectly, a nozzle does not move or a native exception appears.

The installer supports `--check` and `--remove`. The log and verified backups are written to Downloads. To restore a previous release use `--restore BACKUP_DIRECTORY`, with the directory printed by this installer; it verifies backup hashes before replacement. Keep Sea Power closed. Saved missions can retain the old carrier model, routes or ammunition: always test a new ship first.

This waterjet prototype has not been tested in the Sea Power runtime. Send the installer output and `RAN-Australis-DeckController.log` from the enabled mod folder if it fails.

## Rebuild dependencies

The v0.8.5 viewer uses the current exported OBJ and INI geometry. Hull-number appearance is projected from the same per-variant PNG atlas used by the game. Preview texture sampling and studio shading are approximations; they do not simulate Unity lighting, the Mission Editor or native flight scheduling. All four variants use the common current mesh, with lifts at their 22.002 m upper home stop.

The source-generation workflow uses NumPy, Pillow, Shapely and SciPy; preview plots also use Matplotlib. The supplied offline installer uses only Python 3 standard-library modules and needs none of these source-build dependencies. A separately prepared network launcher also uses the standard library but needs an internet connection; its GitHub publication is pending.
