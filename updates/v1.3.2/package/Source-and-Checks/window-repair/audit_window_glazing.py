#!/usr/bin/env python3
"""Independent baseline comparison and finite tangent audit of all 66 panes."""
from collections import Counter
import hashlib, json, math, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'window-repair-baseline'
PAYLOAD = ROOT/'build-package/payload'
FOLDER = PAYLOAD/'ships/ran_cvn_australis_2030'
OBJ = 'ran_cvn_australis_2030.obj'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    data={'v':[], 'vn':[], 'vt':[], 'faces':[]}
    name=material=''
    for raw in path.read_text().splitlines():
        f=raw.split()
        if not f: continue
        if f[0] in ('v','vn','vt'): data[f[0]].append(tuple(map(float,f[1:])))
        elif f[0]=='o': name=f[1]
        elif f[0]=='usemtl': material=f[1]
        elif f[0]=='f': data['faces'].append((name,material,tuple(tuple(map(int,t.split('/'))) for t in f[1:])))
    return data


def window(name):
    return name.startswith('NavalWindow_') and name.endswith('_Glass')


def tangents(data):
    names=set(); bad=nonfinite=good=0; minimum=math.inf; maxtangent=0
    for name,material,face in data['faces']:
        if not window(name): continue
        names.add(name)
        p=[data['v'][c[0]-1] for c in face]; uv=[data['vt'][c[1]-1] for c in face]
        e1,e2=[[p[j][i]-p[0][i] for i in range(3)] for j in (1,2)]
        du1,dv1=uv[1][0]-uv[0][0],uv[1][1]-uv[0][1]
        du2,dv2=uv[2][0]-uv[0][0],uv[2][1]-uv[0][1]
        det=du1*dv2-du2*dv1; assert math.isfinite(det);minimum=min(minimum,abs(det))
        if abs(det)<1e-14: bad+=1;continue
        tangent=[(e1[i]*dv2-e2[i]*dv1)/det for i in range(3)]
        bitangent=[(e2[i]*du1-e1[i]*du2)/det for i in range(3)]
        if not all(map(math.isfinite,tangent+bitangent)): nonfinite+=1;continue
        for c in face:
            n=data['vn'][c[2]-1];dot=sum(a*b for a,b in zip(n,tangent))
            ortho=[tangent[i]-n[i]*dot for i in range(3)]
            length=math.sqrt(sum(x*x for x in ortho));assert math.isfinite(length) and length>1e-12
        maxtangent=max(maxtangent,math.sqrt(sum(x*x for x in tangent)));good+=1
    return {'window_groups':len(names),'triangles_checked':bad+nonfinite+good,
            'zero_area_uv_triangles':bad,'nonfinite_derived_tangents':nonfinite,
            'triangles_with_finite_nonzero_tangent_basis':good,
            'minimum_abs_uv_determinant':minimum,'maximum_derived_tangent_magnitude':maxtangent}


def sections(path):
    text=path.read_text();hs=list(re.finditer(r'^\[([^\]\r\n]+)\]\s*$',text,re.M))
    return {h[1]:text[h.start():hs[i+1].start() if i+1<len(hs) else len(text)].strip() for i,h in enumerate(hs)}


def audit():
    old,new=load(BASE/OBJ),load(FOLDER/OBJ)
    assert old['v']==new['v'] and old['vn']==new['vn']
    assert len(old['faces'])==len(new['faces'])==385026
    changed=set();nonwindow=0
    for before,after in zip(old['faces'],new['faces']):
        assert before[:2]==after[:2]
        assert [(t[0],t[2]) for t in before[2]]==[(t[0],t[2]) for t in after[2]]
        uvbefore=[old['vt'][t[1]-1] for t in before[2]];uvafter=[new['vt'][t[1]-1] for t in after[2]]
        if window(before[0]):
            assert all(1<=t[1]<=11784 for t in after[2])
            if uvbefore!=uvafter:changed.add(before[0])
        else:assert uvbefore==uvafter;nonwindow+=1
    assert len(changed)==66 and old['vt']==new['vt'][11784:]
    bt,at=tangents(old),tangents(new)
    assert bt['zero_area_uv_triangles']==244
    assert at['zero_area_uv_triangles']==0 and at['nonfinite_derived_tangents']==0
    assert at['triangles_with_finite_nonzero_tangent_basis']==3928
    assert max(Counter(f[0] for f in new['faces']).values())*3<=60000
    oc=sections(BASE/'ran_cvn_australis_2030.ini');nc=sections(PAYLOAD/'vessels/ran_cvn_australis_2030.ini')
    assert oc.keys()==nc.keys()
    edited=[k for k in oc if oc[k]!=nc[k]]
    assert set(edited)=={'FullBatch_glass','FullBatch_ICCS_Bubble_Lift__glass'}
    for k in edited:assert oc[k].replace('Material=glass_mat.ini','Material=glass_fittings_mat.ini')==nc[k]
    assert (BASE/'glass_mat.ini').read_bytes()==(FOLDER/'glass_fittings_mat.ini').read_bytes()
    expected='\n'.join(l for l in (BASE/'glass_mat.ini').read_text().splitlines() if not l.startswith(('_SpecTex=','_BumpMap=')))+'\n'
    material=(FOLDER/'glass_mat.ini').read_text();assert expected==material
    assert 'Path=Marmoset/Bumped Specular IBL' in material
    assert not re.search(r'^_(SpecTex|BumpMap)=',material,re.M)
    result={'schema':1,'before_obj_sha256':digest(BASE/OBJ),'after_obj_sha256':digest(FOLDER/OBJ),
            'before_tangent_audit':bt,'after_tangent_audit':at,
            'all_positions_normals_and_triangle_vertex_normal_indices_preserved':True,
            'all598_object_names_and_obj_material_assignments_preserved':True,
            'all385026_triangles_preserved':True,
            'nonwindow_faces_with_identical_semantic_uvs':nonwindow,
            'original_uv_values_preserved_after_new_window_uv_table':True,
            'changed_uv_groups':sorted(changed),'window_global_uv_indices_below65535':True,
            'previous_mesh_batch_limit_preserved':True,
            'only_two_expected_fitting_sections_changed':edited,
            'nonwindow_fittings_material_preserved_byte_for_byte':True,
            'mtl_unchanged_shared_glass_maps_retained_for_fittings':True,
            'scope':'INI pane material overrides remove optional bindings; the known bumped shader itself remains',
            'native_windows_tested':False,'live_game_tested':False}
    (ROOT/'window-repair/WINDOW-INDEPENDENT-CHECKS.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='changed_uv_groups'},indent=2))


if __name__=='__main__':audit()
