# MindIsle 水球 Blender 静态成对场景

本轮仍只提交 still / moving 两种静态视觉状态，没有创建动画或修改 Unity/WebGL。为了让视觉迭代直接服务于冥想主流程，新增了一个可替换的水球组件和主流程接入；它只负责静态画面与状态投影，不宣称已经完成实时流体。

## 可重建

在 `/Users/fran/Documents/Code/mindisle` 执行：

```bash
blender -b --factory-startup --python blender/scripts/build_waterball.py -- --state both --stage complete --output-dir blender/renders
```

预览（32 samples、45% 分辨率）：

```bash
blender -b --factory-startup --python blender/scripts/build_waterball.py -- --state both --preview --stage complete --output-dir blender/renders/iterations/preview
```

脚本每次先恢复 factory startup，不累积对象；`--state still|moving|both` 只控制静态预设。脚本会拒绝其他状态，因此本阶段不会误生成动画。

## 本轮文件

- `waterball_static_pair.blend`：包含 shared orthographic camera、still / moving 两个 Scene 和同拓扑单一外壳。
- `scripts/build_waterball.py`：可重复执行的构建与渲染脚本。
- `waterball_static_parameters.json`：以主体半径 R 和 Blender 秒为单位的静态参数、路径点、Unity 映射边界。
- `renders/mcp-final-v5/still.png`、`renders/mcp-final-v5/moving.png`：Cycles CPU 128 samples 最终静态输出。
- `renders/mcp-final-v5/render_manifest.json`：实际引擎、samples、拓扑摘要、对象计数和动画数据计数。
- `verification/*-comparison.png`：参考图与渲染的全画幅/主体细节并排图。
- `verification/static_acceptance.md`：逐项通过/待修及可见依据。
- `components/waterball/profile.js`、`components/waterball/waterball.js`、`components/waterball/waterball.css`：共享坐标、裁切层、命中区域和冥想时钟；是下一轮 Shader/几何替换的接口。
- `waterball.html`：独立可复现的水球冥想验证页，可用 `?state=moving` 固定运动状态。

## 真实渲染设置

最终输出使用 Blender 5.2.2 LTS、Cycles CPU、128 samples、Cycles denoise、AgX、曝光 0、852×1846。没有 Eevee 回退；manifest 中的 `engine_actual` 为 `CYCLES`。PNG 只是验收参考，不是 Unity 动画背景。

## 视觉实现边界

外壳是单一封闭连续网格；内部是体积吸收密度场与开放弯曲薄膜，不是多个透明球套叠。moving 的外部流带是开口曲面，宽度与 alpha 在尾部同时趋零，节点与曲线起点共享坐标。Unity 需要重建透明水 Shader、折射/Fresnel、灯光响应、AgX/色彩和合成光晕；参数文件中已标出可直接复用、需换算和需重建的部分。

## Unity 运行时交接包

`runtime/water_orb/` 提供不含参考图的可复用运行时组件：真实 UV 球 `water_orb.obj`、五张材质掩码、`WaterOrbRuntime.shader`、可编辑的 `water_orb.blend` 和 `runtime_gate.json`。用 `python3 blender/scripts/export_water_orb_runtime.py` 可重复生成。网格约 2,112 顶点 / 3,968 三角形；视角门槛记录了正视、±10° 和 ±15° 的几何轮廓变化。

本轮还收紧了 `scripts/build_waterball_visual_match.py` 的外缘材质：移除会读成硬白塑料环的窄高光，降低发光层并提高青色透射。Blender 的 Golden Frame 需要在 Metal 后端故障修复后重新渲染；现有旧 PNG 不作为这次修改的通过证据。

## v1 视觉锚点与 App 演进

`visual-targets/still-target-v1.png` 和 `visual-targets/moving-target-v1.png` 是当前更接近参考的视觉目标，已经通过 `components/waterball` 接入 `index.html` 与 `waterball.html`。它们不是孤立图片：真实专注流程用 `MeditationSession` 驱动同一水球组件在 still / moving 间切换，暂停时钟冻结，继续后恢复。当前层是“参考图裁切烘焙层”，下一步会逐项替换为可重建的 Shader/几何层。
