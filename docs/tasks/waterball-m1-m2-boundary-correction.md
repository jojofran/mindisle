# WaterBall M1 → M2 Boundary Correction

## Decision

M1 produces a pose-neutral, provenance-clean, deformation-ready material
source package. Its carriers are internal GPU inputs, not a final rendered
optical result.

The package consists of:

- neutral cloudy volume;
- meaningful thickness / depth data;
- sparse organic water detail.

## Evidence boundary

Raw 2D carrier previews must not assert `sameWaterFamily` or
`materialRepresentationDefect = false`. Those claims require a real rendered
material and a human visual review. The M2 static GPU page is the first place
to evaluate transmission, absorption, refraction, front/internal/rear depth,
and formal-shell integration.

The existing M1.5 JSON remains preserved as historical evidence. This document
records the correction without silently rewriting that authority file.

## Scope handoff

M2 is limited to a static experimental GPU material. It must not introduce
formation, deformation, animation, timing, moving, core migration, or
production changes. The final M1 closure and roadmap activation remain a
human-gated authority transition.
