# 严格 Deadline 与 Anytime MCTS 设计方案

日期：2026-08-05

状态：设计已批准；MAPF/FJSP deadline 核心已实现，Infrastructure Gate 待锁定验证

## 一、问题与结论

本方案建立时，系统已经证明联合 solver portfolio 存在选择价值，但没有统一的强制
取消机制：

- CP-SAT 有内部 time limit；
- DE/PSO 仍按固定代数运行；
- C++ MAPF 的 `cutoffTime` 不是严格墙钟截止；
- HTTP timeout 只保证客户端停止等待，不保证服务端停止计算；
- `DecisionBudget` 目前主要用于 profile eligibility；
- Headroom runner 的预算检查属于事后审计。

因此现有结果只能支持：

> 在当前 cohort 上，各 profile 的观测耗时满足注册预算。

不能支持：

> 任意在线状态都能在 deadline 前停止并返回合法决策。

后续不能直接实现一个“到点时随便取搜索树当前节点”的 MCTS。推荐方案是：

1. 将 MCTS 设计为 anytime 搜索；
2. deadline 只控制是否继续接纳新的完整 simulation；
3. 未完成 simulation 不参与 value backup；
4. root actions 未完成最低配对覆盖时，不使用不完整搜索结果，回退 fixed backend；
5. rollout horizon 使用物理语义定义，与墙钟 deadline 分离；
6. 先实现无截断价值估计的保守版本，再研究 multi-fidelity。

## 二、三类“截断”必须分开

### 2.1 墙钟搜索停止

回答“还能不能启动下一次 simulation”：

```text
当前时间 + 本次 simulation 的保守耗时上界
    <= search soft deadline
```

不满足时停止扩展，返回已完成 simulation 形成的 best-so-far。

这是计算调度规则，不是动作价值启发式。

### 2.2 单个 solver 的 deadline

回答“某个 CP-SAT、DE、PSO 或 MAPF 调用必须何时停止”。

到点后的合法结果只有：

```text
deadline_reached_with_incumbent
timeout_without_incumbent
fallback_used
```

客户端 HTTP timeout 不能代替服务端取消。

### 2.3 rollout 的物理 horizon

回答“一次 simulation 模拟到哪个物理状态”：

```text
terminal
下一个事件决策点
预注册的物理 milestone
固定事件深度
```

它属于价值近似方法，可能引入偏差，必须单独做 horizon ablation。不能因为搜索时间
不够，就把任意中间状态当作 terminal outcome。

## 三、预算契约

### 3.1 不再使用单一联合预算

建议定义：

```text
DecisionBackend budget
  - state_build_ms
  - search_ms
  - commit_reserve_ms
  - cancellation_grace_ms

FJSP repair budget
  - per_call_deadline_ms

MAPF execution budget
  - per_replan_deadline_ms

MCTS simulation budget
  - per_simulation_cap_ms
  - total_search_deadline_ms
```

MAPF 是执行过程中的多次 replan，不应把未来所有 MAPF 查询时间简单加到当前事件决策
预算中。

### 3.2 绝对 deadline

所有组件接收绝对单调时钟截止时间，而不是各自重新计算相对 timeout：

```python
@dataclass(frozen=True)
class Deadline:
    started_at_ns: int
    soft_deadline_ns: int
    hard_deadline_ns: int
    cancellation_grace_ms: int

    def remaining_ms(self, now_ns: int) -> float:
        ...

    def can_admit(
        self,
        runtime_upper_bound_ms: float,
        now_ns: int,
    ) -> bool:
        ...
```

约束：

```text
soft deadline = hard deadline - commit reserve - cancellation grace
```

soft deadline 后不再启动新工作；hard deadline 用于强制取消；commit reserve 只用于
选择 root action、验证 artifact 和执行 fallback。

### 3.3 嵌套 deadline

simulation 内部调用 solver 时：

```text
solver hard deadline
    = min(
        solver profile deadline,
        simulation deadline,
        MCTS hard deadline
      )
```

任何子组件不得把 deadline 向后延长。

## 四、为什么 MCTS 仍然需要 deadline

在线动态制造系统必须在环境继续演化前给出动作。simulation 数量不能预先保证等价的
运行时间，因为：

- 不同 snapshot 的物理 rollout 长度不同；
- solver profile 的耗时分布不同；
- MAPF replan 次数取决于执行轨迹；
- 故障强度会改变剩余问题规模。

仅规定 `N simulations` 无法提供在线延迟边界。因此 MCTS 必须有墙钟 deadline。

但 deadline 不需要决定“哪个动作更好”。MCTS 的 anytime 性质是：

```text
完成 1 次 simulation -> 有一个合法 best-so-far
完成更多 simulation -> 统计估计继续改善
deadline 到达 -> 不再启动新 simulation
```

关键是只使用完整、可审计的 simulation。

## 五、第一版搜索：Stratified Root Monte Carlo

第一版不直接实现深树 progressive-widening MCTS，而先实现一个无歧义的搜索基线。

### 5.1 Root action

```text
root action =
    event response operator
    + FJSP profile
    + MAPF profile activation/defer policy
```

每个 action 必须已经经过 eligibility 和安全切换检查。

### 5.2 配对覆盖轮次

每一轮使用同一个 planning seed，对所有 legal root actions 各运行一次 simulation：

```text
round k:
  action 1 + planning_seed[k]
  action 2 + planning_seed[k]
  ...
  action n + planning_seed[k]
```

这等价于 common random numbers，可减少动作比较方差。

### 5.3 最低完整覆盖

MCTS/Search backend 只有在以下条件成立时才有资格覆盖 fixed backend：

```text
所有 legal root actions
至少完成一个相同 planning seed 的配对 simulation
```

如果剩余预算不足以完成第一轮：

```text
status = insufficient_budget_for_root_coverage
decision = fixed fallback
```

禁止根据动作枚举顺序只评估前几个 action 后直接选择。

### 5.4 simulation admission

第一版使用声明式上界，不学习 runtime predictor：

```text
admit simulation iff
remaining_soft_budget
    >= declared_per_simulation_cap
```

这会偏保守，但不引入 value heuristic。

后续可使用经 coverage calibration 的 runtime upper quantile：

```text
upper_runtime =
    conformal_quantile(
        profile,
        residual_problem_size,
        event_type,
        horizon
    )
```

runtime 模型只决定是否接纳 simulation，不参与 action value。

## 六、第二版 MCTS

完成 Root Monte Carlo Gate 后，再实现 open-loop MCTS。

### 6.1 节点语义

```text
node =
    event decision history
    + planning RNG history
    + abstract physical state hash
```

树深度按未来事件决策次数定义，不按环境 step 或已消耗毫秒定义。

### 6.2 Selection

第一版使用标准、预注册的 UCB1，不调手工权重：

```text
normalized_cost in [0, 1]

score(a) =
    -mean_cost(a)
    + sqrt(2 * log(parent_visits) / action_visits)
```

cost 的上下界来自 episode cap，而不是用验证集调参。

### 6.3 Progressive widening

root portfolio 只有 4--6 个 action，第一版不需要 progressive widening。

只在未来组合空间扩展到：

```text
operator × FJSP × MAPF × repair level × parameter tier
```

时启用：

```text
expanded_children(N) <= ceil(C * N^alpha)
```

`C`、`alpha` 必须预注册并做消融，不能根据 locked validation winner 调整。

### 6.4 Simulation 与 backup

simulation 状态：

```text
completed
cancelled_before_solver
cancelled_during_solver
invalid_physics
timeout_with_fallback
```

只有以下结果可 backup：

```text
completed
timeout_with_fallback 且 fallback 已真实执行到预注册 horizon
```

禁止：

- 将半条 trajectory 的当前 makespan 当 terminal makespan；
- 将未完成 solver 的内部 score 当物理 outcome；
- 用超时前最后一个未验证 artifact 更新 Q；
- 因某 action 更慢而复用其他 action 的 rollout value。

### 6.5 Root action 选择

正常完成最低覆盖后：

```text
selected action =
    completed visit count 最大的 robust child
```

visit 并列时依次使用：

```text
更低 mean cost
更低 upper confidence bound
预注册 action id
```

如果最低覆盖未完成或所有 simulation 均无合法 outcome：

```text
selected action = fixed fallback
```

## 七、rollout horizon 方案

用户担心的启发式主要来自 horizon，而不是 wall-clock stop。

### 7.1 V0：terminal rollout

只接受模拟到 episode terminal 的 outcome。

优点：

- 无 terminal value bias；
- 最适合作为 Search Gate reference。

缺点：

- 单次 simulation 慢；
- 在线预算内可能只能完成很少轮次。

用途：

```text
离线/开发 Search Gate
runtime-quality curve
teacher reference
```

### 7.2 V1：next-decision-event rollout

模拟到：

```text
下一个需要 DecisionBackend 的事件
或 terminal
```

叶节点返回区间：

```text
lower_bound <= terminal cost <= upper_bound
```

第一版不使用学习 value，只使用可审计下界：

- 已耗时；
- 剩余 job precedence critical-path lower bound；
- machine workload lower bound；
- 已承诺 transport lower bound。

区间过宽时继续 rollout，不直接产生点估计。

### 7.3 V2：固定物理 milestone

例如：

```text
受影响 job 的下一道工序完成
故障机器恢复
所有已装载运输完成
```

milestone 必须由事件语义决定，不得按某个算法表现选择。

### 7.4 V3：learned terminal value

只有 V0/V1 数据和 calibration Gate 完成后，才允许：

```text
short rollout + calibrated value artifact
```

OOD 或不确定性过高时回退 V0/V1。

## 八、solver 中断语义

### 8.1 CP-SAT

```text
内部 max_time_in_seconds
+ 外部 killable subprocess watchdog
```

内部停止并返回 FEASIBLE 时可使用 incumbent；外部 watchdog 只作为硬保护。

### 8.2 DE/PSO

每代结束检查 absolute deadline：

```text
initialize population
establish first valid gbest
while generation remains:
    if deadline reached:
        return gbest, deadline_reached_with_incumbent
    run one generation
```

外层仍使用子进程 watchdog，防止某一代或 native 调用卡死。

### 8.3 MAPF C++ solver

当前 binary 通常在正常结束时才输出完整 path。若到点前没有持久化 incumbent：

```text
kill process group
discard partial output
fallback to previous valid trajectory
or invoke reserved safe solver
```

不能声称“强制 kill 后返回当前最好解”，除非修改 native solver，使其周期性发布并
原子写入可验证 incumbent。

### 8.4 HTTP 取消

推荐协议：

```text
POST /solve
  request_id
  absolute_deadline_unix_ns
  cancellation_token

POST /cancel/{request_id}

response:
  status
  elapsed_ms
  stopped_by
  incumbent_available
  artifact_hash
```

客户端 timeout 后必须请求 cancel；服务端必须终止对应 process group 并记录
`cancel_ack_at_ns`。

## 九、安全切换与 MCTS

MAPF profile 在 loaded transport 中不能立即切换。root action 应显式包含：

```text
activate_now
defer_until_safe_boundary
keep_current_profile
```

deferred activation 是状态机，不是隐式 fallback：

```text
pending_profile
requested_at_event
safe_boundary_condition
activated_at_timeline
cancelled_reason
```

MCTS simulation 和真实执行必须使用同一状态机。

## 十、并发策略

第一版采用顺序 simulation：

- 结果确定性更强；
- 容易复现 planning seed；
- 易于确认没有 orphan process；
- 不需要 virtual loss。

只有顺序版本通过 Gate 后，才增加 root-parallel：

- 每个 worker 使用独立 snapshot；
- planning RNG 不共享；
- 只合并 completed results；
- hard deadline 后统一 cancel/join；
- worker 未退出则整个 decision 标记 infrastructure failure。

## 十一、审计契约

每次 MCTS decision 至少记录：

```text
decision_id
snapshot_hash
legal root actions
planning seed schedule
soft/hard deadline
commit reserve
completed/cancelled simulation count
per-action visits, mean cost, confidence interval
per-simulation horizon and status
solver request id and deadline
timeout/incumbent/fallback status
selected action
selection rule
fallback reason
actual wall time
deadline overrun
physical invariant audit
```

禁止只保存 selected action 和最终 Q。

## 十二、Gate

### 12.1 Deadline Infrastructure Gate

使用可控 slow solver fixture，预注册：

```text
100 次连续请求
p99 completion/cancel acknowledgement
    <= hard deadline + cancellation grace
orphan process count = 0
late artifact activation count = 0
snapshot contamination count = 0
timeout fallback physical invariant pass rate = 100%
replay hash match rate = 100%
```

这不是形式化 real-time guarantee，但提供可操作的进程级 deadline 保证。

### 12.2 Root Coverage Gate

```text
MCTS-eligible decisions 的第一轮 root paired coverage = 100%
coverage 不足时 fixed fallback = 100%
partial coverage result 被用于选择的次数 = 0
```

### 12.3 Search Value Gate

在相同 total decision deadline 下比较：

```text
best fixed
static selector
stratified root Monte Carlo
UCT MCTS
oracle
```

核心指标：

```text
regret_closed =
    (M_fixed - M_search)
    / (M_fixed - M_oracle)
```

首轮建议预注册：

```text
mean regret_closed > 0
cluster-bootstrap 95% CI lower > 0
terminal completion 不低于 best fixed
physical invariant pass rate = 100%
deadline Infrastructure Gate 全通过
```

预算曲线：

```text
2 s, 5 s, 10 s, 20 s
```

先确认搜索质量随预算单调或趋于稳定，再讨论在线目标预算。不能先指定一个很小预算，
然后靠不完整 simulation 宣称 MCTS 有效。

## 十三、实施顺序

```text
Phase 0  修正文档：observed budget != hard deadline
Phase 1  Deadline/Cancel/Fallback contract
Phase 2  CP-SAT、DE、PSO、MAPF process watchdog
Phase 3  Deadline Infrastructure Gate
Phase 4  在硬 deadline 下重跑 Portfolio Headroom
Phase 5  Stratified Root Monte Carlo
Phase 6  Root Coverage + Search Value Gate
Phase 7  Open-loop UCT MCTS
Phase 8  物理 horizon / multi-fidelity ablation
Phase 9  MCTS teacher dataset
Phase 10 Neural/BNN/PUCT
```

## 十四、当前决策

1. MCTS 在线运行必须有 deadline；
2. deadline 只停止接纳新 simulation，不定义 action value；
3. 第一版不 backup 未完成 rollout；
4. 第一版不使用任意墙钟时刻的中间状态估值；
5. root 最低配对覆盖不足时直接回退 fixed backend；
6. 先做 terminal rollout reference，再引入物理 horizon；
7. 严格 deadline 基础设施通过前，不进入 MCTS Search Gate；
8. MCTS Search Gate 通过前，不启动神经模型训练。

## 十五、2026-08-05 实施进展

已完成 MAPF 垂直切片：

```text
SkyEngine-MAPF/server/deadline_process.py
  - request_id 级活动进程 registry
  - 每个 solver 使用独立 process group
  - absolute Unix deadline 在进程启动时转换为 monotonic 剩余时间
  - soft SIGTERM + grace + SIGKILL
  - completed / hard_deadline_exceeded / cancelled 审计

SkyEngine-MAPF/adapters/classical_http_server.py
  - /init 和 /probe 接收 request_id、hard_deadline_unix_ns
  - 有效 deadline 取客户端 deadline 与服务端 profile budget 的较早者
  - /cancel/<request_id>
  - /reset 取消全部活动 solver
  - solver 失败响应携带 deadline_audit

SkyEngine RollingMAPFHTTPRouteSolver
  - 为每次 query 生成 request_id 和 absolute deadline
  - HTTP transport timeout 后显式请求 /cancel
  - 同一次 replan 的所有 retry 共享一个 deadline，禁止预算续期
  - hard deadline 或 transport failure 使用 wait_and_replan
  - 不读取可能与当前位置不一致的旧 cache
  - query event 记录 request control、deadline audit 和 fallback
```

验证结果：

```text
MAPF deadline/adapter tests: 15/15
SkyEngine focused deadline/joint tests: 17/17
SkyCausal full Docker regression: 140/140

100 次 slow-process deadline stress:
  p99 <= 100 ms test threshold
  active process count = 0

真实 C++ EECBS:
  agents = 100
  hard deadline = 20 ms
  process audit elapsed = 约 21.1 ms
  outer elapsed = 约 22.2 ms
  termination = SIGTERM
  active process count = 0
```

随后完成 FJSP 垂直切片：

```text
DE / PSO
  - generation boundary 检查 monotonic soft deadline
  - 初始化种群后始终保留合法 gbest incumbent
  - deadline_reached_with_incumbent
  - 实际 generations 与 max_generations 分开记录

CP-SAT
  - 内部 max_time_in_seconds 压缩到 soft deadline 的剩余时间
  - 外部 worker process hard watchdog

三种 FJSP HTTP 服务
  - /solve 使用独立 worker process group
  - request_id、solver_budget_ms、hard_deadline_unix_ns
  - /cancel/<request_id>
  - client deadline 与 server cap 取较早者
  - completed / hard_deadline / solver_cancelled 结构化审计

SkyEngine OnlineFJSPGateway
  - profile budget 传播到服务端
  - transport timeout 后显式 cancel
  - timeout response 不进入 artifact cache
  - timeout 不追加或激活 PlanRevision
  - 动态 partial rescheduling 超时后使用 wait_for_repair
```

新增验证：

```text
FJSP deadline/dynamic tests: 6/6
CP-SAT artifact tests: 2/2
SkyEngine deadline/fallback focused tests: 44/44

FJSP 100 次 slow-worker deadline stress:
  p99 <= 100 ms test threshold
  active worker count = 0

真实 deadline 镜像 HTTP:
  DE: 1000 ms solved；1 ms -> hard_deadline
  PSO: 1000 ms solved；1 ms -> hard_deadline
  CP-SAT: 1000 ms solved；1 ms -> hard_deadline

真实 EECBS deadline 镜像 HTTP:
  500 ms 请求正常完成
  20 ms absolute deadline 下进程被 SIGTERM
  active process count = 0
```

Headroom runner 和联合 Gate 已更新：

- `applied` 和显式 `fallback_used` 都按真实物理 outcome 计分；
- 成功分支必须携带 `completed` deadline audit；
- fallback 分支必须携带 hard-deadline 或 cancel evidence；
- 联合分析 schema 升级为 `skycausal.joint-portfolio-headroom.v2`；
- 原 120-branch cohort 缺少 v2 audit，不能直接冒充严格 deadline cohort。

当前仍不能宣称整个 Deadline Infrastructure Gate 已通过。剩余条件：

1. 在固定 commit 上构建并登记不可变镜像 digest；
2. 对每个真实 solver/profile 做 100 次跨规模 deadline/cancel stress；
3. 对 timeout fallback 做 100% physical invariant 和 replay hash 验证；
4. 使用 v2 runner 在真实 timeout/fallback 计分下重跑联合 Portfolio Headroom；
5. 锁定 cohort 通过后，才开始 Stratified Root Monte Carlo。

## 十六、MCTS 准入、后续路线与最终论证链

当前推进逻辑固定为：

```text
Deadline Infrastructure Gate
  -> v2 Portfolio Headroom Gate
  -> Stratified Root Monte Carlo
  -> Open-loop UCT MCTS
  -> Search Value / Generalization Gate
  -> MCTS teacher dataset
  -> Policy / Value / BNN residual
  -> learned PUCT/MCTS
```

### 16.1 何时开始 MCTS

以下两项必须同时满足：

1. 六类真实 solver 的 100 次 deadline/cancel 压测通过；
2. v2 联合 cohort 在真实 timeout/fallback 计分后，oracle improvement 的
   cluster-bootstrap 95% CI 下界仍大于 0。

第一版先实现 Stratified Root Monte Carlo，建立 root paired coverage 和等预算
flat-search 基线；通过后才实现 open-loop UCT。不能把 root action 枚举或单次
lookahead 直接称为 MCTS。

### 16.2 MCTS 的完成标准

在相同 total wall-clock deadline 下，至少比较：

```text
best fixed
static selector
Stratified Root Monte Carlo
Open-loop UCT MCTS
oracle portfolio
```

MCTS Search Gate 要求：

- 相对 best fixed 的 mean regret closed 大于 0；
- cluster-bootstrap 95% CI 下界大于 0；
- terminal completion 不低于 best fixed；
- p95/p99 decision latency 满足 deadline contract；
- partial simulation backup 次数为 0；
- fallback、physical invariant 和 replay audit 全通过；
- 增加搜索预算后，质量总体单调改善或进入稳定平台。

### 16.3 MCTS 之后做什么

MCTS 通过后保存：

```text
root visit distribution
per-action Q / confidence interval
selected action
completed/cancelled simulation count
search depth
solver/profile usage
```

这些日志形成 teacher dataset，用于：

1. policy/ranking 网络压缩 root action selection；
2. value 网络减少 terminal rollout 数量；
3. BNN residual 估计 epistemic uncertainty；
4. PUCT 在相同质量下减少 simulation；
5. OOD 或高不确定状态回退纯 MCTS 或规则后端。

如果 MCTS Search Gate 不通过，不启动 teacher training；保留 Root Monte Carlo 或
static selector，并将“深树搜索没有额外价值”作为负结果。

### 16.4 最终需要支持的论文结论

主结论不是“MCTS 能求解 FJSP”，而是：

> 动态 FJSP-MAPF 中不存在对所有扰动状态始终占优的固定求解器组合。在相同严格
> 在线计算预算下，具备可审计中断、安全 fallback 和同源物理 rollout 的 anytime
> portfolio MCTS，能够根据当前状态选择 FJSP-MAPF 求解器组合，并显著降低相对
> 最佳固定组合的 capped makespan 和 oracle regret。

扩展结论是：

> MCTS 的搜索知识可以被 policy/value/BNN 后端压缩；神经后端在高置信状态减少
> 在线搜索成本，在 OOD 或高不确定状态可靠回退，不牺牲物理安全和可审计性。

当前实验只允许支持“solver portfolio 存在开发 headroom”和“deadline 核心机制
可运行”。在 v2 cohort 和 MCTS Search Gate 完成前，不得提前写成上述最终结论。

## 十七、2026-08-05 开发 Gate 执行结果

### 17.1 Deadline Infrastructure Stress Gate

六类真实 solver 各执行 100 个连续请求，共 600 个请求：

```text
每个 solver:
  50 normal completion
  25 hard deadline
  25 explicit cancel
```

结果：

- 600/600 请求得到预期 outcome；
- 正常结果全部通过物理结构校验；
- hard deadline 和 explicit cancel 后活动 request 均归零；
- 六类服务均无 late active worker；
- cancel acknowledgement p99 均小于 5 ms；
- hard deadline completion p99 均小于 29 ms；
- CP-SAT 的 commit reserve 由 50 ms 调整为 150 ms，总 hard budget
  保持 1000 ms 不变。

Development stress artifact：

```text
experiment/skycausal/results/deadline_infrastructure_v2_20260805/
development_stress_i100_r2.json

SHA256:
8364bae8848919d1894de75bcd4d061bd5da9bd0e6c62249c3e81c766697d788
```

### 17.2 Environment Replay Calibration

同一 `maze/seed-100` cluster 独立执行两次。六个 profile 的：

```text
physical_outcome_hash
capped_makespan
initial_revision_hash
```

均逐 profile 完全一致。

完整 Python snapshot 的 pickle hash 跨进程不稳定，只用于同一次 run 内的 branch
pairing，不作为跨 run replay 证据。跨 run replay 使用 committed artifact、
exogenous seed 和 physical outcome hash。

### 17.3 v2 Joint Portfolio Headroom Gate

固定开发 cohort：

```text
FJSP: J10P5M6
MAPF: medium-mazes-seed-0000 / 0001
seeds: 100..109
clusters: 20
profiles: 6
branches: 120
FJSP hard budget: 1000 ms
MAPF hard budget: 500 ms
```

原始执行证据：

```text
120/120 branches completed
120/120 FJSP deadline audits = completed
8464/8464 MAPF deadline audits = completed
branch errors = 0
physical invariant failures = 0
FJSP/MAPF fallbacks = 0
maximum FJSP compute time = 458.68 ms
maximum MAPF solver runtime = 443.21 ms
```

Headroom 分析：

```text
schema: skycausal.joint-portfolio-headroom.v2
best fixed: CP-SAT+LG-LaCAM
best fixed mean capped makespan: 462.05
oracle mean capped makespan: 448.00
oracle improvement: 14.05
cluster-bootstrap 95% CI: [7.05, 22.25]
non-best-fixed winner rate: 65%
strict FJSP winners: CP-SAT, DE, PSO
strict MAPF winners: EECBS, LG-LaCAM, MAPF-LNS2
gate: passed
```

Artifacts：

```text
joint_v2_20clusters.json
SHA256 cd1f5af74dce069a3792042862418cd1eab18157cd307e632fe9f3b3246f119b

joint_v2_20clusters_headroom.json
SHA256 5080c2640e19fa2fd5cd22737479aa1b1e28e7d329f4afb83d3fdfa01f33dcb3
```

### 17.4 当前决策

Deadline Infrastructure Gate 和 v2 Portfolio Headroom Gate 均已通过，
因此允许开始 Stratified Root Monte Carlo。

但当前三个仓库仍为 dirty worktree，镜像仍是 development digest。上述结果是
MCTS 开发准入证据，不是论文锁定证据。正式论文实验仍需在固定 commit 和不可变
镜像上复跑。

## 十八、Stratified Root Monte Carlo 首轮实现与实测

### 18.1 已实现语义

新增第一阶段 flat-search backend：

```text
StratifiedRootMonteCarloBackend
```

实现约束：

- wall budget 显式拆成 search、cancellation grace 和 commit reserve；
- 每个 simulation 有独立 soft/hard deadline；
- 同一 planning seed 必须覆盖全部 legal root actions；
- 一个 seed stratum 只有在全部 action 完成后才原子进入统计；
- incomplete、cancelled、hard-deadline、late-completed simulation 不 backup；
- incomplete stratum 中已完成的单个 action 也不 backup；
- 最低 root coverage 不足时回退固定 backend；
- simulation evaluator 异常进入 audit，不产生虚构 cost；
- simulation limit 和 wall deadline 均可停止下一 stratum admission。

专门单元测试和 SkyEngine 全量回归均通过：

```text
Root Monte Carlo focused tests: 10/10
SkyEngine full regression: 154/154
```

### 18.2 真实 process-isolated evaluator

真实 evaluator 对每个 root action：

1. 启动独立 process group；
2. 重建同一决策 snapshot；
3. 激活对应 FJSP-MAPF profile；
4. 执行 terminal physical rollout；
5. 到 per-simulation hard deadline 时 SIGTERM/SIGKILL；
6. 仅将完整 row 作为 `RootSimulationResult.completed` 返回。

1 秒强制超时测试：

```text
worker status: hard_deadline_exceeded
termination: SIGTERM
paired rounds: 0
accepted backup: 0
fallback: CP-SAT+LG-LaCAM
all six solver services active_request_count: 0
```

### 18.3 Snapshot Artifact

初版 runner 每次搜索前重新生成初始 CP-SAT schedule。对 `seed-110`，1 秒墙钟
CP-SAT 两次分别得到不同 FEASIBLE schedule，导致 breakdown snapshot 不同。这
不是搜索随机性，而是状态构造漂移。

修复：

```text
skycausal.root-snapshot-artifact.v1
```

snapshot artifact 记录并校验：

```text
FJSP input SHA256
MAPF input SHA256 + map name
profile config SHA256
baseline profile
environment seed
processing-time preset
AGV count / horizon / due factor
```

首次原子创建，后续只能加载 state key 完全匹配的 artifact。固定 artifact 后，
重复搜索的逐 profile cost 和 physical outcome hash 完全一致。

### 18.4 Moderate-variance budget smoke

固定 artifact：

```text
J10P5M6
maze-b
state seed: 110
processing-time preset: moderate_variance
artifact SHA256:
f00ed31bcbae2b46005cf03b15857d41436d8703f10e27643c5f214bbdc554f5
```

1 paired stratum，65 秒 search budget：

```text
CP-SAT+EECBS       533
CP-SAT+LG-LaCAM    517
DE+EECBS           492
DE+LG-LaCAM        533
PSO+LG-LaCAM       486  <- selected
PSO+MAPF-LNS2      501
```

2 paired strata，125 秒 search budget：

```text
CP-SAT+EECBS       [533, 486] -> 509.5
CP-SAT+LG-LaCAM    [517, 532] -> 524.5
DE+EECBS           [492, 521] -> 506.5
DE+LG-LaCAM        [533, 532] -> 532.5
PSO+LG-LaCAM       [486, 485] -> 485.5  <- selected
PSO+MAPF-LNS2      [501, 515] -> 508.0
```

第一 stratum 在两个独立 run 中逐 profile physical hash 完全一致；第二 seed
产生不同 cost，说明 paired exogenous randomness 已实际生效。

Artifacts：

```text
root_mc_moderate_seed110_one_stratum.json
SHA256 b32566aa1101201259d49336a5e82709dbed05607b4c3b3365136baae1c607e3

root_mc_moderate_seed110_two_strata.json
SHA256 09230a19d79c7069cbf09188956ce19e86cf8b76f2f9a39f0fec9f48bb2079ba
```

### 18.5 当前结论边界

当前可以声称：

```text
Stratified Root Monte Carlo 的 paired coverage、deadline、process kill、
zero partial backup、fixed fallback 和真实物理 rollout 执行链可运行。
```

当前不能声称：

```text
Root Monte Carlo 优于 best fixed 或 static selector；
当前 65/125 秒 terminal rollout 满足最终在线预算；
Open-loop UCT MCTS 已实现或有效；
MCTS Search Value Gate 已通过。
```

下一步是跨 cluster 的 Root Monte Carlo budget/horizon 实验，并将 terminal
rollout 缩短为 next-decision-event 或 physical-milestone horizon。在相同严格
wall-clock budget 下证明 flat search 有价值后，才实现 open-loop UCT。

## 十九、Held-out Search Value Pilot 与并行执行链

### 19.1 严格 held-out 协议

固定 8 个有效 snapshot clusters：

```text
maze:   state seed 110 / 111 / 112 / 113
maze-b: state seed 110 / 111 / 113 / 114
processing-time preset: moderate_variance
```

每个 cluster 严格拆分：

```text
planning seed 1:
  只用于 Root MC 选择 action

planning seed 3:
  只用于 held-out execution 计分
  不进入 action 选择
```

旧的 3-strata terminal runs 还用于离线比较 `k=1` 和 `k=2`。结果：

```text
k=1:
  improvement vs best fixed: 14.75
  95% CI: [4.75, 27.75]
  oracle regret closed: 90.77%
  held-out oracle hit rate: 87.5%

k=2:
  improvement vs best fixed: 13.75
  95% CI: [2.625, 27.125]
  oracle regret closed: 84.62%
  held-out oracle hit rate: 75%
```

第二个 planning stratum 没有带来收益，因此当前 development configuration
选择 `k=1`，不能用“simulation 越多必然越好”作为假设。

### 19.2 Physical milestone 候选被淘汰

实现并实测：

```text
repair completed
+ event 后新完成 5 道 operation
+ remaining job-chain lower bound
```

同一 `maze-b/seed-110` snapshot 的 18 个 simulation：

```text
leaf values: 230 或 231
terminal costs: 487 到 533
leaf/terminal Spearman correlation: 约 0.13
active-plan makespan correlation: 约 0.23
MAPF max SOC correlation: 约 0.39
```

该 leaf value 几乎不能区分 action。虽然物理 rollout 本身约 0.2 秒，但它不能
保留 terminal 排序，因此不得进入 Root MC 或 UCT backup。当前代码保留该 horizon
作为可审计的负结果和后续 learned value 对照，不把它包装成有效短 horizon。

### 19.3 Warm worker 与 paired-stratum parallelism

原先每个 action 启动一个冷 Python process，主要时间消耗在环境和 coordinator
重建。新增：

```text
WarmProfilePoolEvaluator:
  每个 root action 一个预热且可终止的 worker
  每次从不可变 snapshot 恢复

parallel paired stratum:
  同一 planning seed 的全部 action 并发执行
  admission upper bound 从 sum(cap) 改为 max(cap)
  只有全部 action 完成后才原子 commit
```

`repair+5 operations` 的 18 simulations 墙钟：

```text
cold process per simulation: 87.94 s
warm workers, sequential actions: 26.94 s
warm workers, parallel strata: 7.10 s
```

三种执行模式得到相同 action costs。warm sequential 与 cold 的 18 个 physical
hash 中 17 个相同；一个 DE 合法轨迹 hash 不同但 cost 相同，因此跨运行不要求
启发式 solver 产生逐字节相同轨迹。

### 19.4 MAPF session isolation

第一次并行实测暴露出真实并发缺陷：MAPF HTTP 服务原来让全部客户端共享：

```text
_action_cache
_time_step
_num_agents
```

并发 `/init` 和 `/plan` 会互相覆盖，触发 cache replay divergence。修复为：

```text
每个 RollingMAPFHTTPRouteSolver 生成独立 session_id
/init 和 /plan 按 session_id 读写
snapshot restore 生成新 session
profile switch 释放旧 session
worker 正常退出 DELETE session
health 暴露 session_count
```

session-aware development MAPF image：

```text
sha256:d828d5d394facceb166ae73c066ceb4b4d62725705df2c3a5ee389f88551186e
```

8-cluster pilot 的每个 root run 后：

```text
all FJSP/MAPF active_request_count = 0
all MAPF session_count = 0
```

hard-killed worker 仍可能留下远端 session；正式 parallel deadline stress 需要
增加孤儿 session 回收/TTL Gate。

### 19.5 Parallel terminal k=1 held-out 结果

使用 session-isolated warm parallel execution，重新运行 8 个 cluster 的
planning seed 1；原第 3 seed 继续作为完全 held-out execution。

执行证据：

```text
clusters: 8
planning branches: 48/48 completed
process audits: 48/48 completed
root gates: 8/8 passed
online planning wall time:
  mean 2.81 s
  range [2.10, 3.45] s
worker warmup:
  mean 1.25 s
  单列记录，不计入 online search deadline
aggregate action compute:
  mean 15.83 s
```

必须区分：

```text
planning wall time:
  用户等待时间，parallel stratum 取 action 最大延迟

aggregate action compute:
  六个 action 的资源时间之和
```

held-out value：

```text
best fixed: CP-SAT+EECBS
best fixed mean held-out makespan: 449.75
held-out oracle mean makespan: 433.50
best-fixed oracle gap: 16.25

parallel Root MC k=1 mean held-out makespan: 435.00
improvement vs best fixed: 14.75
cluster-bootstrap 95% CI: [4.75, 27.75]
mean held-out oracle regret: 1.50
oracle regret closed: 90.77%
held-out oracle hit rate: 87.5%
```

Analysis artifact：

```text
experiment/skycausal/results/root_parallel_k1_8cluster_20260805/
heldout_analysis.json

SHA256:
f35c0353caa98e5cba2c1c9f573fc1bfd85a65a6d2889a12a8f7ce0964e5b5d2
```

回归：

```text
SkyEngine: 162/162
MAPF deadline/session adapter: 16/16
```

### 19.6 当前结论边界与下一步

当前可以声称：

```text
在 8-cluster development pilot 中，parallel Root MC k=1 的 action selection
在完全 held-out execution seed 上显著优于 best fixed，并关闭约 91% oracle
regret；session-isolated parallel execution 将 online wall 降到约 2.8 秒。
```

当前仍不能声称正式 Search Value Gate 已通过，因为：

```text
有效 cluster 只有 8 个，正式目标至少 20 个；
尚未加入 leakage-safe static selector baseline；
当前 held-out 证据仍来自 dirty development worktree；
2.8 秒仍未证明满足最终在线控制预算；
parallel hard-kill 后的 orphan session TTL Gate 尚未完成。
```

因此下一步顺序保持：

1. 扩展到至少 20 个有效固定 snapshot clusters；
2. 对每个 cluster 保持 planning/execution seed 分离；
3. 加入 cluster-safe static selector；
4. 增加 parallel deadline、worker kill 和 orphan session 回收压力 Gate；
5. 比较 best fixed、static selector、Root MC k=1 和 held-out oracle；
6. 只有上述 Gate 通过后，才实现 open-loop UCT MCTS。

## 二十、20-cluster Search Value Gate 与 Open-loop UCT 首轮结果

### 20.1 20-cluster development cohort

在固定 snapshot、planning seed 与 execution seed 分离的协议下，扩展到 20 个
有效 clusters：

```text
maze:
  110, 111, 112, 113, 115, 116, 117, 118, 119, 120, 121

maze-b:
  110, 111, 113, 114, 115, 116, 117, 118, 120
```

`maze-b/119` 没有安全 machine-breakdown snapshot，按预注册 eligibility 排除，
没有填充惩罚 cost。`maze-b/115` 首次 capture 遇到 FJSP hard deadline，按原候选
顺序重试成功后纳入。

terminal Root MC k=1 的严格 held-out 结果：

```text
best fixed: CP-SAT+EECBS
best fixed mean held-out makespan: 457.60
held-out oracle mean: 436.80
best-fixed oracle gap: 20.80

Root MC mean held-out makespan: 438.55
improvement vs best fixed: 19.05
cluster-bootstrap 95% CI: [8.20, 32.45]
mean oracle regret: 1.75
oracle regret closed: 91.59%
held-out oracle hit rate: 70%

online planning wall:
  mean 2.99 s
  range [2.02, 4.76] s
aggregate action compute mean: 16.84 s
```

主 static baseline 冻结为 leave-one-cluster-out topology-backoff selector：

```text
minimum topology group size: 5
topology prior strength: 10
地图内 profile 均值向 training-fold 全局均值收缩
```

它在当前小样本上弱于 best fixed：

```text
static selector mean held-out makespan: 467.05
improvement vs best fixed: -9.45
95% CI: [-18.95, -1.60]
oracle hit rate: 5%

Root MC improvement vs static selector: 28.50
95% CI: [16.40, 42.20]
```

因此主结论必须建立在 Root MC 相对 best fixed 的正 CI 上，不能只用较弱的
static selector 衬托搜索。

Analysis artifact：

```text
experiment/skycausal/results/root_parallel_k1_20cluster_20260805/
heldout_analysis.json

SHA256:
563c6632369e385ddfc5004ed0dad6304955b442fd85b23f4697c78a3c105f60
```

### 20.2 2/5/10/20 秒 budget curve

使用 20 个真实 paired-stratum wall time 做保守 admission replay：

```text
budget   complete root coverage   mean held-out cost   vs best fixed
2 s      0/20                     459.85               -2.25
5 s      19/20                    440.55               +17.05
10 s     20/20                    438.55               +19.05
20 s     20/20                    438.55               +19.05
```

5 秒：

```text
improvement 95% CI: [6.55, 30.70]
oracle regret closed: 81.97%
```

10/20 秒：

```text
improvement 95% CI lower: 8.30
oracle regret closed: 91.59%
```

这说明当前 terminal k=1 的有效工作点约在 5 到 10 秒。2 秒预算下不能声称搜索
有效，只能执行 fixed fallback。

Artifact：

```text
experiment/skycausal/results/root_parallel_k1_20cluster_20260805/
budget_curve.json

SHA256:
4a7e65b4eeb206ff859fa10866678f6ed3fbee641fba4c73936f0d198061553d
```

### 20.3 Parallel hard-kill 与 orphan session cleanup

为每个 warm worker 的 MAPF session 增加父进程已知的唯一 prefix，并在 worker
被终止后由父进程向全部可能访问的 MAPF 服务执行：

```text
DELETE /sessions/<session_prefix>
```

真实 forced-timeout：

```text
terminal horizon
6-action parallel stratum
search budget: 2 s
per-action hard cap: 1.7 s

6/6 workers: hard_deadline_exceeded
termination: 6/6 SIGTERM
paired rounds: 0
partial backup: 0
selection: fixed fallback
all FJSP/MAPF active_request_count: 0
all MAPF session_count: 0
```

当前 MAPF development image：

```text
sha256:0654b416305a745fe1f4cb2e8ee13947bd8dfb042045462cd9562c1fb075d49a
```

Artifact：

```text
experiment/skycausal/results/root_parallel_deadline_stress_20260805/
forced_timeout.json

SHA256:
89f8d63343b23ef020384241c18ea6cc632396b4495b2b4a5d417925edbf1501
```

### 20.4 Open-loop UCT 内核

已实现：

```text
open-loop action-sequence tree
mandatory paired root coverage
parallel root-stratum atomic commit
UCB1 selection
progressive widening
complete simulation only backup
deadline admission and fixed fallback
robust-child root selection
```

首次真实运行暴露出 UCB 量纲错误：直接使用约 500 的 makespan cost，而 exploration
bonus 约为 1，会退化成 greedy tree。修正为 sibling mean cost 的 min-max
normalized reward，并加入 cost-scale invariance 单测。修正后 4 个追加 simulation
分配到 4 个不同 root branches。

### 20.5 Two-event physical protocol

原 terminal Root MC rollout 关闭随机后续事件，因此只有一个真实决策点，直接套
UCT 只会变成 root bandit。depth=2 使用明确的物理协议：

```text
event 1:
  immutable snapshot 上的 machine breakdown

follow-up eligibility:
  event 1 machine repaired
  至少新完成 5 道 operation
  loaded transport count = 0
  当前或未来已排程 operation 可安全重调
  residual problem 无 unresolved commitments

event 2:
  在首个 eligible state 注入第二次 machine breakdown

horizon:
  terminal
```

长度为 1 的 planning sequence 在第二事件使用冻结的
`CP-SAT+LG-LaCAM` continuation；长度为 2 的 sequence 使用树中第二动作。这样
root coverage 和 depth-2 simulation 都经历相同的两事件物理任务。

### 20.6 首个真实 UCT pilot

单 cluster：

```text
topology/seed: maze-b/110
planning seeds: 50110-50119
search budget: 20 s
simulation limit: 10
root coverage: 6-action parallel
depth-2 simulations: 4
planning wall: 15.25 s
all deadline/session/physical checks: passed
```

planning：

```text
flat Root selected:
  [CP-SAT+EECBS, CP-SAT+LG-LaCAM]

UCT selected:
  [CP-SAT+EECBS, CP-SAT+EECBS]
```

完全独立 execution seed `50120`：

```text
flat Root held-out makespan: 485
UCT held-out makespan: 485
UCT improvement: 0

physical outcome hash:
  两条 sequence 完全相同

PlanRevision output hashes:
  三次 revision 全部相同
```

Artifacts：

```text
planning:
experiment/skycausal/results/open_loop_uct_20260805/
maze_b_seed110_planning50110_final.json
SHA256:
ff56d8db83206f7e639cd8b48b15f762deebd729e820768d513ad010f9bfecd6

held-out execution:
experiment/skycausal/results/open_loop_uct_20260805/
maze_b_seed110_execution50120.json
SHA256:
103e06ea51b8cc34497156321a492f2f784f0e207a868fe0c040971f149e0c74
```

### 20.7 当前结论边界

当前可以声称：

```text
20-cluster development Search Value Gate 按预注册指标通过；
5 到 10 秒是当前 terminal k=1 的有效预算区间；
parallel hard-kill 后 session/request 可回收；
open-loop UCT 的真实 two-event execution chain 已成立。
```

当前不能声称：

```text
UCT 优于 flat Root MC；
单 cluster 的 UCT tie 构成 Search Value evidence；
20 秒 UCT 满足最终在线预算；
development dirty worktree 结果可作为 publication-locked evidence。
```

下一步必须在冻结的 two-event protocol 上做多 cluster、planning/execution seed
分离的 UCT vs flat Root held-out Gate。若 UCT 的正增益 CI 不能通过，应保留 flat
Root MC 作为最终搜索算法，而不是为了算法复杂度强行使用 UCT。

### 20.8 8-cluster UCT development pilot：Gate 失败

按 20.7 的冻结协议执行原 8-cluster development cohort。每个 cluster 使用：

```text
20 s total search budget
5 s per-simulation hard cap
6-action parallel paired root coverage
最多 10 个 simulations
独立 held-out execution seed
```

`maze/112` 中 `PSO+MAPF-LNS2` 分支直到 terminal 没有出现第二安全事件，因此：

```text
complete paired root coverage: false
paired stratum backup: 0
selection: fixed fallback
cohort treatment: two-event eligibility exclusion
```

没有更换 seed 或填充惩罚 cost。其余 7 个有效 clusters 的 UCT 相对 flat Root
held-out improvement：

```text
maze/110:    +16
maze/111:     +4
maze/113:     -4
maze-b/110:  -51
maze-b/111:   +1
maze-b/113:    0
maze-b/114:  +12
```

汇总：

```text
eligible clusters: 7
excluded clusters: 1
wins / ties / losses: 4 / 1 / 2
mean improvement: -3.14
median improvement: +1.00
cluster-bootstrap 95% CI: [-20.15, 8.71]
sequence change rate: 85.71%
same physical outcome rate: 14.29%
mean planning wall: 14.13 s
```

Gate：

```text
minimum cluster count: passed
all planning/held-out infrastructure Gates: passed
mean improvement > 0: failed
cluster-bootstrap CI lower > 0: failed

overall UCT value Gate: failed
```

Analysis artifact：

```text
experiment/skycausal/results/open_loop_uct_8cluster_20260805/
analysis.json

SHA256:
92a151f1f3918a274f56e1982573afb3d3dd9d264c3b11e2851711d6fc400c22
```

当前阶段决策：

```text
不把 UCT 扩展到 20 clusters；
不根据该批 held-out 结果继续调 exploration constant 或 continuation；
保留 Stratified Root MC k=1 作为当前搜索后端；
保留 UCT 内核、two-event evaluator 和负结果；
后续 learned value / PUCT 可在新预注册协议下重新挑战 flat Root。
```

该结论不是“证明 UCT 必然更差”，而是：

```text
在当前 20 s 预算、稀疏 depth-2 sample 和冻结 two-event protocol 下，
没有证据支持 UCT 相对 flat Root 的额外复杂度。
```

因此后续 teacher logs 应优先来自已经通过 20-cluster held-out Gate 的
Stratified Root MC，而不是来自当前未通过 value Gate 的 UCT。
