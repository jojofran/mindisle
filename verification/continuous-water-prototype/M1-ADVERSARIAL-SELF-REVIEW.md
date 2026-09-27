# MindIsle WaterBall M1 Evidence Package
## Adversarial Self-Review and Evidence Correction Report

审计范围：`verification/continuous-water-prototype/` 的 M1 reference、authority、carrier semantics 和 Review 页面。本文不审查 Web、Unity、Blender 或 production 实现，也不把它们作为 M1 结论依据。

## 1. 审计结论

当前唯一 machine-readable M1 authority 是 [`m1-current-evidence.json`](m1-current-evidence.json)。reference package 已复制到 [`references/`](references/)，并由 [`references/provenance.json`](references/provenance.json) 记录原始路径、逐文件 SHA-256、视觉身份和使用政策。

```text
REFERENCE FILES EXIST = PASS
REFERENCE HASH MATCH = PASS
REFERENCE VISUAL IDENTITY = PASS
REPORT LINKS = PASS
REVIEW BROKEN IMAGES = 0
CARRIER NAMING = PASS
CARRIER SOURCE SEMANTICS = PASS
CURRENT M1 AUTHORITY = UNIQUE
HISTORICAL EVIDENCE ISOLATED = PASS
```

```text
M1 REVIEW PACKAGE = READY_FOR_HUMAN_REVIEW
MATERIAL FAMILY = AWAITING HUMAN REVIEW
NEUTRAL POSE = AWAITING HUMAN REVIEW
READY_FOR_M2 = NO
```

## 2. 当前 M1 authority 入口

[`m1-current-evidence.json`](m1-current-evidence.json) 只描述 M1 neutral material study：

- Candidate C 0.25 是 PRIMARY MATERIAL RICHNESS REFERENCE；
- Candidate C 0.50 是 DEPTH / THICKNESS / CLOUDY STRUCTURE REFERENCE；
- Candidate C 0.75 是 MATURE MATERIAL UPPER-BOUND，且 `POSE CONTAMINATION = HIGH`；
- Candidate D K0 是 NEUTRAL / RESTRAINT REFERENCE；
- Frozen K2 是 FINAL OPTICAL / MATERIAL FAMILY ENDPOINT AUTHORITY，`ENDPOINT-ONLY`；
- 当前 Hero/source 仍是 verification-only，不是 production asset authority；
- `TECHNICAL STRUCTURE = PASS`，两个视觉 gate 仍等待人工裁决，`readyForM2 = false`。

该文件禁止声明 M3 spatial transport、M4 core integration、formation/deformation、transitioning、moving 或 production migration 已通过。

## 3. Reference provenance 审计

| Reference | tracked clean path | 最终身份 |
|---|---|---|
| Candidate C 0.00 | [`references/candidate-c-0.00.png`](references/candidate-c-0.00.png) | HISTORICAL SEQUENCE REFERENCE |
| Candidate C 0.25 | [`references/candidate-c-0.25.png`](references/candidate-c-0.25.png) | PRIMARY MATERIAL RICHNESS REFERENCE |
| Candidate C 0.50 | [`references/candidate-c-0.50.png`](references/candidate-c-0.50.png) | DEPTH / THICKNESS / CLOUDY STRUCTURE REFERENCE |
| Candidate C 0.75 | [`references/candidate-c-0.75.png`](references/candidate-c-0.75.png) | MATURE MATERIAL UPPER-BOUND；POSE CONTAMINATION = HIGH |
| Candidate D K0 | [`references/candidate-d-k0.png`](references/candidate-d-k0.png) | NEUTRAL / RESTRAINT REFERENCE |
| Frozen K2 | [`references/frozen-k2.png`](references/frozen-k2.png) | FINAL OPTICAL / MATERIAL FAMILY ENDPOINT；ENDPOINT-ONLY |

六张图片均为 byte-preserving copy，未 resize、crop、recompress、recolor、sharpen、blur、去 UI 或改 alpha。逐文件 hash 与原 dirty worktree 相同，详见 [`references/provenance.json`](references/provenance.json)。

视觉 identity check 已实际打开原图并通过：C0.25 具有白青低饱和、丰富 cloudy volume 和水体厚度；C0.50 具有更明确的 depth/thickness/cloudy structure；C0.75 具有成熟 optical richness，但带 pose contamination；D K0 安静平衡且无明显 cavity；Frozen K2 是真正 final optical endpoint。C0.00 只保留历史连续序列身份。

所有 reference 都是 `VISUAL_REFERENCE_ONLY`。它们不得成为 canonical shader texture、carrier raw input 或 neutral material source texture。C0.75 的 cavity、swirl、directional density 与 Frozen K2 的 final pose 禁止直接采样或复制。

## 4. Carrier A/B/C 与 source semantics

| ID | 名称 | derivedFrom | directSample | neutralizationRequired |
|---|---|---|---:|---:|
| Carrier A | neutral volume | `02_internal_cyan_volume` | false | true |
| Carrier B | sparse water detail | `04_flow_layer`, `05_flow_layer`, `06_fine_ink_wash` | false | true |
| Carrier C | thickness / optical | `11_curvature_highlights` | false | true |

这三类 carrier 是 neutralized / derived material sources，不是 raw pose-contaminated K2 layer。`sources` 字段已从当前 M1 authority 中移除，避免把历史 layer 误读成可直接采样的 source。[`material-source-classification.json`](material-source-classification.json) 与 [`m1-current-evidence.json`](m1-current-evidence.json) 对 02、04、05、06、11 均明确 `directSample = false`、`neutralizationRequired = true`。

## 5. Historical evidence 隔离

[`authority-audit.json`](authority-audit.json) 与 [`evidence.json`](evidence.json) 保留历史价值，但都明确标记为 `HISTORICAL / NON-AUTHORITATIVE FOR M1`，`currentM1Authority = false`，并指向 `m1-current-evidence.json`。它们不能被解释为当前 M1 material family PASS，也不能替代当前 reference package。

## 6. Review 页面复核

Review 页面：[`index.html`](index.html)。默认 reference review 展示七项：

1. Candidate C 0.00；
2. Candidate C 0.25；
3. Candidate C 0.50；
4. Candidate C 0.75（明确 pose contamination）；
5. Candidate D K0；
6. Frozen K2（明确 endpoint-only）；
7. New Neutral Material（verification-only）。

控件可查看 New Neutral hero、Neutral source、Carrier A、Carrier B、Carrier C。页面所有 reference 图片均从 `references/` 加载，并提供 provenance 链接；历史 M3/M4 evidence 不占据 M1 主 Review。

实际加载矩阵：`images checked = 8`、`broken images = 0`、`captions = 7`；8 张图片包含 7 张 reference review 图片和 stage 中重复显示的一张 M1 hero。

页面状态：

```text
M1 VISUAL = AWAITING HUMAN REVIEW
TECHNICAL STRUCTURE = PASS
READY_FOR_M2 = NO
```

## 7. Authority docs

`docs/analysis/CURRENT_RUNTIME_FACTS.md` 与 `docs/analysis/WATERBALL_M0_AUTHORITY_FREEZE.md` 已从原 dirty worktree 纳入 clean branch，保留同一 authority 版本和内容；仅清理 3 个 Markdown 行尾空格以通过 `git diff --check`。`CURRENT_RUNTIME_FACTS` 保留其事实源快照 `037f300`；`037f300..cec2cd6` 未改动 production WaterBall 代码，因此与本基线和 roadmap 兼容。

## 8. 未修改内容

本任务没有修改 Neutral Material 像素、carrier 像素、shader、production renderer、production assets、frozen still manifest、formation、deformation、core implementation、timing 或 roadmap milestone 状态。

## 9. Final gate

```text
CLEAN BRANCH = PASS
REFERENCE VISUAL IDENTITY = PASS
REFERENCE PACKAGE SELF-CONTAINED = PASS
REFERENCE PROVENANCE = PASS
CARRIER SOURCE SEMANTICS = PASS
STATUS CONSISTENCY = PASS
MILESTONE EVIDENCE ISOLATION = PASS

M1 REVIEW PACKAGE = READY_FOR_HUMAN_REVIEW
MATERIAL FAMILY = AWAITING HUMAN REVIEW
NEUTRAL POSE = AWAITING HUMAN REVIEW
READY_FOR_M2 = NO
```

本报告不替代人工 Material Family 或 Neutral Pose 裁决，也不授权进入 M2/M3/M4。
