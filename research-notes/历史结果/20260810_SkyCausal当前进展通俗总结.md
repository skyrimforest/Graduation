# SkyCausal 当前进展通俗总结（纠正版）

日期：2026-08-10

状态：六 profile `T=1` 基线已完成独立确认；Two-Stage 基础设施已通过
freeze validation，但 pilot 尚未执行；开放式、多轮 solver orchestration 尚未完成。

## 纠正说明

本文替换同日早先版本。早先版本把“固定六 profile 的 Root Search”误写成项目最终
方法，并据此判断“主论文核心实验已经完成”。这个判断不符合 workspace 中已经冻结
的研究材料。

正确口径是：

```text
固定六 profile Root Search
  = 已完成的 T=1 阶段基线和基础证据
  != 永久封闭的 action space
  != 完整 Dynamic Algorithm Configuration
  != 项目最终的动态 solver orchestration
```

v2.1 的正式正结果仍然有效，但必须严格限定在这一级证据内。

## 一、项目真正要解决什么

SkyCausal 面向动态 FJSP-MAPF 制造系统：

- FJSP 决定工序在哪台机器、什么时间加工；
- Assigner 决定运输任务由哪台 AGV 执行；
- MAPF 为多台 AGV 规划无碰撞路径；
- 机器故障、拥堵和执行偏差会不断改变后续决策条件。

早期第一性原理材料指出，传统单向链路
`FJSP -> Assigner -> MAPF` 会产生三类耦合损失：

```text
距离盲区：调度只看加工，不看运输距离和时间；
时序错位：计划到达时间与真实运输时序不一致；
拥堵聚集：调度集中释放任务，造成局部路网冲突。
```

因此，研究目标从来不只是“从六个固定组合中选一个”，而是让系统根据当前物理状态、
当前可行解、solver 搜索进展和剩余计算预算，动态管理求解过程。

长期目标是多轮决定：

```text
continue：继续当前 solver；
switch：切换到另一个 solver；
combine：组合不同 solver 或组件的结果；
adjust：调整参数、范围或预算；
commit：提交当前最好且物理可行的方案。
```

同时必须满足 hard deadline、物理安全、资源清理和原子提交约束。

## 二、研究路线应分成四层

### 2.1 原始问题层：闭环耦合与状态依赖适配

早期材料提出了三类方向：

```text
运输感知 FJSP
学习型 Assigner
状态依赖的规则切换、多专家融合和组合外泛化
```

这条路线强调 FJSP、Assigner 和 MAPF 之间的信息反馈，以及固定规则无法适配所有
状态。它说明项目的出发点就是动态适配，而不是固定六选一。

这些方向目前不能统一写成“已经完成”。特别是学习型 Assigner、多专家融合和组合外
泛化仍属于早期研究计划或待验证分支。

### 2.2 基础证据层：六 profile `T=1` Root Search

为了先回答一个更基础的问题，项目冻结了六个联合 profile：

| Profile | FJSP | MAPF |
|---|---|---|
| CP-SAT+EECBS | CP-SAT | EECBS |
| CP-SAT+LG-LaCAM | CP-SAT | LG-LaCAM |
| DE+EECBS | DE | EECBS |
| DE+LG-LaCAM | DE | LG-LaCAM |
| PSO+LG-LaCAM | PSO | LG-LaCAM |
| PSO+MAPF-LNS2 | PSO | MAPF-LNS2 |

它们是为了验证：

1. 不同状态下是否真的存在不同赢家；
2. solver portfolio 是否有可利用的 headroom；
3. 能否在同一个 snapshot 上做公平、可复现的反事实比较；
4. deadline、取消、fallback 和资源清理能否可靠工作。

当前方法在同一个事件决策点上，对六个 profile 各做一次 terminal rollout，然后选择
最小 heldout cost 对应的 profile。它的准确定位是：

```text
T = 1
event-level static algorithm selection
deadline-safe shadow execution baseline
```

这里的 `T=1` 指只在当前事件点做一次 profile 选择，不代表 rollout 只运行一个物理
步。每个 rollout 仍会模拟到生产终止。

### 2.3 过渡机制层：Two-Stage Solver Switching

Two-Stage 不再只问“当前选谁”，而是验证：

```text
solver A 先运行到 T1
-> 导出经过认证的 portable incumbent
-> solver B 在剩余 wall-clock budget 内继续
-> 比较 warm switch、cold switch 和不中断基线
```

首批候选是：

```text
DE -> CP-SAT
PSO -> CP-SAT
```

它验证的核心不是“两阶段一定更好”，而是：

- 是否能观察 solver progress trajectory；
- 是否能在安全边界 cooperative stop；
- 是否能导出与导入公开、可审计的 incumbent；
- warm switch 是否优于 cold switch；
- 切换是否优于让 A 或 B 独占完整预算；
- 所有比较是否使用同一个端到端 wall-clock budget。

### 2.4 最终目标层：开放式、多轮 solver orchestration

最终控制器不应绑定固定六个联合 profile，也不应绑定某个 MCTS、RL 或 BNN。

稳定系统边界是 `DecisionBackend`：

```python
class DecisionBackend:
    def decide(
        self,
        decision_state,
        legal_actions,
        solver_portfolio,
        budget,
    ) -> Decision:
        ...
```

规则、MCTS、GNN、PPO、Offline RL 或混合方法都只是可替换后端。动作应从固定 profile
扩展为带生命周期的 solver option，至少包含：

```text
initiation condition
solver/component and parameters
budget and scope
termination condition
export and cleanup semantics
```

由于制造动作和求解 option 的持续时间不同，长期问题更接近 constrained SMDP 或
options framework，而不是固定一步的普通分类问题。

### 2.5 对未来 FJSP/MAPF solver 开放是硬要求

这里的“开放”不能只理解为以后手工增加更多联合 profile。即使把六个扩成二十个，
只要 controller 仍依赖固定候选名称和固定分类输出，系统仍然是封闭的。

长期架构必须保证：

```text
新 solver 通过版本化 manifest 和 adapter 注册；
每个 solver 自带 config schema，不修改中央参数白名单；
capability 决定它能否 start / observe / continue / warm switch；
solver + config + budget + scope + transition 共同生成 SolverOption；
controller 对动态候选逐项打分，不使用固定 N 类 softmax；
FJSP 与 MAPF 通过 proposal contract 条件组合，不维护完整笛卡尔积；
新增 solver 先 contract/shadow validation，再进入正式 portfolio。
```

在线选择采用分层候选生成：

```text
capability filter
-> state-aware top-K retrieval
-> short probe
-> gray-box racing / successive halving
-> continue / switch / commit
```

六 profile 文件只保留为 legacy reproducibility baseline，不能继续扩展成长期运行时
catalog。完整代码审计、前沿调研、数据契约和实施路线见：

[`20260810_开放式FJSP_MAPF求解器Portfolio前沿调研与架构方案.md`](20260810_开放式FJSP_MAPF求解器Portfolio前沿调研与架构方案.md)。

## 三、六 profile 结果到底证明了什么

正式 artifact：

```text
artifacts/skycausal_publication_confirmation_v2_1_09760697/
```

v2.1 在 40 个独立 cluster 上得到：

```text
Root mean heldout cost：             459.825
Global best fixed mean cost：        483.400
Absolute mean improvement：           23.575
Relative mean reduction：               4.88%
95% stratified-bootstrap CI：      [8.625, 46.325]
Formal status：          FORMAL_CONFIRMATION_PASS
```

安全证据包括：

```text
component stress：                  600/600 PASS
Root normal stress：                 25/25 PASS
Root forced-deadline stress：        25/25 PASS
final active remote requests：           0
final MAPF sessions：                    0
physical violations：                    0
```

因此可以声称：

1. 在冻结的实例、地图、故障类型、六 profile 和 deadline policy 下，portfolio 存在
   显著选择价值；
2. `T=1` Root Search 优于该 cohort 上的全局最佳固定 profile；
3. hard deadline 下的不完整搜索可以安全 fallback；
4. 同源 snapshot、paired evaluation、failure-as-cost 和清理审计已经形成可信基础。

但不能据此声称：

1. 六个 profile 是完整或永久的 action space；
2. 系统已经能动态生成新的 solver option；
3. 系统已经根据中途进展多轮 continue、switch、combine 或 adjust；
4. Two-Stage 或任意多轮 switching 已经提升质量；
5. 学习型 Assigner、RL、BNN 或因果控制器已经完成；
6. 结果已经跨规模、跨地图类型和跨扰动类型泛化。

## 四、为什么固定六种不够

固定六 profile 方案有明确边界：

1. 候选集合是人工冻结的，无法表达新的 solver、参数和预算；
2. 每个候选都做 terminal rollout，计算开销较大；
3. 每次事件只选择一次，不能利用 solver 中途的进展信息；
4. 不能表达“先用启发式快速找解，再用精确 solver 收紧”；
5. 联合 profile 同时改变 FJSP 和 MAPF，不能直接识别收益来自哪一侧；
6. 无法表示安全切换边界、warm-start 能力和 incumbent 可迁移性；
7. 不能直接推广成无条件 `6 x 6` switching matrix。

所以六 profile 实验的价值是建立地基，而不是封闭最终设计。

## 五、Two-Stage 当前真实状态

已经完成：

```text
solver orchestration contract
portable incumbent 与 native checkpoint 的类型分离
continue_run / cold_switch / warm_switch
absolute source cutoff 和剩余预算核算
cooperative stop 和 finalization reserve
DE/PSO -> CP-SAT warm-start smoke
不可变 freeze validation
```

freeze validation 结果：

```text
DE：        50/50 PASS
PSO：       50/50 PASS
CP-SAT：    50/50 PASS
合计：     150/150 PASS
```

尚未完成：

```text
pilot cohort snapshot manifest 捕获与审计
正式 pilot arm execution
warm vs cold 的质量比较
A full / B full / warm switch 的主 contrast
最终 pair 和 T1 选择
独立 confirmation
```

较新的 freeze result 将当前剩余 pilot blocker 记录为：

```text
pilot cohort snapshot manifest has not been captured and audited
```

因此，当前只能说 Two-Stage 机制和基础设施具备进入 pilot 的条件，不能说 switching
已经产生收益。

## 六、现有实现中哪些东西可以复用

六 profile 阶段留下的工程不是一次性工作。以下能力是动态 orchestration 的基础：

```text
可复现 snapshot 和 semantic signature
solver profile registry 和真实 activator
严格 end-to-end wall-clock accounting
远端 request prefix、targeted cancel 和 quiescence
MAPF session cleanup
physical invariant audit
failure-as-cost
immutable artifact provenance
paired planning / heldout evaluation
```

Two-Stage 新增的可复用能力包括：

```text
solver progress observation
cooperative finalization
portable incumbent bundle
warm-start compatibility
safe switch boundary
remaining-budget execution
```

这些才是从 `T=1` 基线走向多轮 options controller 的连续工程主线。

## 七、论文现在应怎样判断

需要区分两种论文范围。

### 7.1 严格收窄的阶段论文

如果论文只研究：

```text
deadline-safe counterfactual selection
within a frozen six-profile portfolio
```

那么 v2.1 已经提供可写的主结果。论文必须在标题、贡献和 limitations 中明确它是
`T=1`、冻结候选集和限定场景下的阶段性方法，不能包装成完整动态 solver controller。

### 7.2 符合长期目标的主论文

如果主论文要声称：

```text
dynamic solver orchestration
state/progress/budget-aware switching
multi-round solver options
```

那么现在还不能说核心实验完成。至少需要先完成 Two-Stage pilot，证明 warm switching
相对 cold、A full 和 B full 有受控收益，并完成物理时钟持续推进、提交时重验证和
完整在线 episode 实验。冻结 snapshot 的 Two-Stage pilot 只能提供切换机制证据，
不能单独证明在线动态 orchestration 成立。

因此，当前可以立即写不会变化的部分：

```text
问题定义
系统与物理约束
DecisionBackend / solver option 契约
deadline-safe execution
T=1 baseline 协议与结果
Two-Stage 实验设计
```

但不应立即把最终标题、摘要和核心贡献冻结为“固定六 profile Root Search”。

现有 `论文/article_skycausal_v2.tex` 仍对应更早的 BNN、因果效应和识别路线，也不能
直接作为当前任一范围的正式主稿继续扩写。

## 八、最合理的下一步

经在线要求复核，下一步不是继续增加固定 profile，也不是优先捕获更多冻结 snapshot，
而是：

1. 定义连续物理时钟、冻结执行前缀和提交时重验证契约；
2. 实现最小 online episode runner；
3. 用历史 development fixture 验证三时钟记账、计划新鲜度和 fallback；
4. 运行只验证基础设施的在线 pilot；
5. 再用受控 snapshot 校准短探测预算并比较逐轮淘汰与浅层 MCTS；
6. 把冻结后的分配器放回完整在线 episode；
7. 再扩展 FJSP-MAPF 分解组合、切换和新求解器开放接入；
8. 全部方法冻结后执行独立在线 confirmation。

论文实验章节以
[`20260811_SkyCausal论文实验设计章节结构_在线主实验修正版.md`](20260811_SkyCausal论文实验设计章节结构_在线主实验修正版.md)
为准。

## 九、关键材料入口

### 原始问题与早期路线

- [`../第一性原理.md`](../第一性原理.md)
- [`paper_positioning.md`](paper_positioning.md)
- [`research_roadmap.md`](research_roadmap.md)

### 动态 solver orchestration 设计

- [`20260804_可插拔求解器组合MCTS调度框架可行性调研.md`](20260804_可插拔求解器组合MCTS调度框架可行性调研.md)
- [`20260804_DecisionBackend与学习后端演进协议.md`](20260804_DecisionBackend与学习后端演进协议.md)
- [`20260806_SkyCausal_TwoStageSolverSwitching实验协议.md`](20260806_SkyCausal_TwoStageSolverSwitching实验协议.md)

### `T=1` 正式结果

- [`../artifacts/skycausal_publication_confirmation_v2_1_09760697/publication_report.md`](../artifacts/skycausal_publication_confirmation_v2_1_09760697/publication_report.md)
- [`20260806_SkyCausal_IndependentConfirmationV2_1协议.md`](20260806_SkyCausal_IndependentConfirmationV2_1协议.md)

### Two-Stage 执行状态

```text
../codebase/SkyEngine/experiment/skycausal/protocols/
  fjsp_two_stage_pilot_v0.json
  fjsp_two_stage_freeze_spec_v0.json
  fjsp_two_stage_freeze_result_v0.json
  fjsp_two_stage_capability_audit_v0.json
```

## 十、最终判断

当前项目不是“固定六种方案已经做完，接下来只需写论文”，而是：

```text
原始闭环耦合问题：                  已明确
动态 DecisionBackend 契约：         已建立
六 profile T=1 基础证据：           已正式 PASS
deadline 与清理基础设施：            已正式 PASS
Two-Stage orchestration 基础设施：   freeze PASS
Two-Stage 质量 pilot：               尚未执行
开放式、多轮 solver options：        尚未完成
最终主论文核心主张：                 仍需根据论文范围和 pilot 结果冻结
```

六 profile 结果是重要且可信的阶段成果，但它应当作为 baseline 和基础证据服务于动态
orchestration 主线，不能反过来取代这条主线。
