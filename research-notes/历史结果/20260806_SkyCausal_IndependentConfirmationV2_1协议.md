# SkyCausal Independent Confirmation Protocol v2

日期：2026-08-06

状态：`FROZEN_FOR_EXECUTION`。正式执行必须从 component stress 开始；在正式
component/root infrastructure stress 全通过前，禁止 capture、planning 或
heldout。

## 一、确认目标

本协议确认同一个预先定义的主结论：

> 在 J10P5M6、两类固定 maze layout、high-severity machine breakdown 和严格
> 12 秒 Root wall budget 下，基于同一物理 snapshot、CRN 和六个联合 solver
> profile 的 Stratified Root Monte Carlo `terminal, k=1`，相对本 cohort 上
> ex-post global best fixed profile 降低 heldout capped terminal makespan。

方法名固定为：

```text
Deadline-Safe Counterfactual Root Search
implementation: Stratified Root Monte Carlo, terminal, k=1
```

本协议不把工程实现包装为新的通用 MCTS，不授权 Teacher/BNN/deterministic
model 训练，不重启 open-loop UCT 调参，也不授权 causal identification 或跨规模
泛化主张。

## 二、与 v1 的关系

已完成的 v1 协议与正式 artifact 保持只读：

```text
v1 protocol:
  research/20260806_SkyCausal_PublicationRerun协议.md

v1 protocol SHA256:
  f650f738528deac5d0cf5e880a52af41439496cc18b87e0c1c06d3999238913c

v1 artifact:
  artifacts/skycausal_publication_rerun_v1_f650f738/

v1 result:
  statistical subgate PASS
  Infrastructure Gate FAIL
  C2/C4 FAIL
```

v1 的 40 个 selected clusters、所有 heldout cost、fallback cluster 和结果后统计均
已观察，禁止作为 v2 确认样本。v2 继承 v1 的 action space、capture eligibility、
预算、failure-as-cost、baseline、primary endpoint 和统计规则；本文件列出的 v2
差异优先。

v1 的正效果量不用于改变零阈值、预算、样本量、profile 或分析方法。它仅解释
为什么必须在新独立 cohort 上确认基础设施修复后的完整证据链。

## 三、冻结工程基础

冻结实现：

```text
SkyEngine commit:
  543c6a6dfe1c446c762268b83d500c60a4fc3f39

SkyEngine image:
  sha256:3a76f010a02cf4fae65a3a6a56156aa0225febb04f832725352edb3e2c880b4d

OCI revision:
  543c6a6dfe1c446c762268b83d500c60a4fc3f39

clean-image/no-source regression:
  227/227 PASS
```

其余 solver commit、image 和 profile 不变：

```text
SkyEngine-MAPF commit:
  68bf40005dcf479442043f07d08648149cc8913e

MAPF image:
  sha256:35a1600badd25ec60dd592819afc692ece3b6259c22dc1de417c308c51ae5c24

SkyEngine-FJSP commit:
  5eadb479c0f038057595b0e44de5d633ad900d21

CP-SAT image:
  sha256:0cec9b5f10da492b799143205ae01e05ad14815fb0bb1359b4b72fd5fd11a660

DE image:
  sha256:1a9504077db33b6b5536c94e34b9a15acccf0aa5f2c9b880c8ef363096ddc6e8

PSO image:
  sha256:08f48c437010490c598b5e96465000783589dceb4857b78ad41c453d51a54bfb

profile:
  experiment/skycausal/protocols/joint_profiles_publication_v1.json

profile SHA256:
  39270a4d5aa31f873f3646f42bcaaeb6649bf94e553a1accc326ec8de27e8f04

machine-readable config:
  experiment/skycausal/protocols/publication_confirmation_v2.json

machine-readable config SHA256:
  9a7887bff9a54131664476f66d76c2edf111c12a3b9346b49943a4196004af93

claim matrix:
  research/20260806_SkyCausal_IndependentConfirmationClaimMatrix.md

claim matrix SHA256:
  c0faa5a1c3e9d5fca787bab7590cd21c1fe1a822f52d8ad9588713b1ea9a43ab
```

基础设施修复只改变执行正确性：

1. Root worker 的 FJSP/MAPF request 使用唯一 prefix；
2. 父进程终止 worker 后按 prefix 定向 cancel 远端 request；
3. cancel ACK、active request 归零和 MAPF session cleanup 都进入 Root Gate；
4. MAPF 预算耗尽且请求未发出的 retry 计为 accounted non-admission；
5. solver internal fallback 计为 failed branch，不得作为 completed backup。

## 四、冻结前 Root Infrastructure Gate

在任何 v2 candidate capture 前，必须把 root-level stress 实现为可重复、可校验的
正式 phase，并在上述无源码挂载镜像上执行。

冻结前 development preflight：

```text
artifact:
  artifacts/skycausal_confirmation_v2_preflight_dev_06/

component stress:
  600/600 PASS

root normal:
  25/25 safety semantics PASS

root forced deadline:
  25/25 safety semantics PASS

final active requests / MAPF sessions:
  0 / 0
```

该 preflight 只授权协议冻结，不计作 publication evidence。

固定 infrastructure snapshot：

```text
development seed:
  140

snapshot SHA256:
  92539be29998bbe3ae96de8295e9081ef26df239fabda50ae641f79004363226

planning seed:
  9960140

role:
  infrastructure stress only; prohibited from effect analysis
```

该 snapshot 早于 publication deterministic-capture policy 字段，仅用于重复
process/request/session lifecycle stress；runner 不把它送入 cohort eligibility，
也不从中生成任何论文效果量。

固定 stress：

```text
component deadline stress:
  6 solvers x (50 normal + 25 hard deadline + 25 explicit cancel)
  = 600 requests

root normal stress:
  25 repetitions
  per-simulation cap = 10000 ms

root forced-deadline stress:
  25 repetitions
  per-simulation cap = 200 ms
```

component normal requests 使用固定的小/中型 synthetic lifecycle fixtures，并保持
profile 的 FJSP `1000 ms`、MAPF `500 ms` hard budget；它们的目标是验证 50 次
successful completion、物理结果和 cleanup，不承担 workload 边界测量。实际
J10P5M6 snapshot 上的 budget-edge completion、solver fallback 与 hard deadline
全部由下述 Root normal stress 保留并审计。

每个 normal-budget Root 只接受以下三种结果：

1. 六分支全部完成并原子提交一个 stratum，全部 Root Gates PASS；
2. 一个或多个分支仅因 `fjsp_solver_fallback` 或
   `mapf_solver_fallback` 失败，六分支均不 backup，effective action 为 runtime
   fallback；
3. 一个或多个分支达到预注册 `10000 ms` hard deadline，全部
   `hard_deadline_exceeded` 均有 process audit，六分支均不 backup，effective
   action 为 runtime fallback。

后两种是预注册的安全退化，不是基础设施失败，但
process/physical/deadline/cleanup/quiescence safety Gates 必须全通过。任何其他
evaluator error、process 状态、partial backup、unaccounted deadline 或非预期
return code 都使 repetition FAIL。每个 forced-deadline Root 必须满足：

```text
six branches hard_deadline_exceeded
paired backup count = 0
partial_backup_count_zero = true
all_process_deadlines_accounted = true
worker_remote_request_cleanup_complete = true
worker_session_cleanup_complete = true
all_services_quiescent = true
all_mapf_sessions_released = true
final active request count = 0
final MAPF session count = 0
```

forced-deadline Root 的 `root_coverage_complete=false` 和整体
`gate_passed=false` 是预期结果，不构成 stress failure；它必须选择 runtime
fallback，且不得产生任何 partial backup。

任一 stress repetition 失败即停止，不得开始 v2 capture。失败 artifact 原样保留。

## 五、独立 Cohort

固定范围：

```text
family:                  j10
FJSP instance:           J10P5M6
topologies:              maze, maze-b
candidate seeds:         300..349 inclusive
target eligible:         20 per topology
event:                   machine_breakdown
severity:                high
response action:         affected_job_partial_rescheduling
AGVs:                    4
processing preset:       moderate_variance
due factor:              1.10
episode cap:             1000
```

`300..349` 未用于 v1、Teacher 或 development `100..149`。不得预先运行六个
profile 来筛 candidate。

每个 candidate 只执行两次 deterministic capture：

```text
CP-SAT workers:                  1
CP-SAT max deterministic time:  0.1
capture hard wall:               5.0 s
capture repetitions:             2
```

两次均 eligible 且 semantic signature 相同才 eligible；不允许第三次补跑。每个
topology 按 seed 升序选择前 20 个 eligible snapshots。任一 topology 在完整
`300..349` 中不足 20 个，Cohort Gate FAIL 并停止。

## 六、Seed Roles 与预算

```text
planning base:       6000000
heldout base:        7000000
topology stride:       10000
bootstrap seed:     20260807
bootstrap reps:          10000
```

planning 和 heldout seeds 严格分离。冻结预算保持：

```text
FJSP hard budget:       1000 ms
MAPF hard budget:        500 ms
Root wall:             12000 ms
per-simulation cap:    10000 ms
commit reserve:          100 ms
cancellation grace:      100 ms
termination grace:        50 ms
rollout:                terminal
k:                             1
```

runtime fallback 固定为 `CP-SAT+LG-LaCAM`。evaluation best fixed 仍是在 v2
完整 heldout cohort 上 ex-post 均值最优的单一 profile，两者不得混同。

## 七、Failure 与统计

planning 任一分支失败、internal fallback、incomplete stratum 或 audit Gate
失败，整个 stratum 禁止 backup，effective action 使用 runtime fallback。
heldout 任一 branch timeout/error/internal fallback，cost 固定为 `1000`。
cluster 不删除。

Primary endpoint：

```text
best_fixed heldout capped makespan
- Root_or_fallback heldout capped makespan
```

Primary Gate：

```text
40/40 clusters retained
mean improvement > 0
topology-stratified cluster-bootstrap 95% CI lower > 0
all Infrastructure Gates PASS
```

bootstrap 使用 percentile 95% CI、10000 replicates、seed `20260807`。不得因
观察 v1 结果而切换单侧检验、删除 failure cluster 或改变 best-fixed 定义。

C1 headroom、C3 baselines 和 C5 `2/5/10/12 s` conservative admission curve
沿用 v1。C5 只有在 v2 C2 通过时才能形成正向工作区间主张。

## 八、正式执行顺序

```text
component-deadline-stress
root-infrastructure-stress
capture
planning
heldout
pair-manifest
analysis
checksums
read-only-freeze
```

每个 phase 开始前验证三仓 commit、五个 image digest、profile/config/protocol
SHA、input SHA、endpoint identity 和 pre-run quiescence。正式运行禁止源码挂载。

最终目录：

```text
artifacts/skycausal_publication_confirmation_v2_<protocol_hash8>/
```

必须同时保留 raw successes、timeouts、cancel ACK、failed branch、health、
session cleanup、run/manifest/snapshot hashes 和完整 provenance。

## 九、停止与冻结规则

以下任一情况立即停止并保留已有 evidence：

1. worktree dirty，或 commit/image/profile/config/protocol hash 不一致；
2. root infrastructure stress 未通过；
3. pre-run quiescence 未通过；
4. eligibility 读取 action-dependent 字段；
5. snapshot/state key 不一致；
6. timeout/failure cluster 被删除；
7. artifact validator 或 checksum 失败。

冻结检查：

- [x] root infrastructure stress 正式 runner 与 analyzer
- [x] 对应 unit/tamper tests
- [x] clean commit 和新 immutable image
- [x] no-source-mount `227/227` regression
- [x] config/claim matrix 最终 SHA
- [x] 状态改为 `FROZEN_FOR_EXECUTION`

冻结后不得根据 v2 中间结果修订 Gate；统计失败或基础设施失败都不能成为重跑同一
cohort 的理由。
