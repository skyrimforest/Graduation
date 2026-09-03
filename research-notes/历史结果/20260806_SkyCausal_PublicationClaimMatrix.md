# SkyCausal Publication Claim Matrix

日期：2026-08-06

状态：`PUBLICATION_RUN_COMPLETE_GATE_FAILED`。预注册版本 SHA256
`dd993373...` 已随正式 artifact 冻结；本文当前状态栏记录 protocol
`f650f738...` 的结果后判定，不改变原通过条件。

## 一、论文定位

建议主标题方向：

> Deadline-Safe Counterfactual Root Search for Online Solver-Portfolio
> Control in Dynamic FJSP-MAPF

方法定位是动态 FJSP-MAPF 中的在线联合 solver-portfolio control，不是新的通用
MCTS tree policy，也不是因果效应识别方法。当前通过 development Gate 的方法是
`Stratified Root Monte Carlo, terminal, k=1`；open-loop UCT 没有通过增益 Gate。

论文最小完整论证链：

```text
可复现物理 snapshot
  -> 同源反事实分支与 CRN
  -> 联合 FJSP-MAPF portfolio 存在 headroom
  -> 严格 deadline 下 Root Search 优于最佳固定 profile
  -> timeout/cancel/session cleanup 不破坏物理安全
  -> quality-latency-fallback 边界可量化
```

## 二、与核心竞争工作的边界

### 2.1 DyRo-MCTS

`DyRo-MCTS` 研究动态 job arrival 下的 job-selection MCTS，以离线策略为 prior，
并把 machine-utilisation robustness 加入 tree policy。它支持“动态调度中在线
lookahead 有价值”，但不能替代本项目需要证明的以下差异：

1. FJSP solver 与显式无碰撞 MAPF solver 的联合 profile action；
2. machine breakdown 后完整物理 snapshot 上的 terminal counterfactual rollout；
3. 六分支 CRN、完整 stratum 原子提交和不完整覆盖 fallback；
4. solver hard deadline、显式 cancel、process group 与 MAPF session isolation；
5. capped terminal cost、oracle regret 和 wall-clock evidence 的统一审计。

因此不得把“使用 MCTS”本身写成创新。可检验创新是 deadline-safe、physically
paired 的联合 solver-portfolio root search。

### 2.2 Li et al. DFJSP-AGV MARL

Li et al. 联合 task selection、machine allocation 与 AGV allocation，并处理四类
动态事件。它是生产物流联合在线决策的强相关工作。本项目只能在下列差异有正式
证据后声称互补贡献：

1. 显式 grid MAPF 与 collision-free path，而不是仅使用运输时间或资源分配；
2. 在同一动态状态上选择 FJSP-MAPF solver profile，而不是学习三类资源动作；
3. 不依赖训练数据的在线 search，以及明确的 fixed fallback；
4. 可审计的 deadline、cancel、quiescence 和 failure-as-cost 语义。

不得声称本项目全面优于 MARL；两者 action space、目标和计算预算不同。论文比较
应采用 problem-setting comparison 和能力矩阵，除非获得可执行的同协议 baseline。

## 三、可检验主张

| ID | 拟支持主张 | 必需证据 | 主基线 | 通过条件 | 当前状态 |
|---|---|---|---|---|---|
| C0 | Snapshot fork、CRN 和远端 MAPF replay 保持同源物理语义 | deterministic-time 双 capture semantic signature、clean-image replay、state/input/output hash、physical invariants | identical-policy twin | 两次 capture 均 eligible 且 semantic signature 相同；全部 replay exact；物理违规为 0 | **PASS**：40/40 selected snapshots，physical invalid=0 |
| C1 | 六个联合 solver profiles 在严格单次 solver budget 下存在互补 headroom | publication heldout 六分支 capped costs | ex-post global best fixed | oracle improvement 均值大于 0 且 cluster-bootstrap 95% CI 下界大于 0；FJSP/MAPF winner algorithm 各至少 2 类 | **PASS**：26.325，95% CI [19.575, 33.425] |
| C2 | Flat Root MC k=1 在独立 heldout execution 上优于最佳固定 profile | planning/heldout seed 分离的 40-cluster paired evaluation | ex-post global best fixed | 全样本 mean improvement 大于 0；95% CI 下界大于 0；Infrastructure Gate 全通过 | **FAIL**：效果量 19.750、95% CI [8.850, 29.475]，但 Infrastructure Gate FAIL |
| C3 | 提升不是由弱 static selector 衬托出来 | 同一 heldout cost matrix 上的强基线表 | global best fixed、topology best fixed、runtime fallback、LOCO static selector、heldout oracle | C2 必须独立通过 global best fixed；其他比较完整报告，不作为替代 Gate | **REPORTED_NOT_AUTHORIZED**：基线完整，C2 未通过 |
| C4 | 搜索在 hard deadline 下可安全退化 | stress run、root run 与 post-run health/quiescence | runtime fallback | hard-deadline 越界、partial backup、late active request、orphan session、物理违规均为 0 | **FAIL**：600/600 stress PASS；root-run quiescence/deadline audit subgate FAIL |
| C5 | 方法具有明确 quality-latency-fallback 工作区间 | 2/5/10/12 秒 conservative admission curve | runtime fallback、best fixed | 10/12 秒主工作点 C2 通过；所有预算均报告 coverage、fallback 和 CI | **FAIL_COMPLETE_REPORTING**：曲线完整且数值为正，C2 依赖未通过 |
| C6 | 当前深层 UCT 不值得额外复杂度 | 冻结 two-event negative pilot | Flat Root MC k=1 | 作为边界/消融报告，不要求正结果，不再调参 | development Gate 失败，已停止 |
| C7 | 结论可跨规模或拓扑外推 | 独立 robustness cohort | 每个子组 best fixed、runtime fallback | 每个预注册子组完整报告；只有正 CI 的子组允许正向声称 | **NOT_EVALUATED** |

### 3.1 正式结果锁

```text
artifact:
  artifacts/skycausal_publication_rerun_v1_f650f738/

pair manifest SHA256:
  be76956c3db18bbca1ac4e57d2949ec1b95a5eb4cc507383aef8f03ea05fcefd

analysis SHA256:
  70b074dc5732ad9fb745730fb8dda5280afe90fe7e697594ef81cb1c52b75e05

global best fixed:
  DE+LG-LaCAM, mean 462.625

Root_or_fallback:
  mean 442.875

primary improvement:
  19.750, 95% CI [8.850, 29.475]
```

统计子 Gate 为正，但 planning/heldout 各有 4 个 infrastructure-invalid clusters。
其中三个 hard-deadline cluster 在 raw Root health Gate 上未及时 quiesce；另有
planning 与 heldout 各一个 internal MAPF fallback 未通过 deadline accounting。
正式 600-request stress Gate 仍为 `600/600 PASS`。按预注册条件，C2 和 C4 必须
判为 `FAIL`，不得用 phase 后最终归零或正效果量覆盖。

## 四、主张层级

### 4.1 必须通过

论文主结果至少要求：

```text
C0 PASS
C1 PASS
C2 PASS
C4 PASS
C5 complete reporting
```

若 C2 失败，不得以 C1 的 oracle headroom 替代实际 controller value，也不得只用
static selector 作为对照宣称搜索有效。

### 4.2 增强但不替代主 Gate

`C3` 用于证明 baseline 强度。`C7` 用于外部有效性。C7 失败时仍可形成范围严格
限定为 `J10P5M6 + two maze layouts + machine breakdown` 的论文，但不能写
“跨规模、跨拓扑泛化”。

### 4.3 负结果

以下结果保留在 appendix 或 limitations：

1. short physical milestone 不稳定；
2. open-loop UCT 相对 flat Root 的 CI 未通过；
3. Teacher v1/v2 coverage 均为 `19/20`，禁止训练；
4. `maze/140` 的 `DE+EECBS` deadline 边界可重复。

这些结果不能被删除，也不能转换为调参依据后重跑原 heldout cohort。

## 五、论文表图与主张绑定

| 产物 | 对应主张 | 必须包含 |
|---|---|---|
| Table 1: Problem and cohort | C0--C7 | family、map、event、severity、AGV、eligible/excluded |
| Table 2: Portfolio headroom | C1 | 六 profile、best fixed、oracle、winner diversity、CI |
| Table 3: Search value | C2/C3 | Root、global/topology fixed、fallback、static、oracle |
| Table 4: Deadline safety | C4 | normal/deadline/cancel、p95/p99/max、active/session residue |
| Figure 1: Method | C0/C2/C4 | snapshot、CRN、parallel stratum、atomic backup、fallback |
| Figure 2: Quality-latency curve | C5 | budget、coverage、fallback、capped makespan、CI |
| Table/Figure A1: Negative ablations | C6 | milestone 与 UCT，不隐藏排除和失败 |
| Table/Figure A2: Robustness | C7 | 按 family/topology 分层，不只报告 pooled mean |

## 六、禁止性表述

在没有额外证据前，禁止：

1. “提出了新的通用 MCTS 算法”；
2. “证明了 causal effect”或“识别了因果效应”；
3. “优于所有 MARL/DRL 方法”；
4. “毫秒级实时决策”；
5. “跨规模、跨地图、跨扰动类型泛化”；
6. “神经策略已可部署”；
7. 把 development、Teacher 或 dirty-worktree artifact 当 publication evidence。

允许的核心表述必须包含适用范围、wall-clock budget、fallback 和 heldout 设计。

## 七、冻结前检查

1. `PublicationRerun协议` 与本文的 C0--C7 一致；
2. primary endpoint 只有一个：heldout capped makespan improvement vs global best fixed；
3. best fixed 在整个 publication cohort 上 ex-post 选择，对 baseline 有利；
4. timeout、solver failure 和不完整 Root coverage 均计入，不做结果后排除；
5. eligibility 只依赖 action-independent snapshot 属性，且双 capture semantic Gate 已冻结；
6. publication seeds 与 development `100..149` 完全隔离；
7. 所有表图可由 frozen raw artifact 一键重建；
8. 文献“首次”主张必须在投稿前重新检索，不由本文件授权。
