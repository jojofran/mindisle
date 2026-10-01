# 025 reference-upper-rebalanced follow-up

上一版 `upper-clean` 把上角 optical depth 和 scatter 压得过低，膜感减弱了，但球体也变得发雾、不完整。此次回退该做法：继续清除 formal film / shell reflection，只对上角局部烘焙暖冷色做中和，保留原有光学量级。

## 直接观察

- `candidate-optical-light-025-reference-upper-rebalanced.png` 的球体上缘连续，左右上角不再出现明显的独立膜状色带。
- 上角保留水体厚度和内部云层，没有被裁成浅色缺口；顶部中央和主体结构未改。
- 深色、分屏、棋盘候选使用同一 upper mask，静态页面和证据文件均已更新。

## 本次只改一项

`field-025-reference-upper-mask.png` 继续只覆盖左右上弧；formal film / shell reflection 仍清理，optical depth / scatter 改为 75% 局部色彩中和而非强度清零。这样保留完整球体，同时压掉 baked warm/cool membrane cue。

`025 reference upper rebalanced = READY FOR HUMAN REVIEW`
