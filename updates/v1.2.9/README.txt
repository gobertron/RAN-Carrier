HMAS AUSTRALIS v1.2.9 - MODDED AIRCRAFT SELECTION FIX
Windows 11 / Windows PowerShell 5.1

1. In Sea Power's Mod Manager, enable the aircraft mod you want to use and
   your local RAN / HMAS Australis carrier. Disable duplicate Australis copies.
2. Exit Sea Power completely so the saved mod order is current.
3. Extract this ZIP, then double-click Refresh-Australis-Mod-Aircraft-v1.2.9.cmd.
4. Restart Sea Power. Use a NEW mission and a NEW Australis carrier, then edit
   its air group and add aircraft from the enabled aircraft mods.

Repeat step 3 after installing or enabling more aircraft mods.
The normal game location is detected automatically, including
F:\SteamLibrary\steamapps\common\Sea Power.
For another location, drag the Sea Power game folder onto the Refresh CMD.

WHAT THIS PATCH DOES
- Discovers stock aircraft plus the always-loaded user tree and enabled local
  and Steam Workshop aircraft mods, using your saved Mod Manager load order.
- Refreshes FlightDeck/AircraftSupported and retains existing custom/embarked
  aircraft IDs. Existing air group, squadron choices and aircraft counts remain.
- Updates existing file-ownership hashes and writes a separate patch report.
- Creates a verified backup outside StreamingAssets before applying changes.
- Preserves base carrier VERSION and in-game description (for example v1.2.8).
  Applied patch version 1.2.9 is recorded in AUSTRALIS-MOD-AIRCRAFT-PATCH.json.

CHECK ONLY
Run Check-Australis-Mod-Aircraft-v1.2.9.cmd for discovery without game changes.

RESTORE
The installer prints the backup folder. Drag that folder onto
Restore-Australis-Mod-Aircraft-v1.2.9.cmd to restore that transaction.
For a non-default game location, use the PowerShell command below instead.
Restore refuses to overwrite files edited after the patch. If you refreshed
several times, restore the newest transaction first, then older ones.

LOGS AND RESULTS
Each CMD creates a dated transcript in your Downloads folder and prints its
location. Copy the transcript or the final error if something fails.
The patch report in the active Australis mod lists discovered aircraft, source
mods, disabled entries and any unreadable definitions.

Aircraft mods must remain enabled. This patch does not enable mods or install
missing aircraft assets. It fixes selection; launch/landing compatibility still
depends on the aircraft and carrier definitions. Flight-deck routes, models,
weapons, controller DLLs and preloader are not changed by this patch.

MANUAL POWERSHELL OPTIONS (game closed)
  powershell -NoProfile -ExecutionPolicy Bypass -File ".\Source-and-Checks\Apply-Mod-Aircraft.ps1" -Mode Install -GameDirectory "F:\SteamLibrary\steamapps\common\Sea Power"
  powershell -NoProfile -ExecutionPolicy Bypass -File ".\Source-and-Checks\Apply-Mod-Aircraft.ps1" -Mode Restore -GameDirectory "F:\SteamLibrary\steamapps\common\Sea Power" -BackupDirectory "<printed backup folder>"
  Optional -LoadOrderPath "<usersettings.ini>" selects an explicit saved order.

VALIDATION
Actual PowerShell fixture tests cover discovery, disabled mods, refresh after
new aircraft, byte/encoding preservation, manifest hashes, rollback/restore
and refusal to overwrite later user edits. See TEST-RESULTS.json for the exact
test runtime. No live Sea Power flight test is claimed.
