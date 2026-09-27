# M1 — Neutral Water Material

## 0. 实际参考检查

本轮实际打开并检查了以下项目内参考：

- [C · formation 0.00](../slice-a-final-review/evidence/formation-0.00.png)
- [C · formation 0.25](../slice-a-final-review/evidence/formation-0.25-close.png)
- [C · formation 0.50](../slice-a-final-review/evidence/formation-0.50-close.png)
- [C · formation 0.75](../slice-a-final-review/evidence/formation-0.75-close.png)
- [Frozen K2](../slice-a-formation-20260927/k2-reference-close.png)
- [Candidate D · K0](../slice-a-final-review/evidence/k0-close.png)

C 0.00 用于淡青 cloudy volume 与基础厚度；C 0.25 / 0.50 用于低频 cloudy depth 与克制的 water/ink 细节；C 0.75 只用于成熟度和光学厚度上限；Candidate D 用于维持中性平衡。中间帧的 cavity、swirl、directional density 与 K2 pose 均未复制。

## 1. 本轮修改

- 重做 `m1-neutral-hero.png` 与 `m1-neutral-source.png` 的 neutral material study：增加非对称低频 cloudy volume、轻微前后光学深度和少量低对比 water detail。
- 继续以 `01_outer_film` 的 formal silhouette / 膜面语言为外层边界；不引入 core、formation、cavity、directional flow、timing 或 production renderer。
- Review 页改为真实并排展示 Candidate C、Candidate D、Frozen K2、New Neutral，并保留三类 carrier debug view；默认打开 New Neutral Hero。

## 2. Material source / carrier 结构

源层边界依据 [waterball-clear-still-source-layer-audit.md](../../docs/analysis/waterball-clear-still-source-layer-audit.md)，产品视觉约束依据 [state-ball-visual-spec.md](../../docs/product/state-ball-visual-spec.md)。

- **Carrier A — neutral volume**：来自 `02_internal_cyan_volume` 的低频 cloudy / thickness vocabulary，经方向中和后形成主体体积。
- **Carrier B — sparse water detail**：来自 `04_flow_layer`、`05_flow_layer`、`06_fine_ink_wash` 的稀疏低对比 detail vocabulary；不做 full-frame alpha takeover。
- **Carrier C — thickness / optical**：来自 `11_curvature_highlights` 的 broad membrane/refraction vocabulary，只保留大尺度光学层次。
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
- **对比**：页面默认并排 Candidate C / Candidate D / Frozen K2 / New Neutral；单选项可查看 neutral source 与三类 carrier debug。
- **运行时检查**：`window.__M1_NEUTRAL__.inspect()` 返回 `state=static`、`cores=false`、`formation=false`、`cavity=false`、`directionalFlow=false`、`passes=1`、`framebuffers=0`。

## 6. Gate result

- TECHNICAL STRUCTURE = **PASS**
- MATERIAL FAMILY = **AWAITING HUMAN REVIEW**
- NEUTRAL POSE = **AWAITING HUMAN REVIEW**
- READY_FOR_M2 = **NO**
