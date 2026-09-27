# M1 — Neutral Water Material

## 0. 实际参考检查

本轮实际打开并检查了以下 self-contained reference package：

- [C · 0.00](references/candidate-c-0.00.png) — historical sequence reference
- [C · 0.25](references/candidate-c-0.25.png) — **PRIMARY MATERIAL RICHNESS REFERENCE**
- [C · 0.50](references/candidate-c-0.50.png) — depth / thickness / cloudy structure reference
- [C · 0.75](references/candidate-c-0.75.png) — mature material upper bound，**POSE CONTAMINATION = HIGH**
- [Candidate D · K0](references/candidate-d-k0.png) — neutral restraint reference
- [Frozen K2](references/frozen-k2.png) — final optical/material endpoint，**ENDPOINT-ONLY**

详细来源、hash、身份和使用边界见 [references/provenance.json](references/provenance.json)。所有图片都是视觉 reference only，不是 shader texture、carrier raw input 或 neutral material source；C0.75 与 Frozen K2 的 cavity、swirl、directional density、final pose 均禁止直接继承。

## 1. 本轮修改

- 保留现有 `m1-neutral-hero.png` 与 `m1-neutral-source.png` 的 neutral material study；本次 reference recovery 没有修改 Neutral Material 像素。
- M1 仍以 `01_outer_film` 的 formal silhouette / 膜面语言为外层边界；本次不引入 core、formation、cavity、directional flow、timing 或 production renderer。
- Review 页改为真实并排展示六张 tracked reference 与 New Neutral，并保留三类 carrier debug view；默认打开 New Neutral Hero。

## 2. Material source / carrier 结构

源层边界依据 [waterball-clear-still-source-layer-audit.md](../../docs/analysis/waterball-clear-still-source-layer-audit.md)，产品视觉约束依据 [state-ball-visual-spec.md](../../docs/product/state-ball-visual-spec.md)。

- **Carrier A — neutral volume**：`derivedFrom = 02_internal_cyan_volume`；`directSample = false`、`neutralizationRequired = true`，经方向中和后形成主体体积。
- **Carrier B — sparse water detail**：`derivedFrom = 04_flow_layer / 05_flow_layer / 06_fine_ink_wash`；`directSample = false`、`neutralizationRequired = true`，只保留稀疏低对比 detail vocabulary，不做 full-frame alpha takeover。
- **Carrier C — thickness / optical**：`derivedFrom = 11_curvature_highlights`；`directSample = false`、`neutralizationRequired = true`，只保留大尺度 broad membrane/refraction vocabulary。
- `03_boundary_mask`、K2 cavity、pose composite、完整 K2 overlay 和 core source 均未作为 neutral 输入。

当前 Hero 是 verification-only 静态 raster preview；它用于人工材质判断，不是 production asset authority，也不证明 M2 静态 GPU 已完成。

## 3. 为什么这轮调整针对主要差距

Hero 中心由单一浅色渐变改为柔和、非对称的多尺度 cloudy volume，避免 cavity、swirl 或单一方向流线；中心与边缘的密度差更连续，保留水体重量。膜面高光被压成宽而低对比的光学层，边缘仍有前后层次但不读成玻璃球。细节只作为几处近乎消失的水感 breakup，避免 fingerprint / contour / marble / procedural-noise 观感。

## 4. Pose contamination / representation blocker

- 没有新增可读的 pose、cavity、swirl 或 directional flow。
- 历史 source layer 仍带有姿态来源信息，当前仅通过低频/稀疏 projection 使用；combined material 是否已经“同一种水”仍需人工 Gate A 判断。
- 未发现需要阻塞本轮提交人工视觉验收的 representation blocker；M2 仍按 roadmap 保持 blocked。

## 5. Evidence

- **M1 Neutral Material Hero**：[`m1-neutral-hero.png`](m1-neutral-hero.png)
- **Neutral source**：[`m1-neutral-source.png`](m1-neutral-source.png)
- **Review page**：[`index.html`](index.html)
- **Reference provenance**：[`references/provenance.json`](references/provenance.json)
- **对比**：页面默认并排 Candidate C / Candidate D / Frozen K2 / New Neutral；单选项可查看 neutral source 与三类 carrier debug。
- **运行时检查**：`window.__M1_NEUTRAL__.inspect()` 返回 `state=static`、`cores=false`、`formation=false`、`cavity=false`、`directionalFlow=false`、`passes=1`、`framebuffers=0`。

## 6. Gate result

- TECHNICAL STRUCTURE = **PASS**
- MATERIAL FAMILY = **AWAITING HUMAN REVIEW**
- NEUTRAL POSE = **AWAITING HUMAN REVIEW**
- READY_FOR_M2 = **NO**
