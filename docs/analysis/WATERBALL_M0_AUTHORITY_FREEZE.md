# WaterBall M0 Authority Freeze

审计日期：2026-09-27
适用范围：M-1 Repository Truth Sync 与 M0 Experimental Authority Freeze。
状态：**M0 PASS**。本文件只建立权限边界，不实现 Neutral Material，不改变 production WaterBall。

## Authority Matrix

| 领域 | FROZEN PRODUCT AUTHORITY | CURRENT IMPLEMENTATION SNAPSHOT | EXPERIMENTAL AUTHORITY |
|---|---|---|---|
| ProductState / interaction semantics | `ProductState = still / transitioning / moving`；当前语义路径是 `clear → press → activated → transitioning → moving`；`pointerUp inside + activation commit` 一次提交；suspend/resume/reset 语义冻结。[AGENTS.md:30-51](../../AGENTS.md#L30-L51) [activation semantics:98-118](../tasks/waterball-activation-motion-semantics.md#L98-L118) | 正常 production construction 默认 `still`；可通过 `setState` 达到的状态只有 `still`；pointer gesture 与 activated 子态已实现；transitioning/moving 与 orbit 仍未实现。[waterball.js:18-24](../../components/waterball/waterball.js#L18-L24) [waterball.js:493-496](../../components/waterball/waterball.js#L493-L496) [waterball.js:530-561](../../components/waterball/waterball.js#L530-L561) | 实验不得改变 ProductState、输入语义、生命周期或新增第二套时钟。 |
| Formal silhouette | formal still atlas 的 `01_outer_film` alpha-derived silhouette；阈值 6；silhouette、center/radius、hitRadius 三者职责分离。[profile.js:27-33](../../components/waterball/profile.js#L27-L33) [still brief:86-92](../tasks/waterball-still-motion-brief.md#L86-L92) | Canvas body/core 已使用 derived mask；现有 WebGL fragment 仍保留圆形 discard，因此只是 snapshot，不能宣称 formal silhouette-only pass。[waterball.js:465-491](../../components/waterball/waterball.js#L465-L491) [waterball.js:224-230](../../components/waterball/waterball.js#L224-L230) | 新材质只能采样/生成受 formal silhouette 约束的 body domain，不得改写 formal still manifest。 |
| Center / radius / hitRadius | `frame=853×1844`、`center=[426.5,925]`、`radius=316`、`hitRadius=300`；hitRadius 只负责命中。[profile.js:3-8](../../components/waterball/profile.js#L3-L8) | 当前 layout 与 inspect 使用这组几何；hit region 仍为圆。[waterball.js:454-463](../../components/waterball/waterball.js#L454-L463) | 实验不得改变中心、半径、命中区或用 hitRadius 代替视觉裁切。 |
| Frozen K2 visual endpoint | 正式 `static_composite.png` / v1 atlas；K2 endpoint 必须是 **PASS** 才能进入 production migration。[assets manifest](../../assets/waterball-still-v1/manifest.json#L1-L46) | 当前 static composite 可作为 K2 endpoint snapshot；中段 overlay 与 full-path double-core 状态仍需单独处理。[waterball.js:883-901](../../components/waterball/waterball.js#L883-L901) | Continuous prototype 的 K2 = FAIL/PARTIAL 只能留在 verification；不能迁移 production。[REPORT](../../verification/continuous-water-prototype/REPORT.md#L79-L93) |
| 07–10 cold/warm optical identity | `07/08` cold pair、`09/10` warm pair 是 frozen K2 optical identity；identity、颜色关系、pair order 冻结。[assets manifest](../../assets/waterball-still-v1/manifest.json#L21-L25) | 当前代码按 pair source-over 平移并报告 `frozen-k2-07-10`。[waterball.js:193-208](../../components/waterball/waterball.js#L193-L208) [waterball.js:1237-1239](../../components/waterball/waterball.js#L1237-L1239) | 新材质可复用 optical pair，但不能用新 shader 重画或替换 07–10 identity。 |
| 11 curvature highlights | 11 可提供曲率/厚度 vocabulary；它不是完全 pose-neutral 的 frozen outer membrane。[source-layer audit](../../docs/analysis/waterball-clear-still-source-layer-audit.md#L27-L40) | 当前旧 renderer 将 11 当动态 layer 使用，另有 runtime shell copy；这只是 comparison/fallback snapshot。[profile.js:62-73](../../components/waterball/profile.js#L62-L73) [waterball.js:121-141](../../components/waterball/waterball.js#L121-L141) | 新路线只能把 11 当作经中和的 broad optical/thickness source，不能把 11 归入完全 frozen outer membrane。 |
| Single-loop / lifecycle | 一个状态驱动的视觉时钟；suspend 冻结、resume 只继续一次、reset 清零；不得有第二套 animation loop。[AGENTS.md:74-100](../../AGENTS.md#L74-L100) [still brief:62-70](../tasks/waterball-still-motion-brief.md#L62-L70) | 当前由 `effectiveVisualTime`、`animationLoopRunning` 和单 RAF 实现；仅作为 runtime snapshot。[waterball.js:577-649](../../components/waterball/waterball.js#L577-L649) | Prototype 可有自己的验证 loop，但不得变成 production second loop。 |
| Current K0/K1 composite | 无产品 authority；只记录当前实现路径与回归比较基线。 | `clearCompositeCanvas` + generated neutral volume + pose-without-cores + dynamic body + runtime 07–10 + WebGL pass，并在 formation 中段叠加完整 static K2 composite。[waterball.js:687-901](../../components/waterball/waterball.js#L687-L901) | M1 不得把该 composite、response curves 或旧 renderer 当新材质 authority。 |
| Current response curves | 无产品 authority；仅为当前 working tree 的实现参数。 | density/cavity/core/pose/late-settle curves 与 1400ms formation duration 当前存在于 code。[waterball.js:691-724](../../components/waterball/waterball.js#L691-L724) | M1 可以在实验目录比较参数，但不得回写 frozen still 或宣称产品已裁决。 |
| Existing WebGL material pass | 不是新连续 renderer 的 authority。 | `prepareMaterialTexture()` 直接把 `staticComposite` 上传为 `textureObject`；fragment shader 直接采样 `u_texture`，并额外绑定 neutral/carrier。[waterball.js:253-255](../../components/waterball/waterball.js#L253-L255) [waterball.js:308-313](../../components/waterball/waterball.js#L308-L313) | 可复用 WebGL context、lifecycle、masking concepts；不可直接复用 baked/static K2 texture semantics 或 K2-pose-contaminated shader logic。**EXISTING WEBGL MATERIAL PASS = NOT CANONICAL FOR NEW CONTINUOUS RENDERER**。 |
| Continuous material route | 不属于 frozen still v1 产品 authority。 | 当前 prototype 为 1 pass/0 framebuffer/7 textures，已证明 continuous parameter interpolation 与无 full-frame takeover，但 material identity FAIL、K2 FAIL。[REPORT](../../verification/continuous-water-prototype/REPORT.md#L13-L17) [REPORT](../../verification/continuous-water-prototype/REPORT.md#L63-L93) | neutral material sources、thickness field、sparse detail carrier、新 shader、deformation field `D`、density/thickness field `R`、continuous-water prototype 全部属于 experimental authority。 |

## M0 Hard Boundaries

### 实验资产位置

- 实验资产、shader、carrier、D/R、neutral source 和 prototype 只能放在 `verification/` 或明确的 `experimental/` 范围。
- 不得写入 `assets/waterball-still-v1/` 的 frozen still v1 manifest、正式 layer order、正式 PNG 或 production asset contract。
- 不得静默替换 production asset contract；任何 migration 都必须有独立的 Rendering Contract v2 记录和 K2 endpoint PASS 证据。
- 当前 working tree 中的 verification 目录与根目录 `verification-*.png` 都只作为现有验证产物读取；本轮不移动、不删除、不转正。

### Full-frame crossfade 边界

新路线禁止：

```
FULL-FRAME STATE IMAGE CROSSFADE
```

允许：

```
CONTINUOUS FIELD / PARAMETER INTERPOLATION
```

允许的连续变化包括同一 body domain 内的 D/R、厚度、密度、carrier、core position 和 optical parameter interpolation；禁止用 K0/K1/K2 三张整帧状态图互相淡入淡出来冒充连续材质。

### K2 migration gate

- `K2 ENDPOINT = PASS` 才能申请 production migration。
- `K2 ENDPOINT = PARTIAL` 或 `FAIL` 只能继续 prototype；当前 continuous-water prototype 属于此类。
- M1 只建立 neutral material 的实验边界，不自动获得 production migration authority。

## Architecture / Manifest Conflict

当前存在两项需要保留的冲突记录：

1. production code 已有 generated neutral/carrier、WebGL material 与 pointer gesture，但 `assets/waterball-still-v1/manifest.json` 仍只描述 static still asset，`moving_status = not implemented`、`visual_acceptance = pending_user_confirmation`；这表示 implementation snapshot 尚未成为 asset contract。
2. 两份 formal manifest 的 layer order、画布与 moving/acceptance 字段一致，但 `source_lock` provenance 不一致：assets copy 写“formal test composite / prior v2-v6 不使用”，test composite manifest 写“current v6 static composite”。[assets manifest](../../assets/waterball-still-v1/manifest.json#L40-L46) [composite manifest](../../test/water-orb-still/2p5d-composite-v1/composite_manifest.json#L40-L44)

本轮不改 manifest，也不以任何一份 source_lock 字符串默默提升实验来源。未来若要把连续 renderer 纳入 production，必须新增独立 **Rendering Contract v2 migration**，明确 source provenance、body-domain silhouette contract、K2 endpoint proof、fallback/rollback 与 asset ownership。

## Gate Result

```text
M-1 REPOSITORY TRUTH SYNC = PASS
M0 EXPERIMENTAL AUTHORITY FREEZE = PASS
READY_FOR_M1_NEUTRAL_MATERIAL = YES
PRODUCTION_MIGRATION = NO
```

“READY_FOR_M1_NEUTRAL_MATERIAL = YES”只表示实验边界已建立；不表示 Neutral Material 已实现，也不表示当前 prototype 或 production K0/K1/K2 已通过视觉迁移。
