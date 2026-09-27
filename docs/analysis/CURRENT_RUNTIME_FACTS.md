# CURRENT RUNTIME FACTS

审计日期：2026-09-27
事实源：当前本地 working tree。HEAD：`037f300508a2f975a34abe4b6ba4371ebf035fa7`（`feat: calibrate clear-still visual composition`）。本轮未修改生产代码、资产或既有文档。

## Runtime

- WaterBall 默认以 `state = 'still'` 构造；`setState()` 只允许 `still`，传入 `transitioning` 或 `moving` 会抛错。[waterball.js:18-24](../../components/waterball/waterball.js#L18-L24) [waterball.js:493-496](../../components/waterball/waterball.js#L493-L496)
- 当前 activation 不提交 ProductState。有效 pointer-up 会把 `interactionVisualState` 设为 `activated`、增加 `activationCount`，随后 microtask 回到 `clear`；`productState/state` 仍为 `still`。[waterball.js:530-561](../../components/waterball/waterball.js#L530-L561)
- `inspect()` 当前返回 `transitionProgress: null`、`movingPhase: null`、`orbitDomainReady: false` / `notImplemented`。[waterball.js:1207-1243](../../components/waterball/waterball.js#L1207-L1243)

## Interaction

- 输入绑定在透明 button 的 `pointerdown`、`pointermove`、`pointerup`、`pointercancel`。[waterball.js:67-75](../../components/waterball/waterball.js#L67-L75)
- `pointerDown` 只有在 `hitRadius` 内才进入 `press`；`pointerMove` 离开命中区后使本次 gesture 失效；`pointerUp` 只有仍在命中区且未失效时才进行一次 activation commit；`pointerCancel` 清除 gesture。[waterball.js:502-576](../../components/waterball/waterball.js#L502-L576)
- 命中区由 `profile.center/radius/hitRadius` 派生为圆形区域；它与视觉 silhouette 是不同职责。[waterball.js:454-463](../../components/waterball/waterball.js#L454-L463) [waterball.js:1218-1223](../../components/waterball/waterball.js#L1218-L1223)
- `suspend` 会取消未提交 gesture、停止 RAF；`resume` 只重新启动一个 RAF；`reset` 回到 `still + clear` 并清零有效视觉时间和 formation。[waterball.js:577-643](../../components/waterball/waterball.js#L577-L643)
- `effectiveVisualTime()` 以 `visualTime + activeSegment` 计算；`animationLoopRunning` 防止重复启动，当前是单 RAF loop。[waterball.js:580-600](../../components/waterball/waterball.js#L580-L600) [waterball.js:644-649](../../components/waterball/waterball.js#L644-L649)

## Rendering

- 当前 K0/K1 路径是 runtime composite：先画 `clearCompositeCanvas`，再叠加运行时生成的 `neutralInternalVolume`、`poseCompositeWithoutCores`、动态 body layers、runtime core pairs 和 WebGL material pass。[waterball.js:687-755](../../components/waterball/waterball.js#L687-L755) [waterball.js:757-886](../../components/waterball/waterball.js#L757-L886)
- `poseCompositeWithoutCores` 排除了 02–11，07–10 由独立 core pair 绘制；这形成了当前 K0/K1 的 core 去重路径。[waterball.js:170-208](../../components/waterball/waterball.js#L170-L208)
- 当前 draw path 在 `formation > 0.45` 时仍会叠加完整 `staticCompositeCanvas`，直到 `formation = 1` 才不再画 runtime core；这属于 implementation snapshot，不是新连续 renderer 的 authority。[waterball.js:883-901](../../components/waterball/waterball.js#L883-L901)
- 正式 silhouette 由 `01_outer_film` alpha、阈值 6、逐行左右边界填充生成；Canvas body/core 使用该 mask。[profile.js:27-33](../../components/waterball/profile.js#L27-L33) [waterball.js:465-491](../../components/waterball/waterball.js#L465-L491)
- 现有 WebGL fragment shader 仍有 `if(r>1.0) discard` 的圆形裁切，并同时采样 formal mask；因此 WebGL pass 尚未证明等同于 formal silhouette-only clipping。[waterball.js:224-230](../../components/waterball/waterball.js#L224-L230) [waterball.js:253-257](../../components/waterball/waterball.js#L253-L257)

## Core

- 07/08 和 09/10 分别组成 cold/warm pair，按 source-over 合成，并由同一套 pair 在 K0/K1 中平移；`inspect()` 报告 `coreOpticalAuthority = frozen-k2-07-10`。[waterball.js:193-208](../../components/waterball/waterball.js#L193-L208) [waterball.js:1067-1088](../../components/waterball/waterball.js#L1067-L1088) [waterball.js:1237-1239](../../components/waterball/waterball.js#L1237-L1239)
- 旧 procedural core field 仍存在，但代码注释将其标成 diagnostic-only；正常 K0/K1 路径调用的是 `drawRuntimeCoreLayers()`。[waterball.js:1095-1100](../../components/waterball/waterball.js#L1095-L1100)
- **Double-core fix 当前状态：局部存在。** 07–10 已从 `poseCompositeWithoutCores` 排除；但完整 K2 overlay 仍使 formation 中段同时存在 runtime core 与 baked K2 composite，不能把“全路径无重复”当作已证事实。[waterball.js:170-208](../../components/waterball/waterball.js#L170-L208) [waterball.js:883-901](../../components/waterball/waterball.js#L883-L901)

## K2

- frozen K2 endpoint 是正式 `static_composite.png` 及 12 层 v1 atlas；`profile.js` 的 layer order 与正式 manifest 对齐。[assets manifest](../../assets/waterball-still-v1/manifest.json#L1-L46) [profile.js](../../components/waterball/profile.js#L34-L60)
- core continuity evidence 报告 `staticCompositeCanvas` 与 frozen `static_composite.png` 的最大像素差为 1、平均绝对差为 0.0061，source assets unchanged。[postfix summary](../../verification/slice-a-core-continuity-20260927/postfix-summary.md#L5-L17)
- 该证据只证明当时记录的 K2 回归与 core pair 规则，不能覆盖当前 formation 中段的完整 K2 overlay。

## K2 optical / 11 curvature

- `11_curvature_highlights` 不是完全 pose-neutral 的 outer membrane；layer audit 将其标为“局部位置/强度带有 K2 关系”。[source-layer audit](../../docs/analysis/waterball-clear-still-source-layer-audit.md#L27-L40)
- 因此 11 只能作为经中和后的 optical/thickness vocabulary，不能归入完全 frozen outer membrane。

## Attraction

- Slice A 的 attraction hard requirement 已移除；允许 very subtle local density/refraction 或辅助 field，但不再以 clearly readable attraction、directional bending、spatial warp 或 perceptible mass drag 作为 PASS 条件。[attraction audit](../../docs/analysis/waterball-attraction-feasibility-audit.md#L7-L11) [attraction boundary](../../docs/analysis/waterball-attraction-feasibility-audit.md#L37-L47)
- production code 仍保留 attraction/WebGL warp debug routes；它们属于诊断入口，不改变 Slice A acceptance boundary。[waterball.js:670-681](../../components/waterball/waterball.js#L670-L681) [waterball.js:909-1043](../../components/waterball/waterball.js#L909-L1043)

## Continuous Prototype

- `verification/continuous-water-prototype/` 是独立 verification 目录。页面明确不含 pointer、lifecycle、moving、orbit、audio 或 production reset；formation 是手动构型参数。[prototype index](../../verification/continuous-water-prototype/index.html#L9-L15)
- Prototype 使用单 WebGL pass、0 framebuffer、7 texture inputs（outer、formal mask、07–10、packed carrier RGB）；不使用 full-frame K2 overlay，连续参数通过 field / carrier / core position interpolation 表达。[REPORT](../../verification/continuous-water-prototype/REPORT.md#L13-L17) [REPORT](../../verification/continuous-water-prototype/REPORT.md#L63-L77)
- 当前实验结论是：STRUCTURAL CONTINUITY = PASS、FULL-FRAME LAYER TAKEOVER = ABSENT，但 MATERIAL IDENTITY = FAIL、K0 = PARTIAL、K2 = FAIL、CONTINUOUS MATERIAL SYSTEM = FAIL、RECOMMEND PRODUCTION MIGRATION = NO。[REPORT](../../verification/continuous-water-prototype/REPORT.md#L79-L93)
- 因此 K2 endpoint 尚未达到 migration gate；PARTIAL/FAIL 只能继续留在 prototype。

## Slice A Final Review

- `verification/slice-a-final-review/index.html` 是 verification-only wrapper，iframe 嵌入 `waterball.html?pure=1`，页面自身不写 formation、不控制 renderer。[review index](../../verification/slice-a-final-review/index.html#L60-L81)
- 该 review 同时展示 production real interaction 的 inspect readout 与已采集的静态 formation evidence；静态 frame scrub 不是实时调参入口。[review index](../../verification/slice-a-final-review/index.html#L86-L101) [review index](../../verification/slice-a-final-review/index.html#L105-L143)

## Known Legacy / Stale Facts

- **CODE CURRENT FACT vs STALE DOCUMENT STATEMENT：** activation semantics brief §2.2 仍写“绑定 click、没有 pointerDown/pointerUp/cancel”；当前代码已有四个 pointer handler、press/commit/cancel 和 lifecycle。[brief §2.2](../../docs/tasks/waterball-activation-motion-semantics.md#L26-L32) [waterball.js:67-75](../../components/waterball/waterball.js#L67-L75)
- **CODE CURRENT FACT vs STALE DOCUMENT STATEMENT：** 同一 brief §14 仍写“当前 Web runtime 尚未实现 pointer gesture”；其“transitioning/moving 尚未实现”仍是 current fact，因为 `setState` 与 `inspect` 仍未提供三态运行。[brief §14](../../docs/tasks/waterball-activation-motion-semantics.md#L266-L273) [waterball.js:493-496](../../components/waterball/waterball.js#L493-L496)
- **CODE CURRENT FACT vs STALE DOCUMENT STATEMENT：** source-layer audit 仍写 `buildClearComposite()` 不使用 07–10、K0 使用 generic radial gradient；当前代码已构建 `coreOpticalLayers` 并在正常 K0/K1 路径使用 frozen 07–10 pair。该 audit 对 02–06/11 的 pose contamination 与缺少独立 neutral source 的结论仍有效。[audit](../../docs/analysis/waterball-clear-still-source-layer-audit.md#L70-L81) [waterball.js:193-208](../../components/waterball/waterball.js#L193-L208)
- **Evidence drift：** `verification/slice-a-core-continuity-20260927/postfix-summary.md` 写“旧 procedural-to-baked optical crossfade 已移除”；当前 code 仍存在 formation 中段的完整 `staticCompositeCanvas` overlay，该 summary 不能作为当前 full-path no-duplicate 事实。
- **Manifest metadata conflict：** `assets/waterball-still-v1/manifest.json` 的 `source_lock` 写“formal test composite、prior v2-v6 不使用”，而 `test/water-orb-still/2p5d-composite-v1/composite_manifest.json` 写“current v6 static composite”。两份 manifest 的画布、layer order、moving_status 和视觉待确认字段一致，但 source provenance 不一致；本轮不改 manifest。[assets manifest](../../assets/waterball-still-v1/manifest.json#L40-L46) [composite manifest](../../test/water-orb-still/2p5d-composite-v1/composite_manifest.json#L40-L44)
- `AGENTS.md`、product visual spec、architecture baseline 主要是 normative authority；它们不应被当作当前实现快照。当前事实以本文件与代码/证据行号为准。
