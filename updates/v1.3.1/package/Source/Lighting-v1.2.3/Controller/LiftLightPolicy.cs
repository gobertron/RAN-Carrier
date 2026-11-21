using System;
namespace RAN.Australis {
// Actual platform height controls illumination in both directions. No timer
// can leave a lit shaft when the platform is flush with the flight deck.
public static class LiftLightPolicy {
    public const double DeckY=22.002, LowerY=11.8, OffDepth=.10, FullDepth=.60;
    public static float Gain(double heightMetres) {
        if(double.IsNaN(heightMetres)||double.IsInfinity(heightMetres)||
           heightMetres<LowerY-.10||heightMetres>DeckY+.10)return 0;
        double t=Math.Max(0,Math.Min(1,(DeckY-heightMetres-OffDepth)/(FullDepth-OffDepth)));
        return (float)(t*t*(3-2*t));
    }
}
}
