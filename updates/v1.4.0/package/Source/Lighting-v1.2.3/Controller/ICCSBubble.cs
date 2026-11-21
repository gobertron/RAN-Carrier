using System;
using System.Collections;
using System.Collections.Generic;
using System.Reflection;
namespace RAN.Australis {
// Visual lift only: never alters launch/recovery/weapon orders or reservations.
internal sealed class ICCSBubbleCycle {
    internal const double QuietSeconds=2, RaiseSeconds=3;
    internal double Fraction {get;private set;}
    double quietSince=double.NaN,previous=double.NaN;
    internal void Block(){Fraction=0;quietSince=double.NaN;}
    internal void Tick(double now,bool positivelyClear){
        if(!LandingSignalPolicy.Finite(now)||now<0){Block();previous=double.NaN;return;}
        if(!double.IsNaN(previous)&&now<previous){Block();previous=now;return;}
        previous=now;
        if(!positivelyClear){Block();return;}
        if(double.IsNaN(quietSince))quietSince=now;
        double f=Math.Max(0,Math.Min(1,(now-quietSince-QuietSeconds)/RaiseSeconds));
        Fraction=f*f*(3-2*f);
    }
}
internal sealed class ICCSBubble {
    internal const string NodeName="ICCS_Bubble_Lift";
    internal const double MetresPerUnit=68.628171085208,RiseMetres=1.05;
    internal const double StowedX=-10.5,StowedY=22,StowedZ=118;
    readonly ICCSBubbleCycle cycle=new ICCSBubbleCycle();
    object transform;Type vectorType;PropertyInfo position;
    bool disabled;string previousReason;
    internal double Fraction=>cycle.Fraction;
    static object Required(object owner,string name){
        if(owner==null)throw new InvalidOperationException("Missing owner for "+name);
        var field=Reflect.Field(owner.GetType(),name);if(field!=null)return field.GetValue(owner);
        const BindingFlags flags=BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Instance|BindingFlags.DeclaredOnly;
        for(var t=owner.GetType();t!=null;t=t.BaseType){
            var p=t.GetProperty(name,flags);
            if(p!=null&&p.CanRead&&p.GetIndexParameters().Length==0)return p.GetValue(owner);
        }
        throw new MissingMemberException(owner.GetType().FullName,name);
    }
    static bool Flag(object owner,string name)=>Required(owner,name) is bool v?v:throw new InvalidOperationException("Missing native boolean "+name);
    static bool Empty(object owner,string name){
        var values=Required(owner,name) as IEnumerable;
        if(values==null)throw new InvalidOperationException("Missing native collection "+name);
        foreach(var unused in values)return false;
        return true;
    }
    internal static bool PositivelyClear(object deck,out string reason){
        reason=null;
        try{
            // Proven native task collections. Even a null entry holds the lift down.
            foreach(var name in new[]{"FlightDeckTasks","_flightDeckTasksToAdd"})
                if(!Empty(deck,name)){reason="Native flight task present";return false;}
            string[] names={"_elevators","_launchPoints","_recoveryPoints"};int[] counts={4,7,4};
            for(int group=0;group<names.Length;group++){
                var points=Required(deck,names[group]) as IList;
                if(points==null||points.Count!=counts[group])throw new InvalidOperationException("Native flight point schema unavailable");
                foreach(var point in points){
                    if(point==null)throw new InvalidOperationException("Native flight point missing");
                    if(Flag(point,"IsBusy")||Flag(point,"IsOccupied")||Required(point,"OccupyingObject")!=null||!Empty(point,"_incomingObjects")){
                        reason="Native flight point reserved or occupied";return false;
                    }
                }
            }
            return true;
        }catch(Exception e){reason="Unverified deck state: "+e.GetBaseException().Message;return false;}
    }
    bool Bind(IDictionary<string,object> models){
        if(transform!=null)return true;
        if(models==null||!models.TryGetValue(NodeName,out object tr)||tr==null)return false;
        var p=Reflect.Get(tr,"localPosition");if(p==null)throw new InvalidOperationException("ICCS localPosition unavailable");
        double x=Convert.ToDouble(Required(p,"x"))*MetresPerUnit,y=Convert.ToDouble(Required(p,"y"))*MetresPerUnit,z=Convert.ToDouble(Required(p,"z"))*MetresPerUnit;
        if(!LandingSignalPolicy.Finite(x)||!LandingSignalPolicy.Finite(y)||!LandingSignalPolicy.Finite(z)||Math.Abs(x-StowedX)>.05||Math.Abs(y-StowedY)>.05||Math.Abs(z-StowedZ)>.05)
            throw new InvalidOperationException("ICCS stowed pose differs from validated geometry");
        var prop=tr.GetType().GetProperty("localPosition");
        if(prop==null||!prop.CanWrite)throw new InvalidOperationException("ICCS localPosition is not writable");
        transform=tr;vectorType=p.GetType();position=prop;Pose();
        Bridge.Log("ICCS visual bubble bound: quiet-deck rise and immediate traffic stow; native catapults unchanged");return true;
    }
    void Pose(){
        if(transform==null)return;
        var p=Activator.CreateInstance(vectorType,(float)(StowedX/MetresPerUnit),(float)((StowedY+RiseMetres*cycle.Fraction)/MetresPerUnit),(float)(StowedZ/MetresPerUnit));
        position.SetValue(transform,p);
    }
    internal void NotifyTraffic(){cycle.Block();try{Pose();}catch(Exception){disabled=true;}}
    internal void Disable(){NotifyTraffic();disabled=true;}
    internal void Tick(object deck,IDictionary<string,object> models,double now){
        if(disabled)return;
        try{
            if(!Bind(models)){cycle.Block();return;}
            bool clear=PositivelyClear(deck,out string reason);cycle.Tick(now,clear);Pose();
            if(reason!=null&&reason!=previousReason)Bridge.Log("ICCS bubble stowed: "+reason);
            previousReason=reason;
        }catch(Exception e){Disable();Bridge.Log("ICCS visual lift disabled/stowed; native flight rules retained: "+e.GetBaseException().Message);}
    }
}
}
