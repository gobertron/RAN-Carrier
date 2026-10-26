using System;using System.Linq;using System.Reflection;using System.Collections.Generic;
namespace RAN.Australis {
internal sealed class Lamp {public float X,Y,Z,R,G,B,Range,Intensity;public bool Down;public Lamp(float x,float y,float z,float r,float g,float b,float range,float intensity,bool down){X=x;Y=y;Z=z;R=r;G=g;B=b;Range=range;Intensity=intensity;Down=down;}}
internal sealed class NightLights {
 static readonly Lamp[] Data={new Lamp(-29f,22.25f,-150f,0.15f,0.38f,0.8f,5f,0.22f,false),
new Lamp(29f,22.25f,-150f,0.15f,0.38f,0.8f,5f,0.22f,false),
new Lamp(-29f,22.25f,-120f,0.15f,0.38f,0.8f,5f,0.22f,false),
new Lamp(29f,22.25f,-120f,0.15f,0.38f,0.8f,5f,0.22f,false),
new Lamp(-29f,22.25f,-90f,0.15f,0.38f,0.8f,5f,0.22f,false),
new Lamp(29f,22.25f,-90f,0.15f,0.38f,0.8f,5f,0.22f,false),
new Lamp(-29f,22.25f,-60f,0.15f,0.38f,0.8f,5f,0.22f,false),
new Lamp(29f,22.25f,-60f,0.15f,0.38f,0.8f,5f,0.22f,false),
new Lamp(-29f,22.25f,-30f,0.15f,0.38f,0.8f,5f,0.22f,false),
new Lamp(29f,22.25f,-30f,0.15f,0.38f,0.8f,5f,0.22f,false),
new Lamp(-29f,22.25f,0f,0.15f,0.38f,0.8f,5f,0.22f,false),
new Lamp(29f,22.25f,0f,0.15f,0.38f,0.8f,5f,0.22f,false),
new Lamp(-29f,22.25f,30f,0.15f,0.38f,0.8f,5f,0.22f,false),
new Lamp(29f,22.25f,30f,0.15f,0.38f,0.8f,5f,0.22f,false),
new Lamp(-29f,22.25f,60f,0.15f,0.38f,0.8f,5f,0.22f,false),
new Lamp(29f,22.25f,60f,0.15f,0.38f,0.8f,5f,0.22f,false),
new Lamp(-29f,22.25f,90f,0.15f,0.38f,0.8f,5f,0.22f,false),
new Lamp(29f,22.25f,90f,0.15f,0.38f,0.8f,5f,0.22f,false),
new Lamp(-29f,22.25f,120f,0.15f,0.38f,0.8f,5f,0.22f,false),
new Lamp(29f,22.25f,120f,0.15f,0.38f,0.8f,5f,0.22f,false),
new Lamp(-29f,22.25f,150f,0.15f,0.38f,0.8f,5f,0.22f,false),
new Lamp(29f,22.25f,150f,0.15f,0.38f,0.8f,5f,0.22f,false),
new Lamp(-18f,19.35f,-120f,1.0f,0.88f,0.65f,13f,0.9f,true),
new Lamp(18f,19.35f,-120f,1.0f,0.88f,0.65f,13f,0.9f,true),
new Lamp(-18f,19.35f,-85f,1.0f,0.88f,0.65f,13f,0.9f,true),
new Lamp(18f,19.35f,-85f,1.0f,0.88f,0.65f,13f,0.9f,true),
new Lamp(-18f,19.35f,-50f,1.0f,0.88f,0.65f,13f,0.9f,true),
new Lamp(18f,19.35f,-50f,1.0f,0.88f,0.65f,13f,0.9f,true),
new Lamp(-18f,19.35f,-15f,1.0f,0.88f,0.65f,13f,0.9f,true),
new Lamp(18f,19.35f,-15f,1.0f,0.88f,0.65f,13f,0.9f,true),
new Lamp(-18f,19.35f,20f,1.0f,0.88f,0.65f,13f,0.9f,true),
new Lamp(18f,19.35f,20f,1.0f,0.88f,0.65f,13f,0.9f,true),
new Lamp(-18f,19.35f,55f,1.0f,0.88f,0.65f,13f,0.9f,true),
new Lamp(18f,19.35f,55f,1.0f,0.88f,0.65f,13f,0.9f,true),
new Lamp(-18f,19.35f,90f,1.0f,0.88f,0.65f,13f,0.9f,true),
new Lamp(18f,19.35f,90f,1.0f,0.88f,0.65f,13f,0.9f,true),
new Lamp(-18f,19.35f,125f,1.0f,0.88f,0.65f,13f,0.9f,true),
new Lamp(18f,19.35f,125f,1.0f,0.88f,0.65f,13f,0.9f,true),
new Lamp(26f,24f,50f,1.0f,0.82f,0.55f,8f,0.35f,false),
new Lamp(26f,24f,-45f,1.0f,0.82f,0.55f,8f,0.35f,false),
new Lamp(30f,24f,-116f,1.0f,0.82f,0.55f,8f,0.35f,false),
new Lamp(30f,24f,86f,1.0f,0.82f,0.55f,8f,0.35f,false),};
 readonly List<object> lights=new List<object>();bool initialized,failed;double next;
 static Type Find(string n)=>AppDomain.CurrentDomain.GetAssemblies().Select(a=>a.GetType(n,false)).FirstOrDefault(t=>t!=null);
 static object V(Type t,float x,float y,float z)=>Activator.CreateInstance(t,x,y,z);
 static void Set(object o,string n,object v)=>o.GetType().GetProperty(n).SetValue(o,v);
 public void Tick(object owner,double now){if(failed||now<next)return;next=now+.75;
  try{if(!initialized){var goType=Find("UnityEngine.GameObject");var lightType=Find("UnityEngine.Light");var color=Find("UnityEngine.Color");
    var root=Reflect.Get(Reflect.Call(owner,"getRootGameObject"),"transform");var vector=Reflect.Get(root,"localPosition").GetType();
    foreach(var l in Data){var go=Activator.CreateInstance(goType,new object[]{"Australis night lamp"});var tr=Reflect.Get(go,"transform");Set(tr,"parent",root);
     Set(tr,"localPosition",V(vector,l.X/(float)BayData.MetresPerUnit,l.Y/(float)BayData.MetresPerUnit,l.Z/(float)BayData.MetresPerUnit));
     Set(tr,"localEulerAngles",V(vector,l.Down?90:0,0,0));
     var light=goType.GetMethod("AddComponent",new[]{typeof(Type)}).Invoke(go,new object[]{lightType});
     Set(light,"type",Enum.ToObject(lightType.GetProperty("type").PropertyType,l.Down?0:2));
     Set(light,"shadows",Enum.ToObject(lightType.GetProperty("shadows").PropertyType,0));
     Set(light,"color",Activator.CreateInstance(color,l.R,l.G,l.B,1f));
     Set(light,"range",l.Range/(float)BayData.MetresPerUnit);Set(light,"intensity",l.Intensity);
     if(l.Down)Set(light,"spotAngle",110f);Set(light,"enabled",false);lights.Add(light);
    }initialized=true;Bridge.Log("Created "+lights.Count+" night lamps (no shadows)");}
    var settings=Find("UnityEngine.RenderSettings");var sun=settings.GetProperty("sun",BindingFlags.Public|BindingFlags.Static)?.GetValue(null);
    bool night=sun!=null && Convert.ToSingle(Reflect.Get(sun,"intensity"))<.18f;
    foreach(var light in lights)Set(light,"enabled",night);
  }catch(Exception e){failed=true;Bridge.Log("Lighting disabled; deck controller retained: "+e.Message);}
 }
}
}
