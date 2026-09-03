# Flat Root Teacher v1 Smoke 审核报告

日期：2026-08-05

结论：Smoke 已冻结，但总体 Gate 失败；不得训练 deterministic neural baseline 或 BNN。

## 一、冻结输入

```text
Teacher:
  Stratified Root MC terminal k=1

Frozen protocol snapshot:
  artifacts/flat_root_teacher_smoke_v1_8c7a0d4d/protocol.md
  SHA256:
  8c7a0d4d870ee7fcd9ddc2f7973e5eb4f4e0fcfb0482e6abee3c12734f8b1363

SkyEngine commit:
  38af10d3c6cb1b0422719bc42a4141fda53af3d8

SkyEngine-MAPF commit:
  68bf40005dcf479442043f07d08648149cc8913e

SkyEngine-FJSP commit:
  1edcf14535d97e0f04d535f34aee81c3d944f6bc

Locked profile SHA256:
  b6e35b5281d7a1bce0c83500e5f41ab3206489fb17ddf08d1b6684e41f4422ce
```

生成和审核均使用固定 SkyEngine image：

```text
sha256:873e7c932732fc9248df0b39323e29ae1a1f280986f23eb84bfb742665b9249a
```

## 二、Cohort

按 topology 内 state seed 升序，只使用 action-independent eligibility，选取前 10 个：

```text
maze:
  130, 131, 132, 134, 135, 136, 137, 138, 139, 140

maze-b:
  130, 131, 132, 133, 134, 135, 136, 137, 138, 139
```

`maze/133` 未捕获到合格 snapshot，在查看 action cost 前排除。没有使用 evaluation
seed，也没有用 action winner 或相对效果决定是否补入候选。

## 三、完整性结果

```text
selected snapshots:       20
planning groups:          20/20
planning branches:       120/120
heldout groups:           19/20
heldout branches:        114/120
validated group dirs:      39
duplicate record IDs:       0
duplicate action branches:  0
split leakage:              0
future/terminal leakage:     0
```

唯一 paired 缺口是 `maze/140` 的 heldout group：

```text
rollout seed:
  3010140

failed action:
  DE+EECBS

failure:
  per-simulation 10000 ms hard deadline

atomic result:
  0/6 branches accepted for backup
  entire heldout group rejected
```

该 run 的即时 health audit 报告 `all_services_quiescent=false`。批处理结束后的独立
health check 已确认六个服务 `active_request_count=0`，且三个 MAPF 服务
`session_count=0`。没有重跑该组，也没有用 seed 141 回填。

## 四、Label-noise Audit

以下结果基于 19 个 planning/heldout 完整配对 cluster，均给出 10000 次
cluster bootstrap 95% CI：

```text
tie-aware winner overlap:
  0.8947 [0.7368, 1.0000]

deterministic winner agreement:
  0.8947 [0.7368, 1.0000]

non-tie pair sign agreement:
  0.9339 [0.8696, 0.9847]
  effective clusters: 18

mean rank Spearman:
  0.8939 [0.7785, 0.9716]

planning winner heldout oracle regret:
  0.5789 [0.0000, 1.6842]

planning winner improvement vs heldout best fixed:
  25.2632 [13.3158, 38.3684]

planning top-2 margin:
  15.1053 [7.3158, 23.8961]

internal fallback rate:
  0

episode-cap rate:
  0
```

`maze-b/134` 没有非 tie action pair，因此该 cluster 对 pair-sign 指标记为 `null`，
没有伪造分数。协议中的四项最低 label signal 检查均通过。

## 五、Power Audit

对“planning winner 相对 heldout best fixed 的均值改善大于 0”做经验 cluster
resampling：

```text
observed paired clusters:
  19

central required cluster estimate:
  11

bootstrap 95% interval:
  [5, 23]

power curve first tested point:
  n=20, estimated power=0.9987
```

该结果只回答上述 primary effect 的检测功效，不等价于神经模型泛化所需训练样本量，
也不授权把 20 个 cluster 当作正式训练 cohort。

## 六、Split

为同时满足 cluster、snapshot、group 和同数值 state seed 不跨 split，使用：

```text
strategy:
  cluster_hash_v1_state_seed_block

seed:
  20260806

cluster counts:
  train              15
  development         3
  locked_validation   2

record counts:
  train              90
  development        18
  locked_validation  12
```

## 七、Gate 决策

```text
training Data Gate:
  PASS

paired audit coverage Gate:
  FAIL (19/20)

label signal Gate on available pairs:
  PASS

primary-effect power target:
  PASS

overall smoke Gate:
  FAIL

model training approved:
  NO
```

v1 数据不得静默补跑、替换 seed 或改写 manifest。若继续搜索蒸馏，下一步应先冻结
v2 的完整组 infrastructure retry/coverage 语义，再使用新的 dataset ID；另一条可选
路径是停止神经分支，直接进入 clean publication rerun。

## 八、冻结 Artifact

目录：

```text
artifacts/flat_root_teacher_smoke_v1_8c7a0d4d
```

关键 SHA256：

```text
dataset ID / teacher_branches.jsonl:
  bc0a23318f6f6da0b96e796cd5371b69b377462ad7e715c182edc8c6eea4e0af

dataset_manifest.json:
  a360940895154b1925c3124ae78d1d4ae4e2bfaa638e0d9b38ecb4c5a522b88c

checksums.sha256:
  72929221e686e4621abf52ece6560e335aedf8aff85b647a651d17ffff2a14f6

data_gate.json:
  c2683380d7ff7da7ea0ff865365a3f93c972e98f36b0fad9a1d5a86dca3d5a6c

label_noise_audit.json:
  66cb22c1449f3a98442736a1cd129de834e4e116abb61202dbe0c61d341cbf02

power_audit.json:
  ad618da6c30a1e6883423da5b6b241d1a0f763819fe6ae209509443fa0582523
```

固定镜像只读复验：

```text
checked files:
  327

status:
  valid
```
