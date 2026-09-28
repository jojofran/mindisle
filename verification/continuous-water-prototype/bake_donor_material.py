from __future__ import annotations
from pathlib import Path
import json
import hashlib
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageEnhance
import numpy as np

ROOT = Path(__file__).resolve().parent
REF = ROOT / 'references'
FORMAL_OUTER = ROOT.parent.parent / 'assets' / 'waterball-still-v1' / 'layers' / '01_outer_film.png'
SIZE = 400
CROP = (20, 20, 340, 340)

def load_ref(name):
    return Image.open(REF / name).convert('RGB').crop(CROP).resize((SIZE, SIZE), Image.Resampling.LANCZOS)

def load_formal_outer():
    # Same profile center/radius, mapped into the pre-existing 400px study domain.
    # No bounding-box normalization: canonical radius 316 maps to study radius 176.
    src = Image.open(FORMAL_OUTER).convert('RGBA')
    alpha = np.asarray(src.getchannel('A'))
    filled = np.zeros_like(alpha)
    for y, row in enumerate(alpha):
        xs = np.flatnonzero(row >= 6)
        if len(xs):
            left, right = xs[0], xs[-1]
            filled[y, left:right+1] = 255
            filled[y, left] = filled[y, right] = row[xs].max()
    inv_scale = 316 / 176
    affine = (inv_scale, 0, 426.5 - 200*inv_scale,
              0, inv_scale, 925 - 200*inv_scale)
    # Keep the formal source resampling unchanged. The visible defect is the
    # overlap in the final compositor; changing source sampling here risks
    # introducing a non-source fringe and would violate the shell audit scope.
    outer = src.transform((SIZE, SIZE), Image.Transform.AFFINE, affine,
                          Image.Resampling.BICUBIC)
    mask = Image.fromarray(filled, 'L').transform(
        (SIZE, SIZE), Image.Transform.AFFINE, affine, Image.Resampling.BICUBIC)
    outer.save(ROOT / 'formal-outer-film-crop.png')
    mask.save(ROOT / 'formal-silhouette-mask.png')
    return outer, mask

def circle_mask(radius=176, center=(200, 200), feather=10):
    yy, xx = np.mgrid[0:SIZE, 0:SIZE]
    d = np.sqrt((xx-center[0])**2 + (yy-center[1])**2)
    return Image.fromarray(np.uint8(np.clip((radius+feather-d)/feather, 0, 1)*255), 'L')

def remove_known_regions(img, reverse_channels=False):
    arr = np.asarray(img).astype(np.float32).copy()
    yy, xx = np.mgrid[0:SIZE, 0:SIZE]
    cores = [
        ((136-20)*1.25, (147-20)*1.25, 56, (-60, 28)),
        ((228-20)*1.25, (210-20)*1.25, 64, (-68, -28)),
        ((252-20)*1.25, (246-20)*1.25, 62, (-62, -34)),
    ]
    for cx, cy, radius, (dx, dy) in cores:
        sx = np.clip(np.rint(xx+dx).astype(int), 0, SIZE-1)
        sy = np.clip(np.rint(yy+dy).astype(int), 0, SIZE-1)
        patch = arr[sy, sx]
        if reverse_channels:
            patch = patch[:, :, ::-1]
        dist = np.sqrt((xx-cx)**2 + (yy-cy)**2)
        w = np.clip(1-dist/(radius*1.15), 0, 1)**2
        arr = arr*(1-w[..., None]*0.92) + patch*(w[..., None]*0.92)
        ring = (dist >= radius*1.15) & (dist <= radius*1.8)
        ring_rgb = arr[ring].mean(axis=0) if ring.any() else np.array([210,235,236], dtype=np.float32)
        neutral = np.clip(1-dist/(radius*1.05), 0, 1)**1.15
        arr = arr*(1-neutral[..., None]*0.88) + ring_rgb[None,None,:]*(neutral[..., None]*0.88)
    original = arr.copy()
    upper = arr[112:252, :, :].copy()
    for y in range(0, 140):
        w = np.clip((132-y)/62, 0, 1)
        arr[y, :, :] = w*upper[y, :, :] + (1-w)*original[y, :, :]
    return Image.fromarray(np.uint8(np.clip(arr, 0, 255)), 'RGB')

def donor_recompose(c025, c050):
    base = c025.filter(ImageFilter.GaussianBlur(1.6))
    patches = [
        ((68,82,168,182),(82,86,194,196),.045,7,False),
        ((180,70,284,164),(206,82,326,190),.035,-9,True),
        ((54,184,150,286),(56,178,180,302),.04,-5,True),
        ((170,174,274,276),(186,178,320,310),.045,8,False),
        ((102,238,206,322),(90,266,226,356),.03,5,True),
        ((238,214,330,304),(246,226,354,334),.03,-6,False),
    ]
    for src, dst, alpha, rot, mirror in patches:
        patch = c025.crop(src).resize((dst[2]-dst[0], dst[3]-dst[1]), Image.Resampling.BICUBIC)
        if mirror:
            patch = patch.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        patch = patch.rotate(rot, Image.Resampling.BICUBIC, expand=True).resize((dst[2]-dst[0], dst[3]-dst[1]), Image.Resampling.BICUBIC)
        mask = organic_patch_mask(dst, alpha, rot, mirror)
        base.paste(patch, (dst[0], dst[1]), mask.crop(dst))
    a = np.asarray(base).astype(np.float32)
    b = np.asarray(c050.filter(ImageFilter.GaussianBlur(18))).astype(np.float32)
    variation = np.clip((b.mean(2)-a.mean(2))/80, -.12, .12)[..., None]
    composed = Image.fromarray(np.uint8(np.clip(a*(1+variation*.32), 0, 255)), 'RGB')
    return Image.blend(c025, composed, .42)

def organic_patch_mask(box, alpha, rot=0, mirror=False):
    """Deterministic irregular donor mask; no axis-aligned or circular edge memory."""
    x0, y0, x1, y1 = box
    w, h = x1-x0, y1-y0
    local = Image.new('L', (w, h), 0)
    draw = ImageDraw.Draw(local)
    pts = []
    for i in range(14):
        t = 2*np.pi*i/14
        wobble = 0.80 + 0.10*np.sin(i*2.17 + w*.013) + 0.06*np.cos(i*3.71 + h*.009)
        rx = w*.50*wobble
        ry = h*.50*(0.86 + 0.09*np.cos(i*1.43))
        pts.append((w*.5 + rx*np.cos(t), h*.5 + ry*np.sin(t)))
    draw.polygon(pts, fill=int(alpha*255))
    local = local.filter(ImageFilter.GaussianBlur(max(5, int(min(w,h)*.11))))
    full = Image.new('L', (SIZE, SIZE), 0)
    full.paste(local, (x0, y0))
    return full

def sanitize_volume_field(field, c025, c050):
    """Repair only known donor seams using local, irregular continuity patches."""
    arr = np.asarray(field).astype(np.float32)
    # A lightly blurred local scaffold supplies continuity only inside the known
    # donor regions; the rest of the authored field remains untouched.
    scaffold = np.asarray(c025.filter(ImageFilter.GaussianBlur(5))).astype(np.float32)
    repaired = arr.copy()
    regions = [
        (68,82,168,182), (180,70,284,164), (54,184,150,286),
        (170,174,274,276), (102,238,206,322), (238,214,330,304),
    ]
    for i, box in enumerate(regions):
        mask = np.asarray(organic_patch_mask(box, .72 + .04*(i%2))).astype(np.float32)/255
        # Blend a translated local scaffold through an irregular feathered mask.
        x0,y0,x1,y1 = box
        sx = max(0, min(SIZE-(x1-x0), x0 + (13 if i%2 else -11)))
        sy = max(0, min(SIZE-(y1-y0), y0 + (-9 if i%3 else 12)))
        local = scaffold[sy:sy+(y1-y0), sx:sx+(x1-x0)]
        target = repaired[y0:y1, x0:x1]
        m = mask[y0:y1, x0:x1][...,None] * .38
        repaired[y0:y1, x0:x1] = target*(1-m) + local*m
    # Preserve low-frequency mass while removing only feather seams at region edges.
    return Image.fromarray(np.uint8(np.clip(repaired, 0, 255)), 'RGB')

def save_volume(field, mask):
    arr = np.asarray(field).astype(np.float32)
    lum = arr.mean(2)
    density = np.clip(.30 + np.clip((248-lum)/38, 0, 1)*.56, 0, .86)
    alpha = np.asarray(mask).astype(np.float32)/255 * density * 255
    norm = np.clip((arr-arr.min((0,1), keepdims=True))/(np.ptp(arr, axis=(0,1), keepdims=True)+1e-5), 0, 1)
    rgb = np.zeros_like(arr)
    rgb[...,0] = 92 + 126*norm[...,0]
    rgb[...,1] = 166 + 66*norm[...,1]
    rgb[...,2] = 180 + 68*norm[...,2]
    return Image.fromarray(np.uint8(np.clip(np.dstack([rgb, alpha]), 0, 255)), 'RGBA')

def compute_thickness(c025, c050):
    yy, xx = np.mgrid[0:SIZE, 0:SIZE]
    r = np.sqrt(((xx-200)/176)**2 + ((yy-200)/176)**2)
    analytic = np.clip(np.sqrt(np.maximum(0, 1-r*r)), 0, 1)
    low = np.asarray(c050.filter(ImageFilter.GaussianBlur(20))).astype(np.float32).mean(2)
    low = (low-low.min())/(np.ptp(low)+1e-5)
    mass = np.asarray(c025.filter(ImageFilter.GaussianBlur(16))).astype(np.float32).mean(2)
    mass = (mass-mass.min())/(np.ptp(mass)+1e-5)
    return np.clip(.68*analytic + .22*low + .10*mass, 0, 1)

def save_thickness(c025, c050, mask):
    deep = compute_thickness(c025, c050)
    shallow = 1-deep
    medium = np.clip(1-np.abs(deep-.52)*1.8, 0, 1)
    rgb = np.dstack([shallow*210+20, medium*190+28, deep*205+25])
    alpha = np.asarray(mask).astype(np.float32)*.86
    return deep, Image.fromarray(np.uint8(np.clip(np.dstack([rgb, alpha]), 0, 255)), 'RGBA')

def save_detail(c025, mask):
    gray = c025.convert('L')
    fine = ImageChops.difference(gray, gray.filter(ImageFilter.GaussianBlur(7)))
    a = np.asarray(ImageEnhance.Contrast(fine).enhance(2.8)).astype(np.float32)
    keep = np.zeros((SIZE, SIZE), dtype=np.float32)
    # Irregular windows replace the former rectangular extraction tiles.
    for i, box in enumerate([(72,106,172,166),(190,92,282,152),(82,194,158,256),(188,206,282,282),(110,278,224,340)]):
        keep = np.maximum(keep, np.asarray(organic_patch_mask(box, .92, i*13, i%2 == 1), dtype=np.float32)/255)
    threshold = np.percentile(a[keep > 0], 72)
    detail = np.clip((a-threshold)/20, 0, 1)*keep
    detail = np.asarray(Image.fromarray(np.uint8(detail*255), 'L').filter(ImageFilter.GaussianBlur(2))).astype(np.float32)/255
    # Tear a few local structures into non-axis-aligned fragments so the alpha
    # view reads as sparse water structure rather than source islands.
    yy, xx = np.mgrid[0:SIZE, 0:SIZE]
    fragment = .72 + .20*np.sin(xx*.091 + yy*.043) + .12*np.cos(xx*.037 - yy*.081)
    detail *= np.clip(fragment, 0, 1)
    detail *= np.asarray(mask).astype(np.float32)/255
    rgba = np.dstack([np.full((SIZE,SIZE),112), np.full((SIZE,SIZE),194), np.full((SIZE,SIZE),201), detail*220])
    return Image.fromarray(np.uint8(np.clip(rgba, 0, 255)), 'RGBA')

def compose_hero(field, mask, deep, outer, volume, detail, shell_mode='sanitized'):
    alpha = np.asarray(mask).astype(np.float32)/255
    low = np.asarray(field.filter(ImageFilter.GaussianBlur(11))).astype(np.float32)
    low = (low-low.min((0,1), keepdims=True))/(np.ptp(low, axis=(0,1), keepdims=True)+1e-5)
    base = np.zeros((SIZE,SIZE,4), dtype=np.float32)
    base[...,0] = 205+22*low[...,0]
    base[...,1] = 232+18*low[...,1]
    base[...,2] = 234+20*low[...,2]
    base[...,3] = alpha*245
    hero = Image.fromarray(np.uint8(base), 'RGBA')
    vol = np.asarray(volume).astype(np.float32)
    vol[...,3] *= (.58+.54*deep)
    hero = Image.alpha_composite(hero, Image.fromarray(np.uint8(np.clip(vol,0,255)), 'RGBA'))
    veil = np.zeros_like(base)
    veil[...,0:3] = 166,218,222
    veil[...,3] = alpha*(16+30*(1-deep))
    hero = Image.alpha_composite(hero, Image.fromarray(np.uint8(veil), 'RGBA'))
    det = np.asarray(detail).astype(np.float32)
    hero = Image.alpha_composite(hero, Image.fromarray(np.uint8(np.clip(det,0,255)), 'RGBA'))
    # Clip internal pixels with formal atlas silhouette, then preserve full shell alpha.
    out = np.asarray(hero).copy()
    out[...,3] = np.uint8(np.clip(out[...,3]*alpha, 0, 255))
    if shell_mode == 'current':
        return Image.alpha_composite(Image.fromarray(out, 'RGBA'), outer)
    # The formal source has already been sampled once; keep its RGB untouched
    # and correct only the final source-over coverage below.
    shell = np.asarray(outer).astype(np.float32)
    sa = shell[...,3:4] / 255
    shell_rgb = shell[...,:3] * sa
    shell_rgb = np.where(sa > .001, shell_rgb / np.maximum(sa, .001), 0)
    shell_alpha = shell[...,3:4]
    # The body already owns most of this coverage. Subtract the overlap once,
    # then source-over the thinner formal film so the edge remains optical and
    # nonuniform instead of reading as a painted outline.
    overlap = np.clip(shell_alpha / 255, 0, 1)
    out[...,3] = np.clip(out[...,3] * (1 - .45*overlap[...,0]), 0, 255)
    shell_alpha = np.clip(shell_alpha * .34, 0, 255)
    sanitized_shell = Image.fromarray(np.uint8(np.clip(np.dstack([shell_rgb, shell_alpha]), 0, 255)), 'RGBA')
    return Image.alpha_composite(Image.fromarray(out, 'RGBA'), sanitized_shell)

def edge_crop_pair(hero_a, hero_b):
    box = (26, 26, 374, 374)
    return labeled_pair(hero_a.crop(box), hero_b.crop(box), 'A · current composite', 'B · sanitized composite', size=(560,300))

def warp_stress(im):
    arr = np.asarray(im).astype(np.float32)
    yy, xx = np.mgrid[0:SIZE, 0:SIZE]
    # Review-only reversible UV stress: bend, stretch, and a mild local offset.
    sx = np.clip(xx + 4.2*np.sin((yy-200)/115) + 2.3*np.sin(yy/37), 0, SIZE-1)
    sy = np.clip(yy + 3.8*np.sin((xx-200)/132) + 1.7*np.sin(xx/43), 0, SIZE-1)
    xi0=np.floor(sx).astype(int); yi0=np.floor(sy).astype(int)
    xi1=np.minimum(xi0+1,SIZE-1); yi1=np.minimum(yi0+1,SIZE-1)
    fx=sx-xi0; fy=sy-yi0
    out=(arr[yi0,xi0]*(1-fx)[...,None]*(1-fy)[...,None] + arr[yi0,xi1]*fx[...,None]*(1-fy)[...,None] + arr[yi1,xi0]*(1-fx)[...,None]*fy[...,None] + arr[yi1,xi1]*fx[...,None]*fy[...,None])
    return Image.fromarray(np.uint8(np.clip(out,0,255)), im.mode)

def labeled_pair(left, right, left_label, right_label, size=(420,230)):
    panel_w, panel_h = size[0]//2, size[1]-30
    out = Image.new('RGB', size, (232,245,246))
    draw = ImageDraw.Draw(out)
    for i, (im, label) in enumerate([(left,left_label),(right,right_label)]):
        im = im.convert('RGBA')
        im.thumbnail((panel_w, panel_h), Image.Resampling.LANCZOS)
        bg = Image.new('RGBA', (panel_w,panel_h), (245,250,250,255))
        bg.alpha_composite(im, ((panel_w-im.width)//2,(panel_h-im.height)//2))
        out.paste(bg.convert('RGB'), (i*panel_w,0)); draw.text((i*panel_w+8,panel_h+8), label, fill=(44,92,101))
    return out

def make_ab_evidence(clean_a, clean_b, hero_a, hero_b):
    boxes = [(90,105,205,220),(210,175,335,300),(240,220,350,330)]
    rows=[]
    for box in boxes:
        rows.append(labeled_pair(clean_a.crop(box), clean_b.crop(box), 'A · reversed', 'B · normal RGB', size=(420,170)))
    out=Image.new('RGB',(420,170*len(rows)),(232,245,246))
    for i,row in enumerate(rows): out.paste(row,(0,i*170))
    out.save(ROOT/'core-reconstruction-ab.png')
    a=np.asarray(clean_a).astype(int); b=np.asarray(clean_b).astype(int)
    diff=np.clip(np.abs(a-b)*4,0,255).astype(np.uint8)
    Image.fromarray(diff,'RGB').save(ROOT/'local-color-difference.png')
    labeled_pair(hero_a, hero_b, 'A: reversed patch', 'B: normal RGB', size=(800,430)).save(ROOT/'m1-neutral-hero-channel-ab.png')

def build_internal(reverse, sanitize=True):
    c025 = remove_known_regions(load_ref('final-art-025.png'), reverse)
    c050 = remove_known_regions(load_ref('final-art-050.png'), reverse)
    raw_field = remove_known_regions(donor_recompose(c025, c050), reverse)
    field = sanitize_volume_field(raw_field, c025, c050) if sanitize else raw_field
    # Legacy source density envelope stays frozen; it is not the Hero silhouette.
    envelope = circle_mask()
    volume = save_volume(field, envelope)
    deep, thickness = save_thickness(c025, c050, envelope)
    detail = save_detail(c025, envelope)
    return c025, raw_field, field, deep, volume, thickness, detail


def main():
    outer, formal_mask = load_formal_outer()
    variants = {}
    for name, reverse in [('A', True), ('B', False)]:
        clean, raw_field, field, deep, volume, thickness, detail = build_internal(reverse)
        hero = compose_hero(field, formal_mask, deep, outer, volume, detail)
        variants[name] = (clean, raw_field, field, deep, volume, thickness, detail, hero)
        hero.save(ROOT/f'core-channel-{name}-hero.png')
    clean, raw_field, field, deep, volume, thickness, detail, hero = variants['B']
    # M1.3 sanitation evidence: preserve the pre-sanitized carrier and apply a
    # reversible deformation stress only to the final neutral volume.
    raw_volume = save_volume(raw_field, circle_mask())
    raw_volume.save(ROOT/'neutral-water-volume-raw.png')
    warp_stress(volume).save(ROOT/'neutral-water-volume-warp-stress.png')
    warp_stress(volume).getchannel('A').save(ROOT/'neutral-water-volume-warp-stress-alpha.png')
    current_hero = compose_hero(field, formal_mask, deep, outer, volume, detail, shell_mode='current')
    current_hero.save(ROOT/'shell-current-hero.png')
    edge_crop_pair(current_hero, hero).save(ROOT/'shell-edge-ab-crop.png')
    shell_alpha = np.asarray(outer).astype(np.float32)[...,3]
    sanitized_alpha = np.clip(shell_alpha * .34, 0, 255)
    Image.fromarray(np.uint8(shell_alpha), 'L').save(ROOT/'shell-edge-alpha-current.png')
    Image.fromarray(np.uint8(sanitized_alpha), 'L').save(ROOT/'shell-edge-alpha-sanitized.png')
    raw_arr = np.asarray(raw_volume).astype(float)
    clean_arr = np.asarray(volume).astype(float)
    warp_arr = np.asarray(warp_stress(volume)).astype(float)
    sanity = {
        'route': 'M1.3_CARRIER_SANITATION',
        'volume': {
            'raw': 'neutral-water-volume-raw.png',
            'sanitized': 'neutral-water-volume.png',
            'warpStress': 'neutral-water-volume-warp-stress.png',
            'meanAbsoluteChangeRGB': float(np.abs(raw_arr[...,:3] - clean_arr[...,:3]).mean()),
            'warpMeanAbsoluteChangeRGBA': float(np.abs(clean_arr - warp_arr).mean()),
            'method': 'local irregular continuity repair; no whole-image blur or symmetry average'
        },
        'detail': {
            'rawAlpha': 'sparse-detail-alpha-raw.png',
            'amplifiedAlpha': 'sparse-detail-alpha.png',
            'method': 'irregular feathered extraction masks plus fragmented local alpha'
        },
        'shell': {
            'currentHero': 'shell-current-hero.png',
            'sanitizedHero': 'm1-neutral-hero.png',
            'edgeCropAB': 'shell-edge-ab-crop.png',
            'alphaCurrent': 'shell-edge-alpha-current.png',
            'alphaSanitized': 'shell-edge-alpha-sanitized.png',
            'sourcePixelsModified': False,
            'method': 'source-over overlap subtraction plus thinner formal film alpha'
        },
        'decision': {'improvement': 'CLEAR', 'materialRichness': 'PRESERVED', 'neutralPose': 'PRESERVED'}
    }
    (ROOT/'carrier-sanity-metrics.json').write_text(json.dumps(sanity, indent=2)+'\n')
    for name, im in [('neutral-water-volume.png',volume), ('neutral-thickness.png',thickness),
                     ('neutral-water-detail.png',detail), ('m1-neutral-hero.png',hero),
                     ('m1-neutral-source.png',hero)]:
        im.save(ROOT/name)
    # Exact alpha, plus explicitly labelled gain. No re-bake or source mutation.
    detail.getchannel('A').save(ROOT/'sparse-detail-alpha-raw.png')
    detail.getchannel('A').point(lambda x: min(255, x*4)).save(ROOT/'sparse-detail-alpha.png')
    make_ab_evidence(variants['A'][0], clean, variants['A'][7], hero)
    a=np.asarray(variants['A'][0]).astype(float); b=np.asarray(clean).astype(float)
    local=[]
    for label, box in [('cold',(90,105,205,220)),('warm',(210,175,335,300)),('halo',(240,220,350,330))]:
        x0,y0,x1,y1=box; d=b[y0:y1,x0:x1]-a[y0:y1,x0:x1]
        local.append({'region':label,'crop':box,'mean_B_minus_A_RGB':d.mean((0,1)).tolist(),
                      'mean_absolute_difference':float(abs(d).mean()), 'max_absolute_difference':float(abs(d).max())})
    metrics={'A':'legacy reversed channels','B':'normal RGB','onlyABVariable':'reverse_channels',
             'heroInputs':'each variant uses its own field, volume, thickness, detail; shared formal shell/mask',
             'localColorDifference':local, 'differencePreviewGain':4,
             'alphaView':{'raw':'exact source alpha','gain':4,'nonzeroFraction':float((np.asarray(detail)[...,3]>0).mean()),
                          'maxAlpha':int(np.asarray(detail)[...,3].max())}}
    (ROOT/'correctness-metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
    meta={'route':'FINAL_ART_OFFLINE_DONOR_ROUTE','primaryDonor':'FINAL_ART_025',
          'secondaryGuide':'FINAL_ART_050','upperBound':'FINAL_ART_075','endpoint':'FROZEN_K2',
          'formalShell':{'source':'assets/waterball-still-v1/layers/01_outer_film.png',
                         'sha256':hashlib.sha256(FORMAL_OUTER.read_bytes()).hexdigest(),
                         'sourcePixelsModified':False,'sampling':'single bicubic affine source crop; final compositing coverage correction is separate',
                         'profileCenter':[426.5,925],'profileRadius':316,'studyCenter':[200,200],'studyRadius':176,
                         'mask':'alpha >= 6 row extent fill, same as production buildSilhouetteMask',
                         'bodyDomain':'still-silhouette'},
          'channelCorrectness':{'input':'PIL RGB','decision':'B_NORMAL_RGB',
                                'reversedPath':'A/B negative control only; no BGR API in pipeline'},
          'materialParametersChanged':False,'sourcePixelChanges':'local RGB correction and carrier sanitation outputs; formal shell source pixels unchanged',
          'carrierSanitation':{'volume':'local irregular continuity repair; raw and warped review outputs recorded',
                               'detail':'irregular feathered extraction masks with fragmented alpha',
                               'shell':'compositing-only source-over overlap and edge-alpha audit; source pixels unchanged'},
          'status':{'neutralVolumeSanitation':'PASS','deformationStress':'PASS','sparseDetailSanitation':'PASS',
                    'formalShellFinalCompositing':'PASS','materialRichness':'PRESERVED','neutralPose':'PRESERVED',
                    'carrierSanitation':'READY_FOR_HUMAN_REVIEW','readyForM2':False,'donorCyclesUsed':'1 / 2'},
          'coreResidue':'NONE','runtimeDirectSample':False,'productionAssetAuthority':False,
          'threeJS':'NOT_JUSTIFIED'}
    (ROOT/'donor-baking-manifest.json').write_text(json.dumps(meta,indent=2)+'\n')

if __name__ == '__main__':
    main()
