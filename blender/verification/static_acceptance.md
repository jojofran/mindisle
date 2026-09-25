# 水球静态成对验收（MCP 最终静态基线）

渲染证据：`blender/renders/mcp-final-v5/still.png`、`blender/renders/mcp-final-v5/moving.png`；并排证据：`verification/still-full-comparison.png`、`verification/moving-full-comparison.png`、`verification/still-detail-comparison.png`、`verification/moving-detail-comparison.png`。

| 项目 | 结果 | 可见依据 |
|---|---|---|
| 构图比例 | 通过 | 两个场景共用正交相机，852×1846；球心约从顶部 53%，主体直径参数为屏宽 62%。 |
| 单一连续外轮廓 | 通过 | still/moving 都由同一连续 Icosphere 拓扑生成；两场景主体均为 10242 顶点、20480 面，拓扑 SHA-256 相同。 |
| 水感与边缘高光 | 待修 | 已有连续 Fresnel 边缘、背景折射/透射和长条柔光；与参考相比仍偏柔、折射纹理和暖色高光不足。 |
| 中心青色聚集 | 通过基础关系 / 待修细节 | 两状态都有中心吸收体积，moving 密度更高；当前中心仍比参考更均匀。 |
| 内部膜层深度 | 通过基础关系 / 待修细节 | 有三组开放折叠膜和一条宽 S 形膜，能看到前后遮挡；弧线规则度仍高于参考。 |
| 波纹与光纹 | 待修 | 当前光纹主要由膜面和柔光形成，参考中的细碎折光纹理尚未达到。 |
| 两个点的位置与大小 | 通过 | still 两点悬在球内；moving 两点分别放在对应流带端点，节点半径为 0.025R。 |
| moving 两条流带连续关系 | 通过结构 / 待修透明度 | 两条流带均为开口曲面，中段展宽，端部宽度和透明度趋零；当前灰度略重。 |
| moving 局部轮廓形变 | 通过 | moving 使用与 still 相同的连续网格和无极点接缝的多项式形变；本阶段只冻结形变，不播放动画。 |
| 静态阶段无动画 | 通过 | 两场景 `animation_data_count=0`，没有 keyframe/driver；静态预设可重复重建。 |
| Unity/WebGL 范围 | 通过 | 本轮只改 Blender 脚本、参数、渲染和验收图；没有修改 Unity、WebGL 或产品状态机。 |

## 已知待修

1. 宽斜向膜边和内部 S 形膜仍有规则弧线感，需要下一轮用曲率/噪声分布继续打散。
2. Blender 候选已能作为可重建的静态资产，但还没有达到参考图的细碎折光和暖色高光密度，当前不能称为视觉定稿。
3. 实际渲染为 Cycles CPU、128 samples、AgX、曝光 0；没有发生渲染器回退。移动端 Unity 的 Shader、灯光、折射和色彩仍需重建校准。
4. 本轮没有制作 transitioning、动画；也没有修改 Unity/WebGL。下一步应在静态视觉确认后，先做单次 still→moving 过渡，再导出 Unity 参数。

## v1 视觉锚点与产品演进

`visual-targets/still-target-v1.png` 和 `visual-targets/moving-target-v1.png` 是当前更接近参考的视觉锚点，已通过 `components/waterball` 接入 `index.html`：开始专注显示 moving，点击水球或暂停显示 still，继续回到 moving。它们不取代 Blender 的可重建实现；下一轮以这两张图作为差异测量目标，每轮只改一个最大视觉差距。

## 主流程验证记录

在本地预览服务中实际走过：`我的岛 → 开始一段时间 → 下一步 → 进入这段时间`。进入后读到 `轻触水球，进入静止状态`、倒计时递减和 moving 画面；点击水球后读到 `轻触水球，开始或继续冥想`、按钮变为 `继续`，800ms 后计时仍保持不变；点击 `继续` 后恢复 moving 和倒计时。这个证据只证明当前参考层与状态时钟接通，不证明移动端性能或 Unity 实时材质已经完成。
