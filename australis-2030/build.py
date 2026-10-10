#!/usr/bin/env python3
"""Build the original Australis 2030 geometry and presentation previews.

No files outside this concept folder are changed. This is not a game installer.
"""
from pathlib import Path
import json
import math
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE.parent))
from generate_source_models import Mesh, COLORS, render, validate  # noqa: E402
from rebuild_game_scale import METRES_PER_UNIT  # noqa: E402
from build_3d_viewer import build_viewer  # noqa: E402

COLORS.update({
    "hull": "#778b96", "underwater": "#394954", "deck": "#394953",
    "island": "#9aacb3", "glass": "#1b3c50", "dark": "#253843",
    "white": "#dfebea", "gold": "#d3b269", "laser": "#4f9b9c",
    "edge": "#71848b", "sensor": "#3a6374", "hatch": "#536b75",
})

DECK = [
    (-32, -185), (27, -185), (41, -169), (49, -138),
    (50, -76), (52, -33), (52, 72), (49, 125),
    (40, 163), (15, 185), (-15, 185), (-39, 161),
    (-48, 123), (-48, 60), (-52, -41), (-52, -114),
    (-43, -168),
]
MAIN_ISLAND_BASE = [
    (31, -30), (40, -33), (47, -23), (48, 28),
    (39, 39), (31, 32),
]
AFT_ISLAND_BASE = [
    (33, -110), (41, -112), (48, -104), (48, -74),
    (41, -66), (33, -69),
]
ELEVATORS = [(50, -50), (51, 69), (-48, 92), (53, -132)]
LASERS = [(-52, 109), (53, 110), (-58, -125), (55, -160)]
CATAPULTS = [((-15, 59), (-15, 157)), ((8, 55), (8, 161)),
             ((23, 52), (28, 144))]
VERTICAL_SPOTS = [(0, -168), (16, -143), (0, -118), (16, -93)]
VERTICAL_SPOT_RADIUS = 10.5
PAD_MARK_ANGLE_DEG = -12
DECK_UNDERSIDE_Y = 20.3
DECK_SURFACE_Y = 22.0


def loft(mesh, name, rings, material):
    """Join equal sized polygon rings into one closed hard-edged component."""
    n = len(rings[0])
    assert n >= 3 and all(len(r) == n for r in rings)
    verts = [p for ring in rings for p in ring]
    faces = [list(reversed(range(n))), list(range((len(rings)-1)*n, len(rings)*n))]
    for layer in range(len(rings)-1):
        a, b = layer*n, (layer+1)*n
        faces += [[a+i, a+(i+1)%n, b+(i+1)%n, b+i] for i in range(n)]
    mesh.add(name, verts, faces, material)


def polygon_at_y(outline, y):
    return [(x, y, z) for x, z in outline]


def scaled_polygon(points, cx, cz, fx, fz):
    return [(cx+(x-cx)*fx, cz+(z-cz)*fz) for x, z in points]


def pad_mark_point(x, z, offset_x, offset_z):
    angle = math.radians(PAD_MARK_ANGLE_DEG)
    return (x+offset_x*math.cos(angle)-offset_z*math.sin(angle),
            z+offset_x*math.sin(angle)+offset_z*math.cos(angle))


def inside_deck(x, z):
    inside = False
    for (ax, az), (bx, bz) in zip(DECK, DECK[1:]+DECK[:1]):
        if (az > z) != (bz > z) and x < ax+(bx-ax)*(z-az)/(bz-az):
            inside = not inside
    return inside


def rectangle_distance(x, z, xlo, xhi, zlo, zhi):
    return math.hypot(max(xlo-x, x-xhi, 0), max(zlo-z, z-zhi, 0))


def lateral_gap(left, right, xlo, xhi):
    return max(xlo-right, left-xhi, 0)


def geometry():
    m = Mesh()
    # The first hull ring shares the whole deck underside outline: the hull
    # rises to the flight deck at the bow, stern, and both sides, then narrows
    # through faceted chines towards its waterline and keel.
    chine = scaled_polygon(DECK, 0, 0, .96, .99)
    shoulder = scaled_polygon(DECK, 0, 0, .90, .96)
    waterline = scaled_polygon(DECK, 0, 0, .82, .93)
    keel = scaled_polygon(DECK, 0, 0, .52, .77)
    loft(m, "HardChineHull", [polygon_at_y(DECK, DECK_UNDERSIDE_Y),
                              polygon_at_y(chine, 12),
                              polygon_at_y(shoulder, 4.5),
                              polygon_at_y(waterline, 0)], "hull")
    loft(m, "UnderwaterBody", [polygon_at_y(waterline, 0),
                               polygon_at_y(keel, -8)], "underwater")
    m.prism("FacetedFlightDeck", DECK, DECK_UNDERSIDE_Y, DECK_SURFACE_Y, "deck")
    for i, (a, b) in enumerate(zip(DECK, DECK[1:] + DECK[:1]), 1):
        m.stripe(f"DeckEdge_{i:02d}", a, b, .28, 22.07, "edge")

    # Larger integrated island amidships; the smaller island controls aft aviation.
    lower_top = scaled_polygon(MAIN_ISLAND_BASE, 39, 3, .82, .82)
    loft(m, "MainRakedIsland",
         [polygon_at_y(MAIN_ISLAND_BASE, 22), polygon_at_y(lower_top, 37)], "island")
    bridge_base = [(33, -17), (41, -19), (46, -12),
                   (46, 26), (38, 33), (33, 27)]
    bridge_top = scaled_polygon(bridge_base, 39, 7, .82, .84)
    loft(m, "IntegratedBridge",
         [polygon_at_y(bridge_base, 36.6), polygon_at_y(bridge_top, 44)], "island")
    m.box("BridgeWindowPort", 32.85, 40, 7, .22, 1.7, 30, "glass")
    m.box("BridgeWindowStarboard", 45.55, 40, 7, .22, 1.7, 30, "glass")
    m.box("BridgeWindowForward", 39, 40, 32.2, 9, 1.6, .22, "glass")
    mast0 = [(35, -3), (41, -4), (44, 1), (44, 19),
             (38, 24), (35, 18)]
    mast1 = scaled_polygon(mast0, 39.5, 10, .68, .68)
    loft(m, "EnclosedSensorMast",
         [polygon_at_y(mast0, 43.7), polygon_at_y(mast1, 55)], "island")
    for face, xyz, dims in [
        ("Port", (34.8, 49, 10), (.2, 5.5, 9)),
        ("Starboard", (44.2, 49, 10), (.2, 5.5, 9)),
        ("Fore", (39.5, 49, 22.2), (6, 5.5, .2)),
        ("Aft", (39.5, 49, -3.0), (6, 5.5, .2)),
    ]:
        m.box(f"IntegratedRadar_{face}", *xyz, *dims, "sensor")
    # Two conformal panel faces represent one shipboard ECM installation.
    m.box("ShipboardECM_Module_PortPanel", 35.2, 53.3, 10, .24, 2.1, 5, "dark")
    m.box("ShipboardECM_Module_StarboardPanel", 43.7, 53.3, 10, .24, 2.1, 5, "dark")

    aft_top = scaled_polygon(AFT_ISLAND_BASE, 40.5, -89, .82, .80)
    loft(m, "AftAviationIsland",
         [polygon_at_y(AFT_ISLAND_BASE, 22), polygon_at_y(aft_top, 33.5)], "island")
    aft_bridge = [(35, -104), (41, -105), (46, -98),
                  (46, -78), (40, -72), (35, -76)]
    loft(m, "AftAviationBridge",
         [polygon_at_y(aft_bridge, 33.3),
          polygon_at_y(scaled_polygon(aft_bridge, 40, -88, .8, .82), 39)], "island")
    m.box("AftAviationWindowPort", 34.85, 36.8, -89, .22, 1.55, 24, "glass")
    m.box("AftAviationWindowStarboard", 45.75, 36.8, -88, .22, 1.55, 20, "glass")
    m.box("AftAviationWindowForward", 40, 36.8, -72.2, 8, 1.55, .2, "glass")
    aft_mast = [(37, -95), (42, -96), (44, -91),
                (44, -83), (39, -80), (37, -84)]
    loft(m, "AftEnclosedMast",
         [polygon_at_y(aft_mast, 38.8),
          polygon_at_y(scaled_polygon(aft_mast, 40.5, -88, .70, .70), 44)],
         "island")

    for i, (x, z) in enumerate(ELEVATORS, 1):
        m.box(f"DeckEdgeLift_{i}", x, 22.12, z, 13, .17, 18, "hatch")
        for side in (-1, 1):
            m.stripe(f"LiftEdge_{i}_{side}", (x-6.4, z+side*8.8),
                     (x+6.4, z+side*8.8), .22, 22.25, "white")

    # Two bow tracks and one angled starboard track; routes come later.
    for i, (start, end) in enumerate(CATAPULTS, 1):
        m.stripe(f"CatapultTrack_{i}", start, end, .52, 22.13, "gold")
        m.stripe(f"CatapultDeckGuide_{i}",
                 (start[0]+1.25, start[1]), (end[0]+1.25, end[1]),
                 .16, 22.14, "edge")

    a, b = np.array((-27., -155.)), np.array((-16., 62.))
    for side in (-1, 1):
        v = np.array((side*11.3, 0.))
        m.stripe(f"AngledLandingEdge_{side}", a+v, b+v, .34, 22.15, "white")
    for i in range(13):
        p = a+(b-a)*(i+.10)/13
        q = a+(b-a)*(i+.49)/13
        m.stripe(f"LandingCentreline_{i+1:02d}", p, q, .44, 22.16, "white")
    for i, t in enumerate((.31, .39, .47, .55), 1):
        p = a+(b-a)*t
        m.stripe(f"ArrestingWire_{i}", p+(-11, 0), p+(11, 0),
                 .16, 22.19, "dark")

    # Four staggered aft spots for vertical takeoff/landing or helicopters.
    # These are visual positions, not operational flight-deck routing.
    for i, (x, z) in enumerate(VERTICAL_SPOTS, 1):
        rim = [(x+VERTICAL_SPOT_RADIUS*math.cos(2*math.pi*j/20),
                z+VERTICAL_SPOT_RADIUS*math.sin(2*math.pi*j/20))
               for j in range(20)]
        m.prism(f"AftVTOL_HeloSpot_{i}", rim, 22.01, 22.08, "hatch")
        for side in (-1, 1):
            m.stripe(f"AftSpot_{i}_HStem_{side}",
                     pad_mark_point(x, z, -4.5, side*3.5),
                     pad_mark_point(x, z, 4.5, side*3.5),
                     .48, 22.12, "white")
        m.stripe(f"AftSpot_{i}_HBar",
                 pad_mark_point(x, z, 0, -3.5),
                 pad_mark_point(x, z, 0, 3.5),
                 .48, 22.13, "white")

    # Faceted fairings let the defensive mounts sit outside launch/recovery.
    for i, (x, z) in enumerate(LASERS, 1):
        sx = -1 if x < 0 else 1
        fairing = [(x-sx*5, z-7), (x+sx*2, z-7),
                   (x+sx*6, z-3), (x+sx*6, z+3),
                   (x+sx*2, z+7), (x-sx*5, z+7)]
        m.prism(f"OutboardFairing_{i}", fairing, 17.8, 21.5, "hull")
        base = [(x-3, z-3.5), (x+3, z-3.5),
                (x+3.7, z), (x+3, z+3.5),
                (x-3, z+3.5), (x-3.7, z)]
        crown = scaled_polygon(base, x, z, .59, .63)
        loft(m, f"LaserEnclosure_{i}",
             [polygon_at_y(base, 21.5), polygon_at_y(crown, 25.6)], "island")
        m.box(f"LaserAperture_{i}", x, 24.4, z+2.6, 2.1, .65, .18, "laser")

    # Low closed hatches preserve the smooth perimeter. No weapon logic here.
    for i, (x, z) in enumerate(((-48, 31), (49, -91)), 1):
        m.box(f"DefensiveHatch_{i}", x, 22.09, z, 5.6, .14, 7, "hatch")
    m.box("BowSonarFairingStudy", 0, -5.5, 164, 6, 3.5, 8, "dark")
    return m


def plan_preview(path):
    width, height = 1770, 940
    im = Image.new("RGB", (width, height), "#111d27")
    draw = ImageDraw.Draw(im)
    regular = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    f = lambda n, heavy=False: ImageFont.truetype(bold if heavy else regular, n)
    draw.text((82, 54), "AUSTRALIS 2030", font=f(41, True), fill="#edf3f3")
    draw.text((82, 112), "FACETED FLIGHT DECK  /  ORIGINAL RAN CONCEPT  /  BOW TO RIGHT",
              font=f(20), fill="#91c9cd")
    scale = 3.75
    def point(x, z):
        return (int(width/2 + z*scale), int(height/2 - x*scale))
    def shape(outline):
        return [point(x, z) for x, z in outline]
    draw.polygon(shape(DECK), fill="#40535e", outline="#b3c4c4", width=3)
    for a, b in zip(DECK, DECK[1:]+DECK[:1]):
        draw.line([point(*a), point(*b)], fill="#758f95", width=3)
    draw.polygon(shape(MAIN_ISLAND_BASE), fill="#9eafb6", outline="#d8e3e2", width=2)
    draw.polygon(shape([(35, -3), (42, -4), (44, 19), (35, 18)]),
                 fill="#366072")
    draw.polygon(shape(AFT_ISLAND_BASE), fill="#8198a2", outline="#c1d8da", width=2)
    draw.polygon(shape([(37, -95), (44, -91), (44, -83), (37, -84)]),
                 fill="#366072")
    for x, z in ELEVATORS:
        p, q = point(x-6.5, z+9), point(x+6.5, z-9)
        draw.rectangle([min(p[0], q[0]), min(p[1], q[1]),
                        max(p[0], q[0]), max(p[1], q[1])],
                       fill="#718790", outline="#c6d3d1", width=2)
    for x, z in VERTICAL_SPOTS:
        px, py = point(x, z)
        radius = round(VERTICAL_SPOT_RADIUS*scale)
        draw.ellipse([px-radius, py-radius, px+radius, py+radius],
                     fill="#586e77", outline="#d4eeee", width=3)
        for side in (-1, 1):
            draw.line([point(*pad_mark_point(x, z, -4.5, side*3.5)),
                       point(*pad_mark_point(x, z, 4.5, side*3.5))],
                      fill="#edf4f2", width=3)
        draw.line([point(*pad_mark_point(x, z, 0, -3.5)),
                   point(*pad_mark_point(x, z, 0, 3.5))],
                  fill="#edf4f2", width=3)
    for (a, b) in CATAPULTS:
        draw.line([point(*a), point(*b)], fill="#d8b66e", width=4)
    a, b = np.array((-27., -155.)), np.array((-16., 62.))
    for side in (-1, 1):
        shift = np.array((side*11.3, 0.))
        draw.line([point(*(a+shift)), point(*(b+shift))],
                  fill="#d4e3e3", width=3)
    for i in range(13):
        draw.line([point(*(a+(b-a)*(i+.1)/13)),
                   point(*(a+(b-a)*(i+.49)/13))], fill="#f2f5f3", width=3)
    for t in (.31, .39, .47, .55):
        p = a+(b-a)*t
        draw.line([point(*(p+(-11, 0))), point(*(p+(11, 0)))],
                  fill="#a3b9c0", width=2)
    for x, z in LASERS:
        px, py = point(x, z)
        draw.regular_polygon((px, py, 10), 6, fill="#62b9b9", outline="#def2ee", width=2)

    # Annotation leaders stay beyond the deck footprint.
    for label, anchor, xy in [
        ("MAIN COMMAND ISLAND", (44, 10), (912, 216)),
        ("AFT AVIATION ISLAND", (42, -88), (590, 207)),
        ("4 OUTBOARD LIFTS", (51, 69), (1250, 207)),
        ("4 CLEAR VTOL / HELO SPOTS", (16, -143), (158, 204)),
        ("3 CATAPULTS", (8, 133), (1378, 655)),
        ("4 LASER ENCLOSURES", (-52, 109), (1266, 757)),
        ("ANGLED RECOVERY", (-27, -100), (155, 718)),
    ]:
        ax, ay = point(*anchor)
        tx, ty = xy
        draw.line([(ax, ay), (tx+8, ty-8)], fill="#607e88", width=2)
        draw.text((tx, ty), label, font=f(18, True), fill="#cadadc")
    draw.text((82, 872), "370 m overall  ·  104 m deck beam  ·  99 aircraft target  ·  CVN concept",
              font=f(22), fill="#a1c8ca")
    draw.text((1276, 880), "GEOMETRY STUDY  /  NOT GAMEPLAY", font=f(16), fill="#91a6af")
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path)


def main():
    spec = json.loads((HERE/"spec.json").read_text())
    assert max(z for _, z in DECK)-min(z for _, z in DECK) == spec["length_m"]
    assert max(x for x, _ in DECK)-min(x for x, _ in DECK) == spec["flight_deck_beam_m"]
    assert len(CATAPULTS) == spec["deck"]["catapult_tracks"]
    assert len(VERTICAL_SPOTS) == spec["deck"]["aft_vertical_operation_spots"]
    assert spec["islands"]["count"] == 2
    assert PAD_MARK_ANGLE_DEG == spec["deck"]["aft_h_mark_angle_degrees"]
    # Check pad footprints and clear longitudinal departure corridors.
    lane_a = np.array((-27., -155.))
    lane_b = np.array((-16., 62.))
    line = lane_b-lane_a
    min_island_gap = min_lift_gap = min_cat_clearance = float("inf")
    min_spot_edge_gap = min(
        math.dist(a, b)-2*VERTICAL_SPOT_RADIUS
        for i, a in enumerate(VERTICAL_SPOTS)
        for b in VERTICAL_SPOTS[i+1:]
    )
    assert min_spot_edge_gap >= 5
    for x, z in VERTICAL_SPOTS:
        for t in range(36):
            theta = 2*math.pi*t/36
            assert inside_deck(x+VERTICAL_SPOT_RADIUS*math.cos(theta),
                               z+VERTICAL_SPOT_RADIUS*math.sin(theta))
        p = np.array((x, z))
        t = min(1., max(0., float(np.dot(p-lane_a, line)/np.dot(line, line))))
        assert np.linalg.norm(p-(lane_a+t*line)) > VERTICAL_SPOT_RADIUS+11.3+1
        for lift_x, lift_z in ELEVATORS:
            assert rectangle_distance(x, z, lift_x-6.5, lift_x+6.5,
                                      lift_z-9, lift_z+9) > VERTICAL_SPOT_RADIUS+1
            gap = lateral_gap(x-VERTICAL_SPOT_RADIUS, x+VERTICAL_SPOT_RADIUS,
                              lift_x-6.5, lift_x+6.5)
            min_lift_gap = min(min_lift_gap, gap)
            assert gap >= 8
        for island in (MAIN_ISLAND_BASE, AFT_ISLAND_BASE):
            xmin, xmax = min(px for px, _ in island), max(px for px, _ in island)
            zmin, zmax = min(pz for _, pz in island), max(pz for _, pz in island)
            assert rectangle_distance(x, z, xmin, xmax, zmin, zmax) > VERTICAL_SPOT_RADIUS+1
            gap = lateral_gap(x-VERTICAL_SPOT_RADIUS, x+VERTICAL_SPOT_RADIUS,
                              xmin, xmax)
            min_island_gap = min(min_island_gap, gap)
            assert gap >= 4
    # The launch line and up to 60 m of forward rollout within the ship's
    # length keep a 12 m plan-view corridor clear of island/lift footprints.
    obstacles = [(min(x for x, _ in island), max(x for x, _ in island),
                  min(z for _, z in island), max(z for _, z in island))
                 for island in (MAIN_ISLAND_BASE, AFT_ISLAND_BASE)]
    obstacles += [(x-6.5, x+6.5, z-9, z+9) for x, z in ELEVATORS]
    for (sx, sz), (ex, ez) in CATAPULTS:
        for z in np.linspace(sz, min(ez+60, 185), 80):
            x = sx+(ex-sx)*(z-sz)/(ez-sz)
            nearest = min(rectangle_distance(x, z, *bounds)
                          for bounds in obstacles)
            min_cat_clearance = min(min_cat_clearance, nearest)
            assert nearest >= 12
    mesh = geometry()
    parts = {name: vertices for name, vertices, _, _ in mesh.parts}
    n = len(DECK)
    assert np.array_equal(parts["HardChineHull"][:n],
                          parts["FacetedFlightDeck"][:n])
    assert np.array_equal(parts["HardChineHull"][-n:],
                          parts["UnderwaterBody"][:n])
    summary = validate({"id": spec["id"], "aircraft_capacity": 99,
                        "air_group": [{"role": "Capacity placeholder", "count": 99}],
                        "offensive_ecm_modules": 1}, mesh)
    summary.update(catapult_tracks=len(CATAPULTS),
                   aft_vertical_operation_spots=len(VERTICAL_SPOTS),
                   deck_edge_lifts=len(ELEVATORS),
                   islands=2, aft_h_mark_angle_degrees=PAD_MARK_ANGLE_DEG,
                   aft_spot_clearance_geometry_checked=True,
                   pad_longitudinal_corridors_clear=True,
                   catapult_launch_corridors_clear=True,
                   minimum_spot_edge_spacing_m=round(min_spot_edge_gap, 2),
                   minimum_pad_to_island_lateral_gap_m=round(min_island_gap, 2),
                   minimum_pad_to_lift_lateral_gap_m=round(min_lift_gap, 2),
                   minimum_catapult_to_obstruction_plan_gap_m=round(min_cat_clearance, 2),
                   hull_deck_perimeter_mates=True)
    source = HERE/"model/source/ran_cvn_australis_2030.obj"
    game = HERE/"model/game-scale/ran_cvn_australis_2030.obj"
    mesh.save(source)
    mesh.save(game, scale=1/METRES_PER_UNIT)
    game.write_text(game.read_text().replace(
        "# RAN Carrier Restart: original model study; coordinates in metres",
        "# Approximate Sea Power scale; origin, deck routing and collision untested", 1))
    (HERE/"previews").mkdir(exist_ok=True)
    render({"name": spec["name"], "aircraft_capacity": 99,
            "propulsion": "Nuclear concept", "length_m": 370,
            "deck_width_m": 104}, mesh,
           HERE/"previews/australis_2030_perspective.png")
    plan_preview(HERE/"previews/australis_2030_deck_plan.png")
    (HERE/"model/validation.json").write_text(
        json.dumps(summary, indent=2)+"\n")
    build_viewer(mesh, COLORS, HERE/"viewer/australis_2030_3d.html")
    print(f"[OK] {summary['parts']} closed components; {summary['triangles']} triangles")
    print("[OK] Original metre OBJ, approximate game-scale OBJ, two PNGs, and 3D viewer")
    print("[STATUS] Design model only; Sea Power integration has not been tested")


if __name__ == "__main__":
    main()
