#!/usr/bin/env python3
"""Build an A-authority / B-internal-texture verification study.

A is the user-selected static K2 authority. B is only used as a texture and
flow-organization reference inside the interior mask; shell and core remain A.
No runtime, production, or interpolation is implemented here.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
from PIL import Image, ImageFilter

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'test/water-orb-still/2p5d-composite-v1'
OUT=Path(__file__).resolve().parent/'k2-authority-study'
BBOX=(88,586,766,1265)
SIZE=360

def read_crop(path):
    return np.asarray(Image.open(path).convert('RGB').crop(BBOX).resize((SIZE,SIZE),Image.Resampling.LANCZOS),dtype=np.float64)/255

def save(name,a):
    Image.fromarray(np.uint8(np.clip(a,0,1)*255+0.5),'RGB').save(OUT/name)

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()

OUT.mkdir(exist_ok=True)
a=read_crop(SOURCE/'static_composite.png')
b=read_crop(SOURCE/'reference_foundation.png')
Y,X=np.mgrid[:SIZE,:SIZE]
r=np.sqrt((X-(SIZE-1)/2)**2+(Y-(SIZE-1)/2)**2)/(SIZE*.46)
interior=np.clip((.86-r)/.12,0,1)
core_path=ROOT/'verification/final-art-025-material-test/k2-source-study/field-core-mask-candidate.png'
core=np.asarray(Image.open(core_path).convert('RGBA').resize((SIZE,SIZE),Image.Resampling.LANCZOS),dtype=np.float64)/255
source_core=[]
for name in ['07_cool_point_core.png','08_cool_point_glow.png','09_warm_point_core.png','10_warm_point_glow.png']:
    layer=np.asarray(Image.open(SOURCE/'layers'/name).convert('RGBA').crop(BBOX).resize((SIZE,SIZE),Image.Resampling.LANCZOS),dtype=np.float64)/255
    source_core.append(layer[...,3])
core_mask=np.maximum.reduce(source_core)
core_mask=np.asarray(Image.fromarray(np.uint8(core_mask*255)).filter(ImageFilter.MaxFilter(17)),dtype=np.float64)/255
mask=interior*(1-np.clip(core_mask*8.0,0,1))
mask=np.clip(mask*.72,0,1)
delta=b-a
candidate=np.clip(a+delta*mask[...,None],0,1)
# The delta view is centered and contrast-boosted for human inspection.
delta_view=np.clip(.5+delta*2.4,0,1)
mask_view=np.repeat(mask[...,None],3,axis=2)
save('a-authority.png',a)
save('b-internal-reference.png',b)
save('a-authority-b-internal-study.png',candidate)
save('b-internal-delta.png',delta_view)
save('b-internal-mask.png',mask_view)
outer=r>.86
core_region=core_mask>.2
interior_region=mask>.05
candidate_a_diff=np.abs(candidate-a)*255
metrics={
 'cycle':2,
 'authority':'A_static_composite',
 'secondary_reference':'B_reference_foundation_internal_texture_only',
 'shell_preservation_mean_abs_rgb_255':round(float(candidate_a_diff[outer].mean()),4),
 'core_preservation_mean_abs_rgb_255':round(float(candidate_a_diff[core_region].mean()),4) if core_region.any() else 0,
 'interior_texture_delta_mean_abs_rgb_255':round(float(np.abs(delta[interior_region]).mean()*255),4),
 'study_mask_coverage':round(float(interior_region.mean()),6),
 'runtime':False,
 'production':False,
}
report={
 'schema':'mindisle.k2-authority-study.v1',
 'status':'HUMAN_REVIEW_PASS__K2_STATIC_CANDIDATE_LOCKED',
 'scope':'A fixed K2 static authority with B interior texture study; no runtime interpolation',
 'authority':{'id':'A','file':'test/water-orb-still/2p5d-composite-v1/static_composite.png','role':'FROZEN_STATIC_K2_AUTHORITY'},
 'secondary_reference':{'id':'B','file':'test/water-orb-still/2p5d-composite-v1/reference_foundation.png','role':'INTERIOR_TEXTURE_AND_FLOW_REFERENCE_ONLY','core':'NOT_INHERITED'},
 'candidate':'a-authority-b-internal-study.png',
 'mask':'b-internal-mask.png',
 'delta':'b-internal-delta.png',
 'metrics':metrics,
 'human_review':{'status':'PASS','recorded':'2026-10-03','verdict':'A shell/core + B interior 最好','locked_candidate':'a-authority-b-internal-study.png'},
 'decision':'Lock A shell/core with B interior organization as the best current K2 static candidate; independent movable field proof is still required.',
 'boundaries':['no ProductState','no formation/deformation','no core movement','no moving','no production migration','no runtime interpolation'],
 'files_sha256':{p.name:digest(p) for p in sorted(OUT.glob('*.png'))}
}
(OUT/'k2-authority-study.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
(OUT/'README.md').write_text('# K2 A-authority / B-internal study\n\nA 是用户选定的 K2 静态 authority。B 只提供内部纹理和流向参考，shell 与 core 保持 A。此页不实现动态、不接入 production。\n')
print(json.dumps({'status':report['status'],'metrics':metrics},ensure_ascii=False))
