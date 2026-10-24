"""Verified native CIWS lift/cover animation data for the original Australis.

All coordinates exported here are physical metres in ship-local space.  The
animation file uses absolute local positions, so its formatter divides the
complete XYZ position by metres_per_unit.  It does not apply WIDTH_SCALE.

Native evidence: AnimationLibrary.ParseAnimation/ParseCompactStep (RVA
2249400/2250104), ObjectBaseLoader.loadAnimations (RVA2397684), and
WeaponSystemCIWS.OnFixedUpdate/updateAnimations (RVA3286760/3288744).
The engine does not initialize these animations to their first pose: register
the moving submodels at their closed positions from moving_model_specs().
"""
from __future__ import annotations

from dataclasses import dataclass


ANIMATION_REFERENCE = "animations_ran_cvn_australis_2030_ciws"
ANIMATION_RELATIVE_PATH = f"animations/{ANIMATION_REFERENCE}.ini"
METRES_PER_UNIT = 217 / 3.161967

CIWS_POSITIONS_M = ((-44.0, 19.0, 148.0),
                    (44.0, 19.0, -72.0),
                    (-44.0, 19.0, -166.0))
CIWS_LIFT_STROKE_M = 5.0
CIWS_DOOR_OPEN_SECONDS = 0.10
CIWS_RISE_SECONDS = 0.30
CIWS_OPEN_SECONDS = CIWS_DOOR_OPEN_SECONDS + CIWS_RISE_SECONDS
CIWS_CLOSE_SECONDS = 1.0
CIWS_CLOSE_LIFT_SECONDS = 0.70
# This is an engine condition, not an authored INI setting.
NATIVE_IDLE_CLOSE_SECONDS = 10.0

CIWS_DECK_TOP_M = 22.002
CIWS_DOOR_CENTRE_Y_M = 22.0
CIWS_DOOR_THICKNESS_M = 0.004
CIWS_DOOR_WIDTH_M = 3.2
CIWS_DOOR_LENGTH_M = 6.4
CIWS_DOOR_OFFSET_M = CIWS_DOOR_WIDTH_M / 2
CIWS_DOOR_TRAVEL_M = 3.2
CIWS_LIFT_WIDTH_M = 4.8
CIWS_LIFT_LENGTH_M = 5.8
CIWS_LIFT_THICKNESS_M = 0.30
CIWS_YAW_LOCAL_POSITION_M = (0.0, 1.0, 0.0)


@dataclass(frozen=True)
class CIWSPod:
    index: int
    position: tuple[float, float, float]

    @property
    def lift(self) -> str:
        return f"CIWS_Lift_{self.index}"

    @property
    def mount(self) -> str:
        return f"CIWS_Mount_{self.index}"

    @property
    def barrel(self) -> str:
        return f"CIWS_Gun_{self.index}"

    @property
    def open_animation(self) -> str:
        return f"CIWS_Deploy_{self.index}"

    @property
    def close_animation(self) -> str:
        return f"CIWS_Stow_{self.index}"

    def door(self, side: str) -> str:
        if side not in ("L", "R"):
            raise ValueError("Door side must be L or R")
        return f"CIWS_Door_{self.index}_{side}"

    def lift_position(self, deployed: bool) -> tuple[float, float, float]:
        x, y, z = self.position
        return x, y + (CIWS_LIFT_STROKE_M if deployed else 0), z

    def door_position(self, side: str, opened: bool) -> tuple[float, float, float]:
        self.door(side)  # Validate side before deriving its direction.
        x, _, z = self.position
        offset = CIWS_DOOR_OFFSET_M + (CIWS_DOOR_TRAVEL_M if opened else 0)
        return x + (-offset if side == "L" else offset), CIWS_DOOR_CENTRE_Y_M, z


PODS = tuple(CIWSPod(i, position) for i, position in enumerate(CIWS_POSITIONS_M, 1))


def animation_reference_rows() -> list[str]:
    """Rows for the vessel [Animations]; the file reference has no extension."""
    return ["NumberOfAnimationReferences=1", f"AnimationFile_1={ANIMATION_REFERENCE}"]


def weapon_animation_rows(index: int) -> list[str]:
    pod = PODS[index - 1]
    if pod.index != index:
        raise ValueError("CIWS index must be 1, 2 or 3")
    return [f"OpenSystemAnimation={pod.open_animation}",
            f"CloseSystemAnimation={pod.close_animation}"]


def moving_model_specs() -> tuple[dict, ...]:
    """Local metre poses and parent hierarchy for real registered OBJ meshes.

    Lift and doors are ship-root children. The existing yaw mesh is a child
    of the lift, and the elevation barrel remains a child of the yaw mesh.
    Mesh vertices for these names must be local to each respective pivot.
    """
    result = []
    for pod in PODS:
        result.extend((
            {"name": pod.lift, "parent": None, "position": pod.lift_position(False)},
            {"name": pod.door("L"), "parent": None, "position": pod.door_position("L", False)},
            {"name": pod.door("R"), "parent": None, "position": pod.door_position("R", False)},
            {"name": pod.mount, "parent": pod.lift, "position": CIWS_YAW_LOCAL_POSITION_M},
            {"name": pod.barrel, "parent": pod.mount, "position": (0.0, 0.0, 0.0)},
        ))
    return tuple(result)


def native_animation_ini(metres_per_unit: float = METRES_PER_UNIT) -> str:
    """Six native animations, three independently bound linear sequences each.

    StepN fields are Time|Position|Rotation|SmoothnessType. Positions are
    absolute local coordinates, 'none' leaves rotation untouched, and explicit
    lowercase 'linear' disables the parser's default eased interpolation.
    """
    if metres_per_unit <= 0:
        raise ValueError("metres_per_unit must be positive")

    def pos(value):
        return ",".join(f"{axis / metres_per_unit:.9f}" for axis in value)

    sections = ["[Animations]", "NumberOfAnimations=6"]
    for i, pod in enumerate(PODS):
        sections.extend((f"Animation{i * 2 + 1}={pod.open_animation}",
                         f"Animation{i * 2 + 2}={pod.close_animation}"))
    for pod in PODS:
        for opening in (True, False):
            name = pod.open_animation if opening else pod.close_animation
            models = (pod.lift, pod.door("L"), pod.door("R"))
            sections.extend(("", f"[{name}]", "NumberOfSequencesToPlay=3"))
            for i, model in enumerate(models, 1):
                sections.extend((f"Sequence{i}={name}_Sequence{i}",
                                 f"Sequence{i}_Model={model}",
                                 f"Sequence{i}_Loop=False"))
            for i, model in enumerate(models, 1):
                if i == 1:
                    if opening:
                        steps = ((0, pod.lift_position(False)),
                                 (CIWS_DOOR_OPEN_SECONDS, pod.lift_position(False)),
                                 (CIWS_OPEN_SECONDS, pod.lift_position(True)))
                    else:
                        steps = ((0, pod.lift_position(True)),
                                 (CIWS_CLOSE_LIFT_SECONDS, pod.lift_position(False)),
                                 (CIWS_CLOSE_SECONDS, pod.lift_position(False)))
                else:
                    side = "L" if i == 2 else "R"
                    if opening:
                        steps = ((0, pod.door_position(side, False)),
                                 (CIWS_DOOR_OPEN_SECONDS, pod.door_position(side, True)),
                                 (CIWS_OPEN_SECONDS, pod.door_position(side, True)))
                    else:
                        steps = ((0, pod.door_position(side, True)),
                                 (CIWS_CLOSE_LIFT_SECONDS, pod.door_position(side, True)),
                                 (CIWS_CLOSE_SECONDS, pod.door_position(side, False)))
                sections.extend(("", f"[{name}_Sequence{i}]", f"NumberOfSteps={len(steps)}"))
                sections.extend(f"Step{n}={time:g}|{pos(position)}|none|linear"
                                for n, (time, position) in enumerate(steps, 1))
    return "\n".join(sections) + "\n"


def add_moving_meshes(mesh) -> None:
    """Add the nine lift/door meshes in local physical metres for native OBJ.

    Existing gun yaw/barrel meshes remain supplied by the main builder. The
    platform's upper face is its local pivot; closed covers meet at x=0 and
    have their upper faces at 22.002 m with the authored root positions.
    """
    for pod in PODS:
        mesh.box(pod.lift, 0, -CIWS_LIFT_THICKNESS_M / 2, 0,
                 CIWS_LIFT_WIDTH_M, CIWS_LIFT_THICKNESS_M, CIWS_LIFT_LENGTH_M, "dark")
        for side in ("L", "R"):
            mesh.box(pod.door(side), 0, 0, 0, CIWS_DOOR_WIDTH_M,
                     CIWS_DOOR_THICKNESS_M, CIWS_DOOR_LENGTH_M, "hatch")


def add_pod_geometry(mesh, width_scale: float, deployed: bool = False) -> None:
    """Source-preview lift/cover meshes in the shared authoring frame.

    Only moving platform/cover parts are added here. The caller supplies its
    fixed pod walls/shelf and gun geometry, positioning the gun at closed or
    deployed lift height to match the chosen preview pose.
    """
    if width_scale <= 0:
        raise ValueError("width_scale must be positive")
    for pod in PODS:
        x, y, z = pod.lift_position(deployed)
        mesh.box(pod.lift, x / width_scale, y - CIWS_LIFT_THICKNESS_M / 2, z,
                 CIWS_LIFT_WIDTH_M / width_scale, CIWS_LIFT_THICKNESS_M,
                 CIWS_LIFT_LENGTH_M, "dark")
        for side in ("L", "R"):
            x, y, z = pod.door_position(side, deployed)
            mesh.box(pod.door(side), x / width_scale, y, z,
                     CIWS_DOOR_WIDTH_M / width_scale, CIWS_DOOR_THICKNESS_M,
                     CIWS_DOOR_LENGTH_M, "hatch")
