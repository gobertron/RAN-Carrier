# Executes the real PowerShell implementation against an isolated Steam fixture.
# Compatible with Windows PowerShell 5.1. No installed game or network is used.
[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
Set-StrictMode -Version 2.0
$module=Join-Path $PSScriptRoot 'Mod-Aircraft-Catalog.ps1'
$wrapper=Join-Path $PSScriptRoot 'Apply-Mod-Aircraft.ps1'
if(!(Test-Path -LiteralPath $module)){throw 'Mod-Aircraft-Catalog.ps1 is missing.'}
. $module
$utf8=New-Object System.Text.UTF8Encoding($false)
$temp=Join-Path ([IO.Path]::GetTempPath()) ('AustralisAircraftTests-'+[guid]::NewGuid().ToString('N'))
$game=Join-Path $temp 'SteamLibrary/steamapps/common/Sea Power'
$stream=Join-Path $game 'Sea Power_Data/StreamingAssets'
$workshop=Join-Path $temp 'SteamLibrary/steamapps/workshop/content/1286220'
$target=Join-Path $stream 'RAN-HMAS-Australis'
$loadOrder=Join-Path $temp 'LoadOrder.ini'
$tests=New-Object 'System.Collections.Generic.List[object]'
function Write-FixtureText([string]$Path,[string]$Text){
 [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($Path))
 [IO.File]::WriteAllText($Path,$Text,$utf8)
}
function Assert-True([bool]$Condition,[string]$Message){if(!$Condition){throw $Message}}
function Assert-Equal($Actual,$Expected,[string]$Message){
 if($Actual -cne $Expected){throw ($Message+'; expected='+[string]$Expected+'; actual='+[string]$Actual)}
}
function Assert-Throws([scriptblock]$Action,[string]$Message){
 $failed=$false;try{& $Action | Out-Null}catch{$failed=$true}
 Assert-True $failed $Message
}
function Invoke-Case([string]$Name,[scriptblock]$Body){
 try{& $Body;$tests.Add([pscustomobject]@{name=$Name;passed=$true;error=''})|Out-Null;Write-Host ('PASS '+$Name)}
 catch{$tests.Add([pscustomobject]@{name=$Name;passed=$false;error=$_.Exception.Message})|Out-Null;Write-Host ('FAIL '+$Name+': '+$_.Exception.Message)}
}
function Snapshot-Game {
 $rows=@(Get-ChildItem -LiteralPath $game -Recurse -File | Sort-Object FullName | ForEach-Object {
  ($_.FullName.Substring($game.Length))+'='+(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
 })
 return ($rows -join "`n")
}
$baseLoadOrder=@'
[LoadOrder]
Mod1Directory=RAN-HMAS-Australis,True,0
Mod2Directory=LocalAirWing,True,0
Mod3Directory=3380210757,True,3380210757
Mod4Directory=3832163513,False,3832163513
Mod5Directory=DisabledLocalWing,False,0
NumberOfModFiles=5
'@
$vesselText=@'
; Preserve this comment and every non-whitelist setting.
[General]
UnitType=CVN
[AirGroup]
stock_f14=Default,8
embarked_custom=Squadron1,2
[FlightDeck]
AircraftCapacity=99
AircraftSupported=stock_f14,existing_custom
GroundCrewCount=16
NumberOfLaunchPoints=7
NumberOfRecoveryPoints=4
[LaunchPoint1]
AllowedType=Plane,STOL
Position=0,0.320568,1.2
[RecoveryPoint1]
AllowedType=Plane,STOL
Arrested=True
'@
$vesselText=$vesselText.Replace("`r`n","`n").Replace("`n","`r`n")+"`r`n"
$vesselPath=Join-Path $target 'vessels/ran_cvn_australis_2030.ini'
try{
 Write-FixtureText (Join-Path $game 'SeaPower.exe') 'fixture only; never execute'
 Write-FixtureText (Join-Path $target '_info.ini') "[Language_en]`nName=RAN / HMAS Australis`n"
 Write-FixtureText (Join-Path $target 'VERSION') "1.2.8`n"
 Write-FixtureText $vesselPath $vesselText
 Write-FixtureText (Join-Path $stream 'original/aircraft/stock_f14.ini') "[General]`nUnitType=Aircraft`n[Weapons]`nValue=1`n"
 Write-FixtureText (Join-Path $stream 'original/aircraft/stock_helo.ini') "[General]`nUnitType=Helicopter`n"
 Write-FixtureText (Join-Path $stream 'original/aircraft/stock_f14_squadrons.ini') "[General]`nUnitType=Aircraft`n"
 Write-FixtureText (Join-Path $stream 'original/aircraft/not_an_aircraft.ini') "[General]`nUnitType=Ship`n"
 Write-FixtureText (Join-Path $stream 'user/aircraft/user_carrier_jet.ini') "[General]`nUnitType=Aircraft`n"
 Write-FixtureText (Join-Path $stream 'LocalAirWing/_info.ini') "[Language_en]`nName=Local naval aircraft`n"
 Write-FixtureText (Join-Path $stream 'LocalAirWing/aircraft/ran_f111n.ini') "[General]`nUnitType=Aircraft`n[Decorative]`nKey=1`n[Decorative]`nKey=2`n"
 Write-FixtureText (Join-Path $stream 'DisabledLocalWing/aircraft/disabled_local_jet.ini') "[General]`nUnitType=Aircraft`n"
 Write-FixtureText (Join-Path $workshop '3380210757/_info.ini') "[Language_en]`nName=Workshop naval aircraft`n"
 Write-FixtureText (Join-Path $workshop '3380210757/aircraft/naval_vtol.ini') "[General] # real comment`nUnitType=VTOL // actual category`n[----- weapons -----]`n[Weapons]`nCount=1`n[Weapons]`nCount=2`n"
 Write-FixtureText (Join-Path $workshop '3380210757/aircraft/STOCK_F14.ini') "[General]`nUnitType=Aircraft`n"
 Write-FixtureText (Join-Path $workshop '3832163513/aircraft/disabled_workshop_jet.ini') "[General]`nUnitType=Aircraft`n"
 Write-FixtureText $loadOrder $baseLoadOrder
 $vesselHash=(Get-FileHash -LiteralPath $vesselPath -Algorithm SHA256).Hash.ToLowerInvariant()
 $runtimePath=Join-Path $target 'RUNTIME-FILES.json'
 $installPath=Join-Path $target 'AUSTRALIS-INSTALL.json'
 $runtime=@{'vessels/ran_cvn_australis_2030.ini'=$vesselHash}
 Write-FixtureText $runtimePath (($runtime | ConvertTo-Json)+"`n")
 $install=@{schema=1;ship_id='ran_cvn_australis_2030';version='1.2.8';manifest_sha256='original-manifest-preserved';installed_files=@{'vessels/ran_cvn_australis_2030.ini'=$vesselHash;'RUNTIME-FILES.json'=(Get-FileHash -LiteralPath $runtimePath -Algorithm SHA256).Hash.ToLowerInvariant()}}
 Write-FixtureText $installPath (($install | ConvertTo-Json -Depth 5)+"`n")

 Invoke-Case 'Discovers stock, always-loaded user, enabled local and enabled Workshop aircraft' {
  $c=Get-AustralisModAircraftCatalog -GameDirectory $game -LoadOrderPath $loadOrder
  foreach($id in @('stock_f14','stock_helo','user_carrier_jet','ran_f111n','naval_vtol')){
   Assert-True (@($c.SupportedIds) -contains $id) ('Missing active aircraft '+$id)
  }
  Assert-True (@($c.SupportedIds) -notcontains 'stock_f14_squadrons') 'Squadron metadata was mistaken for aircraft.'
  Assert-True (@($c.SupportedIds) -notcontains 'not_an_aircraft') 'Non-aircraft definition was advertised.'
 }
 Invoke-Case 'Does not advertise disabled local or Workshop aircraft' {
  $c=Get-AustralisModAircraftCatalog -GameDirectory $game -LoadOrderPath $loadOrder
  foreach($id in @('disabled_local_jet','disabled_workshop_jet')){Assert-True (@($c.SupportedIds) -notcontains $id) ('Disabled aircraft included: '+$id)}
 }
 Invoke-Case 'Accepts mod aircraft without squadron files and with unrelated repeated sections' {
  $c=Get-AustralisModAircraftCatalog -GameDirectory $game -LoadOrderPath $loadOrder
  Assert-True (@($c.SupportedIds) -contains 'ran_f111n') 'Local mod aircraft was dropped by unrelated duplicate sections.'
  Assert-True (@($c.SupportedIds) -contains 'naval_vtol') 'VTOL or comment-tolerant General parsing failed.'
 }
 Invoke-Case 'Deduplicates aircraft identifiers case-insensitively' {
  $c=Get-AustralisModAircraftCatalog -GameDirectory $game -LoadOrderPath $loadOrder
  Assert-Equal (@($c.SupportedIds | Where-Object {$_ -ieq 'stock_f14'}).Count) 1 'Stock/mod duplicate appeared twice.'
 }
 Invoke-Case 'Deduplicates repeated enabled root entries without duplicate aircraft' {
  Write-FixtureText $loadOrder ($baseLoadOrder.Replace('NumberOfModFiles=5',"NumberOfModFiles=6`nMod6Directory=LocalAirWing,True,0"))
  try{
   $c=Get-AustralisModAircraftCatalog -GameDirectory $game -LoadOrderPath $loadOrder
   Assert-Equal (@($c.Roots | Where-Object {$_.Path -eq (Join-Path $stream 'LocalAirWing')}).Count) 1 'Repeated root was scanned twice.'
   Assert-Equal (@($c.SupportedIds | Where-Object {$_ -ieq 'ran_f111n'}).Count) 1 'Repeated root added duplicate aircraft.'
  }finally{Write-FixtureText $loadOrder $baseLoadOrder}
 }
 Invoke-Case 'Refuses unresolved enabled Workshop roots instead of publishing an incomplete catalogue' {
  Write-FixtureText $loadOrder ($baseLoadOrder.Replace('3380210757','9999999999'))
  try{Assert-Throws {Get-AustralisModAircraftCatalog -GameDirectory $game -LoadOrderPath $loadOrder} 'Missing enabled Workshop mod was not reported as a failure.'}
  finally{Write-FixtureText $loadOrder $baseLoadOrder}
 }
 Invoke-Case 'Refuses traversal in enabled local mod directory' {
  Write-FixtureText $loadOrder ($baseLoadOrder.Replace('LocalAirWing,True,0','../escape,True,0'))
  try{Assert-Throws {Get-AustralisModAircraftCatalog -GameDirectory $game -LoadOrderPath $loadOrder} 'Traversal in enabled mod directory was accepted.'}
  finally{Write-FixtureText $loadOrder $baseLoadOrder}
 }
 Invoke-Case 'Refuses ambiguous enabled Workshop mod found in two Steam libraries' {
  $otherWorkshop=Join-Path $temp 'OtherLibrary/steamapps/workshop/content/1286220'
  Write-FixtureText (Join-Path $otherWorkshop '3380210757/aircraft/ambiguous_jet.ini') "[General]`nUnitType=Aircraft`n"
  Assert-Throws {Get-AustralisModAircraftCatalog -GameDirectory $game -LoadOrderPath $loadOrder -AdditionalWorkshopRoots @($otherWorkshop)} 'Ambiguous Workshop roots were silently chosen.'
 }
 Invoke-Case 'Changes only the whitelist line and preserves embarked/custom IDs' {
  $c=Get-AustralisModAircraftCatalog -GameDirectory $game -LoadOrderPath $loadOrder
  $p=Get-AustralisModAircraftPatch -VesselText $vesselText -SupportedIds @($c.SupportedIds)
  $pattern='(?im)^AircraftSupported=[^\r\n]*'
  Assert-Equal ([regex]::Replace($p,$pattern,'AircraftSupported=<catalogue>')) ([regex]::Replace($vesselText,$pattern,'AircraftSupported=<catalogue>')) 'A non-whitelist character changed.'
  $line=[regex]::Match($p,$pattern).Value
  foreach($id in @('ran_f111n','naval_vtol','existing_custom','embarked_custom')){Assert-True (($line.Substring('AircraftSupported='.Length) -split ',') -contains $id) ('Required ID not retained: '+$id)}
 }
 Invoke-Case 'Rejects duplicate FlightDeck or repeated whitelist keys' {
  Assert-Throws {Get-AustralisModAircraftPatch -VesselText ($vesselText+"[FlightDeck]`r`nAircraftSupported=bad`r`n") -SupportedIds @('ran_f111n')} 'Duplicate FlightDeck was accepted.'
  Assert-Throws {Get-AustralisModAircraftPatch -VesselText ($vesselText.Replace('GroundCrewCount=16',"AircraftSupported=duplicate`r`nGroundCrewCount=16")) -SupportedIds @('ran_f111n')} 'Duplicate whitelist key was accepted.'
 }
 Invoke-Case 'Repeated catalogue refresh discovers newly added mod aircraft' {
  $a=Get-AustralisModAircraftCatalog -GameDirectory $game -LoadOrderPath $loadOrder
  $first=Get-AustralisModAircraftPatch -VesselText $vesselText -SupportedIds @($a.SupportedIds)
  Assert-Equal (Get-AustralisModAircraftPatch -VesselText $first -SupportedIds @($a.SupportedIds)) $first 'Unchanged repeated patch is not idempotent.'
  Write-FixtureText (Join-Path $workshop '3380210757/aircraft/new_naval_jet.ini') "[General]`nUnitType=Aircraft`n"
  $b=Get-AustralisModAircraftCatalog -GameDirectory $game -LoadOrderPath $loadOrder
  $second=Get-AustralisModAircraftPatch -VesselText $first -SupportedIds @($b.SupportedIds)
  Assert-True ($second.Contains('new_naval_jet')) 'Newly added enabled mod aircraft was not discovered on rerun.'
  Remove-Item -LiteralPath (Join-Path $workshop '3380210757/aircraft/new_naval_jet.ini')
 }

 if(!(Test-Path -LiteralPath $wrapper)){throw 'Apply-Mod-Aircraft.ps1 is missing; transaction integration tests are required.'}
 Invoke-Case 'Check mode does not change any game files' {
  $before=Snapshot-Game
  & $wrapper -GameDirectory $game -LoadOrderPath $loadOrder -Mode Check | Out-Null
  Assert-Equal (Snapshot-Game) $before 'Check mode changed a game file.'
 }
 Invoke-Case 'Install, later refresh, conflict refusal and both restore transactions execute against real files' {
  $firstBackup=Join-Path $temp 'backup-first'
  $secondBackup=Join-Path $temp 'backup-second'
  $before=Snapshot-Game
  $installed=& $wrapper -GameDirectory $game -LoadOrderPath $loadOrder -Mode Install -BackupDirectory $firstBackup
  Assert-True (Test-Path -LiteralPath $firstBackup -PathType Container) 'No verified backup directory was created.'
  $firstText=[IO.File]::ReadAllText($vesselPath)
  Assert-True $firstText.Contains('ran_f111n') 'Install did not add local carrier aircraft.'
  $pattern='(?im)^AircraftSupported=[^\r\n]*'
  Assert-Equal ([regex]::Replace($firstText,$pattern,'AircraftSupported=<catalogue>')) ([regex]::Replace($vesselText,$pattern,'AircraftSupported=<catalogue>')) 'Install changed non-whitelist vessel data.'
  Assert-Equal ([IO.File]::ReadAllText((Join-Path $target 'VERSION'))) "1.2.8`n" 'Selection patch changed the base carrier version.'
  $runtime=[IO.File]::ReadAllText($runtimePath)|ConvertFrom-Json
  $install=[IO.File]::ReadAllText($installPath)|ConvertFrom-Json
  $actualVesselHash=(Get-FileHash -LiteralPath $vesselPath -Algorithm SHA256).Hash.ToLowerInvariant()
  Assert-Equal $runtime.'vessels/ran_cvn_australis_2030.ini' $actualVesselHash 'Runtime inventory did not record the patched vessel hash.'
  Assert-Equal $install.installed_files.'vessels/ran_cvn_australis_2030.ini' $actualVesselHash 'Installer inventory did not record the patched vessel hash.'
  Assert-Equal $install.version '1.2.8' 'Installer base carrier version changed.'
  Assert-Equal $install.manifest_sha256 'original-manifest-preserved' 'Original manifest provenance changed.'
  Write-FixtureText (Join-Path $workshop '3380210757/aircraft/new_naval_jet.ini') "[General]`nUnitType=Aircraft`n"
  & $wrapper -GameDirectory $game -LoadOrderPath $loadOrder -Mode Install -BackupDirectory $secondBackup | Out-Null
  $secondText=[IO.File]::ReadAllText($vesselPath)
  Assert-True $secondText.Contains('new_naval_jet') 'Installed refresh ignored a newly installed mod aircraft.'
  Write-FixtureText $vesselPath ($secondText+"; user edit after patch`r`n")
  Assert-Throws {& $wrapper -GameDirectory $game -Mode Restore -BackupDirectory $secondBackup} 'Restore overwrote a post-patch user edit.'
  Write-FixtureText $vesselPath $secondText
  & $wrapper -GameDirectory $game -Mode Restore -BackupDirectory $secondBackup | Out-Null
  Assert-Equal ([IO.File]::ReadAllText($vesselPath)) $firstText 'Second restore did not return the first patched configuration.'
  Remove-Item -LiteralPath (Join-Path $workshop '3380210757/aircraft/new_naval_jet.ini')
  & $wrapper -GameDirectory $game -Mode Restore -BackupDirectory $firstBackup | Out-Null
  Assert-Equal (Snapshot-Game) $before 'Final restore did not return every original game file and remove created patch metadata.'
 }
 Invoke-Case 'Restores interrupted transactions containing a mix of before and after file states' {
  foreach($state in @('Installing','RecoveryRequired')){
   $before=Snapshot-Game
   $backup=Join-Path $temp ('backup-interrupted-'+$state)
   & $wrapper -GameDirectory $game -LoadOrderPath $loadOrder -Mode Install -BackupDirectory $backup | Out-Null
   $journalPath=Join-Path $backup 'transaction.json'
   $journal=[IO.File]::ReadAllText($journalPath)|ConvertFrom-Json
   $journal.state=$state
   # Simulate interruption after one replacement: one touched file is already
   # rolled back, remaining touched files retain their installed bytes.
   $entry=@($journal.files | Where-Object {$_.existed})[0]
   [IO.File]::WriteAllBytes((Join-Path $target $entry.relative_path),[IO.File]::ReadAllBytes((Join-Path $backup $entry.backup_file)))
   Write-FixtureText $journalPath (($journal|ConvertTo-Json -Depth 12)+"`n")
   & $wrapper -GameDirectory $game -Mode Restore -BackupDirectory $backup | Out-Null
   Assert-Equal (Snapshot-Game) $before ('Interrupted '+$state+' restore did not recover original bytes.')
  }
 }
 Invoke-Case 'Preserves UTF-8 BOM and UTF-16 little-endian encoding through install and exact-byte restore' {
  $originalBytes=[IO.File]::ReadAllBytes($vesselPath)
  $formats=@(
   [pscustomobject]@{Name='UTF8-BOM';Encoding=(New-Object System.Text.UTF8Encoding($true));Prefix=@(239,187,191)},
   [pscustomobject]@{Name='UTF16-LE';Encoding=[Text.Encoding]::Unicode;Prefix=@(255,254)}
  )
  try{
   foreach($format in $formats){
    $unicodeText=$vesselText+'; non-ASCII comment '+[char]0x00E9+"`r`n"
    [IO.File]::WriteAllText($vesselPath,$unicodeText,$format.Encoding)
    $encodedBefore=[Convert]::ToBase64String([IO.File]::ReadAllBytes($vesselPath))
    $backup=Join-Path $temp ('backup-'+$format.Name)
    & $wrapper -GameDirectory $game -LoadOrderPath $loadOrder -Mode Install -BackupDirectory $backup | Out-Null
    $afterBytes=[IO.File]::ReadAllBytes($vesselPath)
    for($i=0;$i -lt $format.Prefix.Count;$i++){Assert-Equal ([int]$afterBytes[$i]) $format.Prefix[$i] ($format.Name+' BOM changed.')}
    $afterText=[IO.File]::ReadAllText($vesselPath)
    $pattern='(?im)^AircraftSupported=[^\r\n]*'
    Assert-Equal ([regex]::Replace($afterText,$pattern,'AircraftSupported=<catalogue>')) ([regex]::Replace($unicodeText,$pattern,'AircraftSupported=<catalogue>')) ($format.Name+' changed non-whitelist Unicode content.')
    & $wrapper -GameDirectory $game -Mode Restore -BackupDirectory $backup | Out-Null
    Assert-Equal ([Convert]::ToBase64String([IO.File]::ReadAllBytes($vesselPath))) $encodedBefore ($format.Name+' restore was not byte-exact.')
   }
  }finally{[IO.File]::WriteAllBytes($vesselPath,$originalBytes)}
 }
}
finally{
 if(Test-Path -LiteralPath $temp){Remove-Item -LiteralPath $temp -Recurse -Force}
}
$failed=@($tests.ToArray() | Where-Object {!$_.passed})
$summary=[pscustomobject]@{schema=1;tool='Australis modded aircraft selection regression tests';version='1.2.9';passed=($failed.Count -eq 0);test_count=$tests.Count;failed_count=$failed.Count;tests=$tests.ToArray();game_runtime_tested=$false}
$summary | ConvertTo-Json -Depth 8
if($failed.Count){throw ([string]$failed.Count+' modded-aircraft regression test(s) failed.')}
