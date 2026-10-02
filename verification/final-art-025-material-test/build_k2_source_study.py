#!/usr/bin/env python3
"""Build a verification-only K2 endpoint source feasibility study.

This script derives candidate fields from the frozen still layer package. The
outputs are diagnostic candidates, not production assets and not K2 authority.
It intentionally keeps the alpha-over source layers separate from the field
reconstruction so the evidence can show where the representation stops being
independent.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "test/water-orb-still/2p5d-composite-v1"
OUT = Path(__file__).resolve().parent / "k2-source-study"
SIZE = 360
SPHERE_BBOX = (88, 586, 766, 1265)
NEUTRAL = np.array([154, 166, 170], dtype=np.float64) / 255.0

LAYER_NAMES = {
    "outer": "layers/01_outer_film.png",
    "volume": "layers/02_internal_cyan_volume.png",
    "boundary": "layers/03_boundary_mask.png",
    "flow_a": "layers/04_flow_layer.png",
    "flow_b": "layers/05_flow_layer.png",
    "ink": "layers/06_fine_ink_wash.png",
    "cool_core": "layers/07_cool_point_core.png",
    "cool_glow": "layers/08_cool_point_glow.png",
    "warm_core": "layers/09_warm_point_core.png",
    "warm_glow": "layers/10_warm_point_glow.png",
    "curvature": "layers/11_curvature_highlights.png",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def crop_rgba(path: Path) -> np.ndarray:
    image = Image.open(path).convert("RGBA").crop(SPHERE_BBOX).resize((SIZE, SIZE), Image.Resampling.LANCZOS)
    return np.asarray(image, dtype=np.float64) / 255.0


def save_rgba(name: str, rgb: np.ndarray, alpha: np.ndarray) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    data = np.dstack([np.clip(rgb, 0, 1), np.clip(alpha, 0, 1)])
    Image.fromarray(np.uint8(data * 255 + 0.5), "RGBA").save(OUT / name)


def save_rgb(name: str, rgb: np.ndarray) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.uint8(np.clip(rgb, 0, 1) * 255 + 0.5), "RGB").save(OUT / name)


def alpha_over(base: np.ndarray, layer: np.ndarray) -> np.ndarray:
    a = layer[..., 3:4]
    return layer[..., :3] * a + base * (1 - a)


def srgb_to_linear(value: np.ndarray) -> np.ndarray:
    return np.where(value <= 0.04045, value / 12.92, ((value + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(value: np.ndarray) -> np.ndarray:
    value = np.maximum(value, 0)
    return np.where(value <= 0.0031308, value * 12.92, 1.055 * value ** (1 / 2.4) - 0.055)


def main() -> None:
    layers = {key: crop_rgba(SOURCE / path) for key, path in LAYER_NAMES.items()}
    silhouette = layers["outer"][..., 3]
    volume_alpha = layers["volume"][..., 3]
    volume_luma = np.dot(layers["volume"][..., :3], np.array([0.2126, 0.7152, 0.0722]))
    optical = np.clip(volume_luma * volume_alpha, 0, 1)
    inside = silhouette > 0.05
    if inside.any():
        optical /= max(float(np.percentile(optical[inside], 95)), 1e-6)
    optical = np.clip(optical, 0, 1)

    flow = np.zeros((SIZE, SIZE, 3), dtype=np.float64)
    flow_rgba = np.dstack([flow, np.zeros((SIZE, SIZE))])
    for key in ("flow_a", "flow_b", "ink"):
        flow_rgba[..., :3] = alpha_over(flow_rgba[..., :3], layers[key])
    scatter = np.clip(flow_rgba[..., :3], 0, 1)
    scatter_alpha = np.maximum(flow_rgba[..., 3], silhouette * 0.18)

    reflection = layers["curvature"][..., :3]
    reflection_alpha = layers["curvature"][..., 3]
    core_alpha = np.maximum.reduce([layers["cool_core"][..., 3], layers["cool_glow"][..., 3], layers["warm_core"][..., 3], layers["warm_glow"][..., 3]])
    core_rgb = np.maximum.reduce([layers["cool_core"][..., :3], layers["cool_glow"][..., :3], layers["warm_core"][..., :3], layers["warm_glow"][..., :3]])

    # Derived local refraction candidate. This is explicitly a diagnostic
    # gradient field, not a physical recovery of the original K2 renderer.
    blurred = np.asarray(Image.fromarray(np.uint8(optical * 255)).filter(ImageFilter.GaussianBlur(3)), dtype=np.float64) / 255.0
    dy, dx = np.gradient(blurred)
    scale = max(float(np.percentile(np.abs(np.dstack([dx, dy])[inside]), 95)), 1e-6)
    refraction = np.dstack([np.clip(0.5 + dx / (2 * scale), 0, 1), np.clip(0.5 + dy / (2 * scale), 0, 1), np.full((SIZE, SIZE), 0.5)])

    save_rgba("field-silhouette.png", np.repeat(silhouette[..., None], 3, axis=2), silhouette)
    save_rgba("field-optical-depth-candidate.png", np.repeat(optical[..., None], 3, axis=2), silhouette)
    save_rgba("field-scatter-candidate.png", scatter, scatter_alpha)
    save_rgba("field-reflection-candidate.png", reflection, reflection_alpha)
    save_rgba("field-refraction-derived.png", refraction, silhouette)
    save_rgba("field-core-mask-candidate.png", core_rgb, core_alpha)

    # Reconstruct a neutral-background diagnostic from the candidate fields.
    yy, xx = np.mgrid[:SIZE, :SIZE]
    center = (SIZE - 1) / 2
    radius = np.sqrt((xx - center) ** 2 + (yy - center) ** 2) / (SIZE * 0.46)
    path = np.clip(np.sqrt(np.maximum(1 - radius * radius, 0)), 0, 1)
    background = np.broadcast_to(NEUTRAL, (SIZE, SIZE, 3)).copy()
    transmission = np.exp(-np.repeat(optical[..., None], 3, axis=2) * 1.8 * path[..., None])
    reconstructed_linear = srgb_to_linear(background) * transmission
    reconstructed_linear += srgb_to_linear(scatter) * (scatter_alpha[..., None] * 0.35)
    reconstructed_linear += srgb_to_linear(reflection) * (reflection_alpha[..., None] * 0.35)
    reconstructed = linear_to_srgb(reconstructed_linear)
    reconstructed = background * (1 - silhouette[..., None]) + np.clip(reconstructed, 0, 1) * silhouette[..., None]
    save_rgb("k2-candidate-reconstruction-neutral.png", reconstructed)

    # Reference crop is used only for a diagnostic error measure. The crop
    # still contains the frozen reference's baked appearance and is not a
    # claim that the candidate fields are physically correct.
    reference = np.asarray(Image.open(SOURCE / "static_composite.png").convert("RGB").crop(SPHERE_BBOX).resize((SIZE, SIZE), Image.Resampling.LANCZOS), dtype=np.float64) / 255.0
    error = np.abs(reconstructed - reference) * 255
    error_inside = error[inside]
    metrics = {
        "reconstruction_mean_abs_rgb_255": round(float(error_inside.mean()), 4),
        "reconstruction_p95_abs_rgb_255": round(float(np.percentile(error_inside, 95)), 4),
        "silhouette_coverage": round(float(inside.mean()), 6),
        "core_coverage": round(float((core_alpha > 0.05).mean()), 6),
        "source_layer_model": "alpha_over_static_layers",
        "independent_field_recovery": False,
    }
    files = {name: digest(OUT / name) for name in sorted(p.name for p in OUT.glob("*.png"))}
    report = {
        "schema": "mindisle.k2-source-feasibility.v1",
        "status": "READY_FOR_HUMAN_REVIEW__M4_BLOCKED",
        "scope": "verification-only candidate field derivation from frozen K2 still layers; no production or runtime interpolation",
        "source_manifest": "test/water-orb-still/2p5d-composite-v1/composite_manifest.json",
        "source_static_composite": "test/water-orb-still/2p5d-composite-v1/static_composite.png",
        "sphere_crop": {"bbox": list(SPHERE_BBOX), "size": [SIZE, SIZE]},
        "derived_fields": {
            "silhouette": "field-silhouette.png",
            "optical_depth_candidate": "field-optical-depth-candidate.png",
            "scatter_candidate": "field-scatter-candidate.png",
            "reflection_candidate": "field-reflection-candidate.png",
            "refraction_derived": "field-refraction-derived.png",
            "core_mask_candidate": "field-core-mask-candidate.png",
        },
        "metrics": metrics,
        "decision": {
            "static_layer_separation": "PASS_DIAGNOSTIC",
            "candidate_reconstruction": "REVIEW_REQUIRED",
            "independent_k2_field": "NOT_PROVEN",
            "m3": "REMAINS_HUMAN_PASS",
            "m4": "BLOCKED",
            "next_required": "Human review of the candidate reconstruction; if accepted, define a provenance and channel contract before any runtime study.",
        },
        "limitations": [
            "K2 source remains a reference-driven alpha-over layer stack, not a measured physical volume.",
            "Optical depth and refraction are derived candidates, not original K2 fields.",
            "The static composite includes a background/UI plate outside the cropped sphere; it is excluded from field extraction.",
            "No production asset, ProductState, formation, deformation, moving, or runtime interpolation was changed.",
        ],
        "files_sha256": files,
    }
    (OUT / "k2-source-feasibility.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    (OUT / "README.md").write_text(
        "# K2 source feasibility study\n\n"
        "这些 PNG 是从冻结 K2 静止图层派生的 verification-only 候选字段，不是新的 K2 authority，也没有接入 runtime。\n\n"
        "`k2-candidate-reconstruction-neutral.png` 用候选 optical depth、scatter、reflection 和 derived refraction 做一次固定视角重建。它只用于判断现有图层是否足以形成独立字段；如果视觉或误差不成立，需要新的 authored K2 field source。\n\n"
        "详细指标见 `k2-source-feasibility.json`。\n"
    )
    print(json.dumps({"status": report["status"], "metrics": metrics}, ensure_ascii=False))


if __name__ == "__main__":
    main()
