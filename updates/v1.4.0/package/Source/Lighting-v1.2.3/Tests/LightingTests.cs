using System;
using System.Collections.Generic;
using System.Linq;
using RAN.Australis;
namespace UnityEngine {
 public struct Vector3 {public float x,y,z;public Vector3(float a,float b,float c){x=a;y=b;z=c;}}
 public struct Color {public float r,g,b,a;public Color(float x,float y,float z,float w){r=x;g=y;b=z;a=w;}}
 public class Object {public static int Destroyed;public static void Destroy(Object o){Destroyed++;}}
 public class Transform {public Vector3 localPosition{get;set;} public Vector3 localScale{get;set;} public Vector3 localEulerAngles{get;set;} public Vector3 forward{get;set;} public GameObject gameObject{get;set;} public void SetParent(Transform t,bool world){} }
 public enum LightType {Spot,Directional,Point} public enum LightShadows {None,Hard,Soft} public enum LightRenderMode {Auto,ForcePixel,ForceVertex}
 public class Light:Object {public bool enabled{get;set;}=true;public float intensity{get;set;}=1;public Color color{get;set;}=new Color(1,1,1,1);public Transform transform{get;set;}=new Transform();public GameObject gameObject{get;set;} public LightType type{get;set;} public LightShadows shadows{get;set;} public LightRenderMode renderMode{get;set;} public int cullingMask{get;set;} public float range{get;set;} public float spotAngle{get;set;} }
 public class Shader {public string Name;public static Shader Find(string n)=>new Shader{Name=n};}
 public class Material {public Shader shader{get;set;}=Shader.Find("Marmoset/Bumped Specular IBL");public Color color{get;set;}=new Color(.2f,.2f,.2f,1);public bool HasProperty(string s)=>true;public Color GetColor(string s)=>new Color();public bool IsKeywordEnabled(string s)=>false;public void SetColor(string s,Color c){}public void EnableKeyword(string s){}public void DisableKeyword(string s){} }
 public class Renderer {public Material[] materials{get;set;}=new[]{new Material()};}
 public class GameObject:Object {public static List<Light> Created=new List<Light>();public Transform transform{get;set;} public Renderer renderer=new Renderer();public GameObject(string n){transform=new Transform{gameObject=this};} public object AddComponent(Type t){var light=new Light{gameObject=this};Created.Add(light);return light;}public Renderer[] GetComponentsInChildren(Type t,bool all)=>new[]{renderer};}
 public static class RenderSettings {public static Light sun{get;set;} public static bool fog{get;set;} public static Color fogColor{get;set;} public static string fogMode{get;set;} public static float fogStartDistance{get;set;} public static float fogEndDistance{get;set;} public static float fogDensity{get;set;} public static string ambientMode{get;set;}="Flat";public static Color ambientLight{get;set;} public static object ambientProbe{get;set;}public static float ambientIntensity{get;set;}=1;}
}
public class Owner {public bool Ready=true;public UnityEngine.GameObject root=new UnityEngine.GameObject("ship");public UnityEngine.GameObject getRootGameObject(){if(!Ready)throw new Exception("root not ready");return root;}}
class LightingTests {
 static int checks;static void Check(bool value,string name){if(!value)throw new Exception(name);checks++;}
 static void Scene(float sun,float y,float ambient,bool fog=false){UnityEngine.RenderSettings.sun=new UnityEngine.Light{intensity=sun,transform=new UnityEngine.Transform{forward=new UnityEngine.Vector3(0,y,0)}};UnityEngine.RenderSettings.ambientLight=new UnityEngine.Color(ambient,ambient,ambient,1);UnityEngine.RenderSettings.fog=fog;UnityEngine.RenderSettings.fogColor=new UnityEngine.Color(.6f,.6f,.6f,1);UnityEngine.RenderSettings.fogMode="Exponential";UnityEngine.RenderSettings.fogDensity=.15f;}
 static void Main(){
  var p=new LowLightPolicy();Check(p.Tick(0,1)==0,"day off");Check(p.Tick(1,.1)==1,"night on");Check(p.Tick(2,.25)==1,"hysteresis");p.Tick(3,1);p.Tick(4,1);Check(p.Tick(5,1)==0,"bright hold off");Check(p.Tick(6,double.NaN)==0,"unreadable retains state");Check(p.Tick(0,.1)==1,"clock rewind");Check(p.Tick(double.NaN,.1)==0,"invalid time resets");
  Scene(1,-1,.5f);Check(LowLightEnvironment.Brightness()>.3,"clear daytime");Scene(1,-1,.5f,true);Check(LowLightEnvironment.Brightness()<.2,"grey dense storm triggers");Scene(0,1,1);Check(LowLightEnvironment.Brightness()<.2,"night stale ambient probe triggers");Scene(1,-1,.5f);UnityEngine.RenderSettings.fog=true;UnityEngine.RenderSettings.fogDensity=.001f;Check(LowLightEnvironment.Brightness()>.3,"thin fog stays daytime");UnityEngine.RenderSettings.sun=null;UnityEngine.RenderSettings.ambientLight=new UnityEngine.Color(.01f,.01f,.01f,1);Check(LowLightEnvironment.Brightness()<.2,"missing sun night fallback");
  var owner=new Owner();var models=new Dictionary<string,object>();foreach(var spec in NightLightingData.GlowParts)models[spec.Name]=new UnityEngine.GameObject(spec.Name).transform;
  var lights=new NightLights();Scene(1,-1,.5f);lights.Tick(owner,models,0);Check(UnityEngine.GameObject.Created.Count==NightLightingData.Lamps.Length,"mounted light count");Check(UnityEngine.GameObject.Created.All(l=>!l.enabled),"day lights disabled");Scene(0,1,1);lights.Tick(owner,models,1);Check(UnityEngine.GameObject.Created.All(l=>l.enabled&&l.intensity>0),"night real lights enabled");Check(UnityEngine.GameObject.Created.All(l=>l.renderMode==UnityEngine.LightRenderMode.ForcePixel&&l.cullingMask==-1),"pixel lights and layer mask");Check(models.Values.Cast<UnityEngine.Transform>().All(t=>t.gameObject.renderer.materials[0].shader.Name=="Unlit/Color"),"custom shader lens fallback");
  Scene(1,-1,.5f);lights.Tick(owner,models,2);lights.Tick(owner,models,3);lights.Tick(owner,models,4);Check(models.Values.Cast<UnityEngine.Transform>().All(t=>t.gameObject.renderer.materials[0].shader.Name=="Marmoset/Bumped Specular IBL"),"day materials restored");
  int before=UnityEngine.GameObject.Created.Count;var retry=new NightLights();owner.Ready=false;retry.Tick(owner,models,10);owner.Ready=true;retry.Tick(owner,models,11);Check(UnityEngine.GameObject.Created.Count==before,"backoff");Scene(0,1,1);retry.Tick(owner,models,15);Check(UnityEngine.GameObject.Created.Count==before+NightLightingData.Lamps.Length,"transient root retry");
  Check(LiftLightPolicy.Gain(22)==0,"raised lift lights off");Check(LiftLightPolicy.Gain(16)>0,"lowered lift lights on");
  Console.WriteLine("PASS "+checks+" lighting regression checks; native-shaped fixture, not Unity execution");
 }
}
