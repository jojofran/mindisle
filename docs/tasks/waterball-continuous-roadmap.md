# WaterBall Continuous Water Roadmap

Current active milestone: **M2 — Static GPU Material**

本文件是 Continuous Water 的唯一执行入口。它只记录 milestone 状态、边界和下一步；当前代码事实读取 [`docs/analysis/CURRENT_RUNTIME_FACTS.md`](../analysis/CURRENT_RUNTIME_FACTS.md)，产品冻结语义仍以正式 product authority 为准。

## M-1 — Repository Truth Sync

- **Status:** PASS
- **Goal:** 建立当前本地 working tree 的代码事实、证据事实和 stale document 边界。
- **Frozen:** 当前事实入口与已记录的冲突。
- **Allowed:** 更新事实文档、标记冲突、补充证据引用。
- **Forbidden:** 用文档改写代码事实，顺手修复历史文档或 production。
- **Acceptance:** `CURRENT_RUNTIME_FACTS.md` 可作为当前实现事实入口，冲突明确可追溯。
- **Next:** 保持关闭；如有新证据，单独建立回归记录。

## M0 — Authority Freeze

- **Status:** PASS
- **Goal:** 冻结产品 authority、production snapshot 和 experimental authority 的边界。
- **Frozen:** ProductState、formal silhouette、几何参数、K2 endpoint、07–10 optical identity、lifecycle / single-loop 原则。
- **Allowed:** 在 verification / experimental 范围继续验证新路线。
- **Forbidden:** 将实验成功当作 production authority，或静默替换 v1 manifest / asset contract。
- **Acceptance:** authority matrix、full-frame crossfade 边界和 K2 migration gate 已记录。
- **Next:** 保持关闭；后续 milestone 只能在这些边界内执行。

## M0.5 — Last-Good Visual Recovery

- **Status:** PASS
- **Goal:** 汇总历史视觉候选，交由人工裁决 last-good reference。
- **Frozen:** 候选证据不得被 Agent 自动排序或转成 product authority。
- **Allowed:** Review 页面、历史截图、provenance 和 commit 查找信息。
- **Forbidden:** 近似重建历史版本、替换当前 production 或自行宣布 last-good。
- **Acceptance:** 候选来源、可恢复程度和人工选择入口完整记录。
- **Next:** 将人工选择结果作为 M1 的视觉参考输入。

## M1 — Neutral Water Material

- **Status:** PASS / FROZEN
- **Closure:** CLOSED / FROZEN — MATERIAL SOURCE PACKAGE ONLY
- **Goal:** 建立 pose-neutral、provenance-clean、deformation-ready、可供 GPU 采样的 internal material source package。
- **Frozen:** formal silhouette；center / radius / hitRadius；Frozen K2 endpoint；07–10 cold/warm optical identity；ProductState / interaction semantics；lifecycle / single-loop principles。
- **Allowed:** `verification/` 或明确 `experimental/` 范围内的新 neutral material source、neutral volume、thickness / optical source、sparse water detail、material study、screenshots、diagnostics。Primary material reference = Final Art 0.25 verified reference；depth/thickness reference = Final Art 0.50；material maturity upper bound = Final Art 0.75；neutral restraint = Candidate D K0；final endpoint authority = Frozen K2 Final Art。
- **Forbidden:** 修改 production renderer；修改 frozen still v1 manifest；formation / deformation；core migration；timing；transitioning / moving；production migration。
- **Acceptance:** source package 通过 pose-neutral、no-core、no-cavity、no-directional-pose、no-donor-topology、stable provenance、authored cloudy volume、meaningful thickness、organic sparse detail 和 GPU-sampling suitability 检查。raw source 不自证最终 rendered material family；最终视觉 family gate 迁移到 M2。
- **Next:** 保持 source package 关闭；M2 负责 static rendered material family 与 shell / optical integration 的人工 gate。

## M2 — Static GPU Material

- **Status:** ACTIVE
- **Goal:** 将通过 M1 的 neutral material 建立为静态 GPU material study。
- **Frozen:** M1 的 material identity、silhouette、K2 endpoint 和产品语义。
- **Allowed:** 只在 M1 CLOSED 后验证静态 GPU pass、masking 和诊断。
- **Forbidden:** formation、deformation、interaction timing、production migration。
- **Acceptance:** Human Gate A — Static rendered material family；Human Gate B — Static shell / optical integration。GPU material 必须真实采样 neutral volume、thickness / depth、sparse detail、formal silhouette 和 formal outer film；thickness 必须参与最终 pixel output。M2 未通过前禁止 M3。
- **Next:** 完成最多 3 个受限的 builder → fresh critic → repair cycle；结束状态只能是 `READY FOR HUMAN REVIEW` 或 `BLOCKED`，并记录 blocker 类型。

## M3 — Continuous Field

- **Status:** BLOCKED
- **Goal:** 在同一 body domain 内验证 continuous field / parameter interpolation。
- **Frozen:** M1/M2 已通过的 material family、formal silhouette 和 K2 endpoint。
- **Allowed:** D/R field、thickness、density、carrier 和参数插值的 experimental prototype。
- **Forbidden:** full-frame state image crossfade、formation product semantics、production asset 替换。
- **Acceptance:** continuous field 结构通过，且 K2 endpoint = PASS。
- **Next:** 等待 M2 CLOSED。

## M4 — Core Integration

- **Status:** BLOCKED
- **Goal:** 将 frozen 07–10 cold/warm optical identity 接入连续材质实验。
- **Frozen:** 07–10 identity、pair order、色彩关系和 K2 optical authority。
- **Allowed:** core position / optical parameter integration study。
- **Forbidden:** 重画或替换 07–10 identity，或提前改变 ProductState。
- **Acceptance:** core integration 通过 continuity、silhouette 和人工视觉检查。
- **Next:** 等待 M3 CLOSED。

## M5 — Real Interaction Timing

- **Status:** BLOCKED
- **Goal:** 将已通过的连续视觉参数接入真实 interaction timing 验证。
- **Frozen:** ProductState、pointer semantics、effectiveVisualTime、single RAF、suspend / resume / reset。
- **Allowed:** 只验证当前正式纳入 scope 的真实输入与时间路径。
- **Forbidden:** 为满足最终 E2E target 提前实现 moving 或修改产品语义。
- **Acceptance:** 当前 milestone scope 的真实输入、状态读取和生命周期证据通过。
- **Next:** 等待 M4 CLOSED。

## M5.5 — Rendering Contract v2

- **Status:** BLOCKED
- **Goal:** 在 production migration 前建立并人工批准 v2 rendering contract。
- **Frozen:** v1 production baseline、asset ownership、formal silhouette、K2 gate 和回退边界。
- **Allowed:** 明确 source provenance、body-domain contract、K2 proof、fallback / rollback 和 migration ownership。
- **Forbidden:** 在 contract 获批前替换 v1 renderer 或 asset authority。
- **Acceptance:** Rendering Contract v2 获得人工批准，且 K2 endpoint = PASS。
- **Next:** 等待 M5 CLOSED，并完成 contract review。

## M6 — Production Migration

- **Status:** BLOCKED
- **Goal:** 在 contract v2 和 K2 PASS 后迁移 production renderer / asset contract。
- **Frozen:** 已批准的 v2 contract、产品语义和回退路径。
- **Allowed:** 受控 migration、comparison、rollback verification。
- **Forbidden:** 以 prototype PARTIAL / FAIL 结果迁移，或跳过人工 gate。
- **Acceptance:** migration、fallback 和 production evidence 全部通过人工审查。
- **Next:** 等待 M5.5 CLOSED。

## M7 — Moving

- **Status:** BLOCKED
- **Goal:** 在 production migration 完成后实现并验证 moving。
- **Frozen:** ProductState、interaction semantics、lifecycle、silhouette、K2 endpoint 和 approved renderer contract。
- **Allowed:** moving 的真实状态路径、时间行为和目标设备验证。
- **Forbidden:** 在前置 milestone 关闭前伪造或提前实现 transitioning / moving。
- **Acceptance:** 最终 E2E target 与真实状态、视觉、计时、音乐、触感和生命周期证据一致。
- **Next:** 等待 M6 CLOSED。
