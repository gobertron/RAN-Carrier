param([string]$Root=(Split-Path $PSScriptRoot -Parent))
$ErrorActionPreference='Stop'
$script:utf8=New-Object Text.UTF8Encoding($false,$true)
. (Join-Path $Root 'Cvn-Helpers.ps1')
. (Join-Path $Root 'build-package/Helpers/Mod-Aircraft-Catalog.ps1')
. (Join-Path $Root 'Keel-Dependency.ps1')
$m=Get-Content -LiteralPath (Join-Path $Root 'build-package/PACKAGE-MANIFEST.json') -Raw | ConvertFrom-Json
$results=@()
foreach($v in @('0.6.0','0.7.0')){
 $game=Join-Path $PSScriptRoot ('real-profiles/'+$v+'/Sea Power')
 if(Test-Path -LiteralPath $game){Remove-Item -LiteralPath $game -Recurse -Force}
 [void][IO.Directory]::CreateDirectory($game)
 Get-ChildItem -LiteralPath (Join-Path $Root 'payload-assembly/baseline/loader') -Force | Copy-Item -Destination $game -Recurse
 $source='official-release';if($v -eq '0.6.0'){$source='official-v0.6.0'}
 $mod=Join-Path $game 'Sea Power_Data/StreamingAssets/SeaPowerKeel';[void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($mod))
 Copy-Item -LiteralPath (Join-Path $PSScriptRoot ($source+'/SeaPowerKeel')) -Destination $mod -Recurse
 $rows=@([pscustomobject]@{Directory='SeaPowerKeel';WorkshopId='0';Enabled=$true})
 $pref=Join-Path $game 'BepInEx/plugins/AnchorChain.Preloader.dll';$before=Sha $pref
 $d=Get-AustralisKeelDependency -GameDirectory $game -Rows $rows -WorkshopRoots @() -Manifest $m
 if($d.Plans.Count -ne 2){throw ('Expected2 repairs for '+$v)}
 foreach($plan in $d.Plans){[void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($plan.path));Copy-Item -LiteralPath $plan.source -Destination $plan.path;if((Sha $plan.path) -ne $plan.new_sha256){throw 'Repair bytes mismatch'}}
 $e=Get-AustralisKeelDependency -GameDirectory $game -Rows $rows -WorkshopRoots @() -Manifest $m
 if($e.Plans.Count -ne 0 -or $d.DependencySignature -ne $e.DependencySignature -or (Sha $pref) -ne $before){throw ('Repeat or loader preservation failed: '+$v)}
 $results+=[ordered]@{official_version=$v;core_sha256=$e.CoreSha256;compatibility_library_sha256=$e.CompatibilityLibrarySha256;missing_files_repaired=2;repeat_plans=0;dependency_signature_stable=$true;existing_anchorchain_preloader_preserved=$true;production_manifest_used=$true}
}
[ordered]@{passed=2;failed=0;profiles=$results;game_runtime_tested=$false;runtime=$PSVersionTable.PSVersion.ToString()}|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $PSScriptRoot 'REAL-KEEL-DEPENDENCY-CHECKS.json') -Encoding UTF8
Get-Content -LiteralPath (Join-Path $PSScriptRoot 'REAL-KEEL-DEPENDENCY-CHECKS.json')
