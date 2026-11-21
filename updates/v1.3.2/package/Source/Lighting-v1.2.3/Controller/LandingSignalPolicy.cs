using System;
namespace RAN.Australis {
public enum LandingSignal { Off, Low, OnSlope, High, WaveOff }
// A model-mounted approach indication only. It neither steers the aircraft nor
// grants recovery clearance. Native Sea Power recovery remains authoritative.
public static class LandingSignalPolicy {
    public const double GlideSlopeDegrees=3.5, OnSlopeBandDegrees=.25;
    public static LandingSignal Evaluate(double distance,double crossTrack,double height,bool deckFoul=false) {
        if(!Finite(distance)||!Finite(crossTrack)||!Finite(height)||distance<25||distance>6000||height<0||height>1200)return LandingSignal.Off;
        // Hide the ball away from the final-approach sector, including abeam
        // aircraft and aircraft already over/past the touchdown reference.
        if(Math.Abs(crossTrack)>Math.Max(120,distance*.12))return LandingSignal.Off;
        double slope=Math.Atan2(height,distance)*180/Math.PI;
        if(deckFoul||(distance<1200&&(Math.Abs(crossTrack)>Math.Max(18,distance*.025)||slope<1.75||slope>6.5)))return LandingSignal.WaveOff;
        if(slope<GlideSlopeDegrees-OnSlopeBandDegrees)return LandingSignal.Low;
        if(slope>GlideSlopeDegrees+OnSlopeBandDegrees)return LandingSignal.High;
        return LandingSignal.OnSlope;
    }
    public static bool Finite(double value)=>!double.IsNaN(value)&&!double.IsInfinity(value);
    public static bool WaveOffVisible(double now)=>Finite(now)&&now>=0&&now%.5<.25;
}
}
