using System;
using System.Collections;
using System.Collections.Generic;
using System.Reflection;
using System.Runtime.CompilerServices;
namespace RAN.Australis {
internal sealed class Ciws6SweepVolume {
    internal readonly double MinX,MinY,MinZ,MaxX,MaxY,MaxZ;
    internal Ciws6SweepVolume(double minX,double minY,double minZ,double maxX,double maxY,double maxZ){MinX=minX;MinY=minY;MinZ=minZ;MaxX=maxX;MaxY=maxY;MaxZ=maxZ;}
}
// Read-only probes against the audited native schema. No game/Unity assembly
// is linked, no scene setter is invoked and no singleton-creating getter runs.
internal static class Ciws6AircraftClearance {
    internal const double MetresPerUnit=68.628171085208;
    const BindingFlags Declared=BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Instance|BindingFlags.Static|BindingFlags.DeclaredOnly;
    // Cache metadata only. Aircraft lists, lifetime, bounds and transform
    // values are read afresh on every clearance request.
    static readonly Dictionary<(Type,string),MemberInfo> Members=new Dictionary<(Type,string),MemberInfo>();
    static readonly Dictionary<(Type,string,int,Type,Type),MethodInfo> Methods=new Dictionary<(Type,string,int,Type,Type),MethodInfo>();
    static readonly Dictionary<string,Type> RuntimeTypes=new Dictionary<string,Type>();
    static readonly Dictionary<Type,ConstructorInfo> VectorConstructors=new Dictionary<Type,ConstructorInfo>();
    static readonly Dictionary<Type,MethodInfo> UnityEqualities=new Dictionary<Type,MethodInfo>();
    static FieldInfo managerInstance;
    sealed class ReferenceComparer:IEqualityComparer<object> {
        internal static readonly ReferenceComparer Instance=new ReferenceComparer();
        public new bool Equals(object x,object y)=>ReferenceEquals(x,y);
        public int GetHashCode(object value)=>RuntimeHelpers.GetHashCode(value);
    }
    static bool Finite(double value)=>!double.IsNaN(value)&&!double.IsInfinity(value);
    static object Required(object owner,string name){
        if(owner==null)throw new InvalidOperationException("Missing owner for "+name);
        var key=(owner.GetType(),name);
        if(Members.TryGetValue(key,out var cached))return cached is FieldInfo fieldValue?fieldValue.GetValue(owner):((PropertyInfo)cached).GetValue(owner);
        for(var type=owner.GetType();type!=null;type=type.BaseType){
            var field=type.GetField(name,Declared);if(field!=null){Members[key]=field;return field.GetValue(owner);}
            var property=type.GetProperty(name,Declared);
            if(property!=null&&property.CanRead&&property.GetIndexParameters().Length==0){Members[key]=property;return property.GetValue(owner);}
        }
        throw new MissingMemberException(owner.GetType().FullName,name);
    }
    static object Call(object owner,string name,params object[] args){
        if(owner==null)throw new InvalidOperationException("Missing call owner: "+name);
        if(args.Length>2)throw new InvalidOperationException("Unexpected clearance call signature");
        var key=(owner.GetType(),name,args.Length,args.Length>0?args[0]?.GetType():null,args.Length>1?args[1]?.GetType():null);
        if(Methods.TryGetValue(key,out var cached))return cached.Invoke(owner,args);
        MethodInfo found=null;
        foreach(var method in owner.GetType().GetMethods(BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Instance)){
            if(method.Name!=name||method.ContainsGenericParameters)continue;
            var parameters=method.GetParameters();if(parameters.Length!=args.Length)continue;
            bool matches=true;for(int i=0;i<args.Length;i++)if(args[i]==null?parameters[i].ParameterType.IsValueType:!parameters[i].ParameterType.IsInstanceOfType(args[i])){matches=false;break;}
            if(!matches)continue;if(found!=null)throw new AmbiguousMatchException(name);found=method;
        }
        if(found==null)throw new MissingMethodException(owner.GetType().FullName,name);
        Methods[key]=found;
        return found.Invoke(owner,args);
    }
    static Type RuntimeType(string name){
        if(RuntimeTypes.TryGetValue(name,out var cached))return cached;
        Type result=null;
        foreach(var assembly in AppDomain.CurrentDomain.GetAssemblies()){
            var type=assembly.GetType(name,false);if(type==null)continue;
            if(result!=null&&result!=type)throw new InvalidOperationException("Ambiguous runtime type "+name);result=type;
        }
        if(result==null)throw new TypeLoadException(name);RuntimeTypes[name]=result;return result;
    }
    static object ExistingObjectsManager(){
        if(managerInstance!=null)return LiveManager(managerInstance.GetValue(null));
        var manager=RuntimeType("SeaPower.ObjectsManager");
        for(var type=manager.BaseType;type!=null;type=type.BaseType){
            if(!type.IsGenericType||type.GetGenericTypeDefinition().FullName!="SeaPower.Singleton`1"||type.GetGenericArguments()[0]!=manager)continue;
            var field=type.GetField("_instance",Declared);
            if(field==null||!field.IsStatic)throw new MissingFieldException(type.FullName,"_instance");
            managerInstance=field;
            // Singleton<T>.Instance may create/destroy scene objects; observing
            // its audited backing field avoids those native side effects.
            return LiveManager(field.GetValue(null));
        }
        throw new InvalidOperationException("Native ObjectsManager singleton schema unavailable");
    }
    static IEnumerable Collection(object owner,string name){
        var value=Required(owner,name);
        if(value is IEnumerable items&&!(value is string))return items;
        throw new InvalidOperationException("Native collection unavailable: "+name);
    }
    static bool Flag(object owner,string name)=>Required(owner,name) is bool value?value:throw new InvalidOperationException("Native boolean unavailable: "+name);
    static bool NativeType(object value,string fullName){for(var type=value?.GetType();type!=null;type=type.BaseType)if(type.FullName==fullName)return true;return false;}
    static bool UnityLive(object value){
        if(value==null)return false;
        bool unity=false;
        for(var type=value.GetType();type!=null;type=type.BaseType)if(type.FullName=="UnityEngine.Object"){
            if(!UnityEqualities.TryGetValue(type,out var equality)){
                equality=type.GetMethod("op_Equality",BindingFlags.Public|BindingFlags.Static|BindingFlags.DeclaredOnly,null,new[]{type,type},null);
                if(equality!=null)UnityEqualities[type]=equality;
            }
            if(equality==null||!(equality.Invoke(null,new[]{value,null}) is bool destroyed))throw new InvalidOperationException("Unity lifetime check unavailable");
            if(destroyed)return false;unity=true;break;
        }
        if(!unity)throw new InvalidOperationException("Unity lifetime schema unavailable");
        return true;
    }
    static object LiveManager(object value){
        if(!NativeType(value,"SeaPower.ObjectsManager")||!UnityLive(value))throw new InvalidOperationException("Native ObjectsManager unavailable or destroyed");return value;
    }
    static bool Live(object value){
        if(value==null)throw new InvalidOperationException("Null aircraft reservation");
        if(!NativeType(value,"SeaPower.ObjectBase"))throw new InvalidOperationException("Unexpected native aircraft entry");
        if(!UnityLive(value))return false;
        if(Flag(value,"IsDestroyed"))return false;
        if(!Flag(value,"IsAirUnit"))throw new InvalidOperationException("Non-aircraft in native aircraft collection");
        return true;
    }
    static void Add(HashSet<object> aircraft,object value){if(Live(value))aircraft.Add(value);}
    static void AddCollection(HashSet<object> aircraft,object owner,string name){foreach(var value in Collection(owner,name))Add(aircraft,value);}
    static double Number(object value,string member){double result=Convert.ToDouble(Required(value,member));if(!Finite(result))throw new InvalidOperationException("Non-finite "+member);return result;}
    static double[] Vector(object value)=>new[]{Number(value,"x"),Number(value,"y"),Number(value,"z")};
    static bool AirframeRenderer(object renderer){
        if(renderer==null)throw new InvalidOperationException("Missing aircraft renderer");
        if(NativeType(renderer,"UnityEngine.MeshRenderer")||NativeType(renderer,"UnityEngine.SkinnedMeshRenderer"))return true;
        // Effects are not airframe geometry. Inactive mesh LODs are included.
        if(NativeType(renderer,"UnityEngine.ParticleSystemRenderer")||NativeType(renderer,"UnityEngine.LineRenderer")||NativeType(renderer,"UnityEngine.TrailRenderer"))return false;
        throw new InvalidOperationException("Unverified aircraft renderer type "+renderer.GetType().FullName);
    }
    static bool AircraftOverlaps(object aircraft,object frame,Type rendererType,Ciws6SweepVolume sweep){
        var root=Call(aircraft,"getRootGameObject");if(root==null)throw new InvalidOperationException("Live aircraft root unavailable");
        var renderers=Call(root,"GetComponentsInChildren",rendererType,true) as IEnumerable;
        if(renderers==null)throw new InvalidOperationException("Aircraft renderer collection unavailable");
        double[] worldMin={double.PositiveInfinity,double.PositiveInfinity,double.PositiveInfinity},worldMax={double.NegativeInfinity,double.NegativeInfinity,double.NegativeInfinity};
        Type vectorType=null;
        bool any=false;
        foreach(var renderer in renderers){
            if(!AirframeRenderer(renderer))continue;
            var bounds=Required(renderer,"bounds");var centerObject=Required(bounds,"center");var center=Vector(centerObject);var extents=Vector(Required(bounds,"extents"));
            if(extents[0]<0||extents[1]<0||extents[2]<0||extents[0]+extents[1]+extents[2]<=0)throw new InvalidOperationException("Unverified airframe bounds");
            any=true;vectorType=centerObject.GetType();
            for(int axis=0;axis<3;axis++){worldMin[axis]=Math.Min(worldMin[axis],center[axis]-extents[axis]);worldMax[axis]=Math.Max(worldMax[axis],center[axis]+extents[axis]);}
        }
        if(!any||worldMax[0]<=worldMin[0]||worldMax[1]<=worldMin[1]||worldMax[2]<=worldMin[2])throw new InvalidOperationException("Complete live airframe bounds unavailable");
        for(int axis=0;axis<3;axis++)if(!Finite(worldMin[axis])||!Finite(worldMax[axis])||Math.Abs(worldMin[axis])>float.MaxValue||Math.Abs(worldMax[axis])>float.MaxValue)throw new InvalidOperationException("World airframe bounds out of range");
        if(!VectorConstructors.TryGetValue(vectorType,out var vectorConstructor)){
            vectorConstructor=vectorType.GetConstructor(new[]{typeof(float),typeof(float),typeof(float)});
            if(vectorConstructor==null)throw new MissingMethodException(vectorType.FullName,".ctor(float,float,float)");VectorConstructors[vectorType]=vectorConstructor;
        }
        // One world union encloses every solid renderer, so transforming its
        // eight corners is conservative and independent of renderer count.
        double[] min={double.PositiveInfinity,double.PositiveInfinity,double.PositiveInfinity},max={double.NegativeInfinity,double.NegativeInfinity,double.NegativeInfinity};
        for(int bits=0;bits<8;bits++){
            var world=vectorConstructor.Invoke(new object[]{(float)((bits&1)==0?worldMin[0]:worldMax[0]),(float)((bits&2)==0?worldMin[1]:worldMax[1]),(float)((bits&4)==0?worldMin[2]:worldMax[2])});
            var localObject=Call(frame,"InverseTransformPoint",world);var local=Vector(localObject);
            var roundTrip=Vector(Call(frame,"TransformPoint",localObject));var expected=Vector(world);
            for(int axis=0;axis<3;axis++){
                if(Math.Abs(roundTrip[axis]-expected[axis])>1e-4*Math.Max(1,Math.Abs(expected[axis])))throw new InvalidOperationException("Unverified model coordinate frame");
                double metres=local[axis]*MetresPerUnit;min[axis]=Math.Min(min[axis],metres);max[axis]=Math.Max(max[axis],metres);
            }
        }
        return max[0]>=sweep.MinX&&min[0]<=sweep.MaxX&&max[1]>=sweep.MinY&&min[1]<=sweep.MaxY&&max[2]>=sweep.MinZ&&min[2]<=sweep.MaxZ;
    }
    internal static bool Clear(object owner,object deck,object modelFrame,Ciws6SweepVolume sweep,out string reason){
        reason=null;
        try{
            if(owner==null||deck==null||modelFrame==null||sweep==null)throw new InvalidOperationException("Missing aircraft clearance input");
            var limits=new[]{sweep.MinX,sweep.MinY,sweep.MinZ,sweep.MaxX,sweep.MaxY,sweep.MaxZ};
            foreach(var value in limits)if(!Finite(value))throw new InvalidOperationException("Non-finite swept volume");
            if(sweep.MinX>=sweep.MaxX||sweep.MinY>=sweep.MaxY||sweep.MinZ>=sweep.MaxZ)throw new InvalidOperationException("Invalid swept volume");
            var scale=Vector(Required(modelFrame,"lossyScale"));foreach(double axis in scale)if(Math.Abs(axis)<1e-8)throw new InvalidOperationException("Degenerate model frame");
            var aircraft=new HashSet<object>(ReferenceComparer.Instance);
            AddCollection(aircraft,ExistingObjectsManager(),"_listOfAllAircraftObjects");AddCollection(aircraft,owner,"_childAircraft");
            foreach(var name in new[]{"FlightDeckTasks","_flightDeckTasksToAdd","_flightDeckTasksToRemove"})foreach(var task in Collection(deck,name))Add(aircraft,Required(task,"Vehicle"));
            foreach(var name in new[]{"_elevators","_launchPoints","_recoveryPoints","_taxiPoints"})foreach(var point in Collection(deck,name)){
                var occupant=Required(point,"OccupyingObject");if(occupant!=null)Add(aircraft,occupant);else if(Flag(point,"IsOccupied"))throw new InvalidOperationException("Occupied point has no aircraft identity");
                AddCollection(aircraft,point,"_incomingObjects");
            }
            AddCollection(aircraft,deck,"_landingQueue");AddCollection(aircraft,deck,"_holdingQueue");
            var rendererType=RuntimeType("UnityEngine.Renderer");
            foreach(var value in aircraft)if(AircraftOverlaps(value,modelFrame,rendererType,sweep)){reason="AIRCRAFT_SWEEP_OCCUPIED";return false;}
            return true;
        }catch(Exception error){reason="AIRCRAFT_CLEARANCE_UNVERIFIED: "+error.GetBaseException().Message;return false;}
    }
}
}
