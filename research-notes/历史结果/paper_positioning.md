# 论文写作与创新点定位建议

## 1. 建议论文主线

论文最好围绕一个核心问题展开：

> 当 FJSP 的调度决定会产生一组真实的 AGV 路径需求，而路径冲突又会反向改变工件释放和机器可用时间时，固定的调度–运输接口是否仍然有效？能否学习一个 Assigner，根据当前闭环状态选择或融合不同专家的分配策略？

对应的论文逻辑是：

**解耦方法的损失 → 闭环环境建模 → 多专家 Assigner → 跨组合实验验证。**

## 2. 建议保留的三个创新点

### 创新点一：面向 FJSP-MAPF 的闭环联合仿真环境

贡献重点不是“又一个 Gym 环境”，而是明确给出事件语义和反馈链：

`operation/machine decision → transport request → task-to-AGV assignment → collision-aware MAPF → execution events → release/machine state update`

最低实现要求：路径冲突、等待和绕行必须影响实际到达时间；到达时间必须影响后续操作可行动作，而不是只作为日志指标。

### 创新点二：状态依赖的多专家在线蒸馏 Assigner

建议把不同 FJSP 规则、FJSP 求解器或 MAPF 求解器看作具有不同偏好的专家。对同一 student-induced state，让多个专家产生候选分配，短 rollout 或完整 episode 评估相对收益，再估计可靠性权重。

更严谨的表述可以是：

> state-dependent reliability-weighted multi-expert online distillation with rollout-relative supervision.

如果继续使用 GRPO 名称，需要在方法中严格定义 group 内候选动作、相对回报、优势归一化和策略更新；否则建议写成“group-relative policy update”，避免和已有 GRPO 术语产生不必要争议。

### 创新点三：跨算法组合和拥堵强度的泛化验证

将训练和测试拆成不同维度：

- 训练过的 FJSP × MAPF 组合；
- 未见过的 FJSP × MAPF 组合；
- 未见过的车间规模；
- 未见过的 AGV 数量和拥堵强度；
- 发生故障、随机到达或路径阻塞的动态场景。

该创新点本质上是实验性贡献，必须用严格的组合留出实验支撑。

## 3. 推荐论文结构

1. Introduction：提出解耦接口导致的三类耦合损失。
2. Related Work：FJSPT/FJSP-AGV、MAPF/制造运输、神经调度、模仿/离线 RL。
3. Problem Formulation：定义车间图、工序状态、机器状态、AGV 状态、运输任务和事件驱动 MDP。
4. SkyEngine：环境状态、动作、转移、碰撞处理、阻塞反馈和指标。
5. Multi-Expert Assigner：候选动作、student-induced states、专家可靠性、融合和策略更新。
6. Experimental Setup：实例、算法组合、基线、随机种子、训练/测试拆分。
7. Results：总体结果、闭环有效性、专家融合、规模/拥堵/动态泛化。
8. Ablation and Limitations：去掉路径反馈、固定权重、单专家、无 rollout、无修复器等。
9. Conclusion。

## 4. 核心假设与可证伪性

论文应明确写出以下可证伪假设：

- H1：显式路径执行反馈相对于静态运输时间能降低耦合损失。
- H2：状态依赖的专家融合相对于固定权重或单专家在不同拥堵状态下更稳定。
- H3：在训练规模和算法组合外，闭环 Assigner 仍保持较小性能退化。
- H4：收益主要来自减少阻塞/等待，而非单纯增加计算预算。

每个假设都应对应一组对照实验，不要只在结论中定性描述。
