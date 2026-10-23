# Australis 2030 — defensive weapons, aircraft contact and revised deck trial

The current design uses five 95 m steam CATOBAR tracks: three at the bow
and two shallow 6-degree port-waist tracks with staggered launch positions.
Four 22 × 26 m lifts and four
helicopter spots now form two pairs ahead of the islands. The aft island
is smaller with wraparound glazing, and recovery uses a 9-degree port axis.
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
2. Press Play with an empty air group. Confirm hull, five tracks, the smaller
   glazed rear island, main-deck VLS/missile housings and below-deck gun/decoy
   shelves render, then save and reload once. RIM-66E and RGM-109 must be absent.
3. Add a stock **F-14A**. Check bow-facing parking, wheel/platform alignment
   and taxiing inboard. The forward starboard lift is now at z=54 m; the port
   lift sits beside the aft part of the main island at z=-32 m. Check the
   tyres on each lift, while taxiing and at a bow catapult. Main-deck contact
   points are 22 m; pads are 22.08 m and platforms 22.205 m. The previous
   16 cm main-deck clearance has been removed; stock aircraft ground pivots
   remain in use. Check the helicopter tyres on their pads separately.
4. Use **A-7Es** for all five catapults. IDs 1/2/3 are the straight bow bank
   and accept other carrier-capable aircraft. IDs 4/5 are the angled port-waist
   pair, currently restricted to the stock A-7E. Check each lane separately,
   including taxi alignment, deflector position and actual departure heading.
   Check the flush slots, shuttles, trimmed white guides and the staggered
   waist positions; neither track may project beyond the deck edge.
5. Test bow pair 1/3, then centre bow 2. Check waist 4 and 5 separately: each
   must wait for every bow lane and the other waist lane to be clear. Then
   queue a mixed bow/waist group and verify those interlocks. The shared
   one-second minimum does not guarantee an actual interval or lane assignment.
6. Ready and queue a helicopter first, followed by jets. Spots 6/7 are ahead
   of the main island; 8/9 are ahead of the rear island. Check helicopter
   preparation alongside the bow catapults while holding course. Forward
   helicopter spots 6/7 and waist catapults 4/5 must wait for one another;
   bow lanes must remain available. Rear spots can use lifts 1 or 4.
7. Test arrested recovery and taxi back to a lift separately. Recovery blocks
   launches. Check the aircraft hook and stopping point; visible cable lines
   alone do not prove the recovery works.

Bow-lane staging checks use a 25 m span × 30 m length envelope. Waist
lanes have only been checked for the A-7E; they are not yet cleared for the
F-111N families. Five installed lanes do not imply five simultaneous launches
or a validated 99-aircraft deck cycle.

This revision keeps the port lift abreast of the aft part of the main island and checks a
12 m plan-view launch corridor past lifts/islands. Waist departure uses shared
deck space, so a successful single launch does not prove a complete deck cycle.

## Combat check after the empty-deck loading test

1. Confirm radar, ESM, defensive ECM, one offensive ECM, missiles, guns,
   chaff and two towed decoys are listed. Switch radar on in a controlled
   friendly-aircraft mission before introducing hostile targets.
2. In a separate small test, fire one Sea Sparrow from a deck missile housing
   and one from the defensive VLS against a valid airborne target. Check
   fire-control availability, cell origins and the initial turn from vertical.
   These are stock RIM-7M proxies, not ESSM/RAM implementations. No ship strike
   missiles are loaded.
3. Check the 21-position RAM-form launchers separately. They fire stock
   RIM-7M Sea Sparrows with stock SARH guidance, not real RIM-116/ESSM rounds.
4. Reproduce the reported case first: select a nearby hostile test surface
   target within range and fire each 30 mm gun separately. Confirm there is
   no WeaponSystemGun.AlignTurret exception. Then check all three CIWS, their
   yaw/elevation movement, firing origins and outboard arcs against suitable
   air/missile targets. Test SRBOC separately. Five guns have moving objects;
   missile housings, VLS caps and laser hatches remain static.
5. Deploy/retract both stock Nixie decoys at a supported speed. Record tether,
   countermeasure or loading errors. Nulka and lasers remain visual positions.

## Aircraft ammunition check

1. Use a **newly placed carrier in a new mission**, with default ammunition.
   A saved mission can override the new reserve with its old values. Check
   aviation supply reads **6,000,000/6,000,000** and has no individual weapon
   category limits. These stores are separate from the carrier's 12,000 CIWS
   rounds and 2,000 30 mm rounds.
2. Select an armed loadout, not Empty/Ferry: use a stock F-14A air-to-air fit
   and an A-7E Strike fit. Ready them and inspect their missiles/bombs and
   internal guns. Stock F-14A and A-7E gun capacities remain 675 and 1,000;
   no aircraft files are changed by this package.
3. Expend some aircraft ammunition, recover, complete maintenance/rearming,
   then launch again. Check ammunition replenishes and carrier supply falls.
   The reserve budgets four 15,000-point sorties for each of 99 aircraft,
   with actual endurance determined by their selected loadouts. The air group
   still starts empty for user selection.

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

To return to the build used in the supplied screenshots, use its matching
installer after withdrawing the current mod. That build retains the reported
30 mm gun and deck-height issues:

```bash
git -C "$HOME/Downloads/RAN-Carrier-Australis-test" worktree add --detach "$HOME/Downloads/RAN-Carrier-Australis-before-deck-fixes" d4e9b151
python3 "$HOME/Downloads/RAN-Carrier-Australis-before-deck-fixes/tools/install_australis_2030.py"
```

To return to the previous 15-degree waist revision, use its matching installer:

```bash
git -C "$HOME/Downloads/RAN-Carrier-Australis-test" worktree add --detach "$HOME/Downloads/RAN-Carrier-Australis-before-waist-refinement" 016fde6
python3 "$HOME/Downloads/RAN-Carrier-Australis-before-waist-refinement/tools/install_australis_2030.py"
```

To return to the earlier five-bow-track revision:

```bash
git -C "$HOME/Downloads/RAN-Carrier-Australis-test" worktree add --detach "$HOME/Downloads/RAN-Carrier-Australis-before-waist" fae6b9d
python3 "$HOME/Downloads/RAN-Carrier-Australis-before-waist/tools/install_australis_2030.py"
```

To reinstall the older pre-CATOBAR/combat revision instead:

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
