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
from build_3d_viewer import build_viewer, model_revision  # noqa: E402
from render_current_views import render_current_views  # noqa: E402
from combat_fit import (add_geometry as add_combat_geometry, FIT, VLS_BANKS,
                        SAM_POS, RAM_POS, CIWS_POS, GUN_POS, CHAFF_POS, NULKA_POS,
                        deck_weapon_zones)  # noqa: E402

COLORS.update({
    "hull": "#778b96", "underwater": "#394954", "deck": "#394953",
    "island": "#9aacb3", "glass": "#1b3c50", "dark": "#253843",
    "white": "#dfebea", "gold": "#d3b269", "laser": "#4f9b9c",
    "edge": "#71848b", "sensor": "#3a6374", "hatch": "#536b75",
    "track": "#697b85",
})

# Keep one authoring frame for the detailed fittings, then project every X
# coordinate through the same modest width reduction in mesh and game INI.
DECK_BEAM_M = 82.0
WIDTH_SCALE = DECK_BEAM_M/88.0

DECK = [
    (-28, -185), (22, -185), (32, -170), (38, -138),
    (40, -76), (41, -33), (42, 72), (40, 125),
    (38, 163), (30, 185), (-30, 185), (-38, 161),
    (-40, 123), (-39, 60), (-46, -41), (-43, -114),
    (-36, -168),
]
MAIN_ISLAND_BASE = [
    (26, -30), (33, -33), (39, -23), (39, 28),
    (33, 39), (26, 32),
]
AFT_ISLAND_REFERENCE = [
    (26, -110), (33, -112), (39, -104), (39, -74),
    (33, -66), (26, -69),
]
AFT_ISLAND_SCALE = (.80, .72, .65)
AFT_ISLAND_BASE = [(32.5+(x-32.5)*AFT_ISLAND_SCALE[0],
                    -89+(z+89)*AFT_ISLAND_SCALE[2])
                   for x,z in AFT_ISLAND_REFERENCE]
# Abreast the aft part of the main island, behind the waist launch run.
PORT_LIFT_Z = -32.0
# Actual metre dimensions are independent of the hull's width reduction.
# Fore-and-aft parking accommodates the Tomcat without a wide cross-deck lift.
LIFT_WIDTH_M = 22.0
LIFT_LENGTH_M = 26.0
LIFT_CENTRE_X_M = 43.5
ELEVATORS = [(LIFT_CENTRE_X_M/WIDTH_SCALE, -50),
             (LIFT_CENTRE_X_M/WIDTH_SCALE, 54),
             (-LIFT_CENTRE_X_M/WIDTH_SCALE, PORT_LIFT_Z),
             (LIFT_CENTRE_X_M/WIDTH_SCALE, -132)]
LASERS = [(-35, 109), (34, 158), (-40, -60), (31, -157)]
# Three bow tracks and two port-waist tracks, each with a 95 m stroke.
# Waist departures are angled to port, using the shared recovery-deck area.
BOW_CATAPULT_IDS = (1, 2, 3)
WAIST_CATAPULT_IDS = (4, 5)
WAIST_CATAPULT_HEADING_DEG = -6.0
CATAPULTS = [((x/WIDTH_SCALE, 88), (x/WIDTH_SCALE, 183))
             for x in (-14, 0, 14)] + [
    ((x/WIDTH_SCALE, z),
     ((x+95*math.sin(math.radians(WAIST_CATAPULT_HEADING_DEG)))/WIDTH_SCALE,
      z+95*math.cos(math.radians(WAIST_CATAPULT_HEADING_DEG))))
    for x,z in ((-20.2,-1),(-10,-22))
]
# Bow 1/3 can operate as a pair. Waist launches interlock with all bow
# lanes and with each other because departure/taxi areas are shared.
CATAPULT_INTERLOCKS = {
    1: (2, 4, 5), 2: (1, 3, 4, 5), 3: (2, 4, 5),
    4: (1, 2, 3, 5, 6, 7, 8, 9), 5: (1, 2, 3, 4, 6, 7, 8, 9),
}
# Two pairs ahead of the two islands. All four spots share waist staging
# or launch space for larger aircraft; bow lanes remain available.
VERTICAL_SPOTS = [(x/WIDTH_SCALE,z) for x,z in
                  ((-25,60),(1.5,60),(9.5,-60),(9.5,-31))]
HELO_INTERLOCKS = {i:(4,5) for i in range(6,10)}
HELO_ELEVATORS = (2,2,1,1)
LANDING_HEADING_DEG = -9.0
LANDING_LANE_A = np.array((3./WIDTH_SCALE, -166.))
LANDING_LANE_B = np.array(((3.-186*math.tan(math.radians(9)))/WIDTH_SCALE, 20.))
VERTICAL_SPOT_RADIUS = 10.5
PAD_MARK_ANGLE_DEG = -12
DECK_UNDERSIDE_Y = 20.3
DECK_SURFACE_Y = 22.0
# A two-millimetre plate allowance avoids coplanar faces where a platform
# overlaps the deck edge. It replaces the former 20.5 cm platform step.
LIFT_SURFACE_Y = DECK_SURFACE_Y+.002
HELIPAD_SURFACE_Y = DECK_SURFACE_Y+.002
WATERLINE_WIDTH_SCALE = .50
DESIGN_DRAFT_M = 11.5


def physical_xz(points):
    return [(x*WIDTH_SCALE, z) for x, z in points]


def deck_line(mesh,name,a,b,width,material="white",above=.004,thickness=.002):
    """Closed, millimetre-thick deck markings, clear of coplanar z-fighting."""
    direction=np.array(b)-np.array(a)
    length=np.linalg.norm(direction)
    if length==0: raise ValueError(f"Zero-length deck marking: {name}")
    offset=np.array((-direction[1],direction[0]))*width/(2*length)
    mesh.prism(name,[np.array(a)+offset,np.array(b)+offset,
                     np.array(b)-offset,np.array(a)-offset],
               DECK_SURFACE_Y+above,DECK_SURFACE_Y+above+thickness,material)


def catapult_point(route, along, across=0):
    """Authoring-frame point with offsets measured along the physical track."""
    start, end = np.array(physical_xz(route))
    direction = (end-start)/np.linalg.norm(end-start)
    lateral = np.array((direction[1], -direction[0]))
    x, z = start+along*direction+across*lateral
    return (x/WIDTH_SCALE, z)


def landing_point(fraction, across=0):
    a,b = np.array(physical_xz((LANDING_LANE_A,LANDING_LANE_B)))
    direction = (b-a)/np.linalg.norm(b-a)
    lateral = np.array((direction[1],-direction[0]))
    x,z = a+(b-a)*fraction+across*lateral
    return (x/WIDTH_SCALE,z)


def catapult_deflector(route):
    return [catapult_point(route, along, across)
            for along, across in ((-20,-3.5),(-20,3.5),(-16,3.5),(-16,-3.5))]


def catapult_guide_end(route, across):
    """Stop painted guide lines inboard of the deck edge."""
    length = 95.0
    while length > 0:
        points = [catapult_point(route,length,across+delta) for delta in (-.2,.2)]
        if all(inside_deck(x*WIDTH_SCALE,z) for x,z in points): return length
        length -= .5
    raise ValueError("Catapult guide is outside the deck")


def slim_mesh(mesh):
    for _, vertices, _, _ in mesh.parts:
        vertices[:, 0] *= WIDTH_SCALE
    return mesh


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
    return (x+(offset_x*math.cos(angle)-offset_z*math.sin(angle))/WIDTH_SCALE,
            z+offset_x*math.sin(angle)+offset_z*math.cos(angle))


def inside_deck(x, z):
    inside = False
    outline = physical_xz(DECK)
    for (ax, az), (bx, bz) in zip(outline, outline[1:]+outline[:1]):
        if (az > z) != (bz > z) and x < ax+(bx-ax)*(z-az)/(bz-az):
            inside = not inside
    return inside


def rectangle_distance(x, z, xlo, xhi, zlo, zhi):
    return math.hypot(max(xlo-x, x-xhi, 0), max(zlo-z, z-zhi, 0))


def lateral_gap(left, right, xlo, xhi):
    return max(xlo-right, left-xhi, 0)


def bow_sonar_fairing(mesh):
    """Round the sonar blister into the bow; its aft end sits inside the hull."""
    sides, sections = 32, 16
    centre_y, centre_z = -6.2, 160.0
    half_width, half_height, half_length = 3.0, 2.0, 12.0
    vertices = [(0, centre_y, centre_z-half_length)]
    for i in range(1, sections):
        theta = math.pi*i/sections
        radius = math.sin(theta)
        z = centre_z-half_length*math.cos(theta)
        for j in range(sides):
            angle = 2*math.pi*j/sides
            vertices.append((half_width*radius*math.cos(angle),
                             centre_y+half_height*radius*math.sin(angle), z))
    end = len(vertices)
    vertices.append((0, centre_y, centre_z+half_length))
    faces = [[0, 1+(j+1)%sides, 1+j] for j in range(sides)]
    for i in range(sections-2):
        a, b = 1+i*sides, 1+(i+1)*sides
        faces.extend([[a+j, a+(j+1)%sides, b+(j+1)%sides, b+j]
                      for j in range(sides)])
    last = 1+(sections-2)*sides
    faces.extend([[last+j, last+(j+1)%sides, end] for j in range(sides)])
    mesh.add("BowSonarFairingStudy", vertices, faces, "underwater")


def geometry(closed_lasers=True):
    m = Mesh()
    # The first hull ring shares the whole deck underside outline: the hull
    # rises to the flight deck at the bow, stern, and both sides, then narrows
    # through faceted chines towards its waterline and keel.
    chine = hull_outline(.74, .99, .40)
    shoulder = hull_outline(.58, .98, .12)
    waterline = hull_outline(WATERLINE_WIDTH_SCALE, .98, .02)
    keel = hull_outline(.31, .88, .02)
    loft(m, "HardChineHull", [polygon_at_y(DECK, DECK_UNDERSIDE_Y),
                              polygon_at_y(chine, 12),
                              polygon_at_y(shoulder, 4.5),
                              polygon_at_y(waterline, 0)], "hull")
    loft(m, "UnderwaterBody", [polygon_at_y(waterline, 0),
                               polygon_at_y(keel, -DESIGN_DRAFT_M)], "underwater")
    m.prism("FacetedFlightDeck", DECK, DECK_UNDERSIDE_Y, DECK_SURFACE_Y, "deck")
    for i, (a, b) in enumerate(zip(DECK, DECK[1:] + DECK[:1]), 1):
        deck_line(m,f"DeckEdge_{i:02d}",a,b,.28,"edge")

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

    aft_start = len(m.parts)
    aft_top = scaled_polygon(AFT_ISLAND_REFERENCE, 32.5, -89, .82, .80)
    loft(m, "AftAviationIsland",
         [polygon_at_y(AFT_ISLAND_REFERENCE, 22), polygon_at_y(aft_top, 33.5)], "island")
    aft_bridge = [(28, -104), (34, -105), (38, -98),
                  (38, -78), (32, -72), (28, -76)]
    aft_bridge_top = scaled_polygon(aft_bridge, 33, -88, .8, .82)
    loft(m, "AftAviationBridge",
         [polygon_at_y(aft_bridge, 33.3),
          polygon_at_y(aft_bridge_top, 39)], "island")
    # A closed glazed band follows every raked bridge face, including the
    # aft face and chamfered corners. Each pane is a thin closed prism.
    rings = []
    for y in (35.8,38.0):
        t=(y-33.3)/(39-33.3)
        rings.append([(x+(tx-x)*t,y,z+(tz-z)*t)
                      for (x,z),(tx,tz) in zip(aft_bridge,aft_bridge_top)])
    for i in range(6):
        j=(i+1)%6
        outer=[];inner=[]
        for ring in rings:
            for index in (i,j):
                x,y,z=ring[index]
                v=np.array((x-33,z+88));v/=np.linalg.norm(v)
                outer.append((x+v[0]*.09,y,z+v[1]*.09))
                inner.append((x+v[0]*.02,y,z+v[1]*.02))
        m.add(f"AftAviationWindow360_{i+1}",outer+inner,
              [[0,1,3,2],[4,6,7,5],[0,4,5,1],[2,3,7,6],[0,2,6,4],[1,5,7,3]],"glass")
    for face, xyz, dims in [
        ("Port", (28.2, 33.7, -90), (.18, 2.8, 6)),
        ("Starboard", (37.8, 33.7, -90), (.18, 2.8, 6)),
        ("Fore", (33, 33.7, -74), (5.4, 2.8, .18)),
    ]:
        m.box(f"AftSideRadar_{face}", *xyz, *dims, "sensor")
    aft_mast = [(30, -95), (35, -96), (37, -91),
                (37, -83), (33, -80), (30, -84)]
    loft(m, "AftEnclosedMast",
         [polygon_at_y(aft_mast, 38.8),
          polygon_at_y(scaled_polygon(aft_mast, 33.5, -88, .70, .70), 44)],
         "island")
    for _,vertices,_,_ in m.parts[aft_start:]:
        vertices[:,0] = 32.5+(vertices[:,0]-32.5)*AFT_ISLAND_SCALE[0]
        vertices[:,1] = 22+(vertices[:,1]-22)*AFT_ISLAND_SCALE[1]
        vertices[:,2] = -89+(vertices[:,2]+89)*AFT_ISLAND_SCALE[2]

    for i, (x, z) in enumerate(ELEVATORS, 1):
        half_width = LIFT_WIDTH_M/(2*WIDTH_SCALE)
        half_length = LIFT_LENGTH_M/2
        m.box(f"DeckEdgeLift_{i}", x, LIFT_SURFACE_Y-.17/2, z,
              LIFT_WIDTH_M/WIDTH_SCALE, .17, LIFT_LENGTH_M, "hatch")
        for side in (-1, 1):
            deck_line(m,f"LiftEdge_{i}_{side}",
                     (x-half_width+.2/WIDTH_SCALE, z+side*(half_length-.2)),
                     (x+half_width-.2/WIDTH_SCALE, z+side*(half_length-.2)),
                     .22)

    # CATOBAR steam launch tracks; native launch rules use the same axes.
    for i, (start, end) in enumerate(CATAPULTS, 1):
        # A deck-flush blast-deflector panel is marked behind each launch
        # point; actuator volume, exhaust flow and clearances remain unknown.
        route = (start, end)
        m.prism(f"CatapultJetBlastDeflector_{i}",
                catapult_deflector(route), DECK_SURFACE_Y-.14,DECK_SURFACE_Y+.002,"hatch")
        deck_line(m,f"CatapultJetBlastDeflectorHinge_{i}",
                 catapult_point(route,-16,-3.5), catapult_point(route,-16,3.5),
                 .13,"edge")
        for across in (-7/6,7/6):
            deck_line(m,f"CatapultJetBlastDeflectorSeam_{i}_{across:+.2f}",
                     catapult_point(route,-20,across),catapult_point(route,-16,across),
                     .06,"dark",above=.005,thickness=.001)
        # Shallow metal trough and dark slot, with a small shuttle rather
        # than the former raised yellow bar. These are static visual details.
        deck_line(m,f"CatapultTrack_{i}",start,end,.62,"track",above=.001)
        deck_line(m,f"CatapultSlot_{i}",start,end,.13,"dark",above=.004,thickness=.001)
        for side in (-1,1):
            deck_line(m,f"CatapultDeckGuide_{i}_{side}",
                     catapult_point(route,0,side*1.1),
                     catapult_point(route,catapult_guide_end(route,side*1.1),side*1.1),
                     .13,above=.006)
        shuttle = [catapult_point(route,along,across)
                   for along,across in ((-.55,-.22),(-.55,.22),(.55,.22),(.55,-.22))]
        m.prism(f"CatapultShuttle_{i}",shuttle,DECK_SURFACE_Y+.01,DECK_SURFACE_Y+.06,"gold")

    a, b = LANDING_LANE_A, LANDING_LANE_B
    for side in (-1, 1):
        deck_line(m,f"AngledLandingEdge_{side}",landing_point(0,side*11.3),
                  landing_point(1,side*11.3),.34)
    for i in range(13):
        p = a+(b-a)*(i+.10)/13
        q = a+(b-a)*(i+.49)/13
        deck_line(m,f"LandingCentreline_{i+1:02d}",p,q,.44)
    for i, t in enumerate((.31, .39, .47, .55), 1):
        deck_line(m,f"ArrestingWire_{i}",landing_point(t,-11),landing_point(t,11),
                  .08,"gold",above=.015,thickness=.015)
        for side in (-1, 1):
            x,z=landing_point(t,side*11.25)
            m.box(f"ArrestingWireAnchor_{i}_{side}",x,DECK_SURFACE_Y+.015,z,.85,.03,1.4,"dark")
    deck_line(m,"LandingThresholdStripe",landing_point(.02,-11),landing_point(.02,11),.38)

    # Offset helicopter pairs forward of each island; bow launches can run
    # alongside these, but the forward pair shares the waist runway area.
    for i, (x, z) in enumerate(VERTICAL_SPOTS, 1):
        rim = [(x+VERTICAL_SPOT_RADIUS*math.cos(2*math.pi*j/20)/WIDTH_SCALE,
                z+VERTICAL_SPOT_RADIUS*math.sin(2*math.pi*j/20))
               for j in range(20)]
        m.prism(f"AftVTOL_HeloSpot_{i}",rim,DECK_SURFACE_Y-.01,HELIPAD_SURFACE_Y,"hatch")
        for side in (-1, 1):
            deck_line(m,f"AftSpot_{i}_HStem_{side}",
                     pad_mark_point(x, z, -4.5, side*3.5),
                     pad_mark_point(x, z, 4.5, side*3.5),
                     .48)
        deck_line(m,f"AftSpot_{i}_HBar",
                 pad_mark_point(x, z, 0, -3.5),
                 pad_mark_point(x, z, 0, 3.5),
                 .48)

    # The base mesh shows shut, flush armoured hatches. A separate geometry
    # layer is drawn when the viewer's conceptual deploy control is activated.
    if closed_lasers:
        for i, (x, z) in enumerate(LASERS, 1):
            m.box(f"LaserHatchClosed_{i}",x,DECK_SURFACE_Y-.058,z,5,.12,5.8,"hatch")
            deck_line(m,f"LaserHatchSeam_{i}",(x,z-2.6),(x,z+2.6),.09,"edge")
    bow_sonar_fairing(m)
    add_combat_geometry(m, WIDTH_SCALE)
    return slim_mesh(m)


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
    return slim_mesh(m)


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
        return (int(width/2 + z*scale), int(height/2 - x*WIDTH_SCALE*scale))
    def shape(outline):
        return [point(x, z) for x, z in outline]
    def physical_box(x,z,w,l,fill):
        a = point((x-w/2)/WIDTH_SCALE,z-l/2)
        b = point((x+w/2)/WIDTH_SCALE,z+l/2)
        draw.rectangle((min(a[0],b[0]),min(a[1],b[1]),max(a[0],b[0]),max(a[1],b[1])),
                       fill=fill,outline="#9aacb3",width=1)
    for positions in (CIWS_POS,GUN_POS,CHAFF_POS,NULKA_POS):
        for x,y,z in positions:
            physical_box(x*.8,z,24 if positions in (SAM_POS,RAM_POS,CIWS_POS,GUN_POS) else 21,
                         7 if positions in (SAM_POS,RAM_POS,CIWS_POS,GUN_POS) else 2.8,"#52626b")
            physical_box(x,z,3,2.8,"#a4b5bb")
    draw.polygon(shape(DECK), fill="#40535e", outline="#b3c4c4", width=3)
    for x,z in VLS_BANKS:
        physical_box(x,z,4.6,19,"#20333c")
        for row in range(10):
            for side in (-1,1):
                physical_box(x+side*.9,z+(row-4.5)*1.7,1.45,1.35,"#8198a2")
    for positions in (SAM_POS,RAM_POS):
        for x,y,z in positions: physical_box(x,z,3,2.8,"#a4b5bb")
    for a, b in zip(DECK, DECK[1:]+DECK[:1]):
        draw.line([point(*a), point(*b)], fill="#758f95", width=3)
    draw.polygon(shape(MAIN_ISLAND_BASE), fill="#9eafb6", outline="#d8e3e2", width=2)
    draw.polygon(shape([(30, -3), (35, -4), (37, 19), (30, 18)]),
                 fill="#366072")
    draw.polygon(shape(AFT_ISLAND_BASE), fill="#8198a2", outline="#c1d8da", width=2)
    draw.polygon(shape([(32.5+(x-32.5)*.8,-89+(z+89)*.65)
                        for x,z in ((30,-95),(37,-91),(37,-83),(30,-84))]),fill="#366072")
    for x, z in ELEVATORS:
        p = point(x-LIFT_WIDTH_M/(2*WIDTH_SCALE), z+LIFT_LENGTH_M/2)
        q = point(x+LIFT_WIDTH_M/(2*WIDTH_SCALE), z-LIFT_LENGTH_M/2)
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
        draw.line([point(*a), point(*b)], fill="#92a1a6", width=3)
        draw.line([point(*a), point(*b)], fill="#162a35", width=1)
        for side in (-1,1):
            draw.line([point(*catapult_point((a,b),0,side*1.1)),
                       point(*catapult_point((a,b),catapult_guide_end((a,b),side*1.1),side*1.1))],
                      fill="#dce7e6",width=1)
        draw.polygon(shape(catapult_deflector((a,b))),
                     fill="#76909a", outline="#d2dfdf", width=1)
        for across in (-7/6,7/6):
            draw.line([point(*catapult_point((a,b),-20,across)),
                       point(*catapult_point((a,b),-16,across))],fill="#263d48",width=1)
        sx,sy = point(*a)
        draw.ellipse((sx-2,sy-2,sx+2,sy+2),fill="#d8b66e")
    a, b = LANDING_LANE_A, LANDING_LANE_B
    for side in (-1, 1):
        draw.line([point(*landing_point(0,side*11.3)),point(*landing_point(1,side*11.3))],
                  fill="#d4e3e3", width=3)
    for i in range(13):
        draw.line([point(*(a+(b-a)*(i+.1)/13)),
                   point(*(a+(b-a)*(i+.49)/13))], fill="#f2f5f3", width=3)
    for t in (.31, .39, .47, .55):
        draw.line([point(*landing_point(t,-11)),point(*landing_point(t,11))],
                  fill="#d8b66e", width=3)
        for side in (-1, 1):
            px, py = point(*landing_point(t,side*11.25))
            draw.ellipse((px-3, py-3, px+3, py+3), fill="#11212c")
    draw.line([point(*landing_point(.02,-11)),point(*landing_point(.02,11))],fill="#eef4f3",width=3)
    for x, z in LASERS:
        px, py = point(x, z)
        draw.rectangle((px-10, py-9, px+10, py+9),
                       fill="#526a74", outline="#a3d2ce", width=2)
        draw.line((px-8, py, px+8, py), fill="#243d49", width=2)

    # Annotation leaders stay beyond the deck footprint.
    for label, anchor, xy in [
        ("MAIN COMMAND ISLAND", (35, 10), (912, 216)),
        ("AFT AVIATION ISLAND", (34, -88), (590, 207)),
        ("4 LIFTS / 22 x 26 m", (57, 54), (1250, 207)),
        ("4 FORWARD-OFFSET HELO SPOTS", (9.5/WIDTH_SCALE, -60), (158, 204)),
        ("3 BOW CATAPULTS", (0, 136), (1335, 655)),
        ("2 STAGGERED WAIST CATAPULTS", (-28, 45), (850, 715)),
        ("4 FLUSH LASER HATCHES", (-35, 109), (1266, 784)),
        ("4 ARRESTING WIRES", landing_point(.47), (160, 689)),
        ("9 DEGREE PORT RECOVERY", landing_point(.15), (155, 736)),
    ]:
        ax, ay = point(*anchor)
        tx, ty = xy
        draw.line([(ax, ay), (tx+8, ty-8)], fill="#607e88", width=2)
        draw.text((tx, ty), label, font=f(18, True), fill="#cadadc")
    draw.text((82, 872), "370 m overall  ·  82 m deck  ·  99 aircraft  ·  5,300 embarked  ·  CATOBAR",
              font=f(22), fill="#a1c8ca")
    draw.text((1276, 880), "GEOMETRY STUDY  /  NOT GAMEPLAY", font=f(16), fill="#91a6af")
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path)


def main():
    spec = json.loads((HERE/"spec.json").read_text())
    assert max(z for _, z in DECK)-min(z for _, z in DECK) == spec["length_m"]
    assert math.isclose((max(x for x, _ in DECK)-min(x for x, _ in DECK))*WIDTH_SCALE,
                        spec["flight_deck_beam_m"])
    assert len(CATAPULTS) == spec["deck"]["catapult_tracks"]
    assert WAIST_CATAPULT_HEADING_DEG == spec["deck"]["port_waist_heading_degrees"]
    assert PORT_LIFT_Z == spec["deck"]["port_lift_longitudinal_position_m"]
    assert len(VERTICAL_SPOTS) == spec["deck"]["aft_vertical_operation_spots"]
    assert spec["islands"]["count"] == 2
    assert PAD_MARK_ANGLE_DEG == spec["deck"]["aft_h_mark_angle_degrees"]
    assert spec["deck"]["tyre_contact_height_m"] == DECK_SURFACE_Y
    assert spec["deck"]["helipad_contact_height_m"] == HELIPAD_SURFACE_Y
    assert spec["deck"]["lift_contact_height_m"] == LIFT_SURFACE_Y
    # Check pad footprints and clear longitudinal departure corridors.
    lane_a, lane_b = np.array(physical_xz([LANDING_LANE_A, LANDING_LANE_B]))
    line = lane_b-lane_a
    spots = physical_xz(VERTICAL_SPOTS)
    lifts = physical_xz(ELEVATORS)
    islands = [physical_xz(p) for p in (MAIN_ISLAND_BASE, AFT_ISLAND_BASE)]
    min_island_gap = min_lift_gap = min_cat_clearance = float("inf")
    min_spot_edge_gap = min(
        math.dist(a, b)-2*VERTICAL_SPOT_RADIUS
        for i, a in enumerate(spots)
        for b in spots[i+1:]
    )
    assert min_spot_edge_gap >= 5
    for x, z in spots:
        for t in range(36):
            theta = 2*math.pi*t/36
            assert inside_deck(x+VERTICAL_SPOT_RADIUS*math.cos(theta),
                               z+VERTICAL_SPOT_RADIUS*math.sin(theta))
        p = np.array((x, z))
        t = min(1., max(0., float(np.dot(p-lane_a, line)/np.dot(line, line))))
        assert np.linalg.norm(p-(lane_a+t*line)) > VERTICAL_SPOT_RADIUS+11.3+1
        for lift_x, lift_z in lifts:
            assert rectangle_distance(x, z, lift_x-LIFT_WIDTH_M/2, lift_x+LIFT_WIDTH_M/2,
                                      lift_z-LIFT_LENGTH_M/2, lift_z+LIFT_LENGTH_M/2) > VERTICAL_SPOT_RADIUS+1
            gap = rectangle_distance(x,z,lift_x-LIFT_WIDTH_M/2,lift_x+LIFT_WIDTH_M/2,
                                     lift_z-LIFT_LENGTH_M/2,lift_z+LIFT_LENGTH_M/2)-VERTICAL_SPOT_RADIUS
            min_lift_gap = min(min_lift_gap, gap)
            assert gap >= 1
        for island in islands:
            xmin, xmax = min(px for px, _ in island), max(px for px, _ in island)
            zmin, zmax = min(pz for _, pz in island), max(pz for _, pz in island)
            assert rectangle_distance(x, z, xmin, xmax, zmin, zmax) > VERTICAL_SPOT_RADIUS+1
            gap = rectangle_distance(x,z,xmin,xmax,zmin,zmax)-VERTICAL_SPOT_RADIUS
            min_island_gap = min(min_island_gap, gap)
            assert gap >= 1
    for i,(_,z) in enumerate(spots):
        island=islands[0 if i<2 else 1]
        assert z-VERTICAL_SPOT_RADIUS > max(pz for _,pz in island)+1
    # Main-deck weapon keep-outs match the native no-parking zones. Their
    # physical footprints must clear pads, islands, lifts and all launch runs.
    weapon_bounds=[]
    for name,(x,z,w,l) in deck_weapon_zones():
        bounds=(x-w/2,x+w/2,z-l/2,z+l/2)
        weapon_bounds.append(bounds)
        assert all(inside_deck(px,pz) for px in bounds[:2] for pz in bounds[2:]),name
        assert all(rectangle_distance(px,pz,*bounds)>VERTICAL_SPOT_RADIUS
                   for px,pz in spots),name
        for lx,lz in lifts:
            assert bounds[1]<lx-LIFT_WIDTH_M/2 or bounds[0]>lx+LIFT_WIDTH_M/2 or \
                   bounds[3]<lz-LIFT_LENGTH_M/2 or bounds[2]>lz+LIFT_LENGTH_M/2,name
        for px,pz in physical_xz(LASERS):
            assert bounds[1]<px-2.5*WIDTH_SCALE or bounds[0]>px+2.5*WIDTH_SCALE or \
                   bounds[3]<pz-2.9 or bounds[2]>pz+2.9,(name,"laser hatch overlap")
    # The launch line and up to 60 m of forward rollout within the ship's
    # length keep a 12 m plan-view corridor clear of island/lift footprints.
    obstacles = [(min(x for x, _ in island), max(x for x, _ in island),
                  min(z for _, z in island), max(z for _, z in island))
                 for island in islands]
    lift_bounds = [(x-LIFT_WIDTH_M/2, x+LIFT_WIDTH_M/2,
                    z-LIFT_LENGTH_M/2, z+LIFT_LENGTH_M/2) for x, z in lifts]
    obstacles += lift_bounds
    for bounds in lift_bounds:
        for island in islands:
            xmin,xmax = min(x for x,_ in island), max(x for x,_ in island)
            zmin,zmax = min(z for _,z in island), max(z for _,z in island)
            assert bounds[1] <= xmin or bounds[0] >= xmax or bounds[3] <= zmin or bounds[2] >= zmax
    assert spec["deck"]["lift_platform_width_m"] == LIFT_WIDTH_M
    assert spec["deck"]["lift_platform_length_m"] == LIFT_LENGTH_M
    assert LIFT_WIDTH_M >= 19.545+2, "F-14A full-span reference needs side clearance"
    f14_reference_shift = abs(-.074+.012+.0126)*METRES_PER_UNIT
    assert LIFT_LENGTH_M/2 >= 19.1/2+f14_reference_shift
    # All five lanes accept the same broad reference envelope. Check both
    # staging and the aligned taxi approach against fixed deck obstacles.
    # This does not establish clearance through taxi turns or rotor arcs.
    for index in range(5):
        start,end = np.array(physical_xz(CATAPULTS[index]))
        direction = (end-start)/np.linalg.norm(end-start)
        lateral = np.array((direction[1],-direction[0]))
        half_length,half_span = 15,12.5
        for approach in (0,-20):
            for along in np.linspace(-half_length,half_length,7):
                for across in np.linspace(-half_span,half_span,7):
                    x,z = start+(approach+along)*direction+across*lateral
                    assert inside_deck(x,z), (index,approach,"aircraft off deck")
                    assert min(rectangle_distance(x,z,*b) for b in obstacles) >= 1.5, \
                        (index,approach,"aircraft overlaps an island or lift")
                    assert all(rectangle_distance(x,z,*b)>0 for b in weapon_bounds), \
                        (index,approach,"aircraft overlaps a defensive deck mount")
        for along in np.linspace(0,95,96):
            for across in (-half_span,0,half_span):
                x,z=start+along*direction+across*lateral
                assert all(rectangle_distance(x,z,*b)>0 for b in weapon_bounds), \
                    (index,"launch run intersects a defensive deck mount")
    for route in CATAPULTS:
        (sx, sz), (ex, ez) = physical_xz(route)
        length = math.hypot(ex-sx,ez-sz)
        dx,dz = (ex-sx)/length,(ez-sz)/length
        for along in np.linspace(0,length+60,100):
            x,z = sx+along*dx,sz+along*dz
            if z > 185: break
            nearest = min(rectangle_distance(x, z, *bounds)
                          for bounds in obstacles)
            min_cat_clearance = min(min_cat_clearance, nearest)
            assert nearest >= 12
    mesh = geometry()
    parts = {name: vertices for name, vertices, _, _ in mesh.parts}
    for i in range(1,5):
        assert abs(max(parts[f"DeckEdgeLift_{i}"][:,1])-LIFT_SURFACE_Y)<1e-9
        assert abs(max(parts[f"AftVTOL_HeloSpot_{i}"][:,1])-HELIPAD_SURFACE_Y)<1e-9
        assert abs(max(parts[f"LaserHatchClosed_{i}"][:,1])-(DECK_SURFACE_Y+.002))<1e-9
    for name,vertices,_,material in mesh.parts:
        if material=="white":
            assert DECK_SURFACE_Y < min(vertices[:,1]) <= max(vertices[:,1]) <= DECK_SURFACE_Y+.008001,name
    for name,vertices in parts.items():
        if name.startswith("Catapult"):
            assert all(inside_deck(x,z) for x,y,z in vertices), (name,"hardware outside deck")
    n = len(DECK)
    assert np.array_equal(parts["HardChineHull"][:n],
                          parts["FacetedFlightDeck"][:n])
    assert np.array_equal(parts["HardChineHull"][-n:],
                          parts["UnderwaterBody"][:n])
    bow_z = max(z for _, z in DECK)
    immersed_bow = [x for x, z in hull_outline(.82, .98, .02)
                    if math.isclose(z, bow_z*.98)]
    assert len(immersed_bow) == 2
    bow_tip_width = abs(immersed_bow[0]-immersed_bow[1])*WIDTH_SCALE
    assert bow_tip_width < 1.0
    for x, z in physical_xz(LASERS):
        for dx in (-2.8*WIDTH_SCALE, 2.8*WIDTH_SCALE):
            for dz in (-3.1, 3.1):
                assert inside_deck(x+dx, z+dz)
    def area(points):
        return abs(sum(x*z2-x2*z for (x, z), (x2, z2)
                       in zip(points, points[1:]+points[:1])))/2
    waterline = physical_xz(hull_outline(WATERLINE_WIDTH_SCALE, .98, .02))
    keel = physical_xz(hull_outline(.31, .88, .02))
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
                   flight_deck_beam_m=DECK_BEAM_M,
                   bow_outer_catapult_lateral_separation_m=round((CATAPULTS[2][0][0]-CATAPULTS[0][0][0])*WIDTH_SCALE,2),
                   catapult_type="Steam CATOBAR, three bow and two port-waist 95 m tracks",
                   bow_catapult_ids=list(BOW_CATAPULT_IDS),
                   port_waist_catapult_ids=list(WAIST_CATAPULT_IDS),
                   port_waist_heading_degrees=WAIST_CATAPULT_HEADING_DEG,
                   port_lift_longitudinal_position_m=PORT_LIFT_Z,
                   port_waist_launch_stagger_m=abs(CATAPULTS[4][0][1]-CATAPULTS[3][0][1]),
                   catapult_flush_slot_shuttle_details=True,
                   embarked_complement_design_target=FIT["crew"]["total"],
                   accommodation_berths_design_target=FIT["crew"]["berths"],
                   peripheral_vls_cells_visual_target=80,
                   aft_vertical_operation_spots=len(VERTICAL_SPOTS),
                   deck_edge_lifts=len(ELEVATORS),
                   lift_platform_width_m=LIFT_WIDTH_M,
                   lift_platform_length_m=LIFT_LENGTH_M,
                   lift_surface_height_m=LIFT_SURFACE_Y,
                   helipad_contact_height_m=HELIPAD_SURFACE_Y,
                   deck_paint_maximum_height_m=.008,
                   stowed_surfaces_flush=True,
                   overall_beam_including_lifts_m=2*LIFT_CENTRE_X_M+LIFT_WIDTH_M,
                   f14a_lift_reference_envelope_checked=True,
                   islands=2, aft_h_mark_angle_degrees=PAD_MARK_ANGLE_DEG,
                   design_mass_budget_matches_hull_volume_within_one_percent=abs(submerged_volume*1.025-FIT["full_load_displacement_tonnes"])/FIT["full_load_displacement_tonnes"]<.01,
                   aft_spot_clearance_geometry_checked=True,
                   pads_forward_of_their_islands=True,
                   all_vertical_spots_waist_interlocked=True,
                   catapult_reference_envelope_span_m=25,
                   catapult_reference_envelope_length_m=30,
                   catapult_staging_and_aligned_approaches_checked=True,
                   recovery_heading_degrees=LANDING_HEADING_DEG,
                   aft_island_scale=list(AFT_ISLAND_SCALE),
                   aft_bridge_glazing_faces=6,
                   catapult_launch_corridors_clear=True,
                   minimum_spot_edge_spacing_m=round(min_spot_edge_gap, 2),
                   minimum_pad_to_island_footprint_gap_m=round(min_island_gap, 2),
                   minimum_pad_to_lift_footprint_gap_m=round(min_lift_gap, 2),
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
            "deck_width_m": DECK_BEAM_M}, mesh,
           HERE/"previews/australis_2030_perspective.png")
    render({"name": "Australis class — bow view", "aircraft_capacity": 99,
            "propulsion": "Nuclear concept", "length_m": 370,
            "deck_width_m": DECK_BEAM_M}, mesh,
           HERE/"previews/australis_2030_bow.png",
           camera_azimuth_deg=90, camera_elevation_deg=8)
    plan_preview(HERE/"previews/australis_2030_deck_plan.png")
    render({"name": "Australis class — port waist", "aircraft_capacity": 99,
            "propulsion": "Nuclear concept", "length_m": 370,
            "deck_width_m": DECK_BEAM_M}, mesh,
           HERE/"previews/australis_2030_port_waist.png",
           camera_azimuth_deg=-125, camera_elevation_deg=38)
    (HERE/"model/validation.json").write_text(
        json.dumps(summary, indent=2)+"\n")
    revision = model_revision(mesh, COLORS)
    photos = render_current_views(mesh, COLORS, HERE/"previews", revision)
    build_viewer(mesh, COLORS, HERE/"viewer/australis_2030_3d.html", deployed_lasers(), photos)
    print(f"[OK] {summary['parts']} closed components; {summary['triangles']} triangles")
    print(f"[OK] Current model photos and self-contained 3D viewer share revision {revision}")
    print("[OK] Original metre OBJ, approximate game-scale OBJ, four layout previews and four model photos")
    print("[STATUS] User confirmed hull loading; revised visuals and aircraft operations await QA")


if __name__ == "__main__":
    main()
