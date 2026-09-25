# MindIsle 水球静止视觉 v1

这是固定正面视角的参考图驱动 2.5D 静止资产。最终预合成图为 `static_composite.png`；需要分层时，按 `composite_manifest.json` 的 `layer_order` 从下到上进行 alpha-over 合成。

所有正式图层均为 853×1844、RGBA PNG。冷色点和暖色点各自拥有独立的 `core` 与 `glow`，不依赖旧的合并点位层。

本资产只覆盖 `still`。moving、App、Unity 和运行时接入不在此版本内。
