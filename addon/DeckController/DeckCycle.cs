using System;
namespace RAN.Australis {
public enum DeckPhase { Stowed, Clearing, Opening, Ready, Closing }
// Pure simulation-time policy. Target tracking never resets the last-shot timer.
public sealed class DeckCycle {
    public const double DeploySeconds=.75, HoldSeconds=300, StowSeconds=10;
    public DeckPhase Phase {get;private set;}=DeckPhase.Stowed;
    public double Fraction {get;private set;}
    public double LastShot {get;private set;}=double.NegativeInfinity;
    double changed, previous=double.NaN, opened;
    public bool FlightLocked => Phase!=DeckPhase.Stowed;
    public bool CanFire => Phase==DeckPhase.Ready;
    public void Request(double now) {
        if(Phase==DeckPhase.Stowed){Phase=DeckPhase.Clearing;changed=now;}
        else if(Phase==DeckPhase.Closing){Phase=DeckPhase.Opening;changed=now-Fraction*DeploySeconds;}
    }
    public void Shot(double now){if(CanFire)LastShot=now;}
    public void Tick(double now,bool deckClear){
        if(double.IsNaN(now)||double.IsInfinity(now))throw new ArgumentException("Invalid simulation time");
        if(!double.IsNaN(previous)&&now<previous){ // Mission reset: stow before permitting aviation.
            Phase=DeckPhase.Stowed;Fraction=0;LastShot=double.NegativeInfinity;
        }
        previous=now;
        if(Phase==DeckPhase.Clearing&&deckClear){Phase=DeckPhase.Opening;changed=now;}
        if(Phase==DeckPhase.Opening){Fraction=Math.Max(0,Math.Min(1,(now-changed)/DeploySeconds));
            if(Fraction>=1){Phase=DeckPhase.Ready;opened=now;}}
        if(Phase==DeckPhase.Ready&&now-Math.Max(opened,LastShot)>=HoldSeconds){Phase=DeckPhase.Closing;changed=now;}
        if(Phase==DeckPhase.Closing){Fraction=Math.Max(0,1-(now-changed)/StowSeconds);
            if(Fraction<=0){Phase=DeckPhase.Stowed;}}
    }
    // Open the doors first, then lift. Reverse order during slow closure.
    public double DoorFraction => Math.Min(1,Fraction*5);
    public double LiftFraction => Math.Max(0,(Fraction-.2)/.8);
}
}
