#!/usr/bin/env python3
"""Build a traceable, static Final Art 025 material test.

Verification artifact only: fixed-front-view authored layer composition.
No motion, procedural geometry, or runtime migration is introduced.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
FORMAL = ROOT / "test/water-orb-still/2p5d-composite-v1"
LAYERS = FORMAL / "layers"
REFS = ROOT / "verification/continuous-water-prototype/references"
SIZE = (360, 360)
# Formal sphere crop recorded in visual_parameters/asset_validation.
CROP = (88, 587, 766, 1265)

LAYER_NAMES = [
    "00_background_plate.png",
    "01_outer_film.png",
    "02_internal_cyan_volume.png",
    "03_boundary_mask.png",
    "04_flow_layer.png",
    "05_flow_layer.png",
    "06_fine_ink_wash.png",
    "11_curvature_highlights.png",
]
OPTIONAL_POINT_NAMES = [
    "07_cool_point_core.png",
    "08_cool_point_glow.png",
    "09_warm_point_core.png",
    "10_warm_point_glow.png",
]


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def crop_resize(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA").crop(CROP).resize(SIZE, Image.Resampling.LANCZOS)


def alpha_over(images: Iterable[Image.Image]) -> Image.Image:
    out = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    for image in images:
        out = Image.alpha_composite(out, image)
    return out


def write_layer_assets() -> dict[str, str]:
    assets: dict[str, str] = {}
    for name in LAYER_NAMES + OPTIONAL_POINT_NAMES:
        out_name = name.removesuffix(".png").replace("_", "-")
        out_path = OUT / f"layer-{out_name}.png"
        crop_resize(LAYERS / name).save(out_path)
        assets[name] = out_path.name
    return assets


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    assets = write_layer_assets()

    target_025 = REFS / "final-art-025.png"
    static_composite = FORMAL / "static_composite.png"
    target_050 = REFS / "final-art-050.png"
    frozen_k2 = REFS / "frozen-k2-final-art.png"
    m1_neutral = ROOT / "verification/continuous-water-prototype/neutral-water-volume.png"
    for source, name in [
        (target_025, "target-final-art-025.png"),
        (target_050, "target-final-art-050.png"),
        (frozen_k2, "target-frozen-k2.png"),
        (m1_neutral, "m1-neutral-water-volume.png"),
    ]:
        Image.open(source).convert("RGBA").save(OUT / name)
    crop_resize(static_composite).save(OUT / "candidate-formal-static-baseline.png")

    authored_layers = [crop_resize(LAYERS / name) for name in LAYER_NAMES]
    primary = alpha_over(authored_layers)
    primary.save(OUT / "candidate-final-art-025-no-points.png")

    with_points = alpha_over(authored_layers + [crop_resize(LAYERS / name) for name in OPTIONAL_POINT_NAMES])
    with_points.save(OUT / "candidate-final-art-025-with-points.png")

    body_only = alpha_over([crop_resize(LAYERS / name) for name in [
        "00_background_plate.png", "01_outer_film.png", "02_internal_cyan_volume.png",
    ]])
    body_only.save(OUT / "candidate-body-film-only.png")

    structure_only = alpha_over([crop_resize(LAYERS / name) for name in [
        "00_background_plate.png", "01_outer_film.png", "03_boundary_mask.png",
        "04_flow_layer.png", "05_flow_layer.png", "06_fine_ink_wash.png",
        "11_curvature_highlights.png",
    ]])
    structure_only.save(OUT / "candidate-structure-film-without-volume.png")

    manifest = {
        "test_id": "final-art-025-material-test-v1",
        "status": "AWAITING_HUMAN_REVIEW",
        "scope": "static material verification only",
        "production_dependency": False,
        "target": "FINAL_ART_025",
        "secondary_reference": "FINAL_ART_050_DEPTH_ONLY",
        "frozen_endpoint_reference": "FROZEN_K2_ENDPOINT_ONLY",
        "representation": "formal-static-baseline-plus-layer-diagnostics",
        "crop": {"source_size": [853, 1844], "box_xyxy": list(CROP), "output_size": list(SIZE)},
        "primary_candidate": {
            "file": "candidate-formal-static-baseline.png",
            "source": "test/water-orb-still/2p5d-composite-v1/static_composite.png",
            "reason": "形式层包当前已提供烘焙完成的静态材质；先以它作为 Final Art 025 材质基线，不重复叠加已烘焙层。",
            "core_simulation": "not added by this test",
        },
        "raw_layer_diagnostic": {
            "file": "candidate-final-art-025-no-points.png",
            "included_layers": LAYER_NAMES,
            "excluded_layers": OPTIONAL_POINT_NAMES,
            "result": "INVALID_AS_PRIMARY_DUE_TO_DOUBLE_COMPOSITING",
            "reason": "背景板已含完成材质，直接 alpha-over 会重复叠加并制造非目标亮纹/黑带。",
        },
        "comparisons": [
            "candidate-body-film-only.png",
            "candidate-structure-film-without-volume.png",
            "candidate-final-art-025-with-points.png",
            "candidate-final-art-025-no-points.png",
        ],
        "sources": {
            "final-art-025": {"file": str(target_025.relative_to(ROOT)), "sha256": sha(target_025)},
            "final-art-050": {"file": str(target_050.relative_to(ROOT)), "sha256": sha(target_050)},
            "frozen-k2": {"file": str(frozen_k2.relative_to(ROOT)), "sha256": sha(frozen_k2)},
            "m1-neutral-water-volume": {"file": str(m1_neutral.relative_to(ROOT)), "sha256": sha(m1_neutral)},
            "formal-layer-package": {"file": str(FORMAL.relative_to(ROOT)), "layer_order": LAYER_NAMES + OPTIONAL_POINT_NAMES},
            "static-composite": {"file": str(static_composite.relative_to(ROOT)), "sha256": sha(static_composite)},
        },
        "acceptance": {
            "must_show": [
                "透明外膜、内部青绿色体积、连续内部层次和边缘厚度能被分辨",
                "主材质不依赖双核或外部固定弧线",
                "候选图与 Final Art 025 能在同一页面直接对比",
                "没有运动、实时物理或生产资源改动",
            ],
            "human_decision": "人工判断是否接近 Final Art 025 的材质身份；本测试不自动宣告通过。",
        },
    }
    (OUT / "evidence.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
