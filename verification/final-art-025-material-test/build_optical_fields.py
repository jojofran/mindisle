#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reference-directed, single-view optical appearance study, not M2 closure.

025 is an offline donor only. The renderer samples separately derived optical
depth, reflected light, M1 thickness/detail, silhouette and formal film maps.
The absorption/reflection split is inferred, not measured physical truth.
"""
from pathlib import Path
import json
import hashlib
import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
M1 = ROOT / 'verification/continuous-water-prototype'
INPUTS = OUT / 'inputs'
REF = INPUTS / 'final-art-025.png'
N = 400
VIEW = 360
RADIUS = 140
FIELD_RADIUS = 176
BG = np.array([234, 241, 243], dtype=np.float64) / 255
NEUTRAL_REVIEW_BG = np.array([154, 166, 170], dtype=np.float64) / 255
PRIMARY_025_DEPTH_REDUCTION = .34
SHELL_REFLECTION_ESTIMATE = .24
CALIBRATED_SCATTER_STRENGTH = .11
# Follow-up correction requested after Cycle 2: soften the large internal
# shadow that makes the sphere read as a concave bowl. This remains a field
# calibration; it is deliberately separate from the preserved 025 candidate.
SPHERE_RELIEF_DEPTH_REDUCTION = .20
SPHERE_RELIEF_SCATTER_STRENGTH = .095
SPHERE_RELIEF_SHADOW_DEPTH_REDUCTION = .10
SPHERE_RELIEF_SHADOW_SCATTER_STRENGTH = .075
SIMPLE_SHELL_FILM_STRENGTH = .25
REFERENCE_SOFT_SCATTER_STRENGTH = .06
REFERENCE_SOFT_FILM_STRENGTH = .15
REFERENCE_SOFT_REFRACTION_SCALE = 25
REFERENCE_SOFT_TOP_BLUR_RADIUS = 24
REFERENCE_SIDE_FILM_STRENGTH = .05
REFERENCE_SIDE_REFLECTION_STRENGTH = .50
REFERENCE_CORNER_FILM_STRENGTH = 0.0
REFERENCE_CORNER_REFLECTION_STRENGTH = 0.0
REFERENCE_CORNER_OPTICAL_STRENGTH = 1.0
REFERENCE_CORNER_SCATTER_STRENGTH = 1.0
REFERENCE_CORNER_ALPHA_STRENGTH = .75
REFERENCE_CORNER_MASK_BLUR_RADIUS = 10
REFERENCE_UPPER_FILM_STRENGTH = 0.0
REFERENCE_UPPER_REFLECTION_STRENGTH = 0.0
REFERENCE_UPPER_OPTICAL_STRENGTH = .75
REFERENCE_UPPER_SCATTER_STRENGTH = .75
REFERENCE_UPPER_MASK_BLUR_RADIUS = 10
REFERENCE_UPPER_CHROMA_NEUTRALIZE_STRENGTH = .75
REFERENCE_LEFT_SHADOW_DEPTH_REDUCTION = .75
REFERENCE_LEFT_SHADOW_SCATTER_FILL = .05
REFERENCE_LEFT_SHADOW_MASK_BLUR_RADIUS = 4
# Presentation-only follow-up: soften the over-bright shell/readout that
# disappears into light review backgrounds. Fields and silhouette stay frozen.
REFERENCE_HIGHLIGHT_SOFT_REFLECTION = .55
REFERENCE_HIGHLIGHT_SOFT_FILM = .30
REFERENCE_HIGHLIGHT_SOFT_SCATTER = .85

def srgb_to_linear(x):
    return np.where(x <= .04045, x / 12.92, ((x + .055) / 1.055) ** 2.4)

def linear_to_srgb(x):
    x = np.maximum(x, 0)
    return np.where(x <= .0031308, x * 12.92, 1.055 * x ** (1 / 2.4) - .055)

def blur(a, r):
    return np.asarray(Image.fromarray(np.uint8(np.clip(a, 0, 1)*255)).filter(ImageFilter.GaussianBlur(r)), dtype=np.float64)/255

def save_rgb(name, x):
    Image.fromarray(np.uint8(np.clip(x, 0, 1)*255+.5)).save(OUT/name)

def save_rgba(name, rgb, alpha):
    a = np.dstack([rgb, alpha])
    Image.fromarray(np.uint8(np.clip(a, 0, 1)*255+.5), 'RGBA').save(OUT/name)

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def clean_donor():
    im = np.asarray(Image.open(REF).convert('RGB'), dtype=np.float64)/255
    fallback = np.asarray(Image.open(OUT/'candidate-formal-static-baseline.png').convert('RGB'), dtype=np.float64)/255
    yy, xx = np.mgrid[:360, :360]
    # Remove the entire title/subtitle band; it is UI context, not material.
    mask = (yy < 104)
    for cx, cy, rad in [(138,148,8),(228,210,9),(249,245,11)]:
        mask |= (xx-cx)**2+(yy-cy)**2 < rad**2
    # Harmonic repair uses neighboring donor pixels; no synthesized core/shape.
    repaired = im.copy()
    repaired[mask] = blur(im, 10)[mask]
    for _ in range(360):
        avg = (np.roll(repaired,1,0)+np.roll(repaired,-1,0)+np.roll(repaired,1,1)+np.roll(repaired,-1,1))*.25
        repaired[mask] = avg[mask]
    # Normalize the donor's material region to the unchanged M1 field domain.
    p = Image.fromarray(np.uint8(repaired*255+.5))
    scale = RADIUS / FIELD_RADIUS
    field = p.transform((N,N), Image.Transform.AFFINE,
        (scale,0,180-200*scale,0,scale,180-200*scale),Image.Resampling.BICUBIC)
    data = np.asarray(field,dtype=np.float64)/255
    # The top of 025 is covered by UI text. Preserve a clean authored top cap
    # from the formal static baseline instead of manufacturing a flat fill.
    fallback_img = Image.fromarray(np.uint8(fallback*255+.5))
    fallback_field = fallback_img.transform((N,N), Image.Transform.AFFINE,
        (scale,0,180-200*scale,0,scale,180-200*scale),Image.Resampling.BICUBIC)
    fallback_data = np.asarray(fallback_field,dtype=np.float64)/255
    source_y = (np.arange(N)[:,None] + .5) / scale - (180-200*scale) / scale
    blend = np.clip((source_y - 103) / 24, 0, 1)[...,None]
    target_data = data * blend + fallback_data * (1-blend)
    save_rgb('diagnostic-target-donor-with-formal-cap.png',target_data)
    # Primary study uses the clean, authored formal baseline as the donor. The
    # 025 repair remains a visible diagnostic because its UI crop is ambiguous.
    data = fallback_data
    save_rgb('diagnostic-cleaned-donor.png',data)
    Image.fromarray(np.uint8(mask)*255).save(OUT/'diagnostic-donor-removal-mask.png')
    return data, int(mask.sum()), target_data

def background(kind):
    yy,xx=np.mgrid[:VIEW,:VIEW]
    if kind=='light': return np.broadcast_to(BG,(VIEW,VIEW,3)).copy()
    if kind=='neutral': return np.broadcast_to(NEUTRAL_REVIEW_BG,(VIEW,VIEW,3)).copy()
    if kind=='dark': return np.broadcast_to(np.array([28,49,60])/255,(VIEW,VIEW,3)).copy()
    if kind=='split':
        t=np.clip((xx-145)/70,0,1)[...,None]
        return (1-t)*np.array([224,228,210])/255+t*np.array([193,219,231])/255
    grid=((xx//30+yy//30)%2)[...,None]
    return grid*np.array([211,228,231])/255+(1-grid)*np.array([244,246,235])/255

def sample(a, x, y):
    # Bilinear field sampling, matching GPU clamp-to-edge.
    x=np.clip(x,0,a.shape[1]-1);y=np.clip(y,0,a.shape[0]-1)
    ix=np.floor(x).astype(int);iy=np.floor(y).astype(int)
    jx=np.minimum(ix+1,a.shape[1]-1);jy=np.minimum(iy+1,a.shape[0]-1)
    fx=(x-ix)[...,None];fy=(y-iy)[...,None]
    if a.ndim==2:a=a[...,None]
    return (1-fy)*((1-fx)*a[iy,ix]+fx*a[iy,jx])+fy*((1-fx)*a[jy,ix]+fx*a[jy,jx])

def crop_detail(rgb):
    return np.asarray(Image.fromarray(np.uint8(np.clip(rgb,0,1)*255+.5)).crop((60,60,300,300)).resize((360,360),Image.Resampling.LANCZOS),dtype=np.float64)/255

def read_disk_fields(optical_name='field-optical-depth.png', reflected_name='field-reflected-light.png', scatter_name='field-internal-scatter.png', film_name='field-formal-film.png', refraction_name='field-refraction.png'):
    optical_rgba=np.asarray(Image.open(OUT/optical_name).convert('RGBA'),dtype=np.float64)/255
    reflected=np.asarray(Image.open(OUT/reflected_name).convert('RGB'),dtype=np.float64)/255
    depth=np.asarray(Image.open(OUT/'field-thickness.png').convert('RGB'),dtype=np.float64)/255
    refraction=np.asarray(Image.open(OUT/refraction_name).convert('RGB'),dtype=np.float64)/255
    silhouette=np.asarray(Image.open(OUT/'field-silhouette.png').convert('L'),dtype=np.float64)/255
    film=np.asarray(Image.open(OUT/film_name).convert('RGBA'),dtype=np.float64)/255
    detail=np.asarray(Image.open(OUT/'field-m1-detail.png').convert('RGBA'),dtype=np.float64)/255
    scatter=np.asarray(Image.open(OUT/scatter_name).convert('RGB'),dtype=np.float64)/255
    return {
        'optical':optical_rgba[...,:3],
        'depth':depth[...,0],
        'alpha':np.minimum(optical_rgba[...,3],silhouette),
        'reflected':reflected,
        'offset':refraction[...,:2]*2-1,
        'film':film,
        'detail':detail,
        'scatter':scatter,
        'depth_mean':float(depth[...,0][silhouette>.5].mean()),
    }

def render(maps, kind='light', thickness_mode='spatial', reflection=True, refraction=True, film=True, detail=True, scatter=False, interior_lift=0.0, interior_cool=(0.0,0.0,0.0), reflection_strength=1.0, film_strength=1.0, scatter_strength=1.0):
    yy,xx=np.mgrid[:VIEW,:VIEW]
    fx=(xx+.5-VIEW/2)*FIELD_RADIUS/RADIUS+N/2-.5
    fy=(yy+.5-VIEW/2)*FIELD_RADIUS/RADIUS+N/2-.5
    optical=sample(maps['optical'],fx,fy)
    depth=sample(maps['depth'],fx,fy)[...,0]
    alpha=sample(maps['alpha'],fx,fy)[...,0]
    reflected=sample(maps['reflected'],fx,fy)
    offsets=sample(maps['offset'],fx,fy)*6 if refraction else np.zeros((VIEW,VIEW,2))
    if thickness_mode == 'spatial':
        path=depth
    elif thickness_mode == 'constant':
        path=np.full_like(depth,.04)
    elif thickness_mode == 'mean_match':
        path=np.full_like(depth,maps['depth_mean'])
    else:
        raise ValueError(f'unknown thickness_mode: {thickness_mode}')
    if detail:
        detail_field=sample(maps['detail'],fx,fy)
        detail_luma=np.mean(detail_field[...,:3],axis=2)
        detail_alpha=detail_field[...,3]
        optical=optical*(1+.08*detail_alpha*(detail_luma-.5)*2)[...,None]
    bg=background(kind)
    back=srgb_to_linear(sample(bg,xx+offsets[...,0],yy+offsets[...,1]))
    transmit=np.exp(-optical*2*path[...,None])
    color=back*transmit+(srgb_to_linear(reflected)*reflection_strength if reflection else 0)
    if film:
        film_field=sample(maps['film'],fx,fy)
        film_rgb=srgb_to_linear(film_field[...,:3])
        film_alpha=film_field[...,3]
        color += film_rgb*film_alpha[...,None]*.24*film_strength
    if scatter:
        internal_scatter=sample(maps['scatter'],fx,fy)
        color += srgb_to_linear(internal_scatter)*scatter_strength
    out=srgb_to_linear(bg)*(1-alpha[...,None])+np.clip(color,0,1)*alpha[...,None]
    out=np.clip(linear_to_srgb(out),0,1)
    if interior_lift or any(interior_cool):
        view_radius=np.sqrt((xx+.5-VIEW/2)**2+(yy+.5-VIEW/2)**2)/145.0
        weight=np.clip((.84-view_radius)/.25,0,1)*alpha
        # Art-directed material correction: preserve cloud structure while
        # lifting only the interior dark mass toward a pale cool cyan.
        out=np.clip(out+weight[...,None]*interior_lift*(1-out),0,1)
        out=np.clip(out+weight[...,None]*np.asarray(interior_cool)[None,None,:],0,1)
    return out

def main():
    donor, removed, reference_donor=clean_donor()
    yy,xx=np.mgrid[:N,:N]
    radius=np.sqrt((xx+0.5-200)**2+(yy+0.5-200)**2)/FIELD_RADIUS
    analytic=np.sqrt(np.maximum(1-radius**2,0))
    alpha=np.asarray(Image.open(INPUTS/'formal-silhouette-mask.png').convert('L'),dtype=float)/255
    source_thickness=np.asarray(Image.open(INPUTS/'neutral-thickness.png').convert('RGBA'),dtype=float)/255
    # Frozen thickness is a source field; do not treat its alpha as density.
    t=(source_thickness[...,0]-.25)/.6
    depth=np.maximum(.18,.72*analytic+.28*np.clip(t,0,1))
    depth=np.minimum(depth,1)
    neutral=np.asarray(Image.open(INPUTS/'neutral-water-volume.png').convert('RGB'),dtype=float)/255
    detail=np.asarray(Image.open(INPUTS/'neutral-water-detail.png').convert('RGBA'),dtype=float)/255
    # Preserve authored cloudy organization, suppress tiny donor marks.
    smooth=blur(donor,2.2)
    fine_weight=np.where(radius>.84,.88,.60)[...,None]
    appearance=smooth+(donor-smooth)*fine_weight
    # M1 contributes weak local texture, not an opaque blue body or a nucleus.
    neutral_band=neutral-blur(neutral,10)
    appearance=np.clip(appearance+.025*neutral_band,0,1)
    c=srgb_to_linear(appearance)
    b=srgb_to_linear(BG)
    # Single-view art-directed decomposition C = T*B + R.
    # The split is non-unique; storing separate fields makes its limits testable.
    scatter=.055*depth[...,None]
    trans=np.clip(np.minimum(c/b,1)-scatter,.08,1)
    reflected=np.maximum(c-trans*b,0)
    optical=-np.log(trans)/(2*depth[...,None])
    # Absorption map RGB stores optical-depth coefficients in [0,2].
    optical=np.clip(optical,0,1)
    # Local gradients yield refraction offsets; no Bezier/ribbon geometry.
    density=blur(np.mean(optical,axis=2),5)
    gy,gx=np.gradient(density)
    offsets=np.dstack([gx,gy])*65*depth[...,None]
    offsets=np.clip(offsets,-1,1)
    reflection_rgb=np.clip(linear_to_srgb(reflected),0,1)
    save_rgba('field-optical-depth.png',optical,alpha)
    save_rgb('field-reflected-light.png',reflection_rgb)
    internal_scatter_linear=srgb_to_linear(appearance)*(CALIBRATED_SCATTER_STRENGTH*depth[...,None])
    save_rgb('field-internal-scatter.png',linear_to_srgb(internal_scatter_linear))
    save_rgb('field-thickness.png',np.repeat(depth[...,None],3,axis=2))
    save_rgb('field-refraction.png',np.dstack([(offsets+1)*.5,depth]))
    # Copy frozen inputs for future GPU sampling and independent ablations.
    for source,name in [('formal-silhouette-mask.png','field-silhouette.png'),('formal-outer-film-crop.png','field-formal-film.png'),('neutral-water-detail.png','field-m1-detail.png')]:
        Image.open(INPUTS/source).save(OUT/name)
    detail_field=np.asarray(Image.open(OUT/'field-m1-detail.png').convert('RGBA'),dtype=np.float64)/255
    film_field=np.asarray(Image.open(OUT/'field-formal-film.png').convert('RGBA'),dtype=np.float64)/255
    maps={'optical':optical,'depth':depth,'alpha':alpha,'reflected':reflection_rgb,'offset':offsets,'film':film_field,'detail':detail_field,'depth_mean':float(depth[alpha>.5].mean())}
    # Reference-soft follow-up: use the cleaned Final Art 025 appearance only
    # to solve a lighter static field. The candidate still renders through the
    # same thickness, silhouette and PNG round-trip path; it does not replace
    # the formal donor or alter production authority.
    reference_c=srgb_to_linear(reference_donor)
    reference_scatter_linear=reference_c*(REFERENCE_SOFT_SCATTER_STRENGTH*depth[...,None])
    reference_trans=np.clip(np.minimum(reference_c/b,1)-reference_scatter_linear,.08,1)
    reference_reflected=np.maximum(reference_c-reference_trans*b,0)
    reference_optical=np.clip(-np.log(reference_trans)/(2*depth[...,None]),0,1)
    reference_density=blur(np.mean(reference_optical,axis=2),5)
    reference_gy,reference_gx=np.gradient(reference_density)
    reference_offsets=np.clip(np.dstack([reference_gx,reference_gy])*REFERENCE_SOFT_REFRACTION_SCALE*depth[...,None],-1,1)
    # The reference has UI text over the upper cap. Smooth only that internal
    # band so the repaired pixels cannot form a false top ridge or dent.
    field_y=(np.indices((N,N))[0]+.5-N/2)/FIELD_RADIUS
    field_radius=np.sqrt((np.indices((N,N))[1]+.5-N/2)**2+(np.indices((N,N))[0]+.5-N/2)**2)/FIELD_RADIUS
    reference_top_mask=np.clip((-.08-field_y)/.38,0,1)*np.clip((.90-field_radius)/.16,0,1)
    reference_top_mask=blur(reference_top_mask,5)
    def top_blend(field):
        if field.ndim==2:
            smooth=blur(field,REFERENCE_SOFT_TOP_BLUR_RADIUS)
            return field*(1-reference_top_mask)+smooth*reference_top_mask
        smooth=np.dstack([blur(field[...,i],REFERENCE_SOFT_TOP_BLUR_RADIUS) for i in range(field.shape[2])])
        return field*(1-reference_top_mask[...,None])+smooth*reference_top_mask[...,None]
    reference_optical=top_blend(reference_optical)
    reference_reflected=top_blend(reference_reflected)
    reference_scatter_linear=top_blend(reference_scatter_linear)
    reference_offsets=top_blend(reference_offsets)
    reference_film=film_field.copy()
    reference_film[...,3]=np.clip(reference_film[...,3]*REFERENCE_SOFT_FILM_STRENGTH,0,1)
    save_rgba('field-optical-depth-025-reference-soft.png',reference_optical,alpha)
    save_rgb('field-reflected-light-025-reference-soft.png',linear_to_srgb(reference_reflected))
    save_rgb('field-internal-scatter-025-reference-soft.png',linear_to_srgb(reference_scatter_linear))
    save_rgb('field-refraction-025-reference-soft.png',np.dstack([(reference_offsets+1)*.5,depth]))
    save_rgba('field-formal-film-025-reference-soft.png',reference_film[...,:3],reference_film[...,3])
    save_rgb('field-025-reference-top-mask.png',np.repeat(reference_top_mask[...,None],3,axis=2))
    # The side screenshots show a second, unnecessary shell cover. Reduce only
    # the lateral outer bands; the top/bottom cap and central body stay intact.
    field_x=(np.indices((N,N))[1]+.5-N/2)/FIELD_RADIUS
    reference_side_mask=np.clip((np.abs(field_x)-.55)/.23,0,1)*np.clip((.98-field_radius)/.12,0,1)
    reference_side_mask=blur(reference_side_mask,5)
    reference_side_film=reference_film.copy()
    reference_side_film[...,3]*=(1-(1-REFERENCE_SIDE_FILM_STRENGTH)*reference_side_mask)
    reference_side_reflected=reference_reflected*(1-(1-REFERENCE_SIDE_REFLECTION_STRENGTH)*reference_side_mask[...,None])
    save_rgb('field-reflected-light-025-reference-side-clean.png',linear_to_srgb(reference_side_reflected))
    save_rgba('field-formal-film-025-reference-side-clean.png',reference_side_film[...,:3],reference_side_film[...,3])
    save_rgb('field-025-reference-side-mask.png',np.repeat(reference_side_mask[...,None],3,axis=2))
    # The remaining screenshot artifact sits on the outer upper-left arc. The
    # previous mask landed too far inward, so it could not affect the visible
    # duplicate layer. This tighter, shifted mask reaches the arc while its
    # feather keeps the sphere silhouette continuous.
    reference_corner_mask=np.clip((-.45-field_x)/.35,0,1)*np.clip((-.05-field_y)/.45,0,1)*np.clip((1.10-field_radius)/.20,0,1)
    reference_corner_mask=blur(reference_corner_mask,REFERENCE_CORNER_MASK_BLUR_RADIUS)
    reference_corner_film=reference_side_film.copy()
    reference_corner_film[...,3]*=(1-(1-REFERENCE_CORNER_FILM_STRENGTH)*reference_corner_mask)
    reference_corner_reflected=reference_side_reflected*(1-(1-REFERENCE_CORNER_REFLECTION_STRENGTH)*reference_corner_mask[...,None])
    reference_corner_optical=np.clip(reference_optical*(1-REFERENCE_CORNER_OPTICAL_STRENGTH*reference_corner_mask[...,None]),0,1)
    reference_corner_scatter=np.clip(reference_scatter_linear*(1-REFERENCE_CORNER_SCATTER_STRENGTH*reference_corner_mask[...,None]),0,1)
    reference_corner_alpha=np.clip(alpha*(1-REFERENCE_CORNER_ALPHA_STRENGTH*reference_corner_mask),0,1)
    save_rgba('field-optical-depth-025-reference-corner-clean.png',reference_corner_optical,reference_corner_alpha)
    save_rgb('field-reflected-light-025-reference-corner-clean.png',linear_to_srgb(reference_corner_reflected))
    save_rgb('field-internal-scatter-025-reference-corner-clean.png',linear_to_srgb(reference_corner_scatter))
    save_rgba('field-formal-film-025-reference-corner-clean.png',reference_corner_film[...,:3],reference_corner_film[...,3])
    save_rgb('field-025-reference-corner-mask.png',np.repeat(reference_corner_mask[...,None],3,axis=2))
    # The remaining upper-left and upper-right membrane fragments are formal
    # film, not internal water. Remove only the mirrored corner film/reflection
    # contribution and leave the optical volume, scatter and silhouette intact.
    reference_upper_mask=np.clip((np.abs(field_x)-.22)/.40,0,1)*np.clip((.12-field_y)/.48,0,1)*np.clip((1.25-field_radius)/.25,0,1)
    reference_upper_mask=blur(reference_upper_mask,REFERENCE_UPPER_MASK_BLUR_RADIUS)
    reference_upper_film=reference_corner_film.copy()
    reference_upper_film[...,3]*=(1-(1-REFERENCE_UPPER_FILM_STRENGTH)*reference_upper_mask)
    reference_upper_reflected=reference_corner_reflected*(1-(1-REFERENCE_UPPER_REFLECTION_STRENGTH)*reference_upper_mask[...,None])
    reference_upper_optical=np.clip(reference_corner_optical*(1-REFERENCE_UPPER_OPTICAL_STRENGTH*reference_upper_mask[...,None]),0,1)
    reference_upper_scatter=np.clip(reference_corner_scatter*(1-REFERENCE_UPPER_SCATTER_STRENGTH*reference_upper_mask[...,None]),0,1)
    save_rgba('field-optical-depth-025-reference-upper-clean.png',reference_upper_optical,reference_corner_alpha)
    save_rgb('field-reflected-light-025-reference-upper-clean.png',linear_to_srgb(reference_upper_reflected))
    save_rgb('field-internal-scatter-025-reference-upper-clean.png',linear_to_srgb(reference_upper_scatter))
    save_rgba('field-formal-film-025-reference-upper-clean.png',reference_upper_film[...,:3],reference_upper_film[...,3])
    save_rgb('field-025-reference-upper-mask.png',np.repeat(reference_upper_mask[...,None],3,axis=2))
    # Rebalanced candidate: restore the corner's optical magnitude and remove
    # only the baked warm/cool chroma that reads as a second membrane. This
    # keeps the sphere full instead of making the masked area foggy.
    upper_optical_gray=np.mean(reference_corner_optical,axis=2,keepdims=True)
    upper_scatter_gray=np.mean(reference_corner_scatter,axis=2,keepdims=True)
    neutral_weight=REFERENCE_UPPER_CHROMA_NEUTRALIZE_STRENGTH*reference_upper_mask[...,None]
    reference_rebalanced_optical=np.clip(reference_corner_optical*(1-neutral_weight)+upper_optical_gray*neutral_weight,0,1)
    reference_rebalanced_scatter=np.clip(reference_corner_scatter*(1-neutral_weight)+upper_scatter_gray*neutral_weight,0,1)
    save_rgba('field-optical-depth-025-reference-upper-rebalanced.png',reference_rebalanced_optical,reference_corner_alpha)
    save_rgb('field-internal-scatter-025-reference-upper-rebalanced.png',linear_to_srgb(reference_rebalanced_scatter))
    # The left upper arc still carries a gray depth band beyond the intended
    # membrane line. Correct only that narrow outer shadow; do not touch alpha
    # or the full upper-corner volume.
    left_shadow_edge=np.clip((field_radius-.78)/.24,0,1)*np.clip((1.13-field_radius)/.25,0,1)
    left_shadow_region=np.clip((-.20-field_x)/.55,0,1)*np.clip((.08-field_y)/.48,0,1)
    left_shadow_mask=blur(left_shadow_edge*left_shadow_region,REFERENCE_LEFT_SHADOW_MASK_BLUR_RADIUS)
    left_shadow_mask=np.clip(left_shadow_mask/max(float(left_shadow_mask.max()),.001),0,1)
    left_shadow_optical=np.clip(reference_rebalanced_optical*(1-REFERENCE_LEFT_SHADOW_DEPTH_REDUCTION*left_shadow_mask[...,None]),0,1)
    left_shadow_scatter=srgb_to_linear(reference_rebalanced_scatter)
    left_shadow_scatter+=srgb_to_linear(np.array([.88,.95,.96]))[None,None,:]*(REFERENCE_LEFT_SHADOW_SCATTER_FILL*left_shadow_mask[...,None])
    left_shadow_scatter=np.clip(linear_to_srgb(left_shadow_scatter),0,1)
    save_rgba('field-optical-depth-025-reference-left-shadow-clean.png',left_shadow_optical,reference_corner_alpha)
    save_rgb('field-internal-scatter-025-reference-left-shadow-clean.png',left_shadow_scatter)
    save_rgb('field-025-reference-left-shadow-mask.png',np.repeat(left_shadow_mask[...,None],3,axis=2))
    memory_maps=maps.copy()
    # The primary candidate is rendered from the exported PNG fields, not from
    # the in-memory arrays that created them.
    disk_maps=read_disk_fields()
    # Cycle 1: calibrate the exported optical field itself. The mask selects
    # high-depth interior pixels and excludes the formal shell; already-light
    # regions are left unchanged.
    optical_mean=disk_maps['optical'].mean(axis=2)
    field_radius=np.sqrt((np.indices((N,N))[1]+.5-N/2)**2+(np.indices((N,N))[0]+.5-N/2)**2)/FIELD_RADIUS
    interior_region=np.clip((.90-field_radius)/.16,0,1)
    shell_region=np.clip(disk_maps['film'][...,3]/.28,0,1)
    inside_field=disk_maps['alpha']>.5
    p_low,p_high=np.percentile(optical_mean[inside_field],[55,88])
    high_depth=np.clip((optical_mean-p_low)/max(p_high-p_low,.001),0,1)
    calibration_mask=high_depth*interior_region*(1-shell_region)
    calibrated_optical=np.clip(disk_maps['optical']*(1-PRIMARY_025_DEPTH_REDUCTION*calibration_mask[...,None]),0,1)
    save_rgba('field-optical-depth-025-calibrated.png',calibrated_optical,disk_maps['alpha'])
    save_rgb('field-025-optical-calibration-mask.png',np.repeat(calibration_mask[...,None],3,axis=2))
    # Follow-up sphere-relief pass: use the same high-depth/non-shell gate,
    # soften it spatially, then reduce only the broadest internal shadow. A
    # small neutral-silver scatter fill keeps the sphere legible on dark
    # backgrounds without applying a final-RGB tint or flattening detail.
    sphere_relief_mask=blur(calibration_mask,9)
    sphere_relief_mask*=interior_region*(1-shell_region)
    sphere_relief_mask=np.clip(sphere_relief_mask,0,1)
    sphere_relief_optical=np.clip(calibrated_optical*(1-SPHERE_RELIEF_DEPTH_REDUCTION*sphere_relief_mask[...,None]),0,1)
    sphere_relief_scatter_linear=srgb_to_linear(disk_maps['scatter'])
    sphere_relief_scatter_linear += srgb_to_linear(np.array([.82,.91,.92]))[None,None,:]*(SPHERE_RELIEF_SCATTER_STRENGTH*sphere_relief_mask[...,None])
    sphere_relief_scatter=np.clip(linear_to_srgb(sphere_relief_scatter_linear),0,1)
    save_rgba('field-optical-depth-025-sphere-relief.png',sphere_relief_optical,disk_maps['alpha'])
    save_rgb('field-025-sphere-relief-mask.png',np.repeat(sphere_relief_mask[...,None],3,axis=2))
    save_rgb('field-internal-scatter-025-sphere-relief.png',sphere_relief_scatter)
    # One additional local correction targets the actual broad dark deficit in
    # the light-background preview. It is projected back into field space,
    # blurred, and shell-gated; this removes the concavity cue without making
    # the entire centre a uniform radial disc.
    preview_maps=disk_maps.copy()
    preview_maps['optical']=sphere_relief_optical
    preview_maps['scatter']=sphere_relief_scatter
    preview=render(preview_maps,'light',scatter=True)
    preview_linear=srgb_to_linear(preview)
    preview_luma=np.dot(preview_linear,np.array([.2126,.7152,.0722]))
    preview_fill=blur(preview_luma,20)
    view_shadow=np.clip((preview_fill-preview_luma)/.045,0,1)
    view_y,view_x=np.mgrid[:VIEW,:VIEW]
    view_fx=(view_x+.5-VIEW/2)*FIELD_RADIUS/RADIUS+N/2-.5
    view_fy=(view_y+.5-VIEW/2)*FIELD_RADIUS/RADIUS+N/2-.5
    map_x=np.clip(np.rint(view_fx).astype(int),0,N-1)
    map_y=np.clip(np.rint(view_fy).astype(int),0,N-1)
    shadow_relief_map=np.zeros((N,N),dtype=np.float64)
    shadow_relief_weight=np.zeros((N,N),dtype=np.float64)
    np.add.at(shadow_relief_map,(map_y,map_x),view_shadow)
    np.add.at(shadow_relief_weight,(map_y,map_x),1)
    shadow_relief_map=np.divide(shadow_relief_map,np.maximum(shadow_relief_weight,1),out=np.zeros_like(shadow_relief_map),where=shadow_relief_weight>0)
    shadow_relief_map=blur(shadow_relief_map,4)*interior_region*(1-shell_region)*alpha
    shadow_relief_map=np.clip(shadow_relief_map,0,1)
    sphere_relief_optical=np.clip(sphere_relief_optical*(1-SPHERE_RELIEF_SHADOW_DEPTH_REDUCTION*shadow_relief_map[...,None]),0,1)
    sphere_relief_scatter_linear=srgb_to_linear(sphere_relief_scatter)
    sphere_relief_scatter_linear += srgb_to_linear(np.array([.84,.92,.93]))[None,None,:]*(SPHERE_RELIEF_SHADOW_SCATTER_STRENGTH*shadow_relief_map[...,None])
    sphere_relief_scatter=np.clip(linear_to_srgb(sphere_relief_scatter_linear),0,1)
    save_rgba('field-optical-depth-025-sphere-relief.png',sphere_relief_optical,disk_maps['alpha'])
    save_rgb('field-025-shadow-relief-mask.png',np.repeat(shadow_relief_map[...,None],3,axis=2))
    save_rgb('field-internal-scatter-025-sphere-relief.png',sphere_relief_scatter)
    # Keep shell/specular authority outside the future internal field. This is
    # an explicit estimate, not a claim that the single-view split is unique.
    film_linear=srgb_to_linear(disk_maps['film'][...,:3])
    reflected_linear=srgb_to_linear(disk_maps['reflected'])
    shell_reflection_linear=film_linear*disk_maps['film'][...,3,None]*SHELL_REFLECTION_ESTIMATE
    internal_reflection_linear=np.maximum(reflected_linear-shell_reflection_linear,0)
    save_rgb('field-shell-reflection.png',linear_to_srgb(shell_reflection_linear))
    save_rgb('field-internal-reflected-light.png',linear_to_srgb(internal_reflection_linear))
    calibrated_maps=read_disk_fields('field-optical-depth-025-calibrated.png','field-internal-reflected-light.png')
    sphere_relief_maps=read_disk_fields('field-optical-depth-025-sphere-relief.png','field-internal-reflected-light.png','field-internal-scatter-025-sphere-relief.png')
    simple_shell_film=sphere_relief_maps['film'].copy()
    simple_shell_film[...,3]=np.clip(simple_shell_film[...,3]*SIMPLE_SHELL_FILM_STRENGTH,0,1)
    save_rgba('field-formal-film-025-simple-shell.png',simple_shell_film[...,:3],simple_shell_film[...,3])
    simple_shell_maps=read_disk_fields('field-optical-depth-025-sphere-relief.png','field-internal-reflected-light.png','field-internal-scatter-025-sphere-relief.png','field-formal-film-025-simple-shell.png')
    reference_soft_maps=read_disk_fields('field-optical-depth-025-reference-soft.png','field-reflected-light-025-reference-soft.png','field-internal-scatter-025-reference-soft.png','field-formal-film-025-reference-soft.png','field-refraction-025-reference-soft.png')
    reference_side_maps=read_disk_fields('field-optical-depth-025-reference-soft.png','field-reflected-light-025-reference-side-clean.png','field-internal-scatter-025-reference-soft.png','field-formal-film-025-reference-side-clean.png','field-refraction-025-reference-soft.png')
    reference_corner_maps=read_disk_fields('field-optical-depth-025-reference-corner-clean.png','field-reflected-light-025-reference-corner-clean.png','field-internal-scatter-025-reference-corner-clean.png','field-formal-film-025-reference-corner-clean.png','field-refraction-025-reference-soft.png')
    reference_upper_maps=read_disk_fields('field-optical-depth-025-reference-upper-clean.png','field-reflected-light-025-reference-upper-clean.png','field-internal-scatter-025-reference-upper-clean.png','field-formal-film-025-reference-upper-clean.png','field-refraction-025-reference-soft.png')
    reference_rebalanced_maps=read_disk_fields('field-optical-depth-025-reference-upper-rebalanced.png','field-reflected-light-025-reference-upper-clean.png','field-internal-scatter-025-reference-upper-rebalanced.png','field-formal-film-025-reference-upper-clean.png','field-refraction-025-reference-soft.png')
    left_shadow_maps=read_disk_fields('field-optical-depth-025-reference-left-shadow-clean.png','field-reflected-light-025-reference-upper-clean.png','field-internal-scatter-025-reference-left-shadow-clean.png','field-formal-film-025-reference-upper-clean.png','field-refraction-025-reference-soft.png')
    for kind in ['light','neutral','dark','split','checker']:
        candidate=render(disk_maps,kind)
        save_rgb('candidate-optical-'+kind+'.png',candidate)
        save_rgb('candidate-optical-'+kind+'-detail.png',crop_detail(candidate))
        cooler=render(disk_maps,kind,interior_lift=.22,interior_cool=(-.028,.018,.055))
        save_rgb('candidate-optical-'+kind+'-cooler.png',cooler)
        save_rgb('candidate-optical-'+kind+'-cooler-detail.png',crop_detail(cooler))
        matched=render(disk_maps,kind,thickness_mode='mean_match')
        save_rgb('ablation-'+kind+'-thickness-mean-match.png',matched)
        save_rgb('ablation-'+kind+'-thickness-mean-match-detail.png',crop_detail(matched))
        calibrated=render(calibrated_maps,kind,scatter=True)
        save_rgb('candidate-optical-'+kind+'-025-calibrated.png',calibrated)
        save_rgb('candidate-optical-'+kind+'-025-calibrated-detail.png',crop_detail(calibrated))
        sphere_relief=render(sphere_relief_maps,kind,scatter=True)
        save_rgb('candidate-optical-'+kind+'-025-sphere-relief.png',sphere_relief)
        save_rgb('candidate-optical-'+kind+'-025-sphere-relief-detail.png',crop_detail(sphere_relief))
        simple_shell=render(simple_shell_maps,kind,scatter=True)
        save_rgb('candidate-optical-'+kind+'-025-simple-shell.png',simple_shell)
        save_rgb('candidate-optical-'+kind+'-025-simple-shell-detail.png',crop_detail(simple_shell))
        reference_soft=render(reference_soft_maps,kind,scatter=True,detail=False)
        save_rgb('candidate-optical-'+kind+'-025-reference-soft.png',reference_soft)
        save_rgb('candidate-optical-'+kind+'-025-reference-soft-detail.png',crop_detail(reference_soft))
        reference_side=render(reference_side_maps,kind,scatter=True,detail=False)
        save_rgb('candidate-optical-'+kind+'-025-reference-side-clean.png',reference_side)
        save_rgb('candidate-optical-'+kind+'-025-reference-side-clean-detail.png',crop_detail(reference_side))
        reference_corner=render(reference_corner_maps,kind,scatter=True,detail=False)
        save_rgb('candidate-optical-'+kind+'-025-reference-corner-clean.png',reference_corner)
        save_rgb('candidate-optical-'+kind+'-025-reference-corner-clean-detail.png',crop_detail(reference_corner))
        reference_upper=render(reference_upper_maps,kind,scatter=True,detail=False)
        save_rgb('candidate-optical-'+kind+'-025-reference-upper-clean.png',reference_upper)
        save_rgb('candidate-optical-'+kind+'-025-reference-upper-clean-detail.png',crop_detail(reference_upper))
        reference_rebalanced=render(reference_rebalanced_maps,kind,scatter=True,detail=False)
        save_rgb('candidate-optical-'+kind+'-025-reference-upper-rebalanced.png',reference_rebalanced)
        save_rgb('candidate-optical-'+kind+'-025-reference-upper-rebalanced-detail.png',crop_detail(reference_rebalanced))
        left_shadow=render(left_shadow_maps,kind,scatter=True,detail=False)
        save_rgb('candidate-optical-'+kind+'-025-reference-left-shadow-clean.png',left_shadow)
        save_rgb('candidate-optical-'+kind+'-025-reference-left-shadow-clean-detail.png',crop_detail(left_shadow))
        # Review-only highlight softening. This changes display contribution
        # only; optical depth, alpha, silhouette and all exported fields stay
        # identical to the preserved left-shadow-clean candidate.
        highlight_soft=render(left_shadow_maps,kind,scatter=True,detail=False,
                              reflection_strength=REFERENCE_HIGHLIGHT_SOFT_REFLECTION,
                              film_strength=REFERENCE_HIGHLIGHT_SOFT_FILM,
                              scatter_strength=REFERENCE_HIGHLIGHT_SOFT_SCATTER)
        save_rgb('candidate-optical-'+kind+'-025-reference-left-shadow-highlight-soft.png',highlight_soft)
        save_rgb('candidate-optical-'+kind+'-025-reference-left-shadow-highlight-soft-detail.png',crop_detail(highlight_soft))
        calibrated_matched=render(calibrated_maps,kind,thickness_mode='mean_match',scatter=True)
        save_rgb('ablation-025-calibrated-'+kind+'-thickness-mean-match.png',calibrated_matched)
        save_rgb('ablation-025-calibrated-'+kind+'-thickness-mean-match-detail.png',crop_detail(calibrated_matched))
    save_rgb('ablation-thickness-off.png',render(disk_maps,'light',thickness_mode='constant'))
    save_rgb('ablation-thickness-mean-match.png',render(disk_maps,'light',thickness_mode='mean_match'))
    save_rgb('ablation-reflection-off.png',render(disk_maps,'light',reflection=False))
    save_rgb('ablation-refraction-off.png',render(disk_maps,'checker',refraction=False))
    # Reference and old baseline are shown at the same diameter, with no UI crop claim.
    old=Image.open(OUT/'candidate-formal-static-baseline.png').convert('RGB').resize((300,300),Image.Resampling.LANCZOS)
    aligned=Image.new('RGB',(360,360),tuple((BG*255).astype(int)))
    aligned.paste(old,(30,30));aligned.save(OUT/'baseline-aligned.png')
    view_y,view_x=np.mgrid[:VIEW,:VIEW]
    view_fx=(view_x+.5-VIEW/2)*FIELD_RADIUS/RADIUS+N/2-.5
    view_fy=(view_y+.5-VIEW/2)*FIELD_RADIUS/RADIUS+N/2-.5
    inside=sample(disk_maps['alpha'],view_fx,view_fy)[...,0]>.5
    memory_render=render(memory_maps,'light')
    disk_render=render(disk_maps,'light')
    old_constant=render(disk_maps,'light',thickness_mode='constant')
    mean_match=render(disk_maps,'light',thickness_mode='mean_match')
    calibrated_render=render(calibrated_maps,'light',scatter=True)
    calibrated_mean_match=render(calibrated_maps,'light',thickness_mode='mean_match',scatter=True)
    sphere_relief_render=render(sphere_relief_maps,'light',scatter=True)
    roundtrip_delta=np.abs(memory_render-disk_render)*255
    level_delta=np.abs(disk_render-old_constant)*255
    spatial_delta=np.abs(disk_render-mean_match)*255
    calibrated_spatial_delta=np.abs(calibrated_render-calibrated_mean_match)*255
    calibrated_level_delta=np.abs(calibrated_render-render(calibrated_maps,'light',thickness_mode='constant',scatter=True))*255
    doc={
      'experiment':'FINAL_ART_025_REFERENCE_DIRECTED_OPTICAL_STUDY',
      'status':'READY_FOR_HUMAN_REVIEW','m2_closed':False,'m1_modified':False,
      'production_dependency':False,'product_state':'still','animation_loop':False,
      'target':'FINAL_ART_025','goal':'在单视角静态画面中重建 025 的材质外观，并验证不同背景下的透射和厚度贡献。',
      'method':'formal static baseline donor; optical-depth-aware internal calibration; separated internal/shell reflection; PNG field export and disk roundtrip reconstruction',
      'inference':'单张参考无法唯一求解真实材质；本字段是画面定向的近似，不是测得的物理参数。',
      'runtime_final_frame_sampling':False,'gpu_material_renderer':False,
      'actual_primary_donor':{'file':'candidate-formal-static-baseline.png','role':'primary offline donor','used_for_primary':True},
      'final_art_025_diagnostic':{'file':'target-final-art-025.png','role':'visual target and donor-cleaning diagnostic only','used_for_primary':False,'removed_ui_and_point_pixels_diagnostic':removed},
      'primary_candidate':'candidate-optical-light-025-reference-left-shadow-highlight-soft.png',
      'latest_user_followup_candidate':'candidate-optical-light-025-reference-left-shadow-highlight-soft.png',
      'lock_status':'LOCKED_BY_HUMAN_REVIEW_FOR_NEXT_STEP',
      'static_material_lock':'static-material-lock.json',
      'review_preview':{'candidate':'candidate-optical-neutral-025-reference-left-shadow-highlight-soft.png','background':'neutral_mid_gray','rgb_8bit':[154,166,170],'purpose':'降低白色高亮对判断的干扰，检查球体边界、内部体积和左右上角连续性；仅软化显示贡献，不改变材质字段'},
      'previous_candidates':{'candidate-optical-light.png':'PRESERVED_DEEP_MATERIAL_HISTORY','candidate-optical-light-cooler.png':'PRESERVED_FUTURE_MID_DEPTH_TRANSITION_REFERENCE','candidate-optical-light-025-calibrated.png':'SUPERSEDED_STATIC_CALIBRATION','candidate-optical-light-025-reference-left-shadow-clean.png':'SUPERSEDED_PRE_HIGHLIGHT_SOFTENING'},
      'final_rgb_lift':{'used_for_primary':False,'preserved_in_cooler_reference':True},
      'interior_optical_calibration':{'mask':'field-025-optical-calibration-mask.png','depth_percentile_gate':[55,88],'max_optical_reduction':PRIMARY_025_DEPTH_REDUCTION,'shell_exclusion':'formal film alpha','changed':'optical depth / absorption only; no radial-only global tint'},
      'user_followup_sphere_relief':{'candidate':'candidate-optical-light-025-sphere-relief.png','depth_relief_mask':'field-025-sphere-relief-mask.png','shadow_relief_mask':'field-025-shadow-relief-mask.png','scatter_field':'field-internal-scatter-025-sphere-relief.png','additional_depth_reduction':SPHERE_RELIEF_DEPTH_REDUCTION,'neutral_scatter_strength':SPHERE_RELIEF_SCATTER_STRENGTH,'shadow_depth_reduction':SPHERE_RELIEF_SHADOW_DEPTH_REDUCTION,'shadow_scatter_strength':SPHERE_RELIEF_SHADOW_SCATTER_STRENGTH,'purpose':'降低宽幅内部阴影造成的凹陷感，保留云层、外膜、轮廓和点位','is_new_cycle':False},
      'user_followup_simple_shell':{'candidate':'candidate-optical-light-025-simple-shell.png','film_field':'field-formal-film-025-simple-shell.png','film_strength':SIMPLE_SHELL_FILM_STRENGTH,'purpose':'简化边缘光影，只保留一层柔和薄膜，避免复杂环形高光改变球体身份','is_new_cycle':False},
      'user_followup_reference_soft':{'candidate':'candidate-optical-light-025-reference-soft.png','optical_field':'field-optical-depth-025-reference-soft.png','reflected_field':'field-reflected-light-025-reference-soft.png','scatter_field':'field-internal-scatter-025-reference-soft.png','film_field':'field-formal-film-025-reference-soft.png','refraction_field':'field-refraction-025-reference-soft.png','top_repair_mask':'field-025-reference-top-mask.png','appearance_source':'cleaned Final Art 025 visual reference, follow-up static calibration only','scatter_strength':REFERENCE_SOFT_SCATTER_STRENGTH,'film_strength':REFERENCE_SOFT_FILM_STRENGTH,'refraction_scale':REFERENCE_SOFT_REFRACTION_SCALE,'top_blur_radius':REFERENCE_SOFT_TOP_BLUR_RADIUS,'purpose':'恢复参考图中完整浅色球体和简单边缘关系，并消除 UI 修补造成的顶部假形变','is_new_cycle':False},
      'user_followup_reference_side_clean':{'candidate':'candidate-optical-light-025-reference-side-clean.png','side_mask':'field-025-reference-side-mask.png','reflected_field':'field-reflected-light-025-reference-side-clean.png','film_field':'field-formal-film-025-reference-side-clean.png','film_strength_lateral':REFERENCE_SIDE_FILM_STRENGTH,'reflection_strength_lateral':REFERENCE_SIDE_REFLECTION_STRENGTH,'purpose':'去掉左右两侧多余覆盖层，只保留主体和简单轮廓','is_new_cycle':False},
      'user_followup_reference_corner_clean':{'candidate':'candidate-optical-light-025-reference-corner-clean.png','corner_mask':'field-025-reference-corner-mask.png','optical_field':'field-optical-depth-025-reference-corner-clean.png','reflected_field':'field-reflected-light-025-reference-corner-clean.png','scatter_field':'field-internal-scatter-025-reference-corner-clean.png','film_field':'field-formal-film-025-reference-corner-clean.png','optical_strength_upper_left':REFERENCE_CORNER_OPTICAL_STRENGTH,'scatter_strength_upper_left':REFERENCE_CORNER_SCATTER_STRENGTH,'film_strength_upper_left':REFERENCE_CORNER_FILM_STRENGTH,'reflection_strength_upper_left':REFERENCE_CORNER_REFLECTION_STRENGTH,'alpha_strength_upper_left':REFERENCE_CORNER_ALPHA_STRENGTH,'mask_blur_radius':REFERENCE_CORNER_MASK_BLUR_RADIUS,'purpose':'将截图标出的左上方越界叠层从光学深度、散射、反射、薄膜和覆盖度同时收敛，保留球体轮廓并让局部自然淡出','is_new_cycle':False},
      'user_followup_reference_upper_clean':{'candidate':'candidate-optical-light-025-reference-upper-clean.png','upper_corner_mask':'field-025-reference-upper-mask.png','optical_field':'field-optical-depth-025-reference-upper-clean.png','scatter_field':'field-internal-scatter-025-reference-upper-clean.png','reflected_field':'field-reflected-light-025-reference-upper-clean.png','film_field':'field-formal-film-025-reference-upper-clean.png','optical_strength_upper_corners':REFERENCE_UPPER_OPTICAL_STRENGTH,'scatter_strength_upper_corners':REFERENCE_UPPER_SCATTER_STRENGTH,'film_strength_upper_corners':REFERENCE_UPPER_FILM_STRENGTH,'reflection_strength_upper_corners':REFERENCE_UPPER_REFLECTION_STRENGTH,'mask_blur_radius':REFERENCE_UPPER_MASK_BLUR_RADIUS,'purpose':'去掉左右上角多余膜状叠层：同步收敛局部光学深度、散射、formal film 和 shell reflection，保留顶部中央和球体主体的连续轮廓','is_new_cycle':False},
      'user_followup_reference_upper_rebalanced':{'candidate':'candidate-optical-light-025-reference-upper-rebalanced.png','upper_corner_mask':'field-025-reference-upper-mask.png','optical_field':'field-optical-depth-025-reference-upper-rebalanced.png','scatter_field':'field-internal-scatter-025-reference-upper-rebalanced.png','reflected_field':'field-reflected-light-025-reference-upper-clean.png','film_field':'field-formal-film-025-reference-upper-clean.png','chroma_neutralize_strength':REFERENCE_UPPER_CHROMA_NEUTRALIZE_STRENGTH,'purpose':'恢复左右上角完整水体，只中和局部烘焙暖冷色，避免膜状叠层感和雾化缺口','is_new_cycle':False},
      'user_followup_reference_left_shadow_clean':{'candidate':'candidate-optical-light-025-reference-left-shadow-clean.png','left_shadow_mask':'field-025-reference-left-shadow-mask.png','optical_field':'field-optical-depth-025-reference-left-shadow-clean.png','scatter_field':'field-internal-scatter-025-reference-left-shadow-clean.png','depth_reduction':REFERENCE_LEFT_SHADOW_DEPTH_REDUCTION,'neutral_scatter_fill':REFERENCE_LEFT_SHADOW_SCATTER_FILL,'mask_blur_radius':REFERENCE_LEFT_SHADOW_MASK_BLUR_RADIUS,'purpose':'只收敛左上外弧越界的灰色 optical-depth 阴影，恢复膜与球体边界的连续关系，不改 alpha','is_new_cycle':False},
      'user_followup_reference_highlight_soft':{'candidate':'candidate-optical-light-025-reference-left-shadow-highlight-soft.png','neutral_review_candidate':'candidate-optical-neutral-025-reference-left-shadow-highlight-soft.png','base_candidate':'candidate-optical-light-025-reference-left-shadow-clean.png','reflection_strength':REFERENCE_HIGHLIGHT_SOFT_REFLECTION,'film_strength':REFERENCE_HIGHLIGHT_SOFT_FILM,'scatter_strength':REFERENCE_HIGHLIGHT_SOFT_SCATTER,'changed':'display contribution only; optical depth, alpha, silhouette and geometry frozen','purpose':'浅色与中性底上收敛白色壳光造成的边界冲淡，保留深色背景下的完整球体读取','is_new_cycle':False},
      'reflection_separation':{'internal_field':'field-internal-reflected-light.png','shell_field':'field-shell-reflection.png','internal_scatter_field':'field-internal-scatter.png','followup_scatter_field':'field-internal-scatter-025-sphere-relief.png','shell_estimate_weight':SHELL_REFLECTION_ESTIMATE,'internal_scatter_strength':CALIBRATED_SCATTER_STRENGTH,'status':'CALIBRATED_CANDIDATE_ONLY_APPROXIMATION'},
      'frozen_inputs_sampled':['neutral-water-volume.png (offline microtexture)','neutral-thickness.png (offline thickness mixture)','formal-silhouette-mask.png (coverage)','neutral-water-detail.png (detail modulation in render)','formal-outer-film-crop.png (film contribution in render)'],
      'field_usage':{'formal_film_used_in_current_render':True,'m1_detail_used_in_current_render':True,'calibrated_candidate_reads_optical_depth_from_disk':True,'internal_scatter_used_in_calibrated_render':True,'sphere_relief_candidate_reads_optical_and_scatter_from_disk':True,'future_gpu_input_only':True},
      'reference_hash':digest(REF),
      'field_png_roundtrip':{'max_rgb_delta_255':round(float(roundtrip_delta[inside].max()),4),'mean_rgb_delta_255':round(float(roundtrip_delta[inside].mean()),4),'status':'RECONSTRUCTED_FROM_DISK_FIELDS'},
      'thickness_ablation':{'base_constant_004_mean_rgb_delta_255':round(float(level_delta[inside].mean()),3),'base_spatial_vs_mean_matched_rgb_delta_255':round(float(spatial_delta[inside].mean()),3),'calibrated_constant_004_mean_rgb_delta_255':round(float(calibrated_level_delta[inside].mean()),3),'calibrated_spatial_vs_mean_matched_rgb_delta_255':round(float(calibrated_spatial_delta[inside].mean()),3),'depth_mean':calibrated_maps['depth_mean']},
      'calibration_effect':{'optical_depth_mean_before':float(disk_maps['optical'][inside_field].mean()),'optical_depth_mean_after':float(calibrated_maps['optical'][inside_field].mean()),'sphere_relief_optical_depth_mean_after':float(sphere_relief_maps['optical'][inside_field].mean()),'mask_mean_inside':float(calibration_mask[inside_field].mean()),'sphere_relief_mask_mean_inside':float(sphere_relief_mask[inside_field].mean()),'shadow_relief_mask_mean_inside':float(shadow_relief_map[inside_field].mean()),'cyan_mass_not_rebuilt':True},
      'future_transition_envelope':'future-transition-envelope.json',
      'cycles_used':2,
      'fresh_critic_file':'fresh-critic.md',
      'followup_critic_file':'fresh-critic-followup.md',
      'latest_critic_file':'fresh-critic-highlight-soft.md',
      'limitations':['单视角、固定形态','未实现动效、双核迁移或生产接入','不同光照下仍需要独立验证','人工材质身份判断未通过'],
      'corrections':['旧正式静态合成只作为基线，不能冒充本轮新材质','00 背景板含烘焙主体，全层叠加为负例','本候选使用离线派生字段，未把 025 原图作为候选 shader 纹理'],
      'files':{name:digest(OUT/name) for name in ['field-optical-depth.png','field-optical-depth-025-calibrated.png','field-optical-depth-025-sphere-relief.png','field-optical-depth-025-reference-soft.png','field-optical-depth-025-reference-corner-clean.png','field-optical-depth-025-reference-upper-clean.png','field-optical-depth-025-reference-upper-rebalanced.png','field-optical-depth-025-reference-left-shadow-clean.png','field-025-optical-calibration-mask.png','field-025-sphere-relief-mask.png','field-025-shadow-relief-mask.png','field-025-reference-top-mask.png','field-025-reference-side-mask.png','field-025-reference-corner-mask.png','field-025-reference-upper-mask.png','field-025-reference-left-shadow-mask.png','field-reflected-light.png','field-reflected-light-025-reference-soft.png','field-reflected-light-025-reference-side-clean.png','field-reflected-light-025-reference-corner-clean.png','field-reflected-light-025-reference-upper-clean.png','field-internal-reflected-light.png','field-internal-scatter.png','field-internal-scatter-025-sphere-relief.png','field-internal-scatter-025-reference-soft.png','field-internal-scatter-025-reference-corner-clean.png','field-internal-scatter-025-reference-upper-clean.png','field-internal-scatter-025-reference-upper-rebalanced.png','field-internal-scatter-025-reference-left-shadow-clean.png','field-shell-reflection.png','field-thickness.png','field-refraction.png','field-refraction-025-reference-soft.png','field-silhouette.png','field-formal-film.png','field-formal-film-025-simple-shell.png','field-formal-film-025-reference-soft.png','field-formal-film-025-reference-side-clean.png','field-formal-film-025-reference-corner-clean.png','field-formal-film-025-reference-upper-clean.png','field-m1-detail.png','candidate-optical-light.png','candidate-optical-light-cooler.png','candidate-optical-light-025-calibrated.png','candidate-optical-light-025-calibrated-detail.png','candidate-optical-light-025-sphere-relief.png','candidate-optical-light-025-sphere-relief-detail.png','candidate-optical-light-025-simple-shell.png','candidate-optical-light-025-simple-shell-detail.png','candidate-optical-light-025-reference-soft.png','candidate-optical-light-025-reference-soft-detail.png','candidate-optical-light-025-reference-side-clean.png','candidate-optical-light-025-reference-side-clean-detail.png','candidate-optical-light-025-reference-corner-clean.png','candidate-optical-light-025-reference-corner-clean-detail.png','candidate-optical-light-025-reference-upper-clean.png','candidate-optical-light-025-reference-upper-clean-detail.png','candidate-optical-light-025-reference-upper-rebalanced.png','candidate-optical-light-025-reference-upper-rebalanced-detail.png','candidate-optical-light-025-reference-left-shadow-clean.png','candidate-optical-light-025-reference-left-shadow-clean-detail.png','candidate-optical-neutral-025-reference-left-shadow-clean.png','candidate-optical-neutral-025-reference-left-shadow-clean-detail.png','candidate-optical-light-025-reference-left-shadow-highlight-soft.png','candidate-optical-light-025-reference-left-shadow-highlight-soft-detail.png','candidate-optical-neutral-025-reference-left-shadow-highlight-soft.png','candidate-optical-neutral-025-reference-left-shadow-highlight-soft-detail.png','ablation-025-calibrated-light-thickness-mean-match.png']}}
    envelope={
      'status':'REFERENCE_ONLY_NO_INTERPOLATION',
      'production_dependency':False,'runtime_state':False,'m3':False,
      'purpose':'保存 025→050→075→K2 的视觉参数范围，不实现过渡。',
      'static_frozen':{'silhouette':'FROZEN','center':'FROZEN','radius':'FROZEN','hitRadius':'FROZEN','formalShellIdentity':'FROZEN'},
      'future_continuous_parameters':{
        '025':{'opticalDepth':'low','densityStrength':'low','cloudyMassOrganization':'subtle','localRefractionStrength':'very_low','sparseDetailVisibility':'low','transmissionBalance':'silver_white_dominant'},
        '050':{'opticalDepth':'medium','densityStrength':'medium','cloudyMassOrganization':'medium','localRefractionStrength':'medium_low','sparseDetailVisibility':'medium','transmissionBalance':'cyan_more_present'},
        '075':{'opticalDepth':'medium_high','densityStrength':'medium_high','cloudyMassOrganization':'stronger','localRefractionStrength':'medium','sparseDetailVisibility':'medium_high','transmissionBalance':'deeper_cloudy_material'},
        'K2':{'authority':'FROZEN_FINAL_STATIC_ENDPOINT','opticalDepth':'endpoint_authority','densityStrength':'endpoint_authority','localRefractionStrength':'endpoint_authority','sparseDetailVisibility':'endpoint_authority'}
      },
      'separate_future_authority':{'coldWarmCorePosition':'FUTURE_CORE_AUTHORITY','coreOpticalAssets':'FUTURE_CORE_AUTHORITY'},
      'forbidden_this_milestone':['interpolation','formation','deformation','runtime_state','core_movement','moving','production_migration']
    }
    (OUT/'future-transition-envelope.json').write_text(json.dumps(envelope,ensure_ascii=False,indent=2)+'\n')
    (OUT/'optical-evidence.json').write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':doc['status'],'diagnostic_removed_pixels':removed,'thickness_ablation':doc['thickness_ablation'],'field_png_roundtrip':doc['field_png_roundtrip']},ensure_ascii=False))

if __name__=='__main__':main()
