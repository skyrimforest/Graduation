# DecisionBackend 训练与模型发布设计草案

日期：2026-08-05

状态：已批准执行；Deadline 核心已实现，锁定 Gate 与联合 cohort 重跑待执行

## 执行记录

2026-08-05 已落地：

- `DecisionTransition`、`TrainingRecipe` 和 `ModelArtifactManifest` 严格契约；
- event decision audit 到完整 transition 的适配器，缺失 rollout provenance 时拒绝
  生成样本；
- 同 snapshot/counterfactual group/cluster 不跨 split 的冻结数据集；
- 权重、schema、recipe、dataset、split、calibration、evaluation 和 model card 的
  artifact hash 绑定；
- estimator/calibration/shadow/terminal promotion Gate 证据检查；
- 无网络、只读根文件系统的独立 Docker 契约入口；
- FJSP/MAPF 真实 runtime profile activator、same-snapshot FJSP/联合 branch
  runner 和 paired cluster-bootstrap Headroom 分析器；
- 训练契约聚焦 Docker 测试 10/10；加入多算法与联合 profile/Headroom 测试后，
  SkyCausal 全量 Docker 回归 131/131。

实现位置：

```text
codebase/SkyEngine/trainer/decision_backend/
codebase/SkyEngine/docker-compose.train.yaml
codebase/SkyEngine/test/skycausal/test_decision_training.py
```

尚未启动模型训练。MAPF、FJSP 单侧和 6-profile 联合 Headroom Gate 均已通过
开发 smoke。Deadline/Cancel/Fallback 核心现已实现；下一步在固定 commit/镜像上
通过完整 Infrastructure Gate，并用 v2 audit 重跑联合 cohort，再进入 bounded
MCTS Search Gate。正式训练和模型 promotion 仍需锁定 cohort、完整 transition
数据和相应 release gates。

## 一、核心结论

建议 `DecisionBackend` 保持纯在线推理接口，不能强制包含 `train()`：

```text
规则后端       不训练
MCTS 后端      不训练
神经网络后端   离线训练，在线只读加载 artifact
混合 MCTS      MCTS 本身不训练，policy/value 网络单独训练
```

因此系统应拆成两个正交生命周期：

```text
在线决策面
DecisionState + legal actions + budget
        -> DecisionBackend.decide()
        -> Decision

离线训练面
Decision logs / counterfactual rollouts / MCTS search logs
        -> DatasetBuilder
        -> BackendTrainer
        -> ModelArtifact
        -> validation / promotion
        -> NeuralDecisionBackend 只读加载
```

不在 `DecisionBackend` 基类增加 `fit()`、optimizer 或 replay buffer。这样规则、
MCTS、RL、BNN 和因果后端仍共享一个最小、稳定的在线接口。

## 二、MCTS 与训练的关系

### 2.1 纯 MCTS

纯 bounded MCTS 只需要：

- transition/snapshot/fork；
- tree policy；
- rollout policy；
- value backup；
- wall-clock/simulation budget。

它没有训练阶段，也不产出模型权重。每次决策都在当前状态上在线搜索。

墙钟 deadline 不直接截断并估值半条 rollout；simulation admission、root 最低配对
覆盖、solver 取消和 fallback 的完整规则见：

```text
20260805_严格Deadline与AnytimeMCTS设计方案.md
```

### 2.2 MCTS 可以成为教师

MCTS 可额外输出：

```text
root visit distribution
per-action Q / uncertainty
selected action
search depth
simulation count
solver/profile usage
```

这些日志可以离线训练：

- policy network：拟合 root visit distribution；
- value network：拟合 root Q 或 terminal cost-to-go；
- ranking network：拟合 action 相对顺序；
- BNN value：拟合 action residual 及后验不确定性。

此时训练的是神经网络，不是 MCTS。

### 2.3 Learned MCTS

当网络被用作 prior 或 leaf value 时，方法变为：

```text
policy/value network + PUCT/MCTS
```

推理时 MCTS 仍可独立运行；artifact 缺失、schema 不兼容或 OOD Gate 失败时，必须
回退到无网络的 MCTS 或规则后端。

## 三、推荐抽象

### 3.1 在线接口保持不变

```python
class DecisionBackend:
    def decide(
        self,
        decision_state,
        legal_actions,
        solver_portfolio,
        budget,
    ) -> Decision:
        ...
```

神经网络后端只增加构造期 artifact：

```python
class NeuralDecisionBackend(DecisionBackend):
    def __init__(self, artifact, fallback_backend):
        ...
```

运行时约束：

- `model.eval()`；
- `no_grad/inference_mode`；
- 不持有 optimizer；
- 不更新权重或 normalization；
- 不写 replay buffer；
- 所有 OOD、超时和 schema 错误走结构化 fallback。

### 3.2 离线训练接口

后续单独定义：

```python
class BackendTrainer:
    def fit(
        self,
        dataset,
        recipe,
        split_manifest,
    ) -> ModelArtifact:
        ...
```

`BackendTrainer` 不是 `DecisionBackend` 的父类，也不参与在线执行。

### 3.3 训练 Recipe

```text
model family / architecture
feature schema
action vocabulary
target definitions
losses
optimizer / scheduler
random seeds
data filters
split manifest
early stopping metric
calibration method
fallback policy
```

recipe 必须序列化并计算 hash，禁止只保存在命令行历史中。

## 四、统一训练数据契约

建议新增 `DecisionTransition`，至少包含：

```text
schema_version
decision_id
counterfactual_group_id
cluster_id
snapshot_hash

event_type
event_intensity
decision_state
feature_schema_hash

legal_action_ids
legal_action_mask
selected_action_id
selected_solver_profile

behavior_backend
behavior_config_hash
behavior_propensity

duration_steps
cumulative_cost
next_decision_state
terminal

terminal_makespan
terminal_twt
terminal_otd
terminal_nervousness
physical_invariants

planning_seed
execution_seed
code_commit
container_digest
input_artifact_hash
```

### 4.1 必须保留 legal action set

动作空间随事件、物理承诺和 solver 可用性变化。只保存 selected action 无法训练
masked policy，也无法判断模型是否选择了当时不存在的动作。

### 4.2 SMDP duration

等待、改派、局部重调度和 solver 调用持续时间不同，transition 必须保存：

```text
duration_steps
cumulative_cost_between_decisions
```

需要折扣时使用 `gamma ** duration_steps`。首轮 makespan 任务更建议直接训练
undiscounted cost-to-go 或 baseline-relative terminal improvement，避免人为折扣
改变工业目标。

### 4.3 行为概率

offline RL 和因果估计需要 `behavior_propensity`。确定性规则的概率为 0/1，通常
没有足够 overlap，不能仅靠历史固定策略日志识别所有动作效应。

优先数据来源是：

- 同一 snapshot 上对全部 legal actions 做物理 fork；
- 预注册随机化 treatment；
- MCTS 自身的探索/visit distribution。

## 五、训练标签设计

### 5.1 不直接拟合绝对 makespan

绝对 makespan 强烈受实例规模影响，容易再次学到规模代理。建议主标签为：

```text
advantage(s, a)
  = terminal_cost(reference_action)
  - terminal_cost(action_a)
```

reference 首选：

- 当前 best fixed backend；
- 事件对应的安全 baseline；
- wait-for-repair 等预注册动作。

正值表示动作优于 reference，与当前 Value Gate 的 improvement 方向一致。

### 5.2 多目标使用多头输出

首轮不把 makespan、TWT、OTD 和 nervousness 预先揉成一个手工加权 reward。
建议模型分别输出：

```text
delta_makespan
delta_twt
delta_otd
delta_nervousness
failure_probability
```

在线由 `ObjectiveAdapter` 根据实验预注册目标组合。这样更容易解释动作收益来源，
也不必因目标权重变化重新训练全部表示层。

### 5.3 MCTS 蒸馏标签

```text
policy target = normalized root visit counts
value target  = root/leaf backed-up cost
ranking target = per-action Q ordering
```

只蒸馏 selected action 会丢失 MCTS 对次优动作和不确定性的完整信息。

## 六、神经网络训练路线

### 6.1 第一阶段：确定性监督基线

先训练一个小型 masked action-value/ranking network：

```text
state + action/profile features -> predicted advantage
```

损失：

```text
Huber/MSE for advantage
+ pairwise ranking loss
+ optional sign classification loss
```

目标不是立即替代 MCTS，而是验证状态和标签是否存在可泛化信号。

Estimator Gate 沿用：

- pairwise sign accuracy >= 65%；
- rank correlation >= 0.30；
- 未见 FJSP family/topology/event 上方向稳定。

### 6.2 第二阶段：BNN 残差

在确定性基线有信号后，再训练：

```text
prediction = baseline_score + learned_residual
```

BNN 输出至少区分：

```text
posterior mean
epistemic uncertainty
aleatoric uncertainty（若标签噪声需要）
```

推荐首轮比较：

1. deterministic MLP；
2. deep ensemble；
3. MC dropout；
4. variational BNN。

不要因为名称更“贝叶斯”就直接采用最复杂 VI；先用 calibration 和 terminal value
决定。

BNN Gate：

- held-out NLL/CRPS；
- 50/80/95% interval coverage；
- ID/OOD uncertainty separation；
- uncertainty-aware fallback 改善 terminal Value Gate；
- 高不确定状态不比 fixed/MCTS fallback 更差。

### 6.3 第三阶段：MCTS policy/value 引导

只有在网络通过 estimator 和 calibration Gate 后，才作为：

- PUCT prior；
- leaf value；
- progressive widening 候选排序；
- expensive solver profile 的预筛器。

始终保留真实物理 rollout 对高价值 root actions 的校验。

### 6.4 第四阶段：Offline RL

只有满足以下条件才进入 IQL/CQL 等 offline RL：

- behavior coverage 足够；
- action mask 完整；
- duration/cumulative cost 正确；
- terminal outcome 完整；
- held-out simulator evaluation 可用。

首轮不推荐直接在线 PPO。在线 RL 样本昂贵、动作持续时间不同，而且当前 profile
Headroom 尚未证明，直接训练很可能只学习回退或实例规模。

### 6.5 因果训练单独处理

因果模型不是在 BNN loss 上再加一个正则项。它需要独立流程：

- treatment/propensity；
- cross-fitting nuisance models；
- overlap/balance；
- DR/AIPW 或同源反事实 effect target；
- cluster-aware uncertainty；
- sensitivity/placebo/negative control。

因果 effect 可以作为 `DecisionBackend` 的 action advantage 修正项，但必须单独
报告识别假设。

## 七、数据切分与防泄漏

禁止逐行随机切分。推荐 cluster：

```text
(FJSP family, instance, map topology, base seed, branch snapshot)
```

同一 snapshot 的不同动作必须位于同一 split。

至少维护：

```text
train
development
locked validation
cross-event OOD
cross-family OOD
cross-topology OOD
```

测试顺序：

1. leave-one-seed-out 只作开发诊断；
2. leave-one-instance/family-out 判断结构泛化；
3. unseen topology 判断 MAPF 泛化；
4. unseen event 判断统一后端是否成立；
5. locked terminal cohort 只运行一次。

训练数据可以使用模拟未来，但在线推理不得读取测试 episode 的 realized future。
`planning_seed` 与 `execution_seed` 必须不同并进入 manifest。

## 八、ModelArtifact 契约

不能只保存 `model.pt`。正式 artifact 目录建议为：

```text
model.pt
artifact.json
feature_schema.json
action_schema.json
normalization.json
training_recipe.json
dataset_manifest.json
split_manifest.json
calibration.json
evaluation.json
model_card.md
```

`artifact.json` 至少记录：

```text
artifact_schema_version
backend_family
model_architecture
weights_sha256
feature_schema_hash
action_schema_hash
training_recipe_hash
dataset_manifest_hash
code_commit
container_digest
random_seeds
fallback_backend_config
promotion_status
```

在线加载时 hash/schema 任一不匹配都拒绝模型并回退，不能自动补列、截断或改变
action 顺序。

## 九、模型发布 Gate

```text
candidate
  -> estimator_passed
  -> calibration_passed
  -> shadow_passed
  -> terminal_value_passed
  -> promoted
```

### 9.1 Data Gate

- schema/hash 完整；
- 无 terminal/未来特征泄漏；
- cluster split 无交叉；
- legal mask 与物理 eligibility 一致；
- counterfactual branches 完成且不变量通过。

### 9.2 Estimator Gate

- sign accuracy 和 rank correlation 过线；
- 相对 best fixed/MCTS teacher 有可解释增益；
- 不依赖 family/instance ID 捷径。

### 9.3 Calibration/OOD Gate

- BNN interval coverage；
- OOD uncertainty separation；
- fallback 触发率和错误拒绝率；
- 不确定性与真实误差正相关。

### 9.4 Shadow Gate

- 只记录不执行；
- 100% legal action；
- p50/p95 latency 满足 budget；
- 决策可复现；
- 与 fallback 的分歧 cohort 足够。

### 9.5 Terminal Value Gate

- completion 与物理不变量通过；
- mean improvement > 0；
- cluster-bootstrap 95% CI lower > 0；
- 未见 family/topology/event 方向稳定；
- 计入训练外在线推理成本。

## 十、现有 trainer/ 的复用边界

现有 `trainer/` 面向 AGV Assigner，而不是事件级 `DecisionBackend`。

可复用：

- Docker 内 PyTorch 环境；
- `TrainingLogger` 的 train/eval 通道；
- optimizer、checkpoint 和基础 CLI 模式；
- 部分模型与蒸馏 loss 实现经验。

不能直接复用：

1. observation/action 都是 AGV-task assignment，不符合 typed event action；
2. PPO/REINFORCE 按固定一步折扣，未建模 SMDP duration；
3. `Distiller` 当前逐行随机 80/20 切分，会造成同实例/同 snapshot 泄漏风险；
4. checkpoint 只保存权重、optimizer 和少量日志，没有 artifact/schema/data manifest；
5. GRPO 的 K 个 rollout 依次修改同一个 env/coordinator，未从同一 snapshot 恢复，
   当前不能用于可信反事实标签；
6. `docker_run_train.py` 为空，尚无独立、冻结的训练容器入口。

已新增：

```text
trainer/decision_backend/
```

该目录目前只包含训练契约、数据集、artifact 和 CLI。现有 Assigner trainer 的算法
行为未修改；`trainer/__init__.py` 改为惰性加载，避免纯契约工具被未锁定的 PyTorch
依赖阻断。

## 十一、Docker 复现方案

训练必须继续遵守宿主机零依赖：

```text
代码：read-only mount
冻结数据集：read-only mount
artifact 输出：read-write mount
训练镜像：固定 digest
```

建议新增独立 `compose.train.yaml`，不复用在线 engine command：

```text
decision-dataset-builder
decision-trainer
decision-evaluator
```

训练 manifest 必须记录镜像 digest、GPU/CPU 类型、CUDA/PyTorch 版本、seed、命令、
代码 commit 和输入数据 hash。

## 十二、推荐实施顺序

```text
0. Portfolio Headroom Gate
1. DecisionTransition + dataset manifest
2. 同源反事实 action table
3. 确定性 advantage/ranking baseline
4. BNN residual + calibration/OOD gate
5. MCTS policy/value distillation
6. learned PUCT/MCTS
7. Offline RL / causal correction
```

Headroom Gate 未通过时，不进入训练开发。网络不应被用来学习一个没有稳定动作价值
差异的 portfolio。当前开发 Gate 已通过，但现有预算仍是观测后审计；应先通过严格
Deadline Infrastructure Gate，再验证 bounded MCTS 能在等预算下缩小 oracle
regret，最后生成神经模型 teacher labels。

## 十三、审核结论

以下四点已按用户“开始执行”指令进入实施：

1. `DecisionBackend` 永久保持 inference-only，不增加 `train()`；
2. 首个神经网络方法选择“监督 advantage/ranking + BNN residual”，不直接 PPO；
3. 主标签使用相对安全 baseline 的多目标 advantage，不使用绝对 makespan；
4. 训练代码新建 `trainer/decision_backend/`，只复用现有 logger/Docker/PyTorch
   基础，不直接复用当前 Assigner rollout。

当前只实现数据集和 artifact 基础设施。Portfolio Headroom 不再是开发阻塞项；
Trainer、模型及实际训练任务继续等待 MCTS Search Gate 和锁定数据集。

## 十四、2026-08-05 Headroom 预实验结论

MAPF 单侧在 20 个独立 cluster、统一 200 ms 预算下比较 EECBS、LG-LaCAM 和
MAPF-LNS2：

```text
best fixed: LG-LaCAM
best fixed mean capped makespan: 284.15
oracle mean capped makespan: 269.20
oracle improvement: 14.95
cluster-bootstrap 95% CI: [8.65, 22.40]
non-best-fixed winner rate: 75%
strict winner profiles: 3
gate: passed
```

FJSP 使用同一事件 snapshot、同一初始计划、同一 execution/exogenous seed，通过
真实 `profile_activator` 比较 CP-SAT 预算：

```text
1 s vs 5 s:
  5/5 cluster 终态和 physical outcome hash 完全相同
  dynamic solve wall time: 约 11--22 ms
  oracle improvement: 0

10 ms vs 50 ms:
  10 ms: 5/5 无可行 artifact
  50 ms: 5/5 完成
  oracle improvement over best fixed: 0
```

随后补齐 DE/PSO 的动态残余问题契约，包括可变剩余工序数、job release time、
machine availability 和 stateless `/solve` artifact，并在统一 1000 ms 预算下进行
真实多算法比较：

```text
profiles: CP-SAT-1s, DE-extreme-g100, PSO-extreme-g100
valid clusters: 19（2 maps；另 1 cluster 因 clean baseline 未完成而整组排除）
best fixed: DE-extreme-g100
best fixed mean capped makespan: 530.21
oracle mean capped makespan: 505.47
oracle improvement: 24.74
cluster-bootstrap 95% CI: [12.53, 39.11]
non-best-fixed winner rate: 63.2%
strict winner profiles: 3
oracle completion rate: 100%
gate: passed
```

57 条 profile branch 均通过 immediate physical invariants；DE/PSO 完成率为
19/19，CP-SAT 为 17/19。最大动态求解耗时分别约为 DE 402 ms、PSO 136 ms、
CP-SAT 29 ms，均未超过注册的 1000 ms 预算。

因此当前证据支持“FJSP 和 MAPF 两侧都存在 solver selection 价值”。但两组单侧
实验不能替代联合 profile 实验，因此又在无 loaded transport 的安全 snapshot
边界比较 6 个联合 profiles：

```text
profiles:
  CP-SAT+EECBS, CP-SAT+LG-LaCAM
  DE+EECBS, DE+LG-LaCAM
  PSO+LG-LaCAM, PSO+MAPF-LNS2
budgets: FJSP 1000 ms; MAPF 500 ms
clusters: 20（2 maps × seeds 100--109）
best fixed: CP-SAT+EECBS
best fixed mean capped makespan: 461.60
oracle mean capped makespan: 442.30
oracle improvement: 19.30
cluster-bootstrap 95% CI: [9.30, 30.85]
non-best-fixed winner rate: 65%
strict winner FJSP algorithms: CP-SAT, DE, PSO
strict winner MAPF algorithms: EECBS, LG-LaCAM, MAPF-LNS2
completion: 120/120 branches
gate: passed
```

120 条联合 branch 均无错误和 physical invariant 失败，并通过 snapshot、初始计划、
exogenous seed 和预算一致性审计。早期 200 ms 联合诊断虽然统计 Headroom 为正，
但两条 EECBS 分支实际使用约 443--447 ms，故未放行；最终 cohort 预先统一为
500 ms MAPF 预算后重新执行，没有混用旧行。

所以开发 Portfolio Headroom Gate 已通过。solver 强制取消和 fallback 核心已实现，
但完整 Deadline Infrastructure Gate 与 v2 联合 cohort 尚未锁定；通过后才进入
bounded MCTS Search Gate。由于原 manifest 仍标记 `git.dirty=true` 且缺少 v2
deadline audit，该结果不能直接作为锁定论文证据，也不自动授权神经模型 promotion。

结果与协议：

```text
codebase/SkyEngine/experiment/skycausal/results/
  portfolio_headroom_smoke_20260805/README.md
```
