# 水球视觉目标 v1

这两张图是本轮从参考 still / moving 生成的高保真视觉目标，不是把任务替换成孤立图片：

- `still-target-v1.png`：静止状态目标，锁定透明水膜、中心青色深度、暖色点和画面留白。
- `moving-target-v1.png`：运动状态目标，锁定局部形变、内部翻折、两条开放流带和节点端点关系。

它们已经复制为 `assets/waterball-still-v1.png` / `assets/waterball-moving-v1.png`，通过 `components/waterball` 接入根目录 `index.html` 和独立 `waterball.html` 的冥想主流程，作为第一步可体验的视觉资产；Blender 的下一轮会以这两张图为目标逐项反推外壳、体积吸收、膜层、流带和灯光参数。每次迭代保留旧版本，不把生成图直接冒充程序化材质完成。

来源：使用 `demo-reference/still-state.png` 和 `demo-reference/motion-state.png` 作为参考，通过 imagegen 生成 v1；生成式图像只承担视觉目标和第一阶段产品资产，不承担实时材质或 Unity 性能证明。
