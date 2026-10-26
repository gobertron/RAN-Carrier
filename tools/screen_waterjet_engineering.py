#!/usr/bin/env python3
"""Reproducible early waterjet sizing sensitivity; never a performance validation.

Reads the exported hull rather than a rendered concept. Requires NumPy only.
No wave-resistance regression, CFD or empirical jet performance map is fitted.
"""
from pathlib import Path
import argparse, configparser, hashlib, json, math
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'game-mod/RAN-Carrier-Australis-2030'
RHO = 1025.0
NU = 1.19e-6  # assumed reference seawater kinematic viscosity, m2/s
G = 9.80665
KNOT = 1852 / 3600
HP_W = 745.6998715822702  # mechanical horsepower
UNIT = 217 / 3.161967
SOURCES = [
    {'title': 'ITTC 7.5-02-02-01 Resistance Test, 2021 revision 05',
     'url': 'https://www.ittc.info/media/11780/75-02-02-01.pdf',
     'use': 'ITTC-1957 friction correlation and resistance definitions only; no towing test performed.'},
    {'title': 'ITTC 7.5-02-05-03.1 Waterjet Propulsive Performance Prediction, 2011 revision 02',
     'url': 'https://www.ittc.info/media/8067/75-02-05-031.pdf',
     'use': 'Momentum/energy-flux framework and need for propulsion tests; this simplified screen is not the full ITTC procedure.'},
    {'title': 'Wartsila Modular Waterjets, accessed 26 October 2026',
     'url': 'https://www.wartsila.com/marine/products/propulsors-and-gears/waterjets/wartsila-modular-waterjets',
     'use': 'Selection depends on shaft power AND speed; catalogue flange dimensions are not outlet bores.'},
    {'title': 'Wartsila waterjets speed towards new innovations, 7 March 2019',
     'url': 'https://www.wartsila.com/insights/article/wartsila-waterjets-speed-towards-new-innovations',
     'use': 'Published portfolio approximately 500 to 33,000kW; no actual product matched to this carrier.'},
]


def read_hull(obj, group='UnderwaterHull'):
    vertices, faces, active = [], [], False
    for line in obj.read_text().splitlines():
        if line.startswith('o '):
            active = line[2:] == group
        elif line.startswith('v '):
            vertices.append([float(x) * UNIT for x in line.split()[1:]])
        elif line.startswith('f ') and active:
            ids = [int(x.split('/')[0]) - 1 for x in line.split()[1:]]
            faces.extend([ids[0], ids[i], ids[i+1]] for i in range(1, len(ids)-1))
    v, f = np.asarray(vertices), np.asarray(faces)
    assert len(f), f'Missing exported {group} group'
    triangles = v[f]
    below = np.any(triangles[:, :, 1] < -1e-4, axis=1)
    # Exclude artificial closure at Y=0. Retain submerged transom/bottom/sides.
    wet = triangles[below]
    area = np.linalg.norm(np.cross(wet[:, 1]-wet[:, 0], wet[:, 2]-wet[:, 0]), axis=1).sum()/2
    used = v[np.unique(f)]
    return float(area), float(np.ptp(used[:, 2])), float(np.ptp(used[:, 0])), float(-used[:, 1].min())


def required_power(v, thrust, count, bore, hydraulic_efficiency):
    """Uniform far-inlet/outlet velocities; matched ambient exit pressure.

    T=rho*N*A*Vj*(Vj-V), Pshaft=rho*N*A*Vj*(Vj**2-V**2)/(2*eta).
    Ignores hull interaction, pressure correction and nonuniform inlet wake.
    """
    area = math.pi*bore*bore/4
    jet = (v + math.sqrt(v*v + 4*thrust/(RHO*count*area)))/2
    flow = area*jet
    shaft = .5*RHO*count*flow*(jet*jet-v*v)/hydraulic_efficiency
    return shaft, jet, flow


def available_thrust(v, shaft_power, count, bore, hydraulic_efficiency):
    area = math.pi*bore*bore/4
    lo, hi = v, max(v+1, 200.)
    for _ in range(90):
        jet = (lo+hi)/2
        p = .5*RHO*count*area*jet*(jet*jet-v*v)/hydraulic_efficiency
        if p < shaft_power: lo = jet
        else: hi = jet
    jet = (lo+hi)/2
    flow = area*jet
    return RHO*count*flow*(jet-v), jet, flow


def screen(package=PACKAGE, bore=2.35, count=8, efficiency=.85,
           service_allowance=.15, intake_open_area=None):
    package=Path(package).resolve()
    visible_obj = package/'ships/ran_cvn_australis_2030/ran_cvn_australis_2030.obj'
    reference_obj=package/'hydrostatics-envelope.obj'
    obj=reference_obj if reference_obj.exists() else visible_obj
    group='HydrostaticEnvelope' if reference_obj.exists() else 'UnderwaterHull'
    conf = configparser.ConfigParser(interpolation=None, strict=False)
    conf.read(package/'vessels/ran_cvn_australis_2030.ini', encoding='utf-8-sig')
    area, length, beam, draft = read_hull(obj,group)
    hp = conf.getfloat('MainPowerSystem', 'HorsePower')
    installed = hp*HP_W
    max_kn = conf.getfloat('Physics', 'MaxForwardVelocity')
    hydro=json.loads((package/'naval-hull-hydrostatics.json').read_text())
    rows = []
    for knots in sorted(set([10., 15., 20., 25., 28., 30., max_kn])):
        v = knots*KNOT
        reynolds = v*length/NU
        cf = .075/(math.log10(reynolds)-2)**2
        friction = .5*RHO*area*v*v*cf
        cases = []
        for mult in (1.5, 2., 3., 4.):
            resistance = friction*mult
            design_thrust = resistance*(1+service_allowance)
            power, jet, flow = required_power(v, design_thrust, count, bore, efficiency)
            cases.append(dict(arbitrary_total_to_friction_ratio=mult,
                calm_water_resistance_MN=resistance/1e6,
                thrust_with_service_allowance_MN=design_thrust/1e6,
                estimated_required_shaft_MW=power/1e6,
                within_installed_power=power<=installed,
                uniform_jet_exit_velocity_m_per_s=jet,
                volumetric_flow_per_jet_m3_per_s=flow))
        thrust, jet, flow = available_thrust(v, installed, count, bore, efficiency)
        rows.append(dict(speed_kn=knots, speed_m_per_s=v,
            froude_number=v/math.sqrt(G*length), reynolds_number=reynolds,
            ittc57_smooth_friction_coefficient=cf,
            smooth_plate_friction_resistance_MN=friction/1e6, cases=cases,
            full_installed_power=dict(idealised_available_thrust_MN=thrust/1e6,
                equivalent_calm_water_resistance_to_friction_ratio=thrust/(1+service_allowance)/friction,
                jet_exit_velocity_m_per_s=jet, flow_per_jet_m3_per_s=flow,
                mean_intake_velocity_m_per_s=flow/intake_open_area if intake_open_area else None,
                notional_capture_area_per_jet_Q_over_V_m2=flow/v)))
    duty = next(r for r in rows if r['speed_kn']==max_kn)
    hydraulic_sensitivity=[]
    for eta in (.70,.80,.85,.90):
        thrust, jet, flow=available_thrust(max_kn*KNOT,installed,count,bore,eta)
        hydraulic_sensitivity.append(dict(assumed_hydraulic_efficiency=eta,
            full_power_idealised_thrust_MN=thrust/1e6,
            equivalent_calm_water_resistance_to_friction_ratio=thrust/(1+service_allowance)/(duty['smooth_plate_friction_resistance_MN']*1e6)))
    return dict(status='PRELIMINARY SENSITIVITY ONLY; NOT ENGINEERING VALIDATION',
        source_obj=str(obj.relative_to(ROOT)), source_obj_sha256=hashlib.sha256(obj.read_bytes()).hexdigest(),
        visible_obj_sha256=hashlib.sha256(visible_obj.read_bytes()).hexdigest(),
        wetted_area_basis='Closed reference envelope, not perforated hull/duct wetted area; reference only.',
        measured_reference_envelope=dict(wetted_area_m2=area,waterline_length_m=length,
            maximum_beam_m=beam,draft_m=draft),
        geometric_audit=hydro,
        model_inputs=dict(displacement_t=conf.getfloat('Physics','Displacement'),
            native_game_speed_target_kn=max_kn,native_horsepower=hp,
            mechanical_horsepower_conversion_W_per_hp=HP_W,
            total_nominal_power_MW=installed/1e6,
            jet_count=count,equal_power_share_MW=installed/count/1e6,
            concept_exit_bore_m=bore,concept_exit_area_each_m2=math.pi*bore*bore/4,
            mean_intake_area_each_m2=intake_open_area,
            assumed_water_density_kg_per_m3=RHO,assumed_kinematic_viscosity_m2_per_s=NU,
            assumed_shaft_to_uniform_jet_energy_efficiency=efficiency,
            assumed_service_resistance_allowance=service_allowance),
        resistance_multiplier_status='Arbitrary 1.5/2/3/4 times smooth-plate friction sensitivity; not measured predictions, confidence bounds or safe limits.',
        speed_cases=rows,hydraulic_efficiency_sensitivity_at_game_speed=hydraulic_sensitivity,
        conclusion='Eight provisional installations can be drawn and power shared among them, but adequacy at the native speed is unresolved: the unknown real resistance and intake/pump performance can cross the installed-power boundary.',
        limitations=[
            'No CFD, tow/self-propulsion experiment, wave-resistance estimate or validated resistance curve.',
            'Uniform upstream flow set equal to ship speed; boundary-layer ingestion, hull interaction, suction pressure and nozzle pressure corrections omitted.',
            '85% shaft-to-jet energy efficiency is an assumed combined pump/duct loss factor, not a measured map; electrical conversion losses are not separately assessed.',
            'No NPSH, cavitation inception, inlet separation, ventilation in waves, debris-bar loss, bucket load, thrust bearing or structural fatigue analysis.',
            'Wetted area is measured from the exported reference outer shell excluding the artificial waterplane cap; apertures/duct free flooding and appendage resistance require separate correction.',
            '112000t displacement and planning CG are game targets; replacement machinery weight, free-flooded duct volume, loading and damaged conditions need a new weight-centre and stability model.',
            'Concept exit bore is not a catalogue product number or matched pump diameter; no supplier rating accepted.',
            'Native game speed/horsepower are scenario settings, not proof of real performance or eight independent physical thrust forces.'
        ],sources=SOURCES)


def markdown(data):
    h=data['measured_reference_envelope'];p=data['model_inputs'];rows=data['speed_cases']
    duty=next(r for r in rows if r['speed_kn']==p['native_game_speed_target_kn'])
    table=['| Speed | Smooth friction | 1.5 × friction | 2 × friction | 3 × friction | 4 × friction |',
           '|---:|---:|---:|---:|---:|---:|']
    for row in rows:
        table.append(f"| {row['speed_kn']:g} kn | {row['smooth_plate_friction_resistance_MN']:.2f} MN | "+' | '.join(f"{c['estimated_required_shaft_MW']:.1f} MW" for c in row['cases'])+' |')
    eff=['| Assumed shaft-to-jet energy efficiency | Full-power idealised thrust | Equivalent total / friction ratio, including allowance |','|---:|---:|---:|']
    for r in data['hydraulic_efficiency_sensitivity_at_game_speed']:
        eff.append(f"| {100*r['assumed_hydraulic_efficiency']:.0f}% | {r['full_power_idealised_thrust_MN']:.2f} MN | {r['equivalent_calm_water_resistance_to_friction_ratio']:.2f} |")
    flow=duty['full_installed_power']['flow_per_jet_m3_per_s']
    hydro=data['geometric_audit']
    hydro_summary=f"""The exported wet boundary is closed and consistently oriented. Its integrated net geometric displacement is **{hydro['wet_boundary_geometric_displacement_t']:,.2f} t**, after **{hydro['flooded_duct_geometric_volume_m3']:,.2f} m³** of connected flooded ducts are deducted from the gross envelope. The hull was reshaped to compensate for that deduction at the design waterline. Appendage displacement, shell thickness, real equipment mass and loaded draft remain outside this result.

The assumed CG is X=0, Y=+7 m and Z={hydro['configured_planning_centre_of_mass_xyz_m'][2]:.3f} m; its longitudinal position was moved aft to the new wet-boundary LCB. Conditional initial transverse GM is **{hydro['wet_boundary_conditional_initial_transverse_gm_m']:.3f} m** for that assumption. This is not a detailed weight survey or full stability result.

The native geometry audit independently samples all eight real bottom mouths and eight transom openings, checks rotor/bore fit and native 8-propulsion/4-steering bindings, checks the convex collider budget, and screens nozzle spacing and existing internal reservations. No actual motor/service-space design or hydraulic seal approval follows from these checks.
"""
    return f'''# Australis eight-waterjet engineering review

26 October 2026 · v0.8.2 experimental game-build study

## Decision

Proceed as an **experimental Sea Power model**, subject to the geometry and native-system audits. Do not present this as an engineering-validated propulsion design. The eight-unit count is a packaging concept, not a proven requirement. Retain the native {p['native_game_speed_target_kn']:g}-knot game target and {p['native_horsepower']:,.0f} mechanical-horsepower setting; no physical speed improvement is established. Do not increase power merely to make the arithmetic pass.

## Measured and assumed inputs

The screen reads the exported reference envelope `{data['source_obj']}` and native INI. The reference outer-shell length is {h['waterline_length_m']:.2f} m, beam {h['maximum_beam_m']:.2f} m, maximum draft {h['draft_m']:.2f} m and wetted surface {h['wetted_area_m2']:,.2f} m². Its artificial Y=0 cap is excluded from area. This envelope area omits intake holes, duct wetted area and exposed nozzle appendages; it is a friction reference, not the actual perforated propulsion wetted surface. The native displacement target is {p['displacement_t']:,.0f} tonnes. The reference OBJ SHA-256 is `{data['source_obj_sha256']}`; the visible-model SHA-256 is `{data['visible_obj_sha256']}`. Rerun this script after every hull change.

{p['native_horsepower']:,.0f} mechanical hp converts to {p['total_nominal_power_MW']:.2f} MW; equal sharing among eight trains gives {p['equal_power_share_MW']:.2f} MW each. This is a planning division, not proof of the electrical plant, transmission, cooling, motor torque or pump capacity. The provisional {p['concept_exit_bore_m']:.2f} m outlet is a geometric bore, **not** a matched manufacturer's pump size or product designation. Eight 30 MW units would instead total 240 MW and require a separately justified power-plant change; that is not assumed here.

Reference water density is 1,025 kg/m³ and kinematic viscosity is 1.19 × 10⁻⁶ m²/s. Actual seawater temperature and salinity change those properties. The assumed combined shaft-to-uniform-jet energy efficiency is {100*p['assumed_shaft_to_uniform_jet_energy_efficiency']:.0f}%; a {100*p['assumed_service_resistance_allowance']:.0f}% extra resistance allowance is imposed. Neither is measured.

## Reproducible resistance and thrust screen

Use `Re = V L / nu`, `Cf = 0.075 / (log10(Re) - 2)²` and `Rf = rho S V² Cf / 2`. The friction correlation is from the ITTC resistance procedure [1]. It does not supply the unknown form, wave, roughness, air, appendage or broad-transom losses.

To expose that uncertainty, calculate **arbitrary** total-resistance multipliers of 1.5, 2, 3 and 4 times smooth-plate friction. These are sensitivity scenarios, **not** confidence limits or an empirical resistance prediction. A real result can lie outside them.

For N equal outlets of area A, use uniform far-upstream velocity V and jet velocity Vj: `T = rho N A Vj (Vj - V)`; `Q_each = A Vj`; `Pshaft = rho N Q_each (Vj² - V²) / (2 eta)`. Solve for Vj. These are simplified momentum/kinetic-energy equations; ITTC's actual waterjet performance procedure requires measured/derived flow, pressure, velocity distributions, running attitude and hull interaction [2]. That full procedure has not been performed.

Required **total shaft power**, including the assumed service resistance allowance:

{chr(10).join(table)}

At {p['native_game_speed_target_kn']:g} knots, the Froude number is {duty['froude_number']:.3f}. At all nominal power, the simplified model supplies {duty['full_installed_power']['idealised_available_thrust_MN']:.2f} MN and balances a calm-water total/friction multiplier of about {duty['full_installed_power']['equivalent_calm_water_resistance_to_friction_ratio']:.2f} after the allowance. This is **conditional arithmetic**, not a pass threshold for the real ship. Unknown real resistance and inlet/pump losses can move the outcome to either side of available power.

Efficiency sensitivity at that speed, keeping nominal power fixed:

{chr(10).join(eff)}

## Intake, stern and machinery implications

Full-power flow in the simplified {p['native_game_speed_target_kn']:g}-knot case is about {flow:.1f} m³/s per jet ({8*flow:.0f} m³/s combined). Merely dividing by an assumed 10–14 m/s mean intake velocity gives about {flow/14:.1f}–{flow/10:.1f} m² of clear flow section per jet. This is a **continuity illustration**, not an intake design limit. A flat opening's footprint is not its normal flow section. Rounded lips, duct turning, boundary-layer ingestion, uneven distribution, grilles and hull suction change performance. A dark oval painted on the hull is not an open duct.

The broad stern must provide real side-by-side duct routes, supporting webs, pump/motor foundations, thrust bearings, seals, maintenance access and isolation from accommodation/hangar/aviation stores. Visible nozzle spacing can establish an initial envelope only. A simplified in-game collider can bridge visible openings; it must not be described as a fluid mesh.

Both submerged nozzle and intake openings need adequate immersion through trim, pitch and roll; calm-water immersion alone does not rule out ventilation or cavitation. All eight intakes can share a disturbed boundary layer, so counting eight units does not establish damage independence. Independent power feeds, controls, compartments and isolation arrangements need their own design.

For the four fixed boosters, low-speed and reverse handling is not equivalent to eight fully steerable/reversible jets. Outer steering/bucket loads, reverse-jet reingestion and differential-thrust control need manoeuvring studies. Running fewer jets does not automatically save energy: inactive inlet drag, windmilling, closures, transient pump behaviour and the active pump maps matter. No harbour bollard-pull or one-side-failed control claim is made.

## Hydrostatics and stability implications

{hydro_summary}

Full loading cases, GZ curves, downflooding, damage stability, replacement machinery weights, structural strength and rough-sea operation remain unresolved. Positive initial GM alone does not establish any of these.

## External evidence and scope

Wärtsilä publishes waterjet selection by both input power and vessel speed, offers customised inlet arrangements and lists large modular units [3]. Its published portfolio reaches approximately 33 MW per unit [4]. Those facts make a multi-unit study reasonable; they do **not** validate this 112,000-tonne installation or approve the conceptual exit bore. No vendor selection, pump curve, cavitation test or carrier-scale case is supplied.

## Build gate and trial sequence

Pass the exported mesh symmetry/manifold checks, actual duct/nozzle fit checks, displacement/CG assumptions audit, native mount/collider bindings, unchanged aviation-layout checks and transactional installer tests. A machine check can establish geometry and configuration integrity; it cannot establish thrust or seaworthiness.

Then test a fresh carrier in a new mission: observe static waterline/trim, ahead and astern, turning both directions at low and cruising speeds, one-side damage, fresh aircraft launches/recoveries and night appearance. Record exceptions and game version. These trials verify the **game implementation only**. For rollback, use the installer's recorded backup/restore path or reinstall v0.7.0, then restart with a new mission; old saved units can retain state.

Before real design acceptance, obtain resistance and self-propulsion testing/validated CFD, manufacturer pump and inlet matching with cavitation margin, a complete weight-centre model, full intact/damage stability and structures/machinery/controls reviews. The current result supports an experimental game build, not manufacture.

## Sources

'''+''.join(f"{i}. [{s['title']}]({s['url']}) — {s['use']}\n\n" for i,s in enumerate(SOURCES,1))


def write_outputs(data,package=PACKAGE):
    """Build-driver API; saves numerical evidence and matching review text."""
    (package/'waterjet-engineering-screen.json').write_text(json.dumps(data,indent=2)+'\n')
    report=markdown(data)
    (ROOT/'WATERJET-ENGINEERING-REVIEW.md').write_text(report)
    (package/'WATERJET-ENGINEERING-REVIEW.md').write_text(report)
    return data


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package',type=Path,default=PACKAGE)
    parser.add_argument('--outlet-diameter',type=float,default=2.35)
    parser.add_argument('--jets',type=int,default=8)
    parser.add_argument('--pump-efficiency',type=float,default=.85)
    parser.add_argument('--service-allowance',type=float,default=.15)
    parser.add_argument('--intake-open-area',type=float)
    parser.add_argument('--json',type=Path,default=PACKAGE/'waterjet-engineering-screen.json')
    parser.add_argument('--report',type=Path,default=ROOT/'WATERJET-ENGINEERING-REVIEW.md')
    args=parser.parse_args()
    assert args.jets>0 and args.outlet_diameter>0 and 0<args.pump_efficiency<=1
    assert args.service_allowance>=0 and (args.intake_open_area is None or args.intake_open_area>0)
    data=screen(args.package,args.outlet_diameter,args.jets,args.pump_efficiency,args.service_allowance,args.intake_open_area)
    args.json.write_text(json.dumps(data,indent=2)+'\n')
    args.report.write_text(markdown(data))
    print('[SCREEN ONLY] Saved waterjet numerical sensitivity; propulsion feasibility remains unvalidated.')
    print(f"[INPUTS] {data['measured_reference_envelope']['wetted_area_m2']:.1f}m² reference wetted area; {data['model_inputs']['total_nominal_power_MW']:.2f}MW nominal; {args.jets} × {args.outlet_diameter:.2f}m concept outlets")


if __name__=='__main__':
    main()
