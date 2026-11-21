#requires -Version 5.1
[CmdletBinding()]
param([string]$GameDirectory='', [string]$LoadOrderPath='',
 [ValidateSet('Install','Check','Restore')][string]$Mode='Install',
 [string]$RestoreDirectory='', [string]$PackagePath='', [string]$LogDirectory='')
$ErrorActionPreference='Stop';Set-StrictMode -Version 2
if(!$PackagePath){$PackagePath=$PSScriptRoot}
$script:utf8=New-Object Text.UTF8Encoding($false,$true)
$script:lines=New-Object 'System.Collections.Generic.List[string]'
. (Join-Path $PackagePath 'Helpers/Cvn-Helpers.ps1')
. (Join-Path $PackagePath 'Helpers/Restore-Cvn.ps1')
$result=[ordered]@{version='1.4.0';mode=$Mode;status='Preparing';game_tested=$false}
$journal=$null;$journalPath='';$lock=$null;$stageRoot='';$game='';$logStem=''
try{
 if(!$LogDirectory){if($env:LOCALAPPDATA){$LogDirectory=Join-Path $env:LOCALAPPDATA 'RAN-Australis/Logs'}else{$LogDirectory=Join-Path ([IO.Path]::GetDirectoryName((Full $PackagePath))) 'cvn-logs'}}
 NoLink $LogDirectory;[void][IO.Directory]::CreateDirectory($LogDirectory)
 $logStem=Join-Path $LogDirectory ('Australis-v1.4.0-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'-'+[guid]::NewGuid().ToString('N').Substring(0,8))
 Say '[0%] RAN / HMAS Australis v1.4.0 - carrier repair and update'
 Closed;$game=FindGame $GameDirectory;$result.game=$game
 if(!$LoadOrderPath){$LoadOrderPath=Join-Path ([Environment]::GetFolderPath('UserProfile')) 'AppData/LocalLow/Triassic Games/Sea Power/usersettings.ini'}
 $LoadOrderPath=Full $LoadOrderPath;NoLink $LoadOrderPath
 if(!(Test-Path -LiteralPath $LoadOrderPath -PathType Leaf)){throw ('Mod Manager settings not found: '+$LoadOrderPath+'. Start Sea Power once, open Mod Manager, exit, and rerun.')}
 $stream=Join-Path $game 'Sea Power_Data/StreamingAssets';NoLink $stream
 $cvnWorkRoot=Join-Path $game '_Australis-CVN-v1.3.0';NoLink $cvnWorkRoot
 if($Mode -eq 'Restore'){
  if(!$RestoreDirectory){throw 'Restore needs the timestamped archive path as the third CMD argument.'}
  [void][IO.Directory]::CreateDirectory($cvnWorkRoot);$lock=[IO.File]::Open((Join-Path $cvnWorkRoot 'operation.lock'),[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
  RestoreTransaction $RestoreDirectory $game $LoadOrderPath;$result.status='Restored';return
 }
 $package=Full $PackagePath;NoLink $package
 $manifest=[IO.File]::ReadAllText((Join-Path $package 'PACKAGE-MANIFEST.json')) | ConvertFrom-Json
 if($manifest.schema -ne 1 -or $manifest.version -ne '1.4.0'){throw 'Wrong or incomplete test package.'}
 foreach($r in @(Entries $manifest.files)){if($r.Value -notmatch '^[a-f0-9]{64}$' -or (Sha (RelPath $package $r.Name)) -ne $r.Value){throw ('Package verification failed: '+$r.Name)}}
 . (Join-Path $package 'Helpers/Mod-Aircraft-Catalog.ps1')
 . (Join-Path $package 'Helpers/Full-Rebuild-Airwing.ps1')
 . (Join-Path $package 'Helpers/Keel-Dependency.ps1')
 Say '[10%] Complete package and controller hashes verified.'
 $payloadSignature=PayloadSignature $manifest
 if(!(SingleClass (Join-Path $package 'payload'))){throw 'Package must contain one canonical Australis class with its existing sister-ship variants.'}
 $target=Join-Path $stream 'RAN-HMAS-Australis';$old=@();$localNames=@{};$sources=@();$source=''
 foreach($dir in @(Get-ChildItem -LiteralPath $stream -Directory -Force)){
  if($dir.Name -in @('original','user')){continue}
  if(CarrierRoot $dir.FullName){PureCarrier $dir.FullName;NoLink $dir.FullName;$localNames[$dir.Name]=$true
   $old+=,[ordered]@{kind='directory';relative=('Sea Power_Data/StreamingAssets/'+$dir.Name);archive_name=('old-'+$old.Count);files=(Inventory $dir.FullName);sha256=''}
   $obj=Join-Path $dir.FullName 'ships/ran_cvn_australis_2030/ran_cvn_australis_2030.obj';$dll=Join-Path $dir.FullName 'RAN.Australis.DeckController.dll'
   if((Test-Path -LiteralPath $obj) -and (Test-Path -LiteralPath $dll) -and (Sha $obj) -in @($manifest.audited_model_sha256) -and (Sha $dll) -in @($manifest.audited_controller_sha256)){$sources+=,$dir}
  }
 }
 if($sources.Count){$source=(@($sources | Sort-Object @{Expression={$_.Name -ne 'RAN-HMAS-Australis'}},@{Expression={$_.LastWriteTimeUtc};Descending=$true})[0]).FullName}
 if((Test-Path -LiteralPath $target) -and !$localNames.ContainsKey('RAN-HMAS-Australis')){throw 'The target folder contains unrecognised content and was preserved.'}
 # Retire loose historical CVN assets without moving the shared user directory.
 $userVessels=Join-Path $stream 'user/vessels'
 if(Test-Path -LiteralPath $userVessels){NoLink $userVessels;foreach($f in @(Get-ChildItem -LiteralPath $userVessels -File -Filter '*.ini')){
  if($f.BaseName -notmatch '^(?:ran_cvn_(?:australis|southern_cross|federation|commonwealth)_|ran_australis_(?:basic_shell|flightdeck_stage1|stage1_c[1-4]_test)(?:_variants)?$)'){continue}
  if($f.BaseName -notmatch '^(?:ran_cvn_australis_|ran_australis_(?:basic_shell|flightdeck_stage1|stage1_c[1-4]_test))' -and [IO.File]::ReadAllText($f.FullName) -notmatch 'ran_cvn_australis_'){continue}
  NoLink $f.FullName;$old+=,[ordered]@{kind='file';relative=('Sea Power_Data/StreamingAssets/user/vessels/'+$f.Name);archive_name=('old-'+$old.Count);files=@{};sha256=(Sha $f.FullName)}
 }}
 $looseShips=Join-Path $stream 'user/ships'
 if(Test-Path -LiteralPath $looseShips){NoLink $looseShips;foreach($dir in @(Get-ChildItem -LiteralPath $looseShips -Directory | Where-Object {$_.Name -match '^(?:ran_cvn_australis_[A-Za-z0-9_.-]+|ran_australis_(?:basic_shell|flightdeck_stage1))$'})){$old+=,[ordered]@{kind='directory';relative=('Sea Power_Data/StreamingAssets/user/ships/'+$dir.Name);archive_name=('old-'+$old.Count);files=(Inventory $dir.FullName);sha256=''}}}
 foreach($anim in @('ran_australis_stage1_jbd.ini','ran_australis_stage1_lifts.ini')){$ap=Join-Path $stream ('user/animations/'+$anim);if(Test-Path -LiteralPath $ap){NoLink $ap;$old+=,[ordered]@{kind='file';relative=('Sea Power_Data/StreamingAssets/user/animations/'+$anim);archive_name=('old-'+$old.Count);files=@{};sha256=(Sha $ap)}}}
 $looseDll=Join-Path $stream 'user/RAN.Australis.DeckController.dll'
 if(Test-Path -LiteralPath $looseDll){NoLink $looseDll;$old+=,[ordered]@{kind='file';relative='Sea Power_Data/StreamingAssets/user/RAN.Australis.DeckController.dll';archive_name=('old-'+$old.Count);files=@{};sha256=(Sha $looseDll)}}
 $legacyPlugin=Join-Path $game 'BepInEx/plugins/RAN.Australis.DeckController.dll'
 if(Test-Path -LiteralPath $legacyPlugin){NoLink $legacyPlugin;$old+=,[ordered]@{kind='file';relative='BepInEx/plugins/RAN.Australis.DeckController.dll';archive_name=('old-'+$old.Count);files=@{};sha256=(Sha $legacyPlugin)}}
 $assembly=Join-Path $game 'Sea Power_Data/Managed/Seapower-Scripts.dll';NoLink $assembly;$gameHash=Sha $assembly;$result.game_assembly_sha256=$gameHash
 if($gameHash -in @($manifest.supported_game_assembly_sha256)){$result.compatibility_basis='Previously audited game assembly'}elseif($source){$result.compatibility_basis='Existing audited full-carrier upgrade, following the later updater policy';Say '[NOTE] Existing full carrier recognised. This is a test upgrade; this game assembly still needs an in-game compatibility check.'}else{throw ('Fresh installation refused for an unaudited game assembly: '+$gameHash+'. No old CVN content was moved. An existing audited full carrier or current assembly evidence is required.')}
 $result.source=$source
 $settingsHash=Sha $LoadOrderPath;$settingsText=[IO.File]::ReadAllText($LoadOrderPath);$parsed=ParseSettings $settingsText
 $workshopIds=@{};$workshopRoots=@(Get-AustralisCatalogWorkshopRoots $game)
 foreach($root in $workshopRoots){if(!(Test-Path -LiteralPath $root)){continue};NoLink $root;foreach($dir in @(Get-ChildItem -LiteralPath $root -Directory -Force)){if($dir.Name -match '^[0-9]+$' -and (CarrierRoot $dir.FullName)){PureCarrier $dir.FullName;$workshopIds[$dir.Name]=$true;Say ('[WORKSHOP] Duplicate CVN will be disabled: '+$dir.Name)}}}
 $catalogRows=@();$installRows=@()
 foreach($row in $parsed.Rows){
  $isOld=$localNames.ContainsKey($row.Directory) -or $workshopIds.ContainsKey($row.WorkshopId) -or $row.Directory -match '^(?i:RAN[-_ ](?:HMAS[-_ ])?Australis|HMAS[-_ ]Australis|Australis[-_ ](?:Full|Basic|Stage|Workshop|v[0-9]))' -or $row.WorkshopId -eq '3832163513'
  if($isOld){$disabled=[pscustomobject]@{Directory=$row.Directory;Enabled=$false;WorkshopId=$row.WorkshopId};$catalogRows+=,$disabled;if(!($row.WorkshopId -eq '0' -and $row.Directory -ieq 'RAN-HMAS-Australis')){$installRows+=,$disabled}}
  else{$catalogRows+=,$row;$installRows+=,$row}
 }
 $installRows+=,[pscustomobject]@{Directory='RAN-HMAS-Australis';Enabled=$true;WorkshopId='0'}
 $newSettings=SettingsText $settingsText $parsed $installRows
 $scratch=Join-Path ([IO.Path]::GetTempPath()) ('Australis-catalog-'+[guid]::NewGuid().ToString('N')+'.ini')
 try{[IO.File]::WriteAllText($scratch,(SettingsText $settingsText $parsed $catalogRows),$script:utf8);$catalog=Get-AustralisModAircraftCatalog -GameDirectory $game -LoadOrderPath $scratch}finally{if(Test-Path -LiteralPath $scratch){[IO.File]::Delete($scratch)}}
 $catalogSignature=CatalogSignature $catalog
 $result.aircraft_catalog_sha256=$catalogSignature;$result.payload_sha256=$payloadSignature
 $result.aircraft_count=@($catalog.SupportedIds).Count;$result.disabled_aircraft_mods=@($catalog.DisabledMods);$result.archive_items=$old.Count;$result.disabled_workshop_cvn_ids=@($workshopIds.Keys)
 Say ('[25%] Found '+$old.Count+' old CVN items; '+$catalog.SupportedIds.Count+' installed, enabled aircraft IDs.')
 $keelDependency=Get-AustralisKeelDependency -GameDirectory $game -Rows $parsed.Rows -WorkshopRoots $workshopRoots -Manifest $manifest
 $result.loader='Keel';$result.keel=[ordered]@{root=$keelDependency.Root;installed_version=$keelDependency.InstalledVersion;tested_version=$keelDependency.TestedVersion;core_sha256=$keelDependency.CoreSha256;compatibility_library_sha256=$keelDependency.CompatibilityLibrarySha256;stub_sha256=$keelDependency.StubSha256;patcher_sha256=$keelDependency.PatcherSha256;runtime_verified=$false}
 $result.dependency_sha256=$keelDependency.DependencySignature
 $filePlans=@($keelDependency.Plans)
 Say ('[KEEL] Verified installed version '+$keelDependency.InstalledVersion+' against the '+$keelDependency.TestedVersion+' compatibility contract. Missing starter/patcher files to add: '+$filePlans.Count+'. Existing loader files are preserved.')
 # Repeat installations exit without touching game files when the complete current
 # payload, dynamic catalogue, dependency plan and final load order are unchanged.
 $receiptPath=Join-Path $target 'AUSTRALIS-INSTALL.json'
 if((SingleClass $target) -and $old.Count -eq 1 -and $old[0].relative -eq 'Sea Power_Data/StreamingAssets/RAN-HMAS-Australis' -and $filePlans.Count -eq 0 -and $newSettings -ceq $settingsText -and (Test-Path -LiteralPath $receiptPath -PathType Leaf)){
  $intact=$false
  try{
   NoLink $receiptPath;$receipt=[IO.File]::ReadAllText($receiptPath) | ConvertFrom-Json
   if($receipt.schema -eq 1 -and $receipt.ship_id -eq 'ran_cvn_australis_2030' -and $receipt.version -eq '1.4.0' -and $receipt.loader -eq 'Keel' -and $receipt.dependency_sha256 -eq $keelDependency.DependencySignature -and $receipt.game_assembly_sha256 -eq $gameHash -and $receipt.payload_sha256 -eq $payloadSignature -and $receipt.aircraft_catalog_sha256 -eq $catalogSignature){
    $actual=Inventory $target;[void]$actual.Remove('AUSTRALIS-INSTALL.json');$expected=@(Entries $receipt.installed_files)
    $intact=($actual.Count -eq $expected.Count)
    foreach($item in $expected){[void](RelPath $target $item.Name);if(!$actual.ContainsKey($item.Name) -or $actual[$item.Name] -ne $item.Value){$intact=$false;break}}
    foreach($item in @(Entries $manifest.files | Where-Object {$_.Name.StartsWith('payload/') -and $_.Name -notin @('payload/RUNTIME-FILES.json','payload/vessels/ran_cvn_australis_2030.ini')})){if(!$actual.ContainsKey($item.Name.Substring(8)) -or $actual[$item.Name.Substring(8)] -ne $item.Value){$intact=$false;break}}
   }
  }catch{$intact=$false;Say ('[REPAIR] Installed receipt or file check requires a staged refresh: '+$_.Exception.Message)}
  if($intact){$result.status='AlreadyInstalled';$result.target=$target;Say '[100%] RAN / HMAS Australis v1.4.0 is already installed and intact. No game files changed.';return}
 }
 $settingBytes=$script:utf8.GetBytes($newSettings);$h=[Security.Cryptography.SHA256]::Create();try{$newSettingsHash=([BitConverter]::ToString($h.ComputeHash($settingBytes))).Replace('-','').ToLowerInvariant()}finally{$h.Dispose()}
 $filePlans+=,[ordered]@{path=$LoadOrderPath;source='';bytes=$settingBytes;existed=$true;old_sha256=$settingsHash;new_sha256=$newSettingsHash;backup_name=('file-'+$filePlans.Count+'.bin')}
 Say '[40%] Preflight passed. Other ship and aircraft mods retain their settings.'
 if($Mode -eq 'Check'){$result.status='Checked';Say '[100%] Read-only preflight passed. No active game files changed.';return}
 [void][IO.Directory]::CreateDirectory($cvnWorkRoot);$lock=[IO.File]::Open((Join-Path $cvnWorkRoot 'operation.lock'),[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
 $archiveRoot=Join-Path $cvnWorkRoot 'Archives';NoLink $archiveRoot
 if(Test-Path -LiteralPath $archiveRoot){foreach($folder in @(Get-ChildItem -LiteralPath $archiveRoot -Directory)){NoLink $folder.FullName;$jp=Join-Path $folder.FullName 'transaction.json';if(Test-Path -LiteralPath $jp){$prior=[IO.File]::ReadAllText($jp) | ConvertFrom-Json;if($prior.state -notin @('Installed','Restored','RolledBack','Prepared')){throw ('Interrupted installation needs Restore first: '+$folder.FullName)}}}}
 $id=(Get-Date -Format 'yyyyMMdd-HHmmss')+'-'+[guid]::NewGuid().ToString('N').Substring(0,8)
 $archive=Join-Path $archiveRoot $id;$stageRoot=Join-Path $cvnWorkRoot ('Staging/'+$id);$stage=Join-Path $stageRoot 'RAN-HMAS-Australis'
 [void][IO.Directory]::CreateDirectory($stageRoot);Copy-Item -LiteralPath (Join-Path $package 'payload') -Destination $stage -Recurse
 foreach($f in @(Get-ChildItem -LiteralPath (Join-Path $stage 'vessels') -File -Filter 'ran_cvn_*.ini' | Where-Object {$_.BaseName -notmatch '_variants$'})){
  $text=[IO.File]::ReadAllText($f.FullName);$sourceFile='';if($source){$sourceFile=Join-Path $source ('vessels/'+$f.Name)}
  $preserved=$false
  if($sourceFile -and (Test-Path -LiteralPath $sourceFile)){
   $oldIni=Get-AustralisFullAirwingIni ([IO.File]::ReadAllText($sourceFile))
   if($oldIni.ContainsKey('AirGroup') -and $oldIni['AirGroup'].Values.Count){
    $text=Set-AustralisFullAirwingSection $text 'AirGroup' $oldIni['AirGroup'].Raw
    foreach($aid in $oldIni['AirGroup'].Values.Keys){if($aid -notin @($catalog.SupportedIds)){throw ('An embarked aircraft mod is disabled or missing: '+$aid)};if($oldIni.ContainsKey($aid)){$text=Set-AustralisFullAirwingSection $text $aid $oldIni[$aid].Raw}}
    $preserved=$true
   }
  }
  if(!$preserved){$wing=New-AustralisFullAirwing -GameDirectory $game -VesselText $text -AirwingProfile 'Full99';if(!$wing.Configured){throw ('Could not build a valid native air wing: '+$wing.Report.reason)};$text=$wing.Text}
  $patched=Get-AustralisModAircraftPatch -VesselText $text -SupportedIds $catalog.SupportedIds
  [void](Assert-AustralisFullFlightContract -VesselText $patched);[IO.File]::WriteAllText($f.FullName,$patched,$script:utf8)
 }
 Json (Join-Path $stage 'AUSTRALIS-AIRCRAFT-COMPATIBILITY.json') ([ordered]@{version='1.4.0';catalog=$catalog;selection_only=$true;launch_landing_tested=$false})
 $runtime=Inventory $stage;$runtime.Remove('RUNTIME-FILES.json');$runtime.Remove('AUSTRALIS-INSTALL.json');Json (Join-Path $stage 'RUNTIME-FILES.json') $runtime
 $owned=Inventory $stage;$owned.Remove('AUSTRALIS-INSTALL.json');Json (Join-Path $stage 'AUSTRALIS-INSTALL.json') ([ordered]@{schema=1;ship_id='ran_cvn_australis_2030';version='1.4.0';installed_files=$owned;loader='Keel';dependency_sha256=$keelDependency.DependencySignature;payload_sha256=$payloadSignature;aircraft_catalog_sha256=$catalogSignature;game_assembly_sha256=$gameHash;compatibility_basis=$result.compatibility_basis})
 $newInventory=Inventory $stage
 foreach($r in @(Entries $manifest.files | Where-Object {$_.Name.StartsWith('payload/ships/')})){if((Sha (RelPath $stage $r.Name.Substring(8))) -ne $r.Value){throw ('Staged geometry differs: '+$r.Name)}}
 [void][IO.Directory]::CreateDirectory($archive)
 foreach($plan in $filePlans){NoLink $plan.path;if($plan.existed){if((Sha $plan.path) -ne $plan.old_sha256){throw 'An input file changed during preparation.'};Copy-Item -LiteralPath $plan.path -Destination (Join-Path $archive $plan.backup_name);if((Sha (Join-Path $archive $plan.backup_name)) -ne $plan.old_sha256){throw 'Backup failed verification.'}}elseif(Test-Path -LiteralPath $plan.path){throw 'A loader destination appeared during preparation.'}}
 $journal=[ordered]@{schema=1;version='1.4.0';state='Prepared';game=$game;settings_path=$LoadOrderPath;archives=$old;files=@($filePlans | ForEach-Object {[ordered]@{path=$_.path;existed=$_.existed;old_sha256=$_.old_sha256;new_sha256=$_.new_sha256;backup_name=$_.backup_name}});new_inventory=$newInventory}
 $journalPath=Join-Path $archive 'transaction.json';Json $journalPath $journal;$result.archive=$archive
 Say ('[60%] Staged carrier verified. Rollback archive: '+$archive)
 Closed;Assert-AustralisKeelDependencyUnchanged $keelDependency;$journal.state='Archiving';Json $journalPath $journal
 foreach($row in $old){$original=RelPath $game $row.relative;if($row.kind -eq 'directory'){Verify $original $row.files}else{if((Sha $original) -ne $row.sha256){throw 'Old CVN changed before archiving.'}};Move-Item -LiteralPath $original -Destination (Join-Path $archive $row.archive_name)}
 $journal.state='Activating';Json $journalPath $journal
 foreach($plan in $filePlans){if($plan.existed){if((Sha $plan.path) -ne $plan.old_sha256){throw 'Loader/settings changed before activation.'}}elseif(Test-Path -LiteralPath $plan.path){throw 'A new destination became occupied before activation.'};$bytes=$plan.bytes;if($null -eq $bytes){$bytes=[IO.File]::ReadAllBytes($plan.source)};Atomic $plan.path $bytes;if((Sha $plan.path) -ne $plan.new_sha256){throw 'Post-write loader/settings hash mismatch.'}}
 Move-Item -LiteralPath $stage -Destination $target;Verify $target $newInventory
 $remaining=@(Get-ChildItem -LiteralPath $stream -Directory -Force | Where-Object {CarrierRoot $_.FullName})
 if($remaining.Count -ne 1 -or $remaining[0].FullName -ne $target -or !(SingleClass $target)){throw 'More than one local Australis carrier remains active.'}
 $actualSettings=ParseSettings ([IO.File]::ReadAllText($LoadOrderPath));$enabledCvn=@($actualSettings.Rows | Where-Object {$_.Enabled -and ($_.Directory -ieq 'RAN-HMAS-Australis' -or $localNames.ContainsKey($_.Directory) -or $workshopIds.ContainsKey($_.WorkshopId) -or $_.WorkshopId -eq '3832163513')})
 if($enabledCvn.Count -ne 1 -or $enabledCvn[0].Directory -ine 'RAN-HMAS-Australis'){throw 'Final active CVN settings check failed.'}
 $journal.state='Installed';Json $journalPath $journal;$result.status='Installed';$result.target=$target
 Say '[100%] Installed RAN / HMAS Australis v1.4.0. One Australis class with four sister ships is enabled.'
 Say '[NEXT] Restart Sea Power. Press Ctrl+Shift+K and confirm Australis is running under Keel, then test a NEW 2030 mission.'
 Say '[KEEL] If Keel requests one more restart during loader takeover, restart again. Keep its report if Australis does not start.'
 Say '[AIRCRAFT] Enabled modded aircraft are listed; launch/landing compatibility requires testing.'
 Say ('[RESTORE] Run this same CMD with your game folder, Restore, and "'+$archive+'" as its three arguments.')
}catch{
 $failure=$_.Exception.Message;$result.status='Failed';$result.error=$failure;$result.position=$_.InvocationInfo.PositionMessage;$result.stack=$_.ScriptStackTrace
 if($null -ne $journal -and $journal.state -in @('Archiving','Activating')){
  try{RestoreTransaction ([IO.Path]::GetDirectoryName($journalPath)) $game $LoadOrderPath -Automatic;Say '[ROLLBACK] Previous CVN installation restored.'}catch{$rollbackFailure=$_.Exception.Message;$result.rollback_error=$rollbackFailure;try{if(Test-Path -LiteralPath $journalPath){$journal=[IO.File]::ReadAllText($journalPath) | ConvertFrom-Json};$journal.state='RecoveryRequired';Json $journalPath $journal}catch{$result.rollback_journal_error=$_.Exception.Message};Say ('[RECOVERY REQUIRED] '+$rollbackFailure)}
 }
 Say ('[FAILED] '+$failure);throw
}finally{
 if($lock){$lock.Dispose()}
 if($stageRoot -and (Test-Path -LiteralPath $stageRoot)){try{Remove-Item -LiteralPath $stageRoot -Recurse -Force}catch{Say ('[NOTE] Temporary staging retained: '+$stageRoot)}}
 if($logStem){try{[IO.File]::WriteAllText(($logStem+'.log'),(($script:lines.ToArray() -join "`r`n")+"`r`n"),$script:utf8);Json ($logStem+'.json') $result;Write-Host ('[LOG] '+$logStem+'.log');Write-Host ('[REPORT] '+$logStem+'.json')}catch{Write-Host ('[LOG SAVE FAILED] '+$_.Exception.Message)}}
}
