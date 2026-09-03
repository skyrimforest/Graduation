# LLM4Evolve：LLM 作为"算法设计者"的自进化调度（超启发式路线）

> 调研时间：2026-08-26 ｜ 调研方式：联网检索（标注链接均已在本次会话中验证）
> 定位：LLM **不做调度决策**，而是编写/进化调度算法代码（派工规则、邻域算子、进化算子、重调度策略），由仿真器担任 evaluator 打分，形成离线进化闭环。产出的最终物是**确定性代码**，上线零延迟、零幻觉风险。
>
> 姊妹篇：`../LLM4Schedule/`（LLM 端到端直接推理调度）。两条线共用 SkyEngine 的 `GridFactoryEnv` 仿真闭环，本路线是其中接入成本最低、收益最确定的一条。
> 仿真侧机制需求（两线反向推导的共同地基）：`../BaseSimulation机制需求.md`（P1b 段）。

## 1. 核心结论

1. 这是把 LLM 引入现有"搜索 + 仿真"系统**最便宜且最稳**的方式：evaluator 现成（GridFactoryEnv 批量 rollout），被进化对象直接挂到可插拔的 `JobSolver` / `Assigner` 接口上。
2. 技术谱系已经清晰：FunSearch（2023）→ EoH（2024）→ ReEvo（2024）→ AlphaEvolve（2025），每一步的增量分别是"进化循环"、"语言描述与代码协同进化"、"反思机制"、"长上下文 + 异步岛屿种群"。
3. 差异化论文点：**动态联合环境（FJSP + AGV + MAPF）+ 异常/插单/特急单场景下的规则进化**，现有工作几乎都只做静态单问题；再加 VLM 视觉反思（见 §5）可以形成完整 story。
4. **定位升级（2026-08-26）**：被进化对象从"单条派工规则"升级为**专家算子库及其组合方式**——直接回答 BasicSimulation 里"为什么是这些算子"的原始问题，见 §9。

## 2. 核心文献

| 工作 | 出处 | 一句话贡献 |
|---|---|---|
| [FunSearch](https://www.nature.com/articles/s41586-023-06924-6) | Nature 2023.12 | 开山之作：预训练 LLM + 系统化 evaluator 的进化循环，在函数空间搜索；cap set 与在线装箱问题真发现（[DeepMind 博客](https://deepmind.google/blog/funsearch-making-new-discoveries-in-mathematical-sciences-using-large-language-models/)） |
| [EoH](https://arxiv.org/abs/2401.02051) | ICML 2024 | 启发式的**自然语言描述与代码协同进化**，比纯代码进化样本效率高一个量级 |
| [ReEvo](https://arxiv.org/abs/2402.01145) | NeurIPS 2024 | 在 EoH 上加**反思**：短期（最近搜索结果）+ 长期（历史教训累积）语言反馈指导变异；TSP/CVRP/装箱 SOTA（[代码](https://github.com/ai4co/reevo)、[主页](https://ai4co.github.io/reevo/)，**首选代码基础**） |
| [EoH-S](https://arxiv.org/html/2508.03082v2) | arXiv 2025 | 进化"启发式集合"而非单一启发式，按实例分布自动选规则 |
| [EoH-MR](https://www.mdpi.com/2076-3417/15/15/8735) | Applied Sciences 2025 | memetic + 反思混合进化 |
| AlphaEvolve | DeepMind 博客 2025.05 | Gemini 驱动的编码 agent，长上下文 + 异步多岛种群 + 自动评测级联，数据中心调度等真实落地（按名搜索，本次未附链接） |
| LLM4AD | 开源平台 | 算法设计 LLM 平台，汇总了该方向 benchmark 与基线（按名搜索） |
| [ReflecSched](https://arxiv.org/pdf/2508.01724) | arXiv 2025 | **最接近我们场景**：LLM 反思式求解动态 FJSP（纯文本反馈），是"视觉增强反思"的 text-only 对照基线，必读 |
| [awesome-fm4co](https://github.com/ai4co/awesome-fm4co) | 资源库 | 组合优化基础模型论文总库，含 LLM 超启发式分支 |

## 3. 通用进化循环（以 ReEvo 为骨架）

```text
初始化: 种群 P ← {种子规则(经典 PDR: SPT/MWKR/EDD + 少量 LLM 随机生成)}
循环 t = 1..T:
  1. 评估: 每个规则在 GridFactoryEnv 上批量 rollout
     (静态: Brandimarte/Hurink 基准; 动态: 插单 + 异常注入 + 特急单抢占场景)
     指标: makespan / total tardiness / AGV 空驶率 / 重调度稳定性
  2. 反思: LLM 读 (规则代码, 指标, 甘特图/热力图) → 结构化批评
     - 短期: 本轮失败模式(某类实例/某时间窗系统性差)
     - 长期: 跨轮累积教训库(保留精英的"设计说明书")
  3. 变异: LLM 基于批评 + 精英代码, 生成新规则(改代码 or 改语言描述后翻译成代码)
  4. 选择: 锦标赛/精英保留, 剔除编译失败/超时/违反接口的个体
产出: 精英规则集(确定性 Python 函数) + 进化过程日志(论文素材)
```

关键工程点：
- **代码沙箱**：LLM 产出的规则在隔离进程/容器里跑，超时和异常当作最差适应度处理。
- **接口契约**：给 LLM 的 prompt 里固定函数签名（输入 = 你们 `job_observation` 的结构化摘要，输出 = 决策），签名错 = 直接淘汰，不浪费评估预算。
- **评估预算**：动态场景 rollout 贵，用 EoH 的"语言描述进化先行、代码评估殿后"省预算；或 EoH-S 的规则集合按实例聚类分派。

## 4. 与 SkyEngine 的对接

| 进化对象 | 挂载点 | 说明 |
|---|---|---|
| FJSP 派工规则（含插单/抢占逻辑） | `JobSolver.plan()` | 最直接；现有 PSO 重规划可作为一个"被进化对象"而非固定算法 |
| AGV 任务分配规则 | `Assigner.plan()` | 减少空驶/对向拥堵，与 MetricsHub 热力图天然配合 |
| 邻域算子 / 变异策略 | 搜索算法内部 | 给现有搜索算法进化"算子库"，而不是整算法重写 |
| 重调度触发策略 | `sim_server` 在线层 | 何时触发重排、滚动窗口多大——动态场景的独有进化对象 |

操作顺序建议：
1. 先跑通"单对象进化"：只进化 FJSP 派工规则，固定 Assigner/RouteSolver。
2. 引入动态场景（插单/异常注入/特急单），对比静态规则在动态下的退化——这是论文的核心实验。
3. 再做"算子级进化"（进现有搜索算法的邻域结构），证明对搜索本身也有增益。
4. 全程离线，产出代码经人工 review 后进 `JobSolver`。

## 5. VLM 视觉反思扩展（差异化点）

进化循环第 2 步的反思输入，从纯文本指标升级为 **指标 + 甘特图 + AGV 热力图**，让 VLM 指出"M3 在 t=40–60 成瓶颈""通道 X 对向拥堵""急单插入产生三个空闲空洞"等结构化批评。

- 已有铺垫：[Visual-Enhanced Multimodal FJSP](https://dl.acm.org/doi/pdf/10.1145/3746027.3754575)（ACM，视觉+文本融合解 FJSP）、[知识引导多模态 MoE 制造调度](https://www.sciencedirect.com/science/article/abs/pii/S0278612526000464)（RCIM，含甘特图知识）、[graph-to-image MLLM](https://arxiv.org/html/2501.11968v1)、[MLLM 视觉推理解 TSP/mTSP](https://github.com/ai4co/awesome-fm4co)。
- 图表理解基础模型参考：[ChartLlama](https://tingxueronghua.github.io/ChartLlama/)、[Chart-to-Table](https://arxiv.org/html/2401.02384v3)、[MMC](https://aclanthology.org/2024.naacl-long.70/)；[NeurIPS 2025 MAR workshop](https://marworkshop.github.io/neurips25/) 是这个方向的社区阵地。
- 模型选择：批评用 GPT-5/4o 或 Claude；回放视频分析用 Gemini（长视频最强）；要微调特化用 Qwen-VL 系（LoRA 生态成熟）；内部合规用豆包视觉版。
- **必做消融**：text-only critique vs 图+文 critique。如果图像不带来增益，story 不成立——这条必须在实验设计第一天就定好，ReflecSched 就是现成的 text-only 基线。
- 可选加分项：造 FJSP 甘特图-文本配对数据集微调开源 VLM，与 Starjob（纯文本数据集）形成对照，数据集本身可发表。

## 6. 评估口径（与 LLM4Schedule 独立，不共用指标）

**评估对象是"LLM 设计算法的过程与产物"，不是任何单次调度的解。** 单次 rollout 的 makespan 好坏说明不了进化方法的好坏（运气好的随机规则也可能单次跑赢），因此报告指标全部在元层面：

- **样本效率**：进化性能 vs LLM 调用次数曲线（token 成本同列）——本方向的核心比较主轴（EoH/ReEvo 即如此对比）。
- **产物的泛化性**：进化出的规则在**未见过的 held-out 场景族**上的表现。主语是"规则的泛化"，不是"某次调度的质量"。
- **产物的多样性/可读性**：种群内规则差异度、代码长度、与经典规则的距离（新颖性）。EoH 的语言描述机制正好用于可读性论证。
- **过程稳定性**：不同进化种子间的方差、收敛代数、沙箱失败率。
- **元对照组**（注意：对照组不是 PDR）：无反思进化（EoH 式）vs 反思进化（ReEvo 式）、随机代码搜索、人类专家设计流程——比的是"谁来设计算法更有效"。

解质量指标（makespan / tardiness / AGV 空驶等）在本线中**只作为进化循环的内部适应度信号**，如同 RL 的 reward 之于评测表，不进报告口径。

评估场景与内部参考：
- **适应度场景族**：静态 Brandimarte/Hurink + 动态自造场景族（插单率 × 异常率 × 特急单比例网格）。场景族决定进化方向——只在静态实例上评估就只会进化出静态最优规则。held-out 场景族必须第一天就留出，防进化过拟合。
- **内部参考基线**：经典 PDR（SPT/MWKR/EDD/FIFO，[PDR tutorial](https://github.com/meiyi1986/tutorials/blob/master/notebooks/job-shop-scheduling-dispatching-rule.ipynb)）与现有 PSO/搜索算法，用于标定"进化产物是否超过现有人类水平"。

## 7. 风险与注意

- LLM 调用成本集中在进化期，做好缓存（相同代码+相同场景不重评）与并行 rollout。
- 规则可能过拟合评估场景族——留出未见过的实例分布做泛化测试。
- 动态场景评估方差大（随机插单/异常种子），需要多种子平均，预算×3。
- 多对象同时进化（派工+分配+算子）容易 credit assignment 混乱，严格按 §4 的顺序逐层来。

## 8. 待决开放问题（并行思考清单）

1. **被进化对象的第一刀切在哪**：派工规则（最容易验证）vs 重调度触发策略（动态特色、novelty 所在）vs 搜索邻域算子（作用于现有 PSO 内部）。（2026-08-26 更新：整体定位已升级为算子库级进化，见 §9；本条缩小为"算子库内先从哪类算子开刀"。）
2. **规则表示**：纯代码 vs 代码 + 语言描述协同进化（EoH 结论：协同显著提升样本效率）。
3. **反思信息源消融**：text-only 指标 vs + 甘特图/热力图（VLM）。
4. **多样性维护**：niching 还是规则集合（EoH-S 路线），避免种群收敛到单一规则。
5. **预算分配**：LLM 调用预算与 rollout 评估预算的配比（评估贵时先语言层进化、后代码评估）。

## 9. 讨论定案（2026-08-26）：算子级进化与双层优化

**动机升级**：BasicSimulation 当前是人工挑选的专家算子组合（FJSP 求解 / Assigner / MAPF 求解…），"为什么是这些算子"无法回答。本线的被进化对象由此确定为**算子库本身及其组合方式**——比文献中进化单一启发式更贴本系统，也是主要 novelty 来源。

**结构化瓶颈诊断（反思输入必须固定格式，不搞自由发挥）**，固化成标准"瓶颈报告"喂给 LLM：
- 析取图关键路径分析（哪些工序决定 makespan）
- 机器空闲间隙统计
- AGV 饥饿时长（工序完工后等搬运的时间）
- 队列长度时序
- 插单扰动半径（新解相对原解的偏离范围）

有靶子才能设计算子，也让"分析→设计"闭环可被审稿检验，而非玄学反思。

**双层优化框架**（对应"写代码 vs 可学习 NN 算子是两层"的直觉）：
- 外层 = 离散搜索：LLM 在代码空间设计算子骨架、接口、组合方式。
- 内层 = 连续学习：骨架定了之后学参数/权重。
- 先例：NAS（外层搜架构、内层训权重）、AutoML-Zero。

**三阶落地（不跳级）**：
1. 纯代码算子（FunSearch/EoH 式，无内层）：先验证"诊断→设计→替换"闭环能转。
2. 参数化代码算子：LLM 设计带标量旋钮（阈值/权重系数）的算子，旋钮交 CMA-ES 或进化调优——性价比最高的一层，很多"缺的算子"其实只是缺参数。
3. NN 算子：LLM 只设计接口、结构和损失函数，权重走 `trainer/` 训练——完整双层，最重。

**关键工件**：算子接口契约——固定 obs 进/出签名（对齐 Coordinator 的 observation 结构），保证 LLM 产出可插拔、可沙箱、可组合。

**最小闭环（先于完整进化）**：瓶颈报告 → LLM 提一个新算子 → 替换当前组合中表现最差的算子 → 重新评估。转起来后再引入种群与进化机制。

**工程复用注记**（非研究合并）：LLM4Schedule 线训出的 FJSP-GPT 策略天然是一个"NN 专家算子"，将来入库只需接口对齐；两线评估口径与研究问题保持独立。
