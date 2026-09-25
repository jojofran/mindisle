import numpy as np
from PIL import Image
from pathlib import Path

OUT = Path('/Users/fran/Documents/Code/mindisle/image2blender-runs/water-orb')
RD = OUT / 'renders_procedural'
RD.mkdir(parents=True, exist_ok=True)
W, H = 640, 1384
cx, cy, R = W * 0.5, H * 0.5, 232.0
y, x = np.mgrid[0:H, 0:W]
X = (x - cx) / R
Y = (y - cy) / R
r = np.sqrt(X * X + Y * Y)
inside = np.clip((1.035 - r) / 0.045, 0, 1)
depth = np.sqrt(np.clip(1.0 - r * r, 0, 1))
noise = (0.48 * np.sin(2.2 * X + 1.1 * np.sin(1.7 * Y)) + 0.32 * np.sin(3.6 * Y - 0.8 * X) + 0.20 * np.sin(6.3 * (X + 0.28 * Y)))
noise = (noise - noise.min()) / (noise.max() - noise.min())

bg = np.zeros((H, W, 3), dtype=np.float32)
bg[:] = np.array([0.885, 0.945, 0.962], dtype=np.float32)
bg += 0.010 * np.exp(-((X * 0.52) ** 2 + (Y * 0.28) ** 2))[..., None]
bg += 0.006 * noise[..., None]

t = np.clip(0.30 + 0.48 * r + 0.10 * (noise - 0.5) + 0.06 * depth, 0, 1)
deep = np.array([0.060, 0.27, 0.32])
light = np.array([0.62, 0.84, 0.85])
water = deep[None, None, :] * (1 - t[..., None]) + light[None, None, :] * t[..., None]
lobe = np.exp(-(((X + 0.16) / 0.52) ** 2 + ((Y - 0.05) / 0.42) ** 2) * 1.7)
water *= (1 - 0.23 * lobe[..., None])
water += 0.045 * depth[..., None] * np.array([0.18, 0.22, 0.22])

curve = Y - (0.16 - 0.42 * X + 0.12 * np.sin(2.4 * X))
split = 1.0 / (1.0 + np.exp(-curve / 0.16))
water += (split[..., None] - 0.5) * np.array([0.025, 0.065, 0.070])

f1 = np.exp(-((Y - (0.30 - 0.34 * X + 0.12 * np.sin(2.6 * X))) / 0.17) ** 2) * np.exp(-((X + 0.02) / 0.98) ** 4)
f2 = np.exp(-((Y - (-0.28 + 0.28 * X + 0.10 * np.sin(2.2 * X + 0.7))) / 0.20) ** 2) * np.exp(-((X - 0.02) / 1.02) ** 4)
f3 = np.exp(-((Y - (-0.02 + 0.40 * X + 0.08 * np.sin(3.3 * X))) / 0.27) ** 2) * np.exp(-((X + 0.10) / 0.90) ** 4)
water += f1[..., None] * np.array([0.080, 0.160, 0.170])
water -= f2[..., None] * np.array([0.030, 0.080, 0.090])
water += f3[..., None] * np.array([0.050, 0.105, 0.115])

# Two wide wrapped density fields create the reverse-curving relationship
# without introducing a stroked contour or a logo-like single band.
wrap_a = np.exp(-(((Y - (0.22 - 0.40 * X + 0.10 * np.sin(2.1 * X))) / 0.30) ** 2) - (((X + 0.06) / 0.92) ** 2))
wrap_b = np.exp(-(((Y - (-0.18 + 0.38 * X + 0.12 * np.sin(2.0 * X + 0.5))) / 0.34) ** 2) - (((X - 0.04) / 0.96) ** 2))
water += wrap_a[..., None] * np.array([0.055, 0.105, 0.110])
water -= wrap_b[..., None] * np.array([0.032, 0.075, 0.080])

hi1 = np.exp(-((Y - (0.52 - 0.30 * X + 0.08 * np.sin(2.5 * X))) / 0.12) ** 2) * np.exp(-((X - 0.18) / 0.70) ** 4)
hi2 = np.exp(-((Y - (-0.50 + 0.24 * X + 0.08 * np.sin(2.1 * X))) / 0.14) ** 2) * np.exp(-((X + 0.15) / 0.78) ** 4)
water += hi1[..., None] * np.array([0.050, 0.065, 0.065])
water += hi2[..., None] * np.array([0.028, 0.045, 0.045])

edge = np.exp(-((r - 0.92) / 0.075) ** 2)
angle = np.arctan2(Y, X)
edge_variation = 0.16 + 0.10 * np.sin(2.2 * angle + 0.7) + 0.04 * noise
edge_variation += 0.28 * np.exp(-(((X - 0.52) / 0.42) ** 2 + ((Y + 0.32) / 0.36) ** 2))
edge_variation += 0.20 * np.exp(-(((X + 0.48) / 0.46) ** 2 + ((Y - 0.42) / 0.42) ** 2))
water += (edge * edge_variation)[..., None] * np.array([0.42, 0.60, 0.62])

alpha = np.clip(inside * (0.64 + 0.18 * depth + 0.06 * noise) + edge * 0.06, 0, 0.90)
img = bg * (1 - alpha[..., None]) + np.clip(water, 0, 1) * alpha[..., None]

def point(px, py, color):
    global img
    d2 = (X - px) ** 2 + (Y - py) ** 2
    core = np.exp(-d2 / (2 * 0.027 ** 2))
    halo = np.exp(-d2 / (2 * 0.052 ** 2)) * 0.10
    strength = (core + halo)[..., None] * 0.82
    img = img * (1 - strength) + np.array(color)[None, None, :] * strength

point(-0.40, -0.29, [0.66, 0.87, 0.89])
point(0.38, 0.31, [0.94, 0.68, 0.49])
arr = np.clip(img * 255.0, 0, 255).astype(np.uint8)
Image.fromarray(arr, 'RGB').save(RD / 'still_procedural_source.png')
print(RD / 'still_procedural_source.png')
