# 预算受限的广度优先候选竞赛：方法与 Ground Truth 条件

> 状态：方法稿 v1（随 M-C1 实现交付）｜ 实现：`codebase/SkyEngine/experiment/skycausal/budgeted_search/racing.py`
> 运行入口：`docker compose -f docker-compose-search.yaml run --rm search`
> 上位文档：`research/20260826_阶段目标与总体设计.md`（rev2）M-C1

---

## 1. 问题设定

在闭环 FJSP–MAPF 制造系统中，设决策状态
$\tilde{s} = (S_\text{factory}, S_\text{solver}, S_\text{history})$
（工厂物理状态、当前求解器上下文、近期动态），候选动作集
$\mathcal{A}(\tilde{s}) = \{a_\text{keep}, a_1, \dots, a_n\}$
（保留当前组合 or 切换到某合法算子组合），未来随机流 $\xi$ 服从
由外生 Tape 刻画的分布。目标（越小越好）记为 $J$（如 terminal
makespan）。定义：

$$
Q_H(\tilde{s}, a) \;=\; \mathbb{E}_\xi\!\left[\, J\big(\mathrm{Rollout}(\tilde{s}, a, H, \xi)\big) \,\right]
$$

$$
\Delta(\tilde{s}, a) \;=\; Q_H(\tilde{s}, a_\text{keep}) - Q_H(\tilde{s}, a),
\qquad
G(\tilde{s}, a) \;=\; \Delta(\tilde{s}, a) - \lambda\, C_\text{switch}(\tilde{s}, a)
$$

$\Delta > 0$ 表示切换更好；$G$ 进一步扣除切换成本。**$G$ 是系统最终
要预测与决策的量**（M-D1 的输入）。

在线约束：物理时钟持续推进，计算必须在预算
$B = (T_\text{wall}, N_\text{trans}, N_\text{steps})$ 内完成。
Phase 7 的证据约束了设计：uniform 分配显著优于 MCTS 分配
（paired CI $[1.2, 9.6]$），One-Shot 优于周期深搜（$[11.8, 22.4]$），
depth-2 无一 episode 优于 depth-1。因此第一版搜索形态取
**广度优先的候选竞赛**，不做深树展开。

## 2. 算法：Budgeted Racing（逐轮淘汰竞赛）

```text
输入: 根状态 s̃, 候选集 A = {a_keep, a_1..a_n}, tape 池 {ξ_1..ξ_m},
      轮次表 R = [(H_1, k_1, keep_1), ..., (H_R, k_R, keep_R)],
      预算 B = (T_wall, N_trans, N_steps), 分支上限 K

初始化: 每个候选 × 每个 tape 一条"分支"（懒创建）
for r = 1..R:
    # 统一 horizon：本轮所有存活分支推进到同一累计步数 H_r
    for 每个存活候选 a（canonical 序）:
        for 本轮新 tape ξ（每候选同批新增）:
            从根全速 rollout 至 H_r，挂为新分支
        for 旧分支（未终局）:
            以 KEEP 温续跑 ΔH = H_r − H_{r−1} 步   # 增量推进，不重算
    每条分支记录: terminal_status / terminal_makespan / executed_steps
    排序键: (mean cost, std, keep 优先, action_id)   # 全删失平局不淘汰现任
    淘汰至 keep_r 名存活
    若预算耗尽 或 全部分支终局: 终止
输出: 最终排名; 维护的 top-K 最优分支场面（含可续跑的子状态快照）
```

### 2.1 统一 horizon 与删失语义（公平性铁律）

同一轮内所有候选在**相同**累计步数 $H_r$、**相同** tape 集上比较。
预算只决定"能跑多少候选 × 多少 tape × 几轮"，**绝不**给不同候选
不同 horizon——否则比较带系统性偏差。未终局分支记为删失：
$\hat{J} = H_r + p_\text{censor}$（$p_\text{censor}$ 同轮统一），
求解器报错分支记 $H_r + p_\text{error}$（$p_\text{error} > p_\text{censor}$）。
终局分支记真实 makespan。三态（TERMINAL/CENSORED/ERROR）分别
统计，删失罚值不得冒充终局值进入结论。

### 2.2 分支维护与防爆炸

每分支持有子状态快照（`SearchNodeState`），支持两种去向：
(i) 被选为切换动作的执行起点；(ii) 下一决策点继续深化搜索。
树宽上界 = $|\mathcal{A}| \times m$（分支全量）且每轮单调收缩
（淘汰），最终只维护 top-$K$ 个场面（默认 $K=3$），
**任何时刻的内存占用 = 分支数 × 快照大小，随轮次递减，不爆炸**。

### 2.3 温续跑（增量推进）

旧分支的 horizon 扩展用 KEEP 动作从**上次子状态**续跑 $\Delta H$
步，代价 $O(\Delta H)$ 而非 $O(H_r)$。这同时保持 runtime
continuity 语义（Phase 7 唯一强支持的机制），且与切换动作的
cold-start 差异在第一轮已经计入。

## 3. Ground Truth 条件（何时输出是真值）

**命题（穷举退化）**：当轮次表取
$H_R \ge H_\text{term}$（保证终局）、$keep_r = |\mathcal{A}|$
（不淘汰）、tape 池取全部未来流时，Racing 退化为对
$\{(\tilde{s}, a, \xi) : a \in \mathcal{A}, \xi \in \Xi\}$ 的
**完全枚举**，输出

$$
\hat{Q}(\tilde{s}, a) = \frac{1}{|\Xi|}\sum_{\xi} J(\mathrm{Rollout}(\tilde{s},a,H_\text{term},\xi))
$$

即冻结动作集与 tape 集上的**精确 ground truth**（期望的真值仅受
tape 样本量与仿真保真度限制；前者由置信区间量化，后者由
M-A0 保真度前置门保证）。

**推论（anytime 精确性）**：淘汰规则只删除"已被统计支配"的候选；
随着轮次加深、tape 增多，保留集单调收缩且**包含最优候选的概率
不减**（racing 类算法的标准性质，[Maron & Moore 1993 racing；
Karnin et al. 2013 successive halving]）。因此算法是 anytime 的：
预算越充足，结果越接近穷举真值；预算耗尽时输出当前置信下的
最优与删失状态，**不伪造精度**。

**截断与真值的边界**：若 $H_R < H_\text{term}$（预算内到不了终局），
输出的是"截断 horizon 上的相对排序"，其与全 horizon 真值的偏差
必须通过删失比例披露；此时报告明确标注 `stop_reason =
budget_exhausted`，禁止把截断排序表述为 ground truth。

## 4. 成本模型与预算门

单轮成本 $\approx$ 存活候选数 $\times$ tape 数 $\times$（新 tape 全速
$H_r$ + 旧 tape 增量 $\Delta H$）。总量受三重门控：墙钟看门狗
（实测触发过，Phase 7.5 pilot 在 1755 s 安全截停）、转移调用数、
仿真步数。逐轮淘汰使总成本近似几何级数收敛于首轮全宽成本，
比"全候选 × 全 tape × 全 horizon"的朴素枚举省一个数量级量级——
这正是 racing 相对 DFS 深搜与 uniform 一次性评估的优势。

## 5. 复现与运行

```bash
# 默认演示（tiny 配置, 8 候选 + KEEP, 4 轮, top-3 分支）
docker compose -f docker-compose-search.yaml run --rm search

# 自定义
RACING_ROUNDS="20:2:4,60:2:3,120:2:2,200:2:1" \
RACING_BRANCHES=3 RACING_SEED=7 \
docker compose -f docker-compose-search.yaml run --rm search
```

输出（宿主机 `racing_results/<run>/`）：
`racing_result.json`（轮次/淘汰/排名/分支，含语义哈希）、
`racing_report.md`（ASCII 搜索树 + 淘汰表 + 最终排名）。

示例输出（tiny 配置，2026-08-26 实跑，宿主机与容器结果一致）：

```text
round 0 (H=20):  8 候选 → 淘汰 4（全删失劣于存活分布）
round 1 (H=60):  4 → 3（hungarian 删失掉队）
round 2 (H=120): 3 → 2（keep-current 以 76.5 被 73.5 淘汰）
最终: recipe.greedy_adaptive_resastar 73.5 ± 1.0  [TERMINAL, 真实 makespan]
      top-3 分支场面: 72.0 / 72.0 / 73.0（全部终局）
```

宿主机/容器一致性由同一根种子、同一 tape 派生与
`env_builder` 抽取（消除 FastAPI 依赖）保证。

## 6. 与证据基线及后续工作的关系

- 对比 Phase 7 uniform：uniform 是"零轮次的 racing"（同宽无淘汰）；
  racing 在同预算下把深层评估集中在统计上未被支配的候选上。
- 对比 MCTS（NO-GO）：本方法不展开未来决策树，与 Phase 7
  "搜索是标注器不是控制器"的定位一致；树仅存在于候选 × tape 的
  评估结构中，V2（Beam，序列切换）之前不做深树。
- 下游接口：最终排名 + top-K 分支场面直接喂给 M-D1 切换策略
  （$LCB(G) > \tau$）；删失/错误三态进入 G 的置信度估计。
- 未尽事项（诚实边界）：切换成本 $C_\text{switch}$ 尚未在 racing 内
  显式计价（当前仅排序，不影响真值计算）；tape 置信区间与
  successive-halving 最优分配率的正式分析留待 M-A4 协议。
