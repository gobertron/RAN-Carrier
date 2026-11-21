using System;
namespace RAN.Australis {
public enum DeckPhase { Stowed, Clearing, Opening, Ready, Closing }
// Weapon enclosure animation is independent of aviation. Target tracking never
// invents a shot or changes native targeting, ammunition or engagement rules.
public sealed class DeckCycle {
    public const double DeploySeconds=4.5, HoldSeconds=5, StowSeconds=300;
    public DeckPhase Phase {get;private set;}=DeckPhase.Stowed;
    public double Fraction {get;private set;}
    public double LastShot {get;private set;}=double.NegativeInfinity;
    double changed, previous=double.NaN, opened, lastDemand=double.NegativeInfinity;
    // Kept for callers of earlier controllers; bay movement no longer locks flight.
    public bool FlightLocked => false;
    public bool CanFire => Phase==DeckPhase.Ready && Fraction>=1;
    public void Request(double now) {
        // A live request renews an opening/ready mechanism before advancing
        // coarse simulation ticks; continuous demand must never invent stow.
        // An already closing mechanism advances first so its reversal starts
        // at the actual current pose rather than the previous frame's pose.
        ValidateTime(now);
        if(Phase!=DeckPhase.Closing)lastDemand=now;
        Tick(now);
        lastDemand=now;
        if(Phase==DeckPhase.Stowed){Phase=DeckPhase.Opening;changed=now;}
        else if(Phase==DeckPhase.Closing){Phase=DeckPhase.Opening;changed=now-Fraction*DeploySeconds;}
    }
    public void Shot(double now){ValidateTime(now);if(CanFire)LastShot=now;}
    static void ValidateTime(double now){if(double.IsNaN(now)||double.IsInfinity(now))throw new ArgumentException("Invalid simulation time");}
    public void Tick(double now){
        ValidateTime(now);
        if(!double.IsNaN(previous)&&now<previous){ // Mission reset changes enclosure state only.
            Phase=DeckPhase.Stowed;Fraction=0;changed=opened=now;LastShot=double.NegativeInfinity;lastDemand=double.NegativeInfinity;
        }
        previous=now;
        // A previously serialized Clearing state also proceeds without waiting
        // for launch, taxi or recovery tasks. New requests enter Opening directly.
        if(Phase==DeckPhase.Clearing){Phase=DeckPhase.Opening;changed=now;}
        if(Phase==DeckPhase.Opening){Fraction=Math.Max(0,Math.Min(1,(now-changed)/DeploySeconds));
            if(Fraction>=1){Phase=DeckPhase.Ready;opened=changed+DeploySeconds;}}
        if(Phase==DeckPhase.Ready&&now-Math.Max(lastDemand,Math.Max(opened,LastShot))>=HoldSeconds){Phase=DeckPhase.Closing;changed=Math.Max(lastDemand,Math.Max(opened,LastShot))+HoldSeconds;}
        if(Phase==DeckPhase.Closing){Fraction=Math.Max(0,1-(now-changed)/StowSeconds);
            if(Fraction<=0){Phase=DeckPhase.Stowed;}}
    }
    // Historical API compatibility: aircraft ownership is deliberately ignored.
    public void Tick(double now,bool deckClear)=>Tick(now);
    static double Clamp(double value)=>Math.Max(0,Math.Min(1,value));
    // The complete side housing first extends from its flush hull position.
    // Its roof doors open only after the housing stops. The gun then rises
    // vertically; there is no independent sideways gun/carriage stage.
    // Retraction reverses these stages over a full 300 simulation seconds.
    public double HousingFraction => Clamp(Fraction/.25);
    public double SponsonDoorFraction => Clamp((Fraction-.25)/.15);
    public double SponsonDoorPopFraction => Clamp(SponsonDoorFraction/.2);
    public double SponsonDoorSlideFraction => Clamp((SponsonDoorFraction-.2)/.8);
    public double SlideFraction => 0;
    public double RiseFraction => Clamp((Fraction-.4)/.6);
    // Ordinary deck covers and launchers retain their original motion stages.
    public double DoorFraction => Clamp(Fraction/.2);
    // Existing deck launchers/decoys retain their two-stage vertical motion.
    public double LiftFraction => Clamp((Fraction-.2)/.8);
}
}
