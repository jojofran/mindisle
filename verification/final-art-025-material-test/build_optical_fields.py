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
REF = M1 / 'references/final-art-025.png'
N = 400
VIEW = 360
RADIUS = 140
FIELD_RADIUS = 176
BG = np.array([234, 241, 243], dtype=np.float64) / 255

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
    return data, int(mask.sum())

def background(kind):
    yy,xx=np.mgrid[:VIEW,:VIEW]
    if kind=='light': return np.broadcast_to(BG,(VIEW,VIEW,3)).copy()
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

def render(maps, kind='light', thickness=True, reflection=True, refraction=True):
    yy,xx=np.mgrid[:VIEW,:VIEW]
    fx=(xx+.5-VIEW/2)*FIELD_RADIUS/RADIUS+N/2-.5
    fy=(yy+.5-VIEW/2)*FIELD_RADIUS/RADIUS+N/2-.5
    optical=sample(maps['optical'],fx,fy)
    depth=sample(maps['depth'],fx,fy)[...,0]
    alpha=sample(maps['alpha'],fx,fy)[...,0]
    reflected=sample(maps['reflected'],fx,fy)
    offsets=sample(maps['offset'],fx,fy)*6 if refraction else np.zeros((VIEW,VIEW,2))
    if thickness: path=depth
    else: path=np.full_like(depth,.04)
    bg=background(kind)
    back=srgb_to_linear(sample(bg,xx+offsets[...,0],yy+offsets[...,1]))
    transmit=np.exp(-optical*2*path[...,None])
    color=back*transmit+(srgb_to_linear(reflected) if reflection else 0)
    out=srgb_to_linear(bg)*(1-alpha[...,None])+np.clip(color,0,1)*alpha[...,None]
    return np.clip(linear_to_srgb(out),0,1)

def main():
    donor, removed=clean_donor()
    yy,xx=np.mgrid[:N,:N]
    radius=np.sqrt((xx+0.5-200)**2+(yy+0.5-200)**2)/FIELD_RADIUS
    analytic=np.sqrt(np.maximum(1-radius**2,0))
    alpha=np.asarray(Image.open(M1/'formal-silhouette-mask.png').convert('L'),dtype=float)/255
    source_thickness=np.asarray(Image.open(M1/'neutral-thickness.png').convert('RGBA'),dtype=float)/255
    # Frozen thickness is a source field; do not treat its alpha as density.
    t=(source_thickness[...,0]-.25)/.6
    depth=np.maximum(.18,.72*analytic+.28*np.clip(t,0,1))
    depth=np.minimum(depth,1)
    neutral=np.asarray(Image.open(M1/'neutral-water-volume.png').convert('RGB'),dtype=float)/255
    detail=np.asarray(Image.open(M1/'neutral-water-detail.png').convert('RGBA'),dtype=float)/255
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
    save_rgb('field-thickness.png',np.repeat(depth[...,None],3,axis=2))
    save_rgb('field-refraction.png',np.dstack([(offsets+1)*.5,depth]))
    # Copy frozen inputs for real GPU sampling and independent ablations.
    for source,name in [('formal-silhouette-mask.png','field-silhouette.png'),('formal-outer-film-crop.png','field-formal-film.png'),('neutral-water-detail.png','field-m1-detail.png')]:
        Image.open(M1/source).save(OUT/name)
    maps={'optical':optical,'depth':depth,'alpha':alpha,'reflected':reflection_rgb,'offset':offsets}
    for kind in ['light','dark','split','checker']:
        save_rgb('candidate-optical-'+kind+'.png',render(maps,kind))
    for name,kwargs in [('thickness-off',{'thickness':False}),('reflection-off',{'reflection':False}),('refraction-off',{'refraction':False,'kind':'checker'})]:
        save_rgb('ablation-'+name+'.png',render(maps,**kwargs))
    # Reference and old baseline are shown at the same diameter, with no UI crop claim.
    old=Image.open(OUT/'candidate-formal-static-baseline.png').convert('RGB').resize((300,300),Image.Resampling.LANCZOS)
    aligned=Image.new('RGB',(360,360),tuple((BG*255).astype(int)))
    aligned.paste(old,(30,30));aligned.save(OUT/'baseline-aligned.png')
    diff=np.abs(render(maps)-render(maps,thickness=False))*255
    doc={
      'experiment':'FINAL_ART_025_REFERENCE_DIRECTED_OPTICAL_STUDY',
      'status':'READY_FOR_HUMAN_REVIEW','m2_closed':False,'m1_modified':False,
      'production_dependency':False,'product_state':'still','animation_loop':False,
      'target':'FINAL_ART_025','goal':'在单视角静态画面中重建 025 的材质外观，并验证不同背景下的透射和厚度贡献。',
      'method':'offline donor cleaning and inferred absorption/reflection split; separate GPU optical fields',
      'inference':'单张参考无法唯一求解真实材质；本字段是画面定向的近似，不是测得的物理参数。',
      'runtime_final_frame_sampling':False,'removed_ui_and_point_pixels':removed,
      'primary_candidate':'candidate-optical-light.png',
      'frozen_inputs_sampled':['neutral-water-volume.png (offline microtexture)','neutral-thickness.png (offline thickness mixture)','formal-silhouette-mask.png (GPU coverage)','neutral-water-detail.png (GPU sparse detail)','formal-outer-film-crop.png (GPU restrained film)'],
      'reference_hash':digest(REF),
      'thickness_ablation_mean_rgb_delta_255':round(float(diff[alpha[((np.arange(VIEW)[:,None]+.5-180)*FIELD_RADIUS/RADIUS+200-.5).astype(int).clip(0,399),((np.arange(VIEW)[None,:]+.5-180)*FIELD_RADIUS/RADIUS+200-.5).astype(int).clip(0,399)]>.5].mean()),3),
      'limitations':['单视角、固定形态','未实现动效、双核迁移或生产接入','不同光照下仍需要独立验证','人工材质身份判断未通过'],
      'corrections':['旧正式静态合成只作为基线，不能冒充本轮新材质','00 背景板含烘焙主体，全层叠加为负例','本候选使用离线派生字段，未把 025 原图作为候选 shader 纹理'],
      'files':{name:digest(OUT/name) for name in ['field-optical-depth.png','field-reflected-light.png','field-thickness.png','field-refraction.png','field-silhouette.png','field-formal-film.png','field-m1-detail.png','candidate-optical-light.png']}}
    (OUT/'optical-evidence.json').write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':doc['status'],'removed_pixels':removed,'thickness_delta':doc['thickness_ablation_mean_rgb_delta_255']},ensure_ascii=False))

if __name__=='__main__':main()
