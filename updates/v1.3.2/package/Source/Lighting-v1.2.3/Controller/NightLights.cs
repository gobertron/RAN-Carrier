using System;
using System.Linq;
using System.Reflection;
using System.Collections;
using System.Collections.Generic;
namespace RAN.Australis {
internal sealed class Lamp {
 public readonly string Name;public readonly float X,Y,Z,Pitch,Yaw,R,G,B,Range,Intensity,Angle;public readonly bool Spot;
 public Lamp(string name,float x,float y,float z,float pitch,float yaw,float r,float g,float b,float range,float intensity,float angle,bool spot){Name=name;X=x;Y=y;Z=z;Pitch=pitch;Yaw=yaw;R=r;G=g;B=b;Range=range;Intensity=intensity;Angle=angle;Spot=spot;}
}
internal sealed class GlowPart {
 public readonly string Name;public readonly float R,G,B,Gain;
 public GlowPart(string name,float r,float g,float b,float gain){Name=name;R=r;G=g;B=b;Gain=gain;}
}
internal sealed class NightLights {
 sealed class Glow {
  public object Material,OriginalShader,OriginalColor,OriginalEmission,UnlitShader;public bool NativeEmission,OriginalKeyword,Failed;public GlowPart Spec;
 }
 readonly List<object> lights=new List<object>();readonly List<Glow> glows=new List<Glow>();
 readonly LowLightPolicy policy=new LowLightPolicy();bool initialized,failed;double retryAt;int lastState=-1;double next,previous=double.NaN;float lastGain=-1;
 static Type Find(string n)=>AppDomain.CurrentDomain.GetAssemblies().Select(a=>a.GetType(n,false)).FirstOrDefault(t=>t!=null);
 static object V(Type t,float x,float y,float z)=>Activator.CreateInstance(t,x,y,z);
 static void Set(object o,string n,object v)=>o.GetType().GetProperty(n).SetValue(o,v);
 static object Color(float r,float g,float b)=>Activator.CreateInstance(Find("UnityEngine.Color"),r,g,b,1f);
 static void Restore(Glow g){
  if(g.NativeEmission){Reflect.Call(g.Material,"SetColor","_EmissionColor",g.OriginalEmission);Reflect.Call(g.Material,g.OriginalKeyword?"EnableKeyword":"DisableKeyword","_EMISSION");}
  else {Set(g.Material,"shader",g.OriginalShader);Set(g.Material,"color",g.OriginalColor);}
 }
 void Off(){
  foreach(var light in lights){try{Set(light,"enabled",false);Set(light,"intensity",0f);}catch{}}
  foreach(var glow in glows){try{Restore(glow);}catch{}}lastGain=-1;
 }
 public void Disable(){Off();failed=true;}
 void BindGlows(IDictionary<string,object> models){
  Type renderer=Find("UnityEngine.Renderer"),shaderType=Find("UnityEngine.Shader");
  object unlit=shaderType?.GetMethod("Find",BindingFlags.Public|BindingFlags.Static,null,new[]{typeof(string)},null)?.Invoke(null,new object[]{"Unlit/Color"});
  int missing=0;
  foreach(var spec in NightLightingData.GlowParts){try{
   if(models==null||!models.TryGetValue(spec.Name,out object tr)||tr==null){missing++;continue;}
   if(new[]{spec.R,spec.G,spec.B,spec.Gain}.Any(v=>!LandingSignalPolicy.Finite(v)||v<0))throw new InvalidOperationException("Invalid luminous fitting "+spec.Name);
   var renderers=Reflect.Call(Reflect.Get(tr,"gameObject"),"GetComponentsInChildren",renderer,true) as IEnumerable;
   if(renderers==null){missing++;continue;}
   foreach(object item in renderers){
    // Renderer.materials instantiates private per-renderer materials. Never
    // change sharedMaterial: another ship or a steel frame must not glow.
    var materials=Reflect.Get(item,"materials") as IEnumerable;
    if(materials==null)materials=new[]{Reflect.Get(item,"material")};
    foreach(object material in materials){
     if(material==null)continue;
     var glow=new Glow{Material=material,Spec=spec,OriginalShader=Reflect.Get(material,"shader"),OriginalColor=Reflect.Get(material,"color"),UnlitShader=unlit};
     bool emission=false;try{emission=Convert.ToBoolean(Reflect.Call(material,"HasProperty","_EmissionColor"));}catch{}
     // These are individual lens/window meshes, so prefer a visible unlit
     // surface over assuming a custom ship shader implements Standard emission.
     if(unlit!=null)glow.NativeEmission=false;
     else if(emission){glow.NativeEmission=true;glow.OriginalEmission=Reflect.Call(material,"GetColor","_EmissionColor");glow.OriginalKeyword=Convert.ToBoolean(Reflect.Call(material,"IsKeywordEnabled","_EMISSION"));}
     else if(unlit==null){missing++;continue;}
     glows.Add(glow);
    }
   }
  }catch(Exception e){missing++;Bridge.Log("Luminous fitting skipped "+spec.Name+": "+e.Message);}}
  if(missing>0)Bridge.Log("Lighting: "+missing+" luminous fittings unavailable; other lamps retained");
 }
 void Initialize(object owner,IDictionary<string,object> models){
  var goType=Find("UnityEngine.GameObject");var lightType=Find("UnityEngine.Light");
  var root=Reflect.Get(Reflect.Call(owner,"getRootGameObject"),"transform");var vector=Reflect.Get(root,"localPosition").GetType();
  foreach(var l in NightLightingData.Lamps){
   if(new[]{l.X,l.Y,l.Z,l.Pitch,l.Yaw,l.R,l.G,l.B,l.Range,l.Intensity,l.Angle}.Any(v=>!LandingSignalPolicy.Finite(v))||l.Range<=0||l.Intensity<0||l.Angle<=0||l.Angle>=180)throw new InvalidOperationException("Invalid mounted lamp "+l.Name);
   var go=Activator.CreateInstance(goType,new object[]{"Australis "+l.Name});var tr=Reflect.Get(go,"transform");Reflect.Call(tr,"SetParent",root,false);
   Set(tr,"localPosition",V(vector,l.X/(float)BayData.MetresPerUnit,l.Y/(float)BayData.MetresPerUnit,l.Z/(float)BayData.MetresPerUnit));
   Set(tr,"localEulerAngles",V(vector,l.Pitch,l.Yaw,0));Set(tr,"localScale",V(vector,1,1,1));
   var light=goType.GetMethod("AddComponent",new[]{typeof(Type)}).Invoke(go,new object[]{lightType});lights.Add(light);Set(light,"enabled",false);
   Set(light,"type",Enum.ToObject(lightType.GetProperty("type").PropertyType,l.Spot?0:2));
   var mode=lightType.GetProperty("renderMode");
   if(mode!=null&&Enum.IsDefined(mode.PropertyType,"ForcePixel"))mode.SetValue(light,Enum.Parse(mode.PropertyType,"ForcePixel"));
   var mask=lightType.GetProperty("cullingMask");if(mask!=null)mask.SetValue(light,-1);
   Set(light,"shadows",Enum.ToObject(lightType.GetProperty("shadows").PropertyType,0));
   Set(light,"color",Color(l.R,l.G,l.B));Set(light,"range",l.Range/(float)BayData.MetresPerUnit);Set(light,"intensity",0f);
   if(l.Spot)Set(light,"spotAngle",l.Angle);
  }
  BindGlows(models);initialized=true;Bridge.Log("Created "+lights.Count+" mounted lamps and "+glows.Count+" private luminous surfaces; scene brightness controls night/storm lighting");
 }
 void Apply(float gain){
  if(gain==lastGain)return;
  for(int i=0;i<lights.Count;i++){Set(lights[i],"intensity",NightLightingData.Lamps[i].Intensity*gain);Set(lights[i],"enabled",gain>0);}
  foreach(var glow in glows){if(glow.Failed)continue;try{
   if(gain<=0){Restore(glow);continue;}
   var color=Color(glow.Spec.R*glow.Spec.Gain*gain,glow.Spec.G*glow.Spec.Gain*gain,glow.Spec.B*glow.Spec.Gain*gain);
   if(glow.NativeEmission){Reflect.Call(glow.Material,"EnableKeyword","_EMISSION");Reflect.Call(glow.Material,"SetColor","_EmissionColor",color);}
   else {Set(glow.Material,"shader",glow.UnlitShader);Set(glow.Material,"color",color);}
  }catch(Exception e){try{Restore(glow);}catch{}glow.Failed=true;Bridge.Log("Luminous fitting disabled "+glow.Spec.Name+"; other lighting retained: "+e.Message);}}lastGain=gain;
 }
 public void Tick(object owner,IDictionary<string,object> models,double now){
  if(failed)return;
  if(!LandingSignalPolicy.Finite(now)){Off();policy.Reset();next=0;previous=double.NaN;return;}
  if(!double.IsNaN(previous)&&now<previous)next=now;
  if(!double.IsNaN(previous)&&now<previous)retryAt=now;
  previous=now;if(now<next||now<retryAt)return;next=now+.25;
  try{
   if(!initialized)Initialize(owner,models);
   double brightness=LowLightEnvironment.Brightness();float gain=policy.Tick(now,brightness);Apply(gain);
   int state=gain>=1?1:gain<=0?0:2;
   if(state!=2&&state!=lastState){lastState=state;Bridge.Log("[AUSTRALIS_LIGHTING] "+(state==1?"ON":"OFF")+" brightness="+brightness.ToString("F3",System.Globalization.CultureInfo.InvariantCulture)+" lamps="+lights.Count+" surfaces="+glows.Count);}
  }
  catch(Exception e){
   Off();
   // A missing model root during loading is transient. Clean partial lamps
   // before retry so one early frame cannot permanently remove night lighting.
   Type unityObject=Find("UnityEngine.Object");
   foreach(var light in lights){try{
    object go=Reflect.Get(light,"gameObject");
    unityObject?.GetMethod("Destroy",BindingFlags.Public|BindingFlags.Static,null,new[]{unityObject},null)?.Invoke(null,new[]{go});
   }catch{}}
   lights.Clear();glows.Clear();initialized=false;policy.Reset();lastState=-1;retryAt=now+5;
   Bridge.Log("Lighting initialisation will retry in 5 seconds; deck controller retained: "+e.Message);
  }
 }
}
}
