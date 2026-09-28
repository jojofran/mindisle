# M1.2 — Final Art Donor Material Baking

## Final state

- **OLD SOURCE-DERIVED ROUTE = CLOSED**
- **FROM-SCRATCH AUTHORED ROUTE = CLOSED**
- **FINAL ART DONOR ROUTE = READY FOR HUMAN REVIEW**
- **MATERIAL FAMILY = READY FOR HUMAN REVIEW**
- **NEUTRAL POSE = PRESERVED**
- **DONOR CYCLES USED = 2 / 2**
- **THREE.JS = NOT JUSTIFIED**
- **READY_FOR_M2 = NO**

“READY FOR HUMAN REVIEW” 是本轮实验出口，不是 Human Gate A/B 通过，也不打开 M2。

## 1. Authority / provenance

`FINAL_ART_025` 现在被允许作为：

- `visualReference = true`
- `offlineDerivationDonor = true`
- `runtimeDirectSample = false`
- `canonicalFinalFrameTexture = false`
- `productionDependency = false`

`FINAL_ART_050` 只作为 depth / thickness / cloudy organization guide；`FINAL_ART_075` 只作为 upper-bound reference；`FROZEN_K2` 仍是 endpoint authority。Frozen K2 authority 未修改。完整 provenance 见 [`references/provenance.json`](references/provenance.json)。

新生成的三份 source 都记录 `derivedFrom` 与 baking method，并保持 verification-only；runtime 未来只能使用烘焙后的 neutral assets，不能直接使用 Final Art。

## 2. Route Check — Cycle 1

- **CURRENT PRIMARY DEFECT =** authored-source Hero 是均匀雾球；Final Art 的局部 cloudy mass、厚度关系和 sparse water vocabulary 没有进入可见材料。
- **ROOT CAUSE TYPE =** material representation / source organization。
- **DONOR ROUTE CAN SOLVE = YES**。
- **WHY =** `FINAL_ART_025` 已经包含品牌认可的 white-cyan cloudy mass、局部厚薄和稀疏水纹，可通过局部 patch 提取并重新编排；不需要继续全局 neutralization。
- **PROPOSED BAKING CHANGE =** 对 025 做局部 patch / warp / recomposition，先遮掉 UI chrome 与 cold/warm core，再输出 volume、thickness、detail 三份中间源。
- **EXPECTED VISIBLE EFFECT =** Hero 出现 donor-derived 的 authored cloudy structure，并与 025 保持材质家族连续。
- **FAILURE SIGNAL =** 拼接带、截图文字残留、core halo 或 patch 几何边界可见。

### Cycle 1 Fresh Critic

先只看 `FINAL_ART_025`、`FINAL_ART_050`、`FROZEN_K2`、D K0 和第一版 neutral Hero：

1. 是否明显是同一种水：**部分**；
2. 是否仍是雾球 / 磨砂球：**是**；
3. cloudy mass 是否像 authored structure：**否，patch 边界先于材质被看到**；
4. front/internal/rear depth 是否成立：**否**；
5. sparse detail 是否属于水体：**否**；
6. Neutral Pose 是否成立：**是**。

**IMPROVEMENT = REGRESSION**。失败信号明确，不能沿用同一版继续微调。

## 3. Route Check — Cycle 2

- **CURRENT PRIMARY DEFECT =** Cycle 1 的 donor patch 带有可见拼接边界，且原图文字/core 位置记忆残留。
- **ROOT CAUSE TYPE =** local reconstruction / compositing seam。
- **DONOR ROUTE CAN SOLVE = YES**。
- **WHY =** 缺陷集中在局部 patch 的 mask、inpaint 和 upper-region handoff；025 的材料 vocabulary 本身仍然可用。
- **PROPOSED BAKING CHANGE =** 改用 core-clean 局部带重建、宽幅 feather、translated patch warp 和 annular material fill；重新计算 analytic body thickness，并把 025 band-pass 细节稀疏筛选后以低对比接入。
- **EXPECTED VISIBLE EFFECT =** 无 UI chrome、无可读 cold/warm core、无明显 patch seam；Hero 具有非均匀 cloudy mass，厚度源明确表达 shallow / medium / deep。
- **FAILURE SIGNAL =** 仍出现 core residue、明显方向性 cavity/swirl、重复条带、或 source 仍退回均匀 fog disc。

### Cycle 2 Fresh Critic

只看四份 Final Art / D K0 reference 和当前 donor Hero：

1. 是否明显是同一种水：**更清楚，是同一材质家族的 neutral 版本**；
2. 是否仍是雾球 / 磨砂球：**没有明显 blocker**；
3. cloudy mass 是否像 authored structure：**是，局部聚散和水体重量可读**；
4. front/internal/rear depth 是否成立：**在静态 source 层成立，thickness map 明确有 shallow / medium / deep 编码**；
5. sparse detail 是否属于水体：**有，刻意保持低对比、局部存在/缺失**；
6. Neutral Pose 是否仍然成立：**是，无 cavity、swirl、强左→右方向或 K1/K2 结构**。

**IMPROVEMENT = CLEAR**。本轮不再开第三个 donor cycle。

## 4. Asset A — Neutral Water Volume

输出：[`neutral-water-volume.png`](neutral-water-volume.png)。

以 `FINAL_ART_025` 为主要 donor，先去除 UI chrome 和 cold/warm core，再从不同内部区域选取局部 patch，做小幅旋转、翻转和宽幅羽化重组；`FINAL_ART_050` 只提供轻量 low-frequency mass variation。保留了：

- white-cyan cloudy mass；
- 局部实 / 透关系；
- 大尺度非均匀与水体重量；
- donor 的 authored optical complexity。

删除了：

- cold / warm core 及 halo memory；
- 明确 cavity、swirl 和单向 K1/K2 组织；
- screenshot text 和 full-frame state composition。

A 单独看不是 radial gradient、fog disc 或几个 soft blob；它是局部 donor material 的 neutral spatial recomposition。

## 5. Asset B — Thickness / Depth

输出：[`neutral-thickness.png`](neutral-thickness.png)。

使用 analytic sphere/body thickness 作为深度骨架，再加入来自 025/050 的可信低频 local mass variation。RGB 明确编码 shallow / medium / deep，不从 Final Art brightness 直接反推 depth，也没有把图压成单一灰色模糊圆。当前 Hero 的 compositor 使用该深度源控制 front veil、internal mass 与 rear transmission 的相对密度。

## 6. Asset C — Sparse Water Detail

输出：[`neutral-water-detail.png`](neutral-water-detail.png)。

从清理后的 025 提取 band-pass structure，再按局部区域筛选少量 irregular soft ridges、fine cloudy breakup 和断裂水纹；保留不同尺度、低对比、局部存在/缺失，禁止 stain、fingerprint、contour、marble、repeated bands 与 generic FBM。Detail 在 Hero 中只作为低权重 vocabulary，不接管整幅画面。

## 7. Core residue check

Core removal 使用精确位置 mask、translated local patch warp 和周边 annular material fill；不是 blur-to-neutral。当前 review readout 与像素检查记录 `coreResidue = NONE`，Hero 中没有可读 cold/warm dot 或 halo crater。

## 8. Static compositor / review evidence

Review 页面：[`index.html`](index.html)。页面展示：

- `FINAL_ART_025`、`FINAL_ART_050`、`FROZEN_K2`、D K0；
- Neutral Volume、Thickness / Depth、Sparse Detail；
- Current Hero；
- Old Authored Failed Hero vs New Donor Hero。

旧 Hero 只是历史负面证据；新 Hero 只由 formal outer membrane、三份新 baked source 和 minimal neutral optical compositor 组成。没有 runtime direct sampling、full-frame state crossfade、canonical final-frame texture 或 production dependency。

## 9. Old Hero vs New Hero

旧 Hero 是 M1.1 authored-source blocker：均匀青白填充、内部厚度不可读、detail 不成立。新 Hero 的性质改善是：

- cloudy mass 变成 donor-derived 的多尺度局部组织；
- front / internal / rear 的静态厚度关系可由 B source 解释；
- sparse detail 不再是 UI 线段或重复软 blob；
- core、cavity、swirl 和方向性结构不再成为主视觉。

它仍需 Human Gate A/B，不能据此宣布 M2 ready。

## 10. Final report

- donor route 是否可行：**可行，达到 READY FOR HUMAN REVIEW**；
- FINAL_ART_025 保留：white-cyan cloudy mass、局部实/透关系、大尺度非均匀、水体重量、稀疏 water vocabulary、authorial optical complexity；
- 删除：core、halo、cavity、swirl、directional K1/K2 organization、state-specific composition、UI chrome；
- Neutral Volume：局部 donor patch / warp / recomposition + core/text reconstruction；
- Thickness：analytic body thickness + 025/050 low-frequency local mass，RGB shallow/medium/deep；
- Sparse Detail：025 band-pass extraction + sparse region selection + low contrast；
- core residue：**NONE**；
- Route Check：2 次，均记录于本报告；
- Fresh Critic：Cycle 1 = REGRESSION，Cycle 2 = CLEAR；
- improvement：**CLEAR**；
- old Hero vs new Hero：new donor Hero 的 cloudy mass、静态厚度解释和材质家族连续性改善；
- Final Art comparison：025/050 的材质 vocabulary 被保留，075 仅作上限，FROZEN_K2 仍只作 endpoint；
- Neutral Pose：**PRESERVED**；
- provenance：[`references/provenance.json`](references/provenance.json) 与 [`m1-current-evidence.json`](m1-current-evidence.json)；
- commit hash：由本轮最终 git commit 记录；见任务最终报告。

## Final boundary

```text
OLD SOURCE-DERIVED ROUTE = CLOSED
FROM-SCRATCH AUTHORED ROUTE = CLOSED
FINAL_ART_DONOR_ROUTE = READY FOR HUMAN REVIEW
NEUTRAL POSE = PRESERVED
MATERIAL FAMILY = READY FOR HUMAN REVIEW
DONOR CYCLES USED = 2 / 2
THREE.JS = NOT JUSTIFIED
READY_FOR_M2 = NO
```
