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
from PIL import Image, PngImagePlugin


def category(name):
    if name.startswith("Catapult"):
        return "catapults"
    if name.startswith(("DeckEdgeLift", "LiftEdge")):
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


def build_viewer(mesh, colors, path, deployed_mesh=None, photos=None):
    revision = model_revision(mesh, colors)
    photo_buttons, photo_figures, photo_manifest = [], [], []
    for index, photo in enumerate(photos or []):
        image_path = Path(photo["path"])
        binary = image_path.read_bytes()
        with Image.open(image_path) as image:
            image.load()
            if image.text.get("Source revision") != revision:
                raise ValueError(f"Photo does not match the current model revision: {image_path}")
            # Keep the full-colour originals separately. Indexed preview
            # copies make the offline gallery much smaller at the same size.
            metadata = PngImagePlugin.PngInfo()
            metadata.add_text("Source revision", revision)
            preview = io.BytesIO()
            image.quantize(colors=256, dither=Image.Dither.NONE).save(
                preview, format="PNG", optimize=True, pnginfo=metadata)
            embedded_image = preview.getvalue()
        photo_buttons.append(
            f'<button type="button" data-photo="{index}"'
            f' aria-pressed="{str(index == 0).lower()}"'
            f' class="{"active" if index == 0 else ""}">{html.escape(photo["title"])}</button>')
        photo_figures.append(
            f'<figure data-photo="{index}"{" hidden" if index else ""}>'
            f'<img alt="{html.escape(photo["title"])} — exact current carrier mesh" '
            f'width="2400" height="1400" src="data:image/png;base64,{base64.b64encode(embedded_image).decode()}">'
            f'<figcaption><strong>{html.escape(photo["title"])}</strong> '
            f'{html.escape(photo["caption"])} '
            f'<a href="" download="{image_path.name}" data-download-photo>Download PNG</a>'
            '</figcaption></figure>')
        photo_manifest.append({"id": photo["id"], "filename": image_path.name,
                               "sha256": hashlib.sha256(binary).hexdigest(),
                               "embedded_sha256": hashlib.sha256(embedded_image).hexdigest()})
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
    path.parent.mkdir(parents=True, exist_ok=True)
    manifest = {"revision": revision, "closed_model_parts": len(mesh.parts),
                "closed_model_triangles": sum(1 for _ in mesh.triangles()),
                "photos": photo_manifest,
                "view": "Actual current design mesh; not an in-game screenshot",
                "air_group": "Empty; aircraft selected in Sea Power"}
    document = (TEMPLATE
                .replace("__REVISION__", revision)
                .replace("__PHOTO_BUTTONS__", "\n".join(photo_buttons))
                .replace("__PHOTO_FIGURES__", "\n".join(photo_figures))
                .replace("__PRESENTATION_MANIFEST__", json.dumps(manifest, separators=(",", ":")))
                .replace("__MESH_DATA__", json.dumps(base64.b64encode(gzip.compress(
                    json.dumps(payload, separators=(",", ":")).encode(), mtime=0)).decode())))
    path.write_text(document)
    # A distinct filename avoids reopening the older same-name download.
    path.with_name(f"australis_2030_{revision}_3d.html").write_text(document)
    path.with_name(f"australis_2030_{revision}_preview.html").write_text(document)
    (path.parent.parent / "model/presentation-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n")
    return len(payload), sum(part["count"] // 3 for part in payload)


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
  #deploy { width: 100%; margin-bottom: 7px; }
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
  <span class="pill">CURRENT FIVE-CATAPULT LAYOUT</span>
  <div class="revision">Model revision __REVISION__</div>
  <p class="muted">Three bow + two port-waist catapults. Four lifts and four vertical spots. Aircraft support: fixed-wing carrier aircraft, VTOL/STOL and helicopters.</p>
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
  </div>
  <h2>Defensive mount study</h2>
  <button type="button" id="deploy" aria-pressed="false">Deploy four lasers</button>
  <div id="laserStatus" class="muted" aria-live="polite">Flush hatches closed</div>
  <h2>Show parts</h2>
  <div id="layers">
    <label><input type="checkbox" value="hull" checked> Hull and flight deck</label>
    <label><input type="checkbox" value="islands" checked> Two islands and radar</label>
    <label><input type="checkbox" value="catapults" checked> Three bow + two port-waist catapults</label>
    <label><input type="checkbox" value="lifts" checked> Four deck-edge lifts</label>
    <label><input type="checkbox" value="spots" checked> Four helicopter spots ahead of islands</label>
    <label><input type="checkbox" value="recovery" checked> 9° port recovery, four arresting wires</label>
    <label><input type="checkbox" value="laser" checked> Retractable laser positions</label>
    <label><input type="checkbox" value="equipment" checked> Other equipment</label>
  </div>
  </div>
  <div class="footer muted">Actual design-model views, not in-game screenshots. The smaller rear bridge has wraparound glazing. Laser deployment is a visual study; revised flight operations and combat still need in-game testing.<br><br>
    <a href="https://github.com/gobertron/RAN-Carrier/tree/feature/australis-2050-concept/australis-2030/model/source" target="_blank" rel="noopener">Source models on GitHub</a>
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
  const meshData = JSON.parse(await new Response(stream).text());
  const vertexShader = `attribute vec3 position; attribute vec3 normal;
    uniform mat4 projection; uniform mat4 view; uniform float lift;
    varying float light;
    void main() {
      vec3 sun = normalize(vec3(-0.38, 0.86, 0.42));
      light = 0.51 + 0.49 * abs(dot(normalize(normal), sun));
      gl_Position = projection * view * vec4(position + vec3(0.0, lift, 0.0), 1.0);
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
  const uniforms = {projection: gl.getUniformLocation(program, "projection"), view: gl.getUniformLocation(program, "view"), color: gl.getUniformLocation(program, "color"), lift: gl.getUniformLocation(program, "lift")};
  const meshes = meshData.map(item => {
    const binary = atob(item.data);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
    const buffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
    gl.bufferData(gl.ARRAY_BUFFER, bytes, gl.STATIC_DRAW);
    const color = [1, 3, 5].map(i => parseInt(item.color.slice(i, i + 2), 16) / 255);
    return {category: item.category, color, count: item.count, buffer};
  });
  meshData.length = 0;
  const enabled = new Set([...document.querySelectorAll('#layers input:checked')].map(x => x.value));
  const deployButton = document.getElementById('deploy');
  const laserStatus = document.getElementById('laserStatus');
  let deployTarget = 0, deployProgress = 0, lastFrame = 0, animating = false;
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
      } else if (!enabled.has(mesh.category)) continue;
      gl.bindBuffer(gl.ARRAY_BUFFER, mesh.buffer);
      gl.vertexAttribPointer(attributes.pos, 3, gl.FLOAT, false, 24, 0);
      gl.vertexAttribPointer(attributes.norm, 3, gl.FLOAT, false, 24, 12);
      gl.uniform3fv(uniforms.color, mesh.color);
      gl.uniform1f(uniforms.lift, mesh.category === 'laser_turret' ? (deployProgress-1)*4.3 : 0);
      gl.drawArrays(gl.TRIANGLES, 0, mesh.count);
    }
  }
  function animate(timestamp) {
    const step = lastFrame ? Math.min((timestamp-lastFrame)/800, .1) : 0;
    lastFrame = timestamp;
    deployProgress += Math.sign(deployTarget-deployProgress) *
      Math.min(Math.abs(deployTarget-deployProgress), step);
    draw();
    if (Math.abs(deployTarget-deployProgress) > .001) requestAnimationFrame(animate);
    else {
      deployProgress = deployTarget; animating = false; lastFrame = 0;
      laserStatus.textContent = deployTarget ? 'Four turrets raised' : 'Flush hatches closed';
      draw();
    }
  }
  deployButton.addEventListener('click', () => {
    deployTarget = deployTarget ? 0 : 1;
    deployButton.textContent = deployTarget ? 'Retract four lasers' : 'Deploy four lasers';
    deployButton.setAttribute('aria-pressed', String(Boolean(deployTarget)));
    laserStatus.textContent = deployTarget ? 'Hatches open; turrets rising' : 'Turrets lowering; hatches closing';
    if (!animating) { animating = true; requestAnimationFrame(animate); }
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
    from build import main
    main()
