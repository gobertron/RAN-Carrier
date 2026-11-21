using System;
using System.Collections;
using System.Collections.Generic;
using System.Reflection;
namespace RAN.Australis {
// The sixth station alone owns this mechanism. Native head yaw/pitch and all
// five original fixed stations remain outside its transform writes.
internal sealed class RetractableCiws6 {
    internal const double Units=68.628171085208,LiftTravel=6,RoofTravel=3.1,LiftSeconds=3,RoofSeconds=1;
    internal const string Section="WeaponSystem24",Root="CIWS_6_LiftRoot",Fore="CIWS_6_Roof_Fore",Aft="CIWS_6_Roof_Aft";
    static readonly Ciws6SweepVolume Sweep=new Ciws6SweepVolume(-54,12.3,142,-46,26,157);
    readonly Ciws6Policy policy=new Ciws6Policy();
    readonly Ciws6ColliderSync colliders=new Ciws6ColliderSync();
    object lift,fore,aft,frame,six;bool bound,fault,featureSeen;string error;double previous=double.NaN;
    internal Ciws6Phase Phase=>policy.Phase;
    internal string Reason=>error??policy.Reason;
    internal bool Enabled(Carrier c){
        if(featureSeen)return true;
        if(c.Models.ContainsKey(Root)||c.Models.ContainsKey("CIWS_Mount_6")||c.Models.ContainsKey("CIWS_Gun_6")||c.Models.ContainsKey(Fore)||c.Models.ContainsKey(Aft))return featureSeen=true;
        try{if(Reflect.Get(c.Owner,"_ammunitionToWeaponSystemsDictionary") is IDictionary map)foreach(var value in map.Values)if(value is IEnumerable systems)
            foreach(var system in systems)if(Convert.ToString(Reflect.Get(system,"_sectionName"))==Section)return featureSeen=true;}catch{}
        return false;
    }
    static object Required(object owner,string name){
        var value=Reflect.Get(owner,name);if(value==null)throw new InvalidOperationException("Missing CIWS6 member "+name);return value;
    }
    static double Number(object value,string axis)=>Convert.ToDouble(Required(value,axis));
    static bool Finite(double value)=>!double.IsNaN(value)&&!double.IsInfinity(value);
    static bool Close(double a,double b,double tolerance=.005)=>Finite(a)&&Math.Abs(a-b)<=tolerance;
    static object Transform(object gameObject)=>Required(gameObject,"transform");
    static bool SameTransform(object gameObject,object transform)=>gameObject!=null&&ReferenceEquals(Reflect.Get(gameObject,"transform"),transform);
    internal CiwsStationKind Identify(Carrier c,object system){
        try{
            if(!Carrier.NativeType(system,"SeaPower.WeaponSystemCIWS")||!ReferenceEquals(Reflect.Get(system,"_baseObject"),c.Owner))return CiwsStationKind.Unknown;
            string section=Convert.ToString(Reflect.Get(system,"_sectionName"));var mount=Reflect.Get(system,"_mountObject");
            for(int i=1;i<=5;i++)if(section=="WeaponSystem"+(i+8)&&c.Models.TryGetValue("CIWS_Mount_"+i,out object original)&&SameTransform(mount,original))return CiwsStationKind.OriginalFixed;
            if(section!=Section||!c.Models.TryGetValue("CIWS_Mount_6",out object expectedMount)||!SameTransform(mount,expectedMount))return CiwsStationKind.Unknown;
            var attacher=Reflect.Get(system,"_ciws");
            if(attacher==null||!ReferenceEquals(Reflect.Get(attacher,"_baseSystem"),system)||!ReferenceEquals(Reflect.Get(attacher,"_baseObject"),c.Owner)||
                !c.Models.TryGetValue("CIWS_Gun_6",out object gun)||!SameTransform(Reflect.Get(attacher,"_gunObject"),gun))return CiwsStationKind.Unknown;
            if(!c.Models.TryGetValue(Root,out object root)||!ReferenceEquals(Reflect.Get(expectedMount,"parent"),root)||!ReferenceEquals(Reflect.Get(gun,"parent"),expectedMount))return CiwsStationKind.Unknown;
            var mountPivot=Required(expectedMount,"localPosition");var gunPivot=Required(gun,"localPosition");
            if(!Close(Number(mountPivot,"x")*Units,0)||!Close(Number(mountPivot,"y")*Units,2.7)||!Close(Number(mountPivot,"z")*Units,0)||
                !Close(Number(gunPivot,"x")*Units,0)||!Close(Number(gunPivot,"y")*Units,0)||!Close(Number(gunPivot,"z")*Units,0))return CiwsStationKind.Unknown;
            foreach(var tr in new[]{expectedMount,gun})foreach(var axis in new[]{"x","y","z"})if(!Close(Number(Required(tr,"localScale"),axis),1,.0001))return CiwsStationKind.Unknown;
            var parameters=Reflect.Get(system,"_vwp");
            if(parameters==null||!ReferenceEquals(Reflect.Get(attacher,"_vwp"),parameters)||!ReferenceEquals(Reflect.Get(parameters,"_weaponSystem"),system)||
                !ReferenceEquals(Reflect.Get(parameters,"_mountObject"),mount)||Convert.ToString(Reflect.Get(parameters,"_sectionName"))!=Section)return CiwsStationKind.Unknown;
            return CiwsStationKind.RetractableSix;
        }catch{return CiwsStationKind.Unknown;}
    }
    bool Bind(Carrier c){
        if(!Enabled(c))return false;
        if(!bound){
            lift=c.Models[Root];fore=c.Models[Fore];aft=c.Models[Aft];frame=Required(lift,"parent");
            if(!ReferenceEquals(Reflect.Get(fore,"parent"),frame)||!ReferenceEquals(Reflect.Get(aft,"parent"),frame))throw new InvalidOperationException("CIWS6 model frames differ");bound=true;
        }
        if(six==null)try{
            object candidate=null;
            var byAmmo=Required(c.Owner,"_ammunitionToWeaponSystemsDictionary") as IDictionary;
            if(byAmmo==null)throw new InvalidOperationException("CIWS6 native weapon map unavailable");
            foreach(var value in byAmmo.Values){
                if(!(value is IEnumerable systems))throw new InvalidOperationException("CIWS6 native system list unavailable");
                foreach(var system in systems)if(Identify(c,system)==CiwsStationKind.RetractableSix){
                    if(candidate!=null&&!ReferenceEquals(candidate,system)){
                        fault=true;Carrier.StopCiwsBurst(candidate);Carrier.StopCiwsBurst(system);
                        throw new InvalidOperationException("Ambiguous CIWS6 native station");
                    }candidate=system;
                }
            }
            six=candidate;
        }catch(Exception e){error=e.GetBaseException().Message;}
        return true;
    }
    static bool PoseAxes(object transform,double x,double y,double z,bool checkY){
        var p=Required(transform,"localPosition");var a=Required(transform,"localEulerAngles");var scale=Required(transform,"localScale");
        Func<double,bool> zero=v=>Finite(v)&&Math.Abs(Math.IEEERemainder(v,360))<=.1;
        return Close(Number(p,"x")*Units,x)&&(!checkY||Close(Number(p,"y")*Units,y))&&Close(Number(p,"z")*Units,z)&&
            zero(Number(a,"x"))&&zero(Number(a,"y"))&&zero(Number(a,"z"))&&Close(Number(scale,"x"),1,.0001)&&Close(Number(scale,"y"),1,.0001)&&Close(Number(scale,"z"),1,.0001);
    }
    Ciws6Observation Observe(Carrier c,bool aviation,bool includeTraffic,double now){
        var sample=new Ciws6Observation{ControllerHealthy=c.Bound&&!c.Fault&&!fault,StationIdentityVerified=six!=null&&Identify(c,six)==CiwsStationKind.RetractableSix};
        try{
            var lp=Required(lift,"localPosition");var fp=Required(fore,"localPosition");var ap=Required(aft,"localPosition");
            sample.Lift=(Number(lp,"y")*Units-13.2)/LiftTravel;
            sample.RoofFore=(Number(fp,"z")*Units-151.05)/RoofTravel;sample.RoofAft=(147.95-Number(ap,"z")*Units)/RoofTravel;
            // Sliding roof Z is variable; all other pose axes are checked.
            var fa=Required(fore,"localEulerAngles");var aa=Required(aft,"localEulerAngles");var fs=Required(fore,"localScale");var ass=Required(aft,"localScale");
            bool roofAxes=Close(Number(fp,"x")*Units,-50)&&Close(Number(ap,"x")*Units,-50)&&Close(Number(fp,"y")*Units,19.15)&&Close(Number(ap,"y")*Units,19.15);
            foreach(var v in new[]{fa,aa})foreach(var axis in new[]{"x","y","z"})roofAxes&=Close(Math.IEEERemainder(Number(v,axis),360),0,.1);
            foreach(var v in new[]{fs,ass})foreach(var axis in new[]{"x","y","z"})roofAxes&=Close(Number(v,axis),1,.0001);
            sample.FixedAxesVerified=PoseAxes(lift,-50,0,149.5,false)&&roofAxes;
            sample.LiftKnown=Fraction(sample.Lift);sample.RoofKnown=Fraction(sample.RoofFore)&&Fraction(sample.RoofAft);
            bool deployed=Close(sample.Lift,1,.001)&&Close(sample.RoofFore,1,.001)&&Close(sample.RoofAft,1,.001);
            sample.ColliderPoseVerified=colliders.Verify(c.Owner,frame,sample.Lift*LiftTravel,deployed,out string colliderError);
            if(!sample.ColliderPoseVerified)error=colliderError;
            sample.NativeFiringOriginVerified=sample.StationIdentityVerified&&colliders.VerifyAimPoint(c.Owner,frame,six,sample.Lift*LiftTravel,out string aimError);
            if(!sample.NativeFiringOriginVerified&&sample.StationIdentityVerified)error="Native sixth firing origin unverified";
            sample.AviationDemand=aviation||NativeAviationDemand(c.Deck);
            sample.NativeDefenceDemand=sample.StationIdentityVerified&&Carrier.LiveTarget(Reflect.Get(six,"_currentClosestTarget"))&&c.NativeCiwsTargetAllowed(six);
            if(includeTraffic&&(sample.NativeDefenceDemand||policy.HasDefenceHold(now)||sample.Lift>.001||sample.RoofFore>.001||sample.RoofAft>.001)&&!sample.AviationDemand){
                sample.TrafficClear=Ciws6AircraftClearance.Clear(c.Owner,c.Deck,frame,Sweep,out string trafficError);sample.TrafficKnown=sample.TrafficClear;
                if(!sample.TrafficClear)error=trafficError;
            }else{sample.TrafficKnown=true;sample.TrafficClear=!sample.AviationDemand;}
        }catch(Exception e){sample.FixedAxesVerified=false;error=e.GetBaseException().Message;}
        return sample;
    }
    static bool NativeAviationDemand(object deck){
        foreach(var name in new[]{"FlightDeckTasks","_flightDeckTasksToAdd"}){
            if(!(Required(deck,name) is IEnumerable tasks))throw new InvalidOperationException("CIWS6 native aviation tasks unavailable");
            foreach(var task in tasks)return true;
        }
        var launches=Required(deck,"_launchPoints") as IList;var recoveries=Required(deck,"_recoveryPoints") as IList;
        if(launches==null||launches.Count!=7||recoveries==null||recoveries.Count!=4)throw new InvalidOperationException("CIWS6 native flight point schema unavailable");
        for(int i=2;i<=3;i++)if(Convert.ToBoolean(Required(launches[i],"IsBusy")))return true;
        foreach(var point in recoveries)if(Convert.ToBoolean(Required(point,"IsBusy")))return true;
        return false;
    }
    void Stop(){if(six!=null)Carrier.StopCiwsBurst(six);}
    static double Move(double value,double target,double step)=>value<target?Math.Min(target,value+step):Math.Max(target,value-step);
    static bool Fraction(double value)=>Finite(value)&&value>=-.001&&value<=1.001;
    static void Safety(Ciws6Observation from,Ciws6Observation to){to.TrafficKnown=from.TrafficKnown;to.TrafficClear=from.TrafficClear;to.AviationDemand=from.AviationDemand;}
    static void Position(object transform,double x,double y,double z){
        if(!Finite(x)||!Finite(y)||!Finite(z))throw new InvalidOperationException("Invalid CIWS6 pose write rejected");
        var old=Required(transform,"localPosition");var value=Activator.CreateInstance(old.GetType(),(float)(x/Units),(float)(y/Units),(float)(z/Units));
        var p=transform.GetType().GetProperty("localPosition");if(p==null||!p.CanWrite)throw new InvalidOperationException("CIWS6 position is not writable");p.SetValue(transform,value);
    }
    internal void Tick(Carrier c,double now,bool aviation=false){
        if(!Enabled(c))return;
        try{
            error=null;if(!Bind(c)){Stop();return;}
            double dt=Finite(now)&&Finite(previous)&&now>=previous?now-previous:0;previous=now;
            var sample=Observe(c,aviation,true,now);
            // Repair only the proven per-instance proxies, after stopping the
            // sixth native burst. Original five systems are never visited.
            if(!sample.ColliderPoseVerified&&sample.FixedAxesVerified){
                Stop();bool full=Close(sample.Lift,1,.001)&&Close(sample.RoofFore,1,.001)&&Close(sample.RoofAft,1,.001);
                if(colliders.Sync(c.Owner,frame,sample.Lift*LiftTravel,full,out string why)){error=null;var refreshed=Observe(c,aviation,false,now);Safety(sample,refreshed);sample=refreshed;}else error=why;
            }
            if(!sample.NativeFiringOriginVerified&&sample.FixedAxesVerified&&sample.StationIdentityVerified){
                Stop();if(colliders.SyncAimPoint(c.Owner,frame,six,sample.Lift*LiftTravel,out string why)){
                    error=null;var refreshed=Observe(c,aviation,false,now);Safety(sample,refreshed);sample=refreshed;
                }else error=why;
            }
            policy.Tick(now,sample);
            double nextLift=sample.LiftKnown&&policy.LiftTarget.HasValue?Move(sample.Lift,policy.LiftTarget.Value,dt/LiftSeconds):sample.Lift;
            double nextFore=Fraction(sample.RoofFore)?Move(sample.RoofFore,policy.RoofTarget,dt/RoofSeconds):sample.RoofFore;
            double nextAft=Fraction(sample.RoofAft)?Move(sample.RoofAft,policy.RoofTarget,dt/RoofSeconds):sample.RoofAft;
            bool moveLift=sample.LiftKnown&&policy.LiftTarget.HasValue&&!Close(nextLift,sample.Lift,.00000001);
            bool moveFore=Fraction(sample.RoofFore)&&!Close(nextFore,sample.RoofFore,.00000001),moveAft=Fraction(sample.RoofAft)&&!Close(nextAft,sample.RoofAft,.00000001);
            bool moving=moveLift||moveFore||moveAft;
            if(!policy.CanFire||moving)Stop();
            if(sample.FixedAxesVerified&&moving){
                if(moveLift)Position(lift,-50,13.2+LiftTravel*nextLift,149.5);
                if(moveFore)Position(fore,-50,19.15,151.05+RoofTravel*nextFore);
                if(moveAft)Position(aft,-50,19.15,147.95-RoofTravel*nextAft);
                bool full=Close(nextLift,1,.001)&&Close(nextFore,1,.001)&&Close(nextAft,1,.001);
                if(!colliders.Sync(c.Owner,frame,nextLift*LiftTravel,full,out string why))error=why;
                if(six!=null&&!colliders.SyncAimPoint(c.Owner,frame,six,nextLift*LiftTravel,out string aimWhy))error=aimWhy;
            }
            var final=Observe(c,aviation,false,now);Safety(sample,final);policy.Tick(now,final);
            c.ReportSix(now,policy.Phase.ToString().ToUpperInvariant(),Reason);
        }catch(Exception e){fault=true;error=e.GetBaseException().Message;try{Stop();}catch{}try{colliders.Disable();}catch{}c.ReportSix(now,"FAULT",error);}
    }
    internal void AviationRequest(Carrier c,double now){
        if(!Enabled(c))return;
        policy.AviationRequest(now);try{Stop();}catch{fault=true;}Tick(c,now,true);
    }
    internal bool PhysicallyStowed(Carrier c){
        if(!Enabled(c))return true;
        try{if(!Bind(c))return false;var s=Observe(c,true,false,Bridge.StatusNow());policy.Tick(Bridge.StatusNow(),s);return policy.AviationClear;}catch{return false;}
    }
    internal bool MayFire(Carrier c,object system,double now){
        if(Identify(c,system)!=CiwsStationKind.RetractableSix)return false;
        if(six!=null&&!ReferenceEquals(six,system)){fault=true;try{Stop();}catch{}return false;}
        Tick(c,now);return ReferenceEquals(six,system)&&!fault&&policy.CanFire&&Identify(c,system)==CiwsStationKind.RetractableSix&&c.NativeCiwsTargetAllowed(system);
    }
}
}
