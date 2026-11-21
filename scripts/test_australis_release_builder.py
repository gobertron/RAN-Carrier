"""Harmless release-layout fixtures for raw and gzip-stored Australis source."""
from __future__ import annotations

import gzip
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import zipfile

import build_australis_release as builder


class ReleaseBuilderTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="Australis-release-fixture-")
        self.root = Path(self.temporary.name)
        self.package = self.root / "package"
        self.launcher = self.root / "Install-Australis.cmd"
        self.launcher.write_text("@echo off\nrem harmless fixture\n")
        self.files = {
            "Clean-Install-Australis.ps1": "# harmless fixture\n",
            "Helpers/Cvn-Helpers.ps1": "# fixture\n",
            "Helpers/Restore-Cvn.ps1": "# fixture\n",
            "payload/VERSION": "1.3.1\n",
            "payload/_info.ini": "[Language_en]\nName=RAN / HMAS Australis\n",
            "payload/RAN.Australis.DeckController.dll": "fixture-only",
            "payload/vessels/ran_cvn_australis_2030.ini": "[General]\nUnitType=Vessel\n[FlightDeck]\nAircraftCapacity=99\n",
            "payload/vessels/ran_cvn_australis_2030_variants.ini": "[General]\nNumberOfVariants=4\n",
            builder.MODEL_RELATIVE: "v 0 0 0\nv 0 1 0\nv 1 0 0\nf 1 2 3\n",
            "payload/ships/ran_cvn_australis_2030/ran_cvn_australis_2030.mtl": "# fixture\n",
            "payload/language_en/vessel_names.ini": "[ran_cvn_australis_2030]\nDefault=Australis-class CVN - 99 aircraft,Australis\n",
        }
        for name, text in self.files.items():
            path = self.package / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        self.manifest = {"schema": 1, "version": "1.3.1", "mod_directory_name": "RAN-HMAS-Australis", "files": {name: builder.sha(self.package / name) for name in self.files}}
        self.write_manifest()

    def tearDown(self):
        self.temporary.cleanup()

    def write_manifest(self):
        (self.package / "PACKAGE-MANIFEST.json").write_text(json.dumps(self.manifest))

    def compress_model(self):
        path = self.package / builder.MODEL_RELATIVE
        data = path.read_bytes()
        compressed = path.with_name(path.name + ".gz")
        compressed.write_bytes(gzip.compress(data, compresslevel=9, mtime=0))
        path.unlink()
        return data, compressed

    def build(self, name="output"):
        return builder.build(self.package, self.launcher, self.root / name, "1.3.1")

    def test_raw_and_gzip_produce_identical_release_bytes(self):
        raw = self.build("raw-output")
        data, compressed = self.compress_model()
        before = compressed.read_bytes()
        packed = self.build("gzip-output")
        self.assertEqual(raw["sha256"], packed["sha256"])
        self.assertEqual(compressed.read_bytes(), before)
        self.assertFalse((self.package / builder.MODEL_RELATIVE).exists())
        with zipfile.ZipFile(self.root / "gzip-output" / packed["archive"]) as archive:
            self.assertEqual(archive.read(builder.MODEL_RELATIVE), data)
            self.assertNotIn(builder.MODEL_RELATIVE + ".gz", archive.namelist())

    def test_raw_and_gzip_coexistence_rejected(self):
        path = self.package / builder.MODEL_RELATIVE
        path.with_name(path.name + ".gz").write_bytes(gzip.compress(path.read_bytes(), mtime=0))
        with self.assertRaisesRegex(AssertionError, "coexist"):
            self.build()

    def test_corrupt_gzip_rejected(self):
        _, compressed = self.compress_model()
        compressed.write_bytes(b"not a gzip file")
        with self.assertRaises((OSError, EOFError)):
            self.build()

    def test_wrong_uncompressed_hash_rejected(self):
        _, compressed = self.compress_model()
        compressed.write_bytes(gzip.compress(b"v 999 999 999\n", mtime=0))
        with self.assertRaisesRegex(AssertionError, "manifest hash"):
            self.build()

    def test_expanded_size_limit_enforced(self):
        data, _ = self.compress_model()
        with mock.patch.object(builder, "MAX_MODEL_BYTES", len(data)):
            with self.assertRaisesRegex(AssertionError, "smaller than 128 MiB"):
                self.build()

    def test_changed_nonmodel_file_rejected(self):
        self.compress_model()
        (self.package / "payload/VERSION").write_text("tampered")
        with self.assertRaisesRegex(AssertionError, "Hash mismatch"):
            self.build()

    def test_duplicate_class_rejected_after_gzip_expansion(self):
        self.compress_model()
        name = "payload/vessels/ran_cvn_southern_cross_2030.ini"
        (self.package / name).write_text("[General]\nUnitType=Vessel\n")
        self.manifest["files"][name] = builder.sha(self.package / name)
        self.write_manifest()
        with self.assertRaisesRegex(AssertionError, "vessel roots"):
            self.build()

    def test_other_compressed_model_path_is_not_expanded(self):
        _, compressed = self.compress_model()
        compressed.rename(compressed.with_name("other.obj.gz"))
        with self.assertRaisesRegex(AssertionError, "source model is missing"):
            self.build()

    def test_reproducible_gzip_source(self):
        path = self.package / builder.MODEL_RELATIVE
        a = gzip.compress(path.read_bytes(), compresslevel=9, mtime=0)
        b = gzip.compress(path.read_bytes(), compresslevel=9, mtime=0)
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main(verbosity=2)
