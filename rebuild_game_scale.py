#!/usr/bin/env python3
"""Rebuild approximate Sea Power scale OBJ copies from the packaged originals."""
from pathlib import Path
import json
import shutil

ROOT = Path(__file__).resolve().parent
METRES_PER_UNIT = 217 / 3.161967

def main():
    manifest=json.loads((ROOT/'design-manifest.json').read_text())
    for d in manifest['designs']:
        unit=d['id'];source=ROOT/'metre-source-models'/f'{unit}.obj'
        target=ROOT/'game-scale-models/ships'/unit/f'{unit}.obj'
        target.parent.mkdir(parents=True,exist_ok=True)
        rows=[]
        with source.open(encoding='utf8') as f:
            rows=['# Original RAN carrier model study scaled to an observed Sea Power reference mesh.\n',
                  '# Approximate game scale only; engine origin, deck routing and collision need an in-game test.\n']
            for line in f:
                if line.startswith('v '):
                    rows.append('v '+' '.join(f'{float(v)/METRES_PER_UNIT:.8f}' for v in line.split()[1:4])+'\n')
                else:rows.append(line)
        target.write_text(''.join(rows))
        shutil.copy2(source.with_suffix('.mtl'),target.with_suffix('.mtl'))
        print(unit)

if __name__=='__main__':main()
