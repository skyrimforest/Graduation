# SkyCausal v3 论文迭代说明

当前版本：`v0.3`（30 状态在线开发版），18 页。

## 唯一主稿

当前论文主稿：

```text
论文/article_skycausal_v3_cn.tex
```

参考文献：

```text
论文/references_skycausal_v3.bib
```

历史文件 `article.tex` 和 `article_skycausal_v2.tex` 仅作为素材，不再作为当前论文
主线。前者是多专家蒸馏/GRPO 叙事，后者是因果模型/离线 RL 叙事，均与当前实现不符。

## 当前题目

中文：

> SkyCausal：面向连续物理时钟动态 FJSP-MAPF 的开放式、截止期安全求解器组合元调度

英文：

> SkyCausal: Open and Deadline-Safe Solver-Portfolio Meta-Scheduling for
> Dynamic FJSP-MAPF under a Continuous Physical Clock

## 论文主线

```text
动态事件
-> 开放 Solver Catalog
-> solver/config/budget 候选
-> 短 probe 与灰盒进度
-> Root MCTS 分配预算
-> 最新状态 freshness/rebase
-> keep-current 与执行价值排序
-> 原子激活或安全 fallback
```

MCTS 的定位是浅层探测预算分配器，不展开未来制造状态树。

## 证据标记

主稿统一使用：

```text
[已确认]：冻结独立确认支持
[开发证据]：仅用于方法筛选
[待确认]：尚未完成独立确认
```

禁止将开发数据填入“开放在线元调度主结果”表。

## 当前可保留的结果

1. 六 profile `T=1` Root Search：
   - 40 个独立 cluster；
   - 相对最佳固定 profile 平均改善 23.575；
   - 相对降低 4.88%；
   - 95% CI `[8.625, 46.325]`；
   - 安全 Gate 通过。
2. 状态执行价值开发诊断：
   - 50 个连续时钟在线 episode；
   - makespan-only 平均 regret 40.0；
   - ridge Q 平均 regret 9.2；
   - 只有 5 个独立状态，禁止 active。
3. 统一动作 schema 的在线开发 cohort：
   - 30 个独立状态、7 种策略、210 个严格配对 episode；
   - 原始 MCTS 平均终局 498.2，相对 keep-current 为 -5.5；
   - fixed CP-SAT 平均终局 496.8，原始 MCTS 尚未超过该基线；
   - 校准 MCTS 将 CP-SAT 首轮可行覆盖从 0/30 提升至 28/30；
   - 校准 MCTS 平均终局 506.0，比原始 MCTS 差 7.8；
   - 所有 deadline、commit reserve、health、物理时钟和运输安全 Gate 通过；
   - 结果仍为开发证据，禁止填入独立确认主结果表。

## 当前图表

主稿现包含 6 张可复现图：

1. 双泳道系统总体架构；
2. 连续物理时钟、probe 与 commit reserve 时间线；
3. 六 profile 独立确认的预算--质量--coverage 曲线；
4. 六 profile 的状态级改善与选择多样性；
5. 全/短预算动作 regret 与 shadow 执行价值开发诊断。
6. 30 状态统一动作 cohort 与最小可辨识预算消融。

图表证据分层：

```text
方法图：2 张，不承载经验质量结论
已确认结果图：2 张，读取 v2.1 冻结独立确认
开发结果图：2 张，明确标记 development-only
```

绘图脚本和证据 manifest：

```text
论文/scripts/generate_v3_figures.py
论文/figures/v3/figure_manifest.json
```

重建命令：

```bash
./codebase/SkyEngine/.venv/bin/python 论文/scripts/generate_v3_figures.py
```

manifest 记录输入 JSON、生成器、PDF 和 PNG 的 SHA256。重复运行必须得到相同
manifest 哈希。

## 策略实现状态

图表版之后已完成一次实现顺序收敛：

```text
probe 阶段：Q 只记录证据，不改变 MCTS backup cost
commit 阶段：对所有认证 bundle 做最新状态 freshness/rebase
首选 stale：允许切换到同轮新鲜备份
active Q：仅在所有幸存候选预测都获授权时排序
无新鲜候选：keep current
```

当前全量 SkyCausal 回归测试为 `379 OK`。active Q 仍未授权。修正链路已经完成
30 状态重跑；结果表明 solver-specific 最小可辨识预算只修复候选覆盖，没有改善
平均终局。

## 下一轮优先修改

1. 审核题目与四项贡献的最终表述；
2. 用 30 状态数据拟合首次可行概率与执行价值，但保持 shadow；
3. 将 probe runtime/state drift 作为显式成本加入 Root 分配；
4. 采用严格按状态留组，比较原始 MCTS、校准 MCTS、fixed CP-SAT 和 makespan-only；
5. 检查多 lane 并行造成的宿主机资源干扰，正式确认改为资源隔离运行；
6. 扩充相关工作并逐条核验文献元数据；
7. Gate 通过后冻结开放在线元调度确认协议；
8. 独立确认后替换主结果占位表，并重写摘要最后一段和结论。

## 编译

在项目根目录执行：

```bash
bash scripts/latex-build.sh 论文/article_skycausal_v3_cn.tex xelatex
```

输出：

```text
论文/build/article_skycausal_v3_cn.pdf
```
