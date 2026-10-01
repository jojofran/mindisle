# 025 reference-left-shadow-clean follow-up

用户指出左上角灰色阴影太多并越过边界，导致外层膜像断裂。来源拆分确认：该灰带在关闭 formal film、reflection 和 scatter 后仍存在，主要来自左上外弧的 optical-depth field。

## 直接观察

- `candidate-optical-light-025-reference-left-shadow-clean.png` 只把左上外弧灰色阴影收窄，球体内部和 alpha 没有被整块抹掉。
- 膜线与主体边界重新连续；右上角沿用上一版 upper rebalanced，不追加新的全局调色。
- 深色、分屏、棋盘候选同步生成，仍是静态验证，不进入 production 或动态实现。

## 本次只改一项

`field-025-reference-left-shadow-mask.png` 是左上外弧窄带 mask；该区域 optical depth 降低 75%，补入少量中性 scatter，alpha 保持原值。目的是真正移除越界灰影，而不是继续模糊膜层。

`025 reference left shadow clean = READY FOR HUMAN REVIEW`
