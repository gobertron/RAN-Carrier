# Australis installable builds

[RAN-Carrier-Australis-2030-2026-10-24.zip](RAN-Carrier-Australis-2030-2026-10-24.zip) contains the independent 38-file carrier mod,
its standard-library Python installer and validator, a SHA256 inventory, and
installation/rollback instructions. Extract it to Downloads and follow README.txt.

Built from `e04142174e9e3ee41dd5b5dcf85d385133de5cf3`, model revision `64724edac9bc`.
The air group starts empty for user-selected installed carrier-capable aircraft.

Validation: package and stock references pass. The extracted ZIP passes fresh
installation, repeat installation, verified backup/removal and reinstallation
in an isolated test game tree; protected files remain unchanged. In-game flight
cycles, wheel contact and combat still require testing.

Archive SHA256: `eaa109f2caa56943250e9d2fe2f17892b82fefd7f14c80d1c8fc3ea69dfd591a`.


## Retractable CIWS build

[RAN-Carrier-Australis-2030-CIWS-2026-10-24.zip](RAN-Carrier-Australis-2030-CIWS-2026-10-24.zip) includes39 game files and native engagement-drivenCIWSdeployment. Opening is0.4s; closing1s after the nativeidle/restcondition. Source `6bd0366bde6667178909198f43b0ed68c24c355f`. Extracted ZIP validation and isolated install/backup/removal/reinstall pass; actual in-game engagement testing remains pending.
