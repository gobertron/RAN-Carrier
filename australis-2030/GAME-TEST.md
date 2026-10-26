# Australis v0.8.2 — install, test and rollback

The current build passes geometry, native-configuration, lighting-policy and installer checks. **Its Unity appearance and Sea Power flight/combat operation remain untested.** Use a new mission and a fresh ship; saved units can retain older models, routes and ammunition.

## Install or upgrade

1. Close Sea Power.
2. Download [install-ran-australis-v0.8.2-lift-lighting.sh](../builds/install-ran-australis-v0.8.2-lift-lighting.sh) using GitHub's download/raw control. The [ZIP](../builds/RAN-Carrier-Australis-v0.8.2-Lift-Lighting.zip) includes the native package and source; [SHA256SUMS-v0.8.2.txt](../builds/SHA256SUMS-v0.8.2.txt) provides download checksums.
3. Run the standalone installer:

   ```bash
   bash "$HOME/Downloads/install-ran-australis-v0.8.2-lift-lighting.sh"
   ```

4. Enable **AnchorChain** and **RAN Australis Fleet v0.8.2 Lift Lighting**, restart, then place one of the four current ships in a blank mission.

The default Linux game directory is `/home/aram/.local/share/Steam/steamapps/common/Sea Power`. Use `--game "/path/to/Sea Power"` for another location. The installer requires Python 3, the existing official AnchorChain preloader/Harmony and framework, and the game scripts version checked against the supplied reference. It stops on a different game version rather than changing it.

Before replacement it verifies a backup of the existing Australis mod and any old loose controller. It stages the carrier and controller together, verifies the installed hashes and rolls back on publication failure. It does not replace stock, Workshop, RADF, User Data, BepInEx or launch-option files. Keep the working Proton launch option if it is already configured:

```text
WINEDLLOVERRIDES="winhttp.dll=n,b" %command%
```

To run pre-install checks without changing the installation:

```bash
bash "$HOME/Downloads/install-ran-australis-v0.8.2-lift-lighting.sh" --check
```

## First mission checks

| Check | Expected configuration or observation to verify |
|---|---|
| Fleet | HMSCS Australis 91, Southern Cross 92, Federation 93 and Commonwealth 94 are available |
| Layout | Two bow catapults, one port-waist catapult, four internal lifts and three helipads |
| Repairs | Fresh carrier damage-control panel shows five teams |
| Spawn | No native initialization exception; waterline and trim look reasonable |
| Propulsion | Eight stern outlets; internal impellers, four outer steering sleeves and four fixed boosters |
| Standard | Commanded normal aviation speed is 20 kn |
| Full / Flank | Existing 30-kn maximum remains available; damage may reduce attainable speed |

The shared native propulsion model approximates the jets. Do not expect independent thrust allocation, booster staging, animated reverse buckets or eight separate wakes. Full is the chosen emergency operating setting, not an emergency-detection rule.

## Lift lighting — new in v0.8.2

Test each lift separately, first in daylight and then at dusk/night:

1. Observe the lowered platform at the hangar stop, Y=11.8 m. Eight warm-white work lights should illuminate that shaft's walls/working area. The fixtures occupy the existing outer, forward and aft walls; the inboard hangar opening stays clear.
2. Raise the lift. Illumination should fade smoothly in the last 0.60 m below deck and be fully off within 0.10 m of its 22.002 m deck-level stop.
3. Leave the platform flush with the flight deck. Check for no lower-shaft glow around or through the closed platform.
4. Lower it again. Lights should return as it moves below the top-stop fade zone and remain on at the bottom.
5. Move a different lift while the first stays closed. Its light group should respond independently. Exterior night lighting should keep its separate day/night behavior.

The controller uses actual lift position in both directions rather than a timer. Invalid or missing position data fails off. The 193 policy/reflection checks exercise these rules and failure cleanup with a minimal Unity-shaped fixture; they do not validate the live game's rendering. The [cutaway image](previews/Australis-v0.8.2-Lift-Cutaway.png) illustrates the intended states using actual geometry and illustrative lamp shading.

## Aircraft and helicopter checks

Ready armed aircraft before testing. Set the carrier to **Standard, 20 kn**, then test operations separately before attempting a mixed cycle:

1. Launch and recover a known carrier-capable fixed-wing aircraft using each bow catapult, then the waist catapult and arrested-recovery lane.
2. Confirm fixed-wing aircraft use lifts 1–2 and the six-second lift animation carries their native embarked parent correctly.
3. Launch and recover a helicopter or VTOL aircraft through lifts 3–4. Check the aft/front/middle pad preference and that shared taxi/lift conflicts queue correctly.
4. Repeat with the intended F-111N aircraft and loadouts after the basic stock-aircraft check. Eligibility does not establish span, rotor, taxi-turn or loadout clearance for every add-on.
5. Verify that helicopter sea-state/landing-assistance checks and deck conflicts still apply. Standard-speed configuration does not bypass them.
6. Test a small mixed operation only after the separate paths work. A full 99-aircraft deck cycle and 63-plane deck parking remain unverified.

Record aircraft ID, loadout, carrier name, sea state, carrier speed and the failing stage. Keep wind/heading consistent when comparing versions.

## Defensive fit and night checks

Start with the wells stowed and aviation clear. A defensive request should wait for committed aircraft to finish, deploy over 0.75 simulation seconds, permit firing when ready, hold until 300 seconds after the last actual shot and stow over 10 seconds. Aviation should remain interlocked until stowed. Check all five CIWS mounts, including both island roofs, and confirm the forward mount remains clear of the bow catapult.

Test both 30 mm guns and VLS launch directions. The VLS carries stock RIM-66E/RIM-7M proxies; no SM-6 guidance or ballistic-missile interception is implemented. Check subdued deck guidance, landing-light fittings, brighter hangar lighting, doors, bridge panes and painted ship numbers at dusk/night. Actual night brightness and combat behavior remain trial results to collect.

Check slow and cruising turns, astern motion and propulsion damage in a separate mission. Those trials assess the game implementation; they do not establish real waterjet efficiency, cavitation margin, structural strength or seaworthiness.

## Logs and rollback

The installer prints its log and backup paths under Downloads. If a trial fails, retain the installer output, current Sea Power `Player.log`, game version and the enabled mod's `RAN-Australis-DeckController.log`. The historical rudder initialization dependency requires the packaged `[Foam]` section; do not remove it while troubleshooting.

Close Sea Power before restore or removal. To restore the verified backup directory printed by the installer:

```bash
bash "$HOME/Downloads/install-ran-australis-v0.8.2-lift-lighting.sh" --restore "/path/printed/by/installer"
```

To withdraw the current mod while retaining a verified backup:

```bash
bash "$HOME/Downloads/install-ran-australis-v0.8.2-lift-lighting.sh" --remove
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

`tools/test_recovery_installer.py /path/to/private-refs` runs isolated installation, upgrade, restore, removal and injected-failure rollback tests using the expected external game/AnchorChain reference fixture. Those checks passed for the release. `tools/package_recovery.py` checks the current model/report hashes and native package before building the standalone installer and archive.

The full engineering assumptions and remaining physical validation work are in [WATERJET-ENGINEERING-REVIEW.md](../WATERJET-ENGINEERING-REVIEW.md).
