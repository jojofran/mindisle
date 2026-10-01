# 025 reference-side-clean follow-up

用户指出参考校准候选的左右两侧仍有多余覆盖层，像旧外膜叠在球体上。本次只处理左右 lateral shell / reflection，不改变顶部修正和中央浅色主体。

## 直接观察

- 浅色背景：`candidate-optical-light-025-reference-side-clean.png` 去掉左右两块多余覆盖后，球体轮廓更干净，主体仍保持完整浅色球体。
- 深色背景：左右边缘的暖色/暗色覆盖减弱，透明轮廓仍在；内部字段没有被重新加深。
- 分屏 / 棋盘：左右侧背景透过关系更连续，中心浅青和顶部柔化保持不变。

## 本次只改一项

使用 `field-025-reference-side-mask.png` 限定左右外侧带：film alpha 降到 0.05，lateral reflected light 保留 0.50；顶部和中央不动。候选仍从导出 PNG 字段回读重建，没有 final-RGB lift、动态状态或 production 接入。

## 裁决

`025 reference side clean = READY FOR HUMAN REVIEW`

这是针对截图问题的局部修正；旧的 reference-soft、simple-shell 和 sphere-relief 版本保留作对照。
