# M1 — Neutral Water Material

## 0. 参考与本轮边界

本轮使用已锁定的 self-contained Final Art package：

- `FINAL_ART_025`：主要材质丰富度参考；
- `FINAL_ART_050`：深度、厚度和 cloudy structure 参考；
- `FINAL_ART_075`：成熟度上限，只看 optical richness，不继承 cavity、swirl、directional density 或 K2 pose；
- `FROZEN_K2_FINAL_ART`：最终 optical endpoint authority，只用于判断是否属于同一种水；
- `NEUTRAL_RESTRAINT_D_K0`：安静、平衡和无 pose contamination 的约束。

本轮只修改 `verification/continuous-water-prototype/` 中的 M1 experimental material 与 review artifacts。Neutral Pose、formal silhouette、outer membrane、core、formation、deformation、timing、ProductState、production renderer、shader production path 和 frozen v1 assets 均未修改。

## 1. 主要视觉 root cause

当前 New Neutral 的外膜和中性轮廓已经正确，最大差距是内部材质过于平均：cloudy mass 没有自然聚散，前后厚度读数偏弱，内部 sparse detail 几乎消失。因此它更像漂亮的半透明介质，还不像 Final Art 家族中有重量和空间层次的一团水。

## 2. 实际调整

- **Cloudy mass distribution**：在正式 silhouette 内加入柔和、非对称、低频的聚散质量；没有形成 cavity、swirl、directional flow 或中心 radial pose。
- **Optical thickness / depth**：增加 front water layer、cloudy internal mass 与 deeper translucent volume 的低对比叠层，保留银白膜面和柔和 rear transmission；没有玻璃球化、强 lens effect 或强 contrast。
- **Sparse natural detail**：加入少量不同尺度、低对比、近乎消失的内部特征，为未来 deformation 保留可追踪结构；没有 fingerprint、contour、marble、wood grain、repeating bands 或 procedural-noise demo。

这是两次窄幅视觉调整后的最终 M1 experimental output，没有继续堆叠高频 noise。

## 3. Carrier 职责

Carrier A/B/C 的职责没有改变：

- **Carrier A — neutral volume**：`derivedFrom = 02_internal_cyan_volume`，`directSample = false`，`neutralizationRequired = true`；负责大尺度 cloudy volume。
- **Carrier B — sparse water detail**：`derivedFrom = 04_flow_layer / 05_flow_layer / 06_fine_ink_wash`，`directSample = false`，`neutralizationRequired = true`；负责稀疏低对比水感细节。
- **Carrier C — thickness / optical**：`derivedFrom = 11_curvature_highlights`，`directSample = false`，`neutralizationRequired = true`；负责 broad membrane/refraction vocabulary。

没有新增 carrier，也没有把任何 Final Art 或 pose-contaminated layer 作为 raw shader source。

## 4. Pose contamination / representation blocker

当前 hero 没有可读的 core、formation、cavity、swirl 或 directional flow。Neutral Pose 的冻结约束未被修改；本轮没有发现需要升级为 `MATERIAL REPRESENTATION BLOCKER` 的问题。

## 5. Evidence

- **M1 Neutral Material Hero**：[`m1-neutral-hero.png`](m1-neutral-hero.png)
- **Neutral source**：[`m1-neutral-source.png`](m1-neutral-source.png)
- **Review page**：[`index.html`](index.html)
- **Reference provenance**：[`references/provenance.json`](references/provenance.json)
- **Evidence state**：[`m1-current-evidence.json`](m1-current-evidence.json)

Review 页面默认把 `FINAL_ART_025`、`FINAL_ART_050`、`FINAL_ART_075`、`FROZEN_K2_FINAL_ART`、`NEUTRAL_RESTRAINT_D_K0` 和 `NEW_NEUTRAL` 放在同一页面，并提供 Carrier A/B/C debug view。`window.__M1_NEUTRAL__.inspect()` 返回 `state=static`、`cores=false`、`formation=false`、`cavity=false`、`directionalFlow=false`、`passes=1`、`framebuffers=0`。

## 6. Gate result

- **MATERIAL SYSTEM STRUCTURE = PASS**
- **MATERIAL FAMILY = AWAITING HUMAN REVIEW**
- **NEUTRAL POSE = AWAITING HUMAN REVIEW（冻结约束未改动）**
- **READY_FOR_M2 = NO**

本轮不进入 M2，等待人工判断 New Neutral 与 Final Art / Frozen K2 是否明显属于同一种水体材质。
