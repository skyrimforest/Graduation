# SkyCausal Two-Stage Solver Switching 实验协议 v0

日期：2026-08-06

状态：`DRAFT_NOT_EXECUTABLE`

本文定义两阶段异构 solver 接力的机制验证协议。它不修改、替代或回写以下已冻结
publication 协议及其 Gate：

```text
research/20260806_SkyCausal_PublicationRerun协议.md
research/20260806_SkyCausal_PublicationClaimMatrix.md
```

本文在预算、cohort、adapter contract、候选兼容性和统计阈值完成冻结前禁止执行
确认性实验。任何 pilot 结果只能用于补全本文的待冻结项，不得作为论文确认性证据。

## 一、研究目标与边界

### 1.1 长期问题

长期研究目标是：

> 在动态 FJSP-MAPF 系统中，根据物理状态、当前解状态、solver 进展和剩余资源，
> 多轮决定继续、切换、组合、调整或提交 solver option，并在 hard deadline、
> 物理安全、资源约束和原子提交约束下最小化闭环执行成本。

该问题更接近 constrained semi-Markov decision process（SMDP）或 options
framework，而不是固定时间步 MDP。一个 option 至少包含：

```text
initiation condition
solver/component and parameters
budget and scope
termination condition
export/cleanup semantics
```

### 1.2 本协议只验证两阶段机制

本协议只回答：

> 在相同 end-to-end planning wall budget 下，solver A 运行第一阶段后，将可移植
> incumbent 交给 solver B 接续优化，是否优于 A 不间断运行、A checkpoint-resume、
> B 独占全部预算以及 A 到 B 的 cold switch。

第一版不训练动态 controller，不执行 MCTS、RL 或 rolling-horizon policy，不声称：

1. 已实现完整 Dynamic Algorithm Configuration；
2. 已解决开放动作空间中的最优 option 生成；
3. 两阶段结果可直接推广到任意多轮 switching；
4. 当前六个联合 profile 构成永久封闭的 action space；
5. solver 内部私有搜索状态可以跨异构 solver 直接迁移。

### 1.3 当前 Root Search 的定位

当前六 profile Root Search 继续作为：

```text
T = 1
event-level static algorithm selection
deadline-safe shadow execution baseline
```

Branch-local certification 必须在独立协议中先完成确认。本协议不得利用未确认的
branch-local replay 效果替代两阶段 switching 证据。

## 二、首轮研究问题

### RQ1：控制器介入本身有多少开销

比较：

```text
A uninterrupted
A native checkpoint-resume
```

差异包括 checkpoint、observe、resume 和相关 orchestration 开销。若 solver 不支持
native checkpoint-resume，不得用 cold restart 冒充该对照。

### RQ2：跨 solver warm transfer 是否有效

比较：

```text
A -> B cold
A -> B warm
```

该比较隔离可移植 `IncumbentBundle` 的边际价值。

### RQ3：switch 是否优于继续 A

比较：

```text
A native checkpoint-resume
A -> B warm
```

所有 export、cleanup、initialization、import、controller 和 audit 时间必须消耗同一
end-to-end wall budget。

### RQ4：先运行 A 是否优于直接运行 B

比较：

```text
B full budget
A -> B warm
```

该比较防止把“B 本来更强”误解释为“接力有效”。

### RQ5：是否存在 sequence headroom

分别报告：

```text
best fixed single solver
best fixed cold sequence
best fixed warm sequence
per-state cold sequence oracle
per-state warm sequence oracle
two-stage controller
```

### RQ6：switching 是否增加安全和基础设施风险

至少检查：

```text
physical invariant violations
late completion
deadline accounting failures
orphan request/session
cleanup failures
stale or incompatible incumbent
commit reserve violations
atomic commit violations
```

## 三、动作语义与实验分层

### 3.1 当前六个 profile 不是六个原子 solver

当前 publication actions 是联合配置：

```text
(FJSP solver, MAPF solver, parameters, budgets)
```

因此不得直接把六个联合 profile 做成无条件 `6 x 6` switching matrix。一次
joint-profile switch 可能同时改变 FJSP 和 MAPF 组件，无法识别收益来自哪一侧。

### 3.2 首轮动作分为三类

#### A. 同域 improvement

```text
FJSP A -> FJSP B
MAPF A -> MAPF B
```

这是首轮 warm-start 机制实验的主范围。

首批待审计组件：

```text
FJSP:
  CP-SAT
  DE
  PSO

MAPF:
  EECBS
  LG-LaCAM
  MAPF-LNS2
```

候选存在不等于支持 switching。只有通过 adapter、compatibility、deadline 和
transfer Gate 的有向 pair 才能进入实验。

#### B. 跨域 pipeline

```text
FJSP -> MAPF
```

这通常是工作流依赖而不是同域 solver switch。首轮可单独测量预算分配和信息传递，
但不得与同域 warm-switch 结果合并成一个效应量。

#### C. 联合回环

```text
FJSP -> MAPF -> FJSP
```

该回环需要路径冲突向调度层反馈、重新冻结已执行前缀并再次保证联合可行性。本协议
不执行该类实验，留给后续 rolling-horizon 协议。

### 3.3 Configuration grammar

每个两阶段 action 定义为：

```text
sequence_id
domain
solver_a
config_a
stage_1_budget
transition_mode
solver_b
config_b
stage_2_termination
scope
fallback_policy
```

其中：

```text
transition_mode:
  uninterrupted
  native_checkpoint_resume
  cold_switch
  warm_switch
```

合法性由 versioned compatibility matrix 决定，不允许根据运行结果临时删改。

## 四、统一状态契约

### 4.1 Portable IncumbentBundle

跨 solver 只允许传递公开、可审计、语义一致的可移植状态：

```text
schema_version
domain
problem_hash
snapshot_hash
scope_hash
incumbent_id
parent_incumbent_id

schedule
machine_assignments
operation_ordering
agv_paths
frozen_decisions

objective_name
objective_value
lower_bound
bound_scope
bound_source
bound_assumption_hash
optimality_gap
conflict_set

feasibility_status
feasibility_certificate
certificate_scope
certificate_hash

producer_solver
producer_config_hash
created_at_monotonic_ns
provenance_hash
```

约束：

1. `lower_bound` 未注明 scope、来源和假设时不得传递；
2. FJSP feasible schedule 不自动等于联合 FJSP-MAPF feasible；
3. MAPF path reuse 必须绑定 agent、start/goal、reservation 和 frozen-prefix hash；
4. B 导入后必须重新验证它负责域内的可行性；
5. 任何字段语义无法映射时，pair 标记为 incompatible，不得静默丢弃约束。

### 4.2 NativeSolverCheckpoint

solver 私有搜索状态与 `IncumbentBundle` 分离：

```text
schema_version
solver_identity
solver_version
config_hash
problem_hash
snapshot_hash
native_checkpoint_uri
native_checkpoint_sha256
created_at_monotonic_ns
```

私有状态示例：

```text
CP-SAT search state / bound state
DE population
PSO velocity and personal-best state
MAPF-LNS neighborhood history
remote solver session state
```

规则：

```text
A -> A:
  可以使用 NativeSolverCheckpoint

A -> B:
  只允许使用 Portable IncumbentBundle
```

若 A 不支持 native checkpoint，本协议仍可保留 `A uninterrupted`，但
`A native checkpoint-resume` 标记为 unsupported。不得把
`A restart from IncumbentBundle` 与 native resume 合并。

## 五、Orchestration Adapter Contract

每个候选 adapter 必须明确支持或拒绝以下能力：

```text
start(problem, config, budget_context)
observe()
export_incumbent()
import_warm_start(bundle)
native_checkpoint()
native_resume(checkpoint)
continue_run(delta_budget)
stop(reason)
cleanup()
audit()
```

每项返回：

```text
supported
status
started_at_monotonic_ns
completed_at_monotonic_ns
wall_time_ms
service_time_ms
request/session ids
input hash
output hash
deadline audit
error/fallback classification
```

Adapter Conformance Gate：

1. unsupported capability 显式返回，不得假成功；
2. `stop` 后无 late mutation；
3. `cleanup` 后无 active request、orphan session 或未释放缓存所有权；
4. export/import 结果可复放且 hash 稳定；
5. warm-start 后的解不劣于导入 incumbent，除非 solver 明确返回拒绝；
6. deadline 与 cancellation 可归因到具体阶段和具体 solver；
7. audit 能区分 solver failure、adapter failure 和 infrastructure failure。

当前 `SolverProfileActivator` 的 endpoint/config 切换和 cache reset 不视为满足该
contract。现有实验 runner 的文件级 `--resume` 也不视为 native solver resume。

## 六、五类必要对照

设总 planning budget 为 `T`，第一阶段 nominal budget 为 `T1`。所有对照从同一
immutable snapshot 开始。

### 6.1 A uninterrupted

```text
A(T)
```

A 连续运行到统一 selection cutoff，不执行中间 checkpoint、export/import 或
restart。允许只读 telemetry，但必须测量 telemetry 自身开销。

### 6.2 A native checkpoint-resume

```text
A(T1)
-> native checkpoint
-> observe
-> native resume
-> A(remaining budget)
```

用于测量控制器中断和 native resume 的代价。若 native resume 不受支持，该 cell
缺失并单独报告，不填充惩罚值。

### 6.3 B full budget

```text
B(T)
```

用于判断 B 是否本来就是更好的单 solver。

### 6.4 A 到 B cold switch

```text
A(T1)
-> export only for audit, not provided to B
-> stop and cleanup A
-> initialize B from standard initial state
-> B(remaining budget)
```

若 B 的合法启动本身必须接收可行 incumbent，则必须预注册该域的标准 cold-start
artifact；不得让 cold 与 warm 使用不同问题语义。

### 6.5 A 到 B warm switch

```text
A(T1)
-> export Portable IncumbentBundle
-> stop and cleanup A
-> initialize B
-> validate and import bundle
-> B(remaining budget)
```

B 最终结果必须记录：

```text
warm_start_accepted
warm_start_rejection_reason
imported_incumbent_hash
first_feasible_time
first_improvement_time
best_final_incumbent
```

## 七、预算与公平性

### 7.1 End-to-end wall budget

统一计时从第一阶段 solver 初始化前开始，到最终候选结果完成 branch/result audit
并 ready-to-commit 为止。下列时间全部计入：

```text
A initialization and solving
telemetry
checkpoint/export
A stop and cleanup
B initialization
warm-start validation/import
B solving
controller inference
branch/result audit
```

不得给 switching arm 额外免费转换时间。

### 7.2 Commit reserve

设 Root 总 wall budget 为 `B_root`，最终 global health check 和 atomic commit 保留为
`R_commit`：

```text
T = B_root - R_commit
```

`R_commit` 不得用于 solver、transfer、branch/result audit 或 controller inference，
也不得与 `T` 内已计时的 branch/result audit 重复计算。

任何阶段开始前必须检查其 admission upper bound。若剩余时间不足：

```text
不得启动新 solver
尝试认证当前 incumbent
认证失败则执行 frozen fallback
```

### 7.3 资源成本

第一版公平性的主约束是相同 end-to-end wall deadline。另行记录并设置上界：

```text
solver compute time
orchestration overhead
total service-seconds
peak concurrent services
memory/GPU peak when applicable
```

wall time 与 service-seconds 不要求数值完全相等，但都必须报告。若要比较
compute-normalized 效果，必须作为独立资源 regime 预注册，不能事后切换口径。

### 7.4 Stage split

`T1/T` 是 action 的一部分。它必须：

1. 在独立 construction/tuning cohort 上选择；
2. 在 confirmation 前冻结；
3. 不得根据 confirmation heldout 结果调整；
4. 若比较多个 split，预注册多重比较修正或预注册单一 primary split。

本文当前不冻结具体 `T`、`T1` 和 split grid，因此状态保持
`DRAFT_NOT_EXECUTABLE`。

## 八、随机流与信息边界

### 8.1 Planning streams

同一 snapshot 下所有 alternatives 使用成对 planning external streams：

```text
arrival
failure/recovery
processing time
travel time
other environment disturbances
```

solver-internal stream 与 external streams 分离。不同 solver 的随机数消费顺序不得
改变外部随机世界。

### 8.2 Heldout execution streams

最终评价使用与 planning 独立的 heldout execution streams：

```text
planning seed namespace != heldout seed namespace
```

禁止让 planning rollout 命中 heldout future。

### 8.3 Solver seed policy

每个 solver 的 seed mapping、restart seed 和 warm/cold seed 规则必须冻结。若
checkpoint-resume 改变随机数消费，这是 intervention 的一部分，必须通过重复 seed
估计，而不是静默重置为有利轨迹。

## 九、双时钟和 stale-plan 边界

### 9.1 首轮采用冻结物理状态

第一版机制实验只采用：

```text
physical system paused/frozen during planning
shadow solver clock advances
physical state does not advance
```

这样可以隔离 solver transfer 价值，不混入 stale-plan 误差。

### 9.2 在线继续执行模式暂不纳入

若物理系统在 planning 时继续执行，状态必须增加：

```text
snapshot_time
decision_cutoff_time
commit_time
frozen_prefix
predicted physical evolution
staleness audit
```

并且只允许提交在 commit 时仍有效的短前缀。该模式属于后续 rolling-horizon 协议，
不能用首轮冻结系统结果替代。

## 十、Trajectory 日志

所有轨迹使用 monotonic clock，并以 append-only 事件流记录：

```text
schema_version
experiment_id
cluster_id
alternative_id
stage_id
event_index
timestamp_monotonic_ns
elapsed_wall_ms
remaining_wall_ms

solver
solver_version
config_hash
solver_internal_phase
restart_count

incumbent_id
incumbent_hash
current_objective
best_objective
lower_bound
optimality_gap
feasibility_status
conflict_count
path_cost
schedule_perturbation

improvement_delta
time_since_last_improvement_ms
improvement_window_history

transition_mode
switch_reason
checkpoint_status
export_status
cleanup_status
import_status
warm_start_status

solver_compute_ms
orchestration_overhead_ms
service_seconds
audit_status
```

轨迹研究目标是估计：

\[
\mathbb{E}\left[
J(t+\Delta t)-J(t)
\mid x_t,\ \text{continue solver } a
\right]
\]

当前改善斜率只能作为特征，不得直接定义为未来继续价值。

## 十一、Pairwise Transfer Matrix

### 11.1 首轮允许小规模完整测量

对通过 compatibility Gate 的少量同域 solver，可以完整运行合法有向 pair。其目的
是建立 transfer mechanism matrix，不是定义长期在线枚举框架。

每个 pair 至少报告：

```text
cold final cost
warm final cost
warm-start acceptance rate
time to first feasible
time to first improvement
export/import/cleanup overhead
deadline/failure rate
physical validity
```

### 11.2 长期扩展

solver 数量扩大后，不要求永久全量枚举。后续可以研究：

```text
compatibility model
active experimental design
learned pair proposer
uncertainty-aware onboarding
```

但每个 confirmation experiment 仍必须冻结 archive version 和 action grammar。

## 十二、统计分析

### 12.1 五类 primary contrasts

成本越低越好，定义：

```text
checkpoint overhead:
  J(A checkpoint-resume) - J(A uninterrupted)

warm-start value:
  J(A -> B cold) - J(A -> B warm)

switch vs continue:
  J(A checkpoint-resume) - J(A -> B warm)

prefix value for B:
  J(B full budget) - J(A -> B warm)

switch vs uninterrupted:
  J(A uninterrupted) - J(A -> B warm)
```

每个 contrast 必须使用同一 snapshot、成对 planning stream 和独立 heldout stream。

### 12.2 Sequence headroom

分别计算：

\[
J_{\mathrm{SBS}}^{\mathrm{single}},
\quad
J_{\mathrm{SBS}}^{\mathrm{cold\ sequence}},
\quad
J_{\mathrm{SBS}}^{\mathrm{warm\ sequence}},
\quad
J_{\mathrm{VBS}}^{\mathrm{cold\ sequence}},
\quad
J_{\mathrm{VBS}}^{\mathrm{warm\ sequence}}
\]

并分解：

```text
fixed sequence value:
  single SBS - warm-sequence SBS

state-conditional sequence headroom:
  warm-sequence SBS - warm-sequence VBS

controller regret:
  controller - warm-sequence VBS
```

warm 与 cold 必须分别报告，不能只报告 warm oracle。

### 12.3 Confirmatory rules

1. construction、split tuning、controller tuning 和 final confirmation cohort 分离；
2. confirmation 前冻结 primary contrast、样本量和 bootstrap unit；
3. 同一 base instance 的相关故障归入同一 cluster；
4. 使用 cluster-level paired bootstrap 或预注册的 paired randomization test；
5. failure、timeout 和 invalid outcome 按预注册 ITT cost 进入主 endpoint；
6. 成功分支质量、failure rate 和 overhead 作为分项报告；
7. 不得用 sequence oracle 作为可执行 controller 的效果；
8. 不得在 confirmation cohort 上选择 pair、T1 或 warm-start mapping；
9. 多 pair 或多 split 的 primary claim 必须控制多重比较；
10. post-hoc subgroup 只标记为 diagnostic。

### 12.4 Confirmation 前的样本量

样本量必须由 pilot 中的 paired effect、cluster variance、warm-start acceptance rate
和 infrastructure failure rate 联合确定。不得机械复用 40-cluster Root cohort。

## 十三、安全 Gate

### Gate A：Adapter Conformance

```text
all declared capabilities tested
unsupported capabilities explicit
no late mutation
no orphan request/session
replay/provenance hash stable
```

### Gate B：Transfer Validity

```text
bundle schema valid
scope and assumptions compatible
warm import reproducible
imported incumbent feasible
no objective or constraint loss
```

### Gate C：Budget Accounting

```text
all overhead included
selection cutoff respected
commit reserve preserved
service usage reported
```

### Gate D：Mechanism Value

在独立 confirmation cohort 上：

```text
primary warm-start contrast direction positive
paired confidence interval satisfies preregistered threshold
effect not explained only by B full-budget superiority
```

### Gate E：Safety Non-Regression

```text
physical violations = 0
atomic commit violations = 0
late active request/session residue = 0
deadline accounting omissions = 0
```

任一基础设施或安全 Gate 失败，不得以质量收益覆盖。

## 十四、执行阶段

### P0：安全基线

```text
保留旧 Root Search
独立确认 branch-local certification
不修改旧 publication Gate
```

### P1：Adapter 与 Schema

```text
Portable IncumbentBundle
NativeSolverCheckpoint
compatibility matrix
adapter conformance tests
trajectory event schema
```

### P2：Instrumentation Pilot

```text
uninterrupted trajectory
telemetry overhead
native checkpoint-resume overhead
cold/warm import overhead
deadline and cleanup evidence
```

仅用于冻结 `T`、`T1`、合法 pair 和样本量。

### P3a：Pairwise Transfer Experiment

执行五类必要对照：

```text
A uninterrupted
A native checkpoint-resume
B full budget
A -> B cold
A -> B warm
```

### P3b：Sequence Headroom Analysis

```text
single SBS
cold/warm fixed-sequence SBS
cold/warm sequence VBS
switch overhead
compatibility and failure matrix
```

### P4：Two-Stage Controller

仅在 P3 通过后，学习：

\[
\pi(B \mid x_1, A)
\]

首版优先：

```text
frozen rules
decision tree
gradient boosting
cost-sensitive regressor/classifier
```

输出限定为：

```text
continue A
switch to certified B
commit current incumbent
fallback
```

### P5：Rolling-Horizon Orchestration

引入物理继续执行、frozen prefix、staleness audit 和 repeated replanning。

### P6：Options-MCTS / Constrained RL

仅在状态、option、transfer、cost 和 safety transition 稳定后启动。

## 十五、停止条件

以下任一条件成立时，不进入 Two-Stage Controller：

1. 没有异构 pair 通过 Transfer Validity Gate；
2. warm import 经常拒绝或破坏 incumbent；
3. checkpoint/orchestration overhead 吞噬全部潜在收益；
4. warm switch 不优于 cold switch；
5. warm switch 的收益可完全由 B full budget 解释；
6. sequence SBS 不优于 single SBS；
7. switching 引入 deadline、cleanup 或物理安全回归；
8. sequence headroom 只存在于用于选 pair 的 development cohort。

停止不代表长期 orchestration 必然无效，只表示当前 adapter、solver 集合或预算区间
没有足够证据支持进入策略学习。

## 十六、待冻结清单

本文转为 `FROZEN_FOR_PILOT` 前必须补齐：

```text
code commits and immutable images
adapter schema version
trajectory schema version
IncumbentBundle schema version
NativeSolverCheckpoint schema version
compatibility matrix
candidate same-domain pairs
standard cold-start semantics
total wall budgets
commit reserve
T1/T tuning grid
planning and heldout seed namespaces
construction/tuning/confirmation cohorts
primary contrast
failure-as-cost rule
sample-size calculation
bootstrap/test procedure
multiple-comparison procedure
```

## 十七、最终研究边界

本协议若通过，只授权以下结论：

> 在冻结物理 snapshot、严格 end-to-end wall budget 和完整审计下，至少一个
> 预注册同域 solver pair 的 warm two-stage sequence 相对必要单 solver、resume、
> full-budget 和 cold-switch controls 显示可重复的净价值。

本协议不授权：

```text
通用动态 solver orchestration 已解决
任意 solver 都适合 warm switching
多轮 MCTS/RL 必然有效
冻结系统结果可直接推广到物理继续执行模式
当前 pairwise matrix 是永久封闭 portfolio
```

## 十八、P1 Contract 实现记录

2026-08-06 已在可修改开发仓库新增：

```text
codebase/SkyEngine/experiment/skycausal/solver_orchestration_contract.py
codebase/SkyEngine/experiment/skycausal/solver_trajectory.py
codebase/SkyEngine/experiment/skycausal/fjsp_orchestration_adapter.py
codebase/SkyEngine/experiment/skycausal/two_stage_instrumentation.py
codebase/SkyEngine/experiment/skycausal/protocols/
fjsp_two_stage_capability_audit_v0.json
codebase/SkyEngine/test/skycausal/test_solver_orchestration_contract.py
codebase/SkyEngine/test/skycausal/test_solver_trajectory.py
codebase/SkyEngine/test/skycausal/test_fjsp_orchestration_adapter.py
codebase/SkyEngine/test/skycausal/test_two_stage_instrumentation.py
```

已实现：

```text
PortableIncumbentBundle v1
NativeSolverCheckpoint v1
SolverAdapterDescriptor v1
AdapterOperationAudit v1
SolverOrchestrationAdapter abstract contract
directed deny-by-default SolverCompatibilityMatrix v1
append-only SolverTrajectoryEvent/Log v1
canonical hash and round-trip verification
tamper detection
monotonic trajectory validation
```

Compatibility validation 当前强制：

1. unknown pair 默认拒绝；
2. same-domain rule 不得静默跨 FJSP/MAPF；
3. warm switch 要求完整 A/B lifecycle capabilities；
4. warm switch 要求 source export、target import；
5. portable schema version 必须相交并由 rule 冻结；
6. source/target 必须共享预注册 safe switch boundary；
7. native checkpoint-resume 只允许同一 solver contract；
8. unsupported capability 必须显式记录为 `unsupported`；
9. cancel acknowledgement 失败时 request 保持 `unresolved`，阻止 snapshot、
   cleanup Gate 和结果提交。

验证结果：

```text
new orchestration contract/trajectory/FJSP adapter/instrumentation tests:
  48/48 PASS

existing solver profile activation tests:
  5/5 PASS

existing decision backend tests:
  9/9 PASS

full test/skycausal regression:
  277/277 PASS
```

当前限制：

1. 已实现 single-shot stateless FJSP adapter，尚未实现具体 MAPF
   orchestration adapter；
2. 只有 orchestration-dev CP-SAT 支持 portable schedule hint；冻结 CP-SAT
   image、DE 和 PSO 均不声明 warm-start import；
3. 当前 `SolverProfileActivator` 仍是 endpoint/config 切换和 cache reset，不是
   orchestration adapter；
4. 当前 runner 的文件级 `--resume` 不是 native solver checkpoint-resume；
5. 尚未冻结具体 compatibility matrix、pair、budget、cohort 或 primary contrast；
6. 只完成单 fixture instrumentation smoke，尚未采集 cohort trajectory；
7. cooperative stop 后可恢复 portable incumbent，但尚未冻结 live decision
   rule、budget 和 cohort；
8. 尚未运行 P2 instrumentation pilot。

因此本文状态继续保持：

```text
DRAFT_NOT_EXECUTABLE
```

## 十九、首轮真实 Capability Audit

2026-08-06 已完成 CP-SAT、DE、PSO、EECBS、LG-LaCAM 和 MAPF-LNS2 的代码级
capability audit。机器可读记录：

```text
codebase/SkyEngine/experiment/skycausal/protocols/
fjsp_two_stage_capability_audit_v0.json
```

状态固定为：

```text
DEVELOPMENT_ONLY_NOT_FROZEN
allowed_for_pilot = false
```

### 19.1 FJSP 结论

当前冻结 FJSP 服务均为 stateless `/solve` worker：

1. DE/PSO 可以返回完整 schedule artifact；
2. DE/PSO 不导出 population、personal best、velocity 或 RNG continuation state；
3. CP-SAT 原冻结版本不接受 schedule hint；
4. SkyEngine 的 solver/gateway `get_state/set_state` 恢复回放、ledger 和 artifact
   cache，不是 optimizer native checkpoint-resume；
5. 三个服务均有 request-level hard deadline、cancel 和 worker cleanup audit。

因此不得声明：

```text
DE native resume
PSO native resume
CP-SAT native resume
DE population -> CP-SAT transfer
PSO population -> CP-SAT transfer
```

首轮只实现可移植 schedule transfer：

```text
DE/PSO schedule artifact
-> independent residual FJSP feasibility audit
-> PortableIncumbentBundle
-> CP-SAT schedule AddHint
```

CP-SAT 开发实现新增：

```text
warm-start schema:
  skyengine.fjsp-schedule-warm-start.v1

validation:
  schema version
  operation identity
  duplicate detection
  machine alternative validity
  integral residual start time
  complete operation coverage

audit:
  source bundle/incumbent
  hinted operation count
  expected operation count
  coverage
```

该功能只是 CP-SAT hint，不保证沿用原 solver 搜索状态，也不保证质量改善。

### 19.2 MAPF 结论

当前 MAPF `/init` 服务：

1. 计算并在 server session 内缓存 action trajectory；
2. `/plan` 消费缓存 action；
3. `/session` 支持 cleanup；
4. `/cancel` 支持 request cancellation；
5. `keep_shorter_cached_plan` 只比较同一 session 中重新求得的 candidate；
6. 不返回完整 portable paths；
7. 不接受外部 solver 生成的 initial paths；
8. MAPF-LNS2 CLI 只支持选择内部 initializer，不支持导入外部 path 文件；
9. rolling client `get_state/set_state` 通过重新求解和 seek 重建 playback cursor，
   不是 optimizer native checkpoint。

因此当前所有 MAPF cross-solver warm pair 继续 deny。不得将
`keep_shorter_cached_plan` 描述为 LG-LaCAM 到 MAPF-LNS2 warm transfer。

### 19.3 DE/PSO 到 CP-SAT End-to-End Smoke

使用：

```text
source:
  existing frozen DE and PSO services
  commit/image line: 5eadb479c0f0

target:
  isolated orchestration-dev CP-SAT image
  sha256:
  65680f3f8cd75da4c17ea5a9aab9a24840c44d596db57b619bdc5185df7ea741
```

执行链：

```text
same ResidualFJSPProblem
-> DE or PSO bounded /solve
-> schedule audit
-> certified PortableIncumbentBundle
-> CP-SAT bundle/hash/problem/scope validation
-> residual operation remap
-> CP-SAT AddHint
-> bounded /solve
-> target schedule audit
```

两个 source 分别独立执行一次，结果均为：

```text
source requests:             1
target requests:             1
hinted operations:           3
expected operations:         3
hint coverage:               1.0
source active requests end:  0
target active requests end:  0
source objective:            5.0
target objective:            5.0
mechanism Gate:              PASS
quality claim:               NOT AUTHORIZED
```

DE 和 PSO smoke 的 source/target objective 在该 fixture 上均为 `5.0 -> 5.0`。
该相等结果不构成 warm start 有益或无益的证据。

两个临时 target 容器均已删除；publication v2 的三个 FJSP 和三个 MAPF 长期运行
容器未重启、未替换、未修改。

### 19.4 当前可进入的下一阶段

目前只授权：

```text
P2 instrumentation preparation
DE/PSO -> CP-SAT trajectory collection design
```

仍不授权：

```text
two-stage pilot execution
warm-start quality conclusion
portfolio/controller training
MAPF warm switching
native checkpoint-resume comparison
```

## 二十、P2 Instrumentation Preparation

已新增严格 end-to-end wall-budget runner：

```text
experiment/skycausal/two_stage_instrumentation.py
```

当前支持：

```text
A uninterrupted / single full-budget stage
B full-budget stage
A -> B cold switch
A -> B warm switch
```

当前不支持：

```text
A native checkpoint-resume
multi-round switching
physical system continues during planning
automatic controller decisions
```

### 20.1 Budget 语义

Runner 固定：

```text
selection budget = total wall budget - commit reserve
```

以下操作全部消耗 selection budget：

```text
adapter start
solver run
observe
incumbent export
source cleanup/audit
target start
warm import
target run
target cleanup/audit
trajectory serialization
```

每次 solver run 的 admitted budget 是 hard upper bound，不是实际消耗。stage A 若提前
结束，stage B 可使用剩余真实 wall time；因此两个 stage 的 admitted upper bounds
之和可以大于 selection budget，但实际 end-to-end wall time不得超过 selection
deadline。

任一步骤失败时：

1. 执行 failure cleanup；
2. 写入 failure audit；
3. 保留 append-only trajectory；
4. `commit_ready = false`；
5. 不借用 commit reserve。

### 20.2 Trajectory 事件

成功 warm sequence 记录：

```text
stage A:
  start
  run
  observe
  export
  cleanup
  audit

stage B:
  start
  import
  run
  observe
  export
  cleanup
  audit
```

每个事件绑定：

```text
monotonic timestamp
elapsed and remaining wall time
solver/config identity
incumbent and objective
transition mode
operation wall/service time
deadline and cleanup audit
event hash
```

整个 log 和 result 另有独立 canonical hash。

### 20.3 真实服务 Instrumentation Smoke

单 fixture 使用冻结 DE source 和隔离的 orchestration-dev CP-SAT target：

```text
transition mode:          warm_switch
trajectory events:       13
admitted stage A:        1000 ms
admitted stage B:        2592 ms
end-to-end wall:         602.518 ms
remaining selection:     2197 ms
commit reserve:          200 ms
transition wall:         0.320 ms
deadline overrun:        false
commit ready:            true
terminal objective:      5.0
```

说明：

1. `1000 + 2592` 是两个 solver 的 admission upper bounds，不是实际 wall 消耗；
2. 时间只对应该 fixture 和当前机器，不得用于选择正式 `T/T1`；
3. objective `5.0` 不构成 warm-start 质量证据；
4. smoke 只验证计时、日志、认证和 reserve 语义；
5. 临时 target 容器已删除，冻结 publication 容器未修改。

P2 状态：

```text
instrumentation preparation: PASS
instrumentation pilot:       NOT STARTED
budget freeze:               NOT AUTHORIZED
quality claim:               NOT AUTHORIZED
```

### 20.4 Solver 内部 Anytime Trajectory

2026-08-07 已为 DE、PSO 和 CP-SAT 开发版本新增统一格式：

```text
skyengine.fjsp-solver-progress-trace.v1
```

每个 trace 固定：

```text
objective_name
objective_sense
time_origin
sampling
events[]

event:
  event_index
  event_type
  elapsed_ms
  incumbent_objective
  best_bound
  work
```

采样语义：

```text
DE:
  population initialization 后记录 initial
  每代记录 improvement 或 checkpoint
  终止时记录 final

PSO:
  population initialization 后记录 initial
  每代记录 improvement 或 checkpoint
  终止时记录 final

CP-SAT:
  solution callback 记录 initial/incumbent
  同时记录 best objective bound
  终止时记录 final
```

内部 `elapsed_ms` 的 time origin 是 optimizer invocation，不包含完整 HTTP、
worker process、adapter、transfer 和 audit overhead。公平比较仍以 runner 的
end-to-end wall 为准。

SkyEngine strict adapter 新增：

```text
skycausal.fjsp-solver-progress-audit.v1
```

它强制检查：

1. schema version；
2. event index 连续；
3. elapsed time 单调且有限；
4. minimization incumbent 不恶化；
5. bound 为有限数或 null；
6. first event 为 `initial`；
7. last event 为 `final`；
8. terminal objective 与 artifact makespan 一致；
9. trace terminal time 不越过 solver-reported wall time；
10. canonical trace hash。

P2 adapter 使用：

```text
require_solver_progress_trace = true
```

缺失、畸形或终态不一致的 trace 会使 `continue_run` 返回 `failed`，随后进入
failure cleanup/audit，不允许 commit。

新增验证：

```text
SkyEngine full regression:        277/277 PASS
solver progress trace tests:          6/6 PASS
CP-SAT container artifact tests:      7/7 PASS
```

开发镜像：

```text
DE:
  sha256:4be6774752f9fc58d65b7f64a63441a473162bb41b9faa2e786740e730fcdd5f

PSO:
  sha256:5fe7f109c1a4cbe00351ac15218bc9c4eb4a30373f530fbb3af828f061b2ab38

CP-SAT:
  sha256:5f3590cb013ab4794a1d1f54ad24a631133cf88ffd7098e2db767d1670f8fb4a
```

### 20.5 Strict Trace End-to-End Smoke

同一三工序 fixture、`T=3000 ms`、commit reserve `200 ms`、
`T1=1000 ms`：

```text
DE -> CP-SAT warm:
  commit ready:                  true
  end-to-end wall:               424.911 ms
  transition wall:                 0.339 ms
  DE trace events:               12
  DE improvements:                0
  DE optimizer terminal:          2.827 ms
  CP-SAT trace events:            2
  CP-SAT improvements:            0
  CP-SAT optimizer terminal:      1.959 ms

PSO -> CP-SAT warm:
  commit ready:                  true
  end-to-end wall:               431.245 ms
  transition wall:                 1.412 ms
  PSO trace events:              12
  PSO improvements:               0
  PSO optimizer terminal:         1.114 ms
  CP-SAT trace events:            2
  CP-SAT improvements:            0
  CP-SAT optimizer terminal:      2.015 ms
```

该 smoke 说明：

1. internal optimizer time 与 end-to-end stage time 是不同口径；
2. 微型 fixture 中 process/HTTP/audit overhead 主导 wall time；
3. 两个 source 均从 `5.0` 开始并以 `5.0` 结束；
4. target 同样为 `5.0 -> 5.0`；
5. 零 improvement 不构成算法互补性结论；
6. 这些时间不得用于冻结正式 `T/T1`；
7. 该 smoke 使用的 trajectory-dev image 只在 stage 返回后暴露 trace；live
   observation 见 20.6；
8. 临时容器已删除，publication 冻结服务未修改。

因此该阶段只新增授权：

```text
post-stage offline trajectory collection design
strict trace data-quality Gate
```

仍不授权：

```text
P2 cohort execution
live adaptive switching
budget/T1 freeze
quality or complementarity claim
```

### 20.6 Live Observation Contract

2026-08-07 新增：

```text
service:
  GET /progress/<request_id>

gateway:
  begin_solve
  observe_request
  await_request
  forget_request

adapter capabilities:
  start_run
  live_observe
  await_run
```

`/solve` 继续作为唯一最终 artifact 通道。`begin_solve` 只是在 client 后台线程中
调用原 `/solve`；没有新增第二套 worker 或结果状态机。

active worker 使用原子 snapshot：

```text
skyengine.fjsp-live-progress.v1

request_id
solver_id
status
updated_at_unix_ns
trace_schema_version
event_count
latest_event
```

写盘策略：

1. `initial`、`improvement` 和 `final` 强制刷新；
2. checkpoint 按最小时间间隔节流；
3. snapshot 只保存 latest event，不重复写完整历史；
4. stage 正常结束后，最终 artifact 仍携带完整 progress trace；
5. progress 读取失败不伪造 incumbent；
6. active 或 unresolved request 继续阻止 gateway snapshot/restore。

同步 `continue_run` 语义未修改。异步路径必须显式调用：

```text
start
start_run
observe...
await_run
export_incumbent
cleanup
audit
```

### 20.7 Live Observation Smoke

开发 fixture：

```text
jobs:                 10
operations per job:   5
machines:              6
```

结果：

```text
DE:
  mode:                         live then hard cancel
  polls to first incumbent:     9
  live events:                  1
  live objective:              56.0
  stop status:                 completed
  orphan requests:              0
  cancelled incumbent usable:  false

PSO:
  mode:                         live then complete
  polls to first incumbent:     8
  live events:                  1
  live objective:              56.0
  final events:               423
  final objective:             17.0
  await status:                completed
  orphan requests:              0

CP-SAT:
  mode:                         live then complete
  polls to first incumbent:    21
  live events:                  2
  live objective:             244.0
  final events:               121
  final objective:             26.0
  await status:                completed
  orphan requests:              0
```

验证：

```text
SkyEngine full regression:          277/277 PASS
core orchestration focused tests:     48/48 PASS
async gateway focused tests:            2/2 PASS
deadline/live progress tests:           4/4 PASS
solver progress trace tests:            6/6 PASS
CP-SAT container artifact tests:        7/7 PASS
```

live-dev images：

```text
DE:
  sha256:82a419ecf1effda7cdfe2d6998be664d3e55546dce40d9281590be5376492453

PSO:
  sha256:8f289396cd98a51d24c691f701020b1895a6e0b1bf9f29ff26c89e8540bc215a

CP-SAT:
  sha256:2f85963797cef9e22ae57e8cabf2a42ce01880828d15055dddfb890d3893166d
```

临时容器已删除；publication 冻结服务未修改。

### 20.8 Hard Cancel Blocker

当前 `/cancel` 仍通过 process `SIGTERM/SIGKILL` 强制终止。live snapshot 只含
objective/bound/work，不含完整 schedule artifact。因此：

```text
live observation:                      AUTHORIZED
normal completion + final export:      AUTHORIZED
hard cancel cleanup:                   AUTHORIZED
hard cancel + incumbent export:        NOT SUPPORTED
live observation -> safe warm switch:  NOT AUTHORIZED
```

下一 Gate 必须是 cooperative stop：

1. parent 写入 stop request；
2. DE/PSO 在 generation boundary 检查；
3. CP-SAT callback 调用 `stop_search`；
4. worker 用当前 incumbent 生成完整 schedule artifact；
5. independent feasibility audit 通过；
6. 然后才允许 source export 和 target warm import。

在该 Gate 通过前，不得用 live objective slope 触发真实 solver switch，也不得启动
P2 controller cohort。

### 20.9 Cooperative Stop Contract

2026-08-07 已新增：

```text
service:
  POST /stop/<request_id>

gateway:
  request_stop

adapter capability:
  request_stop
```

cooperative stop 与 hard cancel 严格分离：

```text
/stop:
  写入 skyengine.fjsp-cooperative-stop.v1 marker
  不设置 cancel_reason
  不发送 signal
  等待 worker 正常生成 artifact

/cancel:
  保留 SIGTERM/SIGKILL hard fallback
  不承诺恢复 incumbent
```

solver safe boundary：

```text
DE:
  generation boundary

PSO:
  generation boundary

CP-SAT:
  solution callback stop_search
  watchdog stop_search when no new callback arrives
```

异步切换 source 的必要顺序：

```text
start
start_run
observe until finite incumbent
request_stop
await_run
independent schedule audit
export PortableIncumbentBundle
cleanup
audit
```

`request_stop` 在 adapter 已观察到 finite incumbent 前一律拒绝，防止 CP-SAT 在首个
可行解之前停止而无法生成 artifact。

deadline audit 升级为：

```text
skyengine.fjsp-deadline-audit.v2

cooperative_stop_requested_at_unix_ns
cooperative_stop_reason
termination_signal
```

成功 cooperative stop 必须满足：

```text
worker status:        completed
stopped_by:           process_exit
termination_signal:   null
schedule audit:       passed
active requests end:  0
```

### 20.10 Cooperative Stop Warm-Switch Smoke

DE/PSO source fixture：

```text
jobs:                 5
operations per job:   3
machines:              4
```

结果：

```text
DE -> CP-SAT:
  polls to incumbent:       13
  live objective:           29.0
  stopped objective:        29.0
  source trace events:      11
  source schedule:          certified
  termination signal:       null
  target objective:          9.0
  CP-SAT hints:             15/15
  hint coverage:             1.0
  source/target orphans:      0/0

PSO -> CP-SAT:
  polls to incumbent:       13
  live objective:           12.0
  stopped objective:         9.0
  source trace events:      24
  source schedule:          certified
  termination signal:       null
  target objective:          9.0
  CP-SAT hints:             15/15
  hint coverage:             1.0
  source/target orphans:      0/0
```

CP-SAT source 使用较大 `10 jobs × 5 operations × 6 machines` fixture：

```text
polls to incumbent:             30
live objective:                251.0
stopped objective:             239.0
trace events:                    4
cooperative_stop_requested:   true
termination signal:           null
orphan requests:                 0
source schedule:              certified
```

这些 objective 只证明 stop 到 artifact 的机制完整，不构成 DE/PSO/CP-SAT 质量或
互补性结论。

cooperative smoke images：

```text
DE:
  sha256:4bcf5772141f1757a4071c85e30257b096d6ad4cfcf5084c668b437e62221f05

PSO:
  sha256:ec84d3ef282b2ac9380fac91100d95f25d2487d38c828dccc1226802bb7b1ff4

CP-SAT:
  sha256:2ef5219ec4e3ca96bd2a64b4ef179feafe8e632efbcfcad19e7d1e0a00d942e0
```

临时容器已删除；publication 冻结服务未修改。

### 20.11 额外发现：双位数加工时长截断

独立 schedule audit 首次拒绝中型 DE artifact：

```text
duration_mismatch:3:1
```

根因是 DE/PSO online encoder 使用：

```text
np.full(..., "-", dtype=str)
```

NumPy 将字符串宽度固定为 1，导致 `10/11/12` 被截断。已改为 object dtype，并
新增双位数 `12` 时长回归测试。不得将修复前中型 DE/PSO 结果用于实验。

### 20.12 当前授权边界

```text
live observation mechanism:             AUTHORIZED
cooperative stop mechanism:             AUTHORIZED
stopped incumbent certification:        AUTHORIZED
DE/PSO -> CP-SAT warm transfer:         AUTHORIZED FOR DEVELOPMENT
hard cancel incumbent recovery:         NOT SUPPORTED
controller decision rule:               NOT FROZEN
P2 cohort:                              NOT AUTHORIZED
budget/T1 selection:                    NOT AUTHORIZED
quality/complementarity claim:          NOT AUTHORIZED
```

cooperative stop Gate 已通过。下一步不应直接训练 controller，而应冻结 development
pilot 的 pair、cohort、`T/T1` grid、seed namespace、poll interval、primary
contrast 和 abort threshold。

## 二十一、Development Pilot 预注册

2026-08-07 已冻结机器可读设计：

```text
experiment/skycausal/protocols/fjsp_two_stage_pilot_v0.json

schema:
  skycausal.fjsp-two-stage-pilot.v1

SHA256:
  169d7cc7ffb5edec8ecd06b7ee3462b96404386c8f1048cc09fd28dd5692a91f

status:
  SPEC_FROZEN_EXECUTION_BLOCKED
```

### 21.1 Pair 与 Controls

development pilot 只允许：

```text
DE  -> CP-SAT
PSO -> CP-SAT
```

每个 source 必须登记五类 control：

```text
A uninterrupted:          required
A native checkpoint:      unsupported
B full budget:            required
A -> B cold:              required
A -> B warm:              required
```

DE/PSO 当前没有 native optimizer checkpoint。该 control 必须在 manifest 中保留
`unsupported`，不得用 cold restart 冒充。因此 pilot 可以用于 pair/split tuning，
但在 native checkpoint control 缺失时不能支持完整五对照 confirmation claim。

### 21.2 Cohort 隔离

旧范围：

```text
100..149
200..239
300..349
```

已有 development 或 publication outcome 被查看，禁止复用为新 pilot 或
confirmation。

pilot candidate：

```text
state seeds:                 400..419
topologies:                  maze / maze-b
selection:                   每个 topology 按 seed 升序取前 4 个 eligible
snapshot capture:            2 次
eligibility:                 两次均 eligible 且 semantic signature 相同
expected clusters:           8
insufficient cohort policy:  abort，不扩 seed range
```

未来 confirmation reservation：

```text
state seeds:                 500..559
minimum target:              每个 topology 20
pilot 期间:                  禁止 capture 或查看
```

confirmation 样本量只能根据 pilot 的 cluster variance、paired effect、warm
acceptance 和 infrastructure failure rate 计算后，在新协议中冻结。

### 21.3 Random Streams

每个 snapshot 使用三个 solver replicates。solver seed 由固定公式生成：

```text
base
+ topology_code * 1_000_000
+ state_seed * 1_000
+ replicate_index * 10
+ solver_code
```

namespace：

```text
pilot base:          80_000_000
confirmation base:   90_000_000
order base:          81_000_000

solver codes:
  DE:       1
  PSO:      2
  CP-SAT:   3
```

同一 block 内，同一 solver 在 full/cold/warm arm 使用相同 solver seed。arm 顺序按
`SHA256(order_seed, arm_id)` 排序，禁止操作者手工调整。

### 21.4 Budget Grid

所有预算均为 end-to-end wall：

```text
T:
  5000 ms
  10000 ms
  12000 ms

primary T:
  12000 ms

commit reserve:
  200 ms

cooperative finalize reserve:
  250 ms

poll interval:
  10 ms
```

`T1` 是 selection budget `T - commit reserve` 的固定比例：

| T | 25% | 50% | 75% |
|---:|---:|---:|---:|
| 5000 ms | 1200 ms | 2400 ms | 3600 ms |
| 10000 ms | 2450 ms | 4900 ms | 7350 ms |
| 12000 ms | 2950 ms | 5900 ms | 8850 ms |

source 在 `T1 - 250 ms` 进入 cooperative finalization guard；terminal solver 在
selection cutoff 前同样保留 250 ms。若 solver 提前正常结束，接受已认证 artifact，
不得人为 sleep 到 nominal cutoff。若 guard 前没有 finite incumbent，记为
algorithmic capped failure，不得作为 infrastructure exclusion。

### 21.5 Capped Failure

每个 snapshot 的 cap 在执行前由问题本身确定：

```text
max(
  current_time,
  machine_available_at,
  frozen_operation_end
)
+ sum(max processing time over alternatives for each residual operation)
```

合法预算内没有可行 incumbent 时赋 cap。成功 arm 使用
`min(certified makespan, cap)`。禁止根据 outcome 删除失败 arm。

### 21.6 Pilot Selection Rule

每个 `(source, T1)` cell 的三个 paired contrast：

```text
J(cold)   - J(warm)
J(A full) - J(warm)
J(B full) - J(warm)
```

正值表示 warm 更好。cluster 是 physical snapshot；先对同一 cluster 的三个 solver
replicates 求均值，再执行 topology-stratified cluster bootstrap。

pilot cell score：

```text
三个 contrast 的 one-sided 80% LCB 的最小值
```

只在 primary `T=12000 ms`、全部 safety Gate 通过且 warm import acceptance
为 `1.0` 的 cell 中选择：

```text
maximize cell score
```

确定性 tie-break：

```text
1. 更小 T1
2. source solver id 字典序
```

若最佳 cell score `<= 0`：

```text
停止于 pilot
不授权 confirmation
不训练 controller
```

pilot 只用于 tuning 和 estimation，不产生 hypothesis-test claim。未来独立
confirmation 必须使用 paired test、cluster CI，并对三个 primary contrasts 做
`Holm` familywise correction。

### 21.7 Safety 与 Abort Gate

以下任一计数大于零立即停止：

```text
physical invariant violation
schedule audit failure
deadline overrun
orphan request
unresolved request
canonical hash mismatch
hard cancel after observed incumbent
infrastructure-invalid cluster
```

此外要求：

```text
warm import acceptance:  1.0
matrix cell coverage:    1.0
```

失败后必须保留全部 artifact，诊断并发布新协议版本；不得原地修改 protocol 后只补跑
失败 cell。

### 21.8 Preflight 与工作量

cohort capture 前，在不属于 pilot/confirmation 的历史 development snapshot 上执行：

```text
DE/PSO/CP-SAT cooperative stop:
  50 repetitions per solver

fixture:
  historical seed-140 snapshot
  snapshot SHA256: 92539be2...63226
  residual operations: 18
  residual problem hash: da6425ed...302e

execution:
  order: round-robin DE -> PSO -> CP-SAT
  solver seed base: 82_000_000
  solver budget: 5000 ms
  incumbent wait limit: 4500 ms
  poll interval: 10 ms
  cooperative finalization timeout: 250 ms
  percentile: R-7 linear
  fail fast: true

infrastructure-only overrides:
  DE maxgen: 10000
  PSO maxgen: 10000
  CP-SAT time limit: 5.0 s
  CP-SAT workers: 1

required:
  audit/deadline/orphan/signal/ack failures = 0
  finalization p99 <= 200 ms
  finalization max <= 250 ms
```

override 只用于确保每次请求实际进入 cooperative stop，不用于比较 objective。harness
按请求原子写入 canonical-hash record；resume 只允许补齐缺失 record，出现失败
record 后禁止覆盖重跑。

预注册最大工作量：

```text
clusters:                       8
replicates per cluster:         3
budget points:                  3
sequence arms:               1080
solver requests:             1944
```

协议一致性验证：

```text
pilot protocol invariant tests:    6/6 PASS
cooperative preflight tests:       6/6 PASS
live cutoff runner tests:          17/17 PASS
full test/skycausal regression:  298/298 PASS
JSON parse:                       PASS
Markdown code fences:             PASS
git diff --check:                 PASS
```

### 21.9 Live Cutoff Runner

已实现：

```text
LiveCutoffPolicy
TwoStageInstrumentationRunner.run_live_single
TwoStageInstrumentationRunner.run_live_switch
```

状态机严格区分：

```text
normal_completion:
  solver 在 guard 前自然完成

cooperative_stop:
  已观察 finite incumbent
  -> request_stop
  -> await artifact
  -> independent certification

no_incumbent_at_guard:
  algorithmic capped failure
  -> hard cleanup

cooperative finalization failure after incumbent:
  infrastructure/safety failure
  -> hard cleanup
  -> abort Gate
```

runner 额外保证：

1. source 和 terminal stop guard 使用绝对 monotonic deadline；
2. polling、stop、await、export/import、cleanup/audit 均消耗统一 selection wall；
3. unchanged poll 可压缩存储，但总 poll count、omitted audit count 和总 service time
   保留；
4. 缺少任一 live capability 时 deny，不回退到同步 `continue_run`；
5. normal completion 不伪装为 cooperative stop；
6. cold/warm sequence 最终保留 source/target 中 objective 更小的 certified
   incumbent，避免 target 退化人为惩罚 switching arm；
7. source/target bundle 的 objective、problem、snapshot 和 scope 不兼容时禁止结果
   提交。

真实非 cohort fixture：

```text
problem:                         5 jobs x 3 ops x 4 machines
mode:                            DE -> CP-SAT warm
T:                               5000 ms
commit reserve:                   200 ms
T1:                              1000 ms
cooperative finalize reserve:     250 ms
poll interval:                     10 ms

DE first incumbent:              237.709 ms
DE completion:                   cooperative_stop
DE finalization:                  46.183 ms
CP-SAT completion:               normal_completion
CP-SAT hints:                    15/15
hint coverage:                    1.0
final objective:                 10.0
end-to-end wall:               1316.906 ms
remaining selection wall:      3483 ms
source/target orphans:             0/0
commit ready:                    true
```

开发镜像：

```text
DE:
  sha256:4bcf5772141f1757a4071c85e30257b096d6ad4cfcf5084c668b437e62221f05

CP-SAT:
  sha256:2ef5219ec4e3ca96bd2a64b4ef179feafe8e632efbcfcad19e7d1e0a00d942e0
```

该 smoke 只证明 runner budget/stop/export/import 状态机贯通，不构成 objective 增益、
pair 互补性或 `T/T1` 合理性的证据。临时容器已删除。

### 21.10 Cooperative Stop Preflight Result

机器可读结果：

```text
experiment/skycausal/protocols/fjsp_cooperative_preflight_result_v0.json

status:
  PASS

result hash:
  4674b7aac1c74419aea530063a4eb770cad0609ea71775c69b956af7fe136f21

result file SHA256:
  035a1d2539bb085c84fead556a774b328f28c0f1fb6775e357bbd09eb607fce6

executed protocol SHA256:
  169d7cc7ffb5edec8ecd06b7ee3462b96404386c8f1048cc09fd28dd5692a91f

artifact:
  artifacts/skycausal_fjsp_cooperative_preflight_v0_169d7cc7
```

结果：

| Solver | Cooperative stop | p50 finalize | p99 finalize | max finalize |
|---|---:|---:|---:|---:|
| DE | 50/50 | 46.498 ms | 97.049 ms | 109.871 ms |
| PSO | 50/50 | 46.761 ms | 87.770 ms | 89.134 ms |
| CP-SAT | 50/50 | 63.282 ms | 112.329 ms | 114.495 ms |

所有 solver：

```text
schedule audit failures:       0
deadline overruns:             0
orphan requests:               0
unresolved requests:           0
termination signals:           0
stop acknowledgement failures: 0
```

审计链：

```text
signed request records: 150

start manifest:
  cd8ace4438039544d49ec5f2140ebc3ce654708320a10e6a7245feb435f50716

summary:
  f3460db041049f6e9c4388d2a733f4baf2f4f0837291532dca7ee358d157c8fe

completed manifest:
  929d69b297649ef0b6e39eb787405821c4a1d924f3fab3402dfd41c78d9c4e46
```

首次完成后独立检查发现 summary 引用的是 signed running manifest，但旧 harness
完成时只保留了覆盖后的 completed manifest。已从 completed manifest 确定性重建
exact start manifest，hash 与 summary 中原引用完全一致，并修改 harness 后续始终
保留 `manifest.start.json`。此次修复：

```text
request records modified: 0
summary modified:         false
Gate recomputation:       exact match
```

因此新增授权仅为：

```text
cooperative preflight Gate: AUTHORIZED
```

仍不授权 pilot snapshot capture、pilot arm execution、confirmation 或 quality
claim。本次只读取历史 seed-140 fixture，未访问 `400..419` 或 `500..559`。

### 21.11 Freeze 前 Blockers（历史状态）

pilot arm 当前禁止执行的原因：

1. pilot snapshot manifest 尚未 capture；
2. solver commits 与 immutable image digests 尚未冻结；

完整 confirmation 另有 blockers：

1. development pilot 尚未执行；
2. pair 和 `T1` 尚未根据 pilot 选择并冻结；
3. confirmation 样本量尚未冻结；
4. native checkpoint-resume control 仍 unsupported。

native checkpoint blocker 不禁止 development pilot，但在解除前禁止完整五对照
confirmation claim。

因此状态仍为：

```text
protocol design:          FROZEN
pilot execution:          BLOCKED
confirmation access:      FORBIDDEN
controller training:      FORBIDDEN
quality claim:            FORBIDDEN
```

### 21.12 Code / Image Freeze 与 Exact-Image Validation

冻结采用隔离 Git index 和 detached worktree，未移动 active branch，未修改用户
index，也未混入 publication rerun 等无关 dirty changes。

冻结代码：

```text
SkyEngine:
  ref:     refs/skycausal/two-stage-freeze-v0
  commit:  257dfb5c5a5a13958f18405d5757c5b2609f6dd4

SkyEngine-FJSP:
  ref:     refs/skycausal/cooperative-stop-freeze-v0
  commit:  7524e82db9b4a9c518118c5aebfba8c1c91d5e6e
```

不可变镜像：

```text
SkyEngine:
  sha256:b00062e5413d51f9b42341175870dcd09190b0edd723a66ed618ef1fed824d09

DE:
  sha256:04b346e3e08af14a9a13f5a425b703de2884a53de7a0e8b34f97d42d8e8248ab

PSO:
  sha256:12e8f6d18212dc5e23b4d1ad4ed8b2c3d103fea478be9437f0ccbeca30925016

CP-SAT:
  sha256:56e8c4c529bc33e110e27b5d84b4b03246375355223dac2863a7ff12433e75c4
```

四个镜像的 OCI revision 均与相应 freeze commit 精确一致。11 个关键 runtime
文件逐文件比较 commit blob 与镜像内文件 SHA256，mismatch 为 0。无源码挂载
回归：

```text
SkyEngine SkyCausal: 299/299 PASS
CP-SAT artifact:       7/7 PASS
```

由于 final CP-SAT 镜像重新解析了运行时依赖，旧 cooperative preflight 不能仅凭
源码相同直接继承。为此，在查看 pilot cohort 前先冻结 exact-image validation
spec：

```text
experiment/skycausal/protocols/fjsp_two_stage_freeze_spec_v0.json

spec file SHA256:
  6d02ad52859b4278a224183b339c5898742241fa7864ea742812e26b1beac56d
```

随后使用最终镜像重复同一历史 seed-140 fixture 上的 150-request round-robin
cooperative-stop Gate。结果：

| Solver | Cooperative stop | p99 finalize | max finalize |
|---|---:|---:|---:|
| DE | 50/50 | 54.189 ms | 54.294 ms |
| PSO | 50/50 | 66.097 ms | 79.486 ms |
| CP-SAT | 50/50 | 105.475 ms | 149.348 ms |

所有 schedule audit、deadline overrun、orphan、unresolved request、termination
signal 和 stop acknowledgement failure 计数均为 0。审计链：

```text
artifact:
  artifacts/skycausal_fjsp_freeze_validation_v0_257dfb5c_7524e82d

signed request records: 150

start manifest:
  798a40464057855ebadf7a489e3602ba87765de132c2d8f28a4a1152ea7c8e43

summary:
  f51881affb10718c7e4d48982c960438d9b69b087a6bf87460800589b2c20983

completed manifest:
  b2668c4aeb45fcc7e3f7212dfcb27951c33d0eef1343deec11ab04f87c5dceb0
```

独立重算确认三层 manifest 签名、150 个 record hash、执行顺序和 Gate 完全
一致。机器可读结果：

```text
experiment/skycausal/protocols/fjsp_two_stage_freeze_result_v0.json

status:
  PASS

result hash:
  4fcb8c3062802edbad7ab7be158c39726e849be328309e2386be3568a308aa56
```

原 `fjsp_two_stage_pilot_v0.json` 及其执行 SHA256 `169d7c...a91f` 保持
不可变；其中旧 blocker 列表作为预注册时状态保留，由本节 append-only execution
ledger 更新当前授权状态。

当前唯一 development pilot arm blocker 是：

```text
pilot cohort snapshot manifest 尚未 capture 并审计
```

因此当前状态更新为：

```text
protocol design:          FROZEN
code/image freeze:        PASS
exact-image Gate:         150/150 PASS
pilot snapshot capture:   AUTHORIZED_NOT_EXECUTED
pilot execution:          BLOCKED
confirmation access:      FORBIDDEN
controller training:      FORBIDDEN
quality claim:            FORBIDDEN
```

截至本节写入时，`400..419` pilot cohort 尚未 capture，`500..559`
confirmation reservation 仍未访问。
