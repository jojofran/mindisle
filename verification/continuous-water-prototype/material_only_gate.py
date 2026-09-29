from __future__ import annotations

from pathlib import Path
import json
from PIL import Image, ImageFilter, ImageDraw
import numpy as np

ROOT = Path(__file__).resolve().parent
REF = ROOT / 'references'
SIZE = 400
CROP = (20, 20, 340, 340)


def load_ref(name):
    return Image.open(REF / name).convert('RGB').crop(CROP).resize((SIZE, SIZE), Image.Resampling.LANCZOS)


def apply_review_mask(image, mask, background=(28, 61, 68)):
    rgba = image.convert('RGBA')
    rgba.putalpha(mask)
    bg = Image.new('RGBA', (SIZE, SIZE), (*background, 255))
    return Image.alpha_composite(bg, rgba)


def combined_internal(volume, detail, mask):
    base = volume.convert('RGBA')
    base.putalpha(mask)
    det = detail.convert('RGBA')
    d = np.asarray(det).copy()
    d[..., 3] = np.uint8(d[..., 3] * .62)
    return Image.alpha_composite(base, Image.fromarray(d, 'RGBA'))


def labeled_row(images, labels, size=(1200, 330)):
    out = Image.new('RGB', size, (237, 247, 248))
    draw = ImageDraw.Draw(out)
    w = size[0] // len(images)
    for i, (im, label) in enumerate(zip(images, labels)):
        if im.mode == 'RGBA':
            panel_bg = Image.new('RGBA', im.size, (237, 247, 248, 255))
            im = Image.alpha_composite(panel_bg, im).convert('RGB')
        else:
            im = im.convert('RGB')
        im.thumbnail((w - 20, size[1] - 42), Image.Resampling.LANCZOS)
        out.paste(im, (i*w + (w-im.width)//2, 8))
        draw.text((i*w + 10, size[1]-27), label, fill=(43, 91, 99))
    return out


def build_shell_tests(outer, body):
    # A is the M1.4 top-overlay preview already used as the blocker evidence.
    a = Image.open(ROOT / 'shell-m1.4-composite.png').convert('RGBA')
    # B restores the formal manifest's alpha-over order: outer film first,
    # internal body second. No source alpha is changed.
    b = Image.alpha_composite(outer, body)
    # C keeps the same original order and applies one alpha-aware body response
    # in the shell optical zone. The formal outer source remains untouched.
    oa = np.asarray(outer).astype(np.float32)[..., 3]
    body_arr = np.asarray(body).astype(np.float32)
    body_arr[..., 3] *= (1 - .35 * oa / 255)
    c = Image.alpha_composite(outer, Image.fromarray(np.uint8(np.clip(body_arr, 0, 255)), 'RGBA'))
    a.save(ROOT / 'm2-shell-test-a-top-overlay.png')
    b.save(ROOT / 'm2-shell-test-b-original-order.png')
    c.save(ROOT / 'm2-shell-test-c-alpha-aware-original-order.png')
    box = (24, 24, 376, 376)
    labeled_row([a.crop(box), b.crop(box), c.crop(box)], ['A · top overlay', 'B · original order', 'C · alpha-aware'], size=(900, 300)).save(ROOT / 'm2-shell-route-edge-crop.png')
    return a, b, c


def main():
    # Freeze the existing M1.4 material files: this script only reads them and
    # writes review evidence beside them.
    safe = Image.open(ROOT / 'safe-interior-mask.png').convert('L')
    comparison = safe.filter(ImageFilter.MinFilter(21)).filter(ImageFilter.GaussianBlur(3))
    comparison.save(ROOT / 'material-only-comparison-mask.png')
    ref025 = load_ref('final-art-025.png')
    ref050 = load_ref('final-art-050.png')
    volume = Image.open(ROOT / 'neutral-water-volume-unclipped-rgb.png').convert('RGB')
    thickness = Image.open(ROOT / 'neutral-thickness.png').convert('RGBA')
    detail = Image.open(ROOT / 'neutral-water-detail.png').convert('RGBA')
    apply_review_mask(ref025, comparison).save(ROOT / 'material-only-final-art-025-interior.png')
    apply_review_mask(ref050, comparison).save(ROOT / 'material-only-final-art-050-interior.png')
    apply_review_mask(volume, comparison).save(ROOT / 'material-only-neutral-volume.png')
    apply_review_mask(thickness.convert('RGB'), comparison).save(ROOT / 'material-only-neutral-thickness.png')
    apply_review_mask(detail.convert('RGB'), comparison).save(ROOT / 'material-only-neutral-detail.png')
    combined = combined_internal(Image.open(ROOT / 'neutral-water-volume.png'), detail, comparison)
    combined.save(ROOT / 'material-only-combined-neutral-interior.png')
    labeled_row([apply_review_mask(ref025, comparison), apply_review_mask(ref050, comparison), combined],
                ['FINAL_ART_025 interior', 'FINAL_ART_050 interior', 'CURRENT combined neutral interior'], size=(1200, 360)).save(ROOT / 'material-only-family-triad.png')
    outer = Image.open(ROOT / 'formal-outer-film-crop.png').convert('RGBA')
    body = combined_internal(Image.open(ROOT / 'neutral-water-volume.png'), detail, Image.open(ROOT / 'interior-body-mask.png').convert('L'))
    a, b, c = build_shell_tests(outer, body)
    labeled_row([ref025, a, b, c], ['FINAL_ART_025 edge', 'A · top overlay', 'B · original order', 'C · alpha-aware original order'], size=(1200, 350)).save(ROOT / 'm2-shell-route-triad.png')
    metrics = {
        'route': 'M1.5_MATERIAL_ONLY_GATE',
        'materialSourcesFrozen': True,
        'comparisonDomain': 'material-only-comparison-mask.png; same mask for FINAL_ART_025, FINAL_ART_050, and current carriers',
        'materialOnlyCritic': {
            'sameWaterFamily': 'NOT_EVALUATED_AT_RAW_SOURCE_LEVEL',
            'notFogFlatCyanGenericCloud': 'NOT_EVALUATED_AT_RAW_SOURCE_LEVEL',
            'cloudyMass': 'authored nonuniform mass retained',
            'depthThicknessInput': 'present as frozen neutral-thickness source',
            'sparseDetail': 'natural sparse connected features; no box authority',
            'materialRepresentationDefect': 'NOT_EVALUATED_AT_RAW_SOURCE_LEVEL',
            'decision': 'DEFERRED_TO_M2_HUMAN_REVIEW'
        },
        'neutralPose': 'PRESERVED',
        'shellRoute': {
            'A': 'M1.4 current top-overlay',
            'B': 'formal manifest original order: outer film then internal body',
            'C': 'original order with alpha-aware body coverage response',
            'sourceAlphaModified': False,
            'recommendedM2StartingPoint': 'UNRESOLVED',
            'm2PreviewAuthoritative': False,
            'm1ShellClassification': 'M2_STATIC_MATERIAL_INTEGRATION_CONCERN'
        },
        'sourceNormalization': 'M1.4_DE_SHELLED_SOURCE_FROZEN',
        'readyForM2': True
    }
    (ROOT / 'material-only-gate.json').write_text(json.dumps(metrics, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
