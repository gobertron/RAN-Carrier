@echo off
setlocal DisableDelayedExpansion
title RAN HMAS Australis - Install or Update
set "AUSTRALIS_BOOTSTRAP_FILE=%~f0"
set "AUSTRALIS_BOOTSTRAP_GAME=%~1"
set "AUSTRALIS_BOOTSTRAP_MODE=%~2"
set "AUSTRALIS_BOOTSTRAP_RESTORE=%~3"
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoLogo -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop';try{$s=[IO.File]::ReadAllText($env:AUSTRALIS_BOOTSTRAP_FILE);$m=[regex]::Matches($s,'(?ms)^#__AUSTRALIS_BOOTSTRAP_BEGIN__\r?\n(?<code>.*?)^#__AUSTRALIS_BOOTSTRAP_END__\r?$');if($m.Count -ne 1){throw 'Installer launcher is incomplete.'};& ([scriptblock]::Create($m[0].Groups['code'].Value));exit 0}catch{Write-Host ('[FAILED] '+$_.Exception.Message);exit 1}"
set "AUSTRALIS_BOOTSTRAP_EXIT=%errorlevel%"
echo.
if not defined AUSTRALIS_NO_PAUSE pause
exit /b %AUSTRALIS_BOOTSTRAP_EXIT%
#__AUSTRALIS_BOOTSTRAP_BEGIN__
#requires -Version 5.1
$ErrorActionPreference='Stop'
Set-StrictMode -Version 2
$temporary=''
$logPath=''
$bootstrapLines=New-Object 'System.Collections.Generic.List[string]'
function Write-AustralisBootstrap([string]$message){Write-Host $message;[void]$bootstrapLines.Add($message)}
function Get-AustralisBootstrapHash([string]$path){return (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()}
function Test-AustralisRelativePath([string]$relative){
 if(!$relative -or $relative -match '(^/|\\|[<>:"|?*\x00-\x1f])'){return $false}
 foreach($segment in $relative.Split('/')){if(!$segment -or $segment -in @('.','..') -or $segment -match '[. ]$' -or $segment -match '^(?i:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)'){return $false}}
 return $true
}
function Get-AustralisReleaseAsset($release,[string]$name){
 $matches=@($release.assets | Where-Object {$_.name -ceq $name})
 if($matches.Count -ne 1){throw ('The latest stable release does not contain exactly one '+$name+'.')}
 $url=[string]$matches[0].browser_download_url
 if($url -notmatch '^https://github\.com/gobertron/RAN-Carrier/releases/download/v[0-9]+\.[0-9]+\.[0-9]+/'){throw 'Unexpected release download location.'}
 return $url
}
try{
 $logRoot=$env:LOCALAPPDATA
 if(!$logRoot){$logRoot=[IO.Path]::GetTempPath()}
 $logDirectory=Join-Path $logRoot 'RAN-Australis/Logs'
 [void][IO.Directory]::CreateDirectory($logDirectory)
 $logPath=Join-Path $logDirectory ('Australis-launcher-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'-'+[guid]::NewGuid().ToString('N').Substring(0,8)+'.log')
 Write-AustralisBootstrap '[0%] RAN / HMAS Australis - latest stable installer'
 Write-AustralisBootstrap ('[BOOTSTRAP LOG] '+$logPath)
 if(@(Get-Process -Name 'Sea Power','SeaPower','sea_power' -ErrorAction SilentlyContinue).Count){throw 'Close Sea Power and its Mod Manager, then run this launcher again.'}
 $mode=$env:AUSTRALIS_BOOTSTRAP_MODE
 if(!$mode){$mode='Install'}
 if($mode -notin @('Install','Check','Restore')){throw 'Mode must be Install, Check or Restore.'}
 [Net.ServicePointManager]::SecurityProtocol=[Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
 $headers=@{'User-Agent'='RAN-Australis-Windows-Installer';'Accept'='application/vnd.github+json'}
 $api='https://api.github.com/repos/gobertron/RAN-Carrier/releases/latest'
 $release=(Invoke-WebRequest -UseBasicParsing -Uri $api -Headers $headers -TimeoutSec 60).Content | ConvertFrom-Json
 if($release.draft -or $release.prerelease -or [string]$release.tag_name -notmatch '^v[0-9]+\.[0-9]+\.[0-9]+$'){throw 'No supported stable Australis release was returned.'}
 $version=([string]$release.tag_name).Substring(1)
 $zipName='Australis-v'+$version+'-Windows11.zip'
 $zipUrl=Get-AustralisReleaseAsset $release $zipName
 $checksumsUrl=Get-AustralisReleaseAsset $release 'SHA256SUMS.txt'
 Write-AustralisBootstrap ('[10%] Latest stable version: '+$version)
 $temporary=Join-Path ([IO.Path]::GetTempPath()) ('Australis-latest-'+[guid]::NewGuid().ToString('N'))
 [void][IO.Directory]::CreateDirectory($temporary)
 $zipPath=Join-Path $temporary $zipName
 $sumsPath=Join-Path $temporary 'SHA256SUMS.txt'
 Invoke-WebRequest -UseBasicParsing -Uri $checksumsUrl -OutFile $sumsPath -TimeoutSec 60
 $sumPattern='(?mi)^([a-f0-9]{64})[ \t]+\*?'+[regex]::Escape($zipName)+'[ \t]*\r?$'
 $sumMatches=[regex]::Matches([IO.File]::ReadAllText($sumsPath),$sumPattern)
 if($sumMatches.Count -ne 1){throw 'The release checksum list is incomplete or ambiguous.'}
 Write-AustralisBootstrap '[20%] Downloading and staging the complete carrier package.'
 Invoke-WebRequest -UseBasicParsing -Uri $zipUrl -OutFile $zipPath -TimeoutSec 600
 $expectedHash=$sumMatches[0].Groups[1].Value.ToLowerInvariant()
 if((Get-AustralisBootstrapHash $zipPath) -ne $expectedHash){throw 'Downloaded package checksum failed. No game files changed.'}
 Write-AustralisBootstrap '[45%] Package SHA256 verified.'
 Add-Type -AssemblyName System.IO.Compression.FileSystem
 $archive=[IO.Compression.ZipFile]::OpenRead($zipPath)
 try{
  if($archive.Entries.Count -gt 10000){throw 'The package contains too many archive entries.'}
  $seen=@{};$expanded=[long]0
  foreach($entry in $archive.Entries){
   $name=$entry.FullName
   if($name.EndsWith('/')){$name=$name.TrimEnd('/')}
   if(!(Test-AustralisRelativePath $name) -or $seen.ContainsKey($name)){throw ('Unsafe or duplicate archive path: '+$name)}
   $seen[$name]=$true
   if((($entry.ExternalAttributes -shr 16) -band 61440) -eq 40960){throw 'Linked archive content is not supported.'}
   $expanded+=$entry.Length
   if($expanded -gt 1073741824){throw 'The expanded package exceeds the supported size.'}
  }
 }finally{$archive.Dispose()}
 $package=Join-Path $temporary 'package'
 [IO.Compression.ZipFile]::ExtractToDirectory($zipPath,$package)
 $manifestPath=Join-Path $package 'PACKAGE-MANIFEST.json'
 $manifest=[IO.File]::ReadAllText($manifestPath) | ConvertFrom-Json
 if($manifest.schema -ne 1 -or $manifest.version -cne $version -or $manifest.mod_directory_name -cne 'RAN-HMAS-Australis'){throw 'The release package identifies a different platform or version.'}
 $listed=@($manifest.files.PSObject.Properties)
 $actual=@(Get-ChildItem -LiteralPath $package -Recurse -File)
 if($actual.Count -ne $listed.Count+1){throw 'Release package file count differs from its manifest.'}
 foreach($file in $listed){
  if(!(Test-AustralisRelativePath $file.Name) -or $file.Value -notmatch '^[a-f0-9]{64}$'){throw 'The release manifest contains an invalid file entry.'}
  $path=Join-Path $package $file.Name
  if((Get-AustralisBootstrapHash $path) -cne [string]$file.Value){throw ('Release file verification failed: '+$file.Name)}
 }
 Write-AustralisBootstrap ('[60%] '+$listed.Count+' release files verified. Starting the transactional installer.')
 $arguments=@{PackagePath=$package;Mode=$mode}
 if($env:AUSTRALIS_BOOTSTRAP_GAME){$arguments.GameDirectory=$env:AUSTRALIS_BOOTSTRAP_GAME}
 if($env:AUSTRALIS_BOOTSTRAP_RESTORE){$arguments.RestoreDirectory=$env:AUSTRALIS_BOOTSTRAP_RESTORE}
 & (Join-Path $package 'Clean-Install-Australis.ps1') @arguments
 Write-AustralisBootstrap ('[100%] Australis '+$version+' '+$mode+' completed. The installer printed its detailed log and report paths above.')
}catch{
 Write-AustralisBootstrap ('[FAILED] '+$_.Exception.Message)
 [void]$bootstrapLines.Add(($_ | Out-String))
 [void]$bootstrapLines.Add([string]$_.ScriptStackTrace)
 if($logPath){Write-Host ('[COPY THIS LOG] '+$logPath)}
 throw
}finally{
 if($logPath){try{[IO.File]::WriteAllText($logPath,($bootstrapLines -join "`r`n")+"`r`n",(New-Object Text.UTF8Encoding($false)))}catch{Write-Host ('[LOG SAVE FAILED] '+$_.Exception.Message)}}
 if($temporary -and (Test-Path -LiteralPath $temporary)){try{Remove-Item -LiteralPath $temporary -Recurse -Force}catch{Write-Host ('[NOTE] Temporary package retained at '+$temporary)}}
}
#__AUSTRALIS_BOOTSTRAP_END__
