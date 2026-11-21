param([string]$Root=(Split-Path $PSScriptRoot -Parent),[string]$CompatibilityLibrary='', [string]$HarmonyPath='', [string]$ControllerPath='', [string]$OutputPath='')
$ErrorActionPreference='Stop'
$lib=$CompatibilityLibrary;if(!$lib){$lib=Join-Path $Root 'keel-source/lib/AnchorChain.keel.bin'}
$harmony=$HarmonyPath;if(!$harmony){$harmony=Join-Path $Root 'payload-assembly/baseline/loader/BepInEx/core/0Harmony.dll'}
$dll=$ControllerPath;if(!$dll){$dll=Join-Path $Root 'build-package/payload/RAN.Australis.DeckController.dll'}
$ac=[Reflection.Assembly]::LoadFrom($lib)
$h=[Reflection.Assembly]::LoadFrom($harmony)
$a=[Reflection.Assembly]::LoadFrom($dll)
$t=$a.GetType('RAN.Australis.Plugin',$true)
$i=$ac.GetType('AnchorChain.IAnchorChainMod',$true)
if(!$t.IsPublic -or !$i.IsAssignableFrom($t)){throw 'Plugin interface is not compatible.'}
$attrs=@($t.GetCustomAttributesData()|Where-Object {$_.AttributeType.FullName -eq 'AnchorChain.ACPlugin'})
if($attrs.Count -ne 1){throw 'Expected one AnchorChain plugin attribute.'}
$map=$t.GetInterfaceMap($i)
if($map.TargetMethods.Count -ne 1 -or $map.TargetMethods[0].Name -ne 'TriggerEntryPoint' -or $map.TargetMethods[0].GetParameters().Count -ne 0){throw 'Entry point mismatch.'}
$o=[Activator]::CreateInstance($t)
if(!$i.IsInstanceOfType($o)){throw 'Plugin instance could not be constructed.'}
$report=[ordered]@{controller_sha256=(Get-FileHash $dll).Hash.ToLowerInvariant();compatibility_library_sha256=(Get-FileHash $lib).Hash.ToLowerInvariant();library_identity=$ac.FullName;references=@($a.GetReferencedAssemblies()|ForEach-Object {$_.FullName});public_acplugin=$true;interface_binding=$true;plugin_constructed=$true;entry_point_invoked=$false;game_hooks_tested=$false;keel_runtime_tested=$false;runtime=$PSVersionTable.PSVersion.ToString()}
if(!$OutputPath){$OutputPath=Join-Path $PSScriptRoot 'Keel-ABI-CHECKS.json'};$report|ConvertTo-Json -Depth 6|Set-Content -LiteralPath $OutputPath -Encoding UTF8
$report|ConvertTo-Json -Depth 6
