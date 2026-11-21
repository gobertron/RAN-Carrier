#!/usr/bin/env python3
"""Finalize Australis Keel migration; carrier game assets are retained."""
import hashlib,json,re,shutil,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];PACKAGE=ROOT/'build-package';PAYLOAD=PACKAGE/'payload';VERSION='1.4.0'
MODEL_HASH='705258092c28e3b3282ce264b5ceb889ee1c8a56b8b528714c280df6f100ec60'
CONTROLLER_HASH='fdfc08fd97bdd86e89b9b5ef86e96451299e503be164783a9bc1ad7fa696f75b'
KEEL={'workshop_item_id':'3835527459','tested_version':'0.7.0','tested_versions':['0.6.0','0.7.0'],
'core_dll_sha256':['cc3902e37cd541ced9152e0cc7e9e468fa34d88ca227a668b9697d0fafebd7ba','ea03d6ff33514bed3fdd8c32f0cfa480da0b70fcf2f265bade5c48e6cdf54801'],
'compatibility_library_sha256':['e272811050698640a8936834363da91769dbc83e017637e3629c21bca6bea764'],
'stub_dll_sha256':['4a875f0842dbf836cfae5b75d5c5bb10f24ae48e724f5bd1b29dc7b4ba0dc10b','d99c3e57e650ea014b81c75d8a1c9929e10ef77c22d6913d7bb0b19a612dfb5b'],
'patcher_dll_sha256':['aabe792f0c3058f78d0eca1626875f420fe5325a5d5071db46d4874909a876bc','89b732c2f3ddbd6b091caaa6a0db1e124d7413ca874842c9ed8a020bfa0caf0e']}
KEEL['core_versions']={KEEL['core_dll_sha256'][0]:'0.7.0',KEEL['core_dll_sha256'][1]:'0.6.0'}
REFERENCES={'release':'https://github.com/struckl/SeaPowerKeel/releases/tag/v0.7.0','release_commit':'8c2bcc2f9b90bc2b3ea12c8a62247d588207dba9','release_zip_sha256':'9f0a7bd1a9cea705792fbbb2adef0b249b57beaa77e832d3ff0b616aad755e0e','v0.6.0_zip_sha256':'073fe63431572e97d012f043c70c8391a468c9d9c36289d7691725338a19456b','author_guide':'https://github.com/struckl/SeaPowerKeel/blob/v0.7.0/docs/for-mod-authors.md','installation':'https://github.com/struckl/SeaPowerKeel/blob/v0.7.0/docs/install.md','takeover':'https://github.com/struckl/SeaPowerKeel/blob/v0.7.0/docs/how-it-works.md'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def atomic(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.NamedTemporaryFile(dir=p.parent,delete=False) as f:q=Path(f.name);f.write(b)
 q.replace(p)
def copy(a,b):atomic(b,a.read_bytes())
def dump(p,o):atomic(p,(json.dumps(o,indent=2)+'\n').encode())
def inv(p,exclude=()):return {f.relative_to(p).as_posix():sha(f) for f in sorted(p.rglob('*')) if f.is_file() and '__pycache__' not in f.parts and f.relative_to(p).as_posix() not in exclude}
def tree(a,b):
 for p in sorted(a.rglob('*')):
  if p.is_file() and '__pycache__' not in p.parts:copy(p,b/p.relative_to(a))
def section_value(text,section,key,value):
 h=list(re.finditer(r'(?m)^\[([^\]\r\n]+)\][ \t]*$',text));m=[i for i,x in enumerate(h) if x[1].casefold()==section.casefold()];assert len(m)==1
 i=m[0];start=h[i].start();end=h[i+1].start() if i+1<len(h) else len(text);raw=text[start:end]
 pat=re.compile(r'(?m)^'+re.escape(key)+r'=[^\r\n]*$');assert len(pat.findall(raw))==1
 return text[:start]+pat.sub(lambda _:key+'='+value,raw)+text[end:]
def history(s):
 dest=s/'historical/v1.3.2';label=dest/'EVIDENCE-LABEL.txt'
 if not label.exists():
  old=json.loads((PACKAGE/'BUILD-PROVENANCE.json').read_text());assert old['version']=='1.3.2'
  for n in ('BUILD-PROVENANCE.json','TEST-RESULTS.json','README.txt','PACKAGE-MANIFEST.json'):
   if (PACKAGE/n).exists():copy(PACKAGE/n,dest/n)
  for p in sorted(s.iterdir()):
   if p.name=='historical':continue
   if p.is_dir():tree(p,dest/'Source-and-Checks'/p.name)
   else:copy(p,dest/'Source-and-Checks'/p.name)
  atomic(label,b'Historical Australis v1.3.2 evidence. No live visual success was confirmed. These are not v1.4.0 installer or Keel test results.\n')
  for p in list(s.iterdir()):
   if p.name=='historical':continue
   if p.is_dir():shutil.rmtree(p)
   else:p.unlink()
 return json.loads((dest/'BUILD-PROVENANCE.json').read_text()),json.loads((dest/'PACKAGE-MANIFEST.json').read_text())
def finalize():
 assert sha(PAYLOAD/'ships/ran_cvn_australis_2030/ran_cvn_australis_2030.obj')==MODEL_HASH
 assert sha(PAYLOAD/'RAN.Australis.DeckController.dll')==CONTROLLER_HASH
 installer=ROOT/'Clean-Install-Australis.ps1';helper=ROOT/'Keel-Dependency.ps1'
 assert "version='1.4.0'" in installer.read_text() and helper.exists(),'Keel installer sources not ready'
 manifest=json.loads((PACKAGE/'PACKAGE-MANIFEST.json').read_text());supported=list(manifest['supported_game_assembly_sha256']);s=PACKAGE/'Source-and-Checks'
 previous,old_manifest=history(s);assert supported==old_manifest['supported_game_assembly_sha256']
 retained=0
 for n,h in old_manifest['files'].items():
  if n.startswith('payload/ships/') or n in ('payload/vessels/ran_cvn_australis_2030.ini','payload/vessels/ran_cvn_australis_2030_variants.ini','payload/RAN.Australis.DeckController.dll'):
   assert sha(PACKAGE/n)==h,'Game asset changed during loader migration: '+n
   retained+=1
 copy(installer,PACKAGE/installer.name)
 for n in ('Cvn-Helpers.ps1','Restore-Cvn.ps1','Keel-Dependency.ps1'):copy(ROOT/n,PACKAGE/'Helpers'/n)
 loader=PACKAGE/'loader'
 if loader.exists():shutil.rmtree(loader)
 for n in ('anchorchain_workshop_item_id','anchorchain_core_dll_sha256','preloader_sha256'):manifest.pop(n,None)
 manifest['keel']=KEEL
 for p in (ROOT/'cvn-regression/run_regression.py',Path(__file__).resolve(),ROOT/'release-work/README-v1.4.0.txt'):copy(p,s/p.name)
 dump(s/'KEEL-DEPENDENCY-PROVENANCE.json',{'official_release':REFERENCES,'dependency':KEEL,'keel_binaries_bundled':False,'source_copied_from_keel':False,'controller_unchanged':True,'game_hook_compatibility_proven':False})
 abi=ROOT/'keel-audit/Keel-ABI-CHECKS.json';abi_present=abi.is_file()
 if abi_present:copy(abi,s/abi.name)
 abi_script=ROOT/'keel-audit/Test-Australis-KeelAbi.ps1'
 if abi_script.exists():copy(abi_script,s/abi_script.name)
 abi_status='Keel author documentation confirms the existing public ACPlugin/IAnchorChainMod entry; local binary ABI evidence is pending.'
 if abi_present:
  a=json.loads(abi.read_text(encoding='utf-8-sig'));assert a['controller_sha256']==CONTROLLER_HASH and a['public_acplugin'] and a['interface_binding'] and a['plugin_constructed']
  assert not a['entry_point_invoked'] and not a['game_hooks_tested']
  abi_status='Actual controller and official Keel compatibility-library ABI checks passed. TriggerEntryPoint was not invoked; this is not a live game-hook test. See Source-and-Checks/Keel-ABI-CHECKS.json.'
 reg=ROOT/'cvn-regression/TEST-RESULTS.json';r=json.loads(reg.read_text()) if reg.exists() else None
 source_hashes={'installer_sha256':sha(installer),'helpers_sha256':sha(ROOT/'Cvn-Helpers.ps1'),'restore_sha256':sha(ROOT/'Restore-Cvn.ps1'),'test_source_sha256':sha(ROOT/'cvn-regression/run_regression.py'),'keel_dependency_sha256':sha(helper)}
 current=bool(r and all(r.get(k)==v for k,v in source_hashes.items()))
 if r:copy(reg,PACKAGE/'TEST-RESULTS.json');copy(reg,s/'INSTALLER-REGRESSION-RESULTS.json')
 status=(f"{r['passed']} passed, {r['failed']} failed; {r['runtime']}." if current else 'Current v1.4.0 installer and Keel dependency regression checks are pending; included earlier results are historical.')
 dump(s/'EVIDENCE-STATUS.json',{'release_version':VERSION,'installer_regression_matches_current_sources':current,'installer_source_sha256':source_hashes,'status':status,'keel_abi_evidence_present':abi_present,'live_game_tested':False})
 readme=(ROOT/'release-work/README-v1.4.0.txt').read_text().replace('{{REGRESSION_STATUS}}',status).replace('{{ABI_STATUS}}',abi_status)
 atomic(PACKAGE/'README.txt',readme.encode());atomic(PAYLOAD/'README.txt',readme.encode());atomic(PAYLOAD/'VERSION',(VERSION+'\n').encode())
 for path,key,section in ((PAYLOAD/'_info.ini','Description','Language_en'),(PAYLOAD/'language_en/vessel_names.ini','DefaultDescription','ran_cvn_australis_2030')):
  t=path.read_text().replace('; Requires the original controller and verified AnchorChain dependencies.','; Existing controller loaded through the official R.A.T.S. Keel compatibility library.')
  m=re.search(r'(?m)^'+key+r'=([^\r\n]*)$',t);assert m
  value=m[1].replace('Requires AnchorChain and its current official preloader.','Requires R.A.T.S. Keel (Workshop 3835527459), enabled with its starter and takeover patcher. The separate AnchorChain item is not required.')
  value=re.sub(r'\\r\\n\\r\\nv1\.(?:3\.[12]|4\.0):.*$','',value)
  value+=r'\r\n\r\nv1.4.0: official R.A.T.S. Keel loader migration. Model, window UV repair, aircraft and controller retained. Keel RUNNING alone does not prove active game hooks; check the carrier log and test mechanisms in game.'
  t=section_value(t,section,key,value)
  if path.name=='_info.ini':t=section_value(t,'Language_en','Name','RAN / HMAS Australis v1.4.0 - Keel')
  assert not re.search(r'(?im)^\s*StartEarly\s*=\s*true',t)
  atomic(path,t.encode())
 testplan='''AUSTRALIS v1.4.0 / KEEL IN-GAME RETEST
1. Enable official R.A.T.S. Keel, close the game and run Install-Australis.cmd.
2. Restart Sea Power; follow a second-restart request from Keel if displayed.
3. Ctrl+Shift+K: verify RAN Australis Enclosed Deck starts once. Its unchanged legacy controller label can show 0.10.24 while this carrier package is 1.4.0. Save Keel's report/log and takeover report.
4. Check fresh RAN-Australis-DeckController.log for Installed audited route/lift hooks and Bound; NOT ACTIVE means hooks failed even if Keel says RUNNING.
5. Create a new 2030 mission. Verify one class, four variants, intended aircraft selection, fixed-wing launch/recovery, VTOL/helicopters, lifts and catapults.
6. Test CIWS6, ICCS, weapon bays, day/night/storm lights and the outstanding black-window-strip visual repair.
No live game success is inferred from package, ABI or installer checks.
'''
 atomic(PAYLOAD/'TESTPLAN.txt',testplan.encode())
 f=PAYLOAD/'CHANGELOG.txt';old=re.sub(r'(?s)^v1\.4\.0 - .*?\n\n','',f.read_text(),count=1)
 atomic(f,('v1.4.0 - R.A.T.S. Keel loader migration\nRemoves the standalone AnchorChain item/preloader requirement and bundled\nloader files. Uses official enabled Keel and its compatibility library.\nMissing verified starter/patcher files can be copied transactionally from\nthat installed Keel copy; other loader files are preserved. Retains the exact\ncarrier model and controller, class/IDs, aviation and window repair.\nKeel loader compatibility is separate from live game-hook compatibility.\n\n'+old).encode())
 provenance={'schema':1,'version':VERSION,'kind':'Australis official Keel loader migration','repository':'gobertron/RAN-Carrier','canonical_ship_id':'ran_cvn_australis_2030','previous_release':'1.3.2','model_sha256_before':MODEL_HASH,'model_sha256_after':MODEL_HASH,'retained_asset_and_gameplay_file_count':retained,'model_assets_and_gameplay_vessels_unchanged':True,'controller_sha256':CONTROLLER_HASH,'controller_unchanged':True,'keel_dependency':KEEL,'keel_primary_sources':REFERENCES,'keel_binary_or_code_redistributed':False,'standalone_anchorchain_item_required':False,'bundled_bepinex_loader':False,'supported_game_assembly_sha256':supported,'game_build_checked':'Original allowlist and prior user logs; no new live runtime','last_user_confirmed_loaded_version':previous['last_user_confirmed_loaded_version'],'last_user_confirmation':previous['last_user_confirmation'],'previous_window_repair_visual_result_confirmed':False,'keel_abi_evidence_present':abi_present,'installer_regression_matches_current_sources':current,'installer_regression_summary':status,'native_windows_tested':False,'live_game_tested':False,'historical_evidence':'Source-and-Checks/historical/v1.3.2'}
 dump(PACKAGE/'BUILD-PROVENANCE.json',provenance)
 dump(PAYLOAD/'RUNTIME-FILES.json',inv(PAYLOAD,('RUNTIME-FILES.json',)))
 manifest['version']=VERSION;manifest['live_game_tested']=False;manifest['runtime_assembly_profile']='Existing audited carrier upgrade or retained audited game-assembly allowlist; Keel dependency verified separately'
 assert supported==manifest['supported_game_assembly_sha256']
 manifest['files']=inv(PACKAGE,('PACKAGE-MANIFEST.json',));dump(PACKAGE/'PACKAGE-MANIFEST.json',manifest)
 assert manifest['files']==inv(PACKAGE,('PACKAGE-MANIFEST.json',))
 assert not any(n.startswith('loader/') or Path(n).name.casefold().startswith('seapowerkeel') for n in manifest['files'])
 return {'version':VERSION,'package_files':len(manifest['files']),'model_sha256':MODEL_HASH,'controller_sha256':CONTROLLER_HASH,'keel_binary_bundled':False,'current_regressions_verified':current,'regression_summary':status}
if __name__=='__main__':print(json.dumps(finalize(),indent=2))
