# SkyCausal Independent Confirmation v2.1 Claim Matrix

日期：2026-08-06

状态：`FROZEN_FOR_EXECUTION`

本表只适用于未观察的 v2.1 cohort `seed 300..349`。v1 artifact 的统计子 Gate
为正、Infrastructure Gate 为负，因此 v1 的 C2/C4 仍为 FAIL；v2.1 不后验覆盖
v1。

冻结 v2 protocol `98a99cc7...` 在第 18 个 normal Root infrastructure
repetition 停止，candidate capture/planning/heldout 均为 0。v2.1 只把带
`deadline_audit(status=completed, returncode!=0)` 的 FJSP `worker_error`
分类为 accounted request；该分支仍是 failed branch、零 backup 和 runtime
fallback。cohort、预算、profile、统计与通过阈值均不变。

| ID | 拟支持主张 | 通过条件 | 冻结前状态 |
|---|---|---|---|
| C0-v2.1 | 双 capture、snapshot fork、CRN 和 replay 保持同源物理语义 | 40/40 selected snapshots 两次 capture 均 eligible 且 semantic signature 相同；全部 replay physical invariants PASS | NOT RUN |
| C1-v2.1 | 六个联合 profiles 存在互补 headroom | oracle improvement 均值与 stratified-bootstrap 95% CI 下界均大于 0；FJSP/MAPF strict winner algorithm 各至少 2 类 | NOT RUN |
| C2-v2.1 | Root MC `terminal,k=1` 在独立 heldout 上优于 global best fixed | 40/40 retained；mean improvement > 0；95% CI lower > 0；Infrastructure Gate 全通过 | NOT RUN |
| C3-v2.1 | 主结论不依赖弱 static baseline | C2-v2.1 独立优于 global best fixed；topology best fixed、runtime fallback、LOCO static selector、oracle 完整报告 | NOT RUN |
| C4-v2.1 | hard deadline 下搜索可安全退化 | component 600/600；root normal 25/25；root forced-deadline 25/25；无 partial backup、unaccounted termination、late request、orphan session 或 physical invalid | FORMAL NOT RUN |
| C5-v2.1 | 方法具有可量化的 quality-latency-fallback 工作区间 | `2/5/10/12 s` 全部报告 coverage、fallback、cost 和 CI；10/12 秒主工作点依赖 C2-v2.1 PASS | NOT RUN |
| C6 | 深层 UCT 当前不值得额外复杂度 | 冻结 development negative result，只作为消融/边界；禁止继续调参 | FROZEN NEGATIVE |
| C7 | 跨规模或拓扑外推 | 需要另行预注册 robustness cohort | NOT AUTHORIZED |

论文主证据链最低要求：

```text
C0-v2.1 PASS
C1-v2.1 PASS
C2-v2.1 PASS
C4-v2.1 PASS
C5-v2.1 complete reporting
```

禁止用 C1-v2.1 的 oracle headroom 替代 C2-v2.1 的实际 controller value，也
禁止用 v1 的正效果量、phase 后 quiescence、v2 失败 stress 或 development
artifact 填补 v2.1 Gate。

冻结前 development preflight 达到 `600/600 + 25/25 + 25/25`，50 个 Root run
终态 active request 和 MAPF session 均为 0；该结果只授权正式执行，不计作
C4-v2.1 publication evidence。
