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
    (-28, -185), (22, -185), (32, -170), (38, -138),
    (40, -76), (41, -33), (42, 72), (40, 125),
    (32, 163), (12, 185), (-12, 185), (-32, 161),
    (-40, 123), (-39, 60), (-46, -41), (-43, -114),
    (-36, -168),
]
MAIN_ISLAND_BASE = [
    (26, -30), (33, -33), (39, -23), (39, 28),
    (33, 39), (26, 32),
]
AFT_ISLAND_BASE = [
    (26, -110), (33, -112), (39, -104), (39, -74),
    (33, -66), (26, -69),
]
ELEVATORS = [(42, -50), (42, 69), (-42, 92), (41, -132)]
LASERS = [(-35, 109), (36, 119), (-40, -60), (31, -157)]
CATAPULTS = [((-13, 59), (-13, 157)), ((6, 55), (6, 161)),
             ((16, 59), (21, 144))]
VERTICAL_SPOTS = [(6, -165), (6, -136), (6, -107), (6, -78)]
LANDING_LANE_A = np.array((-23., -155.))
LANDING_LANE_B = np.array((-15., 62.))
VERTICAL_SPOT_RADIUS = 10.5
PAD_MARK_ANGLE_DEG = -12
DECK_UNDERSIDE_Y = 20.3
DECK_SURFACE_Y = 22.0
WATERLINE_WIDTH_SCALE = .50
DESIGN_DRAFT_M = 11.5


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


def hull_outline(width_scale, length_scale, bow_tip_scale):
    """Keep broad amidships but narrow the immersed forward stem to a point."""
    result = []
    for x, z in DECK:
        forward = max(0., min(1., (z-110.)/75.))
        bow_factor = 1. - (1. - bow_tip_scale)*forward**1.4
        result.append((x*width_scale*bow_factor, z*length_scale))
    return result


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


def geometry(closed_lasers=True):
    m = Mesh()
    # The first hull ring shares the whole deck underside outline: the hull
    # rises to the flight deck at the bow, stern, and both sides, then narrows
    # through faceted chines towards its waterline and keel.
    chine = hull_outline(.74, .99, .40)
    shoulder = hull_outline(.58, .98, .12)
    waterline = hull_outline(WATERLINE_WIDTH_SCALE, .98, .035)
    keel = hull_outline(.31, .88, .02)
    loft(m, "HardChineHull", [polygon_at_y(DECK, DECK_UNDERSIDE_Y),
                              polygon_at_y(chine, 12),
                              polygon_at_y(shoulder, 4.5),
                              polygon_at_y(waterline, 0)], "hull")
    loft(m, "UnderwaterBody", [polygon_at_y(waterline, 0),
                               polygon_at_y(keel, -DESIGN_DRAFT_M)], "underwater")
    m.prism("FacetedFlightDeck", DECK, DECK_UNDERSIDE_Y, DECK_SURFACE_Y, "deck")
    for i, (a, b) in enumerate(zip(DECK, DECK[1:] + DECK[:1]), 1):
        m.stripe(f"DeckEdge_{i:02d}", a, b, .28, 22.07, "edge")

    # Larger integrated island amidships; the smaller island controls aft aviation.
    lower_top = scaled_polygon(MAIN_ISLAND_BASE, 32.5, 3, .82, .82)
    loft(m, "MainRakedIsland",
         [polygon_at_y(MAIN_ISLAND_BASE, 22), polygon_at_y(lower_top, 37)], "island")
    bridge_base = [(28, -17), (34, -19), (38, -12),
                   (38, 26), (32, 33), (28, 27)]
    bridge_top = scaled_polygon(bridge_base, 33, 7, .82, .84)
    loft(m, "IntegratedBridge",
         [polygon_at_y(bridge_base, 36.6), polygon_at_y(bridge_top, 44)], "island")
    m.box("BridgeWindowPort", 28.25, 40, 7, .22, 1.7, 30, "glass")
    m.box("BridgeWindowStarboard", 37.75, 40, 7, .22, 1.7, 30, "glass")
    m.box("BridgeWindowForward", 33, 40, 30, 8, 1.6, .22, "glass")
    mast0 = [(30, -3), (35, -4), (37, 1), (37, 19),
             (33, 24), (30, 18)]
    mast1 = scaled_polygon(mast0, 33.5, 10, .68, .68)
    loft(m, "EnclosedSensorMast",
         [polygon_at_y(mast0, 43.7), polygon_at_y(mast1, 55)], "island")
    # Conformal radar faces sit against the sides of the command island,
    # rather than on exposed rotating spars above its roof.
    for face, xyz, dims in [
        ("Port", (28.22, 40, 8), (.18, 3.8, 8)),
        ("Starboard", (37.78, 40, 8), (.18, 3.8, 8)),
        ("Fore", (33, 40, 30.05), (6, 3.8, .18)),
        ("Aft", (33, 40, -16.95), (6, 3.8, .18)),
    ]:
        m.box(f"IntegratedRadar_{face}", *xyz, *dims, "sensor")
    # Two conformal panel faces represent one shipboard ECM installation.
    m.box("ShipboardECM_Module_PortPanel", 30.2, 51.3, 10, .24, 2.1, 5, "dark")
    m.box("ShipboardECM_Module_StarboardPanel", 36.8, 51.3, 10, .24, 2.1, 5, "dark")

    aft_top = scaled_polygon(AFT_ISLAND_BASE, 32.5, -89, .82, .80)
    loft(m, "AftAviationIsland",
         [polygon_at_y(AFT_ISLAND_BASE, 22), polygon_at_y(aft_top, 33.5)], "island")
    aft_bridge = [(28, -104), (34, -105), (38, -98),
                  (38, -78), (32, -72), (28, -76)]
    loft(m, "AftAviationBridge",
         [polygon_at_y(aft_bridge, 33.3),
          polygon_at_y(scaled_polygon(aft_bridge, 33, -88, .8, .82), 39)], "island")
    m.box("AftAviationWindowPort", 28.2, 36.8, -89, .22, 1.55, 24, "glass")
    m.box("AftAviationWindowStarboard", 37.8, 36.8, -88, .22, 1.55, 20, "glass")
    m.box("AftAviationWindowForward", 33, 36.8, -73.55, 8, 1.55, .2, "glass")
    for face, xyz, dims in [
        ("Port", (28.2, 35, -90), (.18, 2.8, 6)),
        ("Starboard", (37.8, 35, -90), (.18, 2.8, 6)),
        ("Fore", (33, 35, -74), (5.4, 2.8, .18)),
    ]:
        m.box(f"AftSideRadar_{face}", *xyz, *dims, "sensor")
    aft_mast = [(30, -95), (35, -96), (37, -91),
                (37, -83), (33, -80), (30, -84)]
    loft(m, "AftEnclosedMast",
         [polygon_at_y(aft_mast, 38.8),
          polygon_at_y(scaled_polygon(aft_mast, 33.5, -88, .70, .70), 44)],
         "island")

    for i, (x, z) in enumerate(ELEVATORS, 1):
        m.box(f"DeckEdgeLift_{i}", x, 22.12, z, 13, .17, 18, "hatch")
        for side in (-1, 1):
            m.stripe(f"LiftEdge_{i}_{side}", (x-6.4, z+side*8.8),
                     (x+6.4, z+side*8.8), .22, 22.25, "white")

    # Two bow tracks and one angled starboard track; routes come later.
    for i, (start, end) in enumerate(CATAPULTS, 1):
        # A deck-flush blast-deflector panel is marked behind each launch
        # point; actuator volume, exhaust flow and clearances remain unknown.
        sx, sz = start
        m.box(f"CatapultJetBlastDeflector_{i}",
              sx, 22.095, sz-5.0, 7, .14, 4, "hatch")
        m.stripe(f"CatapultJetBlastDeflectorHinge_{i}",
                 (sx-3.5, sz-3), (sx+3.5, sz-3), .13, 22.18, "edge")
        m.stripe(f"CatapultTrack_{i}", start, end, .52, 22.13, "gold")
        m.stripe(f"CatapultDeckGuide_{i}",
                 (start[0]+1.25, start[1]), (end[0]+1.25, end[1]),
                 .16, 22.14, "edge")

    a, b = LANDING_LANE_A, LANDING_LANE_B
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
                 .24, 22.19, "gold")
        for side in (-1, 1):
            m.box(f"ArrestingWireAnchor_{i}_{side}",
                  p[0]+side*11.25, 22.16, p[1], .85, .20, 1.4, "dark")
    m.stripe("LandingThresholdStripe", (-33, -154), (-11, -154), .38, 22.16, "white")

    # Four aligned off-centre aft spots for vertical takeoff or helicopters.
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

    # The base mesh shows shut, flush armoured hatches. A separate geometry
    # layer is drawn when the viewer's conceptual deploy control is activated.
    if closed_lasers:
        for i, (x, z) in enumerate(LASERS, 1):
            m.box(f"LaserHatchClosed_{i}", x, 22.105, z, 5, .12, 5.8, "hatch")
            m.stripe(f"LaserHatchSeam_{i}", (x, z-2.6), (x, z+2.6),
                     .09, 22.18, "edge")
    m.box("BowSonarFairingStudy", 0, -5.5, 164, 6, 3.5, 8, "dark")
    return m


def deployed_lasers():
    """Additional exhibition mesh; deployment is not Sea Power weapon logic."""
    m = Mesh()
    for i, (x, z) in enumerate(LASERS, 1):
        for side in (-1, 1):
            m.box(f"LaserHatchOpen_{i}_{side}", x+side*2.65, 22.19,
                  z, .24, .24, 5.8, "dark")
        m.box(f"LaserHatchOpen_{i}_fore", x, 22.19,
              z+2.96, 5.55, .24, .22, "dark")
        m.box(f"LaserHatchOpen_{i}_aft", x, 22.19,
              z-2.96, 5.55, .24, .22, "dark")
        m.box(f"LaserTurretPedestal_{i}", x, 22.65, z, 3.6, 1.45, 3.8, "hull")
        base = [(x-1.9, z-2), (x+1.9, z-2),
                (x+2.25, z), (x+1.9, z+2),
                (x-1.9, z+2), (x-2.25, z)]
        crown = scaled_polygon(base, x, z, .72, .72)
        loft(m, f"LaserTurretFaceted_{i}",
             [polygon_at_y(base, 22.7), polygon_at_y(crown, 25.4)], "island")
        m.box(f"LaserEmitter_{i}", x, 24.25, z+1.55, 1.5, .65, .15, "laser")
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
    draw.polygon(shape([(30, -3), (35, -4), (37, 19), (30, 18)]),
                 fill="#366072")
    draw.polygon(shape(AFT_ISLAND_BASE), fill="#8198a2", outline="#c1d8da", width=2)
    draw.polygon(shape([(30, -95), (37, -91), (37, -83), (30, -84)]),
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
        sx, sz = a
        draw.polygon(shape([(sx-3.5, sz-7), (sx+3.5, sz-7),
                            (sx+3.5, sz-3), (sx-3.5, sz-3)]),
                     fill="#76909a", outline="#d2dfdf", width=1)
    a, b = LANDING_LANE_A, LANDING_LANE_B
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
                  fill="#d8b66e", width=3)
        for side in (-1, 1):
            px, py = point(*(p+(side*11.25, 0)))
            draw.ellipse((px-3, py-3, px+3, py+3), fill="#11212c")
    draw.line([point(-33, -154), point(-11, -154)], fill="#eef4f3", width=3)
    for x, z in LASERS:
        px, py = point(x, z)
        draw.rectangle((px-10, py-9, px+10, py+9),
                       fill="#526a74", outline="#a3d2ce", width=2)
        draw.line((px-8, py, px+8, py), fill="#243d49", width=2)

    # Annotation leaders stay beyond the deck footprint.
    for label, anchor, xy in [
        ("MAIN COMMAND ISLAND", (35, 10), (912, 216)),
        ("AFT AVIATION ISLAND", (34, -88), (590, 207)),
        ("4 OUTBOARD LIFTS", (51, 69), (1250, 207)),
        ("4 OFFSET VTOL / HELO SPOTS", (6, -136), (158, 204)),
        ("3 CATAPULTS", (8, 133), (1378, 655)),
        ("4 FLUSH LASER HATCHES", (-35, 109), (1266, 757)),
        ("4 ARRESTING WIRES", (-23, -75), (160, 689)),
        ("ANGLED RECOVERY", (-27, -100), (155, 736)),
    ]:
        ax, ay = point(*anchor)
        tx, ty = xy
        draw.line([(ax, ay), (tx+8, ty-8)], fill="#607e88", width=2)
        draw.text((tx, ty), label, font=f(18, True), fill="#cadadc")
    draw.text((82, 872), "370 m overall  ·  88 m deck beam  ·  99 aircraft target  ·  CVN concept",
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
    lane_a, lane_b = LANDING_LANE_A, LANDING_LANE_B
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
    bow_z = max(z for _, z in DECK)
    immersed_bow = [x for x, z in hull_outline(.82, .98, .035)
                    if math.isclose(z, bow_z*.98)]
    assert len(immersed_bow) == 2
    bow_tip_width = abs(immersed_bow[0]-immersed_bow[1])
    assert bow_tip_width < 1.0
    for x, z in LASERS:
        for dx in (-2.8, 2.8):
            for dz in (-3.1, 3.1):
                assert inside_deck(x+dx, z+dz)
    def area(points):
        return abs(sum(x*z2-x2*z for (x, z), (x2, z2)
                       in zip(points, points[1:]+points[:1])))/2
    waterline = hull_outline(WATERLINE_WIDTH_SCALE, .98, .035)
    keel = hull_outline(.31, .88, .02)
    mid_depth = [((x+x2)/2, (z+z2)/2)
                 for (x, z), (x2, z2) in zip(waterline, keel)]
    submerged_volume = DESIGN_DRAFT_M*(area(waterline)+4*area(mid_depth)+area(keel))/6
    waterline_beam = max(x for x, _ in waterline)-min(x for x, _ in waterline)
    waterline_length = max(z for _, z in waterline)-min(z for _, z in waterline)
    block_coefficient = submerged_volume/(waterline_length*waterline_beam*DESIGN_DRAFT_M)
    assert 40 < waterline_beam < 50 and 80000 < submerged_volume*1.025 < 140000
    assert .55 < block_coefficient < .75
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
                   hull_deck_perimeter_mates=True,
                   bow_waterline_tip_width_m=round(bow_tip_width, 2),
                   design_draft_m=DESIGN_DRAFT_M,
                   maximum_waterline_beam_m=round(waterline_beam, 2),
                   waterline_length_m=round(waterline_length, 2),
                   length_to_waterline_beam_ratio=round(370/waterline_beam, 2),
                   approximate_block_coefficient=round(block_coefficient, 3),
                   approximate_submerged_volume_m3=round(submerged_volume),
                   approximate_displacement_tonnes=round(submerged_volume*1.025),
                   flush_laser_hatches=len(LASERS),
                   arresting_wire_indications=4,
                   radar_faces_on_island_sides=True)
    source = HERE/"model/source/ran_cvn_australis_2030.obj"
    game = HERE/"model/game-scale/ran_cvn_australis_2030.obj"
    mesh.save(source)
    mesh.save(game, scale=1/METRES_PER_UNIT)
    # Overlay this separate OBJ on the base mesh in Blender to inspect the
    # raised state; the interactive viewer handles the closed/open switch.
    deployed_lasers().save(HERE/"model/source/ran_cvn_australis_2030_deployed_lasers.obj")
    game.write_text(game.read_text().replace(
        "# RAN Carrier Restart: original model study; coordinates in metres",
        "# Approximate Sea Power scale; origin, deck routing and collision untested", 1))
    (HERE/"previews").mkdir(exist_ok=True)
    render({"name": spec["name"], "aircraft_capacity": 99,
            "propulsion": "Nuclear concept", "length_m": 370,
            "deck_width_m": 88}, mesh,
           HERE/"previews/australis_2030_perspective.png")
    render({"name": "Australis class — bow view", "aircraft_capacity": 99,
            "propulsion": "Nuclear concept", "length_m": 370,
            "deck_width_m": 88}, mesh,
           HERE/"previews/australis_2030_bow.png",
           camera_azimuth_deg=90, camera_elevation_deg=8)
    plan_preview(HERE/"previews/australis_2030_deck_plan.png")
    (HERE/"model/validation.json").write_text(
        json.dumps(summary, indent=2)+"\n")
    build_viewer(mesh, COLORS, HERE/"viewer/australis_2030_3d.html", deployed_lasers())
    print(f"[OK] {summary['parts']} closed components; {summary['triangles']} triangles")
    print("[OK] Original metre OBJ, approximate game-scale OBJ, three PNGs, and 3D viewer")
    print("[STATUS] Design model only; Sea Power integration has not been tested")


if __name__ == "__main__":
    main()
