# 统一动作 schema 的 30 状态在线开发实验

日期：2026-08-11

证据等级：开发证据，不授权正式质量结论，不授权 active Q。

## 目的

本轮验证三件事：

1. 将 `keep_current` 与 `solver + config + probe budget` 放入同一动作 schema；
2. 在最新状态 freshness/rebase 修正链路上重跑连续物理时钟在线实验；
3. 检查 solver-specific 最小可辨识预算能否修复 Root MCTS 对 CP-SAT 的覆盖盲点。

## 协议

```text
状态 seeds：1000..1029
独立状态：30
策略：7
episode：210
候选：keep-current、CP-SAT、DE、PSO
probe schedule：500ms、1000ms
总搜索窗口：4000ms
commit reserve：500ms
active Q：关闭，仅 shadow 记录
```

七种策略：

```text
keep_current
fixed_cp_sat
fixed_de
fixed_pso
successive_halving
mcts
mcts_calibrated
```

校准 MCTS 的首轮预算：

```text
CP-SAT：1000ms
DE：500ms
PSO：500ms
```

预算门槛由 `SolverOption.metadata` 声明，算法不硬编码 solver 名称。

## 配对与安全审计

```text
action-independent state match：PASS
complete strategy matrix：PASS
decision/outcome action match：PASS
deadline overrun：0
commit reserve overrun：0
health failure：0
physical clock failure：0
transport failure：0
unfinished episode：2
```

未完成 episode 保留 capped terminal timeline，不做删除，避免幸存者偏差。

## 主要结果

| 策略 | Mean terminal | 相对 keep-current | Mean oracle regret |
|---|---:|---:|---:|
| keep-current | 503.70 | 0.00 | 39.00 |
| fixed CP-SAT | 496.80 | -6.90 | 32.10 |
| fixed DE | 504.90 | +1.20 | 40.20 |
| fixed PSO | 526.03 | +22.33 | 61.33 |
| successive halving | 510.53 | +6.83 | 47.63 |
| original MCTS | 498.20 | -5.50 | 35.30 |
| calibrated MCTS | 506.00 | +2.30 | 43.10 |

原始 MCTS 相对 keep-current：

```text
mean = -5.5
95% bootstrap CI = [-21.90, 10.93]
16 胜 / 1 平 / 13 负
```

校准 MCTS 相对原始 MCTS：

```text
mean = +7.8
95% bootstrap CI = [-6.10, 22.53]
11 改善 / 6 持平 / 13 退化
```

校准 MCTS 相对 fixed CP-SAT：

```text
mean = +9.2
95% bootstrap CI = [-2.37, 21.50]
```

## 覆盖诊断

原始 MCTS：

```text
CP-SAT 500ms 首轮可行：0/30
最终选择：CP-SAT 0、DE 15、PSO 14、keep-current 1
```

校准 MCTS：

```text
CP-SAT 1000ms 首轮可行：28/30
最终选择：CP-SAT 15、DE 2、PSO 12、keep-current 1
```

校准确实修复了 CP-SAT 覆盖盲点，但平均终局没有改善。

## 结论

本轮否定以下简单方案：

```text
给慢启动 solver 一个固定的更大首轮预算
=> 自动得到更好的在线元调度
```

原因是候选覆盖不是最终目标。增加 probe 预算会改变物理状态、计划新鲜度和剩余执行
价值；solver 内部 makespan 也不能可靠代表完整 episode 终局。

下一版 Root 分配需要联合建模：

```text
首次可行概率
+ probe runtime / state drift
+ 最新状态执行价值
+ freshness 后可提交概率
```

active Q 继续禁用。应先使用严格按状态留组验证该联合评分是否稳定超过原始 MCTS、
fixed CP-SAT 和 makespan-only，再冻结独立确认协议。

## 运行环境限制

30 状态开发 cohort 使用三条独立容器 lane 并行运行，但宿主机 CPU 仍然共享。相同
seed 1000 的单独 smoke 与三 lane batch 出现不同终局，说明严格 wall-clock probe 会
受到宿主机负载影响。该问题不改变动作独立状态 hash 的配对结果，但会影响候选在有限
时间内得到的 incumbent 和物理推进步数。

因此本轮只能作为算法开发证据。正式确认必须采用资源隔离容器，或以单 lane 顺序复跑，
并加入同 seed wall-clock 重复性审计。

## 可复现产物

```text
artifacts/skycausal_online_meta_unified_action_dev_v1/cohort_30state/
artifacts/skycausal_online_meta_unified_action_dev_v1/cohort_30state_calibrated/
artifacts/skycausal_online_meta_unified_action_dev_v1/analysis_30state_calibrated.json
```

分析内容 hash：

```text
a92c03ddb8f0e380cc557c5592c21e94c148602fa77df8d5bfc313c8140fb80c
```

分析文件 SHA256：

```text
84683ab83449f5e383977ade643562a46653aaea55ba17cefd7c309d6b2e99db
```

代码回归：

```text
379 tests
OK
```
