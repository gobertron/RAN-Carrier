from pathlib import Path
import hashlib, json, os, re, shutil, subprocess, sys, time
ROOT=Path(__file__).resolve().parents[1]; HERE=Path(__file__).resolve().parent
RUNS=HERE/'runs'; PACKAGE=ROOT/'build-package'; BASELINE=ROOT/'payload-assembly/baseline'
PWSH=ROOT/'portable-pwsh/runtime/pwsh'; VERSION='1.4.0'
CORE=b'Fixture legacy AnchorChain core (unused by Keel installer)\n'
KEEL_CORE=b'Fixture Keel core (not executable)\n'
KEEL_LIBRARY=b'Fixture AnchorChain compatibility library (not executable)\n'
KEEL_STUB=b'Fixture Keel starter (not executable)\n'
KEEL_PATCHER=b'Fixture Keel takeover patcher (not executable)\n'
KEEL_FILES={'SeaPowerKeel.dll':KEEL_CORE,'lib/AnchorChain.keel.bin':KEEL_LIBRARY,'copy-to-BepInEx-plugins/SeaPowerKeel.Stub.dll':KEEL_STUB,'SeaPowerKeel.Patcher.dll':KEEL_PATCHER}
SUPPORTED=['3b193dcb71fcbae2f8ede15484223b139948e2b9bd3ae66fc7d45db104350297','eab2297ba92c6013958bdb2cf16d5794a4731330818ce353f89dc2241e16a3bd']
RESULTS=[]
def sha(b): return hashlib.sha256(b).hexdigest()
def write(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists() or p.is_symlink():p.unlink()
 p.write_bytes(b.encode() if isinstance(b,str) else b)
def clone(s,d):shutil.copytree(s,d,copy_function=os.link)
def inv(p,skip=False):
 out={}
 for f in sorted(p.rglob('*')):
  rel=f.relative_to(p).as_posix()
  if skip and rel.startswith('_Australis-CVN-v1.3.0/'):continue
  if f.is_symlink():out[rel]='link:'+os.readlink(f)
  elif f.is_file():out[rel]=sha(f.read_bytes())
 return out
def package(d):
 clone(PACKAGE,d)
 for n in ('Cvn-Helpers.ps1','Restore-Cvn.ps1','Keel-Dependency.ps1'):write(d/'Helpers'/n,(ROOT/n).read_bytes())
 write(d/'Clean-Install-Australis.ps1',(ROOT/'Clean-Install-Australis.ps1').read_bytes())
 m=json.loads((d/'PACKAGE-MANIFEST.json').read_text());assert m['supported_game_assembly_sha256']==SUPPORTED
 assert m['version']==VERSION
 model_sha=sha((d/'payload/ships/ran_cvn_australis_2030/ran_cvn_australis_2030.obj').read_bytes())
 assert model_sha in m['audited_model_sha256'],'Current model must be an accepted upgrade source'
 m['keel']={'workshop_item_id':'3835527459','tested_version':'0.7.0','core_dll_sha256':[sha(KEEL_CORE)],'compatibility_library_sha256':[sha(KEEL_LIBRARY)],'stub_dll_sha256':[sha(KEEL_STUB)],'patcher_dll_sha256':[sha(KEEL_PATCHER)]}
 m['files']=inv(d);m['files'].pop('PACKAGE-MANIFEST.json')
 write(d/'PACKAGE-MANIFEST.json',json.dumps(m,indent=2)+'\n');return d
class F:
 def __init__(self,name):
  self.r=RUNS/name
  if self.r.exists():shutil.rmtree(self.r)
  self.r.mkdir(parents=True);self.p=package(self.r/'package')
  self.g=self.r/'SteamLibrary/steamapps/common/Sea Power';self.s=self.g/'Sea Power_Data/StreamingAssets';self.w=self.r/'SteamLibrary/steamapps/workshop/content/1286220';self.k=self.w/'3835527459';self.u=self.r/'usersettings.ini';self.logs=self.r/'logs'
  write(self.g/'Sea Power.exe',b'fixture executable');write(self.g/'Sea Power_Data/Managed/Seapower-Scripts.dll',b'unknown fixture game assembly')
  for path,typ in [('original/aircraft/stock_fixed.ini','Aircraft'),('original/aircraft/stock_helo.ini','Helicopter'),('AircraftMod/aircraft/local_plane.ini','Aircraft'),('DisabledMod/aircraft/disabled_plane.ini','Aircraft'),('user/aircraft/user_plane.ini','STOL')]:write(self.s/path,'[General]\nUnitType='+typ+'\n')
  write(self.s/'UnrelatedShip/vessels/my_destroyer.ini','[General]\nUnitType=Vessel\n')
  for path in ('UnrelatedShip/retain.txt','user/retain.txt','original/retain.txt'):write(self.s/path,'preserve '+path)
  write(self.w/'3380210757/AnchorChain.dll',CORE);write(self.w/'1234567/aircraft/workshop_plane.ini','[General]\nUnitType=VTOL\n');write(self.w/'3832163513/vessels/ran_cvn_australis_2030.ini','[General]\nUnitType=Vessel\n');write(self.w/'3832163513/cache-retained.txt','preserve Steam cache')
  for rel,data in KEEL_FILES.items():write(self.k/rel,data)
  write(self.k/'_info.ini','[Language_en]\nName=R.A.T.S. Keel fixture\n[Compatibility]\nApproximateVersion=0.9.3\n')
  self.old=self.s/'RAN-Australis-v1.2.0';clone(BASELINE/'payload',self.old)
  for n in ('ran_cvn_australis_2030.ini','ran_cvn_southern_cross_2030.ini'):
   p=self.old/'vessels'/n;t=p.read_text().replace('[AirGroup]\n\n','[AirGroup]\nstock_fixed=Default,2\n\n');assert 'stock_fixed=Default,2' in t;write(p,t)
  write(self.old/'VERSION','1.2.0\n')
  write(self.s/'Older-CVN/vessels/ran_cvn_australis_2025.ini','[General]\nUnitType=Vessel\n')
  write(self.s/'Old-Test-Only/vessels/ran_cvn_southern_cross_2030.ini','[General]\nUnitType=Vessel\n[Models]\nResourcesRoot=ran_cvn_australis_2030.obj\n')
  # Known basic-shell/stage1 native IDs must also retire, without touching other ships.
  write(self.s/'Old-Basic-Shell/vessels/ran_australis_basic_shell.ini','[General]\nUnitType=Vessel\n')
  write(self.s/'Old-Stage1/vessels/ran_australis_flightdeck_stage1.ini','[General]\nUnitType=Vessel\n')
  write(self.s/'Old-Stage1/vessels/ran_australis_stage1_c1_test.ini','[General]\nUnitType=Vessel\n')
  write(self.s/'Old-Stage1/vessels/ran_australis_stage1_c1_test_variants.ini','[Variants]\nVariant1=Test\n')
  write(self.s/'user/vessels/ran_cvn_australis_legacy.ini','[General]\nUnitType=Vessel\n');write(self.s/'user/ships/ran_cvn_australis_legacy/model.obj','legacy model');write(self.s/'user/RAN.Australis.DeckController.dll','legacy controller')
  write(self.s/'user/vessels/ran_australis_flightdeck_stage1.ini','[General]\nUnitType=Vessel\n')
  write(self.s/'user/vessels/ran_australis_stage1_c1_test.ini','[General]\nUnitType=Vessel\n')
  write(self.s/'user/animations/ran_australis_stage1_jbd.ini','[Animation]\nName=old stage1\n')
  write(self.s/'user/animations/ran_australis_stage1_lifts.ini','[Animation]\nName=old stage1 lifts\n')
  write(self.s/'user/animations/unrelated_animation.ini','preserve unrelated animation')
  clone(BASELINE/'loader',self.r/'old-loader')
  for p in (self.r/'old-loader').rglob('*'):
   if p.is_file():dest=self.g/p.relative_to(self.r/'old-loader');dest.parent.mkdir(parents=True,exist_ok=True);os.link(p,dest)
  write(self.g/'BepInEx/plugins/RAN.Australis.DeckController.dll',b'legacy controller in shared plugin path')
  write(self.g/'BepInEx/plugins/Unrelated.Plugin.dll',b'preserve unrelated plugin')
  write(self.g/'BepInEx/plugins/SeaPowerKeel.Stub.dll',KEEL_STUB)
  write(self.g/'BepInEx/patchers/SeaPowerKeel.Patcher.dll',KEEL_PATCHER)
  self.settings='[Video]\nQuality=Ultra\n\n[LoadOrder]\nNumberOfModFiles=10\nMod1Directory=RAN-Australis-v1.2.0,True,0\nMod2Directory=Older-CVN,True,0\nMod3Directory=AircraftMod,True,0\nMod4Directory=DisabledMod,False,0\nMod5Directory=WorkshopAircraft,True,1234567\nMod6Directory=OldAustralisWorkshop,True,3832163513\nMod7Directory=UnrelatedShip,True,0\nMod8Directory=Old-Basic-Shell,True,0\nMod9Directory=Old-Stage1,True,0\nMod10Directory=RATSKeel,True,3835527459\nCustomUserKey=keep-me\n\n[Sound]\nMasterVolume=0.7\n'
  write(self.u,self.settings);self.before=self.snap()
 def snap(self):return {'game':inv(self.g,True),'workshop':inv(self.w),'secondary_workshop':inv(self.r/'SecondaryLibrary') if (self.r/'SecondaryLibrary').exists() else {},'settings':self.u.read_bytes()}
 def unchanged(self):assert self.snap()==self.before,'Active game/settings/cache bytes changed'
 def run(self,mode='Install',restore=None,fault=None):
  a=[str(PWSH),'-NoLogo','-NoProfile'];script=self.p/'Clean-Install-Australis.ps1'
  if fault:
   driver=self.r/('fault-'+fault+'.ps1')
   write(driver,r'''param($Script,$Game,$Settings,$Package,$Logs,$Fault)
$global:cvnFixtureN=0;$global:cvnFixtureSent=$false;$global:cvnFixtureFault=$Fault
function global:Move-Item {
 [CmdletBinding()]param([string]$LiteralPath,[string]$Destination,[switch]$Force,[switch]$Recurse)
 $p=@{LiteralPath=$LiteralPath;Destination=$Destination;ErrorAction='Stop'}
 if($Force){$p.Force=$true};if($Recurse){$p.Recurse=$true}
 if(!$global:cvnFixtureSent -and $Destination -match '[/\\]old-[0-9]+$'){
  $global:cvnFixtureN++;if($global:cvnFixtureFault -eq 'archive-second' -and $global:cvnFixtureN -eq 2){$global:cvnFixtureSent=$true;throw 'Injected archive failure'}
 }
 Microsoft.PowerShell.Management\Move-Item @p
 if($global:cvnFixtureFault -eq 'recovery-journal' -and $Destination -match '[/\\]Held-Test-Build$'){throw 'Injected rollback interruption after hold'}
 if(!$global:cvnFixtureSent -and $global:cvnFixtureFault -in @('after-activation','recovery-journal') -and $LiteralPath -match '[/\\]Staging[/\\]' -and $Destination -match '[/\\]RAN-HMAS-Australis$'){
  $global:cvnFixtureSent=$true
  if($global:cvnFixtureFault -eq 'recovery-journal'){[IO.File]::WriteAllText((Join-Path $Destination 'partial-runtime-write.txt'),'preserve interrupted activation bytes')}
  throw 'Injected activation failure'
 }
}
& $Script -GameDirectory $Game -LoadOrderPath $Settings -PackagePath $Package -LogDirectory $Logs -Mode Install
''')
   a+=['-File',str(driver),'-Script',str(script),'-Game',str(self.g),'-Settings',str(self.u),'-Package',str(self.p),'-Logs',str(self.logs),'-Fault',fault]
  else:
   a+=['-File',str(script),'-GameDirectory',str(self.g),'-LoadOrderPath',str(self.u),'-PackagePath',str(self.p),'-LogDirectory',str(self.logs),'-Mode',mode]
   if restore:a+=['-RestoreDirectory',str(restore)]
  before=set(self.logs.glob('*.json')) if self.logs.exists() else set();p=subprocess.run(a,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=180)
  new=set(self.logs.glob('*.json'))-before;reports=[json.loads(x.read_text()) for x in sorted(new)];report=reports[-1] if reports else None
  write(self.r/(str(time.time_ns())+'-'+mode+'.log'),p.stdout)
  return p.returncode,report,p.stdout
 def success(self):
  c,r,o=self.run();assert c==0,o[-8000:];assert r['status']=='Installed' and r['loader']=='Keel' and len(r['dependency_sha256'])==64,r;return Path(r['archive'])
def test(name,fn):
 start=time.monotonic()
 try:d=fn();row={'name':name,'passed':True,'detail':d}
 except Exception as e:row={'name':name,'passed':False,'error':str(e)}
 row['seconds']=round(time.monotonic()-start,3);RESULTS.append(row);print(json.dumps(row),flush=True)
 (HERE/'TEST-RESULTS.json').write_text(json.dumps({'tests':RESULTS},indent=2)+'\n')
def success_restore():
 f=F('success-restore');archive=f.success();target=f.s/'RAN-HMAS-Australis'
 for p in (f.old,f.s/'Old-Test-Only',f.s/'Older-CVN',f.s/'Old-Basic-Shell',f.s/'Old-Stage1',f.s/'user/vessels/ran_cvn_australis_legacy.ini',f.s/'user/ships/ran_cvn_australis_legacy',f.s/'user/RAN.Australis.DeckController.dll'):assert not p.exists(),str(p)
 assert not (f.g/'BepInEx/plugins/RAN.Australis.DeckController.dll').exists()
 assert (f.g/'BepInEx/plugins/Unrelated.Plugin.dll').read_bytes()==b'preserve unrelated plugin'
 t=(target/'vessels/ran_cvn_australis_2030.ini').read_text();support=re.search(r'^AircraftSupported=(.*)$',t,re.M)[1].split(',')
 assert set(('stock_fixed','stock_helo','local_plane','workshop_plane','user_plane'))<=set(support),support
 assert 'disabled_plane' not in support;assert 'stock_fixed=Default,2' in t
 assert not (target/'vessels/ran_cvn_southern_cross_2030.ini').exists()
 assert not (target/'vessels/ran_cvn_southern_cross_2030_variants.ini').exists()
 assert len(list((target/'vessels').glob('*.ini')))==2
 variants=(target/'vessels/ran_cvn_australis_2030_variants.ini').read_text()
 names=(target/'language_en/vessel_names.ini').read_text()
 for name in ('Australis','Southern Cross','Federation','Commonwealth'):assert name in names
 for number in (91,92,93,94):assert 'hullnumber_'+str(number)+'.png' in variants
 receipt=json.loads((target/'AUSTRALIS-INSTALL.json').read_text());assert receipt['version']==VERSION and receipt['loader']=='Keel' and len(receipt['dependency_sha256'])==64 and len(receipt['aircraft_catalog_sha256'])==64
 for row in ('RAN-HMAS-Australis,True,0','Older-CVN,False,0','OldAustralisWorkshop,False,3832163513','AircraftMod,True,0','DisabledMod,False,0','UnrelatedShip,True,0','CustomUserKey=keep-me','MasterVolume=0.7','Quality=Ultra'):assert row in f.u.read_text(),row
 assert inv(f.w)==f.before['workshop']
 for rel in ('UnrelatedShip/retain.txt','user/retain.txt','original/retain.txt'):assert sha((f.s/rel).read_bytes())==f.before['game']['Sea Power_Data/StreamingAssets/'+rel]
 for _ in range(2):c,r,o=f.run('Restore',archive);assert c==0,o[-8000:];f.unchanged()
 return {'aircraft_ids':support,'exact_restore_and_repeat_restore':True}
def repeat_install():
 f=F('repeat-install');a=f.success();before=f.snap();archives=inv(f.g/'_Australis-CVN-v1.3.0');c,r,o=f.run();assert c==0,o[-8000:];assert r['status']=='AlreadyInstalled',r
 assert f.snap()==before and inv(f.g/'_Australis-CVN-v1.3.0')==archives
 assert len([p for p in f.s.iterdir() if p.is_dir() and (p/'vessels/ran_cvn_australis_2030.ini').exists()])==1
 assert 'stock_fixed=Default,2' in (f.s/'RAN-HMAS-Australis/vessels/ran_cvn_australis_2030.ini').read_text();assert inv(f.w)==f.before['workshop']
 return {'no_game_settings_or_archive_writes':True}
def repair_corrupt_file():
 f=F('repair-corrupt-file');a=f.success();target=f.s/'RAN-HMAS-Australis';texture=target/'ships/ran_cvn_australis_2030/hull.png';want=texture.read_bytes();write(texture,b'corrupt texture')
 b=f.success();assert a!=b and texture.read_bytes()==want
 assert any((b/p).is_file() and (b/p).read_bytes()==b'corrupt texture' for p in ['old-0/ships/ran_cvn_australis_2030/hull.png'])
 c,r,o=f.run();assert c==0 and r['status']=='AlreadyInstalled',o[-8000:]
def catalogue_refresh():
 f=F('catalogue-refresh');a=f.success();write(f.s/'AircraftMod/aircraft/new_carrier_plane.ini','[General]\nUnitType=Aircraft\n')
 b=f.success();assert a!=b
 t=(f.s/'RAN-HMAS-Australis/vessels/ran_cvn_australis_2030.ini').read_text();assert 'new_carrier_plane' in re.search(r'^AircraftSupported=(.*)$',t,re.M)[1].split(',')
 c,r,o=f.run();assert c==0 and r['status']=='AlreadyInstalled',o[-8000:]
def steam_library_detection():
 f=F('steam-library-detection');root=f.r/'SteamRoot';root.mkdir();write(root/'steamapps/libraryfolders.vdf','"libraryfolders"\n{\n "1"\n {\n  "path" "'+str(f.r/'SteamLibrary')+'"\n }\n}\n')
 helper=ROOT/'Cvn-Helpers.ps1';driver=f.r/'detection.ps1';write(driver,"param($Helper,$SteamRoot,$Game)\n$ErrorActionPreference='Stop'\n. $Helper\n$c=@(SteamGameCandidates @($SteamRoot));if($c.Count -ne 1 -or $c[0] -ne $Game){throw 'Secondary Steam library was not detected'}\nif((FindGame $Game) -ne $Game){throw 'Explicit path failed'}\n")
 p=subprocess.run([str(PWSH),'-NoLogo','-NoProfile','-File',str(driver),'-Helper',str(helper),'-SteamRoot',str(root),'-Game',str(f.g)],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30);assert p.returncode==0,p.stdout
 return {'libraryfolders_vdf_secondary_library':True}
def clean_install():
 f=F('clean-install')
 for rel in ('RAN-Australis-v1.2.0','Older-CVN','Old-Test-Only','Old-Basic-Shell','Old-Stage1'):
  shutil.rmtree(f.s/rel)
 for rel in ('user/vessels','user/ships'):
  shutil.rmtree(f.s/rel)
 for rel in ('user/RAN.Australis.DeckController.dll','user/animations/ran_australis_stage1_jbd.ini','user/animations/ran_australis_stage1_lifts.ini'):
  (f.s/rel).unlink()
 (f.g/'BepInEx/plugins/RAN.Australis.DeckController.dll').unlink()
 write(f.s/'original/aircraft/stock_vtol.ini','[General]\nUnitType=VTOL\n')
 for aid in ('stock_fixed','stock_helo','stock_vtol'):
  write(f.s/('original/aircraft/'+aid+'_squadrons.ini'),'[General]\nNumberOfSquadrons=0\n[Default]\nName=Fixture Squadron\n')
 write(f.s/'original/vessels/usn_cvn_nimitz_fixture.ini','[General]\nUnitType=Vessel\n[FlightDeck]\nAircraftCapacity=99\n[AI]\nRole=Carrier\n[LaunchPoint1]\nAllowedType=Plane,Helicopter,VTOL\n[AirGroup]\nstock_fixed=Default,72\nstock_helo=Default,15\nstock_vtol=Default,12\n')
 write(f.u,'[LoadOrder]\nNumberOfModFiles=5\nMod1Directory=AircraftMod,True,0\nMod2Directory=DisabledMod,False,0\nMod3Directory=WorkshopAircraft,True,1234567\nMod4Directory=UnrelatedShip,True,0\nMod5Directory=RATSKeel,True,3835527459\n')
 # Only this isolated test package permits the synthetic game hash. Production
 # retains the original audited game-assembly allowlist without additions.
 m=json.loads((f.p/'PACKAGE-MANIFEST.json').read_text());m['supported_game_assembly_sha256'].append(sha((f.g/'Sea Power_Data/Managed/Seapower-Scripts.dll').read_bytes()));write(f.p/'PACKAGE-MANIFEST.json',json.dumps(m,indent=2)+'\n')
 f.before=f.snap();a=f.success();target=f.s/'RAN-HMAS-Australis';t=(target/'vessels/ran_cvn_australis_2030.ini').read_text()
 for row in ('stock_fixed=Default,72','stock_helo=Default,15','stock_vtol=Default,12'):assert row in t,row
 assert not (target/'vessels/ran_cvn_southern_cross_2030.ini').exists()
 c,r,o=f.run();assert c==0 and r['status']=='AlreadyInstalled',o[-8000:]
 return {'synthetic_audited_game_only':True,'full_native_99_aircraft_profile':True,'production_allowlist_unmodified':True}
def check():
 f=F('check');c,r,o=f.run('Check');assert c==0 and r['status']=='Checked',o[-8000:];f.unchanged();assert not (f.g/'_Australis-CVN-v1.3.0').exists()
def reject(name,change,expected):
 f=F(name);change(f);f.before=f.snap();c,r,o=f.run();assert c!=0 and expected.casefold() in o.casefold(),o[-8000:];f.unchanged()
def rollback(fault):
 f=F('rollback-'+fault);c,r,o=f.run(fault=fault);assert c!=0 and 'Injected' in o,o[-8000:];assert '[ROLLBACK] Previous CVN installation restored.' in o,o[-8000:];f.unchanged()
def interrupted_rollback_journal():
 f=F('rollback-recovery-journal');c,r,o=f.run(fault='recovery-journal');assert c!=0 and '[RECOVERY REQUIRED]' in o,o[-8000:]
 archive=Path(r['archive']);j=json.loads((archive/'transaction.json').read_text());assert j['state']=='RecoveryRequired' and 'held_inventory' in j
 assert 'partial-runtime-write.txt' in j['held_inventory']
 assert (archive/'Held-Test-Build/partial-runtime-write.txt').read_text()=='preserve interrupted activation bytes'
 c,r,o=f.run('Restore',archive);assert c==0,o[-8000:];f.unchanged()
 return {'latest_held_inventory_preserved':True,'manual_resume_restores_exact_original':True}
def concurrent():
 f=F('concurrent-settings');a=f.success();old=f.u.read_bytes();write(f.u,old+b'\n;concurrent edit\n');before=f.snap();c,r,o=f.run('Restore',a);assert c!=0 and 'Auxiliary file changed after installation' in o,o[-8000:];assert f.snap()==before;write(f.u,old);c,r,o=f.run('Restore',a);assert c==0,o[-8000:];f.unchanged()
def modified():
 f=F('modified-build');a=f.success();write(f.s/'RAN-HMAS-Australis/new-user-file.txt','concurrent edit');before=f.snap();c,r,o=f.run('Restore',a);assert c!=0 and 'File count mismatch' in o,o[-8000:];assert f.snap()==before
def symlink(f):
 write(f.r/'outside.txt','outside bytes');(f.old/'unsafe-link.txt').symlink_to(f.r/'outside.txt')
def missing_prerequisite_preserved():
 f=F('missing-prerequisite');(f.g/'BepInEx/core/Mono.Cecil.dll').unlink();f.before=f.snap()
 c,r,o=f.run();assert c!=0 and 'KeelSetup.exe' in o,o[-8000:];f.unchanged()
 return {'missing_existing_runtime_not_replaced':True}
def ac_preloader_preserved():
 f=F('ac-preloader-preserved');p=f.g/'BepInEx/plugins/AnchorChain.Preloader.dll';write(p,b'Custom other loader, never replace')
 f.before=f.snap();a=f.success();assert p.read_bytes()==b'Custom other loader, never replace'
 c,r,o=f.run('Restore',a);assert c==0,o[-8000:];f.unchanged()
 return {'unrelated_loader_bytes_untouched':True}
def dependency_missing_repair(which):
 f=F('missing-keel-'+which);paths={'starter':'BepInEx/plugins/SeaPowerKeel.Stub.dll','patcher':'BepInEx/patchers/SeaPowerKeel.Patcher.dll'}
 for k in (('starter','patcher') if which=='both' else (which,)):(f.g/paths[k]).unlink()
 f.before=f.snap();a=f.success()
 assert (f.g/paths['starter']).read_bytes()==KEEL_STUB
 assert (f.g/paths['patcher']).read_bytes()==KEEL_PATCHER
 before=f.snap();c,r,o=f.run();assert c==0 and r['status']=='AlreadyInstalled',o[-8000:];assert f.snap()==before
 c,r,o=f.run('Restore',a);assert c==0,o[-8000:];f.unchanged()
 return {'copied_from_verified_installed_keel':True,'repeat_noop_then_exact_restore':True}
def check_missing_keel_startup():
 f=F('check-missing-keel-startup')
 for rel in ('BepInEx/plugins/SeaPowerKeel.Stub.dll','BepInEx/patchers/SeaPowerKeel.Patcher.dll'):(f.g/rel).unlink()
 f.before=f.snap();c,r,o=f.run('Check');assert c==0 and r['status']=='Checked',o[-8000:];f.unchanged()
 assert not (f.g/'_Australis-CVN-v1.3.0').exists()
 return {'dependency_repairs_planned_but_not_written_in_check_mode':True}
def dependency_repair_rollback():
 f=F('missing-keel-rollback')
 for rel in ('BepInEx/plugins/SeaPowerKeel.Stub.dll','BepInEx/patchers/SeaPowerKeel.Patcher.dll'):(f.g/rel).unlink()
 f.before=f.snap();c,r,o=f.run(fault='after-activation');assert c!=0 and 'Injected' in o,o[-8000:]
 assert '[ROLLBACK] Previous CVN installation restored.' in o,o[-8000:];f.unchanged()
 return {'new_shared_starter_and_patcher_removed_by_rollback':True}
def ac_absent():
 f=F('ac-absent');shutil.rmtree(f.w/'3380210757');f.before=f.snap();a=f.success()
 assert not (f.w/'3380210757').exists()
 assert (f.g/'BepInEx/plugins/AnchorChain.Preloader.dll').read_bytes()==(BASELINE/'loader/BepInEx/plugins/AnchorChain.Preloader.dll').read_bytes()
 c,r,o=f.run('Restore',a);assert c==0,o[-8000:];f.unchanged()
 return {'no_anchorchain_workshop_subscription_required':True}
def local_keel():
 f=F('local-keel');dest=f.s/'SeaPowerKeel';shutil.move(str(f.k),dest);f.k=dest
 write(f.u,f.settings.replace('RATSKeel,True,3835527459','SeaPowerKeel,True,0'));f.before=f.snap();a=f.success()
 assert all((dest/rel).read_bytes()==data for rel,data in KEEL_FILES.items())
 c,r,o=f.run('Restore',a);assert c==0,o[-8000:];f.unchanged()
 return {'enabled_local_keel_detected':True}
def secondary_keel():
 f=F('secondary-keel');library=f.r/'SecondaryLibrary';dest=library/'steamapps/workshop/content/1286220/3835527459';dest.parent.mkdir(parents=True)
 shutil.move(str(f.k),dest);f.k=dest
 write(f.r/'SteamLibrary/steamapps/libraryfolders.vdf','"libraryfolders"\n{\n "1"\n {\n  "path" "'+str(library)+'"\n }\n}\n')
 f.before=f.snap();a=f.success();assert all((dest/rel).read_bytes()==data for rel,data in KEEL_FILES.items())
 c,r,o=f.run('Restore',a);assert c==0,o[-8000:];f.unchanged()
 return {'keel_workshop_in_secondary_steam_library':True}
def dependency_refresh():
 f=F('dependency-refresh');a=f.success()
 config=f.g/'BepInEx/config/dev.sewerlabs.seapowerkeel.cfg';write(config,'[Loading]\nTakeOver=true\n# Updated user config\n')
 b=f.success();assert b!=a
 assert config.read_text()=='[Loading]\nTakeOver=true\n# Updated user config\n'
 before=f.snap();c,r,o=f.run();assert c==0 and r['status']=='AlreadyInstalled',o[-8000:];assert f.snap()==before
 return {'dependency_config_signature_refreshes_receipt':True}
def unrelated_takeover_key():
 f=F('unrelated-takeover-key');write(f.g/'BepInEx/config/dev.sewerlabs.seapowerkeel.cfg','[Other]\nTakeOver=false\n[Loading]\nTakeOver=true\n');f.before=f.snap();a=f.success()
 c,r,o=f.run('Restore',a);assert c==0,o[-8000:];f.unchanged()
 return {'takeover_setting_read_from_loading_section_only':True}
def upgrade_132():
 f=F('upgrade-132');shutil.rmtree(f.old);f.old=f.s/'RAN-HMAS-Australis';clone(PACKAGE/'payload',f.old)
 write(f.old/'VERSION','1.3.2\n')
 p=f.old/'vessels/ran_cvn_australis_2030.ini';s=p.read_text();s=s.replace('[AirGroup]\n\n','[AirGroup]\nstock_fixed=Default,2\n\n');write(p,s)
 write(f.u,f.settings.replace('RAN-Australis-v1.2.0,True,0','RAN-HMAS-Australis,True,0'));f.before=f.snap()
 old_model=(f.old/'ships/ran_cvn_australis_2030/ran_cvn_australis_2030.obj').read_bytes();a=f.success()
 assert (f.old/'ships/ran_cvn_australis_2030/ran_cvn_australis_2030.obj').read_bytes()==old_model
 assert (f.old/'VERSION').read_text().strip()==VERSION
 c,r,o=f.run('Restore',a);assert c==0,o[-8000:];f.unchanged()
 return {'upgrade_from132_preserves_actual_model_and_airwing':True}
RUNS.mkdir(parents=True,exist_ok=True)
test('successful_cleanup_install_and_exact_restore',success_restore)
test('repeat_install_is_noop_preserves_single_class_and_airwing',repeat_install)
test('upgrade_from132_to140_preserves_model_and_exact_restore',upgrade_132)
test('corrupt_installed_texture_is_backed_up_and_repaired',repair_corrupt_file)
test('new_enabled_aircraft_refreshes_then_repeat_is_noop',catalogue_refresh)
test('secondary_steam_library_detected_from_vdf',steam_library_detection)
test('clean_install_with_synthetic_audited_game_and_native_airwing',clean_install)
test('check_mode_has_no_active_writes',check)
test('unknown_fresh_game_refuses_before_archive',lambda:reject('unknown-fresh',lambda f:shutil.rmtree(f.old),'Fresh installation refused'))
test('malformed_settings_refuses_before_archive',lambda:reject('malformed',lambda f:write(f.u,f.settings.replace('NumberOfModFiles=10','NumberOfModFiles=11')),'Unreadable mod row 11'))
test('symlinked_old_content_refuses_before_archive',lambda:reject('symlink',symlink,'Linked mod content refused'))
test('tampered_payload_refuses_before_archive',lambda:reject('tampered-payload',lambda f:write(f.p/'payload/ships/ran_cvn_australis_2030/hull.png',b'tamper'),'Package verification failed'))
test('invalid_existing_harmony_is_preserved',lambda:reject('invalid-harmony',lambda f:write(f.g/'BepInEx/core/0Harmony.dll',b'custom dependency'),'BepInEx'))
test('unrelated_anchorchain_preloader_preserved',ac_preloader_preserved)
test('rollback_after_first_archive_move_restores_exact_state',lambda:rollback('archive-second'))
test('rollback_after_activation_restores_exact_state',lambda:rollback('after-activation'))
test('interrupted_automatic_rollback_retains_journal_and_resumes',interrupted_rollback_journal)
test('restore_refuses_concurrent_settings_change_then_recovers',concurrent)
test('restore_refuses_modified_test_build',modified)
test('mixed_ship_pack_preserved',lambda:reject('mixed-pack',lambda f:write(f.old/'vessels/unrelated_cruiser.ini','[General]\nUnitType=Vessel\n'),'Mixed ship pack preserved'))
test('mixed_workshop_pack_preserved',lambda:reject('mixed-workshop',lambda f:write(f.w/'3832163513/vessels/unrelated_cruiser.ini','[General]\nUnitType=Vessel\n'),'Mixed ship pack preserved'))
test('disabled_doorstop_config_preserved',lambda:reject('invalid-doorstop',lambda f:write(f.g/'doorstop_config.ini','[General]\nenabled=false\ntarget_assembly=BepInEx/core/BepInEx.Preloader.dll\n'),'Doorstop'))
test('missing_existing_runtime_requires_official_setup_without_writes',missing_prerequisite_preserved)
test('keel_missing_refuses_before_archive',lambda:reject('keel-missing',lambda f:shutil.rmtree(f.k),'Keel'))
test('keel_disabled_refuses_before_archive',lambda:reject('keel-disabled',lambda f:write(f.u,f.settings.replace('RATSKeel,True,3835527459','RATSKeel,False,3835527459')),'Keel'))
test('unknown_keel_core_preserved',lambda:reject('keel-core',lambda f:write(f.k/'SeaPowerKeel.dll',b'unknown Keel core'),'Keel'))
test('missing_keel_compatibility_library_preserved',lambda:reject('keel-library',lambda f:(f.k/'lib/AnchorChain.keel.bin').unlink(),'Keel'))
test('missing_keel_starter_copied_and_restored',lambda:dependency_missing_repair('starter'))
test('missing_keel_patcher_copied_and_restored',lambda:dependency_missing_repair('patcher'))
test('missing_keel_starter_and_patcher_copied_and_restored',lambda:dependency_missing_repair('both'))
test('unknown_existing_keel_starter_preserved',lambda:reject('unknown-starter',lambda f:write(f.g/'BepInEx/plugins/SeaPowerKeel.Stub.dll',b'unknown starter'),'Keel'))
test('unknown_existing_keel_patcher_preserved',lambda:reject('unknown-patcher',lambda f:write(f.g/'BepInEx/patchers/SeaPowerKeel.Patcher.dll',b'unknown patcher'),'Keel'))
test('check_mode_does_not_write_missing_keel_startup',check_missing_keel_startup)
test('rollback_removes_only_new_keel_startup_files',dependency_repair_rollback)
test('no_separate_anchorchain_core_required',ac_absent)
test('enabled_local_keel_detected',local_keel)
test('secondary_workshop_keel_detected',secondary_keel)
test('explicit_takeover_false_is_preserved_and_refused',lambda:reject('takeover-false',lambda f:write(f.g/'BepInEx/config/dev.sewerlabs.seapowerkeel.cfg','[Loading]\nTakeOver=false\n'),'TakeOver'))
test('unrelated_takeover_key_does_not_block',unrelated_takeover_key)
test('dependency_configuration_change_refreshes_receipt',dependency_refresh)
summary={'version':VERSION,'runtime':'PowerShell 7.4.13 / Linux','native_windows_tested':False,'sea_power_tested':False,'dependency_bytes':'Synthetic Keel fixture hashes only; official ABI checked separately','passed':sum(x['passed'] for x in RESULTS),'failed':sum(not x['passed'] for x in RESULTS),'test_source_sha256':sha(Path(__file__).read_bytes()),'installer_sha256':sha((ROOT/'Clean-Install-Australis.ps1').read_bytes()),'helpers_sha256':sha((ROOT/'Cvn-Helpers.ps1').read_bytes()),'restore_sha256':sha((ROOT/'Restore-Cvn.ps1').read_bytes()),'keel_dependency_sha256':sha((ROOT/'Keel-Dependency.ps1').read_bytes()),'tests':RESULTS}
(HERE/'TEST-RESULTS.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({'passed':summary['passed'],'failed':summary['failed']}),flush=True);sys.exit(bool(summary['failed']))
