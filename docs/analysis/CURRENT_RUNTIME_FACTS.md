# 当前 WaterBall 事实入口

更新：2026-10-02。这里只描述当前分支可读取的事实及证据边界。

- 025 静态候选已由人工锁定：`verification/final-art-025-material-test/static-material-lock.json`。它是单视角实验外观基线，不是 production authority。
- M2 静态 GPU pass 来源提交 `cc9e59e` 已由用户本轮确认锁定；8 个字段的当前哈希与 M2 evidence 一致。冻结 shader、字段和显示参数见 `m2-static-gpu-lock.json`。
- 当前只允许 M3 首段独立参数/字段实验。生产入口 `waterball.html`、`components/waterball/` 和 `assets/` 不属于本轮修改范围。
- M3 第二段验证页 `verification/final-art-025-material-test/m3-continuity-preview.html` 只在固定球体内连续改变四个字段参数，并沿既有 refraction field 做有界内部输运；silhouette 采样固定在 base UV，避免内部输运带动外轮廓；播放、暂停、拖拽和重置均为实验页局部行为，不是 ProductState 或 moving。
- M3 连续性闸门已在真实 WebGL2 浏览器中通过：中性背景的 0/.25/.5/.75/1 五点相邻帧均有非零内部变化，外部背景最大漂移为 0，平滑比为 1.0988，检查后恢复到暂停的 025 状态。证据见 `verification/final-art-025-material-test/m3-continuity-evidence.json`；这仍是人工视觉审查前的实验事实，不等于 M3 或 K2 关闭。
- 生产源码仍包含旧 formation、ProductState、visualTime、suspend/resume/reset 和 RAF 实现；本轮没有运行生产 E2E，因此不声明这些行为当前通过。
- 历史 `verification/continuous-water-prototype/m1-current-evidence.json` 的 `AWAITING_HUMAN_REVIEW` 属于旧 neutral-source。它与本次已接受的单视角 025 路线不是同一证据；以当前锁定记录与 roadmap 执行，不补认历史 pose-neutral 验收。
- M2 输出以透射、吸收、反射、scatter、film 重合成。字段来自单视角外观分解，不是唯一物理恢复；固定烘焙高光的形变适用性仍未证明。
- K2 endpoint 尚未通过当前路线验证；M4 及后续运行时、production migration、moving 不得提前开始。
- 主仓库此前保留的 `leader preserve pre-promotion main work` stash 与独立 feature worktree 保持原样。

执行边界与验收见 [roadmap](../tasks/waterball-continuous-roadmap.md)。实验成功不改变产品状态契约或 v1 asset authority。
