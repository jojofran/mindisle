# M2 Static GPU Material

## Scope

This is a verification-only experimental WebGL path. It does not touch
production, ProductState, formation, deformation, timing, moving, or core
integration.

## Renderer structure

`m2-static-material.html` uploads the frozen M1 volume, thickness, and detail
carriers plus the formal silhouette and outer film into one WebGL pass. The
fragment shader samples front, internal, and rear positions from the same
carriers. Thickness drives absorption, transmitted brightness, refractive UV
offset, and the front/internal/rear weighting. The page exposes input and GPU
debug views, three shell integration models, the M1 raw preview, and the M2
GPU hero beside the static references.

## Route checks and Fresh Critic

Cycle 1 found an overexposed white fog-ball. The repair reduced body and shell
weights. Cycle 2 found a flat saturated cyan / weak front-rear read. The repair
added thickness-dependent absorption, refractive sampling, and rim response.
The allowed extension cycle 3 tested a new hypothesis: shader luminance
desaturation of the authored source while retaining thickness modulation.

The result is a pale static water body with a readable thickness gradient and
no uniform white ring, but the internal variation remains too quiet for a
confident Final Art family match. This is an optical-model blocker, not a
source-provenance blocker. The page remains awaiting human visual review.

## Machine evidence

`m2-static-evidence.json` records the browser run: 5 input textures at 400×400,
1 draw, 0 framebuffers, 0 WebGL errors, no animation, and thickness enabled
in final pixel output. It does not claim `sameWaterFamily` or `materialLooksGood`.

## Final state

- M1 source package: structural criteria documented; authority transition is recorded separately because the existing M1.5 authority file is preserved.
- M2: active experimental work.
- M2 static GPU material: `BLOCKED`.
- M2 blocker type: `OPTICAL_MODEL`.
- Three.js: `NOT_JUSTIFIED`; current WebGL needs a material hypothesis change before a renderer comparison is meaningful.
- Ready for M3: `NO`.
