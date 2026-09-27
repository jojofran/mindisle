# M1 — Neutral Water Material · Representation Repair Loop

## 1. 最初 root cause

当前 Neutral 的 formal silhouette 与中性 pose 没有问题。材质 family blocker 来自 representation：旧 hero 主要由手工软 blob 和低强度叠加构成，缺少来自正式 source layers 的可读 cloudy mass、厚度场和 authored-like sparse structure。因此它太平、太薄、太柔，内部细节像 stain。

## 2. Representation correction

本轮没有继续做第三轮参数 polish，而是重构了 M1 experimental material source：

- 从 `02_internal_cyan_volume` 提炼低频 cloudy volume，并通过水平/垂直翻转平均去除 baked directional organization；
- 从 `06_fine_ink_wash` 提炼 authored-like sparse internal structure，保留低对比和不规则尺度，不使用 generic noise；
- 从 `11_curvature_highlights` 提炼 broad thickness / transmission vocabulary，作为低强度前后层；
- 重新组合 cloud / deep volume / sparse detail / transmission 四个静态层，固定 formal silhouette；
- 重新生成 `m1-neutral-hero.png`、`m1-neutral-source.png` 与三类 verification carrier debug 图。

没有采样 `FINAL_ART_025`、`FINAL_ART_050` 或 Frozen K2 作为 shader texture，也没有 full-frame crossfade、core、formation、cavity 或 directional flow。

## 3. 视觉循环结果

- **修复前**：内部是均匀的半透明渐变，细节读成 blob / stain。
- **第一轮 representation repair**：引入 source-derived cloudy field 和 authored-like sparse structure，内部开始出现真实水体组织，但深层厚度仍偏弱。
- **第二轮**：只提高 deep translucent volume 权重，增强前后空间感；没有增加高频噪声或改变 pose。
- **当前**：cloudy mass、内部 sparse structure 和透深已经可读，未再发现明显的 representation-level material-family defect，因此进入人工 Review。

## 4. 最终 material source / carrier 结构

Carrier 职责保持不变，但内部实现已替换：

- **Carrier A — neutral volume**：由 `02_internal_cyan_volume` 中和后的低频 field 提供 cloudy mass；`directSample = false`，`neutralizationRequired = true`。
- **Carrier B — sparse water detail**：由 `06_fine_ink_wash` 中和后的 authored-like field 提供稀疏内部结构；`directSample = false`，`neutralizationRequired = true`。
- **Carrier C — thickness / optical**：由 `11_curvature_highlights` 中和后的 broad field 提供 thickness / transmission；`directSample = false`，`neutralizationRequired = true`。

没有新增 carrier，没有改变 carrier 职责，没有修改 production renderer 或 shader production path。

## 5. Neutral Pose

**NEUTRAL POSE = PRESERVED**。当前 Hero 保持 calm / balanced neutral state；没有 cavity、swirl、directional mass organization、core 或 formation。

## 6. Current vs Final Art 对比

- 相比 `FINAL_ART_025`：当前已补上淡青 cloudy volume、内部质量聚散和低对比水感结构；仍保留 Neutral 的克制亮度。
- 相比 `FINAL_ART_050`：当前已补上更明显的前后透深与内部层次，但不复制其 formation pose、cavity 或 directional flow。
- 相比 `FROZEN_K2_FINAL_ART`：当前属于同一低饱和银白水体材质方向，但仍是无 core、无 formation 的 neutral endpoint study。

## 7. Hero / Review

- **Hero**：[m1-neutral-hero.png](m1-neutral-hero.png)
- **Neutral source**：[m1-neutral-source.png](m1-neutral-source.png)
- **Review page**：[index.html](index.html)
- **Evidence**：[m1-current-evidence.json](m1-current-evidence.json)

Review 页面默认并排展示 `FINAL_ART_025`、`FINAL_ART_050`、`FINAL_ART_075`、`FROZEN_K2_FINAL_ART`、`NEUTRAL_RESTRAINT_D_K0` 和当前 New Neutral，并提供 Carrier A/B/C debug view。

## 8. Three.js feasibility review

Three.js `MeshPhysicalMaterial` 确实提供 `transmission`、`transmissionMap`、`thickness` 和 `thicknessMap`，可以表达体积边界与光学透射；但这些能力仍需要已有的 thickness / transmission source 才能产生有意义的结果，而且官方文档提示其 transmission 路径依赖环境反射并带来更高 per-pixel 成本。当前 blocker 已通过 source representation repair 解决，Three.js 不会补充缺失的 material information；迁移只会增加 renderer abstraction 和玻璃球风险。因此本轮不做 Three.js spike。

**THREE.JS = NOT NEEDED**。

## 9. Final state

- **MATERIAL SYSTEM STRUCTURE = PASS**
- **NEUTRAL POSE = PRESERVED**
- **MATERIAL FAMILY = READY FOR HUMAN REVIEW**
- **READY_FOR_M2 = NO**

本轮不进入 M2，不修改 production，不 push。
