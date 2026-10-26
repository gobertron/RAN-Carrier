#!/usr/bin/env python3
"""Compile with the official .NET SDK and user-provided AnchorChain dev refs.

No game/Unity DLL is linked or redistributed. Run with --sdk PATH/TO/dotnet
--references PATH/TO/extracted/dev --harmony PATH/TO/0Harmony.dll.
"""
import argparse, json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'australis-2030'))
from enclosed_deck import moving_specs
from build import ELEVATORS,WIDTH_SCALE
from lift_lighting import profiles

def build(sdk, references, harmony):
    home=sdk.resolve().parent
    compiler=sorted(home.glob('sdk/*/Roslyn/bincore/csc.dll'))[-1]
    refs=sorted(home.glob('packs/NETStandard.Library.Ref/*/ref/netstandard2.1'))[-1]
    src=ROOT/'addon/DeckController';out=ROOT/'addon/bin';out.mkdir(parents=True,exist_ok=True)
    rows=['namespace RAN.Australis { internal sealed class Motion { public string Name; public double X,Y,Z,Travel; public char Axis; public Motion(string n,double x,double y,double z,char a,double t){Name=n;X=x;Y=y;Z=z;Axis=a;Travel=t;} }','internal static class BayData { public const double MetresPerUnit=217/3.161967; public static readonly Motion[] Motions=new[]{']
    for m in moving_specs():
        rows.append('new Motion('+json.dumps(m['name'])+','+','.join(str(v) for v in m['position'])+",'"+m['axis']+"',"+str(m['travel'])+'),')
    rows+=['}; } }'];(src/'BayData.cs').write_text('\n'.join(rows)+'\n')
    data=profiles([(x*WIDTH_SCALE,z) for x,z in ELEVATORS])
    rows=['// Generated from the same physical positions as the recessed wall fixtures.',
          'namespace RAN.Australis { internal static class LiftLightingData { public static readonly LiftLampGroup[] Groups=new[]{']
    def number(n):return format(float(n),'.9g')+'f'
    for group in data:
        rows.append('new LiftLampGroup('+json.dumps(group['model'])+',new LiftLamp[]{')
        for lamp in group['fixtures']:
            x,y,z=lamp['position'];pitch,yaw,_=lamp['rotation_degrees']
            values=(x,y,z,pitch,yaw,*lamp['color'],lamp['range'],lamp['intensity'],lamp['spot_angle'])
            rows.append('new LiftLamp('+','.join(map(number,values))+'),')
        rows.append('}),')
    rows.append('}; } }');(src/'LiftLightingData.cs').write_text('\n'.join(rows)+'\n')
    args=['-nologo','-target:library','-langversion:12','-deterministic+','-optimize+','-out:'+str(out/'RAN.Australis.DeckController.dll')]
    args += ['-r:'+str(p) for p in refs.glob('*.dll')]
    args += ['-r:'+str(references/'AnchorChain.dll'),'-r:'+str(harmony)]
    args += [str(p) for p in sorted(src.glob('*.cs'))]
    rsp=out/'compile.rsp';rsp.write_text('\n'.join('"'+a+'"' for a in args))
    subprocess.run([str(sdk),str(compiler),'@'+str(rsp)],check=True)
    rsp.unlink()
    print('[OK] Compiled independent AnchorChain plugin')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--sdk',type=Path,required=True);p.add_argument('--references',type=Path,required=True);p.add_argument('--harmony',type=Path,required=True);a=p.parse_args();build(a.sdk,a.references,a.harmony)
