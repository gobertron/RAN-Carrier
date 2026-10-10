#!/usr/bin/env python3
"""Build the original Australis 2050 geometry and presentation previews.

No files outside this concept folder are changed. This is not a game installer.
"""
from pathlib import Path
import json
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE.parent))
from generate_source_models import Mesh, COLORS, render, validate  # noqa: E402
from rebuild_game_scale import METRES_PER_UNIT  # noqa: E402

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
ISLAND_BASE = [
    (31, -30), (40, -33), (47, -23), (48, 28),
    (39, 39), (31, 32),
]
ELEVATORS = [(41, 118), (42, 69), (43, -57), (41, -140)]
LASERS = [(-52, 109), (53, 110), (-58, -125), (55, -126)]


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


def geometry():
    m = Mesh()
    stations = [(-185, 15), (-174, 23), (-148, 27), (-104, 28),
                (-36, 29), (45, 29), (113, 28), (153, 23),
                (174, 12), (185, 1.3)]
    dry, wet = [], []
    for z, b in stations:
        dry.append([(-.68*b, 0, z), (-b, 3, z), (-.98*b, 12, z),
                    (-.76*b, 20.3, z), (.76*b, 20.3, z),
                    (.98*b, 12, z), (b, 3, z), (.68*b, 0, z)])
        wet.append([(-.68*b, 0, z), (-.96*b, -2.5, z),
                    (-.64*b, -8, z), (.64*b, -8, z),
                    (.96*b, -2.5, z), (.68*b, 0, z)])
    loft(m, "HardChineHull", dry, "hull")
    loft(m, "UnderwaterBody", wet, "underwater")
    m.prism("FacetedFlightDeck", DECK, 20.3, 22, "deck")
    for i, (a, b) in enumerate(zip(DECK, DECK[1:] + DECK[:1]), 1):
        m.stripe(f"DeckEdge_{i:02d}", a, b, .28, 22.07, "edge")

    # The single island steps inward and aft as it rises. No open truss mast.
    lower_top = scaled_polygon(ISLAND_BASE, 39, 3, .82, .82)
    loft(m, "RakedIsland",
         [polygon_at_y(ISLAND_BASE, 22), polygon_at_y(lower_top, 37)], "island")
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

    for i, (x, z) in enumerate(ELEVATORS, 1):
        m.box(f"DeckEdgeLift_{i}", x, 22.12, z, 13, .17, 18, "hatch")
        for side in (-1, 1):
            m.stripe(f"LiftEdge_{i}_{side}", (x-6.4, z+side*8.8),
                     (x+6.4, z+side*8.8), .22, 22.25, "white")

    # Two bow and two waist indications; functional launch routes come later.
    cats = [((-15, 59), (-15, 157)), ((8, 55), (8, 161)),
            ((5, -18), (18, 75)), ((20, -38), (31, 62))]
    for i, (start, end) in enumerate(cats, 1):
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
    draw.text((82, 54), "AUSTRALIS 2050", font=f(41, True), fill="#edf3f3")
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
    draw.polygon(shape(ISLAND_BASE), fill="#9eafb6", outline="#d8e3e2", width=2)
    draw.polygon(shape([(35, -3), (42, -4), (44, 19), (35, 18)]),
                 fill="#366072")
    for x, z in ELEVATORS:
        p, q = point(x-6.5, z+9), point(x+6.5, z-9)
        draw.rectangle([min(p[0], q[0]), min(p[1], q[1]),
                        max(p[0], q[0]), max(p[1], q[1])],
                       fill="#718790", outline="#c6d3d1", width=2)
    for (a, b) in [((-15, 59), (-15, 157)), ((8, 55), (8, 161)),
                   ((5, -18), (18, 75)), ((20, -38), (31, 62))]:
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
        ("RAKED ISLAND / FLUSH ARRAYS", (44, 10), (896, 224)),
        ("4 DECK-EDGE LIFTS", (41, 118), (1372, 244)),
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
    mesh = geometry()
    summary = validate({"id": spec["id"], "aircraft_capacity": 99,
                        "air_group": [{"role": "Capacity placeholder", "count": 99}],
                        "offensive_ecm_modules": 1}, mesh)
    source = HERE/"model/source/ran_cvn_australis_2050.obj"
    game = HERE/"model/game-scale/ran_cvn_australis_2050.obj"
    mesh.save(source)
    mesh.save(game, scale=1/METRES_PER_UNIT)
    game.write_text(game.read_text().replace(
        "# RAN Carrier Restart: original model study; coordinates in metres",
        "# Approximate Sea Power scale; origin, deck routing and collision untested", 1))
    (HERE/"previews").mkdir(exist_ok=True)
    render({"name": spec["name"], "aircraft_capacity": 99,
            "propulsion": "Nuclear concept", "length_m": 370,
            "deck_width_m": 104}, mesh,
           HERE/"previews/australis_2050_perspective.png")
    plan_preview(HERE/"previews/australis_2050_deck_plan.png")
    (HERE/"model/validation.json").write_text(
        json.dumps(summary, indent=2)+"\n")
    print(f"[OK] {summary['parts']} closed components; {summary['triangles']} triangles")
    print("[OK] Original metre OBJ, approximate game-scale OBJ, and two previews")
    print("[STATUS] Design model only; Sea Power integration has not been tested")


if __name__ == "__main__":
    main()
