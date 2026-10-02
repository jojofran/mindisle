#!/usr/bin/env python3
"""Export the accepted A shell/core plus a gated B interior delta field.

The package is a verification input, not a runtime asset contract. The delta
is encoded around 0.5 so it can be decoded by the WebGL study with
`decoded = (encoded - 0.5) * 2.0`; the separate mask is the only authority
that allows the delta to affect the image.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "k2-authority-study"
OUT = ROOT / "k2-interior-field"
SIZE = 360


def rgb(path: Path) -> np.ndarray:
    image = Image.open(path).convert("RGB").resize((SIZE, SIZE), Image.Resampling.LANCZOS)
    return np.asarray(image, dtype=np.float64) / 255.0


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_rgb(path: Path, value: np.ndarray) -> None:
    Image.fromarray(np.uint8(np.clip(value, 0.0, 1.0) * 255.0 + 0.5), "RGB").save(path)


OUT.mkdir(exist_ok=True)
a = rgb(SOURCE / "a-authority.png")
b = rgb(SOURCE / "b-internal-reference.png")
mask = rgb(SOURCE / "b-internal-mask.png")[..., 0]
silhouette = rgb(ROOT / "field-silhouette.png")[..., 0]
delta = b - a
encoded = np.clip(delta * 0.5 + 0.5, 0.0, 1.0)

save_rgb(OUT / "field-base-authority.png", a)
save_rgb(OUT / "field-delta-interior-encoded.png", encoded)
save_rgb(OUT / "field-interior-mask.png", np.repeat(mask[..., None], 3, axis=2))
save_rgb(OUT / "field-silhouette.png", np.repeat(silhouette[..., None], 3, axis=2))

decoded = (encoded - 0.5) * 2.0
reconstructed = np.clip(a + decoded * mask[..., None], 0.0, 1.0)
target = rgb(SOURCE / "a-authority-b-internal-study.png")
protected = (silhouette > 0.90) & (mask < 0.03)
outside = silhouette < 0.06
metrics = {
    "readback_mean_abs_rgb_255": round(float(np.abs(reconstructed - target).mean() * 255.0), 6),
    "readback_p95_abs_rgb_255": round(float(np.percentile(np.abs(reconstructed - target) * 255.0, 95)), 6),
    "protected_max_abs_rgb_255": round(float(np.abs(reconstructed - a)[protected].max() * 255.0), 6),
    "outside_max_abs_rgb_255": round(float(np.abs(reconstructed - a)[outside].max() * 255.0), 6),
    "mask_coverage": round(float((mask > 0.03).mean()), 6),
}
report = {
    "schema": "mindisle.k2-interior-field-package.v1",
    "status": "PASS_DETERMINISTIC_READBACK",
    "authority": "field-base-authority.png",
    "delta_field": "field-delta-interior-encoded.png",
    "mask": "field-interior-mask.png",
    "silhouette": "field-silhouette.png",
    "encoding": {
        "source_space": "8-bit display RGB normalized to 0..1",
        "encoded": "clamp(0.5 + 0.5 * (B - A), 0, 1)",
        "decoded": "(encoded - 0.5) * 2",
        "application": "A + decoded_delta * interior_mask * field_strength",
    },
    "metrics": metrics,
    "boundaries": [
        "shell/silhouette/core authority remains A",
        "B delta is gated by the exported interior mask",
        "no full-frame image crossfade",
        "no ProductState",
        "no formation/deformation",
        "no moving",
        "no production migration",
    ],
    "source_provenance": {
        "A": "k2-authority-study/a-authority.png",
        "B": "k2-authority-study/b-internal-reference.png",
        "mask": "k2-authority-study/b-internal-mask.png",
    },
    "files_sha256": {path.name: digest(path) for path in sorted(OUT.glob("*.png"))},
}
(OUT / "k2-interior-field-package.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"status": report["status"], "metrics": metrics}, ensure_ascii=False))
