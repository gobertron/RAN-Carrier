#!/usr/bin/env python3
"""Exercise replacement, backups, restore, removals and failure rollback."""
from pathlib import Path
import tempfile,sys,shutil,json,hashlib
from unittest.mock import patch
import install_recovery as installer
from validate_recovery import ini
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'game-mod'/installer.MOD
REFS=Path(sys.argv[1])

def fixture(root):
    game=root/'steamapps/common/Sea Power';assets=game/'Sea Power_Data/StreamingAssets';stock=assets/'original'
    (stock/'vessels').mkdir(parents=True);(stock/'vessels/usn_cvn_nimitz.ini').write_text('[General]\n')
    (stock/'systems').mkdir();(stock/'ammunition').mkdir()
    c=ini(SOURCE/'vessels/ran_cvn_australis_2030.ini')
    for family,file in (('SensorSystem','sensors.ini'),('WeaponSystem','weapons.ini')):
        profiles=set(c[s]['SystemName'] for s in c.sections() if s.startswith(family) and s[len(family):].isdigit() and c[s]['Type']!='Visual')
        (stock/'systems'/file).write_text('\n'.join('['+s+']\nFixture=True' for s in profiles))
    import re
    for section in c.sections():
        for key,value in c[section].items():
            if re.fullmatch(r'Ammunition\d*|Countermeasure',key):(stock/'ammunition'/f'{value}.ini').write_text('[Fixture]\n')
    (game/'Sea Power_Data/Managed').mkdir();shutil.copy2(REFS/'Seapower-Scripts.dll',game/'Sea Power_Data/Managed/Seapower-Scripts.dll')
    (game/'BepInEx/plugins').mkdir(parents=True);(game/'BepInEx/core').mkdir()
    shutil.copy2(REFS/'dev/AnchorChain.Preloader.dll',game/'BepInEx/plugins/AnchorChain.Preloader.dll')
    shutil.copy2(REFS/'preloader/BepInEx/core/0Harmony.dll',game/'BepInEx/core/0Harmony.dll')
    (assets/'framework').mkdir();shutil.copy2(REFS/'dev/AnchorChain.dll',assets/'framework/AnchorChain.dll')
    for name in ('RADF','User Data'):
        (assets/name).mkdir();(assets/name/'sentinel').write_text(name)
    return game,assets,root/'backups'

def main():
    with tempfile.TemporaryDirectory(prefix='ran-install-tests-') as temp:
        root=Path(temp);game,assets,backups=fixture(root);target=assets/installer.MOD;legacy=assets/installer.DLL
        before={name:installer.fingerprint(assets/name) for name in ('original','RADF','User Data','framework')}
        loader=installer.fingerprint(game/'BepInEx')
        installer.install(game,backups,check=True);assert not target.exists()
        installer.install(game,backups);assert installer.fingerprint(target)==installer.fingerprint(SOURCE)
        installer.install(game,backups);assert not backups.exists(),'Idempotent install should not create backups'
        # Upgrade a genuinely different mod, including withdrawal of old loose DLL.
        (target/'old-build-marker').write_text('previous carrier');legacy.write_bytes(b'previous controller')
        old=installer.fingerprint(target);installer.install(game,backups)
        saved=next(backups.iterdir());assert installer.fingerprint(saved/'mod')==old and not legacy.exists()
        installer.install(game,backups,restore=saved);assert installer.fingerprint(target)==old and legacy.read_bytes()==b'previous controller'
        # A publication failure must restore both paths and their original bytes.
        rename=Path.rename
        def fail(self,dest):
            if self.name=='new' and Path(dest)==target:raise OSError('Injected publication failure')
            return rename(self,dest)
        with patch.object(Path,'rename',fail):
            try:installer.switch(assets,SOURCE)
            except OSError:pass
            else:raise AssertionError('Failure injection did not trigger')
        assert installer.fingerprint(target)==old and legacy.read_bytes()==b'previous controller'
        # Incompatible game DLL must leave the installed version untouched.
        managed=game/'Sea Power_Data/Managed/Seapower-Scripts.dll';data=managed.read_bytes();managed.write_bytes(b'wrong version')
        try:installer.install(game,backups)
        except ValueError as e:assert 'Game scripts version' in str(e)
        else:raise AssertionError('Unsupported game version accepted')
        assert installer.fingerprint(target)==old;managed.write_bytes(data)
        # A damaged backup must be rejected before withdrawing the current mod.
        (saved/'mod/old-build-marker').write_text('tampered')
        try:installer.install(game,backups,restore=saved)
        except ValueError:pass
        else:raise AssertionError('Damaged backup accepted')
        assert installer.fingerprint(target)==old
        installer.install(game,backups,remove=True);assert not target.exists() and not legacy.exists()
        installer.install(game,backups,remove=True)
        for name,hashes in before.items():assert installer.fingerprint(assets/name)==hashes,name
        assert installer.fingerprint(game/'BepInEx')==loader
        # Resolve the historical preloader-path bug in a plugins-only fixture.
        assert not (game/'BepInEx/patchers').exists()
        print('[PASS] Check/fresh/idempotent/upgrade/legacy migration/restore/removal, bad DLL, corrupt backup, injected rollback; protected folders unchanged')
if __name__=='__main__':main()
