$ErrorActionPreference='Stop'
Set-StrictMode -Version 2
$utf8=New-Object Text.UTF8Encoding($false)
$oldHash='03b5ef5652e97814835615b5b2facce7b8398d35aab064004957bbe97eb9189f'
$newHash='@@DLLHASH@@'
$objHash='@@OBJHASH@@'
function Hash-File([string]$p){if(!(Test-Path -LiteralPath $p -PathType Leaf)){throw "Missing required file: $p"};return (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}
function Write-Bytes([string]$p,[byte[]]$bytes){$temp=$p+'.lighting-'+[Guid]::NewGuid().ToString('N')+'.tmp';try{[IO.File]::WriteAllBytes($temp,$bytes);[IO.File]::Copy($temp,$p,$true)}finally{if(Test-Path -LiteralPath $temp){Remove-Item -LiteralPath $temp -Force}}}
try {
 if(@(Get-Process -Name 'Sea Power','SeaPower' -ErrorAction SilentlyContinue).Count -gt 0){throw 'Close Sea Power before applying or restoring the lighting patch.'}
 $game=$env:AUSTRALIS_LIGHT_GAME;if([string]::IsNullOrWhiteSpace($game)){$game='F:\SteamLibrary\steamapps\common\Sea Power'}
 $game=[IO.Path]::GetFullPath($game)
 $mod=Join-Path $game 'Sea Power_Data/StreamingAssets/RAN-Australis-Full-Restore'
 if(!(Test-Path -LiteralPath $mod -PathType Container)){throw "Working Full Restore installation not found: $mod"}
 if((Get-Item -LiteralPath $mod).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Mod folder is a link. Use the actual installed game path.'}
 $dll=Join-Path $mod 'RAN.Australis.DeckController.dll'
 $obj=Join-Path $mod 'ships/ran_cvn_australis_2030/ran_cvn_australis_2030.obj'
 if((Hash-File $obj) -ne $objHash){throw 'This lighting patch requires the exact Full Restore v1.2.0 model. No files changed.'}
 $observed=Hash-File $dll
 $mode=$env:AUSTRALIS_LIGHT_MODE;if([string]::IsNullOrWhiteSpace($mode)){$mode='Install'}
 if($mode -notin @('Install','Check','Restore')){throw 'Mode must be Install, Check or Restore.'}
 if($observed -notin @($oldHash,$newHash)){throw "Unrecognised controller hash: $observed. No files changed."}
 $self=[IO.File]::ReadAllText($env:AUSTRALIS_LIGHT_SELF)
 $match=[regex]::Matches($self,'(?ms)^#__AUSTRALIS_LIGHT_DLL_BEGIN__\r?\n(?<data>.*?)^#__AUSTRALIS_LIGHT_DLL_END__\r?$')
 if($match.Count -ne 1){throw 'Embedded lighting controller is missing or truncated.'}
 $bytes=[Convert]::FromBase64String($match[0].Groups['data'].Value)
 $sha=[Security.Cryptography.SHA256]::Create();try{$digest=([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-','').ToLowerInvariant()}finally{$sha.Dispose()}
 if($digest -ne $newHash){throw 'Embedded controller hash failed. No files changed.'}
 if($mode -eq 'Check'){Write-Host '[PASS] Working model, supported controller and embedded lighting patch verified.';exit 0}
 if($mode -eq 'Restore'){
  if($observed -ne $newHash){throw 'Patched controller is not currently installed.'}
  $backup=$env:AUSTRALIS_LIGHT_BACKUP;if([string]::IsNullOrWhiteSpace($backup)){throw 'Pass the exact backup folder printed when this patch was installed.'}
  $record=Get-Content -LiteralPath (Join-Path $backup 'backup.json') -Raw | ConvertFrom-Json
  if($record.mod_path -ne $mod -or $record.patch -ne '1.2.3-lighting'){throw 'Backup belongs to another installation.'}
  foreach($row in $record.files){if($row.name -notin @('RAN.Australis.DeckController.dll','RUNTIME-FILES.json','AUSTRALIS-INSTALL.json')){throw 'Unexpected backup entry.'};if((Hash-File (Join-Path $backup $row.name)) -ne $row.old_sha256){throw 'Backup hash failed.'};if((Hash-File (Join-Path $mod $row.name)) -ne $row.new_sha256){throw 'An installed file changed after the patch; restore stopped.'}}
  foreach($row in $record.files){Write-Bytes (Join-Path $mod $row.name) ([IO.File]::ReadAllBytes((Join-Path $backup $row.name)))}
  Write-Host '[RESTORED] Exact pre-patch controller and inventories restored.';exit 0
 }
 if($observed -eq $newHash){Write-Host '[OK] Lighting patch is already installed.';exit 0}
 $runtime=Join-Path $mod 'RUNTIME-FILES.json';$inventory=Get-Content -LiteralPath $runtime -Raw | ConvertFrom-Json
 if($inventory.'RAN.Australis.DeckController.dll' -ne $oldHash){throw 'Runtime inventory differs from the working baseline. No files changed.'}
 $inventory.'RAN.Australis.DeckController.dll'=$newHash
 $runtimeBytes=$utf8.GetBytes(($inventory | ConvertTo-Json -Depth 100)+"`n")
 $changes=@(@{name='RAN.Australis.DeckController.dll';data=$bytes},@{name='RUNTIME-FILES.json';data=$runtimeBytes})
 $marker=Join-Path $mod 'AUSTRALIS-INSTALL.json'
 if(Test-Path -LiteralPath $marker){
  $installed=Get-Content -LiteralPath $marker -Raw | ConvertFrom-Json
  if($installed.installed_files.'RAN.Australis.DeckController.dll' -ne $oldHash){throw 'Installed controller inventory differs. No files changed.'}
  $installed.installed_files.'RAN.Australis.DeckController.dll'=$newHash
  $sha=[Security.Cryptography.SHA256]::Create();try{$installed.installed_files.'RUNTIME-FILES.json'=([BitConverter]::ToString($sha.ComputeHash($runtimeBytes))).Replace('-','').ToLowerInvariant()}finally{$sha.Dispose()}
  $changes+=@{name='AUSTRALIS-INSTALL.json';data=$utf8.GetBytes(($installed | ConvertTo-Json -Depth 100)+"`n")}
 }
 $downloads=Join-Path ([Environment]::GetFolderPath('UserProfile')) 'Downloads'
 $backup=Join-Path $downloads ('Australis-Lighting-Backups/'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'-'+[Guid]::NewGuid().ToString('N').Substring(0,8))
 [void][IO.Directory]::CreateDirectory($backup)
 $rows=@();foreach($change in $changes){$path=Join-Path $mod $change.name;Copy-Item -LiteralPath $path -Destination (Join-Path $backup $change.name);$sha=[Security.Cryptography.SHA256]::Create();try{$new=([BitConverter]::ToString($sha.ComputeHash($change.data))).Replace('-','').ToLowerInvariant()}finally{$sha.Dispose()};$rows+=@{name=$change.name;old_sha256=(Hash-File $path);new_sha256=$new}}
 [IO.File]::WriteAllText((Join-Path $backup 'backup.json'),(@{patch='1.2.3-lighting';mod_path=$mod;files=$rows} | ConvertTo-Json -Depth 20),$utf8)
 try{foreach($change in $changes){Write-Bytes (Join-Path $mod $change.name) $change.data};foreach($row in $rows){if((Hash-File (Join-Path $mod $row.name)) -ne $row.new_sha256){throw 'Post-write verification failed.'}}}
 catch{foreach($row in $rows){Write-Bytes (Join-Path $mod $row.name) ([IO.File]::ReadAllBytes((Join-Path $backup $row.name)))};throw}
 Write-Host '[INSTALLED] Australis v1.2.3 lighting patch on Full Restore v1.2.0.'
 Write-Host ('[BACKUP] '+$backup)
 Write-Host '[NEXT] Start a new mission and check clear day, storm and night. In-game rendering remains to be confirmed.'
 exit 0
}catch{Write-Host ('[FAILED] '+$_.Exception.Message);exit 1}
