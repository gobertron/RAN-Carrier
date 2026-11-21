function RestoreTransaction([string]$folder,[string]$g,[string]$settings,[switch]$Automatic){
 # Shared helpers are loaded by the clean installer before this function.
 # Restore derives progress from verified bytes so interrupted restores can resume.
 Closed
 $folder=Full $folder;$g=Full $g;$settings=Full $settings
 NoLink $folder;NoLink $g;NoLink $settings
 $journalPath=Join-Path $folder 'transaction.json';NoLink $journalPath
 if(!(Test-Path -LiteralPath $journalPath -PathType Leaf)){throw 'Restore transaction.json was not found.'}
 $record=[IO.File]::ReadAllText($journalPath) | ConvertFrom-Json
 foreach($field in @('schema','version','game','settings_path','state','archives','files','new_inventory')){
  if(!$record.PSObject.Properties[$field]){throw ('Restore journal field is missing: '+$field)}
 }
 if($record.schema -ne 1 -or $record.version -notin @('1.3.0','1.3.1','1.3.2','1.4.0') -or (Full $record.game) -ne $g -or (Full $record.settings_path) -ne $settings){throw 'Restore journal belongs to another game, settings file or installer version.'}
 if($record.state -notin @('Prepared','Archiving','Activating','Installed','Restoring','RecoveryRequired','Restored')){throw ('Transaction cannot be restored from state '+$record.state)}
 $stream=Join-Path $g 'Sea Power_Data/StreamingAssets';NoLink $stream
 if($folder -eq $stream -or $folder.StartsWith($stream+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'Restore archive must be outside StreamingAssets.'}
 $target=Join-Path $stream 'RAN-HMAS-Australis';NoLink $target
 $held=Join-Path $folder 'Held-Test-Build';NoLink $held
 $loaderPattern='^(?:winhttp\.dll|doorstop_config\.ini|\.doorstop_version|BepInEx/(?:core/[^/]+\.(?:dll|xml)|plugins/(?:AnchorChain\.Preloader|SeaPowerKeel\.Stub)\.dll|patchers/SeaPowerKeel\.Patcher\.dll|config/BepInEx\.cfg))$'
 $restoreErrors=New-Object 'System.Collections.Generic.List[string]'
 $restoreConflicts=New-Object 'System.Collections.Generic.List[object]'
 if($record.PSObject.Properties['restore_conflicts']){foreach($item in @($record.restore_conflicts)){[void]$restoreConflicts.Add($item)}}
 $origins=@{};$archiveNames=@{};$filePaths=@{};$backupNames=@{}
 $plans=New-Object 'System.Collections.Generic.List[object]'
 $auxPlans=New-Object 'System.Collections.Generic.List[object]'
 $canonical=$null
 # Inventory names are also untrusted journal data, even after JSON parsing.
 $newRows=@(Entries $record.new_inventory)
 foreach($item in $newRows){
  [void](RelPath $target $item.Name)
  if([string]$item.Value -notmatch '^[a-fA-F0-9]{64}$'){throw 'Invalid new-build inventory hash.'}
 }
 foreach($row in @($record.archives)){
  foreach($field in @('kind','relative','archive_name')){if(!$row.PSObject.Properties[$field]){throw ('Archive journal field is missing: '+$field)}}
  if($row.kind -notin @('directory','file') -or !(ArchivePathAllowed $row.relative) -or $row.archive_name -notmatch '^old-[0-9]+$'){throw 'Unsafe archive restore entry.'}
  $original=Full (RelPath $g $row.relative);$saved=RelPath $folder $row.archive_name
  if($origins.ContainsKey($original) -or $archiveNames.ContainsKey($row.archive_name)){throw 'Repeated archive restore entry.'}
  $origins[$original]=$true;$archiveNames[$row.archive_name]=$true
  if($row.kind -eq 'directory'){
   if(!$row.PSObject.Properties['files']){throw 'Directory archive has no file inventory.'}
   foreach($item in @(Entries $row.files)){
    [void](RelPath $original $item.Name)
    [void](RelPath $saved $item.Name)
    if([string]$item.Value -notmatch '^[a-fA-F0-9]{64}$'){throw 'Invalid directory archive hash.'}
   }
  }elseif(!$row.PSObject.Properties['sha256'] -or [string]$row.sha256 -notmatch '^[a-fA-F0-9]{64}$'){throw 'Invalid file archive hash.'}
  $plan=[pscustomobject]@{Row=$row;Original=$original;Saved=$saved;Archived=(Test-Path -LiteralPath $saved);OriginalPresent=(Test-Path -LiteralPath $original)}
  if($original -eq $target){if($row.kind -ne 'directory'){throw 'Canonical carrier archive must be a directory.'};$canonical=$plan}
  if($plan.Archived){
   if($row.kind -eq 'directory'){
    if(!(Test-Path -LiteralPath $saved -PathType Container)){throw 'Directory archive has become a file.'};Verify $saved $row.files
   }else{
    if(!(Test-Path -LiteralPath $saved -PathType Leaf) -or (Sha $saved) -ne $row.sha256){throw 'File archive verification failed.'}
   }
   if($plan.OriginalPresent -and $original -ne $target){throw ('Restore destination already exists: '+$original)}
  }else{
   if(!$plan.OriginalPresent){throw ('Both original and archive are missing: '+$original)}
   if($row.kind -eq 'directory'){
    if(!(Test-Path -LiteralPath $original -PathType Container)){throw 'Original directory has become a file.'};Verify $original $row.files
   }elseif(!(Test-Path -LiteralPath $original -PathType Leaf) -or (Sha $original) -ne $row.sha256){throw 'Unarchived original file changed.'}
  }
  [void]$plans.Add($plan)
 }
 # Distinct archive paths must not contain each other.
 $originList=@($origins.Keys)
 for($i=0;$i -lt $originList.Count;$i++){for($j=$i+1;$j -lt $originList.Count;$j++){
  if($originList[$i].StartsWith($originList[$j]+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or $originList[$j].StartsWith($originList[$i]+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'Overlapping archive restore destinations.'}
 }}
 $holdTarget=$false;$holdInventory=$record.new_inventory
 $heldInventory=$record.new_inventory
 if($record.PSObject.Properties['held_inventory']){
  $heldInventory=$record.held_inventory
  foreach($item in @(Entries $heldInventory)){[void](RelPath $held $item.Name);if([string]$item.Value -notmatch '^[a-fA-F0-9]{64}$'){throw 'Invalid held-build inventory hash.'}}
 }
 if(Test-Path -LiteralPath $held){if(!(Test-Path -LiteralPath $held -PathType Container)){throw 'Held test build has become a file.'};Verify $held $heldInventory}
 if(Test-Path -LiteralPath $target){
  if($null -eq $canonical -or $canonical.Archived){
   if(!(Test-Path -LiteralPath $target -PathType Container)){throw 'Installed test target has become a file.'}
   if($Automatic){$holdInventory=Inventory $target}else{Verify $target $record.new_inventory}
   if(Test-Path -LiteralPath $held){throw 'Both the active and held test builds exist; restore stopped.'}
   $holdTarget=$true
  }
 }
 foreach($row in @($record.files)){try{
  foreach($field in @('path','existed','old_sha256','new_sha256','backup_name')){if(!$row.PSObject.Properties[$field]){throw ('Auxiliary journal field is missing: '+$field)}}
  if(![IO.Path]::IsPathRooted([string]$row.path)){throw 'Auxiliary restore path must be absolute.'}
  $dest=Full $row.path;NoLink $dest
  $allowed=($dest -eq $settings)
  if($dest.StartsWith($g+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){
   $relative=$dest.Substring($g.Length+1).Replace('\','/');if($relative -match $loaderPattern){$allowed=$true}
  }
  if(!$allowed -or $filePaths.ContainsKey($dest) -or $row.existed -isnot [bool] -or $row.backup_name -notmatch '^file-[0-9]+\.bin$' -or $backupNames.ContainsKey($row.backup_name) -or [string]$row.new_sha256 -notmatch '^[a-fA-F0-9]{64}$'){throw 'Unsafe auxiliary restore entry.'}
  $filePaths[$dest]=$true;$backupNames[$row.backup_name]=$true
  $saved=RelPath $folder $row.backup_name
  if($row.existed){
   if([string]$row.old_sha256 -notmatch '^[a-fA-F0-9]{64}$' -or !(Test-Path -LiteralPath $saved -PathType Leaf) -or (Sha $saved) -ne $row.old_sha256){throw 'Auxiliary backup verification failed.'}
   if(Test-Path -LiteralPath $dest){
    if(!(Test-Path -LiteralPath $dest -PathType Leaf)){throw ('Auxiliary destination is not a file: '+$dest)}
    $current=Sha $dest
    if(!$Automatic -and $current -notin @($row.old_sha256,$row.new_sha256)){throw ('Auxiliary file changed after installation: '+$dest)}
   }elseif(!$Automatic){throw ('Original auxiliary file is missing: '+$dest)}
  }else{
   if([string]$row.old_sha256){throw 'New auxiliary file has an unexpected original hash.'}
   if(Test-Path -LiteralPath $dest){if(!(Test-Path -LiteralPath $dest -PathType Leaf) -or (!$Automatic -and (Sha $dest) -ne $row.new_sha256)){throw ('New auxiliary file changed after installation: '+$dest)}}
  }
  [void]$auxPlans.Add([pscustomobject]@{Row=$row;Destination=$dest;Saved=$saved})
 }catch{
  if(!$Automatic){throw}
  [void]$restoreErrors.Add('Auxiliary preflight: '+$_.Exception.Message)
 }}
 if($record.state -eq 'Restored' -and !$Automatic){
  foreach($plan in $plans){if($plan.Archived){throw 'Restored journal still contains archived originals.'}}
  foreach($plan in $auxPlans){if($plan.Row.existed){if((Sha $plan.Destination) -ne $plan.Row.old_sha256){throw 'Restored auxiliary file no longer matches its original.'}}elseif(Test-Path -LiteralPath $plan.Destination){throw 'Restored transaction still has a new auxiliary file.'}}
  if($holdTarget){throw 'Restored journal still has an active test build.'}
  Say '[RESTORED] Previous CVN installation was already restored and verified.'
  return [pscustomobject]@{State='Restored';ArchiveDirectory=$folder;TargetDirectory=$target}
 }
 # All inputs have passed. Recheck each operand immediately before its mutation.
 Closed
 $record.state='Restoring';Json $journalPath $record
 if($holdTarget){
  NoLink $held;NoLink $target
  if(Test-Path -LiteralPath $held){throw 'Held test destination appeared during restore.'}
  if($Automatic){$record | Add-Member -NotePropertyName 'held_inventory' -NotePropertyValue $holdInventory -Force;Json $journalPath $record}
  Verify $target $holdInventory
  Move-Item -LiteralPath $target -Destination $held -ErrorAction Stop
  Verify $held $holdInventory
 }
 foreach($plan in $plans){try{
  $row=$plan.Row;NoLink $plan.Original;NoLink $plan.Saved
  if(Test-Path -LiteralPath $plan.Saved){
   if(Test-Path -LiteralPath $plan.Original){throw ('Restore destination appeared during restore: '+$plan.Original)}
   if($row.kind -eq 'directory'){Verify $plan.Saved $row.files}else{if((Sha $plan.Saved) -ne $row.sha256){throw 'File archive changed during restore.'}}
   [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($plan.Original))
   Move-Item -LiteralPath $plan.Saved -Destination $plan.Original -ErrorAction Stop
  }
  if($row.kind -eq 'directory'){Verify $plan.Original $row.files}else{if(!(Test-Path -LiteralPath $plan.Original -PathType Leaf) -or (Sha $plan.Original) -ne $row.sha256){throw 'Original file restore verification failed.'}}
 }catch{
  if(!$Automatic){throw}
  [void]$restoreErrors.Add('Original CVN restore: '+$_.Exception.Message)
 }}
 foreach($plan in $auxPlans){try{
  $row=$plan.Row;$dest=$plan.Destination;NoLink $dest;NoLink $plan.Saved
  $present=Test-Path -LiteralPath $dest;$current=''
  if($present){if(!(Test-Path -LiteralPath $dest -PathType Leaf)){throw 'Auxiliary destination is no longer a file.'};$current=Sha $dest}
  $expected=@($row.new_sha256);if($row.existed){$expected+=,$row.old_sha256}
  if($present -and $current -notin $expected){
   if(!$Automatic){throw 'Auxiliary file changed during restore.'}
   # An automatic rollback must not abandon the carrier folders over a torn
   # auxiliary write. Keep the unexpected bytes before restoring the original.
   $conflictRoot=Join-Path $folder 'Conflicts';NoLink $conflictRoot
   [void][IO.Directory]::CreateDirectory($conflictRoot)
   $conflict=Join-Path $conflictRoot ('aux-'+[guid]::NewGuid().ToString('N')+'.bin');NoLink $conflict
   Copy-Item -LiteralPath $dest -Destination $conflict -ErrorAction Stop
   if((Sha $conflict) -ne $current -or (Sha $dest) -ne $current){throw 'Conflicting auxiliary bytes changed during preservation.'}
   [void]$restoreConflicts.Add([pscustomobject]@{path=$dest;sha256=$current;backup_path=$conflict})
   $record | Add-Member -NotePropertyName 'restore_conflicts' -NotePropertyValue $restoreConflicts.ToArray() -Force
   Json $journalPath $record
   Say ('[ROLLBACK CONFLICT SAVED] '+$conflict)
  }
  if($row.existed){
   if(!$present -and !$Automatic){throw 'Auxiliary file disappeared during restore.'}
   if(!$present -or $current -ne $row.old_sha256){
    if((Sha $plan.Saved) -ne $row.old_sha256){throw 'Auxiliary backup changed during restore.'}
    if($present){if((Sha $dest) -ne $current){throw 'Auxiliary file changed before restore write.'}}elseif(Test-Path -LiteralPath $dest){throw 'Auxiliary destination appeared before restore write.'}
    Atomic $dest ([IO.File]::ReadAllBytes($plan.Saved))
   }
   if((Sha $dest) -ne $row.old_sha256){throw 'Auxiliary restore verification failed.'}
  }elseif($present){
   if((Sha $dest) -ne $current){throw 'New auxiliary file changed before restore removal.'}
   [IO.File]::Delete($dest)
  }
 }catch{
  if(!$Automatic){throw}
  [void]$restoreErrors.Add('Auxiliary restore: '+$_.Exception.Message)
 }}
 if($restoreErrors.Count){
  $record.state='RecoveryRequired';$record | Add-Member -NotePropertyName 'restore_errors' -NotePropertyValue $restoreErrors.ToArray() -Force;Json $journalPath $record
  Say '[RESTORE PARTIAL] Original CVN folders were restored where possible; additional recovery remains necessary.'
  throw ('Automatic restoration needs recovery: '+($restoreErrors.ToArray() -join '; '))
 }
 if($record.PSObject.Properties['restore_errors']){$record.PSObject.Properties.Remove('restore_errors')}
 $record.state='Restored';Json $journalPath $record
 Say '[RESTORED] Previous CVN folders, settings and loader were restored and verified.'
 return [pscustomobject]@{State='Restored';ArchiveDirectory=$folder;TargetDirectory=$target}
}
