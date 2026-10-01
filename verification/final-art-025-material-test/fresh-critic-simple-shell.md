# 025 simple-shell follow-up

这是对上一版 `sphere relief` 的针对性修正：用户确认内部凹陷有所改善，但边缘光影变得过于复杂，偏离最初完整、轻薄的球体。

## 直接观察

- 浅色背景：`candidate-optical-light-025-simple-shell.png` 保留球体完整读法，边缘只留下柔和薄膜，环形高光明显收敛。
- 深色背景：`candidate-optical-dark-025-simple-shell.png` 仍能看到球体和内部浅青云层；边缘不再抢过主体。
- 分屏 / 棋盘：透明度、轮廓和背景透过关系仍然存在；没有重新加入复杂边缘纹理。

## 本次只改一项

沿用 `sphere relief` 的内部 optical field，只把 formal film 的 alpha 贡献降到 `0.25`，并从磁盘回读 `field-formal-film-025-simple-shell.png` 重建四背景候选。没有移动外膜几何、轮廓、球心、半径或点位，也没有使用 final-RGB lift。

## 裁决

`025 simple shell = READY FOR HUMAN REVIEW`

这是静态候选，仍需人工确认边缘是否已经回到初始参考的简洁关系。动态实现、production 接入和 M3 继续关闭。
