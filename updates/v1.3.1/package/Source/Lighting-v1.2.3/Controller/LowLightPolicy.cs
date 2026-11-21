using System;
using System.Linq;
using System.Reflection;
namespace RAN.Australis {
// Relative rendering brightness, not calibrated lux. Scene sun and ambient
// illumination drive these local lights; no clock/weather/gameplay is changed.
internal sealed class LowLightPolicy {
    public const double OnBrightness=.20,OffBrightness=.30,BrightHoldSeconds=2,FadeSeconds=1;
    bool initialized,active;double previous=double.NaN,brightSince=double.NaN;
    public float Gain {get;private set;}
    public void Reset(){initialized=false;active=false;previous=brightSince=double.NaN;Gain=0;}
    public float Tick(double now,double brightness){
        if(!LandingSignalPolicy.Finite(now)){Reset();return Gain;}
        bool valid=LandingSignalPolicy.Finite(brightness)&&brightness>=0;
        if(!initialized||now<previous){
            active=valid?brightness<=OnBrightness:active;Gain=active?1:0;
            initialized=true;previous=now;brightSince=double.NaN;return Gain;
        }
        double elapsed=Math.Min(1,Math.Max(0,now-previous));previous=now;
        if(valid){
            if(brightness<=OnBrightness){active=true;brightSince=double.NaN;}
            else if(brightness>=OffBrightness){
                if(double.IsNaN(brightSince))brightSince=now;
                if(now-brightSince>=BrightHoldSeconds)active=false;
            }else brightSince=double.NaN;
        }else brightSince=double.NaN; // An unreadable frame retains the last state.
        float step=(float)(elapsed/FadeSeconds);
        Gain=active?Math.Min(1,Gain+step):Math.Max(0,Gain-step);return Gain;
    }
}
internal static class LowLightEnvironment {
    const BindingFlags Static=BindingFlags.Public|BindingFlags.Static;
    static Type Find(string name)=>AppDomain.CurrentDomain.GetAssemblies().Select(a=>a.GetType(name,false)).FirstOrDefault(t=>t!=null);
    static object Read(Type type,string name){try{return type?.GetProperty(name,Static)?.GetValue(null);}catch{return null;}}
    static double Number(object value,double fallback=double.NaN){try{double n=Convert.ToDouble(value);return value!=null&&LandingSignalPolicy.Finite(n)?n:fallback;}catch{return fallback;}}
    static double Lum(object color){
        if(color==null)return double.NaN;
        double r=Number(Reflect.Get(color,"r")),g=Number(Reflect.Get(color,"g")),b=Number(Reflect.Get(color,"b"));
        return LandingSignalPolicy.Finite(r)&&LandingSignalPolicy.Finite(g)&&LandingSignalPolicy.Finite(b)?Math.Max(0,.2126*r+.7152*g+.0722*b):double.NaN;
    }
    static double Probe(object probe){
        if(probe==null)return double.NaN;
        try{
            Type vector=Find("UnityEngine.Vector3"),color=Find("UnityEngine.Color");
            var directions=Array.CreateInstance(vector,5);var colors=Array.CreateInstance(color,5);
            float[][] axes={new[]{0f,1f,0f},new[]{1f,0f,0f},new[]{-1f,0f,0f},new[]{0f,0f,1f},new[]{0f,0f,-1f}};
            for(int i=0;i<5;i++)directions.SetValue(Activator.CreateInstance(vector,axes[i][0],axes[i][1],axes[i][2]),i);
            Reflect.Call(probe,"Evaluate",directions,colors);double sum=0;
            foreach(object item in colors){double n=Lum(item);if(!LandingSignalPolicy.Finite(n))return double.NaN;sum+=n;}
            return sum/5;
        }catch{return double.NaN;}
    }
    static double FogTransmission(Type settings){
        if(!Equals(Read(settings,"fog"),true))return 1;
        // A one-kilometre sightline in this model's native world units provides
        // a bounded visual proxy for dense weather. This does not change
        // fog or claim to simulate cloud optical depth or real illuminance.
        double distance=1000/BayData.MetresPerUnit,transmission=1;
        string mode=Convert.ToString(Read(settings,"fogMode"));
        if(mode=="Linear"){
            double start=Number(Read(settings,"fogStartDistance")),end=Number(Read(settings,"fogEndDistance"));
            if(LandingSignalPolicy.Finite(start)&&LandingSignalPolicy.Finite(end)&&end>start)transmission=Math.Max(0,Math.Min(1,(end-distance)/(end-start)));
        }else if(mode=="Exponential"||mode=="ExponentialSquared"){
            double density=Number(Read(settings,"fogDensity"));
            if(LandingSignalPolicy.Finite(density)&&density>=0){double optical=density*distance;transmission=mode=="ExponentialSquared"?Math.Exp(-optical*optical):Math.Exp(-optical);}
        }
        return transmission<=.35?transmission:1;
    }
    public static double Brightness(){
        Type settings=Find("UnityEngine.RenderSettings");if(settings==null)return double.NaN;
        object sun=Read(settings,"sun");double direct=0;bool validDirect=false;
        if(sun!=null){
            bool enabled=!Equals(Reflect.Get(sun,"enabled"),false);
            double intensity=Number(Reflect.Get(sun,"intensity"));validDirect=!enabled||LandingSignalPolicy.Finite(intensity);
            double color=Lum(Reflect.Get(sun,"color"));if(!LandingSignalPolicy.Finite(color))color=1;
            double forwardY=Number(Reflect.Get(Reflect.Get(Reflect.Get(sun,"transform"),"forward"),"y"));
            double downward=LandingSignalPolicy.Finite(forwardY)?Math.Max(0,Math.Min(1,-forwardY)):1;
            direct=enabled&&LandingSignalPolicy.Finite(intensity)?Math.Max(0,intensity)*color*downward:0;
        }
        string mode=Convert.ToString(Read(settings,"ambientMode"));double ambient=double.NaN;
        if(mode=="Skybox"){
            ambient=Probe(Read(settings,"ambientProbe"));
            double intensity=Number(Read(settings,"ambientIntensity"),1);
            if(LandingSignalPolicy.Finite(ambient))ambient*=Math.Max(0,intensity);
        }else if(mode=="Trilight"){
            double sky=Lum(Read(settings,"ambientSkyColor")),equator=Lum(Read(settings,"ambientEquatorColor")),ground=Lum(Read(settings,"ambientGroundColor"));
            if(new[]{sky,equator,ground}.All(LandingSignalPolicy.Finite))ambient=.5*sky+.35*equator+.15*ground;
        }
        if(!LandingSignalPolicy.Finite(ambient))ambient=Lum(Read(settings,"ambientLight"));
        // Missing/disabled sun can occur at night; use the observable ambient
        // fallback instead of treating a missing sun as permanent daytime.
        if(!validDirect&&!LandingSignalPolicy.Finite(ambient))return double.NaN;
        bool belowHorizon=sun!=null&&Number(Reflect.Get(Reflect.Get(Reflect.Get(sun,"transform"),"forward"),"y"))>=0;
        return Combine(direct,ambient,FogTransmission(settings),belowHorizon);
    }
    internal static double Combine(double direct,double ambient,double transmission,bool belowHorizon){
        // A retained ambient probe must not prevent night activation after sunset.
        double fill=LandingSignalPolicy.Finite(ambient)?Math.Max(0,ambient):0;
        if(belowHorizon)fill=Math.Min(fill,.20);
        double brightness=Math.Max(0,direct*transmission+.6*fill);
        // Visibility lights are needed in dense fog even when its colour is grey
        // or bright. Do not require fogColour to be almost black.
        if(transmission<=.35)brightness=Math.Min(brightness,.5*transmission);
        return brightness;
    }
}
}
