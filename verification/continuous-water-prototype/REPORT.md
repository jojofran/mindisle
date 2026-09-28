# M1.3 — Carrier Sanitation

## Final state

- **NEUTRAL VOLUME SANITATION = PASS**
- **DEFORMATION STRESS = PASS**
- **SPARSE DETAIL SANITATION = PASS**
- **FORMAL SHELL FINAL COMPOSITING = PASS**
- **MATERIAL RICHNESS = PRESERVED**
- **NEUTRAL POSE = PRESERVED**
- **CARRIER SANITATION = READY FOR HUMAN REVIEW**
- **READY_FOR_M2 = NO**

本轮只清理三个 carrier artifact：volume donor seam / geometry memory、sparse detail 矩形 patch、formal shell 最终合成描边感。没有改 Final Art、Frozen K2、thickness semantics、carrier roles、production、ProductState、interaction、formation、deformation system、core、timing、moving、roadmap，也没有进入 Three.js。

## Route Check

CURRENT PRIMARY DEFECT = neutral volume donor seam + sparse detail rectangular islands + shell continuous white rim
ROOT CAUSE TYPE = local carrier reconstruction masks and final source-over coverage
DONOR ROUTE CAN SOLVE = YES
WHY = artifacts are local reconstruction/compositing defects; the accepted Final Art donor and formal shell source already contain the required material vocabulary and optical identity
PROPOSED BAKING CHANGE = irregular local continuity repair, fragmented feathered detail masks, shell overlap subtraction with thinner source-over film alpha
EXPECTED VISIBLE EFFECT = no readable pasted arcs/seams, no rectangular detail islands, thinner nonuniform optical edge
FAILURE SIGNAL = any seam or rectangle survives the warp/alpha review, or the shell becomes a painted outline / material richness regresses

## Cycle 1 — Sanitize → Render → Stress Test → Fresh Critic

### Neutral Volume

原始 neutral-water-volume-raw.png 仍能读出 donor patch 的圆弧与重叠区域。修复只作用于六个已知 donor region：用确定性的 irregular feather mask，把局部 translated scaffold 混入原 authored field；没有 whole-image blur、镜像平均或 flatten cloudy structure。最终 carrier 是 neutral-water-volume.png。

Review-only neutral-water-volume-warp-stress.png 对最终 volume 施加小幅水平弯曲、垂直弯曲和 mild local stretch；这是可逆观察，不是 M3 deformation。warp 后没有拉出可读的圆弧、矩形边界、pasted island 或 feather seam，因此 DEFORMATION STRESS = PASS。

### Sparse Detail

原始问题是 keep window 造成的矩形 patch islands。现在使用不同尺度的 irregular feathered extraction mask，并叠加确定性的 fragment modulation，让结构断裂、非轴向、局部存在/缺失。sparse-detail-alpha-raw.png 保留真实 alpha；sparse-detail-alpha.png 只提高显示增益。Fresh alpha review 中不能数出明显矩形岛，读感是少量稀疏水纹 / ink-like internal structures，因此 SPARSE DETAIL SANITATION = PASS。

### Shell Edge Compositing

Formal source 仍是 assets/waterball-still-v1/layers/01_outer_film.png，source pixels 未修改，也没有替换 shell source。A/B 输出见 shell-current-hero.png、m1-neutral-hero.png 和 shell-edge-ab-crop.png。审计确认问题来自 body 与 formal film 的 edge coverage 重叠；修复只在最终 compositor 中先扣除 overlap，再以较薄的 formal film alpha 做一次 source-over。shell-edge-alpha-current.png 与 shell-edge-alpha-sanitized.png 是 alpha 对照。

修复后的边缘更薄、更不均匀，连续白 rim / outline-like 感明显下降；formal source 视觉信息保留，因此 FORMAL SHELL FINAL COMPOSITING = PASS。

## Fresh Critic

只看 FINAL_ART_025、FINAL_ART_050、FROZEN_K2、D K0 与当前输出：

1. donor seam 还可见吗？当前静态与 warp stress 中没有明显 seam 或圆弧记忆。
2. sparse detail 还像 patch 吗？alpha view 不再呈矩形岛，读作稀疏、断裂的水纹结构。
3. shell 还像描边吗？A/B 中 B 的连续白边明显减弱，更接近 Final Art 的薄膜折射。
4. current Hero 是否保持原有 material richness？保持；cloudy mass、local density、white/cyan balance 和 authored spatial information 没有被全图抹平。
5. Neutral Pose 是否仍保持？保持；没有新增 cavity、swirl、强方向组织或 state-specific composition。

IMPROVEMENT = CLEAR。本轮没有进入第二个 sanitation cycle；没有 NONE、REGRESSION 或需要重复同一策略的信号。

## Final comparison and provenance

Current Hero：m1-neutral-hero.png。它只使用三个 verification-only baked carriers、formal outer film compositor 和既有 static composition；不直接采样 FINAL_ART_025，不成为 production asset contract。

完整输出与确定性指标见 carrier-sanity-metrics.json；原始 carrier 与 review-only stress/alpha 资产用于审计，不进入 runtime。

## Final boundary

NEUTRAL VOLUME SANITATION = PASS
DEFORMATION STRESS = PASS
SPARSE DETAIL SANITATION = PASS
FORMAL SHELL FINAL COMPOSITING = PASS
MATERIAL RICHNESS = PRESERVED
NEUTRAL POSE = PRESERVED
CARRIER SANITATION = READY FOR HUMAN REVIEW
READY_FOR_M2 = NO
DONOR CYCLES USED = 1 / 2
THREE.JS = NOT JUSTIFIED

Commit hash：本轮提交后记录于最终报告。
