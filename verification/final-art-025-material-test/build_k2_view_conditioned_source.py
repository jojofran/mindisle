#!/usr/bin/env python3
"""Author bounded view-conditioned interior source fields for M3 verification only."""
from pathlib import Path
import hashlib
import json
import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'k2-complete-authored-field'
OUT = ROOT / 'k2-view-conditioned-source'
OUT.mkdir(exist_ok=True)
SCALE = 0.004

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def scalar(name):
    return np.asarray(Image.open(SOURCE / name).convert('RGB'), dtype=np.float32)[..., 0] / 255.0

def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)

def blurred(value, radius=30):
    image = Image.fromarray(np.rint(np.clip(value, 0, 1) * 255).astype(np.uint8))
    return np.asarray(image.filter(ImageFilter.GaussianBlur(radius)), dtype=np.float32) / 255.0

def save_signed(name, value):
    encoded = np.rint(np.clip(value / SCALE, -1, 1) * 32767 + 32768).astype(np.uint16)
    rgb = np.stack([encoded >> 8, encoded & 255, np.zeros_like(encoded)], axis=-1).astype(np.uint8)
    path = OUT / name
    Image.fromarray(rgb).save(path)
    disk = np.asarray(Image.open(path).convert('RGB'), dtype=np.float32)
    decoded = (disk[..., 0] * 256 + disk[..., 1] - 32768) / 32767 * SCALE
    return path, decoded

mask = scalar('field-interior-mask.png')
silhouette = scalar('field-silhouette.png')
thickness = scalar('field-thickness.png')
density = scalar('field-density.png')
depth = scalar('field-optical-depth.png')

# Build a distinct view-conditioned source from the low-frequency optical field.
# It is intentionally smaller than the general parallax field and never reaches
# the shell/core exclusion zones.
interior = smooth(8 / 255, 0.34, mask)
shell_safe = smooth(0.84, 0.995, silhouette)
low_frequency = blurred(0.72 * depth / 0.333 + 0.28 * thickness / 0.72)
gx, gy = np.gradient(low_frequency)
gradient_norm = np.sqrt(gx * gx + gy * gy)
direction_x = gx / np.maximum(gradient_norm, 0.002)
direction_y = gy / np.maximum(gradient_norm, 0.002)
material_weight = interior * shell_safe * (0.30 + 0.70 * np.sqrt(np.clip(low_frequency, 0, 1)))
material_weight *= 0.90 + 0.10 * np.clip(density / 0.196, 0, 1)

yaw = np.clip(direction_x * material_weight * 0.003, -SCALE, SCALE)
pitch = np.clip(direction_y * material_weight * 0.003, -SCALE, SCALE)
paths = {}
paths['field-view-yaw.png'], yaw_disk = save_signed('field-view-yaw.png', yaw)
paths['field-view-pitch.png'], pitch_disk = save_signed('field-view-pitch.png', pitch)

protected = (mask <= 8 / 255) | (silhouette == 0)
determinants = []
size = mask.shape[0]
for yaw_angle in (-0.15, 0, 0.15):
    for pitch_angle in (-0.15, 0, 0.15):
        displacement = np.stack([
            yaw_disk * (yaw_angle / 0.15),
            pitch_disk * (pitch_angle / 0.15),
        ], axis=-1)
        dxx = np.gradient(displacement[..., 0], 1 / size, axis=1)
        dxy = np.gradient(displacement[..., 0], 1 / size, axis=0)
        dyx = np.gradient(displacement[..., 1], 1 / size, axis=1)
        dyy = np.gradient(displacement[..., 1], 1 / size, axis=0)
        determinants.append(float(((1 + dxx) * (1 + dyy) - dxy * dyx).min()))

metrics = {
    'protected_max_uv_displacement': float(max(np.abs(yaw_disk[protected]).max(), np.abs(pitch_disk[protected]).max())),
    'max_view_conditioned_uv_displacement': float(max(np.abs(yaw_disk).max(), np.abs(pitch_disk).max())),
    'min_bounded_warp_jacobian_determinant': min(determinants),
    'active_yaw_std': float(yaw_disk[mask > 0.34].std()),
    'active_pitch_std': float(pitch_disk[mask > 0.34].std()),
}
assert metrics['protected_max_uv_displacement'] == 0
assert metrics['min_bounded_warp_jacobian_determinant'] > 0
assert metrics['active_yaw_std'] > 0 and metrics['active_pitch_std'] > 0

sources = [
    'field-interior-mask.png',
    'field-silhouette.png',
    'field-thickness.png',
    'field-density.png',
    'field-optical-depth.png',
]
report = {
    'schema': 'mindisle.k2-view-conditioned-source.v1',
    'status': 'PASS_DISK_READBACK_AND_NONFOLDING__BROWSER_TECHNICAL_PASS__VISUAL_REVIEW_PENDING',
    'scope': 'M3 verification; bounded view-conditioned interior source; shell/core/silhouette frozen',
    'view_domain': {'yaw': [-0.15, 0.15], 'pitch': [-0.15, 0.15], 'units': 'normalized bounded study offsets'},
    'derivation': 'low-frequency optical-depth/thickness gradient, interior mask, shell exclusion and density modulation',
    'encoding': {
        'format': 'RGB PNG, RG big-endian scalar uint16, B unused',
        'decode': '(uint16 - 32768) / 32767 * 0.004',
        'unit': 'UV per normalized bounded view offset',
        'sampling': 'decode neighboring texels before bilinear interpolation',
        'color_space': 'raw numeric data; no sRGB conversion or premultiplication',
    },
    'metrics': metrics,
    'source_sha256': {name: sha(SOURCE / name) for name in sources},
    'files_sha256': {path.name: sha(path) for path in sorted(OUT.glob('*.png'))},
    'limitations': [
        'bounded source study only; not arbitrary free-view recovery',
        'single-view signed residual still mixes reflection/scatter/film',
        'no camera rotation, occlusion reconstruction, ProductState, M4 or production migration',
    ],
}
(OUT / 'k2-view-conditioned-source.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(metrics, ensure_ascii=False))
