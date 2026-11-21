namespace RAN.Australis {
internal enum MotionRole { Door, Lift, SponsonHousing, SponsonDoor, SponsonSlide, SponsonLift }
// Coordinates and travel are physical metres from the same authored motion
// data used by the native model exporter. Only parent positions are changed;
// turret yaw and gun elevation remain under native weapon control.
internal sealed class Motion {
    public readonly string Name;
    public readonly double X,Y,Z,Travel,SlideX,SlideY,SlideZ,RiseX,RiseY,RiseZ,HousingX,HousingY,HousingZ;
    public readonly double DoorPopX,DoorPopY,DoorPopZ,DoorSlideX,DoorSlideY,DoorSlideZ;
    public readonly char Axis;
    public readonly MotionRole Role;
    public Motion(string name,double x,double y,double z,char axis,double travel,
                  MotionRole role,double slideX,double slideY,double slideZ,
                  double riseX,double riseY,double riseZ,
                  double housingX=0,double housingY=0,double housingZ=0,
                  double doorPopX=0,double doorPopY=0,double doorPopZ=0,
                  double doorSlideX=0,double doorSlideY=0,double doorSlideZ=0){
        Name=name;X=x;Y=y;Z=z;Axis=axis;Travel=travel;Role=role;
        SlideX=slideX;SlideY=slideY;SlideZ=slideZ;
        RiseX=riseX;RiseY=riseY;RiseZ=riseZ;
        HousingX=housingX;HousingY=housingY;HousingZ=housingZ;
        DoorPopX=doorPopX;DoorPopY=doorPopY;DoorPopZ=doorPopZ;
        // Explicit vector data supports the roof panels. The axis fallback is
        // for older/synthetic pod-door callers without vector arguments.
        bool vectors=doorPopX!=0||doorPopY!=0||doorPopZ!=0||doorSlideX!=0||doorSlideY!=0||doorSlideZ!=0;
        DoorSlideX=vectors?doorSlideX:(role==MotionRole.SponsonDoor&&axis=='x'?travel:0);
        DoorSlideY=vectors?doorSlideY:(role==MotionRole.SponsonDoor&&axis=='y'?travel:0);
        DoorSlideZ=vectors?doorSlideZ:(role==MotionRole.SponsonDoor&&axis=='z'?travel:0);
    }
    public void Position(DeckCycle cycle,out double x,out double y,out double z){
        // Every independently registered pod root carries the housing stage
        // exactly once. Native gun descendants inherit it through their lift.
        x=X+HousingX*cycle.HousingFraction;
        y=Y+HousingY*cycle.HousingFraction;
        z=Z+HousingZ*cycle.HousingFraction;
        if(Role==MotionRole.SponsonLift || Role==MotionRole.SponsonSlide){
            x+=SlideX*cycle.SlideFraction+RiseX*cycle.RiseFraction;
            y+=SlideY*cycle.SlideFraction+RiseY*cycle.RiseFraction;
            z+=SlideZ*cycle.SlideFraction+RiseZ*cycle.RiseFraction;
        }else if(Role==MotionRole.SponsonDoor){
            // Lift the roof leaf clear before sliding it along the housing.
            // Reversing these fractions closes the leaf before seating.
            x+=DoorPopX*cycle.SponsonDoorPopFraction+DoorSlideX*cycle.SponsonDoorSlideFraction;
            y+=DoorPopY*cycle.SponsonDoorPopFraction+DoorSlideY*cycle.SponsonDoorSlideFraction;
            z+=DoorPopZ*cycle.SponsonDoorPopFraction+DoorSlideZ*cycle.SponsonDoorSlideFraction;
        }else if(Role!=MotionRole.SponsonHousing){
            double fraction=Role==MotionRole.Door?cycle.DoorFraction:cycle.LiftFraction;
            if(Axis=='x')x+=Travel*fraction;
            else if(Axis=='y')y+=Travel*fraction;
            else if(Axis=='z')z+=Travel*fraction;
        }
    }
}
}
