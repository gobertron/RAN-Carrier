using System;
namespace RAN.Australis {
// Pure offline policy. No Unity, Sea Power, Harmony, logging, native state,
// scene writes or production Plugin integration participates in this class.
internal enum Ciws6Phase { Stowed, Opening, Raising, Deployed, Lowering, Closing, Fault }
internal enum CiwsStationKind { Unknown, OriginalFixed, RetractableSix }
internal sealed class Ciws6Observation {
    // Fractions must be measured from the real mechanism; command fractions
    // and elapsed animation times are never substitutes for these samples.
    internal bool FixedAxesVerified,LiftKnown,RoofKnown,ColliderPoseVerified;
    internal double Lift,RoofFore,RoofAft;
    // Complete parked/taxi/recovery/departing-aircraft coverage is required.
    // A task or point disappearing alone does not establish TrafficClear.
    internal bool TrafficKnown,TrafficClear,AviationDemand;
    internal bool ControllerHealthy,StationIdentityVerified,NativeFiringOriginVerified,NativeDefenceDemand;
}
internal sealed class Ciws6Policy {
    internal const double QuietSeconds=2,AviationLeaseSeconds=2,DefenceHoldSeconds=5,PoseTolerance=.001;
    internal Ciws6Phase Phase {get;private set;}=Ciws6Phase.Stowed;
    // Targets only. The later verified adapter must move toward unchanged
    // targets at a bounded rate rather than restarting a timed animation.
    // null holds lift movement until the roof is positively open.
    internal double? LiftTarget {get;private set;}=0;
    internal double RoofTarget {get;private set;}
    internal bool CanFire {get;private set;}
    internal bool StopFireRequested=>!CanFire;
    internal bool AviationClear {get;private set;}
    internal string Reason {get;private set;}="STARTUP";
    double previous=double.NaN,quietSince=double.NaN,aviationUntil=double.NegativeInfinity,lastDefence=double.NegativeInfinity;
    bool invalidAviationClock;
    static bool Finite(double value)=>!double.IsNaN(value)&&!double.IsInfinity(value);
    static bool Fraction(double value)=>Finite(value)&&value>=-PoseTolerance&&value<=1+PoseTolerance;
    static bool Near(double value,double target)=>Math.Abs(value-target)<=PoseTolerance;
    internal bool HasDefenceHold(double now)=>Finite(now)&&now-lastDefence<=DefenceHoldSeconds;
    internal void AviationRequest(double now){
        quietSince=double.NaN;
        if(Finite(now)&&now>=0)aviationUntil=Math.Max(aviationUntil,now+AviationLeaseSeconds);
        else invalidAviationClock=true;
        // A fresh measured-pose tick is mandatory before admitting an
        // affected movement, even if the last sample was physically stowed.
        CanFire=false;AviationClear=false;
    }
    void Stow(bool liftKnown,bool liftStowed,bool roofsOpen,bool roofsClosed,bool fault){
        if(liftKnown&&liftStowed){LiftTarget=0;RoofTarget=0;Phase=roofsClosed?Ciws6Phase.Stowed:Ciws6Phase.Closing;}
        else if(roofsOpen){LiftTarget=0;RoofTarget=1;Phase=Ciws6Phase.Lowering;}
        else{LiftTarget=null;RoofTarget=1;Phase=Ciws6Phase.Opening;}
        if(fault)Phase=Ciws6Phase.Fault;
    }
    internal void Tick(double now,Ciws6Observation sample){
        CanFire=false;AviationClear=false;
        bool liftKnown=sample!=null&&sample.FixedAxesVerified&&sample.LiftKnown&&Fraction(sample.Lift);
        bool roofKnown=sample!=null&&sample.FixedAxesVerified&&sample.RoofKnown&&Fraction(sample.RoofFore)&&Fraction(sample.RoofAft);
        bool liftStowed=liftKnown&&Near(sample.Lift,0),liftRaised=liftKnown&&Near(sample.Lift,1);
        bool roofsClosed=roofKnown&&Near(sample.RoofFore,0)&&Near(sample.RoofAft,0);
        bool roofsOpen=roofKnown&&Near(sample.RoofFore,1)&&Near(sample.RoofAft,1);
        AviationClear=liftStowed&&roofsClosed&&sample.ColliderPoseVerified;
        bool clock=Finite(now)&&now>=0&&!invalidAviationClock,rewind=clock&&!double.IsNaN(previous)&&now<previous;
        invalidAviationClock=false;
        if(!clock||rewind){quietSince=double.NaN;lastDefence=double.NegativeInfinity;aviationUntil=double.NegativeInfinity;}
        previous=clock?now:double.NaN;
        string fault=!clock?"CLOCK_UNVERIFIED":sample==null?"OBSERVATION_MISSING":
            !sample.ControllerHealthy?"CONTROLLER_FAULT":!sample.StationIdentityVerified?"STATION_IDENTITY_UNVERIFIED":!sample.NativeFiringOriginVerified?"FIRING_ORIGIN_UNVERIFIED":
            !liftKnown||!roofKnown?"MECHANISM_POSE_UNVERIFIED":!sample.ColliderPoseVerified?"COLLIDER_POSE_UNVERIFIED":null;
        if(fault!=null){quietSince=double.NaN;Reason=fault;Stow(liftKnown,liftStowed,roofsOpen,roofsClosed,true);return;}
        if(sample.NativeDefenceDemand)lastDefence=now;
        bool traffic=!sample.TrafficKnown||!sample.TrafficClear||sample.AviationDemand||now<aviationUntil;
        if(traffic||rewind){
            quietSince=double.NaN;Reason=rewind?"CLOCK_REWIND":!sample.TrafficKnown?"AIRCRAFT_CLEARANCE_UNVERIFIED":
                !sample.TrafficClear?"AIRCRAFT_SWEEP_OCCUPIED":"AVIATION_DEMAND";
            Stow(liftKnown,liftStowed,roofsOpen,roofsClosed,false);return;
        }
        if(double.IsNaN(quietSince))quietSince=now;
        bool demand=sample.NativeDefenceDemand||now-lastDefence<=DefenceHoldSeconds;
        if(!demand||now-quietSince<QuietSeconds){
            Reason=!demand?"NO_NATIVE_DEFENCE_DEMAND":"QUIET_DWELL";
            Stow(liftKnown,liftStowed,roofsOpen,roofsClosed,false);return;
        }
        RoofTarget=1;
        if(!roofsOpen){LiftTarget=null;Phase=Ciws6Phase.Opening;Reason="OPENING_ROOF";return;}
        LiftTarget=1;
        if(!liftRaised){Phase=Ciws6Phase.Raising;Reason="RAISING_STATION";return;}
        Phase=Ciws6Phase.Deployed;Reason="VERIFIED_DEPLOYED";CanFire=sample.NativeDefenceDemand;
    }
    internal static bool WeaponAllowed(CiwsStationKind station,bool existingNativeGuard,bool sixReady)=>
        station==CiwsStationKind.OriginalFixed?existingNativeGuard:
        station==CiwsStationKind.RetractableSix&&existingNativeGuard&&sixReady;
}
}
