# MindIsle 水球交互与运动语义 brief

**Status: DRAFT / SEMANTIC_LOCK_PENDING**  
**范围：只锁定 ProductState、InteractionVisualState、输入语义、运动连续性、生命周期和验收边界；不进入实现。**

## 1. 文档定位与继承关系

本 brief 定义 frozen still 之后的“激活与运动”语义。它不修改 [`docs/tasks/waterball-still-motion-brief.md`](waterball-still-motion-brief.md)，不把当前 Web、Unity、Blender 或历史 moving 结果提升为产品权威，也不冻结具体代码字段、算法、duration、easing、渲染器或资产制作方式。

本 brief 必须继承：

- `still → transitioning → moving` 和 `reset → still` 的 ProductState 契约；
- frozen still 的 silhouette、主体中心、半径、hitRadius、银白透明膜面、青绿色体积及左上冷点 / 右下暖点身份；
- `state-ball-visual-spec.md` 对透明体积、内部流动、稳定触摸范围和禁用项的约束；
- suspend 时冻结有效视觉时间，resume 从冻结点继续，reset 回到初始静止视觉的生命周期原则。

## 2. 仓库当前事实（FACT）

### 2.1 正式产品与资产事实

- 产品文档只承认 `still`、`transitioning`、`moving` 三个 ProductState；moving 再次触摸回到 still 尚未裁决。
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

- `still`：尚未激活，或当前保持安静；
- `transitioning`：从正式 still pose 连续增强到 moving；
- `moving`：专注运动持续进行。

`clear-still`、`press`、`still pose`、`still-pose crossing` 都不是 ProductState。

### 3.2 InteractionVisualState

- `clear-still`：`ProductState=still` 下的默认未点击视觉；是 frozen still 的更清透、更平静版本。
- `press`：`ProductState=still` 下 pointer 按下且手势尚未提交或取消；表达手指正在按住这一团水。
- `still pose`：有效点击提交后的正式 frozen still 构型；是激活后的瞬时视觉基准，不是新的 ProductState。
- `transitioning`：`ProductState=transitioning` 下，从 still pose 连续增强内部质量迁移、密度边界、局部压缩 / 拉伸和光学响应。
- `moving`：`ProductState=moving` 下的持续、单向、逆时针周期运动。
- `still-pose crossing`：`ProductState=moving` 内每圈经过的周期关键构型；画面接近 still pose，但不回到 still，也不重置 phase。

## 4. clear-still 语义

clear-still 必须仍然读成同一颗水球的安静起始态：

- 保持 frozen still 的 silhouette、中心、半径、hitRadius、银白透明膜面、冷暖点 identity 与整体水球语言；
- 减弱中央青绿色密度、内部水体存在感、密度边界、折射起伏和微动态显著度；
- 弱化明显中心凹陷，但不引入另一套轮廓或另一颗球；
- 目标感受是“水还在，只是更安静、更清透”。

clear-still 不通过整体缩放、整体漂移、点位移出或新外部装饰表达。

## 5. press 与有效点击

### 5.1 press

`pointerDown` 在 hitRadius 内时进入 press，ProductState 仍为 `still`。press 可以有轻微局部膜面、水体和折射响应，但必须保持 silhouette、中心、半径和 hitRadius 不变。

### 5.2 有效点击

一次有效点击不要求长按：

```text
pointerDown inside
→ press
→ pointerUp inside
→ activation committed
→ still pose
→ transitioning
→ moving
```

提交只发生一次。`still pose` 直接继承 frozen still 的微动态语言、有效视觉时间、reset / suspend / resume 语义、silhouette、center、radius、hitRadius 和冷暖点身份。

### 5.3 取消与越界

- `pointerDown outside`：不进入 press，不改变 ProductState，保持 clear-still。
- `pointerCancel`：不提交激活，平滑回到 clear-still。
- `pointerUp outside`：不提交激活，平滑回到 clear-still。
- 已进入 press 后拖出、再重新进入并释放：当前仓库没有既定语义，必须单独裁决，不得由实现默认补齐。

## 6. transitioning 语义

transitioning 表示同一团水从 still pose 连续增强到 moving。增强对象是内部质量迁移、密度边界变化、局部压缩 / 拉伸、折射与光学响应以及 moving 所需的点位运动。不能切换为另一套动画、另一颗球、外部水带或独立环带。

本 brief 不冻结 duration、easing、具体算法、采样频率或字段组织；这些选择不能改变连续性、权威边界和验收结果。

## 7. moving 语义

进入 moving 后 ProductState 持续保持 `moving`。运动满足：

- 持续、单向、逆时针、周期性向前推进；phase 只能按 `0 → 2π → 4π → 6π ...` 前进；
- 一个周期自然经历低幅 → 增强 → peak → 回落 → 再增强；回落是同一逆时针运动的幅度变化，不是反向或呼吸式倒放；
- 主体中心、主要 silhouette、尺寸和 hitRadius 保持稳定；主要变化发生在球体内部；
- 冷点 identity 始终为左上 canonical identity，暖点 identity 始终为右下 canonical identity；两点参与同一连续运动，轨迹不 teleport、不交换，不读成独立 UI 灯珠；
- 默认 moving 中点位及水体仍受正式 silhouette 内部裁切；若某个 moving 参考要求越过 silhouette，必须记录为 AUTHORITY DELTA。

## 8. STILL-POSE CROSSING

moving 每完成一圈时，冷暖点重新接近各自 still canonical position，内部水体密度重新接近 still 分布，膜面与折射关系重新接近 still pose。该构型命名为 **STILL-POSE CROSSING**。

crossing 期间及之后：

- ProductState 仍为 `moving`；
- moving phase 继续前进；
- 水体仍在运动，不反转、不 reset、不重新切动画；
- crossing 之后直接进入下一轮 moving rise。

因此视觉关系是：

```text
clear-still → press → still pose → transitioning → moving rise → moving peak → moving return → still-pose crossing → moving rise → ...
```

第一次 `still pose` 属于 ProductState=`still`；之后每圈的 `still-pose crossing` 只属于 ProductState=`moving` 内的周期构型。

## 9. 三类稳定权威

整个流程必须维持以下职责分离：

1. 正式 still silhouette / outer-shell alpha：负责视觉裁切；
2. `profile.center` / `profile.radius`：负责内部运动坐标与尺度；
3. `profile.hitRadius`：负责交互命中。

状态变化不得改变三者；命中区不能推导视觉裁切，运动坐标不能改写轮廓，视觉轮廓不能反过来改变命中区。

## 10. 时间与生命周期语义

- `clear-still → press → still pose → transitioning → moving` 必须连续；动画不能脱离真实 ProductState 自行播放。
- suspend 时冻结当前视觉、transition progress 和 moving phase；不补偿后台经过的时间。
- resume 从冻结位置继续，并且只恢复一次，不跳跃、不重复累计。
- reset 无论当前处于哪个 ProductState，都回到 `ProductState=still + InteractionVisualState=clear-still` 的初始视觉，并清除 transition progress 与 moving phase。
- STILL-POSE CROSSING 不触发 reset，不改变 ProductState，不清除 moving phase。
- 若挂起时尚未提交的 press 手势失去输入连续性，不得在恢复后补提交激活；该手势按取消处理，回到 clear-still。该规则是为避免后台输入补触发的低风险语义推导，具体实现字段不在本 brief 中冻结。

## 11. 结构化状态 / 输入表

| ProductState | InteractionVisualState | Event | Next ProductState | Next InteractionVisualState | Visual Result | Notes |
|---|---|---|---|---|---|---|
| `still` | `clear-still` | `pointerDown inside` | `still` | `press` | 局部轻微按压响应，轮廓、中心、半径、hitRadius 不变 | 不提交激活 |
| `still` | `clear-still` | `pointerDown outside` | `still` | `clear-still` | 无变化 | 外部误触不改变状态 |
| `still` | `press` | `pointerUp inside` | `still`（瞬时） | `still pose` | 恢复 frozen still 正式构型 | `activation committed`，随后进入 transitioning |
| `still` | `press` | `pointerUp outside` | `still` | `clear-still` | 平滑取消 press | 不触发 transitioning |
| `still` | `press` | `pointerCancel` | `still` | `clear-still` | 平滑取消 press | 不触发 transitioning |
| `still` | `press` | 拖出后重新进入再释放 | 未定 | 未定 | 不得由实现猜测 | PRODUCT DECISION REQUIRED |
| `still` | `still pose` | `activation committed` | `transitioning` | `transitioning` | 同一水体连续增强内部质量迁移与光学响应 | 不新增 ProductState |
| `transitioning` | `transitioning` | transition complete | `moving` | `moving` | 连续进入持续运动 | 不冻结 duration / easing |
| 任意 | 当前视觉态 | `suspend` | 不变 | 不变 | 当前画面、progress、phase 冻结 | 后台时间不补偿 |
| 任意 | 当前视觉态 | `resume` | 不变 | 不变 | 从冻结位置继续一次 | 不跳跃、不重复 |
| 任意 | 当前视觉态 | `reset` | `still` | `clear-still` | 回到 clear-still 初始视觉 | 清除 progress / phase |
| `moving` | `moving` | 一圈完成，接近 canonical positions | `moving` | `still-pose crossing` | 画面自然再次接近 still | 不 reset、不反转 |
| `moving` | `still-pose crossing` | crossing 后继续推进 | `moving` | `moving` | 直接进入下一轮 moving rise | phase 单调前进 |
| `moving` | `moving` | tap / pointerDown | `moving` | `moving`（未定） | 当前不定义再次触摸效果 | MOVING RE-TOUCH = DEFERRED / PRODUCT DECISION REQUIRED |

## 12. AUTHORITY DELTA

以下事项不能由本 brief 静默覆盖，必须在实现或 review 前显式处理：

1. 当前 Web renderer 的合成径向 mask、动态层变换和 WebGL pass 尚未证明等同于正式 still atlas 的 outer-shell alpha 裁切；若实现继续使用它们，必须先解决正式 silhouette authority delta。
2. Unity 原型中的外部 ribbons、独立点位轨迹与本 brief 的“点位嵌入同一水体、默认保持 silhouette 内”要求存在潜在冲突；Unity 结果只能作为实现事实，不能作为产品语义覆盖。
3. 若任何 moving 参考图要求水带、点位或高光越过正式 silhouette，必须以产品 visual spec 为准并记录差异。
4. 正式 manifest 当前仍写有 `moving_status: not implemented` 与 `visual_acceptance: pending_user_confirmation`；这说明资产状态和本语义 brief 的锁定状态不能互相替代。

## 13. PRODUCT DECISION REQUIRED

- 拖出后重新进入再释放：是否按“只要最终在内就提交”，还是按“连续按压轨迹不能离开命中区”；在裁决前不得实现默认行为。
- `MOVING RE-TOUCH`：moving 中再次点击是否保持 moving、暂停、回到 still，或触发其他语义；本轮保持 DEFERRED。
- reduced-motion：`transitioning` 与 `moving` 的具体视觉降级方式；若现有产品规范没有答案，保持 PRODUCT DECISION REQUIRED。

## 14. 与 frozen still / architecture baseline 的一致性

### 一致

- 保留三态 ProductState、reset → still、状态为唯一事实来源、动画为状态投影；
- 继承 frozen still 的 silhouette、center、radius、hitRadius、点位身份、裁切 authority 与 suspend / resume / reset 原则；
- moving 主要发生在球内，连续、缓慢、可重复，且不能通过外部装饰或整体缩放表达；
- 不改变正式 still brief，不把 Unity 或历史 moving 结果当作新的产品权威。

### 尚未一致但属于实现前阻塞事实

- 当前 Web runtime 尚未实现 pointer gesture、activation commit、transitioning、moving 或 moving crossing；
- 当前 Web runtime 的动态裁切实现尚未证明服从正式 atlas silhouette authority；
- 当前主流程的 `MindIsleSession` 定义未在仓库中找到；
- 正式 manifest 的 moving 与 visual acceptance 仍未完成产品确认。

这些是实现前必须带入 review 的事实，不在本 brief 中修复。

## 15. 语义验收边界

本 brief 在进入 FROZEN 前必须由 review 检查：

1. 任何输入都能映射到表中的真实状态转移，且外部误触、取消、越界释放不会误激活；
2. `still pose`、`transitioning`、`moving` 之间没有视觉跳变或第二颗球语义；
3. moving phase 单调前进，peak 后的回落不被读成反向运动；
4. 每圈的 STILL-POSE CROSSING 不会 reset、倒放或切换回 still；
5. 冷暖点 identity、轨迹连续性、正式 silhouette 裁切和 hitRadius 职责保持稳定；
6. suspend / resume / reset 对当前视觉、progress、phase 的结果可观察且可重复；
7. moving 再触摸、reduced-motion 和拖出重入释放仍明确标为未决，不被文案、按钮或动画暗示成已裁决。

## 16. 结论与后续门槛

本文件是 **DRAFT / SEMANTIC_LOCK_PENDING**。它完成交互与运动语义的候选锁定，不代表产品已经 FROZEN，也不代表任何 runtime、视觉或 Unity 验收通过。

下一步只能是 consistency review：逐项检查本 brief 与 frozen still、visual spec、architecture baseline、正式 manifest 和当前输入事实；review PASS 且上述 PRODUCT DECISION REQUIRED 完成后，才可将本文件标为 FROZEN，再进入 Sol Leader + Luna Worker 的实现阶段。
