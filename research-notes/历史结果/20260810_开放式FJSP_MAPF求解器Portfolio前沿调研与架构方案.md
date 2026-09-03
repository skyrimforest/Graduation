# 开放式 FJSP-MAPF 求解器 Portfolio 前沿调研与架构方案

日期：2026-08-10

状态：开放式采样 v0 已实现并通过聚焦测试；真实 solver catalog、manifest 发现和
live adapter 执行尚未接入。

## 一、结论

固定六个联合 profile 不能满足 SkyCausal 的长期目标。即使把六个扩成二十个，问题也
没有解决，因为 controller 仍然依赖一个人工枚举、永久封闭的候选列表。

正确目标不是：

```text
维护一个越来越大的 joint-profile JSON
```

而是：

```text
开放 solver catalog
+ solver 自描述 capability/config schema
+ 状态与预算条件下的 option 生成
+ progress-aware 在线调度
+ 统一、安全、可审计的执行契约
```

开放性的验收标准应当是：

> 新增一个符合契约的 FJSP 或 MAPF solver 时，不修改 `DecisionBackend` 的输出维度，
> 不重写固定 profile 矩阵，也不重新定义系统动作语义。系统通过注册 manifest、
> contract validation、短探测和受控准入自动生成新的候选 option。

这仍然不是“任意代码自动上线”。生产和正式实验必须保持 deny-by-default：

```text
对未来 solver 开放
!=
对未经验证的 solver 无条件放行
```

## 二、六 profile 当前为什么是封闭实现

### 2.1 `SolverPortfolio` 是固定元组

当前：

```text
experiment/skycausal/decision_backend.py
```

中的 `SolverPortfolio` 在构造时接收固定的 `Sequence[SolverProfile]`，后端按 profile
名称引用候选。`DecisionAction` 也只保存一个 `solver_profile` 字符串。

这意味着当前系统支持的是：

```text
configurable finite list
```

而不是：

```text
discoverable and extensible solver option space
```

### 2.2 action 由 recovery operator 与全部 profile 直接做乘积

`EventDecisionController._collect()` 当前生成：

```text
eligible recovery operator x available fixed profile
```

它没有表达：

- solver 参数的条件空间；
- 不同预算下的同一 solver option；
- start、continue、adjust、switch、fork、commit 等生命周期动作；
- 当前运行 solver 的 progress；
- warm-start、checkpoint 和 safe boundary；
- 新 solver 的短探测与在线准入。

### 2.3 MAPF 参数使用中心化白名单

`solver_profile_activation.py` 中的 `_MAPF_CONFIG_FIELDS` 是一个中心化字段集合。未来
solver 只要增加专有参数，就必须修改 SkyEngine 核心代码。

这违反开放性要求。参数合法性应由每个 solver 的版本化 config schema 负责，而不是
由中央模块了解所有算法参数。

### 2.4 联合 profile 文件人工枚举 FJSP-MAPF 组合

当前：

```text
experiment/skycausal/protocols/joint_profiles_deadline_v2.json
```

显式保存六个 FJSP-MAPF 组合。它适合冻结一次 publication experiment，但不适合作为
长期运行时 catalog。

### 2.5 已有 orchestration contract 是正确地基

当前代码已经具备可复用的开放性基础：

```text
SolverAdapterDescriptor
SolverOrchestrationAdapter
PortableIncumbentBundle
NativeSolverCheckpoint
SolverCompatibilityMatrix
continue_run / cold_switch / warm_switch
operation audit
```

问题不在这些底层契约，而在上层仍以固定 `SolverProfile` 和手写 joint profile 生成
动作。

## 三、前沿进展

### 3.1 MAPF 已明确进入 algorithm selection 阶段

MAPF 不存在全场景支配算法。不同算法在地图拓扑、agent 密度、冲突结构、时间限制和
质量约束下表现不同。

代表工作：

1. [MAPFASTER, IROS 2022](https://doi.org/10.1109/IROS47612.2022.9981981)
   使用轻量网络从候选 MAPF solver 中选择预计最快的算法。
2. [No Panacea in Planning, 2024](https://arxiv.org/abs/2404.03554)
   把选择范围从最优算法扩展到 optimal、bounded-suboptimal 和 unbounded-suboptimal
   solver，并同时考虑 runtime-quality 权衡和同一算法的不同超参数。
3. [Algorithm Selection for Optimal MAPF via Graph Embedding, 2024](https://arxiv.org/abs/2406.10827)
   用可在线计算的 graph embedding 表示新地图和 agent start-goal 结构，重点评估
   in-grid、in-grid-type 和 between-grid-type 泛化。
4. [Where Paths Collide: A Comprehensive Survey, 2025](https://arxiv.org/abs/2505.19219)
   将当前 MAPF 方法归纳为 search、SAT/SMT/CSP/MIP compilation、learning 和 hybrid
   等多个族群，进一步说明候选空间不应绑定少数现有算法。

对本项目的直接含义：

```text
MAPF solver id 和 hyperparameter configuration 都应是 option 的一部分；
选择目标不能只有“最快”，还要包含可行率、路径质量和制造端成本；
模型输入必须能处理新地图、新 agent 数和新 solver descriptor；
固定类别 softmax 无法支持新 solver 插入。
```

### 3.2 MAPF 前沿正在从静态选择走向内部动态组合

[LNS2+RL, 2025](https://arxiv.org/abs/2405.17794) 在 LNS2 的早期迭代使用质量较高但
较慢的 MARL replanner，在后期自适应切换到更快的 PP，从而在一次求解过程中动态
平衡质量和速度。

该工作的重要启示不是要求 SkyCausal 复现它，而是：

> “solver”不应被视为不可分割黑盒。未来候选可能是单算法、参数化算法、内部混合
> 算法，也可能是由 controller 编排的多个算法阶段。

因此 catalog 应同时允许：

```text
atomic solver
parameterized solver
solver-native hybrid
controller-composed option sequence
```

### 3.3 Dynamic Algorithm Configuration 强调运行中调参

[DACBench, IJCAI 2021](https://www.automl.org/automated-algorithm-design/dac/dacbench-benchmarking-dynamic-algorithm-configuration/)
强调需要统一 controller 与 target algorithm 之间的 interaction point、runtime
statistics、cost、parameter range 和 transition。

[Seq-MADAC, NeurIPS 2025](https://openreview.net/forum?id=27aIOGfkAV) 进一步研究具有
依赖顺序的动态参数配置，例如先选择 operator，再选择该 operator 的参数。

这说明 SkyCausal 的 action 不能是一个扁平 profile 标签。更合理的是分层生成：

```text
domain
-> solver family
-> solver implementation
-> parameter configuration
-> budget/scope
-> transition mode
```

各层之间存在条件依赖，不能无条件做完整笛卡尔积。

### 3.4 Gray-box 配置利用 solver 中途进展

[Realtime Gray-Box Algorithm Configuration, 2023](https://doi.org/10.1007/s10472-023-09890-x)
使用 solver 的 intermediate output 判断正在运行的配置是否值得继续，并提前终止
不 promising 的候选以释放资源。

这与 SkyCausal 已有能力直接对应：

```text
observe progress
incumbent objective
lower bound / gap
time to first feasible
improvement rate
cooperative stop
remaining wall budget
```

所以后续不应继续依赖六个 terminal rollout 全部跑完。更合理的在线机制是：

```text
短 probe
-> 淘汰明显不合适候选
-> 给 promising option 增加预算
-> 必要时 warm switch
-> deadline 前 commit
```

### 3.5 Anytime portfolio 应随预算变化

[A Method for the Automated Configuration of Anytime Portfolios of Algorithms,
EJOR 2026](https://doi.org/10.1016/j.ejor.2025.07.024) 指出，单一配置难以在所有
runtime budget 上表现良好，应构造面向不同运行时长的配置 portfolio，并提前终止
不 promising 的配置。

这支持把：

```text
solver + config + budget
```

视为 option，而不是仅把 `solver name` 当成 action。

[Greedy Restart Schedules, GECCO 2025](https://arxiv.org/abs/2504.11440) 还表明，简单
的预算调度和 restart schedule 就能构成强 baseline。SkyCausal 在训练 MCTS/RL 前，
必须先比较非学习 racing/scheduling 基线。

### 3.6 FJSP 前沿是 heuristic portfolio 和动态 hyper-heuristic

代表工作：

1. [Knowledge-and-Learning-Based Hyper-Heuristics, IEEE TETCI 2025](https://doi.org/10.1109/TETCI.2025.3540422)
   用 Q-learning 从 GA、ABC、brain storm 和 Jaya 等低层搜索方法中动态选择。
2. [Selection Hyper-Heuristics and Job Shop Scheduling, Journal of Scheduling
   2025](https://doi.org/10.1007/s10951-024-00819-8)
   研究由多个低层 dispatching rule 构成的 selection hyper-heuristic 及跨规模训练。
3. [DSevolve, 2026 preprint](https://arxiv.org/abs/2603.27628)
   不再演化一个固定 elite rule，而是离线构造行为多样的 heuristic archive，在线用
   轻量 probe fingerprint 检索当前状态适合的规则。
4. [Policy-Based DRL Hyper-Heuristics, 2026 preprint](https://arxiv.org/abs/2601.11189)
   研究状态依赖的规则切换、动作预过滤和 switching commitment。

其中两篇 2026 工作仍是预印本，只能作为趋势证据，不能当作已确认结论。共同趋势
仍然清楚：

```text
固定单一算法
-> 固定候选集选择
-> 状态依赖 hyper-heuristic
-> 多样性 archive + probe/retrieval
-> 运行中 configuration/scheduling
```

## 四、开放式总体架构

建议将系统拆成七层：

```text
1. Solver Catalog
2. Capability and Schema Registry
3. Option Generator
4. Candidate Pruner / Retriever
5. DecisionBackend
6. Orchestration Executor
7. Audit and Admission Gate
```

数据流：

```text
physical state + event + remaining budget
                  |
                  v
        Solver Catalog snapshot
                  |
                  v
       capability/schema filtering
                  |
                  v
       conditional option generation
                  |
                  v
       top-K retrieval / short probes
                  |
                  v
   DecisionBackend: continue/switch/adjust
                  |
                  v
       deadline-safe orchestration
                  |
                  v
      certified incumbent + audit
```

### 4.1 Solver Catalog

每个 solver 通过独立 manifest 注册，不再由中央文件枚举联合 profile。

最小 manifest：

```yaml
schema_version: skycausal.solver-manifest.v1
solver_id: mapf.eecbs
solver_version: 2026.08+commit
domain: mapf
artifact:
  image_digest: sha256:...
  service_protocol: skyengine.mapf.v2
input_schema: skycausal.mapf-problem.v2
output_schema: skycausal.mapf-path-bundle.v2
config_schema: schemas/mapf.eecbs.config.v1.json
capabilities:
  - start
  - observe
  - continue_run
  - export_incumbent
  - cleanup
  - audit
safe_switch_boundaries:
  - before_route_activation
portable_bundle_schemas:
  - skycausal.mapf-path-bundle.v2
resource_requirements:
  cpu: 4
  gpu: 0
license:
  use: research_only
```

开放性来自 manifest 和 adapter contract，而不是来自修改中央 enum。

### 4.2 Config Schema

每个 solver 自己声明：

```text
parameter type
range or choices
default
conditional dependency
mutability
restart requirement
budget coupling
```

例如：

```yaml
suboptimality:
  type: float
  minimum: 1.0
  maximum: 3.0
  mutable_during_run: false

lns_neighbor_size:
  type: integer
  minimum: 4
  maximum: 64
  active_if:
    algorithm_family: lns
```

实现上可以采用 JSON Schema 加一层 SkyCausal 扩展，也可以直接采用 ConfigSpace 的
conditional configuration 表达。关键是删除中央 `_MAPF_CONFIG_FIELDS`。

### 4.3 Solver Option

`SolverOption` 是一次可执行、有生命周期的候选，不是永久 profile。

```python
@dataclass(frozen=True)
class SolverOption:
    option_id: str
    solver_id: str
    solver_version: str
    domain: str
    config: Mapping[str, object]
    scope: Mapping[str, object]
    budget_ms: int
    initiation_condition: Mapping[str, object]
    termination_condition: Mapping[str, object]
    transition_mode: str
    warm_start_from: str | None
    required_capabilities: tuple[str, ...]
    provenance_hash: str
```

同一个 solver 可以生成多个 option：

```text
EECBS(w=1.1, 200 ms)
EECBS(w=1.5, 500 ms)
EECBS(w=2.0, 1000 ms)
MAPF-LNS2(neighbor=8, 500 ms)
MAPF-LNS2(neighbor=32, 2000 ms)
```

### 4.4 Solver Observation

为了支持 gray-box 调度，所有 adapter 应尽量输出统一 progress envelope：

```python
@dataclass(frozen=True)
class SolverObservation:
    solver_id: str
    elapsed_ms: int
    has_feasible_incumbent: bool
    incumbent_objective: float | None
    lower_bound: float | None
    optimality_gap: float | None
    improvement_rate: float | None
    explored_units: int | None
    failure_risk: float | None
    resource_usage: Mapping[str, float]
```

不支持某字段的 solver 返回 `None`，不能伪造。controller 根据 capability mask 处理。

### 4.5 Lifecycle Action

上层动作改为：

```text
START(option)
CONTINUE(run_id, delta_budget)
ADJUST(run_id, mutable_parameters)
CHECKPOINT(run_id)
COLD_SWITCH(source, target_option)
WARM_SWITCH(source, target_option, incumbent)
FORK(source_incumbent, option_set)
COMMIT(incumbent_id)
ABORT(run_id)
```

不是每个 solver 都支持所有动作。合法性由 descriptor、config schema、当前运行状态、
safe boundary 和剩余预算共同决定。

## 五、避免开放空间爆炸

开放不等于运行全部组合。新增 solver 后不能执行：

```text
all FJSP x all MAPF x all configs x all budgets x all switch times
```

建议采用分层、多保真生成。

### 5.1 第一层：静态 capability filter

先过滤：

```text
domain mismatch
unsupported event/scope
insufficient remaining budget
resource unavailable
license not allowed
schema incompatible
unsafe switch boundary
uncertified adapter
```

### 5.2 第二层：contextual retrieval

使用当前状态特征检索少量候选：

FJSP 特征示例：

```text
remaining operations
machine flexibility
load skew
critical path estimate
breakdown scope
incumbent quality
```

MAPF 特征示例：

```text
map/topology embedding
agent density
start-goal distance distribution
predicted conflict count
bottleneck width
loaded transport count
planning horizon
```

solver descriptor 特征：

```text
algorithm family
optimality guarantee
anytime capability
warm-start capability
resource class
historical latency/quality quantiles
```

### 5.3 第三层：短 probe

对 retrieval 的 top-K option 运行小预算 probe，收集：

```text
time to first feasible
initial objective
bound/gap
improvement slope
failure signal
cleanup latency
```

probe 是 option generation 的一部分，不是事后偷看 heldout。

### 5.4 第四层：racing / successive halving

按进展逐轮分配预算：

```text
K short probes
-> retain promising K/2
-> increase budget
-> retain promising candidates
-> commit or switch
```

淘汰规则必须预注册，并把 solver failure、adapter failure 和 infrastructure failure
分开。

### 5.5 第五层：progressive widening

当预算增加时，再逐步引入：

```text
更多 solver
更多参数配置
更多 budget tier
更多 transition mode
```

不能在一开始展开整个开放空间。

## 六、FJSP 与 MAPF 不能继续绑成原子 profile

### 6.1 FJSP 和 MAPF 的安全语义不同

FJSP 主要生成 schedule proposal，portable incumbent 较自然：

```text
machine assignment
operation sequence
planned start/end
objective and certificate
```

MAPF 还涉及：

```text
active route
reservation table
remote playback state
loaded transport commitment
execution window
```

因此 MAPF 不允许在任意物理时刻切换。更合理的切换边界包括：

```text
before route activation
at rolling replanning boundary
after reservation cleanup
no irreversible loaded-route mutation
```

### 6.2 使用 proposal contract 解耦

建议定义：

```text
FJSP solver
  -> ScheduleProposal
  -> TransportDemandSignature
  -> MAPF option generation
  -> PathProposal
  -> Joint feasibility/evaluation
```

这样新增 FJSP solver 只需能输出 `ScheduleProposal`，新增 MAPF solver 只需能消费统一
MAPF problem 并输出 `PathProposal`，无需预先手写所有联合 profile。

### 6.3 使用 factorized beam search，不做完整乘积

一次 joint decision 可以按以下方式生成：

1. 从开放 FJSP catalog 取 top `k_f` option；
2. 对其 schedule proposal 提取运输和拥堵 signature；
3. 对每个 proposal 从 MAPF catalog 取条件 top `k_m` option；
4. 只保留总预算、资源和物理约束下的 beam；
5. 对 beam 做短 paired rollout 或真实 solver racing。

复杂度从完整：

```text
|F| x |M| x |C_f| x |C_m| x |B|
```

降为受控的：

```text
k_f x k_m
```

同时保持未来 solver 可加入。

## 七、兼容性不应维护完整 pairwise matrix

当前 `SolverCompatibilityMatrix` deny-by-default 是正确的，但所有 pair 都手写 rule 会
产生 `O(N^2)` 维护成本。

建议改成：

```text
capability/schema predicate
+ certification evidence
+ sparse exception overrides
```

通用推导规则：

```text
uninterrupted:
  same solver id/version + continue capability

native resume:
  same solver id/version + common checkpoint schema

cold switch:
  same domain + target start capability + safe boundary

warm switch:
  same domain
  + source export capability
  + target import capability
  + shared portable schema
  + matching problem/snapshot/scope hashes
  + certified safe boundary
```

每个新 solver 只需声明 descriptor 并通过 certification，不必为全部旧 solver 手写
规则。已知不兼容或需要特殊转换的 pair 再写 override。

## 八、controller 必须与 solver 数量无关

禁止使用：

```text
固定 N 类 softmax
```

因为添加第 `N+1` 个 solver 会改变网络输出结构并要求重新训练。

推荐统一评分：

```text
score(
  physical_state,
  solver_descriptor,
  option_config,
  progress_observation,
  remaining_budget
)
```

对每个候选 option 使用同一个 scorer，然后在动态候选集合中排序。可选模型包括：

```text
gradient boosted ranker
pairwise cost model
contextual bandit
Deep Sets / Set Transformer
graph-conditioned option scorer
survival model for time-to-feasible
```

新增 solver 的冷启动流程：

```text
descriptor prior
-> short probe
-> online calibration
-> shadow outcomes
-> eligible ranking
```

这使新 solver 可以先零样本进入探测阶段，再逐步积累自身数据，而不是等待重做完整
分类器训练集。

## 九、建议的第一版控制算法

第一版不要直接训练 MCTS 或 RL。先实现一个可解释的
`GrayBoxRacingDecisionBackend`：

1. catalog/filter 生成候选；
2. descriptor + state heuristic 取 top-K；
3. 给每个候选相同短 probe 预算；
4. 按 feasibility、objective、gap、improvement slope 和 cleanup risk 排序；
5. successive halving 分配后续预算；
6. 允许从快速可行 solver warm switch 到精确/改进 solver；
7. 在 commit reserve 前提交最好 certified incumbent；
8. 任一审计失败都走现有安全 fallback。

它比固定六 terminal rollout 更接近当前前沿，并具有三个优点：

```text
无需大训练集
能直接利用现有 progress instrumentation
可作为后续 contextual bandit、Options-MCTS 和 RL 的强基线
```

## 十、新 solver 准入流程

建议五级状态：

```text
DISCOVERED
CONTRACT_VALID
SHADOW_VALID
PORTFOLIO_ELIGIBLE
TRANSFER_ELIGIBLE
```

### 10.1 `DISCOVERED`

要求：

```text
manifest 可解析
artifact digest 固定
license 明确
config schema 可验证
```

此阶段不能执行正式任务。

### 10.2 `CONTRACT_VALID`

要求：

```text
health/start/stop/cleanup/audit contract tests
input/output schema tests
hard deadline tests
determinism/seed audit
invalid result rejection
```

### 10.3 `SHADOW_VALID`

要求：

```text
同源 snapshot shadow run
不激活物理结果
性能轨迹和 failure taxonomy 完整
最终 request/session 归零
```

### 10.4 `PORTFOLIO_ELIGIBLE`

要求：

```text
在独立 calibration cohort 上至少有非空适用区间
没有基础设施违规
failure-as-cost 后仍有保留价值
```

它可以参与 cold start、静态选择和 racing。

### 10.5 `TRANSFER_ELIGIBLE`

额外要求：

```text
portable schema compatibility
warm import acceptance
safe switch boundary
cooperative finalization latency
transfer quality validation
```

只有该级别才能参与 warm switch。

## 十一、开放性的实验设计

### RQ1：新 solver 能否在不修改 controller 的情况下接入

实验：

1. 用现有 solver 构建 controller；
2. 冻结 controller 代码和 scorer 结构；
3. 后加入一个 MAPF solver 和一个 FJSP solver；
4. 只提供 manifest、adapter、config schema 和 calibration；
5. 检查是否无需增加固定输出类别即可参与候选生成和选择。

这是开放性最关键的验收，不是“配置文件里又多了两项”。

### RQ2：开放生成能否接近 exhaustive oracle

比较：

```text
full exhaustive oracle, offline only
fixed six profile
static top-K retrieval
probe + racing
probe + racing + warm switch
```

指标：

```text
regret to exhaustive oracle
wall-clock overhead
coverage
failure-as-cost
number of evaluated options
```

### RQ3：gray-box 是否优于 terminal-only

比较相同 wall-clock budget 下：

```text
all terminal rollout
fixed restart schedule
successive halving
progress-aware early stop
```

### RQ4：是否能跨 solver、规模和拓扑泛化

至少做：

```text
leave-one-solver-out
leave-one-map-type-out
cross-agent-count
cross-FJSP-scale
cross-event-type
```

### RQ5：联合制造目标是否优于单组件目标

MAPF 局部 SoC 最好不一定带来制造 makespan 最好。需要比较：

```text
MAPF-local selector
FJSP-local selector
factorized end-to-end selector
joint end-to-end oracle
```

## 十二、实现顺序

### P0：冻结边界

1. 保留 `joint_profiles_deadline_v2.json`，只用于复现六 profile 结果；
2. 禁止把该文件升级成长期 catalog；
3. 冻结 `SolverProfile` 为 legacy v1 contract。

### P1：开放 catalog 和 schema

新增建议：

```text
experiment/skycausal/solver_catalog.py
experiment/skycausal/solver_manifest.py
experiment/skycausal/solver_option.py
experiment/skycausal/manifests/solvers/*.json
experiment/skycausal/schemas/config/*.json
```

验收：

```text
新增 dummy solver 只增加 manifest/adapter/schema；
核心 controller 和 action class 不增加 solver-specific 分支。
```

### P2：OptionGenerator

新增：

```text
capability filter
conditional config sampler
budget tier generator
factorized FJSP-MAPF beam
stable option hash
```

同时实现 `LegacyProfileOptionAdapter`，把六 profile 映射成 legacy options，保证旧实验
可复现。

### P3：统一 progress envelope

为 CP-SAT、DE、PSO 和首批 MAPF solver 逐步实现：

```text
time to first feasible
incumbent trajectory
bound/gap when available
improvement units
resource usage
```

缺失能力必须显式为 unsupported。

### P4：GrayBoxRacingDecisionBackend

先实现非学习 top-K、probe、successive halving、commit reserve 和 fallback。

2026-08-10 已完成第一版独立采样核心：

```text
experiment/skycausal/portfolio_sampling.py
test/skycausal/test_portfolio_sampling.py
```

当前实现包括：

```text
SolverOption 与稳定 option hash
FactorizedTopKComposer
OptionProbeResult
PortfolioSamplingBudget
ProgressiveWideningPortfolioMCTS
solver failure -> capped cost
infrastructure/deadline accounting failure -> declared fallback
```

其中 MCTS 只作用于 solver-option 根节点，不展开未来制造物理状态。候选开放宽度为：

```text
max(
  initial_candidate_count,
  ceil(c_pw * total_visits ** alpha)
)
```

已激活候选使用归一化成本 UCT 分配下一次 probe。probe budget 可按访问次数从短到长
递增，例如：

```text
100 ms -> 250 ms -> 500 ms
```

factorized composer 只计算：

```text
top-k FJSP x top-k MAPF
```

而不是完整 catalog 笛卡尔积。当前 evaluator 仍是可插拔 callback；它尚未连接真实
solver manifest、`SolverOrchestrationAdapter` 和 live service，因此该实现只证明
采样与组合契约可运行，不构成算法质量结论。

### P5：开放性准入实验

优先选择仓库已有但未进入六 profile 的 solver：

MAPF：

```text
PBS
LaCAM3
CBSH2-RTC
RHCR-style PBS
PIBT
```

FJSP：

```text
DRL
```

先证明无需改 controller 即可接入。A* 和 MAPF-GPT 的输入/执行语义与 rolling MAPF
不同，应在 service protocol 和 capability 层明确区分，不应为了数量强行加入同一
实验。

### P6：学习型 selector/controller

只有在开放 catalog、option generation、progress trace 和跨 solver 数据稳定后，再
训练 solver-count-agnostic ranker、contextual bandit 或 SMDP controller。

## 十三、与当前 Two-Stage 的关系

Two-Stage 仍然应该继续，但定位调整为：

```text
验证 portable incumbent、safe stop、remaining budget 和 warm switch 的机制实验
```

它不是最终候选空间。`DE -> CP-SAT`、`PSO -> CP-SAT` 是首批 transfer contract
校准 pair。

Two-Stage pilot 通过后，应把 pair-specific runner 抽象进通用 option executor，而
不是继续手写更多 pair。

## 十四、论文贡献应怎样表述

如果开放架构和实验完成，论文贡献可以升级为：

> 一个面向动态 FJSP-MAPF 的开放式、预算约束、进展感知 solver orchestration
> 框架。它通过版本化 solver capability、条件 option generation、多保真 gray-box
> racing 和 deadline-safe incumbent transfer，在无需固定 solver 输出空间的情况下
> 接入新的 FJSP/MAPF solver。

关键科研点不是插件系统本身，而是：

```text
开放候选空间如何在 hard deadline 下生成和收缩；
异构 solver progress 如何用于预算重分配；
FJSP proposal 与 MAPF planner 如何因子化组合；
新 solver 如何在低数据下安全冷启动；
开放 selector 如何在新增 solver 后保持有效。
```

六 profile `T=1` 结果继续作为：

```text
closed-set baseline
portfolio headroom evidence
deadline infrastructure evidence
```

不能作为最终方法。

## 十五、最终决定

本项目应采用以下技术路线：

```text
固定 joint profiles
  -> legacy reproducibility only

开放 solver manifests
  -> future FJSP/MAPF discovery and validation

capability-driven SolverOption
  -> solver/config/budget/scope/transition 统一动作

factorized top-K + probe + racing
  -> 避免开放空间笛卡尔爆炸

gray-box progress scheduling
  -> continue/stop/switch/commit

solver-count-agnostic scorer
  -> 新 solver 无需修改固定输出维度

deny-by-default admission
  -> 保持 deadline、物理安全和可审计性
```

这才满足“未来更多 MAPF 和 FJSP 求解器持续加入”的要求。
