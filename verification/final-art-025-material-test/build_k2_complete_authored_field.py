#!/usr/bin/env python3
"""Build a complete fixed-view authored K2 field package.

The package separates the frozen A shell/core from the authored A+B interior
fit. It is a verification artifact, not a unique physical or free-view field.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "k2-authored-optical-field"
OUT = ROOT / "k2-complete-authored-field"
SIZE = 360
OUT.mkdir(exist_ok=True)


def read(path: Path, mode: str = "RGB") -> np.ndarray:
    return np.asarray(Image.open(path).convert(mode).resize((SIZE, SIZE), Image.Resampling.LANCZOS), dtype=np.float64) / 255.0


def save(path: Path, value: np.ndarray) -> None:
    Image.fromarray(np.uint8(np.clip(value, 0.0, 1.0) * 255.0 + 0.5), "RGB").save(path)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


authority = read(SOURCE / "field-base-a-authority.png")
target = read(SOURCE / "field-authority-rgb.png")
silhouette = read(SOURCE / "field-silhouette.png")[..., 0]
interior = read(SOURCE / "field-interior-mask.png")[..., 0] * silhouette
core = read(SOURCE / "field-core-mask.png")[..., 0] * silhouette
shell = np.clip(silhouette - interior - core, 0.0, 1.0)
depth = read(SOURCE / "field-optical-depth-authored.png")[..., 0] * interior
thickness = read(SOURCE / "field-thickness-authored.png")[..., 0] * interior
refraction = read(SOURCE / "field-refraction-authored.png")
residual = read(SOURCE / "field-residual-signed-encoded.png")
residual_signed = residual * 2.0 - 1.0
transmission = np.exp(-depth[..., None] * thickness[..., None] * 1.65)
density = np.clip(depth * (0.35 + 0.65 * thickness), 0.0, 1.0) * interior

save(OUT / "field-authority-a-rgb.png", authority)
save(OUT / "field-target-a-plus-b-rgb.png", target)
save(OUT / "field-shell-authority.png", authority * shell[..., None])
save(OUT / "field-core-authority.png", authority * core[..., None])
save(OUT / "field-interior-target.png", target * interior[..., None])
save(OUT / "field-silhouette.png", np.repeat(silhouette[..., None], 3, axis=2))
save(OUT / "field-shell-mask.png", np.repeat(shell[..., None], 3, axis=2))
save(OUT / "field-interior-mask.png", np.repeat(interior[..., None], 3, axis=2))
save(OUT / "field-core-mask.png", np.repeat(core[..., None], 3, axis=2))
save(OUT / "field-optical-depth.png", np.repeat(depth[..., None], 3, axis=2))
save(OUT / "field-density.png", np.repeat(density[..., None], 3, axis=2))
save(OUT / "field-thickness.png", np.repeat(thickness[..., None], 3, axis=2))
save(OUT / "field-transmission.png", np.repeat(transmission, 3, axis=2))
save(OUT / "field-refraction.png", refraction)
save(OUT / "field-residual-signed-encoded.png", residual)

# The authored fit is allowed to affect only the interior mask. Frozen A is
# copied back for shell/core/outside so the package has an explicit authority boundary.
BG = np.array([224.0, 235.0, 239.0]) / 255.0
fit = np.clip(BG * transmission + residual_signed, 0.0, 1.0)
reconstructed = authority * (1.0 - interior[..., None]) + fit * interior[..., None]
error = np.abs(reconstructed - target) * 255.0
shell_region = (silhouette > 0.90) & (interior < 0.03) & (core < 0.03)
core_region = (silhouette > 0.90) & (core > 0.03)
outside_region = silhouette < 0.06
interior_region = interior > 0.03
metrics = {
    "reconstructed_mean_abs_rgb_255_vs_target": round(float(error.mean()), 6),
    "reconstructed_p95_abs_rgb_255_vs_target": round(float(np.percentile(error, 95)), 6),
    "shell_max_abs_rgb_255_vs_a": round(float(np.abs(reconstructed - authority)[shell_region].max() * 255.0), 6),
    "core_max_abs_rgb_255_vs_a": round(float(np.abs(reconstructed - authority)[core_region].max() * 255.0), 6),
    "outside_max_abs_rgb_255_vs_a": round(float(np.abs(reconstructed - authority)[outside_region].max() * 255.0), 6),
    "interior_mean_abs_rgb_255_vs_target": round(float(np.abs(reconstructed - target)[interior_region].mean() * 255.0), 6),
    "shell_coverage": round(float(shell_region.mean()), 6),
    "interior_coverage": round(float(interior_region.mean()), 6),
    "core_coverage": round(float(core_region.mean()), 6),
}
report = {
    "schema": "mindisle.k2-complete-authored-field.v1",
    "status": "PASS_FIXED_VIEW_COMPLETE_AUTHORED_FIELD_PACKAGE",
    "scope": "complete authored field package at fixed front view; verification only",
    "authority": "field-authority-a-rgb.png; A shell/core/silhouette remain frozen",
    "target": "field-target-a-plus-b-rgb.png; B contributes only authored interior target",
    "field_roles": {
        "shell": "frozen A authority masked by shell mask",
        "core": "frozen A authority masked by core mask",
        "silhouette": "frozen body boundary",
        "optical_depth": "authored positive interior depth estimate",
        "density": "derived interior density contribution for future study",
        "thickness": "authored spherical thickness estimate",
        "transmission": "exp(-depth * thickness * 1.65)",
        "refraction": "depth-gradient authored refraction estimate",
        "residual": "signed unresolved reflection/scatter/film contribution; not separated physical reflection",
    },
    "metrics": metrics,
    "limitations": [
        "single-view authored factorization; not unique physical recovery",
        "no free-view validation or view-dependent response",
        "signed residual still mixes reflection/scatter/film",
        "no ProductState, formation/deformation, moving, runtime interpolation, or production migration",
    ],
    "human_gate": "current fixed-view visual review PASS_REVIEW; complete package still requires a later human endpoint review",
    "files_sha256": {p.name: digest(p) for p in sorted(OUT.glob("*.png"))},
}
(OUT / "k2-complete-authored-field.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"status": report["status"], "metrics": metrics}, ensure_ascii=False))
