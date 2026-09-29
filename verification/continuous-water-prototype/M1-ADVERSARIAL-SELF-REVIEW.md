# MindIsle WaterBall M1 Evidence Package
## Corrected Final Art Authority and Clean Branch Consistency Review

> **SUPERSEDED STATUS (boundary correction):** this review predates the M1 →
> M2 boundary correction. Its raw visual-family conclusions and `READY_FOR_M2`
> line are historical. Current authority is `m1-current-evidence.json`.

审计范围：M1 current reference authority、provenance、Review 页面、roadmap identity、carrier semantics 和历史错误映射隔离。本文不审查 Web、Unity、Blender 或 production 实现，也不重新制作 Neutral Material。

## 1. Correction result

人工裁决已将 M1 canonical reference 从临时 Candidate C 标签切换到 Final Art IDs。当前唯一 machine-readable M1 authority 是 [`m1-current-evidence.json`](m1-current-evidence.json)，reference provenance 是 [`references/provenance.json`](references/provenance.json)。

```text
CORRECT FINAL_ART_025 = PASS
CORRECT FINAL_ART_050 = PASS
CORRECT FINAL_ART_075 = PASS
CORRECT FROZEN_K2 = PASS
REFERENCE HASH MATCH = PASS
CURRENT AUTHORITY USES NO WRONG CANDIDATE_C = PASS
```

## 2. Canonical reference identity

| ID | tracked path | role | authority / use policy |
|---|---|---|---|
| `FINAL_ART_025` | [`references/final-art-025.png`](references/final-art-025.png) | PRIMARY_MATERIAL_RICHNESS_REFERENCE | `VISUAL_MATERIAL_REFERENCE_ONLY` |
| `FINAL_ART_050` | [`references/final-art-050.png`](references/final-art-050.png) | DEPTH_THICKNESS_CLOUDY_STRUCTURE_REFERENCE | `VISUAL_MATERIAL_REFERENCE_ONLY`；不是 neutral pose reference |
| `FINAL_ART_075` | [`references/final-art-075.png`](references/final-art-075.png) | MATURE_MATERIAL_UPPER_BOUND | `POSE_CONTAMINATION = HIGH`；禁止复制 cavity/swirl/directional density/K2 pose |
| `FROZEN_K2_FINAL_ART` | [`references/frozen-k2-final-art.png`](references/frozen-k2-final-art.png) | FINAL_OPTICAL_ENDPOINT_AUTHORITY | `FROZEN_ENDPOINT`；`ENDPOINT_ONLY = true`；`DIRECT_SHADER_SOURCE = false` |
| `NEUTRAL_RESTRAINT_D_K0` | [`references/neutral-restraint-d-k0.png`](references/neutral-restraint-d-k0.png) | NEUTRAL_RESTRAINT_REFERENCE | 只负责安静、平衡、无明显 cavity/directional pose |
| `FINAL_ART_FIVE_FRAME` | [`references/final-art-five-frame.png`](references/final-art-five-frame.png) | SEQUENCE_CONTEXT_REFERENCE | context only；不是 shader source |
| `FINAL_ART_CLOSE_STRIP` | [`references/final-art-close-strip.png`](references/final-art-close-strip.png) | CLOSE_SEQUENCE_CONTEXT_REFERENCE | context only；不是 shader source |

六张新 Final Art 文件均来自原 dirty worktree 的唯一精确文件名。0.25/0.50/0.75/K2 close 在原 dirty worktree 的 `verification/m0.5-last-good-review/index.html` 中被明确引用；five-frame/close-strip 是原 dirty worktree 中唯一同名 root evidence。该历史页面仅用于 provenance 判断，不是 clean branch 当前输入。原图已实际打开确认视觉身份，复制前后逐文件 SHA-256 一致。

## 3. Wrong mapping isolation

此前的 Candidate C / old Frozen K2 映射已从 current `references/` 移到 [`historical/wrong-reference-mapping/`](historical/wrong-reference-mapping/)。该目录的 README 明确标记：

```text
NON_AUTHORITATIVE = true
WRONG_M1_REFERENCE_MAPPING = true
```

当前 authority 不再引用 `formation-0.25-close.png`、`formation-0.50-close.png`、`formation-0.75-close.png` 或 `k2-reference-close.png`。这些文件只保留历史追溯价值，不能被解释为 M1 material authority。

## 4. Current Neutral Material state

现有 `m1-neutral-hero.png` 与 `m1-neutral-source.png` 没有删除或修改；按当前边界，它们只证明 source-package inputs，不证明最终 optical family：

```text
M1 SOURCE PACKAGE = PASS / FROZEN
M1 CLOSURE SCOPE = MATERIAL SOURCE PACKAGE ONLY
RAW MATERIAL FAMILY = NOT_EVALUATED_AT_RAW_SOURCE_LEVEL
FINAL OPTICAL FAMILY = DEFERRED_TO_M2_HUMAN_REVIEW
READY_FOR_M2 = YES
```

本轮只修正 visual authority、provenance、review package 和 roadmap identity，不 retune Neutral Material，不进入 M2。

## 5. Carrier semantics

| Carrier | 定义 | derivedFrom | directSample | neutralizationRequired |
|---|---|---|---:|---:|
| A | neutral volume | `02_internal_cyan_volume` | false | true |
| B | sparse water detail | `04_flow_layer`, `05_flow_layer`, `06_fine_ink_wash` | false | true |
| C | thickness / optical | `11_curvature_highlights` | false | true |

Final Art / K2 reference 不会成为 carrier raw source。`material-source-classification.json` 与 `m1-current-evidence.json` 保持上述语义。

## 6. Roadmap and document audit

- `docs/tasks/waterball-continuous-roadmap.md`：已完成 M1 source-package boundary correction；M1 source package PASS/FROZEN，M2 ACTIVE，M3 BLOCKED。
- `AGENTS.md`：NO_CHANGE。
- `docs/analysis/CURRENT_RUNTIME_FACTS.md`：NO_CHANGE；视觉 reference 修正不改变 runtime facts。
- `docs/analysis/WATERBALL_M0_AUTHORITY_FREEZE.md`：NO_CHANGE；implementation authority 不涉及本次 reference identity。
- `REPORT.md`、`m1-current-evidence.json`、`index.html`：已统一使用 Final Art canonical IDs。

历史 M0.5 review 可以继续出现 Candidate C 作为历史恢复标签，但不得作为 current M1 authority；current package 已无旧 Candidate C image path。

## 7. Review page evidence

Review 页面：[`index.html`](index.html)。默认分组为：

1. Material Authority：Final Art 0.25、0.50、0.75、Frozen K2 Final Art；
2. Neutral Restraint：Neutral Restraint D K0；
3. Current Experiment：New Neutral Material；
4. Context：Final Art Five Frame、Final Art Close Strip。

实际打开 clean branch 页面后确认：

- `broken images = 0`；
- 0.25/0.50/0.75/K2 为本次人工确认的 Final Art 文件；
- 页面不再显示旧 formation 组作为 current reference；
- `FINAL_ART_075` caption 明确 `POSE CONTAMINATION = HIGH`；
- Frozen K2 caption 明确 `ENDPOINT ONLY`；
- New Neutral Material 像素未被修改。

## 8. Final consistency gate

```text
FINAL ART REFERENCE IDENTITY = PASS
REFERENCE PROVENANCE = PASS
CURRENT M1 AUTHORITY = CONSISTENT
WRONG REFERENCE MAPPING = REMOVED
REPORT / JSON / HTML = CONSISTENT
ROADMAP REFERENCE IDENTITY = CONSISTENT
CARRIER SEMANTICS = PASS
HISTORICAL WRONG MAPPING = NON_AUTHORITATIVE
BROKEN IMAGES = 0
git diff --check = PASS

M1 SOURCE PACKAGE = PASS / FROZEN
M1 = CLOSED / FROZEN — MATERIAL SOURCE PACKAGE ONLY
RAW MATERIAL FAMILY = DEFERRED_TO_M2_HUMAN_REVIEW
READY_FOR_M2 = YES
```

本报告不替代人工 Material Family 或 Neutral Pose 裁决，也不授权进入 M2。
