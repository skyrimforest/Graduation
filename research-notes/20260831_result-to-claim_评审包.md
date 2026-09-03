# Result-to-Claim 评审包（manual 模式，2026-08-31）

> ARIS `/result-to-claim` skill 产物。本环境无 Codex MCP，按
> `reviewer-routing.md` 走 `--reviewer: manual`：**把 §4 的提示词完整粘贴给
> 任一强外部模型**（GPT-5.x / Gemini / GLM-4.x web 均可），把回复按 §5 模板
> 回填到本文件末尾。在那之前，所有 claim 的裁决状态 = `REVIEW_UNAVAILABLE`。
>
> 证据预检已由确定性脚本完成（无模型参与）：
> `../.aris/verify_e1_e2a_claims.py` → `../.aris/evidence_precheck.json`
> **51/53 项 verified**；2 项为同一口径混用发现（见 §3 已知问题 #1）。

## 1. 拟裁决的 Claims（来自设计文档冻结口径）

| # | Claim（论文口径） | 直接证据 | 预检 |
|---|---|---|---|
| C1 | 决策点限时闭环 MCTS 搜组合 + Racing 评估 + LCB 门控切换，显著优于固定组合（never switch） | E1: −33.0 步, 72/72 胜, t=−20.1 | ✓ |
| C2 | 在线自适应搜索显著优于离线预计算静态映射（static_map 由 round-1 全量数据派生） | E1: −10.9 步, 53/72 胜, t=−8.7 | ✓ |
| C3 | hero_v0b 优于及格线 one-shot uniform（设计文档明言：不显著优于它须如实报告） | E1: 均值 −1.8, t=−3.1; **中位 96.5 vs 97.0 持平; 胜率仅 14/71** | ✓（最弱一环） |
| C4 | 切换效应强异质、方向随时机反转（"何时换"有实证答案：晚不早） | E2a: early −57.0/2.3%, mid −79.1/7.0%, late +19.0/30.2%（140 有效配对） | ✓ |
| C5 | M-C0 成本表 disruption_steps=2 严重低估真实切换代价 | E2a: 早期切换平均毁掉 57 步 | ✓ |
| C6 | v0b 优于 best-of-8 随机 golden 参考值（参考非基线） | E1: 70/72 更优, 平均 −38.2 步 | ✓ |

## 2. 实验与数据（已核实）

- **E1**：72 spec × 5 方法严格配对（同 episode 物化、同 tape、同初始配方）。
  数据：`codebase/SkyEngine/experiment/skycausal/results/e1_hero_v0_20260827/`
  + `e1_hero_v0b_20260827/`（v0b 单独目录，按 episode_id 对齐合并后重算，全部数字复现）。
- **E2a**：36 决策根 × 5 切换目标，同 Tape 下 KEEP vs SWITCH-then-KEEP 至终局。
  原始 155 delta → 删失 15 → 有效 140；summary 与原始 pairs 交叉重算一致。
- 统计口径：TERMINAL-only 配对 + 中位数 + 胜率（均值仅参考，见 §3 #2）。

## 3. 已知问题与诚实边界（评审必须考虑）

1. **【已传染进论文 v4】oneshot 中位数口径混用**：报告/论文表用 97.5
   （含删失的全 72 条 eval 口径），但其声明的 TERMINAL-only 口径 = 97.0。
   论文 `tab:e1-main` 的 caption 写着"TERMINAL 口径"却用了 97.5，自相矛盾。
   修复后 96.5 vs 97.0 对 v0b 更有利，方向不变。**待修复，不影响裁决方向。**
2. 均值受删失罚值污染：oneshot 1 次 MAX_STEPS +1000 罚值拖高其均值约 9 步；
3. 纯触发式 hero_v0 在中位/胜率口径下输给 oneshot（8/71）——论文已如实保留；
4. E2a 估计量 = 单次切换后 KEEP 到终局，不外推多次切换策略；目标集固定 5 配方；
5. E3（λ/τ 敏感性）与 E4（穷举校验）**未跑**；racing 未显式计价 C_switch；
6. C6 的 golden 是 K=8 参考值非全局最优（协议 §8），只能作参照不能作基线。

## 4. 粘贴给外部模型的提示词（原样复制）

```text
RESULT-TO-CLAIM EVALUATION（ARIS 纪律：请只依据给出的数据裁决，不要脑补）

背景：柔性制造 FJSP+MAPF 闭环调度。研究对象 = "班子不固定"的元级决策：
决策点上用限时闭环 MCTS 在算子组合空间内搜索候选，Racing 统一 horizon
评估，净收益 LCB(G)>τ 才切换。72 个 workload spec，5 方法严格配对
（同 episode、同 tape、同初始配方）。统计口径 = TERMINAL-only 配对 +
中位数 + 胜率（均值仅供参考，因为删失罚值会污染均值）。

[E1 主结果] TERMINAL 口径 72 配对
  fixed_never    mean 131.7 median 132.0 (72/72 终局)
  oneshot_uniform mean 100.7 median 97.0 (71/72, 一次 MAX_STEPS 删失)
  hero_v0(纯触发) mean 114.3 median 113.0 (72/72)  ← 诚实口径下输给 oneshot 8/71
  hero_v0b(开局搜索+触发修正) mean 98.7 median 96.5 (72/72)
  static_map(离线预计算最优固定起点) mean 109.6 median 110.5 (72/72)
  配对: v0b vs fixed −33.0 (72/72胜, t=−20.1); vs static_map −10.9 (53/72, t=−8.7);
        vs hero_v0 −15.6 (65/72, t=−11.5); vs oneshot −1.8 (14/71胜, t=−3.1, 中位持平);
        vs golden best-of-8 参考值 70/72 更优 (平均 −38.2)

[E2a 配对反事实] 36 决策根 × 5 切换目标，同 Tape 重放至终局，有效 140 对
  总体 Δ=J(keep)−J(switch): 均值 −35.0，切换更优仅 14.3%
  early(前1/3): Δ=−57.0, 切换更优 2.3% | mid: Δ=−79.1, 7.0% | late: Δ=+19.0, 30.2%

[Evidence pre-check] 51/53 项由确定性脚本从原始 manifest 重算 verified；
  唯一不一致 = oneshot 中位数口径混用（97.5 含删失 vs 97.0 TERMINAL-only，待修复）。

[拟裁决的 claims]
  C1 hero(v0b) 显著优于固定组合基线
  C2 在线搜索显著优于离线预计算静态映射
  C3 hero_v0b 优于及格线 one-shot uniform（注意：均值显著但中位持平、胜率 14/71）
  C4 切换效应强异质且方向随时机反转（晚利早害）
  C5 成本表常数 disruption_steps=2 严重低估真实切换代价
  C6 v0b 显著优于 best-of-8 随机参考轨迹

[已知边界] E3(λ/τ 敏感性)与 E4(穷举校验)未跑；racing 未显式计价切换成本；
  E2a 为单次切换估计量；golden 为 K 内最优参考非全局最优；单一 codebase 单一规模。

请对每个 claim 输出（7 字段，逐条）：
1. claim_supported: yes | partial | no
2. what_results_support: 数据实际显示了什么
3. what_results_dont_support: 数据够不到 claim 的哪部分
4. missing_evidence: 具体缺什么证据
5. suggested_claim_revision: 该收紧/放宽/改述吗，给出建议措辞
6. next_experiments_needed: 补证据的具体实验（如有）
7. confidence: high | medium | low
最后给出：整体叙事（论文故事线）当前最大的薄弱环节是什么。
要诚实。单一数据集/规模上的正结果不支持泛化性 claim；C3 的均值显著
但中位持平、胜率 14/71——请特别严格地裁决这一条。
```

## 5. 裁决回填区（外部模型回复后粘贴至此）

```text
verdict: REVIEW_UNAVAILABLE   ← 外部评审完成后替换
C1: ____
C2: ____
C3: ____
C4: ____
C5: ____
C6: ____
整体最薄弱环节: ____
路由决定（result-to-claim Step 4）: ____（confirm / supplement / pivot）
```

## 6. 路由预告（Step 4，ARIS 纪律）

- 若 C1/C2/C4 = yes 且 C3 = partial → **supplement**：跑 E3/E4 补及格线证据，
  claim 措辞按外部模型建议收紧后进入论文写作（`/paper-writing` W3）；
- 若 C3 = no → 主线叙事降级为"开局浅搜为主 + 门控修正为辅"，如实报告；
- 任何 yes 的 claim 若消融不全 → 触发 `/ablation-planner`。
