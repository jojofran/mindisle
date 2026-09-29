# M1.5 — Material-Only Final Gate & Shell Integration Handoff

## Final state

- **M1.3 = CLOSED / EVIDENCE PRESERVED**
- **M1.4 DE-SHELLING = PASS**
- **M1.4 SOURCE TOPOLOGY MEMORY = REMOVED**
- **M1 INTERNAL MATERIAL FAMILY = READY FOR HUMAN REVIEW**
- **NEUTRAL POSE = PRESERVED**
- **FORMAL SHELL OWNERSHIP = DEFERRED_TO_M2**
- **M2 SHELL STARTING POINT = UNRESOLVED**
- **M1 MATERIAL PACKAGE = READY FOR HUMAN REVIEW**
- **READY_FOR_M2 = NO**

本轮没有重烘焙、修改或替换任何 M1 carrier；没有修改 production、formal source、Final Art references、ProductState、formation、deformation、core、timing、moving 或 roadmap，也没有进入 M2 或 push。

## 1. M1.4 继续有效的结果

M1.4 的 safe interior、de-shelled donor interior、unclipped RGB、whole-interior coordinate field、topology stress 和 whole-safe-interior sparse feature extraction 全部保留。M1.4 的 shell blocker 被重新分类为 integration concern，不再阻塞 M1 internal material gate。

## 2. Material-Only comparison domain

建立 material-only-comparison-mask.png，基于现有 SAFE_INTERIOR，统一应用到 FINAL_ART_025 interior、FINAL_ART_050 interior 和 current material。它只限制观察区域，不修改任何 reference RGB；outer shell、core、UI、formation 和 directional pose 都被排除。

## 3. Fresh Critic A — Internal Material Only

只看 FINAL_ART_025 interior、FINAL_ART_050 interior 和 CURRENT combined neutral interior：

1. **是否属于同一种水体材质？** 是。当前保留 white/cyan cloudy water vocabulary 和 authored density variation。
2. **是否是 fog、flat cyan、generic cloud 或 shader blob？** 不是。虽然 current interior 更简化，但仍有连续 cloudy mass、局部密度变化和 sparse internal structures。
3. **cloudy mass 是否自然聚散？** 是。没有回到 radial gradient 或 generic fog。
4. **depth / thickness 是否足以成为后续输入？** 是。neutral-thickness 保持冻结并单独展示。
5. **sparse detail 是否自然、稀疏、无 patch topology？** 是。detail 使用冻结的 M1.4 whole-interior feature extraction 结果。
6. **是否存在普通用户一眼可见的 material representation defect？** 未发现。

因此：

**M1 INTERNAL MATERIAL FAMILY = READY FOR HUMAN REVIEW**。

## 4. Neutral Pose Gate

当前没有 cavity、swirl、强 directional organization 或 core；整体保持 calm / balanced。

**NEUTRAL POSE = PRESERVED**。这仍需 Human Confirmation，不由本轮自行宣告 Human PASS。

## 5. Shell Route Validation

只做一次明确的 A/B/C preview，内部 material 完全相同，formal source pixels 和 source alpha 均未修改：

- **A — M1.4 current top-overlay**：保留 membrane identity，但仍有偏强的 uniform white ring。
- **B — ORIGINAL-ORDER SEMANTICS**：formal outer film 先合成，internal body 后合成；uniform ring 下降，但 shell identity 被 internal body 大幅覆盖。
- **C — ALPHA-AWARE ORIGINAL ORDER**：formal film 仍在 body 下方，body 根据 formal alpha 做轻微 coverage response；比 B 稍有 edge response，但仍不足以确认 Final Art edge language。

Fresh Critic：

1. 最不像 uniform white ring：B / C。
2. 最保留 formal membrane identity：A。
3. 最接近 FINAL_ART_025 edge language：当前没有一个明确胜出；A 的 identity 较好但 ring 偏强，B/C 的 ring 较弱但 optical membrane 不足。
4. blocker 是否属于 compositor / integration？是。M1 internal material gate 已通过，问题发生在 layer order / body ownership 的静态整合。

因此：

- **FORMAL SHELL OWNERSHIP = DEFERRED_TO_M2**
- **M2 SHELL STARTING POINT = UNRESOLVED**

M2 preview 是 NON-AUTHORITATIVE，不关闭 M2。

## 6. Authority correction

本轮不再把 01_outer_film full source alpha 作为必须 top-most overlay 的 frozen authority。冻结的是 formal source asset、silhouette 和 visual identity；原始 manifest 的 layer order 仍需在 M2 static integration 中验证。

## 7. Material source changes

没有修改：

- neutral-water-volume
- neutral-thickness
- neutral-water-detail
- safe interior
- current donor de-shell result
- Final Art references
- formal assets

新增内容全部是 material-only review 和非权威 shell route preview。

## Final boundary

M1 INTERNAL MATERIAL FAMILY = READY FOR HUMAN REVIEW
NEUTRAL POSE = PRESERVED
FORMAL SHELL OWNERSHIP = DEFERRED_TO_M2
M2 SHELL STARTING POINT = UNRESOLVED
M1 MATERIAL PACKAGE = READY FOR HUMAN REVIEW
READY_FOR_M2 = NO

Commit hash：本轮提交后记录于最终报告。
