# FJSP–AGV/MAPF 联合调度领域调研

**调研日期：2026-07-12**

## 1. 调研范围

本次调研覆盖四个相互关联的方向：

1. FJSP/FJSPT/FJSP-AGV 的联合调度与运输约束；
2. 面向动态扰动的强化学习和多智能体强化学习调度；
3. 图神经网络、Transformer、离线强化学习和学习引导优化；
4. 模仿学习、多策略/多专家融合与滚动执行。

## 2. 代表性近期工作

### 2.1 FJSPT 与 AGV 联合决策

[Learning-enabled Flexible Job-shop Scheduling for Scalable Smart Manufacturing](https://arxiv.org/abs/2402.08979)（2024）提出 Heterogeneous Graph Scheduler，将工序、机器和车辆建模为异构图节点，重点解决 DRL 在训练规模外的泛化问题。其启示是 SkyEngine 的观测接口应保留 operation–machine–AGV–route 的关系结构，而不是把所有对象压成固定长度向量。

[A Multi-Agent Deep Reinforcement Learning for Flexible Job Shop Scheduling Problem with Transportation](https://link.springer.com/chapter/10.1007/978-3-032-00284-6_7)（2025）将 FJSPT 拆分为工序选择、机器选择和 AGV 选择，并使用图注意力表达车间状态。其难点仍主要是组合动作空间和训练稳定性，路径执行层面的碰撞反馈不是核心贡献。

[A cooperative agent deep reinforcement learning framework for solving flexible job shop scheduling problem with automated guided vehicles](https://doi.org/10.1016/j.eswa.2025.128142)（2025）进一步采用协作多智能体 DRL 处理 AGV 选择、工序排序和机器选择。它代表了“把运输资源纳入联合决策”的主流路线，但需要重点比较其运输建模是显式路径仿真，还是以运输时间/资源约束代替路径执行。

[Deep reinforcement learning for solving efficient and energy-saving flexible job shop scheduling problem with multi-AGV](https://www.sciencedirect.com/science/article/abs/pii/S0305054825001157)（2025）表明多 AGV、效率和能耗的多目标优化仍是活跃方向。SkyEngine 可以吸收其多目标评价方式，但需避免将贡献表述成单纯的多目标奖励设计。

### 2.2 动态调度与闭环反馈

[Dynamic scheduling for flexible job shop based on MachineRank algorithm and reinforcement learning](https://www.nature.com/articles/s41598-024-79593-8)（2024）将新工件、机器故障、加工时间变化和不确定 AGV 运输时间纳入动态调度，并使用 D3QN 选择调度规则。它说明“动态事件 + AGV 状态”已经被纳入 FJSP 研究，但更多是把运输不确定性作为状态或时间扰动，而不是让路径冲突结果真实地改变后续可行动作。

[Dynamic flexible job shop scheduling based on deep reinforcement learning](https://doi.org/10.1177/09544054241272855)（2024/2025）面向随机到达的动态 FJSP，采用事件触发式 MDP 进行在线决策。对 SkyEngine 的直接启示是应采用事件驱动决策点，而非每个仿真时间步都要求 Assigner 做动作。

[Multi-agent reinforcement learning for flexible shop scheduling problem: a survey](https://doi.org/10.3389/fieng.2025.1611512)（2025）总结了 FSSP 中 MARL 的集中训练/分散执行、协作机制、状态空间和扰动处理。该综述也反映出当前研究的普遍问题：实验环境、状态定义和评价指标差异较大，跨方法复现实验困难。因此，SkyEngine 的可插拔接口和固定评测协议本身可以作为论文贡献的一部分，但必须提供足够的基线和公开配置。

### 2.3 图表示、离线学习与学习引导优化

[Offline reinforcement learning for job-shop scheduling problems](https://arxiv.org/abs/2410.15714)（2024）使用异构图和可变动作空间，试图同时利用专家模仿和回报优化，针对在线 DRL 样本效率低、行为克隆泛化差的问题。它与 SkyEngine 的多专家数据生成方向高度相关，提示实验中应加入行为克隆、离线 RL 或“专家数据 + 在线修正”的对照。

[Learning-guided Rolling Horizon Optimization for Long-Horizon Flexible Job-Shop Scheduling](https://openreview.net/forum?id=Aly68Y5Es0)（ICLR 2025）用学习模型决定滚动时域中哪些变量可以固定，减少重复优化。这个方向说明论文不必把所有决策都交给神经策略；更稳妥的方案是让学习器负责排序/分配，保留 MAPF 或局部优化器负责可行性。

[Leveraging Constraint Programming in a Deep Learning Approach for Dynamically Solving the Flexible Job-Shop Scheduling Problem](https://arxiv.org/abs/2403.09249)（2024）将约束规划与深度学习结合，用高质量解监督网络并在问题缩小时交给 CP 求精。它支持 SkyEngine 采用“学习 Assigner + 可行性校验/局部修复”的混合架构，而不是声称端到端网络独立解决所有约束。

[RESCHED: Rethinking Flexible Job Shop Scheduling from a Transformer-Based Architecture with Simplified States](https://openreview.net/forum?id=s5pWbwf2tk)（ICLR 2026）强调简化状态和 Transformer 的规模泛化，说明“特征越多越好”并不是可靠的创新点。SkyEngine 的 17 项指标应区分为评估指标与输入特征，避免将所有统计量直接喂给模型造成信息泄漏或过拟合。

[Towards Generalizable Multi-Policy Optimization with Self-Evolution for Job Scheduling](https://openreview.net/forum?id=VPm6afl0Sc)（NeurIPS 2025）研究共享网络下的多策略优化和自适应模仿强度。它与“多专家融合”存在概念邻近关系，因此 SkyEngine 的创新不能只写成“多个专家加权平均”；必须突出专家来自不同 FJSP/MAPF 求解器、可靠性由闭环 rollout 结果估计，并且融合权重随状态和拥堵变化。

## 3. 当前领域共识与不足

### 已经比较拥挤的贡献

- 使用 PPO、DQN 或 MARL 解决 FJSP；
- 使用 GNN/GAT/Transformer 表示工序、机器和 AGV；
- 将 AGV 数量、运输时间、能耗或机器故障加入目标函数；
- 在标准 FJSP/FJSPT benchmark 上报告 makespan 优于若干启发式规则。

单独做这些内容很难形成有说服力的新颖性。

### SkyEngine 可以切入的空白

1. **路径执行层闭环**：调度动作产生运输请求，MAPF 真实执行后返回等待、冲突、绕行、阻塞、死锁等事件，这些事件直接改变机器/工件的释放时间和下一决策可行域。
2. **算法组合泛化**：把 FJSP 求解器和 MAPF 求解器作为可插拔专家/环境组件，研究 Assigner 是否能跨组合迁移，而不是只在单一算法上调参。
3. **状态依赖的专家可信度**：不同专家在低拥堵、高拥堵、窄通道和长距离运输等状态下表现不同，融合权重应该由相对 rollout 结果估计，而不是固定权重。
4. **面向耦合的评测**：除 makespan 外，报告运输等待占比、机器饥饿、AGV 空载率、冲突次数、阻塞传播长度、重调度次数和可行率，证明收益来自耦合建模而非奖励函数投机。

## 4. 对论文定位的建议

推荐定位为：

> A reproducible closed-loop co-simulation environment and state-dependent multi-expert assigner for FJSP–MAPF joint scheduling.

不建议定位为“首个 FJSP-AGV 联合强化学习方法”，因为 2024–2025 年已有多篇 FJSPT/FJSP-AGV DRL/MARL 工作。更稳妥的表述是：现有工作多在调度层联合考虑运输资源，SkyEngine 将路径可行性和执行反馈提升为显式环境状态，并研究跨求解器组合的学习型任务分配。

## 5. 需要特别避免的风险

- 把“闭环”写在摘要里，但环境实际上只使用静态距离矩阵；
- 把 GRPO 作为名称而没有明确 group、优势估计、策略更新和与 PPO 的区别；
- 只和简单规则比较，不和最强的单专家、联合优化或 OR-Tools/CP 基线比较；
- 只报告平均 makespan，不报告不同随机种子、实例规模、拥堵强度和失败/不可行 episode；
- 用同一批实例生成专家、训练模型和测试模型，导致泛化结论失效。

## 6. 建议优先阅读顺序

1. HGS：确定异构图状态和规模泛化基线；
2. Offline RL for JSS：确定专家数据、行为克隆和离线学习对照；
3. L-RHO：理解学习与传统优化器协作的稳健方式；
4. 2025 FJSP-AGV/MARL 工作：整理联合决策基线；
5. RESCHED 和多策略优化：避免重复已有的 Transformer/多策略贡献。
