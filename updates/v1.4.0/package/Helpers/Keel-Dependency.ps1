# Original Australis checks; third-party loader binaries are not redistributed.
function Get-AustralisKeelBoolean([string]$Path,[string]$Section,[string]$Key){
 if(!(Test-Path -LiteralPath $Path -PathType Leaf)){return $true};NoLink $Path
 $sections=@(Get-AustralisCatalogSections ([IO.File]::ReadAllText($Path)) | Where-Object {$_.Name -ieq $Section})
 if($sections.Count -gt 1){throw ('Repeated dependency configuration section: '+$Path)}
 if(!$sections.Count){return $true}
 $m=[regex]::Matches($sections[0].Raw,('(?im)^[ \t]*'+[regex]::Escape($Key)+'[ \t]*=[ \t]*([^\r\n]*)$'))
 if($m.Count -gt 1){throw ('Repeated dependency configuration value: '+$Key)}
 if(!$m.Count){return $true};$value=$m[0].Groups[1].Value.Trim()
 if($value -notmatch '^(?i:true|false)$'){throw ('Unreadable '+$Key+'; configuration preserved: '+$Path)}
 return ($value -ieq 'true')
}
function Get-AustralisKeelDependency {
 param([string]$GameDirectory,$Rows,[string[]]$WorkshopRoots,$Manifest)
 if(!$Manifest.PSObject.Properties['keel']){throw 'The release manifest has no Keel dependency contract.'};$c=$Manifest.keel
 foreach($n in @('workshop_item_id','tested_version','core_dll_sha256','compatibility_library_sha256','stub_dll_sha256','patcher_dll_sha256')){if(!$c.PSObject.Properties[$n]){throw ('Incomplete Keel dependency contract: '+$n)}}
 if([string]$c.workshop_item_id -ne '3835527459'){throw 'Unexpected Keel Workshop identity.'}
 foreach($n in @('core_dll_sha256','compatibility_library_sha256','stub_dll_sha256','patcher_dll_sha256')){if(!@($c.$n).Count){throw ('Empty Keel hash list: '+$n)};foreach($h in @($c.$n)){if([string]$h -notmatch '^[a-f0-9]{64}$'){throw ('Invalid Keel hash: '+$n)}}}
 $stream=Join-Path $GameDirectory 'Sea Power_Data/StreamingAssets';$found=@{}
 foreach($r in @($Rows)){if(!$r.Enabled){continue};$roots=@()
  if([string]$r.WorkshopId -eq '0'){$roots+=,(RelPath $stream ([string]$r.Directory))}else{foreach($w in $WorkshopRoots){$roots+=,(RelPath $w ([string]$r.WorkshopId))}}
  foreach($p in $roots){if(!(Test-Path -LiteralPath $p -PathType Container)){continue};NoLink $p
   foreach($d in @($p,(Join-Path $p 'SeaPowerKeel'))){if(Test-Path -LiteralPath (Join-Path $d 'SeaPowerKeel.dll') -PathType Leaf){NoLink $d;$found[(Full $d)]=$true}}
  }
 }
 if(!$found.Count){throw 'R.A.T.S. Keel is missing or disabled. Subscribe to Workshop item 3835527459 or install its official release, enable Keel in Mods, close Sea Power and retry.'}
 if($found.Count -ne 1){throw 'More than one enabled Keel installation was found. Enable only one official Keel copy, restart Sea Power, close it and retry.'}
 $root=@($found.Keys)[0];$hint='Run KeelSetup.exe from the official Keel folder, then close Sea Power and retry. Folder: '+$root
 $observed=New-Object 'System.Collections.Generic.List[object]';$signature=New-Object 'System.Collections.Generic.List[string]'
 function Observe([string]$p,[string]$h){[void]$observed.Add([pscustomobject]@{Path=$p;Exists=[bool]$h;Sha256=$h})}
 $core=RelPath $root 'SeaPowerKeel.dll';$coreHash=Sha $core
 if($coreHash -notin @($c.core_dll_sha256)){throw ('Installed Keel core is not in this release''s verified compatibility set: '+$coreHash+'. Use the official '+$c.tested_version+' release or provide the log for review. Folder: '+$root)};Observe $core $coreHash
 $installedVersion='unknown (verified dependency hash)'
 if($c.PSObject.Properties['core_versions']){
  $versionRows=@(Entries $c.core_versions | Where-Object {$_.Name -eq $coreHash})
  if($versionRows.Count -eq 1){$installedVersion=[string]$versionRows[0].Value;if($installedVersion -notmatch '^[0-9]+\.[0-9]+\.[0-9]+(?:\.[0-9]+)?$'){throw 'Invalid Keel version label in the dependency contract.'}}
 }
 $lib=RelPath $root 'lib/AnchorChain.keel.bin'
 if(!(Test-Path -LiteralPath $lib -PathType Leaf)){throw ('Keel compatibility library is missing. '+$hint)}
 $libHash=Sha $lib;if($libHash -notin @($c.compatibility_library_sha256)){throw ('Keel compatibility library is not recognised: '+$libHash+'. '+$hint)};Observe $lib $libHash
 foreach($i in @(@('winhttp.dll','',''),@('BepInEx/core/BepInEx.dll','BepInEx','5'),@('BepInEx/core/0Harmony.dll','0Harmony','2'),@('BepInEx/core/BepInEx.Preloader.dll','',''),@('BepInEx/core/Mono.Cecil.dll','',''))){
  $p=RelPath $GameDirectory $i[0];if(!(Test-Path -LiteralPath $p -PathType Leaf)){throw ('BepInEx 5 is not installed completely; missing '+$i[0]+'. '+$hint)}
  if($i[1]){try{$a=[Reflection.AssemblyName]::GetAssemblyName($p)}catch{throw ('Unreadable BepInEx managed dependency was preserved: '+$i[0]+'. '+$hint)};if($i[1] -eq 'BepInEx'){$minimum=[version]'5.4.23.2'}else{$minimum=[version]'2.9.0.0'};if($a.Name -ne $i[1] -or $a.Version.Major -ne [int]$i[2] -or $a.Version -lt $minimum){throw ('Unsupported BepInEx managed dependency was preserved: '+$i[0]+'. '+$hint)}}
  $h=Sha $p;Observe $p $h;[void]$signature.Add($i[0]+'='+$h)
 }
 $door=RelPath $GameDirectory 'doorstop_config.ini'
 if(!(Test-Path -LiteralPath $door -PathType Leaf)){throw ('BepInEx Doorstop configuration is missing. '+$hint)}
 $text=[IO.File]::ReadAllText($door)
 if($text -notmatch '(?im)^\s*enabled\s*=\s*true\s*$' -or $text -notmatch '(?im)^\s*target_assembly\s*=\s*BepInEx[\\/]core[\\/]BepInEx\.Preloader\.dll\s*$'){throw 'Existing Doorstop configuration is disabled or points to another loader. It was preserved. Enable its BepInEx preloader before installing.'}
 $h=Sha $door;Observe $door $h;[void]$signature.Add('doorstop_config.ini='+$h)
 $cfg=RelPath $GameDirectory 'BepInEx/config/dev.sewerlabs.seapowerkeel.cfg';$bep=RelPath $GameDirectory 'BepInEx/config/BepInEx.cfg'
 if(!(Get-AustralisKeelBoolean $cfg 'Loading' 'TakeOver')){throw ('Keel takeover is disabled. Set [Loading] TakeOver=true in '+$cfg+', restart Sea Power, close it and retry. The configuration was preserved.')}
 if(!(Get-AustralisKeelBoolean $bep 'Caching' 'EnableAssemblyCache')){throw ('BepInEx assembly cache is disabled. Set [Caching] EnableAssemblyCache=true in '+$bep+', restart Sea Power, close it and retry. The configuration was preserved.')}
 foreach($p in @($cfg,$bep)){$h='';if(Test-Path -LiteralPath $p -PathType Leaf){$h=Sha $p};Observe $p $h;[void]$signature.Add($p+'='+$h)}
 $plans=New-Object 'System.Collections.Generic.List[object]';$hashes=@{}
 foreach($i in @(@('BepInEx/plugins/SeaPowerKeel.Stub.dll','copy-to-BepInEx-plugins/SeaPowerKeel.Stub.dll','stub_dll_sha256','Keel starter'),@('BepInEx/patchers/SeaPowerKeel.Patcher.dll','SeaPowerKeel.Patcher.dll','patcher_dll_sha256','Keel takeover patcher'))){
  $dest=RelPath $GameDirectory $i[0]
  if(Test-Path -LiteralPath $dest){
   if(!(Test-Path -LiteralPath $dest -PathType Leaf)){throw ($i[3]+' destination is not a file and was preserved: '+$dest)}
   $h=Sha $dest;if($h -notin @($c.($i[2]))){throw ($i[3]+' is present but unrecognised and was preserved: '+$h+'. '+$hint)};Observe $dest $h
  }else{
   Observe $dest ''; $src=RelPath $root $i[1]
   if(!(Test-Path -LiteralPath $src -PathType Leaf)){throw ($i[3]+' source is missing. '+$hint)}
   $h=Sha $src;if($h -notin @($c.($i[2]))){throw ($i[3]+' source is unrecognised and was not copied: '+$h+'. '+$hint)};Observe $src $h
   [void]$plans.Add([ordered]@{path=$dest;source=$src;bytes=$null;existed=$false;old_sha256='';new_sha256=$h;backup_name=('file-'+$plans.Count+'.bin')})
  }
  $hashes[$i[0]]=$h;[void]$signature.Add($i[0]+'='+$h)
 }
 [void]$signature.Add('loader=Keel');[void]$signature.Add('root='+$root);[void]$signature.Add('core='+$coreHash);[void]$signature.Add('compatibility_library='+$libHash)
 return [pscustomobject]@{Loader='Keel';InstalledVersion=$installedVersion;TestedVersion=[string]$c.tested_version;Root=$root;CoreSha256=$coreHash;CompatibilityLibrarySha256=$libHash;StubSha256=$hashes['BepInEx/plugins/SeaPowerKeel.Stub.dll'];PatcherSha256=$hashes['BepInEx/patchers/SeaPowerKeel.Patcher.dll'];DependencySignature=(TextSha (($signature.ToArray() | Sort-Object) -join "`n"));Plans=$plans.ToArray();ObservedFiles=$observed.ToArray();ConfigPath=$cfg;SetupPath=(Join-Path $root 'KeelSetup.exe');RuntimeVerified=$false}
}
function Assert-AustralisKeelDependencyUnchanged($Dependency){
 foreach($f in @($Dependency.ObservedFiles)){NoLink $f.Path;$present=Test-Path -LiteralPath $f.Path
  if($f.Exists){if(!(Test-Path -LiteralPath $f.Path -PathType Leaf) -or (Sha $f.Path) -ne $f.Sha256){throw ('Keel dependency changed during preparation: '+$f.Path)}}elseif($present){throw ('A missing Keel dependency appeared during preparation: '+$f.Path)}
 }
}
