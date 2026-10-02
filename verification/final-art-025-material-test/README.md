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

当前已由人工确认并锁定 `candidate-optical-light-025-reference-left-shadow-highlight-soft.png` 为 `025_STATIC_MATERIAL_LOCKED`。中性灰审查预览为 `candidate-optical-neutral-025-reference-left-shadow-highlight-soft.png`。锁定记录见 `static-material-lock.json`；旧候选仍保留为历史/回退证据，不再作为下一步入口。

实际主 donor 是 candidate-formal-static-baseline.png。它来自正式 2.5D 包中的 static_composite.png，按球体边界裁切后作为离线 donor。它不是最终候选，也不是 Final Art 025 原图。

锁定后的主候选由 optical-evidence.json 指向 `candidate-optical-light-025-reference-left-shadow-highlight-soft.png`。它沿用已校准的 optical fields，只对浅色/中性背景上的高光显示贡献做轻量收敛。它直接降低高 optical-depth、内部、非 shell 区域的 absorption；没有继续使用 final-RGB lift。candidate-optical-light-cooler.png 保留为未来 mid-depth / transition reference，candidate-optical-light.png 保留为较深材料基线。

主候选从导出的 optical、internal reflection、internal scatter、thickness、refraction、silhouette、formal shell reflection 和 M1 detail PNG 回读后重建；当前仍是静态验证，不是 GPU 运行时。

candidate-final-art-025-no-points.png、candidate-final-art-025-with-points.png 是诊断图，不是主候选。自查发现正式背景板已经包含完成后的材质，直接再把 01–11 层 alpha-over 会重复叠加，产生非目标亮纹和黑带，因此已明确标为无效主路线。

## 运行

在仓库根目录运行：

python3 verification/final-art-025-material-test/build_final_art_025_material_test.py

然后打开 index.html。页面中的层开关用于解释层的贡献，不代表生产合成顺序。

构建所需的冻结输入已复制到本目录的 `inputs/`，两个 builder 只从该目录读取，避免依赖 verification/continuous-water-prototype 目录中的其他文件。

## 边界

- still 静态验证；
- 不实现 transitioning / moving；
- 不添加实时物理、GPU 体积光线步进或运动；
- 不把点核、双核当作主体材质结构；
- 不修改生产资源；
- 不修改生产资源；
- 状态为 `LOCKED_BY_HUMAN_REVIEW_FOR_NEXT_STEP`；这只锁定静态 025 审查基线，不代表 GPU 运行时或 M2 已关闭。DIAGNOSTIC_ONLY 的 evidence.json 仍只记录旧层叠诊断。

## v2 光学字段候选

build_optical_fields.py 生成当前主候选 candidate-optical-light.png。它没有把 Final Art 025 原图当作最终 shader 贴图，而是把正式静态材质基线拆成可检查的光学字段：

- field-optical-depth.png：吸收 / 光学深度；
- field-reflected-light.png：反射光；
- field-thickness.png：M1 厚度输入；
- field-refraction.png：局部折射偏移；
- field-silhouette.png、field-formal-film.png、field-m1-detail.png：正式轮廓、外膜和 M1 细节输入。

这一拆分是单视角画面定向的近似，不是从单张参考图测得的真实物理参数。Final Art 025 的去文字 / 去光点计数只属于诊断分支，未作为主 donor 使用。optical-evidence.json 记录了实际 donor、optical-depth 校准 mask、internal/shell reflection 分离、字段 PNG 回读、四背景候选、厚度均值匹配消融和限制。future-transition-envelope.json 只记录 025 → 050 → 075 → K2 的视觉范围，不实现 interpolation、formation 或 runtime state。它仍然需要人工判断，不能自动关闭 M2。

## 锁定后的下一步

下一步只做静态 GPU 材质接入准备：读取锁定候选对应的 optical depth、thickness、scatter/reflection、refraction、silhouette、formal film 和 detail 字段，并在独立验证 pass 中复现静态画面。不得修改 production、ProductState、formation、deformation、moving 或进入 M3；不得重新启用旧的 00–11 全层 alpha-over 路线。

## M2 静态 GPU 材质验证

入口：`m2-static-gpu-material.html`。页面用 WebGL2 片元着色器从磁盘重新读取 8 个锁定字段，复现 025 的静态画面；同一 pass 可切换浅色、中性灰、深色、分屏和棋盘背景，并比较空间厚度、均值匹配厚度和厚度关闭三种状态。对比区显示的是同一 GPU 帧的复制，避免第二个 WebGL 上下文造成假空白。

由于浏览器会阻止 `file://` 页面把旁边的本地 PNG 上传为 WebGL 纹理，需要在仓库根目录启动本地静态服务器后打开：

```text
python3 -m http.server 8765 --bind 127.0.0.1 --directory verification/final-art-025-material-test
```

然后访问 `http://127.0.0.1:8765/m2-static-gpu-material.html`。

本页的结论边界是“静态字段可被 GPU 读取并影响输出”，不是生产材质接入或动态材质成立。验证记录见 `m2-static-gpu-evidence.json`；它记录了浏览器加载状态、背景闸门、PNG 回读误差和厚度消融数值。M2 已按 `m2-static-gpu-lock.json` 锁定，生产 renderer、ProductState、formation、deformation 和 moving 仍未触碰；M3 只从下面的首段隔离页面开始。

## M3 首段连续字段研究

入口：`m3-continuous-field-study.html`。这是 M2 之后的第一段连续字段实验，同一个固定球体使用同一组锁定 PNG，只开放四个真实 GPU uniform：`optical depth`、`cloudy density`、`local refraction`、`sparse detail`。`025 锁定` 和 `恢复 025` 都回到 M2 的默认值；`中段研究`、`深度研究` 只是 future transition study preset，不能当作 050、075 或 K2 authority。

本页保持 spatial thickness、silhouette、formal film、reflection、center、radius 和 hitRadius 冻结，没有时间循环、状态变化、formation、deformation、core movement 或 production migration。`window.__M3_FIELD_STUDY__.inspect()` 可读取当前参数，`reset()` 可执行真实重置。证据见 `m3-continuous-field-evidence.json`。

## M3 连续动态 2.5D 预览

入口：`m3-continuity-preview.html`。这是在同一固定 body domain 上的下一段实验：025、mid-depth、deep-depth 作为同一条参数路径的锚点，内部字段沿已有 refraction field 做有界的小幅输运。页面提供真实播放、暂停、进度拖拽和回到 025，`window.__M3_CONTINUITY_STUDY__.inspect()` 可读取当前连续位置。

这不是三张静态图的交叉淡化，也不是 production 的 `ProductState`、`transitioning` 或 `moving`。内部字段可以沿 refraction 方向做小幅输运，但 silhouette 固定使用 base UV，外轮廓不随内部变化漂移。页面的“运行连续性闸门”会在中性背景采样 0/.25/.5/.75/1，检查外部背景稳定、内部变化非零和平滑比，并在结束后恢复原状态。K2 仅作为静态终点参照，当前不向 K2 插值。相邻锚点帧、播放/暂停/重置、连续性闸门和边界记录见 `m3-continuity-evidence.json`。
