using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
namespace RAN.Australis {
internal sealed class OpticalLandingSystem {
    static readonly string[] Apertures={"OLS_DatumLeft","OLS_DatumRight","OLS_Ball_High","OLS_Ball_OnSlope","OLS_Ball_Low","OLS_WaveOff"};
    readonly Dictionary<string,object> apertures=new Dictionary<string,object>();
    readonly Dictionary<string,bool> states=new Dictionary<string,bool>();
    bool initialized,failed;
    static Type Find(string name)=>AppDomain.CurrentDomain.GetAssemblies().Select(a=>a.GetType(name,false)).FirstOrDefault(t=>t!=null);
    static void Set(object value,string name,object data)=>value.GetType().GetProperty(name).SetValue(value,data);
    static object V(Type type,float x,float y,float z)=>Activator.CreateInstance(type,x,y,z);
    void Show(string name,bool enabled){
        if(states.TryGetValue(name,out bool previous)&&previous==enabled)return;
        Reflect.Call(Reflect.Get(apertures[name],"gameObject"),"SetActive",enabled);states[name]=enabled;
    }
    void Pose(LandingSignal signal,double now) {
        Show(Apertures[0],true);Show(Apertures[1],true);
        Show(Apertures[2],signal==LandingSignal.High);Show(Apertures[3],signal==LandingSignal.OnSlope);
        Show(Apertures[4],signal==LandingSignal.Low);Show(Apertures[5],signal==LandingSignal.WaveOff&&LandingSignalPolicy.WaveOffVisible(now));
    }
    public void Disable(){foreach(var kv in apertures){try{Reflect.Call(Reflect.Get(kv.Value,"gameObject"),"SetActive",false);}catch{}}failed=true;}
    void Illuminate(object tr,string name){
        // The aperture is real registered model geometry. Its own mesh bounds
        // determine the lamp's local mounting point, so an absolute vertex
        // origin cannot leave the light floating at the ship centre.
        var go=Reflect.Get(tr,"gameObject");var rendererType=Find("UnityEngine.Renderer");
        var renderers=Reflect.Call(go,"GetComponentsInChildren",rendererType,true) as IEnumerable;
        if(renderers==null)throw new InvalidOperationException("Missing optical aperture renderer "+name);
        object renderer=null;foreach(var item in renderers){renderer=item;break;}
        if(renderer==null)throw new InvalidOperationException("Empty optical aperture renderer "+name);
        var colorType=Find("UnityEngine.Color");bool green=name.StartsWith("OLS_Datum"),red=name=="OLS_WaveOff"||name=="OLS_Ball_Low";
        float r=green?.08f:1f,g=green?1f:red?.08f:.60f,b=green?.25f:.04f;
        var color=Activator.CreateInstance(colorType,r,g,b,1f);
        var material=Reflect.Get(renderer,"material");var shaderType=Find("UnityEngine.Shader");
        var shader=shaderType?.GetMethod("Find",BindingFlags.Public|BindingFlags.Static,null,new[]{typeof(string)},null)?.Invoke(null,new object[]{"Unlit/Color"});
        if(shader!=null){Set(material,"shader",shader);Set(material,"color",color);}
        else Bridge.Log("Unlit optical shader unavailable; retaining aperture material for "+name);
        // A subtle, shadowless lens light is parented to the actual aperture.
        var goType=Find("UnityEngine.GameObject");var lightType=Find("UnityEngine.Light");
        var lamp=Activator.CreateInstance(goType,new object[]{"Australis "+name+" lens light"});var lampTr=Reflect.Get(lamp,"transform");
        var rendererGo=Reflect.Get(renderer,"gameObject");
        Reflect.Call(lampTr,"SetParent",Reflect.Get(rendererGo,"transform"),false);
        var meshFilterType=Find("UnityEngine.MeshFilter");
        var filter=Reflect.Call(rendererGo,"GetComponent",meshFilterType);
        var bounds=Reflect.Get(Reflect.Get(filter,"sharedMesh"),"bounds");
        var center=Reflect.Get(bounds,"center");
        if(center==null)throw new InvalidOperationException("Missing optical aperture mesh centre "+name);
        Set(lampTr,"localPosition",center);var vector=center.GetType();Set(lampTr,"localScale",V(vector,1,1,1));
        var light=goType.GetMethod("AddComponent",new[]{typeof(Type)}).Invoke(lamp,new object[]{lightType});
        Set(light,"enabled",true);Set(light,"type",Enum.ToObject(lightType.GetProperty("type").PropertyType,2));
        Set(light,"shadows",Enum.ToObject(lightType.GetProperty("shadows").PropertyType,0));
        Set(light,"color",color);Set(light,"range",.32f/(float)BayData.MetresPerUnit);Set(light,"intensity",.30f);
    }
    void Initialize(IDictionary<string,object> models){
        foreach(string name in Apertures){if(!models.TryGetValue(name,out object tr)||tr==null)throw new InvalidOperationException("Missing mounted optical aperture "+name);apertures[name]=tr;}
        foreach(string name in Apertures){Show(name,false);Illuminate(apertures[name],name);}
        initialized=true;Bridge.Log("Optical landing indicator bound: native Approach task and deck-local aircraft position; visual guidance only");
    }
    public void Tick(object owner,object deck,IDictionary<string,object> models,double now,bool deckFoul){
        if(failed)return;
        try {
            if(!initialized)Initialize(models);
            if(!LandingSignalPolicy.Finite(now)){Pose(LandingSignal.Off,0);return;}
            var tasks=Reflect.Get(deck,"FlightDeckTasks") as IEnumerable;
            if(tasks==null){Pose(LandingSignal.Off,now);return;}
            var root=Reflect.Get(Reflect.Call(owner,"getRootGameObject"),"transform");
            double closest=double.PositiveInfinity;LandingSignal selected=LandingSignal.Off;
            foreach(object task in tasks){
                var vehicle=Reflect.Get(task,"Vehicle");var recovery=Reflect.Get(task,"_recoveryPoint");
                if(vehicle==null||recovery==null||!Convert.ToBoolean(Reflect.Get(recovery,"_isArrested")))continue;
                // Native onEnter sets the state name and isLanding flag. This
                // excludes launch/taxi, hold/circuit and helicopter tasks.
                string state=Convert.ToString(Reflect.Get(Reflect.Get(task,"_stateMachine"),"CurrentStateName"));
                if(state!="Approach"||!Convert.ToBoolean(Reflect.Get(vehicle,"isLanding")))continue;
                string kind=Convert.ToString(Reflect.Get(Reflect.Get(task,"VehicleType"),"_type"));if(kind=="Helicopter")continue;
                var world=Reflect.Call(vehicle,"getUnityPosition");
                var local=Reflect.Call(root,"InverseTransformPoint",world);var touchdown=Reflect.Get(recovery,"_position");
                if(local==null||touchdown==null)continue;
                double units=BayData.MetresPerUnit;
                double dx=(Convert.ToDouble(Reflect.Get(local,"x"))-Convert.ToDouble(Reflect.Get(touchdown,"x")))*units;
                double dz=(Convert.ToDouble(Reflect.Get(local,"z"))-Convert.ToDouble(Reflect.Get(touchdown,"z")))*units;
                double height=(Convert.ToDouble(Reflect.Get(local,"y"))-Convert.ToDouble(Reflect.Get(touchdown,"y")))*units;
                double yaw=Convert.ToDouble(Reflect.Get(recovery,"_rotation"))*Math.PI/180;
                double distance=-(dx*Math.Sin(yaw)+dz*Math.Cos(yaw));
                double cross=dx*Math.Cos(yaw)-dz*Math.Sin(yaw);
                LandingSignal signal=LandingSignalPolicy.Evaluate(distance,cross,height,deckFoul);
                if(signal!=LandingSignal.Off&&distance<closest){closest=distance;selected=signal;}
            }
            Pose(selected,now);
        } catch(Exception e){Disable();Bridge.Log("Optical landing indication disabled; native aviation retained: "+e.Message);}
    }
}
}
