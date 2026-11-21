# Australis mesh batching repair

The previous OBJ combines railings, edges and island trim in one `FullBatch_edge`
object with 132,280 triangles, 396,840 face corners and 291,427 distinct
position/UV/normal tuples. This exceeds a 16-bit per-mesh vertex index range.
Unity documents its default index format as 16 bit; its mesh importer may need
32-bit indices when meshes exceed 65,535 vertices:
https://docs.unity3d.com/ScriptReference/Mesh-indexFormat.html

The actual Sea Power runtime importer was not instrumented here. Its overflow
is a plausible explanation for the screenshot's black projecting line, not a
confirmed in-game diagnosis. No source positions lie outside the carrier's
bounds. The repair removes this concrete oversized-batch risk without changing
the vessel's shape or approved layout.

`repair_mesh_batches.py` splits five static groups at triangle boundaries into
chunks with at most 60,000 face corners, even if a loader expands every corner.
The first part retains the original object name. Twelve added parts receive
native `[Submodels]` registrations and matching material sections. Root hull
collider and all moving-part names and parent transforms remain unchanged.
The repaired model has 598 objects and 385,026 triangles.

The complete triangle/material multiset and all position, UV and normal tables
compare exactly to the previous source. Bounds and visible surface geometry
are unchanged. The first Hull chunk retains every original root-bound extremum,
including waterline and vertical bounds. Up to six original hull triangles move
earlier in the face order to preserve those bounds. Every resulting object has at most 47,878 distinct complete
vertex tuples. The repair is idempotent and uses atomic file replacement so
hardlinked historical files and test fixtures retain their original bytes.

Run from the project root:

```sh
python model-repair/repair_mesh_batches.py --payload build-package/payload --report model-repair/MODEL-REPAIR-REPORT.json
```

`MODEL-REPAIR-REPORT.json` records before/after counts, checksums and all new
submodel names. `INDEPENDENT-CHECKS.json` records a second comparison against
the unchanged extracted Full Restore v1.2.1 baseline.

The two native SLQ-25 Nixie decoys intentionally retain their 579 m cables.
Those can explain twin pale lines behind a vessel at 12 knots; they should be
retested separately from the black island spike. No decoy capability was removed.

Live Sea Power testing is still required: new scenario, one normal 99-aircraft
class, hull and both islands viewed from each side, moving mechanisms, towed
decoys stowed and deployed, and aircraft launch and recovery.
