# 025 中性灰背景审查

用户指出浅色背景的高亮会干扰球体判断。本次只切换展示底色，不改 optical depth、scatter、film、reflection、alpha 或 silhouette。

## 观察

- `candidate-optical-neutral-025-reference-left-shadow-clean.png` 使用 RGB 154/166/170 的均匀中性灰底，轮廓比浅色底更容易读出。
- 白色边缘高亮被压低后，球体仍保持完整圆形；左上外弧的灰色阴影没有再被高亮误读成断裂的多余膜。
- 内部仍可见淡青云层和局部厚度，未变成纯白或无体积的雾球。
- 中性灰底只是 review preview；浅色、深色、分屏、棋盘四种背景仍保留用于背景闸门。

## 结论

`025 material + neutral review background = READY FOR HUMAN REVIEW`

本次没有修改生产、运行时、动态或 M3，也没有把中性底色当作材质字段。
