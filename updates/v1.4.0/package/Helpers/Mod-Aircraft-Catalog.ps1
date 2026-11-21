# Australis 1.2.9: functions only, compatible with Windows PowerShell 5.1.
# Reads enabled installed sources. Does not enable mods or alter aircraft files.
function Assert-AustralisCatalogPath {
 param([Parameter(Mandatory=$true)][string]$Path)
 $current=[IO.Path]::GetFullPath($Path)
 while($current){
  if(Test-Path -LiteralPath $current){
   $item=Get-Item -LiteralPath $current -Force -ErrorAction Stop
   if($item.Attributes -band [IO.FileAttributes]::ReparsePoint){throw ('Linked source path refused: '+$current)}
  }
  if($current -eq [IO.Path]::GetPathRoot($current)){break}
  $parent=[IO.Path]::GetDirectoryName($current.TrimEnd([IO.Path]::DirectorySeparatorChar,[IO.Path]::AltDirectorySeparatorChar))
  if(!$parent -or $parent -eq $current){break};$current=$parent
 }
}
function Read-AustralisCatalogText {
 param([Parameter(Mandatory=$true)][string]$Path)
 Assert-AustralisCatalogPath $Path
 $text=[IO.File]::ReadAllText([IO.Path]::GetFullPath($Path))
 if($text.IndexOf([char]0xfffd) -ge 0 -or $text.IndexOf([char]0) -ge 0){throw ('Unreadable text encoding: '+$Path)}
 return $text
}
function Get-AustralisCatalogSections {
 param([Parameter(Mandatory=$true)][AllowEmptyString()][string]$Text)
 $headers=[regex]::Matches($Text,'(?m)^[ \t]*\[([^\]\r\n]+)\][ \t]*(?:(?:[;#]|//)[^\r\n]*)?\r?$')
 $result=@()
 for($i=0;$i -lt $headers.Count;$i++){
  $header=$headers[$i];$end=$Text.Length
  if($i+1 -lt $headers.Count){$end=$headers[$i+1].Index}
  $result+=,[pscustomobject]@{Name=$header.Groups[1].Value.Trim();Index=$header.Index;HeaderLength=$header.Length;End=$end;Raw=$Text.Substring($header.Index,$end-$header.Index)}
 }
 return $result
}
function Get-AustralisCatalogWorkshopRoots {
 param([string]$GameDirectory,[string[]]$AdditionalWorkshopRoots=@())
 $result=@{};$libraries=@{};$vdfPaths=@{}
 $game=[IO.Path]::GetFullPath($GameDirectory)
 $common=[IO.Path]::GetDirectoryName($game.TrimEnd([IO.Path]::DirectorySeparatorChar,[IO.Path]::AltDirectorySeparatorChar))
 $steamapps=[IO.Path]::GetDirectoryName($common)
 if($steamapps){$libraries[[IO.Path]::GetDirectoryName($steamapps)]=$true;$vdfPaths[(Join-Path $steamapps 'libraryfolders.vdf')]=$true}
 # Registry reads only, used to locate additional Steam libraries on Windows.
 if($env:OS -eq 'Windows_NT'){
  foreach($registry in @('HKCU:\Software\Valve\Steam','HKLM:\SOFTWARE\WOW6432Node\Valve\Steam','HKLM:\SOFTWARE\Valve\Steam')){
   $setting=Get-ItemProperty -LiteralPath $registry -ErrorAction SilentlyContinue
   if($setting){foreach($property in @('SteamPath','InstallPath')){
    $value='';if($setting.PSObject.Properties[$property]){$value=[string]$setting.PSObject.Properties[$property].Value}
    if($value){$libraries[[IO.Path]::GetFullPath($value)]=$true;$vdfPaths[(Join-Path $value 'steamapps/libraryfolders.vdf')]=$true}
   }}
  }
 }
 foreach($vdf in @($vdfPaths.Keys)){
  if(Test-Path -LiteralPath $vdf -PathType Leaf){
   $text=Read-AustralisCatalogText $vdf
   foreach($match in [regex]::Matches($text,'(?m)^[ \t]*"(?:path|[0-9]+)"[ \t]+"([^"]+)"')){
    $value=$match.Groups[1].Value.Replace('\\','\')
    if([IO.Path]::IsPathRooted($value)){$libraries[[IO.Path]::GetFullPath($value)]=$true}
   }
  }
 }
 foreach($library in $libraries.Keys){$result[(Join-Path $library 'steamapps/workshop/content/1286220')]=$true}
 foreach($root in $AdditionalWorkshopRoots){if($root){$result[[IO.Path]::GetFullPath($root)]=$true}}
 return @($result.Keys | Sort-Object)
}
function Get-AustralisModAircraftCatalog {
 [CmdletBinding()]
 param([Parameter(Mandatory=$true)][string]$GameDirectory,
       [Parameter(Mandatory=$true)][string]$LoadOrderPath,
       [Alias('WorkshopRoots')][string[]]$AdditionalWorkshopRoots=@())
 $game=[IO.Path]::GetFullPath($GameDirectory)
 $streaming=Join-Path $game 'Sea Power_Data/StreamingAssets'
 $original=Join-Path $streaming 'original'
 Assert-AustralisCatalogPath $streaming
 if(!(Test-Path -LiteralPath (Join-Path $original 'aircraft') -PathType Container)){throw 'Original game aircraft directory was not found.'}
 $settings=Read-AustralisCatalogText $LoadOrderPath
 $loadSections=@(Get-AustralisCatalogSections $settings | Where-Object {$_.Name -ieq 'LoadOrder'})
 if($loadSections.Count -ne 1){throw 'Expected exactly one [LoadOrder] section in the selected settings file.'}
 $values=@{}
 foreach($line in ($loadSections[0].Raw -split '\r?\n')){
  if($line -match '^[ \t]*(NumberOfModFiles|Mod[0-9]+Directory)[ \t]*=[ \t]*(.*?)[ \t]*(?:(?:[;#]|//).*)?$'){
   $key=$matches[1];if($values.ContainsKey($key)){throw ('Repeated LoadOrder key: '+$key)};$values[$key]=$matches[2]
  }
 }
 $count=0
 if(!$values.ContainsKey('NumberOfModFiles') -or ![int]::TryParse([string]$values['NumberOfModFiles'],[ref]$count) -or $count -lt 0 -or $count -gt 10000){throw 'LoadOrder NumberOfModFiles is missing or invalid.'}
 $workshopRoots=@(Get-AustralisCatalogWorkshopRoots $game $AdditionalWorkshopRoots)
 $roots=New-Object 'System.Collections.Generic.List[object]'
 $disabled=New-Object 'System.Collections.Generic.List[object]'
 $warnings=New-Object 'System.Collections.Generic.List[string]'
 $excluded=New-Object 'System.Collections.Generic.List[object]'
 $records=New-Object 'System.Collections.Generic.List[object]'
 $unresolved=New-Object 'System.Collections.Generic.List[object]'
 $rootSeen=@{}
 $roots.Add([pscustomobject]@{Path=$original;Kind='original';Enabled=$true;Directory='original';WorkshopId='0'})
 $rootSeen[[IO.Path]::GetFullPath($original)]=$true
 $user=Join-Path $streaming 'user'
 if(Test-Path -LiteralPath $user -PathType Container){
  Assert-AustralisCatalogPath $user
  $roots.Add([pscustomobject]@{Path=$user;Kind='user';Enabled=$true;Directory='user';WorkshopId='0'})
  $rootSeen[[IO.Path]::GetFullPath($user)]=$true
 }
 for($i=1;$i -le $count;$i++){
  $key='Mod'+$i+'Directory'
  if(!$values.ContainsKey($key)){throw ('LoadOrder is incomplete; missing '+$key)}
  $fields=([string]$values[$key]) -split ','
  if($fields.Count -ne 3){throw ('Invalid mod entry: '+$key)}
  $directory=$fields[0].Trim();$enabledText=$fields[1].Trim();$workshopId=$fields[2].Trim()
  if($enabledText -inotmatch '^(True|False)$' -or $workshopId -notmatch '^[0-9]+$'){throw ('Invalid enabled state or Workshop ID: '+$key)}
  if(!$directory -or $directory -in @('.','..') -or $directory -match '[\\/:*?"<>|]' -or $directory -ne $directory.TrimEnd([char[]]'. ')){throw ('Unsafe mod directory in '+$key)}
  if($enabledText -ieq 'False'){
   $disabled.Add([pscustomobject]@{Directory=$directory;WorkshopId=$workshopId;Enabled=$false;Reason='Disabled in Mod Manager; enable the aircraft mod before refreshing Australis.'});continue
  }
  $candidates=@();$kind='localmod'
  if($workshopId -ne '0'){
   $kind='workshop'
   foreach($root in $workshopRoots){$candidate=Join-Path $root $workshopId;if(Test-Path -LiteralPath $candidate -PathType Container){$candidates+=,$candidate}}
  }else{
   $candidate=Join-Path $streaming $directory
   if(Test-Path -LiteralPath $candidate -PathType Container){$candidates+=,$candidate}
  }
  $candidates=@($candidates | Select-Object -Unique)
  if($candidates.Count -ne 1){
   $unresolved.Add([pscustomobject]@{Directory=$directory;WorkshopId=$workshopId;Reason=$(if(!$candidates.Count){'Enabled mod root not found'}else{'Enabled Workshop mod exists in multiple libraries; resolution is ambiguous'})});continue
  }
  $path=[IO.Path]::GetFullPath($candidates[0]);Assert-AustralisCatalogPath $path
  if(!$rootSeen.ContainsKey($path)){
   $roots.Add([pscustomobject]@{Path=$path;Kind=$kind;Enabled=$true;Directory=$directory;WorkshopId=$workshopId});$rootSeen[$path]=$true
  }
 }
 if($unresolved.Count){throw ('Enabled mod roots could not be resolved: '+(($unresolved.ToArray() | ForEach-Object {$_.Directory+' ('+$_.Reason+')'}) -join '; ')+'. No catalogue was applied. Check Steam libraries and the selected LoadOrder settings.')}
 $ids=@{};$ignored=0
 foreach($root in $roots.ToArray()){
  $aircraft=Join-Path $root.Path 'aircraft'
  if(!(Test-Path -LiteralPath $aircraft -PathType Container)){continue}
  Assert-AustralisCatalogPath $aircraft
  foreach($file in @(Get-ChildItem -LiteralPath $aircraft -File -Filter '*.ini' -ErrorAction Stop | Sort-Object Name)){
   if($file.BaseName -match '_(squadrons|variants)$'){continue}
   Assert-AustralisCatalogPath $file.FullName
   try{
    $text=Read-AustralisCatalogText $file.FullName
    $general=@(Get-AustralisCatalogSections $text | Where-Object {$_.Name -ieq 'General'})
    if($general.Count -eq 0){$ignored++;continue}
    if($general.Count -ne 1){throw 'Aircraft definition has repeated [General] sections.'}
    $matchesType=[regex]::Matches($general[0].Raw,'(?im)^[ \t]*UnitType[ \t]*=[ \t]*([A-Za-z]+)[ \t]*(?:(?:[;#]|//)[^\r\n]*)?\r?$')
    if($matchesType.Count -ne 1){throw 'Aircraft [General] has no single readable UnitType.'}
    $type=$matchesType[0].Groups[1].Value
    if($type -notin @('Aircraft','STOL','VTOL','Helicopter')){$ignored++;continue}
    $id=$file.BaseName
    if($id -notmatch '^[A-Za-z0-9][A-Za-z0-9_.-]*$' -or $id.Contains('..')){throw 'Aircraft identifier is unsafe.'}
    $ids[$id]=$true
    $records.Add([pscustomobject]@{Id=$id;UnitType=$type;Path=$file.FullName;Origin=$root.Kind;ModDirectory=$root.Directory;WorkshopId=$root.WorkshopId})
   }catch{$excluded.Add([pscustomobject]@{Path=$file.FullName;ModDirectory=$root.Directory;Reason=$_.Exception.Message})}
  }
 }
 if(!$ids.Count){throw 'No aircraft definitions were discovered in the active source roots.'}
 [string[]]$supported=@($ids.Keys);[Array]::Sort($supported,[StringComparer]::OrdinalIgnoreCase)
 if($disabled.Count){$warnings.Add('Disabled mods are not added. Enable the desired aircraft mod in Mod Manager, close Sea Power, then run Refresh again.')}
 if($excluded.Count){$warnings.Add('Some aircraft files could not be read; inspect Excluded in the report for exact reasons.')}
 return [pscustomobject]@{Version='1.2.9';SupportedIds=$supported;Aircraft=$records.ToArray();Roots=$roots.ToArray();Excluded=$excluded.ToArray();DisabledMods=$disabled.ToArray();Warnings=$warnings.ToArray();UnresolvedEnabledMods=@();IgnoredFiles=$ignored;LoadOrderPath=[IO.Path]::GetFullPath($LoadOrderPath);SelectionCatalogueOnly=$true;AirOperationsTested=$false}
}
function Get-AustralisModAircraftPatch {
 [CmdletBinding()]
 param([Parameter(Mandatory=$true)][AllowEmptyString()][string]$VesselText,
       [Parameter(Mandatory=$true)][AllowEmptyCollection()][string[]]$SupportedIds)
 $sections=@(Get-AustralisCatalogSections $VesselText)
 $flight=@($sections | Where-Object {$_.Name -ieq 'FlightDeck'})
 if($flight.Count -ne 1){throw 'Expected exactly one [FlightDeck] section in the Australis vessel file.'}
 $ids=@{}
 foreach($id in $SupportedIds){
  if($id -notmatch '^[A-Za-z0-9][A-Za-z0-9_.-]*$' -or $id.Contains('..')){throw 'Discovered aircraft identifier is unsafe.'};$ids[$id]=$true
 }
 $entry=[regex]::Matches($flight[0].Raw,'(?im)^(?<prefix>[ \t]*AircraftSupported[ \t]*=[ \t]*)(?<value>[^\r\n]*)')
 if($entry.Count -gt 1){throw 'Repeated AircraftSupported key in [FlightDeck].'}
 $comment=''
 if($entry.Count -eq 1){
  $value=$entry[0].Groups['value'].Value
  $commentMatch=[regex]::Match($value,'[ \t]+(?:[;#]|//).*$')
  if($commentMatch.Success){$comment=$commentMatch.Value;$value=$value.Substring(0,$commentMatch.Index)}
  foreach($old in ($value -split ',')){
   $id=$old.Trim();if(!$id){continue}
   if($id -notmatch '^[A-Za-z0-9][A-Za-z0-9_.-]*$' -or $id.Contains('..')){throw 'Existing AircraftSupported identifier is unsafe.'};$ids[$id]=$true
  }
 }
 foreach($group in @($sections | Where-Object {$_.Name -ieq 'AirGroup'})){
  foreach($match in [regex]::Matches($group.Raw,'(?im)^[ \t]*([A-Za-z0-9][A-Za-z0-9_.-]*)[ \t]*=[ \t]*(?:Default|Random|Squadron[1-9][0-9]*)[ \t]*,')){
   $id=$match.Groups[1].Value;if($id.Contains('..')){throw 'Existing AirGroup identifier is unsafe.'};$ids[$id]=$true
  }
 }
 if(!$ids.Count){throw 'The resulting aircraft selection list would be empty.'}
 [string[]]$supported=@($ids.Keys);[Array]::Sort($supported,[StringComparer]::OrdinalIgnoreCase)
 $value=$supported -join ','
 if($entry.Count -eq 1){
  $match=$entry[0];$replacement=$match.Groups['prefix'].Value+$value+$comment
  $offset=$flight[0].Index+$match.Index
  return $VesselText.Substring(0,$offset)+$replacement+$VesselText.Substring($offset+$match.Length)
 }
 $newline="`n";if($VesselText.Contains("`r`n")){$newline="`r`n"}
 $offset=$flight[0].Index+$flight[0].HeaderLength
 if($offset -lt $VesselText.Length -and $VesselText[$offset] -eq [char]10){$offset++;return $VesselText.Substring(0,$offset)+'AircraftSupported='+$value+$newline+$VesselText.Substring($offset)}
 return $VesselText.Substring(0,$offset)+$newline+'AircraftSupported='+$value+$newline+$VesselText.Substring($offset)
}
