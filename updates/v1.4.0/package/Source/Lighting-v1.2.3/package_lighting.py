from pathlib import Path
import base64,hashlib,json,shutil
r=Path.cwd();p=r/'deliverable';dll=r/'build/RAN.Australis.DeckController.dll';sha=lambda b:hashlib.sha256(b).hexdigest()
code=(r/'patch-template.ps1').read_text().replace('@@DLLHASH@@',sha(dll.read_bytes())).replace('@@OBJHASH@@',sha((r/'working/payload/ships/ran_cvn_australis_2030/ran_cvn_australis_2030.obj').read_bytes()))
(r/'patch.ps1').write_text(code)
bootstrap="$ErrorActionPreference='Stop';try{$s=[IO.File]::ReadAllText($env:AUSTRALIS_LIGHT_SELF);$m=[regex]::Matches($s,'(?ms)^#__AUSTRALIS_LIGHT_PS_BEGIN__\\r?\\n(?<code>.*?)^#__AUSTRALIS_LIGHT_PS_END__\\r?$');if($m.Count -ne 1){throw 'Installer code is missing or truncated.'};& ([ScriptBlock]::Create($m[0].Groups['code'].Value))}catch{Write-Host ('[FAILED] '+$_.Exception.Message);exit 1}"
header=['@echo off','setlocal DisableDelayedExpansion','title HMAS Australis Lighting Patch v1.2.3','set "AUSTRALIS_LIGHT_SELF=%~f0"','set "AUSTRALIS_LIGHT_GAME=%~1"','set "AUSTRALIS_LIGHT_MODE=%~2"','set "AUSTRALIS_LIGHT_BACKUP=%~3"','powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -Command "'+bootstrap+'"','set "AUSTRALIS_LIGHT_RESULT=%errorlevel%"','echo.','pause','exit /b %AUSTRALIS_LIGHT_RESULT%','#__AUSTRALIS_LIGHT_PS_BEGIN__']
b=base64.b64encode(dll.read_bytes()).decode();cmd='\n'.join(header)+'\n'+code+'\n#__AUSTRALIS_LIGHT_PS_END__\n#__AUSTRALIS_LIGHT_DLL_BEGIN__\n'+'\n'.join(b[i:i+120] for i in range(0,len(b),120))+'\n#__AUSTRALIS_LIGHT_DLL_END__\n';(p/'Apply-Australis-Lighting-v1.2.3.cmd').write_bytes(cmd.replace('\r\n','\n').replace('\n','\r\n').encode())
shutil.copytree(r/'lighting-src',p/'Source/Controller',dirs_exist_ok=True);shutil.copytree(r/'tests',p/'Source/Tests',dirs_exist_ok=True)
for f in ['build_lighting.py','run_checks.py','patch-template.ps1','package_lighting.py']:shutil.copyfile(r/f,p/'Source'/f)
shutil.copyfile(r/'build/TEST-RESULTS.json',p/'TEST-RESULTS.json')
changed=[x.name for x in (r/'lighting-src').glob('*.cs') if x.read_bytes()!=(r/'baseline/Source/Component-v024/Controller'/x.name).read_bytes()]
assert sorted(changed)==['LowLightPolicy.cs','NightLights.cs']
(p/'CHANGE-REVIEW.json').write_text(json.dumps({'patch':'1.2.3-lighting','base':'Full Restore v1.2.0 (user reports working in game)','changed_controller_sources':changed,'unchanged_sources':len(list((r/'lighting-src').glob('*.cs')))-2,'old_controller_sha256':sha((r/'working/payload/RAN.Australis.DeckController.dll').read_bytes()),'new_controller_sha256':sha(dll.read_bytes()),'model_sha256':sha((r/'working/payload/ships/ran_cvn_australis_2030/ran_cvn_australis_2030.obj').read_bytes()),'compiled_target':'netstandard2.1','framework_reference':'actual official AnchorChain 1.1.0, pinned baseline hash','game_or_unity_execution':False,'geometry_aviation_weapons_sensors_modified':False,'scope':'Behaviour corrections validated by native-shaped fixtures; in-game outcome is pending'},indent=2))
print(changed)
