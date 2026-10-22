# Australis 2030 — CATOBAR size, crew and combat fit

These are Australis concept targets. Geometry and configuration are built;
the new flight and combat fit still needs game testing.

## Size and people

| Item | Target |
|---|---:|
| Overall length / main flight-deck width | 370 m / 82 m |
| Maximum width including lifts | 109 m |
| Waterline beam / draft | approximately 41 m / 11.5 m |
| Full-load mass budget and native displacement | 112,000 metric tonnes |
| Simplified hull-volume displacement estimate | approximately 112,402 tonnes |
| Ship's company / air wing / staff | 2,850 / 2,250 / 200 |
| Total embarked / berths | 5,300 / 5,800 |
| Aircraft target | 99 |
| Hangar envelope | 245 × 30 × 8 m; 7,350 m² |
| Proposed hangar / deck aircraft allocation | 36 / 63; parking layout unverified |
| Lifts | Four; 22 × 26 m; bow-facing parking |

The [U.S. Navy Ford reference](https://www.history.navy.mil/content/dam/nhhc/news-and-events/multimedia%20gallery/New%20Infographics/Ford%20Media%20Kit-2.pdf)
lists 1,092 feet, 4,539 people including air wing/staff and 75+ aircraft.
Australis is longer and has a larger aircraft target. Its 5,300-person estimate
allows for aviation maintenance, damage control, nuclear specialists,
additional weapons and five steam launch lanes. Automation does not remove
those functions. These crew numbers are project estimates, not Ford figures.

Dimensions were not multiplied by headcount. Hull volume constrains the mass
budget; accommodation, workshops and aviation spaces constrain arrangements.
This remains a space/weight study, not a detailed general arrangement or a
stability calculation. The 99-plane allocation needs a folded-aircraft study.

| Concept mass allocation | Metric tonnes |
|---|---:|
| Structure | 42,000 |
| Machinery | 12,500 |
| Ship and aviation outfit | 15,000 |
| Combat equipment and electronics | 5,000 |
| Aviation fuel | 9,000 |
| Aircraft and wing equipment | 6,500 |
| Ordnance and stores | 5,500 |
| Water and fluids | 4,500 |
| Personnel, effects and provisions | 2,500 |
| Design allowance | 9,500 |
| **Total** | **112,000** |

These allocations are proposed, not measured lightship weights. Unspent
design allowance must eventually become equipment, ballast or revised
load/draft figures. Hull-volume and budget figures agree within one percent;
that checks approximate scale only.

Hotel-service allowances are 795 m³/day fresh water at 150 litres/person,
three 450 m³/day watermakers (900 m³/day with one unavailable), 15,900 meals/day
and 60 days of provisions. The figures live in `combat-fit.json`; no invented
crew or water-production keys are added to the vessel INI.

## Five steam CATOBAR lanes

| Catapult | Transverse position | Stroke | Aircraft test scope |
|---|---:|---:|---|
| 1, outboard | 28 m port | 95 m | Stock A-7E only pending other footprint checks |
| 2, middle bank | 14 m port | 95 m | Carrier-capable aircraft; large reference envelope checked |
| 3, middle bank | Centreline | 95 m | Carrier-capable aircraft; large reference envelope checked |
| 4, middle bank | 14 m starboard | 95 m | Carrier-capable aircraft; large reference envelope checked |
| 5, outboard | 28 m starboard | 95 m | Stock A-7E only pending other footprint checks |

The bow deck is broader while the immersed bow retains a fine stem. The
starboard forward lift moves from z=69 m to z=54 m to clear the launch/taxi
area. The port lift stays abreast of the main island; four helicopter/VTOL
spots remain aft.

Adjacent lanes interlock: 1↔2, 2↔3, 3↔4 and 4↔5. Alternate sets 1/3/5 or 2/4
can prepare independently. Five installed catapults do not authorize five
simultaneous departures. Outboard taxi approaches join 10 m behind the launch
point; middle approaches join 20 m behind. Actual timing depends on the shared
one-second minimum, preparation, occupancy and ship course.

Recovery uses the angled deck and arresting cables, with the hook on the
aircraft. The prototype blocks launches during recovery. Sea Power does not
model our steam plant: accumulator volume, steam demand, recharge and deck
cycle remain studies. No unverified steam-particle prefab is enabled.
Ford uses [EMALS](https://www.navair.navy.mil/product/Electromagnetic-Aircraft-Launch-System-EMALS);
Australis retains steam CATOBAR as requested.

## Equipment targets and current game representation

Stock proxies retain their stock guidance, range and performance. Modern
names describe desired equipment, not performance silently assigned to it.

| Equipment target | Positions | Current native representation |
|---|---:|---|
| Mk57-style peripheral VLS | 80 cells, four banks | Mk41; 64 stock RIM-66E SM-2 and 16 RGM-109C Tomahawks total |
| ESSM self-defence | Two eight-round mounts | Mk29; 16 stock RIM-7M Sea Sparrows total |
| RIM-116 RAM-form launchers | Two 21-position mounts | Original launcher; 42 stock RIM-7Ms total; SARH, **not RAM guidance** |
| Phalanx | Three | Stock Mk15 Block 1; 12,000 shared rounds |
| Mk46-style 30 mm remote guns | Two | Original 200-round/min adapter; stock British 30 mm ammunition; 2,000 shared rounds |
| EASR/SPY-6-style search | Main-island panel fit | Stock SPY-1A search proxy |
| SPY-3-style multifunction faces | Conformal island panels | Original geometry; stock SPG-62/Mk95 fire-control proxies |
| Surface search / approach control | Island-mounted | Stock SPS-67 / SPN-43 |
| SLQ-32/SEWIP-style passive warning | Main island | Stock AN/SLQ-32 ESM |
| Defensive EW | Main island | Stock AN/SLQ-32 jammer |
| Offensive EW | One logical installation | Original game-balance values: 250 km, 30 kW, gain 12, 60° cone; **not measured SEWIP specifications** |
| Mk36 SRBOC | Eight | Stock chaff system and late ship chaff |
| Nulka active decoy | Four | Original visible launchers; hovering active-decoy behaviour unimplemented |
| Nixie torpedo decoy | Two stern attachments | Stock SLQ-25/Nixie countermeasure |
| Retracting defensive lasers | Four hatches | Visual study; operational weapon and game deployment animation unimplemented |

The native fit has 21 weapons, 11 sensors and two towed decoys. Mounts and
hatches are fixed original blockouts in this trial. Port/starboard weapon
sectors face outboard; blast, fragmentation and arc masking are unverified.
Zumwalt's former AGS and an unverified hypersonic installation are not added.

## Reference basis

- [Naval Aviation News, Winter 2022](https://navalaviationnews.navy.mil/Portals/59/Documents/2022_00Winter.pdf): Ford dimensions, crew, air group and ESSM/RAM/CIWS families.
- [Raytheon Zumwalt systems](https://www.rtx.com/raytheon/what-we-do/sea/zumwalt-class-destroyer): peripheral VLS, automation and integrated power concepts.
- [NAVSEA Zumwalt SM-2 trial](https://www.navsea.navy.mil/Media/News/Article/2386284/uss-zumwalt-successfully-completes-first-standard-missile-shot/): Mk57/Standard Missile relationship.
- [Northrop Grumman SEWIP](https://www.northropgrumman.com/what-we-do/mission-solutions/electronic-warfare/surface-electronic-warfare-improvement-program-sewip): electronic-attack role, not our simulation numbers.
- [NAVSEA Australian Nulka collaboration](https://www.navsea.navy.mil/Media/News/Article/1617036/royal-australian-navy-delegation-visits-nswc-dahlgren-division-in-the-wake-of-r/): Australian/U.S. active offboard decoy development.
- The supplied Sea Power copy provides schema/profile references. No stock/Workshop model, texture, DLL or INI bytes are redistributed.
