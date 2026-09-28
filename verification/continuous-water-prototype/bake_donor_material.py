from __future__ import annotations
from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageEnhance
import numpy as np
ROOT=Path(__file__).resolve().parent; REF=ROOT/'references'; SIZE=400; CROP=(20,20,340,340)
def load_ref(name): return Image.open(REF/name).convert('RGB').crop(CROP).resize((SIZE,SIZE),Image.Resampling.LANCZOS)
def circle_mask(radius=176,center=(200,200),feather=10):
 yy,xx=np.mgrid[0:SIZE,0:SIZE]; d=np.sqrt((xx-center[0])**2+(yy-center[1])**2); return Image.fromarray(np.uint8(np.clip((radius+feather-d)/feather,0,1)*255),'L')
def feather_rect(box,blur=16):
 m=Image.new('L',(SIZE,SIZE),0); ImageDraw.Draw(m).rectangle(box,fill=255); return m.filter(ImageFilter.GaussianBlur(blur))
def remove_known_regions(img):
 arr=np.asarray(img).astype(np.float32).copy()
 # Remove source cores through translated local patch warps with a radial falloff.
 yy,xx=np.mgrid[0:SIZE,0:SIZE]
 cores=[((136-20)*1.25,(147-20)*1.25,56,(-60,28)),((228-20)*1.25,(210-20)*1.25,64,(-68,-28)),((252-20)*1.25,(246-20)*1.25,62,(-62,-34))]
 for cx,cy,r,(dx,dy) in cores:
  sx=np.clip(np.rint(xx+dx).astype(int),0,SIZE-1); sy=np.clip(np.rint(yy+dy).astype(int),0,SIZE-1)
  patch=arr[sy,sx][:,:,::-1]
  dist=np.sqrt((xx-cx)**2+(yy-cy)**2); w=np.clip(1-dist/(r*1.15),0,1)**2
  arr=arr*(1-w[...,None]*0.92)+patch*(w[...,None]*0.92)
  ring=(dist>=r*1.15)&(dist<=r*1.8)
  ring_rgb=arr[ring].mean(axis=0) if ring.any() else np.array([210,235,236],dtype=np.float32)
  neutral=np.clip(1-dist/(r*1.05),0,1)**1.15
  arr=arr*(1-neutral[...,None]*0.88)+ring_rgb[None,None,:]*(neutral[...,None]*0.88)
 # Fill the UI-covered upper interior with a translated, core-clean local donor band.
 # The source band is composited into the original over a broad vertical feather.
 original=arr.copy(); upper=arr[112:252,:,:].copy()
 for y in range(0,140):
  w=np.clip((132-y)/62,0,1)
  arr[y,:,:]=w*upper[y,:,:]+(1-w)*original[y,:,:]
 return Image.fromarray(np.uint8(np.clip(arr,0,255)),'RGB')
def donor_recompose(c025,c050):
 base=c025.filter(ImageFilter.GaussianBlur(1.6)); patches=[((68,82,168,182),(82,86,194,196),.045,7,False),((180,70,284,164),(206,82,326,190),.035,-9,True),((54,184,150,286),(56,178,180,302),.04,-5,True),((170,174,274,276),(186,178,320,310),.045,8,False),((102,238,206,322),(90,266,226,356),.03,5,True),((238,214,330,304),(246,226,354,334),.03,-6,False)]
 for src,dst,alpha,rot,mirror in patches:
  p=c025.crop(src).resize((dst[2]-dst[0],dst[3]-dst[1]),Image.Resampling.BICUBIC)
  if mirror:p=p.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
  p=p.rotate(rot,Image.Resampling.BICUBIC,expand=True).resize((dst[2]-dst[0],dst[3]-dst[1]),Image.Resampling.BICUBIC); m=Image.new('L',(SIZE,SIZE),0); ImageDraw.Draw(m).ellipse(dst,fill=int(alpha*255)); m=m.filter(ImageFilter.GaussianBlur(30)); base.paste(p,(dst[0],dst[1]),m.crop(dst))
 a=np.asarray(base).astype(np.float32); b=np.asarray(c050.filter(ImageFilter.GaussianBlur(18))).astype(np.float32); variation=np.clip((b.mean(2)-a.mean(2))/80,-.12,.12)[...,None]; composed=Image.fromarray(np.uint8(np.clip(a*(1+variation*.32),0,255)),'RGB'); return Image.blend(c025,composed,.42)
def save_volume(field,mask):
 arr=np.asarray(field).astype(np.float32); lum=arr.mean(2); density=np.clip(.30+np.clip((248-lum)/38,0,1)*.56,0,.86); alpha=np.asarray(mask).astype(np.float32)/255*density*255; norm=np.clip((arr-arr.min((0,1),keepdims=True))/(np.ptp(arr,axis=(0,1),keepdims=True)+1e-5),0,1); rgb=np.zeros_like(arr); rgb[...,0]=92+126*norm[...,0]; rgb[...,1]=166+66*norm[...,1]; rgb[...,2]=180+68*norm[...,2]; Image.fromarray(np.uint8(np.clip(np.dstack([rgb,alpha]),0,255)),'RGBA').save(ROOT/'neutral-water-volume.png')
def save_thickness(c025,c050,mask):
 yy,xx=np.mgrid[0:SIZE,0:SIZE]; r=np.sqrt(((xx-200)/176)**2+((yy-200)/176)**2); analytic=np.clip(np.sqrt(np.maximum(0,1-r*r)),0,1); low=np.asarray(c050.filter(ImageFilter.GaussianBlur(20))).astype(np.float32).mean(2); low=(low-low.min())/(np.ptp(low)+1e-5); mass=np.asarray(c025.filter(ImageFilter.GaussianBlur(16))).astype(np.float32).mean(2); mass=(mass-mass.min())/(np.ptp(mass)+1e-5); deep=np.clip(.68*analytic+.22*low+.10*mass,0,1); shallow=1-deep; medium=np.clip(1-np.abs(deep-.52)*1.8,0,1); rgb=np.dstack([shallow*210+20,medium*190+28,deep*205+25]); alpha=np.asarray(mask).astype(np.float32)*.86; Image.fromarray(np.uint8(np.clip(np.dstack([rgb,alpha]),0,255)),'RGBA').save(ROOT/'neutral-thickness.png'); return deep
def save_detail(c025,mask):
 gray=c025.convert('L'); fine=ImageChops.difference(gray,gray.filter(ImageFilter.GaussianBlur(7))); a=np.asarray(ImageEnhance.Contrast(fine).enhance(2.8)).astype(np.float32); keep=np.zeros((SIZE,SIZE),dtype=np.float32)
 for x0,y0,x1,y1 in [(72,106,172,166),(190,92,282,152),(82,194,158,256),(188,206,282,282),(110,278,224,340)]: keep[y0:y1,x0:x1]=1
 threshold=np.percentile(a[keep>0],72); detail=np.clip((a-threshold)/20,0,1)*keep; detail=np.asarray(Image.fromarray(np.uint8(detail*255),'L').filter(ImageFilter.GaussianBlur(2))).astype(np.float32)/255; detail*=np.asarray(mask).astype(np.float32)/255; rgba=np.dstack([np.full((SIZE,SIZE),112),np.full((SIZE,SIZE),194),np.full((SIZE,SIZE),201),detail*220]); Image.fromarray(np.uint8(np.clip(rgba,0,255)),'RGBA').save(ROOT/'neutral-water-detail.png')
def save_hero(field,mask,deep):
 yy,xx=np.mgrid[0:SIZE,0:SIZE]; r=np.sqrt((xx-200)**2+(yy-200)**2)/176; alpha=np.asarray(mask).astype(np.float32)/255; f=np.asarray(field).astype(np.float32); low=np.asarray(field.filter(ImageFilter.GaussianBlur(11))).astype(np.float32); low=(low-low.min((0,1),keepdims=True))/(np.ptp(low,axis=(0,1),keepdims=True)+1e-5); base=np.zeros((SIZE,SIZE,4),dtype=np.float32); base[...,0]=205+22*low[...,0]; base[...,1]=232+18*low[...,1]; base[...,2]=234+20*low[...,2]; base[...,3]=alpha*245; hero=Image.fromarray(np.uint8(base),'RGBA'); vol=np.asarray(Image.open(ROOT/'neutral-water-volume.png').convert('RGBA')).astype(np.float32); vol[...,3]*=(.58+.54*deep); hero=Image.alpha_composite(hero,Image.fromarray(np.uint8(np.clip(vol,0,255)),'RGBA')); veil=np.zeros_like(base); veil[...,0:3]=166,218,222; veil[...,3]=alpha*(16+30*(1-deep)); hero=Image.alpha_composite(hero,Image.fromarray(np.uint8(veil),'RGBA')); det=np.asarray(Image.open(ROOT/'neutral-water-detail.png').convert('RGBA')).astype(np.float32); det[...,3]*=1.0; hero=Image.alpha_composite(hero,Image.fromarray(np.uint8(np.clip(det,0,255)),'RGBA')); rim=np.asarray(Image.fromarray(np.uint8(np.clip((r-.84)/.16,0,1)*alpha*255),'L').filter(ImageFilter.GaussianBlur(3))).astype(np.float32)/255; membrane=np.zeros_like(base); membrane[...,0:3]=248,253,252; membrane[...,3]=rim*104; hero=Image.alpha_composite(hero,Image.fromarray(np.uint8(membrane),'RGBA')); hi=np.zeros_like(base); hi[...,0:3]=255,255,255; hi[...,3]=np.clip((r-.91)/.09,0,1)*alpha*np.clip(.32+.18*np.cos((xx-200)/65)+.10*np.cos((yy-200)/80),0,.6)*54; hero=Image.alpha_composite(hero,Image.fromarray(np.uint8(hi),'RGBA')); out=np.asarray(hero).copy(); out[...,3]=np.uint8(np.clip(out[...,3]*alpha,0,255)); Image.fromarray(out,'RGBA').save(ROOT/'m1-neutral-hero.png'); Image.fromarray(out,'RGBA').save(ROOT/'m1-neutral-source.png')
def main():
 c025=remove_known_regions(load_ref('final-art-025.png')); c050=remove_known_regions(load_ref('final-art-050.png')); field=remove_known_regions(donor_recompose(c025,c050)); mask=circle_mask(); save_volume(field,mask); deep=save_thickness(c025,c050,mask); save_detail(c025,mask); save_hero(field,mask,deep); meta={'route':'FINAL_ART_OFFLINE_DONOR_ROUTE','primaryDonor':'FINAL_ART_025','secondaryGuide':'FINAL_ART_050','upperBound':'FINAL_ART_075','endpoint':'FROZEN_K2','method':{'volume':'local donor patch recomposition after patch-inpainting UI text and cold/warm cores','thickness':'analytic sphere body thickness plus low-frequency 025/050 local mass variation; RGB shallow/medium/deep encoding','detail':'band-pass extraction from cleaned 025, sparse region selection, low-contrast alpha','hero':'formal outer membrane + baked volume + baked depth-controlled veil + sparse donor detail'},'forbidden':['runtime_direct_sampling','full_frame_state_crossfade','canonical_final_frame_texture','production_dependency'],'coreResidue':'NONE_BY_MASKED_PATCH_RECONSTRUCTION','threeJS':'NOT_JUSTIFIED'}; (ROOT/'donor-baking-manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
