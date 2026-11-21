using System;
using System.Collections;
using System.Collections.Generic;
namespace RAN.Australis {
internal sealed class ShuttleMount {
    public readonly string Name;public readonly float X,Y,Z,Yaw,Length;
    public ShuttleMount(string name,float x,float y,float z,float yaw,float length){Name=name;X=x;Y=y;Z=z;Yaw=yaw;Length=length;}
}
// A visual carriage. The native aircraft position drives the power stroke;
// only its unloaded return is timed, after the native launch task has left.
internal sealed class ShuttleCycle {
    public double Distance {get;private set;}
    double previous=double.NaN,returnStart,returnDistance;bool active,returning;
    public void Reset(){Distance=0;previous=double.NaN;active=false;returning=false;}
    public void Tick(double now,double? measuredDistance,double length){
        if(!LandingSignalPolicy.Finite(now)||!LandingSignalPolicy.Finite(length)||length<=0){Reset();return;}
        if(!double.IsNaN(previous)&&now<previous){Reset();previous=now;return;}
        previous=now;
        if(measuredDistance.HasValue&&LandingSignalPolicy.Finite(measuredDistance.Value)){
            Distance=Math.Max(0,Math.Min(length,measuredDistance.Value));active=true;returning=false;return;
        }
        if(active){active=false;returning=true;returnStart=now;returnDistance=Distance;}
        if(returning){double t=Math.Max(0,Math.Min(1,(now-returnStart)/6));double ease=t*t*(3-2*t);Distance=returnDistance*(1-ease);if(t>=1)returning=false;}
    }
}
internal sealed class CatapultShuttles {
    sealed class Live {
        public readonly ShuttleMount Spec;public readonly object Transform;public readonly ShuttleCycle Cycle=new ShuttleCycle();
        public Live(ShuttleMount spec,object transform){Spec=spec;Transform=transform;}
    }
    readonly List<Live> shuttles=new List<Live>();bool initialized,failed;
    static double Number(object value,string field)=>Convert.ToDouble(Reflect.Get(value,field));
    static void Pose(Live shuttle){
        var p=Reflect.Get(shuttle.Transform,"localPosition");double a=shuttle.Spec.Yaw*Math.PI/180,u=BayData.MetresPerUnit;
        var v=Activator.CreateInstance(p.GetType(),(float)((shuttle.Spec.X+Math.Sin(a)*shuttle.Cycle.Distance)/u),
            (float)(shuttle.Spec.Y/u),(float)((shuttle.Spec.Z+Math.Cos(a)*shuttle.Cycle.Distance)/u));
        shuttle.Transform.GetType().GetProperty("localPosition").SetValue(shuttle.Transform,v);
    }
    public void Disable(){foreach(var shuttle in shuttles){try{shuttle.Cycle.Reset();Pose(shuttle);}catch{}}failed=true;}
    void Initialize(IDictionary<string,object> models){
        foreach(var spec in CatapultShuttleData.Mounts){
            if(!models.TryGetValue(spec.Name,out object transform)||transform==null)throw new InvalidOperationException("Missing catapult carriage "+spec.Name);
            shuttles.Add(new Live(spec,transform));
        }
        initialized=true;Bridge.Log("Catapult carriages bound to native PlaneTakeOff/STOLTakeOff task positions; visual only");
    }
    public void Tick(object owner,object deck,IDictionary<string,object> models,double now){
        if(failed)return;
        try{
            if(!initialized)Initialize(models);
            var tasks=Reflect.Get(deck,"FlightDeckTasks") as IEnumerable;
            var root=Reflect.Get(Reflect.Call(owner,"getRootGameObject"),"transform");double u=BayData.MetresPerUnit;
            foreach(var shuttle in shuttles){
                double? sample=null;double length=shuttle.Spec.Length;
                if(tasks!=null)foreach(object task in tasks){
                    var point=Reflect.Get(task,"_launchPoint");var aircraft=Reflect.Get(task,"Vehicle");
                    if(point==null||aircraft==null||!Convert.ToBoolean(Reflect.Get(point,"_hasCatapult")))continue;
                    string state=Convert.ToString(Reflect.Get(Reflect.Get(task,"_stateMachine"),"CurrentStateName"));
                    if(state!="PlaneTakeOff"&&state!="STOLTakeOff")continue;
                    if(Convert.ToBoolean(Reflect.Get(aircraft,"isDestroyed")))continue;
                    var position=Reflect.Get(point,"_position");if(position==null)continue;
                    double px=Number(position,"x")*u,py=Number(position,"y")*u,pz=Number(position,"z")*u;
                    if(!LandingSignalPolicy.Finite(px)||!LandingSignalPolicy.Finite(py)||!LandingSignalPolicy.Finite(pz))continue;
                    if(Math.Abs(px-shuttle.Spec.X)>.5||Math.Abs(py-shuttle.Spec.Y)>.5||Math.Abs(pz-shuttle.Spec.Z)>.5)continue;
                    double yaw=Number(point,"_rotation"),yawError=(yaw-shuttle.Spec.Yaw+540)%360-180;
                    if(!LandingSignalPolicy.Finite(yaw)||Math.Abs(yawError)>1)continue;
                    double nativeLength=Number(point,"_catapultLength");
                    if(!LandingSignalPolicy.Finite(nativeLength)||nativeLength<=0)continue;
                    length=Math.Min(shuttle.Spec.Length,nativeLength);
                    var world=Reflect.Call(aircraft,"getUnityPosition");var local=Reflect.Call(root,"InverseTransformPoint",world);if(local==null)continue;
                    double dx=Number(local,"x")*u-px,dz=Number(local,"z")*u-pz,a=yaw*Math.PI/180;
                    double along=dx*Math.Sin(a)+dz*Math.Cos(a),cross=dx*Math.Cos(a)-dz*Math.Sin(a);
                    if(!LandingSignalPolicy.Finite(along)||!LandingSignalPolicy.Finite(cross)||Math.Abs(cross)>5||along< -5)continue;
                    sample=along;break;
                }
                shuttle.Cycle.Tick(now,sample,length);Pose(shuttle);
            }
        }catch(Exception e){Disable();Bridge.Log("Catapult carriage visualization disabled; native launches retained: "+e.Message);}
    }
}
}
