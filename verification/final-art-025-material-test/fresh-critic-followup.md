# 025 sphere-relief follow-up

这是用户在 Cycle 2 之后针对“仍有凹陷感”的一次定向跟进，不重新开启 025 的第三个 calibration cycle，也不改变原有 `candidate-optical-light-025-calibrated.png`。

## 直接观察

- 浅色背景：`candidate-optical-light-025-sphere-relief.png` 的主体更接近完整球体；大块水体阴影被压低，银白透明层级更清楚，局部云层和点位仍在。
- 深色背景：`candidate-optical-dark-025-sphere-relief.png` 通过局部中性散射保留球体读法，中心不再塌成黑洞；仍能看到少量内部云影，透明外膜没有被移除。
- 分屏 / 棋盘：球体轮廓、外膜和背景透过关系保持；修正没有变成单纯的蓝色或白色全局提亮。

## 本次修正

1. 在既有高 optical-depth、内部、非 shell mask 上做空间柔化，继续降低宽幅内部吸收。
2. 从浅色预览中提取宽幅阴影 deficit，反投影为 `field-025-shadow-relief-mask.png`，只在对应内部区域补入少量银白散射。
3. 没有使用 final-RGB lift，没有修改 formal shell、轮廓、球心、半径或点位。

## 裁决

`025 sphere relief = READY FOR HUMAN REVIEW`

这是静态候选，不是人工材质身份 PASS；暗背景下残余云影和外膜高光仍需人工决定是否接受。动态实现、production 接入和 M3 继续关闭。
