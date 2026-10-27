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
[ACPlugin("io.github.gobertron.ran-carrier.deck-controller", "RAN Australis Enclosed Deck", "0.8.2")]
public sealed class Plugin : IAnchorChainMod {
    public void TriggerEntryPoint(){Bridge.Install();}
}
internal static class Reflect {
    const BindingFlags Flags=BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Instance|BindingFlags.Static|BindingFlags.DeclaredOnly;
    static readonly Dictionary<string,FieldInfo> Fields=new Dictionary<string,FieldInfo>();
    public static FieldInfo Field(Type t,string n){string k=t.FullName+":"+n; if(Fields.TryGetValue(k,out var f))return f;
        for(var c=t;c!=null;c=c.BaseType){f=c.GetField(n,Flags);if(f!=null){Fields[k]=f;return f;}}return null;}
    public static object Get(object o,string n){if(o==null)return null;var f=Field(o.GetType(),n);if(f!=null)return f.GetValue(o);
        return o.GetType().GetProperty(n,BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Instance)?.GetValue(o);}
    public static object Call(object o,string n,params object[] a){return o.GetType().GetMethod(n,BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Instance)?.Invoke(o,a);}
    public static int Count(object x)=>x is ICollection c?c.Count:0;
}
internal sealed class Carrier {
    public readonly object Owner; public object Deck; public readonly DeckCycle Cycle=new DeckCycle();
    public readonly Dictionary<string,object> Models=new Dictionary<string,object>();
    readonly NightLights lights=new NightLights();
    readonly LiftLights liftLights=new LiftLights();
    int bindAttempts; DeckPhase logged=DeckPhase.Stowed;
    public bool Bound; public bool Fault; public Carrier(object o){Owner=o;}
    public bool Bind(){if(Bound)return true;Models.Clear();
        object go=Reflect.Call(Owner,"getRootGameObject"); if(go==null)return false;
        void Walk(object tr){string n=Convert.ToString(Reflect.Get(tr,"name"));if(n!=null&&!Models.ContainsKey(n))Models[n]=tr;
            int count=Convert.ToInt32(Reflect.Get(tr,"childCount"));for(int i=0;i<count;i++)Walk(Reflect.Call(tr,"GetChild",i));}
        Walk(Reflect.Get(go,"transform"));
        Bound=BayData.Motions.All(m=>Models.ContainsKey(m.Name));
        if(Bound)Bridge.Log("Bound "+BayData.Motions.Length+" enclosed-bay transforms on "+Convert.ToString(Reflect.Call(Owner,"getObjectIniName")));
        else if(++bindAttempts==120)Bridge.Log("Waiting for model binding; aviation/weapons locked. Missing: "+string.Join(",",BayData.Motions.Where(m=>!Models.ContainsKey(m.Name)).Select(m=>m.Name)));
        return Bound;
    }
    public bool Clear(){if(Deck==null)return false;
        // Queued tasks/hold patterns own no aircraft yet. Let committed vehicles
        // finish their native launch/recovery; do not cancel/rewrite reservations.
        var tasks=Reflect.Get(Deck,"FlightDeckTasks") as IEnumerable;
        if(tasks==null)return false;
        foreach(var task in tasks)if(Reflect.Get(task,"Vehicle")!=null)return false;
        return true;
    }
    public void Tick(double now){if(Fault)return;try{
        if(!Bind())return;liftLights.Tick(Owner,Models,now);lights.Tick(Owner,now);Cycle.Tick(now,Clear());Pose();
        if(logged!=Cycle.Phase){logged=Cycle.Phase;Bridge.Log("mission="+now.ToString("F3",System.Globalization.CultureInfo.InvariantCulture)+" phase="+logged+" flightLocked="+Cycle.FlightLocked+" lastShot="+Cycle.LastShot.ToString(System.Globalization.CultureInfo.InvariantCulture));}
    }catch(Exception e){liftLights.Disable();Fault=true;Bridge.Log("Carrier controller stopped; aviation/weapons locked: "+e);}}
    public void Pose(){foreach(var m in BayData.Motions){var tr=Models[m.Name];var p=Reflect.Get(tr,"localPosition");
        var t=p.GetType(); double f=m.Axis=='y'?Cycle.LiftFraction:Cycle.DoorFraction;
        var pos=Activator.CreateInstance(t,(float)((m.X+(m.Axis=='x'?m.Travel*f:0))/BayData.MetresPerUnit),
            (float)((m.Y+(m.Axis=='y'?m.Travel*f:0))/BayData.MetresPerUnit),
            (float)((m.Z+(m.Axis=='z'?m.Travel*f:0))/BayData.MetresPerUnit));
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
            new[]{"WeaponSystemGun","fire","0","WeaponGate","pre"},
            new[]{"WeaponSystemCIWS","FireAtTarget","0","WeaponGate","pre"},
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
        // CIWS reporting type is an extension class; resolved by signature, not namespace guess.
        var reports=game.GetTypes().SelectMany(t=>t.GetMethods(BindingFlags.Static|BindingFlags.Public|BindingFlags.NonPublic))
            .Where(m=>m.Name=="RecordCiwsRoundsFired"&&m.GetParameters().Length==3).ToArray();
        if(reports.Length!=1)throw new MissingMethodException("CIWS round report");
        for(int i=0;i<hooks.Length;i++){var hm=new HarmonyMethod(typeof(Bridge).GetMethod(hooks[i][3],BindingFlags.Static|BindingFlags.NonPublic));
            harmony.Patch(methods[i],prefix:hooks[i][4]=="pre"?hm:null,postfix:hooks[i][4]=="post"?hm:null);}
        harmony.Patch(reports[0],postfix:new HarmonyMethod(typeof(Bridge).GetMethod(nameof(CiwsShot),BindingFlags.Static|BindingFlags.NonPublic)));
        installed=true;Log("Installed 15 audited hooks. Experimental: in-game QA required.");
    }catch(Exception e){harmony?.UnpatchSelf();Log("NOT ACTIVE: "+e);}}
    static double Now()=>Convert.ToDouble(clock.Invoke(null,null));
    static Carrier For(object owner){if(owner==null)return null;var id=Convert.ToString(Reflect.Call(owner,"getObjectIniName"));
        if(!new[]{Unit,"ran_cvn_southern_cross_2030","ran_cvn_federation_2030","ran_cvn_commonwealth_2030"}.Contains(Path.GetFileNameWithoutExtension(id)))return null;return carriers.GetValue(owner,o=>new Carrier(o));}
    static Carrier SystemCarrier(object system)=>For(Reflect.Get(system,"_baseObject"));
    static Carrier DeckCarrier(object deck){var c=SystemCarrier(deck);if(c!=null)c.Deck=deck;return c;}
    static void DeckTick(object __instance){var c=DeckCarrier(__instance);c?.Tick(Now());}
    static bool LaunchGate(object __instance){var c=DeckCarrier(Reflect.Get(__instance,"_flightDeck"));if(c!=null)OrderHelicopterLifts(__instance);return c==null||(!c.Fault&&c.Bound&&!c.Cycle.FlightLocked);}

    static void OrderHelicopterLifts(object pending){
        try{
            string kind=Convert.ToString(Reflect.Get(pending,"vehicleType"));
            if(kind!="Helicopter"&&kind!="VTOL")return;
            var elevators=Reflect.Get(pending,"_elevators") as IList;
            var points=Reflect.Get(pending,"_launchPoints") as IList;
            if(elevators==null||points==null||elevators.IsReadOnly)return;
            int Rank(object e){var ids=Reflect.Get(e,"_launchPoints") as IEnumerable;if(ids==null)return 99;
                int best=99;foreach(var obj in ids){int id=Convert.ToInt32(obj);if(id<1||id>points.Count)continue;
                    var point=points[id-1];if(Convert.ToBoolean(Reflect.Get(point,"IsBusy"))||Convert.ToBoolean(Reflect.Get(point,"IsBlockedByPoint")))continue;
                    int rank=id==6?0:id==4?1:id==5?2:99;best=Math.Min(best,rank);}return best;}
            // Only this task's candidate list changes; reservations and the ship list stay native.
            var sorted=elevators.Cast<object>().OrderBy(Rank).ToArray();
            for(int i=0;i<sorted.Length;i++)elevators[i]=sorted[i];
        }catch(Exception e){Log("Pad preference unavailable; native scheduler retained: "+e.Message);}
    }
    static bool RecoveryGate(object __instance)=>LaunchGate(__instance);
    static bool WeaponGate(object __instance){var c=SystemCarrier(__instance);if(c==null)return true;
        c.Tick(Now());if(c.Fault||!c.Bound)return false;c.Cycle.Request(Now());return c.Cycle.CanFire;}
    static void Fired(object system){var c=SystemCarrier(system);c?.Cycle.Shot(Now());}
    static void GunShot(object __instance)=>Fired(Reflect.Get(__instance,"_vwsg"));
    static void CiwsShot(object[] __args){if(Convert.ToInt32(__args[2])>0)Fired(__args[1]);}
    static void CountBefore(object __instance,out int __state){__state=Reflect.Count(Reflect.Get(__instance,"_weapons"));}
    static void ContainerShot(object __instance,int __state){if(Reflect.Count(Reflect.Get(__instance,"_weapons"))<__state)Fired(Reflect.Get(__instance,"_weaponSystem"));}
    static void MagazineShot(object __instance,bool __result){if(__result)Fired(Reflect.Get(__instance,"_weaponSystem"));}
    static void ChaffBefore(object __instance,out int __state){__state=Convert.ToInt32(Reflect.Get(__instance,"_pendingRounds"));}
    static void ChaffShot(object __instance,int __state){if(Convert.ToInt32(Reflect.Get(__instance,"_pendingRounds"))<__state)Fired(Reflect.Get(__instance,"_parentSystem"));}
}
}
