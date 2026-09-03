# Flat Root Teacher 完整组 Retry 协议 v2

起草日期：2026-08-05

状态：v2 实现与镜像已固定；以本文最终 SHA256 生成独立 v2 数据

## 一、变更原因

Teacher v1 的 planning 数据完整，但 `maze/140` heldout 的 `DE+EECBS` worker 在
10000 ms hard deadline 终止，导致 paired coverage 只有 19/20。

v1 artifact 已只读冻结：

```text
path:
  artifacts/flat_root_teacher_smoke_v1_8c7a0d4d

dataset ID:
  bc0a23318f6f6da0b96e796cd5371b69b377462ad7e715c182edc8c6eea4e0af

checksums.sha256 SHA256:
  72929221e686e4621abf52ece6560e335aedf8aff85b647a651d17ffff2a14f6
```

禁止修改、补跑或重新标记 v1。本协议定义独立 v2 collection semantics；任何 v2
结果必须使用新的协议 hash、attempt bundle 和 dataset manifest。

## 二、不变项

v2 不改变：

```text
Teacher backend:
  Stratified Root Monte Carlo terminal k=1

action vocabulary/order:
  与 v1 完全一致

Root run budget:
  wall budget             12000 ms
  per-simulation hard cap 10000 ms
  commit reserve            100 ms
  cancellation grace        100 ms
  worker termination grace   50 ms

atomic commit:
  六个 action 全部按时完成才 commit
  incomplete attempt 的 0/6 branch 可进入标签

seed policy:
  与 v1 完全一致

label recipe:
  terminal capped makespan
  hard/tie-aware/tau10 policy targets
  oracle regret
  safe-baseline advantage
  best-fixed advantage
```

模型特征、raw branch/group schema、physical invariant、split 和 Neural/BNN Gate
均沿用 v1。v2 只增加离线 collection attempt 层，不增加在线 decision budget。

## 三、固定 Cohort

v2 不重新做 eligibility 选择，直接复用 v1 已在 action outcome 之前锁定的 20 个
snapshot：

```text
maze:
  130, 131, 132, 134, 135, 136, 137, 138, 139, 140

maze-b:
  130, 131, 132, 133, 134, 135, 136, 137, 138, 139
```

权威来源：

```text
v1 cohort_manifest.json SHA256:
  7cf8f09055649718bee3f87b17d590b63a6a72cc1c78fc91392ee512e72b8aac

v1 checksums.sha256 SHA256:
  72929221e686e4621abf52ece6560e335aedf8aff85b647a651d17ffff2a14f6
```

v2 必须逐文件复验并复制相同 snapshot bytes。不得重新捕获 snapshot、增加 seed、
删除难例或根据 v1 winner/cost/timeout 选择子集。

## 四、Attempt 语义

### 4.1 固定次数

每个 planning 或 heldout group 最多运行：

```text
max_full_group_attempts = 2
```

第一次成功时不运行第二次。第一次失败只有满足第 4.3 节的 infrastructure class
才能进入第二次；第二次后无论结果如何都停止。

### 4.2 同一反事实问题

两个 attempt 必须完全共享：

```text
snapshot bytes/hash
state seed
solver seed
rollout seed
seed role
六动作 vocabulary/order
profile config hash
Root run budget
三仓 source commit
全部 image digest
```

attempt index 不进入 solver/exogenous seed。每个 attempt 创建新的 worker process 和
MAPF session prefix，但不能改变反事实随机变量。

### 4.3 唯一允许的 Retry Class

允许 retry：

```text
retryable_atomic_hard_deadline:
  至少一个 action status=hard_deadline
  completed_simulation_count=0
  accepted_for_backup count=0
  partial_backup count=0
  physical/deadline/source Gate 无独立失败

retryable_postrun_quiescence:
  六分支结果完整
  但固定 post-run quiescence barrier 未通过
  整次 attempt 结果不得进入标签
```

禁止 retry：

```text
完整组 cost/winner 不理想
完整组出现 tie 或 margin 太小
physical invariant failure
terminal horizon incomplete
provenance/schema/input hash mismatch
snapshot eligibility failure
任一 partial backup 或部分 completed_simulation 已 commit
未注册异常类别
```

不得只重跑失败 action，不得合并两个 attempt 的分支，不得从一次 attempt 取 cost、
另一次 attempt 取 audit。

## 五、Quiescence Barrier

每次 attempt 前后都必须运行：

```text
timeout:
  5000 ms

poll interval:
  10 ms

stable samples:
  3 consecutive samples

FJSP condition:
  status=ok
  active_request_count=0

MAPF condition:
  status=ok
  active_request_count=0
  session_count=0
```

pre-attempt barrier 失败时不得启动 worker。post-attempt barrier 失败时，该 attempt
即使六分支完成也不得被接受；barrier 在 5000 ms 内未恢复则停止，不得继续 retry。

## 六、Accepted Attempt

accepted attempt 必须同时满足：

```text
Root run gate_passed=true
14 项 Root gate_checks 全 true
post-attempt stable quiescence=true
六个 action 各有且只有一个 completed attempt
六分支来自同一个 attempt index
adapter 完整复验通过
```

选择规则是“第一个满足全部条件的 attempt”，不是 cost 最优 attempt。失败 attempt
不得删除；accepted run 也不得覆盖其文件。

## 七、Attempt Bundle

每个 planning/heldout group 必须保存：

```text
attempt_bundle.json
attempt_01.json
attempt_01_manifest.json
attempt_01.log

若发生 retry:
  attempt_02.json
  attempt_02_manifest.json
  attempt_02.log
```

bundle schema：

```text
skycausal.flat-root-teacher-attempt-bundle.v1
```

bundle 至少绑定：

```text
protocol SHA256
family/topology/state seed
rollout seed
snapshot path/hash
固定 retry policy
每次 pre/post quiescence health audit
每次 run/manifest/log SHA256
return code
failure classification
accepted attempt index
final status
bundle hash
```

accepted branch/group payload继续使用 v1 raw schema，因为 action、state、cost 和标签
语义未改变；`protocol_sha256` 必须写 v2 hash。v2 dataset manifest 额外绑定每个
attempt bundle hash，因此不能与 v1 record 静默混合。

## 八、v2 Smoke Gate

v2 必须重新运行固定 20 cluster 的 planning 和 heldout，共 40 个 group。不得只补
`maze/140`。

Coverage Gate：

```text
planning accepted groups = 20/20
heldout accepted groups = 20/20
accepted branches = 240/240
attempt bundle validation = 40/40
snapshot byte match = 20/20
cross-attempt branch mixing count = 0
partial backup count = 0
post-run quiescence pass = 40/40
```

必须报告：

```text
first-attempt success rate
retry-trigger count and class
second-attempt success rate
retry exhaustion count
per-action hard-deadline count
quiescence latency distribution
```

Data/Label/Power Gate 沿用 v1。只有 v2 coverage、Data、Label 和 locked test Gate
全部通过后，才能讨论 deterministic neural baseline；BNN 仍需后续独立 Gate。

## 九、固定实现

```text
SkyEngine commit:
  b1389e9017a331f19ce7354370410fc741b3ff1e

SkyEngine image:
  sha256:b0f4a000c7863edc6e1c3b67760046c9eab4ce215ed80cefa7ce94c6ddef7933

OCI revision / embedded commit:
  b1389e9017a331f19ce7354370410fc741b3ff1e

solver images/profile:
  与 v1 locked provenance 完全相同
```

验证：

```text
retry contract tests:
  9/9 passed

Teacher/Root/Decision focused:
  45/45 passed

source-mounted SkyCausal:
  199/199 passed

immutable-image SkyCausal:
  199/199 passed

real first-attempt bundle/conversion preflight:
  passed

forced two-attempt retry_exhausted preflight:
  passed, 2 x 6 hard deadlines, 0 partial backups
```

## 十、实现与发布 Checklist

- [x] 实现 attempt classifier 和不可变 bundle
- [x] 实现 pre/post stable quiescence barrier
- [x] 强制 max attempts=2、same snapshot/seed、full-group only
- [x] 增加 hard deadline、partial backup、physical failure 测试
- [x] 增加 bundle tamper 和 cross-attempt mixing 测试
- [x] 实现 bundle-aware 原子 Teacher converter
- [x] Docker focused regression 通过
- [x] SkyCausal full regression 通过
- [x] clean commit 并重建 SkyEngine immutable image
- [x] 写入最终 commit 和 image digest
- [ ] 复制并复验 20 个 v1 snapshot
- [ ] 生成独立 v2 artifact
- [ ] 运行 Coverage/Data/Label/Power Gate
- [ ] 冻结 manifest 和 checksums

## 十一、当前决策

```text
v1 artifact:
  保留，只读，不补跑

v2 implementation:
  已固定

v2 data generation:
  允许，仅使用本文最终 SHA256 和固定 20 snapshot

model training:
  禁止
```
