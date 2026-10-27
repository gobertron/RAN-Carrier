#!/usr/bin/env python3
"""Transactional installer for this independent carrier; Python stdlib only."""
from pathlib import Path
from datetime import datetime
import argparse,contextlib,hashlib,json,os,shutil,sys,tempfile
from validate_recovery import validate,IDS,ini
ROOT=Path(__file__).resolve().parents[1]
MOD='RAN-Carrier-Australis-2030'
DLL='RAN.Australis.DeckController.dll'
AUDITED='eab2297ba92c6013958bdb2cf16d5794a4731330818ce353f89dc2241e16a3bd'
VERSION='0.8.5-naval-details'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def progress(n,msg):print(f'[{n:3d}%] {msg}',flush=True)
def report_installation(target,assets,workshop_root):
    release=json.loads((target/'recovery-release.json').read_text())
    if release['version']!=VERSION:raise ValueError('Installed release version does not match this installer')
    print('[VERIFIED] '+ini(target/'_info.ini')['Language_en']['Name'])
    print('[VERIFIED] Four carriers; eight waterjets; Standard 20 kn / Full 30 kn; lift-wall lighting')
    fittings=json.loads((target/'naval-fittings.json').read_text())
    print('[VERIFIED] Enlarged numbers 91–94; '+str(fittings['windows'])+' framed windows; '+str(fittings['doors'])+' naval doors; surface alignment verified')
    # Diagnose competing copies; never remove another mod or Workshop content.
    duplicates=set();scan_errors=[]
    wanted={ship_id+'.ini' for ship_id in IDS}
    for root in (assets,workshop_root):
        if not root.is_dir():continue
        # This optional diagnostic must not turn a completed installation into
        # a failure because another mod has unreadable paths or linked folders.
        # Walk each tree once, do not follow links, and skip our verified copy.
        try:
            for directory,children,files in os.walk(root,followlinks=False,onerror=scan_errors.append):
                directory=Path(directory)
                if directory==target:children[:]=[];continue
                if directory.name=='vessels' and wanted.intersection(files):
                    duplicates.add(str(directory.parent))
        except OSError as error:scan_errors.append(error)
    for folder in sorted(duplicates):print('[OTHER COPY] '+folder)
    if duplicates:print('[ACTION] Disable older Australis copies in the game mod menu; do not delete Workshop or stock files.')
    if scan_errors:print('[NOTE] Other-copy scan was incomplete because some folders could not be read; the installed package is verified.')
    print('[NEXT] Enable AnchorChain and RAN Australis Fleet v0.8.5 Naval Details. Restart Sea Power.')
    print('[NEXT] Use a fresh ship in a new blank mission; existing missions may retain old models and routes.')
def fingerprint(root):
    if root.is_symlink() or not root.is_dir():raise ValueError('Expected a real folder: '+str(root))
    out={}
    for p in root.rglob('*'):
        if p.is_symlink():raise ValueError('Refusing a symbolic link in '+str(p))
        if p.is_file():out[p.relative_to(root).as_posix()]=sha(p)
        elif not p.is_dir():raise ValueError('Refusing a special file: '+str(p))
    return out
def verify_manifest(root):
    m=json.loads((root/'BUILD-MANIFEST.json').read_text())
    for name,digest in m['sha256_files'].items():
        p=Path(name)
        if p.is_absolute() or '..' in p.parts or sha(root/p)!=digest:raise ValueError('Package checksum failure: '+name)
    progress(15,'Verified '+str(len(m['sha256_files']))+' package files')
def running():
    for p in Path('/proc').glob('[0-9]*/comm'):
        try:n=p.read_text().strip().lower()
        except OSError:continue
        if n in ('sea power.exe','seapower.exe','sea power','seapower'):raise ValueError('Close Sea Power before installing or restoring.')
def snapshot(target,legacy,backups):
    if backups.is_symlink():raise ValueError('Refusing a linked backup folder')
    backups.mkdir(parents=True,exist_ok=True)
    folder=backups/('v'+VERSION+'-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f'));folder.mkdir()
    files={};had_mod=target.exists();had_legacy=legacy.exists()
    if had_mod:
        before=fingerprint(target);shutil.copytree(target,folder/'mod')
        if fingerprint(folder/'mod')!=before:raise ValueError('Mod backup verification failed')
        files.update({'mod/'+k:v for k,v in before.items()})
    if had_legacy:
        if legacy.is_symlink() or not legacy.is_file():raise ValueError('Refusing a linked or invalid legacy controller')
        shutil.copy2(legacy,folder/'legacy.dll');files['legacy.dll']=sha(legacy)
    metadata={'schema':1,'mod_name':MOD,'had_mod':had_mod,'had_legacy_controller':had_legacy,'sha256_files':files}
    (folder/'backup.json').write_text(json.dumps(metadata,indent=2)+'\n')
    verify_backup(folder)
    print('[BACKUP] '+str(folder))
    return folder
def verify_backup(folder):
    if folder.is_symlink():raise ValueError('Refusing a linked backup')
    m=json.loads((folder/'backup.json').read_text())
    if m.get('schema')!=1 or m.get('mod_name')!=MOD:raise ValueError('This is not an Australis recovery-installer backup')
    for name,digest in m['sha256_files'].items():
        p=Path(name)
        if p.is_absolute() or '..' in p.parts or (folder/p).is_symlink() or sha(folder/p)!=digest:raise ValueError('Backup verification failed: '+name)
    if m['had_mod'] and fingerprint(folder/'mod')!={k[4:]:v for k,v in m['sha256_files'].items() if k.startswith('mod/')}:raise ValueError('Backup contains unexpected mod files')
    return m
def switch(assets,source=None,legacy_source=None,remove=False):
    """Stage first; retain previous paths until both changes verify."""
    target=assets/MOD;legacy=assets/DLL
    if target.is_symlink() or legacy.is_symlink():raise ValueError('Refusing a linked mod or legacy DLL')
    with tempfile.TemporaryDirectory(prefix='.ran-recovery-',dir=assets) as temp:
        temp=Path(temp);staged=temp/'new';old=temp/'previous';old_legacy=temp/'previous.dll'
        if source is not None:
            shutil.copytree(source,staged)
            if fingerprint(source)!=fingerprint(staged):raise ValueError('Staged file verification failed')
        if legacy_source is not None:shutil.copy2(legacy_source,temp/'new.dll')
        moved_mod=moved_legacy=published_mod=published_legacy=False
        try:
            if target.exists():target.rename(old);moved_mod=True
            if legacy.exists():legacy.rename(old_legacy);moved_legacy=True
            if source is not None:staged.rename(target);published_mod=True
            if legacy_source is not None:(temp/'new.dll').rename(legacy);published_legacy=True
            if source is not None and fingerprint(target)!=fingerprint(source):raise ValueError('Installed mod verification failed')
            if legacy_source is not None and sha(legacy)!=sha(legacy_source):raise ValueError('Restored legacy DLL verification failed')
        except BaseException:
            if published_mod and target.exists():shutil.rmtree(target)
            if published_legacy:legacy.unlink(missing_ok=True)
            if moved_mod:old.rename(target)
            if moved_legacy:old_legacy.rename(legacy)
            print('[ROLLBACK] Previous mod and controller restored after failure.')
            raise
def install(game,backups,check=False,remove=False,restore=None):
    game=game.expanduser().resolve();assets=game/'Sea Power_Data/StreamingAssets'
    if not assets.is_dir() or assets.is_symlink():raise ValueError('Sea Power StreamingAssets folder not found: '+str(assets))
    if backups.resolve().is_relative_to(game):raise ValueError('Backups must be outside the game folder')
    target=assets/MOD;legacy=assets/DLL
    if target.is_symlink() or legacy.is_symlink():raise ValueError('Refusing a linked mod/controller target')
    running();progress(5,'Game location: '+str(game))
    if remove:
        if not target.exists() and not legacy.exists():progress(100,'Our carrier/controller are already absent');return
        snapshot(target,legacy,backups);switch(assets,remove=True);progress(100,'Carrier withdrawn; verified backup retained');return
    if restore is not None:
        restore=restore.expanduser().resolve();m=verify_backup(restore)
        snapshot(target,legacy,backups)
        switch(assets,restore/'mod' if m['had_mod'] else None,restore/'legacy.dll' if m['had_legacy_controller'] else None)
        progress(100,'Verified previous installation restored');return
    verify_manifest(ROOT)
    managed=game/'Sea Power_Data/Managed/Seapower-Scripts.dll'
    if not managed.is_file() or sha(managed)!=AUDITED:raise ValueError('Game scripts version differs from your supplied, checked DLL. Nothing installed. Send this log and your current game version.')
    progress(30,'Supported game scripts confirmed')
    preloaders=list((game/'BepInEx/plugins').rglob('AnchorChain.Preloader.dll'))+list((game/'BepInEx/patchers').rglob('AnchorChain.Preloader.dll'))
    if not any(p.is_file() and p.stat().st_size for p in preloaders) or not (game/'BepInEx/core/0Harmony.dll').is_file():raise ValueError('Working AnchorChain preloader/Harmony not found. Restore the official ACPreloader package, then rerun. Expected preloader location: BepInEx/plugins/AnchorChain.Preloader.dll')
    workshop_root=game.parents[1]/'workshop/content/1286220'
    workshop=workshop_root/'3380210757'
    if not any(p.is_file() for root in (workshop,assets) for p in root.rglob('AnchorChain.dll')):raise ValueError('AnchorChain framework not found. Enable your Workshop subscription 3380210757 before installing.')
    progress(40,'AnchorChain preloader, framework and Harmony found')
    package=ROOT/'game-mod'/MOD
    validate(package,assets/'original')
    progress(60,'Fleet, repair teams, native animations and stock references verified')
    if check:progress(100,'Checks passed; no game files changed');return
    if target.exists() and fingerprint(target)==fingerprint(package) and not legacy.exists():
        report_installation(target,assets,workshop_root)
        progress(100,'Australis v'+VERSION+' is already installed; installed package hashes verified');return
    if target.exists() or legacy.exists():snapshot(target,legacy,backups)
    progress(75,'Staging carrier and controller together')
    switch(assets,package)
    report_installation(target,assets,workshop_root)
    print('[LIMIT] Waterjet prototype; native propulsion, steering, flight, lift, night and combat trials remain pending.')
    progress(100,'Australis v'+VERSION+' installed; installed package hashes verified');print('[INSTALLED] '+str(target))
class Tee:
    def __init__(self,*streams):self.streams=streams
    def write(self,s):
        for f in self.streams:f.write(s);f.flush()
    def flush(self):
        for f in self.streams:f.flush()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--game',type=Path,default=Path.home()/'.local/share/Steam/steamapps/common/Sea Power');p.add_argument('--backups',type=Path,default=Path.home()/'Downloads/RAN-Carrier-Australis-2030-backups');p.add_argument('--log-dir',type=Path,default=Path.home()/'Downloads')
    group=p.add_mutually_exclusive_group();group.add_argument('--check',action='store_true');group.add_argument('--remove',action='store_true');group.add_argument('--restore',type=Path)
    a=p.parse_args();a.log_dir.mkdir(parents=True,exist_ok=True);logpath=a.log_dir/('RAN-Australis-recovery-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f')+'.log')
    with logpath.open('w') as log,contextlib.redirect_stdout(Tee(sys.stdout,log)),contextlib.redirect_stderr(Tee(sys.stderr,log)):
        try:progress(0,'Australis v'+VERSION+' — reconstructed fleet installer');install(a.game,a.backups,a.check,a.remove,a.restore);return 0
        except Exception as e:print('[STOP] '+str(e));print('[HELP] Copy this log into chat for troubleshooting.');return 1
        finally:print('[LOG] '+str(logpath))
if __name__=='__main__':sys.exit(main())
