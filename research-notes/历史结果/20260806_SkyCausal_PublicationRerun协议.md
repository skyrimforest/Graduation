# SkyCausal Clean Publication Rerun Protocol v1

日期：2026-08-06

状态：`FROZEN_FOR_EXECUTION`。统计协议、主 cohort、publication
orchestrator、fallback-aware analyzer、最终 clean commit 和不可变镜像均已
冻结。publication evidence 只能由本文规定的正式 phase 顺序生成。

关联 Claim Matrix：

```text
research/20260806_SkyCausal_PublicationClaimMatrix.md
```

## 一、目标与边界

本协议只验证以下主结论：

> 在 J10P5M6、两类固定 maze layout、high-severity machine breakdown 和严格
> 12 秒 root wall budget 下，基于同一物理 snapshot、CRN 和六个联合 solver
> profile 的 Flat Root MC k=1，相对 publication cohort 上的 ex-post global
> best fixed profile 降低 heldout capped terminal makespan。

主方法名称：

```text
Deadline-Safe Counterfactual Root Search
implementation: Stratified Root Monte Carlo, terminal, k=1
```

本文不授权：

1. neural Teacher、deterministic model 或 BNN 训练；
2. open-loop UCT 调参或重跑；
3. causal identification、跨规模泛化或跨扰动泛化主张；
4. 修改 Teacher v1/v2 或已有 20-cluster development artifact；
5. 用旧 development 结果填充 publication 缺失值。

## 二、冻结工程基础

当前已审计基础版本：

```text
SkyEngine commit:
  00cdfceb2c472942f9b201432097ac50f2d27149

SkyEngine image:
  sha256:4bceed45473e3857f522d11883aaa6754faca2c613b38b6b3572da6c3451b4ad

SkyEngine-MAPF commit:
  68bf40005dcf479442043f07d08648149cc8913e

SkyEngine-MAPF image:
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

machine-readable protocol:
  experiment/skycausal/protocols/publication_rerun_v1.json

machine-readable protocol SHA256:
  f97742ce496318d666839bbcf62279e8ea84242a99af27a0777a88652b0dd46f
```

冻结前已完成：

1. clean-image 全量 SkyCausal 回归 `218/218`；
2. 六 endpoint、24-request integration smoke；
3. final clean commit；
4. commit-tagged immutable image；
5. 无源码挂载容器全量回归 `218/218`；
6. OCI revision 与 final commit 精确一致。

正式运行必须设置并锁定：

```text
SKYENGINE_CODE_COMMIT
FJSP_CODE_COMMIT
MAPF_CODE_COMMIT
SKYENGINE_IMAGE_DIGEST
FJSP_IMAGE_DIGEST
FJSP_CP_SAT_IMAGE_DIGEST
FJSP_DE_IMAGE_DIGEST
FJSP_PSO_IMAGE_DIGEST
MAPF_IMAGE_DIGEST
```

其中 `FJSP_IMAGE_DIGEST` 等于 CP-SAT image digest；三个 solver-specific FJSP
digest 必须分别与 frozen profile 精确一致。deadline stress 还必须验证六个
endpoint 返回的 solver/algorithm identity。

正式 phase 顺序固定为：

```text
deadline-stress
capture
planning
heldout
pair-manifest
analysis
```

## 三、主确认 Cohort

### 3.1 固定维度

```text
FJSP:
  family: j10
  input: J10P5M6.json

MAPF:
  maze:
    medium-mazes-seed-0000@medium_maps.yaml
  maze-b:
    medium-mazes-seed-0001@medium_maps.yaml

event:
  machine_breakdown

severity:
  high

response:
  affected_job_partial_rescheduling

AGV:
  4

processing time:
  moderate_variance

due factor:
  1.10

episode cap:
  1000
```

### 3.2 Candidate 与选择规则

每个 topology 的 candidate state seeds 固定为：

```text
200..239
```

按 seed 升序选择前 20 个 action-independent eligible snapshots：

```text
maze:    target 20
maze-b:  target 20
total:   target 40
```

若任一 topology 在 `200..239` 中不足 20 个 eligible snapshots：

```text
cohort Gate = FAIL
不得扩展 seed range
不得从另一 topology 补齐
不得根据 action cost 替换 snapshot
```

### 3.3 Eligibility

Eligibility 只能读取 action 执行前的 snapshot：

1. 已到达预注册的第一个安全 machine-breakdown decision；
2. 当前没有 loaded transport；
3. event、target machine 和 repair scope 可序列化；
4. snapshot restore 后 state key、event cursor 和 RNG state 一致；
5. 六个 profile 对该状态均为声明 action，但不要求提前执行成功；
6. 两次独立 capture 均 eligible；
7. 两次 capture 的 semantic signature 完全一致。

每个 candidate 固定执行两次 action-independent capture。snapshot 生成使用：

```text
CP-SAT workers:                 1
CP-SAT max deterministic time: 0.1
capture hard wall limit:        5.0 s
capture repetitions:            2
```

`max deterministic time` 固定 CP-SAT 搜索工作量；5 秒只作为基础设施 hard
deadline，不是 action 的在线预算。该设置不进入六分支 action profile，正式 action
仍使用 1000 ms FJSP hard budget。

semantic signature 绑定：

```text
state key and capture policy
clean physical outcome hash
canonical physical environment state
schedule audit without runtime UUID
machine-breakdown target
```

request UUID、wall time、deadline timestamp 和 disabled exception injector 的未使用
RNG state 不进入 semantic signature，但保留在原始 snapshot 和 manifest 中。两次
snapshot 文件各自保留 SHA256；仅第一份作为后续 planning/heldout 的冻结输入。

若两次 eligibility 不一致或 semantic signature 不一致，该 candidate 按
action-independent instability 排除，不允许追加第三次 capture。

禁止读取：

```text
profile terminal cost
profile runtime
winner
planning selection
heldout outcome
```

orchestrator 必须自动按候选顺序执行并输出选择日志，操作者不得手工挑选。

### 3.4 Capture 实现审计

implementation-gate preflight 发现原 1 秒 wall-clock CP-SAT capture 不可作为
publication cohort 生成器。同一 request hash、seed 和输入的 5 次 clean solve
中，CP incumbent makespan 出现 `29/30` 两种结果，并使同一 `maze/133` 的
eligibility 在连续运行中出现 `true/false`。

引入 `max_deterministic_time=0.1` 后，同一请求连续 5 次的 CP 分支数、schedule、
terminal physical hash 全部一致。`maze/seed-200` 两次完整 capture 的 snapshot
文件 SHA256 不同（保留各自运行时审计），但 semantic signature 一致。以上仅为
实现 Gate 证据，不计入 publication cohort 或论文效果量。

## 四、Seed Roles

每个 topology 使用不同 namespace：

```text
topology code:
  maze:   1
  maze-b: 2

planning rollout seed:
  4_000_000 + topology_code * 10_000 + state_seed

heldout execution seed:
  5_000_000 + topology_code * 10_000 + state_seed

bootstrap seed:
  20_260_806
```

约束：

1. state seed 只负责 snapshot；
2. planning seed 只用于 profile selection；
3. heldout seed 只用于最终评价；
4. planning/heldout 不共享 rollout RNG；
5. heldout cost 不得反馈到 action selection；
6. attempt index 不进入任何随机种子。

## 五、Action Space 与 Baselines

固定 action 顺序：

```text
CP-SAT+EECBS
CP-SAT+LG-LaCAM
DE+EECBS
DE+LG-LaCAM
PSO+LG-LaCAM
PSO+MAPF-LNS2
```

区分：

```text
runtime fallback:
  CP-SAT+LG-LaCAM

evaluation global best fixed:
  在全部 40 个 heldout clusters 上，对六个 profile 的 capped mean
  取最小者；这是对 fixed baseline 有利的 ex-post 选择。
```

必须报告：

1. runtime fallback；
2. ex-post global best fixed；
3. ex-post per-topology best fixed；
4. leave-one-cluster-out topology-backoff static selector；
5. heldout oracle。

static selector 只使用其他 clusters 的 planning costs：

```text
fold:
  leave one cluster out

feature:
  topology only

minimum topology group:
  5

topology prior strength:
  10

forbidden:
  state seed
  planning/heldout seed
  snapshot hash
  heldout profile cost
  terminal outcome
```

Root Search 的主 Gate 必须独立优于 global best fixed，不能以 static selector
更弱为替代证据。

## 六、严格预算与执行语义

### 6.1 Solver budget

沿用 profile v2：

```text
FJSP hard budget: 1000 ms
MAPF hard budget:  500 ms
```

每个 solver outcome 必须是：

```text
completed
hard_deadline
explicit_cancel
```

且均有 request/session/process audit。

### 6.2 Root budget

```text
wall budget:              12000 ms
per-simulation hard cap:  10000 ms
commit reserve:             100 ms
cancellation grace:         100 ms
termination grace:           50 ms
simulation limit:             6
execution mode: warm_profile_pool
rollout horizon: terminal
strata:                       1
```

六个 action 从同一 snapshot 并行执行。只有六分支全部 completed 且全部物理、
deadline 和 process Gates 通过，才允许原子提交 paired stratum，并选择最低
planning capped cost。

### 6.3 在线 fallback

任一 planning branch 出现：

```text
hard deadline
explicit cancel
process failure
physical invariant failure
incomplete terminal horizon
post-run cleanup failure
```

则：

```text
paired backup count = 0
selected profile = CP-SAT+LG-LaCAM
cluster 保留在主分析
```

不得从其余五个分支中选择，不得重跑单 action，不得跨 attempt 拼接。

### 6.4 Heldout failure-as-cost

heldout 六分支用于构造评价 cost matrix，不执行 action selection。每个 branch：

```text
completed and physically valid:
  cost = terminal makespan

hard deadline / cancel / solver error / invalid physical output /
incomplete episode:
  cost = episode cap = 1000
```

失败 branch 保留并计 cap。只要 snapshot eligibility 已通过，不能因 heldout
结果排除 cluster。

### 6.5 Retry 与恢复

solver deadline、Root deadline、branch failure 和 post-action cleanup failure
均不允许 retry。

只允许下列 pre-admission infrastructure resume：

```text
尚未启动任何 simulation；
没有生成 snapshot 或 action outcome；
失败原因是 image pull、container startup 或 pre-run health unavailable；
最多恢复一次；
两次 preflight 记录均写入 manifest。
```

每个 candidate 的两次 capture 是预注册测量，不属于 retry。第二次完成后不允许
追加 capture。一旦 planning/heldout action admission 开始，该 cluster 不再重跑。

## 七、主指标与统计

### 7.1 Primary endpoint

对每个 cluster `i`：

```text
improvement_i =
  capped_cost_i(global_best_fixed)
  - capped_cost_i(Root_or_fallback)
```

全体 40 clusters 的 mean improvement 是唯一 primary endpoint。

### 7.2 Primary CI

```text
method:
  topology-stratified cluster bootstrap

replicates:
  10000

seed:
  20260806

interval:
  percentile 95%
```

每次 bootstrap 在 maze 与 maze-b 内分别有放回抽取 20 个，再合并计算均值。

Primary Search Value Gate：

```text
eligible cluster count = 40
mean improvement > 0
95% CI lower > 0
all eligible clusters included
all provenance checks pass
all physical invariant violation counts = 0
all process/request/session outcomes accounted
```

任一失败则 C2 为 `FAIL`。不得改用相对百分比、median 或子组结果替代。

### 7.3 Secondary metrics

完整报告但不替代 primary Gate：

1. relative improvement；
2. win/tie/loss；
3. oracle regret 与 regret closed；
4. oracle hit rate；
5. selection profile distribution；
6. root complete-coverage rate；
7. fallback rate；
8. per-topology effect 与 CI；
9. global/per-topology fixed、static selector 和 oracle 对比；
10. planning wall p50/p95/p99/max；
11. aggregate action compute；
12. solver request latency p50/p95/p99/max；
13. hard deadline、cancel、fallback、late worker 和 orphan session counts。

secondary comparisons 不做多重比较后的正式 superiority 声明。

## 八、Headroom 与 Deadline Gates

### 8.1 Portfolio Headroom Gate

从同一 40-cluster heldout cost matrix 计算：

```text
oracle improvement =
  global best fixed capped cost - heldout oracle capped cost
```

Gate：

```text
mean oracle improvement > 0
95% stratified-bootstrap CI lower > 0
non-best-fixed winner rate >= 0.20
strict FJSP winner algorithms >= 2
strict MAPF winner algorithms >= 2
```

### 8.2 Deadline Safety Gate

正式数据运行前，在最终 publication image 上复跑六类 solver stress：

```text
per solver:
  50 normal completion
  25 hard deadline
  25 explicit cancel

total:
  600 requests
```

Gate：

```text
expected outcome: 600/600
physical invalid completion: 0
unaccounted request: 0
active_request_count after barrier: 0
MAPF session_count after barrier: 0
late active worker: 0
```

Root runs还必须满足：

```text
partial backup: 0
unaccounted process termination: 0
post-run quiescence failure: 0
```

### 8.3 Session Cleanup 实现审计

首次 formal preflight（旧 protocol SHA256 `fdf823c6...`）在第 0 个 publication
request 前被 pre-stress quiescence Gate 拒绝。原因是 development stress smoke
使用 MAPF legacy session 且未删除，三个 MAPF endpoint 各残留 1 个 session。
该次失败保存在：

```text
artifacts/skycausal_publication_rerun_v1_fdf823c6/
```

修复后每个 MAPF stress request 使用独立 `session_id=request_id`，每次 normal、
hard-deadline 或 explicit-cancel 后均显式执行 session DELETE，并把 cleanup
response 和终态 `session_count` 写入 raw row。修复后的 24-request integration
smoke 达到：

```text
expected outcome:       24/24
session cleanup failure: 0
orphan session:          0
final MAPF session_count: 0/0/0
```

旧 preflight 没有生成 publication cost 或 cohort 数据，不进入正式分析。

### 8.4 Capture 装配与 Fallback Analyzer 审计

旧 protocol SHA256 `b19cf619...` 下的第一次 capture 在首个 candidate 读取 input
SHA 前停止：运行容器没有挂载 frozen FJSP input。该次失败为 `0` 个
publication action、`0` 个 selected cluster，保存在：

```text
artifacts/skycausal_publication_rerun_v1_b19cf619_failed_capture_mount_01/
```

补齐只读 input mount 后，旧 protocol 的 C4 和 capture Gate 均通过；planning
在第 10 个已写出 cluster 停止。触发条件是六分支均 completed、六分支均被完整
stratum 原子接受，但全局 `all_mapf_deadlines_accounted=false`。旧 analyzer
错误地把该全局审计失败当成 partial backup。该次停止为 `0` 个 heldout run，
保存在：

```text
artifacts/skycausal_publication_rerun_v1_b19cf619/
```

冻结语义修正为：

```text
strict accepted subset:
  invalid partial backup -> hard reject

all six accepted + any required global audit fails:
  Root incomplete -> runtime fallback
```

修复同时规定：incomplete Root 的内部 reported profile 不与 effective runtime
fallback 比较；只有 complete Root 才要求 reported profile 精确等于重算的最低
cost profile。两次旧 protocol 运行均不进入最终 publication 分析。

## 九、Quality-Latency-Fallback Curve

使用正式 planning raw wall time做预注册 conservative admission replay：

```text
budgets:
  2 s
  5 s
  10 s
  12 s

reserve:
  admission margin 100 ms
  commit reserve   100 ms
  cancel grace     100 ms
```

完整 paired stratum 的 measured wall 超过可用 simulation time 时，选择 runtime
fallback。每个 budget 必须报告：

```text
coverage
fallback count
capped heldout mean
improvement vs global best fixed
95% CI
oracle regret closed
```

该图是 admission-policy replay，不得伪装为四次独立 wall-clock 执行。

## 十、Robustness Extension

跨规模/随机地图是 C7 的增强证据，但当前 J20 dynamic Root budget 尚未在最终
solver images 上校准。因此本协议不允许直接把 J20 或 random topology 加入
primary cohort。

执行顺序：

1. 使用明确标记为 development-only 的新 calibration seeds；
2. 只评估 J20/J10-random 的可运行性、deadline 和 snapshot eligibility；
3. 不把 calibration cost 写入论文结果；
4. 另行冻结 `PublicationRobustness补充协议`；
5. 使用完全未观察的新 seeds 执行 robustness cohort。

若不完成补充协议，论文范围必须限定为本协议第三节，不得声称 C7。

## 十一、Artifact

最终目录：

```text
artifacts/skycausal_publication_rerun_v1_<protocol_hash8>/
```

必须包含：

```text
protocol.md
claim_matrix.md
cohort_manifest.json
candidate_log.jsonl
snapshots/
capture/
stress/
planning/
heldout/
health/
analysis/
  infrastructure_gate.json
  headroom.json
  search_value.json
  budget_curve.json
  subgroup_analysis.json
tables/
figures/
provenance.json
dataset_manifest.json
checksums.sha256
```

每个 run 绑定：

```text
run JSON SHA256
manifest SHA256
stdout/stderr log SHA256
snapshot SHA256
profile SHA256
input SHA256
protocol SHA256
三仓 full commit
SkyEngine、CP-SAT、DE、PSO、MAPF image digests
六 endpoint solver/algorithm identity
pre/post health and quiescence
```

完成后：

```text
chmod -R a-w artifact_directory
固定 image 内无源码挂载复验
全目录 checksum 复验
```

## 十二、预注册表图

主文：

```text
Table 1  Cohort and protocol
Table 2  Six-profile headroom
Table 3  Heldout search value and baselines
Table 4  Deadline/cancel/session safety
Figure 1 Counterfactual Root Search execution contract
Figure 2 Quality-latency-fallback curve
```

Appendix：

```text
per-cluster costs and selections
per-topology results
static selector details
all failure classifications
milestone negative result
open-loop UCT negative result
Teacher v1/v2 coverage failure
```

## 十三、执行 Checklist

### A. 实现冻结

- [x] publication config schema 与参数 validator
- [x] ordered candidate/eligibility orchestrator
- [x] deterministic-time CP-SAT capture 与双 capture semantic Gate
- [x] planning incomplete -> runtime fallback
- [x] heldout branch failure -> episode cap
- [x] topology-stratified bootstrap analyzer
- [x] baseline、headroom、budget 与 deadline reports
- [x] unit tests 与 tamper tests
- [x] full SkyCausal regression
- [x] clean commit 与 immutable image
- [x] no-source-mount image regression
- [x] 最终 commit/image/profile/config hashes

### B. 数据执行

- [ ] 600-request Deadline Safety Gate
- [ ] ordered candidate scan
- [ ] 40 snapshots frozen
- [ ] 40 planning runs
- [ ] 40 heldout runs
- [ ] final health/quiescence
- [ ] C0/C1/C2/C4/C5 analyses
- [ ] tables/figures
- [ ] manifest/checksums/read-only freeze
- [ ] fixed-image independent validation

## 十四、停止规则

出现以下任一情况立即停止后续 publication run，但保留已有证据：

1. 三仓 commit 或 image digest 与协议不一致；
2. profile/input/protocol hash 不一致；
3. publication worktree dirty；
4. pre-run quiescence 不通过；
5. candidate selection 读取 action-dependent 字段；
6. snapshot/state key 不一致；
7. artifact validator 或 checksum 失败。

统计 Gate 失败不是删除数据或重跑的理由。完整数据仍冻结，论文主张按 Claim
Matrix 降级。
