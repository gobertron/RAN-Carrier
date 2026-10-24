"""Render revision-labelled views directly from the closed Australis mesh.

These are deterministic orthographic model renders, with no invented
aircraft, texture details, water or other geometry added to the source.
"""
from __future__ import annotations

import math
import io
from pathlib import Path
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont, PngImagePlugin


VIEWS = (
    ("starboard", "Starboard aft", -57.0, 34.0),
    ("port_waist", "Port waist", -125.0, 38.0),
    ("deck", "Flight deck — bow up", None, None),
    ("bow", "Bow", 90.0, 10.0),
)
CAPTION = "3 bow + 2 waist catapults · 2 islands · 4 lifts · 4 vertical pads"


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    suffix = "-Bold" if bold else ""
    return ImageFont.truetype(
        f"/usr/share/fonts/truetype/dejavu/DejaVuSans{suffix}.ttf", size)


def _basis(azimuth: float | None, elevation: float | None):
    # Reorder authored XYZ into horizontal X/Z and vertical Y, exactly as
    # the repository's original per-pixel renderer does.
    if azimuth is None:
        return (np.array((0., 0., 1.)), np.array((1., 0., 0.)),
                np.array((0., 1., 0.)))
    az, el = math.radians(azimuth), math.radians(elevation)
    direction = np.array((math.cos(el)*math.cos(az),
                          math.cos(el)*math.sin(az), math.sin(el)))
    right = np.array((-math.sin(az), math.cos(az), 0.))
    return direction, right, np.cross(direction, right)


def _render(triangles, colors, title: str, azimuth, elevation,
            revision: str, path: Path) -> None:
    # A 1.5x depth-buffer render resolves narrow painted lines cleanly while
    # keeping each file practical to embed in the offline HTML gallery.
    width, height = 3600, 2100
    final_size = (2400, 1400)
    direction, right, up = _basis(azimuth, elevation)
    world = np.concatenate([tri[:, (0, 2, 1)] for _, tri, _ in triangles])
    projected = np.column_stack((world@right, world@up))
    low, high = projected.min(axis=0), projected.max(axis=0)
    centre = (high+low)/2
    # Reserve generous header/footer space; no silhouette is cropped.
    scale = min((width-330)/(high[0]-low[0]),
                (height-520)/(high[1]-low[1]))
    screen_centre = np.array((width/2, 250+(height-520)/2))
    gradient = np.linspace(0, 1, height, dtype=np.float32)[:, None, None]
    background = (np.array((24., 37., 49.))*(1-gradient)
                  + np.array((12., 22., 32.))*gradient).astype(np.uint8)
    rgb = np.repeat(background, width, axis=1)
    depth = np.full((height, width), -np.inf, dtype=np.float32)
    light = np.array((.25, -.40, .88))
    light /= np.linalg.norm(light)
    palette = {name: np.array([int(color[i:i+2], 16) for i in (1, 3, 5)])
               for name, color in colors.items()}
    for _, triangle, material in triangles:
        vertices = triangle[:, (0, 2, 1)]
        xy = (np.column_stack((vertices@right, vertices@up))-centre)*scale
        xy[:, 1] *= -1
        xy += screen_centre
        z = vertices@direction
        xmin, xmax = max(0, math.floor(xy[:, 0].min())), min(width-1, math.ceil(xy[:, 0].max()))
        ymin, ymax = max(0, math.floor(xy[:, 1].min())), min(height-1, math.ceil(xy[:, 1].max()))
        if xmax < xmin or ymax < ymin:
            continue
        a, b, c = xy
        denominator = ((b[1]-c[1])*(a[0]-c[0])
                       + (c[0]-b[0])*(a[1]-c[1]))
        if abs(denominator) < 1e-8:
            continue
        # Broadcast one-dimensional pixel coordinates to avoid unnecessary
        # full-size meshgrid arrays for the large hull/deck triangles.
        xx = np.arange(xmin, xmax+1, dtype=np.float64)[None, :]+.5
        yy = np.arange(ymin, ymax+1, dtype=np.float64)[:, None]+.5
        u = ((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/denominator
        v = ((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/denominator
        q = 1-u-v
        distance = u*z[0]+v*z[1]+q*z[2]
        depth_region = depth[ymin:ymax+1, xmin:xmax+1]
        mask = (u >= -1e-7) & (v >= -1e-7) & (q >= -1e-7) & (distance > depth_region)
        if not np.any(mask):
            continue
        # Swapping authored Y/Z reverses handedness, so reverse the cross
        # product to preserve the source's outward-facing normals.
        normal = -np.cross(vertices[1]-vertices[0], vertices[2]-vertices[0])
        normal /= max(np.linalg.norm(normal), 1e-10)
        # Soft key and fill illumination keep facet boundaries readable,
        # without changing any model materials or painting fictional detail.
        shade = .58+.42*max(float(normal@light), 0.)
        color = np.clip(palette[material]*shade, 0, 255).astype(np.uint8)
        depth_region[mask] = distance[mask]
        rgb[ymin:ymax+1, xmin:xmax+1][mask] = color
    image = Image.fromarray(rgb).resize(final_size, Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(image)
    draw.text((88, 42), "AUSTRALIS 2030", font=_font(40, True), fill="#eef4f4")
    draw.text((88, 98), f"Actual model render · {title}", font=_font(27), fill="#92c8ce")
    revision_text = f"REVISION {revision}"
    revision_font = _font(19, True)
    revision_width = draw.textlength(revision_text, font=revision_font)
    draw.text((2312-revision_width, 56), revision_text,
              font=revision_font, fill="#b1c3cb")
    draw.line((88, 161, 2312, 161), fill="#405664", width=2)
    draw.line((88, 1276, 2312, 1276), fill="#405664", width=2)
    draw.text((88, 1301), CAPTION, font=_font(23), fill="#b1d2d6")
    draw.text((88, 1342), "Model geometry only · no aircraft displayed · not a gameplay screenshot",
              font=_font(19), fill="#94aab7")
    metadata = PngImagePlugin.PngInfo()
    metadata.add_text("Title", f"Australis 2030 — {title}")
    metadata.add_text("Source revision", revision)
    metadata.add_text("Description", "Actual closed source mesh; "+CAPTION)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", pnginfo=metadata, optimize=True)
    data = buffer.getvalue()
    # Encode and verify in memory, then replace atomically. A reader can
    # never see an empty or partly encoded PNG during a rebuild.
    with Image.open(io.BytesIO(data)) as check:
        check.load()
        assert check.size == final_size
        assert check.text.get("Source revision") == revision
    with tempfile.NamedTemporaryFile(prefix=path.stem+"-", suffix=".tmp",
                                     dir=path.parent, delete=False) as staged:
        staged.write(data)
        staged_path = Path(staged.name)
    try:
        staged_path.replace(path)
    finally:
        staged_path.unlink(missing_ok=True)


def render_current_views(mesh, colors, output_dir: Path, revision: str) -> list[dict]:
    """Write four exact-model PNGs and return gallery metadata for the viewer."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    if not revision or len(revision) > 80:
        raise ValueError("A short, nonempty source revision is required")
    triangles = list(mesh.triangles())
    if not triangles:
        raise ValueError("The current model has no triangles")
    out = []
    for view_id, title, azimuth, elevation in VIEWS:
        path = output_dir/f"australis_2030_current_{view_id}.png"
        _render(triangles, colors, title, azimuth, elevation, revision, path)
        out.append({"id": view_id, "title": title,
                    "caption": CAPTION, "path": path})
    for view in out:
        with Image.open(io.BytesIO(view["path"].read_bytes())) as check:
            check.load()
            assert check.size == (2400, 1400)
            assert check.text.get("Source revision") == revision
    return out
