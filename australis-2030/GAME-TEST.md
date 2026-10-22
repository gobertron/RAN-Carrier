# Australis 2030 — five-lane CATOBAR and combat-fit trial

The current design uses five 95 m steam CATOBAR tracks: three in the middle
and two outboard. Four 22 × 26 m lifts and four aft helicopter spots remain.
The targets are 99 aircraft, 5,300 embarked personnel, 5,800 berths and
112,000 tonnes. See [DESIGN-BASIS.md](DESIGN-BASIS.md) for the size/crew budget
and the modern-equipment-to-stock-proxy mapping.

The user confirmed hull loading after the missing `[Foam]` section was added
in `cbdaef4`. Later screenshots show F-14As on the lifts, A-7Es on the deck
and a fixed-wing aircraft airborne. The **five-lane and combat revision has
not yet passed an in-game test**. It has no RADF or Workshop dependency.

The installer now checks required stock profiles and ammunition files before
staging. Close Sea Power before updating. Its removal step retains a verified
backup under `~/Downloads/RAN-Carrier-Australis-2030-backups/`.

## Install from the draft branch

In a terminal on the Sea Power computer, run:

```bash
git clone --branch feature/australis-2050-concept \
  https://github.com/gobertron/RAN-Carrier.git "$HOME/Downloads/RAN-Carrier-Australis-test"
python3 "$HOME/Downloads/RAN-Carrier-Australis-test/tools/install_australis_2030.py"
```

If the checkout already exists, run
`git -C "$HOME/Downloads/RAN-Carrier-Australis-test" pull --ff-only` before
running the installer. The installer only creates
`Sea Power_Data/StreamingAssets/RAN-Carrier-Australis-2030` and verifies its
files. If that folder already contains different data, it stops safely. To
withdraw the old folder while retaining a verified copy under
`~/Downloads/RAN-Carrier-Australis-2030-backups/`, run:

```bash
python3 "$HOME/Downloads/RAN-Carrier-Australis-test/tools/install_australis_2030.py" --remove
```

Then run the first install command again. Do not merge the mod files into
`StreamingAssets/user` or the RADF folder.

For a previously installed first version, close Sea Power and use this exact
upgrade sequence:

```bash
git -C "$HOME/Downloads/RAN-Carrier-Australis-test" pull --ff-only
python3 "$HOME/Downloads/RAN-Carrier-Australis-test/tools/install_australis_2030.py" --remove
python3 "$HOME/Downloads/RAN-Carrier-Australis-test/tools/install_australis_2030.py"
```

The removal command backs up the old Australis folder. If any command fails,
stop there and share its output.

## Flight check

1. Enable **RAN Australis 2030 Editor Prototype**, restart, and create a
   **new blank mission with a newly placed carrier**. Select Australia > CVN
   with Hide Anachronistic off. Keep failed Melbourne prototypes disabled.
2. Press Play with an empty air group. Confirm hull, five tracks, two islands
   and outboard weapon shelves render, then save and reload once.
3. Add a stock **F-14A**. Check bow-facing parking, wheel/platform alignment
   and taxiing inboard. The forward starboard lift is now at z=54 m; the port
   lift remains abreast of the main island.
4. Use **A-7Es** for all five catapults. IDs 1/5 are the outboard pair,
   currently restricted to the stock A-7E. IDs 2/3/4 form the middle bank and
   accept other carrier-capable aircraft. Check each lane separately first.
5. Test outer pair 1/5, then middle pair 2/4, then centre 3. Adjacent lanes
   interlock. The shared one-second minimum does not guarantee an actual
   interval or the game scheduler's lane assignment.
6. Ready and queue a helicopter first, followed by jets. Check that aft
   preparation/launch progresses alongside forward preparation while the
   carrier holds course. Aft launch spots are now IDs 6–9.
7. Test arrested recovery and taxi back to a lift separately. Recovery blocks
   launches. Check the aircraft hook and stopping point; visible cable lines
   alone do not prove the recovery works.

Middle-lane staging checks use a 25 m span × 30 m length envelope. Outboard
lanes have only been checked for the A-7E; they are not yet cleared for the
F-111N families. Five installed lanes do not imply five simultaneous launches
or a validated 99-aircraft deck cycle.

## Combat check after the empty-deck loading test

1. Confirm radar, ESM, defensive ECM, one offensive ECM, missiles, guns,
   chaff and two towed decoys are listed. Switch radar on in a controlled
   friendly-aircraft mission before introducing hostile targets.
2. In a separate small test, fire one Sea Sparrow and one VLS SM-2 against a
   valid airborne target, then a Tomahawk against a valid land target. Check
   fire-control availability and projectile origins.
3. Check the 21-position RAM-form launchers separately. They fire stock
   RIM-7M Sea Sparrows with stock SARH guidance, not real RIM-116/ESSM rounds.
4. Test CIWS, 30 mm and SRBOC separately, observing firing origins and outboard
   sectors. Housings are fixed blockouts; turret and hatch animation is absent.
5. Deploy/retract both stock Nixie decoys at a supported speed. Record tether,
   countermeasure or loading errors. Nulka and lasers remain visual positions.

## Diagnostics and rollback

If an exception occurs, close Sea Power and collect the current log before
restarting:

```bash
python3 "$HOME/Downloads/RAN-Carrier-Australis-test/tools/collect_australis_editor_diagnostics.py"
```

Withdraw the current mod while retaining a verified backup:

```bash
python3 "$HOME/Downloads/RAN-Carrier-Australis-test/tools/install_australis_2030.py" --remove
```

To reinstall the pre-CATOBAR/combat revision, use its matching installer:

```bash
git -C "$HOME/Downloads/RAN-Carrier-Australis-test" worktree add --detach "$HOME/Downloads/RAN-Carrier-Australis-before-catobar" 74e378e
python3 "$HOME/Downloads/RAN-Carrier-Australis-before-catobar/tools/install_australis_2030.py"
```

## Rebuild

Geometry needs Python, NumPy and Pillow. The built installer uses the standard
library only.

```bash
python3 australis-2030/build.py
python3 tools/build_australis_2030_mod.py
python3 tools/validate_australis_2030_mod.py
```

Add `--stock-root "/path/to/Sea Power/Sea Power_Data/StreamingAssets/original"`
to validate actual installed dependencies. The installer does this automatically.
