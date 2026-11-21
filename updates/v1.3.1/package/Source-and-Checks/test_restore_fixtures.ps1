$ErrorActionPreference='Stop'
Set-StrictMode -Version 2
$script:lines=New-Object 'System.Collections.Generic.List[string]'
$script:utf8=New-Object Text.UTF8Encoding($false)
. "$PSScriptRoot/Cvn-Helpers.ps1"
. "$PSScriptRoot/Restore-Cvn.ps1"
$root=Join-Path $PSScriptRoot ('restore-fixtures-'+[guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($root)
$passed=New-Object 'System.Collections.Generic.List[string]'
function Put([string]$p,[string]$s){[void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($p));[IO.File]::WriteAllText($p,$s)}
function Fixture([string]$name){
 $g=Join-Path $root $name;$stream=Join-Path $g 'Sea Power_Data/StreamingAssets';[void][IO.Directory]::CreateDirectory($stream)
 $folder=Join-Path $g '_Australis-Archives/test';[void][IO.Directory]::CreateDirectory($folder)
 $settings=Join-Path $g 'usersettings.ini';Put $settings 'settings old'
 $target=Join-Path $stream 'RAN-HMAS-Australis'
 $r=[ordered]@{schema=1;version='1.3.0';game=$g;settings_path=$settings;state='Prepared';archives=@();files=@();new_inventory=@{}}
 return [pscustomobject]@{G=$g;Stream=$stream;Folder=$folder;Settings=$settings;Target=$target;R=$r}
}
function Save($f){Json (Join-Path $f.Folder 'transaction.json') $f.R}
function Assert([bool]$v,[string]$s){if(!$v){throw $s}}
function OldDirectory($f,[string]$name,[string]$slot,[bool]$archived){
 $p=Join-Path $f.Stream $name;Put (Join-Path $p 'vessels/ran_cvn_australis_2030.ini') 'original CVN';$inv=Inventory $p
 $f.R.archives+=@{kind='directory';relative=('Sea Power_Data/StreamingAssets/'+$name);archive_name=$slot;files=$inv}
 if($archived){Move-Item -LiteralPath $p -Destination (Join-Path $f.Folder $slot)}
}
function NewBuild($f){Put (Join-Path $f.Target 'vessels/ran_cvn_australis_2030.ini') 'new CVN';Put (Join-Path $f.Target 'VERSION') '1.3.0';$f.R.new_inventory=Inventory $f.Target}
function Aux($f,[bool]$existing){
 $old='';if($existing){$old=Sha $f.Settings;Copy-Item -LiteralPath $f.Settings -Destination (Join-Path $f.Folder 'file-0.bin')}else{Remove-Item -LiteralPath $f.Settings}
 Put $f.Settings 'settings new'
 $f.R.files+=@{path=$f.Settings;existed=$existing;old_sha256=$old;new_sha256=(Sha $f.Settings);backup_name='file-0.bin'}
}
try {
 $f=Fixture 'empty';Save $f;[void](RestoreTransaction $f.Folder $f.G $f.Settings);Assert ((Get-Content (Join-Path $f.Folder 'transaction.json') -Raw | ConvertFrom-Json).state -eq 'Restored') 'empty restore failed';$passed.Add('Empty Prepared transaction')
 $f=Fixture 'installed';OldDirectory $f 'RAN-HMAS-Australis' 'old-0' $true;OldDirectory $f 'Australis-Older' 'old-1' $true;NewBuild $f;Aux $f $true;$f.R.state='Installed';Save $f
 [void](RestoreTransaction $f.Folder $f.G $f.Settings);Assert ([IO.File]::ReadAllText((Join-Path $f.Target 'vessels/ran_cvn_australis_2030.ini')) -eq 'original CVN') 'canonical original not restored';Assert ([IO.File]::ReadAllText($f.Settings) -eq 'settings old') 'settings not restored';Assert (Test-Path (Join-Path $f.Folder 'Held-Test-Build/VERSION')) 'new build not held';[void](RestoreTransaction $f.Folder $f.G $f.Settings);$passed.Add('Installed restore plus idempotent rerun')
 $f=Fixture 'partial-archive';OldDirectory $f 'RAN-HMAS-Australis' 'old-0' $false;OldDirectory $f 'Australis-Older' 'old-1' $true;$f.R.state='Archiving';Save $f;[void](RestoreTransaction $f.Folder $f.G $f.Settings);Assert (Test-Path (Join-Path $f.Stream 'Australis-Older')) 'partial archive original missing';$passed.Add('Partial Archiving with unarchived canonical')
 $f=Fixture 'partial-activate';OldDirectory $f 'RAN-HMAS-Australis' 'old-0' $true;Aux $f $true;$f.R.state='Activating';Save $f;[void](RestoreTransaction $f.Folder $f.G $f.Settings);Assert (Test-Path $f.Target) 'partial activation original missing';$passed.Add('Partial Activating before new target exists')
 $f=Fixture 'first-install';NewBuild $f;Aux $f $false;$f.R.state='Installed';Save $f;[void](RestoreTransaction $f.Folder $f.G $f.Settings);Assert (!(Test-Path $f.Target)) 'new-only target remains';Assert (!(Test-Path $f.Settings)) 'new-only settings remains';$passed.Add('New-only install removed reversibly')
 $f=Fixture 'concurrent-settings';OldDirectory $f 'RAN-HMAS-Australis' 'old-0' $true;NewBuild $f;Aux $f $true;Put $f.Settings 'concurrent user edit';$f.R.state='Installed';Save $f;$blocked=$false
 try{[void](RestoreTransaction $f.Folder $f.G $f.Settings)}catch{$blocked=$true};Assert $blocked 'concurrent settings accepted';Assert (Test-Path (Join-Path $f.Target 'VERSION')) 'target moved before full validation';Assert ([IO.File]::ReadAllText($f.Settings) -eq 'concurrent user edit') 'concurrent settings overwritten';$passed.Add('Concurrent auxiliary edit blocks before writes')
 $f=Fixture 'changed-target';OldDirectory $f 'RAN-HMAS-Australis' 'old-0' $true;NewBuild $f;Put (Join-Path $f.Target 'VERSION') 'edited';$f.R.state='Installed';Save $f;$blocked=$false
 try{[void](RestoreTransaction $f.Folder $f.G $f.Settings)}catch{$blocked=$true};Assert $blocked 'changed target accepted';Assert (Test-Path (Join-Path $f.Folder 'old-0')) 'archive moved before target validation';$passed.Add('Concurrent carrier edit blocks before writes')
 $f=Fixture 'resume';OldDirectory $f 'RAN-HMAS-Australis' 'old-0' $true;OldDirectory $f 'Australis-Older' 'old-1' $true;NewBuild $f;Aux $f $true;Move-Item -LiteralPath $f.Target -Destination (Join-Path $f.Folder 'Held-Test-Build');Move-Item -LiteralPath (Join-Path $f.Folder 'old-0') -Destination $f.Target;$f.R.state='Restoring';Save $f;[void](RestoreTransaction $f.Folder $f.G $f.Settings);Assert (Test-Path (Join-Path $f.Stream 'Australis-Older')) 'resume did not finish';$passed.Add('Interrupted Restoring resumes from verified originals')
 $f=Fixture 'tampered-path';$f.R.archives+=@{kind='file';relative='Sea Power_Data/StreamingAssets/original/untouched.ini';archive_name='old-0';sha256=('a'*64)};Save $f;$blocked=$false;try{[void](RestoreTransaction $f.Folder $f.G $f.Settings)}catch{$blocked=$true};Assert $blocked 'original game path accepted';Assert ((Get-Content (Join-Path $f.Folder 'transaction.json') -Raw | ConvertFrom-Json).state -eq 'Prepared') 'unsafe journal written';$passed.Add('Original-game path rejected')
 $f=Fixture 'auto-torn-settings';OldDirectory $f 'RAN-HMAS-Australis' 'old-0' $true;Aux $f $true;Put $f.Settings 'torn partial settings write';$f.R.state='Activating';Save $f
 [void](RestoreTransaction $f.Folder $f.G $f.Settings -Automatic);Assert (Test-Path $f.Target) 'torn auxiliary write stranded original CVN';Assert ([IO.File]::ReadAllText($f.Settings) -eq 'settings old') 'automatic settings restore failed';$conflicts=@(Get-ChildItem (Join-Path $f.Folder 'Conflicts') -File);Assert ($conflicts.Count -eq 1 -and [IO.File]::ReadAllText($conflicts[0].FullName) -eq 'torn partial settings write') 'torn settings not preserved';$passed.Add('Automatic rollback preserves torn settings and restores carrier')
 $f=Fixture 'auto-loader-dependencies';OldDirectory $f 'RAN-HMAS-Australis' 'old-0' $true
 $rels=@('winhttp.dll','doorstop_config.ini','.doorstop_version','BepInEx/core/BepInEx.dll','BepInEx/core/0Harmony.xml','BepInEx/plugins/AnchorChain.Preloader.dll','BepInEx/config/BepInEx.cfg');$i=0
 foreach($rel in $rels){$p=Join-Path $f.G $rel;Put $p ('new loader '+$i);$f.R.files+=@{path=$p;existed=$false;old_sha256='';new_sha256=(Sha $p);backup_name=('file-'+$i+'.bin')};if($i -eq 1){Remove-Item $p};if($i -eq 3){Put $p 'torn new dll'};$i++}
 $f.R.state='Activating';Save $f;[void](RestoreTransaction $f.Folder $f.G $f.Settings -Automatic);Assert (Test-Path $f.Target) 'missing loader dependency stranded carrier';foreach($rel in $rels){Assert (!(Test-Path (Join-Path $f.G $rel))) 'new dependency remains after rollback'};Assert (@(Get-ChildItem (Join-Path $f.Folder 'Conflicts') -File).Count -eq 1) 'partial loader bytes not retained';$passed.Add('Full loader whitelist handles absent and torn newly-created dependencies')
 $f=Fixture 'auto-bad-backup';OldDirectory $f 'RAN-HMAS-Australis' 'old-0' $true;OldDirectory $f 'Australis-Older' 'old-1' $true;Aux $f $true;Put (Join-Path $f.Folder 'file-0.bin') 'corrupt backup';$f.R.state='Activating';Save $f;$blocked=$false
 try{[void](RestoreTransaction $f.Folder $f.G $f.Settings -Automatic)}catch{$blocked=$true};Assert $blocked 'bad auxiliary backup not reported';Assert ((Test-Path $f.Target) -and (Test-Path (Join-Path $f.Stream 'Australis-Older'))) 'bad auxiliary backup stranded original CVN folders';Assert ((Get-Content (Join-Path $f.Folder 'transaction.json') -Raw | ConvertFrom-Json).state -eq 'RecoveryRequired') 'bad backup recovery state missing';$passed.Add('Auxiliary backup failure aggregates after restoring valid original carriers')
 $f=Fixture 'auto-partial-target';OldDirectory $f 'RAN-HMAS-Australis' 'old-0' $true;NewBuild $f;Put (Join-Path $f.Target 'VERSION') 'partial target publication';$f.R.state='Activating';Save $f
 [void](RestoreTransaction $f.Folder $f.G $f.Settings -Automatic);Assert ([IO.File]::ReadAllText((Join-Path $f.Target 'vessels/ran_cvn_australis_2030.ini')) -eq 'original CVN') 'partial test target prevented original recovery';Assert ([IO.File]::ReadAllText((Join-Path $f.Folder 'Held-Test-Build/VERSION')) -eq 'partial target publication') 'partial test target lost';[void](RestoreTransaction $f.Folder $f.G $f.Settings);$passed.Add('Automatic rollback retains partial target with resumable held inventory')
 $f=Fixture 'auto-missing-old-aux';OldDirectory $f 'RAN-HMAS-Australis' 'old-0' $true;Aux $f $true;Remove-Item $f.Settings;$f.R.state='Activating';Save $f;[void](RestoreTransaction $f.Folder $f.G $f.Settings -Automatic);Assert ([IO.File]::ReadAllText($f.Settings) -eq 'settings old') 'missing old auxiliary file not restored';$passed.Add('Automatic rollback restores a missing original auxiliary file')
 $result=[ordered]@{runtime=$PSVersionTable.PSVersion.ToString();passed=$passed.Count;tests=$passed.ToArray();scope='PowerShell Core filesystem fixtures; Windows 5.1 and live game untested'}
 Json (Join-Path $PSScriptRoot 'restore-fixtures-results.json') $result
 $result | ConvertTo-Json -Depth 10
}finally{if(Test-Path -LiteralPath $root){Remove-Item -LiteralPath $root -Recurse -Force}}
