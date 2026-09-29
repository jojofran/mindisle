from pathlib import Path
import json
import math
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).parent
OUT = ROOT
W = H = 400
SLICES = 8


def rgba(name):
    return np.asarray(Image.open(ROOT / name).convert('RGBA')).astype(np.float32) / 255.0


def gray(name):
    return np.asarray(Image.open(ROOT / name).convert('L')).astype(np.float32) / 255.0


def save_rgba(path, rgb, alpha):
    arr = np.concatenate([np.clip(rgb, 0, 1), np.clip(alpha[..., None], 0, 1)], axis=2)
    Image.fromarray(np.round(arr * 255).astype(np.uint8), 'RGBA').save(path)


volume = rgba('neutral-water-volume.png')
thickness_rgb = volume.copy()
thickness_rgb = rgba('neutral-thickness.png')
detail = rgba('neutral-water-detail.png')
mask = gray('formal-silhouette-mask.png')
film = rgba('formal-outer-film-crop.png')
base_rgb = volume[..., :3]
base_density = volume[..., 3]
detail_a = detail[..., 3]
# Same semantic conversion used by the M2.1 shader, kept as derived data only.
th = np.clip(0.48 + 0.62 * (thickness_rgb[..., 0] - thickness_rgb[..., 2]) + 0.12 * (thickness_rgb[..., 1] - 0.5), 0.06, 0.94)

# Build a deterministic 8-slice atlas. Alpha is derived from authored mass and a
# depth envelope; thickness is intentionally applied later as a ray extent control.
slices = []
for i in range(SLICES):
    z = (i + 0.5) / SLICES
    centered = np.abs((z - 0.5) * 2.0)
    envelope = np.clip(1.0 - centered, 0.0, 1.0) ** 0.62
    veil = 0.20 + 0.80 * envelope
    # Weak deterministic depth-band decomposition, derived from the source alpha.
    band = 0.90 + 0.10 * np.cos(math.pi * (z - 0.5))
    alpha = np.clip(base_density * mask * veil * band, 0.0, 1.0)
    save_rgba(OUT / f'm2.2-volume-slice-{i:02d}.png', base_rgb, alpha)
    slices.append(np.concatenate([base_rgb, alpha[..., None]], axis=2))

atlas = np.concatenate(slices, axis=1)
Image.fromarray(np.round(np.clip(atlas, 0, 1) * 255).astype(np.uint8), 'RGBA').save(OUT / 'm2.2-volume-slice-atlas.png')

# Density montage for human review.
thumbs = []
for i, sl in enumerate(slices):
    a = np.round(sl[..., 3] * 255).astype(np.uint8)
    im = Image.fromarray(a, 'L').convert('RGB')
    im = im.resize((200, 200), Image.Resampling.BILINEAR)
    draw = ImageDraw.Draw(im)
    draw.rectangle((0, 0, 199, 24), fill=(16, 51, 57))
    draw.text((8, 6), f'z{i}  {((i + .5) / SLICES):.3f}', fill=(232, 250, 250))
    thumbs.append(im)
montage = Image.new('RGB', (800, 400), (16, 51, 57))
for i, im in enumerate(thumbs):
    montage.paste(im, ((i % 4) * 200, (i // 4) * 200))
montage.save(OUT / 'm2.2-z-slice-montage.png')

# CPU mirror of the shader, used only to make deterministic representation evidence.
# It does not stand in for a WebGL runtime pass.
Y, X = np.mgrid[0:H, 0:W]
p = np.stack([(X + 0.5) / W * 2 - 1, (Y + 0.5) / H * 2 - 1], axis=-1)
r2 = np.sum(p * p, axis=-1)
inside = (r2 <= 1.0) * (mask > 0.02)
ray_half = np.sqrt(np.clip(1.0 - r2, 0, 1))
ray_length = 2.0 * ray_half


def atlas_sample(z):
    q = np.clip(z, 0, 1) * (SLICES - 1)
    lo = np.floor(q).astype(np.int32)
    hi = np.minimum(lo + 1, SLICES - 1)
    f = (q - lo)[..., None]
    out = np.empty((H, W, 4), dtype=np.float32)
    for c in range(4):
        a = np.stack([s[..., c] for s in slices], axis=0)
        l = a[lo, Y, X]
        h = a[hi, Y, X]
        out[..., c] = l * (1 - f[..., 0]) + h * f[..., 0]
    return out


def render(samples=12, depth=True, density=True, thick=True, detail_enabled=True):
    accum = np.zeros((H, W, 3), dtype=np.float32)
    trans = np.ones((H, W), dtype=np.float32)
    mid = atlas_sample(np.full((H, W), .5, dtype=np.float32))
    if not depth:
        d = mid[..., 3] if density else np.full((H, W), .24, dtype=np.float32)
        if thick:
            d *= 0.62 + 0.76 * th
        else:
            d *= 1.04
        if detail_enabled:
            d *= 1.0 + detail_a * 0.55
        a = 1.0 - np.exp(-d * 1.35)
        accum = mid[..., :3] * a[..., None]
        trans = 1 - a
    else:
        for j in range(samples):
            z = (j + 0.5) / samples
            # Thickness changes how much of the derived depth envelope is traversed.
            extent = (0.68 + 0.64 * th) if thick else np.full((H, W), 1.0, dtype=np.float32)
            zmap = np.clip(0.5 + (z - 0.5) * extent, 0, 1)
            s = atlas_sample(zmap)
            d = s[..., 3] if density else np.full((H, W), .24, dtype=np.float32)
            if thick:
                d *= 0.62 + 0.76 * th
            else:
                d *= 1.04
            if detail_enabled:
                d *= 1.0 + detail_a * (0.35 + 0.65 * abs(2 * z - 1))
            dt = ray_length / float(samples)
            a = 1.0 - np.exp(-d * (1.10 + 0.70 * th) * dt)
            contrib = trans * a
            accum += s[..., :3] * contrib[..., None]
            trans *= 1.0 - a
    coverage = np.clip(1.0 - trans, 0.0, 1.0)
    col = accum / np.maximum(coverage[..., None], 1e-3)
    # Frozen formal shell contribution, kept intentionally weak and unchanged.
    film_a = film[..., 3] * (0.24 + 0.18 * trans)
    col = col * (1.0 - film_a[..., None] * 0.30) + film[..., :3] * film_a[..., None]
    bg = np.array([0.91, 0.97, 0.97], dtype=np.float32)
    rgb = col * coverage[..., None] + film[..., :3] * film_a[..., None] + bg[None, None, :] * np.clip(1.0 - coverage - film_a, 0.0, 1.0)[..., None]
    rgb[~inside] = bg
    return np.clip(rgb, 0, 1), np.clip(trans, 0, 1), np.clip(1 - trans, 0, 1), np.clip(coverage, 0, 1)


def save_render(name, result):
    rgb, _, _, _ = result
    Image.fromarray(np.round(rgb * 255).astype(np.uint8), 'RGB').save(OUT / name)


renders = {}
for n in (8, 12, 16):
    renders[n] = render(samples=n)
    save_render(f'm2.2-cpu-hero-s{n:02d}.png', renders[n])

for key, kwargs in {
    'depth-off': dict(samples=12, depth=False),
    'density-off': dict(samples=12, density=False),
    'density-on': dict(samples=12, density=True),
    'thickness-off': dict(samples=12, thick=False),
    'thickness-on': dict(samples=12, thick=True),
    'detail-off': dict(samples=12, detail_enabled=False),
    'detail-on': dict(samples=12, detail_enabled=True),
}.items():
    result = render(**kwargs)
    save_render(f'm2.2-cpu-{key}.png', result)

# Ray/debug views use the 12-sample default.
def save_gray(name, img):
    a = np.clip(img, 0, 1)
    a[~inside] = 0
    Image.fromarray(np.round(a * 255).astype(np.uint8), 'L').save(OUT / name)

r12 = renders[12]
save_gray('m2.2-ray-length.png', ray_length / 2.0)
save_gray('m2.2-accumulated-density.png', r12[2])
save_gray('m2.2-final-transmittance.png', r12[1])
save_gray('m2.2-depth-slice-view.png', atlas_sample(np.full((H, W), .5, dtype=np.float32))[..., 3])


def mae(a, b):
    x = np.asarray(Image.open(OUT / a).convert('RGB')).astype(np.float32)
    y = np.asarray(Image.open(OUT / b).convert('RGB')).astype(np.float32)
    d = np.abs(x - y)
    return {'maeRgb': round(float(d.mean()), 4), 'maxRgb': int(d.max()), 'changedPixels': int((d.max(axis=2) > 0).sum())}

metrics = {
    'representation': 'derived-8-slice-density-atlas',
    'sourceFiles': ['neutral-water-volume.png', 'neutral-thickness.png', 'neutral-water-detail.png', 'formal-silhouette-mask.png', 'formal-outer-film-crop.png'],
    'sliceCount': SLICES,
    'sliceAtlas': 'm2.2-volume-slice-atlas.png',
    'sliceMontage': 'm2.2-z-slice-montage.png',
    'ray': {'analyticSphere': True, 'entryExit': True, 'rayLength': '2*sqrt(1-r2)'},
    'accumulation': 'front-to-back Beer-Lambert-style source-over',
    'cpuMirrorOnly': True,
    'sampleAblation': {'s08_vs_s12': mae('m2.2-cpu-hero-s08.png', 'm2.2-cpu-hero-s12.png'), 's12_vs_s16': mae('m2.2-cpu-hero-s12.png', 'm2.2-cpu-hero-s16.png')},
    'ablations': {
        'depthOffOn': mae('m2.2-cpu-depth-off.png', 'm2.2-cpu-hero-s12.png'),
        'densityOffOn': mae('m2.2-cpu-density-off.png', 'm2.2-cpu-density-on.png'),
        'thicknessOffOn': mae('m2.2-cpu-thickness-off.png', 'm2.2-cpu-thickness-on.png'),
        'detailOffOn': mae('m2.2-cpu-detail-off.png', 'm2.2-cpu-detail-on.png')
    },
    'runtime': {'renderer': 'experimental-webgl', 'gpuCapture': 'NOT_REPRODUCED', 'passes': 1, 'framebuffers': 0, 'shaderErrors': 'NOT_REPRODUCED'},
    'shell': 'alpha-aware-frozen',
    'productionDependency': False,
    'm1SourcesModified': False,
}
(OUT / 'm2.2-cpu-evidence.json').write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(metrics, ensure_ascii=False, indent=2))
