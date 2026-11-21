# Functions only. Windows PowerShell 5.1 compatible.
# Original installed carrier/amphib aircraft references are read and verified.
# No game, mod, aircraft, squadron or stock-asset files are modified here.
function Get-AustralisFullAirwingIni {
 param([string]$Text)
 $sections=@{}
 $headers=[regex]::Matches($Text,'(?m)^[ \t]*\[([^\]\r\n]+)\][ \t]*(?:(?:[;#]|//)[^\r\n]*)?\r?$')
 for($i=0;$i -lt $headers.Count;$i++){
  $h=$headers[$i];$name=$h.Groups[1].Value.Trim();$end=$Text.Length
  if($i+1 -lt $headers.Count){$end=$headers[$i+1].Index}
  # Genuine original Tarawa repeats empty decorative divider headers.
  # Those are not native data sections; real duplicate sections remain fatal.
  if($name -cnotmatch '^[A-Za-z_][A-Za-z0-9_.-]*$'){continue}
  if($sections.ContainsKey($name)){throw ('Repeated real INI section: ['+$name+']')}
  $raw=$Text.Substring($h.Index,$end-$h.Index);$values=@{}
  foreach($line in ($raw -split '\r?\n')){
   if($line -match '^[ \t]*([^;#=\[\r\n][^=]*?)\s*=(.*)$'){
    $key=$matches[1].Trim();$value=$matches[2].Trim()
    $value=[regex]::Replace($value,'[ \t]+(?:[;#]|//).*$', '').Trim()
    if($values.ContainsKey($key)){throw ('Repeated INI key: ['+$name+'] '+$key)}
    $values[$key]=$value
   }
  }
  $sections[$name]=[pscustomobject]@{Name=$name;Raw=$raw;Values=$values}
 }
 return $sections
}
function Get-AustralisFullAirwingValue {
 param($Ini,[string]$Section,[string]$Key,[string]$Default='')
 if($Ini.ContainsKey($Section) -and $Ini[$Section].Values.ContainsKey($Key)){return [string]$Ini[$Section].Values[$Key]}
 return $Default
}
function Assert-AustralisFullAirwingPath {
 param([string]$Path)
 if([string]::IsNullOrWhiteSpace($Path)){throw 'An aircraft source path was empty.'}
 $p=[IO.Path]::GetFullPath($Path)
 while($p){
  if(Test-Path -LiteralPath $p){if((Get-Item -LiteralPath $p -Force).Attributes -band [IO.FileAttributes]::ReparsePoint){throw ('Linked aircraft source path refused: '+$p)}}
  if($p -eq [IO.Path]::GetPathRoot($p)){break}
  $p=[IO.Path]::GetDirectoryName($p.TrimEnd([IO.Path]::DirectorySeparatorChar,[IO.Path]::AltDirectorySeparatorChar))
 }
}
function Get-AustralisFullAirwingSha {
 param([string]$Path)
 Assert-AustralisFullAirwingPath $Path
 return (Get-FileHash -LiteralPath $Path -Algorithm SHA256 -ErrorAction Stop).Hash.ToLowerInvariant()
}
function Read-AustralisFullAirwingText {
 param([string]$Path)
 Assert-AustralisFullAirwingPath $Path
 if(-not [IO.File]::Exists($Path)){throw ('Original aircraft source file missing: '+$Path)}
 $text=[IO.File]::ReadAllText($Path)
 if($text.Contains([char]0xfffd)){throw ('Invalid Unicode source text: '+$Path)}
 return $text
}
function Set-AustralisFullAirwingSection {
 param([string]$Text,[string]$Name,[string]$Replacement)
 $newline="`n";if($Text.Contains("`r`n")){$newline="`r`n"}
 $h=[regex]::Match($Text,'(?im)^[ \t]*\['+[regex]::Escape($Name)+'\][ \t]*(?:(?:[;#]|//)[^\r\n]*)?\r?$')
 $replacementText=$Replacement.Replace("`r`n","`n").Replace("`n",$newline).TrimEnd([char[]]"`r`n")+$newline+$newline
 if(-not $h.Success){return $Text.TrimEnd([char[]]"`r`n")+$newline+$newline+$replacementText}
 $tail=$Text.Substring($h.Index+$h.Length);$next=[regex]::Match($tail,'(?m)^[ \t]*\[[^\]\r\n]+\]');$end=$Text.Length
 if($next.Success){$end=$h.Index+$h.Length+$next.Index}
 return $Text.Substring(0,$h.Index)+$replacementText+$Text.Substring($end)
}
function Get-AustralisFullAirwingPriority {
 param([string]$Carrier)
 $s=$Carrier.ToLowerInvariant()
 if($s -match 'nimitz'){return 0};if($s -match 'enterprise'){return 1}
 if($s -match 'kitty.?hawk'){return 2};if($s -match 'america'){return 3}
 if($s -match 'forrestal'){return 4};if($s -match 'tarawa'){return 5}
 if($s -match 'invincible'){return 6};if($s -match 'kuznetsov|orel'){return 7}
 if($s -match 'kiev'){return 8}
 return 50
}
function Get-AustralisFullAirwingSelectors {
 param($Squadrons,[string]$SourceValue)
 $selectors=New-Object 'System.Collections.Generic.List[object]'
 $squadronCount=0
 [void][int]::TryParse((Get-AustralisFullAirwingValue $Squadrons 'General' 'NumberOfSquadrons' '0'),[ref]$squadronCount)
 foreach($entry in ($SourceValue -split '\|')){
  $fields=$entry -split ',';$count=0
  if($fields.Count -lt 2 -or $fields.Count -gt 3 -or -not [int]::TryParse($fields[1].Trim(),[ref]$count) -or $count -le 0){throw 'Invalid native original AirGroup entry.'}
  $token=$fields[0].Trim();$suffix=''
  if($token -ceq 'Default' -or $token -ceq 'Random'){
   if(-not $Squadrons.ContainsKey('Default')){throw 'Original AirGroup selector requires a missing [Default] squadron.'}
  }elseif($token -cmatch '^Squadron([1-9][0-9]*)$'){
   $index=[int]$matches[1]
   if($index -gt $squadronCount -or -not $Squadrons.ContainsKey($token)){throw ('Original numbered squadron is unavailable: '+$token)}
  }else{throw ('Unsupported native squadron selector: '+$token)}
  if($fields.Count -eq 3){
   $third=$fields[2].Trim()
   if($third -cnotmatch '^[A-Za-z0-9_.-]+$'){throw 'Unsafe third native AirGroup field.'}
   $suffix=','+$third
  }
  [void]$selectors.Add([pscustomobject]@{Token=$token;SourceCount=$count;Suffix=$suffix})
 }
 if($selectors.Count -lt 1){throw 'Original aircraft row had no valid squadron selectors.'}
 return $selectors.ToArray()
}
function Format-AustralisFullAirwingEntry {
 param($Selectors,[int]$Count)
 if($Count -lt 1){throw 'Allocated AirGroup count must be positive.'}
 $rows=@($Selectors);if($rows.Count -lt 1){throw 'No validated original squadron selectors.'}
 $total=0;foreach($row in $rows){$total+=[int]$row.SourceCount}
 $allocation=New-Object 'System.Collections.Generic.List[int]';$given=0
 for($i=0;$i -lt $rows.Count;$i++){
  $part=[int][Math]::Floor(([double]$Count*$rows[$i].SourceCount)/$total)
  [void]$allocation.Add($part);$given+=$part
 }
 for($i=0;$given -lt $Count;$i=($i+1) % $rows.Count){$allocation[$i]++;$given++}
 $parts=New-Object 'System.Collections.Generic.List[string]'
 for($i=0;$i -lt $rows.Count;$i++){if($allocation[$i] -gt 0){[void]$parts.Add($rows[$i].Token+','+$allocation[$i]+$rows[$i].Suffix)}}
 return $parts.ToArray() -join '|'
}
function Get-AustralisFullAirwingCatalog {
 param([string]$GameDirectory)
 if([string]::IsNullOrWhiteSpace($GameDirectory)){throw 'Sea Power game directory was blank.'}
 $game=[IO.Path]::GetFullPath($GameDirectory)
 $original=Join-Path $game 'Sea Power_Data/StreamingAssets/original'
 $vessels=Join-Path $original 'vessels';$aircraft=Join-Path $original 'aircraft'
 Assert-AustralisFullAirwingPath $original
 if(-not [IO.Directory]::Exists($vessels) -or -not [IO.Directory]::Exists($aircraft)){throw 'Original game vessels/aircraft folders are unavailable. No aircraft identifiers were guessed.'}
 $raw=New-Object 'System.Collections.Generic.List[object]';$failures=New-Object 'System.Collections.Generic.List[string]'
 foreach($file in @(Get-ChildItem -LiteralPath $vessels -File -Filter '*.ini' | Sort-Object Name)){
  if($file.BaseName -match '_variants$'){continue}
  try{
   $ini=Get-AustralisFullAirwingIni (Read-AustralisFullAirwingText $file.FullName);$cap=0
   if(-not [int]::TryParse((Get-AustralisFullAirwingValue $ini 'FlightDeck' 'AircraftCapacity'),[ref]$cap) -or $cap -le 0){continue}
   if((Get-AustralisFullAirwingValue $ini 'General' 'UnitType') -cne 'Vessel'){continue}
   $roles=Get-AustralisFullAirwingValue $ini 'AI' 'Role'
   if($roles -notmatch '(?i)(^|,)(Carrier|CVS|Landing)(,|$)' -and $file.BaseName -notmatch '(?i)_(?:cv[a-z]*|lha|lhd|takr)_'){continue}
   $hasAviation=$false
   foreach($section in $ini.Keys){if($section -match '^LaunchPoint[1-9][0-9]*$' -and (Get-AustralisFullAirwingValue $ini $section 'AllowedType') -match '(?i)(^|,)(Plane|STOL|VTOL|Helicopter)(,|$)'){$hasAviation=$true}}
   if(-not $hasAviation){continue}
   $priority=Get-AustralisFullAirwingPriority $file.BaseName
   $sections=New-Object 'System.Collections.Generic.List[object]'
   if($ini.ContainsKey('AirGroup')){[void]$sections.Add([pscustomobject]@{Name='AirGroup';Source=$file.FullName;Values=$ini['AirGroup'].Values;Year=0})}
   $variants=Join-Path $vessels ($file.BaseName+'_variants.ini')
   if([IO.File]::Exists($variants)){
    $variant=Get-AustralisFullAirwingIni (Read-AustralisFullAirwingText $variants)
    foreach($section in @($variant.Keys | Sort-Object)){
     if(($section -eq 'Default' -or $section -match '^Variant[1-9][0-9]*$') -and (Get-AustralisFullAirwingValue $variant $section 'CustomAirGroup') -ieq 'True'){
      $year=0;$service=Get-AustralisFullAirwingValue $variant $section 'ServiceDate' (Get-AustralisFullAirwingValue $variant 'Default' 'ServiceDate')
      [void][int]::TryParse(($service -split '\|')[0],[ref]$year)
      [void]$sections.Add([pscustomobject]@{Name=$section;Source=$variants;Values=$variant[$section].Values;Year=$year})
     }
    }
   }
   foreach($section in $sections){foreach($id in @($section.Values.Keys | Sort-Object)){
    $value=[string]$section.Values[$id]
    if($value -cnotmatch '^(?:Default|Random|Squadron[1-9][0-9]*),[ \t]*[1-9][0-9]*'){continue}
    if($id -cnotmatch '^[A-Za-z0-9][A-Za-z0-9_.-]*$' -or $id.Contains('..')){throw 'Unsafe original carrier aircraft identifier.'}
    [void]$raw.Add([pscustomobject]@{Id=$id;Value=$value;Carrier=$file.FullName;Source=$section.Source;Section=$section.Name;Priority=$priority;Year=$section.Year;CarrierIni=$ini})
   }}
  }catch{[void]$failures.Add($file.Name+': '+$_.Exception.Message)}
 }
 $catalog=@{}
 foreach($candidate in @($raw.ToArray() | Sort-Object Priority,@{Expression='Year';Descending=$true},Id,Carrier,Source,Section)){
  if($catalog.ContainsKey($candidate.Id)){continue}
  try{
   $id=[string]$candidate.Id;$path=Join-Path $aircraft ($id+'.ini');$sq=Join-Path $aircraft ($id+'_squadrons.ini')
   $a=Get-AustralisFullAirwingIni (Read-AustralisFullAirwingText $path);$s=Get-AustralisFullAirwingIni (Read-AustralisFullAirwingText $sq)
   $kind=Get-AustralisFullAirwingValue $a 'General' 'UnitType'
   if($kind -cnotin @('Aircraft','STOL','Helicopter','VTOL')){throw ('Unsupported native aircraft UnitType: '+$kind)}
   $category='Fixed';if($kind -ceq 'Helicopter'){$category='Helicopter'}elseif($kind -ceq 'VTOL'){$category='VTOL'}
   $selectors=@(Get-AustralisFullAirwingSelectors $s $candidate.Value)
   $support=''
   if($candidate.CarrierIni.ContainsKey($id)){
    $support=$candidate.CarrierIni[$id].Raw
    if([regex]::IsMatch($support,'(?im)^[ \t]*[^;#=\r\n]*(?:Elevator|LaunchPoint|TaxiPath|RecoveryPoint)[^=\r\n]*=')){throw 'Original aircraft support section contains ship-specific point indices; choose another carrier candidate.'}
   }
   $catalog[$id]=[pscustomobject]@{Id=$id;UnitType=$kind;Category=$category;Priority=$candidate.Priority;Modern=($candidate.Priority -lt 50);Selectors=$selectors;SourceValue=$candidate.Value;SupportText=$support;Carrier=('original/vessels/'+[IO.Path]::GetFileName($candidate.Carrier));CarrierSha=(Get-AustralisFullAirwingSha $candidate.Carrier);Source=('original/vessels/'+[IO.Path]::GetFileName($candidate.Source));SourceSection=$candidate.Section;SourceSha=(Get-AustralisFullAirwingSha $candidate.Source);AircraftSha=(Get-AustralisFullAirwingSha $path);SquadronsSha=(Get-AustralisFullAirwingSha $sq)}
  }catch{[void]$failures.Add($candidate.Id+': '+$_.Exception.Message)}
 }
 $rows=@($catalog.Values | Sort-Object Priority,Id)
 if($rows.Count -eq 0){throw 'No original carrier/amphib aircraft rows passed aircraft/squadron verification.'}
 return [pscustomobject]@{Rows=$rows;Failures=@($failures.ToArray());GameDirectory=$game;SourceScope='Installed original carrier/amphib rosters and original aircraft/squadron files only; no stock asset files redistributed.'}
}
function Apply-AustralisFullAirwing {
 param([Parameter(Mandatory=$true)][string]$VesselText,[Parameter(Mandatory=$true)]$Wing)
 $target=Get-AustralisFullAirwingIni $VesselText;$capacity=0
 if(-not [int]::TryParse((Get-AustralisFullAirwingValue $target 'FlightDeck' 'AircraftCapacity'),[ref]$capacity) -or $capacity -lt [int]$Wing.Report.aircraft_count){throw 'Vessel capacity is below the requested full airwing profile.'}
 if(-not $target.ContainsKey('AirGroup') -or $target['AirGroup'].Values.Count -ne 0){throw 'Full-rebuild vessel template must contain one empty [AirGroup].'}
 $result=Set-AustralisFullAirwingSection $VesselText 'AirGroup' $Wing.AirGroupText
 $flight=$target['FlightDeck'].Raw;$pattern='(?im)^[ \t]*AircraftSupported[ \t]*=[^\r\n]*\r?$'
 $count=[regex]::Matches($flight,$pattern).Count
 if($count -gt 1){throw 'Repeated AircraftSupported key.'}
 $line='AircraftSupported='+(@($Wing.SupportedIds) -join ',')
 if($count -eq 1){$flight=[regex]::Replace($flight,$pattern,$line)}else{$flight=$flight.TrimEnd([char[]]"`r`n")+"`n"+$line+"`n"}
 $result=Set-AustralisFullAirwingSection $result 'FlightDeck' $flight
 foreach($id in @($Wing.SupportSections.Keys | Sort-Object)){
  if($target.ContainsKey($id)){throw ('Aircraft support section collides with vessel template: '+$id)}
  $result=Set-AustralisFullAirwingSection $result $id ([string]$Wing.SupportSections[$id])
 }
 return $result
}
# v1.2.1: validate routing inputs before accepting aircraft catalog entries.
# This checks native configuration completeness, not actual aircraft footprint,
# Harmony hook application or a completed landing.
function Assert-AustralisFullFlightContract {
 param([Parameter(Mandatory=$true)][string]$VesselText)
 $ini=Get-AustralisFullAirwingIni $VesselText
 foreach($pair in @(@('NumberOfElevators',4),@('NumberOfLaunchPoints',7),@('NumberOfRecoveryPoints',4),@('NumberOfTaxiPaths',15),@('NumberOfDeckZones',16))){
  if((Get-AustralisFullAirwingValue $ini 'FlightDeck' $pair[0]) -cne [string]($pair[1])){throw ('Controller flight contract mismatch: FlightDeck/'+$pair[0]+' must be '+$pair[1])}
 }
 foreach($pair in @(@('Elevator',4),@('LaunchPoint',7),@('RecoveryPoint',4),@('TaxiPath',15),@('DeckZone',16))){
  for($i=1;$i -le [int]$pair[1];$i++){
   if(-not $ini.ContainsKey($pair[0]+$i)){throw ('Flight contract is missing ['+$pair[0]+$i+']')}
  }
 }
 foreach($index in 1..4){
  $name='RecoveryPoint'+$index;$allowed=Get-AustralisFullAirwingValue $ini $name 'AllowedType'
  $elevators=Get-AustralisFullAirwingValue $ini $name 'AssociatedElevators'
  if([string]::IsNullOrWhiteSpace($elevators)){throw ('Recovery point lacks associated lifts: '+$name)}
  foreach($id in $elevators.Split(',')){
   if($id -notmatch '^[1-4]$' -or -not $ini.ContainsKey('Elevator'+$id)){throw ('Recovery lift reference is invalid: '+$name)}
   $found=$false
   foreach($path in 1..15){
    if((Get-AustralisFullAirwingValue $ini ('TaxiPath'+$path) 'From') -ceq $name -and (Get-AustralisFullAirwingValue $ini ('TaxiPath'+$path) 'To') -ceq ('Elevator'+$id)){$found=$true;break}
   }
   if(-not $found){throw ('Recovery point has no taxi path to its associated lift: '+$name+' -> Elevator'+$id)}
  }
  foreach($field in @('Position','ExitPosition')){
   $vector=Get-AustralisFullAirwingValue $ini $name $field
   if(($vector.Split(',')).Count -ne 3){throw ('Recovery vector is missing or invalid: '+$name+'/'+$field)}
   foreach($component in $vector.Split(',')){
    $number=0.0
    if(-not [double]::TryParse($component,[Globalization.NumberStyles]::Float,[Globalization.CultureInfo]::InvariantCulture,[ref]$number) -or [double]::IsNaN($number) -or [double]::IsInfinity($number)){throw ('Recovery vector is not finite: '+$name+'/'+$field)}
   }
  }
  if($allowed -match '(^|,)(Plane|STOL|VTOL)(,|$)'){
   $circuit=Get-AustralisFullAirwingValue $ini $name 'CircuitWaypoints'
   if([string]::IsNullOrWhiteSpace($circuit)){throw ('Plane/STOL/VTOL recovery lacks generic CircuitWaypoints: '+$name)}
   foreach($waypoint in $circuit.Split('|')){
    if(($waypoint.Split(',')).Count -ne 3){throw ('Generic recovery waypoint is invalid: '+$name)}
    foreach($component in $waypoint.Split(',')){
     $number=0.0
     if(-not [double]::TryParse($component,[Globalization.NumberStyles]::Float,[Globalization.CultureInfo]::InvariantCulture,[ref]$number) -or [double]::IsNaN($number) -or [double]::IsInfinity($number)){throw ('Generic recovery waypoint is not finite: '+$name)}
    }
   }
  }
  if($allowed -match '(^|,)Helicopter(,|$)' -and [string]::IsNullOrWhiteSpace((Get-AustralisFullAirwingValue $ini $name 'HelicopterCircuitWaypoints'))){throw ('Mixed vertical recovery lacks the helicopter circuit: '+$name)}
 }
 if((Get-AustralisFullAirwingValue $ini 'RecoveryPoint1' 'Arrested') -cne 'True'){throw 'The fixed-wing recovery point must remain arrested.'}
 if((Get-AustralisFullAirwingValue $ini 'RecoveryPoint1' 'BlocksLaunchPoints') -cne '3,4'){throw 'The arrested recovery corridor must block C3/C4, without blocking disjoint bow launches.'}
 foreach($index in 3..4){
  if((Get-AustralisFullAirwingValue $ini ('LaunchPoint'+$index) 'BlocksRecoveryPoints') -cne '1,2,3,4'){throw 'C3/C4 must exclude every active recovery point.'}
 }
 return [pscustomobject]@{status='PASS_STATIC_FLIGHT_CONTRACT';native_counts='4 lifts / 7 launches / 4 recoveries / 15 routes / 16 zones';generic_vtol_recovery_inputs=$true;live_landing_verified=$false}
}

function New-AustralisFullAirwing {
 [CmdletBinding()]
 param([Parameter(Mandatory=$true)][string]$GameDirectory,[Parameter(Mandatory=$true)][AllowEmptyString()][string]$VesselText,[Alias('Profile')][ValidateSet('Full99','Test24')][string]$AirwingProfile='Full99',$Catalog=$null)
 $report=[ordered]@{version='1.2.1';configured=$false;profile=$AirwingProfile;flight_contract=$null;reason='';source_scope='Installed original carrier/amphib rosters only';capacity=0;aircraft_count=0;category_counts=[ordered]@{};selected_units=@();supported_aircraft_ids=@();candidate_failures=@();all_aircraft_types_required=$true;arbitrary_third_party_compatibility_claimed=$false;live_game_tested=$false}
 try{
  $target=Get-AustralisFullAirwingIni $VesselText;$capacity=0
  if(-not [int]::TryParse((Get-AustralisFullAirwingValue $target 'FlightDeck' 'AircraftCapacity'),[ref]$capacity) -or $capacity -lt 1){throw 'Target vessel has no positive FlightDeck/AircraftCapacity.'}
  if(-not $target.ContainsKey('AirGroup') -or $target['AirGroup'].Values.Count -ne 0){throw 'Target vessel must contain one empty [AirGroup].'}
  $report.flight_contract=Assert-AustralisFullFlightContract -VesselText $VesselText
  if($null -eq $Catalog){$Catalog=Get-AustralisFullAirwingCatalog $GameDirectory}
  $quota=[ordered]@{Fixed=72;Helicopter=15;VTOL=12};if($AirwingProfile -eq 'Test24'){$quota=[ordered]@{Fixed=16;Helicopter=4;VTOL=4}}
  $wanted=0;foreach($v in $quota.Values){$wanted+=[int]$v}
  if($capacity -lt $wanted){throw ('Target capacity '+$capacity+' is below '+$AirwingProfile+' count '+$wanted)}
  $supported=@($Catalog.Rows | Sort-Object Id | ForEach-Object {$_.Id})
  $supports=@{};foreach($row in $Catalog.Rows){if($row.SupportText){$supports[$row.Id]=[string]$row.SupportText}}
  $selected=New-Object 'System.Collections.Generic.List[object]';$lines=New-Object 'System.Collections.Generic.List[string]'
  [void]$lines.Add('[AirGroup]');[void]$lines.Add('; Full rebuild '+$AirwingProfile+': validated installed native carrier/amphib aircraft.');[void]$lines.Add('; Original squadron selectors are retained; aircraft assets are referenced only.')
  foreach($category in $quota.Keys){
   $pool=@($Catalog.Rows | Where-Object {$_.Category -ceq $category -and $_.Modern} | Sort-Object Priority,Id)
   if($pool.Count -lt 1){throw ('No verified modern original-game '+$category+' carrier/amphib aircraft. All three aviation categories are required; no active files should be changed.')}
   $limit=[Math]::Min($pool.Count,[int]$quota[$category]);$allocation=New-Object 'System.Collections.Generic.List[int]'
   for($i=0;$i -lt $limit;$i++){[void]$allocation.Add(0)}
   for($i=0;$i -lt [int]$quota[$category];$i++){$allocation[$i % $limit]++}
   for($i=0;$i -lt $limit;$i++){
    $row=$pool[$i];$count=$allocation[$i];$value=Format-AustralisFullAirwingEntry $row.Selectors $count
    [void]$lines.Add($row.Id+'='+$value)
    [void]$selected.Add([pscustomobject]@{id=$row.Id;unit_type=$row.UnitType;category=$category;count=$count;value=$value;original_carrier=$row.Carrier;original_carrier_sha256=$row.CarrierSha;airgroup_source=$row.Source;airgroup_source_section=$row.SourceSection;airgroup_source_sha256=$row.SourceSha;aircraft_sha256=$row.AircraftSha;squadrons_sha256=$row.SquadronsSha;original_airgroup_value=$row.SourceValue})
   }
   $report.category_counts[$category]=[int]$quota[$category]
  }
  $report.capacity=$capacity;$report.aircraft_count=$wanted;$report.selected_units=@($selected.ToArray());$report.supported_aircraft_ids=$supported;$report.candidate_failures=@($Catalog.Failures);$report.source_scope=$Catalog.SourceScope
  $report.reason='Balanced native profile derived from verified original carrier/amphib rosters. Explicit original squadron selectors retained. Native game behavior remains untested.'
  $wing=[pscustomobject]@{Configured=$true;Text='';Report=[pscustomobject]$report;AirGroupText=($lines.ToArray() -join "`n");SupportedIds=$supported;SupportSections=$supports;Catalog=$Catalog}
  $wing.Text=Apply-AustralisFullAirwing -VesselText $VesselText -Wing $wing
  $report.configured=$true;$wing.Report=[pscustomobject]$report
  return $wing
 }catch{
  $report.reason=$_.Exception.Message
  return [pscustomobject]@{Configured=$false;Text=$VesselText;Report=[pscustomobject]$report;AirGroupText='';SupportedIds=@();SupportSections=@{};Catalog=$Catalog}
 }
}
