# M1.2 — Donor Material Correctness Repair

## Final state

- **DONOR MATERIAL ROUTE = PASS**
- **FORMAL SHELL FIDELITY = PASS**
- **CORE RECONSTRUCTION COLOR = PASS**
- **CORE RESIDUE = NONE**
- **SPARSE DETAIL REVIEWABILITY = PASS**
- **NEUTRAL POSE = PRESERVED**
- **MATERIAL FAMILY = READY FOR HUMAN REVIEW**
- **READY_FOR_M2 = NO**

本轮只修 correctness 与 fidelity；没有重新设计 neutral material，没有进入 M2，没有修改 production，也没有 push。

## 1. Hero shell 原来的错误

旧 Hero 使用 `analytic circle mask + procedural white rim`。这造成均匀白描边，和正式 Still 的薄、不均匀、随曲率变化的 outer film 不是同一个 shell identity。

## 2. 正式 shell 修复

修复后 Hero 使用：

- `assets/waterball-still-v1/layers/01_outer_film.png` 的真实视觉内容；
- profile 冻结的 center `[426.5, 925]` 与 radius `316`；
- 与 production `buildSilhouetteMask()` 一致的 `alpha >= 6` 逐行左右边界填充 mask；
- 同一 400px study body domain 的 affine 映射。

没有修改正式 PNG 像素内容，没有重新画白色圆环，也没有改变 center / radius / body domain。正式 source hash、crop 和 mask 见 [`donor-baking-manifest.json`](donor-baking-manifest.json)、[`formal-outer-film-crop.png`](formal-outer-film-crop.png) 和 [`formal-silhouette-mask.png`](formal-silhouette-mask.png)。

结果：均匀白描边感明显消失，Hero 外膜更接近 Final Art / Frozen Still 的薄膜折射身份，内部 donor material 保持。

## 3. RGB/BGR correctness A/B

原实现中的：

```python
patch = arr[sy, sx][:, :, ::-1]
```

输入 `arr` 来自 PIL RGB image → numpy RGB array。当前 pipeline 没有 BGR API，也没有 OpenCV context，因此这个反转没有依据。

A/B 只改变 `reverse_channels`：

- **A**：保留 channel reversal，作为 negative control；
- **B**：正常 RGB patch，其他步骤与 shell 完全相同。

输出：

- [`core-reconstruction-ab.png`](core-reconstruction-ab.png)
- [`local-color-difference.png`](local-color-difference.png)
- [`m1-neutral-hero-channel-ab.png`](m1-neutral-hero-channel-ab.png)
- [`correctness-metrics.json`](correctness-metrics.json)

Fresh comparison 显示 B 的局部色彩与 donor 周边连续，A 在 cold/warm reconstruction 区域出现偏暖/偏灰偏移。因此最终修复采用 **B_NORMAL_RGB**，没有保留 unexplained channel swap。

## 4. Core / halo reconstruction

只做局部 correctness repair：translated local patch、radial falloff 和周边 annular material fill。没有使用大 blur 掩盖问题。

检查项：

- cold core：无可读色偏；
- warm core：无可读色偏；
- halo：无亮斑、暗斑或 crater；
- patch boundary：无明显矩形边界；
- final Hero：无 localized blue/orange residue。

**CORE RESIDUE = NONE**。

## 5. Sparse Detail Alpha Visualization

`neutral-water-detail.png` 的 source asset 保持不变。新增 review-only：

- [`sparse-detail-alpha-raw.png`](sparse-detail-alpha-raw.png)：原始 alpha；
- [`sparse-detail-alpha.png`](sparse-detail-alpha.png)：只提高显示增益，不改变 source；
- Review 页面中的 `SPARSE DETAIL — ALPHA VIEW`。

Alpha view 可直接检查 detail 的分布、稀疏程度、局部存在/缺失和是否形成 blob / fingerprint / contour。当前分布是少量、断裂、不同尺度、低覆盖率结构，未见规则重复带。

## 6. Corrected Hero

当前 Hero：[`m1-neutral-hero.png`](m1-neutral-hero.png)。

它使用同一套：

- Neutral Volume；
- Thickness；
- Sparse Detail；
- corrected B_NORMAL_RGB reconstruction；
- formal `01_outer_film` + formal silhouette mask。

没有重新调 cloudy richness、thickness design、detail vocabulary、formation 或 deformation。

## 7. Final Art comparison / Fresh Critic

只看 `FINAL_ART_025`、`FINAL_ART_050`、`FROZEN_K2` 与 corrected Hero：

1. **外膜是否仍有明显白描边/程序化圆环感？** 没有，formal outer film 的不均匀薄膜折射可读。
2. **内部 water material 是否保留 donor-route cloudy richness？** 保留；内部 material representation 未重做。
3. **core reconstruction 是否存在色偏或痕迹？** A 有偏移，B 已消除；B 为最终版本。
4. **front / internal / rear depth 是否仍成立？** 成立；Thickness source 与 Hero compositor 未改设计。
5. **sparse detail alpha 是否自然且稀疏？** 是；新增 alpha view 后可直接检查。
6. **Hero 是否更接近 Final Art material family？** 是；shell fidelity 修复后更接近 Final Art / Frozen Still 的整体身份。

**IMPROVEMENT = CLEAR**。未发现 correctness-level blocker，也没有发生 internal material regression。

## 8. 是否修改 material representation

没有重新设计 material representation。修改仅限：

- formal shell source / mask correctness；
- core reconstruction RGB channel correctness；
- review-only alpha visualization；
- generated evidence 与 provenance。

## Final boundary

```text
DONOR MATERIAL ROUTE = PASS
FORMAL SHELL FIDELITY = PASS
CORE RECONSTRUCTION COLOR = PASS
CORE RESIDUE = NONE
SPARSE DETAIL REVIEWABILITY = PASS
NEUTRAL POSE = PRESERVED
MATERIAL FAMILY = READY FOR HUMAN REVIEW
READY_FOR_M2 = NO
```

Commit hash：本轮提交后记录于最终报告。
