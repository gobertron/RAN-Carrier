using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Collections;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using AnchorChain;
using HarmonyLib;
namespace RAN.Australis {
[ACPlugin("io.github.gobertron.ran-carrier.deck-controller", "RAN Australis Enclosed Deck", "0.10.24")]
public sealed class Plugin : IAnchorChainMod {
    public void TriggerEntryPoint(){Bridge.Install();}
}
internal sealed class Carrier {
    public readonly object Owner; public object Deck; public readonly DeckCycle Cycle=new DeckCycle();
    public readonly Dictionary<string,object> Models=new Dictionary<string,object>();
    readonly NightLights lights=new NightLights();
    readonly LiftLights liftLights=new LiftLights();
    readonly OpticalLandingSystem opticalLanding=new OpticalLandingSystem();
    readonly CatapultShuttles catapultShuttles=new CatapultShuttles();
    readonly ICCSBubble bubble=new ICCSBubble();
    readonly DeckStatus status;
    readonly RetractableCiws6 sixth=new RetractableCiws6();
    internal void ReportSix(double now,string state,string reason){status.Sixth(now,state,reason);}
    internal void SixthTraffic(){try{sixth.AviationRequest(this,Bridge.StatusNow());}catch{}}
    internal bool CiwsMayFire(object system,double now){
        var kind=sixth.Identify(this,system);
        if(kind==CiwsStationKind.OriginalFixed)return FixedCiwsMayFire(system);
        if(!Bound||Fault){StopCiwsBurst(system);return false;}
        bool allowed=kind==CiwsStationKind.RetractableSix&&sixth.MayFire(this,system,now);
        if(!allowed)StopCiwsBurst(system);return allowed;
    }
    internal bool CiwsStartAllowed(object system,double now)=>sixth.Identify(this,system)==CiwsStationKind.OriginalFixed||CiwsMayFire(system,now);
    internal void BubbleTraffic(){bubble.NotifyTraffic();}
    int bindAttempts; DeckPhase logged=DeckPhase.Stowed; string trafficSchemaError;
    readonly Dictionary<int,string> deflectorErrors=new Dictionary<int,string>();
    public bool Bound; public bool Fault; public Carrier(object o,string unit=null){Owner=o;status=new DeckStatus(unit,Bridge.Log);}
    internal void ReportAdmission(string operation,bool allowed,string error){
        try{status.Admission(operation,allowed,error,Bound,Fault,Bridge.StatusNow());}catch{}
    }
    public void ReportTraffic(string error){
        if(error!=null&&error!=trafficSchemaError)Bridge.Log("Route admission held: "+error);
        trafficSchemaError=error;
    }
    internal bool DeflectorFlat(int catapult){
        Models.TryGetValue("JBD"+catapult,out object transform);
        bool flat=DeckTraffic.DeflectorFlat(transform,catapult,out string error);
        string reason=error??(flat?null:"Deflector remains raised or displaced");
        deflectorErrors.TryGetValue(catapult,out string previous);
        if(reason!=null&&reason!=previous)Bridge.Log("Affected aviation admission held at JBD"+catapult+": "+reason);
        if(reason==null)deflectorErrors.Remove(catapult);else deflectorErrors[catapult]=reason;
        return flat&&(catapult<=2||sixth.PhysicallyStowed(this));
    }
    public bool Bind(){if(Bound)return true;Models.Clear();
        object go=Reflect.Call(Owner,"getRootGameObject"); if(go==null)return false;
        void Walk(object tr){string n=Convert.ToString(Reflect.Get(tr,"name"));if(n!=null&&!Models.ContainsKey(n))Models[n]=tr;
            int count=Convert.ToInt32(Reflect.Get(tr,"childCount"));for(int i=0;i<count;i++)Walk(Reflect.Call(tr,"GetChild",i));}
        Walk(Reflect.Get(go,"transform"));
        Bound=BindingReady(Models);
        if(Bound)Bridge.Log("Bound "+BayData.Motions.Length+" remaining enclosed-bay transforms and five fixed CIWS stations on "+Convert.ToString(Reflect.Call(Owner,"getObjectIniName")));
        else if(++bindAttempts==120)Bridge.Log("Waiting for model binding; aviation/weapons locked. Missing: "+string.Join(",",BayData.Motions.Select(m=>m.Name).Concat(FixedCiwsData.RequiredNames).Where(n=>!Models.ContainsKey(n))));
        return Bound;
    }
    internal static bool BindingReady(IDictionary<string,object> models)=>BayData.Motions.All(m=>models.ContainsKey(m.Name)) && FixedCiwsData.RequiredNames.All(models.ContainsKey);
    internal static bool ExtendsEnclosureCycle(object system)=>!NativeType(system,"SeaPower.WeaponSystemCIWS");
    internal bool FixedCiwsMayFire(object system){
        bool allowed=NativeCiwsTargetAllowed(system);
        if(!allowed)StopCiwsBurst(system);
        return allowed;
    }
    internal static bool NativeType(object value,string fullName){
        for(var type=value?.GetType();type!=null;type=type.BaseType)if(type.FullName==fullName)return true;
        return false;
    }
    internal static bool LiveTarget(object target)=>target!=null && !Convert.ToBoolean(Reflect.Get(target,"IsDestroyed")??false);
    internal bool IsNativeInboundMissile(object target){
        if(!LiveTarget(target)||!NativeType(target,"SeaPower.Missile"))return false;
        var threats=Reflect.Get(Owner,"_threats") as IEnumerable;
        if(threats!=null)foreach(var threat in threats)if(ReferenceEquals(threat,target))return true;
        return false;
    }
    internal static void StopCiwsBurst(object system){
        if(NativeType(system,"SeaPower.WeaponSystemCIWS")&&Convert.ToBoolean(Reflect.Get(system,"_isFiring")??false))Reflect.Call(system,"StopFire");
    }
    internal bool NativeCiwsTargetAllowed(object system){
        // The pinned native CIWS already selects incoming weapons in Hold.
        // Admit only a live missile in the owner's native threat list when
        // Hold is selected. No whole-ship status is changed, even temporarily.
        return Convert.ToString(Reflect.Get(Owner,"_weaponStatus"))!="Hold" ||
            IsNativeInboundMissile(Reflect.Get(system,"_currentClosestTarget"));
    }
    internal bool AutomaticDefenceDemand(){
        // These native collections already contain game-vetted threats/assignments.
        // Deploying does not change ROE, create targets or dispatch native fire.
        // In Hold, known native threats still deploy the defensive enclosure.
        string status=Convert.ToString(Reflect.Get(Owner,"_weaponStatus"));
        if(status=="Free")return true;
        if(status!="Tight" && status!="Hold")return false;
        var threats=Reflect.Get(Owner,"_threats") as IEnumerable;
        if(threats!=null)foreach(var target in threats)if(LiveTarget(target))return true;
        // Offensive/manual target assignments alone must not defeat Hold.
        if(status=="Hold")return false;
        // The audited ObjectBase maps ammunition IDs to its live weapon systems.
        var byAmmo=Reflect.Get(Owner,"_ammunitionToWeaponSystemsDictionary") as IDictionary;
        if(byAmmo!=null)foreach(var value in byAmmo.Values){
            var systems=value as IEnumerable;if(systems==null)continue;
            foreach(var system in systems)
                if(LiveTarget(Reflect.Get(system,"_currentClosestTarget")) || LiveTarget(Reflect.Get(system,"_targetObject")))return true;
        }
        return false;
    }
    public void Tick(double now){if(Fault){sixth.Tick(this,now);status.Tick(now,Bound,Fault);return;}try{
        if(!Bind()){status.Tick(now,Bound,Fault);return;}sixth.Tick(this,now);bubble.Tick(Deck,Models,now);liftLights.Tick(Owner,Models,now);lights.Tick(Owner,Models,now);if(AutomaticDefenceDemand())Cycle.Request(now);Cycle.Tick(now);Pose();opticalLanding.Tick(Owner,Deck,Models,now,false);catapultShuttles.Tick(Owner,Deck,Models,now);status.Tick(now,Bound,Fault);
        if(logged!=Cycle.Phase){logged=Cycle.Phase;Bridge.Log("mission="+now.ToString("F3",System.Globalization.CultureInfo.InvariantCulture)+" phase="+logged+" flightLocked="+Cycle.FlightLocked+" lastShot="+Cycle.LastShot.ToString(System.Globalization.CultureInfo.InvariantCulture));}
    }catch(Exception e){liftLights.Disable();lights.Disable();opticalLanding.Disable();catapultShuttles.Disable();bubble.Disable();Fault=true;status.Tick(now,Bound,Fault);Bridge.Log("Carrier controller stopped; aviation/weapons locked: "+e);}}
    public void Pose(){foreach(var m in BayData.Motions){var tr=Models[m.Name];var p=Reflect.Get(tr,"localPosition");
        var t=p.GetType();m.Position(Cycle,out double x,out double y,out double z);
        var pos=Activator.CreateInstance(t,(float)(x/BayData.MetresPerUnit),
            (float)(y/BayData.MetresPerUnit),(float)(z/BayData.MetresPerUnit));
        tr.GetType().GetProperty("localPosition").SetValue(tr,pos);
    }}
}
internal static class Bridge {
    static Assembly game; static MethodInfo clock; static Harmony harmony;
    static ConditionalWeakTable<object,Carrier> carriers=new ConditionalWeakTable<object,Carrier>();
    const string Unit="ran_cvn_australis_2030";
    static bool installed;
    internal static void Log(string s){try{File.AppendAllText(Path.Combine(Path.GetDirectoryName(typeof(Plugin).Assembly.Location),"RAN-Australis-DeckController.log"),DateTime.UtcNow.ToString("O")+" "+s+Environment.NewLine);}catch{} }
    static Type T(string name)=>game.GetType("SeaPower."+name,true);
    static MethodInfo M(string type,string name,int count){var a=T(type).GetMethods(BindingFlags.Instance|BindingFlags.Static|BindingFlags.Public|BindingFlags.NonPublic).Where(m=>m.Name==name&&m.GetParameters().Length==count).ToArray();
        if(a.Length!=1)throw new MissingMethodException(type,name+"/"+count);return a[0];}
    public static void Install(){if(installed)return;try{
        game=AppDomain.CurrentDomain.GetAssemblies().Single(a=>a.GetType("SeaPower.GameTime")!=null);
        clock=M("GameTime","get_missionElapsedTime",0); harmony=new Harmony("io.github.gobertron.ran-carrier.deck-controller");
        // Resolve ALL mandatory hooks before patching. A version mismatch leaves
        // no partially installed patch set. The installer is version-pinned too.
        var hooks=new[]{
            new[]{"FlightDeck","OnUpdate","0","DeckTick","post"},
            new[]{"HandlePendingLaunchTask","onUpdate","0","LaunchGate","pre"},
            new[]{"HoldingPattern","TryGetRecoveryPoint","1","RecoveryGate","pre"},
            new[]{"FlightDeck","launchVehicle","8","AircraftSpawned","post"},
            new[]{"Elevator","getLaunchPoint","3","PointSelection","pre"},
            new[]{"Elevator","GetRideRotation","1","LiftHeading","post"},
            new[]{"WeaponSystemGun","fire","0","WeaponGate","pre"},
            new[]{"WeaponSystemCIWS","FireAtTarget","0","WeaponGate","pre"},
            new[]{"WeaponSystemCIWS","StartFire","0","SixthStartFire","pre"},
            new[]{"WeaponSystemLauncher","launch","5","WeaponGate","pre"},
            new[]{"WeaponSystemLauncher","testLaunchWeapon","1","WeaponGate","pre"},
            new[]{"WeaponSystemChaff","launchChaff","0","WeaponGate","pre"},
            new[]{"GunBarrel","LaunchProjectile","2","GunShot","post"},
            new[]{"WeaponContainer","launch","5","CountBefore","pre"},
            new[]{"WeaponContainer","launch","5","ContainerShot","post"},
            new[]{"WeaponContainer","LaunchFromMagazine","6","MagazineShot","post"},
            new[]{"ChaffAttacher","launchChaffCloud","0","ChaffBefore","pre"},
            new[]{"ChaffAttacher","launchChaffCloud","0","ChaffShot","post"}
        };
        var methods=hooks.Select(h=>M(h[0],h[1],int.Parse(h[2]))).ToArray();
        // Every scope is restored on both normal return and native exceptions.
        var scopeHooks=new[]{new[]{"HandlePendingLaunchTask","onUpdate","0","LaunchScopeFinished"},
            new[]{"HoldingPattern","TryGetRecoveryPoint","1","RecoveryScopeFinished"},
            new[]{"Elevator","getLaunchPoint","3","PointScopeFinished"}};
        var scopeMethods=scopeHooks.Select(h=>M(h[0],h[1],int.Parse(h[2]))).ToArray();
        // CIWS reporting type is an extension class; resolved by signature, not namespace guess.
        var reports=game.GetTypes().SelectMany(t=>t.GetMethods(BindingFlags.Static|BindingFlags.Public|BindingFlags.NonPublic))
            .Where(m=>m.Name=="RecordCiwsRoundsFired"&&m.GetParameters().Length==3).ToArray();
        if(reports.Length!=1)throw new MissingMethodException("CIWS round report");
        for(int i=0;i<hooks.Length;i++){var hm=new HarmonyMethod(typeof(Bridge).GetMethod(hooks[i][3],BindingFlags.Static|BindingFlags.NonPublic));
            harmony.Patch(methods[i],prefix:hooks[i][4]=="pre"?hm:null,postfix:hooks[i][4]=="post"?hm:null);}
        for(int i=0;i<scopeHooks.Length;i++)harmony.Patch(scopeMethods[i],finalizer:new HarmonyMethod(typeof(Bridge).GetMethod(scopeHooks[i][3],BindingFlags.Static|BindingFlags.NonPublic)));
        harmony.Patch(reports[0],postfix:new HarmonyMethod(typeof(Bridge).GetMethod(nameof(CiwsShot),BindingFlags.Static|BindingFlags.NonPublic)));
        installed=true;Log("Installed audited route/lift hooks and fixed CIWS admission. CIWS require no enclosure deployment; other enclosed weapons retain their motion cycle. In-game QA required.");
    }catch(Exception e){harmony?.UnpatchSelf();Log("NOT ACTIVE: "+e);}}
    static double Now()=>Convert.ToDouble(clock.Invoke(null,null));
    internal static double StatusNow(){try{return Now();}catch{return double.NaN;}}
    static Carrier For(object owner){if(owner==null)return null;var id=Convert.ToString(Reflect.Call(owner,"getObjectIniName"));
        if(!new[]{Unit,"ran_cvn_southern_cross_2030","ran_cvn_federation_2030","ran_cvn_commonwealth_2030"}.Contains(Path.GetFileNameWithoutExtension(id)))return null;return carriers.GetValue(owner,o=>new Carrier(o,Path.GetFileNameWithoutExtension(id)));}
    static Carrier SystemCarrier(object system)=>For(Reflect.Get(system,"_baseObject"));
    static Carrier DeckCarrier(object deck){var c=SystemCarrier(deck);if(c!=null)c.Deck=deck;return c;}
    static void DeckTick(object __instance){var c=DeckCarrier(__instance);c?.Tick(Now());}
    // Weapon enclosure state does not stop aviation; traffic reservations and
    // native point/task checks still decide which individual movements fit.
    static bool FlightReady(Carrier c)=>c==null||(!c.Fault&&c.Bound);
    static bool LaunchGate(object __instance,out DeckTraffic.Scope __state){
        __state=null;var c=DeckCarrier(Reflect.Get(__instance,"_flightDeck"));
        if(c==null)return true;c.BubbleTraffic();c.SixthTraffic();if(!FlightReady(c)){c.ReportAdmission("LAUNCH",false,null);return false;}
        bool allowed=DeckTraffic.BeginLaunch(__instance,out __state,out string error,c.DeflectorFlat);c.ReportTraffic(error);c.ReportAdmission("LAUNCH",allowed,error);return allowed;
    }
    static Exception LaunchScopeFinished(Exception __exception,DeckTraffic.Scope __state)=>ScopeFinished(__exception,__state);
    static Exception ScopeFinished(Exception exception,DeckTraffic.Scope scope){
        try{DeckTraffic.Finish(scope);}catch(Exception error){var c=DeckCarrier(scope?.Deck);if(c!=null)c.Fault=true;Log("Route candidate restoration failed; new aviation held: "+error);}
        return exception;
    }
    static void AircraftSpawned(object __instance,object[] __args,object __result){
        var c=DeckCarrier(__instance);if(c==null)return;c.BubbleTraffic();c.SixthTraffic();
        try{DeckTraffic.Spawned(__instance,__args[0],__result);}catch(Exception error){c.Fault=true;Log("Route plan capture failed; new aviation held: "+error);}
    }
    static bool PointSelection(object __instance,out DeckTraffic.Scope __state){
        __state=null;var c=DeckCarrier(Reflect.Get(__instance,"_flightDeck"));if(c==null)return true;c.BubbleTraffic();c.SixthTraffic();
        bool allowed=DeckTraffic.BeginPointSelection(__instance,out __state,out string error);c.ReportTraffic(error);return allowed;
    }
    static Exception PointScopeFinished(Exception __exception,DeckTraffic.Scope __state)=>ScopeFinished(__exception,__state);
    static void LiftHeading(object __instance,object[] __args,ref float __result){
        var c=DeckCarrier(Reflect.Get(__instance,"_flightDeck"));if(c==null)return;
        if(DeckTraffic.TryRideHeading(__instance,__args[0],out float heading,out string error))__result=heading;
        if(error!=null){c.Fault=true;c.ReportTraffic(error);}
    }
    static bool RecoveryGate(object __instance,object[] __args,out DeckTraffic.Scope __state){
        __state=null;var c=DeckCarrier(Reflect.Get(__instance,"_flightDeck"));
        if(c==null)return true;c.BubbleTraffic();c.SixthTraffic();if(!FlightReady(c)){c.ReportAdmission("RECOVERY",false,null);return false;}
        bool allowed=DeckTraffic.BeginRecovery(__instance,__args[0],out __state,out string error,c.DeflectorFlat);c.ReportTraffic(error);c.ReportAdmission("RECOVERY",allowed,error);return allowed;
    }
    static Exception RecoveryScopeFinished(Exception __exception,DeckTraffic.Scope __state){
        try{DeckTraffic.FinishRecovery(__state,__exception);}catch(Exception error){
            var c=DeckCarrier(__state?.Deck);if(c!=null)c.Fault=true;Log("Recovery route capture failed; new aviation held: "+error);
        }
        return __exception;
    }
    static bool WeaponGate(object __instance){var c=SystemCarrier(__instance);if(c==null)return true;
        double now=Now();c.Tick(now);if(c.Fault||!c.Bound){Carrier.StopCiwsBurst(__instance);return false;}
        // Fixed CIWS are permanently exposed. Native targeting, ammunition,
        // fire-control and missile-only Hold admission still apply; the
        // unrelated enclosure cycle never delays or moves these guns.
        if(Carrier.NativeType(__instance,"SeaPower.WeaponSystemCIWS"))return c.CiwsMayFire(__instance,now);
        c.Cycle.Request(now);bool ready=c.Cycle.CanFire;if(!ready)Carrier.StopCiwsBurst(__instance);return ready;}
    static bool SixthStartFire(object __instance){
        var c=SystemCarrier(__instance);if(c==null)return true;
        // Only the new section receives this final guard. The original five
        // retain their native StartFire path and prior admission behavior.
        return c.CiwsStartAllowed(__instance,StatusNow());
    }
    static void Fired(object system){if(!Carrier.ExtendsEnclosureCycle(system))return;var c=SystemCarrier(system);c?.Cycle.Shot(Now());}
    static void GunShot(object __instance)=>Fired(Reflect.Get(__instance,"_vwsg"));
    static void CiwsShot(object[] __args){if(Convert.ToInt32(__args[2])>0)Fired(__args[1]);}
    static void CountBefore(object __instance,out int __state){__state=Reflect.Count(Reflect.Get(__instance,"_weapons"));}
    static void ContainerShot(object __instance,int __state){if(Reflect.Count(Reflect.Get(__instance,"_weapons"))<__state)Fired(Reflect.Get(__instance,"_weaponSystem"));}
    static void MagazineShot(object __instance,bool __result){if(__result)Fired(Reflect.Get(__instance,"_weaponSystem"));}
    static void ChaffBefore(object __instance,out int __state){__state=Convert.ToInt32(Reflect.Get(__instance,"_pendingRounds"));}
    static void ChaffShot(object __instance,int __state){if(Convert.ToInt32(Reflect.Get(__instance,"_pendingRounds"))<__state)Fired(Reflect.Get(__instance,"_parentSystem"));}
}
}
