# Australis release packaging

Run `python3 scripts/build_australis_release.py --version 1.3.2` from the
repository root. The release workflow runs the same builder.

The repository stores the large model at
`updates/v1.3.2/package/payload/ships/ran_cvn_australis_2030/ran_cvn_australis_2030.obj.gz`
to fit repository upload limits. This is the only compressed source placeholder
the builder supports. The package manifest continues to name and checksum the
uncompressed `ran_cvn_australis_2030.obj`.

The builder copies source into temporary staging, expands that exact model with
a 128 MiB limit, checks the uncompressed SHA256 against the manifest, removes the
staged `.gz`, then verifies the complete normal package. The original source is
unchanged. A source containing both `.obj` and `.obj.gz` is rejected.

The published Windows ZIP contains the editable raw OBJ and normal game layout.
Neither the game nor the installer needs to handle a gzip file. The complete
manifest, stable vessel ID and single class are checked before archiving.

To create a reproducible compressed source manually, use Python's
`gzip.compress(raw_bytes, compresslevel=9, mtime=0)`. Keep the raw model's hash in
the manifest. Run `python3 scripts/test_australis_release_builder.py` to check raw
and compressed source equivalence, corruption and size limits.
