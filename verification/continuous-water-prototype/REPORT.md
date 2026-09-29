# M1.4 — Donor Interior De-shelling & Source-Space Normalization

## Final state

- **M1.3 = CLOSED / EVIDENCE PRESERVED**
- **DONOR DE-SHELLING = PASS**
- **SOURCE TOPOLOGY MEMORY = REMOVED**
- **SPARSE DETAIL FEATURE EXTRACTION = PASS**
- **FORMAL SHELL OWNERSHIP = BLOCKED**
- **MATERIAL RICHNESS = PRESERVED**
- **NEUTRAL POSE = PRESERVED**
- **M1.4 SOURCE NORMALIZATION = BLOCKED**
- **READY_FOR_M2 = NO**
- **DONOR CYCLES USED = 1 / 2**

本轮没有重做 M1.3 sanitation，没有改 thickness、production、ProductState、interaction、formation、deformation system、core、timing、moving，也没有进入 M2 或 Three.js。

## 1. M1.3 保留项

M1.3 的 irregular local blending、RGB/BGR correctness、core residue removal、formal outer source 接入和 Neutral Pose 证据全部保留。M1.3 仅作为实验关闭，不回滚。

## 2. M1.3 自验收的修正

M1.3 的 hard seam 检查通过，但本轮复审确认它仍保留 donor sphere / circular geometry memory；固定 6 个 volume region 和 5 个 detail support box 也仍是隐藏的 topology authority。M1.3 的 0.34 outer-film attenuation 只能算实验性 compositing，不能当作 frozen optical fidelity。

## 3. Donor de-shell 方法

从 FINAL_ART_025 先建立 safe interior，再用 whole-interior material coordinate field 做两组大尺度坐标 remap，并以 multi-band deterministic blend 重新组织 cloudy material。最终构造路径不再调用固定 6-region donor_recompose 或 fixed-region sanitize。

## 4. SAFE INTERIOR 定义

SAFE_INTERIOR_MASK 基于 FINAL_ART_025 的视觉 body extent，经内缩去除 membrane/rim band，并排除 UI/text 与低置信边缘。它只决定 donor vocabulary 的取样资格，不成为 runtime silhouette，也不进入 production authority。

## 5. Unclipped RGB evidence

neutral-water-volume-unclipped-rgb.png 在没有 silhouette alpha 时仍是连续 cloudy water material；没有完整圆环、第二颗球、shell arc、stacked sphere 或 circular donor boundary。这个 gate 通过。

## 6. Fixed-box authority

固定 6 个 volume box 和固定 5 个 detail box 保留在脚本中作为 historical negative evidence，但不再参与 M1.4 final construction。最终 topology authority 已切换到 whole-interior coordinate field 和 actual connected feature selection。

## 7. Sparse feature extraction

Detail 从整个 SAFE_INTERIOR 做 3/7/13 尺度 band-pass，按 connected / elongated feature 的面积、形态和对比度筛选，再做 irregular feather。输出 raw alpha、amplified alpha 和 feature-support-view。Alpha 中不再能读出 5 个 box 或固定 patch island。

## 8. Warp topology stress

对 de-shelled material field 做 horizontal bend、vertical bend、diagonal shear 和 local stretch。stress 后未出现 hidden sphere、source sphere edge、repeated donor topology 或 patch cluster。SOURCE TOPOLOGY MEMORY = REMOVED。

## 9. Shell ownership 修正

M1.4 A/B 保持内部 water material 完全相同：

- A：M1.3 body coverage + attenuated formal film；
- B：interior-body falloff + full formal outer-film source alpha。

B 没有全局乘 0.34，但 full formal source 仍形成接近连续的高亮环，和 FINAL_ART_025 的 optical context 不能确认一致。因此 FORMAL SHELL OWNERSHIP = BLOCKED。不能用再次削弱 formal film 的方式掩盖这个 blocker。

## 10. Material richness

cloudy mass、white/cyan balance、local density 和 authored spatial complexity 保留，没有退化成 radial gradient、fog 或 generic noise。

## 11. Neutral Pose

Neutral Pose 保持，没有新增 cavity、swirl、强方向组织或 state-specific composition。

## 12. Before / After Hero

M1.3 Hero 与 M1.4 Hero 已在 review 页面并列。M1.4 的内部 material 已完成 de-shelling 和 source-space normalization；当前阻塞仅是正式 outer-film full-alpha optical ownership。

## 13. Fresh Critic / cycle

第 1 轮 Route Check → Build → Render → Stress → Fresh Critic：

- volume de-shelling：CLEAR；
- topology stress：CLEAR；
- sparse feature extraction：CLEAR；
- shell ownership：REGRESSION relative to accepted Final Art context。

由于 shell 问题属于 formal source/compositing authority 边界，继续重复同一 sanitation strategy 没有依据，未机械消耗第 2 轮，进入 blocker 结论。

## 14. Provenance

FINAL_ART_025 仍为 offline derivation donor；FINAL_ART_050 仍只作 depth/thickness guide；FROZEN_K2 authority 未改。runtime direct sample、canonical final-frame texture 和 production dependency 均为 false。Thickness 在 M1.4 冻结。

## Final boundary

DONOR DE-SHELLING = PASS
SOURCE TOPOLOGY MEMORY = REMOVED
SPARSE DETAIL FEATURE EXTRACTION = PASS
FORMAL SHELL OWNERSHIP = BLOCKED
MATERIAL RICHNESS = PRESERVED
NEUTRAL POSE = PRESERVED
M1.4 SOURCE NORMALIZATION = BLOCKED
READY_FOR_M2 = NO
THREE.JS = NOT JUSTIFIED

Commit hash：本轮提交后记录于最终报告。
