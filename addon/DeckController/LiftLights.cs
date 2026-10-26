using System;
using System.Linq;
using System.Reflection;
using System.Collections.Generic;
namespace RAN.Australis {
internal sealed class LiftLamp {
    public readonly float X,Y,Z,Pitch,Yaw,R,G,B,Range,Intensity,Angle;
    public LiftLamp(float x,float y,float z,float pitch,float yaw,float r,float g,float b,float range,float intensity,float angle){
        X=x;Y=y;Z=z;Pitch=pitch;Yaw=yaw;R=r;G=g;B=b;Range=range;Intensity=intensity;Angle=angle;
    }
}
internal sealed class LiftLampGroup {
    public readonly string Model; public readonly LiftLamp[] Fixtures;
    public LiftLampGroup(string model,LiftLamp[] fixtures){Model=model;Fixtures=fixtures;}
}
internal sealed class LiftLights {
    sealed class Live {
        public readonly LiftLampGroup Spec;public readonly List<object> Lights=new List<object>();
        public float LastGain=-1;public Live(LiftLampGroup spec){Spec=spec;}
    }
    readonly List<Live> groups=new List<Live>();bool initialized,failed;
    static Type Find(string name)=>AppDomain.CurrentDomain.GetAssemblies().Select(a=>a.GetType(name,false)).FirstOrDefault(t=>t!=null);
    static object V(Type type,float x,float y,float z)=>Activator.CreateInstance(type,x,y,z);
    static void Set(object obj,string name,object value)=>obj.GetType().GetProperty(name).SetValue(obj,value);
    static void Off(Live group){foreach(var light in group.Lights){try{Set(light,"enabled",false);Set(light,"intensity",0f);}catch{}}group.LastGain=-1;}
    void OffAll(){foreach(var group in groups)Off(group);}
    public void Disable(){OffAll();failed=true;}
    void Initialize(object owner){
        var goType=Find("UnityEngine.GameObject");var lightType=Find("UnityEngine.Light");var color=Find("UnityEngine.Color");
        var root=Reflect.Get(Reflect.Call(owner,"getRootGameObject"),"transform");
        var vector=Reflect.Get(root,"localPosition").GetType();
        foreach(var spec in LiftLightingData.Groups){
            var live=new Live(spec);groups.Add(live);
            foreach(var lamp in spec.Fixtures){
                var go=Activator.CreateInstance(goType,new object[]{"Australis "+spec.Model+" wall light"});
                var tr=Reflect.Get(go,"transform");Set(tr,"parent",root);
                Set(tr,"localPosition",V(vector,lamp.X/(float)BayData.MetresPerUnit,lamp.Y/(float)BayData.MetresPerUnit,lamp.Z/(float)BayData.MetresPerUnit));
                Set(tr,"localEulerAngles",V(vector,lamp.Pitch,lamp.Yaw,0));
                var light=goType.GetMethod("AddComponent",new[]{typeof(Type)}).Invoke(go,new object[]{lightType});
                live.Lights.Add(light);Set(light,"enabled",false);Set(light,"intensity",0f);
                Set(light,"type",Enum.ToObject(lightType.GetProperty("type").PropertyType,0)); // Spot
                Set(light,"shadows",Enum.ToObject(lightType.GetProperty("shadows").PropertyType,0));
                Set(light,"color",Activator.CreateInstance(color,lamp.R,lamp.G,lamp.B,1f));
                Set(light,"range",lamp.Range/(float)BayData.MetresPerUnit);Set(light,"spotAngle",lamp.Angle);
            }
        }
        initialized=true;Bridge.Log("Created lift wall lights: "+groups.Sum(g=>g.Lights.Count)+" spots; actual lift height controls off/fade, independent of night lamps");
    }
    public void Tick(object owner,IDictionary<string,object> models,double now){
        if(failed)return;
        try{
            if(!initialized)Initialize(owner);
            // Always read current transforms, including paused/manual motion or a
            // mission-time reset. This must not use NightLights' .75 s throttle.
            foreach(var group in groups){
                float gain=0;
                try{
                    if(models!=null&&models.TryGetValue(group.Spec.Model,out var tr)&&tr!=null){
                        var position=Reflect.Get(tr,"localPosition");
                        gain=LiftLightPolicy.Gain(Convert.ToDouble(Reflect.Get(position,"y"))*BayData.MetresPerUnit);
                    }
                }catch{gain=0;}
                if(gain==group.LastGain)continue;
                for(int i=0;i<group.Lights.Count;i++){
                    var light=group.Lights[i];Set(light,"intensity",group.Spec.Fixtures[i].Intensity*gain);Set(light,"enabled",gain>0);
                }
                group.LastGain=gain;
            }
        }catch(Exception e){OffAll();failed=true;Bridge.Log("Lift lighting disabled; deck controller retained: "+e.Message);}
    }
}
}
