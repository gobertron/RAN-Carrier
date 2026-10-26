#!/usr/bin/env python3
"""Compile/run production lift-light code against a minimal Unity-shaped fixture.

Verifies actual-height gating and failure cleanup. This is not an in-game or
Unity renderer test. Pass the same local dotnet executable used by the builder.
"""
from pathlib import Path
import argparse,json,subprocess,tempfile

ROOT=Path(__file__).resolve().parents[1]

def run(sdk):
    sdk=Path(sdk).resolve();home=sdk.parent
    compiler=sorted(home.glob('sdk/*/Roslyn/bincore/csc.dll'))[-1]
    refs=sorted(home.glob('packs/Microsoft.NETCore.App.Ref/*/ref/net8.0'))[-1]
    src=ROOT/'addon/DeckController'
    sources=[src/name for name in ('LiftLightPolicy.cs','LiftLights.cs','LiftLightingData.cs','LiftLightTests.cs.txt')]
    for source in sources:
        if not source.is_file():raise FileNotFoundError(f'Build the controller/generated lighting data first: {source}')
    with tempfile.TemporaryDirectory(prefix='australis-lift-light-tests-') as folder:
        out=Path(folder)/'LiftLightTests.dll'
        args=['-nologo','-target:exe','-langversion:12','-deterministic+','-out:'+str(out)]
        args+=['-r:'+str(p) for p in refs.glob('*.dll')]
        args+=[str(p) for p in sources]
        response=Path(folder)/'compile.rsp';response.write_text('\n'.join('"'+arg+'"' for arg in args))
        subprocess.run([str(sdk),str(compiler),'@'+str(response)],check=True)
        runtime_version=sorted(home.glob('shared/Microsoft.NETCore.App/*'))[-1].name
        out.with_suffix('.runtimeconfig.json').write_text(json.dumps({'runtimeOptions':{'tfm':'net8.0','framework':{'name':'Microsoft.NETCore.App','version':runtime_version}}}))
        subprocess.run([str(sdk),str(out)],check=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('sdk',type=Path);a=p.parse_args();run(a.sdk)
