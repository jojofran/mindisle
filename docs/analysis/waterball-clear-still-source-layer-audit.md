# Waterball Clear-Still Source Layer Audit

**Document type:** Technical Evidence / Implementation Audit  
**Status:** CLOSED  
**Verdict:** `NOT FEASIBLE WITH CURRENT FORMAL LAYERS`

## Purpose

本审计用于验证：当前 frozen still 的正式 layers 与现有 runtime representation，是否具有足够自由度表达：

```text
K0 clear-still → K1 press-forming → K2 frozen still-pose
```

本文件只记录实现可行性、源层能力和诊断证据，不重新定义产品视觉目标，不覆盖产品语义或交互语义。

审计对象：

- [正式 still manifest](../../test/water-orb-still/2p5d-composite-v1/composite_manifest.json)
- [正式 still layers](../../test/water-orb-still/2p5d-composite-v1/layers/)
- [profile.js](../../components/waterball/profile.js)
- [waterball.js](../../components/waterball/waterball.js)
- 当前 K0/K1/K2 runtime 表示

## Layer Audit

| Layer | Visual Role | Stable Material Identity? | Pose-dependent? | Contains Baked Core? | Contains Baked Cavity/Swirl? | Reusable for K0? | Evidence / Notes |
|---|---|---:|---:|---:|---:|---:|---|
| `00_background_plate` | 背景底板 | 否 | 否 | 否 | 否 | 否 | 非水球材质，仅用于合成可读性。 |
| `01_outer_film` | 银白透明外膜、主体轮廓、厚度语言 | 是 | 否/很少 | 否 | 否 | 是，但只能作为壳 | A/B 诊断中可独立形成稳定膜面；同时被 profile 作为 silhouette authority。 |
| `02_internal_cyan_volume` | 青绿色主体体积 | 部分是 | 是 | 否 | 部分 | 部分 | 已携带方向性密度；C 诊断中已出现偏 K2 的内部质量分布。 |
| `03_boundary_mask` | 内部弯曲明暗边界 | 否 | 是 | 否 | 是 | 否，除非排除 | D 诊断中直接形成明显内部边界/回旋提示。 |
| `04_flow_layer` | 内部流动带 | 部分是 | 是 | 否 | 否，但带方向性 | 部分 | 可作为极弱细节，不能作为中性 K0 主体。 |
| `05_flow_layer` | 第二层内部流动带 | 部分是 | 是 | 否 | 否，但带方向性 | 部分 | 与上一层相同，表达的是方向性流动结构。 |
| `06_fine_ink_wash` | 水墨/细部密度纹理 | 部分是 | 是 | 否 | 部分 | 部分 | 具有水体材质价值，但也包含姿态相关的密度结构。 |
| `07_cool_point_core` | 冷点亮核 | 是 | 位置已烘焙 | 是 | 否 | 部分 | 可以提供 bright core，不能提供周围水体响应。 |
| `08_cool_point_glow` | 冷点 halo | 是 | 位置已烘焙 | 否，仅 halo | 否 | 部分 | 有独立 halo，但没有 local density/refraction field。 |
| `09_warm_point_core` | 暖点亮核 | 是 | 位置已烘焙 | 是 | 否 | 部分 | 可以提供 bright core，不能提供周围水体响应。 |
| `10_warm_point_glow` | 暖点 halo | 是 | 位置已烘焙 | 否，仅 halo | 否 | 部分 | 有独立 halo，但没有 local density/refraction field。 |
| `11_curvature_highlights` | 膜面曲率高光 | 是 | 局部位置/强度带有 K2 关系 | 否 | 否 | 部分 | 可复用膜面材质语言，但不是中性的可重定位高光场。 |

## Stable Material Identity vs Pose-dependent Structure

### Stable Material Identity

当前可复用的稳定材质身份主要来自：

- `01_outer_film` 的银白透明膜面；
- curvature / membrane highlight 的高光语言；
- edge refraction 与水体厚度感；
- 细微表面 detail；
- 整体透明、有厚度的水球材质身份。

这些能力足以支持 K0 保留“同一颗水球”的外壳身份，但不足以单独构成 K0 的内部水体。

### Pose-dependent Structure

当前正式资产中属于姿态相关或带有姿态倾向的结构包括：

- `02_internal_cyan_volume` 已有的方向性密度；
- `03_boundary_mask`；
- `04_flow_layer` 与 `05_flow_layer`；
- `06_fine_ink_wash` 的部分内部结构；
- frozen core positions；
- frozen cavity / swirl；
- 与当前构型绑定的 local optical response。

当前正式资产没有独立的 **neutral internal volume**。因此不能仅靠切换既有层的 alpha、顺序或强度，稳定得到“无明显 cavity、但仍有体积”的 K0。

## Core Audit

正式 core/glow 可以拆出：

- bright core：可以；
- halo：可以；
- local density response：不可以；
- local refraction response：不可以。

原因：`07/09` 是独立亮核，`08/10` 是独立 halo，但没有与周围水体联动的密度层或折射层。当前 `buildClearComposite()` 只合成背景、外膜、内部体积、边界、流层、ink 和 curvature highlight，没有使用正式 `07–10` core/glow 图层（见 [waterball.js:210-226](../../components/waterball/waterball.js#L210-L226)）。

当前 K0 runtime 在 [waterball.js:634-679](../../components/waterball/waterball.js#L634-L679) 使用通用 radial gradient 绘制中部 core 与 halo。因此当前表现容易退化为平面的 blue/orange dot，而不是嵌入水体的 optical core。

## Diagnostic Evidence

以下图像是本审计生成的诊断证据，不是产品素材，也不改变正式资产：

- [A–G side-by-side](../../verification/source-layer-audit/A-G-side-by-side.png)
- [Core audit](../../verification/source-layer-audit/core-audit.png)

A–G 的含义：

- **A**：outer film only；验证外膜可独立成立，但中心为空；
- **B**：outer film + curvature highlight；验证膜面高光身份；
- **C**：B + cyan volume；已出现方向性内部质量分布；
- **D**：C + boundary/flow/ink，排除 core；内部回旋/流动结构明显增强；
- **E**：frozen K2 composite；正式 frozen still 对照；
- **F**：当前 K0 runtime 的源层合成重建；显示通用径向点位为何读成平面色点；
- **G**：稳定材质层 + 诊断用 synthetic neutral volume，仅用于证明缺失的中性内部体积能力，不是正式资产。

## Feasibility Verdict

### K0 REPRESENTATION FEASIBILITY

**NOT FEASIBLE WITH CURRENT FORMAL LAYERS**

依据：

1. 缺少独立的 neutral internal volume；
2. `02_internal_cyan_volume` 已携带 K2 directional density；
3. `03–06` 包含不同程度的 K2 pose-dependent structure；
4. core/glow 缺少 local density / refraction field；
5. 当前 runtime 只能减弱或重组既有层生成“较浅版本”，无法稳定表达真正独立但同源的 K0 pose。

## Allowed Next Step

后续允许的最小技术升级为：

### MINIMAL RUNTIME-DERIVED REPRESENTATION UPGRADE

允许增加运行时可控的表示能力：

- neutral internal volume；
- runtime core optical field；
- derived density mask；
- derived cavity control mask；
- local refraction field；
- 从正式 still layers 派生中间 mask / field。

以上属于 runtime representation upgrade，不是新的产品素材。

本审计不授权：

- 新建完整 clear-still 成品 PNG；
- 修改 frozen still 正式 PNG；
- 修改 manifest 的产品语义；
- 替换 K2 frozen authority；
- 新建第二个 WaterBall renderer；
- 新建第二套 animation loop。

## Authority Boundary

本文件只负责技术可行性与实现约束证据。

产品视觉与交互语义仍由以下文档负责：

- [state-ball-visual-spec.md](../product/state-ball-visual-spec.md)
- [waterball-activation-motion-semantics.md](../tasks/waterball-activation-motion-semantics.md)

frozen still 事实仍由以下内容负责：

- [waterball-still-motion-brief.md](../tasks/waterball-still-motion-brief.md)
- [正式 still manifest](../../test/water-orb-still/2p5d-composite-v1/composite_manifest.json)
- [正式 still assets](../../test/water-orb-still/2p5d-composite-v1/layers/)

本审计不得覆盖上述上级权威，也不得把技术缺口解释为新的产品语义。

## Current Slice Status

```text
Slice A Interaction = PASS
Slice A Lifecycle = PASS
Slice A Runtime Foundation = PASS

Slice A Visual Representation = FAIL
K0 Visual = FAIL
K1 Visual = NOT ACCEPTED
K2 Frozen Still = PASS

READY_FOR_SLICE_B = NO
```

原因：当前 source representation 不足，必须先完成最小 runtime representation upgrade。

## Closure

本审计已关闭。它只固化已有诊断事实，不修改运行时代码、产品语义、正式资产、manifest、产品 spec、activation semantics 或 architecture baseline。
