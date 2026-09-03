# DecisionBackend 与学习后端演进协议

日期：2026-08-04

状态：策略后端第一版已实现；Portfolio Headroom Gate 待执行

## 一、设计结论

SkyCausal 的稳定研究对象不应是某一种 MCTS、RL 或因果算法，而应是：

> 面向动态 FJSP-MAPF 的事件驱动、预算约束、可审计决策契约。

`DecisionBackend` 是算法替换边界。规则、MCTS、RL、BNN 和因果推断都只能通过
同一状态、动作、预算和审计接口接入，不能绕过物理可行性检查或直接修改环境。

训练职责补充（2026-08-05 已批准执行）：

- 规则和纯 MCTS 后端不需要训练；
- `DecisionBackend` 建议永久保持 inference-only，不增加 `train()`；
- 神经网络、BNN、RL 和 learned-MCTS 的模型由独立离线 Trainer 生成 artifact；
- 在线后端只读加载通过 Gate 的 artifact，并始终保留规则/MCTS fallback。

完整待审核设计见：
[`20260805_DecisionBackend训练与模型发布设计草案.md`](20260805_DecisionBackend训练与模型发布设计草案.md)。

当前冻结的执行顺序为：

```text
Physical State / Event
        |
        v
EventResponseRegistry
        |
        v
Eligibility + Feasibility Mask
        |
        v
DecisionBackend
        |
        v
Decision + Audit
        |
        v
Profile Activator / Physical Action Handler
        |
        v
SkyEngine Transition
```

## 二、两篇核心文献的定位

### 2.1 DyRo-MCTS

本地原文：
[`papers/2025_DyRo-MCTS_Dynamic_Job_Shop_Scheduling.pdf`](papers/2025_DyRo-MCTS_Dynamic_Job_Shop_Scheduling.pdf)

可直接继承：

- offline policy 作为 MCTS prior；
- 在 decision time 做有限预算 lookahead；
- 区分即时 action value 与面向未来扰动的 robustness；
- 报告不同 decision budget 下的收益和额外在线耗时。

不能直接照搬：

- 论文处理动态 JSS 和新 Job 到达，不是 FJSP-MAPF；
- robustness 主要来自机器利用率/空闲分布，不覆盖 AGV 冲突和载货承诺；
- 动作是 Job priority，不是“恢复算子 + FJSP profile + MAPF profile + 预算”；
- OpenReview 最终拒稿的核心意见包括创新主要集中于 UCT robustness 项、
  DJSS MCTS 对比不足和适用范围论证不足。

因此本项目不能把“给 UCT 增加一项”作为主贡献。

### 2.2 动态 FJSP-AGV 四事件 MARL

书目信息：
[`papers/metadata/2025_Li_DFJSP_AGV_MARL.md`](papers/metadata/2025_Li_DFJSP_AGV_MARL.md)

可直接继承：

- task selection、machine allocation、AGV allocation 的多主体分解；
- 高维动作的有效解码；
- 动态事件下的实时响应与 total tardiness 评价；
- priority rules、GP 和 RL 方法的 baseline 体系。

本项目必须增加：

- 显式 collision-free MAPF，而不是只做 AGV 分配；
- 区分 empty/loaded transport 和不可撤销载货承诺；
- 统一 typed event action；
- FJSP/MAPF solver portfolio；
- 同源反事实、独立 planning RNG 和严格 wall-clock budget；
- terminal makespan、TWT、OTD 和物理不变量联合 Gate。

当前只能从公开摘要确认论文报告了四类 disturbance events。取得合法全文前，不把
SkyCausal 的“机器故障、AGV 故障、道路阻塞、紧急订单”表述为与原文四事件
逐项完全一致；该映射需要全文核验。

## 三、统一契约

### 3.1 DecisionState

```text
event_type
online features
physical/event context
```

状态只能包含决策时可观测信息。terminal makespan、测试折 outcome、事后关键路径
和 oracle action 禁止进入。

### 3.2 DecisionAction

```text
action_id
recovery_operator
operator_parameters
solver_profile
compute_budget_ms
rank
eligibility metadata
```

稳定动作语义为：

```text
恢复算子 + 算子参数 + FJSP profile + MAPF profile + 计算预算
```

动作在送入后端前必须通过 eligibility 和物理可行性过滤。后端没有选择非法动作的
接口。

### 3.3 SolverProfile

每个 profile 至少记录：

```text
name
fjsp_profile
mapf_profile
minimum_budget_ms
maximum_budget_ms
supported_event_types
license / rolling / warm-start / safe-switch metadata
```

profile 被选择不等于已生效。执行控制器只有在接入真实 `profile_activator` 后才允许
执行带 profile 的动作；否则必须显式失败，禁止只改审计标签而不改物理求解器。

### 3.4 DecisionBudget

首版以 `wall_time_ms` 为硬约束，并预留 `simulation_limit`。后续 MCTS/RL 比较
必须在相同 wall-clock budget 下进行，不能用 simulation count 代替实际延迟。

### 3.5 Decision Audit

每次选择至少保存：

- backend 类型与完整配置；
- DecisionState 在线特征；
- 全部 legal actions；
- 每个候选的规则匹配和 score；
- 最终 action/profile；
- budget；
- profile activation 和物理 action outcome。

## 四、首批策略后端

### 4.1 FixedDecisionBackend

用途：

- 固定动作 baseline；
- 安全回退；
- 单一 profile 对照；
- 反事实 treatment 冻结。

指定动作不可用时，只能按显式 fallback 顺序或稳定 rank 选择其它合法动作。

### 4.2 PriorityDecisionBackend

用途：

- 透明阈值规则；
- eligibility-aware 优先级；
- 作为学习方法前的最低复杂度 selector。

规则配置由 `source + feature path + operator + value` 构成。配置采用严格 schema，
未知字段直接报错，防止策略参数被静默丢弃。

机器故障首批透明策略：

```text
wait_only
v1_positive_advantage
v3_physical_positive_advantage
global_projection_positive_advantage
```

这些策略只用于基础设施与假设筛查。已有独立实验表明 v1/v3/global estimator
尚未通过 Value Gate，因此不能作为论文最终方法。

### 4.3 PortfolioDecisionBackend

该后端分两步：

1. 用 operator backend 选择恢复算子；
2. 在预算和事件约束下选择 solver profile。

第一版只完成纯选择契约和审计。真实在线切换还需实现：

- FJSP artifact 安装；
- MAPF reservation/playback/cache 迁移；
- loaded AGV safe-switch boundary；
- timeout/cancellation；
- profile activation rollback。

## 五、RL、BNN 与因果推断的职责

用户提出 BNN 和因果推断适合解释性场景，这个方向成立，但需要严格区分三者职责。

### 5.1 RLDecisionBackend

负责长期序列决策：

```text
state -> masked action/profile policy
```

必须使用 SMDP duration-aware return，避免把等待 8 步和一次长时局部重调度当成
等时长动作。RL 不负责证明动作因果效应，也不应绕过 feasibility mask。

### 5.2 BayesianValueBackend

BNN 更适合承担：

- action value / residual value 的后验均值；
- epistemic uncertainty；
- OOD 和低数据区间检测；
- risk-aware action ranking；
- 高不确定性时回退规则/MCTS。

BNN 的不确定性不是因果解释。仅能说明“模型对该估计有多不确定”，不能说明
“动作导致了多少收益”。

### 5.3 CausalEffectBackend

因果模块更适合估计：

```text
CATE(s, action_a, action_b)
```

前提包括：

- 同源反事实或可辩护的可忽略性；
- consistency；
- positivity/overlap；
- 正确的决策时协变量；
- 不使用动作后的中介变量；
- cluster-aware uncertainty。

当前 SkyEngine 的 snapshot/fork 和 common random numbers 为同源反事实提供了
较强基础，但仍要避免 planning seed 与 execution seed 泄漏。

### 5.4 推荐混合形式

保留 baseline 兼容的残差注入：

```text
score(a) = baseline_score(a)
         + gate(s, a) * learned_residual(s, a)
```

其中：

```text
gate = eligibility
     * overlap_gate
     * uncertainty_gate
     * OOD_gate
```

候选实现：

- RL policy 给 MCTS/PUCT 提供 prior；
- BNN value 给出 `mean + risk_weight * std`；
- causal effect model 约束或修正 action advantage；
- 任一 Gate 失败时回退到 fixed/priority backend。

## 六、准入 Gate

### 6.1 Strategy Integrity Gate

- 不同策略配置必须进入 decision audit；
- 未消费配置必须报错；
- 至少一个受控状态上产生不同 selected action；
- selected action 必须全部 legal；
- 相同输入、配置、seed 产生相同 decision hash。

### 6.2 Portfolio Headroom Gate

- oracle portfolio 相对 best fixed mean improvement > 0；
- cluster-bootstrap 95% CI 下界 > 0；
- 至少 20% independent clusters 的 winner 不同；
- winner 至少覆盖 2 个 FJSP 和 2 个 MAPF profiles。

不通过则停止 portfolio MCTS。

### 6.3 Search Gate

- pairwise sign accuracy >= 65%；
- rank correlation >= 0.30；
- 等 wall-clock budget 下显著缩小 oracle regret；
- 报告 p50/p95 decision latency 和 timeout。

### 6.4 BNN Gate

- held-out NLL/CRPS 优于确定性 value baseline；
- 50/80/95% interval coverage 校准；
- OOD uncertainty 显著高于 ID；
- uncertainty gate 能改善 terminal value，而非只改善离线拟合。

### 6.5 Causal Gate

- overlap、balance 和 effective sample size 通过；
- randomized/same-snapshot treatment 上能恢复已知效应方向；
- placebo 和 negative-control 不显著；
- DR/AIPW 与直接同源反事实估计一致；
- 未见 instance/event holdout 上方向稳定。

### 6.6 Terminal Value Gate

- completion 和物理不变量通过；
- mean terminal improvement > 0；
- cluster-bootstrap 95% CI 下界 > 0；
- 同时报告 makespan、TWT、OTD、nervousness 和 wall-clock cost。

## 七、当前实现映射

代码：

- `experiment/skycausal/decision_backend.py`
  - typed state/action/profile/budget/decision；
  - fixed、priority、portfolio；
  - strict config factory。
- `experiment/skycausal/event_decision.py`
  - eligibility 过滤；
  - backend 调用；
  - decision/profile/action 联合审计；
  - 无 profile activator 时禁止伪执行。
- `experiment/skycausal/machine_decision_policies.py`
  - 首批机器故障透明策略配置。
- `experiment/skycausal/machine_response.py`
  - 原子动作 registry；
  - backend-driven controller 入口。
- `test/skycausal/test_decision_backend.py`
  - 配置透传、合法性、策略差异、portfolio 预算和事件执行测试。
- `trainer/decision_backend/`
  - transition、cluster split、dataset、recipe 和 artifact 契约；
  - audit-to-transition 严格适配；
  - promotion Gate 与离线 CLI。
- `docker-compose.train.yaml`
  - 无网络、只读训练契约与数据/artifact 工具入口。
- `test/skycausal/test_decision_training.py`
  - 数据泄漏、不可变 manifest、artifact 篡改和 Gate 证据测试。

## 八、下一步探索顺序

1. 通过 Strategy Integrity Gate，并把 selected action 与物理 outcome hash 联合
   写入实验结果；
2. 将 FJSP/MAPF profile 构造成少量行为差异明显的组合，先跑单侧 diversity；
3. 执行 Portfolio Headroom Gate；
4. Headroom 通过后实现 flat rollout，再实现 progressive-widening MCTS；
5. MCTS 生成可靠 visit/Q 标签后训练 policy/value；
6. 最后引入 BNN uncertainty gate 和 causal effect correction。

当前不直接训练 RL+BNN，也不把 `DecisionBackend` 软件抽象本身包装成论文算法
贡献。下一阶段的首要证据仍是 solver portfolio 是否存在可泛化的选择价值。
