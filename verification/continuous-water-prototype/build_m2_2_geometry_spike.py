from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageFilter

ROOT=Path(__file__).parent
W=H=512

def load(name): return np.asarray(Image.open(ROOT/name).convert('RGBA').resize((W,H), Image.Resampling.LANCZOS)).astype(np.float32)/255
bg=np.array([0.91,0.965,0.97],dtype=np.float32)
vol=load('neutral-water-volume.png')
mask=load('formal-silhouette-mask.png')[...,0]
film=load('formal-outer-film-crop.png')
base=vol[...,:3]
# Source-derived palette: no external color asset.
mean=np.sum(base*mask[...,None],axis=(0,1))/max(mask.sum(),1)
water=np.array([0.30*mean[0]+0.10,0.38*mean[1]+0.10,0.50*mean[2]+0.12],dtype=np.float32)
inner=np.array([0.12*mean[0]+0.02,0.28*mean[1]+0.06,0.34*mean[2]+0.08],dtype=np.float32)
light=np.clip(0.75*mean+0.25*np.array([0.96,1.0,1.0]),0,1)
Y,X=np.mgrid[0:H,0:W]; x=X/(W-1)*2-1; y=Y/(H-1)*2-1
sphere=np.clip(1-x*x-y*y,0,1); body=np.clip(mask,0,1)*np.sqrt(sphere)

def bezier(points,t):
    p=np.array(points,dtype=np.float32)
    a=(1-t)**3; b=3*(1-t)**2*t; c=3*(1-t)*t*t; d=t**3
    return a[:,None]*p[0]+b[:,None]*p[1]+c[:,None]*p[2]+d[:,None]*p[3]

def curve_distance(points):
    ts=np.linspace(0,1,180)
    pts=bezier(points,ts)
    px=pts[:,0]; py=pts[:,1]
    # normalized screen coordinate to nearest polyline sample
    dx=x[...,None]-px[None,None,:]; dy=y[...,None]-py[None,None,:]
    return np.sqrt(dx*dx+dy*dy).min(axis=2)

def ribbon(points,width,alpha,color,blur=0):
    d=curve_distance(points)
    a=np.exp(-((d/max(width,1e-4))**2)*2.2)*alpha*body
    if blur:
        im=Image.fromarray(np.round(a*255).astype(np.uint8),'L').filter(ImageFilter.GaussianBlur(blur))
        a=np.asarray(im).astype(np.float32)/255
    return color[None,None,:],a

def over(rgb, a, c, ca):
    oa=np.clip(ca,0,1)
    return rgb*(1-oa[...,None])+c*oa[...,None], a+oa*(1-a)

rgb=base*0.28 + water[None,None,:]*0.72
alpha=body*0.36
layers=[]
# Two broad internal masses provide the depth anchors seen in the reference family.
# Their palette is sampled from the frozen neutral volume; their positions are the
# geometry-route experiment, not a new M1 authority.
blob_a=np.exp(-(((x+0.22)/0.34)**2+((y+0.14)/0.25)**2)*2.1)*body*0.58
blob_b=np.exp(-(((x-0.22)/0.30)**2+((y-0.18)/0.31)**2)*2.0)*body*0.46
rgb,alpha=over(rgb,alpha,inner[None,None,:],blob_a)
layers.append(blob_a)
rgb,alpha=over(rgb,alpha,water[None,None,:]*0.78+light[None,None,:]*0.22,blob_b)
layers.append(blob_b)
# Rear mass: broad cool/teal arc. Geometry is the carrier; source palette is frozen-derived.
for pts,w,a,c,b in [
    ([(-0.72,-0.04),(-0.34,-0.60),(0.20,-0.54),(0.68,-0.10)],0.22,0.56,inner,15),
    ([(-0.60,0.36),(-0.22,0.74),(0.36,0.56),(0.70,0.20)],0.18,0.46,water,12),
    ([(-0.64,0.10),(-0.12,-0.12),(0.25,0.22),(0.60,0.04)],0.10,0.50,light,8),
    ([(-0.46,0.40),(-0.04,0.08),(0.31,-0.03),(0.50,-0.36)],0.07,0.38,light,5),
]:
    c0,aa=ribbon(pts,w,a,c,b); rgb,alpha=over(rgb,alpha,c0,aa); layers.append(aa)
# Subtle interior shade from the two primary bands; this makes the depth readable without fake edge-rim.
structure=np.clip((layers[0]*0.9+layers[1]*0.75),0,1)
rgb=np.clip(rgb*(1-0.28*structure[...,None]),0,1)
# Frozen shell is composited last and remains the only outer-film source.
shella=film[...,3]*0.72
rgb,alpha=over(rgb,alpha,film[...,:3],shella)
out=rgb*alpha[...,None]+bg[None,None,:]*(1-alpha[...,None])
out[body<0.01]=bg
Image.fromarray(np.round(np.clip(out,0,1)*255).astype(np.uint8),'RGB').save(ROOT/'m2.2-g-geometry-spike.png')
# Debug layers and a side-by-side montage.
for i,a in enumerate(layers):
    Image.fromarray(np.round(np.clip(a,0,1)*255).astype(np.uint8),'L').save(ROOT/f'm2.2-g-layer-{i+1}.png')
mont=Image.new('RGB',(1024,512),(232,246,247))
hero=Image.open(ROOT/'m2.2-g-geometry-spike.png').convert('RGB')
mont.paste(hero,(0,0)); right=Image.new('RGB',(512,512),(19,57,64));
for i,a in enumerate(layers):
    tile=Image.fromarray(np.round(np.clip(a,0,1)*255).astype(np.uint8),'L').convert('RGB').resize((170,240))
    right.paste(tile,((i%3)*170,(i//3)*256))
mont.paste(right,(512,0)); mont.save(ROOT/'m2.2-g-geometry-layer-montage.png')
metrics={'representation':'geometry-alternative-spike','carrier':'analytic sphere domain + two derived mass anchors + four translucent internal sheets','sourcePalette':'derived from neutral-water-volume.rgb','shell':'formal-outer-film alpha-aware frozen','productionDependency':False,'m1SourcesModified':False,'layers':6,'visualStatus':'AWAITING_HUMAN_REVIEW'}
(ROOT/'m2.2-g-geometry-evidence.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(metrics,ensure_ascii=False,indent=2))
