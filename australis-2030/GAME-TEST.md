# Australis v0.8.5 — install, test and rollback

The current build passes geometry, native-configuration, lighting-policy and installer checks. **Its Unity appearance and Sea Power flight/combat operation remain untested.** Use a new mission and a fresh ship; saved units can retain older models, routes and ammunition.

## Naval details in v0.8.5

Hull numbers **91–94** are enlarged on the flight deck and both main-island sides and aligned to their model surfaces. The shared native class still selects the matching number atlas for each named ship. Both bridge structures receive individual framed naval-style windows, with consistent sill heights and mullions on their actual raked faces. Watertight-style doors use raised coamings, rounded corners, hinges, dogs and handles aligned to the supporting surface.

The deck number panel is **10.8 × 8.8 m**, with an approximately **8.44 × 6.53 m** painted glyph. Both port and starboard main-island panels are **9.6 × 5.6 m**, with approximately **7.69 × 4.20 m** glyphs. The panels follow their actual supporting planes with a small surface offset; the enlarged island markings sit between the lower access doors and bridge glazing.

These fittings are original decorative model geometry; they do not create functioning doors or establish watertight integrity, ballistic protection or naval-design certification. Their appearance, texture orientation and visibility still need an in-game check. The change retains the preceding hull, waterjet, class-list and flight-deck configuration.

## Class list and installer corrections

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



If an earlier installer stopped at 40% with `section '---------- Surface ships ----------' already exists` in `original/systems/sensors.ini`, it did not reach backup or replacement. The old carrier remains installed. v0.8.3 accepts repeated stock catalogue headings by checking section-name membership only; it does not edit stock files. Strict parsing remains in place for our own INIs, and actual missing dependencies still stop installation.

The hull shape, propulsion and flight-deck geometry retain the preceding configuration. A common model and native number textures serve the four variants. Lift-home configuration and taxi routes are corrected; the compiled deck controller remains v0.8.2. The class list and number-panel appearance require a live-game check alongside the outstanding flight, lighting and engineering trials.

## Install or upgrade

1. Close Sea Power.
2. [Download the v0.8.5 offline installer](../builds/install-ran-australis-v0.8.5-naval-details-offline.sh?raw=1) and save it in Downloads.
3. Run the downloaded offline installer:

   ```bash
   bash "$HOME/Downloads/install-ran-australis-v0.8.5-naval-details-offline.sh"
   ```

4. Wait for **100%** and `installed package hashes verified`. A `[STOP]` means installation did not complete; retain its printed log.
5. Open Sea Power's mod menu. Enable **AnchorChain** and **RAN Australis Fleet v0.8.5 Naval Details**, and disable older Australis entries. Match any `[OTHER COPY]` paths printed by the installer to the older entries.
6. Restart Sea Power, create a new blank mission, expand **Australis-class**, and select one of its four named ships directly. There should be no extra “2025” submenu for each ship. Place a fresh carrier for this first check.

Alternatively, download the smaller [network installer](../builds/install-ran-australis-v0.8.5-naval-details.sh?raw=1); it requires Python 3 and an internet connection:

```bash
bash "$HOME/Downloads/install-ran-australis-v0.8.5-naval-details.sh"
```

[Download the v0.8.5 offline installer](../builds/install-ran-australis-v0.8.5-naval-details-offline.sh?raw=1). It contains the complete verified package and editable source and requires Python 3; no internet connection is needed after download, and no earlier installer is required. The smaller [network installer](../builds/install-ran-australis-v0.8.5-naval-details.sh?raw=1) is an alternative that requires an internet connection and reconstructs the same verified release file manifest.

The default Linux game directory is `$HOME/.local/share/Steam/steamapps/common/Sea Power`. Use `--game "/path/to/Sea Power"` for another location. The installer requires Python 3, the existing official AnchorChain preloader/Harmony and framework, and the game scripts version checked against the supplied reference. It stops on a different game version rather than changing it.

Successful completion should print `[100%] Australis v0.8.5-naval-details installed; installed package hashes verified`, the installed mod path, and `[VERIFIED] RAN Australis Fleet v0.8.5 Naval Details`. A repeat installation prints `already installed; installed package hashes verified`. A `[STOP]` message is not a completed upgrade. Keep the printed log if another dependency check fails.

After verifying the installed hashes, the installer prints `[VERIFIED] RAN Australis Fleet v0.8.5 Naval Details` so you can identify the exact release. It also scans local mod folders and the Sea Power Workshop directory for competing copies of the same carrier vessel definitions. Each match is listed as `[OTHER COPY]` with its folder path; disable older Australis copies in the game mod menu. The diagnostic does not delete or change those copies. An unreadable folder produces a note that the scan was incomplete without invalidating the verified installation.

Before replacement it verifies a backup of the existing Australis mod and any old loose controller. It stages the carrier and controller together, verifies the installed hashes and rolls back on publication failure. It does not replace stock, Workshop, RADF, User Data, BepInEx or launch-option files. Keep the working Proton launch option if it is already configured:

```text
WINEDLLOVERRIDES="winhttp.dll=n,b" %command%
```

To run pre-install checks without changing the installation:

```bash
bash "$HOME/Downloads/install-ran-australis-v0.8.5-naval-details-offline.sh" --check
```

## First mission checks

| Check | Expected configuration or observation to verify |
|---|---|
| Class list | One Australis-class entry directly contains HMSCS Australis 91, Southern Cross 92, Federation 93 and Commonwealth 94; no repeated year submenus |
| Variant paint | Select each named variant; enlarged deck and island numbers match 91, 92, 93 and 94, remain upright on both sides and do not cover operational markings |
| Naval windows | Inspect the main and aft bridge at close range from both sides; frames and panes follow the raked face, with consistent sill heights and no floating or embedded strips |
| Naval doors | Inspect rounded coamings, hinges, dogs, handles and hull-side access supports; fittings sit against their surface and clear nearby windows and number panels |
| Layout | Two bow catapults, one port-waist catapult, four internal lifts and three helicopter-only pads |
| Lift idle state | All four platforms start flush at Y=22.002 m with shaft lights off; native demand lowers them and each cycle returns them to the upper home stop |
| Repeated flights | Launch and recover repeatedly through each lift; another cycle remains available after the preceding one completes |
| Repairs | Fresh carrier damage-control panel shows five teams |
| Spawn | No native initialization exception; waterline and trim look reasonable |
| Propulsion | Eight stern outlets; internal impellers, four outer steering sleeves and four fixed boosters |
| Standard | Commanded normal aviation speed is 20 kn |
| Full / Flank | Existing 30-kn maximum remains available; damage may reduce attainable speed |

The shared native propulsion model approximates the jets. Do not expect independent thrust allocation, booster staging, animated reverse buckets or eight separate wakes. Full is the chosen emergency operating setting, not an emergency-detection rule.

## Lift lighting — new in v0.8.2

Test each lift separately, first in daylight and then at dusk/night:

1. Confirm the idle platform starts flush at Y=22.002 m with shaft lights off. During a native aircraft-demand cycle, observe it lowered to the hangar stop, Y=11.8 m. Eight warm-white work lights should illuminate that shaft's walls/working area. The fixtures occupy the existing outer, forward and aft walls; the inboard hangar opening stays clear.
2. Raise the lift. Illumination should fade smoothly in the last 0.60 m below deck and be fully off within 0.10 m of its 22.002 m deck-level stop.
3. Leave the platform flush with the flight deck. Check for no lower-shaft glow around or through the closed platform.
4. Lower it again. Lights should return as it moves below the top-stop fade zone and remain on at the bottom.
5. Move a different lift while the first stays closed. Its light group should respond independently. Exterior night lighting should keep its separate day/night behavior.

The controller uses actual lift position in both directions rather than a timer. Invalid or missing position data fails off. The 193 policy/reflection checks exercise these rules and failure cleanup with a minimal Unity-shaped fixture; they do not validate the live game's rendering. The [cutaway image](previews/Australis-v0.8.4-Lift-Cutaway.png) illustrates the intended states using actual geometry and illustrative lamp shading.

## Aircraft and helicopter checks

Ready armed aircraft before testing. Set the carrier to **Standard, 20 kn**, then test operations separately before attempting a mixed cycle:

1. Launch and recover a known carrier-capable fixed-wing aircraft using each bow catapult, then the waist catapult and arrested-recovery lane.
2. Confirm fixed-wing launch and arrested recovery can use each of lifts 1–4 through the configured routes. Observe each native lower/raise cycle, then repeat the operation: the lift should return to its upper home stop and remain available.
3. Launch and recover a helicopter through its designated pad/lift routes. Check the aft/front/middle pad preference and that shared taxi/lift conflicts queue correctly. The pads accept Helicopter only; test carrier-capable VTOL/STOL aircraft on the catapult and arrested-recovery paths.
4. Repeat with the intended F-111N aircraft and loadouts after the basic stock-aircraft check. Eligibility does not establish span, rotor, taxi-turn or loadout clearance for every add-on.
5. Verify that helicopter sea-state/landing-assistance checks and deck conflicts still apply. Standard-speed configuration does not bypass them.
6. Confirm fixed-wing recovery blocks all six launch points and conflicting launch requests queue. Test a small mixed operation only after the separate paths work. A full 99-aircraft deck cycle and 63-plane deck parking remain unverified.

Record aircraft ID, loadout, carrier name, sea state, carrier speed and the failing stage. Keep wind/heading consistent when comparing versions.

## Defensive fit and night checks

Start with the wells stowed and aviation clear. A defensive request should wait for committed aircraft to finish, deploy over 0.75 simulation seconds, permit firing when ready, hold until 300 seconds after the last actual shot and stow over 10 seconds. Aviation should remain interlocked until stowed. Check all five CIWS mounts, including both island roofs, and confirm the forward mount remains clear of the bow catapult.

Test both 30 mm guns and VLS launch directions. The VLS carries stock RIM-66E/RIM-7M proxies; no SM-6 guidance or ballistic-missile interception is implemented. Check subdued deck guidance, landing-light fittings, brighter hangar lighting, doors, bridge panes and painted ship numbers at dusk/night. Actual night brightness and combat behavior remain trial results to collect.

Check slow and cruising turns, astern motion and propulsion damage in a separate mission. Those trials assess the game implementation; they do not establish real waterjet efficiency, cavitation margin, structural strength or seaworthiness.

## Logs and rollback

The installer prints its log and backup paths under Downloads. If a trial fails, retain the installer output, current Sea Power `Player.log`, game version and the enabled mod's `RAN-Australis-DeckController.log`. The historical rudder initialization dependency requires the packaged `[Foam]` section; do not remove it while troubleshooting.

Close Sea Power before restore or removal. To restore the verified backup directory printed by the installer:

```bash
bash "$HOME/Downloads/install-ran-australis-v0.8.5-naval-details-offline.sh" --restore "/path/printed/by/installer"
```

To withdraw the current mod while retaining a verified backup:

```bash
bash "$HOME/Downloads/install-ran-australis-v0.8.5-naval-details-offline.sh" --remove
```

Restart and use another fresh mission after changing versions.

## Rebuild and offline checks

Source generation needs Python with NumPy, Pillow, Shapely and SciPy; plots also need Matplotlib. The shipped controller can be used directly. To recompile it, supply an external .NET SDK and official development references; these private/reference files are not bundled:

```bash
python3 tools/build_deck_controller.py \
  --sdk /path/to/dotnet \
  --references /path/to/AnchorChain/dev \
  --harmony /path/to/0Harmony.dll
python3 tools/rebuild_recovery.py
python3 tools/validate_recovery.py
python3 tools/test_lift_lighting.py /path/to/dotnet
```

`tools/test_recovery_installer.py /path/to/local-reference-fixture` runs isolated installation, upgrade, restore, removal and injected-failure rollback tests using the expected external game/AnchorChain reference fixture. The stock-catalogue regression cases and full installer upgrade/restore/rollback suite pass in isolated fixtures. They reproduce the duplicate divider at line 624 and confirm that missing actual profiles/ammunition and duplicate authored INIs are still rejected. A successful run on the live installation is still to be confirmed. `tools/package_recovery.py` checks the current model/report hashes and native package before building the complete offline installer and archive. `tools/build_network_installer.py` produces the smaller GitHub network installer from the same verified target manifest.

The full engineering assumptions and remaining physical validation work are in [WATERJET-ENGINEERING-REVIEW.md](../WATERJET-ENGINEERING-REVIEW.md).
