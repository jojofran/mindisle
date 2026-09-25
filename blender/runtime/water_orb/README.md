# WaterOrb runtime handoff

这是一份不依赖参考图的轻量运行时资产：`water_orb.obj` 是真实 UV 球网格，五张 PNG 只表达厚度、流动、折光、法线和发光掩码。`water_orb.blend` 是可编辑的 Blender 源文件副本；`WaterOrbRuntime.shader` 是 Unity URP 的低成本重建版本。

## Unity 映射

| Blender 视觉层 | Unity 实现 |
|---|---|
| 连续球体外轮廓 | `water_orb.obj`，平滑法线，半径 1 |
| 中心青色深度 | `water_orb_thickness.png` → `_CoreDark/_CoreLight` 插值 |
| 宽面流带 | `water_orb_flow_mask.png` → `_FlowColor`；灰度图只控制影响区域，方向由 Shader 程序生成；`_FlowSpeed` 可设为 0 做静态帧 |
| 细碎折光 | `water_orb_caustic.png` → `_CausticStrength` |
| 表面扰动 | `water_orb_normal.png` → 法线偏移 |
| 外缘与暖点 | `water_orb_emission.png` → `_EmissionColor` |
| Fresnel 水膜 | Shader 中 `pow(1-dot(N,V), _RimPower)` |
| Blender 透射/玻璃 | URP 透明混合；需要更强折射时接入场景颜色，否则保持当前廉价降级 |

## 推荐设置

使用 URP Transparent 材质，关闭深度写入，开启相机 HDR；在移动端将 `_CausticStrength` 保持在 0.08–0.16，避免多层透明壳。若目标设备不支持场景颜色折射，直接保留 Fresnel + 厚度 + 法线版本，球体仍保持真实视差和轮廓。

网格约 2,112 顶点 / 3,968 三角形，纹理为 5 张 512² 灰度或 RGB 图。资产不包含原始参考图，也不把背景、文字或界面烘焙进材质。

`water_orb_thickness.png` 是近球体的中心厚、边缘薄场；`water_orb_flow_mask.png` 是 S 形影响遮罩，不是向量流图。运行时方向来自 Shader 内的程序场，避免把灰度亮度误称为二维流向。

逐项审计记录见 `runtime_audit.json`。当前纹理语义、Shader 采样关系和无参考图约束已通过静态检查；Golden Frame 与 ±10–15° 实际渲染仍需在 Blender 中完成。

## 当前验证边界

OBJ、材质图和 Shader 可由脚本重复生成；静态 Blender 脚本已降低硬白弧线并提高青色透射。由于本机 Blender 5.2.2 的 Metal 后端初始化崩溃，修订后的 Golden Frame 尚未重新渲染，旧 PNG 不能作为本轮修订的视觉通过证据。
