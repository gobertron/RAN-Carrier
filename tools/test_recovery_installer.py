#!/usr/bin/env python3
"""Exercise replacement, backups, restore, removals and failure rollback."""
from pathlib import Path
import tempfile,sys,shutil,json,hashlib,configparser,re,io,contextlib
from unittest.mock import patch
import install_recovery as installer
import validate_recovery as validator
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
        # Stock catalogues contain decorative section headers more than once.
        # Reproduce the user's sensors.ini failure exactly at line 624. These
        # files test reference discovery, not real sensor/weapon behaviour.
        divider='[---------- Surface ships ----------]'
        lines=[divider,'; Stock catalogue separator, not a system profile.']
        for profile in sorted(profiles):lines.extend(('['+profile+']','Fixture=True'))
        assert len(lines)<623,'Fixture catalogue unexpectedly exceeds regression line'
        lines.extend('; Catalogue padding' for _ in range(623-len(lines)))
        lines.extend((divider,'RepeatedKey=first','RepeatedKey=second',
                      '[fixture_duplicate_keys]','Fixture=first','Fixture=second',
                      '; [fixture_commented_out_profile]','# [fixture_hash_commented_profile]'))
        (stock/'systems'/file).write_text('\n'.join(lines)+'\n')
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
        stock=assets/'original'
        for file in ('sensors.ini','weapons.ini'):
            catalogue=stock/'systems'/file
            try:ini(catalogue)
            except configparser.DuplicateSectionError as e:
                assert e.section=='---------- Surface ships ----------' and e.lineno==624
            else:raise AssertionError('Stock fixture no longer reproduces the strict-parser failure')
            sections=validator.stock_section_names(catalogue)
            assert 'fixture_duplicate_keys' in sections
            assert 'fixture_commented_out_profile' not in sections
            assert 'fixture_hash_commented_profile' not in sections
        # Tolerance is confined to stock section-name discovery. Authored mod
        # INIs must still reject ambiguous repeated sections and repeated keys.
        own=root/'duplicate-owned.ini'
        for text,error in (('[General]\nVersion=1\n[General]\nVersion=2\n',configparser.DuplicateSectionError),
                           ('[General]\nVersion=1\nVersion=2\n',configparser.DuplicateOptionError)):
            own.write_text(text)
            try:ini(own)
            except error:pass
            else:raise AssertionError('Authored mod INI duplicate was accepted')
        installer.install(game,backups,check=True);assert not target.exists()
        installer.install(game,backups);assert installer.fingerprint(target)==installer.fingerprint(SOURCE)
        installer.install(game,backups);assert not backups.exists(),'Idempotent install should not create backups'
        duplicate=assets/'Older-Australis-Copy/vessels'
        duplicate.mkdir(parents=True)
        marker=duplicate/(validator.IDS[0]+'.ini');marker.write_text('[General]\n')
        workshop_copy=game.parents[1]/'workshop/content/1286220/12345/vessels'
        workshop_copy.mkdir(parents=True);workshop_marker=workshop_copy/(validator.IDS[0]+'.ini')
        workshop_marker.write_text('[General]\n')
        out=io.StringIO()
        with contextlib.redirect_stdout(out):installer.install(game,backups)
        assert '[VERIFIED] RAN Australis Fleet v0.8.5 Naval Details' in out.getvalue()
        assert '[OTHER COPY] '+str(duplicate.parent) in out.getvalue()
        assert '[OTHER COPY] '+str(workshop_copy.parent) in out.getvalue()
        assert marker.read_text()=='[General]\n' and workshop_marker.read_text()=='[General]\n'
        assert not backups.exists(),'Read-only duplicate detection should not create backups'
        # A diagnostic failure in an unrelated mod must not report a failed
        # installation after the canonical package has already been verified.
        def unreadable_walk(root,**kwargs):
            kwargs['onerror'](PermissionError('Fixture unreadable unrelated mod'))
            return iter(())
        out=io.StringIO()
        with patch.object(installer.os,'walk',unreadable_walk),contextlib.redirect_stdout(out):
            installer.report_installation(target,assets,game.parents[1]/'workshop/content/1286220')
        assert '[NOTE] Other-copy scan was incomplete' in out.getvalue()
        assert '[VERIFIED]' in out.getvalue() and marker.read_text()=='[General]\n'
        shutil.rmtree(duplicate.parent);shutil.rmtree(workshop_copy.parent)
        # Upgrade a genuinely different mod, including withdrawal of old loose DLL.
        (target/'old-build-marker').write_text('previous carrier');legacy.write_bytes(b'previous controller')
        old=installer.fingerprint(target);installer.install(game,backups)
        saved=next(backups.iterdir());assert installer.fingerprint(saved/'mod')==old and not legacy.exists()
        installer.install(game,backups,restore=saved);assert installer.fingerprint(target)==old and legacy.read_bytes()==b'previous controller'
        # Repeated stock separators must not weaken genuine dependency checks.
        # Both failures happen before backup/staging/replacement, retaining the
        # installed older mod and its loose controller byte for byte.
        def dependency_failure(expected):
            previous=installer.fingerprint(target);controller=legacy.read_bytes()
            backup_paths={p.name for p in backups.iterdir()}
            try:installer.install(game,backups)
            except ValueError as e:assert expected in str(e),(expected,str(e))
            else:raise AssertionError('Missing stock dependency was accepted')
            assert installer.fingerprint(target)==previous and legacy.read_bytes()==controller
            assert {p.name for p in backups.iterdir()}==backup_paths,'Precheck failure created a backup'
        c=ini(SOURCE/'vessels/ran_cvn_australis_2030.ini')
        local=set(ini(SOURCE/'systems/sensors.ini').sections())
        required={c[s]['SystemName'] for s in c.sections() if re.fullmatch(r'SensorSystem\d+',s) and c[s]['Type']!='Visual'}
        stock_only=sorted(required-local);assert stock_only,'Missing-stock regression needs a stock-only sensor'
        sensor=stock_only[0];catalogue=stock/'systems/sensors.ini';original=catalogue.read_bytes()
        catalogue.write_bytes(original.replace(('['+sensor+']').encode(),('['+sensor+'_missing]').encode()))
        try:dependency_failure('Missing stock system '+sensor)
        finally:catalogue.write_bytes(original)
        ammo=next(iter(sorted((stock/'ammunition').glob('*.ini'))));withdrawn=root/'withdrawn-stock-round.ini'
        ammo.rename(withdrawn)
        try:dependency_failure('Missing stock round '+ammo.stem)
        finally:withdrawn.rename(ammo)
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
        print('[PASS] Duplicate stock divider at line624 and duplicate stock keys; commented headers excluded; authored INIs remain strict')
        print('[PASS] Check/fresh/idempotent/upgrade/legacy migration/restore/removal, missing stock system/round, bad DLL, corrupt backup, injected rollback; protected folders unchanged')
if __name__=='__main__':main()
