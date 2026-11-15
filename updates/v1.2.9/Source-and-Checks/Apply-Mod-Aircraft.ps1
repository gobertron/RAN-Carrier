#requires -Version 5.1
[CmdletBinding()]
param(
 [string]$GameDirectory='',
 [string]$LoadOrderPath='',
 [ValidateSet('Check','Install','Restore')][string]$Mode='Install',
 [string]$BackupDirectory=''
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version 2
. (Join-Path $PSScriptRoot 'Mod-Aircraft-Catalog.ps1')
$patchVersion='1.2.9'
function Get-PatchSha([byte[]]$Bytes) {
 $h=[Security.Cryptography.SHA256]::Create()
 try { return ([BitConverter]::ToString($h.ComputeHash($Bytes))).Replace('-','').ToLowerInvariant() } finally { $h.Dispose() }
}
function Assert-PatchPath([string]$Path) {
 $walk=[IO.Path]::GetFullPath($Path)
 while($walk){
  if((Test-Path -LiteralPath $walk) -and ((Get-Item -LiteralPath $walk -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)){throw ('Linked path refused: '+$Path)}
  $next=[IO.Path]::GetDirectoryName($walk);if($next -eq $walk){break};$walk=$next
 }
}
function Get-PatchGame([string]$Requested) {
 $candidates=New-Object 'System.Collections.Generic.List[string]'
 if($Requested){[void]$candidates.Add($Requested)}
 else {
  [void]$candidates.Add('F:\SteamLibrary\steamapps\common\Sea Power')
  if(${env:ProgramFiles(x86)}){[void]$candidates.Add((Join-Path ${env:ProgramFiles(x86)} 'Steam/steamapps/common/Sea Power'))}
  if($env:OS -eq 'Windows_NT'){
   $steam=Get-ItemProperty -LiteralPath 'HKCU:\Software\Valve\Steam' -ErrorAction SilentlyContinue
   if($steam -and $steam.PSObject.Properties['SteamPath']){
    [void]$candidates.Add((Join-Path $steam.SteamPath 'steamapps/common/Sea Power'))
    $vdf=Join-Path $steam.SteamPath 'steamapps/libraryfolders.vdf'
    if(Test-Path -LiteralPath $vdf){foreach($m in [regex]::Matches([IO.File]::ReadAllText($vdf),'"path"\s*"([^"]+)"')){[void]$candidates.Add((Join-Path $m.Groups[1].Value.Replace('\\','\') 'steamapps/common/Sea Power'))}}
   }
  }
 }
 foreach($candidate in $candidates){
  $game=[IO.Path]::GetFullPath($candidate).TrimEnd([char[]]@('/','\'))
  if([IO.Path]::GetFileName($game) -ieq 'StreamingAssets'){$game=[IO.Directory]::GetParent([IO.Directory]::GetParent($game).FullName).FullName}
  if(Test-Path -LiteralPath (Join-Path $game 'Sea Power_Data/StreamingAssets/original/aircraft') -PathType Container){Assert-PatchPath $game;return $game}
 }
 throw 'Sea Power was not found. Drag its game folder onto the installer, or pass -GameDirectory.'
}
function Read-PatchFile([string]$Path) {
 Assert-PatchPath $Path
 $bytes=[IO.File]::ReadAllBytes($Path);$skip=0;$encoding=New-Object Text.UTF8Encoding($false,$true)
 if($bytes.Length -ge 3 -and $bytes[0] -eq 239 -and $bytes[1] -eq 187 -and $bytes[2] -eq 191){$skip=3;$encoding=New-Object Text.UTF8Encoding($true,$true)}
 elseif($bytes.Length -ge 2 -and $bytes[0] -eq 255 -and $bytes[1] -eq 254){$skip=2;$encoding=New-Object Text.UnicodeEncoding($false,$true,$true)}
 elseif($bytes.Length -ge 2 -and $bytes[0] -eq 254 -and $bytes[1] -eq 255){$skip=2;$encoding=New-Object Text.UnicodeEncoding($true,$true,$true)}
 return [pscustomobject]@{Bytes=$bytes;Text=$encoding.GetString($bytes,$skip,$bytes.Length-$skip);Encoding=$encoding;Sha=(Get-PatchSha $bytes)}
}
function Encode-PatchText([string]$Text,$Encoding) {return ,([byte[]]($Encoding.GetPreamble()+$Encoding.GetBytes($Text)))}
function Json-PatchBytes($Data) {return ,([Text.Encoding]::UTF8.GetBytes(($Data | ConvertTo-Json -Depth 100)+"`n"))}
function Write-PatchAtomic([string]$Path,[byte[]]$Bytes) {
 Assert-PatchPath $Path
 $temp=$Path+'.australis-'+[Guid]::NewGuid().ToString('N')+'.tmp'
 try {
  [IO.File]::WriteAllBytes($temp,$Bytes)
  if([IO.File]::Exists($Path)){[IO.File]::Replace($temp,$Path,[System.Management.Automation.Language.NullString]::Value)}else{[IO.File]::Move($temp,$Path)}
  if((Get-PatchSha ([IO.File]::ReadAllBytes($Path))) -ne (Get-PatchSha $Bytes)){throw ('Write verification failed: '+$Path)}
 } finally {if([IO.File]::Exists($temp)){[IO.File]::Delete($temp)}}
}
function Save-PatchJournal($Journal,[string]$Path) {Write-PatchAtomic $Path (Json-PatchBytes $Journal)}
function Get-PatchLocalTarget([string]$Stream,$Catalog) {
 $candidates=@()
 foreach($root in $Catalog.Roots){
  if(!$root.Enabled -or $root.Kind -ne 'localmod'){continue}
  $dir=[IO.Path]::GetFullPath($root.Path).TrimEnd([char[]]@('/','\'))
  if([IO.Path]::GetDirectoryName($dir) -ne $Stream){continue}
  if(Test-Path -LiteralPath (Join-Path $dir 'vessels/ran_cvn_australis_2030.ini') -PathType Leaf){$candidates+=$dir}
 }
 if($candidates.Count -ne 1){throw ('Expected one enabled local Australis carrier; found '+$candidates.Count+'. Enable your local RAN-HMAS-Australis and disable duplicate copies in Mod Manager, then exit the game.')}
 return [string]$candidates[0]
}

if(@(Get-Process -Name 'Sea Power','SeaPower','sea_power' -ErrorAction SilentlyContinue).Count){throw 'Close Sea Power before applying or restoring this selection patch.'}
$game=Get-PatchGame $GameDirectory
$stream=[IO.Path]::GetFullPath((Join-Path $game 'Sea Power_Data/StreamingAssets')).TrimEnd([char[]]@('/','\'))
if($Mode -eq 'Restore'){
 if(!$BackupDirectory){throw 'Restore requires the backup folder printed by the installer.'}
 $backup=[IO.Path]::GetFullPath($BackupDirectory);Assert-PatchPath $backup
 $journalPath=Join-Path $backup 'transaction.json'
 $journal=([IO.File]::ReadAllText($journalPath) | ConvertFrom-Json)
 if($journal.schema -ne 1 -or $journal.patch_version -ne $patchVersion -or $journal.game_directory -ne $game){throw 'Backup belongs to another game or patch.'}
 if($journal.state -notin @('Installed','Installing','Prepared','RecoveryRequired','Restoring')){throw ('Backup is not a restorable transaction: '+$journal.state)}
 $target=[IO.Path]::GetFullPath($journal.target_directory).TrimEnd([char[]]@('/','\'))
 if([IO.Path]::GetDirectoryName($target) -ne $stream -or [IO.Path]::GetFileName($target) -in @('original','user')){throw 'Backup target is not a local mod directory.'}
 # Validate every restore input and every current output before changing one byte.
 foreach($entry in $journal.files){
  if($entry.relative_path -notmatch '^(?:vessels/ran_cvn_[A-Za-z0-9_.-]+\.ini|RUNTIME-FILES\.json|AUSTRALIS-INSTALL\.json|AUSTRALIS-MOD-AIRCRAFT-PATCH\.json)$'){throw 'Unsafe backup target path.'}
  $dest=Join-Path $target $entry.relative_path;Assert-PatchPath $dest
  if(Test-Path -LiteralPath $dest -PathType Leaf){
   $current=Get-PatchSha ([IO.File]::ReadAllBytes($dest))
   if($current -ne $entry.installed_sha256 -and (!$entry.existed -or $current -ne $entry.original_sha256)){throw ('Restore refused because the installed file changed: '+$entry.relative_path)}
  }elseif($entry.existed){throw ('Restore refused because an original file is missing: '+$entry.relative_path)}
  if($entry.existed){
   if($entry.backup_file -notmatch '^before-[0-9]+\.bin$'){throw 'Unsafe backup file name.'}
   $saved=Join-Path $backup $entry.backup_file;Assert-PatchPath $saved
   if((Get-PatchSha ([IO.File]::ReadAllBytes($saved))) -ne $entry.original_sha256){throw 'Backup file hash mismatch.'}
  }
 }
 $journal.state='Restoring';Save-PatchJournal $journal $journalPath
 foreach($entry in $journal.files){
  $dest=Join-Path $target $entry.relative_path
  if($entry.existed){Write-PatchAtomic $dest ([IO.File]::ReadAllBytes((Join-Path $backup $entry.backup_file)))}elseif([IO.File]::Exists($dest)){[IO.File]::Delete($dest)}
 }
 $journal.state='Restored';Save-PatchJournal $journal $journalPath
 Write-Host '[100%] Previous aircraft selection restored.'
 return [pscustomobject]@{Version=$patchVersion;Mode=$Mode;BackupDirectory=$backup;ChangedFiles=@($journal.files.relative_path);TargetDirectory=$target}
}
if(!$LoadOrderPath){
 $userDir=[Environment]::GetFolderPath('UserProfile')
 $LoadOrderPath=Join-Path $userDir 'AppData/LocalLow/Triassic Games/Sea Power/usersettings.ini'
}
Write-Host '[10%] Reading enabled mods and installed aircraft.'
$catalog=Get-AustralisModAircraftCatalog -GameDirectory $game -LoadOrderPath $LoadOrderPath
$target=Get-PatchLocalTarget $stream $catalog
Assert-PatchPath $target
if($Mode -eq 'Install'){
 $backupRoot=Join-Path $game '_Australis-Aircraft-Backups'
 if(Test-Path -LiteralPath $backupRoot){
  Assert-PatchPath $backupRoot
  foreach($folder in Get-ChildItem -LiteralPath $backupRoot -Directory){
   $priorPath=Join-Path $folder.FullName 'transaction.json'
   if(Test-Path -LiteralPath $priorPath){
    Assert-PatchPath $priorPath;$prior=[IO.File]::ReadAllText($priorPath) | ConvertFrom-Json
    if($prior.patch_version -eq $patchVersion -and $prior.state -notin @('Installed','Restored','RolledBack')){throw ('An interrupted patch needs Restore first. Backup: '+$folder.FullName)}
   }
  }
 }
}
Write-Host ('[CARRIER] '+$target)
$plans=New-Object 'System.Collections.Generic.List[object]'
$ids=@{};foreach($id in $catalog.SupportedIds){$ids[$id]=$true}
$vessels=@(Get-ChildItem -LiteralPath (Join-Path $target 'vessels') -File -Filter 'ran_cvn_*.ini' | Where-Object {$_.BaseName -notmatch '_variants$' -and $_.BaseName -match 'australis|southern_cross'})
if(!$vessels.Count){throw 'No Australis vessel definitions found.'}
$addedCount=0;$supportedCount=0
foreach($file in $vessels){
 $before=Read-PatchFile $file.FullName
 $patched=Get-AustralisModAircraftPatch -VesselText $before.Text -SupportedIds $catalog.SupportedIds
 $after=Encode-PatchText $patched $before.Encoding
 $prior=@();$found=[regex]::Match($before.Text,'(?im)^[ \t]*AircraftSupported[ \t]*=([^\r\n]*)')
 if($found.Success){$prior=@($found.Groups[1].Value.Split(',') | ForEach-Object {$_.Trim()} | Where-Object {$_})}
 $now=[regex]::Match($patched,'(?im)^[ \t]*AircraftSupported[ \t]*=([^\r\n]*)').Groups[1].Value.Split(',')
 $addedCount+=@($now | Where-Object {$_ -notin $prior}).Count;$supportedCount=$now.Count
 [void]$plans.Add([pscustomobject]@{Relative=('vessels/'+$file.Name);Before=$before.Bytes;After=$after})
}
Write-Host ('[50%] '+$catalog.SupportedIds.Count+' loaded aircraft IDs found; '+$addedCount+' support-list additions.')
Write-Host ('[MODS] '+@($catalog.DisabledMods).Count+' disabled entries skipped. Aircraft mods must be enabled to appear in game.')
if($Mode -eq 'Check'){
 return [pscustomobject]@{Version=$patchVersion;Mode=$Mode;BackupDirectory='';ChangedFiles=@($plans | Where-Object {(Get-PatchSha $_.Before) -ne (Get-PatchSha $_.After)} | ForEach-Object {$_.Relative});AddedCount=$addedCount;SupportedCount=$supportedCount;TargetDirectory=$target;Catalog=$catalog;GameFilesModified=$false}
}
$report=[ordered]@{schema=1;patch_version=$patchVersion;created_utc=[DateTime]::UtcNow.ToString('o');scope='Selection-list refresh from stock and enabled local/Workshop aircraft; flight operations untested';base_version_preserved=$true;airgroup_preserved=$true;routes_or_geometry_modified=$false;catalog=$catalog;vessels=@($plans | ForEach-Object {@{path=$_.Relative;sha256=(Get-PatchSha $_.After)}})}
$reportName='AUSTRALIS-MOD-AIRCRAFT-PATCH.json'
$reportBytes=Json-PatchBytes $report
$reportPath=Join-Path $target $reportName;$priorReport=[byte[]]@()
Assert-PatchPath $reportPath
if(Test-Path -LiteralPath $reportPath){$priorReport=[IO.File]::ReadAllBytes($reportPath)}
[void]$plans.Add([pscustomobject]@{Relative=$reportName;Before=$priorReport;After=$reportBytes})
# Keep existing ownership records aligned with the small set of edited files.
$runtimePath=Join-Path $target 'RUNTIME-FILES.json'
if(Test-Path -LiteralPath $runtimePath){
 $runtime=Read-PatchFile $runtimePath;$runtimeData=$runtime.Text | ConvertFrom-Json
 foreach($plan in $plans){$runtimeData | Add-Member -NotePropertyName $plan.Relative -NotePropertyValue (Get-PatchSha $plan.After) -Force}
 [void]$plans.Add([pscustomobject]@{Relative='RUNTIME-FILES.json';Before=$runtime.Bytes;After=(Json-PatchBytes $runtimeData)})
}
$installPath=Join-Path $target 'AUSTRALIS-INSTALL.json'
if(Test-Path -LiteralPath $installPath){
 $install=Read-PatchFile $installPath;$installData=$install.Text | ConvertFrom-Json
 if(!$installData.PSObject.Properties['installed_files']){throw 'Existing install record has no installed_files map.'}
 foreach($plan in $plans){$installData.installed_files | Add-Member -NotePropertyName $plan.Relative -NotePropertyValue (Get-PatchSha $plan.After) -Force}
 $installData | Add-Member -NotePropertyName 'mod_aircraft_patch_version' -NotePropertyValue $patchVersion -Force
 [void]$plans.Add([pscustomobject]@{Relative='AUSTRALIS-INSTALL.json';Before=$install.Bytes;After=(Json-PatchBytes $installData)})
}
if(!$BackupDirectory){$BackupDirectory=Join-Path $game ('_Australis-Aircraft-Backups/'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'-'+[Guid]::NewGuid().ToString('N').Substring(0,8))}
$backup=[IO.Path]::GetFullPath($BackupDirectory);Assert-PatchPath $backup
if($backup.StartsWith($stream+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or $backup -eq $stream){throw 'Backup folder must be outside StreamingAssets.'}
if((Test-Path -LiteralPath $backup) -and @(Get-ChildItem -LiteralPath $backup -Force).Count){throw 'Backup directory must be new or empty.'}
[void][IO.Directory]::CreateDirectory($backup)
$entries=@();$index=0
foreach($plan in $plans){
 $dest=Join-Path $target $plan.Relative;Assert-PatchPath $dest
 $existed=Test-Path -LiteralPath $dest -PathType Leaf
 if($existed -and (Get-PatchSha ([IO.File]::ReadAllBytes($dest))) -ne (Get-PatchSha $plan.Before)){throw ('File changed during planning: '+$plan.Relative)}
 $saved='before-'+$index+'.bin';$originalHash=''
 if($existed){[IO.File]::WriteAllBytes((Join-Path $backup $saved),$plan.Before);$originalHash=Get-PatchSha $plan.Before;if((Get-PatchSha ([IO.File]::ReadAllBytes((Join-Path $backup $saved)))) -ne $originalHash){throw 'Backup verification failed.'}}
 $entries+=[pscustomobject]@{relative_path=$plan.Relative;existed=[bool]$existed;backup_file=$saved;original_sha256=$originalHash;installed_sha256=(Get-PatchSha $plan.After)};$index++
}
$journal=[pscustomobject]@{schema=1;patch_version=$patchVersion;state='Prepared';game_directory=$game;target_directory=$target;files=$entries}
$journalPath=Join-Path $backup 'transaction.json';Save-PatchJournal $journal $journalPath
try {
 $journal.state='Installing';Save-PatchJournal $journal $journalPath
 for($i=0;$i -lt $plans.Count;$i++){
  $plan=$plans[$i];$entry=$entries[$i];$dest=Join-Path $target $plan.Relative
  if($entry.existed){if((Get-PatchSha ([IO.File]::ReadAllBytes($dest))) -ne $entry.original_sha256){throw ('File changed before activation: '+$plan.Relative)}}elseif(Test-Path -LiteralPath $dest){throw ('New target appeared before activation: '+$plan.Relative)}
  Write-PatchAtomic $dest $plan.After
 }
 $journal.state='Installed';Save-PatchJournal $journal $journalPath
} catch {
 $originalError=$_.Exception.Message;$rollbackError=''
 foreach($entry in $entries){
  try {
   $dest=Join-Path $target $entry.relative_path
   if(Test-Path -LiteralPath $dest){
    $current=Get-PatchSha ([IO.File]::ReadAllBytes($dest))
    if($current -eq $entry.installed_sha256){if($entry.existed){Write-PatchAtomic $dest ([IO.File]::ReadAllBytes((Join-Path $backup $entry.backup_file)))}else{[IO.File]::Delete($dest)}}
    elseif(!$entry.existed -or $current -ne $entry.original_sha256){throw ('Unexpected concurrent change: '+$entry.relative_path)}
   }
  } catch {$rollbackError+=$_.Exception.Message+'; '}
 }
 $journal.state='RolledBack';if($rollbackError){$journal.state='RecoveryRequired'}
 Save-PatchJournal $journal $journalPath
 throw ($originalError+'; transaction '+$journal.state+'. Backup: '+$backup+' '+$rollbackError)
}
Write-Host '[100%] Modded aircraft selection list refreshed. Restart Sea Power and place a new Australis in a new mission.'
Write-Host ('[BACKUP] '+$backup)
return [pscustomobject]@{Version=$patchVersion;Mode=$Mode;BackupDirectory=$backup;ChangedFiles=@($entries.relative_path);AddedCount=$addedCount;SupportedCount=$supportedCount;TargetDirectory=$target;GameFilesModified=$true}
