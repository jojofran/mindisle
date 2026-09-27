# M1 — Neutral Water Material · Representation Repair + Self-Critic Loop

## 最终判断

本轮严格执行了 4 个 representation-level cycles，达到绝对上限。Fresh Critic 仍能指出明显的 material-family defect，因此不能交给人工 Review，也不能写成 READY。

- **MATERIAL SYSTEM STRUCTURE = PASS**
- **NEUTRAL POSE = PRESERVED**
- **MATERIAL FAMILY = MATERIAL REPRESENTATION BLOCKER**
- **REPAIR CYCLES USED = 4 / 4**
- **THREE.JS = NOT JUSTIFIED**
- **READY_FOR_M2 = NO**

## 初始 root cause

旧 Neutral 主要由软 blob、低对比渐变和透明叠加组成。它没有把 material information 表达为可读的 outer membrane、front water layer、cloudy internal mass、deeper thickness structure 和 rear transmission，因此看起来像青色磨砂雾球，而不是 Final Art 家族中的一团水。

## Cycle 1

**Route Check**：`C. REPRESENTATION`；当前路径可以尝试，但不能继续用旧 Hero 叠加补丁。改动前的假设是：用 `01_outer_film` 作为独立膜面底座，再叠加中和后的 A/B/C。

**修改**：从 formal outer-film alpha 重建底座，并叠加 source-derived cloudy、sparse、curvature layers。

**Fresh Critic**：

1. 外膜几乎消失；
2. 内部变成均匀网状纹理；
3. front/internal/rear depth 没有成立。

**IMPROVEMENT = REGRESSION**。Route Review 结论：outer-film alpha 只能作为膜面补层，不能独立承担 Hero。

## Cycle 2

**Route Check**：`B. CHANGE REPRESENTATION`；改为 verified neutral membrane baseline + 显式 front/internal/rear compositing，并把 Carrier B 限制为稀疏局部结构。

**修改**：恢复中性膜面基线，加入 localized internal mass、rear transmission、soft rim 和 sparse source fragments。

**Fresh Critic**：

1. 膜面恢复；
2. 内部深层质量仍然太淡；
3. sparse detail 仍不可读。

**IMPROVEMENT = MARGINAL**。触发 Extension Self-Review。

## Cycle 3 · Extension +1

**为什么上一轮不足**：Cycle 2 仍主要使用 source alpha，丢失了 source RGB/albedo 的空间组织。

**错误假设**：认为 alpha field 足以表达厚度与内部质量。

**本轮根本不同**：把中和后的 source RGB/albedo 作为 material value 和 chroma field，而不是只作透明度。

**Fresh Critic**：内部深浅变化仍弱，front/internal/rear separation 仍不成立，sparse detail 仍像模糊斑点。

**IMPROVEMENT = MARGINAL**。继续同类 RGB 权重调节被判定为重复失败 strategy。

## Cycle 4 · Final Extension +1

**为什么上一轮不足**：source RGB 虽然提供了色彩组织，但 compositor 仍把它当单一透明色层。

**错误假设**：认为提高 source value 对比就会自然产生空间厚度。

**本轮根本不同**：建立独立 front/deep/rear depth maps，使用 multiply darkening 表达深层密度，再以 pale transmission 表达前后层。

**Fresh Critic**：

1. 内部深层质量仍太淡，读不成 `FINAL_ART_050` 的 thickness；
2. front/rear separation 仍主要依赖边缘；
3. sparse detail 仍不足以形成同一种水的识别度。

**IMPROVEMENT = MARGINAL**。达到绝对 4 轮上限，停止继续调参。

## Route Review

已尝试：

- full source-derived alpha compositor；
- fixed membrane + explicit front/internal/rear compositing；
- source RGB/albedo encoding；
- independent depth-map compositing。

这些路线都保持了 Neutral Pose，但没有提供足够的内部厚度与 authored sparse structure。当前 M1 source layers 的 pose-neutral information 不足以继续高价值修复，因此结论为：

**MATERIAL REPRESENTATION BLOCKER**。

## 最终 representation / carrier

Carrier 职责仍为：A = neutral volume，B = sparse water detail，C = thickness / optical。四轮中分别测试了 alpha-derived、RGB-derived、depth-map 和 fixed-membrane compositing；没有采样 Final Art/K2 作为 shader texture，没有 full-frame crossfade，没有 core、formation、cavity 或 directional flow。

## Three.js Gate

Three.js `MeshPhysicalMaterial` 支持 `transmission`、`transmissionMap`、`thickness` 和 `thicknessMap`，但当前 blocker 是 pose-neutral source information 不足，不是 renderer capability 不足。没有证据表明 Three.js 能补充缺失的内部 material information；做 spike 只会引入玻璃球和环境反射风险。

**THREE.JS = NOT JUSTIFIED**。

## Evidence

- Hero：[m1-neutral-hero.png](m1-neutral-hero.png)
- Review：[index.html](index.html)
- Evidence：[m1-current-evidence.json](m1-current-evidence.json)
- 本轮只修改 `verification/continuous-water-prototype/`，未修改 production，未进入 M2，未 push。
