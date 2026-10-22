# Australis 2030: first Sea Power editor test

This opt-in package is an independent RAN carrier prototype. The packaged
mesh, basic textures and vessel INI are original to this project. It uses a
stock Sea Power Nimitz resource name as a fallback, without copying game
files. It has no RADF, Workshop or F-111N dependency.

The previous Melbourne prototypes caused a Mission Editor load exception.
Close Sea Power before installing, and disable both Melbourne prototypes in
Mod Manager for this isolated test. Leave RADF as it was before.

**12 October editor finding:** The isolated first Australis package registered
and could be selected, but its 3D vessel did not appear. Loading the mission
raised a `VesselRudderSystem.init()` null-reference exception. The supplied
session log names `ran_cvn_australis_2030` as the affected vessel, reports an
empty cavitation effect and a mesh collider fallback, then records the rudder
exception. The installed OBJ was the first export, without face UV/normal
indices. The next package added those indices, an original collision hull,
and a stock game cavitation effect. The second test below showed that these
changes did not clear the rudder exception.

**Second editor finding:** The 17:49 isolated game run used the corrected OBJ
and vessel INI (verified by their SHA-256 hashes). The cavitation error is gone,
but the collision fallback and the same rudder exception remain. Inspection
of the supplied `Seapower-Scripts.dll` shows that the vessel foam loader returns
immediately if `[Foam]` is missing; the rudder initialization subsequently
reads the absent stern foam trail's transform. This package now includes
the stock-style foam configuration with original Australis positions. All
visible hull and rudder geometry remains original. The editor map displays a
unit marker; press **Play** to test 3D load.

**22 October successful load:** The user installed `cbdaef4`, started the
mission and confirmed that the original hull renders without the previous
loading exception. The screenshots show the two islands and marked flight
deck, with an empty aircraft list. This confirms the mission-load gate only;
aircraft operations, damage collision and combat systems remain untested.

**Visual correction awaiting check:** The stock flag's baked mast offset plus
our extra vertical translation left it floating above the main island. Its
INI translation is now 25 m lower. The rectangular bow sonar study is replaced
by a rounded, closed fairing, with its aft end embedded in the underwater hull
and the same hull finish. Check the flag from both sides and the bow from
underwater after upgrading; the flag should sit just above the enclosed mast,
and the fairing should show no projecting rectangular corners.

The single port lift (Elevator 3) has also moved aft from z=92 m to z=3 m,
abreast of the larger forward island. Its spawn/ride positions and both taxi
directions now follow that location. Check lift placement and a single-aircraft
taxi movement after confirming the revised hull loads.

**22 October flight trial:** The later screenshots show fixed-wing aircraft
staging at the bow, a helicopter at the aft lift, and an aircraft airborne.
They also show crowding and launch-track alignment problems. These observations
do not yet confirm recovery or a complete deck cycle.

**Launch-spacing revision:** The deck is now 82 m wide (previously 88 m),
with an approximately 41 m waterline beam. The port and starboard launch
tracks are about 40 m apart. The centre track is staggered forward and
interlocked with both outer tracks, so it operates separately from the pair.
Taxi approaches now end 20 m behind each launch point on that track's axis;
the validator measures the exported gold mesh tracks against native launch
positions, headings and catapult lengths.

The supplied game assembly confirms that `PlaneTakeOff` and
`HelicopterTakeOff` both use the same `FlightDeck.LaunchDelay` timer. This
revision changes it from nine seconds to one second, removes the aft launch
spots' forward-catapult blocks, and gives the forward lifts separate routes
to the port and starboard catapults. A one-second interval is a minimum,
not a synchronized launch command; crew preparation, engine/rotor warmup,
deck occupancy and the ship staying on course still govern actual launches.
Fixed-wing recovery remains separate from launch operations.

**F-14A lift correction:** The next overhead screenshot identifies F-14As
on the lifts and A-7Es on the catapults. The old visible platforms were only
about 12.1 m across by 18 m long, with the ride references displaced inboard.
All four platforms are now 22 m across by 26 m fore-and-aft. Their spawn and
ride references are at the platform centre and surface height, and aircraft
face the bow. Taxi paths join the inboard edge before crossing each platform.
The main deck remains 82 m wide; the maximum width including the lift
extensions is 109 m. The port lift remains abreast of the main island.

Static validation measures the actual exported platforms and checks a
full-span F-14A reference footprint, allowing for its stock deck-position and
ground-pivot terms. It also checks the A-7E open-wing staging footprint at all
three catapults. Aircraft INIs are not altered. These revised lift placements
and turns still need a fresh game test.

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

## First editor check

1. In Mod Manager enable **RAN Australis 2030 Editor Prototype**. Disable
   **RAN Carrier Original 1959 Prototype** and **RAN Melbourne 1959 Carrier
   Test** if present. Restart Sea Power.
2. Open Mission Editor with a **new blank mission**. Select Australia and the
   carrier/CVN category, with **Hide Anachronistic** off. Search **Australis**.
3. Place one **Australis Test** on the sea and press **Play**. Confirm that
   the mission opens without the rudder exception and that the original
   faceted hull renders. Then save and reload the mission. Look for two
   islands, four offset H spots, three catapult lanes and angled cables.
4. If it loads, test one stock, game-compatible fixed-wing aircraft on a
   catapult and one helicopter on a vertical spot separately. Record whether
   spawn, taxi, launch and recovery work. The air group starts empty.

## Paired launch check

Use a new blank mission and a newly placed carrier, so saved deck-point
positions do not preserve the previous layout. Add two fixed-wing aircraft
of the same type and one helicopter to its air group in the editor.

For the lift correction, first ready a stock **F-14A** and inspect it on each
lift: the nose should point toward the bow, the aircraft should fit within
the platform, and the wheels should sit on its surface. Watch it taxi inboard
without clipping an island. Then use **A-7Es** for the paired catapult check
below, inspecting their alignment with the gold tracks. Check a return to a
lift separately after a successful recovery.

1. Ready the helicopter first, then the two jets. Queue the helicopter's
   launch first so its longer warmup can begin before the jets reach the bow.
2. Queue the two jets. Confirm they use the separate outer catapults, align
   with the gold tracks, and maintain wing clearance while staging and taxiing.
3. With the carrier holding a steady course, record the actual interval
   between the outer launches and whether the helicopter can taxi/launch
   while the forward pair prepares. A longer interval alone does not prove
   the timer was ignored; compare each aircraft's preparation state.
4. After the outer pair clears, test the centre catapult with one jet. It
   should wait while either outer point is occupied, then align and launch.

The source check uses a 25 m wingspan by 30 m length staging envelope for
the outer pair, including clearance from islands and lifts. This does not
validate every aircraft model, jet blast, taxi intersection or a 99-aircraft
deck cycle. If the new deck fails, withdraw this mod with `--remove`; that
command retains a verified backup. The previous working release remains
available at commit `e587b60`. To reinstall that package, close the game and
use its matching installer from a separate checkout:

```bash
python3 "$HOME/Downloads/RAN-Carrier-Australis-test/tools/install_australis_2030.py" --remove
git -C "$HOME/Downloads/RAN-Carrier-Australis-test" worktree add --detach "$HOME/Downloads/RAN-Carrier-Australis-previous-e587b60" e587b60
python3 "$HOME/Downloads/RAN-Carrier-Australis-previous-e587b60/tools/install_australis_2030.py"
```

If the editor hangs or throws an exception, close Sea Power and collect the
current logs **before restarting it**:

```bash
python3 "$HOME/Downloads/RAN-Carrier-Australis-test/tools/collect_australis_editor_diagnostics.py"
```

The command prints an error-context text file and a diagnostics ZIP in
`~/Downloads`. Provide the text excerpt or ZIP, then withdraw this mod with
`--remove` to restore the previous game state. This is the first runtime gate;
the static validator cannot prove that the game accepts every key, geometry
or reference.

The 99-aircraft capacity, aircraft deck cycle, working radars, long-range
offensive ECM and retracting laser weapons are later milestones. The offline
3D viewer has a visual laser deployment control, but the game package only
contains closed hatch geometry. Its flag resource remains a stock placeholder
for this editor test.

## Rebuild and check package locally

Building the original mesh requires Python, NumPy and Pillow. Installing the
already built package requires only Python's standard library.

```bash
python3 tools/build_australis_2030_mod.py
python3 tools/validate_australis_2030_mod.py
```
