# 机器故障工序-机器组合 Value Gate 报告

## 一、结论

将单工序改派从“固定最早工序后选机器”扩大为“全 operation-machine pair
选择”后，动作差异覆盖充足、基础设施完全正确，但 terminal Value Gate 未通过。

主结果：

```text
42 disagreement units
15 independent clusters
21 win / 1 tie / 20 loss
mean improvement: -5.55
95% CI: [-24.17, 12.53]
```

不能将该方法作为论文正贡献。

## 二、方法

对照：

```text
固定 planned start 最早的 eligible operation
→ 用 v3 选择该工序的目标机器
```

新动作：

```text
枚举全部 eligible operations
→ 为每个工序选择最佳 v3 机器
→ 全局选择 predicted advantage 最大的 pair
```

两个动作都只改派一个工序，使用相同 PlanRevision 和物理执行流程。

## 三、Coverage Gate

| 指标 | 结果 |
|---|---:|
| multi-operation clusters | 17/40 |
| operation disagreement clusters | 15/40 |
| disagreement instances | 2 |
| disagreement topologies | 2 |

Coverage Gate 通过。

## 四、Infrastructure Gate

| 检查 | 结果 |
|---|---:|
| terminal branches | 360 |
| completion | 360/360 |
| invariant pass | 360/360 |
| runner errors | 0 |
| agreement outcome ties | 78/78 |
| agreement physical hashes | 78/78 |

实验差异确实来自 operation-machine pair 选择，而非执行污染。

## 五、Value Gate

| Cohort | Mean improvement | 95% CI |
|---|---:|---:|
| disagreement only | -5.55 | [-24.17, 12.53] |
| all units | -1.94 | [-8.62, 4.38] |
| agreement only | 0.00 | [0.00, 0.00] |

按实例：

| Instance | Mean | 95% CI | Win/Tie/Loss |
|---|---:|---:|---:|
| Kacem `k2` | +13.35 | [-13.43, 34.67] | 14/1/5 |
| Brandimarte `mk01` | -22.73 | [-43.00, -1.46] | 7/0/15 |

`mk01` 上全 pair 选择具有统计明确的负效应。

## 六、预测为什么失败

| Instance | Predicted gain | Realized | Pearson | Sign accuracy |
|---|---:|---:|---:|---:|
| `k2` | +20.80 | +13.35 | +0.548 | 70.0% |
| `mk01` | +44.50 | -22.73 | -0.036 | 31.8% |

v3 在 `mk01` 上预测收益更高，但真实结果更差。说明当前公式可能遗漏：

1. 被改派工序是否真正处于端到端 makespan 敏感链；
2. 跨 job 的机器排队传播；
3. 工序完成变早后，后继运输和机器资源是否真实可用；
4. `mk01` 更长工艺路线中的级联阻塞；
5. pair 插入导致的非局部机器竞争。

## 七、后续边界

下一步只允许做 `mk01` 与 `k2` 的误差分解：

- 对齐 predicted components 与 realized delay；
- 找出发生符号反转的物理状态；
- 判断缺失量能否在 branch point 在线观测。

在找到可泛化的物理变量前，不继续扩大恢复动作，不进入 Causal、BNN、Offline
RL 或 CBQ-IQL。
