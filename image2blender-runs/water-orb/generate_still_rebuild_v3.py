import numpy as np
from PIL import Image
from pathlib import Path

OUT = Path('/Users/fran/Documents/Code/mindisle/image2blender-runs/water-orb')
RD = OUT / 'renders_rebuild_v3'
RD.mkdir(parents=True, exist_ok=True)
W, H = 853, 1844
cx, cy, R = 426.5, 925.0, 318.0
y, x = np.mgrid[0:H, 0:W]
X = (x - cx) / R
Y = (y - cy) / R
r = np.sqrt(X * X + Y * Y)
orb = np.clip((1.02 - r) / 0.018, 0, 1)
inside = (r <= 1.0).astype(np.float32)

# Quiet pale blue-white background with a very light center lift.
bg = np.zeros((H, W, 3), np.float32)
bg[:] = [0.885, 0.945, 0.965]
bg += (0.018 * np.exp(-((X * .70) ** 2 + (Y * .42) ** 2)))[..., None]

# Slow water variation, intentionally structured rather than blurred into a flat fill.
noise = 0.55 * np.sin(2.4 * X + 0.5 * np.sin(1.7 * Y)) + 0.30 * np.sin(4.2 * Y - .6 * X) + 0.15 * np.sin(8 * (X + .16 * Y))
noise = (noise - noise.min()) / (noise.max() - noise.min())

# Continuous internal water mass with a broad reverse-curving division.
curve = Y - (0.08 - 0.68 * X + 0.18 * np.sin(2.15 * X))
side = 1 / (1 + np.exp(-curve / .14))
side_a = np.array([.08, .25, .30])
side_b = np.array([.52, .76, .77])
water = side_a[None, None, :] * (1 - side[..., None]) + side_b[None, None, :] * side[..., None]
# Offset mass and a pale counter-mass keep the boundary organic, not logo-like.
dark_mass = np.exp(-(((X + .16) / .60) ** 2 + ((Y + .03) / .50) ** 2) * 1.6)
pale_mass = np.exp(-(((X - .22) / .64) ** 2 + ((Y - .18) / .58) ** 2) * 1.7)
water *= (1 - .17 * dark_mass[..., None])
water += pale_mass[..., None] * np.array([.08, .11, .10])
water += (noise - .5)[..., None] * np.array([.018, .036, .040])

# Three broad internal flow fields; each tapers and fades before the shell edge.
def field(fn, width, fade_x):
    dist = Y - fn(X)
    return np.exp(-(dist / width) ** 2) * np.exp(-((X / fade_x) ** 6))
f1 = field(lambda q: .38 - .34*q + .10*np.sin(2.2*q), .14, 1.0)
f2 = field(lambda q: -.30 + .30*q + .12*np.sin(2.0*q + .7), .18, 1.0)
f3 = field(lambda q: .02 + .44*q + .08*np.sin(3.0*q), .24, .92)
water += f1[..., None] * np.array([.11, .20, .21])
water -= f2[..., None] * np.array([.05, .11, .12])
water += f3[..., None] * np.array([.07, .14, .15])

# A thin but non-uniform water membrane; no complete white ring.
edge = np.exp(-((r - .935) / .052) ** 2)
angle = np.arctan2(Y, X)
edge_dir = .16 + .08*np.sin(2.4*angle + .5)
edge_dir += .24*np.exp(-(((X-.50)/.42)**2 + ((Y+.28)/.40)**2))
edge_dir += .18*np.exp(-(((X+.48)/.48)**2 + ((Y-.38)/.44)**2))
water += edge[..., None] * edge_dir[..., None] * np.array([.40, .60, .63])

# Local soft refraction strips, broader than a line and never isolated white spots.
hi_a = field(lambda q: .52 - .30*q + .10*np.sin(2.0*q), .095, .82)
hi_b = field(lambda q: -.55 + .24*q + .08*np.sin(2.3*q), .12, .88)
water += hi_a[..., None] * np.array([.055, .070, .065])
water += hi_b[..., None] * np.array([.030, .045, .045])

# Composite a translucent volume over the background while keeping the outline complete.
alpha = np.clip(inside * (.50 + .16*np.sqrt(np.clip(1-r*r,0,1)) + .06*(noise-.5)) + edge*.08, 0, .82)
img = bg * (1-alpha[...,None]) + np.clip(water,0,1) * alpha[...,None]

# A readable but broken-up membrane edge: soft, directional, never a uniform ring.
rim_strength = np.clip(edge_dir * edge * 0.55, 0, 0.34)
rim_color = np.array([.62, .82, .83])
img = img * (1-rim_strength[...,None]) + rim_color[None,None,:] * rim_strength[...,None]

# Two small embedded points: matched size and restrained glow.
def point(px, py, col):
    global img
    d2=(X-px)**2+(Y-py)**2
    core=np.exp(-d2/(2*.024**2)); halo=np.exp(-d2/(2*.052**2))*.11
    s=(core+halo)[...,None]*.76
    img=img*(1-s)+np.array(col)[None,None,:]*s
point(-.40,-.30,[.65,.84,.88])
point(.38,.31,[.92,.67,.49])

Image.fromarray(np.clip(img*255,0,255).astype(np.uint8),'RGB').save(RD/'still_source.png')
