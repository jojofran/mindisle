#!/usr/bin/env python3
"""Audit the selected K2 static authority and the legacy layer source package.

This is a verification-only provenance check. It does not derive runtime fields
or change any production asset.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
TEST = ROOT / "test/water-orb-still/2p5d-composite-v1"
HERE = Path(__file__).resolve().parent
OUT = HERE / "k2-source-study/k2-endpoint-source-audit.json"
BBOX = (88, 586, 766, 1265)
SIZE = (360, 360)


def rgb(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGB"), dtype=np.float64)


def crop(path: Path) -> np.ndarray:
    image = Image.open(path).convert("RGB").crop(BBOX).resize(SIZE, Image.Resampling.LANCZOS)
    return np.asarray(image, dtype=np.float64)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def metrics(left: np.ndarray, right: np.ndarray) -> dict[str, float]:
    error = np.abs(left - right)
    return {
        "mean_abs_rgb_255": round(float(error.mean()), 6),
        "p95_abs_rgb_255": round(float(np.percentile(error, 95)), 6),
        "max_abs_rgb_255": round(float(error.max()), 6),
    }


def main() -> None:
    static = TEST / "static_composite.png"
    foundation = TEST / "reference_foundation.png"
    authority = HERE / "k2-authority-study/a-authority.png"
    candidate = HERE / "k2-authority-study/a-authority-b-internal-study.png"
    feasibility = json.loads((HERE / "k2-source-study/k2-source-feasibility.json").read_text())
    authority_manifest = json.loads((HERE / "k2-authority-study/k2-authority-study.json").read_text())

    static_crop = crop(static)
    authority_rgb = rgb(authority)
    foundation_crop = crop(foundation)
    candidate_rgb = rgb(candidate)
    authority_error = metrics(authority_rgb, static_crop)
    foundation_error = metrics(authority_rgb, foundation_crop)
    interior_delta = metrics(candidate_rgb, authority_rgb)

    report = {
        "schema": "mindisle.k2-endpoint-source-audit.v1",
        "status": "A_STATIC_AUTHORITY_LOCKED__LEGACY_MANIFEST_DIAGNOSTIC_ONLY",
        "scope": "verification-only provenance audit; no runtime interpolation or production migration",
        "crop": {"bbox": list(BBOX), "size": list(SIZE)},
        "selected_authority": {
            "id": "A",
            "file": "k2-authority-study/a-authority.png",
            "source": "test/water-orb-still/2p5d-composite-v1/static_composite.png",
            "authority_status": "FROZEN_STATIC_K2_AUTHORITY",
            "authority_vs_static_crop": authority_error,
            "exact_match": authority_error["max_abs_rgb_255"] == 0.0,
        },
        "secondary_reference": {
            "id": "B",
            "file": "test/water-orb-still/2p5d-composite-v1/reference_foundation.png",
            "role": "INTERIOR_TEXTURE_AND_FLOW_REFERENCE_ONLY",
            "vs_selected_authority": foundation_error,
        },
        "locked_candidate": {
            "file": "k2-authority-study/a-authority-b-internal-study.png",
            "role": "A_SHELL_CORE_PLUS_B_INTERIOR",
            "interior_delta_vs_authority": interior_delta,
            "shell_core_preservation": authority_manifest["metrics"],
        },
        "legacy_manifest": {
            "manifest": "test/water-orb-still/2p5d-composite-v1/composite_manifest.json",
            "layer_native_recomposition": feasibility["metrics"]["layer_native_recomposition"],
            "layer_native_mean_abs_rgb_255": feasibility["metrics"]["layer_native_mean_abs_rgb_255"],
            "full_source_mean_abs_rgb_255": feasibility["metrics"]["source_package_full_mean_abs_rgb_255"],
            "role": "DIAGNOSTIC_ONLY_UNTIL_PROVEN_CONSISTENT",
        },
        "decision": {
            "static_authority": "A_LOCKED",
            "manifest_layer_stack": "NOT_K2_AUTHORITY",
            "full_independent_k2_field": "NOT_PROVEN",
            "next": "Build an authored K2 field handoff against A with protected shell/core; do not interpolate legacy layer output.",
        },
        "files_sha256": {
            "static_composite.png": digest(static),
            "reference_foundation.png": digest(foundation),
            "a-authority.png": digest(authority),
            "a-authority-b-internal-study.png": digest(candidate),
        },
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "authority_exact_match": report["selected_authority"]["exact_match"], "legacy_recomposition": report["legacy_manifest"]["layer_native_recomposition"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
