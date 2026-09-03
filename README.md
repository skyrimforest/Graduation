# Three Invisible Barriers: Unblocking Closed-Loop Replanning in Coupled Job-Shop Scheduling and Multi-Agent Path Finding

ICAPS 2027 投稿材料与实验证据仓库（**私有**——双盲评审期间请勿公开）。

## 论文核心主张

在生产级耦合排产栈（FJSP 调度 + MAPF 路径规划微服务 + 离散事件网格工厂）中，
闭环计划修订被三层"隐形屏障"阻塞，每一层都静默失效且足以独立杀死闭环：

1. **编码屏障（Representability）**——修订请求编码器无法表达在途承诺的后继，
   任意一个在途运输即可否决修订激活（2401 次触发中 47% 被否决）。
2. **执行屏障（Execution consistency）**——每次修订为所有未开工工序整体重建
   运输请求且不去重：已在途的工序被二次投递、**已完工的工序被二次加工**
   （9% 的工序在含修订的 episode 中被幽灵再加工）。
3. **接口屏障（Interface feasibility）**——调度层静默生成"两台 AGV 终点为同一
   机器格"的运输承诺，MAPF 形式上不可解；路由器逐次超时，全场冻结且无法自愈。

三项修复（保守承诺投影 / 运输唯一性不变量+终点互斥+暂存交接 / 同格免运）全部为
执行层小改动、带独立开关，关闭开关可精确复现旧行为——这是 E8 消融实验的基础。

## 核心结果

| 证据 | 数字 |
|---|---|
| 编码屏障 | 修订激活率 53% → **99%**（n=2401 触发） |
| 执行屏障 | 幽灵再加工 86 → **0**，冗余投递 112 → **0**（E8 双臂） |
| 消融 | dedupe 单独即清零幽灵；same-cell 免运若无 dedupe 反而放大（86→133） |
| **因果翻转** | 同一批格子同一种子：legacy 下 static 12:0 全胜 → 修复后 full 8:4 反超 |
| R2 战役级 | 修复引擎上 **full 101:49 胜 static**（n=202 完整配对，Wilcoxon p=5×10⁻⁸，均快 47.5 步） |
| 可靠性 | 流式到达场景：修订失败 1–18 次/格 → **0**，吞吐 +23–31% |

旧栈上"重规划惨败 25–125%"的结论被证明是执行层病灶向策略账上转嫁的
执行腐败成本——**在验证跨层语义之前，任何 when-to-replan 策略评价都不可信**。

## 仓库结构

```
paper-icaps2027/     ICAPS 主论文 (LaTeX + PDF + 图表 + 讲稿 PPT)
paper-2..7-*         六个后续方向的中文初稿（基准评测/学习分解/lifelong/死锁/鲁棒/LLM诊断）
results/             战役原始数据: E1-E4 主因子(948) + E8 双臂(52) + 五臂消融(130) + E5
analysis/            配对分析脚本 (imputation + Wilcoxon)
20260901_FJSP_MAPF七方向科研地图.md   七方向研究地图
papers/              论文工作区: 1~7号方向 + 反事实模拟/LLMEnvolve/LLMSchedule/毕业论文_天工 (LaTeX 源+PDF)
research-notes/      研究笔记: 历史结果54篇 + 各方向README + 阶段设计/验收报告/评审包
literature/          文献库: common(通用) + 各方向专题 PDF + bib
reports/             汇报PPT + 调研报告 + 创新点构思v0.1-0.3 + PPT生成脚本
templates/           南大模板(NJUThesis) + 毕业论文模板
latex/ scripts/      论文编译工具链 (Dockerfile + latex-build.sh + compose.latex.yaml)
RESTORE.md           新服务器完整复现指南
bootstrap.sh         一键重建工作区脚本
```

## 复现说明

实验代码与引擎改动独立管理：

- **引擎**：`skyrimforest/SkyEngine`（分支 `0902dedupe`，含 10 个带开关的修复提交；
  开关：`AGV_TRANSFER_DEDUPE` / `AGV_CELL_RESERVE` / `AGV_SAMECELL_SKIP` /
  `AGV_PARK_DISCIPLINE` / `AGV_ASSIGN_LOSS_GUARD`，全部置 0 复现旧行为）
- **实验代码**：`sky_research`（`closeloop/run_full.py` 战役 runner、
  `closeloop/pilot_ab.py` 双臂、`closeloop/pilot_abl.py` 五臂消融、
  `vis/make_frames.py` 全程帧生成器）
- 全部 episode 子进程隔离 + 硬超时 + 种子确定性（双栈复验 bit-identical）

## 状态

- [x] E1-E4 主因子（修复引擎，948 集）
- [x] E8 双臂 + 五臂消融
- [ ] E5/E6/E7 修复引擎重跑（myopic leak-free 变体）
- [ ] ICAPS-27 官方模板换壳
