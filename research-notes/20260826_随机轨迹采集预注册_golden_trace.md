# 随机轨迹采集预注册（golden trace，rounds 迭代制）

> 状态：round-1 执行前冻结 ｜ 日期：2026-08-26
> 上位文档：`20260826_阶段目标与总体设计.md`（rev2）
> 本协议替代 M-A1/M-A2 原方案中"干净根 + t>0 决策点采样"的采集形式，
> 改为**整条闭环 episode 轨迹采集**（用户 2026-08-26 决策）。
> 旧 216 根污染数据已删除（`phase76b_.../roots/`），审计记录保留。

---

## 1. 目的

在没有 judgement 模块的前提下，用**随机决策轨迹 + best-of-K 选择**生成
golden 数据：每个 episode 规格（spec）采集 K 条完整闭环轨迹，按终局
makespan 选出最优一条，作为该 spec 本轮的 golden trace。后续轮次用已训
judgement 模块偏置采样，形成迭代（expert-iteration 风格）。

## 2. 轮次（round）定义——冻结词表

```text
collection_round = 1  : 纯均匀随机采样；judgement_module_id = null
collection_round = r>1: 采样分布由 round 1..r-1 数据训练出的 judgement
                        模块偏置（如 epsilon-greedy 围绕模型 argmax）；
                        必须记录 judgement_module_id、trained_on_rounds、
                        采样分布参数。round r+1 的协议须先行评审。
```

每条 trace 的每行数据都带 `collection_round`、`trace_id`、`episode_id`、
`trace_index`（spec 内第几条）。

## 3. 采集机制

- **闭环机制**：复用 Phase 7 冻结闭环（`OnlineOrchestrationController`
  循环 + `materialize_episode`）。监控窗口 10 步、决策间隔 10 步、
  终局上限沿用 `PHASE7_TERMINAL_MAX_STEPS`。
- **决策规则（round-1）**：在每个决策点，取 `SequentialAdmissionPolicy`
  的 admitted 动作集（KEEP + 合法 SWITCH），**均匀随机抽一个**执行。
  无前瞻 rollout、无 oracle 调用（这是与 Phase 7 搜索策略的本质区别，
  因此单条轨迹成本 ≈ 一次纯执行）。
- **随机种子**：`canonical_hash({round, episode_id, trace_index, step,
  invocation_index})` 派生，确定性可复现。
- **安全机制**：SafetyController 照常生效（可能否决随机动作），如实记录。
- **初始配方**：与 Phase 7 `never_current` 相同（`recipe.greedy_nearest_liveness`）。

## 4. 配方池（扩池后，round-1 冻结）

维度目标：FJSP × ASSIGNER × MAPF 三维都要有变化。

| 来源 | 配方 | 说明 |
|---|---|---|
| phase3_default（8） | greedy × 7 assigner × resastar；nearest_liveness | 冻结存量 |
| 新增 assigner（3） | fifo / greedy / load_balance × resastar | 进程内、无门禁、确定性 |
| 新增 MAPF（3） | nearest / hungarian / urgency × mapf.astar | 进程内、无门禁；astar 不支持动态故障 → 故障 episode 中被合法性掩码屏蔽（按状态掩码，非全局剔除） |
| 新增 FJSP（1） | `recipe.online_nearest_resastar`（fjsp.online_fjsp = CP-SAT） | **沿用 Phase 4 冻结证据**：`sequential/dynamic_fjsp.py` 的 10 项 ExternalSolverGate 全 True，镜像 digest 校验（two-stage-freeze-v0），服务 localhost:18120 |

池共 15 个配方。**fjsp.de / fjsp.pso / 9 个外部 MAPF（lacam/pibt/eecbs 等）
不入本轮池**：manifest 均为 shadow 层级、无已冻结的门禁证据（尤其
same-input replay 验证），纳入需先做 M-C0 完整验证——记为后续任务，
不属于本协议范围。

## 5. 选择规则（每 spec 选 golden）

1. 候选 = 本 spec 的 K 条 trace 中 `terminal_status == "TERMINAL"` 的；
2. 目标：最小 `evaluation_makespan`；
3. 平手 tie-break：更少 `switch_count` → 更小 `trace_index`；
4. 全部非 TERMINAL 时该 spec 本轮无 golden（如实记录，不降格选取）。

K 条 trace 的摘要全部保留；golden trace 落全量工件（见 §6）。

## 6. 数据 schema（`skycausal.golden-trace.v1`）

每 trace 目录：

```text
episodes/<episode_id>/trace<k>/
  trace.json            身份+轮次标注+结果（makespan/switch_count/状态）
  decision_log.json     每决策点一行：features 7 域、active_recipe、
                        admitted_action_ids（本协议新增字段）、
                        selected_first_action、commit_result、时延
  decision_roots/*.pkl  每决策点根快照（env+runtime，可复放/oracle 重算）
  trajectory_metrics.json  逐步指标（时序层）
  switch_log.json       仅 SWITCH 行
manifest.json           全局清单：round、池、K、种子规则、每 spec 摘要、
                        golden 指认、语义哈希
```

## 7. 成本门与试点

- 试点：1 个 spec × K=2（含 CP-SAT 配方可达性验证）+ 1 条全 KEEP
  轨迹做**对齐校验**。
- 全量：72 spec × K=8。预计超 2 小时或 10GB 则暂停确认（分级门控纪律）。
- CP-SAT 每步调用约 0.5–1s（budget 1s），含 online_fjsp 的轨迹显著更贵；
  试点实测后若单条 >10 分钟，则 CP-SAT 配方降级为分层子集覆盖
  （每 workload 家族抽 1 个 spec），在 manifest 中如实记录。

### 7.1 对齐校验结果与基线修正（2026-08-26 执行时发现）

原定与 Phase 7 存档（20260815）对齐——**失败但归因明确**：
`episode_identity` 中仅 `initial_physical_snapshot_hash` 漂移（环境层
代码在 0815 后有无意变更），原版 Phase 7 runner 用当前代码重跑
`never_current` 同样得 makespan 51.0（存档 63.0），即存档已不可复现。
修正后的对齐基线 = **当前代码重跑的 never_current**：
全 KEEP 轨迹与其 makespan/final_step/决策数/逐决策 feature_hash 与
state_hash 序列全部一致 → 采集器与冻结闭环语义逐位对齐 PASS。

环境漂移本身作为独立事实记录（影响所有 0815 存档的可复现性声明，
M-A0 保真度门需覆盖），不阻塞本采集——本采集的所有数据由当前代码
自洽生成并带完整身份哈希。

### 7.2 试点驱动的采样与健壮性修订（全量开跑前，2026-08-26）

试点（small_sparse 4 条 + burst_priority 4 条）暴露三个问题，据此修订：

1. **mapf.astar 配方撤出池**（池 15→12）：冷切换成功但中途必死
   （TransitionStatus.NO_PATH——裸 A* 无预约表，多 AGV 冲突无解）。
   证据：pilot t00/t01/t03。MAPF 维度扩展改由后续 M-C0 外部服务路线承担。
2. **采样分布从"动作集均匀"改为"KEEP 先验 + SWITCH 均匀"**：
   每决策点以 p_keep=0.7 保持、否则在合法 SWITCH 中均匀抽。理由：
   纯均匀（14 动作，P(切换)≈93%）在重负载下产生 21–43 次切换的
   churn 轨迹并 MAX_STEPS（pilot t00/t03），破坏 Phase 7 已确立的
   runtime continuity 机制；0.7 先验给出 ~12 切换/条，TERMINAL 率
   与探索度平衡。仍然是无模型随机（round-1 语义不变）。
3. **切换失败回退（switch-fallback）**：提交的 SWITCH 若 transition
   失败（INFEASIBLE/ERROR/NO_PATH/TIMEOUT/UNSUPPORTED/NO_ASSIGNMENT），
   同一决策点回退执行 KEEP 并记录失败尝试（`switch_fallback` 字段），
   不再让整个 episode 死亡。动机：CP-SAT 计划修订的
   "unresolved commitments" 取决于求解器输出而非纯状态，无法用准入
   掩码预判（pilot burst_priority t01 一步死亡）。KEEP 失败仍致命。
   已保留的 CP-SAT 状态级掩码（no_loaded_transport）仍然生效。
4. 工件去重：search_calls 不再重复写根快照 pickle，引用
   decision_roots 同步快照（重轨迹 ~29MB→约减半）。

### 7.3 全量成本预估（修订后）

burst_priority 重负载 ~59s/条（MAX_STEPS 520 步满跑）、small_sparse
~4s/条；6 workload 混合均值估 ~20-30s/条。72×8=576 条，单进程约
3-5h → 用 6 worker 进程并行压到 ~40-60min（12 核机器；CP-SAT 服务
单请求串行，p_keep=0.7 下碰撞率低）。磁盘估 4-7GB（去重后），
低于 10GB 门。

## 8. 已知限制（如实声明）

1. CP-SAT 为 wall-clock 求解器（deterministic=False）：trace 记录的是
   实际发生的行为；**精确逐位复放**不保证（Phase 4E 已记录该性质）。
   本协议的 golden 选取基于 realized makespan，不基于反事实标签，
   因此不违反 4E 的排除理由；但 round≥2 若需在含 CP-SAT 状态上做
   oracle 标签，须先过 quiescent+digest 复放纪律。
2. 随机轨迹的"最优"是 K 中的最优，非全局最优；轮次迭代的意义正在于此。
3. `rollout_count` 字段在本采集中的语义 = 采样器调用次数（无前瞻），
   decision_log 的 diagnostics 里有 `lookahead_rollouts: 0` 明示。

## 9. 验收清单

- [x] 全 KEEP 对齐校验 PASS（vs 当前代码重跑的 never_current；0815 存档因环境漂移不可复现，见 §7.1）
- [x] CP-SAT 服务健康 + 镜像 digest 校验 PASS（fjsp_service_check.json）
- [x] 池内 12 配方全部在数据中出现（assigner×10 各 350-395 次切换；
      liveness 311；online CP-SAT 51 次成功切入，其余被
      no_loaded_transport 掩码如实记录为拒绝）
- [x] 72 spec × K=8 = 576 条完成；504 TERMINAL / 72 MAX_STEPS；
      manifest_hash=85f25228…，fingerprint=2847152f…
- [x] 每 spec golden 指认完成且可追溯（trace_id + 种子规则）；
      golden makespan 均值 136.9 vs 全部 TERMINAL 轨迹均值 210.4
- [x] 磁盘 3.7GB（低于 10GB 门）；13,732 决策行全部带 admitted_action_ids；
      switch-fallback 共 4 次（如实记录）
