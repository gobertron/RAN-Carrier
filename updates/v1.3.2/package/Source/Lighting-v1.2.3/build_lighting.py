from pathlib import Path
import hashlib,json,subprocess
root=Path.cwd();sdk=root/'toolchain';ref=sdk/'packs/NETStandard.Library.Ref/2.1.0/ref/netstandard2.1';anchor=next((sdk/'acdev').rglob('AnchorChain.dll'));harmony=sdk/'ACPreloader/BepInEx/core/0Harmony.dll'
if not harmony.exists():harmony=root/'working/loader/BepInEx/core/0Harmony.dll'
assert hashlib.sha256(anchor.read_bytes()).hexdigest()=='e272811050698640a8936834363da91769dbc83e017637e3629c21bca6bea764'
out=root/'build';out.mkdir(exist_ok=True)
def compile(name,sources,kind='library',core=False):
 refs=(sdk/'packs/Microsoft.NETCore.App.Ref/8.0.33/ref/net8.0') if core else ref
 args=['-nologo','-target:'+kind,'-langversion:12','-deterministic+','-optimize+','-out:'+str(out/name)]+['-r:'+str(p) for p in sorted(refs.glob('*.dll'))]+['-r:'+str(anchor),'-r:'+str(harmony)]+list(map(str,sources))
 rsp=out/(name+'.rsp');rsp.write_text('\n'.join('"'+a+'"' for a in args));r=subprocess.run([str(sdk/'dotnet'),str(sdk/'sdk/8.0.427/Roslyn/bincore/csc.dll'),'@'+str(rsp)],capture_output=True,text=True);print(r.stdout,r.stderr);r.check_returncode();return out/name
if __name__=='__main__':
 p=compile('RAN.Australis.DeckController.dll',sorted((root/('Controller' if (root/'Controller').exists() else 'lighting-src')).glob('*.cs')));print(hashlib.sha256(p.read_bytes()).hexdigest())
