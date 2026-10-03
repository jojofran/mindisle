#!/usr/bin/env python3
"""Author inferred 2.5D interior displacement bases, not camera-view recovery."""
from pathlib import Path
import hashlib
import json
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'k2-complete-authored-field'
OUT = ROOT / 'k2-parallax-field'
OUT.mkdir(exist_ok=True)
SCALE = 0.08

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def scalar(name):
    return np.asarray(Image.open(SOURCE / name).convert('RGB'), dtype=float)[..., 0] / 255

def smooth(a, b, x):
    t = np.clip((x-a)/(b-a), 0, 1)
    return t*t*(3-2*t)

def save_basis(name, vector, axis):
    # RG = signed scalar in unsigned 16-bit storage; no alpha/premultiplication.
    n = np.rint(np.clip(vector[..., axis]/SCALE, -1, 1)*32767+32768).astype(np.uint16)
    rgb = np.stack([n >> 8, n & 255, np.zeros_like(n)], axis=-1).astype(np.uint8)
    Image.fromarray(rgb).save(OUT / name)
    v = np.asarray(Image.open(OUT / name).convert('RGB'), dtype=float)
    decoded = (v[..., 0]*256+v[..., 1]-32768)/32767*SCALE
    result = np.zeros_like(vector)
    result[..., axis] = decoded
    return result

mask = scalar('field-interior-mask.png')
thickness = scalar('field-thickness.png')
density = scalar('field-density.png')
sil = scalar('field-silhouette.png')
# All depth placement is an authored inference. Avoid a single flat shift:
# thicker water has greater parallax; cloudy density modulates it slightly.
weight = smooth(8/255, .35, mask) * smooth(.85, .99, sil)
lever = .007 * weight * (.30 + .70*np.sqrt(thickness)) * (.9 + .1*density)
zeros = np.zeros_like(lever)
yaw = save_basis('field-parallax-horizontal.png', np.stack([lever, zeros], axis=-1), 0)
pitch = save_basis('field-parallax-vertical.png', np.stack([zeros, -lever], axis=-1), 1)
protected = (mask <= 8/255) | (sil == 0)
determinants = []
size = mask.shape[0]
for a in [-1, 0, 1]:
    for b in [-1, 0, 1]:
        disp = yaw*a + pitch*b
        dxdy, dxdx = np.gradient(disp[..., 0], 1/size)
        dydy, dydx = np.gradient(disp[..., 1], 1/size)
        determinants.append(float(((1+dxdx)*(1+dydy)-dxdy*dydx).min()))
metrics = {
    'protected_max_uv_displacement': float(max(np.abs(yaw[protected]).max(), np.abs(pitch[protected]).max())),
    'max_basis_uv_displacement': float(max(np.linalg.norm(yaw, axis=-1).max(), np.linalg.norm(pitch, axis=-1).max())),
    'min_corner_warp_jacobian_determinant': min(determinants),
    'active_horizontal_displacement_std': float(yaw[..., 0][mask>.35].std()),
}
assert metrics['protected_max_uv_displacement'] == 0
assert metrics['min_corner_warp_jacobian_determinant'] > 0
assert metrics['active_horizontal_displacement_std'] > 0
sources = ['field-interior-mask.png', 'field-thickness.png', 'field-density.png', 'field-silhouette.png']
report = {
    'schema': 'mindisle.k2-interior-parallax-field.v1',
    'status': 'PASS_DISK_READBACK_AND_NONFOLDING__VISUAL_REVIEW_PENDING',
    'scope': 'M3 verification; inferred depth-aware internal parallax; fixed front camera',
    'derivation': 'thickness-dependent lever, density modulation and smooth core/shell exclusion',
    'encoding': {'format':'RGB PNG, RG big-endian scalar uint16, B unused; horizontal=X, vertical=Y',
                 'decode':'(uint16 - 32768) / 32767 * 0.08', 'unit':'UV per normalized parallax control',
                 'color_space':'raw numeric data; no sRGB conversion or premultiplication',
                 'sampling':'decode neighboring texels before bilinear interpolation'},
    'metrics': metrics,
    'source_sha256': {n:sha(SOURCE/n) for n in sources},
    'files_sha256': {p.name:sha(p) for p in sorted(OUT.glob('*.png'))},
    'limitations': ['inferred single-view 2.5D depth placement, not recovered 3D volume',
                    'no camera rotation, occlusion reconstruction or view-dependent lighting',
                    'signed optical residual remains baked; do not warp it beyond bounded study',
                    'no M4, ProductState, core movement, formation or production changes'],
}
(OUT/'k2-parallax-field.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
print(json.dumps(metrics))
