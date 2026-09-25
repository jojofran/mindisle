# MindIsle 中央水球交互原型

打开 `Assets/Scenes/Main.unity` 后点击 Play。正式画面只有中央水球；初始状态为 `still`，点击水球本体后进入约 1 秒的 `transitioning`，随后进入持续 `moving`。状态由 `MindIslePrototype.CurrentState` 暴露，过渡进度由 `TransitionProgress` 暴露，运动时钟由 `FlowClock` 暴露。开发环境按 `R` 可重置到确定性的 `still`，正式画面不显示调试控件。

水球、内部薄膜和两个点由实时程序化 Shader 渲染；运动状态的两条外部流带由同一套状态参数驱动的可复用曲线网格渲染，没有使用参考图、视频、序列帧或静态图片切换。轮廓、命中测试和流带采样共享同一套竖屏球面边界；点击球外区域不会改变状态。静止状态冻结流动时钟，只保留两个点的轻微呼吸；挂起时钟冻结，恢复后只继续一次。

`Assets/Editor/OrbPreviewCheck.cs` 提供 `MindIsle/Run Orb Preview Check` 菜单项，验证 `still → transitioning → moving → reset`、中段进度、球外误触、运动时钟、资源实例复用和 Shader 编译，并输出 `../verification/still-state.png`、`transitioning-mid.png`、`moving-keyframe.png`（冻结的程序化运动目标姿态）和 `moving-state.png`（释放冻结后的真实运动帧）。这些 PNG 是 Unity 实际渲染记录，不作为运行时素材。

当前验证环境为 Unity 6000.6.2f1、macOS Metal。尚未宣称 Android/iOS 真机性能结论。
