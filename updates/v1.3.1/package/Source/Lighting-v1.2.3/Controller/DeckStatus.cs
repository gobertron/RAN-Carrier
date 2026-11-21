using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;
using System.Threading;
namespace RAN.Australis {
// Observes existing decisions only. A status sink failure must never affect the
// carrier controller, native admission, timing, movement or weapon rules.
internal sealed class DeckStatus {
    internal const double TransitionSeconds=1;
    static int nextInstance;
    readonly int instance=Interlocked.Increment(ref nextInstance);
    readonly string unit;
    readonly Action<string> sink;
    readonly Dictionary<string,Channel> channels=new Dictionary<string,Channel>();
    double previous=double.NaN;
    int episode=1;
    sealed class Value {
        internal readonly string State,Reason,Message;
        internal Value(string state,string reason,string message){State=state;Reason=reason;Message=message;}
        internal bool Same(Value other)=>other!=null&&State==other.State&&Reason==other.Reason&&Message==other.Message;
    }
    sealed class Channel {internal Value Sent,Pending;internal double At;}
    internal DeckStatus(string unit,Action<string> sink){
        this.unit=Token(unit);this.sink=sink;
    }
    static string Token(string value){
        if(string.IsNullOrEmpty(value))return "unknown";
        var result=new StringBuilder();
        foreach(char c in value)if(c>='a'&&c<='z'||c>='A'&&c<='Z'||c>='0'&&c<='9'||c=='_'||c=='-')result.Append(c);
        return result.Length==0?"unknown":result.ToString();
    }
    static string Quote(string value){
        var result=new StringBuilder("\"");
        foreach(char c in value??""){
            if(c=='"'||c=='\\')result.Append('\\').Append(c);
            else if(c<32)result.Append("\\u").Append(((int)c).ToString("x4",CultureInfo.InvariantCulture));
            else result.Append(c);
        }
        return result.Append('"').ToString();
    }
    bool Clock(double now){
        if(double.IsNaN(now)||double.IsInfinity(now)||now<0)return false;
        if(!double.IsNaN(previous)&&now<previous){channels.Clear();episode++;}
        previous=now;return true;
    }
    void Emit(string operation,Channel channel,Value value,double now){
        // Remember attempted writes too: an inaccessible log must not turn a
        // repeated native poll into repeated I/O attempts every frame.
        channel.Sent=value;channel.Pending=null;channel.At=now;
        string line="[AUSTRALIS_STATUS] schema=1 unit="+unit+" instance="+instance.ToString(CultureInfo.InvariantCulture)+
            " episode="+episode.ToString(CultureInfo.InvariantCulture)+" mission="+now.ToString("F3",CultureInfo.InvariantCulture)+
            " operation="+operation+" state="+value.State+" reason="+value.Reason+" message="+Quote(value.Message);
        try{sink?.Invoke(line);}catch{}
    }
    void Publish(string operation,Value value,double now,bool immediate=false){
        if(!channels.TryGetValue(operation,out var channel))channels.Add(operation,channel=new Channel());
        if(value.Same(channel.Sent)){channel.Pending=null;return;}
        channel.Pending=value;
        if(immediate||channel.Sent==null||now-channel.At>=TransitionSeconds)Emit(operation,channel,value,now);
    }
    void Flush(double now){
        foreach(var row in channels)if(row.Value.Pending!=null&&now-row.Value.At>=TransitionSeconds)Emit(row.Key,row.Value,row.Value.Pending,now);
    }
    void Initialize(double now,bool bound,bool fault){
        Publish("CONTROLLER",fault?new Value("FAULT","CONTROLLER_FAULT","Controller fault; new aviation admission held"):
            bound?new Value("READY","MODEL_BOUND","Controller bound and healthy; route availability is checked per request"):
            new Value("BINDING","MODEL_BINDING","Waiting for required carrier model transforms"),now,fault);
        if(!channels.ContainsKey("LAUNCH"))Publish("LAUNCH",new Value("IDLE","NO_REQUEST_OBSERVED","No launch request observed in this mission episode"),now);
        if(!channels.ContainsKey("RECOVERY"))Publish("RECOVERY",new Value("IDLE","NO_REQUEST_OBSERVED","No recovery request observed in this mission episode"),now);
    }
    internal void Tick(double now,bool bound,bool fault){
        try{if(!Clock(now))return;Initialize(now,bound,fault);Flush(now);}catch{}
    }
    internal void Admission(string operation,bool allowed,string error,bool bound,bool fault,double now){
        try{
            if(operation!="LAUNCH"&&operation!="RECOVERY"||!Clock(now))return;
            Initialize(now,bound,fault);
            Value value=allowed?new Value("ADMITTED","MOD_ADMISSION","Mod admission permitted native processing; launch or recovery completion is not confirmed"):
                fault?new Value("WAIT","CONTROLLER_FAULT","Controller fault; request held"):
                !bound?new Value("WAIT","MODEL_BINDING","Waiting for required carrier model transforms"):
                error!=null?new Value("ERROR","ROUTE_CHECK_ERROR",error):
                new Value("WAIT","NO_SAFE_COMPATIBLE_ROUTE","Waiting for a safe compatible route");
            Publish(operation,value,now);Flush(now);
        }catch{}
    }
    internal void Sixth(double now,string state,string reason){
        try{
            if(!Clock(now))return;
            string code=Token(reason);
            if(code!=reason||string.IsNullOrEmpty(reason))code="NATIVE_STATE_UNVERIFIED";
            foreach(char c in code)if(!(c>='A'&&c<='Z'||c>='0'&&c<='9'||c=='_')){code="NATIVE_STATE_UNVERIFIED";break;}
            string message="Sixth CIWS "+state.ToLowerInvariant()+"; original five remain fixed";
            if(!string.IsNullOrEmpty(reason))message+="; "+reason;
            Publish("CIWS6",new Value(state,code,message),now,state=="FAULT");Flush(now);
        }catch{}
    }
}
}
