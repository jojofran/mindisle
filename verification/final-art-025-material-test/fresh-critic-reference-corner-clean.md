# 025 reference-corner-clean follow-up

用户指出顶部左侧仍有一块越出球体的额外叠层。复核发现上一版遮罩落在球体内部，未覆盖截图中的外弧；本次把遮罩移到左上外弧，并对该区域的光学深度、散射、film、反射和覆盖度一起做羽化收敛。

## 直接观察

- `candidate-optical-light-025-reference-corner-clean.png` 的左上角越界叠层已移除，球体轮廓保持连续；10px 羽化避免出现硬切口。
- 中央浅色主体、顶部柔化、右侧主体和点位没有被改动。
- 深色、分屏、棋盘候选同步使用同一 corner mask，避免背景变化时重新出现该覆盖层。

## 本次只改一项

`field-025-reference-corner-mask.png` 只覆盖左上角外侧带；该区域的 optical depth 和 internal scatter 收敛为零，film 和 reflected light 清零，alpha 以 10px 羽化半径降低 75%，silhouette、主体中心和其余轮廓保持原值。

`025 reference corner clean = READY FOR HUMAN REVIEW`
