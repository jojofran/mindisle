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

mean = np.sum(base * mask[..., None], axis=(0, 1)) / max(mask.sum(), 1)
teal = np.clip(0.58 * mean + np.array([0.02, 0.10, 0.14]), 0, 1)
deep_teal = np.clip(0.30 * mean + np.array([0.01, 0.05, 0.08]), 0, 1)
mist = np.clip(0.66 * mean + np.array([0.30, 0.35, 0.36]), 0, 1)
white = np.array([0.96, 0.99, 0.98], dtype=np.float32)
warm = np.array([1.00, 0.42, 0.18], dtype=np.float32)

def bezier(points, t):
    p = np.asarray(points, dtype=np.float32)
    a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
    return a[:, None] * p[0] + b[:, None] * p[1] + c[:, None] * p[2] + d[:, None] * p[3]

def curve_distance(points):
    pts = bezier(points, np.linspace(0, 1, 260))
    dx = x[..., None] - pts[:, 0][None, None, :]
    dy = y[..., None] - pts[:, 1][None, None, :]
    return np.sqrt(dx * dx + dy * dy).min(axis=2)

def flow(points, width, opacity, blur=1):
    a = np.exp(-((curve_distance(points) / width) ** 2) * 1.55) * opacity * body
    im = Image.fromarray(np.round(np.clip(a, 0, 1) * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(blur))
    return np.asarray(im).astype(np.float32) / 255.0

def ellipse(cx, cy, sx, sy, angle=0):
    ca, sa = np.cos(angle), np.sin(angle)
    xx = (x - cx) * ca + (y - cy) * sa
    yy = -(x - cx) * sa + (y - cy) * ca
    return np.exp(-((xx / sx) ** 2 + (yy / sy) ** 2) * 1.65) * body

def over(rgb, alpha, color, a):
    a = np.clip(a, 0, 1)
    return rgb * (1 - a[..., None]) + color * a[..., None], alpha + a * (1 - alpha)

# Continuous interior carrier. There are no discrete core/nucleus masks.
rgb = np.clip(base * 0.25 + np.array([0.56, 0.84, 0.86], dtype=np.float32) * 0.75, 0, 1)
alpha = body * 0.34
layers = []
labels = []

# A broad continuous body gives the water somewhere to carry the flow.
body_field = ellipse(-0.04, 0.02, 0.60, 0.45, 0.08) * 0.50
rgb, alpha = over(rgb, alpha, teal, body_field)
layers.append(body_field); labels.append("continuous-body-field")

# Two opposed arcs are the main mass topology; they overlap as sheets instead
# of becoming two isolated dark spots.
specs = [
    ([(-0.88, 0.14), (-0.56, -0.64), (0.12, -0.66), (0.76, -0.12)], 0.19, 0.72, deep_teal, "opposed-arc-A-rear"),
    ([(0.86, 0.18), (0.48, 0.70), (-0.18, 0.68), (-0.78, 0.20)], 0.17, 0.64, teal, "opposed-arc-B-rear"),
    ([(-0.76, -0.28), (-0.24, 0.12), (0.28, 0.44), (0.74, 0.28)], 0.11, 0.60, mist, "cross-flow-mid"),
    ([(-0.72, 0.36), (-0.28, -0.02), (0.26, -0.24), (0.68, -0.52)], 0.075, 0.66, white, "front-sheet-A"),
    ([(-0.60, -0.06), (-0.18, 0.32), (0.28, 0.34), (0.58, 0.58)], 0.050, 0.52, white, "front-sheet-B"),
]
for points, width, opacity, color, label in specs:
    a = flow(points, width, opacity)
    rgb, alpha = over(rgb, alpha, color, a)
    layers.append(a); labels.append(label)

# The frozen detail source only perturbs the continuous sheets; it cannot create
# a new topology because its alpha is sparse.
rgb = np.clip(rgb + detail[..., None] * np.array([0.018, 0.026, 0.030], dtype=np.float32) * body[..., None], 0, 1)

# Frozen film plus a localized anisotropic edge response, avoiding a uniform ring.
edge = np.clip((1 - np.sqrt(sphere)) * 1.7, 0, 1)
direction = np.clip(0.65 + 0.35 * (-0.35 * x - 0.55 * y), 0, 1)
rim = edge * direction * 0.20 * body
rgb, alpha = over(rgb, alpha, white, rim)
layers.append(rim); labels.append("anisotropic-film-rim")
film_a = film[..., 3] * (0.28 + 0.16 * direction)
rgb, alpha = over(rgb, alpha, film[..., :3], film_a)

# Small optical points remain as accents only, not internal nuclei.
for cx, cy, color, opacity, label in [(-0.38, -0.30, teal + np.array([0.02, 0.08, 0.12]), 0.62, "cool-accent"), (0.34, 0.31, warm, 0.96, "warm-accent")]:
    halo = ellipse(cx, cy, 0.13, 0.13) * opacity * 0.58
    core = ellipse(cx, cy, 0.032, 0.032) * opacity
    rgb, alpha = over(rgb, alpha, color, halo)
    rgb, alpha = over(rgb, alpha, white, core)
    layers.append(np.clip(halo + core, 0, 1)); labels.append(label)

out = rgb * alpha[..., None] + bg[None, None, :] * (1 - alpha[..., None])
out[body < 0.01] = bg
save_rgb("m2.2-g3-geometry-spike.png", out)

for i, layer in enumerate(layers, 1):
    Image.fromarray(np.round(np.clip(layer, 0, 1) * 255).astype(np.uint8), "L").save(ROOT / f"m2.2-g3-layer-{i:02d}.png")

hero = Image.open(ROOT / "m2.2-g3-geometry-spike.png").convert("RGB")
mont = Image.new("RGB", (1024, 768), (232, 246, 247))
mont.paste(hero, (0, 0))
for i, layer in enumerate(layers):
    tile = Image.fromarray(np.round(np.clip(layer, 0, 1) * 255).astype(np.uint8), "L").convert("RGB").resize((128, 128))
    mont.paste(tile, (512 + (i % 4) * 128, (i // 4) * 128))
mont.save(ROOT / "m2.2-g3-layer-montage.png")

inside = body > 0.05
safe = np.nan_to_num(out, nan=0.0, posinf=1.0, neginf=0.0)
lum = safe[..., 0] * 0.2126 + safe[..., 1] * 0.7152 + safe[..., 2] * 0.0722
gx = np.abs(np.diff(lum, axis=1)); gy = np.abs(np.diff(lum, axis=0))
gradient = np.sqrt(gx[:-1, :] ** 2 + gy[:, :-1] ** 2)
metric = {
    "representation": "geometry-alternative-spike-g3",
    "carrier": "continuous body field + 2 opposed curved arcs + 3 ordered flow sheets + anisotropic film rim + optical accents",
    "discreteCoreCount": 0,
    "sourcePalette": "derived from neutral-water-volume.rgb",
    "layers": len(layers),
    "luminanceStdInside": float(lum[inside].std()),
    "p95Gradient": float(np.percentile(gradient[inside[:-1, :-1]], 95)),
    "warmRBMax": float(np.max((out[..., 0] - out[..., 2])[inside])),
    "coolBRMax": float(np.max((out[..., 2] - out[..., 0])[inside])),
    "m1SourcesModified": False,
    "productionDependency": False,
    "visualStatus": "AWAITING_HUMAN_REVIEW",
}
(ROOT / "m2.2-g3-geometry-evidence.json").write_text(json.dumps(metric, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(metric, ensure_ascii=False, indent=2))
