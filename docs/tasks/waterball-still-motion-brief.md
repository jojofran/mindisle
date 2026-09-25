# 水球 still 微动态实现说明（FROZEN / READY_FOR_LUNA_IMPLEMENTATION）

## 目的

把 `still` 做成未来 `moving` 的低幅、慢速起始态：用户第一眼仍读到“安静、透明、有体积的水球”，持续观察 2–4 秒后能感知球内水体持续、低幅、连续地运动并改变光影。核心原则是“不要让图层动；让水动。图层只是同一水体运动的不同视觉投影”。`still` 与未来 `moving` 应保持同一内部水体运动语言的连续视觉关系，但这不等于当前已经共享同一套运行时实现。主体中心、整体轮廓和触摸命中区保持稳定。该说明供后续 Luna worker 实现；本文件不代表实现已通过。

## 作用域边界

本文件冻结的约束全部属于 **WATERBALL STILL MICRO-MOTION SLICE**。以下规则只约束 still 微动态 milestone 及其 still renderer：点位中心固定、点位本体不随 still 内部流体外移、不采用球外轨迹、动态视觉贡献受正式 still silhouette 裁切，以及不新增外部结构。

这些规则继续作为 still-only slice 的 frozen 验收事实，但不约束后续 `ProductState=transitioning` / `moving`。transitioning / moving 的点位轨迹、球外 core、attached fluid / ink trail、orbit / radial cycle 由 [`docs/tasks/waterball-activation-motion-semantics.md`](waterball-activation-motion-semantics.md) 与 [`docs/product/state-ball-visual-spec.md`](../product/state-ball-visual-spec.md) 管辖。

## 修改范围

- **待确认阶段**：只修改本 brief；不修改代码、资产、manifest、Unity、Blender 或产品状态契约。
- **用户确认后，Luna 实现阶段**：可修改水球运行时渲染适配器、still 微动态所需的视觉时钟/参数/诊断，以及对应测试与验证代码。
- 不得修改正式 still PNG；不得改变 `composite_manifest.json` 的图层顺序、稳定几何或语义；不得改变 `profile.center`、`profile.radius`、`profile.hitRadius`；不得改页面其他交互或 Blender/Unity 历史资产。
- 若实现必须突破上述边界，立即停止并请求产品裁决，不得用实现便利默默扩大范围。

## 参考依据与事实边界

- 产品视觉权威：`docs/product/state-ball-visual-spec.md`。
- 运行时和切片边界：`docs/architecture/state-ball-app-baseline-v0.1.md`。
- 正式 still 资产及合成顺序：`test/water-orb-still/2p5d-composite-v1/README.md`、`composite_manifest.json`，以及对应的 `assets/waterball-still-v1/`。
- 几何事实：853×1844 画布，中心 `[426.5, 925]`，半径 316，命中半径 300；点位来自 `visual_parameters.json`（冷点左上、暖点右下）。
- moving 参考只能作为“连续内部流动”的方向证据。仓库中的 `demo-reference/motion-state.png`、`verification/moving-state.png`、`verification/moving-keyframe.png`、`assets/waterball-moving-v1.png` 和历史 Blender moving renders 均不是新的产品权威；若与正式 v1 still 或产品约束冲突，保留产品约束并记录冲突。

## 当前反复失败的原因

1. 把已经合成好的 `staticCompositeCanvas` 与多个可动画图层重复叠加，造成“静态球 + 另一套运动球”的双重边界，内部体积与高光不再是同一水体。
2. 外壳曲率高光使用大幅位移、shear、scale、blur 和额外 `screen` 波层，运动轨迹超出原曲率语义，读成外露环带、白边或脱离球体的装饰。
3. 边界、体积、流层各自使用不同相位和独立透明度，缺少统一、连续的内部水体运动关系；各视觉层没有表现为同一水体运动的不同响应，结果是局部 alpha/周期变化，而不是水体整体搬运。
4. 当前运行时把 `still` 绑定到 `idleTime/idlePhase` 连续帧循环；`idleTime/idlePhase` 尚未形成满足 `reset/suspend/resume` 的统一事实来源。`transitioning → moving` 尚未实现，且不属于当前 milestone。
5. WebGL material pass 对整张静态合成纹理做二次采样，会把外壳、点位和内部颜色一起扰动；即使保留点位位置，也容易出现颜色漂移、边缘发灰和“滤镜覆盖”。
6. 通过调 alpha、周期或单个高光位置只能改变强弱，不能修复层职责、裁切和流场关系，所以会陷入挤牙膏式迭代。

## 必须稳定的内容（不可作为运动自由度）

- 外壳的银白透明膜面、连续球体轮廓、主体中心、半径和纵横比例。
- 内部青绿色总体积及其冷暖层次；不得变成均匀青色圆、灰色圆盘或纯雾团。
- 在本 still 微动态 milestone 内，冷色点在左上、暖色点在右下的对角关系保持稳定。点位的 core、glow 位置和相对色相不能随 still 内部流场漂移、翻转或变成按钮光点。
- 触摸命中区与视觉主体一致：中心和 `hitRadius` 不随帧变化，球外触摸不能改变状态。
- 资产图层顺序仍以 manifest 的 alpha-over 顺序为准；本 still-only milestone 不能引入外部管线、独立环带、网格或新装饰资产。
- 页面背景可替换但不能成为水球语义的一部分。

## 视觉运动层级

以下是用户应看到的三层关系，不是对具体资产层或 renderer pass 的一一规定：

1. **内部主体体积的质量迁移**：青绿色水体有缓慢的厚薄、压缩、拉伸和回流，仍被读成同一团水。
2. **内部密度边界与流动结构**：体积内部的明暗边界、密度带和雾化结构连续迁移，不能变成独立管线或 Logo。
3. **膜面与折射高光响应**：银白透明膜面只在轮廓内部做光学重分配，表现透射、遮蔽和折射变化，不单独跑出一条高光轨迹。

在本 still 微动态 milestone 内，点位中心固定在左上冷色 / 右下暖色位置；点位的 halo、折射边缘和局部亮度可以受附近水体影响，但点位本体不能随 still 内部流体外移。允许具有呼吸感的局部水体运动；呼吸感来自局部流动造成的质量压缩、拉伸、回流、密度变化、折射边界变化和光影厚度重新分配，不得实现为整个球体一起涨缩或统一 scale 动画。不同区域应有轻微时序差，外轮廓、中心、半径和命中区始终稳定。

本 still-only milestone 不采用球外轨迹或点位外移；未来 transitioning / moving 不由本条约束。moving 参考在本文件中只提供 still 微动态所需的内部连续流动、质量迁移和光学响应方向证据。

## 推荐的运动逻辑

在本 still-only milestone 内，实现可以采用共享流动逻辑、连续位移场或等价方案；本 brief 不冻结具体算法、方向、速度排序、固定相位差或 renderer pass。无论采用何种技术，结果必须让内部质量迁移统一，边界保持连续，膜面和折射高光对同一水体变化作出光学响应。不要把点位当作力源而移动点本身，不要让任何单层的运动取代整体水体运动。

`still` 的时间应从 0 开始、可挂起冻结、恢复只继续一次；它是未来 moving 的低幅视觉起点，而不是要求当前与 moving 使用同一套运行时实现。当前 milestone 不实现 `transitioning` 或 `moving`；本 still-only 实现不突然增加外部结构，未来切片的 transitioning / moving 外部 orbit elements 由 activation semantics 与 visual spec 单独管辖。`reset` 回到 still 的初始相位和稳定视觉。状态仍由状态机唯一授权，动画不能反向改变状态。

## 合成边界与实现建议

- 本 still-only milestone 优先在正式视觉范围内部做裁切位移/密度重分配；背景、外壳膜面和点位中心等稳定事实保持固定，再让水体内部的视觉投影响应同一运动逻辑。
- 本 still-only milestone 若使用 shader，输入应按视觉职责共享同一球体 mask；不得对整张静态合成图做无差别噪声扰动。shader 失败或设备不稳定时，可选择其他能保持相同视觉结果的确定性实现。
- 本 still 微动态切片中的动态视觉贡献必须受正式 still atlas 的 silhouette / outer-shell alpha mask 裁切；该规则只约束 still renderer，不定义 moving orbit elements 的像素范围。still 切片内任何像素不得越过正式外轮廓，不能用解析圆替代该视觉裁切权威。若实现使用几何变换，变换原点固定为 profile.center。
- 本 still-only milestone 不新增位图、Blender/Unity 资产或外部装饰。确认后的实现修改范围仅限运行时渲染适配器、still 微动态所需的局部参数/诊断及对应测试；不可修改正式 still PNG、manifest 的稳定几何与图层顺序、产品状态契约、Unity/Blender 旧参考或页面触摸语义。
- 实现应保留可观察接口，至少能读取当前状态、有效视觉时间、视觉就绪、中心、半径和命中区；这些诊断用于验证，不作为视觉设计依据。不要把“有效视觉时间”冻结成某个代码字段名。

## 正常页面验收（人眼证据优先）

当前 milestone 只覆盖：`reset → still ready → t0 → t2 → t4 → suspend → resume → reset`。`transitioning → moving` 移出当前切片；未来实现仍必须保持与本 brief 所述的视觉连续性，但不得把它写成当前切片已完成的事实。

在正常页面、正常背景和非 debug 模式下，沿真实路径进入页面并保持观察。运行时定义三个固定取样点：`VisualReady=true` 后视觉时间为 0 的首个稳定帧是 `t0`；有效视觉时钟达到 2.0 秒是 `t2`；达到 4.0 秒是 `t4`。`suspend` 必须冻结视觉时钟和画面，不累计后台时间；`resume` 从冻结点继续，不能跳过或重复累计；最终 `reset` 回到 still ready 和新的 `t0`。

记录同一页面的三个时刻：

- `t0`：加载完成、尚未触摸。球体应立即读成透明水球；外壳银白膜面、青绿色体积、左上冷点、右下暖点清晰，不能看到技术层或跳变。
- `t2`：约两秒。第一眼结构不变；持续观察可发现内部体积/流层发生柔和的连续位移或光影改变，运动主要在球内，点位仍像嵌入体积而非漂浮灯珠。
- `t4`：约四秒。运动方向和密度变化仍连贯，没有回环瞬跳、闪烁、白环、外露管线、整体漂移或轮廓呼吸失控；与 moving 参考的“内部水体在动”感相符，同时仍是同一个静止起始态。

验收必须同时完成真实页面进入、状态读取和视觉观察，覆盖上述当前 milestone。当前 milestone 不验证中心点击触发状态迁移，也不得为本 brief 新增 `still → transitioning`；球外触摸仅用于既有命中语义的回归保护，不能改变状态。挂起时钟和视觉冻结；恢复后只继续一次；reset 可重复回到 still。允许生成 t0/t2/t4 验证截图、日志和状态证据，但这些验证产物不得当作产品素材。`idlePhase`、帧数、像素差异、单张截图或“看起来像”都不能单独作为通过证据。缩略图检查仍需保留水球的透明体积、银白膜面、青绿色内部和两点对角关系。

## 三类稳定权威

- 正式 still atlas 的 silhouette 与 outer-shell alpha mask：负责动态像素视觉裁切，决定哪些像素可以显示在球体内。
- `profile.center` 与 `profile.radius`：负责坐标归一化和运动场定位，定义内部运动相对于球体的位置尺度。
- `hitRadius`：只负责交互命中，不参与像素裁切或运动场计算。

三者都必须稳定，任何一个都不能替代另外两个；视觉裁切不能用命中区推断，运动场不能改写轮廓，命中区也不能随动画漂移。

## 失败时必须换方案的规则

- 若连续两轮只改变 alpha、周期、blur 或单个高光位置仍读成“贴图在抖/高光在跑”，停止参数微调，改为统一流动逻辑/连续位移场 + 三层视觉关系的实现。
- 如果用户首先感知到高光/贴图在跑，而不是水在流，则判定失败；必须回到内部主体质量迁移、密度边界连续性和光学响应三层关系重新设计。
- 若外轮廓、中心或命中区出现可见位移，立即撤回几何变换，改为内部裁切位移；不得用反向位移补偿。
- 若出现白环、外露管线、独立高光斑、点位漂移或颜色整体漂移，关闭该层/该 pass 并回到稳定层固定、动态层受 mask 裁切的合成方案。
- 若正常页面在 `t0/t2/t4` 无法凭人眼辨认“内部在动”，不要用加大透明度或速度硬救；更换为可观察的中尺度体积/流层运动，并保持低幅慢速。
- 若 shader 在目标环境不可用、帧率不稳或诊断状态与视觉时间脱节，切换到确定性的 Canvas 分层实现；产品语义和资产边界不随工具改变。
- 若本 still-only milestone 的视觉差异只能通过新增外部结构表达，判定方案失败，回到内部流动和光影重分配；这不裁决未来 moving 的 orbit / attached trail 语义。

## 明确不做

- 待确认阶段不修改运行时代码或资产，不生成新的验证证据；确认后的 Luna 实现阶段按“修改范围”执行，并允许生成 t0/t2/t4 验证截图、日志和状态证据，但这些产物不得当作产品素材。
- 不修改正式 still PNG、`composite_manifest.json` 的顺序/几何，不替换银白透明外壳、青绿色体积或点位颜色关系。
- 不恢复或采用旧 Blender/Unity moving 结果作为产品目标，不把历史 render、debug 材质或 shaderDebug 画面当验收图。
- 本 still-only milestone 不引入实时流体物理、粒子、后处理、复杂 3D、外部环带、绳状曲线、Logo 化 S/太极结构或强 Bloom。
- 不用 `idlePhase`、帧数、像素差异或单张截图替代正常页面的人眼 t0/t2/t4 证据；当前 milestone 不宣称 moving 通过，也不在没有真实状态读取和视觉证据时宣称 still 微动态通过。

## 一致性裁定

- **scope**：待确认阶段只改本 brief；确认后的 Luna 阶段严格按“修改范围”执行，验证产物不进入产品素材。
- **authority**：状态机、正式 still atlas 的 silhouette / outer-shell alpha mask、`profile.center` / `profile.radius` 与 `hitRadius` 的职责彼此独立；动画不得反向改变状态或稳定几何。
- **state**：当前 milestone 只覆盖 still 的 reset、挂起、恢复和可重复观察；不验证中心点击触发迁移，不新增 `still → transitioning`，球外触摸仅作既有命中语义回归保护；`transitioning → moving` 未实现且移出本切片。
- **time**：统一使用“有效视觉时间”描述 t0/t2/t4 及挂起/恢复行为，不冻结任何代码字段命名；`idleTime/idlePhase` 仅作为当前失败原因，不作为验收事实来源。
- **validation**：通过条件必须同时有真实页面路径、状态读取和视觉观察；允许生成 t0/t2/t4 截图、日志和状态证据，但它们不是产品素材，单张截图或“看起来像”不能单独通过。

裁定：本 brief **FROZEN / READY_FOR_LUNA_IMPLEMENTATION**。
