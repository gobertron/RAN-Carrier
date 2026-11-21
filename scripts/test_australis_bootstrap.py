"""Run the real embedded bootstrap with mocked HTTP and harmless package fixtures.

This exercises download/verification control flow without installing game files.
Use --pwsh powershell on Windows to run it under Windows PowerShell 5.1.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import zipfile

RUNNER = r'''
param([string]$Launcher,[string]$Fixture,[string]$Marker,[string]$ExpectedFailure)
$ErrorActionPreference='Stop'
$env:LOCALAPPDATA=Join-Path $Fixture 'logs'
$env:AUSTRALIS_BOOTSTRAP_MODE='Check'
$env:AUSTRALIS_BOOTSTRAP_GAME='Mock game directory'
$env:AUSTRALIS_MOCK_MARKER=$Marker
$script:fixturePath=$Fixture
function Get-Process {param([string[]]$Name,[object]$ErrorAction) @()}
function Invoke-WebRequest {
 param([switch]$UseBasicParsing,[string]$Uri,[hashtable]$Headers,[int]$TimeoutSec,[string]$OutFile)
 if($Uri -eq 'https://api.github.com/repos/gobertron/RAN-Carrier/releases/latest'){
  return [pscustomobject]@{Content=[IO.File]::ReadAllText((Join-Path $script:fixturePath 'release.json'))}
 }
 if($Uri.EndsWith('/SHA256SUMS.txt')){Copy-Item -LiteralPath (Join-Path $script:fixturePath 'SHA256SUMS.txt') -Destination $OutFile;return}
 if($Uri.EndsWith('/Australis-v1.3.1-Windows11.zip')){Copy-Item -LiteralPath (Join-Path $script:fixturePath 'package.zip') -Destination $OutFile;return}
 throw ('Unexpected mocked request: '+$Uri)
}
$text=[IO.File]::ReadAllText($Launcher)
$block=[regex]::Matches($text,'(?ms)^#__AUSTRALIS_BOOTSTRAP_BEGIN__\r?\n(?<code>.*?)^#__AUSTRALIS_BOOTSTRAP_END__\r?$')
if($block.Count -ne 1){throw 'Bootstrap extraction failed.'}
$failed=$false
try{& ([scriptblock]::Create($block[0].Groups['code'].Value))}catch{$failed=$true;Write-Host ('[EXPECTED CHECK] '+$_.Exception.Message)}
if($ExpectedFailure -eq 'true'){
 if(!$failed){throw 'Unsafe fixture unexpectedly succeeded.'}
 if(Test-Path -LiteralPath $Marker){throw 'Installer ran before unsafe package was rejected.'}
}else{
 if($failed -or !(Test-Path -LiteralPath $Marker)){throw 'Valid fixture did not reach installer.'}
 $result=[IO.File]::ReadAllText($Marker) | ConvertFrom-Json
 if($result.Mode -ne 'Check' -or $result.GameDirectory -ne 'Mock game directory'){throw 'Installer arguments were not preserved.'}
}
$logs=@(Get-ChildItem -LiteralPath (Join-Path $env:LOCALAPPDATA 'RAN-Australis/Logs') -Filter '*.log')
if($logs.Count -ne 1){throw 'Bootstrap log was not saved.'}
if($ExpectedFailure -eq 'true' -and [IO.File]::ReadAllText($logs[0].FullName) -notmatch '\[FAILED\]'){throw 'Failure log lost its error.'}
'''


def fixture(directory: Path, case: str) -> None:
    installer = b'''param([string]$PackagePath,[string]$Mode,[string]$GameDirectory,[string]$RestoreDirectory)
[IO.File]::WriteAllText($env:AUSTRALIS_MOCK_MARKER,(@{Mode=$Mode;GameDirectory=$GameDirectory}|ConvertTo-Json))
'''
    manifest = {
        "schema": 1, "version": "1.3.1", "mod_directory_name": "RAN-HMAS-Australis",
        "files": {"Clean-Install-Australis.ps1": hashlib.sha256(installer).hexdigest()},
    }
    with zipfile.ZipFile(directory / "package.zip", "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("Clean-Install-Australis.ps1", installer + (b"# tampered\n" if case == "manifest_corruption" else b""))
        archive.writestr("PACKAGE-MANIFEST.json", json.dumps(manifest))
        if case == "unsafe_zip_path":
            archive.writestr("../escaped.txt", b"must never be extracted")
        if case == "case_collision":
            archive.writestr("clean-install-australis.ps1", installer)
    archive_hash = hashlib.sha256((directory / "package.zip").read_bytes()).hexdigest()
    if case == "checksum_corruption":
        archive_hash = "0" * 64
    (directory / "SHA256SUMS.txt").write_text(f"{archive_hash}  Australis-v1.3.1-Windows11.zip\n")
    release = {
        "tag_name": "v1.3.1", "draft": False, "prerelease": case == "prerelease_rejection",
        "assets": [{"name": name, "browser_download_url": "https://github.com/gobertron/RAN-Carrier/releases/download/v1.3.1/" + name}
                   for name in ("Australis-v1.3.1-Windows11.zip", "SHA256SUMS.txt")],
    }
    if case == "foreign_asset_rejection":
        release["assets"][0]["browser_download_url"] = "https://example.invalid/other.zip"
    (directory / "release.json").write_text(json.dumps(release))


def run(pwsh: str, output: Path | None) -> dict:
    root = Path(__file__).resolve().parents[1]
    launcher = root / "Install-Australis.cmd"
    cases = ("valid_package", "checksum_corruption", "unsafe_zip_path", "manifest_corruption", "case_collision", "prerelease_rejection", "foreign_asset_rejection")
    results = []
    with tempfile.TemporaryDirectory(prefix="Australis-bootstrap-check-") as temp:
        work = Path(temp)
        runner = work / "runner.ps1"
        runner.write_text(RUNNER, encoding="utf-8")
        for case in cases:
            directory = work / case
            directory.mkdir()
            fixture(directory, case)
            command = [pwsh, "-NoLogo", "-NoProfile", "-File", str(runner), "-Launcher", str(launcher), "-Fixture", str(directory), "-Marker", str(directory / "invoked.json"), "-ExpectedFailure", "false" if case == "valid_package" else "true"]
            completed = subprocess.run(command, capture_output=True, text=True, errors="replace", timeout=60)
            results.append({"case": case, "passed": completed.returncode == 0})
            if completed.returncode:
                print(completed.stdout)
                print(completed.stderr)
    report = {"runtime": pwsh, "tests": results, "passed": sum(r["passed"] for r in results), "failed": sum(not r["passed"] for r in results), "http_mocked": True, "game_files_modified": False, "live_game_tested": False}
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pwsh", default="pwsh")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = run(args.pwsh, args.output)
    print(json.dumps(report, indent=2))
    raise SystemExit(1 if report["failed"] else 0)
