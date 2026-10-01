# 025 highlight-soft follow-up

深色背景下球体轮廓完整，浅色和中性灰底上白色壳光与浅色内部叠加，造成边缘对比被冲淡。本轮只做展示贡献的轻量软化，不重新制作材质字段。

## 本轮变化

- reflection 显示贡献：`1.00 → 0.55`
- formal film 显示贡献：`1.00 → 0.30`
- internal scatter 显示贡献：`1.00 → 0.85`
- optical depth、alpha、silhouette、center、radius、refraction、geometry：保持不变

## 复核

- 浅色底：顶部和左右边缘不再被白色壳光冲成断层，球体连续性更容易读出。
- 中性灰底：内部淡青和外轮廓仍在，边缘不再出现额外的亮膜感。
- 深色底：仍保持完整球体读取，只是高光更克制。
- 棋盘、分屏和四背景检查继续使用同一组 frozen fields。

`025 highlight-soft = READY FOR HUMAN REVIEW`
