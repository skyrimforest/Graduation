# 开放式 Portfolio 浅层 MCTS 综合方案与本轮迭代记录

日期：2026-08-10

状态：开放式采样核心、最小 Solver Catalog 和真实 FJSP probe evaluator 已实现；
历史 fixture smoke 通过，正式 calibration 尚未开始。

后续实验分层、对照组、消融、开放接入、外部方法复现和独立确认规则见：
[`20260811_开放式求解器元搜索实验评估与复现协议.md`](20260811_开放式求解器元搜索实验评估与复现协议.md)。

2026-08-11 实施结果见：
[`20260811_开放式SolverCatalog与真实FJSPProbe首轮实现记录.md`](20260811_开放式SolverCatalog与真实FJSPProbe首轮实现记录.md)。

## 一、这轮迭代解决了什么

本轮针对两个问题进行了纠正和实现：

1. 固定六个 FJSP-MAPF joint profile 不能作为长期 action space；
2. 需要一种能对动态 solver option 快速采样、分配预算并选择组合的方法。

最终采用的方向是：

```text
开放 Solver Catalog
+ 每个 solver 独立 config schema
+ capability-driven SolverOption
+ FJSP/MAPF factorized top-K 组合
+ short probe 和 gray-box observation
+ progressive-widening Root MCTS
+ solver 数量无关的统一 scorer
+ contract/shadow/portfolio/transfer 分级准入
```

其中 MCTS 只用于：

```text
solver option 采样
probe 预算分配
候选组合选择
```

不再用于展开未来制造物理状态树。

## 二、为什么只使用浅层 Root MCTS

项目已经有一个冻结负结果：

```text
Open-loop UCT 没有优于 Root Search
```

因此不能在没有新证据的情况下重新把深层制造状态 MCTS 当成主方法。

这次使用的 MCTS 与旧实验不是同一个问题：

| 旧 Open-loop UCT | 当前 Portfolio Root MCTS |
|---|---|
| 展开多步制造事件动作 | 只搜索当前 solver option |
| tree depth 大于 1 | 固定 depth = 1 |
| 节点是物理动作序列 | 节点是 solver/config/budget 候选 |
| rollout 到未来制造状态 | 短 probe 获取 solver 进展 |
| 已验证无额外收益 | 尚待 live solver value test |

所以当前方法更准确地说是：

```text
带 progressive widening 的 Root UCT / best-arm sampling
```

而不是通用深层 MCTS。

## 三、从前沿工作吸收了什么

### 3.1 No Panacea 和 MAG

参考：

- [No Panacea in Planning](https://arxiv.org/abs/2404.03554)
- [Algorithm Selection for Optimal MAPF via Graph Embedding](https://arxiv.org/abs/2406.10827)

吸收点：

```text
候选不只是 solver name；
候选应包含 solver + hyperparameters + budget；
选择需要考虑地图、agent、冲突和质量约束；
selector 应面向 solver descriptor，而不是固定类别编号。
```

对应到本项目：

```text
EECBS(w=1.1, budget=200 ms)
EECBS(w=1.5, budget=500 ms)
MAPF-LNS2(neighbor=8, budget=500 ms)
```

应被视为不同的 `SolverOption`。

### 3.2 LNS2+RL

参考：

- [LNS2+RL](https://arxiv.org/abs/2405.17794)

吸收点：

```text
求解器执行过程可以分阶段；
前期和后期可以使用不同搜索组件；
continue/switch 的价值依赖当前进展，而不只依赖初始状态。
```

对应到本项目：

```text
快速 solver 先找到可行解
-> 导出 portable incumbent
-> 精确或改进 solver 使用剩余预算继续
```

这与现有 Two-Stage `DE/PSO -> CP-SAT` 机制验证一致。

### 3.3 Gray-Box Configuration

参考：

- [Realtime Gray-Box Algorithm Configuration](https://doi.org/10.1007/s10472-023-09890-x)

吸收点：

```text
不能只看 solver 最终结果；
应观察 time-to-first-feasible、incumbent、gap 和 improvement rate；
明显不 promising 的候选应提前终止。
```

当前 v0 已定义统一 `OptionProbeResult`，记录：

```text
status
feasible
elapsed_ms
objective_value
lower_bound
optimality_gap
improvement_rate
metadata
```

当前 UCT backup 仍以同预算下的 objective/capped failure cost 为主。gap 和
improvement rate 已进入审计数据，但尚未冻结跨 solver 的统一量纲和 scalarizer。

### 3.4 Anytime Portfolio

参考：

- [Automated Configuration of Anytime Portfolios, EJOR 2026](https://doi.org/10.1016/j.ejor.2025.07.024)

吸收点：

```text
同一个 solver/config 在不同预算下表现不同；
probe 应从短预算逐步增加；
预算应优先分配给当前更有希望的候选。
```

当前实现支持可配置 budget schedule，例如：

```text
10 ms -> 20 ms -> 40 ms
```

这是单元测试中的示例，不是正式实验预算。真实服务的 budget grid 必须经过
cooperative-stop calibration 和预注册。

### 3.5 DSevolve

参考：

- [DSevolve, 2026 preprint](https://arxiv.org/abs/2603.27628)

吸收点：

```text
不要只维护一个全局最优 solver/rule；
应维护行为不同的候选 archive；
用轻量 probe 识别当前状态适合哪个候选。
```

DSevolve 目前是预印本，只作为趋势依据。本项目借鉴的是：

```text
多样候选 + 状态检索 + 短 probe
```

不是直接采用其具体算法。

## 四、综合系统架构

### 4.1 Solver Catalog

每个 solver 通过 manifest 注册：

```text
solver_id
solver_version
domain
artifact/image digest
service protocol
input/output schema
config schema
capabilities
safe switch boundaries
resource requirements
license
```

新增 solver 不修改 controller 的固定输出维度。

### 4.2 SolverOption

一次可执行候选至少包含：

```text
solver id/version
domain
config
budget
required capabilities
prior score
metadata
stable option hash
```

同一个 solver 可以产生多个 option。

### 4.3 Factorized FJSP-MAPF 组合

禁止直接展开：

```text
all FJSP
x all MAPF
x all configs
x all budgets
```

采用：

```text
state/capability filter
-> top-k FJSP options
-> top-k MAPF options
-> compatibility filter
-> bounded joint beam
```

当前 `FactorizedTopKComposer` 只计算：

```text
k_f x k_m
```

而不是整个 catalog 笛卡尔积。

后续接入真实制造状态后，应进一步变为：

```text
FJSP option
-> ScheduleProposal
-> TransportDemandSignature
-> 条件 MAPF retrieval
-> PathProposal
-> joint evaluation
```

### 4.4 Short Probe

每次 probe 必须：

```text
不激活真实物理结果
使用独立 planning seed
有显式 admitted budget
记录 monotonic 实测耗时
记录 solver 上报耗时
保留完整 failure taxonomy
结束后完成 cleanup/audit
```

### 4.5 Root MCTS Sampler

根节点是当前候选集合，每个 child 是一个 `SolverOption` 或
`JointSolverOption`。

运行过程：

```text
1. 按 prior 排序候选；
2. 激活 initial_candidate_count 个候选；
3. 对未访问候选执行短 probe；
4. 对已访问候选使用 UCT 选择下一次 probe；
5. 随访问次数增加逐步开放新候选；
6. 按 schedule 增加同一候选的 probe budget；
7. budget/deadline 到达后选择平均 capped cost 最低的可行候选。
```

## 五、Progressive Widening

候选开放宽度为：

```text
allowed(N) = min(
  candidate_count,
  max(
    initial_candidate_count,
    ceil(c_pw * max(1, N) ** alpha)
  )
)
```

其中：

```text
N：当前已接受 backup 的 probe 数；
c_pw：开放速度常数；
alpha：开放指数，范围 (0, 1]。
```

作用：

```text
小预算时只评估少量高 prior 候选；
预算增加后逐步纳入更多新 solver/config；
不要求候选数量固定；
不要求一次覆盖全部开放 catalog。
```

## 六、UCT 预算分配

对已激活候选，当前使用归一化成本 UCT。

设候选 `i` 的平均 capped cost 为 `mean_i`，同层已访问候选最小和最大平均成本为
`min_mean`、`max_mean`。

成本越低越好，因此 exploitation 为：

```text
exploitation_i =
  (max_mean - mean_i) / (max_mean - min_mean)
```

若同层成本相同，则 exploitation 取 `0.5`。

探索项：

```text
exploration_i =
  c_uct * sqrt(log(N + 1) / visits_i)
```

最终：

```text
UCT_i = exploitation_i + exploration_i
```

未访问候选分数为正无穷，保证进入 active set 后至少被 probe 一次。

## 七、Probe Budget

每个候选第 `n` 次访问使用：

```text
schedule[min(n, len(schedule) - 1)]
```

例如：

```text
第一次：10 ms
第二次：20 ms
第三次及以后：40 ms
```

admission 同时受四个条件限制：

```text
全局剩余 probe budget
单个 option 声明的 budget cap
单次 probe deadline
总 search deadline
```

不能因为全局 schedule 包含 `500 ms`，就让一个只声明支持 `100 ms` 的 option 被
错误推进到 `500 ms`。

## 八、Backup 和 Fallback

### 8.1 可行 probe

```text
backed_up_cost = objective_value
```

### 8.2 Solver failure

以下失败作为 solver 行为证据保留：

```text
solver_failure
hard_deadline
cancelled
no feasible incumbent
```

统一：

```text
backed_up_cost = pre-registered failure_cost
```

不能删除失败样本。

### 8.3 Infrastructure failure

以下情况不允许作为 solver 质量 backup：

```text
evaluator exception
infrastructure_failure
solver 上报 elapsed 超过 admitted budget
monotonic 实测 elapsed 超过 admitted budget
完成时间超过总 search deadline
```

发生后立即选择显式 fallback option，并保留 audit。

### 8.4 最终选择

仅在至少有一个 feasible probe 时选择：

```text
mean backed-up cost 最低
-> feasible count 更多
-> visits 更多
-> stable option_id
```

若没有可行 probe，则使用预声明 fallback。

## 九、一次示例运行

假设 catalog 中有：

```text
FJSP：CP-SAT、DE、PSO、DRL
MAPF：EECBS、LG-LaCAM、MAPF-LNS2、PBS、LaCAM3、PIBT
```

第一步根据当前故障状态、资源和 capability 得到：

```text
FJSP top-3
MAPF top-4
```

最多只生成：

```text
3 x 4 = 12 joint options
```

而不是直接枚举全部 solver/config/budget。

随后：

```text
第 1 轮：给初始候选短 probe；
第 2 轮：UCT 重新采样表现较好或不确定性较高的候选；
第 3 轮：progressive widening 引入新候选；
后续轮：增加 promising 候选的 probe budget；
结束：选择平均 capped cost 最低的可行 option。
```

真实运行还需要 evaluator 将 option 转成：

```text
start solver
observe progress
export incumbent if supported
stop/cleanup
produce OptionProbeResult
```

## 十、本轮实际实现

### 10.1 新增开放采样模块

文件：

```text
codebase/SkyEngine/experiment/skycausal/portfolio_sampling.py
```

新增：

```text
SolverOption
JointSolverOption
FactorizedCompositionResult
FactorizedTopKComposer
OptionProbeResult
PortfolioSamplingBudget
PortfolioSamplingDecision
ProgressiveWideningPortfolioMCTS
```

实现能力：

```text
动态候选数量
稳定 option hash
FJSP/MAPF bounded beam 组合
compatibility callback
progressive widening
归一化成本 UCT
渐增 probe budget
option-specific budget cap
failure-as-cost
显式 fallback
evaluator exception audit
reported/monotonic 双重 deadline audit
```

### 10.2 新增测试

文件：

```text
codebase/SkyEngine/test/skycausal/test_portfolio_sampling.py
```

新增 `17` 个采样专项测试，覆盖：

```text
option hash 稳定性
domain 校验
bounded factorized composition
输入顺序不影响组合结果
probe result 契约
动态加入新 solver
joint option 直接进入 sampler
progressive widening 不展开完整 catalog
probe budget 逐级增加
option budget cap
solver failure capped cost
evaluator exception fallback
reported deadline violation
monotonic 实测 deadline violation
无可行候选 fallback
```

### 10.3 同步研究材料

已更新：

```text
research/20260810_开放式FJSP_MAPF求解器Portfolio前沿调研与架构方案.md
```

把状态从“纯设计提案”更新为：

```text
2026-08-10：采样核心 v0 已实现；
当时真实 solver catalog、manifest 和 live adapter 尚未接入。
```

2026-08-11 更新：

```text
Solver Manifest/Catalog 已实现；
CP-SAT、DE、PSO manifests 已加入；
真实 FJSP probe evaluator 已接入；
历史 fixture real-service smoke 已通过；
正式 calibration 仍未开始。
```

### 10.4 没有修改冻结 publication 路径

本轮没有修改：

```text
六 profile publication protocol
v2.1 正式 artifact
现有 Root Search 结果
Two-Stage freeze result
```

新采样器是独立模块，避免改变已确认结果的复现语义。

## 十一、验证结果

执行：

```bash
./.venv/bin/python -m unittest -v \
  test.skycausal.test_portfolio_sampling \
  test.skycausal.test_root_monte_carlo \
  test.skycausal.test_solver_orchestration_contract
```

结果：

```text
Ran 50 tests
OK
```

同时执行：

```bash
./.venv/bin/python -m py_compile \
  experiment/skycausal/portfolio_sampling.py \
  test/skycausal/test_portfolio_sampling.py
```

结果通过。

## 十二、本轮没有完成什么

当前不能声称：

```text
已经从真实 solver 获得效率曲线；
采样 MCTS 已经优于六 profile Root Search；
已经完成跨 solver live switch 的元搜索控制器；
已经训练 solver-count-agnostic scorer；
已经确定正式 probe budget；
已经通过独立 cohort 的 Value Gate。
```

当前已用历史 fixture 真实调用 CP-SAT、DE、PSO，但只有一次开发 smoke，三个 solver
目标值均为 `38`。这只能验证调用、观察、协作停止、认证和 cleanup 链路，不能形成
效率曲线或选择价值证据。DRL、MAPF 和新 calibration cohort 尚未接入。

## 十三、后续实施顺序

### P1：Solver Manifest 和 Catalog（最小版本已完成）

实现：

```text
solver_manifest.py
solver_catalog.py
per-solver config schema
artifact/capability/license validation
```

验收：

```text
新增 dummy solver 只增加 manifest、adapter 和 schema；
sampler/controller 不增加 solver-specific 分支。
```

### P2：OrchestrationProbeEvaluator（FJSP 版本已完成）

把 `SolverOption` 连接到现有：

```text
SolverOrchestrationAdapter
start_run
observe
await_run
request_stop
export_incumbent
cleanup
audit
```

输出真实 `OptionProbeResult`。

### P3：先接 FJSP live probe（历史 smoke 已完成）

优先：

```text
CP-SAT
DE
PSO
```

原因：

```text
已有 progress instrumentation；
已有 cooperative-stop freeze；
已有 portable FJSP incumbent；
切换边界比 MAPF 更清晰。
```

### P4：运行 development-only calibration

采集：

```text
time to first feasible
objective trajectory
gap when available
improvement rate
finalization latency
failure rate
```

据此冻结真正的 probe schedule，而不是直接使用单测中的 `10/20/40 ms`。

### P5：接 MAPF live probe

按能力分组：

```text
rolling MAPF
one-shot classical MAPF
learned policy
```

MAPF 必须额外验证：

```text
reservation cleanup
route activation boundary
loaded transport commitment
session cleanup
path feasibility
```

### P6：价值实验

比较：

```text
best fixed
六 profile T=1 Root Search
random option sampling
uniform short probe
successive halving
progressive-widening Root MCTS
offline exhaustive oracle
```

所有方法使用同一端到端 wall-clock budget。

## 十四、论文中的正确定位

如果 live probe 和独立 Value Gate 通过，可以将方法描述为：

> 面向开放 FJSP-MAPF solver catalog 的、预算约束、进展感知 portfolio sampling
> 方法。它使用 factorized option generation、短 probe 和 progressive-widening
> Root MCTS，在 hard deadline 下动态分配评估预算，并保留安全 fallback。

在 Value Gate 通过前，只能写成：

```text
开放式 solver-option contract
+ 可运行的采样器原型
+ 机制与安全测试
```

不能写成已验证的算法性能贡献。

## 十五、最终判断

本轮已经完成：

```text
从固定六 profile 转向开放 SolverOption；
从完整联合枚举转向 factorized top-K；
从全部 terminal rollout 转向渐增 short probe；
从固定覆盖转向 progressive widening；
从均匀采样转向 UCT 预算分配；
从仅信任 solver 报告转向 monotonic deadline 双重审计；
完成独立代码、17 个专项测试和 50 项相关回归。
```

下一步不是继续扩写采样算法，而是实现真实 `OrchestrationProbeEvaluator`，用现有
CP-SAT、DE、PSO 服务产生第一批真实效率轨迹。只有拿到真实轨迹，才能判断 Root MCTS
是否比简单 successive halving 更值得保留。
