# Australis window glazing repair

The closer user screenshot shows the black strip extending directly from the
bridge window row. It persists after v1.3.1's mesh batching correction. That
earlier oversized batch was a real compatibility risk, but it did not resolve
this observed fault.

This repair addresses a separate demonstrated source defect: **244 of 3,928
window triangles have zero-area UV mappings**. Their texture derivatives cannot
define a tangent basis. Some remaining triangles have extreme derivatives:
the maximum calculated tangent magnitude is approximately 2,158.78 before the
repair and 0.02805 afterward. This is a source defect and a plausible render-path
problem; its connection to the exact in-game strip remains unconfirmed.

`repair_window_glazing.py` regenerates finite per-triangle projected UVs for all
66 named panes. All positions, normals, triangle vertex/normal indices, object
names and OBJ material assignments remain exact. Pane names continue to match
the existing night-light controller. New pane UVs occupy source indices 1-11784;
the previous UV table moves intact and every other face is remapped to its same
UV values. All 381,098 non-window triangles preserve their mapping exactly.

The panes retain the known `Marmoset/Bumped Specular IBL` shader and original
opaque `glass.png`. Only their INI `_BumpMap` and `_SpecTex` bindings are removed.
The shader itself remains a bumped shader; this is not a claim that every tangent
path has been disabled. The two other glass fittings use a byte-identical copy
of their original material as `glass_fittings_mat.ini`, so this material change
affects only the 66 panes. The shared OBJ MTL remains unchanged for those fittings;
the native per-submodel INI material overrides provide the scoped pane setup.

The independent audit checks every old/new triangle and derives all window
tangent/bitangent vectors. After repair, no pane has a zero-area UV triangle;
all 3,928 have a finite, nonzero tangent basis. Minimum absolute UV determinant
is approximately 0.01143. Previous mesh batch limits, shape, waterline, attachment
points, and controller DLL remain unchanged. All 141 other model-folder assets
match the preceding package hashes. Glass texture alpha remains 255 throughout.

Run the repair against the delivered v1.3.1 payload:

```sh
python window-repair/repair_window_glazing.py --payload build-package/payload --report window-repair/WINDOW-REPAIR-REPORT.json
python window-repair/audit_window_glazing.py
```

The audit expects the original v1.3.1 OBJ, vessel INI and glass material under
`window-repair-baseline/`. Source OBJ SHA256 must be
`df050f9f730242db5045afad7aa24540c3db22eb13af0b1b01a2b3c21cfbde65`.
The repair refuses other inputs before writing. Final OBJ SHA256 is
`705258092c28e3b3282ce264b5ceb889ee1c8a56b8b528714c280df6f100ec60`.

Evidence files are `WINDOW-REPAIR-REPORT.json`, `WINDOW-INDEPENDENT-CHECKS.json`
and `WINDOW-ASSET-CHECKS.json`. Native Windows and Sea Power tests remain
outstanding. Retest the same close bridge view and both window rows in a new
scenario, then check evening/night illumination.
