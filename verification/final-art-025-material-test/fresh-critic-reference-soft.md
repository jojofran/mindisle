# 025 reference-soft follow-up

用户指出上一版虽然减轻了凹陷，但光影和边缘仍偏复杂，偏离最初参考中的完整浅色球体；随后又指出顶部有轻微变形。本次把参考图中已确认的浅色内部关系用于一次离线静态 field calibration，并只对顶部修补带做柔化。

## 直接观察

- 浅色背景：`candidate-optical-light-025-reference-soft.png` 更接近完整、轻薄的球体；内部只保留很淡的青色层次，边缘只留下简单薄膜，顶部不再出现假脊线或凹口。
- 深色背景：`candidate-optical-dark-025-reference-soft.png` 保留透明球体轮廓，内部对比显著降低；深色下仍需人工判断是否需要更强的中性散射。
- 分屏 / 棋盘：球体轮廓和背景透过关系保持，没有重新加入复杂环形边缘。

## 本次只改一项

从清理后的 Final Art 025 参考外观反求 optical depth、reflected light、scatter 和低强度 refraction 字段，再从 PNG 回读重建。顶部 UI 修补带只做局部柔化，并记录为 `field-025-reference-top-mask.png`；formal film alpha 降到 0.15。没有做 final-RGB lift，也没有修改生产或动态状态。

## 裁决

`025 reference soft = READY FOR HUMAN REVIEW`

这是最接近当前参考图的离线静态候选。旧 formal-baseline、sphere-relief 和 simple-shell 版本全部保留，供人工比较；动态实现、production 接入和 M3 继续关闭。
