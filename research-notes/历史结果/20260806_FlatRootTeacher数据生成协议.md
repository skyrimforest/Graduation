# Flat Root Teacher 数据生成协议 v1

起草日期：2026-08-05

状态：v1 smoke 已执行并冻结；总体 Gate 失败，禁止神经训练

本次数据生成绑定的是 artifact 内不可变协议副本：

```text
artifacts/flat_root_teacher_smoke_v1_8c7a0d4d/protocol.md
SHA256:
8c7a0d4d870ee7fcd9ddc2f7973e5eb4f4e0fcfb0482e6abee3c12734f8b1363
```

本文后续更新只记录执行结果，不静默改变上述生成协议。

## 一、目标与边界

本协议冻结 SkyCausal 第一版 Teacher 数据的生成语义。Teacher 只使用已经通过
20-cluster development Search Value Gate 的：

```text
Stratified Root Monte Carlo
+ terminal rollout
+ k=1 complete paired stratum
```

本阶段目标是生成可审计、可重放、可版本化派生标签的全动作反事实数据，不是训练
MCTS，也不是启动 Policy、Value、BNN、PPO、GRPO、offline RL 或因果模型。

本协议不改变已经完成的论文 evaluation protocol。以下 20 个 development/evaluation
clusters 永久禁止进入 Teacher 训练数据：

```text
maze:
  110, 111, 112, 113, 115, 116, 117, 118, 119, 120, 121

maze-b:
  110, 111, 113, 114, 115, 116, 117, 118, 120
```

Open-loop UCT 当前 Value Gate 失败，其日志不能作为 Teacher v1 标签来源。

## 二、协议标识与冻结项

协议逻辑标识：

```text
skycausal.flat-root-teacher-protocol.v1
```

以下任一项变化都必须提升协议版本，旧数据不得静默重写：

```text
teacher backend
action vocabulary 或顺序
legal-action 语义
状态原始 schema
模型特征投影
snapshot/cluster 定义
planning/execution seed 规则
rollout horizon
terminal cost
完整 stratum 提交规则
fallback
cohort 与排除规则
split 规则
label recipe
provenance schema
Data/Neural Gate
```

协议批准后应将本文规范化内容计算 SHA256，并写入每条原始记录和 dataset manifest。

## 三、Teacher 执行语义

### 3.1 固定后端

```text
backend:
  stratified_root_monte_carlo

root mode:
  parallel complete paired stratum

k:
  1

horizon:
  terminal

minimum paired rounds:
  1

simulation limit:
  6

fallback:
  CP-SAT+LG-LaCAM
```

同一 `counterfactual_group_id` 必须满足：

```text
同一 immutable snapshot
+ 同一 decision state
+ 同一 planning seed
+ 同一 solver seed policy
+ 同一 action vocabulary/legal mask
+ 6 个 action 各完成一次 terminal rollout
```

只有 6 个 action 全部在 hard deadline 内完成并通过审计，整个 stratum 才能原子
提交。任一 action 为 `cancelled`、`hard_deadline`、`failed`、late completion 或
horizon incomplete 时，整组不得进入 Teacher dataset。

禁止：

```text
保存已完成的局部分支并补齐缺失 action
给失败 action 填充惩罚 cost
更换单个 action 的 seed 重跑
按并发完成顺序改变 action 顺序
使用 incomplete stratum 派生 winner/Q/value
```

### 3.2 固定运行参数

Teacher v1 smoke 固定：

```text
family:
  j10

FJSP instance:
  /dataset/fjsp/J10P5M6.json

MAPF:
  maze   -> medium-mazes-seed-0000@/dataset/mapf/medium_maps.yaml
  maze-b -> medium-mazes-seed-0001@/dataset/mapf/medium_maps.yaml

event:
  machine_breakdown

severity:
  high

processing-time preset:
  moderate_variance

num_agv:
  4

episode cap:
  1000

due factor:
  1.1

safe switch boundary:
  no_loaded_transport
```

搜索预算沿用已经完成真实运行验证的配置。`per-simulation hard cap` 是 admission
上界，不等于预期真实耗时；wall budget 必须额外容纳 reserve 和 cancellation
grace：

```text
search wall budget:
  12000 ms

per-simulation hard cap:
  10000 ms

commit reserve:
  100 ms

cancellation grace:
  100 ms

worker termination grace:
  50 ms
```

若该 12 秒 wall 配置不能完成完整 root coverage，则执行 fixed fallback，但该次
运行只写入 `rejected_groups.jsonl`，不得进入 Teacher branch 表。

## 四、Action Schema v1

动作词表和顺序固定为：

```text
0  CP-SAT+EECBS
1  CP-SAT+LG-LaCAM
2  DE+EECBS
3  DE+LG-LaCAM
4  PSO+LG-LaCAM
5  PSO+MAPF-LNS2
```

Teacher v1 只接收六个 profile 全部合法的安全切换状态：

```text
legal_action_ids:
  与 action vocabulary 完全相同

legal_action_mask:
  [true, true, true, true, true, true]
```

如果任一 profile 在 snapshot 上不合法或不可用，整个 group 标记为
`ineligible_action_space`，不得缩小词表后继续生成。

需要严格区分：

```text
Teacher/fixed fallback:
  CP-SAT+LG-LaCAM

development evaluation best fixed:
  CP-SAT+EECBS
```

二者都会进入派生标签，但不能互相替代。

## 五、State 与 Feature Schema v1

### 5.1 不可变原始状态

原始记录必须保存完整的 `DecisionState`，至少包括：

```text
event_type
features.type
features.branch_step
features.earliest_allowed_step
features.machine_id
features.current_operation
features.current_operation_on_critical_path
features.affected_operations
features.alternative_operations
features.frozen_operations
features.planned_on_failed_machine
features.repair_scope
features.safe_switch_loaded_transport_count
context.family
context.topology
context.state_seed
context.snapshot_hash
context.snapshot_artifact_sha256
```

还必须补充静态 instance descriptors：

```text
num_jobs
num_machines
num_agv
total_operation_count
episode_cap
```

原始状态以 canonical JSON 计算 `state_payload_hash`。同一反事实组的 6 条 branch
记录必须具有相同 hash。

### 5.2 初始模型特征投影

原始状态和模型特征分层保存。Teacher raw data 不因模型变化而重写；模型只能通过
有版本号的 feature recipe 派生输入。

`flat-root-features.v1` 固定包含：

```text
categorical:
  event_type
  topology

boolean:
  current_operation_on_critical_path

size/context:
  num_jobs
  num_machines
  num_agv
  total_operation_count

progress:
  branch_step
  branch_progress = branch_step / episode_cap
  decision_wait_steps = branch_step - earliest_allowed_step
  decision_wait_ratio = decision_wait_steps / episode_cap

scope:
  affected_operation_count
  affected_operation_ratio
  alternative_operation_count
  alternative_operation_ratio
  frozen_operation_count
  frozen_operation_ratio
  planned_failed_machine_count
  planned_failed_machine_ratio
  repair_scope_count
  repair_scope_ratio

transport:
  safe_switch_loaded_transport_count
  safe_switch_loaded_transport_ratio
```

operation ratio 的分母为 `total_operation_count`，transport ratio 的分母为
`num_agv`。分母必须为正，否则拒绝样本。

以下字段只用于 provenance、分组和诊断，不得进入 v1 模型输入：

```text
state_seed
planning_seed
execution_seed
snapshot_hash
snapshot_artifact_sha256
current job/operation ID
machine ID
source file path
request ID
process PID
wall-clock timestamp
terminal outcome
selected action
```

这样保留完整状态，同时避免模型直接记忆 seed、snapshot、job、operation 或 machine
身份。

## 六、Training-only Smoke Cohort

### 6.1 候选集合

v1 smoke 只使用以下预注册候选，不得看结果后追加其他 seed：

```text
maze:
  state seeds 130--149

maze-b:
  state seeds 130--149
```

每个 topology 按 state seed 升序捕获 snapshot，取前 10 个通过资格检查的 cluster，
目标最多 20 个 training-only clusters。若任一 topology 不足 10 个有效 cluster，
smoke Gate 失败；不得用 evaluation seed 或候选集合外 seed 补齐。

资格检查只允许使用 action-independent 条件：

```text
clean baseline terminal completed
machine-breakdown target 存在
snapshot 可序列化并可重放
loaded transport count = 0
六个 profile 在该状态全部 legal
initial physical invariant audit 通过
```

不得按某个 action 的 cost、winner 或相对效果决定 cluster 是否进入 cohort。

### 6.2 Cluster 定义

```text
cluster_id = SHA256(
  family
  + FJSP input SHA256
  + topology
  + MAPF input SHA256
  + state_seed
  + snapshot_artifact_sha256
)
```

同一 snapshot 只属于一个 cluster；snapshot 的所有 planning/execution branches
必须位于同一 split。

## 七、Seed Policy v1

固定 topology code：

```text
maze   = 1
maze-b = 2
```

对每个 cluster：

```text
seed_offset =
  topology_code * 10000 + state_seed

solver_seed =
  state_seed

teacher_planning_seed =
  2000000 + seed_offset

heldout_execution_seed =
  3000000 + seed_offset
```

例如：

```text
maze/state_seed=130:
  solver_seed = 130
  teacher_planning_seed = 2010130
  heldout_execution_seed = 3010130

maze-b/state_seed=130:
  solver_seed = 130
  teacher_planning_seed = 2020130
  heldout_execution_seed = 3020130
```

同一组 6 个 action 共享 planning seed，满足 Common Random Numbers。planning seed
生成 Teacher labels；execution seed 只用于独立 held-out label-noise/value audit，
不得进入训练标签。

Smoke 阶段每个 cluster 执行两组完整六分支 rollout：

```text
teacher_planning:
  可进入训练原始表

heldout_execution:
  只进入 audit 表，不进入模型 fit
```

不得把 `heldout_execution_seed` 填入由 planning rollout 派生的 terminal outcome，
也不得用同一个 `DecisionTransition.execution_seed` 字段混淆两种 seed 角色。代码
实现前必须扩展契约，显式区分：

```text
rollout_seed
seed_role
reserved_execution_seed
```

## 八、Raw Paired-cost Schema v1

### 8.1 分层原则

Teacher 原始事实不是“Root MC 选中了哪个 action”，而是同一 snapshot 上六个 action
的完整 terminal costs。原始表一行对应：

```text
counterfactual_group_id + action_id + seed_role
```

原始 schema：

```text
skycausal.flat-root-teacher-branch.v1
```

`DecisionTransition` 是后续派生产物，不能替代原始 paired-cost 表。

### 8.2 必填字段

身份与分组：

```text
schema_version
protocol_version
protocol_sha256
record_id
counterfactual_group_id
cluster_id
seed_role
state_seed
rollout_seed
reserved_execution_seed
solver_seed
```

状态：

```text
snapshot_hash
snapshot_artifact_sha256
state_payload
state_payload_hash
feature_schema_version
feature_schema_sha256
model_features
model_features_hash
event_type
```

动作：

```text
action_schema_version
action_schema_sha256
action_vocabulary
legal_action_ids
legal_action_mask
action_id
action_rank
fjsp_algorithm
mapf_algorithm
profile_config_hash
```

结果：

```text
status
horizon_type
horizon_completed
terminal_done
terminal_raw_makespan
terminal_capped_makespan
episode_cap
rollout_step_count
physical_outcome_hash
fjsp_fallback_used
mapf_fallback_count
```

Deadline 与物理审计：

```text
accepted_for_atomic_commit
late_completed
process_deadline_audit
fjsp_deadline_audit
mapf_deadline_audits_hash
physical_invariants
failed_physical_invariants
```

Provenance：

```text
skyengine_commit
mapf_commit
fjsp_commit
skyengine_image_digest
mapf_image_digest
fjsp_image_digest
profile_config_sha256
snapshot_source_sha256
fjsp_input_sha256
mapf_input_sha256
source_run_sha256
source_manifest_sha256
```

所有 hash 均为 64 位小写 SHA256；container digest 使用完整 `sha256:` 前缀。

### 8.3 Group summary

`teacher_groups.jsonl` 由 branch 表确定性派生，每组至少包含：

```text
counterfactual_group_id
cluster_id
seed_role
ordered_action_costs
optimal_action_ids
teacher_selected_action_id
fallback_action_id
best_fixed_action_id
top2_margin
group_branch_hashes
group_hash
```

`teacher_selected_action_id` 使用固定 action order 对最小 cost 做 deterministic
tie-break，必须与在线 Root MC 当前实现一致。`optimal_action_ids` 同时保存全部并列
最优 action，避免后续模型把任意 tie-break 当成强偏好。

## 九、Terminal Cost 与 Label Recipe v1

### 9.1 Cost

主 cost：

```text
terminal_capped_makespan =
  terminal_raw_makespan,  terminal_done = true
  1000,                   terminal_done = false
```

Teacher v1 只接受 terminal horizon。episode cap 是合法的 capped terminal outcome，
但不能伪装为完成。

每组 cost 必须为有限非负数。当前离散时间环境要求 cost 为整数值；JSON 中可表示为
`571.0`，但不得出现非整数时间步。

### 9.2 确定性标签

对 action `a`，令：

```text
c(a) = terminal_capped_makespan
c* = min_a c(a)
c_fallback = c(CP-SAT+LG-LaCAM)
c_best_fixed = c(CP-SAT+EECBS)
```

派生：

```text
value_target(a):
  c(a)

normalized_value_target(a):
  c(a) / 1000

oracle_regret(a):
  c(a) - c*

safe_baseline_advantage(a):
  c_fallback - c(a)

best_fixed_advantage(a):
  c_best_fixed - c(a)
```

`advantage` 统一采用“正值表示 action 更好”；`oracle_regret` 统一采用“越小越好”。
禁止只写无方向说明的 `advantage` 字段。

### 9.3 Policy 与 ranking 标签

```text
hard_policy_target:
  对 teacher_selected_action_id 为 1，其余为 0

tie_aware_policy_target:
  在 optimal_action_ids 上均匀分布

soft_policy_target_tau10:
  exp(-(c(a) - c*) / 10.0)
  再在 legal actions 上归一化

pairwise_target(a_i, a_j):
  sign(c(a_j) - c(a_i))
```

`pairwise_target > 0` 表示 `a_i` 优于 `a_j`。cost 完全相同时 pairwise target 为 0，
训练 pairwise loss 时不强迫排序。

原始 paired costs 一旦冻结，不因后续模型、loss 或 temperature 选择变化而重写。
新增标签只能创建新的 label recipe 和派生 artifact。

## 十、Dataset 目录与 Manifest

冻结数据集目录至少包含：

```text
raw_runs/
snapshots/
teacher_branches.jsonl
heldout_audit_branches.jsonl
teacher_groups.jsonl
heldout_audit_groups.jsonl
rejected_groups.jsonl
feature_schema.json
action_schema.json
label_recipe.json
cohort_manifest.json
split_manifest.json
provenance.json
dataset_manifest.json
checksums.sha256
```

所有 JSON/JSONL 使用：

```text
UTF-8
finite JSON
key 排序
无 NaN/Infinity
JSONL 无空行
文件末尾换行
```

目录不可覆盖。任何内容变化都生成新的 dataset ID：

```text
dataset_id = SHA256(teacher_branches.jsonl)
```

`dataset_manifest.json` 必须绑定所有文件 hash、协议 hash、feature/action/label schema
hash、source artifact hash 和三仓 commit/image provenance。

## 十一、Split Policy v1

禁止逐行随机切分。单位必须是 `cluster_id`，并同时约束：

```text
counterfactual_group_id 不跨 split
snapshot_hash 不跨 split
state_seed 不跨 split
teacher/heldout audit seed role 不跨 split
```

Smoke 使用现有 `cluster_hash_v1`：

```text
split seed:
  20260806

ratios:
  train             0.70
  development       0.15
  locked_validation 0.15
```

`heldout_execution` 分支只用于同 split 内的 audit，不参与任何 split 的模型 fit。

正式数据扩展后另行预注册：

```text
cross_event_ood
cross_family_ood
cross_topology_ood
```

当前两个 topology 的 smoke 不能宣称完成 cross-topology OOD 验证。

## 十二、Provenance Gate

生成 smoke 数据前必须同时满足：

```text
SkyEngine worktree clean
SkyEngine-MAPF worktree clean
SkyEngine-FJSP worktree clean
三仓 commit 已记录
镜像由对应 clean commit 重建
profile config 直接保存最终 image digests
runner 禁止使用 image-digest override
run manifest 的 image 字段非 null
snapshot/input/profile config 全部有 SHA256
JSON/protocol/artifact 已进入 Git 或不可变对象存储
```

2026-08-05 provenance 固定结果：

```text
SkyEngine HEAD:
  38af10d3c6cb1b0422719bc42a4141fda53af3d8

SkyEngine-MAPF HEAD:
  68bf40005dcf479442043f07d08648149cc8913e

SkyEngine-FJSP HEAD:
  1edcf14535d97e0f04d535f34aee81c3d944f6bc

状态:
  三仓 worktree clean
```

由上述 clean commits 重建并验证的镜像：

```text
SkyEngine:
  sha256:873e7c932732fc9248df0b39323e29ae1a1f280986f23eb84bfb742665b9249a

MAPF classical:
  sha256:35a1600badd25ec60dd592819afc692ece3b6259c22dc1de417c308c51ae5c24

CP-SAT:
  sha256:6c48ca1271d391831fae0b8fe8c62f997608bc689d34c01ca37796ee35574550

DE:
  sha256:c47348edbdd173a0c84c7a4d4bbec9309fdc293be3d3402e23b3a5b8c4c33624

PSO:
  sha256:86d5a92ccf76f28fbe51e7f2c45acf2a3f75ebdca15be6c2c23ef8980763daf5
```

固定 profile：

```text
path:
  experiment/skycausal/protocols/joint_profiles_deadline_v2.json

SHA256:
  b6e35b5281d7a1bce0c83500e5f41ab3206489fb17ddf08d1b6684e41f4422ce

状态:
  已进入 SkyEngine Git
  直接保存四个 solver image digest
  Root MC CLI 已移除 image digest override
```

SkyEngine 镜像内置源码、完整 commit 和 OCI revision。无 `.git` 的容器运行时，
manifest 从 `SKYENGINE_CODE_COMMIT` 恢复 `dirty=false` 的镜像 commit。Root MC
还会在启动前强制校验：

```text
SKYENGINE_IMAGE_DIGEST
FJSP_IMAGE_DIGEST
MAPF_IMAGE_DIGEST
FJSP_CODE_COMMIT
MAPF_CODE_COMMIT
```

顶层 `FJSP_IMAGE_DIGEST` 记录 fixed fallback 的 CP-SAT 镜像；每条 Teacher branch
仍从 profile config 记录该 action 的 CP-SAT、DE 或 PSO 精确 digest。

结论：生成 training-only smoke 的 Provenance Gate 已通过。该结论不批准神经训练，
也不把既有 dirty development artifacts 重标为 publication evidence。

## 十三、Data Gate

每个进入 `teacher_branches.jsonl` 的 group 必须全部通过：

```text
branch count = 6
action set 与 Action Schema v1 完全一致
action order 可确定性恢复
legal mask 全 true
同组 state/snapshot/cluster/planning seed 完全一致
6 个 action 均 status=completed
6 个 action 均 horizon=terminal 且 completed=true
6 个 action 均 accepted_for_atomic_commit=true
late completion count = 0
partial backup count = 0
physical invariant pass rate = 100%
deadline audit coverage = 100%
source run gate_passed = true
teacher selected action = 固定顺序 argmin(cost)
profile/image provenance 完整
source artifact hash 可重算
不属于禁止训练的 20-cluster cohort
```

Dataset 级 Gate：

```text
有效 training-only cluster count >= 10
目标 smoke cluster count = 20
snapshot/cluster/group split leakage count = 0
duplicate record ID count = 0
duplicate action branch count = 0
future/terminal feature leakage count = 0
dataset replay hash match rate = 100%
```

任一 group 失败时整组进入 `rejected_groups.jsonl`，保留拒绝原因和 source hash，但不
产生任何训练标签。

## 十四、Label-noise 与 Power Audit

Smoke 的 `heldout_execution` 六分支只用于审计：

```text
planning/heldout tie-aware winner overlap
planning/heldout deterministic winner agreement
六 action rank Spearman
非 tie action-pair sign agreement
planning winner 的 heldout oracle regret
planning winner 相对 heldout best fixed 的 improvement
planning top-2 margin 分布
各 action cost 方差
内部 fallback 发生率
episode-cap 发生率
```

最低信号检查：

```text
tie-aware winner overlap >= 60%
非 tie pairwise sign agreement >= 65%
mean rank Spearman >= 0.30
planning winner 的 heldout mean improvement vs best fixed > 0
```

所有指标按 cluster bootstrap 给出 95% CI。若最低信号检查失败，不启动训练；先
审查 state schema、Teacher k=1 噪声和 cohort eligibility，不允许直接用神经网络
吸收不稳定标签。

正式训练规模不预先拍定。使用 smoke 的 cluster-level margin、winner disagreement
和 heldout regret 分布进行 bootstrap power simulation，要求：

```text
two-sided alpha = 0.05
target power >= 0.80
split 单位 = cluster
至少预留 15% locked validation
```

power audit 输出建议规模及其 CI 后，才能冻结正式 training-only cohort。预期规模为
数百个独立 clusters，但该预期不是样本量结论。

## 十五、DecisionTransition 映射边界

现有 `DecisionTransition` 可以承载部分 branch 信息，但当前不能直接作为 Teacher
原始 schema，原因包括：

```text
只禁止同组重复 action，未强制每组恰好 6 actions
decision_transition_from_audit() 只接收 applied online decision
单个 code_commit/container_digest 不能表达三仓和多镜像 provenance
planning_seed/execution_seed 无法表达 seed role
当前 simulation row 未保存 rollout_step_count
behavior_propensity 不适用于穷举反事实 branch
完整 terminal physical invariant audit 未进入 compact row
```

审核通过后的代码阶段应新增严格适配器：

```text
Root MC run artifact
  -> FlatRootTeacherBranch
  -> complete group validator
  -> versioned DecisionTransition derivative
```

映射时：

```text
selected_action_id:
  当前 branch 的 action，不是 Teacher winner

behavior_backend:
  stratified_root_monte_carlo.teacher_branch

behavior_propensity:
  null；不得伪造为 1/6

terminal_makespan:
  当前 branch 的 terminal capped makespan
```

必须先补齐 `rollout_step_count` 和 seed-role 契约，不得从 makespan 或 wall time猜测
`duration_steps`。

## 十六、Neural/BNN Gate

Teacher dataset 通过不等于模型可发布。

### 16.1 Deterministic Ranking/Value Gate

```text
legal action rate = 100%
cluster-held-out pairwise sign accuracy >= 65%
cluster-held-out rank correlation >= 0.30
相对 best fixed 的 heldout terminal mean improvement > 0
cluster-bootstrap 95% CI lower > 0
相对 Teacher 的 imitation regret 单独报告
无 future、seed、snapshot 或 ID shortcut
CPU 容器 p99 单次推理延迟 <= 50 ms
artifact/hash/replay Gate = 100%
```

### 16.2 BNN/Uncertainty Gate

确定性基线先通过，才允许训练 BNN residual、deep ensemble、MC dropout 或
variational BNN。至少报告：

```text
heldout NLL/CRPS
50/80/95% interval coverage
ID/OOD uncertainty separation
uncertainty 与绝对误差的相关性
fallback 触发率
错误接受率与错误拒绝率
```

### 16.3 Fallback 与 Terminal Gate

```text
高不确定样本 deterministic fallback = 100%
schema/hash/OOD/timeout 错误 deterministic fallback = 100%
fallback 后 physical invariant pass rate = 100%
相对 best fixed 的 terminal completion 不退化
相对 best fixed 的 mean improvement > 0
cluster-bootstrap 95% CI lower > 0
在线延迟计入完整 feature extraction 和 artifact loading policy
```

只有独立 locked test cohort 同时通过质量、延迟、uncertainty、fallback 和 artifact
Gate，神经后端才可进入 promotion。否则继续使用 flat Root MC k=1。

## 十七、当前 Artifact 审计

2026-08-05 只读复核结果：

```text
Root 20-cluster held-out:
  563c6632369e385ddfc5004ed0dad6304955b442fd85b23f4697c78a3c105f60

Budget curve:
  4a7e65b4eeb206ff859fa10866678f6ed3fbee641fba4c73936f0d198061553d

Forced timeout:
  89f8d63343b23ef020384241c18ea6cc632396b4495b2b4a5d417925edbf1501

UCT negative result:
  92a151f1f3918a274f56e1982573afb3d3dd9d264c3b11e2851711d6fc400c22

结论:
  四个 SHA256 全部与交接文档一致
```

这四个 JSON 仍是 dirty development evidence，保持本地隔离且不得改写 provenance。
固定 profile 与 Teacher schemas 已进入 Git；后续 smoke 的 run、manifest、snapshot
和 dataset artifacts 必须写入不可变目录或对象存储，不能只依赖工作区文件。

## 十八、审核后实施 Checklist

### A. 固定工程状态

- [x] 分仓审计并提交 Deadline、Root MC、UCT 和训练底座改动
- [x] 从 clean commit 重建 SkyEngine、MAPF、FJSP 镜像
- [x] 更新 `joint_profiles_deadline_v2.json` 的全部 solver digest
- [x] 移除 Teacher Root MC 命令中的 image digest override
- [x] 缺少 image digest/source commit 时 Root MC 启动即失败
- [x] profile config 与 Teacher schemas 进入版本控制
- [x] 通过 SkyEngine 190/190、MAPF 16/16、FJSP 6/6 回归

### B. 实现 Teacher 契约

- [x] 新增 `FlatRootTeacherBranch` 严格 schema
- [x] 新增完整六 action group validator
- [x] 强制 action order，不使用并发完成顺序
- [x] 补充 `rollout_step_count`
- [x] 补充完整 terminal physical invariant audit
- [x] 扩展三仓 commit 与多镜像 provenance
- [x] 显式区分 `rollout_seed`、`seed_role`、`reserved_execution_seed`
- [x] 新增 raw branch 到 `DecisionTransition` 的版本化适配器
- [x] 增加 incomplete group、重复 action、seed 泄漏和 split 泄漏测试

### C. 生成 Smoke

- [x] 只使用 maze/maze-b 的 state seeds 130--149
- [x] 每个 topology 取前 10 个 action-independent eligible clusters
- [ ] 每个 cluster 生成 planning 与 heldout execution 两个完整六分支组：19/20
- [x] 运行 Data Gate：planning 20/20 通过，paired coverage 失败
- [x] 运行 label-noise audit：19 个完整 pair 的最低信号检查通过
- [x] 运行 cluster-level primary-effect power audit
- [x] 冻结 dataset manifest、327 个文件 checksum 和全部 SHA256

### D. 决策点

- [x] Smoke 总体 Gate 失败，停止训练
- [ ] 若继续蒸馏，先冻结 v2 完整组 infrastructure retry/coverage 语义
- [ ] 若通过，先训练 deterministic ranking/value baseline
- [ ] deterministic baseline 通过后才进入 BNN residual
- [x] 神经后端未通过 locked Terminal Gate 时继续使用 flat Root MC k=1

## 十九、审核结论栏

当前建议：

```text
Teacher backend:
  批准 Stratified Root MC terminal k=1

Teacher schema/adapter:
  已实现并通过 Docker 契约测试

training-only smoke:
  已执行并冻结

training Data Gate:
  通过，20 groups / 120 branches

paired audit coverage Gate:
  失败，19/20 heldout groups

模型训练:
  禁止

总体 smoke Gate:
  失败
```

详细结果见：

```text
20260805_FlatRootTeacherSmoke审核报告.md
```

不得重跑单个 action、补入 seed 141 或改写 v1 manifest。若继续蒸馏，先定义并冻结
v2 的完整组 infrastructure retry/coverage 规则；否则转入 clean publication rerun。
