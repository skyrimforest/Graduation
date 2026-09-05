# 批1精读：ReflecSched + LLMHeurFromTraces（2026-09-04）

> 对应《精读导读_20260904》批1前两篇（T0 最近邻）。两篇全文（txt）已通读，笔记 A/B 中承重数字逐条对过原文。
> 原文：`research/7_LLM诊断解释/papers/txt/{ReflecSched_2025.txt, LLMHeurFromTraces_2026.txt}`
> 产出目标（导读§三批1）：每篇一句差异声明草稿 + 反事实 seed 协议最终版参数。

---

## 一、ReflecSched（arXiv:2508.01724v3，2026-01-19 修订）

**ReflecSched: Solving Dynamic Flexible Job-Shop Scheduling via LLM-Powered Hierarchical Reflection**
Shijie Cao, Yuan Yuan（北航 CS + 青岛研究院/杭州创新研究院/中关村实验室）。代码承诺接收后开源：github.com/cls1277/ReflecSched（当前未见仓库，引用时注意）。

### 1.1 任务卡三问的回答

**① 经验文本 E 的生成与刷新机制**
- 生成：分层自上而下仿真 l=L_max→0，递归 Simulate-Reflect-Refine。每层：随机基策略 π_base（每个决策点从 **24 个 PDR 组合池**采样） rollout → 取代价 Ĵ^(l)（假设性部分 makespan）**最优/最差两条轨迹 ζ_best/ζ_worst**（对比式极端采样）→ LLM 蒸馏 E = F_LLM(ζ_best, ζ_worst)。
- 分层语义：l=2 长程层识别未来机器争用等全局约束（全程用 π_base）；l=1 中程层在 E2 圈定的窗口内细化；l=0 基层对每个可行动作做 forced rollout（先执行该动作、其余步 π_base）系统评估。高层经验 E2→E1 逐层 refine，输出**单一**策略原则。
- 输出格式：XML `<comparison_summary>`（路径差异分析）+ `<key_insights>`（新综合原则）；反思 prompt 显式要求对旧经验做 **CONFIRM / CONTRADICT / ADD NUANCE** 判定，且"不要罗列新旧规则，合成一条更优更一般的规则"。
- 刷新：**仅动态事件触发**（新任务到达/机器故障等），事件间所有决策点复用同一份 E；决策 prompt 只含即时动态状态 + E（`<key_insights>` 标签嵌入），**不含静态数据**（对应长上下文悖论的解法；附录 H：Dynamic Gantt=Enabled / Static Data=Disabled）。
- 理论包装：近似策略迭代（API）+ rollout 算法；Prop 1（条件策略改进 E[V^πE] ≤ E[V^πbase]）依赖两假设——Cost Function Approximation（rollout 代价≈cost-to-go）与 Faithful Reflection；作者自认 lookahead 内"无新事件"的确定性投影假设只是经验上成立。

**② "在线"的证据（经验服务当步决策）**
- E 在 episode 内、事件触发时生成，注入后续每个决策点的 prompt，直到下次事件刷新；相关工作中明确 E 是 "transient, textual Strategic Experience"（规划期算子，非持久记忆库）。附录 B.3：紧急任务到达即触发反射模块重新评估，"基于最近证据"强化高优先级规则。→ **在线前馈成立**。
- 工程兜底：动作经环境内核过滤可行性；输出不合法时多数投票 + 启发式 tie-break 恢复（Appendix B.3）。

**③ 有无任何事后/离线分析成分：无。**
全部反思是规划期在线算子。离线部分只有基准构建（GEN-Bench 判别分+全局平衡的贪心筛选、PDR-Bench 唯一最优 PDR 筛选、MK-Bench 静态→动态改造），与诊断无关。→ related work 切割点清晰：**它把 LLM 读到的"未来 rollout 对比"前馈为策略经验；没有事后诊断、没有 ground truth 对照、没有同 seed 反事实验证、不产出可审计的证据链。**

### 1.2 实验设置与关键数字

- 基准：GEN-Bench（20 Normal + 18 Small，自建并按判别力+无 PDR 偏置贪心筛选）；PDR-Bench（111+12，唯一最优 PDR 诊断集）；MK-Bench（MK01–MK10 加动态事件：horizon=下界×1.2、60% 任务 t=0、指数到达、50% 故障概率 MTTR~U(1,4)、30% 取消、紧急任务插瓶颈机）；JMS-Bench（半导体 cluster tool，PM1–5+机械手，热批插入/腔室故障/取消）。实例参数：Normal 15–20 任务×2–4 工序×3–5 机器；事件注入用确定性 seed（事件队列随实例固定 → 各方法天然面对相同事件流）。
- 调用协议：诊断期 5 样本多数投票 T=0.8；终版对比实验 T=0.2（附录 H：T=0.2/top-p 0.8/top-k 20/max 8192，CoT，非 thinking）；每实例 3 次独立运行取均值；Wilcoxon signed-rank，**样本量=实例数**。
- 主结果（GEN-Bench Avg RPD/Avg Rank）：最佳变体 Qwen3-14B **6.09%/4.39**；其余 7 变体 6.94–8.03%；IDDQN 10.45/6.58、HMPSAC 11.00/6.68、DAN 10.74/6.47、PPO-OC 13.47/8.05、GP 54.85/11.42。vs LLM-Direct：**平均胜率 71.35%，平均 RPD 降 2.755%**。vs 逐实例最优 PDR oracle：无显著差（Normal RPD 0.062%、p=0.8107；Small RPD 0.933%、p=0.1240）。MK-Bench 最佳 DS-v3.2 6.83/3.90；JMS-Bench 最佳 Qwen3-14B 6.18/4.00。
- 消融（Qwen3-8B）：① 去分层（单层 L=0）加 rollouts 到 24 也追不上全框架——"暴力平搜无效"；② 经验质量：Full > Shuffled > Generic，**Noise（best/worst 互换）严重劣化**→ not all reflection 有益；③ 证据选择：best+worst 对比式 > Top-K Best / Top-K Worst / Quartile；Normal 上 Top-K Worst > Top-K Best（**从失败学比从成功学更有价值**）；④ 预算约束 L×R=24 下 **L=2,R=12 最优**（宽而中深 > 纯宽 L=1 > 纯深 L=6）。注意 §6.5.1 的"全框架"写的是 L=6,R=24（预算 144），与 §6.5.3 预算 24 的最优配置 L=2,R=12 并存，主配置口径在文中未完全统一——引用其超参时以 §6.5.3 为准并注明。
- 效率：token 表（GEN-Bench/实例）：**Normal 规模 ReflecSched 全面更省**（GPT-4o 137.4k→115.4k 等，平均省 **15.1%**；论文归因：决策 prompt 剔除静态块、只带精简 E）；**Small 规模反而约 2 倍更贵**（21–24k → 45–53k，反射开销占主导）。累计墙钟 break-even vs HMPSAC：DS-v3.2 约 74 个实例、GPT-5-nano 约 50 个；N 超过 break-even 后 DRL 摊销占优。硬件 H100 80G + vLLM。案例研究：cluster tool 故障场景 makespan 36.67 vs 贪心基线 40.0。

### 1.3 笔记核对（B 表第 19 行、B§四-5、A§八）

| 笔记条目 | 原文核实 | 结论 |
|---|---|---|
| 诊断期 5 样本多数投票 temp0.8、终版 temp0.2 | §6.1 原文逐字一致；附录 H 补充 top-p 0.8/top-k 20 | ✓ |
| "24 种 PDR 基策略 rollout→取最好/最差轨迹" | 24 = PDR 组合池大小（π_base 每步从中采样）；rollout 数 R 是独立超参（主配置 24；预算实验最优 L=2,R=12） | ✓ 但建议措辞区分"池大小 24"与"rollout 数 R" |
| E 仅动态事件时刷新 | §5.2 ✓ | ✓ |
| "省 15% token" | 15.1% 是 **Normal 规模 vs LLM-Direct 的整体 token 效率**（Table 4），归因是决策 prompt 更精简（无静态块），**不是**事件触发刷新直接省出来的；且 Small 规模贵 ~2 倍 | ⚠ 建议改写为"Normal 规模平均省 15.1%（精简 prompt 所致）；事件触发刷新是独立设计" |
| 模型清单 GPT-4o/DeepSeek-V3/Qwen3-8~32B | 另有 DS-V3.2、GPT-5-nano（Table 3 七个后端） | ⚠ 补全 |
| 反思喂 contrastive 证据、CONFIRM/CONTRADICT/ADD NUANCE、合成单一原则 | 附录 E.2 逐字吻合；Noise/Shuffled/Generic 消融支撑"噪声经验有害" | ✓ |
| "同 seed 下采纳/不采纳的 ΔKPI best/worst 对" | **不是 ReflecSched**：它对比的是同状态下两条模拟未来轨迹（确定性投影，无新事件），无 seed 配对概念；同 seed 配对是我们自设协议（源自 LLMHeurFromTraces） | ⚠ 引用归属要分开 |
| 事件驱动触发省 token | 触发机制 ✓；token 结论见上行 ⚠ | ⚠ |

### 1.4 差异声明草稿（related work 用）

> ReflecSched 在决策时刻用 LLM 对比蒸馏多条启发式 rollout 的未来轨迹，生成前馈式"策略经验"以纠直接调度的短视；它是**运行时在线反思**——既不产出事后诊断结论，也无任何同 seed 反事实或证据链验证，与我们"事后归因四元组 + 重仿真配对验证"的对象、时机与产出均不同。

### 1.5 可抄 / 可批判

- 可抄：对比式极端经验（best/worst 轨迹对 + CONFIRM/CONTRADICT/ADD NUANCE + 合成单一原则）；事件触发刷新；决策 prompt 剔静态保动态（长上下文悖论）；Noise 消融模板（证明 not all reflection 有益）；GEN-Bench 的判别力+全局平衡筛选配方（对我们场景库选题可复用）；"Top-K Worst 优于 Top-K Best"可佐证我们"从失败案例学"的取材策略。
- 可批判：反射以"最优/最差 rollout"为证据，无真实事件流参与（确定性投影）；无验证环节——E 好坏只能靠端到端 makespan 间接体现；Wilcoxon 样本量取实例数而非配对粒度；L/R 口径未统一；宣称 zero-shot 无训练瓶颈但 Small 规模 token 翻倍。

---

## 二、LLMHeurFromTraces（arXiv:2608.09343v1，2026-08-10）

**LLM-Guided Heuristic Design from Simulation Traces: A Case Study in Dynamic Production and AGV Scheduling**
Jinbo Li, Chuanhao Li（清华工业工程系，通讯 chuanhao-li@tsinghua.edu.cn）。定位是 **case study**（单一环境：FreezoneX 2025 智能工厂调度赛题，github supcon-international/25-AdventureX-SUPCON-Hackathon）。

### 2.1 框架一句话

SBO 里"均值分数管选择、事件级轨迹管诊断"：manager agent 查**可查询 trace 库**（非全量入上下文）+ KPI 分组摘要，对 incumbent 最低分复制的**诊断回放**提瓶颈假设、给 3–4 个修改方向；editor agents 并行各实现一个可执行候选（改 scheduler.py/param_estimator.py）；执行检查 + R 次重复仿真评分 + best-so-far（严格更优才替换）。**LLM 只在评估批次之间修改代码，单次仿真运行内策略固定**（可审计、可版本化、部署前可测）。

### 2.2 任务卡三问的回答

**① Seed 协议全文细节（我们的反事实协议直接继承它的，数字逐条如下）**
- **搜索期**：每个候选评估用**独立 seed 集**（R=10 打分复制 + 1 次诊断回放，回放分不计入均值）；incumbent 保留旧评估、不用候选 seed 重评 → 提升判定比较的是**独立估计的均值**，搜索不会过拟合某一组固定随机实现（原文："the search does not adapt to one fixed set of realizations"）。
- **终评（Appendix B.4）**：每设定下每方法族冻结一个代表策略（两阶段 MILP、最优规则、最优元启发式、最优 Gemini-3.1-Pro 终版），四者跑**同一组 100 个连续 seed（123–222）**；配对差 D_n = S^LLM_n − S^b_n；双侧 Wilcoxon signed-rank（W=min(W+,W−)）；**每设定 3 个基线比较的 p 值做 Holm 校正**；报告**配对差中位数**（Table 16：Default 14.36–15.11、随机故障 14.02–14.57、T=3000min 14.18–25.79、变到达间隔 13.56–13.85）。12 个比较全部 100/100 seed 更优 → W=0，渐近 p=3.90e-18，Holm 后 1.17e-17。
- 关键口径（写我们协议时必须带上）：同 seed 只是**共同外生随机输入**，"不同策略的事件序列不必产生相同实现轨迹"——即 matched seed ≠ matched trajectory。
- 复评属**独立检查**（independent check），正文报告的框架分数仍是搜索期存储的 incumbent 均值——**双口径并存**（优化期均值 + matched-seed 复核），与我们笔记 A§五一致。

**② 经理/编辑分工与停止条件**
- Manager（≤20 步）：读 incumbent 策略代码 + 存储均值 + 保留诊断证据（分组 KPI 摘要 + trace 库查询记录/汇总）+ 历史搜索记录 → 提 k_t 个不同修改方向（建议区间 **3–4**，manager 在区间内自选）。
- Editors（各 ≤25 步，每方向一个 agent，fresh context、隔离 workspace）：实现一个可执行候选，可扩展 param_estimator.py 做数据驱动参数估计（用 incumbent trace 库的**冻结快照**做赛前估计；打分复制只读快照不更新，仅诊断回放写新轨迹，胜出者的轨迹成为下一轮快照）。
- 停止条件（三选一触发即停）：t=T=**10** 轮；S̄_t ≥ S_tar=80；连续 **C_stall=3** 轮无进步。另有事件级停止：目标达成前这些条件兜底。

**③ 失败如何记账**
- 候选装载/运行失败 → 触发有界修复：editing agent 修 ≤**N_repair=3** 次，**每次修复后完整重跑 Evaluate_R**；仍失败 → **候选直接丢弃**（不进选择，incumbent 默认保留）。
- ⚠ 笔记 A§五"失败记 ΔKPI=−∞ 不丢弃"**不在本文中**——原文是丢弃语义；−∞ 记账是我们自设的协议选择（更保守、避免"修复丢弃"与"真差"混淆），写论文时不要把 −∞ 归给本文。

### 2.3 实验与关键数字

- 环境：3 产线 ×（工位 A–C、输送 AB/BC/CQ、CQ 缓冲、质检站、充电位、2 AGV），共享原料/成品库；动态订单（默认每 10 min 一单）、有限缓冲、C 型品 re-entrant、质检返工（<80 返工、<60 报废）、充电约束、可选随机故障。总分 = 8 指标归一加权（生产效率 40% / 质量成本 30% / AGV 效率 30%）。
- 超时选取：初始策略跑 3000 min×1000 复制，分数 ~500 min 后趋稳（±2 分）→ 默认 T_sim=500 min。
- 基线：两阶段滚动 MILP（Gurobi 2s，超时/非最优则贪心兜底；mean 62.97）；规则组合 135 个（5×9×3，各 100 复制，最优 62.62）；GA/DE/PSO 搜 14 维规则权重单纯形（稳定性惩罚适应度 S̄−0.35σ̂，20 复制×10 代，最优 63.58）。**基线动作空间均不含充电控制**——论文自己承认这部分差距来自决策空间更大而非 trace 引导本身，消融用于隔离 trace 贡献。
- 主结果：Gemini-3.1-Pro 5 次独立优化平均 **77.51**（76.10–78.61）、GPT-5.5 76.13、GLM-5 73.83、GPT-5.4-mini 72.84，全部 > 基线 low-60 档。代表轨迹：62.49 →(主动充电+就近任务) 70.28 →(下游清空优先) 75.98@5 →(前后端平衡) **78.61@8**，后 2 轮无进步（+25.8%）。
- 鲁棒性：随机故障（间隔 U(80,120)/恢复 U(20,60)）**不重优化**仍 100/100 seed 占优；换设定**分别重优化**：T=3000min 得 74.16（72.37–78.16）、到达间隔 U(5,15) 得 76.34（74.71–78.97），均超基线（MILP 在长时域跌到 50.03）。
- 消融（5 次运行）：去并行（单候选）→ 均值降（Gemini 77.51→73.65；mini 72.84→66.22）且**下限崩**（76.10→62.36），平均轮数 9.2→5.8（无进步早停更易触发）；去 trace 库（连参数估计一起关）→ 均值降 77.51→76.16、72.84→69.28，**轻量模型受损更大**（trace 证据对小模型是 grounding）。

### 2.4 笔记核对（B 表第 21 行、B§四-5、A§五）

| 笔记条目 | 原文核实 | 结论 |
|---|---|---|
| 经理 ≤20 步 / 编辑 ≤25 步 | Table 10：manager 20、editing 25 | ✓ |
| 3–4 并行候选 | Table 10 建议区间 3–4 | ✓ |
| T=10 轮、无进步 3 轮停 | Table 10：T=10、C_stall=3 iterations | ✓ |
| 失败修复 ≤3 次 | Table 10：N_repair=3；修复后完整重评，仍败则丢弃 | ✓ |
| 可查询 trace 库（按需查，非全量入上下文） | §3.2/§3.3 ✓；另有冻结快照+仅诊断回放写库机制（笔记未记，已补） | ✓ |
| 搜索期独立 seed、终评 matched seeds | §4.1 + Appendix B.4 ✓ | ✓ |
| 连续 100 seed | seeds **123–222**，连续 | ✓ |
| 双侧 Wilcoxon + Holm 校正；报配对差中位数 | B.4 ✓；12 比较全部 100/100，p=3.9e-18，Holm 1.17e-17；Table 16 报中位数配对差 | ✓ |
| 优化独立重复 ≥5 次 | 每 backbone 5 次独立完整优化 ✓（A.5 另有 1000 复制定时距预实验） | ✓ |
| 双口径报告 | ✓（正文报存储均值，B.4 独立复核） | ✓ |
| **失败记 ΔKPI=−∞** | **原文无**：持续失败候选直接丢弃，无 −∞ 记账 | ✗ 属我们自设，勿引为本篇出处 |
| "它优化启发式，我们产出诊断四元组" | ✓ 定位准确；另注意其 trace 读取是**优化指导**（回放最差复制），非受控反事实归因 | ✓ |

### 2.5 差异声明草稿（related work 用）

> 与本文同享"重仿真验证 LLM 输出"的骨架（独立 seed 搜索 + matched-seed 配对 Wilcoxon/Holm 复核），但 LLMHeurFromTraces 以 trace 证据**优化策略代码**、以总分择优，产出是一个更好的策略；我们以受控注入的 ground truth 为对象、产出**诊断四元组**，反事实重仿真用于**验证归因结论**而非搜索更好策略——同一协议，验证对象与产出形态不同。

### 2.6 可抄 / 可批判

- 可抄（协议级，全部已核对）：R=10+1 回放、回放分不计均值；搜索期独立 seed + incumbent 不重评；终评 100 连续 seed 配对 + Holm + 中位数配对差；严格更优才替换；C_stall=3 / N_repair=3 / T=10 / k_t=3–4；trace 库按需查询 + 冻结快照；时距选取预实验（1000 复制看分数稳定点）；"同 seed ≠ 同轨迹"的表述原文句式可直接借。
- 可批判：单一环境（hackathon 赛题）case study；基线动作空间缺充电控制（差距部分来自空间更大，作者自认）；诊断对象是"最差复制"（作者自认不代表典型工况、未隔离不同 trace 选择策略）；历史经验未结构化（无成功/失败修订记忆）；单 incumbent 分支无多样性；**全文没有 root-cause 正确率类指标**——只有总分差，诊断对不对无从单独评价（这正是我们"诊断四元组+评分器"的空位）。

---

## 三、两篇对照 → 我们方向7的增量

| 维度 | ReflecSched | LLMHeurFromTraces | 我们（方向7） |
|---|---|---|---|
| LLM 读什么 | 本状态出发的**未来** rollout 对比 | incumbent **最差复制重放的过去** trace | 受控注入故障后的运行**事实**轨迹 + 反事实重仿真 |
| 时机 | 运行时在线（事件触发） | 离线优化批次之间 | 事后诊断 |
| 产出 | 自然语言策略经验 E（不可验证） | 更优的策略代码 | 诊断四元组（可逐项评分） |
| 验证 | 端到端 makespan，无过程验证 | matched-seed 配对重仿真（协议最近先例） | 同 seed 配对反事实 + 证据链评分 |
| 有无 GT | 无 | 无（分数即真值） | 有（planted fault） |
| 核心风险 | E 无法证伪；小样本轨迹对比 | 最差复制≠典型工况；诊断无单独指标 | ——（待我们补） |

**批1产出落地**：
1. **反事实 seed 协议定稿参数（继承+自设分明）**：搜索/分析期独立 seed（ incumbent 不重评）；终评公共 100 连续 seed（如 123–222）配对重仿真；双侧 Wilcoxon signed-rank + Holm；报配对差中位数+分布图；优化/分析独立重复 ≥5 次；双口径报告；失败记 **ΔKPI=−∞（自设，源自无出处，论文中注明 design choice）**；协议表述引 LLMHeurFromTraces §4.1+B.4，"同 seed≠同轨迹"引其原文口径。
2. **related work 切割段一句话草稿**见 §1.4 / §2.5。
3. **经验/证据设计**（二级阶梯反思精化）：对比式极端证据 + CONFIRM/CONTRADICT/ADD NUANCE + 单一原则合成 + 噪声消融（ReflecSched）；trace 按需查询 + 快照冻结（LLMHeurFromTraces）。
4. **新发现的引用风险**：ReflecSched 代码"接收后开源"（截至 2026-09 未见仓库，勿引代码可用性）；其 L/R 超参口径文内不一致（引 §6.5.3 L=2,R=12 并加注）；笔记 B"省 15% token"归因需改写（见 §1.3 表）；笔记 A"ΔKPI=−∞"出处需改标自设。
