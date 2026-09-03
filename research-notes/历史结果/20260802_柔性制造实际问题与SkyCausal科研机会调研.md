# 柔性制造实际问题、前沿进展与 SkyCausal 科研机会调研

**调研日期：2026-08-02**

## 1. 结论

只研究 FJSP 与 MAPF 的联合求解还不够完整。它解决的是柔性制造中的一个重要
执行耦合问题，但真实车间还持续受到急单、加工时间波动、设备故障、运输设备
故障、临时封路、维护资源、质量返工和交期压力影响。

结合 2025-2026 年文献与当前代码能力，建议把项目扩展为以下总问题：

> **多源扰动下的因果风险感知柔性制造恢复决策：在有限计算与调整预算下，
> 判断何时采取何种粒度的路径、运输和生产重调度干预，以改善交期可靠性、
> 终端产出和系统稳定性。**

推荐英文表述：

> **Causal and Risk-Aware Recovery for Flexible Manufacturing under
> Multi-Source Disruptions**

这不是放弃 FJSP-MAPF，而是把它放回真实制造问题中：

- FJSP 决定机器、工序与生产节奏；
- MAPF 决定物料搬运能否按计划执行；
- 扰动改变生产资源和物流资源的可用性；
- 恢复策略选择不干预、局部路径修复、AGV 重分配、局部排程修复或联合重调度；
- 研究目标从静态 makespan 扩展为交期、尾部风险、恢复成本和计划稳定性。

当前最值得立即验证的主线是：

> **机器、AGV、路网、加工时长和急单等多源扰动下，学习干预时机与干预范围。**

两个后续扩展课题是：

1. **不确定执行条件下的急单接受、交期承诺与资源预留；**
2. **面向机器退化的生产-运输-维护联合决策。**

质量返工、能耗、人员技能与人体工学具有现实价值，但当前系统缺少相应状态和
动作，不应与主线同时展开。

## 2. 调研边界与证据口径

本报告重点核验：

- 2025-2026 年动态柔性车间、韧性生产、维护、质量、绿色制造和学习调度；
- 与当前 SkyEngine、SkyEngine-FJSP、SkyEngine-MAPF 可执行能力的对应关系；
- 贝叶斯网络、贝叶斯神经网络、因果推断和前沿 RL 的适用条件；
- 可在现有系统上形成可证伪实验的问题，而不是只做概念性技术组合。

证据成熟度分为：

- **已发表期刊/会议**：可用于确认研究方向和最近邻工作；
- **预印本**：用于识别趋势，不作为“领域已经证明”的唯一依据；
- **当前代码能力**：以源码和已有测试为准；
- **待实现设想**：不得写成已有系统能力。

## 3. 柔性制造最新进展

### 3.1 从静态排程转向多状态、动态和韧性排程

2025 年 Computers & Industrial Engineering 的多类型数据框架将设备班次、
设备可用性、故障、维护、返工和插单统一表示为状态约束，并在航空发动机加工
车间验证。这说明实际问题的关键已从“再设计一个优化器”转向“如何把异构生产
状态稳定地接入优化器”：

- Siyang Ji, Zipeng Wang, Jihong Yan,
  *A Multi-Type data driven framework for solving flexible job shop scheduling
  problem considering multiple production resource states*,
  CIE 2025.
  DOI: [10.1016/j.cie.2024.110835](https://doi.org/10.1016/j.cie.2024.110835)

2025 年 IEEE Access 进一步发布了来自柔性包装制造的动态 FJSP 数据，包含
机器能力、优先级、换型时间、加工速度、路径柔性和非计划停机。其意义不只在
算法结果，而在于真实数据、滚动时域和事件驱动评估正在成为研究可信度要求：

- Masmur Tarigan et al.,
  *Advancing Dynamic Flexible Job Shop Scheduling With a Real-World Dataset
  and Genetic Adaptive Scheduling System*,
  IEEE Access 2025.
  DOI: [10.1109/ACCESS.2025.3630184](https://doi.org/10.1109/ACCESS.2025.3630184)

对本项目的含义：

- 单一 `J10P5M6 + maze` 只能做系统预验证；
- 正式研究需要多 FJSP、多个地图、不同 AGV 数和多种扰动；
- 需要保留事件日志、计划修订、恢复动作和终端结果的完整可追溯链。

### 3.2 从“发生故障就全量重排”转向触发时机与修复范围

频繁重排会产生 schedule nervousness，即计划频繁变化导致现场准备、物料、
人员和外部承诺被反复打乱。2025 年多触发研究已经开始同时决定“何时重排”和
“在哪里重排”，避免过度重排和不足重排：

- Rong Duan et al.,
  *A Multi-Trigger Mechanism Design for Rescheduling Decision Assistance in
  Smart Job Shops Based on Machine Learning*,
  Sustainability 2025.
  DOI: [10.3390/su17052198](https://doi.org/10.3390/su17052198)

2025 年 CIE 的 schedule repair 工作则直接用 DRL 研究机器故障后的局部计划
修复：

- Lingling Lv et al.,
  *Schedule repair for flexible job shops under machine breakdowns by deep
  reinforcement learning*,
  CIE 2025.
  DOI: [10.1016/j.cie.2025.111256](https://doi.org/10.1016/j.cie.2025.111256)

对本项目的含义：

- 研究动作不能只有 `query / no query`；
- 应明确干预层级和作用范围；
- 必须把计划稳定性、重调度耗时和现场调整次数纳入目标。

本项目据此统一定义“恢复等级 0-4”：

- 恢复等级 0：no-response / neglect；
- 恢复等级 1：route repair / replanning；
- 恢复等级 2：transport reassignment；
- 恢复等级 3：schedule repair / partial rescheduling；
- 恢复等级 4：full / joint rescheduling。

历史实验标签 `U0-U3` 只用于兼容旧结果。新报告不再使用单字母恢复等级编号。

### 3.3 生产、运输、维护和质量正在走向联合优化

2025 年 CIE 已研究 AGV 随机故障下的动态柔性车间，并联合考虑多站点设备
维护与能源/满意度目标：

- Liuran Lu et al.,
  *Integrated optimization of dynamic flexible job shop scheduling with AGV
  breakdowns and multi-site equipment maintenance on the demand side*,
  CIE 2025.
  DOI: [10.1016/j.cie.2025.111361](https://doi.org/10.1016/j.cie.2025.111361)

2025 年 IET 工作把机器退化、突发故障和有限维护资源放入动态 FJSP，并使用
DQN 选择维护插入：

- Nanxing Chen et al.,
  *A Novel DQN-Based Hybrid Algorithm for Integrated Scheduling and Machine
  Maintenance in Dynamic Flexible Job Shops*,
  IET Collaborative Intelligent Manufacturing 2025.
  DOI: [10.1049/cim2.70028](https://doi.org/10.1049/cim2.70028)

2025 年 IJPR 工作进一步联合生产调度、维护和质量控制，显示仅优化生产计划
会忽略设备可用性、质量损失和延期成本之间的依赖：

- Azam Kheyri, Sharareh Taghipour,
  *Integrated optimisation of production scheduling, maintenance, and quality
  control under non-homogeneous Poisson process failures with multiple
  assignable causes*,
  IJPR 2025.
  DOI: [10.1080/00207543.2025.2543492](https://doi.org/10.1080/00207543.2025.2543492)

2026 年质量驱动工作将加工、检测和可选返工形成闭环，并以概率方式处理质量
不确定性：

- Zhiyong Luo et al.,
  *Quality-driven multi-stage dynamic scheduling optimization for flexible
  manufacturing via digital twin with integrated rework mechanism*,
  2026.
  DOI: [10.1177/01423312261442257](https://doi.org/10.1177/01423312261442257)

对本项目的含义：

- “生产与物流联合”仍有价值，但已不是最终边界；
- 更强的问题是不同资源层扰动如何传播，以及哪种跨层干预最有效；
- 维护和质量适合作为主线验证后再增加的机制，不能先堆入系统。

### 3.4 数字孪生的研究重点转向预测、反事实评估和动态重构

2025 年 T-ASE 的动态产线重构工作用数字孪生监测扰动、能力本体生成候选配置，
再通过快速仿真评估恢复方案：

- Bo Fu et al.,
  *Digital Twin-based Smart Manufacturing: Dynamic Line Reconfiguration for
  Disturbance Handling*,
  IEEE T-ASE 2025.
  DOI: [10.1109/TASE.2025.3563320](https://doi.org/10.1109/TASE.2025.3563320)

2025 年模块化制造研究则按工作站、工艺路线和系统三个层级设计响应策略：

- Lei Liu et al.,
  *Multi-level dynamics response-based resilient production control for
  digital twin-enabled modular manufacturing systems*,
  IJCIM 2025.
  DOI: [10.1080/0951192X.2025.2563255](https://doi.org/10.1080/0951192X.2025.2563255)

SkyEngine 当前更准确的学术定位应是**可干预的事件级数字孪生实验环境**，
而不是宣称拥有完整工业数字孪生。它具备状态演化、事件注入、日志和求解器
闭环，但尚未接入真实传感器、MES/ERP 和设备能力本体。

### 3.5 从期望性能转向尾部风险、不确定性和 OOD 可靠性

随机加工时间下，仅优化名义 makespan 会得到脆弱计划。随机 FJSP 的神经组合
优化研究已显式采样加工时间场景，并优化期望 makespan 或 VaR：

- Igor G. Smit et al.,
  *Neural Combinatorial Optimization for Stochastic Flexible Job Shop
  Scheduling Problems*,
  arXiv:2412.14052.
  [论文与代码](https://arxiv.org/abs/2412.14052)

2025 年 BNN 制造研究将 epistemic、aleatoric 和 OOD 不确定性同时用于装配
质量预测，并输出区间和特征贡献：

- Jie Wu et al.,
  *Uncertainty-aware Bayesian neural network with SHAP interpretability for
  data-driven assembly quality prediction in complex manufacturing systems*,
  Advanced Engineering Informatics 2025/2026.
  DOI: [10.1016/j.aei.2025.103730](https://doi.org/10.1016/j.aei.2025.103730)

对本项目的含义：

- BNN 的价值是可信区间、数据不足和 OOD 保守决策，不是自动获得因果性；
- 主指标应增加 P90/P95、CVaR、交期违约率和校准误差；
- 必须测试未见 FJSP、地图、AGV 数、扰动组合和强度。

### 3.6 RL 从在线试错转向离线、分布式价值和可解释规则组合

2025 年离线 RL 工作表明，调度策略可以从历史求解和执行日志学习，不必在真实
车间在线试错；分位数 critic 还能学习回报分布：

- Jesse van Remmerden et al.,
  *Generalizing Beyond Suboptimality: Offline Reinforcement Learning Learns
  Effective Scheduling through Random Data*,
  arXiv:2509.10303.
  [论文](https://arxiv.org/abs/2509.10303)

2026 年 DSevolve 预印本提出离线演化可解释规则组合，在线用轻量 probe 对当前
车间做指纹并选择规则。这一趋势与 SkyEngine 已有 counterfactual probe 很接近：

- Jin Huang et al.,
  *DSevolve: Enabling Real-Time Adaptive Scheduling on Dynamic Shop Floor with
  LLM-Evolved Heuristic Portfolios*,
  arXiv:2603.27628.
  [论文](https://arxiv.org/abs/2603.27628)

这些结果不说明“必须使用 RL 或 LLM”。相反，它们提高了基线要求：

- learned policy 必须超过固定阈值、周期策略和可解释启发式；
- 端到端神经策略必须证明 OOD、实时性和约束可行性；
- LLM 更适合离线生成可审计规则，不适合直接进入毫秒级安全控制回路。

### 3.7 贝叶斯与因果方法正在从预测走向干预

2026 年两层贝叶斯网络工作把局部故障、返工和加工波动映射到工序延期，再沿
前序和机器约束传播到系统层：

- Yingying Zhu et al.,
  *Spatiotemporal dual dimensional disturbance perception and Bayesian
  quantitative assessment method for flexible job shop scheduling*,
  Digital Twin 2026.
  DOI: [10.1080/27525783.2026.2690864](https://doi.org/10.1080/27525783.2026.2690864)

2025 年贝叶斯动态调度预印本根据新观测更新扰动后验，并兼顾长期成本与
schedule nervousness：

- Taicheng Zheng et al.,
  *Bayesian dynamic scheduling of multipurpose batch processes under incomplete
  look-ahead information*,
  arXiv:2512.01093.
  [论文](https://arxiv.org/abs/2512.01093)

因果制造也开始从“解释故障”转向“估计措施效果”。2026 年 PriMa-Causa
预印本用干预效应对维护措施排序，AAAI 2026 IAAI 的 CausalTrace 则结合本体、
因果发现、反事实和根因分析：

- Felix Saretzky et al.,
  *Integrating a Causal Foundation Model into a Prescriptive Maintenance
  Framework for Optimising Production-Line OEE*,
  arXiv:2512.00969.
- Chathurangi Shyalika et al.,
  *CausalTrace: A Neurosymbolic Causal Analysis Agent for Smart Manufacturing*,
  AAAI 2026 IAAI, arXiv:2510.12033.

对本项目的含义：

- 仅使用 BN 预测扰动传播已不足以形成强创新；
- 可形成差异的是显式物流冲突、可执行干预、已知 propensity、终端反事实和
  有限预算；
- 仿真环境能随机化干预并复用相同外生随机数，因此比纯观察工厂日志更适合
  建立因果识别的 ground truth。

## 4. 当前系统能力审计

### 4.1 已具备，可直接用于实验

| 能力 | 当前事实 | 可支持的问题 |
|---|---|---|
| FJSP 求解 | CP-SAT、DE、PSO、DRL 和规则求解 | 机器选择、工序排序、排程修复基线 |
| MAPF 执行 | EECBS、PBS、MAPF-LNS2、LaCAM3、LG-LaCAM 等 | 显式路径冲突、查询成本、求解失败 |
| 事件级生产物流闭环 | 工序释放、运输、到机、加工和下一工序释放 | 端到端 makespan 与延迟传播 |
| 机器故障 | 计划事件或概率事件，支持维修后恢复 | 设备停机与恢复策略 |
| AGV 故障 | 计划事件或概率事件，故障期间不可分配 | 运输资源失效与重分配 |
| 临时路障 | 可配置持续时间并保持地图连通性 | 路网阻断、动态绕行与 MAPF 重规划 |
| 加工时间随机性 | 全局、机器级、工序级多种分布 | 风险排程、尾部交期和校准 |
| 急单插入 | 优先级、交期、候选机器、重规划和阶段跟踪 | 急单响应、交期承诺和计划稳定性 |
| 状态保存/恢复 | 生产、AGV、网格和事件状态可序列化 | paired counterfactual rollout |
| 查询与事件日志 | MAPF query、失败类型、事件和 terminal 指标 | 干预数据集、因果效果和成本统计 |

### 4.2 已有但需要补强

1. **急单能力第一版只支持 `PSO + nearest`。**  
   需要把重规划接口推广到其它 JobSolver、Assigner 和 RouteSolver 组合。

2. **交期字段存在，但正式 tardiness 指标仍主要位于 legacy monitor。**  
   需要把 total weighted tardiness、on-time delivery 和违约率纳入主指标。

3. **状态保存/恢复尚未形成完整反事实 API。**  
   需要同时保存求解器缓存、随机数状态、异常注入器状态和动作日志，保证不同
   干预共享同一组外生扰动。

4. **现有 query probe 主要比较 MAPF refinement。**  
   需要扩展到 AGV 重分配、局部 schedule repair 和联合重调度。

5. **异常是离散停机或路障。**  
   机器退化、故障风险随负载累积、维护动作和有限维修人员尚未建模。

6. **在线 FJSP 仍缺少可回放的计划版本链。**  
   后续不把调度固定为单一初始序列，而是维护初始计划、第 1 次计划修订、第 2
   次计划修订等版本；任意扰动时刻可从当前剩余问题触发局部排程修复或联合完全
   重调度，并将输入、冻结范围、solver/image/seed、输出计划和 hash 保存为
   `PlanRevision`。这样可同时保留在线重调度能力和 paired counterfactual replay。

### 4.3 当前不具备，不应直接宣称

- 产品质量、检测、返工概率和报废；
- 机器能耗曲线、分时电价和碳强度；
- 人员技能、班次、疲劳和人机协作；
- 原料短缺、供应商到货和跨工厂协同；
- 真实设备传感器、MES/ERP 闭环和工业部署；
- 机器健康退化状态、维护动作、备件与维修人员；
- 已验证的 BNN、CATE、DR/AIPW 或离线 RL 端到端收益。

## 5. 问题-方法-系统映射

| 实际问题 | 工业目标 | 当前可做程度 | 推荐方法 | 优先级 |
|---|---|---:|---|---:|
| 多源扰动后的恢复动作选择 | 恢复交付、减少停机与频繁重排 | 高 | BN/BNN + CATE + 分层干预 | P0 |
| 急单接受与交期承诺 | OTD、违约成本、客户服务水平 | 高 | 校准概率/BNN + robust optimization | P1 |
| 有限计算预算下的滚动决策 | 实时性与质量权衡 | 高 | myopic/knapsack，再验证 offline RL | P0 |
| 机器故障与 AGV/路网联动 | 防止局部故障跨层放大 | 高 | 因果传播图 + paired rollout | P0 |
| 随机加工与运输时间 | 交期尾部风险和保守调度 | 高 | quantile、CVaR、deep ensemble/BNN | P0 |
| 生产-维护联合优化 | 可用率、维护成本、交期 | 中 | 退化模型 + prescriptive maintenance | P1 |
| 质量检测与返工闭环 | 一次通过率、质量成本 | 低 | BNN 质量预测 + 因果工艺干预 | P2 |
| 能源/碳感知生产物流 | 电费、峰值功率、碳排 | 低 | 多目标优化或 constrained RL | P2 |
| 人机协作与人员技能 | 安全、疲劳、技能匹配 | 很低 | HRC 调度/MARL | 暂缓 |
| 动态产线布局重构 | 吞吐恢复、设备重配置 | 很低 | 数字孪生 + 配置优化 | 暂缓 |

## 6. 推荐主线：多源扰动下的因果分层恢复

### 6.1 研究问题

在时刻 \(t\)，系统观察到状态 \(X_t\) 和扰动历史 \(H_t\)，可选择：

\[
U_t \in
\{
u_0:\text{不干预},
u_1:\text{路径修复},
u_2:\text{AGV重分配},
u_3:\text{局部排程修复},
u_4:\text{联合重调度}
\}.
\]

每个动作有不同的计算成本、执行调整成本和未来收益。目标是在预算约束下最小化：

\[
\mathbb{E}[
C_{\max}
+ \lambda_1 TWT
+ \lambda_2 N_{\text{change}}
+ \lambda_3 C_{\text{compute}}
]
+ \rho\operatorname{CVaR}_{\alpha}(TWT),
\]

其中：

- \(TWT\) 为总加权延期；
- \(N_{\text{change}}\) 为计划变化或现场调整量；
- \(C_{\text{compute}}\) 为 MAPF、重分配和重调度求解成本；
- CVaR 衡量尾部交期风险。

核心问题不是预测“是否会延期”，而是估计：

\[
\tau_u(x)=
\mathbb{E}[Y(u)-Y(u_0)\mid X=x],
\]

即在当前状态采用恢复动作 \(u\) 相对不干预的条件因果收益。

### 6.2 与最近邻工作的差异

| 最近邻 | 已解决 | 本项目需要新增 |
|---|---|---|
| 两层 BN FJSP 2026 | 扰动概率与延期传播 | 显式 MAPF、可执行干预、终端因果效果 |
| Multi-trigger 2025 | 何时、在哪里重排 | 多动作效应、预算、校准不确定性 |
| CIE AGV breakdown 2025 | AGV 故障与 FJSPT/维护 | 路径冲突、在线多源扰动、恢复层级 |
| Schedule repair DRL 2025 | 机器故障后的计划修复 | 生产-物流联动、反事实识别、OOD |
| DSevolve 2026 预印本 | probe 选可解释调度规则 | 跨层干预、因果收益和资源预算 |
| 当前 SkyCausal | 是否查询/优化 MAPF | 多源扰动与多粒度恢复动作 |

### 6.3 建议的方法结构

#### 层 1：机制约束的动态贝叶斯图

不做无约束结构发现。用已知机制固定：

\[
\text{扰动}
\rightarrow \text{资源可用性/路径冲突}
\rightarrow \text{运输或加工延迟}
\rightarrow \text{机器饥饿/关键路径}
\rightarrow \text{交期与 makespan}.
\]

BN/DBN 负责概率传播和缺失观测下的后验更新。

#### 层 2：校准的不确定性模型

先比较：

1. 分位数 LightGBM/MLP；
2. Deep Ensemble；
3. MC Dropout；
4. 轻量 BNN。

只有 BNN 在 held-out FJSP/地图/扰动上同时改善 NLL、coverage、ECE 和最终策略
效用时，才保留 BNN 作为贡献。否则 Deep Ensemble 更简单可靠。

区分：

- aleatoric uncertainty：扰动和加工/运输本身随机；
- epistemic uncertainty：未见实例、地图或扰动组合导致知识不足。

前者用于 CVaR，后者用于保守回退到强求解器或人工规则。

#### 层 3：因果干预效应

在仿真中随机化恢复动作，记录已知 propensity。比较：

- outcome regression；
- IPW；
- AIPW / Doubly Robust learner；
- causal forest 或 DR learner；
- 非因果 MLP trigger。

以状态时刻为 treatment unit，避免错误假设多工件、多 AGV 之间互不干扰。

#### 层 4：预算策略

按以下顺序验证复杂度：

1. 固定阈值；
2. 估计效用最大的 myopic policy；
3. 有限预算 knapsack / dynamic programming；
4. contextual bandit；
5. conservative distributional offline RL。

只有动作改变未来状态、预算机会成本明显且前 3 类方法不足时，才进入 RL。
不建议从 PPO/GRPO 起步。

## 7. 两个扩展课题

### 7.1 急单接受、交期承诺与资源预留

实际问题：

> 新订单到达时，系统应接受、拒绝、承诺何种交期，是否预留机器和 AGV
> 能力，才能在未知未来扰动下控制违约风险？

动作可以是：

- 接受/拒绝；
- 报价交期；
- 优先级；
- 预留机器、AGV 或 MAPF/重调度预算。

主指标：

- on-time delivery rate；
- total weighted tardiness；
- 接单收益减违约成本；
- 原有订单受影响程度；
- 交期区间覆盖率和宽度。

推荐先用 conformal prediction、分位数模型或 BNN 输出完成时间分布，再做
chance-constrained acceptance。该课题工业叙事强、增量实现较小，适合成为
主线后的独立论文或应用章节。

### 7.2 生产-运输-维护联合决策

实际问题：

> 机器健康逐步退化时，应何时维护、把工件迁移到哪台机器、如何调整运输，
> 才能避免故障造成的生产与物流级联损失？

需要新增：

- 随负载、加工时长和速度演化的 health/RUL；
- preventive/corrective maintenance 动作；
- 维护时长、成本、备件和维修人员容量；
- 维护前后的故障概率与加工质量影响。

推荐方法：

- Weibull/NHPP 或半马尔可夫退化基线；
- BNN/深度生存模型给出 RUL 不确定性；
- 因果方法评估维护动作对 OEE、交期和故障率的效果；
- 预算化离线 RL 仅用于多步维护-生产联动。

该方向价值高，但比 P0 多一个完整资源层，应在主线稳定后进入。

## 8. 实验设计

### 8.1 基准因子

生产维度：

- Brandimarte、Hurink、Kacem、Fattahi 等多个 family；
- job/machine 规模；
- 柔性度、机器负载不均衡、交期紧迫度；
- 正常订单与急单到达率。

物流维度：

- maze、warehouse、open、bottleneck 等地图；
- AGV 数、任务密度、dock 冲突率；
- EECBS、LaCAM3、LG-LaCAM 等强求解器。

扰动维度：

- 机器故障频率与维修时长；
- AGV 故障频率与维修时长；
- 临时路障频率与持续时间；
- 加工时间分布与方差；
- 急单到达率、优先级与交期；
- 单一、并发和链式扰动。

### 8.2 干预基线

1. `No-response`：只让环境自然恢复；
2. `Always-full`：每次事件都联合重调度；
3. `Periodic`：固定周期重调度；
4. `Single-threshold`：固定延期或拥堵阈值；
5. `Multi-trigger`：按事件类型和影响范围选择动作；
6. `Predictive gate`：普通监督模型；
7. `Uncertainty-aware gate`：BNN/ensemble；
8. `Causal myopic`：按估计 CATE 选择动作；
9. `Budgeted causal policy`：预算条件化长期策略；
10. `Outcome oracle`：从同状态分叉所有动作，作为仿真上界。

### 8.3 主指标

终端生产指标：

- episode 完成率；
- capped makespan；
- total/mean/max weighted tardiness；
- on-time delivery rate；
- throughput。

韧性指标：

- 扰动后性能最低点；
- time-to-recover；
- resilience triangle / cumulative performance loss；
- 级联影响工序和 Job 数。

干预代价：

- MAPF 查询与总求解时间；
- 重分配、局部修复和全局重排次数；
- 计划变更的工序数、机器数和开始时间偏移；
- schedule nervousness。

模型指标：

- NLL、Brier、ECE；
- P50/P90 coverage 与 interval width；
- CATE bias、PEHE 和 policy value；
- OOD detection AUROC；
- CVaR 和 worst-group performance。

### 8.4 因果 ground truth

建议利用已有状态序列化能力构造 paired rollout：

1. 在决策时刻冻结完整环境和求解器状态；
2. 固定后续外生随机数和事件流；
3. 从同一状态分别执行每个候选干预；
4. 运行到固定 horizon 或终止；
5. 记录终端 outcome 与干预成本；
6. 得到仿真中的 individual treatment effect ground truth。

这一步比直接在观察日志上报告 CATE 更重要，因为它能验证估计器是否真的恢复
干预收益，而不是只拟合相关性。

### 8.5 OOD 与反证

必须至少保留以下 held-out 组合：

- 未见 FJSP family；
- 未见地图拓扑；
- 未见 AGV 数和机器数；
- 未见扰动强度；
- 未见并发扰动组合；
- 未见 JobSolver × MAPF solver 组合。

反证条件：

- 简单阈值已达到相同 policy value；
- BNN 校准或 OOD 不优于 ensemble；
- CATE 方法不优于 outcome regression；
- 长期预算策略不优于 myopic/knapsack；
- 干预收益只存在于单一地图或单一 seed；
- 恢复收益被计划变更成本抵消。

## 9. 推荐推进顺序

### 基础正确性验收

- 正式实现 tardiness、OTD、recovery 和 nervousness；
- 补齐异常注入器、随机数、求解器缓存的完整快照恢复；
- 验证同状态、同外生随机数、同动作严格复现；
- 修复现有负 transport delay 指标。

通过条件：paired rollout 的无干预双跑完全一致。

### 扰动级联验证

- 运行无扰动与单一/并发扰动；
- 量化机器故障、AGV 故障、路障和加工波动对运输、机器饥饿、交期的传播；
- 比较只修 MAPF 与联合恢复。

通过条件：至少一种可复现扰动中，跨层恢复显著优于单层恢复。

### 恢复策略价值验证

- 比较 no-response、always-full、periodic、固定阈值和 multi-trigger；
- 加入计划变更与计算成本；
- 绘制 quality-cost-stability Pareto。

通过条件：不存在一个简单固定动作支配所有状态。

### 不确定性方法价值验证

- 比较 point、quantile、ensemble、MC Dropout 和 BNN；
- 先看校准，再看在线 policy value；
- 在 OOD 上验证保守回退。

通过条件：不确定性感知策略优于同容量点预测策略，且不是仅靠更大模型。

### 因果方法价值验证

- 用 randomized intervention 数据训练 OR/IPW/DR；
- 用 paired rollout ground truth 验证 CATE；
- 比较因果和非因果 gate 的 policy value。

通过条件：DR/CATE 在选择偏差或 OOD 下稳定优于 outcome regression。

### 长期决策方法价值验证

- 比较 myopic、knapsack、bandit 与 offline RL；
- 固定动作、数据和计算预算；
- 检验序列机会成本和长期信用分配。

通过条件：offline RL 在多预算上稳定改善终端指标，否则不把 RL 写为贡献。

### 实际数据与迁移验证

- 尝试引入公开动态 FJSP 数据或企业匿名日志；
- 用真实数据拟合扰动分布，在 SkyEngine 中回放；
- 报告 sim-to-real 分布差异和保守结论。

## 10. 论文与项目组合建议

### 主论文

**题目候选：**

> SkyCausal-R: Causal and Risk-Aware Hierarchical Recovery for Flexible
> Manufacturing under Multi-Source Disruptions

**三项贡献候选：**

1. 一个把 FJSP、显式 MAPF 和多源扰动统一到事件级执行中的可复现实验协议；
2. 一个能区分扰动传播风险与干预因果收益的校准模型；
3. 一个在计算和计划变更预算下选择恢复时机与范围的分层策略。

### 扩展论文 A

> Calibrated Due-Date Quotation and Rush-Order Admission under Coupled
> Production-Logistics Uncertainty

### 扩展论文 B

> Prescriptive Maintenance and Production-Logistics Co-Scheduling with
> Uncertain Machine Degradation

## 11. 最终判断

当前系统最稀缺、最有研究价值的资产，不只是已有多个 FJSP 和 MAPF 求解器，
而是：

- 可以在真实事件链中观察生产与物流的级联；
- 可以可控地注入多种扰动；
- 可以保存状态并生成反事实；
- 可以记录强求解器查询成本与失败；
- 可以逐步把“预测风险”升级为“选择干预”。

因此，下一阶段不应优先增加更多网络结构或更多静态求解器。应先完成
先完成基础正确性、扰动级联和恢复策略价值验证，证明**多源扰动下干预范围选择
确实存在稳定价值**。只有该事实成立，
BNN、因果推断和离线 RL 才有清晰、不可替代的研究职责。
