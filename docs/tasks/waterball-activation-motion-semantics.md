# MindIsle 水球交互与运动语义 brief

**Status: SEMANTICS FROZEN**
**范围：只锁定 ProductState、InteractionVisualState、输入语义、运动连续性、生命周期和验收边界；不进入实现。**

## 1. 文档定位与继承关系

本 brief 定义 frozen still 之后的“激活与运动”语义。它不修改 [`docs/tasks/waterball-still-motion-brief.md`](waterball-still-motion-brief.md)，不把当前 Web、Unity、Blender 或历史 moving 结果提升为产品权威，也不冻结具体代码字段、算法、duration、easing、渲染器或资产制作方式。

本 brief 必须继承：

- `still → transitioning → moving` 的 ProductState 契约；旧 still-only slice 的 `reset → still` 事实仍然有效，但本流程在更高一层增加 `still` 下的 `clear` 子态；
- frozen still / still-pose 的 silhouette、主体中心、半径、hitRadius、银白透明膜面、青绿色体积及冷暖点 identity；clear-still 可以是更清透、更平静、更弱激活的独立视觉变体，不重新定义 frozen still；
- `state-ball-visual-spec.md` 对透明体积、内部流动、稳定触摸范围和禁用项的约束；
- suspend 时冻结有效视觉时间，resume 从冻结点继续，reset 将有效视觉时间归零并建立新的 clear-still t0；

## 2. 仓库当前事实（FACT）

### 2.1 正式产品与资产事实

- 产品文档只承认 `still`、`transitioning`、`moving` 三个 ProductState；当前切片规定 moving 再次触摸保持 moving 且无状态效果，未来 toggle 行为另行 deferred。
- 正式 still v1 是固定正面视角的 853×1844 RGBA 分层资产；manifest 定义 alpha-over 图层顺序，moving 状态在 manifest 中仍标为未实现。
- `profile.center = [426.5, 925]`、`profile.radius = 316`、`profile.hitRadius = 300`；`profile.gravity` 中冷点位于左上、暖点位于右下。
- frozen still brief 要求三类权威分离：正式 still atlas 的 silhouette / outer-shell alpha 负责视觉裁切，`profile.center` / `profile.radius` 负责内部运动坐标，`hitRadius` 只负责命中。

### 2.2 当前 Web 运行时事实

- `components/waterball/waterball.js` 构造时默认 `state = 'still'`，交互绑定在透明 button 的 `click` 事件；没有已实现的 `pointerDown → pointerUp → cancel` 手势阶段。
- 当前 `setState` 只接受 `still`；传入 `transitioning` 或 `moving` 会抛出错误。当前 `onActivate` 只派发命中事件并调用外部回调，不提交 ProductState 激活。
- 当前运行时有 `suspend`、`resume`、`reset` 和 `inspect()`，可读取 state、visualTime、hitRegion、center、radius、reducedMotion 与 lifecycle 计数；这些字段是现状证据，不是本 brief 要冻结的字段名。
- 当前 renderer 仍把静态合成图与动态层、WebGL material pass 叠加，并使用运行时生成的径向 mask；这与 frozen still 所要求的“正式 atlas silhouette / outer-shell alpha 作为动态视觉裁切权威”尚未形成一致证据。
- `waterball.html` 的当前回调只更新状态文案。`index.html` 试图把 session state 映射为 `still` / `moving`，但仓库中未发现 `MindIsleSession` 定义；该页面不能单独作为当前三态 Web runtime 已通过的证据。

### 2.3 Unity 及历史实现事实

- `unity/Assets/Scripts/MindIslePrototype.cs` 独立实现了三态枚举、中心命中、`transitioning → moving`、暂停与 reset；`OrbPreviewCheck.cs` 有相应编辑器检查。
- 该 Unity 实现使用自己的点位、轨迹和外部 ribbon 资源，属于并行实现与历史验证材料；它不能覆盖正式 still visual spec，也不能静默决定本 brief 的点位轨迹或外部结构。

## 3. ProductState 与 InteractionVisualState

### 3.1 ProductState

ProductState 继续只有：

- `still`：尚未激活，或当前保持安静；其 InteractionVisualState 只能是 `clear`、`press` 或 `activated`；
- `transitioning`：从正式 still-pose 连续增强到 moving；transitioning 的视觉语义由 ProductState 负责；
- `moving`：专注运动持续进行。

`clear-still` 是 `InteractionVisualState=clear` 的视觉名称；`press` 和 `activated` 是 `ProductState=still` 下的交互视觉子态；`moving-low`、`moving-rise`、`moving-peak`、`moving-ease` 是 `ProductState=moving` 内的视觉强弱阶段，不是额外的 ProductState 或 InteractionVisualState。

### 3.2 InteractionVisualState

- `clear`：`ProductState=still` 下的默认未点击子态；其视觉名称为 clear-still，是 frozen still / still-pose 的更清透、更平静、更弱激活版本。
- `press`：`ProductState=still` 下 pointer 按下且手势尚未提交或取消；表达手指正在按住这一团水。
- `activated`：`ProductState=still` 下由 pointerUp inside 原子提交产生的瞬时子态；视觉立即采用正式 still-pose，随后在同一提交的确定性连续中进入 transitioning，不产生第二个可重复触发事件。

transitioning 与 moving 只由 ProductState 表达；moving 内的 low / rise / peak / ease 只描述连续视觉阶段，不作为 InteractionVisualState 值。

## 4. clear-still 语义

clear-still 正式允许不同于 frozen still，但必须仍然读成同一颗水球的安静起始态：

- 保持同一 silhouette identity、中心、半径、hitRadius、银白透明膜面语言、冷暖点 identity 与整体水球语言；
- 冷点仍嵌在左上 canonical position 附近，暖点仍嵌在右下 canonical position 附近；两者属于水球视觉系统，不表现为独立 UI 灯珠；
- 减弱中央青绿色密度、内部水体存在感、密度边界、折射起伏和微动态显著度；
- 弱化明显中心凹陷，但不引入另一套轮廓或另一颗球；
- 目标感受是“水还在，只是更安静、更清透、更少被激活”；
- frozen still 不因 clear-still 而重新定义；正式 still-pose 仍直接继承 frozen still。

clear-still 不通过整体缩放、整体漂移、点位移出或新外部装饰表达。它的差异只能体现在允许的清透度、密度、折射和微动态弱化上。

## 5. press 与有效点击

### 5.1 press

`pointerDown` 在 hitRadius 内时进入 press，ProductState 仍为 `still`。press 可以有轻微局部膜面、水体和折射响应，但必须保持 silhouette、中心、半径和 hitRadius 不变。
press 期间两个点仍嵌在水球内部并保持各自 canonical identity；允许附近水体对 halo、折射边缘和局部亮度产生轻微影响，但不得开始球外轨迹。

### 5.2 有效点击

一次有效点击不要求长按：

```text
pointerDown inside
→ press
→ pointerUp inside + activation commit（原子提交）
→ activated / still-pose
→ transitioning
→ moving
```

`pointerUp inside` 与 activation commit 是同一次原子状态提交，提交只发生一次；不得把它们拆成两个可重复触发的产品事件。`activated` 只表达这一原子提交的瞬时 still 子态，正式视觉直接继承 frozen still 的 still-pose、微动态语言、silhouette、center、radius、hitRadius 和冷暖点 identity；在进入 transitioning 前，冷点仍位于左上 canonical position 附近，暖点仍位于右下 canonical position 附近并嵌在主体水体内。

### 5.3 取消与越界

- `pointerDown outside`：不进入 press，不改变 ProductState，保持 clear-still。
- `pointerCancel`：不提交激活，平滑回到 clear-still。
- `pointerUp outside`：不提交激活，平滑回到 clear-still。
- pointerDown inside 后，只要本次 gesture 曾离开 hitRadius，本次 press 立即失效并回到 `ProductState=still + InteractionVisualState=clear`；之后即使重新进入并 pointerUp inside，也不提交 activation，必须重新 pointerDown inside。

## 6. transitioning 语义

transitioning 表示同一团水从 still-pose 连续增强到 moving。增强对象是内部质量迁移、密度边界变化、局部压缩 / 拉伸、折射与光学响应以及 moving 所需的点位运动。随着 transitioning 推进，冷暖点逐渐离开各自 canonical position，向主体边界运动，可以连续穿过主体 silhouette 并进入球体外围轨迹；这一过程不得 teleport，也不得突然切换为另一套动画、另一颗球、外部水带或独立环带。主体 silhouette、center、radius 和 hitRadius 始终稳定，只有两个 core 及其直接关联的受控流体响应可以越过主体 silhouette。

本 brief 不冻结 duration、easing、具体算法、采样频率或字段组织；这些选择不能改变连续性、权威边界和验收结果。

## 7. moving 语义

进入 moving 后 ProductState 持续保持 `moving`。运动满足：

- 持续、单向、逆时针、周期性向前推进；phase 只能按 `0 → 2π → 4π → 6π ...` 前进；
- 一个周期自然经历低幅 → 增强 → peak → 回落 → 再增强；回落是同一逆时针运动的幅度变化，不是反向或呼吸式倒放；
- 主体中心、主要 silhouette、尺寸和 hitRadius 保持稳定；主体水体的主要变化发生在球体内部，球外变化仅限于 core 及其直接关联的受控流体响应；
- still / clear-still 中，冷点 canonical position 是左上，暖点 canonical position 是右下；
- transitioning / moving 中，两个 core 本体允许参与同一逆时针连续运动；halo、refraction response 和轻量水膜 / 水墨拖尾从属于各自 core，并随 core 连续变化；
- 冷暖 identity 始终不交换，轨迹不 teleport；两个 core 可以暂时位于主体 silhouette 外并沿球外轨迹环绕，但不得成为独立装饰物；主体 silhouette 与 hitRadius 不因球外 orbit elements 扩大；
- moving 同时包含持续的角向运动和径向距离变化：角向 phase 始终逆时针向前；moving-ease 时两个 core 随连续轨迹缓慢靠近主体，进入下一段 moving-rise 时再缓慢远离，形成非同步整体缩放式的呼吸感；径向变化不得造成反向、teleport、phase reset 或 ProductState 改变；
- canonical position 只表示 still / clear-still / press / still-pose 中的静止归位位置，以及未来明确 moving → still 停止流程的归位目标；moving 周期不要求、也不得周期性回到这些位置。

moving 的强弱阶段统一称为：

```text
moving-low → moving-rise → moving-peak → moving-ease → moving-rise → ...
```

这些阶段全部属于 ProductState=`moving`。`moving-ease` 的“靠近主体”不是 still-pose，也不是停止；下一段 `moving-rise` 会在 phase 继续前进的同时再次逐渐远离主体。

### 7.1 reduced-motion

reduced-motion 是产品级语义降级，不改变状态机：

- 状态迁移逻辑保持一致，`clear`、`press`、`activated`、transitioning 和 moving 仍可被识别；
- 不依赖持续明显运动来表达状态；
- transitioning / moving 使用显著降低或取消持续运动的视觉表现，但仍保留状态可识别的静态或短暂差异；
- reset / suspend / resume 语义保持一致；
- 本 brief 不冻结具体 shader、duration、easing 或视觉参数。

## 8. moving 周期与未来 stop-return

moving 每完成一圈只表示 orbit phase 继续向前进入下一圈。冷暖点不会因为完成一圈而回到 still canonical positions，也不会重新成为 still 构型；它们保持同一逆时针方向继续前进。moving 的连续视觉关系是：

```text
clear-still → press → still-pose → transitioning → 光点离开主体 → moving
moving-low → moving-rise → moving-peak → moving-ease → moving-rise → ...
```

只有未来产品明确发生停止时，才允许进入归位流程：

```text
moving → stop / return transition（仅为未来流程占位，不是 ProductState）→ 逆时针运动持续减弱
       → orbit 半径逐渐收敛 → 两点重新进入水球
       → 回到各自 canonical positions → still
```

归位必须是连续减弱和连续收敛，不得倒放 moving、reverse、rewind、phase reset、renderer reset 或 teleport。`stop / return transition` 不是第四个 ProductState；停止触发条件及其未来状态映射本轮保持 `DEFERRED`，不新增停止手势或状态迁移。

## 9. 三类稳定权威

整个流程必须维持以下职责分离：

1. 正式 still silhouette / outer-shell alpha：负责视觉裁切；
2. `profile.center` / `profile.radius`：负责内部运动坐标与尺度；
3. `profile.hitRadius`：负责交互命中。

状态变化不得改变三者；命中区不能推导视觉裁切，运动坐标不能改写主体轮廓，视觉轮廓不能反过来改变命中区。正式 still silhouette / outer-shell alpha 是主体水球的视觉边界，不等同于 moving orbit elements 的像素范围；moving 中的 cold/warm core 及其直接关联的受控流体尾迹可以暂时位于主体 silhouette 外，但不扩大 hitRadius，也不改变主体 silhouette 的稳定性。

## 10. 时间与生命周期语义

- `clear-still → press → activated / still-pose → transitioning → moving` 必须连续；动画不能脱离真实 ProductState 自行播放。
- suspend 时冻结当前视觉、transition progress、moving phase 和有效生命周期时间；不补偿后台经过的时间。
- 如果 suspend 发生在尚未提交的 press：立即按 pointerCancel 处理，ProductState 保持 `still`，InteractionVisualState 回到 `clear`，取消本次 gesture，然后冻结生命周期时间；resume 后保持 clear-still，不恢复已失去输入连续性的 press。
- 其他 ProductState 继续遵循正常 suspend / resume 冻结语义，resume 从冻结位置继续一次，不跳跃、不重复累计。
- reset 无论当前处于哪个 ProductState，都回到 `ProductState=still + InteractionVisualState=clear`，有效视觉时间归零并建立新的 clear-still t0；transitionProgress 与 movingPhase 同时回到确定性初始值。
- 旧 still-only slice 中 `reset → still t0` 的事实仍然有效；本流程只在更高一层交互语义中增加 clear 子态，不回写或重新定义 frozen still。
- moving 周期边界不触发 reset，不改变 ProductState，不清除 moving phase；只有未来明确的 stop-return 流程才允许 moving → still。

## 11. 结构化状态 / 输入表

| ProductState | InteractionVisualState | Event | Next ProductState | Next InteractionVisualState | Visual Result | Notes |
|---|---|---|---|---|---|---|
| `still` | `clear` | `pointerDown inside` | `still` | `press` | 局部轻微按压响应，轮廓、中心、半径、hitRadius 不变 | 不提交激活 |
| `still` | `clear` | `pointerDown outside` | `still` | `clear` | 无变化 | 外部误触不改变状态 |
| `still` | `press` | `pointerUp inside + activation commit`（原子提交） | `still` | `activated` | 立即采用 frozen still 的 still-pose | 不拆成两个可重复产品事件；随后在同一确定性连续中进入 transitioning |
| `still` | `activated` | 同一原子提交的连续交接（非新输入事件） | `transitioning` | — | 从 still-pose 连续增强内部质量迁移与光学响应 | transitioning / moving 不使用 InteractionVisualState 值 |
| `still` | `press` | `pointerUp outside` | `still` | `clear` | 平滑取消 press | 不触发 transitioning |
| `still` | `press` | `pointerCancel` | `still` | `clear` | 平滑取消 press | 不触发 transitioning |
| `still` | `press` | `pointerMove outside` | `still` | `clear` | 本次 gesture 失效并回到 clear | 之后重新进入不能复活本次 press，必须重新 pointerDown inside |
| `still` | `clear` | 曾离开 hitRadius 后 `pointerUp inside` | `still` | `clear` | 不提交 activation | 需要新的 pointerDown inside |
| `transitioning` | — | 任意完整 pointer gesture（down/up/cancel/drag） | `transitioning` | — | no state effect | 不进入 press，不产生 activation，不重启 transition |
| `transitioning` | — | transition complete | `moving` | — | 连续进入持续运动 | 不冻结 duration / easing |
| 任意 | 当前 still 子态或 — | `suspend` | 不变 | 不变；press 时按 pointerCancel 回到 `clear` | 当前画面、progress、phase 和生命周期时间冻结 | 后台时间不补偿 |
| 任意 | 当前 still 子态或 — | `resume` | 不变 | 不变；取消的 press 不恢复 | 从冻结位置继续一次 | 不跳跃、不重复 |
| 任意 | 当前 still 子态或 — | `reset` | `still` | `clear` | 有效视觉时间归零，建立新的 clear-still t0 | transitionProgress / movingPhase 回到确定性初始值 |
| `moving` | — | orbit phase 完成一圈并进入下一圈 | `moving` | — | moving-low / moving-rise 等强弱阶段继续；光点不回到 canonical positions | phase 单调前进，不 reset、不反转 |
| `moving` | — | moving-ease → 下一段 moving-rise | `moving` | — | 光点先缓慢靠近主体，再缓慢远离；角向运动持续逆时针 | 径向变化不改变 ProductState，不 reset phase |
| `moving` | — | 任意完整 pointer gesture（down/up/cancel/drag） | `moving` | — | no state effect | 不进入 press，不改变状态，不暂停，不回 still，不反转，不 reset phase；未来 toggle 行为 DEFERRED |

## 12. AUTHORITY DELTA

以下事项不能由本 brief 静默覆盖，必须在实现或 review 前显式处理：

1. **clear-still 与 frozen still 的视觉差异**：clear-still 正式允许比 frozen still / still-pose 更清透、更平静、更弱激活；frozen still 仍只作为 activated still-pose 的既有视觉基准，不能被 clear-still 回写或重新定义。
2. 当前 Web renderer 的合成径向 mask、动态层变换和 WebGL pass 尚未证明等同于正式 still atlas 的 outer-shell alpha 裁切；若实现继续使用它们，必须先解决正式 silhouette authority delta。
3. Unity 原型中的外部 ribbons、独立点位轨迹与本 brief 的“球外元素必须从属于冷暖 core、连续附着并随 moving 轨迹自然变化”要求存在潜在冲突；Unity 结果只能作为实现事实，不能作为产品语义覆盖。
4. moving 参考图中的独立水带、固定环带、Logo 化弧线或与光点无关的外部结构仍不是产品权威；只有由冷暖 core 脱离、环绕和回归自然产生的受控流体尾迹可以被继承。
5. 正式 manifest 当前仍写有 `moving_status: not implemented` 与 `visual_acceptance: pending_user_confirmation`；这说明资产状态和本语义 brief 的锁定状态不能互相替代。

## 13. PRODUCT DECISION REQUIRED

当前无剩余、会阻塞本轮语义冻结的 PRODUCT DECISION REQUIRED。

- moving 中再次点击在当前切片已裁决为 `moving → moving` 且 no state effect；未来 toggle 行为保持 DEFERRED，作为后续产品扩展，不阻塞本 brief。
- moving → still 的停止触发条件保持 DEFERRED；本 brief 只锁定未来一旦停止，归位必须沿原逆时针运动连续减弱并收敛，不新增停止手势或状态迁移。
- reduced-motion 的产品级状态语义已锁定；具体 shader、duration、easing、幅度和参数仍属于实现选择，不在本 brief 中冻结。

## 14. 与 frozen still / architecture baseline 的一致性

### 一致

- 保留三态 ProductState、状态为唯一事实来源、动画为状态投影；旧 still-only slice 的 reset → still 事实与本流程的 reset → still + clear 分层关系已明确；
- 继承 frozen still / still-pose 的 silhouette、center、radius、hitRadius、点位 identity、裁切 authority 与 suspend / resume 原则；clear-still 的视觉差异已单独记录为 authority delta；
- 主体水体运动主要发生在球内，连续、缓慢、可重复；冷暖 core 及其直接关联的受控流体响应可以暂时位于球外，但不能演变为独立外部装饰或整体缩放；
- 不改变正式 still brief，不把 Unity 或历史 moving 结果当作新的产品权威。

### 尚未一致但属于实现前阻塞事实

- 当前 Web runtime 尚未实现 pointer gesture、activation commit、transitioning、moving 或 moving 的 orbit / radial cycle；
- 当前 Web runtime 的动态裁切实现尚未证明服从正式 atlas silhouette authority；
- 当前主流程的 `MindIsleSession` 定义未在仓库中找到；
- 正式 manifest 的 moving 与 visual acceptance 仍未完成产品确认。

这些是实现前必须带入 review 的事实，不构成语义 brief 的内部冲突，也不在本 brief 中修复。

## 15. 语义验收边界

本 brief 在进入 FROZEN 前必须由 review 检查：

1. 任何输入都能映射到表中的真实状态转移，且外部误触、取消、越界释放不会误激活；
2. `clear-still`、`press`、`activated`、`transitioning`、`moving` 之间没有视觉跳变或第二颗球语义；
3. moving phase 单调前进，peak 后的回落不被读成反向运动；
4. moving 每圈只推进 orbit phase，不回到 canonical positions，不产生 still 构型；moving-low / moving-rise / moving-peak / moving-ease 均保持 ProductState=`moving`；
5. 冷暖点 identity、逆时针轨迹连续性、径向远近变化、主体 silhouette 稳定性、球外 orbit elements 的附着关系和 hitRadius 职责保持稳定；
6. suspend / resume / reset 对当前视觉、有效视觉时间、progress、phase 的结果可观察且可重复；
7. moving 再触摸保持 moving 且 no state effect；reduced-motion 保持状态迁移但降低或取消持续运动；拖出后重入释放不能复活原 gesture；
8. moving 周期统一使用 `moving-low`、`moving-rise`、`moving-peak`、`moving-ease`；`still-pose` 只用于 still 下的静止构型和未来 stop-return 的目标构型；InteractionVisualState 只使用 `clear`、`press`、`activated`。

## 16. consistency-only review

- **状态分层**：PASS。ProductState 只包含 `still`、`transitioning`、`moving`；InteractionVisualState 只表达 `still` 下的 `clear`、`press`、`activated`。
- **原子激活**：PASS。`pointerUp inside + activation commit` 是一次原子提交，`activated` 只是该提交的瞬时 still 子态，不存在第二个可重复产品事件。
- **取消与拖出**：PASS。pointerCancel、pointerUp outside、曾离开 hitRadius 的 gesture 都回到 clear；重新进入后必须重新 pointerDown inside。
- **transitioning / moving 输入**：PASS。transitioning 与 moving 中完整 pointer gesture 均为 no-op，不进入 press、不产生 activation、不重启 transition、不改变 moving phase。
- **生命周期**：PASS。press+suspend 立即按 pointerCancel 处理；reset 明确产生新的 clear-still t0，并归零有效视觉时间、transitionProgress、movingPhase。
- **运动连续性与点位 authority**：PASS。moving phase 单调前进，moving-ease 到下一段 moving-rise 时径向距离连续变化但不反向、不 reset；产品视觉规格已吸收冷暖 core 的同一逆时针连续轨迹、主体 silhouette 稳定、core 与受控尾迹可暂时球外、identity 不交换和 canonical position 仅作为静止/停止归位目标的语义。
- **reduced-motion**：PASS。状态迁移不变，视觉运动降低或取消，reset / suspend / resume 不变。
- **阻塞检查**：无 BLOCKER；无 MAJOR 内部语义冲突。剩余 authority delta 和 runtime 未实现项属于后续实现 / visual spec gate，不改变本 brief 的语义结论。

## 17. 结论与后续门槛

本文件已通过 consistency-only review，状态为 **SEMANTICS FROZEN**。这只冻结本 brief 的交互与运动语义，不代表 runtime、视觉资产或 Unity 验收通过。

下一步可以进入实现前的独立 authority / runtime gate：处理文档中列出的 AUTHORITY DELTA，并以真实输入、状态读取和视觉证据验证实现；不得回写 frozen still 或用实现现状改变本 brief。
