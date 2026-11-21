RAN / HMAS AUSTRALIS v1.4.0 - R.A.T.S. KEEL / WINDOWS 11

Close Sea Power and run the same Install-Australis.cmd launcher. It fetches the
latest stable Australis release, verifies its checksum, stages the replacement,
backs up the previous carrier, and records rollback information.

LOADER SETUP
Use the official R.A.T.S. Keel release (validated here with v0.6.0 and v0.7.0), enabled in
Sea Power's Mods menu. Keel supplies the compatible AnchorChain library used by
Australis's existing controller; the separate AnchorChain Workshop item and its
preloader are no longer an Australis installation requirement.

Official Workshop: https://steamcommunity.com/sharedfiles/filedetails/?id=3835527459
Official release: https://github.com/struckl/SeaPowerKeel/releases/tag/v0.7.0
Official installation guide: https://github.com/struckl/SeaPowerKeel/blob/v0.7.0/docs/install.md

If Keel or BepInEx 5.4.23.2+ is not set up, use the official KeelSetup.exe from Keel's own
folder. Enable Keel in Mods and close the game before running this launcher.
Keel files are not bundled in Australis. The installer uses an enabled local or
Workshop Keel copy. It can add a missing verified starter and takeover patcher
from that copy. Unknown existing files or incompatible loader settings stop
preflight with a specific action; they are preserved. The controller also
requires the existing Harmony 2.9.0.0+ runtime shipped with this BepInEx setup.

Existing AnchorChain/Alpine loader files are not deleted or renamed. Keel's
own takeover patcher handles loader ownership. Other platforms and aircraft
mods retain their settings. Restart after changing the mod list; if Keel asks
for another restart, follow that message.

WHAT THIS RELEASE PRESERVES
One Australis-class CVN, stable ID ran_cvn_australis_2030, 99 aircraft capacity
and the four normal sister ships, hulls 91-94. Existing enabled modded aircraft
selection, air-wing retention, routes, weapons, sensors, lighting, mechanisms
and the v1.3.2 window UV/material repair are retained. The actual model assets
and controller DLL are unchanged in this loader migration. Aircraft inclusion
still does not prove every airframe can safely launch or recover.

The prior game-build allowlist is unchanged. Keel loader compatibility is
separate from compatibility of Australis's reflection-based game hooks. No
unknown game assembly is newly approved for fresh installation by this update.

VERIFICATION
40 passed, 0 failed; PowerShell 7.4.13 / Linux.
Actual controller and official Keel compatibility-library ABI checks passed. TriggerEntryPoint was not invoked; this is not a live game-hook test. See Source-and-Checks/Keel-ABI-CHECKS.json.
Package hashes, the single platform ID and the unchanged assets are checked.
Native Windows and live Sea Power results must be read separately from offline
fixture results. Historical v1.3.2 evidence is labelled under Source-and-Checks.
The user confirmed v1.3.1 loads one class, but its black window strip persisted.
The v1.3.2 visual repair has no confirmed live result in this release record.

IN-GAME TEST
Restart Sea Power, create a NEW 2030 scenario and add Australis. Ctrl+Shift+K
opens Keel's report; check that RAN Australis Enclosed Deck starts once.
Its unchanged legacy controller label can show 0.10.24 while this carrier
package is 1.4.0.
A Keel RUNNING result alone does not prove the controller hooks are active:
inspect the carrier's own RAN-Australis-DeckController.log for fresh
"Installed audited route/lift hooks" and "Bound" messages, and no "NOT ACTIVE:".
Also retain BepInEx/Keel-report.txt, BepInEx/Keel-log.txt and Keel-takeover.txt.
Check the windows, launch/recovery, helicopters/VTOL, lifts, catapults, CIWS6,
ICCS bubble, weapon bays and daylight/night/storm lighting in the actual game.

The installer prints its log, JSON report and restore archive path. To restore,
run the same launcher with game folder, Restore, and the printed archive path.
Archives keep the shared _Australis-CVN-v1.3.0 directory for compatibility.

WORKSHOP AUTHORS
If publishing this carrier as a Workshop item, set its required item to R.A.T.S.
Keel 3835527459. The GitHub package does not edit Steam Workshop relationships.
