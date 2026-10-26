# Australis eight-waterjet engineering review

26 October 2026 · v0.8.2 experimental game-build study

## Decision

Proceed as an **experimental Sea Power model**, subject to the geometry and native-system audits. Do not present this as an engineering-validated propulsion design. The eight-unit count is a packaging concept, not a proven requirement. Retain the native 30-knot game target and 280,000 mechanical-horsepower setting; no physical speed improvement is established. Do not increase power merely to make the arithmetic pass.

## Measured and assumed inputs

The screen reads the exported reference envelope `game-mod/RAN-Carrier-Australis-2030/hydrostatics-envelope.obj` and native INI. The reference outer-shell length is 362.60 m, beam 41.00 m, maximum draft 11.50 m and wetted surface 17,062.16 m². Its artificial Y=0 cap is excluded from area. This envelope area omits intake holes, duct wetted area and exposed nozzle appendages; it is a friction reference, not the actual perforated propulsion wetted surface. The native displacement target is 112,000 tonnes. The reference OBJ SHA-256 is `8fe31e61831c30255cbd2cdcd6664baa2c9355a41ca6f8d97618bf3319d33545`; the visible-model SHA-256 is `cea47680a8cec6d40d26b9299c776f6ab728d37c3ec0bbb6b46d18a004fc2fbe`. Rerun this script after every hull change.

280,000 mechanical hp converts to 208.80 MW; equal sharing among eight trains gives 26.10 MW each. This is a planning division, not proof of the electrical plant, transmission, cooling, motor torque or pump capacity. The provisional 2.35 m outlet is a geometric bore, **not** a matched manufacturer's pump size or product designation. Eight 30 MW units would instead total 240 MW and require a separately justified power-plant change; that is not assumed here.

Reference water density is 1,025 kg/m³ and kinematic viscosity is 1.19 × 10⁻⁶ m²/s. Actual seawater temperature and salinity change those properties. The assumed combined shaft-to-uniform-jet energy efficiency is 85%; a 15% extra resistance allowance is imposed. Neither is measured.

## Reproducible resistance and thrust screen

Use `Re = V L / nu`, `Cf = 0.075 / (log10(Re) - 2)²` and `Rf = rho S V² Cf / 2`. The friction correlation is from the ITTC resistance procedure [1]. It does not supply the unknown form, wave, roughness, air, appendage or broad-transom losses.

To expose that uncertainty, calculate **arbitrary** total-resistance multipliers of 1.5, 2, 3 and 4 times smooth-plate friction. These are sensitivity scenarios, **not** confidence limits or an empirical resistance prediction. A real result can lie outside them.

For N equal outlets of area A, use uniform far-upstream velocity V and jet velocity Vj: `T = rho N A Vj (Vj - V)`; `Q_each = A Vj`; `Pshaft = rho N Q_each (Vj² - V²) / (2 eta)`. Solve for Vj. These are simplified momentum/kinetic-energy equations; ITTC's actual waterjet performance procedure requires measured/derived flow, pressure, velocity distributions, running attitude and hull interaction [2]. That full procedure has not been performed.

Required **total shaft power**, including the assumed service resistance allowance:

| Speed | Smooth friction | 1.5 × friction | 2 × friction | 3 × friction | 4 × friction |
|---:|---:|---:|---:|---:|---:|
| 10 kn | 0.34 MN | 4.3 MW | 5.9 MW | 9.5 MW | 13.4 MW |
| 15 kn | 0.72 MN | 13.6 MW | 18.9 MW | 30.3 MW | 42.7 MW |
| 20 kn | 1.24 MN | 31.0 MW | 43.0 MW | 69.0 MW | 97.2 MW |
| 25 kn | 1.88 MN | 58.8 MW | 81.6 MW | 130.8 MW | 184.1 MW |
| 28 kn | 2.33 MN | 81.4 MW | 113.0 MW | 181.0 MW | 254.7 MW |
| 30 kn | 2.65 MN | 99.3 MW | 137.7 MW | 220.6 MW | 310.3 MW |

At 30 knots, the Froude number is 0.259. At all nominal power, the simplified model supplies 8.74 MN and balances a calm-water total/friction multiplier of about 2.86 after the allowance. This is **conditional arithmetic**, not a pass threshold for the real ship. Unknown real resistance and inlet/pump losses can move the outcome to either side of available power.

Efficiency sensitivity at that speed, keeping nominal power fixed:

| Assumed shaft-to-jet energy efficiency | Full-power idealised thrust | Equivalent total / friction ratio, including allowance |
|---:|---:|---:|
| 70% | 7.40 MN | 2.42 |
| 80% | 8.30 MN | 2.72 |
| 85% | 8.74 MN | 2.86 |
| 90% | 9.17 MN | 3.01 |

## Intake, stern and machinery implications

Full-power flow in the simplified 30-knot case is about 109.2 m³/s per jet (874 m³/s combined). Merely dividing by an assumed 10–14 m/s mean intake velocity gives about 7.8–10.9 m² of clear flow section per jet. This is a **continuity illustration**, not an intake design limit. A flat opening's footprint is not its normal flow section. Rounded lips, duct turning, boundary-layer ingestion, uneven distribution, grilles and hull suction change performance. A dark oval painted on the hull is not an open duct.

The broad stern must provide real side-by-side duct routes, supporting webs, pump/motor foundations, thrust bearings, seals, maintenance access and isolation from accommodation/hangar/aviation stores. Visible nozzle spacing can establish an initial envelope only. A simplified in-game collider can bridge visible openings; it must not be described as a fluid mesh.

Both submerged nozzle and intake openings need adequate immersion through trim, pitch and roll; calm-water immersion alone does not rule out ventilation or cavitation. All eight intakes can share a disturbed boundary layer, so counting eight units does not establish damage independence. Independent power feeds, controls, compartments and isolation arrangements need their own design.

For the four fixed boosters, low-speed and reverse handling is not equivalent to eight fully steerable/reversible jets. Outer steering/bucket loads, reverse-jet reingestion and differential-thrust control need manoeuvring studies. Running fewer jets does not automatically save energy: inactive inlet drag, windmilling, closures, transient pump behaviour and the active pump maps matter. No harbour bollard-pull or one-side-failed control claim is made.

## Hydrostatics and stability implications

The exported wet boundary is closed and consistently oriented. Its integrated net geometric displacement is **112,000.07 t**, after **900.40 m³** of connected flooded ducts are deducted from the gross envelope. The hull was reshaped to compensate for that deduction at the design waterline. Appendage displacement, shell thickness, real equipment mass and loaded draft remain outside this result.

The assumed CG is X=0, Y=+7 m and Z=-11.259 m; its longitudinal position was moved aft to the new wet-boundary LCB. Conditional initial transverse GM is **4.361 m** for that assumption. This is not a detailed weight survey or full stability result.

The native geometry audit independently samples all eight real bottom mouths and eight transom openings, checks rotor/bore fit and native 8-propulsion/4-steering bindings, checks the convex collider budget, and screens nozzle spacing and existing internal reservations. No actual motor/service-space design or hydraulic seal approval follows from these checks.


Full loading cases, GZ curves, downflooding, damage stability, replacement machinery weights, structural strength and rough-sea operation remain unresolved. Positive initial GM alone does not establish any of these.

## External evidence and scope

Wärtsilä publishes waterjet selection by both input power and vessel speed, offers customised inlet arrangements and lists large modular units [3]. Its published portfolio reaches approximately 33 MW per unit [4]. Those facts make a multi-unit study reasonable; they do **not** validate this 112,000-tonne installation or approve the conceptual exit bore. No vendor selection, pump curve, cavitation test or carrier-scale case is supplied.

## Build gate and trial sequence

Pass the exported mesh symmetry/manifold checks, actual duct/nozzle fit checks, displacement/CG assumptions audit, native mount/collider bindings, unchanged aviation-layout checks and transactional installer tests. A machine check can establish geometry and configuration integrity; it cannot establish thrust or seaworthiness.

Then test a fresh carrier in a new mission: observe static waterline/trim, ahead and astern, turning both directions at low and cruising speeds, one-side damage, fresh aircraft launches/recoveries and night appearance. Record exceptions and game version. These trials verify the **game implementation only**. For rollback, use the installer's recorded backup/restore path or reinstall v0.7.0, then restart with a new mission; old saved units can retain state.

Before real design acceptance, obtain resistance and self-propulsion testing/validated CFD, manufacturer pump and inlet matching with cavitation margin, a complete weight-centre model, full intact/damage stability and structures/machinery/controls reviews. The current result supports an experimental game build, not manufacture.

## Sources

1. [ITTC 7.5-02-02-01 Resistance Test, 2021 revision 05](https://www.ittc.info/media/11780/75-02-02-01.pdf) — ITTC-1957 friction correlation and resistance definitions only; no towing test performed.

2. [ITTC 7.5-02-05-03.1 Waterjet Propulsive Performance Prediction, 2011 revision 02](https://www.ittc.info/media/8067/75-02-05-031.pdf) — Momentum/energy-flux framework and need for propulsion tests; this simplified screen is not the full ITTC procedure.

3. [Wartsila Modular Waterjets, accessed 26 October 2026](https://www.wartsila.com/marine/products/propulsors-and-gears/waterjets/wartsila-modular-waterjets) — Selection depends on shaft power AND speed; catalogue flange dimensions are not outlet bores.

4. [Wartsila waterjets speed towards new innovations, 7 March 2019](https://www.wartsila.com/insights/article/wartsila-waterjets-speed-towards-new-innovations) — Published portfolio approximately 500 to 33,000kW; no actual product matched to this carrier.

