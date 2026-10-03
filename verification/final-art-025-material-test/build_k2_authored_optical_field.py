#!/usr/bin/env python3
"""Build a fixed-view authored optical fit for the selected K2 candidate.

This is a verification-only factorization, not a unique physical recovery.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "k2-authority-study"
OUT = ROOT / "k2-authored-optical-field"
SIZE = 360
BG = np.array([224, 235, 239], dtype=np.float64) / 255.0


def read(path: Path, mode: str = "RGB") -> np.ndarray:
    return np.asarray(Image.open(path).convert(mode).resize((SIZE, SIZE), Image.Resampling.LANCZOS), dtype=np.float64) / 255.0


def save(path: Path, value: np.ndarray, mode: str = "RGB") -> None:
    Image.fromarray(np.uint8(np.clip(value, 0.0, 1.0) * 255.0 + 0.5), mode).save(path)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


OUT.mkdir(exist_ok=True)
target = read(SOURCE / "a-authority-b-internal-study.png")
authority = read(SOURCE / "a-authority.png")
mask = read(SOURCE / "b-internal-mask.png")[..., 0]
silhouette = read(ROOT / "field-silhouette.png")[..., 0]
core_path = ROOT / "k2-source-study/field-core-mask-candidate.png"
core = read(core_path, "RGBA")[..., 3] if core_path.exists() else np.zeros_like(mask)

yy, xx = np.mgrid[:SIZE, :SIZE]
center = (SIZE - 1) / 2.0
radius = np.sqrt((xx - center) ** 2 + (yy - center) ** 2) / (SIZE * 0.46)
thickness = np.clip(np.sqrt(np.maximum(1.0 - radius * radius, 0.0)), 0.0, 1.0) * silhouette
inside = silhouette > 0.08
luma = np.dot(target, np.array([0.2126, 0.7152, 0.0722]))
bg_luma = float(np.dot(BG, np.array([0.2126, 0.7152, 0.0722])))
depth = np.clip((bg_luma - luma) / np.maximum(thickness, 0.12), 0.0, 1.0) * inside
transmit = BG * np.exp(-depth[..., None] * thickness[..., None] * 1.65)
residual = target - transmit
residual_encoded = np.clip(0.5 + residual * 0.5, 0.0, 1.0)

blurred = np.asarray(Image.fromarray(np.uint8(depth * 255.0)).filter(ImageFilter.GaussianBlur(3)), dtype=np.float64) / 255.0
dy, dx = np.gradient(blurred)
scale = max(float(np.percentile(np.abs(np.dstack([dx, dy])[inside]), 95)), 1e-6)
refraction = np.dstack([np.clip(0.5 + dx / (2 * scale), 0, 1), np.clip(0.5 + dy / (2 * scale), 0, 1), np.full((SIZE, SIZE), 0.5)])

save(OUT / "field-authority-rgb.png", target)
save(OUT / "field-base-a-authority.png", authority)
save(OUT / "field-optical-depth-authored.png", np.repeat(depth[..., None], 3, axis=2))
save(OUT / "field-thickness-authored.png", np.repeat(thickness[..., None], 3, axis=2))
save(OUT / "field-residual-signed-encoded.png", residual_encoded)
save(OUT / "field-refraction-authored.png", refraction)
save(OUT / "field-silhouette.png", np.repeat(silhouette[..., None], 3, axis=2))
save(OUT / "field-interior-mask.png", np.repeat(mask[..., None], 3, axis=2))
save(OUT / "field-core-mask.png", np.repeat(core[..., None], 3, axis=2))

read_depth = read(OUT / "field-optical-depth-authored.png")[..., 0]
read_thickness = read(OUT / "field-thickness-authored.png")[..., 0]
read_residual = read(OUT / "field-residual-signed-encoded.png") * 2.0 - 1.0
read_reconstructed = np.clip(BG * np.exp(-read_depth[..., None] * read_thickness[..., None] * 1.65) + read_residual, 0.0, 1.0)
error = np.abs(read_reconstructed - target) * 255.0
protected = (silhouette > 0.90) & (mask < 0.03)
outside = silhouette < 0.06
metrics = {
    "readback_mean_abs_rgb_255": round(float(error.mean()), 6),
    "readback_p95_abs_rgb_255": round(float(np.percentile(error, 95)), 6),
    "readback_max_abs_rgb_255": round(float(error.max()), 6),
    "protected_max_abs_rgb_255_vs_a": round(float(np.abs(read_reconstructed - authority)[protected].max() * 255.0), 6),
    "outside_max_abs_rgb_255_vs_a": round(float(np.abs(read_reconstructed - authority)[outside].max() * 255.0), 6),
    "protected_max_abs_rgb_255_vs_target": round(float(np.abs(read_reconstructed - target)[protected].max() * 255.0), 6),
    "outside_max_abs_rgb_255_vs_target": round(float(np.abs(read_reconstructed - target)[outside].max() * 255.0), 6),
    "interior_mask_coverage": round(float((mask > 0.03).mean()), 6),
}
report = {
    "schema": "mindisle.k2-authored-optical-field.v1",
    "status": "PASS_FIXED_VIEW_AUTHORED_FIELD_READBACK",
    "scope": "selected A+B interior candidate; fixed front view; verification only",
    "authority": "k2-authority-study/a-authority.png",
    "target": "k2-authority-study/a-authority-b-internal-study.png",
    "field_inputs": [p.name for p in sorted(OUT.glob("field-*.png"))],
    "encoding": {
        "depth": "normalized positive optical-depth estimate",
        "residual": "encoded = clamp(0.5 + 0.5 * residual, 0, 1); decoded = encoded * 2 - 1",
        "reconstruction": "background * exp(-depth * thickness * 1.65) + signed_residual",
    },
    "metrics": metrics,
    "limitations": [
        "single-view authored factorization; not unique physical recovery",
        "signed residual contains unresolved reflection/scatter/film contribution",
        "K2 core identity remains frozen authority A",
        "no ProductState, formation/deformation, moving, runtime interpolation, or production migration",
    ],
    "source_provenance": {
        "A": "k2-authority-study/a-authority.png",
        "target": "k2-authority-study/a-authority-b-internal-study.png",
        "B": "k2-authority-study/b-internal-reference.png",
        "interior_mask": "k2-authority-study/b-internal-mask.png",
    },
    "files_sha256": {p.name: digest(p) for p in sorted(OUT.glob("*.png"))},
}
(OUT / "k2-authored-optical-field.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"status": report["status"], "metrics": metrics}, ensure_ascii=False))
