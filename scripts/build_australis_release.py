"""Validate and archive a complete Australis release package for Windows 11.

The repository may store its single large OBJ as .obj.gz. It is expanded only
in temporary staging; the release archive always contains the editable .obj
and its original manifest hash, with no compressed source placeholder.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import tempfile
import zipfile

MODEL_RELATIVE = "payload/ships/ran_cvn_australis_2030/ran_cvn_australis_2030.obj"
MAX_MODEL_BYTES = 128 * 1024 * 1024


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_relative(value: str) -> bool:
    if not value or "\\" in value or re.search(r'[<>:"|?*\x00-\x1f]', value):
        return False
    path = PurePosixPath(value)
    if path.is_absolute() or str(path) != value:
        return False
    for part in value.split("/"):
        if part in ("", ".", "..") or part[-1:] in (".", " "):
            return False
        if re.match(r"(?i)^(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)", part):
            return False
    return True


def verify_package(package: Path, version: str) -> dict:
    manifest_path = package / "PACKAGE-MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["schema"] == 1 and manifest["version"] == version, "Wrong release manifest"
    assert manifest["mod_directory_name"] == "RAN-HMAS-Australis"
    paths = sorted(package.rglob("*"))
    assert not any(p.is_symlink() for p in paths), "Symlinks cannot be released"
    files = {p.relative_to(package).as_posix(): p for p in paths if p.is_file()}
    assert all(safe_relative(name) for name in files), "Unsafe Windows package path"
    assert len({name.casefold() for name in files}) == len(files), "Case-insensitive path collision"
    listed = manifest["files"]
    assert set(files) - {"PACKAGE-MANIFEST.json"} == set(listed), "Manifest file set differs"
    for name, expected in listed.items():
        assert re.fullmatch("[a-f0-9]{64}", expected) and sha(files[name]) == expected, f"Hash mismatch: {name}"
    for required in (
        "Clean-Install-Australis.ps1", "Helpers/Cvn-Helpers.ps1", "Helpers/Restore-Cvn.ps1",
        "payload/VERSION", "payload/_info.ini", "payload/RAN.Australis.DeckController.dll",
        "payload/vessels/ran_cvn_australis_2030.ini", "payload/vessels/ran_cvn_australis_2030_variants.ini",
        "payload/ships/ran_cvn_australis_2030/ran_cvn_australis_2030.obj",
        "payload/ships/ran_cvn_australis_2030/ran_cvn_australis_2030.mtl",
    ):
        assert required in files, f"Missing {required}"
    assert (package / "payload/VERSION").read_text().strip() == version
    vessel_roots = []
    for path in (package / "payload/vessels").glob("*.ini"):
        text = path.read_text(encoding="utf-8-sig")
        if re.search(r"(?mi)^\s*UnitType\s*=\s*Vessel\s*$", text):
            vessel_roots.append(path.stem)
    assert vessel_roots == ["ran_cvn_australis_2030"], f"Duplicate or wrong vessel roots: {vessel_roots}"
    assert re.search(r"(?mi)^\s*AircraftCapacity\s*=\s*99\s*$", (package / "payload/vessels/ran_cvn_australis_2030.ini").read_text())
    assert re.search(r"(?mi)^\s*NumberOfVariants\s*=\s*4\s*$", (package / "payload/vessels/ran_cvn_australis_2030_variants.ini").read_text())
    names = (package / "payload/language_en/vessel_names.ini").read_text(encoding="utf-8-sig")
    assert re.search(r"(?m)^\[ran_cvn_australis_2030\]$", names)
    assert "24 aircraft test" not in names.casefold()
    assert not any("ran_cvn_southern_cross_2030" in name for name in files if name.startswith("payload/vessels/"))
    return {"version": version, "manifest_verified_files": len(listed), "stable_ship_id": vessel_roots[0], "vessel_class_count": len(vessel_roots), "windows_executed": False, "live_game_tested": False}


def stage_package(source: Path, destination: Path) -> str:
    """Resolve the exact optional compressed source asset without editing source."""
    paths = list(source.rglob("*"))
    assert not source.is_symlink() and not any(p.is_symlink() for p in paths), "Symlinks cannot be released"
    assert all(safe_relative(p.relative_to(source).as_posix()) for p in paths), "Unsafe source package path"
    raw = source / MODEL_RELATIVE
    compressed = source / (MODEL_RELATIVE + ".gz")
    assert not (raw.exists() and compressed.exists()), "Raw and compressed model coexist; choose one source representation"
    assert raw.is_file() or compressed.is_file(), "Required Australis source model is missing"
    shutil.copytree(source, destination)
    if not compressed.is_file():
        return "raw OBJ"
    manifest = json.loads((source / "PACKAGE-MANIFEST.json").read_text(encoding="utf-8"))
    expected_hash = manifest["files"][MODEL_RELATIVE]
    assert re.fullmatch("[a-f0-9]{64}", expected_hash), "Invalid uncompressed model hash"
    expanded = destination / MODEL_RELATIVE
    written = 0
    actual_hash = hashlib.sha256()
    with gzip.open(compressed, "rb") as original, expanded.open("wb") as output:
        while True:
            block = original.read(min(1024 * 1024, MAX_MODEL_BYTES - written + 1))
            if not block:
                break
            written += len(block)
            assert written < MAX_MODEL_BYTES, "Expanded source model must be smaller than 128 MiB"
            actual_hash.update(block)
            output.write(block)
    assert actual_hash.hexdigest() == expected_hash, "Expanded source model differs from its manifest hash"
    (destination / (MODEL_RELATIVE + ".gz")).unlink()
    return "gzip source expanded to verified raw OBJ"


def build_staged(package: Path, launcher: Path, output: Path, version: str) -> dict:
    report = verify_package(package, version)
    assert launcher.is_file() and launcher.name == "Install-Australis.cmd"
    output.mkdir(parents=True, exist_ok=True)
    archive_path = output / f"Australis-v{version}-Windows11.zip"
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(package.rglob("*")):
            if path.is_file():
                member = zipfile.ZipInfo(path.relative_to(package).as_posix(), (1980, 1, 1, 0, 0, 0))
                member.create_system = 3
                member.external_attr = (stat.S_IFREG | 0o644) << 16
                member.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(member, path.read_bytes(), compresslevel=9)
    published_launcher = output / launcher.name
    if published_launcher.resolve() != launcher.resolve():
        published_launcher.write_bytes(launcher.read_bytes())
    checksums = {archive_path.name: sha(archive_path), launcher.name: sha(published_launcher)}
    (output / "SHA256SUMS.txt").write_text("".join(f"{digest}  {name}\n" for name, digest in checksums.items()), encoding="ascii")
    report.update({"archive": archive_path.name, "archive_bytes": archive_path.stat().st_size, "sha256": checksums, "zip_integrity_passed": False})
    with zipfile.ZipFile(archive_path) as archive:
        assert archive.testzip() is None
        assert "PACKAGE-MANIFEST.json" in archive.namelist()
        assert all(safe_relative(x) for x in archive.namelist())
    report["zip_integrity_passed"] = True
    (output / "RELEASE-CHECKS.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def build(package: Path, launcher: Path, output: Path, version: str) -> dict:
    with tempfile.TemporaryDirectory(prefix="Australis-release-stage-") as temporary:
        staged = Path(temporary) / "package"
        representation = stage_package(package, staged)
        report = build_staged(staged, launcher, output, version)
    report["repository_model_representation"] = representation
    report["release_model_representation"] = "editable raw OBJ"
    (output / "RELEASE-CHECKS.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    root = Path(__file__).resolve().parents[1]
    parser.add_argument("--version", default="1.3.1")
    parser.add_argument("--package", type=Path)
    parser.add_argument("--output", type=Path, default=root / "release-assets")
    args = parser.parse_args()
    assert re.fullmatch(r"\d+\.\d+\.\d+", args.version), "Stable semantic version required"
    package = args.package or root / "updates" / f"v{args.version}" / "package"
    print(json.dumps(build(package, root / "Install-Australis.cmd", args.output, args.version), indent=2))
