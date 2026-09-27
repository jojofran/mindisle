# M1 — Neutral Water Material

## 0. 实际参考检查

本轮实际打开并检查了以下 self-contained reference package：

- [Final Art 0.25](references/final-art-025.png) — **FINAL_ART_025 / PRIMARY MATERIAL RICHNESS REFERENCE**
- [Final Art 0.50](references/final-art-050.png) — **FINAL_ART_050 / DEPTH_THICKNESS_CLOUDY_STRUCTURE_REFERENCE**
- [Final Art 0.75](references/final-art-075.png) — **FINAL_ART_075 / MATURE MATERIAL UPPER-BOUND / POSE CONTAMINATION = HIGH**
- [Frozen K2 Final Art](references/frozen-k2-final-art.png) — **FROZEN_K2_FINAL_ART / FINAL OPTICAL ENDPOINT / ENDPOINT-ONLY**
- [Neutral Restraint D K0](references/neutral-restraint-d-k0.png) — **NEUTRAL_RESTRAINT_D_K0 / NEUTRAL RESTRAINT ONLY**
- [Final Art Five Frame](references/final-art-five-frame.png) — **FINAL_ART_FIVE_FRAME / SEQUENCE CONTEXT REFERENCE**
- [Final Art Close Strip](references/final-art-close-strip.png) — **FINAL_ART_CLOSE_STRIP / CLOSE SEQUENCE CONTEXT REFERENCE**

详细来源、hash、身份和使用边界见 [references/provenance.json](references/provenance.json)。所有图片都是视觉 reference only，不是 shader texture、carrier raw input 或 neutral material source；Final Art 0.75 的 cavity、swirl、directional density、final pose 与 Frozen K2 的 final pose 均禁止直接继承。

## 1. 本轮修改

- 保留现有 `m1-neutral-hero.png` 与 `m1-neutral-source.png` 的 neutral material study；本次 reference recovery 没有修改 Neutral Material 像素。
- M1 仍以 `01_outer_film` 的 formal silhouette / 膜面语言为外层边界；本次不引入 core、formation、cavity、directional flow、timing 或 production renderer。
- Review 页按 Material Authority、Neutral Restraint、Current Experiment、Context 四组展示 tracked reference；New Neutral 仍保持原像素并标为 existing experimental output。

## 2. Material source / carrier 结构

源层边界依据 [waterball-clear-still-source-layer-audit.md](../../docs/analysis/waterball-clear-still-source-layer-audit.md)，产品视觉约束依据 [state-ball-visual-spec.md](../../docs/product/state-ball-visual-spec.md)。

- **Carrier A — neutral volume**：`derivedFrom = 02_internal_cyan_volume`；`directSample = false`、`neutralizationRequired = true`，经方向中和后形成主体体积。
- **Carrier B — sparse water detail**：`derivedFrom = 04_flow_layer / 05_flow_layer / 06_fine_ink_wash`；`directSample = false`、`neutralizationRequired = true`，只保留稀疏低对比 detail vocabulary，不做 full-frame alpha takeover。
- **Carrier C — thickness / optical**：`derivedFrom = 11_curvature_highlights`；`directSample = false`、`neutralizationRequired = true`，只保留大尺度 broad membrane/refraction vocabulary。
- `03_boundary_mask`、K2 cavity、pose composite、完整 K2 overlay 和 core source 均未作为 neutral 输入。

当前 Hero 是 verification-only 静态 raster preview；它用于人工材质判断，不是 production asset authority，也不证明 M2 静态 GPU 已完成。

## 3. Corrected reference basis

现有 `m1-neutral-hero.png` 与 `m1-neutral-source.png` 是在旧 reference mapping 背景下产生的 existing experimental output。本轮只替换 visual authority、provenance 与 review basis，不 retune、不删除、也不改变任何 Neutral Material 像素。

## 4. Pose contamination / representation blocker

- 没有新增可读的 pose、cavity、swirl 或 directional flow。
- 历史 source layer 仍带有姿态来源信息，当前仅通过低频/稀疏 projection 使用；combined material 是否已经“同一种水”仍需人工 Gate A 判断。
- 未发现需要阻塞本轮提交人工视觉验收的 representation blocker；M2 仍按 roadmap 保持 blocked。

## 5. Evidence

- **M1 Neutral Material Hero**：[`m1-neutral-hero.png`](m1-neutral-hero.png)
- **Neutral source**：[`m1-neutral-source.png`](m1-neutral-source.png)
- **Review page**：[`index.html`](index.html)
- **Reference provenance**：[`references/provenance.json`](references/provenance.json)
- **对比**：页面按四组展示 Final Art authority、Neutral Restraint、Current Experiment 与 sequence context；单选项可查看 neutral source 与三类 carrier debug。
- **运行时检查**：`window.__M1_NEUTRAL__.inspect()` 返回 `state=static`、`cores=false`、`formation=false`、`cavity=false`、`directionalFlow=false`、`passes=1`、`framebuffers=0`。

## 6. Gate result

- TECHNICAL STRUCTURE = **PASS**
- MATERIAL FAMILY = **AWAITING HUMAN REVIEW AGAINST CORRECTED FINAL-ART REFERENCES**
- NEUTRAL POSE = **AWAITING HUMAN REVIEW**
- READY_FOR_M2 = **NO**
