#!/usr/bin/env python3
"""Build the compact online installer from a verified base and target manifest.

The full offline installer remains a separate deliverable. This launcher fetches
an immutable, checksum-pinned archive already published by this project, applies
only the changed files, and verifies the complete target before installing.
"""
from pathlib import Path, PurePosixPath
import argparse
import base64
import gzip
import hashlib
import io
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BASE_NAME = 'RAN-Carrier-Australis-v0.8.2-Lift-Lighting.zip'
BASE_SHA256 = 'd01b90ca371c708cebf590efe5a19465c13cd2977f4402e53de1566d37250bdb'
BASE_URL = (
    'https://raw.githubusercontent.com/gobertron/RAN-Carrier/'
    '7a201850ff180213ca766dcbbb9bceaedb6c7e94/builds/' + BASE_NAME
)
TARGET_VERSION = '0.8.5-naval-details'
OUTPUT_NAME = 'install-ran-australis-v0.8.5-naval-details.sh'
MAX_OVERLAY_BYTES = 512 * 1024


def sha(data):
    return hashlib.sha256(data).hexdigest()


def safe_name(name):
    p = PurePosixPath(name)
    if (not name or p.is_absolute() or '..' in p.parts or '\\' in name
            or '\x00' in name or str(p) != name):
        raise ValueError('Unsafe package path: ' + repr(name))
    return name


BOOTSTRAP = r'''import argparse,base64,gzip,hashlib,io,json,ssl,stat,sys,tempfile,time,urllib.request,zipfile
from datetime import datetime
from pathlib import Path,PurePosixPath

BASE_URL=__BASE_URL__
BASE_SHA256=__BASE_SHA256__
BASE_SIZE=__BASE_SIZE__
OVERLAY_DATA=__OVERLAY_DATA__
OVERLAY_SHA256=__OVERLAY_SHA256__
MANIFEST_SHA256=__MANIFEST_SHA256__
VERSION=__VERSION__

def sha(data):return hashlib.sha256(data).hexdigest()
def safe_name(name):
    p=PurePosixPath(name)
    if not name or p.is_absolute() or '..' in p.parts or '\\' in name or '\x00' in name or str(p)!=name:
        raise ValueError('Unsafe package path: '+repr(name))
    return name

def fetch_base(report):
    context=ssl.create_default_context()
    for attempt in range(1,4):
        try:
            report('[DOWNLOAD] Verified-source carrier archive; attempt '+str(attempt)+'/3')
            request=urllib.request.Request(BASE_URL,headers={'User-Agent':'RAN-Australis-Installer/'+VERSION})
            with urllib.request.urlopen(request,timeout=25,context=context) as response:
                if not response.geturl().startswith('https://'):
                    raise ValueError('Download redirect did not retain HTTPS')
                data=bytearray();last_percent=-1
                while True:
                    block=response.read(256*1024)
                    if not block:break
                    data.extend(block)
                    if len(data)>BASE_SIZE:raise ValueError('Download is larger than the pinned archive')
                    percent=min(100,int(len(data)*100/BASE_SIZE))
                    if percent//25!=last_percent//25:
                        report('[DOWNLOAD] '+str(percent)+'% received')
                        last_percent=percent
            if len(data)!=BASE_SIZE or sha(data)!=BASE_SHA256:
                raise ValueError('Downloaded archive checksum mismatch; nothing installed')
            report('[DOWNLOAD] 100% received; archive SHA256 verified')
            return bytes(data)
        except (OSError,ValueError) as error:
            if attempt==3:raise RuntimeError('Carrier download failed after 3 attempts: '+str(error)) from error
            report('[RETRY] Download did not verify; retrying shortly')
            time.sleep(attempt)

def reconstruct(base_data,root):
    if len(base_data)!=BASE_SIZE or sha(base_data)!=BASE_SHA256:
        raise ValueError('Source archive checksum mismatch')
    packed=base64.b64decode(OVERLAY_DATA,validate=True)
    if sha(packed)!=OVERLAY_SHA256:raise ValueError('Embedded update checksum failed; download this script again')
    overlay=json.loads(gzip.decompress(packed))
    manifest_bytes=base64.b64decode(overlay['manifest'],validate=True)
    if sha(manifest_bytes)!=MANIFEST_SHA256:raise ValueError('Target manifest checksum mismatch')
    manifest=json.loads(manifest_bytes)
    if manifest['version']!=VERSION:raise ValueError('Target manifest version mismatch')
    desired=manifest['sha256_files']
    updates=overlay['files']
    if not set(updates)<=set(desired):raise ValueError('Update includes an undeclared target file')
    with zipfile.ZipFile(io.BytesIO(base_data)) as archive:
        if archive.testzip() is not None:raise ValueError('Verified source archive could not be read')
        entries={}
        for entry in archive.infolist():
            if entry.is_dir():continue
            full=safe_name(entry.filename)
            if stat.S_ISLNK(entry.external_attr>>16):raise ValueError('Symbolic link in source archive')
            if '/' not in full:raise ValueError('Unexpected source archive layout')
            relative=full.split('/',1)[1]
            if relative in entries:raise ValueError('Duplicate source archive path')
            entries[relative]=entry
        # Read only target-manifest entries. Obsolete source files are never
        # extracted, so the resulting tree is exactly the current release.
        for name,expected in desired.items():
            safe_name(name)
            if name in updates:
                update=updates[name]
                if isinstance(update,str):
                    data=base64.b64decode(update,validate=True)
                elif isinstance(update,dict):
                    kind=update.get('kind')
                    allowed={'kind','source_path','source_sha256'}
                    if kind=='splice':allowed|={'prefix_bytes','suffix_bytes','insert'}
                    if kind not in ('copy','splice') or set(update)!=allowed:
                        raise ValueError('Invalid embedded file-delta record: '+name)
                    source_path=safe_name(update['source_path'])
                    if source_path not in entries:raise ValueError('Missing delta source: '+source_path)
                    source=archive.read(entries[source_path])
                    if sha(source)!=update['source_sha256']:raise ValueError('File-delta source checksum mismatch')
                    if kind=='copy':data=source
                    else:
                        prefix,suffix=update['prefix_bytes'],update['suffix_bytes']
                        if (type(prefix) is not int or type(suffix) is not int or prefix<0 or suffix<0
                                or prefix+suffix>len(source)):
                            raise ValueError('Invalid file-delta bounds: '+name)
                        insert=base64.b64decode(update['insert'],validate=True)
                        data=source[:prefix]+insert+(source[len(source)-suffix:] if suffix else b'')
                else:raise ValueError('Invalid embedded target file: '+name)
            elif name in entries:
                data=archive.read(entries[name])
            else:raise ValueError('Missing target file: '+name)
            if sha(data)!=expected:raise ValueError('Target file checksum mismatch: '+name)
            target=root/name
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(data)
    (root/'BUILD-MANIFEST.json').write_bytes(manifest_bytes)
    actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    if actual!=set(desired)|{'BUILD-MANIFEST.json'}:raise ValueError('Reconstructed package has unexpected files')
    return len(desired)

def main():
    if any(arg in ('-h','--help') for arg in sys.argv[1:]):
        print('Australis '+VERSION+' online installer (Python 3 and internet required).')
        print('Downloads a checksum-pinned source archive, applies the embedded update,')
        print('then verifies the complete package before any game files are changed.')
        print('Close Sea Power before installation. Options:')
        print('  --game PATH        Sea Power installation folder')
        print('  --backups PATH     Folder for verified installation backups')
        print('  --log-dir PATH     Log folder (default: ~/Downloads)')
        print('  --check            Validate without installing')
        print('  --remove           Remove this carrier after a verified backup')
        print('  --restore PATH     Restore a verified installation backup')
        return 0
    parser=argparse.ArgumentParser(add_help=False,allow_abbrev=False)
    parser.add_argument('--log-dir',type=Path,default=Path.home()/'Downloads')
    options,_=parser.parse_known_args()
    log_dir=options.log_dir.expanduser()
    log_dir.mkdir(parents=True,exist_ok=True)
    log_path=log_dir/('RAN-Australis-download-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f')+'.log')
    with log_path.open('w') as log:
        def report(message):
            print(message,flush=True);log.write(message+'\n');log.flush()
        installing=False
        try:
            report('[PREPARE] Australis '+VERSION+' online installer')
            data=fetch_base(report)
            with tempfile.TemporaryDirectory(prefix='ran-australis-online-') as temp:
                root=Path(temp)
                count=reconstruct(data,root)
                report('[VERIFIED] '+str(count)+' target files; starting installation checks')
                sys.dont_write_bytecode=True
                sys.path.insert(0,str(root/'tools'))
                from install_recovery import main as install_main
                installing=True
                return install_main()
        except Exception as error:
            report('[STOP] '+str(error))
            if installing:
                report('[HELP] Installer stopped unexpectedly; retain its log and backup for review.')
            else:
                report('[HELP] Package preparation failed; no game files were changed. Copy this log into chat.')
            report('[LOG] '+str(log_path))
            return 1
if __name__=='__main__':sys.exit(main())
'''


def build(root=ROOT, output=None):
    root = Path(root)
    base = root / 'builds' / BASE_NAME
    base_data = base.read_bytes()
    if sha(base_data) != BASE_SHA256:
        raise ValueError('The local immutable base archive does not match its published checksum')
    manifest_bytes = (root / 'BUILD-MANIFEST.json').read_bytes()
    manifest = json.loads(manifest_bytes)
    if manifest['version'] != TARGET_VERSION:
        raise ValueError('Create the final ' + TARGET_VERSION + ' BUILD-MANIFEST.json first')
    files = {}
    with zipfile.ZipFile(io.BytesIO(base_data)) as archive:
        base_files = {}
        for entry in archive.infolist():
            if entry.is_dir():
                continue
            safe_name(entry.filename)
            relative = entry.filename.split('/', 1)[1]
            if relative in base_files:
                raise ValueError('Duplicate path in base archive')
            base_files[relative] = entry
        base_by_sha = {sha(archive.read(entry)): name for name, entry in base_files.items()}
        for name, expected in manifest['sha256_files'].items():
            safe_name(name)
            data = (root / name).read_bytes()
            if sha(data) != expected:
                raise ValueError('Target tree differs from manifest: ' + name)
            original = archive.read(base_files[name]) if name in base_files else None
            if original != data:
                # Reuse an unchanged base file that moved to a non-discovered
                # reference folder; do not duplicate it in the compact update.
                if expected in base_by_sha:
                    files[name] = {'kind': 'copy', 'source_path': base_by_sha[expected],
                                   'source_sha256': expected}
                    continue
                full = base64.b64encode(data).decode('ascii')
                if original is not None:
                    # A bounded common-prefix/suffix splice handles appended
                    # number panels without embedding an entire large OBJ.
                    prefix = 0
                    limit = min(len(original), len(data))
                    while prefix < limit and original[prefix] == data[prefix]:
                        prefix += 1
                    suffix = 0
                    while suffix < limit-prefix and original[-suffix-1] == data[-suffix-1]:
                        suffix += 1
                    patch = {'kind': 'splice', 'source_path': name,
                             'source_sha256': sha(original), 'prefix_bytes': prefix,
                             'suffix_bytes': suffix,
                             'insert': base64.b64encode(data[prefix:len(data)-suffix if suffix else None]).decode('ascii')}
                    if len(gzip.compress(json.dumps(patch).encode(), mtime=0)) < len(gzip.compress(full.encode(), mtime=0)):
                        files[name] = patch
                        continue
                files[name] = full
    overlay = {'manifest': base64.b64encode(manifest_bytes).decode('ascii'), 'files': files}
    packed = gzip.compress(json.dumps(overlay, separators=(',', ':'), sort_keys=True).encode(), mtime=0)
    if len(packed) > MAX_OVERLAY_BYTES:
        raise ValueError('Compact update exceeds 512 KiB; do not publish an oversized tool request')
    values = {
        '__BASE_URL__': BASE_URL, '__BASE_SHA256__': BASE_SHA256,
        '__BASE_SIZE__': len(base_data), '__OVERLAY_DATA__': base64.b64encode(packed).decode('ascii'),
        '__OVERLAY_SHA256__': sha(packed), '__MANIFEST_SHA256__': sha(manifest_bytes),
        '__VERSION__': TARGET_VERSION,
    }
    script = BOOTSTRAP
    for key, value in values.items():
        script = script.replace(key, repr(value))
    shell = (
        '#!/usr/bin/env bash\nset -euo pipefail\n'
        'command -v python3 >/dev/null || { echo "[STOP] Python 3 is required."; exit 1; }\n'
        'python3 - "$@" <<\'AUSTRALIS_NETWORK_PY\'\n' + script + '\nAUSTRALIS_NETWORK_PY\n'
    )
    output = Path(output) if output else root / 'builds' / OUTPUT_NAME
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(shell)
    output.chmod(0o755)
    result = {'installer': str(output), 'bytes': output.stat().st_size,
              'overlay_bytes': len(packed), 'changed_files': len(files),
              'target_files': len(manifest['sha256_files']), 'sha256': sha(output.read_bytes())}
    print(json.dumps(result, indent=2))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    build(args.root, args.output)
