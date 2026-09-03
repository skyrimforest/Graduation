# SkyCausal MCTS 阶段进展与新窗口交接

更新时间：2026-08-05

## 一、文档用途

本文是新窗口继续演进时的入口文档，目标是让后续工作不依赖聊天上下文。

详细设计与逐次实验记录仍以：

```text
20260805_严格Deadline与AnytimeMCTS设计方案.md
```

为主。本文只保留当前有效结论、代码与 artifact 索引、风险边界和下一步执行顺序。

### 2026-08-05 续作状态

已完成新窗口只读审计并起草：

```text
20260806_FlatRootTeacher数据生成协议.md
```

协议已明确 raw paired-cost schema、training-only cohort、seed role、cluster-safe
split、label recipe、Data Gate 和 Neural/BNN Gate，并已完成 Teacher 契约代码：

```text
trainer/decision_backend/flat_root_teacher.py
trainer/decision_backend/schemas/flat_root_action_schema_v1.json
trainer/decision_backend/schemas/flat_root_feature_schema_v1.json
test/skycausal/test_flat_root_teacher.py
```

已实现完整六分支原子校验、Root MC artifact adapter、版本化 label/group summary、
DecisionTransition 派生、不可变目录写入与复验 CLI。源 runner 已补充
`rollout_step_count`、raw makespan 和 terminal physical invariants；run manifest
新增 MAPF/FJSP source commit。

最新 Docker 回归：

```text
DecisionBackend contracts:
  22/22 passed

SkyEngine SkyCausal:
  190/190 passed

SkyEngine-MAPF deadline/session:
  16/16 passed

SkyEngine-FJSP deadline/dynamic artifacts:
  6/6 passed

Fixed-image endpoint smoke:
  CP-SAT / DE / PSO all passed
```

Teacher v1 smoke 已生成并冻结，神经模型仍未训练：

```text
planning groups:
  20/20

heldout groups:
  19/20

training Data Gate:
  passed

paired audit coverage Gate:
  failed

overall smoke Gate:
  failed

model training approved:
  no
```

Teacher v2 完整组 retry 已实现、生成和冻结，总体 Gate 仍失败：

```text
attempt bundles:
  40/40

first-attempt success:
  38/40

legal full-group retry:
  1

second-attempt success:
  0/1

planning / heldout groups:
  19/20 / 19/20

overall smoke Gate:
  failed

model training approved:
  no
```

Provenance 固定已完成：

```text
三仓 worktree clean，commit 已记录；
MAPF、CP-SAT、DE、PSO 均从 clean commit 重建并固定 digest；
joint_profiles_deadline_v2.json 已写入最终 digest 并进入 Git；
Root MC 已移除 image digest override；
缺少 image digest/source commit 时 Root MC 启动即失败；
SkyEngine 镜像已内置源码与 commit，manifest 无 .git 时仍可审计；
dirty development results 保持本地隔离，不进入正式提交。
```

因此 Step 1--5 已执行。v2 证明完整组 retry 不能恢复 `maze/140`：planning 因
MAPF deadline-accounting Gate 被 nonretryable rejection，heldout 的 `DE+EECBS`
连续两次命中 10 秒 hard deadline。不得追加 attempt、补跑单 action、跨 attempt
拼接或回填 seed 141；停止 neural Teacher 分支，优先进入 clean publication rerun。

## 二、快速恢复上下文

工作区：

```text
/Users/bytedance/project/learn/flex_manufacture
```

论文研究目录：

```text
/Users/bytedance/project/learn/flex_manufacture/
260601天工论文准备/research
```

三个代码仓库：

```text
SkyEngine:
  260601天工论文准备/codebase/SkyEngine

SkyEngine-MAPF:
  260601天工论文准备/codebase/SkyEngine-MAPF

SkyEngine-FJSP:
  260601天工论文准备/codebase/SkyEngine-FJSP
```

当前一句话状态：

```text
严格 deadline、solver portfolio 和 Stratified Root MC 已完成 development Gate；
Open-loop UCT 已真实实现但 Value Gate 失败；
flat Root MC k=1 Teacher 协议、三仓 commit 和不可变镜像均已固定；
Teacher v1 smoke 因 paired coverage=19/20 未通过总体 Gate；
Teacher v2 完整组 retry 后仍只有 19/20 paired coverage；
继续使用 flat Root MC k=1，不启动神经训练，转入 publication rerun。
```

## 三、论文问题与当前定位

当前研究对象是动态 FJSP-AGV 中的事件触发在线恢复决策。MCTS/Root MC 的定位不是
替代 CP-SAT、DE、PSO、EECBS、LG-LaCAM 或 MAPF-LNS2，而是作为
Solver-Portfolio Controller，在事件发生后选择联合 FJSP-MAPF profile。

当前论文论证链：

```text
RQ1  不同 solver profile 是否存在互补性？
     -> Joint Portfolio Headroom Gate 已通过。

RQ2  严格 deadline 下的在线物理搜索是否优于固定 profile？
     -> Stratified Root MC k=1 development Gate 已通过。

RQ3  更深的 Open-loop UCT 是否优于 flat Root？
     -> 当前 20 s two-event 协议下 Gate 失败，不继续扩展。

可选 RQ4  能否把 Root MC 的选择能力蒸馏到毫秒级神经后端？
     -> 尚未生成正式 teacher dataset，也未训练模型。
```

论文主线目前不依赖神经网络即可成立。Policy/Value/BNN 是“搜索蒸馏与低延迟部署”
增强项，不能反过来改写已经完成的 Root MC evaluation protocol。

## 四、关键术语

### 4.1 DecisionBackend

统一推理接口，输入事件状态、legal actions、solver portfolio 和 budget，输出一个
可审计 action。已有：

```text
fixed
priority
portfolio
stratified_root_monte_carlo
open_loop_uct
```

`DecisionBackend` 保持 inference-only；optimizer、梯度更新和 dataset 构建属于
独立 Trainer。

### 4.2 Flat Root / Stratified Root MC

当前通过 Gate 的搜索方法：

```text
同一 immutable snapshot
+ 同一 planning seed
+ 6 个 root actions 全部 terminal rollout
+ 完整 paired stratum 才原子 backup
+ 任一 action incomplete，则整层零 backup
+ coverage 不足时 fixed fallback
```

当前 `k=1` 表示每个 root action 在一次在线决策中完成一个共享 planning seed 的
paired evaluation。它不是“只执行一步物理仿真”，而是每个 action 都跑到 terminal。

### 4.3 Teacher 协议

Teacher 指已经验证有效的 flat Root MC。冻结 teacher 协议不是冻结模型权重，而是
在生成训练数据前锁死：

```text
状态特征
action vocabulary 和顺序
legal-action mask
snapshot/cluster 定义
planning seed 规则
rollout horizon
terminal cost
完整 stratum 语义
fallback
数据切分
label 派生 recipe
```

MCTS/Root MC 本身不训练。后续被训练的是 Policy、Value 和 BNN 后端。

## 五、当前联合 action space

固定顺序：

```text
CP-SAT+EECBS
CP-SAT+LG-LaCAM
DE+EECBS
DE+LG-LaCAM
PSO+LG-LaCAM
PSO+MAPF-LNS2
```

配置：

```text
experiment/skycausal/protocols/joint_profiles_deadline_v2.json
```

注意两个不同概念：

```text
evaluation best fixed:
  CP-SAT+EECBS

当前 profile config baseline / fixed fallback:
  CP-SAT+LG-LaCAM
```

论文比较必须使用 best fixed；在线 coverage 不足时执行的是声明的 fixed fallback。

## 六、严格预算语义

后续不得再混用以下概念：

```text
DecisionBudget:
  root search admission 和 eligibility

solver internal limit:
  solver 主动停止

HTTP timeout:
  transport guard，并触发远端 cancel

process hard deadline:
  SIGTERM + grace + SIGKILL

rollout horizon:
  simulation 的物理评价边界

planning wall time:
  用户真实等待时间

aggregate action compute:
  并行 actions 的总资源消耗
```

安全语义：

```text
一个 planning seed 下，全部 actions completed：
  整个 stratum 一次性 backup

任一 action cancelled / hard_deadline / failed / late_completed：
  整个 stratum 零 backup
```

## 七、已完成的核心结果

### 7.1 Deadline Infrastructure

六类 solver 共 600 请求：

```text
每个 solver:
  50 normal
  25 hard deadline
  25 explicit cancel

600/600 outcome 符合预期
active request 最终全部归零
无 late artifact activation
正常结果全部通过物理结构校验
```

Parallel forced-timeout：

```text
6/6 workers hard_deadline_exceeded
paired rounds = 0
partial backup = 0
fixed fallback
all MAPF session_count = 0
```

### 7.2 Joint Portfolio Headroom

20 clusters、6 profiles：

```text
best fixed mean capped makespan: 462.05
oracle mean: 448.00
oracle improvement: 14.05
95% CI: [7.05, 22.25]
non-best-fixed winner rate: 65%
Gate: passed
```

说明动态选择 solver profile 具有真实研究价值。

### 7.3 20-cluster Root MC Search Value

严格 planning/execution seed 分离：

```text
best fixed: CP-SAT+EECBS
best fixed mean held-out makespan: 457.60
held-out oracle mean: 436.80

Root MC k=1 mean: 438.55
improvement vs best fixed: 19.05
95% CI: [8.20, 32.45]
oracle regret closed: 91.59%
held-out oracle hit rate: 70%

planning wall mean: 2.99 s
planning wall range: [2.02, 4.76] s
aggregate compute mean: 16.84 s
```

主 static baseline 使用 leave-one-cluster-out topology shrinkage，但表现弱于 best
fixed。因此论文的关键证据是 Root MC 相对 best fixed 的正 CI，不能只用较弱的
static selector 衬托。

### 7.4 Budget Curve

```text
budget   root coverage   mean held-out cost   vs best fixed
2 s      0/20            459.85               -2.25
5 s      19/20           440.55              +17.05
10 s     20/20           438.55              +19.05
20 s     20/20           438.55              +19.05
```

当前 terminal k=1 的有效工作点约为 5 到 10 秒。2 秒预算不能声称搜索有效。

### 7.5 短物理 Horizon 负结果

已实验：

```text
machine repaired
+ event 后新完成 5 道 operation
+ remaining job-chain lower bound
```

其 leaf/terminal Spearman 约 0.13，几乎没有 action 排序能力。该 leaf value 不得
用于 Root MC 或 UCT backup，只作为负结果和未来 learned value 对照。

### 7.6 Open-loop UCT 负结果

已实现真实 two-event evaluator、UCB1、progressive widening、parallel root
coverage 和完整 simulation backup。修复过 UCB cost 量纲问题，当前 exploitation
使用 sibling mean cost min-max normalization。

7 个有效 clusters 的 held-out UCT 相对 flat Root：

```text
wins / ties / losses: 4 / 1 / 2
mean improvement: -3.14
95% CI: [-20.15, 8.71]
mean planning wall: 14.13 s
Gate: failed
```

阶段决策：

```text
不扩到 20 clusters；
不根据该批 held-out 结果继续调 UCB 或 continuation；
保留 UCT 代码和负结果；
当前搜索后端保留 Stratified Root MC k=1。
```

这不证明 UCT 永远更差，只说明当前 20 秒、稀疏 depth-2 two-event 协议没有证据
支持它相对 flat Root 的复杂度。

## 八、关键代码索引

### 8.1 Decision 与训练契约

```text
experiment/skycausal/decision_backend.py
experiment/skycausal/event_decision.py
experiment/skycausal/solver_profile_activation.py

trainer/decision_backend/contracts.py
trainer/decision_backend/collection.py
trainer/decision_backend/dataset.py
trainer/decision_backend/artifact.py
trainer/decision_backend/cli.py
trainer/decision_backend/README.md
```

已有：

```text
DecisionTransition
cluster-safe split
DecisionDatasetManifest
TrainingRecipe
ModelArtifactManifest
audit-to-transition adapter
Docker-only dataset/artifact CLI
hash 与 Gate 校验
lazy PyTorch import
```

当前仅有训练基础设施，没有正式神经模型训练。

### 8.2 Root MC

```text
experiment/skycausal/root_monte_carlo.py
experiment/skycausal/run_root_monte_carlo.py
experiment/skycausal/analyze_root_monte_carlo.py
experiment/skycausal/analyze_root_mc_budget_curve.py
experiment/skycausal/rollout_horizon.py
```

### 8.3 UCT

```text
experiment/skycausal/open_loop_uct.py
experiment/skycausal/multi_event_profile_sequence.py
experiment/skycausal/run_open_loop_uct.py
experiment/skycausal/evaluate_open_loop_sequences.py
experiment/skycausal/analyze_open_loop_uct.py
```

### 8.4 Deadline

SkyEngine：

```text
experiment/skycausal/run_deadline_infrastructure_stress.py
sky_executor/.../online_fjsp_gateway.py
sky_executor/.../http_route_solver.py
```

SkyEngine-FJSP：

```text
FJSP-master/deadline_process.py
FJSP-master/DE_solver/*
FJSP-master/PSO_solver/*
OR-solver/*
```

SkyEngine-MAPF：

```text
server/deadline_process.py
server/base.py
adapters/classical_http_server.py
```

## 九、关键 Artifact

相对 SkyEngine 根目录：

```text
Root 20-cluster held-out:
experiment/skycausal/results/root_parallel_k1_20cluster_20260805/
heldout_analysis.json
SHA256:
563c6632369e385ddfc5004ed0dad6304955b442fd85b23f4697c78a3c105f60

Budget curve:
experiment/skycausal/results/root_parallel_k1_20cluster_20260805/
budget_curve.json
SHA256:
4a7e65b4eeb206ff859fa10866678f6ed3fbee641fba4c73936f0d198061553d

Forced timeout:
experiment/skycausal/results/root_parallel_deadline_stress_20260805/
forced_timeout.json
SHA256:
89f8d63343b23ef020384241c18ea6cc632396b4495b2b4a5d417925edbf1501

UCT analysis:
experiment/skycausal/results/open_loop_uct_8cluster_20260805/
analysis.json
SHA256:
92a151f1f3918a274f56e1982573afb3d3dd9d264c3b11e2851711d6fc400c22
```

主设计文档当前 SHA256：

```text
fe12c8bb927bfc1b17d445a317c699a1113f3643a54958458f6c8d787af9b613
```

Teacher v1 生成时冻结协议 SHA256：

```text
8c7a0d4d870ee7fcd9ddc2f7973e5eb4f4e0fcfb0482e6abee3c12734f8b1363
```

执行后协议审核文档 SHA256：

```text
ea7c8968e0fc0fb5fd7bfb27c18df6f4b0442f9960296c5f9812ec0ebde42b9b
```

Teacher smoke 审核报告 SHA256：

```text
b749a41efbb6fb03c499a11d1948cf9c7bece18d087ca97235dd73debdafbf3f
```

Teacher smoke artifact：

```text
path:
  artifacts/flat_root_teacher_smoke_v1_8c7a0d4d

dataset ID:
  bc0a23318f6f6da0b96e796cd5371b69b377462ad7e715c182edc8c6eea4e0af

dataset_manifest.json SHA256:
  a360940895154b1925c3124ae78d1d4ae4e2bfaa638e0d9b38ecb4c5a522b88c

checksums.sha256 SHA256:
  72929221e686e4621abf52ece6560e335aedf8aff85b647a651d17ffff2a14f6

fixed-image read-only validation:
  327 files, valid
```

Teacher v2 协议与审核报告：

```text
protocol:
  research/20260806_FlatRootTeacher完整组Retry协议_v2.md
  SHA256:
  2166de55eeaeb4e0476bedb64c8e088a0456710a3ced47fbd51edeb73ce58441

audit report:
  research/20260806_FlatRootTeacher完整组Retry审核报告_v2.md
  SHA256:
  ab00848162355f391ca8320d5e2ae9d0ab35e506fdc75e738cce7d10166a0e9c
```

Teacher v2 artifact：

```text
path:
  artifacts/flat_root_teacher_smoke_v2_2166de55

dataset ID:
  0b62b89d254d8d7f893740667a91f72c19b7149d8b1daf77781df24f9ba25042

dataset_manifest.json SHA256:
  d95e354a92ae89b54757646861c5895f8e8be87322e114e6e3c28cf420c411ce

checksums.sha256 SHA256:
  32deab81e9526e893379141872a4893fb4eadbea9194fb8619f74b1f179a1523

fixed-image read-only validation:
  437 files, valid
```

## 十、回归状态

最近完整验证：

```text
Teacher v2 retry contract: 9/9 passed
Teacher/Root/Decision focused: 45/45 passed
SkyEngine source-mounted SkyCausal: 199/199 passed
SkyEngine fixed-image SkyCausal: 199/199 passed
SkyEngine-MAPF deadline/session: 16/16 passed
SkyEngine-FJSP deadline/dynamic artifacts: 6/6 passed
CP-SAT / DE / PSO fixed-image endpoint smoke: passed
git diff --check: passed
```

固定 SkyEngine 镜像的完整回归命令不挂载源码或 `.git`：

```bash
cd /Users/bytedance/project/learn/flex_manufacture/260601天工论文准备/codebase/SkyEngine

docker run --rm \
  skyengine:b1389e9017a3 \
  python -m unittest discover -s test/skycausal -q
```

## 十一、固定仓库与镜像

### 11.1 三仓 clean commits

```text
SkyEngine:
  b1389e9017a331f19ce7354370410fc741b3ff1e

SkyEngine-MAPF:
  68bf40005dcf479442043f07d08648149cc8913e

SkyEngine-FJSP:
  1edcf14535d97e0f04d535f34aee81c3d944f6bc

状态:
  三仓 worktree clean
```

SkyEngine 主仓拆分提交：

```text
8ddd9477  deadline-aware solver portfolio + Root MC
38509444  Open-loop UCT negative result
8416d0ad  Flat Root Teacher data contracts
38af10d3  immutable source image
b1389e90  auditable Teacher full-group retries
```

### 11.2 Clean-commit image digests

```text
SkyEngine:
  sha256:b0f4a000c7863edc6e1c3b67760046c9eab4ce215ed80cefa7ce94c6ddef7933

MAPF classical:
  sha256:35a1600badd25ec60dd592819afc692ece3b6259c22dc1de417c308c51ae5c24

FJSP CP-SAT:
  sha256:6c48ca1271d391831fae0b8fe8c62f997608bc689d34c01ca37796ee35574550

FJSP DE:
  sha256:c47348edbdd173a0c84c7a4d4bbec9309fdc293be3d3402e23b3a5b8c4c33624

FJSP PSO:
  sha256:86d5a92ccf76f28fbe51e7f2c45acf2a3f75ebdca15be6c2c23ef8980763daf5
```

### 11.3 Locked profile

```text
path:
  experiment/skycausal/protocols/joint_profiles_deadline_v2.json

SHA256:
  b6e35b5281d7a1bce0c83500e5f41ab3206489fb17ddf08d1b6684e41f4422ce
```

该 profile 和 Teacher schemas 已进入 Git。Root MC 不再接受 digest override，并
要求完整镜像 digest 与 MAPF/FJSP commit 环境。原 dirty smoke 结果继续保持本地
忽略，不得重标为 publication evidence。

## 十二、文献状态

核心文献：

```text
papers/2025_DyRo-MCTS_Dynamic_Job_Shop_Scheduling.pdf
SHA256:
306e8578c0d544f83f0cb0a90ba89ca7262882690d4d75dd897bfff8168e09c8
pdfinfo: 16 pages

papers/2025_Li_DFJSP_AGV_MARL.pdf
SHA256:
b9004ce988f9c655dcfac08db8a5401737660fdf64cfa4e07707b296f3574d71
pdfinfo: 13 pages
```

两份当前文件都能被 `pdfinfo` 和 `pdftotext` 正常解析，标题正确。

但以下文档仍写着 MARL 全文未取得，状态已经不一致：

```text
papers/README.md
papers/metadata/2025_Li_DFJSP_AGV_MARL.md
```

新窗口应先确认 PDF 来源合规，再同步更新 README、metadata 和 manifest。不要只
根据文件存在就删除 closed-access 来源说明。

## 十三、下一阶段：Flat Root Teacher Protocol v1

### 13.1 先写协议，不先训练

建议新增：

```text
research/20260806_FlatRootTeacher数据生成协议.md
```

必须预先锁定：

```text
teacher backend:
  Stratified Root MC k=1

action vocabulary:
  固定 6 profiles 和固定顺序

horizon:
  terminal

cost:
  capped makespan

pairing:
  same snapshot + Common Random Numbers

commit:
  complete-stratum atomic backup

fallback:
  CP-SAT+LG-LaCAM

provenance:
  code commit + image digest + snapshot artifact hash
```

### 13.2 训练 cohort 必须与论文 evaluation cohort 隔离

严禁把以下 20-cluster development/evaluation cohort直接用于训练：

```text
maze:
  110,111,112,113,115,116,117,118,119,120,121

maze-b:
  110,111,113,114,115,116,117,118,120
```

应使用新的 map/environment/snapshot seeds 创建 training-only cohort，并以
snapshot/cluster 为切分单位。planning seed 和 execution seed 也必须分离。

正式规模不要直接拍脑袋。建议顺序：

```text
10-20 个 training-only clusters:
  只做 schema、coverage、label-noise smoke

完成 label noise 和 power audit 后:
  再确定正式训练规模，预期需要数百个独立 clusters
```

### 13.3 原始 teacher log 必须保存完整 action costs

不要只保存 winner：

```text
state
legal_action_mask
6 个 action 的 paired terminal costs
selected action
planning seed
snapshot hash
process/deadline audit
physical invariant audit
profile/image provenance
```

推荐原始记录一行对应一个 `counterfactual_group_id + action_id`，同组必须包含完整
6 actions。这样后续可以版本化派生：

```text
hard policy label:
  argmin cost

soft policy/ranking label:
  根据相对 regret 或 temperature 计算

value target:
  state-action terminal cost

advantage target:
  action cost - group best cost
```

原始 paired costs 一旦固化，不因模型选择变化而重写。

### 13.4 当前建议的模型顺序

```text
Phase A:
  deterministic ranking/value baseline

Phase B:
  Policy Network，学习 masked action ranking

Phase C:
  Value Network，预测 state-action cost/regret

Phase D:
  BNN residual / ensemble uncertainty

Phase E:
  uncertainty Gate + Root MC fallback

Phase F:
  新预注册协议下再考虑 PUCT
```

当前不要直接做 PPO、GRPO、offline RL 或因果效果宣称。原因：

```text
训练 cohort 尚未生成；
行为 overlap 和 propensity 尚未审计；
当前主要价值来自同 snapshot 全 action counterfactual，而不是历史行为日志；
旧 GRPO rollout 污染和旧 Distiller random split 仍未修复。
```

### 13.5 Neural/BNN Gate

模型至少需要：

```text
合法 action rate = 100%
cluster-held-out ranking/regret 改善
相对 best fixed 的 terminal value 不退化
相对 teacher 的 imitation regret 可接受
推理延迟显著低于 Root MC
OOD/uncertainty calibration 通过
高不确定样本 deterministic fallback = 100%
artifact/hash/replay Gate 通过
```

神经模型只有在独立 locked test cohort 上同时通过质量、延迟和 fallback Gate 后，
才能升级为论文主贡献。否则保持为可选增强或负结果。

## 十四、Publication Evidence 仍缺什么

以下工程前置已经完成：

1. 三仓审计并提交；
2. 固定三仓 source commit；
3. 固定 FJSP/MAPF/SkyEngine image digest；
4. 更新 profile config 并移除 Root MC digest override。

当前关键结果仍是 development evidence。正式论文证据还需要：

1. 冻结 publication cohort、exclusion rule 和 static selector；
2. 锁定 planning/execution seeds；
3. 将新 run、manifest、snapshot 明确写入不可变存储；
4. 从 fixed images 重跑 Deadline、Headroom、Root Search Value；
5. 生成 publication tables/figures，并核验 artifact SHA256。

## 十五、当前不可声称事项

不得声称：

```text
publication-locked Search Value Gate 已通过；
2.99 s 已满足最终实时控制要求；
UCT 优于 flat Root；
短 K=5 leaf value 可用于 MCTS backup；
static selector 是强 baseline；
神经网络已经训练或发布；
BNN 已经通过 OOD/calibration Gate；
因果效应已被识别；
当前 dirty development artifact 可直接作为论文最终证据。
```

当前可以声称的 development 结论：

```text
solver portfolio 存在显著 headroom；
strict deadline/cancel/fallback 执行链成立；
flat Root MC k=1 在 20 个 held-out development clusters 上显著优于 best fixed；
当前 Open-loop UCT 没有显示相对 flat Root 的额外价值；
搜索蒸馏具有明确的工程动机，但尚未完成实验。
```

## 十六、新窗口建议执行顺序

### Step 1：只读审计（已完成）

1. 阅读本文；
2. 阅读主设计文档第 12、19、20 章；
3. 检查三个仓库 `git status`；
4. 检查四个关键 artifact 的 SHA256；
5. 不立即修改算法超参数。

### Step 2：固定当前工程状态（已完成）

1. 分仓审计 dirty changes；
2. 把 Deadline、Root MC、UCT 代码拆成可解释 commits；
3. 重建镜像并更新 profile config；
4. 重跑 SkyEngine 190 + MAPF 16 + FJSP 6 项回归。

### Step 3：写 Teacher Protocol v1（已完成）

只写协议和 checklist，先审核：

```text
feature schema
action schema
raw group schema
seed policy
cluster split policy
label derivation recipe
dataset manifest
neural Gate
```

### Step 4：小规模 training-only data smoke（已执行，总体 Gate 失败）

只使用协议预注册的 state seeds 130--149，冻结了 20 个 training-only clusters：

```text
planning:                 20 groups / 120 branches
heldout audit:            19 groups / 114 branches
split leakage:             0
duplicate records:         0
label signal checks:       passed on 19 complete pairs
paired coverage:           failed at 19/20
dataset replay validation: 327 files valid
```

### Step 5：完整组 Retry v2（已执行，总体 Gate 失败）

```text
attempt bundles:          40/40
first-attempt success:    38/40
retry triggers:            1
second-attempt success:    0/1
planning groups:          19/20
heldout groups:           19/20
paired coverage:          19/20
fixed-image validation:  437 files valid
```

### Step 6：当前执行分支

```text
停止 neural Teacher 分支；
保留 v1/v2 只读负结果；
进入 clean publication rerun；
不得训练 deterministic ranking/value baseline 或 BNN。
```

## 十七、给新窗口的首条指令模板

可以直接发送：

```text
工作目录：
/Users/bytedance/project/learn/flex_manufacture

请先完整阅读：
1. 260601天工论文准备/research/
   20260805_SkyCausal_MCTS阶段进展与新窗口交接.md
2. 260601天工论文准备/research/
   20260805_严格Deadline与AnytimeMCTS设计方案.md
3. 260601天工论文准备/research/
   20260805_DecisionBackend训练与模型发布设计草案.md
4. 260601天工论文准备/research/
   20260805_FlatRootTeacherSmoke审核报告.md
5. 260601天工论文准备/research/
   20260806_FlatRootTeacher完整组Retry审核报告_v2.md

当前已决定：
- 保留 Stratified Root MC k=1；
- Open-loop UCT Value Gate 失败，不继续调参；
- 20-cluster evaluation cohort 不得用于训练；
- 三仓 commit、SkyEngine v2 镜像 digest 和 locked profile 已固定；
- Teacher v1 planning Data Gate 通过，但 paired coverage 只有 19/20；
- Teacher v2 完整组 retry 后 planning/heldout 都是 19/20；
- v1/v2 overall smoke Gate 均失败，两个 artifact 均只读；
- 神经网络尚未训练。

先不要训练模型，也不要补跑或改写 v1/v2。下一步进入 clean publication rerun，
先冻结 publication cohort、exclusion、seeds、tables 和 artifact 输出协议。
```
