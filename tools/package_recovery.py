#!/usr/bin/env python3
"""Package this reconstruction with checksums and an offline standalone installer."""
from pathlib import Path
import json,hashlib,base64,zipfile
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT.parent/'finished-v085'
LABEL='RAN-Carrier-Australis-v0.8.5-Naval-Details'
sha=lambda b:hashlib.sha256(b).hexdigest()
def selected():
    files=[]
    files+=list((ROOT/'game-mod/RAN-Carrier-Australis-2030').rglob('*'))
    files+=list((ROOT/'addon/DeckController').glob('*.cs'))
    files+=[ROOT/'addon/DeckController/LiftLightTests.cs.txt']
    files += [ROOT/'addon/bin/RAN.Australis.DeckController.dll']
    files += [ROOT/n for n in ('VERSION','RECOVERY-README.md','WATERJET-ENGINEERING-REVIEW.md','generate_source_models.py','rebuild_game_scale.py')]
    files += list((ROOT/'australis-2030').glob('*.py'))
    files += [ROOT/'australis-2030/model/source'/f'ran_cvn_australis_2030.{ext}' for ext in ('obj','mtl')]
    files += [ROOT/'australis-2030/spec.json']
    files += [ROOT/'tools'/n for n in ('build_australis_2030_mod.py','build_deck_controller.py','build_internal_arrangement.py','internal_fit.py','rebuild_recovery.py','validate_recovery.py','install_recovery.py','test_recovery_installer.py','package_recovery.py','build_current_game_preview.py','audit_naval_hull.py','preview_naval_hull.py','screen_waterjet_engineering.py','test_lift_lighting.py','class_list.py','build_network_installer.py')]
    return sorted({p for p in files if p.is_file() and '__pycache__' not in p.parts})
def main():
    OUT.mkdir(exist_ok=True)
    import sys
    sys.path.insert(0,str(ROOT/'tools'))
    from audit_naval_hull import audit
    from validate_recovery import validate
    package=ROOT/'game-mod/RAN-Carrier-Australis-2030'
    measured=audit(package,write=False)
    recorded=json.loads((package/'naval-hull-hydrostatics.json').read_text())
    assert recorded['obj_sha256']==measured['obj_sha256'],'Rebuild the hydrostatics report after model changes'
    assert recorded['hydrostatic_reference_obj_sha256']==measured['hydrostatic_reference_obj_sha256'],'Stale reference-envelope report'
    screen=json.loads((package/'waterjet-engineering-screen.json').read_text())
    assert screen['visible_obj_sha256']==measured['obj_sha256'],'Stale engineering screen'
    assert screen['source_obj_sha256']==measured['hydrostatic_reference_obj_sha256'],'Stale engineering reference geometry'
    validate(package)
    files=selected()
    manifest={'version':'0.8.5-naval-details','description':'Experimental eight-waterjet Australis; preliminary engineering screen, native conventional propulsion approximation','in_game_tested':False,'sha256_files':{p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in files}}
    (ROOT/'BUILD-MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
    archive=OUT/(LABEL+'.zip')
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in files:z.write(p,LABEL+'/'+p.relative_to(ROOT).as_posix())
        z.write(ROOT/'BUILD-MANIFEST.json',LABEL+'/BUILD-MANIFEST.json')
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name,digest in manifest['sha256_files'].items():assert sha(z.read(LABEL+'/'+name))==digest
    data=archive.read_bytes()
    bootstrap='''import sys,base64,hashlib,io,zipfile,tempfile,stat
from pathlib import Path
PAYLOAD=__PAYLOAD__
EXPECTED=__EXPECTED__
data=base64.b64decode(PAYLOAD)
if hashlib.sha256(data).hexdigest()!=EXPECTED:raise SystemExit('[STOP] Embedded package checksum failed; download this installer again.')
with tempfile.TemporaryDirectory(prefix='ran-australis-recovery-') as folder:
    folder=Path(folder)
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        if z.testzip():raise SystemExit('[STOP] Embedded package is damaged.')
        for e in z.infolist():
            p=Path(e.filename)
            if p.is_absolute() or '..' in p.parts or stat.S_ISLNK(e.external_attr>>16):raise SystemExit('[STOP] Unsafe archive entry.')
        z.extractall(folder)
    roots=list(folder.iterdir())
    if len(roots)!=1 or not roots[0].is_dir():raise SystemExit('[STOP] Invalid package layout.')
    sys.dont_write_bytecode=True
    sys.path.insert(0,str(roots[0]/'tools'))
    from install_recovery import main
    sys.exit(main())
'''.replace('__PAYLOAD__',repr(base64.b64encode(data).decode())).replace('__EXPECTED__',repr(sha(data)))
    installer=OUT/'install-ran-australis-v0.8.5-naval-details-offline.sh'
    installer.write_text('#!/usr/bin/env bash\nset -euo pipefail\ncommand -v python3 >/dev/null || { echo "[STOP] Python 3 is required."; exit 1; }\npython3 - "$@" <<\'AUSTRALIS_RECOVERY_PY\'\n'+bootstrap+'\nAUSTRALIS_RECOVERY_PY\n')
    installer.chmod(0o755)
    (OUT/'SHA256SUMS-v0.8.5-offline.txt').write_text('\n'.join(sha(p.read_bytes())+'  '+p.name for p in (archive,installer))+'\n')
    print('[OK]',installer.name,installer.stat().st_size,'bytes;',len(files),'verified files')
if __name__=='__main__':main()
