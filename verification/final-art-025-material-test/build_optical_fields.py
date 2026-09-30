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

def crop_detail(rgb):
    return np.asarray(Image.fromarray(np.uint8(np.clip(rgb,0,1)*255+.5)).crop((60,60,300,300)).resize((360,360),Image.Resampling.LANCZOS),dtype=np.float64)/255

def read_disk_fields():
    optical_rgba=np.asarray(Image.open(OUT/'field-optical-depth.png').convert('RGBA'),dtype=np.float64)/255
    reflected=np.asarray(Image.open(OUT/'field-reflected-light.png').convert('RGB'),dtype=np.float64)/255
    depth=np.asarray(Image.open(OUT/'field-thickness.png').convert('RGB'),dtype=np.float64)/255
    refraction=np.asarray(Image.open(OUT/'field-refraction.png').convert('RGB'),dtype=np.float64)/255
    silhouette=np.asarray(Image.open(OUT/'field-silhouette.png').convert('L'),dtype=np.float64)/255
    film=np.asarray(Image.open(OUT/'field-formal-film.png').convert('RGBA'),dtype=np.float64)/255
    detail=np.asarray(Image.open(OUT/'field-m1-detail.png').convert('RGBA'),dtype=np.float64)/255
    return {
        'optical':optical_rgba[...,:3],
        'depth':depth[...,0],
        'alpha':np.minimum(optical_rgba[...,3],silhouette),
        'reflected':reflected,
        'offset':refraction[...,:2]*2-1,
        'film':film,
        'detail':detail,
        'depth_mean':float(depth[...,0][silhouette>.5].mean()),
    }

def render(maps, kind='light', thickness_mode='spatial', reflection=True, refraction=True, film=True, detail=True, interior_lift=0.0, interior_cool=(0.0,0.0,0.0)):
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
    color=back*transmit+(srgb_to_linear(reflected) if reflection else 0)
    if film:
        film_field=sample(maps['film'],fx,fy)
        film_rgb=srgb_to_linear(film_field[...,:3])
        film_alpha=film_field[...,3]
    color += film_rgb*film_alpha[...,None]*.24
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
    # Copy frozen inputs for future GPU sampling and independent ablations.
    for source,name in [('formal-silhouette-mask.png','field-silhouette.png'),('formal-outer-film-crop.png','field-formal-film.png'),('neutral-water-detail.png','field-m1-detail.png')]:
        Image.open(M1/source).save(OUT/name)
    detail_field=np.asarray(Image.open(OUT/'field-m1-detail.png').convert('RGBA'),dtype=np.float64)/255
    film_field=np.asarray(Image.open(OUT/'field-formal-film.png').convert('RGBA'),dtype=np.float64)/255
    maps={'optical':optical,'depth':depth,'alpha':alpha,'reflected':reflection_rgb,'offset':offsets,'film':film_field,'detail':detail_field,'depth_mean':float(depth[alpha>.5].mean())}
    memory_maps=maps.copy()
    # The primary candidate is rendered from the exported PNG fields, not from
    # the in-memory arrays that created them.
    disk_maps=read_disk_fields()
    for kind in ['light','dark','split','checker']:
        candidate=render(disk_maps,kind)
        save_rgb('candidate-optical-'+kind+'.png',candidate)
        save_rgb('candidate-optical-'+kind+'-detail.png',crop_detail(candidate))
        cooler=render(disk_maps,kind,interior_lift=.22,interior_cool=(-.028,.018,.055))
        save_rgb('candidate-optical-'+kind+'-cooler.png',cooler)
        save_rgb('candidate-optical-'+kind+'-cooler-detail.png',crop_detail(cooler))
        matched=render(disk_maps,kind,thickness_mode='mean_match')
        save_rgb('ablation-'+kind+'-thickness-mean-match.png',matched)
        save_rgb('ablation-'+kind+'-thickness-mean-match-detail.png',crop_detail(matched))
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
    roundtrip_delta=np.abs(memory_render-disk_render)*255
    level_delta=np.abs(disk_render-old_constant)*255
    spatial_delta=np.abs(disk_render-mean_match)*255
    doc={
      'experiment':'FINAL_ART_025_REFERENCE_DIRECTED_OPTICAL_STUDY',
      'status':'READY_FOR_HUMAN_REVIEW','m2_closed':False,'m1_modified':False,
      'production_dependency':False,'product_state':'still','animation_loop':False,
      'target':'FINAL_ART_025','goal':'在单视角静态画面中重建 025 的材质外观，并验证不同背景下的透射和厚度贡献。',
      'method':'formal static baseline donor; inferred absorption/reflection split; PNG field export and disk roundtrip reconstruction',
      'inference':'单张参考无法唯一求解真实材质；本字段是画面定向的近似，不是测得的物理参数。',
      'runtime_final_frame_sampling':False,'gpu_material_renderer':False,
      'actual_primary_donor':{'file':'candidate-formal-static-baseline.png','role':'primary offline donor','used_for_primary':True},
      'final_art_025_diagnostic':{'file':'target-final-art-025.png','role':'visual target and donor-cleaning diagnostic only','used_for_primary':False,'removed_ui_and_point_pixels_diagnostic':removed},
      'primary_candidate':'candidate-optical-light-cooler.png',
      'interior_tone_adjustment':{'interior_lift':0.22,'interior_cool_rgb':[-0.028,0.018,0.055],'scope':'interior mass only; outer film, silhouette and point positions unchanged'},
      'frozen_inputs_sampled':['neutral-water-volume.png (offline microtexture)','neutral-thickness.png (offline thickness mixture)','formal-silhouette-mask.png (coverage)','neutral-water-detail.png (detail modulation in render)','formal-outer-film-crop.png (film contribution in render)'],
      'field_usage':{'formal_film_used_in_current_render':True,'m1_detail_used_in_current_render':True,'future_gpu_input_only':True},
      'reference_hash':digest(REF),
      'field_png_roundtrip':{'max_rgb_delta_255':round(float(roundtrip_delta[inside].max()),4),'mean_rgb_delta_255':round(float(roundtrip_delta[inside].mean()),4),'status':'RECONSTRUCTED_FROM_DISK_FIELDS'},
      'thickness_ablation':{'constant_004_mean_rgb_delta_255':round(float(level_delta[inside].mean()),3),'spatial_vs_mean_matched_rgb_delta_255':round(float(spatial_delta[inside].mean()),3),'depth_mean':maps['depth_mean']},
      'limitations':['单视角、固定形态','未实现动效、双核迁移或生产接入','不同光照下仍需要独立验证','人工材质身份判断未通过'],
      'corrections':['旧正式静态合成只作为基线，不能冒充本轮新材质','00 背景板含烘焙主体，全层叠加为负例','本候选使用离线派生字段，未把 025 原图作为候选 shader 纹理'],
      'files':{name:digest(OUT/name) for name in ['field-optical-depth.png','field-reflected-light.png','field-thickness.png','field-refraction.png','field-silhouette.png','field-formal-film.png','field-m1-detail.png','candidate-optical-light.png','candidate-optical-light-cooler.png','candidate-optical-light-cooler-detail.png','ablation-light-thickness-mean-match.png']}}
    (OUT/'optical-evidence.json').write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':doc['status'],'diagnostic_removed_pixels':removed,'thickness_ablation':doc['thickness_ablation'],'field_png_roundtrip':doc['field_png_roundtrip']},ensure_ascii=False))

if __name__=='__main__':main()
