# Flat Root Teacher 完整组 Retry v2 审核报告

日期：2026-08-05

结论：v2 artifact 已冻结；完整组 retry 未恢复 `maze/140`，Data/Coverage Gate
失败，禁止训练 deterministic neural baseline 或 BNN。

## 一、冻结输入

```text
Teacher:
  Stratified Root MC terminal k=1

Protocol:
  artifacts/flat_root_teacher_smoke_v2_2166de55/protocol.md
  SHA256:
  2166de55eeaeb4e0476bedb64c8e088a0456710a3ced47fbd51edeb73ce58441

SkyEngine commit:
  b1389e9017a331f19ce7354370410fc741b3ff1e

SkyEngine image:
  sha256:b0f4a000c7863edc6e1c3b67760046c9eab4ce215ed80cefa7ce94c6ddef7933

SkyEngine-MAPF commit:
  68bf40005dcf479442043f07d08648149cc8913e

SkyEngine-FJSP commit:
  1edcf14535d97e0f04d535f34aee81c3d944f6bc

Locked profile SHA256:
  b6e35b5281d7a1bce0c83500e5f41ab3206489fb17ddf08d1b6684e41f4422ce
```

20 个 snapshot 逐字节复制自只读 v1 artifact，`20/20` 与 v1 cohort manifest
中的 SHA256 相同。没有新增 seed、重新捕获 snapshot 或使用 evaluation cohort。

## 二、实现验证

```text
retry contract tests:             9/9
Teacher/Root/Decision focused:   45/45
source-mounted SkyCausal:       199/199
immutable-image SkyCausal:      199/199
```

固定镜像中的 OCI revision、embedded commit 和 run manifest 均指向同一 clean
commit。40 个 attempt bundle 和 38 个正式 group 均由固定镜像 validator 重放。

## 三、Collection 结果

```text
selected snapshots:       20/20
attempt bundles:          40/40
total full-group attempts:   41
planning groups:          19/20
planning branches:       114/120
heldout groups:           19/20
heldout branches:        114/120
paired clusters:          19/20
cross-attempt mixing:          0
partial backup:                0
all quiescence barriers:    PASS
```

## 四、Retry Audit

```text
first-attempt success:
  38/40 = 0.95

retry triggers:
  1
  class = retryable_atomic_hard_deadline

second-attempt success:
  0/1 = 0

retry exhaustion:
  1

final bundle status:
  accepted                         38
  nonretryable_nonatomic_failure    1
  retry_exhausted                   1

hard deadlines by action:
  DE+EECBS    2
  all others  0
```

82 个 pre/post quiescence barrier 的延迟：

```text
minimum:   39.67 ms
median:    44.12 ms
p95:       56.69 ms
maximum:  234.40 ms
```

所有 barrier 最终均满足：

```text
FJSP active_request_count = 0
MAPF active_request_count = 0
MAPF session_count = 0
stable samples = 3
```

## 五、两个 Rejected Group

### 5.1 `maze/140 teacher_planning`

```text
attempt count:
  1

classification:
  nonretryable_nonatomic_failure

completed simulations:
  6/6

accepted backups before group Gate:
  6/6

failed Gate:
  all_mapf_deadlines_accounted = false
```

失败来自 `DE+EECBS` 的一个 MAPF query：

1. 初始 500 ms EECBS request 已以 `hard_deadline_exceeded` 记账；
2. 后续两个 retry 在同一 deadline 下因 `no remaining budget` 未启动；
3. 两者记录 `cancel.status=not_started`；
4. 当前 Root gate 不把 `not_started` 视为 accounted。

physical invariants、session cleanup、service quiescence 和其余 Root gate 均通过。
但 v2 只允许 atomic hard deadline 或 post-run quiescence failure 触发 retry，不能因
已有六个 costs 而绕过失败 Gate，因此该组没有第二次 attempt，也没有进入 dataset。

### 5.2 `maze/140 heldout_execution`

```text
attempt 1:
  DE+EECBS hard deadline at 10019.09 ms

attempt 2:
  DE+EECBS hard deadline at 10021.85 ms

classification:
  retryable_atomic_hard_deadline x 2

result:
  retry_exhausted
```

两次 attempt 的其余五个 action 都完成，但每次都是整组六分支 atomic rejection。
两次 post-run barrier 均恢复到稳定 quiescence；没有跨 attempt 拼接分支。

## 六、Label 与 Power Audit

19 个完整配对 cluster 的结果与 v1 一致：

```text
tie-aware winner overlap:
  0.8947 [0.7368, 1.0000]

non-tie pair sign agreement:
  0.9339 [0.8696, 0.9847]

mean rank Spearman:
  0.8939 [0.7785, 0.9716]

planning winner heldout oracle regret:
  0.5789 [0.0000, 1.6842]

planning winner improvement vs heldout best fixed:
  25.2632 [13.3158, 38.3684]
```

Label signal Gate 和 primary-effect power target 通过，但不能抵消 cohort completeness
失败，也不授权训练。

## 七、Gate 决策

```text
training Data Gate:
  FAIL (19/20 planning groups, 114/120 branches)

paired audit coverage Gate:
  FAIL (19/20)

label signal Gate:
  PASS on 19 complete pairs

primary-effect power target:
  PASS

overall smoke Gate:
  FAIL

model training approved:
  NO
```

完整组 retry 对偶发 infrastructure failure 的语义已经实现并验证，但本次缺口是
`DE+EECBS` 在固定输入和预算下的可重复边界行为。不得增加 attempt、重跑单 action、
跨 attempt 拼接、调整 v2 budget 或回填 seed 141。

## 八、冻结 Artifact

目录：

```text
artifacts/flat_root_teacher_smoke_v2_2166de55
```

关键 SHA256：

```text
dataset ID / teacher_branches.jsonl:
  0b62b89d254d8d7f893740667a91f72c19b7149d8b1daf77781df24f9ba25042

dataset_manifest.json:
  d95e354a92ae89b54757646861c5895f8e8be87322e114e6e3c28cf420c411ce

checksums.sha256:
  32deab81e9526e893379141872a4893fb4eadbea9194fb8619f74b1f179a1523

data_gate.json:
  a5caba2c4d6f0b0921533a5cb370f4e33fd822c7898cbca123be748c22c0b0ce

retry_audit.json:
  81d50e3040f72eb3ac065279afb629f20d8232bd04d7cf0ea78b836271fc9bff

label_noise_audit.json:
  98d16c3b970eb0791a07bb242bd035fddd09ebcf57cbfa862bc379c82546382a

power_audit.json:
  ad618da6c30a1e6883423da5b6b241d1a0f763819fe6ae209509443fa0582523
```

固定镜像只读复验：

```text
checked files:
  437

status:
  valid
```

artifact 已执行 `chmod -R a-w`，后续只允许只读复验。

## 九、后续决策

v2 已回答“完整组 infrastructure retry 能否恢复 coverage”：不能。当前不应继续
追加 retry 或训练模型。优先路径是停止 neural Teacher 分支，进入 clean publication
rerun；若未来重新研究该边界，必须新建协议版本，先独立审计：

```text
MAPF no-remaining-budget / not_started accounting semantics
DE+EECBS terminal runtime distribution
per-action cap 与 publication control deadline 的关系
```
