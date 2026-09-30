# Final Art 025 材质测试

这是一个隔离的静态材质验证目录，不连接生产运行时，也不改变 M1 冻结输入。

## 目的

先回答一个问题：已有的正式静态材质基线，是否已经比此前的程序化几何 / 蓝色雾团路线更接近 Final Art 025。

本轮只看静态材质身份：

- 透明外膜和边缘厚度；
- 内部青绿色体积；
- 连续、柔和的内部层次；
- 小而内嵌的光点是否喧宾夺主；
- 是否仍像材质，而不是固定外部弧线或平面雾。

Final Art 050 只作为深度和厚度的辅助参照，冻结 K2 只作为端点参照。它们不改变本轮目标。

## 当前候选

实际主 donor 是 candidate-formal-static-baseline.png。它来自正式 2.5D 包中的 static_composite.png，按球体边界裁切后作为离线 donor。它不是最终候选，也不是 Final Art 025 原图。

当前主候选是 optical-evidence.json 中的 candidate-optical-light.png。它从导出的 optical、reflected、thickness、refraction、silhouette、formal film 和 M1 detail PNG 回读后重建；当前仍是静态验证，不是 GPU 运行时。

candidate-final-art-025-no-points.png、candidate-final-art-025-with-points.png 是诊断图，不是主候选。自查发现正式背景板已经包含完成后的材质，直接再把 01–11 层 alpha-over 会重复叠加，产生非目标亮纹和黑带，因此已明确标为无效主路线。

## 运行

在仓库根目录运行：

python3 verification/final-art-025-material-test/build_final_art_025_material_test.py

然后打开 index.html。页面中的层开关用于解释层的贡献，不代表生产合成顺序。

## 边界

- still 静态验证；
- 不实现 transitioning / moving；
- 不添加实时物理、GPU 体积光线步进或运动；
- 不把点核、双核当作主体材质结构；
- 不修改生产资源；
- 状态仍为 READY_FOR_HUMAN_REVIEW，需要人工判断 Final Art 025 的材质身份；DIAGNOSTIC_ONLY 的 evidence.json 只记录旧层叠诊断。

## v2 光学字段候选

build_optical_fields.py 生成当前主候选 candidate-optical-light.png。它没有把 Final Art 025 原图当作最终 shader 贴图，而是把正式静态材质基线拆成可检查的光学字段：

- field-optical-depth.png：吸收 / 光学深度；
- field-reflected-light.png：反射光；
- field-thickness.png：M1 厚度输入；
- field-refraction.png：局部折射偏移；
- field-silhouette.png、field-formal-film.png、field-m1-detail.png：正式轮廓、外膜和 M1 细节输入。

这一拆分是单视角画面定向的近似，不是从单张参考图测得的真实物理参数。Final Art 025 的去文字 / 去光点计数只属于诊断分支，未作为主 donor 使用。optical-evidence.json 记录了实际 donor、字段 PNG 回读、四背景候选、厚度均值匹配消融和限制。它仍然需要人工判断，不能自动关闭 M2。
