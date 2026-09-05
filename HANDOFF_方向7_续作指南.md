# HANDOFF — 方向7（LLM 调度诊断）续作交接文档

> 交接日期：2026-09-04 晚。写给继任的 LLM 会话或研究者。
> 读完本文 + §1 必读材料，你就可以不问任何问题直接开工。
> **若你只记住三件事：① 答案字段绝不进 prompt；② 别信任何"全对"的数字；
> ③ 每完成一项就按 §6 纪律推远端。**

## 0. 你接手的是什么

FJSP+MAPF 耦合制造调度系统的"引擎接地 LLM 事后诊断层"：LLM 从运行档案产出
（定位/归因/证据/干预）四元组，每一项由引擎闭环验证（注入真值/证据回查/同种子
反事实重仿真）。当前成熟度：方法与基准设计 8/10，**实验完成度随本周末 frontier
模型接入决定**。已有两轮外部评审：结论"framework 有意思，缺 LLM 主实验"——
主实验（规则/4B）现已补齐，8B 已完成，frontier 与 agentic 待做。

## 1. 必读材料（全部在 Graduation 仓 `papers/7_LLM调度诊断/`，按序）

1. `方法论_v0.2_数据与答案生产规范.md` —— 实现规范。**v0.2 由并行会话增补**：
   KPI 三级粒度阶梯、hard 视图三道质检防线、信息二维网格（粒度×预算）四臂对照——
   这是下一轮实验的设计蓝图，但**尚未实现**。
2. `P1交付报告_20260904.md` + `本机LLM冒烟_20260904.md` —— 已完成实验与教训。
3. `前沿调研_20260903.md` / `归因范式精读_20260904.md` / `LLM调用方式精读_20260904.md`
   —— 三路调研 + 15/13 篇全文精读（归因范式、各家 LLM 调用方式、可抄工程细节）。
4. `评审核对_20260904.md` —— 外部评审的事实核验与采纳清单（英文标题/RQ1/
   taxonomy 二分/Diagnostic Utility 已落进论文 v2.1）。
5. **并行会话产物（另一 LLM 的工作，尚未与实验线对账——你的第一项任务）**：
   `最近邻精读_ReflecSched_LLMHeurFromTraces_20260904.md`（差异声明草稿+seed 协议终版）、
   `OpsLLM精读_复现与改进路线_20260904.md`（ISSRE'26 复现评估：注入造数据+过程奖励RL
   可行但缺的四样恰是我们的牌）、`RCA前沿借鉴_未来研究目标_20260904.md`
   （G1–G5 带优先级研究目标，引用全部标 unverified）、`精读导读_20260904.md`（25 篇
   txt 的分层阅读计划）、`方法论_v0.2`（见上）。

## 2. 当前实验事实（已定稿，直接引用，勿重跑）

**基准 cases_v2**（`sky_research@0901llmdiag llmdiag/v2/cases_v2.json`）：
52 核验场景 × easy/hard 孪生 = 104 案例；构成 baseline 34 / blocking 30 /
machine 14 / machine_agv 10 / starvation 8 / stochastic 8；
26 场景被核验器拦截（13 配对作废/5 配方未复现/1 接口屏障超时等）。

**主对照表**（温度 0，干净档案视图）：

| 诊断器 | easy 定位/JRA | hard 定位/JRA | 忠实度 |
|---|---|---|---|
| 规则 | 0.596 / 0.596 | 0.413 / 0.346 | — |
| Qwen3-4B | 0.250 / 0.212 | 0.087 / 0.038 | 0.97–0.99 |
| Qwen3-8B | 0.115 / 0.038 | 0.000 / 0.019 | 0.995–1.0 |

**五发现**：F1 规模单调变差（8B<4B<<规则）；F2 hard 档崩塌（abduction 缺口）；
F3 忠实—正确分离（0.97–1.00 与正确率无关）；F4 基率忽视（30+/34 基线被过度诊断）；
F5 词表锚定失败（`corridor` 从未出现，cause 半对）。干预药房 100% 合规。
（机理注：本批均本地 Ollama Qwen3 系列；思考链关不掉是已知限制。）

## 3. 代码地图（`SkyEngine-research@0901llmdiag`，`llmdiag/v2/`）

| 文件 | 职责 |
|---|---|
| `scenarios.py` | 场景网格生成（注入36+基线6+涌现8+CRN孪生28）→ scenarios_v2.jsonl |
| `run_scenarios.py` | 容器内跑批（mp 隔离+300s 硬超时+断点续跑+热力图剥离） |
| `build_archive.py` | 核验器+档案构建（配对作废/改标/证据ID化/easy-hard 孪生） |
| `score.py` | 三层判分（定位双字段/归因严格+宽容/JRA/证据回查） |
| `diagnoser_rule.py` | 规则基线 |
| `diagnoser_llm.py` | LLM 诊断器（**model_view 白名单防泄露**；JsonRegen×3；单案例容错；结果按模型命名） |
| `smoke_local_llm.py` | 冒烟脚本 |

运行环境：docker 容器 `skyresearch`（挂载 codebase 至 /work）+ 微服务
fjsp:8002 / mapf:8001。跑批：`docker exec -w /work/sky_research skyresearch python llmdiag/v2/run_scenarios.py`。
LLM 调用：本机 Ollama（`LLM_BASE_URL=http://localhost:11434`，qwen3:4b/8b 已就绪）。
论文编译：`docker run --rm -v "$PWD:/workspace" -w /workspace skycausal-latex:2026 xelatex ...`。

## 4. 硬教训（每一条都付过学费）

1. **泄露防火墙**：ground_truth/meta/scen_id/case_id 任何部分不得进入 prompt——
   首次全量 100% 即因此作废（留档 `results_llm_*_LEAKY_do_not_use.json`）。
   新增观测视图时必须走 `model_view()` 白名单。
2. **别信好数字**：连 hard 档都满分=泄露警报。分数跳变先查测量再查模型。
3. **arXiv ID 幻觉**：搜索引擎给的 ID 必须经 arXiv API 或 pypdf 标题核验
   （FunSearch/OpenRCA 两轮翻车记录在文献包 README）。
4. **结果文件按模型命名**（results_{model}.json）——默认同名曾导致 4B/8B 互相覆盖
   与"假完成"（resume 全跳过）。
5. **跑批三件套永远开着**：进程隔离+硬超时+断点续跑；跑批器与诊断器都要
   单案例容错（机器休眠一次网络异常就曾击穿全量）。
6. **引用纪律**：manifest 里 citation_only 不得下载引用；数字（如 CloudOpsBench
   JRA 0.76/ECR 0.38）必须能指到 txt 原句。
7. **同步纪律**：代码→sky_research 对应分支 push；文档/论文→Graduation 对应目录
   push（工作区→发布仓是拷贝不是软链）。结果文件名不得复用。

## 5. 下一步（优先级+入口）

1. **对账（你的第一项任务）**：把并行会话的方法论 v0.2（粒度阶梯/四臂/hard 质检）、
   G1–G5、OpsLLM 差异牌与 §2 实测结果对账——哪些建议被 F1–F5 支持/推翻，
   产出 `实验对账_YYYYMMDD.md`。
2. **frontier 两行**（等用户提供 LLM_BASE_URL/API_KEY/MODEL）：
   `LLM_MODEL=xxx python3 diagnoser_llm.py --variant all --out results_<name>.json`。
3. **反事实执行器**（干预判分，无 API 依赖）：解析 intervention → 改
   num_agv/assigner/trigger/padding → `run_closed_episode` 同 seed 重跑 → ΔKPI。
   与 CRN 孪生的 `fault_delta_makespan` 对齐（那是"应恢复量"）。
4. **服务器扩网格**：`bash bootstrap.sh` 重建 → scenarios.py 放开网格
   （+mk04-06/+seeds/bottleneck 与 plan_mismatch 配方/拥塞配方换迷宫图）→ 500+ 场景。
5. **agentic 工具层**（矩阵最后一行）：引擎包成 5-6 个查询工具（查KPI/查事件/
   查修订/提交干预→触发反事实），步数预算 ≤20，过程指标 MTTI/工具覆盖。
6. **论文**：[LLM_SCALE_TABLE]（frontier 行）；英文稿转译；
   测量有效性一节写泄露事故（abstraction firewall）。

## 6. 汇报纪律

每完成一项：① 代码+结果 push sky_research；② 文档/论文更新 push Graduation；
③ 数字变化同步改论文表格并重编译（latex 容器命令见 §3）；
④ 向用户汇报时给"事实/数字/文件路径"三元组，不给无出处的结论。
