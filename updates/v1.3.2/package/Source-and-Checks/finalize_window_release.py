#!/usr/bin/env python3
"""Finalize Australis 1.3.2 window repair metadata; rerun after installer checks."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "build-package"
PAYLOAD = PACKAGE / "payload"
VERSION = "1.3.2"
PREVIOUS_MODEL_HASH = "df050f9f730242db5045afad7aa24540c3db22eb13af0b1b01a2b3c21cfbde65"
REPORTED_GAME_HASH = "46d765d07124c80149a3fc84aa5e4899efe85acf479a6e32f08d5c0bec3c9c16"
WINDOW_REPORT = ROOT / "window-repair/WINDOW-REPAIR-REPORT.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(data)
    temporary.replace(path)


def copy(source: Path, target: Path) -> None:
    atomic(target, source.read_bytes())


def dump(path: Path, value) -> None:
    atomic(path, (json.dumps(value, indent=2) + "\n").encode("utf-8"))


def inventory(folder: Path, exclude=()) -> dict[str, str]:
    return {p.relative_to(folder).as_posix(): sha(p) for p in sorted(folder.rglob("*"))
            if p.is_file() and "__pycache__" not in p.parts
            and p.relative_to(folder).as_posix() not in exclude}


def copy_tree(source: Path, destination: Path) -> None:
    for path in sorted(source.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts:
            copy(path, destination / path.relative_to(source))


def retain_previous_evidence(sources: Path) -> dict:
    historical = sources / "historical/v1.3.1"
    history_provenance = historical / "BUILD-PROVENANCE.json"
    if not (historical / "EVIDENCE-LABEL.txt").exists():
        previous = json.loads((PACKAGE / "BUILD-PROVENANCE.json").read_text())
        assert previous["version"] == "1.3.1", "Original v1.3.1 provenance is required for the first finalization"
        for name in ("BUILD-PROVENANCE.json", "TEST-RESULTS.json", "README.txt"):
            path = PACKAGE / name
            if path.is_file():
                copy(path, historical / name)
        # Snapshot the prior evidence without recursively copying this snapshot.
        for entry in sorted(sources.iterdir()):
            if entry.name == "historical":
                continue
            destination = historical / "Source-and-Checks" / entry.name
            if entry.is_dir():
                copy_tree(entry, destination)
            elif entry.is_file():
                copy(entry, destination)
        atomic(historical / "EVIDENCE-LABEL.txt", (
            "Historical Australis v1.3.1 source and checks.\n"
            "User subsequently confirmed one class loads, while the black window strip persists.\n"
            "These files are not v1.3.2 verification results.\n").encode())
        # The old evidence is retained above; leave current sources unambiguous.
        for entry in list(sources.iterdir()):
            if entry.name == "historical":
                continue
            if entry.is_dir():
                shutil.rmtree(entry)
            else:
                entry.unlink()
    previous = json.loads(history_provenance.read_text())
    assert previous["version"] == "1.3.1"
    assert previous["model_sha256_after"] == PREVIOUS_MODEL_HASH
    return previous


def set_ini_value(text: str, section: str, key: str, value: str) -> str:
    headers = list(re.finditer(r"(?m)^\[([^\]\r\n]+)\][ \t]*$", text))
    matches = [i for i, header in enumerate(headers) if header[1].casefold() == section.casefold()]
    assert len(matches) == 1
    index = matches[0]
    start = headers[index].start()
    end = headers[index + 1].start() if index + 1 < len(headers) else len(text)
    raw = text[start:end]
    pattern = re.compile(r"(?m)^" + re.escape(key) + r"=[^\r\n]*$")
    assert len(pattern.findall(raw)) == 1, key
    raw = pattern.sub(lambda _: key + "=" + value, raw)
    return text[:start] + raw + text[end:]


def finalize() -> dict:
    report = json.loads(WINDOW_REPORT.read_text())
    model = PAYLOAD / "ships/ran_cvn_australis_2030/ran_cvn_australis_2030.obj"
    model_hash = sha(model)
    assert report["before_obj_sha256"] == PREVIOUS_MODEL_HASH
    assert report["after_obj_sha256"] == model_hash
    for field in ("positions_preserved", "normals_preserved", "triangle_position_indices_preserved", "nonwindow_uv_semantics_preserved"):
        assert report[field] is True, field
    assert report["degenerate_uv_triangles_after"] == 0
    assert report["window_groups_repaired"] == 66
    assert report["degenerate_uv_triangles_before"] == 244
    assert report["live_game_tested"] is False
    independent = json.loads((ROOT / "window-repair/WINDOW-INDEPENDENT-CHECKS.json").read_text())
    assert independent["after_obj_sha256"] == model_hash
    assert independent["after_tangent_audit"]["window_groups"] == report["window_groups_repaired"]
    assert independent["after_tangent_audit"]["triangles_checked"] == report["window_triangle_count"]
    assert independent["after_tangent_audit"]["zero_area_uv_triangles"] == 0
    material_root = PAYLOAD / "ships/ran_cvn_australis_2030"
    assert sha(material_root / "glass_mat.ini") == report["after_material_sha256"]
    assert sha(material_root / "glass_fittings_mat.ini") == report["fittings_material_sha256"]
    for suffix in ("", "_variants"):
        assert not (PAYLOAD / ("vessels/ran_cvn_southern_cross_2030" + suffix + ".ini")).exists()

    manifest_path = PACKAGE / "PACKAGE-MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    supported = list(manifest["supported_game_assembly_sha256"])
    assert REPORTED_GAME_HASH not in supported
    sources = PACKAGE / "Source-and-Checks"
    previous = retain_previous_evidence(sources)
    assert supported == previous["supported_game_assembly_sha256"], "Fresh-install game assembly allowlist changed"
    controller_hash = sha(PAYLOAD / "RAN.Australis.DeckController.dll")
    assert controller_hash == previous["controller_sha256"], "Lighting controller unexpectedly changed"
    assert sha(PACKAGE / "loader/BepInEx/plugins/AnchorChain.Preloader.dll") == previous["official_preloader_sha256"]

    installer = ROOT / "Clean-Install-Australis.ps1"
    assert "version='1.3.2'" in installer.read_text(), "Current 1.3.2 installer is required"
    copy(installer, PACKAGE / installer.name)
    for name in ("Cvn-Helpers.ps1", "Restore-Cvn.ps1"):
        copy(ROOT / name, PACKAGE / "Helpers" / name)
    window_sources = sources / "window-repair"
    if window_sources.exists():
        shutil.rmtree(window_sources)
    copy_tree(ROOT / "window-repair", window_sources)
    for path in (ROOT / "cvn-regression/run_regression.py", ROOT / "test_restore_fixtures.ps1",
                 ROOT / "restore-fixtures-results.json", Path(__file__).resolve(),
                 ROOT / "release-work/README-v1.3.2.txt"):
        copy(path, sources / path.name)

    regression_path = ROOT / "cvn-regression/TEST-RESULTS.json"
    regression = json.loads(regression_path.read_text()) if regression_path.exists() else None
    current_hashes = {"installer_sha256": sha(installer), "helpers_sha256": sha(ROOT / "Cvn-Helpers.ps1"),
                      "restore_sha256": sha(ROOT / "Restore-Cvn.ps1"),
                      "test_source_sha256": sha(ROOT / "cvn-regression/run_regression.py")}
    regression_current = bool(regression and all(regression.get(key) == value for key, value in current_hashes.items()))
    if regression:
        copy(regression_path, PACKAGE / "TEST-RESULTS.json")
        copy(regression_path, sources / "INSTALLER-REGRESSION-RESULTS.json")
    if regression_current:
        status = f"{regression['passed']} passed, {regression['failed']} failed; {regression['runtime']}."
    elif regression:
        status = f"Historical result only ({regression['passed']} passed); current v1.3.2 installer checks are pending."
    else:
        status = "Current v1.3.2 installer checks are pending."
    evidence_status = {"release_version": VERSION, "installer_regression_matches_current_sources": regression_current,
                       "installer_source_sha256": current_hashes, "status": status,
                       "historical_evidence": "historical/v1.3.1", "live_game_tested": False}
    dump(sources / "EVIDENCE-STATUS.json", evidence_status)

    readme = (ROOT / "release-work/README-v1.3.2.txt").read_text()
    for token, value in {"WINDOW_GROUPS": report["window_groups_repaired"],
                         "DEGENERATE_BEFORE": report["degenerate_uv_triangles_before"],
                         "DEGENERATE_AFTER": report["degenerate_uv_triangles_after"],
                         "REGRESSION_STATUS": status}.items():
        readme = readme.replace("{{" + token + "}}", str(value))
    assert "{{" not in readme
    atomic(PACKAGE / "README.txt", readme.encode())
    atomic(PAYLOAD / "README.txt", readme.encode())
    atomic(PAYLOAD / "VERSION", (VERSION + "\n").encode())
    info_path = PAYLOAD / "_info.ini"
    info = info_path.read_text()
    info = set_ini_value(info, "Language_en", "Name", "RAN / HMAS Australis v1.3.2")
    description_match = re.search(r"(?m)^Description=([^\r\n]*)$", info)
    assert description_match
    description = re.sub(r"\\r\\n\\r\\nv1\.3\.[12]:.*$", "", description_match[1])
    description += (r"\r\n\r\nv1.3.2: window UV mapping and window-material dependency repair; retains the single 99-aircraft class, existing lighting controller and enabled modded aircraft selection. v1.3.1 loaded one class but its black window strip persisted. A visual Sea Power retest is required.")
    info = set_ini_value(info, "Language_en", "Description", description)
    atomic(info_path, info.encode())
    testplan = """AUSTRALIS v1.3.2 IN-GAME RETEST

1. Close/restart Sea Power, then create a NEW 2030 scenario and carrier.
2. Confirm one normal 99-aircraft class and four sister-ship variants.
3. Inspect both islands from each side, close up and at distance, for the black window strip.
4. Check windows and existing lighting in daylight, dusk, night and storm conditions.
5. Stow/deploy the two 579m Nixie decoys and assess their native pale cables separately.
6. Test enabled modded aircraft selection and the intended airframe's deck fit.
7. Test fixed-wing launch/recovery, helicopters, VTOL, lifts and catapults.
8. Test CIWS6, the ICCS bubble and weapon bays under applicable native conditions.
9. If the strip remains, retain a close-up screenshot, installer log/JSON and game log.

The source UV/material corrections are verified offline. Visual and functional
success in Sea Power remain unconfirmed for v1.3.2.
"""
    atomic(PAYLOAD / "TESTPLAN.txt", testplan.encode())
    changelog_path = PAYLOAD / "CHANGELOG.txt"
    old = re.sub(r"(?s)^v1\.3\.2 - .*?\n\n", "", changelog_path.read_text(), count=1)
    entry = (f"v1.3.2 - window UV and material dependency repair\n"
             f"Repairs UVs in {report['window_groups_repaired']} window groups; "
             f"{report['degenerate_uv_triangles_before']} degenerate UV triangles become {report['degenerate_uv_triangles_after']}.\n"
             "Preserves positions, normals, triangle position indices and nonwindow UV\n"
             "semantics. Window-only glass drops bump/specular maps; two other glass\n"
             "fittings retain their original material. Existing night-lighting controller,\n"
             "single class, stable ID, sister variants and aircraft operations are retained.\n"
             "User confirmed v1.3.1 loads one class but the black window strip persists.\n"
             "No v1.3.2 visual or functional Sea Power success is claimed.\n\n")
    atomic(changelog_path, (entry + old).encode())
    provenance = {
        "schema": 1, "version": VERSION, "kind": "Australis window UV and material dependency repair",
        "repository": "gobertron/RAN-Carrier", "canonical_ship_id": "ran_cvn_australis_2030",
        "model_baseline": "v1.3.1 conservative batching on Full Restore v1.2.1 / v0.10.26",
        "last_user_confirmed_loaded_version": "1.3.1",
        "last_user_confirmation": {"version": "1.3.1", "single_class_loads": True,
            "black_window_strip_persists": True, "full_functional_success_confirmed": False},
        "earlier_working_baseline": {"version": "1.2.0", "limits": "Loading confirmed; lighting, aircraft and mechanisms had outstanding checks"},
        "model_sha256_before": report["before_obj_sha256"], "model_sha256_after": model_hash,
        "window_repair": report,
        "visual_fault_resolved_in_game": False,
        "source_defect_status": "Degenerate window UV source triangles corrected; the persistent black strip requires an in-game retest",
        "single_class_retained": {"canonical_id": "ran_cvn_australis_2030", "aircraft_capacity": 99,
            "sister_ships": ["HMAS Australis 91", "HMAS Southern Cross 92", "HMAS Federation 93", "HMAS Commonwealth 94"]},
        "native_nixie_decoys": previous["native_nixie_decoys"],
        "controller_sha256": controller_hash, "night_lighting_controller_unchanged": True,
        "controller_source": previous["controller_source"],
        "official_preloader_sha256": previous["official_preloader_sha256"],
        "official_workshop_core": previous["official_workshop_core"],
        "supported_game_assembly_sha256": supported,
        "reported_prior_game_assembly_sha256": REPORTED_GAME_HASH,
        "reported_game_hash_added_to_allowlist": False,
        "game_build_checked": "Original compatibility manifest and prior user logs; no new game runtime executed",
        "installer_regression_matches_current_sources": regression_current,
        "installer_regression_summary": status,
        "native_windows_tested": False, "live_game_tested": False,
        "historical_v1_3_1_evidence": "Source-and-Checks/historical/v1.3.1",
        "current_geometry_evidence": "Source-and-Checks/window-repair",
        "independent_window_audit": "Source-and-Checks/window-repair/WINDOW-INDEPENDENT-CHECKS.json",
    }
    dump(PACKAGE / "BUILD-PROVENANCE.json", provenance)
    dump(PAYLOAD / "RUNTIME-FILES.json", inventory(PAYLOAD, ("RUNTIME-FILES.json",)))
    manifest["version"] = VERSION
    manifest["audited_model_sha256"] = list(dict.fromkeys(list(manifest["audited_model_sha256"]) + [PREVIOUS_MODEL_HASH, model_hash]))
    assert manifest["supported_game_assembly_sha256"] == supported
    manifest["live_game_tested"] = False
    manifest["files"] = inventory(PACKAGE, ("PACKAGE-MANIFEST.json",))
    dump(manifest_path, manifest)
    assert manifest["files"] == inventory(PACKAGE, ("PACKAGE-MANIFEST.json",))
    assert json.loads((PAYLOAD / "RUNTIME-FILES.json").read_text()) == inventory(PAYLOAD, ("RUNTIME-FILES.json",))
    return {"version": VERSION, "model_sha256": model_hash, "package_files": len(manifest["files"]),
            "window_groups_repaired": report["window_groups_repaired"],
            "degenerate_uv_triangles_corrected": report["degenerate_uv_triangles_before"],
            "installer_regression_matches_current_sources": regression_current,
            "installer_regression_summary": status, "night_lighting_controller_unchanged": True,
            "native_windows_tested": False, "live_game_tested": False}


if __name__ == "__main__":
    print(json.dumps(finalize(), indent=2))
