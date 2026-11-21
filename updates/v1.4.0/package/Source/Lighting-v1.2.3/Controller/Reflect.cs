using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
namespace RAN.Australis {
// Reflect against the user-supplied game/Unity runtime. No game assembly is
// linked into or redistributed with this independent plugin.
internal static class Reflect {
    const BindingFlags Declared=BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Instance|BindingFlags.Static|BindingFlags.DeclaredOnly;
    const BindingFlags Instance=BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Instance;
    static readonly Dictionary<string,FieldInfo> Fields=new Dictionary<string,FieldInfo>();
    public static FieldInfo Field(Type type,string name){
        string key=type.AssemblyQualifiedName+":"+name;
        if(Fields.TryGetValue(key,out var field))return field;
        for(var current=type;current!=null;current=current.BaseType){
            field=current.GetField(name,Declared);
            if(field!=null){Fields[key]=field;return field;}
        }
        return null;
    }
    public static object Get(object value,string name){
        if(value==null)return null;
        var field=Field(value.GetType(),name);if(field!=null)return field.GetValue(value);
        for(var current=value.GetType();current!=null;current=current.BaseType){
            var property=current.GetProperty(name,Declared);
            if(property!=null)return property.GetValue(value);
        }
        return null;
    }
    public static object Call(object value,string name,params object[] args){
        if(value==null)return null;
        // Unity has SetParent(Transform) / SetParent(Transform,bool), and
        // InverseTransformPoint(Vector3) / InverseTransformPoint(x,y,z).
        // Name-only GetMethod throws before either call reaches Unity.
        var candidates=value.GetType().GetMethods(Instance)
            .Where(m=>m.Name==name&&!m.ContainsGenericParameters&&m.GetParameters().Length==args.Length)
            .Where(m=>m.GetParameters().Select((p,i)=>args[i]==null
                ?(!p.ParameterType.IsValueType||Nullable.GetUnderlyingType(p.ParameterType)!=null)
                :p.ParameterType.IsInstanceOfType(args[i])).All(ok=>ok)).ToArray();
        if(candidates.Length==0)throw new MissingMethodException(value.GetType().FullName,name+"/"+args.Length);
        // Prefer the exact parameter signature over an object fallback.
        int Exact(MethodInfo method)=>method.GetParameters().Select((p,i)=>args[i]!=null&&p.ParameterType==args[i].GetType()?1:0).Sum();
        int score=candidates.Max(Exact);candidates=candidates.Where(m=>Exact(m)==score).ToArray();
        if(candidates.Length!=1)throw new AmbiguousMatchException(value.GetType().FullName+"."+name+"/"+args.Length);
        return candidates[0].Invoke(value,args);
    }
    public static int Count(object value)=>value is ICollection collection?collection.Count:0;
}
}
