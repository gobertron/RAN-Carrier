#!/usr/bin/env python3
"""Embed the original Australis mesh in an offline WebGL preview."""
from collections import defaultdict
from pathlib import Path
import base64
import gzip
import hashlib
import html
import io
import json
import struct

import numpy as np
from PIL import Image
from enclosed_deck import BAYS, moving_specs

MOTIONS={m["name"]:(m["axis"],m["travel"]) for m in moving_specs()}
for b in BAYS:
    kind,index=b.key.rsplit("_",1)
    for part in ("Housing","Barrel","Launcher"):
        MOTIONS[f"{kind}_{part}_{index}"]=("y",b.stroke)


def category(name):
    if name in MOTIONS:
        axis,travel=MOTIONS[name]
        return f'bay:{axis}:{travel:g}'
    for b in BAYS:
        if name.startswith(b.key.split('_')[0]+'_Tube_'+b.key.split('_')[1]+'_'):
            return f'bay:y:{b.stroke:g}'
    if name.startswith("Catapult"):
        return "catapults"
    if name.startswith(("DeckEdgeLift", "InternalLift", "LiftPlatform", "LiftEdge")):
        return "lifts"
    if name.startswith(("AftVTOL", "AftSpot")):
        return "spots"
    if name.startswith(("AngledLanding", "LandingCentreline", "ArrestingWire",
                        "LandingThreshold")):
        return "recovery"
    if name.startswith(("LaserHatchClosed", "LaserHatchSeam")):
        return "laser_closed"
    if name.startswith("LaserHatchOpen"):
        return "laser_open"
    if name.startswith(("LaserTurret", "LaserEmitter")):
        return "laser_turret"
    if name.startswith("CIWS_Door_") and name.endswith("_L"):
        return "ciws_door_l"
    if name.startswith("CIWS_Door_") and name.endswith("_R"):
        return "ciws_door_r"
    if name.startswith(("CIWS_Housing_", "CIWS_Barrel_", "CIWS_Lift_")):
        return "ciws_moving"
    if name.startswith(("MainRaked", "IntegratedBridge", "BridgeWindow",
                        "EnclosedSensor", "IntegratedRadar", "ShipboardECM",
                        "AftAviation", "AftEnclosed", "AftSideRadar")):
        return "islands"
    if name.startswith(("Laser", "OutboardFairing", "DefensiveHatch",
                        "BowSonarFairing", "PVLS", "ESSM", "RAM", "CIWS",
                        "Mk46", "SRBOC", "Nulka", "Nixie")):
        return "equipment"
    return "hull"


def model_revision(mesh, colors):
    """Stable identity shared by the mesh viewer and its exact-model photos."""
    digest = hashlib.sha256(b"Australis exact-model presentation v2\0")
    digest.update(json.dumps(colors, sort_keys=True).encode())
    for name, vertices, faces, material in mesh.parts:
        digest.update(json.dumps([name, faces, material], separators=(",", ":")).encode())
        digest.update(np.asarray(vertices, dtype="<f8").tobytes())
    return digest.hexdigest()[:12]


def build_viewer(mesh, colors, path, deployed_mesh=None, photos=None, fleet=None):
    revision = model_revision(mesh, colors)
    photo_buttons, photo_figures, photo_manifest = [], [], []
    for index, photo in enumerate(photos or []):
        image_path = Path(photo["path"])
        binary = image_path.read_bytes()
        with Image.open(image_path) as image:
            image.load()
            if image.text.get("Source revision") != revision:
                raise ValueError(f"Photo does not match the current model revision: {image_path}")
            # Full-resolution PNG sources remain unchanged in previews/.
            # Smaller gallery copies reduce the self-contained viewer size.
            image = image.convert('RGB')
            image.thumbnail((1600, 940), Image.Resampling.LANCZOS)
            preview = io.BytesIO()
            image.save(preview, format='WEBP', quality=85, method=6)
            embedded_image = preview.getvalue()
            image_width, image_height = image.size
        photo_buttons.append(
            f'<button type="button" data-photo="{index}"'
            f' aria-pressed="{str(index == 0).lower()}"'
            f' class="{"active" if index == 0 else ""}">{html.escape(photo["title"])}</button>')
        photo_figures.append(
            f'<figure data-photo="{index}"{" hidden" if index else ""}>'
            f'<img alt="{html.escape(photo["title"])} — exact current carrier mesh" '
            f'width="{image_width}" height="{image_height}" src="data:image/webp;base64,{base64.b64encode(embedded_image).decode()}">'
            f'<figcaption><strong>{html.escape(photo["title"])}</strong> '
            f'{html.escape(photo["caption"])} '
            f'<a href="" download="{image_path.stem}-preview.webp" data-download-photo>Download gallery preview</a>'
            '</figcaption></figure>')
        photo_manifest.append({"id": photo["id"], "filename": image_path.name,
                               "sha256": hashlib.sha256(binary).hexdigest(),
                               "embedded_sha256": hashlib.sha256(embedded_image).hexdigest(),
                               "embedded_format": "image/webp",
                               "embedded_size": [image_width, image_height]})
    if not photo_figures:
        raise ValueError("Build the current model photos before building its viewer")
    groups = defaultdict(list)
    triangles = list(mesh.triangles())
    if deployed_mesh is not None:
        triangles.extend(deployed_mesh.triangles())
    for name, triangle, material in triangles:
        normal = np.cross(triangle[1] - triangle[0], triangle[2] - triangle[0])
        length = np.linalg.norm(normal)
        if length < 1e-10:
            continue
        normal /= length
        for vertex in triangle:
            groups[(category(name), material)].extend((*vertex, *normal))
    payload = []
    for (part, material), coordinates in sorted(groups.items()):
        values = struct.pack("<" + "f" * len(coordinates), *coordinates)
        payload.append({"category": part, "color": colors[material],
                        "count": len(coordinates) // 6,
                        "data": base64.b64encode(values).decode("ascii")})
    if fleet:
        fleet_payload = []
        for ship in fleet:
            ship_groups = defaultdict(list)
            for name, triangle, material in ship["mesh"].triangles():
                normal = np.cross(triangle[1]-triangle[0], triangle[2]-triangle[0])
                length = np.linalg.norm(normal)
                if length < 1e-10:
                    continue
                normal /= length
                for vertex in triangle:
                    ship_groups[(category(name), material)].extend((*vertex, *normal))
            ship_payload = []
            for (part, material), coordinates in sorted(ship_groups.items()):
                values = struct.pack("<" + "f"*len(coordinates), *coordinates)
                ship_payload.append({"category": part, "color": colors[material],
                                     "count": len(coordinates)//6,
                                     "data": base64.b64encode(values).decode("ascii")})
            fleet_payload.append({"id": ship["id"], "name": ship["name"],
                                  "revision": model_revision(ship["mesh"], colors),
                                  "mesh": ship_payload})
        # The numbered hulls share almost every aggregate. Keep each unique
        # part once, retaining the exact original float32 bytes for every ship.
        unique_parts, part_indices = [], {}
        for ship in fleet_payload:
            references = []
            for part in ship['mesh']:
                key = json.dumps(part, sort_keys=True, separators=(',', ':'))
                if key not in part_indices:
                    part_indices[key] = len(unique_parts)
                    unique_parts.append(part)
                references.append(part_indices[key])
            ship['mesh'] = references
        payload = {"parts": unique_parts, "fleet": fleet_payload}
    path.parent.mkdir(parents=True, exist_ok=True)
    manifest = {"revision": revision, "closed_model_parts": len(mesh.parts),
                "closed_model_triangles": sum(1 for _ in mesh.triangles()),
                "photos": photo_manifest,
                "view": "Actual current design mesh; not an in-game screenshot",
                "air_group": "Empty; aircraft selected in Sea Power"}
    if fleet:
        manifest["fleet"] = [{"id": ship["id"], "name": ship["name"],
                              "revision": model_revision(ship["mesh"], colors),
                              "obj_sha256": ship["obj_sha256"],
                              "ini_sha256": ship["ini_sha256"],
                              "visible_parts": len(ship["mesh"].parts),
                              "triangles": sum(1 for _ in ship["mesh"].triangles())}
                             for ship in fleet]
    document = (TEMPLATE
                .replace("__REVISION__", revision)
                .replace("__PHOTO_BUTTONS__", "\n".join(photo_buttons))
                .replace("__PHOTO_FIGURES__", "\n".join(photo_figures))
                .replace("__PRESENTATION_MANIFEST__", json.dumps(manifest, separators=(",", ":")))
                .replace("__MESH_DATA__", json.dumps(base64.b64encode(gzip.compress(
                    json.dumps(payload, separators=(",", ":")).encode(), mtime=0)).decode())))
    if fleet:
        options = "".join(f'<option value="{i}">{html.escape(ship["name"])}</option>'
                          for i, ship in enumerate(fleet))
        document = document.replace('<h2>Camera</h2>',
            '<h2>Fleet ship</h2><label for="shipChoice" class="muted">Actual exported ship</label>'
            f'<select id="shipChoice" aria-label="Fleet ship">{options}</select>'
            '<p class="muted">Photos show Australis 91. Select another ship to inspect its own exported mesh.</p><h2>Camera</h2>')
        document = document.replace('</style>',
            'select{width:100%;background:#263e4c;color:#e1edef;border:1px solid #496572;'
            'border-radius:7px;padding:10px;font:inherit}\n</style>')
    path.write_text(document)
    (path.parent.parent / "model").mkdir(parents=True,exist_ok=True)
    (path.parent.parent / "model/presentation-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n")
    return (len(payload["fleet"]), sum(payload['parts'][index]["count"]//3 for ship in payload["fleet"] for index in ship["mesh"])) if fleet else (len(payload), sum(part["count"] // 3 for part in payload))


TEMPLATE = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="ran-model-revision" content="__REVISION__">
<title>Australis 2030 — current model photos and 3D · __REVISION__</title>
<style>
  :root { color-scheme: dark; font-family: system-ui, sans-serif; background: #101c27; color: #e8f1f1; }
  * { box-sizing: border-box; }
  body { margin: 0; min-height: 100vh; display: grid; grid-template-columns: minmax(220px, 285px) 1fr; }
  aside { background: #172a36; border-right: 1px solid #36505d; padding: 24px; z-index: 1; max-height:100vh; overflow:auto; }
  h1 { font-size: 1.58rem; margin: 0 0 4px; line-height: 1.13; letter-spacing: .025em; }
  .eyebrow { font-size: .7rem; letter-spacing: .15em; color: #87bfc4; font-weight: 700; margin-bottom: 16px; }
  .muted { color: #b0c4cb; font-size: .86rem; line-height: 1.48; }
  .pill { display: inline-block; padding: 5px 9px; border: 1px solid #7ca6a6; border-radius: 100px; color: #a9dbd8; font-size: .72rem; letter-spacing: .06em; margin: 13px 0 24px; }
  .revision { font-family: ui-monospace, monospace; color: #a9dbd8; font-size: .76rem; margin-top: 10px; }
  h2 { font-size: .72rem; color: #82bfc5; text-transform: uppercase; letter-spacing: .13em; margin: 20px 0 9px; }
  .buttons { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 7px; }
  button { color: #e1edef; background: #263e4c; border: 1px solid #496572; border-radius: 7px; padding: 9px; font: inherit; font-size: .82rem; cursor: pointer; }
  button:hover, button:focus-visible, button.active { background: #32626b; border-color: #8fcdcc; }
  #deploy, #deployCIWS { width: 100%; margin-bottom: 7px; }
  #deployCIWS { margin-top: 14px; }
  label { display: flex; align-items: center; gap: 9px; margin: 8px 0; font-size: .84rem; cursor: pointer; }
  input[type=checkbox] { accent-color: #7fd1cf; width: 16px; height: 16px; }
  .footer { margin-top: 23px; border-top: 1px solid #35505c; padding-top: 14px; }
  a { color: #a8e3e0; }
  [hidden] { display: none !important; }
  main { position: relative; min-width: 0; height: 100vh; overflow: hidden; display:grid; grid-template-rows:auto 1fr; background: #101c27; }
  .tabs { display:flex; gap:8px; align-items:center; padding:14px 18px; border-bottom:1px solid #36505d; flex-wrap:wrap; }
  .tabs .muted { margin-left:auto; font-size:.76rem; }
  #modelPanel { position:relative; min-height:0; }
  #photosPanel { overflow:auto; padding:16px; }
  figure { margin:0; }
  figure img { display:block; width:100%; height:auto; border:1px solid #35505c; border-radius:8px; background:#101c27; }
  figcaption { padding:14px 3px; font-size:.86rem; color:#b0c4cb; line-height:1.5; }
  figcaption strong { color:#eef3f4; display:block; font-size:1rem; }
  figcaption a { display:block; margin-top:10px; }
  canvas { display: block; width: 100%; height: 100%; cursor: grab; touch-action: none; }
  canvas:active { cursor: grabbing; }
  .hint { position: absolute; bottom: 18px; left: 20px; padding: 9px 12px; border-radius: 7px; color: #c6d8d8; background: #11212cbb; font-size: .8rem; pointer-events: none; }
  .bow { position: absolute; top: 22px; right: 22px; padding: 7px 10px; background: #152a37bb; border: 1px solid #51747c; border-radius: 5px; font-size: .78rem; pointer-events: none; }
  #error { position: absolute; top: 30%; left: 15%; right: 15%; text-align: center; background: #3f2730; padding: 22px; display: none; }
  @media (max-width: 700px) { body { grid-template-columns: 1fr; grid-template-rows: auto minmax(380px, 68vh); } aside { padding: 17px; max-height:none; } main { height: 68vh; } .buttons { grid-template-columns: repeat(2, 1fr); } .footer { margin-top: 12px; } .pill { margin-bottom:8px; } .tabs .muted { margin-left:0; } }
</style>
</head>
<body>
<aside>
  <div class="eyebrow">ROYAL AUSTRALIAN NAVY · DESIGN STUDY</div>
  <h1>Australis 2030</h1>
  <div class="muted">CATOBAR · 370 m · 82 m main deck · 99 aircraft · 5,300 embarked targets</div>
  <span class="pill">v0.8.2 LIFT LIGHTING</span>
  <div class="revision">Model revision __REVISION__</div>
  <p class="muted">Two bow + one port-waist catapult. Four lifts and three helipads. Aircraft support: fixed-wing carrier aircraft, VTOL/STOL and helicopters.</p>
  <div id="photoControls">
    <h2>Current model photos</h2>
    <div class="buttons" id="photoViews">__PHOTO_BUTTONS__</div>
    <p class="muted">These views and the rotatable model use the same current mesh. Aircraft are selected in Sea Power; this model has no parked aircraft.</p>
  </div>
  <div id="modelControls" hidden>
  <h2>Camera</h2>
  <div class="buttons" id="views">
    <button type="button" data-view="perspective" class="active">Perspective</button>
    <button type="button" data-view="top">Deck / top</button>
    <button type="button" data-view="starboard">Starboard</button>
    <button type="button" data-view="bow">Bow</button>
    <button type="button" data-view="port">Port waist</button>
    <button type="button" data-view="stern">Stern / waterjets</button>
    <button type="button" data-view="underwater">Underwater hull</button>
  </div>
  <h2>Model poses</h2>
  <button type="button" id="moveLifts">Raise all four lifts</button>
  <p class="muted">Lifts start at hangar level. Six-second movement preview; Unity runtime lighting is not simulated.</p>
  <button type="button" id="deploy" aria-pressed="false">Deploy four lasers</button>
  <div id="laserStatus" class="muted" aria-live="polite">Flush hatches closed</div>
  <button type="button" id="deployCIWS" aria-pressed="false">Raise enclosed weapons</button>
  <div id="ciwsStatus" class="muted" aria-live="polite">Enclosed bays stowed; flight deck available</div>
  <p class="muted">Deployment demonstration only. The viewer does not fire weapons.</p>
  <h2 hidden>Show parts</h2>
  <div id="layers" hidden>
    <label><input type="checkbox" value="hull" checked> Hull and flight deck</label>
    <label><input type="checkbox" value="islands" checked> Two islands and radar</label>
    <label><input type="checkbox" value="catapults" checked> Two bow + one port-waist catapult</label>
    <label><input type="checkbox" value="lifts" checked> Four internal lifts</label>
    <label><input type="checkbox" value="spots" checked> Three helicopter pads around the towers</label>
    <label><input type="checkbox" value="recovery" checked> 9° port recovery, four arresting wires</label>
    <label><input type="checkbox" value="laser" checked> Retractable laser positions</label>
    <label><input type="checkbox" value="equipment" checked> Other equipment</label>
  </div>
  </div>
  <div class="footer muted">Actual design-model views, not in-game screenshots. The smaller rear bridge has wraparound glazing. Manual pose preview. AnchorChain addon: .75 s deploy, hold 300 s after last shot, 10 s stow, aviation locked until closed. Combat/flight lock await in-game testing; lasers remain visual concepts.<br><br>
    Original model sources and installers are included in the numbered release package.
  </div>
</aside>
<main>
  <nav class="tabs" aria-label="Presentation view">
    <button type="button" id="photosTab" class="active" aria-pressed="true">Current model photos</button>
    <button type="button" id="modelTab" aria-pressed="false">Rotate 3D model</button>
    <span class="muted">Same mesh · revision __REVISION__</span>
  </nav>
  <section id="photosPanel" aria-label="Current model photos">__PHOTO_FIGURES__</section>
  <section id="modelPanel" hidden>
  <canvas id="scene" aria-label="Rotatable three-dimensional Australis carrier model"></canvas>
  <div class="bow">BOW → +Z</div>
  <div class="hint">Drag to orbit · wheel / pinch to zoom</div>
  <div id="error" role="alert"></div>
  </section>
</main>
<script type="application/json" id="presentationManifest">__PRESENTATION_MANIFEST__</script>
<script>
"use strict";
document.querySelectorAll('[data-download-photo]').forEach(link => {
  link.href = link.closest('figure').querySelector('img').src;
});
document.getElementById('photoViews').addEventListener('click', event => {
  const button = event.target.closest('button[data-photo]'); if (!button) return;
  document.querySelectorAll('#photoViews button').forEach(x => {
    const active = x === button; x.classList.toggle('active', active);
    x.setAttribute('aria-pressed', String(active));
  });
  document.querySelectorAll('#photosPanel figure').forEach(x => {
    x.hidden = x.dataset.photo !== button.dataset.photo;
  });
});
for (const id of ['photosTab', 'modelTab']) {
  document.getElementById(id).addEventListener('click', () => {
    const model = id === 'modelTab';
    document.getElementById('modelPanel').hidden = !model;
    document.getElementById('modelControls').hidden = !model;
    document.getElementById('photosPanel').hidden = model;
    document.getElementById('photoControls').hidden = model;
    for (const tab of ['photosTab', 'modelTab']) {
      const active = tab === id; document.getElementById(tab).classList.toggle('active', active);
      document.getElementById(tab).setAttribute('aria-pressed', String(active));
    }
    window.dispatchEvent(new Event('resize'));
  });
}
const canvas = document.getElementById("scene");
const gl = canvas.getContext("webgl", {antialias: true});
const errorBox = document.getElementById("error");
if (!gl) {
  errorBox.textContent = "WebGL is unavailable in this browser. Current model photos are available in the other tab.";
  errorBox.style.display = "block";
} else {
  (async () => {
  if (typeof DecompressionStream !== 'function') {
    errorBox.textContent = 'This browser can show the current model photos. Open the HTML in a current Firefox or Chrome browser to rotate the model.';
    errorBox.style.display = 'block';
    return;
  }
  const packedMesh = __MESH_DATA__;
  const compressed = Uint8Array.from(atob(packedMesh), c => c.charCodeAt(0));
  const stream = new Blob([compressed]).stream().pipeThrough(new DecompressionStream('gzip'));
  const decodedMesh = JSON.parse(await new Response(stream).text());
  const fleetData = Array.isArray(decodedMesh) ? null : decodedMesh.fleet.map(ship => ({
    ...ship, mesh: ship.mesh.map(part => typeof part === 'number' ? decodedMesh.parts[part] : part)
  }));
  const meshData = fleetData ? fleetData[0].mesh : decodedMesh;
  const vertexShader = `attribute vec3 position; attribute vec3 normal;
    uniform mat4 projection; uniform mat4 view; uniform vec3 offset;
    varying float light;
    void main() {
      vec3 sun = normalize(vec3(-0.38, 0.86, 0.42));
      light = 0.51 + 0.49 * abs(dot(normalize(normal), sun));
      gl_Position = projection * view * vec4(position + offset, 1.0);
    }`;
  const fragmentShader = `precision mediump float; uniform vec3 color;
    varying float light;
    void main() { gl_FragColor = vec4(color * light, 1.0); }`;
  function shader(type, source) {
    const s = gl.createShader(type); gl.shaderSource(s, source); gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
    return s;
  }
  const program = gl.createProgram();
  gl.attachShader(program, shader(gl.VERTEX_SHADER, vertexShader));
  gl.attachShader(program, shader(gl.FRAGMENT_SHADER, fragmentShader));
  gl.linkProgram(program);
  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(program));
  gl.useProgram(program);
  const attributes = {pos: gl.getAttribLocation(program, "position"), norm: gl.getAttribLocation(program, "normal")};
  const uniforms = {projection: gl.getUniformLocation(program, "projection"), view: gl.getUniformLocation(program, "view"), color: gl.getUniformLocation(program, "color"), offset: gl.getUniformLocation(program, "offset")};
  function uploadMeshes(data) { return data.map(item => {
    const binary = atob(item.data);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
    const buffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
    gl.bufferData(gl.ARRAY_BUFFER, bytes, gl.STATIC_DRAW);
    const color = [1, 3, 5].map(i => parseInt(item.color.slice(i, i + 2), 16) / 255);
    return {category: item.category, color, count: item.count, buffer};
  }); }
  let meshes = uploadMeshes(meshData);
  const shipChoice = document.getElementById('shipChoice');
  if (shipChoice && fleetData) shipChoice.addEventListener('change', () => {
    const ship = fleetData[Number(shipChoice.value)];
    for (const mesh of meshes) gl.deleteBuffer(mesh.buffer);
    meshes = uploadMeshes(ship.mesh);
    document.querySelector('h1').textContent = ship.name;
    document.querySelector('.revision').textContent = 'Model revision '+ship.revision;
    document.querySelector('.tabs .muted').textContent = ship.name+' · '+ship.revision;
    draw();
  });
  const enabled = new Set([...document.querySelectorAll('#layers input:checked')].map(x => x.value));
  const deployButton = document.getElementById('deploy');
  const laserStatus = document.getElementById('laserStatus');
  const ciwsButton = document.getElementById('deployCIWS');
  const ciwsStatus = document.getElementById('ciwsStatus');
  let deployTarget = 0, deployProgress = 0;
  let ciwsTarget = 0, ciwsProgress = 0;
  let liftTarget = 0, liftProgress = 0;
  let lastFrame = null, animating = false;
  function ciwsMotion(progress) {
    // Native demonstration: doors open over the first 0.10 s, then the
    // three mount assemblies rise 5 m over 0.10–0.40 s. Reverse to stow.
    return {door: Math.min(1, Math.max(0, progress/.2)),
            lift: Math.min(1, Math.max(0, (progress-.2)/.8))};
  }
  function updateCiwsStatus() {
    let text;
    if (ciwsProgress <= .000001) text = 'Enclosed bays stowed; flight deck available';
    else if (ciwsProgress >= .999999) text = 'Weapons raised; aviation locked in the addon';
    else if (ciwsTarget) text = ciwsProgress < .25 ? 'Bay hatches opening' : 'Weapons rising';
    else text = ciwsProgress > .25 ? 'Weapons lowering' : 'Bay hatches closing';
    if (ciwsStatus.textContent !== text) ciwsStatus.textContent = text;
  }
  let azimuth = 147*Math.PI/180, elevation = 34*Math.PI/180, distance = 540, top = false;
  const target = [0, 19, 0];
  function normalize(a) { const l = Math.hypot(...a); return a.map(x => x / l); }
  function cross(a,b) { return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]; }
  function lookAt(eye, target, up) {
    const z = normalize(eye.map((v, i) => v - target[i]));
    // The Sea Power authoring frame is +X starboard, +Y up, +Z bow.
    // Use its left-handed screen basis so photos and the 3D view agree.
    const x = normalize(cross(z, up));
    const y = cross(x, z);
    return new Float32Array([
      x[0], y[0], z[0], 0, x[1], y[1], z[1], 0, x[2], y[2], z[2], 0,
      -x.reduce((s,v,i)=>s+v*eye[i],0), -y.reduce((s,v,i)=>s+v*eye[i],0),
      -z.reduce((s,v,i)=>s+v*eye[i],0), 1
    ]);
  }
  function perspective(aspect) {
    const f = 1 / Math.tan(Math.PI / 6), near = 1, far = 3000;
    return new Float32Array([f/aspect,0,0,0, 0,f,0,0, 0,0,(far+near)/(near-far),-1, 0,0,2*far*near/(near-far),0]);
  }
  function draw() {
    const rect = canvas.getBoundingClientRect();
    const ratio = Math.min(devicePixelRatio || 1, 2);
    const width = Math.max(1, Math.round(rect.width * ratio));
    const height = Math.max(1, Math.round(rect.height * ratio));
    if (canvas.width !== width || canvas.height !== height) { canvas.width = width; canvas.height = height; }
    gl.viewport(0, 0, width, height);
    gl.clearColor(0.055, 0.105, 0.145, 1);
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
    gl.enable(gl.DEPTH_TEST);
    gl.depthFunc(gl.LEQUAL);
    const eye = top ? [0, target[1]+distance, 0.001] : [
      distance*Math.sin(azimuth)*Math.cos(elevation),
      target[1]+distance*Math.sin(elevation),
      distance*Math.cos(azimuth)*Math.cos(elevation)
    ];
    gl.uniformMatrix4fv(uniforms.projection, false, perspective(width/height));
    gl.uniformMatrix4fv(uniforms.view, false, lookAt(eye, target, top ? [0,0,1] : [0,1,0]));
    gl.enableVertexAttribArray(attributes.pos);
    gl.enableVertexAttribArray(attributes.norm);
    for (const mesh of meshes) {
      if (mesh.category.startsWith('laser_')) {
        if (!enabled.has('laser')) continue;
        if (mesh.category === 'laser_closed' && deployProgress > .001) continue;
        if (mesh.category !== 'laser_closed' && deployProgress < .001) continue;
      } else if (mesh.category.startsWith('bay:') || mesh.category.startsWith('ciws_')) {
        if (!enabled.has('equipment')) continue;
      } else if (!enabled.has(mesh.category)) continue;
      gl.bindBuffer(gl.ARRAY_BUFFER, mesh.buffer);
      gl.vertexAttribPointer(attributes.pos, 3, gl.FLOAT, false, 24, 0);
      gl.vertexAttribPointer(attributes.norm, 3, gl.FLOAT, false, 24, 12);
      gl.uniform3fv(uniforms.color, mesh.color);
      const offset = [0, 0, 0];
      if (mesh.category === 'laser_turret') offset[1] = (deployProgress-1)*4.3;
      const ciws = ciwsMotion(ciwsProgress);
      if (mesh.category.startsWith('bay:')) {
        const [,axis,travel]=mesh.category.split(':');
        offset['xyz'.indexOf(axis)]=Number(travel)*(axis==='y'?ciws.lift:ciws.door);
      }
      if (mesh.category === 'lifts') offset[1] = liftProgress * 10.202;
      if (mesh.category === 'ciws_moving') offset[1] = ciws.lift*5;
      if (mesh.category === 'ciws_door_l') offset[0] = -ciws.door*3.2;
      if (mesh.category === 'ciws_door_r') offset[0] = ciws.door*3.2;
      gl.uniform3fv(uniforms.offset, offset);
      gl.drawArrays(gl.TRIANGLES, 0, mesh.count);
    }
  }
  function animate(timestamp) {
    const elapsed = lastFrame === null ? 0 : Math.max(0, (timestamp-lastFrame)/1000);
    lastFrame = timestamp;
    function advance(current, targetValue, duration) {
      return current + Math.sign(targetValue-current) *
        Math.min(Math.abs(targetValue-current), elapsed/duration);
    }
    liftProgress = advance(liftProgress, liftTarget, 6);
    deployProgress = advance(deployProgress, deployTarget, .8);
    ciwsProgress = advance(ciwsProgress, ciwsTarget, ciwsTarget ? .75 : 10);
    updateCiwsStatus();
    draw();
    if (Math.abs(liftTarget-liftProgress) > .000001 || Math.abs(deployTarget-deployProgress) > .000001 || Math.abs(ciwsTarget-ciwsProgress) > .000001) {
      requestAnimationFrame(animate);
    } else {
      deployProgress = deployTarget; ciwsProgress = ciwsTarget;
      animating = false; lastFrame = null;
      laserStatus.textContent = deployTarget ? 'Four turrets raised' : 'Flush hatches closed';
      updateCiwsStatus();
      draw();
    }
  }
  function startDeploymentAnimation() {
    if (!animating) { animating = true; lastFrame = null; requestAnimationFrame(animate); }
  }
  deployButton.addEventListener('click', () => {
    deployTarget = deployTarget ? 0 : 1;
    deployButton.textContent = deployTarget ? 'Retract four lasers' : 'Deploy four lasers';
    deployButton.setAttribute('aria-pressed', String(Boolean(deployTarget)));
    laserStatus.textContent = deployTarget ? 'Hatches open; turrets rising' : 'Turrets lowering; hatches closing';
    startDeploymentAnimation();
  });
  document.getElementById('moveLifts').addEventListener('click', event => {
    liftTarget = liftTarget ? 0 : 1;
    event.target.textContent = liftTarget ? 'Lower all four lifts' : 'Raise all four lifts';
    startDeploymentAnimation();
  });
  ciwsButton.addEventListener('click', () => {
    ciwsTarget = ciwsTarget ? 0 : 1;
    ciwsButton.textContent = ciwsTarget ? 'Lower weapons (manual preview)' : 'Raise enclosed weapons';
    ciwsButton.setAttribute('aria-pressed', String(Boolean(ciwsTarget)));
    ciwsStatus.textContent = ciwsTarget ? 'Bay hatches opening' : 'Weapons lowering';
    startDeploymentAnimation();
  });
  document.querySelectorAll('#layers input').forEach(input => input.addEventListener('change', () => {
    if (input.checked) enabled.add(input.value); else enabled.delete(input.value);
    draw();
  }));
  document.getElementById('views').addEventListener('click', event => {
    const button = event.target.closest('button[data-view]'); if (!button) return;
    document.querySelectorAll('#views button').forEach(x => x.classList.toggle('active', x === button));
    const view = button.dataset.view;
    top = view === 'top';
    if (view === 'perspective') { azimuth=147*Math.PI/180; elevation=34*Math.PI/180; distance=540; }
    if (view === 'top') distance=520;
    if (view === 'starboard') { azimuth=Math.PI/2; elevation=.20; distance=530; }
    if (view === 'port') { azimuth=-Math.PI/2; elevation=.55; distance=530; }
    if (view === 'bow') { azimuth=0; elevation=.25; distance=480; }
    if (view === 'stern') { azimuth=Math.PI; elevation=-.06; distance=440; }
    if (view === 'underwater') { azimuth=2.40; elevation=-.35; distance=480; }
    draw();
  });
  const pointers = new Map();
  let pinchDistance = 0;
  canvas.addEventListener('pointerdown', event => {
    canvas.setPointerCapture(event.pointerId);
    pointers.set(event.pointerId, [event.clientX, event.clientY]);
    if (pointers.size === 2) { const p=[...pointers.values()]; pinchDistance=Math.hypot(p[0][0]-p[1][0],p[0][1]-p[1][1]); }
  });
  canvas.addEventListener('pointermove', event => {
    if (!pointers.has(event.pointerId)) return;
    const previous = pointers.get(event.pointerId);
    pointers.set(event.pointerId, [event.clientX, event.clientY]);
    if (pointers.size === 2) {
      const p=[...pointers.values()]; const next=Math.hypot(p[0][0]-p[1][0],p[0][1]-p[1][1]);
      if (pinchDistance) distance=Math.max(230,Math.min(1100,distance*pinchDistance/next));
      pinchDistance=next;
    } else {
      if (top) { top=false; azimuth=147*Math.PI/180; elevation=1.35; }
      azimuth += (event.clientX-previous[0])*.007;
      elevation = Math.max(-.14,Math.min(1.50,elevation+(event.clientY-previous[1])*.006));
      document.querySelectorAll('#views button').forEach(x=>x.classList.remove('active'));
    }
    draw();
  });
  for (const name of ['pointerup','pointercancel','lostpointercapture']) {
    canvas.addEventListener(name, event => { pointers.delete(event.pointerId); pinchDistance=0; });
  }
  canvas.addEventListener('wheel', event => {
    event.preventDefault(); distance=Math.max(230,Math.min(1100,distance*Math.exp(event.deltaY*.001)));
    draw();
  }, {passive:false});
  new ResizeObserver(draw).observe(canvas);
  window.addEventListener('resize', draw);
  draw();
  })().catch(() => {
    errorBox.textContent = 'The 3D view could not start. The Current model photos tab remains available.';
    errorBox.style.display = 'block';
  });
}
</script>
</body>
</html>
'''


if __name__ == "__main__":
    import sys
    sys.dont_write_bytecode = True
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
    from build_current_game_preview import main
    main()
