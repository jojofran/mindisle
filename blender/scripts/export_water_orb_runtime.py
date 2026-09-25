"""Build a small Unity-compatible water-orb handoff package.

The generated maps are material inputs (thickness, flow, caustics, normal and
emission masks).  They do not contain the supplied reference or a finished
render.  The mesh is a genuine UV sphere so it keeps a real silhouette under
small view changes.
"""
from __future__ import annotations

import json
import math
import shutil
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runtime" / "water_orb"
OUT.mkdir(parents=True, exist_ok=True)
SIZE = 512


def save_gray(path: Path, data: np.ndarray) -> None:
    Image.fromarray(np.uint8(np.clip(data, 0.0, 1.0) * 255.0), "L").save(path)


def save_rgb(path: Path, data: np.ndarray) -> None:
    Image.fromarray(np.uint8(np.clip(data, 0.0, 1.0) * 255.0), "RGB").save(path)


def write_mesh(path: Path, segments: int = 64, rings: int = 32) -> dict[str, int]:
    vertices: list[tuple[float, float, float]] = []
    uvs: list[tuple[float, float]] = []
    faces: list[tuple[int, int, int]] = []
    for j in range(rings + 1):
        v = j / rings
        phi = math.pi * v
        sp, cp = math.sin(phi), math.cos(phi)
        for i in range(segments):
            u = i / segments
            theta = 2.0 * math.pi * u
            st, ct = math.sin(theta), math.cos(theta)
            # A barely perceptible broad deformation keeps the silhouette
            # organic while remaining a reusable, static mesh.
            bulge = 1.0 + 0.025 * math.sin(theta * 2.0) * sp * sp
            vertices.append((bulge * sp * ct, bulge * cp, bulge * sp * st))
            uvs.append((u, 1.0 - v))
    for j in range(rings):
        for i in range(segments):
            a = j * segments + i
            b = j * segments + (i + 1) % segments
            c = (j + 1) * segments + (i + 1) % segments
            d = (j + 1) * segments + i
            if j > 0:
                faces.append((a, b, d))
            if j < rings - 1:
                faces.append((b, c, d))
    with path.open("w", encoding="utf-8") as f:
        f.write("# MindIsle water orb runtime mesh; genuine UV sphere\n")
        f.write("mtllib water_orb.mtl\nusemtl WaterOrb\n")
        for x, y, z in vertices:
            f.write(f"v {x:.7f} {y:.7f} {z:.7f}\n")
        for u, v in uvs:
            f.write(f"vt {u:.7f} {v:.7f}\n")
        for x, y, z in vertices:
            f.write(f"vn {x:.7f} {y:.7f} {z:.7f}\n")
        for a, b, c in faces:
            # OBJ indices are one based; reuse the position index for normal
            # and UV because the sphere is authored as a single continuous
            # surface.
            f.write(f"f {a+1}/{a+1}/{a+1} {b+1}/{b+1}/{b+1} {c+1}/{c+1}/{c+1}\n")
    return {"vertices": len(vertices), "triangles": len(faces)}


def write_material() -> None:
    (OUT / "water_orb.mtl").write_text(
        """# Reusable component maps; no finished screenshot is embedded.
newmtl WaterOrb
Ka 0.08 0.25 0.27
Kd 0.38 0.73 0.75
Ks 0.90 0.96 0.95
Ns 90
d 0.78
map_Kd water_orb_flow_mask.png
map_Bump water_orb_normal.png
""",
        encoding="utf-8",
    )


def write_maps() -> None:
    y, x = np.mgrid[0:SIZE, 0:SIZE].astype(np.float32)
    u, v = x / (SIZE - 1), y / (SIZE - 1)
    px, py = u - 0.5, v - 0.5
    r = np.sqrt(px * px + py * py) / 0.5
    inside = np.clip(1.0 - r * r, 0.0, 1.0)
    sphere_depth = np.sqrt(inside)
    center = np.exp(-((r / 0.82) ** 2))
    # Thickness is an optical body-depth approximation: smooth, radial and
    # view-independent.  It deliberately contains no S-shaped flow path.
    subtle = 0.018 * np.sin(px * 8.0 + py * 5.0) * np.exp(-((r / 1.05) ** 4))
    thickness = np.clip(0.08 + 0.72 * sphere_depth + subtle, 0.0, 1.0)
    save_gray(OUT / "water_orb_thickness.png", thickness)

    # This is a grayscale influence mask, not a vector flow map.  The
    # direction is generated procedurally in the Unity shader.
    s_path = px - 0.12 * np.sin((py + 0.03) * 8.0) + 0.035 * np.sin(py * 17.0)
    s = np.exp(-((s_path / 0.095) ** 2)) * np.exp(-((r / 1.1) ** 6))
    broad = 0.5 + 0.5 * np.sin((px * 4.2 + py * 1.7 + 0.30 * np.sin(py * 5.0)) * math.pi)
    broad *= np.exp(-((r / 1.05) ** 4))
    flow_mask = np.clip(0.08 + 0.52 * broad * (0.35 + 0.65 * center) + 0.42 * s, 0.0, 1.0)
    save_gray(OUT / "water_orb_flow_mask.png", flow_mask)

    # Large warped bands plus a deterministic low-frequency value field.  The
    # field is generated once at a coarse scale and upsampled, so the result
    # has irregular spacing without a visibly repeating fabric pattern.
    rng = np.random.default_rng(1907)
    coarse = Image.fromarray(np.uint8(rng.random((24, 24)) * 255.0), "L")
    value = np.asarray(coarse.resize((SIZE, SIZE), Image.Resampling.BICUBIC), dtype=np.float32) / 255.0
    wx = px + 0.18 * np.sin(py * 4.5) + 0.06 * np.sin(py * 11.0)
    wy = py + 0.12 * np.sin(px * 3.2)
    band = 0.5 + 0.5 * np.sin((wx * 3.2 + wy * 1.9 + value * 0.55) * math.pi)
    detail = 0.5 + 0.5 * np.sin((wx * 8.5 - wy * 5.8 + value * 1.3) * math.pi)
    broken = np.clip((band - 0.45) / 0.42, 0.0, 1.0) * (0.35 + 0.65 * detail)
    caustic = np.clip(broken * (0.35 + 0.65 * center), 0.0, 1.0)
    save_gray(OUT / "water_orb_caustic.png", caustic)

    h = 0.42 * flow_mask + 0.38 * caustic
    dy, dx = np.gradient(h)
    # Subtle tangent-space disturbance; the neutral state stays near (0.5,
    # 0.5, 1.0) so the orb does not become embossed or frosted.
    normal = np.stack((-dx * 0.55, -dy * 0.55, np.ones_like(h)), axis=-1)
    normal /= np.maximum(np.linalg.norm(normal, axis=-1, keepdims=True), 1e-6)
    save_rgb(OUT / "water_orb_normal.png", normal * 0.5 + 0.5)

    rim = np.clip((r - 0.60) / 0.35, 0.0, 1.0) ** 1.8
    warm = np.exp(-(((px - 0.28) / 0.18) ** 2 + ((py + 0.20) / 0.22) ** 2))
    cool = np.exp(-(((px + 0.30) / 0.17) ** 2 + ((py - 0.24) / 0.19) ** 2))
    emission = np.clip(0.16 * rim + 0.80 * warm + 0.45 * cool, 0.0, 1.0)
    save_gray(OUT / "water_orb_emission.png", emission)


def main() -> None:
    mesh_stats = write_mesh(OUT / "water_orb.obj")
    write_material()
    write_maps()
    legacy_flow = OUT / "water_orb_flow.png"
    if legacy_flow.exists():
        legacy_flow.unlink()
    # Preserve the authored Blender source as the editable handoff.  The
    # generated OBJ/maps remain independent and Unity-compatible.
    source = ROOT / "waterball_visual_match.blend"
    if source.exists():
        shutil.copy2(source, OUT / "water_orb.blend")
    gate = {}
    vertices = []
    for line in (OUT / "water_orb.obj").read_text(encoding="utf-8").splitlines():
        if line.startswith("v "):
            vertices.append([float(value) for value in line.split()[1:]])
    points = np.asarray(vertices)
    for name, yaw, pitch in (("front", 0, 0), ("yaw+10", 10, 0), ("yaw-10", -10, 0),
                             ("pitch+10", 0, 10), ("pitch-10", 0, -10),
                             ("yaw+15", 15, 0), ("yaw-15", -15, 0)):
        ya, pi = math.radians(yaw), math.radians(pitch)
        ry = np.array([[math.cos(ya), 0, math.sin(ya)], [0, 1, 0], [-math.sin(ya), 0, math.cos(ya)]])
        rx = np.array([[1, 0, 0], [0, math.cos(pi), -math.sin(pi)], [0, math.sin(pi), math.cos(pi)]])
        # Use scalar component expressions instead of chained matmul; this
        # avoids an Accelerate warning seen on the task host while preserving
        # the same Y-then-X rotation.
        qx = points[:, 0] * math.cos(ya) + points[:, 2] * math.sin(ya)
        qy = points[:, 1]
        qz = -points[:, 0] * math.sin(ya) + points[:, 2] * math.cos(ya)
        projected = np.column_stack((qx, qy * math.cos(pi) - qz * math.sin(pi),
                                     qy * math.sin(pi) + qz * math.cos(pi)))
        span = projected[:, :2].max(0) - projected[:, :2].min(0)
        gate[name] = {"projected_width": round(float(span[0]), 4),
                      "projected_height": round(float(span[1]), 4),
                      "silhouette_ratio": round(float(span[0] / span[1]), 4)}
    (OUT / "runtime_gate.json").write_text(json.dumps({"mesh_view_checks": gate}, indent=2), encoding="utf-8")
    manifest = {
        "asset": "MindIsle WaterOrb",
        "mesh": "water_orb.obj",
        "mesh_stats": mesh_stats,
        "maps": [
            "water_orb_thickness.png",
            "water_orb_flow_mask.png",
            "water_orb_caustic.png",
            "water_orb_normal.png",
            "water_orb_emission.png",
        ],
        "reference_embedded": False,
        "runtime_shader": "WaterOrbRuntime.shader",
        "runtime_gate": "runtime_gate.json",
        "audit": "runtime_audit.json",
        "coordinate_system": "Unity Y-up, object radius 1, front camera +Z",
    }
    (OUT / "runtime_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
