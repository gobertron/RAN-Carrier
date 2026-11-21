from build_lighting import *
import shutil
sources=sorted((root/('Controller' if (root/'Controller').exists() else 'lighting-src')).glob('*.cs'))
fixture_root=root/'Tests' if (root/'Tests').exists() else root/'baseline/Source/Component-v024/Controller'
for p in (anchor,harmony):shutil.copy2(p,out/p.name)
reports={}
for name,fixture in [('LightingTests',(root/'Tests/LightingTests.cs' if (root/'Tests').exists() else root/'tests/LightingTests.cs')),('DeckStatusTests',fixture_root/'DeckStatusTests.cs.txt'),('Ciws6PolicyTests',fixture_root/'Ciws6PolicyTests.cs.txt'),('Ciws6AircraftClearanceTests',fixture_root/'Ciws6AircraftClearanceTests.cs.txt'),('Ciws6ColliderSyncTests',fixture_root/'Ciws6ColliderSyncTests.cs.txt'),('Ciws6IntegrationTests',fixture_root/'Ciws6IntegrationTests.cs.txt')]:
 exe=compile(name+'.dll',sources+[fixture],kind='exe',core=True);exe.with_suffix('.runtimeconfig.json').write_text(json.dumps({'runtimeOptions':{'tfm':'net8.0','framework':{'name':'Microsoft.NETCore.App','version':'8.0.33'}}}));r=subprocess.run([str(sdk/'dotnet'),str(exe)],capture_output=True,text=True);print(name,r.stdout,r.stderr);r.check_returncode();reports[name]=r.stdout.strip()
(out/'TEST-RESULTS.json').write_text(json.dumps(reports,indent=2))
