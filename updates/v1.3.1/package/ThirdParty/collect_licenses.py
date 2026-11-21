"""Collect upstream license texts at exact release-source revisions.
No game, Unity, developer-reference or test assemblies are fetched here.
"""
from pathlib import Path
import concurrent.futures,hashlib,io,json,time,urllib.request,zipfile
DEST=Path(__file__).resolve().parent
SPEC=[
 ('AnchorChain-MIT.txt','AnchorChain','V1.1.0','28d225be917533fcc25e19cf8f25ac44010f8abd','MIT','https://raw.githubusercontent.com/SeaPower-Modders/AnchorChain/28d225be917533fcc25e19cf8f25ac44010f8abd/LICENSE.md'),
 ('BepInEx-MIT.txt','BepInEx','5.4.23.2','eda9ae89dd2c8bc9c7824d3658c13bcff4e5336e','MIT','https://raw.githubusercontent.com/BepInEx/BepInEx/eda9ae89dd2c8bc9c7824d3658c13bcff4e5336e/LICENSE'),
 ('BepInEx.Harmony-MIT.txt','BepInEx.Harmony and Harmony compatibility shims','BepInEx 5.4.23.2 submodule','0d24abfed64596ee88b4242b9c7e3daa849d6d28','MIT','https://raw.githubusercontent.com/BepInEx/BepInEx.Harmony/0d24abfed64596ee88b4242b9c7e3daa849d6d28/LICENSE'),
 ('UnityDoorstop-LICENSE.txt','UnityDoorstop','4.3.0','d061d7eabe9fc36140e7239955515801e2b9db12','LGPL-2.1','https://raw.githubusercontent.com/NeighTools/UnityDoorstop/d061d7eabe9fc36140e7239955515801e2b9db12/LICENSE'),
 ('HarmonyX-LICENSE.txt','HarmonyX','2.9.0','31d794f3affce55fa87c99efac7dae23a126cf52','MIT','https://raw.githubusercontent.com/BepInEx/HarmonyX/31d794f3affce55fa87c99efac7dae23a126cf52/LICENSE'),
 ('Harmony-LICENSE.txt','Harmony original code included in HarmonyX','2.9.0 upstream tree','31d794f3affce55fa87c99efac7dae23a126cf52','MIT','https://raw.githubusercontent.com/BepInEx/HarmonyX/31d794f3affce55fa87c99efac7dae23a126cf52/LICENSE.Harmony'),
 ('MonoMod-LICENSE.txt','MonoMod','22.01.29.01','68cf23127bd2394004e8a812b160a0862c95a309','MIT','https://raw.githubusercontent.com/MonoMod/MonoMod/68cf23127bd2394004e8a812b160a0862c95a309/LICENSE'),
 ('Mono.Cecil-LICENSE.txt','Mono.Cecil','0.10.4','98ec890d44643ad88d573e97be0e120435eda732','MIT','https://raw.githubusercontent.com/jbevain/cecil/98ec890d44643ad88d573e97be0e120435eda732/LICENSE.txt'),
]
def fetch(url):
 for i in range(3):
  try:return urllib.request.urlopen(url,timeout=20).read()
  except Exception:
   if i==2:raise

def one(spec):
 name,component,version,revision,lic,url=spec;b=fetch(url)
 if lic=='MIT':assert b'Permission is hereby granted' in b
 else:assert b'GNU LESSER GENERAL PUBLIC LICENSE' in b
 (DEST/name).write_bytes(b)
 return {'file':name,'component':component,'version':version,'source_revision':revision,'license':lic,'url':url,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'status':'saved'}

def main():
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as e:records=list(e.map(one,SPEC))
 wrong=DEST/'BepInEx-LGPL.txt'
 if wrong.exists():wrong.unlink()
 # Unmodified complete upstream Doorstop source, including build scripts and
 # license, accompanies the LGPL component. No executable/assembly is present.
 url='https://codeload.github.com/NeighTools/UnityDoorstop/zip/d061d7eabe9fc36140e7239955515801e2b9db12'
 b=fetch(url)
 with zipfile.ZipFile(io.BytesIO(b)) as z:
  assert z.testzip() is None
  assert not any(x.lower().endswith(('.dll','.exe','.pdb')) for x in z.namelist())
  assert any(x.endswith('/xmake.lua') for x in z.namelist())
  assert any(x.endswith('/LICENSE') for x in z.namelist())
 p=DEST/'UnityDoorstop-4.3.0-source.zip';p.write_bytes(b)
 records.append({'file':p.name,'component':'UnityDoorstop source','version':'4.3.0','source_revision':'d061d7eabe9fc36140e7239955515801e2b9db12','license':'LGPL-2.1','url':url,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'status':'saved','archive_contains_executables_or_assemblies':False,'upstream_archive_unmodified':True})
 (DEST/'LICENSE-PROVENANCE.json').write_text(json.dumps(records,indent=2)+'\n')
 print(json.dumps({'files':len(records),'status':'saved','lgpl_source_bytes':len(b)}))
if __name__=='__main__':main()
