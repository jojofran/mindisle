# 当前 WaterBall 事实入口

更新：2026-10-02。这里只描述当前分支可读取的事实及证据边界。

- 025 静态候选已由人工锁定：`verification/final-art-025-material-test/static-material-lock.json`。它是单视角实验外观基线，不是 production authority。
- M2 静态 GPU pass 来源提交 `cc9e59e` 已由用户本轮确认锁定；8 个字段的当前哈希与 M2 evidence 一致。冻结 shader、字段和显示参数见 `m2-static-gpu-lock.json`。
- 当前只允许 M3 首段独立参数/字段实验。生产入口 `waterball.html`、`components/waterball/` 和 `assets/` 不属于本轮修改范围。
- M3 第二段验证页 `verification/final-art-025-material-test/m3-continuity-preview.html` 只在固定球体内连续改变四个字段参数，并沿既有 refraction field 做有界内部输运；silhouette 采样固定在 base UV，避免内部输运带动外轮廓；播放、暂停、拖拽和重置均为实验页局部行为，不是 ProductState 或 moving。
- M3 连续性闸门已在真实 WebGL2 浏览器中通过：中性背景的 0/.25/.5/.75/1 五点相邻帧均有非零内部变化，外部背景最大漂移为 0，平滑比为 1.0988，检查后恢复到暂停的 025 状态。证据见 `verification/final-art-025-material-test/m3-continuity-evidence.json`；当前连续路径已获用户人工 PASS；这仍不等于 M3 或 K2 关闭。
- 生产源码仍包含旧 formation、ProductState、visualTime、suspend/resume/reset 和 RAF 实现；本轮没有运行生产 E2E，因此不声明这些行为当前通过。
- 历史 `verification/continuous-water-prototype/m1-current-evidence.json` 的 `AWAITING_HUMAN_REVIEW` 属于旧 neutral-source。它与本次已接受的单视角 025 路线不是同一证据；以当前锁定记录与 roadmap 执行，不补认历史 pose-neutral 验收。
- M2 输出以透射、吸收、反射、scatter、film 重合成。字段来自单视角外观分解，不是唯一物理恢复；固定烘焙高光的形变适用性仍未证明。
- K2 endpoint 尚未通过当前路线验证；已完成 K2 endpoint gate 审计，证据见 `verification/final-art-025-material-test/k2-endpoint-gate.json`：已有固定视角的 authored optical fit 字段包，但仍没有经验证的完整、自由视角 K2 optical field；静态 K2 PNG 和 pose-dependent 07–10 layers 仍不能直接充当独立字段，因此连续终点仍 BLOCKED。M4 及后续运行时、production migration、moving 不得提前开始。
- 用户已裁决 A（`static_composite.png`）为 K2 静态 authority，并确认 **A shell/core + B interior 最好**；B（`reference_foundation.png`）只作为内部纹理/流向参考，B 的 core 不继承。当前候选 `a-authority-b-internal-study.png` 已人工通过并锁定为 K2 静态候选，自动检查确认 shell 和 core 保持 A。此前 manifest 与 static_composite 的源包不一致仍保留为证据，独立 K2 field recovery 尚未证明。
- K2 authored interior handoff 已在 `k2-interior-field-study.html` 明确为 A → A+B interior slice：从 `k2-interior-field/k2-interior-field-package.json` 的 base/delta/mask/silhouette 回读，并在真实 Ego Browser WebGL2 中复核播放、暂停、reset 和保护区闸门；5 个 fieldStrength 采样点的外部背景最大漂移为 0，高置信度 shell/core 保护区最大漂移为 0，内部最小相邻变化为 0.7915/255；离线 delta 回读均值误差为 0.118862/255、P95 为 0.443137/255。证据见 `verification/final-art-025-material-test/k2-interior-field-evidence.json`；当前仍不代表完整 K2 optical endpoint、runtime、M4 或 production readiness。
- 在上述 handoff 之后，`k2-authored-optical-field-study.html` 提供了从磁盘字段回读的 fixed-view authored optical fit：以冻结的 A shell/core 为 base，以 A+B interior 候选为 target，独立读取 optical depth、thickness、signed residual、refraction、mask 与 silhouette 后重建；回读均值误差 0.517228/255、P95 1.039790/255、最大误差 1.680228/255。该结果证明字段包可以在固定视角复现本轮候选，不证明唯一物理恢复、自由视角稳定性或完整 K2 endpoint；signed residual 仍包含未分离的 reflection/scatter/film，M3、M4 与 production migration 继续未关闭。
- `k2-endpoint-review.html` 现在是人工审查入口，集中链接 authority、interior handoff、authored field 和 endpoint gate，并明确下一步是人工确认后补完整 K2 field 证据；不把 fixed-view fit 误报为 M3/K2 完成。
- authored optical field 页已补四背景 GPU 闸门：light、dark、split、checker 五个进度采样均保持 outside/protected 最大漂移 0，interior 有非零变化；证据见 `verification/final-art-025-material-test/k2-authored-optical-field-gpu-evidence.json`。该结果仍是 fixed-view verification，不能替代自由视角 K2 endpoint 或人工材质判断。
- 用户已对当前 fixed-view K2 authored field 做出人工 `PASS_REVIEW`：球体完整、播放时只动内部、四背景下仍像水；裁决和后续统一规则记录在 `verification/final-art-025-material-test/k2-endpoint-gate.json` 与 `verification/final-art-025-material-test/k2-visual-review-protocol.md`。这允许继续补完整 K2 field，但不关闭完整 endpoint gate。
- 已生成 `k2-complete-authored-field/`：A shell、A core、silhouette、B interior mask、optical depth、density、thickness、transmission、refraction 和 unresolved signed residual 均有独立字段；固定视角回读的 shell 最大相对 A 误差 2.031373/255、core 0、outside 0，完整 package 仍标记为 free-view BLOCKED，需人工审查后才能决定下一步。
- `k2-complete-field-study.html` 已把上一轮通过版本与完整字段包放在同一页左右对照；右侧新字段可播放、暂停、切背景并生成单项裁决文本，真实浏览器检查确认字段加载和交互可用。
- 用户曾确认旧 0.012 输运幅度下的自动播放内部变化自然；为解决“点击播放没拖动滑杆明显”，验证页将输运幅度调到 0.026，并把自动播放节奏调整为约 3.3 秒一轮的平滑 sweep（phase 速率 0.0026，strength 频率 0.72，flow 频率 0.9）。这是仅限研究页的可见性调参，静态 field package、shell、core 不变；当前 0.026 / 0.0026 调整已获用户人工确认；独立 K2 field proof、M4 和 production readiness 仍未通过，source audit 已确认 A 与冻结 static composite 逐像素一致；旧 manifest mismatch 被保留为诊断问题，下一步是对 fixed-view authored field 做人工视觉审查，再决定是否继续补完整 K2 endpoint 证据。
- 主仓库此前保留的 `leader preserve pre-promotion main work` stash 与独立 feature worktree 保持原样。

执行边界与验收见 [roadmap](../tasks/waterball-continuous-roadmap.md)。实验成功不改变产品状态契约或 v1 asset authority。
