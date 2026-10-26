"""Original recessed lift-wall fixtures and shared runtime lighting profiles.

All profile coordinates are physical metres, +X starboard, +Y up, +Z forward.
The port/inboard shaft face is an open hangar doorway and receives no fixtures.
Lenses use ordinary non-emissive material; runtime lamps supply the illumination.
"""

DECK_LEVEL_M = 22.002
LOWER_LEVEL_M = 11.8
OFF_DEPTH_M = .10
FULL_DEPTH_M = .60


def profiles(elevator_centres_physical):
    """Return JSON-serializable profiles for four independently gated shafts.

    The platform is 22 x 26 m. Its sweep ends at X +/-11 and Z +/-13 m;
    inner wall faces are offset by another .20 m. Lamp emitters sit .06 m
    in front of the enclosing wall, outside the platform's swept envelope.
    Unity Euler X=+30 aims the forward light vector down; a 50-degree cone
    therefore has its highest ray five degrees below the horizontal plane.
    """
    result = []
    for index, (x, z) in enumerate(elevator_centres_physical, 1):
        fixtures = []
        for y in (15., 19.):
            for dz in (-7., 7.):
                fixtures.append(dict(
                    name=f'LiftWallLamp_{index}_outer_{int(y)}_{int(dz):+d}',
                    position=(x+11.14, y, z+dz),
                    rotation_degrees=(30., -90., 0.), wall='outer',
                    color=(1., .88, .65), range=7., intensity=.65,
                    spot_angle=50.))
            for wall, dz, yaw in (('forward', 13.14, 180.), ('aft', -13.14, 0.)):
                fixtures.append(dict(
                    name=f'LiftWallLamp_{index}_{wall}_{int(y)}',
                    position=(x+4., y, z+dz),
                    rotation_degrees=(30., yaw, 0.), wall=wall,
                    color=(1., .88, .65), range=7., intensity=.65,
                    spot_angle=50.))
        result.append(dict(id=index, model=f'LiftPlatform{index}',
                           centre_xz_m=(x, z), fixtures=fixtures))
    return result


def add_fixtures(mesh, width_scale, elevator_centres_physical):
    """Add recessed housings/lenses to existing enclosing walls only.

    Housings fit within the 150 mm shaft-wall thickness. Lens fronts remain
    at least .15 m outside the moving platform's full plan footprint. These
    are visible fittings, not new collision or illuminated/emissive surfaces.
    """
    def box(name, x, y, z, dx, dy, dz, material):
        mesh.box(name, x/width_scale, y, z, dx/width_scale, dy, dz, material)

    for shaft in profiles(elevator_centres_physical):
        for lamp in shaft['fixtures']:
            x, y, z = lamp['position']
            name = lamp['name']
            if lamp['wall'] == 'outer':
                box(name+'_Housing', x+.12, y, z, .12, .30, .90, 'hatch')
                box(name+'_Lens', x+.0225, y, z, .025, .16, .72, 'edge')
            else:
                side = 1 if lamp['wall'] == 'forward' else -1
                box(name+'_Housing', x, y, z+side*.12, .90, .30, .12, 'hatch')
                box(name+'_Lens', x, y, z+side*.0225, .72, .16, .025, 'edge')
