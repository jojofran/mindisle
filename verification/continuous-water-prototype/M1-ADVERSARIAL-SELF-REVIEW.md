# MindIsle WaterBall M1 Evidence Package
## Adversarial Self-Review and Evidence Correction Report

审计范围：仅审查当前目录中的 M1 Evidence Package。
审计对象：verification/continuous-water-prototype/。
审计目标：检查 reference provenance、Carrier A/B/C 命名、状态一致性、M1 milestone 隔离、REPORT 与实际文件的一致性，以及 Review 页面是否可复核。
本报告不审查 Web、Unity、Blender 或其他仓库的实现状态，也不把它们作为 M1 结论依据。

## 1. 审计结论

本次审计发现并修正了 5 类问题：

1. Frozen K2 在 REPORT 与 Review 页面使用了不同 reference 文件。
2. REPORT 中 Carrier B/C 的定义与现有 evidence metadata 不一致。
3. 旧 evidence.json 同时包含连续 transport、core continuity 和 M1 material study，容易被误读为当前 M1 authority。
4. Review 页面原本没有逐项展示 Candidate C 0.00、0.25、0.50、0.75。
5. 缺少只包含当前 M1 authority 的 machine-readable evidence 入口。

修正后：

    REFERENCE PROVENANCE = PASS
    CARRIER NAMING CONSISTENCY = PASS
    STATUS CONSISTENCY = PASS
    MILESTONE EVIDENCE ISOLATION = PASS

    M1 REVIEW PACKAGE = READY_FOR_HUMAN_REVIEW
    MATERIAL FAMILY = AWAITING HUMAN REVIEW
    NEUTRAL POSE = AWAITING HUMAN REVIEW
    READY_FOR_M2 = NO

## 2. 当前 M1 authority 入口

当前唯一的 M1 machine-readable authority 是：

- [m1-current-evidence.json](m1-current-evidence.json)

该文件只包含：

- milestone = M1
- Candidate C primary reference
- Candidate D K0 restraint reference
- Frozen K2 endpoint reference
- current neutral material hero/source
- Carrier A/B/C 定义
- current technical structure status
- MATERIAL FAMILY human gate
- NEUTRAL POSE human gate
- readyForM2 = false

该文件明确禁止将 M3 spatial transport、M4 core integration 或未来 milestone completion 当作当前 M1 结论。

## 3. Reference provenance 审计

| Reference | 当前路径 | 用途 |
|---|---|---|
| Candidate C 0.00 | [formation-0.00.png](../slice-a-final-review/evidence/formation-0.00.png) | primary material input |
| Candidate C 0.25 | [formation-0.25-close.png](../slice-a-final-review/evidence/formation-0.25-close.png) | cloudy/depth reference |
| Candidate C 0.50 | [formation-0.50-close.png](../slice-a-final-review/evidence/formation-0.50-close.png) | cloudy/detail reference |
| Candidate C 0.75 | [formation-0.75-close.png](../slice-a-final-review/evidence/formation-0.75-close.png) | optical maturity upper bound |
| Candidate D K0 | [k0-close.png](../slice-a-final-review/evidence/k0-close.png) | neutral restraint |
| Frozen K2 | [k2-reference-close.png](../slice-a-formation-20260927/k2-reference-close.png) | endpoint reference |
| New Neutral Material | [m1-neutral-hero.png](m1-neutral-hero.png) | current M1 hero |

所有路径均为相对于本报告目录的路径。

### 修正前的问题

REPORT 原先使用：

    ../slice-a-final-review/evidence/k2-close.png

Review 页面使用：

    ../slice-a-formation-20260927/k2-reference-close.png

这两个文件不是同一 artifact。修正后 REPORT、Review 页面和 m1-current-evidence.json 统一使用：

    ../slice-a-formation-20260927/k2-reference-close.png

结论：

    REFERENCE PROVENANCE = PASS

## 4. Carrier A/B/C 审计

| ID | 名称 | 来源 | 视觉职责 |
|---|---|---|---|
| Carrier A | neutral volume | 02_internal_cyan_volume | large cloudy volume |
| Carrier B | sparse water detail | 04_flow_layer、05_flow_layer、06_fine_ink_wash | low-contrast sparse detail |
| Carrier C | thickness / optical | 11_curvature_highlights | broad membrane/refraction vocabulary |

对应文件：

- [REPORT.md](REPORT.md)
- [m1-current-evidence.json](m1-current-evidence.json)
- [index.html](index.html)
- [authority-audit.json](authority-audit.json)

修正前，REPORT 将 Carrier B 写成 thickness/optical、Carrier C 写成 sparse detail，而现有 evidence metadata 与 Review 控件使用相反含义。现在所有当前 M1 入口统一为上表定义。

    CARRIER NAMING CONSISTENCY = PASS

## 5. Status consistency 审计

当前 M1 的技术状态和人工视觉 gate 分开记录：

    TECHNICAL STRUCTURE = PASS
    MATERIAL FAMILY = AWAITING HUMAN REVIEW
    NEUTRAL POSE = AWAITING HUMAN REVIEW
    READY_FOR_M2 = NO

这表示证据结构可复核，但材质家族和 neutral pose 仍需人工裁决，M1 尚未关闭，M2 不得开始。

以下文件已明确标记为非当前 M1 authority：

- [authority-audit.json](authority-audit.json)
  - HISTORICAL_NON_AUTHORITATIVE_FOR_M1
  - currentM1Authority = false
  - supersededBy = m1-current-evidence.json
- [evidence.json](evidence.json)
  - HISTORICAL_MIXED_SCOPE_NON_AUTHORITATIVE_FOR_M1
  - currentM1Authority = false
  - supersededBy = m1-current-evidence.json

这些文件保留历史 transport、continuity、core 或 prototype 数据，但不能被解释为当前 M1 material family PASS。

    STATUS CONSISTENCY = PASS

## 6. Milestone isolation 审计

M1 当前只允许 neutral material study。当前 M1 authority 没有声明以下内容已通过：

- M3 spatial transport PASS
- M4 core integration PASS
- formation product semantics
- deformation
- core migration
- transitioning / moving
- production renderer migration
- future milestone completion

当前 Hero 与 source 只用于 verification-only 的人工材质判断：

- [m1-neutral-hero.png](m1-neutral-hero.png)
- [m1-neutral-source.png](m1-neutral-source.png)

Review 页面中的 Candidate C、Candidate D 和 Frozen K2 被标记为 reference input，不作为 M1 pass result。

    MILESTONE EVIDENCE ISOLATION = PASS

## 7. Review 页面复核

Review 页面：

- [index.html](index.html)

当前默认页面展示 7 项：

1. Candidate C 0.00
2. Candidate C 0.25
3. Candidate C 0.50
4. Candidate C 0.75
5. Candidate D K0
6. Frozen K2
7. New Neutral Material

控件还可以查看：

- New Neutral Material hero
- Neutral source
- Carrier A
- Carrier B
- Carrier C

实际加载检查：

    images checked = 8
    broken images = 0
    captions = 7

8 张图片包含 7 张 reference review 图片，以及默认 stage 中重复显示的一张 M1 hero。

页面状态：

    M1 VISUAL = AWAITING HUMAN REVIEW
    TECHNICAL STRUCTURE = PASS
    READY_FOR_M2 = NO

## 8. 原判断复核

### 已确认

- M1 仍为 ACTIVE。
- M2 仍为 BLOCKED。
- M3/M4 evidence 不能作为 M1 current authority。
- MATERIAL FAMILY 仍需人工判断。
- NEUTRAL POSE 仍需人工判断。
- READY_FOR_M2 必须为 NO。
- 当前 Hero 不是 production asset authority。

### 被推翻或修正

1. “Review 页面已经完整展示所有指定 reference”不成立，原页面缺少 Candidate C 四个逐项入口，已补齐。
2. “Carrier A/B/C 已完全一致”不成立，REPORT 中 B/C 含义曾与 evidence metadata 相反，已统一。
3. “Frozen K2 provenance 已统一”不成立，REPORT 与 Review 页面原先指向不同文件，已统一。
4. “旧 evidence 可以直接作为当前 M1 evidence”不成立，旧 JSON 已标记 historical/superseded，并新增 current M1 入口。

## 9. 修改清单

本次只修改 evidence/report/review package：

- [REPORT.md](REPORT.md)
  - 修正 Frozen K2 路径
  - 修正 Carrier B/C 命名
  - 将 MATERIAL SYSTEM STRUCTURE 改为 TECHNICAL STRUCTURE
- [index.html](index.html)
  - 增加 Candidate C 四个逐项 reference
  - 统一 Candidate D 和 Frozen K2 provenance
  - 将状态文案改为 TECHNICAL STRUCTURE = PASS
- [authority-audit.json](authority-audit.json)
  - 标记为历史、非当前 M1 authority
- [evidence.json](evidence.json)
  - 标记为历史混合范围、非当前 M1 authority
- [m1-current-evidence.json](m1-current-evidence.json)
  - 新增当前 M1 machine-readable evidence 入口

## 10. 未修改内容

本次没有修改：

- Neutral Material 像素结果
- Carrier 像素结果
- shader
- production renderer
- production assets
- frozen still manifest
- formation
- deformation
- core implementation
- timing
- roadmap milestone 状态

## 11. 最终裁决

    REFERENCE PROVENANCE = PASS
    CARRIER NAMING CONSISTENCY = PASS
    STATUS CONSISTENCY = PASS
    MILESTONE EVIDENCE ISOLATION = PASS

    M1 REVIEW PACKAGE = READY_FOR_HUMAN_REVIEW
    MATERIAL FAMILY = AWAITING HUMAN REVIEW
    NEUTRAL POSE = AWAITING HUMAN REVIEW
    READY_FOR_M2 = NO

本报告只对 M1 Evidence Package 的证据组织和自检修正负责，不替代人工 Material Family 或 Neutral Pose 裁决。
