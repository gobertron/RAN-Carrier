#!/usr/bin/env python3
"""Embed the original Australis mesh in an offline WebGL preview."""
from collections import defaultdict
from pathlib import Path
import base64
import json
import struct

import numpy as np


def category(name):
    if name.startswith(("CatapultTrack", "CatapultDeckGuide")):
        return "catapults"
    if name.startswith(("DeckEdgeLift", "LiftEdge")):
        return "lifts"
    if name.startswith(("AftVTOL", "AftSpot")):
        return "spots"
    if name.startswith(("AngledLanding", "LandingCentreline", "ArrestingWire")):
        return "recovery"
    if name.startswith(("MainRaked", "IntegratedBridge", "BridgeWindow",
                        "EnclosedSensor", "IntegratedRadar", "ShipboardECM",
                        "AftAviation", "AftEnclosed")):
        return "islands"
    if name.startswith(("Laser", "OutboardFairing", "DefensiveHatch",
                        "BowSonarFairing")):
        return "equipment"
    return "hull"


def build_viewer(mesh, colors, path):
    groups = defaultdict(list)
    for name, triangle, material in mesh.triangles():
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
    path.write_text(TEMPLATE.replace("__MESH_DATA__", json.dumps(payload, separators=(",", ":"))))
    return len(payload), sum(part["count"] // 3 for part in payload)


TEMPLATE = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Australis 2030 — interactive 3D design preview</title>
<style>
  :root { color-scheme: dark; font-family: system-ui, sans-serif; background: #101c27; color: #e8f1f1; }
  * { box-sizing: border-box; }
  body { margin: 0; min-height: 100vh; display: grid; grid-template-columns: minmax(220px, 285px) 1fr; }
  aside { background: #172a36; border-right: 1px solid #36505d; padding: 24px; z-index: 1; }
  h1 { font-size: 1.58rem; margin: 0 0 4px; line-height: 1.13; letter-spacing: .025em; }
  .eyebrow { font-size: .7rem; letter-spacing: .15em; color: #87bfc4; font-weight: 700; margin-bottom: 16px; }
  .muted { color: #b0c4cb; font-size: .86rem; line-height: 1.48; }
  .pill { display: inline-block; padding: 5px 9px; border: 1px solid #7ca6a6; border-radius: 100px; color: #a9dbd8; font-size: .72rem; letter-spacing: .06em; margin: 13px 0 24px; }
  h2 { font-size: .72rem; color: #82bfc5; text-transform: uppercase; letter-spacing: .13em; margin: 20px 0 9px; }
  .buttons { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 7px; }
  button { color: #e1edef; background: #263e4c; border: 1px solid #496572; border-radius: 7px; padding: 9px; font: inherit; font-size: .82rem; cursor: pointer; }
  button:hover, button:focus-visible, button.active { background: #32626b; border-color: #8fcdcc; }
  label { display: flex; align-items: center; gap: 9px; margin: 8px 0; font-size: .84rem; cursor: pointer; }
  input[type=checkbox] { accent-color: #7fd1cf; width: 16px; height: 16px; }
  .footer { margin-top: 23px; border-top: 1px solid #35505c; padding-top: 14px; }
  a { color: #a8e3e0; }
  main { position: relative; min-width: 0; height: 100vh; overflow: hidden; background: radial-gradient(ellipse at 54% 40%, #263f50 0%, #152734 55%, #101b27 100%); }
  canvas { display: block; width: 100%; height: 100%; cursor: grab; touch-action: none; }
  canvas:active { cursor: grabbing; }
  .hint { position: absolute; bottom: 18px; left: 20px; padding: 9px 12px; border-radius: 7px; color: #c6d8d8; background: #11212cbb; font-size: .8rem; pointer-events: none; }
  .bow { position: absolute; top: 22px; right: 22px; padding: 7px 10px; background: #152a37bb; border: 1px solid #51747c; border-radius: 5px; font-size: .78rem; pointer-events: none; }
  #error { position: absolute; top: 30%; left: 15%; right: 15%; text-align: center; background: #3f2730; padding: 22px; display: none; }
  @media (max-width: 700px) { body { grid-template-columns: 1fr; grid-template-rows: auto minmax(380px, 68vh); } aside { padding: 17px; } main { height: 68vh; } .buttons { grid-template-columns: repeat(4, 1fr); } .footer { margin-top: 12px; } }
</style>
</head>
<body>
<aside>
  <div class="eyebrow">ROYAL AUSTRALIAN NAVY · DESIGN STUDY</div>
  <h1>Australis 2030</h1>
  <div class="muted">Twin-island carrier · 370 m overall · 104 m deck beam · 99 aircraft target</div>
  <span class="pill">ORIGINAL CONCEPT MESH</span>
  <h2>Camera</h2>
  <div class="buttons" id="views">
    <button type="button" data-view="perspective" class="active">Perspective</button>
    <button type="button" data-view="top">Deck / top</button>
    <button type="button" data-view="starboard">Starboard</button>
    <button type="button" data-view="bow">Bow</button>
  </div>
  <h2>Show parts</h2>
  <div id="layers">
    <label><input type="checkbox" value="hull" checked> Hull and flight deck</label>
    <label><input type="checkbox" value="islands" checked> Two islands and radar</label>
    <label><input type="checkbox" value="catapults" checked> Three catapults</label>
    <label><input type="checkbox" value="lifts" checked> Four deck-edge lifts</label>
    <label><input type="checkbox" value="spots" checked> Four VTOL / helicopter spots</label>
    <label><input type="checkbox" value="recovery" checked> Angled recovery lane</label>
    <label><input type="checkbox" value="equipment" checked> Other equipment</label>
  </div>
  <div class="footer muted">Drag to rotate. Scroll or pinch to zoom. The mesh is a design preview; deck operations and Sea Power integration have not been tested.<br><br>
    <a href="../model/source/ran_cvn_australis_2030.obj" download>Download OBJ mesh</a> ·
    <a href="../model/source/ran_cvn_australis_2030.mtl" download>Materials</a>
  </div>
</aside>
<main>
  <canvas id="scene" aria-label="Rotatable three-dimensional Australis carrier model"></canvas>
  <div class="bow">BOW → +Z</div>
  <div class="hint">Drag to orbit · wheel / pinch to zoom</div>
  <div id="error" role="alert"></div>
</main>
<script>
"use strict";
const meshData = __MESH_DATA__;
const canvas = document.getElementById("scene");
const gl = canvas.getContext("webgl", {antialias: true});
const errorBox = document.getElementById("error");
if (!gl) {
  errorBox.textContent = "WebGL is unavailable in this browser. The OBJ download can be opened in Blender.";
  errorBox.style.display = "block";
} else {
  const vertexShader = `attribute vec3 position; attribute vec3 normal;
    uniform mat4 projection; uniform mat4 view;
    varying float light;
    void main() {
      vec3 sun = normalize(vec3(-0.38, 0.86, 0.42));
      light = 0.51 + 0.49 * abs(dot(normalize(normal), sun));
      gl_Position = projection * view * vec4(position, 1.0);
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
  const uniforms = {projection: gl.getUniformLocation(program, "projection"), view: gl.getUniformLocation(program, "view"), color: gl.getUniformLocation(program, "color")};
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
  let azimuth = -2.48, elevation = 0.48, distance = 540, top = false;
  const target = [0, 19, 0];
  function normalize(a) { const l = Math.hypot(...a); return a.map(x => x / l); }
  function cross(a,b) { return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]; }
  function lookAt(eye, target, up) {
    const z = normalize(eye.map((v, i) => v - target[i]));
    const x = normalize(cross(up, z));
    const y = cross(z, x);
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
    gl.uniformMatrix4fv(uniforms.view, false, lookAt(eye, target, top ? [1,0,0] : [0,1,0]));
    gl.enableVertexAttribArray(attributes.pos);
    gl.enableVertexAttribArray(attributes.norm);
    for (const mesh of meshes) {
      if (!enabled.has(mesh.category)) continue;
      gl.bindBuffer(gl.ARRAY_BUFFER, mesh.buffer);
      gl.vertexAttribPointer(attributes.pos, 3, gl.FLOAT, false, 24, 0);
      gl.vertexAttribPointer(attributes.norm, 3, gl.FLOAT, false, 24, 12);
      gl.uniform3fv(uniforms.color, mesh.color);
      gl.drawArrays(gl.TRIANGLES, 0, mesh.count);
    }
  }
  document.querySelectorAll('#layers input').forEach(input => input.addEventListener('change', () => {
    if (input.checked) enabled.add(input.value); else enabled.delete(input.value);
    draw();
  }));
  document.getElementById('views').addEventListener('click', event => {
    const button = event.target.closest('button[data-view]'); if (!button) return;
    document.querySelectorAll('#views button').forEach(x => x.classList.toggle('active', x === button));
    const view = button.dataset.view;
    top = view === 'top';
    if (view === 'perspective') { azimuth=-2.48; elevation=.48; distance=540; }
    if (view === 'top') distance=520;
    if (view === 'starboard') { azimuth=Math.PI/2; elevation=.20; distance=530; }
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
      if (top) { top=false; azimuth=-2.48; elevation=1.35; }
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
  draw();
}
</script>
</body>
</html>
'''


if __name__ == "__main__":
    import sys
    sys.dont_write_bytecode = True
    from build import geometry, COLORS
    target = Path(__file__).resolve().parent / "viewer/australis_2030_3d.html"
    parts, triangles = build_viewer(geometry(), COLORS, target)
    print(f"[OK] {target} ({parts} colored groups, {triangles} triangles)")
