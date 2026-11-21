using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Runtime.CompilerServices;
namespace RAN.Australis {
// Exact surveyed operation reservations. All native lifetime/support checks remain
// authoritative. Temporary candidate field references are restored by finalizers.
internal static class DeckTraffic {
    static readonly string[] Groups={"_elevators","_launchPoints","_recoveryPoints"};
    const int CatapultCount=4;
    static readonly int[] Counts={4,7,4};
    static readonly ConditionalWeakTable<object,State> States=new ConditionalWeakTable<object,State>();
    [ThreadStatic] static Scope currentLaunch;
    internal sealed class Scope {
        internal readonly object Deck;internal object Vehicle;internal bool RecoveryAdmission;
        internal Scope Previous;internal bool IsLaunch,FixedWing,BowFallbackMayConsume;bool restored;
        internal readonly Dictionary<object,RouteTrafficOperation> Plans=new Dictionary<object,RouteTrafficOperation>(References.Instance);
        readonly List<Change> changes=new List<Change>();
        internal Scope(object deck){Deck=deck;}
        internal void Replace(object owner,string member,object value){
            var field=Reflect.Field(owner.GetType(),member);
            if(field==null)throw new MissingFieldException(owner.GetType().FullName,member);
            changes.Add(new Change(owner,field,field.GetValue(owner)));field.SetValue(owner,value);
        }
        internal void Restore(){
            if(restored)return;restored=true;
            Exception failure=null;
            try {for(int i=changes.Count-1;i>=0;i--)try{changes[i].Field.SetValue(changes[i].Owner,changes[i].Value);}catch(Exception e){failure=failure??e;}}
            finally {if(IsLaunch)currentLaunch=Previous;}
            if(failure!=null)throw new InvalidOperationException("Native candidate restoration failed",failure);
        }
    }
    sealed class Change {internal readonly object Owner,Value;internal readonly FieldInfo Field;
        internal Change(object o,FieldInfo f,object v){Owner=o;Field=f;Value=v;}}
    sealed class State {
        internal readonly Dictionary<object,int> Plans=new Dictionary<object,int>(References.Instance);
        internal bool PreferWaist;
        internal int NextWaist=3;
        internal int NextBow=1;
    }
    sealed class References:IEqualityComparer<object> {
        internal static readonly References Instance=new References();
        public new bool Equals(object a,object b)=>ReferenceEquals(a,b);
        public int GetHashCode(object value)=>RuntimeHelpers.GetHashCode(value);
    }
    sealed class Contact {internal int E,L,R;}
    sealed class Snapshot {
        internal readonly Dictionary<object,Contact> Contacts=new Dictionary<object,Contact>(References.Instance);
        internal ulong Mask;internal bool RearBusy,FixedRecovery,AnyRecovery,WaistBusy;
    }
    internal static void Finish(Scope scope){scope?.Restore();}
    internal static bool BeginLaunch(object pending,out Scope scope,out string error,Func<int,bool> deflectorFlat=null){
        scope=null;error=null;
        try {
            var deck=Required(pending,"_flightDeck");var snapshot=Read(deck);
            var task=Required(pending,"_launchTask");var type=Required(task,"VehicleType");
            string kind=Convert.ToString(Required(type,"_type"));object nativeKind=Required(pending,"vehicleType");
            bool vertical=kind=="Helicopter"||kind=="VTOL",fixedWing=kind=="Plane"||kind=="STOL";
            if(!vertical&&!fixedWing)return false;
            string loadout=Loadout(task,type,kind);
            var candidates=Required(pending,"_elevators") as IList;
            if(candidates==null)throw new InvalidOperationException("Pending elevator candidates unavailable");
            var elevators=Points(deck,0);var launches=Points(deck,1);
            var state=States.GetValue(deck,_=>new State());
            // Preserve an owed bow while traffic temporarily blocks it. A
            // genuinely omitted/unsupported bow must not prevent the offered
            // fallback bow from yielding to a ready waist after its own turn.
            bool owedBowOffered=false;
            if(fixedWing)foreach(var elevator in candidates){
                int e=Index(elevators,elevator);
                if(e==0)throw new InvalidOperationException("Pending elevator does not belong to carrier");
                var ids=Required(elevator,"_launchPoints") as IList;
                if(ids==null)throw new InvalidOperationException("Native launch associations unavailable");
                if(!ids.Cast<object>().Any(v=>Convert.ToInt32(v)==state.NextBow))continue;
                var point=launches[state.NextBow-1];var operation=Find(0,e,0,state.NextBow,0);
                if(operation!=null&&Allowed(point,nativeKind)&&Support(elevator,type,loadout)&&
                    Support(point,type,loadout)&&FlatDeflectors(operation,deflectorFlat))owedBowOffered=true;
            }
            var drainingFor=new List<RouteTrafficOperation>();
            if(fixedWing&&state.PreferWaist&&!snapshot.AnyRecovery){
                ulong committedBows=0;
                foreach(var operation in RouteTrafficData.Operations)
                    if(operation.FromKind==0&&operation.ToIndex<=2)committedBows|=1UL<<operation.Id;
                foreach(var elevator in candidates){
                    int e=Index(elevators,elevator);
                    if(e==0)throw new InvalidOperationException("Pending elevator does not belong to carrier");
                    if(Flag(elevator,"IsBusy")||!Support(elevator,type,loadout))continue;
                    var ids=Required(elevator,"_launchPoints") as IList;
                    if(ids==null)throw new InvalidOperationException("Native launch associations unavailable");
                    if(!ids.Cast<object>().Any(v=>Convert.ToInt32(v)==state.NextWaist))continue;
                    var point=launches[state.NextWaist-1];
                    if(Flag(point,"IsBusy")||!Allowed(point,nativeKind)||!Support(point,type,loadout))continue;
                    var desired=Find(0,e,0,state.NextWaist,0);
                    if(desired==null||!Safe(desired,snapshot.Mask&~committedBows)||!FlatDeflectors(desired,deflectorFlat))continue;
                    // Native IsBusy counts even null/destroyed incoming
                    // entries. Keep its point blockers authoritative, but do
                    // not manufacture an extra software drain when no live or
                    // retained bow operation exists to clear that raw wait.
                    bool unmappedBusyBow=false;
                    for(int p=1;p<=2;p++)if(Flag(launches[p-1],"IsBusy")){
                        ulong pointOperations=0;
                        foreach(var op in RouteTrafficData.Operations)
                            if(op.FromKind==0&&op.ToKind==0&&op.ToIndex==p)pointOperations|=1UL<<op.Id;
                        if((desired.ConflictMask&pointOperations)!=0&&(snapshot.Mask&pointOperations)==0)unmappedBusyBow=true;
                    }
                    if(unmappedBusyBow)continue;
                    // Native raw point reservations may precede aircraft/task
                    // publication. Do not drain bows for an independently busy
                    // non-bow point that shares this complete operation.
                    bool nonBowBlocked=false;
                    for(int p=3;p<=launches.Count;p++)if(p!=state.NextWaist&&Flag(launches[p-1],"IsBusy"))
                        foreach(var op in RouteTrafficData.Operations)
                            if(op.FromKind==0&&op.ToKind==0&&op.ToIndex==p&&(desired.ConflictMask&(1UL<<op.Id))!=0)nonBowBlocked=true;
                    if(!nonBowBlocked)drainingFor.Add(desired);
                }
            }
            var selections=new List<Tuple<object,RouteTrafficOperation,int>>();
            foreach(var elevator in candidates){
                int e=Index(elevators,elevator);
                if(e==0)throw new InvalidOperationException("Pending elevator does not belong to carrier");
                if(vertical&&e<3)continue;
                if(Flag(elevator,"IsBusy")||Flag(elevator,"IsBlockedByPoint")||!Support(elevator,type,loadout))continue;
                var ids=Required(elevator,"_launchPoints") as IList;
                if(ids==null)throw new InvalidOperationException("Native launch associations unavailable");
                RouteTrafficOperation chosen=null;int best=int.MaxValue;int ordinal=0;
                foreach(var value in ids){
                    int id=Convert.ToInt32(value);ordinal++;
                    if(id<1||id>launches.Count||(vertical?id<=CatapultCount:id>CatapultCount))continue;
                    var point=launches[id-1];
                    if(!Allowed(point,nativeKind)||!Support(point,type,loadout)||Flag(point,"IsBusy")||Flag(point,"IsBlockedByPoint"))continue;
                    var operation=Find(0,e,0,id,id<=CatapultCount?0:1);
                    if(operation==null||!Permitted(operation,snapshot)||!FlatDeflectors(operation,deflectorFlat))continue;
                    if(id<=2&&drainingFor.Any(desired=>(operation.ConflictMask&(1UL<<desired.Id))!=0))continue;
                    // A new peer waist cannot keep renewing the shared zone
                    // while the eligible preferred waist drains committed bows.
                    if(id>=3&&id<=CatapultCount&&id!=state.NextWaist&&
                        drainingFor.Any(desired=>(operation.ConflictMask&(1UL<<desired.Id))!=0))continue;
                    int rank=vertical?VerticalRank(id)*100+ordinal:
                        (state.PreferWaist?id==state.NextWaist:id==state.NextBow)?0:ordinal+1;
                    if(rank<best){best=rank;chosen=operation;}
                }
                if(chosen!=null)selections.Add(Tuple.Create(elevator,chosen,best));
            }
            if(selections.Count==0)return false;
            scope=new Scope(deck){FixedWing=fixedWing,BowFallbackMayConsume=!owedBowOffered};
            if(kind=="Helicopter"||kind=="VTOL")selections=selections.OrderBy(row=>row.Item3).ToList();
            // The shared bow turn alternates C1/C2; the waist turn alternates
            // C3/C4. Opportunistic compatible admissions preserve any owed bow.
            // A blocked preferred waist permits safe fallbacks to keep moving.
            else if(scope.FixedWing)
                selections=selections.OrderBy(row=>state.PreferWaist?
                    (row.Item2.ToIndex==state.NextWaist?0:row.Item2.ToIndex>=3?1:2):
                    (row.Item2.ToIndex==state.NextBow?0:row.Item2.ToIndex<=2?1:
                        row.Item2.ToIndex==state.NextWaist?2:3)).ToList();
            scope.Replace(pending,"_elevators",Clone(candidates,selections.Select(row=>row.Item1)));
            foreach(var selection in selections){
                var original=(IList)Required(selection.Item1,"_launchPoints");
                scope.Replace(selection.Item1,"_launchPoints",Clone(original,new object[]{selection.Item2.ToIndex}));
                // The native spawning path reads this float synchronously. Keep
                // its original value untouched outside this task's scope.
                scope.Replace(selection.Item1,"_spawnRotation",selection.Item2.StartHeading);
                scope.Plans.Add(selection.Item1,selection.Item2);
            }
            scope.IsLaunch=true;scope.Previous=currentLaunch;currentLaunch=scope;return true;
        }catch(Exception failure){error=failure.GetBaseException().Message;try{scope?.Restore();}catch(Exception restore){error+="; "+restore.GetBaseException().Message;}scope=null;return false;}
    }
    // Native launchVehicle reserves E synchronously before this postfix; the plan
    // is attached before pending.Launched callbacks or the next pending update.
    internal static void Spawned(object deck,object elevator,object vehicle){
        if(currentLaunch==null||!ReferenceEquals(currentLaunch.Deck,deck)||!Live(vehicle))return;
        if(!currentLaunch.Plans.TryGetValue(elevator,out var plan))throw new InvalidOperationException("Native spawn used an unreserved elevator");
        var state=States.GetValue(deck,_=>new State());state.Plans[vehicle]=plan.Id;
        if(currentLaunch.FixedWing){
            if(plan.ToIndex<=2&&!state.PreferWaist){
                if(plan.ToIndex==state.NextBow){
                    state.PreferWaist=true;state.NextBow=plan.ToIndex==1?2:1;
                }else if(currentLaunch.BowFallbackMayConsume)state.PreferWaist=true;
            }else if(plan.ToIndex==3||plan.ToIndex==4){
                // Yield the shared corridor to the still-owed bow after any
                // waist admission, including an opportunistic peer admission.
                // An opportunistic peer cannot erase the still-deferred waist.
                state.PreferWaist=false;
                if(plan.ToIndex==state.NextWaist)state.NextWaist=plan.ToIndex==3?4:3;
            }
        }
    }
    // Supply the reserved route's lift heading through the native ride API.
    // No transform, taxi controller, physics or committed movement is replaced.
    internal static bool TryRideHeading(object elevator,object vehicle,out float heading,out string error){
        heading=0;error=null;
        try {
            if(!Live(vehicle))return false;
            var deck=Required(elevator,"_flightDeck");int e=Index(Points(deck,0),elevator);
            if(e==0)return false;
            RouteTrafficOperation plan=null;
            if(States.TryGetValue(deck,out var state)&&state.Plans.TryGetValue(vehicle,out int id)){
                var candidate=ById(id);
                if((candidate.FromKind==0?candidate.FromIndex:candidate.ToIndex)!=e)return false;
                // A retired plan must not alter a later native/foreign ride.
                var contacts=Contacts(deck);
                if(!contacts.Contacts.ContainsKey(vehicle))return false;
                plan=candidate;
            }else if(currentLaunch!=null&&ReferenceEquals(currentLaunch.Deck,deck)){
                // getObjectToLaunch can ask for ride orientation before the
                // synchronous launchVehicle postfix records the actual vehicle.
                currentLaunch.Plans.TryGetValue(elevator,out plan);
            }
            if(plan==null)return false;
            heading=plan.FromKind==0?plan.StartHeading:plan.EndHeading;
            if(float.IsNaN(heading)||float.IsInfinity(heading))throw new InvalidOperationException("Reserved lift heading is invalid");
            return true;
        }catch(Exception failure){error=failure.GetBaseException().Message;return false;}
    }
    // Run native selection with one pinned ID. Do not substitute its result or
    // bypass support/loadout/blocker checks. A failed native choice waits safely.
    internal static bool BeginPointSelection(object elevator,out Scope scope,out string error){
        scope=null;error=null;
        try {
            var deck=Required(elevator,"_flightDeck");var state=States.GetValue(deck,_=>new State());
            var incoming=Required(elevator,"_incomingObjects") as ICollection;
            if(incoming==null)throw new InvalidOperationException("Elevator reservations unavailable");
            RouteTrafficOperation plan=null;
            foreach(var vehicle in incoming){
                if(!Live(vehicle)||!state.Plans.TryGetValue(vehicle,out int id))continue;
                var candidate=ById(id);if(candidate.FromKind!=0)continue;
                if(plan!=null&&plan.Id!=candidate.Id)throw new InvalidOperationException("Multiple pinned launches share an elevator");plan=candidate;
            }
            if(plan==null)return true;
            scope=new Scope(deck);var original=(IList)Required(elevator,"_launchPoints");
            scope.Replace(elevator,"_launchPoints",Clone(original,new object[]{plan.ToIndex}));return true;
        }catch(Exception failure){error=failure.GetBaseException().Message;try{scope?.Restore();}catch(Exception restore){error+="; "+restore.GetBaseException().Message;}scope=null;return false;}
    }
    // Native recovery tests RP then chooses least-busy compatible E. Restrict
    // each RP candidate list, so a safe alternative cannot authorize an unsafe E.
    internal static bool BeginRecovery(object holding,object vehicle,out Scope scope,out string error,Func<int,bool> deflectorFlat=null){
        scope=null;error=null;
        try {
            var deck=Required(holding,"_flightDeck");var snapshot=Read(deck);
            if(deflectorFlat!=null&&(!deflectorFlat(3)||!deflectorFlat(4)))return false;
            var recoveries=Points(deck,2);var elevators=Points(deck,0);object nativeKind=Required(holding,"_vehicleType");
            string kind=Convert.ToString(nativeKind);bool vertical=kind=="Helicopter"||kind=="VTOL",fixedWing=kind=="Plane"||kind=="STOL";
            scope=new Scope(deck){Vehicle=vehicle,RecoveryAdmission=true};bool any=false;
            for(int r=1;r<=recoveries.Count;r++){
                var point=recoveries[r-1];var original=Required(point,"_elevators") as IList;
                if(original==null)throw new InvalidOperationException("Recovery elevator associations unavailable");
                var permitted=new List<object>();
                if((vertical?r>1:fixedWing&&r==1)&&Allowed(point,nativeKind))foreach(var elevator in original){
                    int e=Index(elevators,elevator);
                    if(e==0)throw new InvalidOperationException("Recovery elevator does not belong to carrier");
                    if(vertical&&e<3||fixedWing&&e>2)continue;
                    var operation=Find(1,r,1,e,r==1?0:1);
                    if(operation!=null&&Permitted(operation,snapshot)&&FlatDeflectors(operation,deflectorFlat))permitted.Add(elevator);
                }
                // Lift 2's surveyed return lane leaves Lift 1/C2 available for
                // a following bow launch. Keep Lift 1 as the native fallback.
                if(fixedWing&&r==1)permitted=permitted.OrderBy(e=>Index(elevators,e)==2?0:1).ToList();
                scope.Replace(point,"_elevators",Clone(original,permitted));if(permitted.Count>0)any=true;
            }
            return any;
        }catch(Exception failure){error=failure.GetBaseException().Message;try{scope?.Restore();}catch(Exception restore){error+="; "+restore.GetBaseException().Message;}scope=null;return false;}
    }
    internal static void FinishRecovery(Scope scope,Exception exception){
        if(scope==null)return;scope.Restore();
        if(exception!=null||!scope.RecoveryAdmission||!Live(scope.Vehicle))return;
        var snapshot=Contacts(scope.Deck);
        if(!snapshot.Contacts.TryGetValue(scope.Vehicle,out var contact)||contact.R==0||contact.E==0)return;
        var operation=Find(1,contact.R,1,contact.E,contact.R==1?0:1);
        if(operation==null)throw new InvalidOperationException("Native recovery selected an unmodelled route");
        States.GetValue(scope.Deck,_=>new State()).Plans[scope.Vehicle]=operation.Id;
    }
    internal static bool Safe(RouteTrafficOperation operation,ulong occupied)=>(operation.ConflictMask&occupied)==0;
    static bool FlatDeflectors(RouteTrafficOperation operation,Func<int,bool> flat){
        if(flat==null)return true;
        for(int id=1;id<=CatapultCount;id++)
            if((operation.RequiredFlatJBDMask&(1U<<(id-1)))!=0&&!flat(id))return false;
        return true;
    }
    // Read only the delivered Unity transform. Native animation retains sole
    // ownership of deflector movement. A destroyed takeoff can leave a raised
    // orphan with no point/task owner, so logical reservation release alone is
    // insufficient evidence that its deck surface is clear again.
    internal static bool DeflectorFlat(object transform,int catapult,out string error){
        error=null;
        try{
            if(catapult<1||catapult>CatapultCount)throw new InvalidOperationException("Unknown physical catapult deflector");
            var angles=Required(transform,"localEulerAngles");
            double x=Convert.ToDouble(Required(angles,"x")),y=Convert.ToDouble(Required(angles,"y")),z=Convert.ToDouble(Required(angles,"z"));
            if(new[]{x,y,z}.Any(a=>double.IsNaN(a)||double.IsInfinity(a)))throw new InvalidOperationException("Non-finite physical deflector pose");
            var plan=RouteTrafficData.Operations.FirstOrDefault(p=>p.FromKind==0&&p.ToIndex==catapult&&p.Category==0);
            if(plan==null)throw new InvalidOperationException("Missing deflector heading contract");
            Func<double,double,double> delta=(a,b)=>Math.Abs(Math.IEEERemainder(a-b,360));
            return delta(x,0)<=.1&&delta(y,plan.EndHeading)<=.1&&delta(z,0)<=.1;
        }catch(Exception failure){error=failure.GetBaseException().Message;return false;}
    }
    static bool ArrestedRecovery(RouteTrafficOperation operation)=>operation.FromKind==1&&operation.FromIndex==1;
    static bool Recovery(RouteTrafficOperation operation)=>operation.FromKind==1;
    static bool WaistLaunch(RouteTrafficOperation operation)=>operation.FromKind==0&&(operation.ToIndex==3||operation.ToIndex==4);
    static bool RearOperation(RouteTrafficOperation operation)=>operation.FromKind==0?
        operation.FromIndex>=3||operation.ToIndex==3||operation.ToIndex==4:operation.ToIndex>=3;
    static bool Permitted(RouteTrafficOperation operation,Snapshot snapshot){
        if(!Safe(operation,snapshot.Mask))return false;
        // Both waist tracks are unavailable throughout every aircraft recovery,
        // including helicopter/VTOL pad returns. The reciprocal rule lets an
        // already committed waist operation finish before a new landing starts.
        if(WaistLaunch(operation)&&snapshot.AnyRecovery)return false;
        if(Recovery(operation)&&snapshot.WaistBusy)return false;
        // The landing corridor may share time with a disjoint bow launch, but
        // lifts 3/4 and both waist catapults stay clear for the whole arrested
        // recovery operation, including the elevator-owned return after RP1
        // hands off. No new waist departure may enter that landing reservation.
        // Their existing committed movements always finish; only new admission
        // waits. Fixed-wing returns use the two bow lifts, not a rear lift.
        if(ArrestedRecovery(operation))return operation.ToIndex<=2&&!snapshot.RearBusy;
        if(snapshot.FixedRecovery&&RearOperation(operation))return false;
        if(snapshot.FixedRecovery&&snapshot.RearBusy&&operation.FromKind==0&&operation.ToIndex<=2)return false;
        return true;
    }
    static int VerticalRank(int point)=>point==7?0:point==5?1:point==6?2:10+point;
    static RouteTrafficOperation Find(int fk,int f,int tk,int t,int cat)=>RouteTrafficData.Operations.FirstOrDefault(p=>p.FromKind==fk&&p.FromIndex==f&&p.ToKind==tk&&p.ToIndex==t&&p.Category==cat);
    static RouteTrafficOperation ById(int id)=>RouteTrafficData.Operations.Single(p=>p.Id==id);
    static bool Allowed(object point,object kind)=>Reflect.Call(point,"IsAllowed",kind) is bool allowed?allowed:throw new InvalidOperationException("Native allowed-type check unavailable");
    static bool Support(object point,object type,string loadout){
        var result=Reflect.Call(point,"CheckSupport",Required(type,"_fileName"),Required(type,"_unitRoles"),Flag(type,"_isLarge"),Flag(type,"_isVeryLarge"),loadout);
        if(!(result is bool supported))throw new InvalidOperationException("Native aircraft support check unavailable");return supported;
    }
    static string Loadout(object task,object type,string kind){
        if(kind!="VTOL")return "";
        int index=Convert.ToInt32(Required(task,"_loadoutIndex"));var loadouts=Required(type,"_loadouts") as IList;
        if(loadouts==null||index<0||index>=loadouts.Count)throw new InvalidOperationException("Native VTOL loadout unavailable");return Convert.ToString(Required(loadouts[index],"Name"));
    }
    static Snapshot Read(object deck){
        var snapshot=Contacts(deck);var state=States.GetValue(deck,_=>new State());
        // Native PlaneTakeOff releases its launch-point contacts at OffGround,
        // before its task and lowering JBD finish. Retain only a known committed
        // fixed-wing plan during that actual native state. An unadmitted hold
        // can never manufacture a reservation from an airborne task alone.
        foreach(string listName in new[]{"FlightDeckTasks","_flightDeckTasksToAdd"}){
            var tasks=Required(deck,listName) as IEnumerable;if(tasks==null)throw new InvalidOperationException("Native flight tasks unavailable");
            foreach(var task in tasks){
                var vehicle=Required(task,"Vehicle");if(!Live(vehicle))continue;
                if(!snapshot.Contacts.TryGetValue(vehicle,out var contact)){
                    if(!state.Plans.TryGetValue(vehicle,out int committed))continue;
                    var plan=ById(committed);if(plan.FromKind!=0||plan.Category!=0)continue;
                    string phase=Convert.ToString(Required(Required(task,"_stateMachine"),"CurrentStateName"));
                    if(phase!="PlaneTakeOff"&&phase!="STOLTakeOff")continue;
                    contact=new Contact{L=plan.ToIndex};snapshot.Contacts.Add(vehicle,contact);
                }
                Merge(ref contact.E,Index(Points(deck,0),Required(task,"_elevator")));
                Merge(ref contact.L,Index(Points(deck,1),Required(task,"_launchPoint")));
                Merge(ref contact.R,Index(Points(deck,2),Required(task,"_recoveryPoint")));
            }
        }
        foreach(var vehicle in state.Plans.Keys.ToArray())if(!snapshot.Contacts.ContainsKey(vehicle))state.Plans.Remove(vehicle);
        foreach(var row in snapshot.Contacts){
            var contact=row.Value;ulong mask=0;
            if(state.Plans.TryGetValue(row.Key,out int id)){
                var plan=ById(id);
                if(contact.L>0&&(plan.FromKind!=0||plan.ToIndex!=contact.L))throw new InvalidOperationException("Native launch left its pinned route");
                if(contact.R>0&&(plan.FromKind!=1||plan.FromIndex!=contact.R))throw new InvalidOperationException("Native recovery left its reserved route");mask=1UL<<id;
            }else foreach(var operation in RouteTrafficData.Operations){
                // Restored/native-only tasks conservatively cover every route
                // matching their known endpoints until an exact plan is known.
                if(contact.R>0){if(operation.FromKind!=1||operation.FromIndex!=contact.R||contact.E>0&&operation.ToIndex!=contact.E)continue;}
                else if(contact.L>0){if(operation.FromKind!=0||operation.ToIndex!=contact.L||contact.E>0&&operation.FromIndex!=contact.E)continue;}
                // A restored elevator owner with no endpoint identity may be a
                // launch OR the final lift-owned phase of a return. Preserve
                // both possibilities until a native endpoint identifies it.
                else if(contact.E==0||!(operation.FromKind==0&&operation.FromIndex==contact.E||operation.FromKind==1&&operation.ToIndex==contact.E))continue;
                mask|=1UL<<operation.Id;
            }
            if(mask==0)throw new InvalidOperationException("Unmapped live aircraft deck reservation");snapshot.Mask|=mask;
        }
        // Native point busy flags cover service/point reservations with no
        // aircraft yet. Exact plans retain rear/recovery identity after the
        // initial lift or recovery point hands its owner to the next point.
        foreach(var operation in RouteTrafficData.Operations)if((snapshot.Mask&(1UL<<operation.Id))!=0){
            if(RearOperation(operation))snapshot.RearBusy=true;
            if(ArrestedRecovery(operation))snapshot.FixedRecovery=true;
            if(Recovery(operation))snapshot.AnyRecovery=true;
            if(WaistLaunch(operation))snapshot.WaistBusy=true;
        }
        var elevators=Points(deck,0);var launches=Points(deck,1);var recoveries=Points(deck,2);
        snapshot.RearBusy|=Flag(elevators[2],"IsBusy")||Flag(elevators[3],"IsBusy")||
            Flag(launches[2],"IsBusy")||Flag(launches[3],"IsBusy");
        snapshot.FixedRecovery|=Flag(recoveries[0],"IsBusy");
        snapshot.AnyRecovery|=recoveries.Cast<object>().Any(point=>Flag(point,"IsBusy"));
        snapshot.WaistBusy|=Flag(launches[2],"IsBusy")||Flag(launches[3],"IsBusy");
        return snapshot;
    }
    static Snapshot Contacts(object deck){
        var snapshot=new Snapshot();
        for(int group=0;group<3;group++){
            var points=Points(deck,group);
            for(int i=0;i<points.Count;i++){
                var point=points[i];if(point==null)throw new InvalidOperationException("Native flight point missing");
                var incoming=Required(point,"_incomingObjects") as ICollection;if(incoming==null)throw new InvalidOperationException("Native point incoming list unavailable");
                foreach(var vehicle in incoming)Add(snapshot,vehicle,group,i+1);
                Flag(point,"IsOccupied");Add(snapshot,Required(point,"OccupyingObject"),group,i+1);
            }
        }
        return snapshot;
    }
    static void Add(Snapshot snapshot,object vehicle,int group,int index){
        if(!Live(vehicle))return;
        if(!snapshot.Contacts.TryGetValue(vehicle,out var contact)){contact=new Contact();snapshot.Contacts.Add(vehicle,contact);}
        if(group==0)Merge(ref contact.E,index);else if(group==1)Merge(ref contact.L,index);else Merge(ref contact.R,index);
    }
    static void Merge(ref int current,int next){if(next==0)return;if(current!=0&&current!=next)throw new InvalidOperationException("Aircraft owns incompatible native points");current=next;}
    static IList Points(object deck,int group){var list=Required(deck,Groups[group]) as IList;if(list==null||list.Count!=Counts[group])throw new InvalidOperationException(Groups[group]+" must contain "+Counts[group]+" native points");return list;}
    static int Index(IList list,object value){if(value==null)return 0;for(int i=0;i<list.Count;i++)if(ReferenceEquals(list[i],value))return i+1;return 0;}
    static IList Clone(IList source,IEnumerable<object> values){var clone=Activator.CreateInstance(source.GetType()) as IList;if(clone==null||clone.IsReadOnly||clone.IsFixedSize)throw new InvalidOperationException("Native candidate list is not cloneable");foreach(var value in values)clone.Add(value);return clone;}
    static bool Flag(object owner,string name)=>Required(owner,name) is bool value?value:throw new InvalidOperationException("Native boolean unavailable: "+name);
    static object Required(object owner,string name){
        if(owner==null)throw new InvalidOperationException("Missing owner for "+name);var field=Reflect.Field(owner.GetType(),name);if(field!=null)return field.GetValue(owner);
        const BindingFlags flags=BindingFlags.Instance|BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.DeclaredOnly;
        for(var type=owner.GetType();type!=null;type=type.BaseType){var property=type.GetProperty(name,flags);if(property!=null&&property.CanRead&&property.GetIndexParameters().Length==0)return property.GetValue(owner);}
        throw new MissingMemberException(owner.GetType().FullName,name);
    }
    static bool Live(object vehicle){
        if(vehicle==null)return false;
        for(var type=vehicle.GetType();type!=null;type=type.BaseType){
            if(type.FullName!="UnityEngine.Object")continue;
            var equality=type.GetMethod("op_Equality",BindingFlags.Public|BindingFlags.Static|BindingFlags.DeclaredOnly,null,new[]{type,type},null);
            if(equality==null)throw new MissingMethodException("UnityEngine.Object.op_Equality");if(!(equality.Invoke(null,new[]{vehicle,null}) is bool destroyed))throw new InvalidOperationException("Unity null check unavailable");if(destroyed)return false;break;
        }
        return !Flag(vehicle,"IsDestroyed");
    }
}
}
