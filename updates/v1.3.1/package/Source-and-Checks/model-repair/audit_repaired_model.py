#!/usr/bin/env python3
"""Compare the prepared model against the extracted, unchanged known baseline."""
from pathlib import Path
import hashlib
import json
import re
from repair_mesh_batches import OBJ_REL, VESSEL_REL, parse, repair, section

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / 'build-package/payload'
BASELINE = ROOT / 'payload-assembly/baseline/payload'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit():
    obj, cfg = PAYLOAD / OBJ_REL, PAYLOAD / VESSEL_REL
    hashes = sha(obj), sha(cfg)
    rerun = repair(PAYLOAD)
    assert hashes == (sha(obj), sha(cfg))
    assert not rerun['added_static_meshes']
    before, after = parse((BASELINE / OBJ_REL).read_text()), parse(obj.read_text())
    assert before['face_material_multiset_sha256'] == after['face_material_multiset_sha256']
    assert before['coordinate_tables_sha256'] == after['coordinate_tables_sha256']
    assert before['bounds'] == after['bounds']
    assert before['objects']['Hull']['bounds'] == after['objects']['Hull']['bounds']
    old, new = (BASELINE / VESSEL_REL).read_text(), cfg.read_text()
    for name in re.findall(r'^\[([^\]]+)\]$', old, re.M):
        if name == 'Submodels':
            continue
        assert section(old, name)[2].strip() == section(new, name)[2].strip(), name
    _, _, new_parts = section(new, 'Submodels')
    parts = re.findall(r'^MeshRepair_\d+=(.+)$', new_parts, re.M)
    assert len(parts) == 12
    for name in parts:
        assert name in after['objects']
        _, _, body = section(new, name)
        assert f'Mesh={name}\n' in body
        assert not re.search(r'^(Position|Rotation|Scale|Parent)=', body, re.M)
        # Exactly the same unparented static-mesh schema as the loaded baseline.
        assert set(re.findall(r'^([A-Za-z]+)=', body, re.M)) == {'Mesh', 'Material'}
    result = {
        'mesh_repair_idempotent': True,
        'independent_baseline_triangle_material_multiset_comparison': True,
        'independent_baseline_coordinate_uv_normal_comparison': True,
        'all_original_ini_sections_except_submodels_byte_equivalent': True,
        'baseline_obj_unmodified': sha(BASELINE / OBJ_REL) == 'a017c86cfac2491c791712e55571db3adbe48ca344a68b477c90a78d5ee05627',
        'root_models_section_and_collider_unchanged': True,
        'root_hull_local_bounds_unchanged': before['objects']['Hull']['bounds'],
        'full_shape_bounds_unchanged': before['bounds'],
        'original_moving_part_names_and_hierarchy_unchanged': True,
        'additional_static_parts_match_loaded_baseline_native_schema': True,
        'general_dimensions_and_waterline_coordinates_unchanged': True,
        'objects_before': len(before['objects']), 'objects_after': len(after['objects']),
        'triangles_preserved': after['counts']['f'],
        'max_expanded_face_corners': max(x['expanded_corners'] for x in after['objects'].values()),
        'max_unique_tuples': max(x['unique_vertex_uv_normal_tuples'] for x in after['objects'].values()),
        'stock_game_files_available_for_new_comparison': False,
        'reference': 'Full Restore v1.2.1 source and the model shown loaded in user screenshots',
        'live_game_tested': False,
    }
    (ROOT / 'model-repair/INDEPENDENT-CHECKS.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    audit()
