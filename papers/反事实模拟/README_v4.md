# 反事实模拟方向论文（v4）迭代说明

本目录是原 `论文/` 目录的副本，专用于**反事实模拟与真值获取**方向的论文迭代。
原目录冻结不动。姊妹方向（LLM 调度等）在 `论文_LLMSchedule/`、`论文_LLMEnvolve/`
另行迭代。

## 当前主稿

```text
article_counterfactual_v4_cn.tex     ← 本方向唯一主稿（v4）
references_counterfactual_v4.bib
```

历史草稿（article.tex / v2 / v3 及其构建产物）已于 2026-08-26 清理；v3 冻结数据图保留在 `figures/v3/` 供主稿引用。

## v4 相对 v3 的定位变化

| 维度 | v3 | v4 |
|---|---|---|
| 核心主张 | 在线求解器组合元调度 | 反事实模拟基础设施 + 预算受限真值获取 |
| MCTS 角色 | 待确认的主方法 | **被 paper-grade 证伪的基线**（936 配对 episode 负结果表） |
| 新方法 | — | Budgeted Racing（统一 horizon 逐轮淘汰 + 温续跑 + top-K 分支场面） |
| 搜索定位（rev3，2026-08-26 晚） | 元调度（被证伪）→ 标注器 | **双工作点**：限时 = 在线求解器（对象级 MCTS，目标架构 M-E1）；不限时 = golden truth。元级/对象级搜索边界显式化 |
| 理论 | — | 穷举退化命题（ground truth 条件）+ anytime 推论 |
| 求解器上下文 | 未入状态定义 | $\tilde{s}=(S_\text{factory}, S_\text{solver}, S_\text{history})$ |
| 正式定义 | 定性描述 | $Q_H$ / $\Delta$ / $G$ 公式化 |

## 证据分层（沿用 v3 纪律）

```text
[已确认]   六 profile T=1 独立确认（+23.575 / 4.88%，CI [8.625,46.325]）
[负结果]   Phase 7 深度元调度证伪（5 项配对结论表）
[开发证据] 执行价值诊断、30 状态 cohort、Racing 演示（tiny 场面）
```

## 图表

- `figures/v3/fig01--06`：沿用 v3 冻结数据重建（禁止手改数值）
- `figures/v4/fig07_racing_elimination`：Racing 逐轮淘汰 + top-K 分支
  （数据源：`codebase/SkyEngine/racing_results/compose-smoke/racing_result.json`）
- `figures/v4/fig08_racing_structure`：Racing 搜索结构示意（真实动作标注）

重建命令（图与 manifest 哈希联动）：

```bash
./codebase/SkyEngine/.venv/bin/python 论文_反事实模拟/scripts/generate_v4_figures.py
```

## 编译

```bash
bash scripts/latex-build.sh 论文_反事实模拟/article_counterfactual_v4_cn.tex xelatex
```

输出：`论文_反事实模拟/build/article_counterfactual_v4_cn.pdf`（当前 11 页，
零未定义引用）。

## 待办（按 research/20260826_阶段目标与总体设计.md rev2 里程碑）

1. Racing 从 tiny 演示升级到正式场面（依赖 M-A1/A2 干净根与 t>0 决策点）；
2. $C_\text{switch}$ 计价与 $LCB(G)>\tau$ 切换策略实验（M-D1）；
3. 删失统计语义的正式协议（M-A4）后替换演示数据为独立确认数据；
4. 摘要与结论随独立确认结果重写。

## 本阶段工程成果（2026-08-26，已并入主稿第 5.5 节）

- 确定性缺陷修复：异常注入器无种子 OS 熵导致快照语义哈希跨运行漂移 → 确定性缺省 + 回归固化；
- 求解器目录补全：+9 个外部 MAPF manifest（镜像摘要/配置 schema/预算/能力/shadow 准入），目录达 32 条目；
- 批处理栈解耦：环境构造抽取为无 Web 依赖模块，搜索工具链可在单一 compose 服务运行；
- Budgeted Racing M-C1 落地：统一 horizon 逐轮淘汰、温续跑、top-K 分支场面、四维预算门；
- 回归：621 passed / 3 skipped（新增 33 项测试）；
- 复现：`docker compose -f codebase/SkyEngine/docker-compose-search.yaml run --rm search`，
  宿主机与容器输出同语义哈希。

## rev3 重构（2026-08-26 晚）：按"限时 MCTS + 反事实论证"定位更新主稿

依据 `research/20260826_搜索定位修正_限时MCTS与反事实论证.md`：

- 标题改为《限时搜索、反事实论证与真值获取》；摘要四段式（基础设施 / 元级负结果 / 双工作点+Racing / 目标架构）；
- §1.2 改为"搜索的双重角色"：元级 vs 对象级搜索边界 + RQ4（求解与论证）；
- 新增 §6 目标架构（\pending）：双工作点形式化、限时对象级 MCTS 设计（anytime/runtime continuity/防深搜陷阱/公平性）、反事实论证层（解释忠实度）、聚合特征选取消融、LLM baseline 关系；
- Racing 章降格定位为"已实现实例：候选竞赛评估器"，并在架构中内嵌为 MCTS 节点评估器；
- 负结果章标题明确"元级"；结论按双工作点重写。
- M-E1（对象级 MCTS）未实现——论文中以 \pending 如实标注，待实现并过强制基线后再升级为 \development。
