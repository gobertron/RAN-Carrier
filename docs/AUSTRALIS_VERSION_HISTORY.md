> **21 November 2026 — v1.3.2:** targeted bridge-window texture-coordinate and material repair after the v1.3.1 in-game retest showed the black strip persisted. Tower geometry, stable platform ID, aircraft configuration and night-lighting controller remain intact. [Release](https://github.com/gobertron/RAN-Carrier/releases/tag/v1.3.2) · [Source/evidence](../updates/v1.3.2/). Runtime visual correction still needs an in-game retest; package and installer results are recorded separately.

> **21 November 2026 — v1.3.1:** split five oversized static batches while retaining all 385,026 triangle faces and dimensions; remove the separate 24-aircraft test class, retain the canonical ID and four sister ships; add intact repeat-install no-op, recovery journal repair and a stable release launcher. [Release](https://github.com/gobertron/RAN-Carrier/releases/tag/v1.3.1) · [Source/evidence](../updates/v1.3.1/). 23 local filesystem regression checks passed; native Windows and live game results must be read separately from the release Actions run.

# RAN / HMAS Australis — development version history

Reconciled **15 November 2026** for *Sea Power: Naval Combat in the Missile Age*.

This table brings together the saved Australis artifacts, their release/installation notes, relevant source packages and the dedicated GitHub development branch. It includes earlier HMSCS naming, Australis 2030/2050 concepts, four-ship fleet variants and the Windows 11 rebuild. The current display-name preference is **RAN / HMAS Australis**.

**Latest documented delivery: v1.2.9 — Modded Aircraft Selection Fix.** This is an updater, not a self-contained carrier rebuild. **Latest complete carrier-source/build version found in GitHub: v0.8.5**, on `feature/australis-2050-concept`. The v1.2.9 patch source and Windows package are tracked here. Earlier later-version full models/controllers/installers remain catalogued separately from the complete source branch.

The audit found **no GitHub Release objects or version tags**. Version headings below describe development/delivery labels, not newly created tags or releases. No Steam Workshop publication or live game pass is inferred from an archive, preview or successful installer.

Dates are the release-note date where stated, otherwise the earliest saved artifact date converted to **Australia/Sydney**. “By 1 November” means the version was described in the earlier consolidated history; its exact release date was not recovered. Saved metadata can predate later edits/renames and does not by itself establish release order.

Downloads and related lists:

- [Version table as CSV](AUSTRALIS_VERSION_HISTORY.csv)
- [Complete artifact index](AUSTRALIS_ARTIFACT_INDEX.md) and [CSV](AUSTRALIS_ARTIFACT_INDEX.csv)
- [Machine-readable version register](australis-version-history.json)
- [Existing Australis source branch](https://github.com/gobertron/RAN-Carrier/tree/feature/australis-2050-concept)

## Version and change table

"Archive delivery" means the named delivery was recovered from the saved project record, while a matching version-specific build was not verified in the audited GitHub tree. A visual-only row establishes a saved version label, not an implemented feature.

| Version / name | Documented or saved date | What changed | Deliverable type | GitHub implementation evidence |
|---|---|---|---|---|
| [v0.4.0](#version-v0-4-0) — Historical reference | Unknown | Current spec credits original v0.4.0 lift positions and 22 x 26 m platforms as retained. | Reference only | [Reference in GitHub; release artifact not recovered](https://github.com/gobertron/RAN-Carrier/blob/6f3e5010dec72eded4a69bfcccb77c6c054c67b1/australis-2030/spec.json) |
| [v0.5.0](#version-v0-5-0) — Historical reference | Unknown | Listed as previous_version in v0.5.1 release metadata; no change summary or named artifact found in inspected current branch. | Reference only | [Reference in GitHub; release artifact not recovered](https://github.com/gobertron/RAN-Carrier/blob/6f3e5010dec72eded4a69bfcccb77c6c054c67b1/builds/Australis-v0.5.1-release.json) |
| [v0.5.1](#version-v0-5-1) — Five Repair Teams | 2026-10-25 | Five native repair teams; Dedicated ship page. | Published artifact and source | [Source and named build tracked](https://github.com/gobertron/RAN-Carrier/blob/6f3e5010dec72eded4a69bfcccb77c6c054c67b1/builds/Australis-v0.5.1-release.json) |
| [v0.5.3](#version-v0-5-3) — Independent Carrier Prototype | 2026-10-25 | Installed independent Australis package with verified controller/preloader dependency detection; Audited four lifts, the earlier three-bow/two-waist launch-track prototype, 80 VLS cells, 21 weapon systems, 11 sensors, two towed decoys and five damage-control teams; Verified game model bindings, stores and installer output; live combat/flight/animation tests remained pending. | Historical release notes | Archive delivery; matching GitHub build not verified |
| [v0.5.9](#version-v0-5-9) — Defensive Platforms and Helicopter Operations | 2026-10-25 | Defensive platforms stop 0.08 m above flight deck instead of a 24 m base; deploy 0.75 simulation seconds after committed aviation clears, hold 300 seconds after last shot, stow over 10 seconds; CIWS count rises from three to five with two roof-retracting mounts; between-tower mount moves starboard; shared 20 mm ammunition rises to 20,000; Helicopter pad priority aft, front, middle; independent pads retain shared-lift and same-pad conflicts; Native taxi speeds forward 15, backward -10, slow 10; LaunchDelay=1 and SpawnInterval=1. | Archived release notes only in current branch | [Release notes tracked; named build absent](https://github.com/gobertron/RAN-Carrier/blob/6f3e5010dec72eded4a69bfcccb77c6c054c67b1/australis-2030/releases/v0.5.9/README.md) |
| [v0.6.0](#version-v0-6-0) — Historical reference | Unknown | Installer described as lost; recovery build reconstructs subsequent requested features from recoverable v0.5.1 and is not a byte-for-byte restoration. | Reference only | [Reference in GitHub; release artifact not recovered](https://github.com/gobertron/RAN-Carrier/blob/6f3e5010dec72eded4a69bfcccb77c6c054c67b1/builds/README.md) |
| [v0.6.1](#version-v0-6-1) — Recovery reconstruction | 2026-10-26 | Rebuilt from recoverable v0.5.1 and v0.5.9 notes; four hulls, three catapults, four internal lifts, three helipads, five CIWS and five repair teams; six-second native lift travel and revised light fittings. | Recovery game package | Archive delivery; matching GitHub build not verified |
| [v0.6.2](#version-v0-6-2) — Forward CIWS recovery adjustment | 2026-10-26 | Recovery artifact and bow-CIWS preview survive; later v0.7.0 README confirms the forward CIWS had moved to port with covers clear of its catapult. | Recovery package / partial evidence | Archive delivery; matching GitHub build not verified |
| [v0.7.0](#version-v0-7-0) — Symmetric underwater hull | 2026-10-26 | Replaced asymmetric underwater body with a symmetric 110-station hull; added paired shafts, five-blade propellers, rudders and bilge keels; hull-shaped convex collider and approximately 112,000 t geometric displacement. | Recovery game package | Archive delivery; matching GitHub build not verified |
| [v0.8.0](#version-v0-8-0) — Eight-waterjet prototype | 2026-10-26 | Broadened stern for eight outlets, underside intakes and internal wet ducts; four steering nozzles and four fixed boosters; recalibrated net wet displacement near 112,000 t. | Experimental game package / engineering study | Archive delivery; matching GitHub build not verified |
| [v0.8.1](#version-v0-8-1) — Standard air operations speed | 2026-10-26 | Configured native telegraph ladder: Astern -7, Stop 0, Creep 6, Slow 12, Standard 20, Full 30 and Flank 30 knots; retained native aircraft eligibility and deck conflict rules. | Game configuration package | Archive delivery; matching GitHub build not verified |
| [v0.8.2](#version-v0-8-2) — Lift Lighting | 2026-10-26 | Eight recessed warm-white lights per shaft, 32 total, independently driven by actual lift height during day and night; fade from 0.60 m below deck and off within 0.10 m; Standard 20 kn, Full 30 kn and Flank 30 kn; Eight-waterjet broad-stern prototype with intake/outlet openings and wet ducts; four steering nozzles and four fixed boosters; flooded ducts accounted for in 112,000 t geometric displacement; Carries four numbered hulls, three catapults, four internal lifts, three helicopter pads, five retractable CIWS and five repair teams; six-second lift animations. | Published artifact and source | [Source and named build tracked](https://github.com/gobertron/RAN-Carrier/blob/6f3e5010dec72eded4a69bfcccb77c6c054c67b1/australis-2030/releases/v0.8.2/README.md) |
| [v0.8.3](#version-v0-8-3) — Stock-Catalogue Installer Fix | 2026-10-26 | Allows repeated catalogue divider headers in stock sensors.ini, resolving precheck failure at 40%; authored mod INIs remain strict; Retains v0.8.2 model, speeds and controller; separate ship definitions still produced dated submenus. | Archived package/installer; GitHub publication interrupted | [Release notes tracked; named build absent](https://github.com/gobertron/RAN-Carrier/blob/6f3e5010dec72eded4a69bfcccb77c6c054c67b1/australis-2030/releases/v0.8.3/README.md) |
| [v0.8.4](#version-v0-8-4) — Class and Flight Deck Fix | 2026-10-27 | Consolidates Australis-class into one vessel definition with four native variants: HMSCS Australis 91, Southern Cross 92, Federation 93 and Commonwealth 94; Lifts idle at flight-deck level 22.002 m, lower on demand and return upper; resolves lower-home busy-state conflict; All four lifts support fixed-wing routes: 12 lift-to-catapult, four arrested-recovery-to-lift, three helicopter launch and three helicopter recovery routes, 22 total; Three dedicated pads become helicopter-only; carrier-capable VTOL/STOL use catapult and arrested recovery; Retains v0.8.3 repeated stock catalogue header fix and compiled controller v0.8.2. | Published network installer and notes | [Source and named build tracked](https://github.com/gobertron/RAN-Carrier/blob/6f3e5010dec72eded4a69bfcccb77c6c054c67b1/australis-2030/releases/v0.8.4/README.md) |
| [v0.8.5](#version-v0-8-5) — Naval Details | 2026-10-27 | Enlarges hull numbers 91-94 on flight deck and main-island sides using native per-variant textures; Adds individual framed naval-style windows and decorative watertight-style doors aligned to actual surfaces; Updates four-ship viewer and matching renders from exported model geometry and number atlases; Retains v0.8.4 class/flight-deck fixes, 22 taxi routes, upper-home lifts and controller v0.8.2. | Published artifact and source | [Source and named build tracked](https://github.com/gobertron/RAN-Carrier/blob/6f3e5010dec72eded4a69bfcccb77c6c054c67b1/australis-2030/releases/v0.8.5/README.md) |
| [v0.8.6](#version-v0-8-6) — Deck Systems | 2026-10-27 | Added three native task-driven hinged blast deflectors (2.5 s to 65 degrees), aircraft-position-based landing display and supported/recessed light fittings; attached lift markings to moving platforms. | Game package / offline installer | Archive delivery; matching GitHub build not verified |
| [v0.8.7](#version-v0-8-7) — Tower integration | 2026-10-27 | A version-labelled visual artifact survives for tower integration. Exact code/model changes and a standalone game release are not established. | Visual artifact names only | Archive delivery; matching GitHub build not verified |
| [v0.8.9](#version-v0-8-9) — Hull, Towers, Flight Routing and Weapons | 2026-10-29 | Main/aft tower alignment, flat/angular surfaces, sightlines and roof weapons refined; ensign repositioned; Integrated revised bulbous bow detail; Revised lift-to-catapult preferences: L1→C2, L2→C1/C2, L3→C2, L4→C3 (earlier three-catapult layout; superseded later). | Historical release notes | Archive delivery; matching GitHub build not verified |
| [v0.9.4](#version-v0-9-4) — Combat clearance / concurrent operations | 2026-10-29 | A version-labelled visual artifact survives for combat clearance / concurrent operations. Exact code/model changes and a standalone game release are not established. | Visual artifact names only | Archive delivery; matching GitHub build not verified |
| [v0.9.5](#version-v0-9-5) — Night lighting | 2026-10-29 | A version-labelled visual artifact survives for night lighting. Exact code/model changes and a standalone game release are not established. | Visual artifact names only | Archive delivery; matching GitHub build not verified |
| [v0.9.6](#version-v0-9-6) — Crew stations | 2026-10-29 | A version-labelled visual artifact survives for crew stations. Exact code/model changes and a standalone game release are not established. | Visual artifact names only | Archive delivery; matching GitHub build not verified |
| [v0.9.7](#version-v0-9-7) — Tower alignment | 2026-10-29 | A version-labelled visual artifact survives for tower alignment. Exact code/model changes and a standalone game release are not established. | Visual artifact names only | Archive delivery; matching GitHub build not verified |
| [v0.9.8](#version-v0-9-8) — Weapon finish | 2026-10-29 | A version-labelled visual artifact survives for weapon finish. Exact code/model changes and a standalone game release are not established. | Visual artifact names only | Archive delivery; matching GitHub build not verified |
| [v0.9.9](#version-v0-9-9) — Hangar operations | 2026-10-29 | A version-labelled visual artifact survives for hangar operations. Exact code/model changes and a standalone game release are not established. | Visual artifact names only | Archive delivery; matching GitHub build not verified |
| [v0.10.0](#version-v0-10-0) — Hull / radar fit | 2026-10-30 | A version-labelled visual artifact survives for hull / radar fit. Exact code/model changes and a standalone game release are not established. | Visual artifact names only | Archive delivery; matching GitHub build not verified |
| [v0.10.4](#version-v0-10-4) — Vertical CIWS Deployment | By 2026-11-01 | Five CIWS changed to a staged housing/roof/gun vertical deployment design; Target deployment time 4.5 seconds; retraction about 300 seconds after a quiet period; Threat/Free Fire deployment and automatic missile self-defence under Hold Fire designed into controller logic. | Historical release notes | Archive delivery; matching GitHub build not verified |
| [v0.10.5](#version-v0-10-5) — Raised CIWS Housings | By 2026-11-01 | All five CIWS housings raised by approximately 4.7 m into the dark-grey hull band immediately beneath the flight deck; Vertical deployment concept, firing policy and retraction timing retained. | Historical release notes | Archive delivery; matching GitHub build not verified |
| [v0.10.6](#version-v0-10-6) — Four-Catapult Controller | By 2026-11-01 | Added a fourth usable launch lane: two bow and two waist catapults; Added queueing of conflicting deck movements and recovery interlocks for C3/C4; Previously raised CIWS housings retained. In-game verification outstanding. | Historical release notes | Archive delivery; matching GitHub build not verified |
| [v0.10.7](#version-v0-10-7) — Compact Waist Zone / Stern Recovery | By 2026-11-01 | C3/C4 regrouped into a compact shared waist area, taking turns to avoid conflicts; Their planned paths cleared C1/C2; The angled landing area extended to the aft edge of the ship; waist launch lockout during recovery retained. | Historical release notes | Archive delivery; matching GitHub build not verified |
| [v0.10.8](#version-v0-10-8) — Forward Waist-Catapult Relocation | By 2026-11-01 | C3/C4 moved toward the forward/port weapons area and away from helicopter pads, lifts and recovery lanes; Shared aircraft routes queued; landing lockout retained. Offline checks passed, live tests pending. | Historical release notes | Archive delivery; matching GitHub build not verified |
| [v0.10.9](#version-v0-10-9) — Staggered Waist Catapult Study | By 2026-11-01 | Ford-inspired staggered C3/C4 placement, approximately 24 m apart, with angled tracks behind the bow pair; Deck traffic queuing, combined launch controls and landing interlocks refined; Offline tests passed. Superseded by the distinct outboard launch lanes of v0.10.10. | Historical release notes | Archive delivery; matching GitHub build not verified |
| [v0.10.10](#version-v0-10-10) — Outboard Waist Deck | By 2026-11-01 | C1/C2 bow catapults retained in their established arrangement; C3/C4 rebuilt as distinct, physically supported launch lanes on a port/outboard deck extension; C3/C4 clear the bow tracks; conflicting taxi and launch movements queue. | Historical release notes | Archive delivery; matching GitHub build not verified |
| [v0.10.11](#version-v0-10-11) — Touching Forward Lifts | By 2026-11-01 | Lift 1 and Lift 2 brought together at a clean common edge; independent lift travel retained; Native model, hangar/shaft interfaces, deck paint and adjacent structural clearances revised; Four-track outboard deck, stern landing route, traffic queuing and CIWS provisions retained. | Complete game package and offline installer | Archive delivery; matching GitHub build not verified |
| [v0.10.11-W1](#version-v0-10-11-w1) — Naval Grey and Weathered Finish | 2026-11-05 | Applied naval-grey service-wear textures, darker non-skid deck and revised UV mapping to the actual game model; retained geometry and gameplay. | Appearance patch | Archive delivery; matching GitHub build not verified |
| [v0.10.12](#version-v0-10-12) — Naval Bow Update | 2026-11-05 | Reshaped the dry bow while retaining the calibrated underwater hull; checked mesh displacement, draft and configured centre of mass offline. | Native-model patch | Archive delivery; matching GitHub build not verified |
| [v0.10.13](#version-v0-10-13) — Maintained Service / Fixed CIWS | 2026-11-05 | Applied maintained service-grey Option A finish and five fixed elevated CIWS platforms with matching mounts/controller; introduced Windows PowerShell installer and controller-placement cleanup. | Windows updater and complete mod | Archive delivery; matching GitHub build not verified |
| [v0.10.14](#version-v0-10-14) — Option C Finish | 2026-11-07 | Applied Option C material colours: darker charcoal deck, lighter upperworks and cool-grey hull; retained wear textures and geometry. | Windows updater and complete mod | Archive delivery; matching GitHub build not verified |
| [v0.10.15](#version-v0-10-15) — Hull-Integrated Revision | 2026-11-07 | Integrated curved deck/CIWS supports into the hull, increased bow stem rake and added individual ship identification bands; retained nominal hull dimensions and wet-volume/trim values. | Windows updater and complete mod | Archive delivery; matching GitHub build not verified |
| [v0.10.16](#version-v0-10-16) — Bridge, ICCS Bubble and Galleries | 2026-11-07 | Added all-round aft-bridge glazing, retracting ICCS bubble between C1/C2 and hull-integrated weapon galleries. | Windows updater and complete mod | Archive delivery; matching GitHub build not verified |
| [v0.10.17](#version-v0-10-17) — Quality of Life | 2026-11-07 | Added decorative crew safety/service fittings, readable controller admission feedback and optional read-only Deck Watcher. | Windows updater and complete mod | Archive delivery; matching GitHub build not verified |
| [v0.10.18](#version-v0-10-18) — Forward Retracting CIWS | 2026-11-07 | Added retracting forward-port sixth CIWS with C3/C4 interlocks and state feedback; retained five fixed mounts and ICCS. | Windows updater and complete mod | Archive delivery; matching GitHub build not verified |
| [v0.10.19](#version-v0-10-19) — Crew Safety and Stern Loading Concept | 2026-11-07 | Previewed extra raft racks, catch nets, crew access/lighting and rounded CIWS surround, plus rear folding-ramp/vestibule concept; playable v0.10.18 unchanged. | 3D design preview only | Archive delivery; matching GitHub build not verified |
| [v0.10.20](#version-v0-10-20) — Enlarged Stern Loading Review | 2026-11-07 | Enlarged preview stern opening to 28 × 8 m and widened the enclosed loading route with matching ramp/barriers; game loading integration deferred. | 3D design preview only | Archive delivery; matching GitHub build not verified |
| [v0.10.21](#version-v0-10-21) — Fixed Closed Rear Doors | 2026-11-07 | Replaced opening-ramp concept with decorative fixed-closed 28 × 8 m rear doors; removed loading/opening controls. | 3D design preview only | Archive delivery; matching GitHub build not verified |
| [v0.10.22](#version-v0-10-22) — Exterior Survival and Landing Lights | 2026-11-07 | Previewed 288 raft canisters, six rescue stations and eighteen additional landing-strip inset lights, with nominal 7,200 raft places. | 3D design preview only | Archive delivery; matching GitHub build not verified |
| [v0.10.23](#version-v0-10-23) — Flush Raft Cradles and CIWS Surround | 2026-11-07 | Made raft cradles follow the hull and cleaned forward-CIWS surround mesh/UV defects; retained canister size/count. | 3D design preview only | Archive delivery; matching GitHub build not verified |
| [v0.10.24](#version-v0-10-24) — Hull Alignment / Windows Game Build | 2026-11-07 | Aligned hull/CIWS supports and tower arrays, cleared hatches and packaged the approved model with stock-air-wing derivation and Windows installer fixes; per-face sensor sectors remain design-only. | 3D design preview, then complete Windows game package | Archive delivery; matching GitHub build not verified |
| [v0.10.25](#version-v0-10-25) — Native Model Hotfix | 2026-11-08 | Registered 99 omitted native model parts to restore CIWS/enclosure references, closed forward hull seam and separated rear-tower glazing; retained v0.10.24 controller. | Complete Windows game package / native-model hotfix | Archive delivery; matching GitHub build not verified |
| [v0.10.26](#version-v0-10-26) — Rear Tower Model Repair | 2026-11-08 | Corrected rear-tower face directions/normals and shell joins; retained previous model hotfixes and did not claim a script-startup-timeout fix. | Complete Windows game package / tower geometry hotfix | Archive delivery; matching GitHub build not verified |
| [v1.0](#version-v1-0) — Basic Shell | 2026-11-08 | Reduced to unarmed static hull, deck and islands with native movement/physics; no aircraft operations, weapon, operating sensor, decoy or custom controller; Kept independent unit ID ran_australis_basic_shell and approximately 370 m / 112,000 tonne / 30 knot game configuration. | Independent native-only reduced carrier package | Archive delivery; matching GitHub build not verified |
| [v1.0.1](#version-v1-0-1) — Basic Shell installer (model v1.0.0) | 2026-11-08 | One self-contained Windows CMD with embedded verified model ZIP, explicit installer/game path handling, phase-specific failure reporting and transcript logs; Installer v1.0.1 carries Basic Shell model v1.0.0 and checks its complete hash manifest before installation. | Single-CMD installer revision, not new model version | Archive delivery; matching GitHub build not verified |
| [v1.0.2](#version-v1-0-2) — Basic Shell | 2026-11-08 | Corrected shell model and matching v1.0.2 identity/manifest in a self-contained installer; Recognizes an unmodified v1.0.0 shell, stages the replacement, backs up the old shell, verifies activation and restores it on failure; modified or unknown prior shells are refused. | Corrected native-only shell plus installer | Archive delivery; matching GitHub build not verified |
| [v1.1.0](#version-v1-1-0) — Flight Deck Stage 1 | 2026-11-13 | Restored four animated lifts, four catapult lanes and blast deflectors, angled arrested recovery area and return taxi routes on the working Basic Shell; Added combined carrier plus four isolated C1/C2/C3/C4 calibration entries, with a small installed-stock-aircraft test wing; Still unarmed; operating sensors, helicopter operations and old custom deck-controller remain excluded. | Independent controlled flight-deck test package | Archive delivery; matching GitHub build not verified |
| [v1.2.0](#version-v1-2-0) — Full Restore | 2026-11-13 | Restored v0.10.26 systems: 4 lifts, 4 catapults and 3 vertical pads; 1 arrested and 3 vertical recovery points, 15 taxi routes and 16 deck zones; Restored 24 weapon entries including 6 CIWS, 12 sensors, 66 enclosed-bay mechanisms, forward CIWS6, ICCS, lighting, safety fittings, 8 waterjets and 4 steering units; Provided Full99 mixed wing (72 fixed-wing/STOL, 15 helicopter, 12 VTOL) and Test24 profile (16/4/4), derived from installed stock definitions; Batched only unreferenced static geometry: registered visual parts 1,687 to 529 while preserving 380,558 triangles, mechanism aliases and audited controller bytes; repaired aft-bridge glow alias partition. | Full carrier restoration package | Archive delivery; matching GitHub build not verified |
| [v1.2.1](#version-v1-2-1) — Full Restore reliability | 2026-11-13 | Added missing generic VTOL CircuitWaypoints and ExitPosition at the three existing vertical recovery pads; retained fixed-wing recovery geometry and controller; Added aviation route/circuit/count preflight, protected edited/unowned files on upgrade and journaled obsolete-owned-file retirement; Expanded duplicate native-ID reporting across local mods and Workshop; included session Collect mode with scoped CPU/memory/log capture. | Full restoration reliability revision | Archive delivery; matching GitHub build not verified |
| [v1.2.2](#version-v1-2-2) — Compatibility Check | 2026-11-13 | Collected actual game/core/preloader/controller hashes, Steam build identity, native metadata/signature/fingerprint evidence, relevant mod/load-order and carrier configuration; Used a pinned metadata reader to inspect the newly observed game assembly without executing target DLL code or bypassing the installer compatibility gate. | Read-only diagnostics; not carrier-model update | Archive delivery; matching GitHub build not verified |
| [v1.2.3](#version-v1-2-3) — Lighting Patch / Archive and Update | 2026-11-13 | Corrected dense storm/fog and below-horizon activation, unlit lens/window visibility, per-pixel mounted lamps, retry after temporary lamp initialization failures and lighting diagnostics; Changed only NightLights.cs and LowLightPolicy.cs; retained geometry, aviation, weapons, sensors and other controller mechanisms; Base mod still identifies as v1.2.0; v1.2.3 identifies the patch; Staged and verified installed full ship, applied v1.2.3 lighting DLL and metadata, moved recognized local Australis copies outside active StreamingAssets and activated one canonical full copy; Added repeat-safe operation, transaction recovery and exact previous-folder restoration; preserved user air wing and unrelated mods. | Controller lighting-only patch for v1.2.0 / Archive-before-update installer carrying the same lighting patch | Archive delivery; matching GitHub build not verified |
| [v1.2.4](#version-v1-2-4) — All Carrier Aircraft | 2026-11-13 | Expanded AircraftSupported to validated original carrier/amphib fixed-wing/STOL plus all validated stock VTOL/helicopters; retained custom supported/embarked IDs; Recognized native-only Basic Shell copies for duplicate archiving; kept v1.2.3 lighting, existing air wing, 99 capacity and flight geometry/routes. | Cumulative archive updater and catalogue expansion | Archive delivery; matching GitHub build not verified |
| [v1.2.5](#version-v1-2-5) — Detection Fix | 2026-11-13 | Accepted both audited original v0.10.26 and Full Restore model hashes plus supported lighting controllers; Created missing RUNTIME-FILES.json only in staged copy; supported game-root or StreamingAssets input; canonical active folder changed to RAN-HMAS-Australis; Retained lighting and carrier/VTOL/helicopter catalogue; printed detected versions/hashes before mutation. | Cumulative archive updater with legacy installation compatibility | Archive delivery; matching GitHub build not verified |
| [v1.2.6](#version-v1-2-6) — All Stock Aircraft | 2026-11-13 | Included every readable original-game Aircraft/STOL/VTOL/Helicopter definition, including land aircraft/bombers; removed roster/year/nationality/size and missing-squad-file exclusions; Read only General/UnitType to tolerate repeated decorative sections; preserved existing air wing/custom IDs, 99 capacity, geometry, routes and lighting. | Cumulative archive updater with all-stock selection catalogue | Archive delivery; matching GitHub build not verified |
| [v1.2.7](#version-v1-2-7) — Controller Startup Repair | 2026-11-13 | Diagnosed 'Could not find AnchorChain chainloader' with stale controller timestamps; replaced supported old preloader with verified official AnchorChain 1.2.0 discovery/retry DLL; Backed up/restored preloader and local ship folders as one recovery transaction; retained all-stock catalogue and lighting controller; Included mechanism diagnostic collection for confirming fresh bindings and CIWS6/ICCS/weapon bay behavior. | Cumulative ship updater plus official preloader repair | Archive delivery; matching GitHub build not verified |
| [v1.2.8](#version-v1-2-8) — In-Game Info Sheet | 2026-11-13 | Wrote ship information sheet to _info.ini Language_en Description and language_en/vessel_names.ini DefaultDescription for the existing class/variants; Documented fictional naval strike/sea control role, configured dimensions/displacement/speed/propulsion, 99 capacity, four catapults/four lifts/three pads, layered defence/sensors and four hull identities; Included matching readable Australis-Info-Sheet.txt and retained lighting, all-stock catalogue, archiving and official preloader repair. | Cumulative ship updater with Mod Manager and encyclopedia descriptions | Archive delivery; matching GitHub build not verified |
| [v1.2.9](#version-v1-2-9) — Modded Aircraft Selection Fix | 2026-11-15 | Discovers aircraft from enabled local/Workshop mods and the user tree; refreshes AircraftSupported on every run while preserving the existing air wing, routes and base version; verified backup/restore and ownership-hash updates. | Windows selection-list patch; existing carrier required | [Source and package](../updates/v1.2.9/README.txt) |



## Latest Windows delivery relationship

[v1.2.9 download](../builds/HMAS-Australis-v1.2.9-Modded-Aircraft-Selection-Fix-Windows11.zip) adds enabled mod aircraft to the selection list of an existing full local carrier. Enable the aircraft mods, exit the game, run Refresh, then restart with a new carrier. It is repeatable after adding more mods and retains the underlying carrier version label.

The original Basic Shell, Flight Deck Stage 1 and Full Restore packages have different scopes. v1.2.2 is a **read-only compatibility checker**. v1.2.3 has both a **lighting-only patch for v1.2.0** and a separate **archive/update tool**. v1.2.4–v1.2.8 are updates applied to a detected existing Australis installation, not complete standalone model archives. Follow each package's own prerequisites; the version numbers alone do not establish an installation chain.

The “all aircraft” v1.2.6 catalogue can include land-based aircraft. A catalogue entry is not proof of supported deck clearance, launch or arrested recovery. The v1.2.7 controller startup repair was delivered after CIWS6, ICCS and weapon-bay failures; a successful live retest of every mechanism is still unconfirmed in the recovered evidence. v1.2.8 adds descriptions while retaining that repair.

## Supporting work and visual variants

The artifact index also covers the unversioned appearance reviews, three-dimensional viewers, native-model reference images, night view of v1.2.0, Workshop descriptions and artwork, metadata/name repair, world-carrier comparisons, runtime diagnostics, startup/code isolation tools and mechanism diagnostic collectors/results. These are supporting deliverables, not additional carrier releases. The early Linux shell installers are historical artifacts; current delivery packages target Windows 11.

The 8 October fleet/restart concepts are ancestry of Australis. Shared carrier reference archives are indexed as inputs, not newly authored Australis releases. The separate Melbourne 1959 prototype branch and the F-111N aircraft project are not counted as Australis version releases.

## History gaps and interpretation

- v0.4.0 and v0.5.0 survive as references; complete individual release histories were not recovered.
- v0.6.0 is explicitly described as lost. v0.6.1 is a reconstruction rather than a byte-for-byte restoration.
- v0.8.8, v0.9.0–v0.9.3 and v0.10.1–v0.10.3 lack independently recovered change notes/artifacts in this audit. No changes are invented for them.
- v0.8.7, v0.9.4–v0.9.9 and v0.10.0 have version-labelled visual filenames, with detailed implementation unestablished.
- The saved v0.6.2, v0.8.0 and v0.8.3 ZIPs had unreadable central directories during this inspection. Corroborating later notes or GitHub documents are used where available; this audit does not certify those ZIPs as installable.
- CIWS design changed over time: five retractable mounts, then five fixed raised mounts in v0.10.13, then an additional retractable forward CIWS6 in v0.10.18. Earlier descriptions are superseded by the applicable version rather than combined into one specification.
- The historical 99-aircraft target, geometry/ballast calculations and controller fixture results are not a demonstrated full-capacity live flight/combat test.

## Unversioned development commits

These are commit milestones, not invented semantic-version releases. Commit messages provide the summary; they do not establish a live game result.

| Sydney date | Development milestone | Commit |
|---|---|---|
| 2026-10-09 | Add 14 Royal Australian Navy carrier design concepts | [82e49fb9](https://github.com/gobertron/RAN-Carrier/commit/82e49fb95189f3914a79e9eab388a2f022fd89f8) |
| 2026-10-10 | Add original faceted Australis 2050 carrier concept | [a3e8560f](https://github.com/gobertron/RAN-Carrier/commit/a3e8560fe6f4128bb3dcf4fa8acc905871eaf05e) |
| 2026-10-10 | Keep Australis concept build isolated from parent cache files | [807ebd98](https://github.com/gobertron/RAN-Carrier/commit/807ebd98bf9a0b21b28442893cb225f6e5f676a8) |
| 2026-10-10 | Align Australis dimensions with the 370 by 104 metre concept | [560c159e](https://github.com/gobertron/RAN-Carrier/commit/560c159e285d4428d359e56d2f438b46c7eeda24) |
| 2026-10-10 | Add four aft VTOL helicopter spots and three catapults to Australis | [9aa99c6a](https://github.com/gobertron/RAN-Carrier/commit/9aa99c6a99ca65b9e9559ba57f4787e7e2b966d8) |
| 2026-10-10 | Give Australis 2050 two islands and staggered angled VTOL pads | [1c2654dd](https://github.com/gobertron/RAN-Carrier/commit/1c2654dd6018de1c3689ed6c3e05b1b51889f74e) |
| 2026-10-10 | Separate Australis launch and VTOL lanes from lifts and islands | [3cd9c86a](https://github.com/gobertron/RAN-Carrier/commit/3cd9c86acbdb9a131d70e80817386773bfc3a743) |
| 2026-10-10 | Revise Australis as 2030 with starboard catapult and midship lift | [7d314ad3](https://github.com/gobertron/RAN-Carrier/commit/7d314ad3541c3f6cee492907db54b923bfbde90f) |
| 2026-10-10 | Add offline interactive 3D viewer for Australis 2030 | [7461b81e](https://github.com/gobertron/RAN-Carrier/commit/7461b81e5fd6d9f658f17042677a7e9ed66629f6) |
| 2026-10-10 | Join Australis hull to full flight-deck perimeter | [86aa0463](https://github.com/gobertron/RAN-Carrier/commit/86aa0463a1546504fa072799f3ad6dbf8037a383) |
| 2026-10-10 | Taper Australis bow to waterline stem and add bow preview | [289b3088](https://github.com/gobertron/RAN-Carrier/commit/289b308805c0057a49bd7e2b8a79478a15d6110b) |
| 2026-10-10 | Refine Australis hull and carrier deck with retractable laser study | [d6d2e731](https://github.com/gobertron/RAN-Carrier/commit/d6d2e7314b137558635fd3014018fac2ef981fc2) |
| 2026-10-10 | Add standalone Australis 2030 editor-test package and safe installer | [c280d597](https://github.com/gobertron/RAN-Carrier/commit/c280d5979055bf9b522776d1109c8a4127503773) |
| 2026-10-12 | Add Australis editor diagnostics and correct checkout instructions | [44a4084e](https://github.com/gobertron/RAN-Carrier/commit/44a4084ecf4599c0d7ee1a97c2b3b8a608bb41d0) |
| 2026-10-12 | Export Australis OBJ with UV and normal face indices | [e2f432d0](https://github.com/gobertron/RAN-Carrier/commit/e2f432d090d1f705c23bf8dbc957a124c54a813a) |
| 2026-10-12 | Add Australis collision mesh and resolve editor effect reference | [4eb69f75](https://github.com/gobertron/RAN-Carrier/commit/4eb69f75a68503ec7cf8facaad7c2ccac5cf83c0) |
| 2026-10-12 | Initialize Australis stern foam trail for rudder setup | [cbdaef47](https://github.com/gobertron/RAN-Carrier/commit/cbdaef47ac4852d358ed4b6abb327d8008c0063c) |
| 2026-10-22 | Refine Australis flag, bow fairing and port lift placement | [e587b60a](https://github.com/gobertron/RAN-Carrier/commit/e587b60a21d0dd6c75f9b90df0f154624610493e) |
| 2026-10-22 | Space Australis catapults and enable paired launch scheduling | [26b5cc1f](https://github.com/gobertron/RAN-Carrier/commit/26b5cc1fa1eef9db1234c4973cc37c815629ae8a) |
| 2026-10-22 | Size Australis lifts for F-14A and centre aircraft ride positions | [74e378ee](https://github.com/gobertron/RAN-Carrier/commit/74e378eee0a4dc20920af45316ff61ee43620c2b) |
| 2026-10-22 | Build five-lane Australis CATOBAR layout and declared combat fit | [fae6b9d1](https://github.com/gobertron/RAN-Carrier/commit/fae6b9d1238a3c59f3884fe031270c0cd95dc838) |
| 2026-10-22 | Australis: place three catapults at bow and two on port waist | [016fde6f](https://github.com/gobertron/RAN-Carrier/commit/016fde6f9b6daeb598a4d0a674eea84a88850921) |
| 2026-10-23 | Refine Australis waist catapults and deck fittings | [d4e9b151](https://github.com/gobertron/RAN-Carrier/commit/d4e9b151fa8f127607f2e2da2bba4955cfa11c6b) |
| 2026-10-23 | Fix Australis gun barrel references and aircraft deck contact; revise defensive deck fit | [fb57038f](https://github.com/gobertron/RAN-Carrier/commit/fb57038ffa0fa2a6834d39fef567aad2ad61f633) |
| 2026-10-24 | Rebuild Australis with near-flush aircraft contact surfaces | [a4b56566](https://github.com/gobertron/RAN-Carrier/commit/a4b5656605434e75a6e0e80c33744308e0df4a99) |
| 2026-10-24 | Enable broad carrier aircraft support and clear larger waist approaches | [9629c2a3](https://github.com/gobertron/RAN-Carrier/commit/9629c2a35af83290ffa6762d74bba09caf817f2a) |
| 2026-10-24 | Refresh Australis viewer with matching current-model photos | [e0414217](https://github.com/gobertron/RAN-Carrier/commit/e04142174e9e3ee41dd5b5dcf85d385133de5cf3) |
| 2026-10-24 | Package verified Australis carrier build for installation | [16200d73](https://github.com/gobertron/RAN-Carrier/commit/16200d73ac2aad762114bf9114f04fb8b8c64d21) |
| 2026-10-24 | Add engagement-driven retractable CIWS to Australis | [6bd0366b](https://github.com/gobertron/RAN-Carrier/commit/6bd0366bde6667178909198f43b0ed68c24c355f) |
| 2026-10-24 | Package retractable-CIWS Australis build with verified installer | [005fd729](https://github.com/gobertron/RAN-Carrier/commit/005fd729dd7b20be09f1958d7af78bb7a93be7f0) |

## Evidence by version

Evidence paths below identify the exact recovered notes or package members used for each summary. Later archives remain in the saved project collection; their presence here does not mean that they are available as GitHub downloads.

<a id="version-v0-4-0"></a>

### v0.4.0 — Historical reference

Evidence: `australis-2030/spec.json`.

GitHub: [australis-2030/spec.json](https://github.com/gobertron/RAN-Carrier/blob/6f3e5010dec72eded4a69bfcccb77c6c054c67b1/australis-2030/spec.json).

<a id="version-v0-5-0"></a>

### v0.5.0 — Historical reference

Evidence: `builds/Australis-v0.5.1-release.json`.

GitHub: [builds/Australis-v0.5.1-release.json](https://github.com/gobertron/RAN-Carrier/blob/6f3e5010dec72eded4a69bfcccb77c6c054c67b1/builds/Australis-v0.5.1-release.json).

<a id="version-v0-5-1"></a>

### v0.5.1 — Five Repair Teams

Evidence: `builds/Australis-v0.5.1-release.json`; `builds/README.md`; `a8dc55b2980cb3682c42179decb372e2f6b704b6`.

GitHub: [builds/Australis-v0.5.1-release.json](https://github.com/gobertron/RAN-Carrier/blob/6f3e5010dec72eded4a69bfcccb77c6c054c67b1/builds/Australis-v0.5.1-release.json) · [builds/README.md](https://github.com/gobertron/RAN-Carrier/blob/6f3e5010dec72eded4a69bfcccb77c6c054c67b1/builds/README.md) · [a8dc55b2](https://github.com/gobertron/RAN-Carrier/commit/a8dc55b2980cb3682c42179decb372e2f6b704b6).

Tracked builds: `builds/RAN-Carrier-Australis-v0.5.1-Five-Repair-Teams.zip`; `builds/install-ran-australis-v0.5.1.sh`.

<a id="version-v0-5-3"></a>

### v0.5.3 — Independent Carrier Prototype

Evidence: `RAN_Australis_Full_Version_History.txt`.

Limits: Original detailed source/package not recovered for every historical row; offline checks are not live game confirmation.

<a id="version-v0-5-9"></a>

### v0.5.9 — Defensive Platforms and Helicopter Operations

Evidence: `australis-2030/releases/v0.5.9/README.md`; `130e9062206697f5da281f3bdcad2519ab60fadd`.

GitHub: [australis-2030/releases/v0.5.9/README.md](https://github.com/gobertron/RAN-Carrier/blob/6f3e5010dec72eded4a69bfcccb77c6c054c67b1/australis-2030/releases/v0.5.9/README.md) · [130e9062](https://github.com/gobertron/RAN-Carrier/commit/130e9062206697f5da281f3bdcad2519ab60fadd).

Limits: The current branch has archived notes but no v0.5.9-named standalone ZIP/installer. Do not imply that those artifacts are available there.

<a id="version-v0-6-0"></a>

### v0.6.0 — Historical reference

Evidence: `builds/README.md`; `australis-2030/README.md`; `game-mod/RAN-Carrier-Australis-2030/recovery-release.json`.

GitHub: [builds/README.md](https://github.com/gobertron/RAN-Carrier/blob/6f3e5010dec72eded4a69bfcccb77c6c054c67b1/builds/README.md) · [australis-2030/README.md](https://github.com/gobertron/RAN-Carrier/blob/6f3e5010dec72eded4a69bfcccb77c6c054c67b1/australis-2030/README.md) · [game-mod/RAN-Carrier-Australis-2030/recovery-release.json](https://github.com/gobertron/RAN-Carrier/blob/6f3e5010dec72eded4a69bfcccb77c6c054c67b1/game-mod/RAN-Carrier-Australis-2030/recovery-release.json).

<a id="version-v0-6-1"></a>

### v0.6.1 — Recovery reconstruction

Evidence: `RAN-Carrier-Australis-v0.6.1-Recovery.zip / RECOVERY-README.md`.

Limits: Reconstruction, not a byte-for-byte restoration of lost v0.6.0. Live game testing unconfirmed.

<a id="version-v0-6-2"></a>

### v0.6.2 — Forward CIWS recovery adjustment

Evidence: `RAN-Carrier-Australis-v0.6.2-Recovery.zip (filename only)`; `Australis-v0.6.2-Bow-CIWS.png (filename only)`; `RAN-Carrier-Australis-v0.7.0-Recovery.zip / RECOVERY-README.md`.

Limits: The saved v0.6.2 ZIP central directory could not be read. Detailed changes are limited to the subsequent v0.7.0 note; archive not repaired.

<a id="version-v0-7-0"></a>

### v0.7.0 — Symmetric underwater hull

Evidence: `RAN-Carrier-Australis-v0.7.0-Recovery.zip / RECOVERY-README.md`.

Limits: Geometric/conditional hydrostatic values and game settings only; live waterline, handling and aviation not confirmed.

<a id="version-v0-8-0"></a>

### v0.8.0 — Eight-waterjet prototype

Evidence: `Australis-v0.8.0-Engineering-Review.md`; `RAN_Australis_Full_Version_History.txt`.

Limits: Saved ZIP central directory could not be read; changes corroborated by standalone engineering review and subsequent readable packages. Native aggregate propulsion does not model eight independent thrust systems.

<a id="version-v0-8-1"></a>

### v0.8.1 — Standard air operations speed

Evidence: `RAN-Carrier-Australis-v0.8.1-Standard-Air-Ops.zip / RECOVERY-README.md`.

<a id="version-v0-8-2"></a>

### v0.8.2 — Lift Lighting

Evidence: `australis-2030/releases/v0.8.2/README.md`; `builds/README.md`; `7a201850ff180213ca766dcbbb9bceaedb6c7e94`.

GitHub: [australis-2030/releases/v0.8.2/README.md](https://github.com/gobertron/RAN-Carrier/blob/6f3e5010dec72eded4a69bfcccb77c6c054c67b1/australis-2030/releases/v0.8.2/README.md) · [builds/README.md](https://github.com/gobertron/RAN-Carrier/blob/6f3e5010dec72eded4a69bfcccb77c6c054c67b1/builds/README.md) · [7a201850](https://github.com/gobertron/RAN-Carrier/commit/7a201850ff180213ca766dcbbb9bceaedb6c7e94).

Tracked builds: `builds/RAN-Carrier-Australis-v0.8.2-Lift-Lighting.zip`; `builds/install-ran-australis-v0.8.2-lift-lighting.sh`.

Limits: Immutable old installer can stop on repeated stock sensors.ini catalogue divider headings. Superseded.

<a id="version-v0-8-3"></a>

### v0.8.3 — Stock-Catalogue Installer Fix

Evidence: `australis-2030/releases/v0.8.3/README.md`.

GitHub: [australis-2030/releases/v0.8.3/README.md](https://github.com/gobertron/RAN-Carrier/blob/6f3e5010dec72eded4a69bfcccb77c6c054c67b1/australis-2030/releases/v0.8.3/README.md).

Limits: Notes explicitly say GitHub installer publication was interrupted. Correction included in v0.8.4. No v0.8.3 standalone installer in current tree.

<a id="version-v0-8-4"></a>

### v0.8.4 — Class and Flight Deck Fix

Evidence: `australis-2030/releases/v0.8.4/README.md`; `builds/README.md`.

GitHub: [australis-2030/releases/v0.8.4/README.md](https://github.com/gobertron/RAN-Carrier/blob/6f3e5010dec72eded4a69bfcccb77c6c054c67b1/australis-2030/releases/v0.8.4/README.md) · [builds/README.md](https://github.com/gobertron/RAN-Carrier/blob/6f3e5010dec72eded4a69bfcccb77c6c054c67b1/builds/README.md).

Tracked builds: `builds/install-ran-australis-v0.8.4-class-list-fix.sh`.

Limits: No v0.8.4 ZIP/offline installer in current branch tree; source notes call them separate deliverables. Native state simulation passed 20 cycles per lift, but live testing unconfirmed.

<a id="version-v0-8-5"></a>

### v0.8.5 — Naval Details

Evidence: `australis-2030/releases/v0.8.5/README.md`; `README.md`; `VERSION`; `6f3e5010dec72eded4a69bfcccb77c6c054c67b1`.

GitHub: [australis-2030/releases/v0.8.5/README.md](https://github.com/gobertron/RAN-Carrier/blob/6f3e5010dec72eded4a69bfcccb77c6c054c67b1/australis-2030/releases/v0.8.5/README.md) · [README.md](https://github.com/gobertron/RAN-Carrier/blob/6f3e5010dec72eded4a69bfcccb77c6c054c67b1/README.md) · [VERSION](https://github.com/gobertron/RAN-Carrier/blob/6f3e5010dec72eded4a69bfcccb77c6c054c67b1/VERSION) · [6f3e5010](https://github.com/gobertron/RAN-Carrier/commit/6f3e5010dec72eded4a69bfcccb77c6c054c67b1).

Tracked builds: `builds/RAN-Carrier-Australis-v0.8.5-Naval-Details.zip`; `builds/install-ran-australis-v0.8.5-naval-details-offline.sh`; `builds/install-ran-australis-v0.8.5-naval-details.sh`.

Limits: Latest source/artifacts on this GitHub branch at audit time; this does not mean latest delivery across user conversations.

<a id="version-v0-8-6"></a>

### v0.8.6 — Deck Systems

Evidence: `install-ran-australis-v0.8.6-deck-systems-offline.sh / embedded RECOVERY-README.md`.

Limits: Embedded payload inspected without executing installer; visual and flight behavior require live checks.

<a id="version-v0-8-7"></a>

### v0.8.7 — Tower integration

Evidence: `Australis-v0.8.7-Tower-Integration.png`.

Limits: Metadata inventory only; no gameplay or implementation claim is inferred from the image filename.

<a id="version-v0-8-9"></a>

### v0.8.9 — Hull, Towers, Flight Routing and Weapons

Evidence: `RAN_Australis_Full_Version_History.txt`.

Limits: Original detailed source/package not recovered for every historical row; offline checks are not live game confirmation.

<a id="version-v0-9-4"></a>

### v0.9.4 — Combat clearance / concurrent operations

Evidence: `Australis-v0.9.4-Combat-Clearance.png`; `Australis-v0.9.4-Concurrent-Operations.png`.

Limits: Metadata inventory only; no gameplay or implementation claim is inferred from the image filename.

<a id="version-v0-9-5"></a>

### v0.9.5 — Night lighting

Evidence: `Australis-v0.9.5-Night-Lighting.png`.

Limits: Metadata inventory only; no gameplay or implementation claim is inferred from the image filename.

<a id="version-v0-9-6"></a>

### v0.9.6 — Crew stations

Evidence: `Australis-v0.9.6-Crew-Stations.png`.

Limits: Metadata inventory only; no gameplay or implementation claim is inferred from the image filename.

<a id="version-v0-9-7"></a>

### v0.9.7 — Tower alignment

Evidence: `Australis-v0.9.7-Tower-Alignment.png`.

Limits: Metadata inventory only; no gameplay or implementation claim is inferred from the image filename.

<a id="version-v0-9-8"></a>

### v0.9.8 — Weapon finish

Evidence: `Australis-v0.9.8-Weapon-Finish.png`.

Limits: Metadata inventory only; no gameplay or implementation claim is inferred from the image filename.

<a id="version-v0-9-9"></a>

### v0.9.9 — Hangar operations

Evidence: `Australis-v0.9.9-Hangar-Operations.png`.

Limits: Metadata inventory only; no gameplay or implementation claim is inferred from the image filename.

<a id="version-v0-10-0"></a>

### v0.10.0 — Hull / radar fit

Evidence: `Australis-v0.10.0-Hull-Radar-Fit.png`.

Limits: Metadata inventory only; no gameplay or implementation claim is inferred from the image filename.

<a id="version-v0-10-4"></a>

### v0.10.4 — Vertical CIWS Deployment

Evidence: `RAN_Australis_Full_Version_History.txt`.

Limits: Original detailed source/package not recovered for every historical row; offline checks are not live game confirmation.

<a id="version-v0-10-5"></a>

### v0.10.5 — Raised CIWS Housings

Evidence: `RAN_Australis_Full_Version_History.txt`.

Limits: Original detailed source/package not recovered for every historical row; offline checks are not live game confirmation.

<a id="version-v0-10-6"></a>

### v0.10.6 — Four-Catapult Controller

Evidence: `RAN_Australis_Full_Version_History.txt`.

Limits: Original detailed source/package not recovered for every historical row; offline checks are not live game confirmation.

<a id="version-v0-10-7"></a>

### v0.10.7 — Compact Waist Zone / Stern Recovery

Evidence: `RAN_Australis_Full_Version_History.txt`.

Limits: Original detailed source/package not recovered for every historical row; offline checks are not live game confirmation.

<a id="version-v0-10-8"></a>

### v0.10.8 — Forward Waist-Catapult Relocation

Evidence: `RAN_Australis_Full_Version_History.txt`.

Limits: Original detailed source/package not recovered for every historical row; offline checks are not live game confirmation.

<a id="version-v0-10-9"></a>

### v0.10.9 — Staggered Waist Catapult Study

Evidence: `RAN_Australis_Full_Version_History.txt`.

Limits: Original detailed source/package not recovered for every historical row; offline checks are not live game confirmation.

<a id="version-v0-10-10"></a>

### v0.10.10 — Outboard Waist Deck

Evidence: `RAN_Australis_Full_Version_History.txt`.

Limits: Original detailed source/package not recovered for every historical row; offline checks are not live game confirmation.

<a id="version-v0-10-11"></a>

### v0.10.11 — Touching Forward Lifts

Evidence: `RAN_Australis_Full_Version_History.txt`.

Limits: Original detailed source/package not recovered for every historical row; offline checks are not live game confirmation.

<a id="version-v0-10-11-w1"></a>

### v0.10.11-W1 — Naval Grey and Weathered Finish

Evidence: `RAN-Australis-W1-Change-Notes.txt`; `RAN-Australis-W1-Installation.txt`.

Prerequisites: Existing v0.10.11 Touching Forward Lifts mod.

Limits: Separate visual revision, not a new controller/game-compatibility version. Native asset and installer fixtures passed; live appearance/flight/combat verification pending.

<a id="version-v0-10-12"></a>

### v0.10.12 — Naval Bow Update

Evidence: `Australis-v0.10.12-Installation.txt`.

Prerequisites: Existing v0.10.11, clean or W1.

Limits: Offline geometry checks only; no separate ballast-tank simulation; live flotation/handling/gameplay pending.

<a id="version-v0-10-13"></a>

### v0.10.13 — Maintained Service / Fixed CIWS

Evidence: `Australis-v0.10.13-Windows-Installation.txt`.

Prerequisites: Existing AnchorChain / ACPreloader.

Limits: Offline package, controller and upgrade/restore checks; PowerShell exercised on Linux, not Windows 11 or live Sea Power.

<a id="version-v0-10-14"></a>

### v0.10.14 — Option C Finish

Evidence: `Australis-v0.10.14-Windows-Installation.txt`.

Prerequisites: Updater requires v0.10.13; complete mod available for earlier/new installs; AnchorChain / ACPreloader.

Limits: Preview procedural overlay was not part of native shader patch. Offline native materials/hash checks; live visual/operational verification pending.

<a id="version-v0-10-15"></a>

### v0.10.15 — Hull-Integrated Revision

Evidence: `Australis-v0.10.15-Windows-Installation.txt`.

Prerequisites: Updater accepts v0.10.13 or v0.10.14; AnchorChain / ACPreloader.

Limits: Geometry/installer checks ran offline; PowerShell 7.4.6 on Linux, not Windows PowerShell 5.1 or live game.

<a id="version-v0-10-16"></a>

### v0.10.16 — Bridge, ICCS Bubble and Galleries

Evidence: `Australis-v0.10.16-Windows-Installation.txt`.

Prerequisites: Updater requires v0.10.15; complete mod for earlier/new installs; AnchorChain / ACPreloader.

Limits: No live Windows 11 / Sea Power acceptance is established by these notes.

<a id="version-v0-10-17"></a>

### v0.10.17 — Quality of Life

Evidence: `Australis-v0.10.17-Windows-Installation.txt`.

Prerequisites: Updater requires v0.10.16; AnchorChain / ACPreloader.

Limits: Decorative safety details do not add simulated rescue/firefighting rules. Watcher displays last observations/admission, not native launch completion or continuous occupancy. Offline fixtures only.

<a id="version-v0-10-18"></a>

### v0.10.18 — Forward Retracting CIWS

Evidence: `Australis-v0.10.18-Windows-Installation.txt`.

Prerequisites: Updater requires v0.10.17; mod controller and AnchorChain / ACPreloader required, no supported native fallback.

Limits: Nominal four-second mechanical stow does not guarantee four-second route release. Missing clearance/faults hold operation. Live firing, tracking, collision and aviation tests pending.

<a id="version-v0-10-19"></a>

### v0.10.19 — Crew Safety and Stern Loading Concept

Evidence: `Australis-v0.10.19-Design-Notes.txt`.

Prerequisites: Built from v0.10.18 model.

Limits: v0.10.18 playable mod unchanged; no new controller or installer. Ramp controls, game collision/animation integration and dock loading deferred. Props are inactive weapons.

<a id="version-v0-10-20"></a>

### v0.10.20 — Enlarged Stern Loading Review

Evidence: `Australis-v0.10.20-Loading-Design-Notes.txt`.

Prerequisites: v0.10.19 preview baseline.

Limits: Prior playable mod kept separately; game loading, collision/animation and structural/watertight behavior not implemented. AirGroup list empty in these design assets.

<a id="version-v0-10-21"></a>

### v0.10.21 — Fixed Closed Rear Doors

Evidence: `Australis-v0.10.21-Fixed-Doors-Notes.txt`.

Prerequisites: v0.10.20 preview.

Limits: Supersedes opening-door/deployable-ramp concept. No aircraft loading simulation, door animations or game installer.

<a id="version-v0-10-22"></a>

### v0.10.22 — Exterior Survival and Landing Lights

Evidence: `Australis-v0.10.22-Design-Notes.txt`.

Prerequisites: v0.10.21 preview baseline.

Limits: Nominal raft capacity is a planning assumption, not certified installation or simulated evacuation. Editable OBJ/INI, viewer, renders/source/validation supplied; no live game/browser rendering claimed.

<a id="version-v0-10-23"></a>

### v0.10.23 — Flush Raft Cradles and CIWS Surround

Evidence: `Australis-v0.10.23-Design-Notes.txt`.

Prerequisites: v0.10.22 preview baseline.

Limits: Static raft fittings without deployment animation; prior preview pose controls and fixed closed stern doors retained. Offline model/shader/viewer checks only.

<a id="version-v0-10-24"></a>

### v0.10.24 — Hull Alignment / Windows Game Build

Evidence: `Australis-v0.10.24-Design-Notes.txt`; `RAN-HMAS-Australis-v0.10.24-Windows11-Guide.txt`.

Prerequisites: AnchorChain Workshop core required separately.

Limits: Do not confuse design preview sensor requirement with native per-face scanning: independent per-face native scanning not implemented. 99 aircraft is design capacity; actual embarked wing derives from installed data. No live Windows/game execution.

<a id="version-v0-10-25"></a>

### v0.10.25 — Native Model Hotfix

Evidence: `RAN-HMAS-Australis-v0.10.25-Windows11-Guide.txt`.

Prerequisites: AnchorChain core.

Limits: Missing native parts establish a concrete null-reference path, but generic GameMain popups may have other causes; live Windows/game success unverified.

<a id="version-v0-10-26"></a>

### v0.10.26 — Rear Tower Model Repair

Evidence: `RAN-HMAS-Australis-v0.10.26-Windows11-Guide.txt`.

Prerequisites: AnchorChain core.

Limits: Repairs geometry; does not demonstrate a fix for separate Script runtime startup failed after 10 heartbeat attempts timeout. Runtime cause/flicker acceptance still require local evidence.

<a id="version-v1-0"></a>

### v1.0 — Basic Shell

Evidence: `RAN-Australis-Basic-Shell-Installer-v1.0.1-Windows11.zip -> embedded payload SHELL-MANIFEST.json (version 1.0.0), _info.ini and vessels/ran_australis_basic_shell.ini`.

Prerequisites: Native-only model; no custom controller required..

Limits: Original v1.0 ZIP not materialized in this audit; exact model v1.0.0 is recovered from the later v1.0.1 installer payload.

<a id="version-v1-0-1"></a>

### v1.0.1 — Basic Shell installer (model v1.0.0)

Evidence: `Install-Australis-Basic-Shell-v1.0.1.cmd -> InstallerVersion=1.0.1 / ModelVersion=1.0.0 and embedded SHELL-MANIFEST.json`.

Prerequisites: Existing Windows Sea Power installation..

Limits: CMD source and embedded package inspected; execution not repeated here.

<a id="version-v1-0-2"></a>

### v1.0.2 — Basic Shell

Evidence: `Install-Australis-Basic-Shell-v1.0.2.cmd -> InstallerVersion/ModelVersion=1.0.2, SHELL-MANIFEST.json, ManifestTable/VerifyAgainst and upgrade transaction source`; `Australis-Stage1-v1.1.0-Test-Plan.txt -> user-confirmed working v1.0.2 baseline`; `RAN-Australis-Stage1-v1.1.0-Source-and-Checks.zip -> BUILD-INPUTS.json confirms user validation date 2026-11-13`.

Prerequisites: Native-only shell; no controller/flight systems..

Limits: Later Stage1 source records user-confirmed game load/work on 13 November. Precise geometry correction rationale was not recovered from the single-CMD package, so not invented.

<a id="version-v1-1-0"></a>

### v1.1.0 — Flight Deck Stage 1

Evidence: `Australis-Stage1-v1.1.0-Test-Plan.txt`; `RAN-Australis-Stage1-v1.1.0-Source-and-Checks.zip -> package/payload/README.txt, package/PACKAGE-BUILD.json and BUILD-INPUTS.json`; `RAN-Australis-Full-Restore-v1.2.0-Source-and-Checks.zip -> aviation/LANDING-REGRESSION-AUDIT.json`.

Prerequisites: Installer derives supported original-game aircraft; separate Basic Shell fallback preserved..

Limits: Full Restore audit records user confirmation that Stage1 loads and launches but aircraft do not land. That report supersedes a blanket untested description but is not full flight-deck acceptance.

<a id="version-v1-2-0"></a>

### v1.2.0 — Full Restore

Evidence: `RAN-Australis-Full-Restore-v1.2.0-Source-and-Checks.zip -> package/payload/README.txt, aviation/AVIATION-INDEX.json and model/INDEPENDENT-GEOMETRY-REVIEW.json`; `Australis-Full-Restore-v1.2.0-Test-Plan.txt`; `HMAS-Australis-v1.2.3-Lighting-Patch-for-v1.2.0.zip -> CHANGE-REVIEW.json`.

Prerequisites: Audited AnchorChain Workshop core and preloader; pinned game/core hashes; original controller internal component version remains 0.10.24..

Limits: Later lighting-patch review records a user-reported working v1.2.0 baseline. Native recovery, mechanism completeness and FPS are not established by that general report; original build checks are offline only. No measured FPS gain claimed.

<a id="version-v1-2-1"></a>

### v1.2.1 — Full Restore reliability

Evidence: `Australis-Full-Restore-v1.2.1-Lessons-and-Changes.txt`; `RAN-Australis-Full-Restore-v1.2.1-Source-and-Checks.zip -> documentation/README.txt and aviation/AVIATION-LESSONS.txt`; `Australis-Compatibility-Check-v1.2.2-Source-and-Checks.zip -> DIAGNOSIS.txt`.

Prerequisites: Same complete v0.10.26 model/controller feature contract; audited native game/core required..

Limits: Subsequent diagnostic review confirms Windows installer launched and payload hash checks passed, then stopped on an unaudited game assembly hash before mod/game writes. VTOL configuration completeness is not proof of fixed-wing landing repair. Runtime performance proposal was UNCOMPILED_NOT_APPLIED and excluded from installation.

<a id="version-v1-2-2"></a>

### v1.2.2 — Compatibility Check

Evidence: `Australis-Compatibility-Check-v1.2.2-Source-and-Checks.zip -> DIAGNOSIS.txt and installer/README.txt`.

Prerequisites: Sea Power closed, existing installation to inspect..

Limits: Does not install a ship or approve the new assembly hash. Structural metadata matches cannot establish runtime behavior or FPS.

<a id="version-v1-2-3"></a>

### v1.2.3 — Lighting Patch / Archive and Update

Evidence: `HMAS-Australis-v1.2.3-Lighting-Patch-for-v1.2.0.zip -> README.txt, CHANGE-REVIEW.json, TEST-RESULTS.json and INSTALLER-TEST-RESULTS.json`; `HMAS-Australis-v1.2.3-Archive-and-Update-Windows11.zip -> README.txt and included installer test results`.

Prerequisites: Working Full Restore v1.2.0 installed; existing AnchorChain..

Limits: README records 334 isolated/native-shaped controller checks and PowerShell 7.4.6/Linux install/restore fixtures; no Windows CMD/5.1 or Unity/Sea Power lighting/FPS test. Recorded PowerShell/Linux staging/archive/rollback/restore fixtures only; actual lighting rendering/FPS remains pending.

<a id="version-v1-2-4"></a>

### v1.2.4 — All Carrier Aircraft

Evidence: `HMAS-Australis-v1.2.4-All-Carrier-Aircraft-Archive-Update-Windows11.zip -> README.txt`.

Prerequisites: Working compatible Full Restore v1.2.0/v1.2.3 installed; not standalone ship package..

Limits: Catalogue fixtures recorded; selection compatibility is not automatic embarkation or live launch/recovery proof. Land-only bombers excluded at this version.

<a id="version-v1-2-5"></a>

### v1.2.5 — Detection Fix

Evidence: `HMAS-Australis-v1.2.5-Detection-Fix-Archive-Update-Windows11.zip -> README.txt`.

Prerequisites: Installed verified v0.10.26 or Full Restore v1.2.0/v1.2.1, with or without v1.2.3/v1.2.4 updates..

Limits: Recorded copied-fixture upgrade/restoration of actual original v0.10.26 payload with no inventory; not native game acceptance.

<a id="version-v1-2-6"></a>

### v1.2.6 — All Stock Aircraft

Evidence: `HMAS-Australis-v1.2.6-All-Aircraft-Archive-Update-Windows11.zip -> README.txt`.

Prerequisites: Compatible installed full carrier, directly over v1.2.5 or supported original/Full Restore models..

Limits: Selection catalogue only: does not make land-only aircraft fit, launch or recover. Fixture tests do not establish Windows/Sea Power behavior.

<a id="version-v1-2-7"></a>

### v1.2.7 — Controller Startup Repair

Evidence: `HMAS-Australis-v1.2.7-Controller-Startup-Repair-Windows11.zip -> README.txt`.

Prerequisites: Existing full carrier and verified official AnchorChain 1.2.0 core; known supported preloader hashes only..

Limits: Targets confirmed startup/discovery fault; no motion-formula rewrite. Actual startup, mechanism operation and FPS still require game confirmation. Linux fixture tests cover install/rollback/restoration but not Windows/Mono.

<a id="version-v1-2-8"></a>

### v1.2.8 — In-Game Info Sheet

Evidence: `HMAS-Australis-v1.2.8-In-Game-Info-Sheet-Windows11.zip -> README.txt and Australis-Info-Sheet.txt`.

Prerequisites: Compatible original v0.10.26 model or existing v1.2.5/v1.2.6/v1.2.7 update and verified AnchorChain 1.2.0 core..

Limits: Recorded copied-fixture description/hash/restore checks only; actual Windows/Sea Power text rendering and mechanisms remain unverified. Latest delivered updater, not a standalone complete carrier download.

<a id="version-v1-2-9"></a>

### v1.2.9 — Modded Aircraft Selection Fix

Discovers aircraft from enabled local/Workshop mods and the user tree; refreshes AircraftSupported on every run while preserving the existing air wing, routes and base version; verified backup/restore and ownership-hash updates.

[Windows package](../builds/HMAS-Australis-v1.2.9-Modded-Aircraft-Selection-Fix-Windows11.zip) · [Source and instructions](../updates/v1.2.9/README.txt) · [Regression results](../updates/v1.2.9/TEST-RESULTS.json).

Enable the desired aircraft mods in Mod Manager before refreshing. The source resolves saved enabled local and Workshop roots, reports disabled/unreadable entries and retains existing supported/embarked IDs. No flight-route, geometry or DLL changes are included. Patch state is separate from the preserved base carrier VERSION.
