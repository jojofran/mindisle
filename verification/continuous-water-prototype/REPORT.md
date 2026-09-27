# M1.1 — Authored Neutral Material Source

## Final state

- **OLD SOURCE-DERIVED ROUTE = CLOSED**
- **AUTHORED MATERIAL ROUTE = BLOCKED**
- **NEUTRAL POSE = PRESERVED**
- **MATERIAL FAMILY = M1 MATERIAL SOURCE BLOCKER**
- **CYCLES USED = 3 / 3**
- **THREE.JS = NOT JUSTIFIED**
- **READY_FOR_M2 = NO**

## 1. 为什么旧 source-derived route 失败

旧路线依赖带有 K2 关系的 source layers，再通过 alpha、flip、RGB、depth map 和 multiply/screen 中和。四轮旧 M1 repair 已证明：这些 source layers 无法在保持 Neutral Pose 的同时提供足够可信的内部厚度与 authored sparse structure。继续调旧 Carrier 权重已关闭。

## 2. 新 authored material route

本轮建立了三份独立 verification source：

- **`neutral-water-volume.png`**：确定性绘制的大尺度 cloudy mass，负责自然聚散、局部透/实和水体重量；
- **`neutral-thickness.png`**：显式 shallow / medium / deep 的 RGB depth encoding，负责后续 transmission / density modulation；
- **`neutral-water-detail.png`**：少量不规则、断裂、不同长度的 authored-like 内部细纹，负责未来可追踪结构。

这些 source 不采样 Final Art/K2，不使用 FBM、simplex、random blobs 或 full-frame crossfade。

## 3. Cycle 1

**Route Check**：`SOURCE / REPRESENTATION`；当前 authored route 可行。先把 authored source 直接作为静态 Hero 的显式材料层。

**修改**：绘制独立 volume、thickness、detail，并将它们直接叠入 Hero。

**Fresh Critic**：结果是平面贴图；thickness 读成硬边；detail 像 UI 线段。

**IMPROVEMENT = REGRESSION**。

## 4. Cycle 2

**Route Check**：`COMPOSITING`；source 本身可保留，但必须从 visible paint layer 改为 density/depth/transmission control。

**修改**：volume 控制内部密度，thickness 控制前后透射，detail 只做低强度局部调制，恢复 verified membrane baseline。

**Fresh Critic**：硬边消失，但 Hero 重新退回均匀青白雾球；内部质量和 sparse structure 仍不可读。

**IMPROVEMENT = MARGINAL**。

## 5. Cycle 3 · Extension +1

**为什么 Cycle 2 不足**：authored source 数据存在，但进入 Hero 的可见度太低。

**本轮改变**：提高 deep density、front veil 和 rear transmission 的可见度，验证 source 是否能形成明确厚度。

**Fresh Critic**：仍是单一 translucent fill；front/internal/rear separation 不成立；sparse detail 不可读。

**IMPROVEMENT = NONE**。

## 6. Route Review

已完成：

- 新建 authored neutral volume；
- 新建显式 thickness/depth source；
- 新建 authored sparse detail；
- 直接贴图 compositing；
- density/depth/transmission compositing；
- 提高 depth 可见度的 extension。

当前合理下一步已经不再是继续调这些离线 raster 参数。现有工具/资产条件下，authored source 仍不能稳定表达 Final Art 所需的内部水体组织，因此本轮停止为 **M1 MATERIAL SOURCE BLOCKER**。

## 7. Three.js

`MeshPhysicalMaterial` 的 transmission/thickness 能力不能补充当前缺失的 authored material information。当前 blocker 仍在 source / representation 层，不满足 Three.js spike gate。

**THREE.JS = NOT JUSTIFIED**。

## 8. Evidence

- Review：[index.html](index.html)
- Hero：[m1-neutral-hero.png](m1-neutral-hero.png)
- Neutral Volume：[neutral-water-volume.png](neutral-water-volume.png)
- Neutral Thickness：[neutral-thickness.png](neutral-thickness.png)
- Neutral Detail：[neutral-water-detail.png](neutral-water-detail.png)
- Evidence：[m1-current-evidence.json](m1-current-evidence.json)

只修改了 `verification/continuous-water-prototype/`，未修改 production、M2、roadmap 或 Neutral Pose。
