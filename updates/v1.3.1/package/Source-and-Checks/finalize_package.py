#!/usr/bin/env python3
"""Refresh prepared Australis 1.3.1 metadata and inventories; rerun after tests."""
from pathlib import Path
import hashlib
import json
import shutil
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'build-package'
PAYLOAD = PACKAGE / 'payload'
VERSION = '1.3.1'
MODEL_HASH = 'df050f9f730242db5045afad7aa24540c3db22eb13af0b1b01a2b3c21cfbde65'
REPORTED_GAME_HASH = '46d765d07124c80149a3fc84aa5e4899efe85acf479a6e32f08d5c0bec3c9c16'
ORIGINAL_MODELS = ['a017c86cfac2491c791712e55571db3adbe48ca344a68b477c90a78d5ee05627',
                   'bd4f8e0222e27b475f226d455687c75493bb163418b8ccfc8504c210e6175fac']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(data)
    temporary.replace(path)


def dump(path, obj):
    atomic(path, (json.dumps(obj, indent=2) + '\n').encode())


def copy(source, target):
    atomic(target, source.read_bytes())


def inventory(folder, exclude=()):
    return {p.relative_to(folder).as_posix(): sha(p) for p in sorted(folder.rglob('*'))
            if p.is_file() and '__pycache__' not in p.parts
            and p.relative_to(folder).as_posix() not in exclude}


def finalize():
    manifest_path = PACKAGE / 'PACKAGE-MANIFEST.json'
    manifest = json.loads(manifest_path.read_text())
    supported = list(manifest['supported_game_assembly_sha256'])
    assert REPORTED_GAME_HASH not in supported
    model = PAYLOAD / 'ships/ran_cvn_australis_2030/ran_cvn_australis_2030.obj'
    assert sha(model) == MODEL_HASH
    assert (PAYLOAD / 'VERSION').read_text().strip() == VERSION
    for suffix in ('', '_variants'):
        assert not (PAYLOAD / ('vessels/ran_cvn_southern_cross_2030' + suffix + '.ini')).exists()
    copy(ROOT / 'Clean-Install-Australis.ps1', PACKAGE / 'Clean-Install-Australis.ps1')
    for name in ('Cvn-Helpers.ps1', 'Restore-Cvn.ps1'):
        copy(ROOT / name, PACKAGE / 'Helpers' / name)
    sources = PACKAGE / 'Source-and-Checks'
    if sources.exists():
        shutil.rmtree(sources)
    sources.mkdir()
    for folder in ('model-repair', 'class-repair'):
        for p in sorted((ROOT / folder).rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts:
                copy(p, sources / folder / p.relative_to(ROOT / folder))
    for p in (ROOT / 'cvn-regression/run_regression.py', ROOT / 'test_restore_fixtures.ps1',
              ROOT / 'restore-fixtures-results.json', Path(__file__).resolve()):
        copy(p, sources / p.name)
    regression_path = ROOT / 'cvn-regression/TEST-RESULTS.json'
    if regression_path.exists():
        copy(regression_path, PACKAGE / 'TEST-RESULTS.json')
        copy(regression_path, sources / 'INSTALLER-REGRESSION-RESULTS.json')
    readme = ROOT / 'release-work/README.txt'
    copy(readme, PACKAGE / 'README.txt')
    copy(readme, PAYLOAD / 'README.txt')
    if (PACKAGE / 'README-TEST.txt').exists():
        (PACKAGE / 'README-TEST.txt').unlink()
    testplan = '''AUSTRALIS v1.3.1 IN-GAME RETEST

1. Restart Sea Power and create a NEW 2030 scenario.
2. Confirm one normal 99-aircraft class and four sister-ship variants.
3. Reselect normal Southern Cross in scenarios using the removed test ID.
4. Inspect hull and both islands from each side for the former black spike.
5. Stow/deploy the two 579m Nixie decoys and check their native pale cables.
6. Test enabled modded aircraft selection and intended airframe deck fit.
7. Test launch/recovery, helicopters, VTOL, lifts and catapults.
8. Test dusk/night/storm lights, weapon bays, ICCS bubble and CIWS6.
9. Keep installer log, JSON report and game log for any failure.

Offline checks are not a live game pass.
'''
    atomic(PAYLOAD / 'TESTPLAN.txt', testplan.encode())
    changelog = PAYLOAD / 'CHANGELOG.txt'
    old = changelog.read_text()
    entry = '''v1.3.1 - single class and conservative mesh batching repair
Retires the separate 24-aircraft test definition, retaining the canonical
99-aircraft class, stable ID and sister variants 91-94. Splits five oversized
static batches while preserving triangles, materials, shape, root bounds,
waterline, colliders and moving references. Retains two 579m Nixie cables,
lighting/controller and enabled modded aircraft selection. Installer includes
intact-repeat detection plus migration and rollback checks. Source batch risk
confirmed; black spike explanation requires live Sea Power retest. Native
Windows and Sea Power execution remain outstanding.

'''
    if not old.startswith('v1.3.1 - '):
        atomic(changelog, (entry + old).encode())
    report = json.loads((ROOT / 'model-repair/MODEL-REPAIR-REPORT.json').read_text())
    assert report['after_obj_sha256'] == MODEL_HASH
    class_report = json.loads((ROOT / 'class-repair/CLASS-REPAIR-RESULTS.json').read_text())
    provenance = {
        'schema': 1, 'version': VERSION, 'kind': 'Australis single-class mesh repair',
        'repository': 'gobertron/RAN-Carrier', 'canonical_ship_id': 'ran_cvn_australis_2030',
        'model_baseline': 'Full Restore v1.2.1 / v0.10.26, consolidated in v1.3.0',
        'last_user_confirmed_working_version': '1.2.0',
        'last_working_version_limits': 'Loading confirmed; lights, aircraft and mechanisms had outstanding checks',
        'model_sha256_before': report['before_obj_sha256'], 'model_sha256_after': MODEL_HASH,
        'mesh_repair': {
            'objects_before': len(report['before']['objects']),
            'objects_after': len(report['after']['objects']),
            'triangle_count_preserved': report['after']['counts']['f'],
            'all_triangle_material_records_preserved': report['all_faces_and_material_assignments_preserved'],
            'coordinate_uv_normal_tables_preserved': report['all_position_uv_normal_tables_preserved'],
            'root_hull_bounds_preserved': report['root_hull_bounds_unchanged'],
            'max_expanded_face_corners_per_mesh': report['max_expanded_face_corners_per_mesh'],
            'new_static_meshes': report['added_static_meshes'],
            'cause_status': report['root_cause_status']},
        'single_class_repair': class_report,
        'native_nixie_decoys': {'count': 2, 'cable_length_m': 579, 'retained': True},
        'controller_sha256': sha(PAYLOAD / 'RAN.Australis.DeckController.dll'),
        'controller_source': 'v1.2.3 corrected lighting source retained in v1.2.8',
        'official_preloader_sha256': sha(PACKAGE / 'loader/BepInEx/plugins/AnchorChain.Preloader.dll'),
        'official_workshop_core': {'item_id': '3380210757', 'version': '1.2.0', 'bundled': False,
            'sha256': '17abaf4b006f2fe984807f62661cf8b78f7b01e60bb04ae16046bda0620dd614'},
        'supported_game_assembly_sha256': supported,
        'reported_prior_game_assembly_sha256': REPORTED_GAME_HASH,
        'reported_game_hash_added_to_allowlist': False,
        'game_build_checked': 'Prior user logs and original compatibility manifest; no new game runtime executed',
        'native_windows_tested': False, 'live_game_tested': False,
        'regression_report_included': regression_path.exists(),
        'geometry_and_class_reports': ['Source-and-Checks/model-repair/MODEL-REPAIR-REPORT.json',
            'Source-and-Checks/model-repair/INDEPENDENT-CHECKS.json',
            'Source-and-Checks/class-repair/CLASS-REPAIR-TESTS.json']}
    dump(PACKAGE / 'BUILD-PROVENANCE.json', provenance)
    dump(PAYLOAD / 'RUNTIME-FILES.json', inventory(PAYLOAD, ('RUNTIME-FILES.json',)))
    manifest['version'] = VERSION
    # Carry forward only delivered historical baselines, excluding abandoned
    # intermediate repair files that were never approved for delivery.
    manifest['audited_model_sha256'] = ORIGINAL_MODELS + [MODEL_HASH]
    assert manifest['supported_game_assembly_sha256'] == supported
    manifest['live_game_tested'] = False
    manifest['files'] = inventory(PACKAGE, ('PACKAGE-MANIFEST.json',))
    dump(manifest_path, manifest)
    assert manifest['files'] == inventory(PACKAGE, ('PACKAGE-MANIFEST.json',))
    assert json.loads((PAYLOAD / 'RUNTIME-FILES.json').read_text()) == inventory(PAYLOAD, ('RUNTIME-FILES.json',))
    return {'version': VERSION, 'package_files': len(manifest['files']),
            'payload_files': len(json.loads((PAYLOAD / 'RUNTIME-FILES.json').read_text())),
            'model_sha256': MODEL_HASH, 'regression_report_included': regression_path.exists(),
            'native_windows_tested': False, 'live_game_tested': False}


if __name__ == '__main__':
    print(json.dumps(finalize(), indent=2))
