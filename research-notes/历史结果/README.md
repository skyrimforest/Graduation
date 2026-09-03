# SkyEngine 论文调研资料

本目录用于记录 SkyEngine 项目的领域调研、论文定位、创新点判断和实验实施方案。

## 当前入口

- [20260810_SkyCausal当前进展通俗总结.md](20260810_SkyCausal当前进展通俗总结.md)：纠正版总览，区分原始闭环耦合问题、六 profile `T=1` 基线、Two-Stage 机制验证和开放式多轮 solver orchestration 长期目标。
- [20260811_SkyCausal论文实验设计章节结构_在线主实验修正版.md](20260811_SkyCausal论文实验设计章节结构_在线主实验修正版.md)：最新论文实验章节蓝图；将连续物理时钟、提交时重验证和完整在线 episode 设为主实验，将冻结快照降级为预算校准与机制诊断，并重新定义研究问题、对照、指标、统计、Gate、结果章节和工程顺序。
- [20260810_开放式FJSP_MAPF求解器Portfolio前沿调研与架构方案.md](20260810_开放式FJSP_MAPF求解器Portfolio前沿调研与架构方案.md)：审计固定 profile 的封闭点，调研 MAPF algorithm selection、FJSP hyper-heuristic、Dynamic Algorithm Configuration 和 anytime portfolio，并定义面向未来 solver 的 catalog、config schema、`SolverOption`、gray-box racing、准入 Gate 与开放性实验。
- [20260810_开放式Portfolio浅层MCTS综合方案与本轮迭代记录.md](20260810_开放式Portfolio浅层MCTS综合方案与本轮迭代记录.md)：汇总前沿方法借鉴、factorized option generation、short probe、progressive-widening Root MCTS、failure/deadline 语义，并记录本轮采样 v0 代码、测试结果、未完成边界和下一轮 live probe 计划。
- [20260811_开放式求解器元搜索实验评估与复现协议.md](20260811_开放式求解器元搜索实验评估与复现协议.md)：以中文设计机制诊断、主要对照、消融、开放接入、外部方法三级复现、数据隔离、统计门槛和复现产物；其中冻结快照部分已明确降级为辅助实验，在线主结论以上述修正版章节蓝图为准。当前不授权访问确认数据。
- [20260811_开放式SolverCatalog与真实FJSPProbe首轮实现记录.md](20260811_开放式SolverCatalog与真实FJSPProbe首轮实现记录.md)：记录 CP-SAT/DE/PSO manifests、开放 catalog、真实 orchestration probe evaluator、成对 seed 修正、343 项全量回归，以及 `9/9 PASS` 的 immutable historical preflight；新 calibration cohort 仍被协议阻断，不包含质量结论。
- 六 profile `T=1` 正式结果位于 `../artifacts/skycausal_publication_confirmation_v2_1_09760697/`，状态为 `FORMAL_CONFIRMATION_PASS`。该结果是限定候选集下的阶段性基础证据，不代表最终 action space 或完整动态 controller 已完成。
- [20260806_SkyCausal_TwoStageSolverSwitching实验协议.md](20260806_SkyCausal_TwoStageSolverSwitching实验协议.md)：从 `T=1` 静态选择过渡到 progress/budget-aware solver switching 的冻结快照机制协议；不能替代连续物理时钟在线主实验。
- 当前 Two-Stage 基础设施 freeze validation 为 `150/150 PASS`；冻结快照质量 pilot 尚未执行。该机制实验剩余 blocker 是 pilot cohort manifest，但当前更高优先级是连续物理时钟 online episode runner。

## 文件说明

- [20260802_柔性制造实际问题与SkyCausal科研机会调研.md](20260802_柔性制造实际问题与SkyCausal科研机会调研.md)：从多源扰动、交期、维护、质量、数字孪生、BNN、因果推断和离线 RL 等方向审计柔性制造的实际问题，并给出当前系统可执行的主线与实验 Gate。
- [20260802_FJSP_MAPF前沿调研.md](20260802_FJSP_MAPF前沿调研.md)：2023–2026 年 FJSPT、TAPF/MAPF 与生产–路径联合优化的代表工作、方法趋势和研究空白。
- [20260802_项目进展审计与选题优化.md](20260802_项目进展审计与选题优化.md)：结合代码审计和 Docker 生命周期实测，对当前工程成熟度、论文风险和新选题进行评估。
- [20260802_下一阶段推进计划.md](20260802_下一阶段推进计划.md)：围绕数据契约、终止性、MAPF oracle、反证实验、风险预测和预算化重调度的 Gate 式实施方案。
- [20260804_可插拔求解器组合MCTS调度框架可行性调研.md](20260804_可插拔求解器组合MCTS调度框架可行性调研.md)：将研究对象抽象为预算约束的 solver-portfolio 元调度框架，明确 MCTS 只是可替换 `DecisionBackend`，不是系统本身。
- [20260804_DecisionBackend与学习后端演进协议.md](20260804_DecisionBackend与学习后端演进协议.md)：冻结状态、动作、预算、审计和学习后端的替换边界。
- [20260805_严格Deadline与AnytimeMCTS设计方案.md](20260805_严格Deadline与AnytimeMCTS设计方案.md)：区分墙钟停止、solver deadline 与物理 rollout horizon，定义完整 simulation admission、root 配对覆盖、强制取消、fallback 和 MCTS Search Gate。
- [literature_review.md](literature_review.md)：截至 2026-07-12 的相关领域论文调研与研究空白分析。
- [paper_positioning.md](paper_positioning.md)：论文主线、创新点表述、贡献边界和建议的论文结构。
- [experiment_plan.md](experiment_plan.md)：从最小可运行环境到完整消融实验的实施计划。

## 2026-08-02 阶段判断（历史）

现有工作已经较充分地研究了 FJSP、FJSPT、FJSP-AGV 和动态车间调度。2025–2026 年又出现了 ACES、DQN+PBS 和 CP-FJSPT-H 等更接近生产–路径联合优化的工作，因此 SkyEngine 不能再依赖“首次闭环联合环境”或普通 AGV 分配 RL 作为核心创新。

截至 2026-08-02，项目保留“受限 MAPF 查询预算下的风险感知闭环滚动 FJSP 调度”作为第一阶段核心验证，并将完整科研边界扩展为“多源扰动下的因果风险感知柔性制造恢复决策”。论文能否成立的关键证据是：显式路径执行或机器、AGV、路网、加工时长和急单扰动是否跨层改变生产结果，以及系统能否在相同计算和计划变更预算下正确选择路径修复、AGV 重分配、局部排程修复或联合重调度。

本次 Docker 生命周期实测为 `530/532 PASS`，但 500 步内只完成 `8/10` 个 Job 和 `46/50` 道 Operation。当前应先修复数据契约、CPU/GPU profile、episode 终止性和指标有效性，再接入可识别的 MAPF oracle 并运行反证实验；多专家蒸馏和 GRPO 暂不作为论文主线。
