using System;
using System.Collections;
using System.Collections.Generic;
using System.Reflection;
using System.Runtime.CompilerServices;
namespace RAN.Australis {
// Native proof: VesselLoader0x06008ff3 adds Vessel to the same runtime root
// returned by getRootGameObject0x060066e0. Collider aliases are loaded by
// 0x060068c9/0x060068cb. Never find/mutate through _obp prefab maps;
// _collidersGO is an unused field. No reparenting or hierarchy activation.
internal sealed class Ciws6ColliderSync {
 internal const double MetresPerUnit=68.628171085208,ToleranceMetres=.035;
 internal const string MeshAlias="CIWS6_LiftMeshCollider",DamageAlias="coll_ciws6_damage";
 const double CentreX=-50,CentreY=15.7515940881427,CentreZ=149.5,SizeX=6.02,SizeY=6.0631881762855,SizeZ=6.02;
 const BindingFlags Instance=BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Instance;
 object owner,frame,root,mesh,damage,meshComponent,damageComponent;
 MethodInfo physicsSync;bool bound,synchronized,lastEnabled;double lastDelta;
 sealed class Proxy {
  internal readonly object Transform,Component;internal readonly double[] Origin,Scale;
  internal Proxy(object t,object c,double[] o,double[] s){Transform=t;Component=c;Origin=o;Scale=s;}
 }
 Proxy[] proxies;
 sealed class AimOwner {internal readonly object Owner;internal AimOwner(object value){Owner=value;}}
 static readonly ConditionalWeakTable<object,AimOwner> aimOwners=new ConditionalWeakTable<object,AimOwner>();
 object aimSystem,aimBox;bool aimSynchronized;double aimDelta;
 static bool Finite(double n)=>!double.IsNaN(n)&&!double.IsInfinity(n);
 static object Required(object v,string n)=>Reflect.Get(v,n)??throw new InvalidOperationException("Missing collider member "+n);
 static double Number(object v,string n){double d=Convert.ToDouble(Required(v,n));if(!Finite(d))throw new InvalidOperationException("Non-finite collider coordinate");return d;}
 static double[] Values(object v)=>new[]{Number(v,"x"),Number(v,"y"),Number(v,"z")};
 static Type RuntimeType(string name){
  Type found=null;foreach(var a in AppDomain.CurrentDomain.GetAssemblies()){
   var t=a.GetType(name,false);if(t==null)continue;
   if(found!=null&&found!=t)throw new InvalidOperationException("Ambiguous runtime type "+name);found=t;
  }return found??throw new TypeLoadException(name);
 }
 static bool NativeType(object v,string name){for(var t=v?.GetType();t!=null;t=t.BaseType)if(t.FullName==name)return true;return false;}
 static void Alive(object v){
  if(v==null)throw new InvalidOperationException("Missing Unity collider object");
  var t=RuntimeType("UnityEngine.Object");var eq=t.GetMethod("op_Equality",BindingFlags.Public|BindingFlags.Static,null,new[]{t,t},null);
  if(eq==null||!(eq.Invoke(null,new[]{v,null}) is bool dead)||dead)throw new InvalidOperationException("Destroyed/unverified Unity collider object");
 }
 static object Vec(double[] v)=>Activator.CreateInstance(RuntimeType("UnityEngine.Vector3"),(float)v[0],(float)v[1],(float)v[2]);
 static bool Below(object tr,object ancestor){
  var seen=new HashSet<object>();for(int i=0;i<128&&tr!=null;i++){
   if(ReferenceEquals(tr,ancestor))return true;if(!seen.Add(tr))throw new InvalidOperationException("Collider ancestry cycle");tr=Reflect.Get(tr,"parent");
  }return false;
 }
 static object Unique(object scope,string name){
  object result=null;int count=0;var seen=new HashSet<object>();
  void Walk(object tr,int depth){
   if(depth>128||!seen.Add(tr))throw new InvalidOperationException("Invalid collider hierarchy");Alive(tr);
   if(Convert.ToString(Required(tr,"name"))==name){result=tr;count++;}
   int n=Convert.ToInt32(Required(tr,"childCount"));if(n<0||n>100000)throw new InvalidOperationException("Invalid collider child count");
   for(int i=0;i<n;i++)Walk(Reflect.Call(tr,"GetChild",i),depth+1);
  }
  Walk(scope,0);if(count!=1)throw new InvalidOperationException("Collider alias not unique: "+name+" ("+count+")");return result;
 }
 static object Component(object tr,string type){
  var values=Reflect.Call(Required(tr,"gameObject"),"GetComponents",RuntimeType(type)) as IEnumerable;object result=null;int count=0;
  if(values==null)throw new InvalidOperationException("Collider component enumeration unavailable");
  foreach(var c in values){result=c;count++;}
  if(count!=1)throw new InvalidOperationException("Collider component not unique: "+type);Alive(result);return result;
 }
 static void Set(object obj,string property,object value){
  var p=obj.GetType().GetProperty(property,Instance);if(p==null||!p.CanWrite)throw new MissingMemberException(obj.GetType().FullName,property);p.SetValue(obj,value);
 }
 double[] ModelPoint(object tr,double[] local)=>Values(Reflect.Call(frame,"InverseTransformPoint",Reflect.Call(tr,"TransformPoint",Vec(local))));
 static void Close(double[] a,double[] b,string reason){
  double e=0;for(int i=0;i<3;i++){if(!Finite(a[i])||!Finite(b[i]))throw new InvalidOperationException("Non-finite "+reason);e+=(a[i]-b[i])*(a[i]-b[i]);}
  if(Math.Sqrt(e)*MetresPerUnit>ToleranceMetres)throw new InvalidOperationException(reason+" differs by "+(Math.Sqrt(e)*MetresPerUnit).ToString("F4")+" m");
 }
 void Basis(Proxy p){
  var origin=ModelPoint(p.Transform,new double[3]);
  for(int axis=0;axis<3;axis++){
   var point=new double[3];point[axis]=1;var endpoint=ModelPoint(p.Transform,point);var delta=new double[3];var expected=new double[3];expected[axis]=p.Scale[axis];
   for(int i=0;i<3;i++)delta[i]=endpoint[i]-origin[i];Close(delta,expected,"Collider model-frame basis");
  }
 }
 static double[] At(Proxy p,double d)=>new[]{p.Origin[0],p.Origin[1]+d/MetresPerUnit,p.Origin[2]};
 static object Direct(object parent,string name){
  object found=null;int matches=0;int count=Convert.ToInt32(Required(parent,"childCount"));
  for(int i=0;i<count;i++){var child=Reflect.Call(parent,"GetChild",i);if(Convert.ToString(Required(child,"name"))==name){found=child;matches++;}}
  if(matches!=1)throw new InvalidOperationException("Native collider branch not unique: "+name);return found;
 }
 void Ownership(object candidate,object modelFrame){
  if(!NativeType(candidate,"SeaPower.ObjectBase"))throw new InvalidOperationException("Owner is not a native ObjectBase");Alive(candidate);
  var go=Reflect.Call(candidate,"getRootGameObject");Alive(go);
  if(!ReferenceEquals(Required(candidate,"gameObject"),go))throw new InvalidOperationException("Vessel does not own runtime collider root");
  var actualRoot=Required(go,"transform");
  if(bound&&(!ReferenceEquals(candidate,owner)||!ReferenceEquals(modelFrame,frame)||!ReferenceEquals(actualRoot,root)))throw new InvalidOperationException("Collider owner/model frame changed");
  if(!Below(modelFrame,actualRoot))throw new InvalidOperationException("Model frame is outside owner runtime hierarchy");
  root=actualRoot;
 }
 void Branches(){
  var colliders=Direct(root,"Colliders");var kinetics=Direct(colliders,"kinematiccolliders");var systems=Direct(colliders,"systemcolliders");
  var actualMesh=Unique(colliders,MeshAlias);var actualDamage=Unique(colliders,DamageAlias);
  if(bound&&(!ReferenceEquals(actualMesh,mesh)||!ReferenceEquals(actualDamage,damage)))throw new InvalidOperationException("Owned collider aliases changed");
  if(!ReferenceEquals(Reflect.Get(actualMesh,"parent"),kinetics)||!ReferenceEquals(Reflect.Get(actualDamage,"parent"),systems))throw new InvalidOperationException("Collider alias is in wrong native branch");
  mesh=actualMesh;damage=actualDamage;
 }
 void Shape(){
  if(!(Required(meshComponent,"convex") is bool convex)||!convex)throw new InvalidOperationException("Moving physics proxy is not convex");
  var b=Required(Required(meshComponent,"sharedMesh"),"bounds");
  Close(Values(Required(b,"center")),new[]{CentreX/MetresPerUnit,CentreY/MetresPerUnit,CentreZ/MetresPerUnit},"Moving proxy mesh centre");
  Close(Values(Required(b,"size")),new[]{SizeX/MetresPerUnit,SizeY/MetresPerUnit,SizeZ/MetresPerUnit},"Moving proxy mesh size");
  Close(Values(Required(damageComponent,"center")),new double[3],"Native damage cube centre");
  Close(Values(Required(damageComponent,"size")),new[]{1d,1d,1d},"Native damage cube size");
 }
 void Bind(object candidate,object modelFrame){
  Ownership(candidate,modelFrame);owner=candidate;frame=modelFrame;Branches();
  meshComponent=Component(mesh,"UnityEngine.MeshCollider");damageComponent=Component(damage,"UnityEngine.BoxCollider");
  proxies=new[]{new Proxy(mesh,meshComponent,new double[3],new[]{1d,1d,1d}),new Proxy(damage,damageComponent,new[]{CentreX/MetresPerUnit,CentreY/MetresPerUnit,CentreZ/MetresPerUnit},new[]{SizeX/MetresPerUnit,SizeY/MetresPerUnit,SizeZ/MetresPerUnit})};
  Shape();foreach(var p in proxies){Basis(p);Close(ModelPoint(p.Transform,new double[3]),p.Origin,"Initial authored stowed collider pose");}
  physicsSync=RuntimeType("UnityEngine.Physics").GetMethod("SyncTransforms",BindingFlags.Public|BindingFlags.Static,null,Type.EmptyTypes,null);
  if(physicsSync==null||physicsSync.ReturnType!=typeof(void))throw new MissingMethodException("UnityEngine.Physics.SyncTransforms");bound=true;
 }
 static void Arguments(double delta,bool deployed){
  if(!Finite(delta)||delta<-.001||delta>6.001)throw new InvalidOperationException("Invalid measured lift displacement");
  if(deployed&&Math.Abs(delta-6)>.025)throw new InvalidOperationException("Enabled collider requested before full deployment");
 }
 internal bool Sync(object candidate,object modelFrame,double delta,bool deployed,out string reason){
  // A stable deployed/stowed pose must not toggle colliders or flush physics.
  // The caller stops station6 before invoking this method for motion/repair.
  if(Verify(candidate,modelFrame,delta,deployed,out reason))return true;
  reason=null;synchronized=false;
  try{
   Arguments(delta,deployed);if(!bound)Bind(candidate,modelFrame);else{Ownership(candidate,modelFrame);Branches();Shape();}
   foreach(var p in proxies){Alive(p.Component);Basis(p);}
   // Disable owned proxies before any position change. The caller stops only
   // station6's burst before mechanism/collider movement or enable changes.
   foreach(var p in proxies)Set(p.Component,"enabled",false);
   foreach(var p in proxies){
    var desiredWorld=Reflect.Call(frame,"TransformPoint",Vec(At(p,delta)));var parent=Required(p.Transform,"parent");
    Set(p.Transform,"localPosition",Reflect.Call(parent,"InverseTransformPoint",desiredWorld));
   }
   foreach(var p in proxies)Set(p.Component,"enabled",deployed);
   // Native ObjectsManager/RelocationHandler also invoke this exact API.
   physicsSync.Invoke(null,null);lastDelta=delta;lastEnabled=deployed;synchronized=true;
   if(Verify(candidate,modelFrame,delta,deployed,out reason))return true;Disable();return false;
  }catch(Exception e){reason="CIWS6 collider synchronization: "+e.GetBaseException().Message;Disable();return false;}
 }
 internal bool Verify(object candidate,object modelFrame,double delta,bool deployed,out string reason){
  reason=null;
  try{
   Arguments(delta,deployed);if(!bound||!synchronized)throw new InvalidOperationException("Colliders have not synchronized");
   Ownership(candidate,modelFrame);Branches();Shape();
   if(Math.Abs(lastDelta-delta)>.001||lastEnabled!=deployed)throw new InvalidOperationException("Collider synchronization stamp is stale");
   foreach(var p in proxies){
    Alive(p.Transform);Alive(p.Component);Basis(p);Close(ModelPoint(p.Transform,new double[3]),At(p,delta),"Measured collider world pose");
    if(!(Required(p.Component,"enabled") is bool active)||active!=deployed)throw new InvalidOperationException("Collider enable state differs from mechanism");
   }
   if(deployed&&(!(Required(Required(mesh,"gameObject"),"activeInHierarchy") is bool live)||!live))throw new InvalidOperationException("Deployed kinematic physics proxy is inactive");
   return true;
  }catch(Exception e){reason="CIWS6 collider verification: "+e.GetBaseException().Message;return false;}
 }
 internal void Disable(){
  synchronized=false;
  foreach(var pair in new[]{new[]{mesh,meshComponent},new[]{damage,damageComponent}})try{
   if(pair[0]!=null&&pair[1]!=null&&root!=null&&Below(pair[0],root))Set(pair[1],"enabled",false);
  }catch{}
  try{physicsSync?.Invoke(null,null);}catch{}
 }
 object AimBox(object candidate,object modelFrame,object station,bool claim){
  if(!bound)throw new InvalidOperationException("Physical collider binding unavailable");Ownership(candidate,modelFrame);Branches();
  if(!NativeType(station,"SeaPower.WeaponSystemCIWS")||!ReferenceEquals(Required(station,"_baseObject"),candidate))throw new InvalidOperationException("Aim-point system is not owned native CIWS6");
  var values=Required(station,"_colliders") as IList;
  if(values==null||values.Count!=1)throw new InvalidOperationException("Station6 requires exactly one native damage HitBox");
  var box=values[0];
  if(!NativeType(box,"SeaPower.HitBox")||Convert.ToString(Required(box,"_name"))!=DamageAlias||!ReferenceEquals(Required(box,"_go"),Required(damage,"gameObject")))throw new InvalidOperationException("Native HitBox is not the owned runtime damage proxy");
  if(aimBox!=null&&(!ReferenceEquals(box,aimBox)||!ReferenceEquals(station,aimSystem)))throw new InvalidOperationException("Native station6 HitBox binding changed");
  if(aimOwners.TryGetValue(box,out var association)){
   if(!ReferenceEquals(association.Owner,candidate))throw new InvalidOperationException("HitBox shared between vessel instances");
  }else if(claim)aimOwners.Add(box,new AimOwner(candidate));else throw new InvalidOperationException("Runtime HitBox ownership not synchronized");
  return box;
 }
 // Native BaseSystem.get_AimPointPosition(0x060072e8) uses the owning Vessel
 // transform and the first runtime HitBox._position, not its moving GO pose.
 internal bool SyncAimPoint(object candidate,object modelFrame,object station,double delta,out string reason){
  if(VerifyAimPoint(candidate,modelFrame,station,delta,out reason))return true;
  reason=null;aimSynchronized=false;
  try{
   Arguments(delta,false);var box=AimBox(candidate,modelFrame,station,true);Basis(proxies[1]);
   Close(ModelPoint(damage,new double[3]),At(proxies[1],delta),"Physical proxy before aim-point synchronization");
   var world=Required(damage,"position");var local=Reflect.Call(Required(candidate,"transform"),"InverseTransformPoint",world);
   var field=Reflect.Field(box.GetType(),"_position");
   if(field==null||field.IsStatic||field.IsInitOnly||field.FieldType!=RuntimeType("UnityEngine.Vector3"))throw new MissingFieldException("Runtime HitBox._position");
   field.SetValue(box,local);aimSystem=station;aimBox=box;aimDelta=delta;aimSynchronized=true;
   return VerifyAimPoint(candidate,modelFrame,station,delta,out reason);
  }catch(Exception e){reason="CIWS6 native aim-point synchronization: "+e.GetBaseException().Message;return false;}
 }
 internal bool VerifyAimPoint(object candidate,object modelFrame,object station,double delta,out string reason){
  reason=null;
  try{
   Arguments(delta,false);if(!aimSynchronized||Math.Abs(aimDelta-delta)>.001)throw new InvalidOperationException("Native aim-point synchronization stamp stale");
   var box=AimBox(candidate,modelFrame,station,false);Basis(proxies[1]);
   var expected=At(proxies[1],delta);Close(ModelPoint(damage,new double[3]),expected,"Physical proxy for native aim point");
   var world=Reflect.Call(Required(candidate,"transform"),"TransformPoint",Required(box,"_position"));
   Close(Values(Reflect.Call(frame,"InverseTransformPoint",world)),expected,"Runtime HitBox native position");
   Close(Values(Reflect.Call(frame,"InverseTransformPoint",Required(station,"AimPointPosition"))),expected,"Native system aim-point getter");return true;
  }catch(Exception e){reason="CIWS6 native aim-point verification: "+e.GetBaseException().Message;return false;}
 }
}
}
