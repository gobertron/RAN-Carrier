function Say([string]$s){Write-Host $s;[void]$script:lines.Add($s)}
function Sha([string]$p){return (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}
function Full([string]$p){return [IO.Path]::GetFullPath($p).TrimEnd([char[]]@('/','\'))}
function NoLink([string]$p){
 $walk=[IO.Path]::GetFullPath($p)
 while($walk){$item=Get-Item -LiteralPath $walk -Force -ErrorAction SilentlyContinue;if($item -and ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)){throw ('Linked path refused: '+$walk)};$next=[IO.Path]::GetDirectoryName($walk);if($next -eq $walk){break};$walk=$next}
}
function RelPath([string]$root,[string]$rel){
 if(!$rel -or $rel -match '(^/|\\|:|(^|/)\.\.?(/|$)|[<>"|?*\x00-\x1f])'){throw ('Unsafe relative path: '+$rel)}
 foreach($part in $rel.Split('/')){if(!$part -or $part -match '[. ]$' -or $part -match '^(?i:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)'){throw 'Unsafe path segment.'}}
 $p=Join-Path $root $rel;NoLink $p;return $p
}
function Entries($o){if($o -is [Collections.IDictionary]){foreach($k in $o.Keys){[pscustomobject]@{Name=[string]$k;Value=$o[$k]}}}else{foreach($p in $o.PSObject.Properties){[pscustomobject]@{Name=$p.Name;Value=$p.Value}}}}
function Atomic([string]$p,[byte[]]$bytes){
 NoLink $p;[void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($p));$temp=$p+'.cvn-'+[guid]::NewGuid().ToString('N')+'.tmp'
 try{[IO.File]::WriteAllBytes($temp,$bytes);if([IO.File]::Exists($p)){[IO.File]::Replace($temp,$p,[System.Management.Automation.Language.NullString]::Value)}else{[IO.File]::Move($temp,$p)}}finally{if([IO.File]::Exists($temp)){[IO.File]::Delete($temp)}}
}
function Json([string]$p,$o){Atomic $p ($script:utf8.GetBytes(($o | ConvertTo-Json -Depth 100)+"`n"))}
function Inventory([string]$root){
 NoLink $root;$map=@{};$queue=New-Object 'System.Collections.Generic.Queue[string]';$queue.Enqueue($root)
 while($queue.Count){foreach($f in @(Get-ChildItem -LiteralPath $queue.Dequeue() -Force)){
  if($f.Attributes -band [IO.FileAttributes]::ReparsePoint){throw ('Linked mod content refused: '+$f.FullName)}
  if($f.PSIsContainer){$queue.Enqueue($f.FullName)}else{$rel=$f.FullName.Substring($root.Length).TrimStart([char[]]@('/','\')).Replace('\','/');$map[$rel]=Sha $f.FullName}
 }};return $map
}
function Verify([string]$root,$expected){$actual=Inventory $root;$rows=@(Entries $expected);if($actual.Count -ne $rows.Count){throw ('File count mismatch: '+$root)};foreach($r in $rows){if(!$actual.ContainsKey($r.Name) -or $actual[$r.Name] -ne $r.Value){throw ('File verification failed: '+$root+' / '+$r.Name)}}}
function Closed{if(@(Get-Process -Name 'Sea Power','SeaPower','sea_power' -ErrorAction SilentlyContinue).Count){throw 'Close Sea Power and its Mod Manager before running this script.'}}
function GamePathValid([string]$p){
 return ((Test-Path -LiteralPath (Join-Path $p 'Sea Power.exe') -PathType Leaf) -and (Test-Path -LiteralPath (Join-Path $p 'Sea Power_Data/StreamingAssets/original/aircraft') -PathType Container))
}
function SteamGameCandidates([string[]]$roots){
 $libraries=@{};$paths=@{}
 foreach($root in $roots){if(!$root){continue};$fullRoot=Full $root;$libraries[$fullRoot]=$true
  $vdf=Join-Path $fullRoot 'steamapps/libraryfolders.vdf'
  if(Test-Path -LiteralPath $vdf -PathType Leaf){NoLink $vdf
   foreach($m in [regex]::Matches([IO.File]::ReadAllText($vdf),'(?m)^\s*"(?:path|[0-9]+)"\s*"([^"\r\n]+)"')){
    $candidate=$m.Groups[1].Value.Replace('\\','\');if([IO.Path]::IsPathRooted($candidate)){$libraries[(Full $candidate)]=$true}
   }
  }
 }
 foreach($library in $libraries.Keys){$p=Join-Path $library 'steamapps/common/Sea Power';if(GamePathValid $p){$paths[(Full $p)]=$true}}
 return @($paths.Keys | Sort-Object)
}
function FindGame([string]$requested){
 if($requested){$g=Full $requested;if(!(GamePathValid $g)){throw ('Sea Power.exe and original aircraft were not found in the supplied game folder: '+$g)};NoLink $g;return $g}
 $roots=New-Object 'System.Collections.Generic.List[string]'
 foreach($base in @(${env:ProgramFiles(x86)},$env:ProgramFiles)){if($base){$roots.Add((Join-Path $base 'Steam'))}}
 if($env:OS -eq 'Windows_NT'){
  foreach($registry in @('HKCU:\Software\Valve\Steam','HKLM:\SOFTWARE\WOW6432Node\Valve\Steam','HKLM:\SOFTWARE\Valve\Steam')){
   $setting=Get-ItemProperty -LiteralPath $registry -ErrorAction SilentlyContinue
   if($setting){foreach($property in @('SteamPath','InstallPath')){if($setting.PSObject.Properties[$property] -and $setting.PSObject.Properties[$property].Value){$roots.Add([string]$setting.PSObject.Properties[$property].Value)}}}
  }
 }
 $candidates=@(SteamGameCandidates $roots.ToArray())
 $known='F:\SteamLibrary\steamapps\common\Sea Power'
 if((GamePathValid $known) -and $known -notin $candidates){$candidates+=,$known}
 if($candidates.Count -eq 1){NoLink $candidates[0];return $candidates[0]}
 if($candidates.Count){Say ('[GAME] Multiple installations found: '+($candidates -join '; '))}else{Say '[GAME] Steam library detection did not identify Sea Power.'}
 if($env:OS -eq 'Windows_NT'){
  $answer=(Read-Host 'Enter the full game folder containing Sea Power.exe').Trim().Trim('"')
  if($answer){$g=Full $answer;if(GamePathValid $g){NoLink $g;return $g}}
 }
 throw 'Sea Power could not be selected. Drag the folder containing Sea Power.exe onto this CMD, or supply its path as the first argument.'
}
function TextSha([string]$text){$h=[Security.Cryptography.SHA256]::Create();try{return ([BitConverter]::ToString($h.ComputeHash($script:utf8.GetBytes($text)))).Replace('-','').ToLowerInvariant()}finally{$h.Dispose()}}
function PayloadSignature($manifest){
 $rows=@(Entries $manifest.files | Where-Object {$_.Name.StartsWith('payload/')} | Sort-Object Name)
 return TextSha (($rows | ForEach-Object {$_.Name+'='+$_.Value}) -join "`n")
}
function CatalogSignature($catalog){
 $rows=@('Ids='+(@($catalog.SupportedIds) -join ','))
 foreach($aircraft in @($catalog.Aircraft | Sort-Object Path)){$rows+=($aircraft.Id+'|'+$aircraft.UnitType+'|'+$aircraft.Path+'|'+(Sha $aircraft.Path))}
 return TextSha ($rows -join "`n")
}
function SingleClass([string]$root){
 $v=Join-Path $root 'vessels';if(!(Test-Path -LiteralPath $v -PathType Container)){return $false};NoLink $v
 $definitions=@(Get-ChildItem -LiteralPath $v -File -Filter '*.ini' | Where-Object {$_.BaseName -notmatch '_variants$'})
 return ($definitions.Count -eq 1 -and $definitions[0].BaseName -eq 'ran_cvn_australis_2030' -and (Test-Path -LiteralPath (Join-Path $v 'ran_cvn_australis_2030_variants.ini') -PathType Leaf))
}
function CarrierRoot([string]$p){
 $v=Join-Path $p 'vessels'
 if(!(Test-Path -LiteralPath $v -PathType Container)){return $false};NoLink $v
 foreach($f in @(Get-ChildItem -LiteralPath $v -File -Filter '*.ini')){
  if($f.BaseName -notmatch '^(?:ran_cvn_australis_[A-Za-z0-9_.-]+|ran_cvn_southern_cross_2030|ran_australis_basic_shell|ran_australis_flightdeck_stage1)$'){continue}
  NoLink $f.FullName;$text=[IO.File]::ReadAllText($f.FullName)
  if($f.BaseName -eq 'ran_cvn_southern_cross_2030' -and $text -notmatch '(?im)^\s*ResourcesRoot\s*=\s*ran_cvn_australis_2030\.obj\s*$'){continue}
  if($text -match '(?im)^\s*UnitType\s*=\s*Vessel\s*$'){return $true}
 }
 return $false
}
function PureCarrier([string]$p){
 foreach($file in @(Get-ChildItem -LiteralPath (Join-Path $p 'vessels') -File -Filter '*.ini')){if($file.BaseName -notmatch '^(?:ran_cvn_(?:australis|southern_cross|federation|commonwealth)_|ran_australis_(?:basic_shell|flightdeck_stage1|stage1_c[1-4]_test)(?:_variants)?$)'){throw ('Mixed ship pack preserved: '+$p)}}
 foreach($cat in @('aircraft','submarines','land_units')){if((Test-Path -LiteralPath (Join-Path $p $cat)) -and @(Get-ChildItem -LiteralPath (Join-Path $p $cat) -File -Filter '*.ini').Count){throw ('Mixed mod pack preserved: '+$p)}}
}
function ParseSettings([string]$text){
 $sections=@(Get-AustralisCatalogSections $text | Where-Object {$_.Name -ieq 'LoadOrder'})
 if($sections.Count -ne 1){throw 'Expected one [LoadOrder] section in usersettings.ini.'};$section=$sections[0]
 $n=[regex]::Matches($section.Raw,'(?im)^\s*NumberOfModFiles\s*=\s*([0-9]+)\s*$');if($n.Count -ne 1){throw 'Invalid NumberOfModFiles.'};$count=[int]$n[0].Groups[1].Value;if($count -gt 10000){throw 'Invalid mod count.'}
 $rows=@();for($i=1;$i -le $count;$i++){
  $m=[regex]::Matches($section.Raw,('(?im)^\s*Mod'+$i+'Directory\s*=\s*([^,\r\n]+),\s*(True|False),\s*([0-9]+)\s*$'))
  if($m.Count -ne 1){throw ('Unreadable mod row '+$i)};$rows+=,[pscustomobject]@{Directory=$m[0].Groups[1].Value.Trim();Enabled=($m[0].Groups[2].Value -ieq 'True');WorkshopId=$m[0].Groups[3].Value}
 }
 return [pscustomobject]@{Section=$section;Rows=$rows}
}
function SettingsText([string]$text,$parsed,$rows){
 $nl="`n";if($text.Contains("`r`n")){$nl="`r`n"}
 $extra=@($parsed.Section.Raw -split '\r?\n' | Where-Object {$_ -notmatch '^\s*(?:\[LoadOrder\]|NumberOfModFiles\s*=|Mod[0-9]+Directory\s*=)' -and $_.Trim()})
 $out='[LoadOrder]'+$nl+'NumberOfModFiles='+@($rows).Count+$nl;$i=1
 foreach($r in $rows){$flag='False';if($r.Enabled){$flag='True'};$out+='Mod'+$i+'Directory='+$r.Directory+','+$flag+','+$r.WorkshopId+$nl;$i++}
 if($extra.Count){$out+=($extra -join $nl)+$nl};$out+=$nl
 return $text.Substring(0,$parsed.Section.Index)+$out+$text.Substring($parsed.Section.End)
}
function ArchivePathAllowed([string]$rel){
 if($rel -eq 'BepInEx/plugins/RAN.Australis.DeckController.dll'){return $true}
 if($rel -match '^Sea Power_Data/StreamingAssets/([^/]+)$'){return $matches[1] -notin @('original','user')}
 return $rel -match '^Sea Power_Data/StreamingAssets/user/(?:vessels/(?:ran_cvn_(?:australis|southern_cross|federation|commonwealth)_[A-Za-z0-9_.-]+|ran_australis_(?:basic_shell|flightdeck_stage1|stage1_c[1-4]_test)(?:_variants)?)\.ini|ships/(?:ran_cvn_australis_[A-Za-z0-9_.-]+|ran_australis_(?:basic_shell|flightdeck_stage1))|animations/ran_australis_stage1_(?:jbd|lifts)\.ini|RAN\.Australis\.DeckController\.dll)$'
}
