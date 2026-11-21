RAN / HMAS AUSTRALIS v1.3.2 - WINDOWS 11

Close Sea Power, then double-click the same Install-Australis.cmd launcher.
It fetches the latest stable release, checks the package, stages the replacement
and records a backup for rollback. AnchorChain Workshop item 3380210757 remains
required. The installer prints its version, log and JSON report paths.

You confirmed that v1.3.1 loads one class, but its black window strip persists.
This release repairs the source UV mapping for 66 window groups:
244 degenerate UV triangles become 0. Window
positions, normals and triangle position indices are preserved. The window
material no longer depends on bump or specular maps; the other two glass
fittings retain their previous material through glass_fittings_mat.ini.
These source corrections still require a visual Sea Power retest. They do not
establish that the black strip has disappeared in game.

One 99-aircraft Australis class retains Australis 91, Southern Cross 92,
Federation 93 and Commonwealth 94. The stable ID is ran_cvn_australis_2030.
99 is capacity, not an automatic embarked total. Existing air wings are retained
where possible. Old missions using the retired 24-aircraft test ID need the
normal Southern Cross variant selected again.

The night-lighting controller is unchanged. Existing aircraft selection,
equipment, decoys, lifts, catapults and mechanisms are retained. Aircraft list
inclusion does not establish launch/recovery compatibility for every airframe.
The two native 579 m Nixie cables remain separate from the black window fault.

Current installer regression evidence: 23 passed, 0 failed; PowerShell 7.4.13 / Linux.
Checks performed on synthetic filesystems do not constitute a live Sea Power or
complete Windows installation test. The original fresh-install game assembly
allowlist is unchanged. No new game build has been approved by this release.

After updating, restart Sea Power and create a NEW 2030 scenario. Inspect both
islands from either side, close up and at distance. Then check daytime, dusk,
night and storm lighting, aircraft selection and launch/recovery, lifts,
catapults, CIWS6, the ICCS bubble and weapon bays. If the strip remains, retain a
close-up screenshot and the printed installer log, JSON report and game log.

Source and current evidence are in Source-and-Checks/window-repair and
BUILD-PROVENANCE.json. Historical v1.3.1 repair and installer evidence is labelled
under Source-and-Checks/historical/v1.3.1. The raw editable OBJ is included in the
release package; only its repository source representation may be gzip packed.

No v1.3.2 in-game retest is claimed.
