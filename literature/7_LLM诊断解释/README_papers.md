# 方向7 LLM诊断解释 — 文献包

论文：`论文_7_LLM调度诊断/article_llmdiag_v1_cn.tex`；代码：sky_research 分支 0901llmdiag
调研综合：`论文_7_LLM调度诊断/前沿调研_20260903.md`（工作流范式/构造验证/可检验假设）

## 管理方式

- `papers/*.pdf`：已下载并经 pypdf 验证标题（32 篇）
- `papers/manifest.csv`：六列清单（filename,title,year,source,status,role），status ∈
  downloaded_verified / citation_only / unverified_title
- `papers/txt/`：归因范式精读用的 pdftotext 抽取文本
- `papers/fetch_papers.py`：批量下载+验证脚本（新论文追加进 PAPERS 列表重跑即可）
- 引用纪律：manifest 里 status=citation_only 的一律"仅引用"；搜索引擎给的 arXiv ID
  必须经 arXiv API 或 pypdf 标题核验（本轮 FunSearch/OpenRCA 的 ID 两次为幻觉，
  已改走 Nature DOI/OpenReview 仅引用）

## 重点文献（按用途）

**最近邻（related work 必须显式切割）**
- ReflecSched_2025：LLM 读仿真轨迹提炼策略经验——**在线**前馈，我们做**事后**诊断
- LLMHeurFromTraces_2026：重仿真验证 LLM 输出的最近学术先例（100 matched seeds）——
  它优化启发式，我们做诊断四元组
- DynaSchedBench_2026：被诊断对象是 LLM agent 而非调度系统
- LLMDigitalTwin_2025：DT 实施前验证纠正动作（流程工业）——干预桥先例

**归因范式精读对象（txt/ 已抽取）**
- RCACopilot / RCAgent / mABC / CloudOpsBench / OpenRCA2 / HowFar_RCA_Telemetry /
  LogReasoner / LLM_RCA_Failures
- OpenRCA2_2026（因果过程监督）与 CloudOpsBench_2026（场景闭环+状态冻结）优先

**方法学依据**
- TamingRandomness_ABM_2024：CRN 随机流同步（反事实协议）
- CorrectnessNotFaithfulness_2024：statement 级忠实度（引用对≠论断被支持）
- CounterBench / ExecutableCounterfactuals / WhatIfBench：LLM 反事实能力边界
  → hard 案例（无事件统计推断）的实验假设来源

**场景库模板**：CloudOpsBench 的 Generator→Executor→Verifier + 状态快照冻结

## 跨方向存放

- CO-Bench、HeurAgenix 在 `research/2_统一基准评测/papers/`
- 仅引用未下载：FunSearch(Nature,无arXiv)、OpenRCA 原版(OpenReview反爬)、
  MASC(付费墙)、MAEF(付费墙)、"LLMs Can Schedule"(存在性未确证，勿引)
