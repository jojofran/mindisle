from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).parent
W = H = 512

def load(name):
    return np.asarray(Image.open(ROOT / name).convert("RGBA").resize((W, H), Image.Resampling.LANCZOS)).astype(np.float32) / 255.0

def save_rgb(name, arr):
    Image.fromarray(np.round(np.clip(arr, 0, 1) * 255).astype(np.uint8), "RGB").save(ROOT / name)

bg = np.array([0.91, 0.965, 0.97], dtype=np.float32)
volume = load("neutral-water-volume.png")
mask = np.clip(load("formal-silhouette-mask.png")[..., 0], 0, 1)
film = load("formal-outer-film-crop.png")
detail = load("neutral-water-detail.png")[..., 3]
base = volume[..., :3]
Y, X = np.mgrid[0:H, 0:W]
x = X / (W - 1) * 2 - 1
y = Y / (H - 1) * 2 - 1
sphere = np.clip(1 - x * x - y * y, 0, 1)
body = np.clip(mask, 0, 1) * np.sqrt(sphere)

# Palette is derived from frozen neutral-water-volume RGB. Warm/cool roles are
# geometry-route hypotheses, not new M1 source pixels.
mean = np.sum(base * mask[..., None], axis=(0, 1)) / max(mask.sum(), 1)
cool = np.clip(0.52 * mean + np.array([0.04, 0.13, 0.20]), 0, 1)
deep = np.clip(0.18 * mean + np.array([0.01, 0.04, 0.07]), 0, 1)
milky = np.clip(0.62 * mean + np.array([0.34, 0.39, 0.40]), 0, 1)
warm = np.array([0.98, 0.56, 0.32], dtype=np.float32)
warm_soft = np.array([0.96, 0.62, 0.38], dtype=np.float32)

def ellipse(cx, cy, sx, sy, angle=0.0):
    ca, sa = np.cos(angle), np.sin(angle)
    xx = (x - cx) * ca + (y - cy) * sa
    yy = -(x - cx) * sa + (y - cy) * ca
    return np.exp(-((xx / sx) ** 2 + (yy / sy) ** 2) * 2.0) * body

def bezier(points, t):
    p = np.asarray(points, dtype=np.float32)
    a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
    return a[:, None] * p[0] + b[:, None] * p[1] + c[:, None] * p[2] + d[:, None] * p[3]

def curve_distance(points):
    ts = np.linspace(0, 1, 240)
    pts = bezier(points, ts)
    dx = x[..., None] - pts[:, 0][None, None, :]
    dy = y[..., None] - pts[:, 1][None, None, :]
    return np.sqrt(dx * dx + dy * dy).min(axis=2)

def ribbon(points, width, alpha, blur=0):
    a = np.exp(-((curve_distance(points) / width) ** 2) * 2.0) * alpha * body
    if blur:
        im = Image.fromarray(np.round(a * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(blur))
        a = np.asarray(im).astype(np.float32) / 255.0
    return np.clip(a, 0, 1)

def over(rgb, alpha, color, a):
    a = np.clip(a, 0, 1)
    return rgb * (1 - a[..., None]) + color * a[..., None], alpha + a * (1 - alpha)

rgb = np.clip(base * 0.30 + np.array([0.52, 0.82, 0.84], dtype=np.float32) * 0.70, 0, 1)
alpha = body * 0.22
layers = []
layer_meta = []

# Independent, opposed mass bands; their separation is part of the route test.
mass_a = np.clip(ellipse(-0.25, -0.16, 0.47, 0.18, -0.32) * 0.72 + ellipse(-0.02, -0.03, 0.28, 0.13, -0.28) * 0.28, 0, 1)
mass_b = np.clip(ellipse(0.24, 0.20, 0.44, 0.19, 0.36) * 0.68 + ellipse(0.03, 0.09, 0.25, 0.12, 0.34) * 0.32, 0, 1)
rgb, alpha = over(rgb, alpha, deep, mass_a * 0.88)
layers.append(mass_a * 0.88); layer_meta.append("mass-A-front-left")
rgb, alpha = over(rgb, alpha, cool, mass_b * 0.78)
layers.append(mass_b * 0.78); layer_meta.append("mass-B-rear-right")

# A broad central body keeps the opposed bands embedded in water rather than
# reading as detached graphic strokes.
central = ellipse(-0.02, 0.02, 0.38, 0.30, 0.08) * 0.58
rgb, alpha = over(rgb, alpha, cool * 0.78 + milky * 0.22, central)
layers.append(central); layer_meta.append("central-cyan-body")

sheet_specs = [
    ([(-0.78, -0.34), (-0.45, -0.72), (0.12, -0.47), (0.68, 0.02)], 0.16, 0.54, deep, "rear-arc-A"),
    ([(0.76, 0.36), (0.38, 0.70), (-0.18, 0.47), (-0.68, 0.08)], 0.18, 0.50, cool, "rear-arc-B"),
    ([(-0.68, 0.34), (-0.24, 0.00), (0.18, -0.10), (0.66, -0.42)], 0.060, 0.74, milky, "front-flow-A"),
    ([(-0.56, -0.02), (-0.18, 0.22), (0.24, 0.36), (0.54, 0.56)], 0.035, 0.78, milky, "front-flow-B"),
]
for pts, width, a, color, label in sheet_specs:
    aa = ribbon(pts, width, a, 2)
    rgb, alpha = over(rgb, alpha, color, aa)
    layers.append(aa); layer_meta.append(label)

rgb = np.clip(rgb + detail[..., None] * np.array([0.02, 0.03, 0.035], dtype=np.float32) * body[..., None], 0, 1)
film_a = film[..., 3] * (0.30 + 0.20 * np.clip(1 - sphere, 0, 1))
rgb, alpha = over(rgb, alpha, film[..., :3], film_a)

# Compact cool and warm points are added after the film wash so their colour
# roles remain legible in the same places as the reference vocabulary.
for color, a, label, cx, cy in [
    (cool + np.array([0.04, 0.08, 0.11]), 0.78, "cool-point", -0.38, -0.30),
    (warm_soft, 0.98, "warm-point", 0.34, 0.31),
]:
    halo = ellipse(cx, cy, 0.16, 0.16) * a * 0.62
    core = ellipse(cx, cy, 0.050, 0.050) * a
    rgb, alpha = over(rgb, alpha, color, halo)
    rgb, alpha = over(rgb, alpha, np.array([1.0, 0.98, 0.90], dtype=np.float32), core)
    layers.append(np.clip(halo + core, 0, 1)); layer_meta.append(label)
out = rgb * alpha[..., None] + bg[None, None, :] * (1 - alpha[..., None])
out[body < 0.01] = bg
save_rgb("m2.2-g2-geometry-spike.png", out)

for i, layer in enumerate(layers, 1):
    Image.fromarray(np.round(np.clip(layer, 0, 1) * 255).astype(np.uint8), "L").save(ROOT / f"m2.2-g2-layer-{i:02d}.png")

hero = Image.open(ROOT / "m2.2-g2-geometry-spike.png").convert("RGB")
mont = Image.new("RGB", (1024, 768), (232, 246, 247))
mont.paste(hero.resize((512, 512)), (0, 0))
for i, layer in enumerate(layers):
    tile = Image.fromarray(np.round(np.clip(layer, 0, 1) * 255).astype(np.uint8), "L").convert("RGB").resize((128, 128))
    mont.paste(tile, (512 + (i % 4) * 128, (i // 4) * 128))
mont.save(ROOT / "m2.2-g2-layer-montage.png")

inside = body > 0.05
safe = np.nan_to_num(out, nan=0.0, posinf=1.0, neginf=0.0)
lum = safe[..., 0] * 0.2126 + safe[..., 1] * 0.7152 + safe[..., 2] * 0.0722
gradx = np.abs(np.diff(lum, axis=1))
grady = np.abs(np.diff(lum, axis=0))
gradient = np.sqrt(gradx[:-1, :] ** 2 + grady[:, :-1] ** 2)
metric = {
    "representation": "geometry-alternative-spike-g2",
    "carrier": "analytic sphere + 2 opposed curved mass bands + 4 ordered sheets + compact warm/cool points",
    "sourcePalette": "derived from neutral-water-volume.rgb",
    "layers": len(layers),
    "luminanceStdInside": float(lum[inside].std()),
    "meanGradient": float((gradx.mean() + grady.mean()) * 0.5),
    "p95Gradient": float(np.percentile(gradient[inside[:-1, :-1]], 95)),
    "massACoverageInside": float(np.mean((mass_a > 0.20)[inside])),
    "massBCoverageInside": float(np.mean((mass_b > 0.20)[inside])),
    "warmRBMax": float(np.max((out[..., 0] - out[..., 2])[inside])),
    "coolBRMax": float(np.max((out[..., 2] - out[..., 0])[inside])),
    "warmPointCenter": [0.34, 0.31],
    "coolPointCenter": [-0.38, -0.30],
    "m1SourcesModified": False,
    "productionDependency": False,
    "visualStatus": "AWAITING_HUMAN_REVIEW",
    "gate": {
        "luminanceStdMin": 0.08,
        "p95GradientMin": 0.010,
        "warmRBMin": 0.08,
        "coolBRMin": 0.08,
        "passed": False,
        "failed": ["luminanceStdInside", "p95Gradient"],
        "blocker": "VOLUME_CONSTRUCTION",
    },
}
(ROOT / "m2.2-g2-geometry-evidence.json").write_text(json.dumps(metric, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(metric, ensure_ascii=False, indent=2))
