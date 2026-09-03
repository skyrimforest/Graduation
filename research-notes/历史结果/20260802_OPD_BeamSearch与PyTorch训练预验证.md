# OPD、Beam Search 与 PyTorch 干预网络预验证

## 1. 本阶段问题

首轮实验已经证明昂贵 LaCAM* refinement 能修复少数困难 episode，但固定的 40-step 阈值有两个问题：

1. 阈值以下仍可能存在有价值的 refinement；
2. 阈值以上也并非每次 refinement 都有收益。

因此需要学习“何时值得花查询预算”，而不是把 LaCAM* 永久打开。

## 2. OPD 对当前场景的可落地启发

LLM 场景中的 On-Policy Distillation 不能机械照搬到工厂调度。当前可落地版本是：

1. 学生策略实际运行 GridFactoryEnv；
2. 在学生访问到的滚动状态上调用 LaCAM/LaCAM* 教师；
3. 教师通过 `/probe` 返回反事实轨迹长度，但不替换在线计划；
4. 学生学习 refinement 收益和 wall-clock 成本；
5. 后续只在预测净收益超过预算门槛时进行真实干预。

这保留了 OPD 最重要的性质：监督分布来自学生自身访问状态，而不是静态离线状态或教师轨迹。

### 已完成的隔离验证

`/probe` 不修改活动规划缓存，也不推进未来规划 seed。对 `map0000/seed42`：

- 无 probe：makespan 315，84 个 base plans，2 次真实 refinement；
- 50% probe：makespan 315，84 个 base plans，2 次真实 refinement；
- 额外产生 46 次反事实查询。

因此 probe 数据不会通过缓存或随机 seed 污染在线 outcome。

## 3. Beam Search 的适用边界

### 不适合

Beam search 不应替代底层 MAPF 安全求解器。仅用高层 beam 输出逐车动作，无法自然保证：

- vertex conflict；
- edge swap conflict；
- 共享 dock 的终点唯一性；
- 动态重规划后的轨迹一致性。

### 适合

后续可在三个高层位置使用 beam search：

1. 对机器选择和工序派工保留 top-k 候选；
2. 对重复 dock 的 winner、waiting junction 和 clearance 顺序进行候选搜索；
3. 对“无 refinement / 200ms refinement / 500ms refinement”形成预算动作 beam。

每个 beam candidate 仍交由 LaCAM 验证，最终比较预测 makespan 改善和查询成本。这样 beam search 扩展高层干预空间，LaCAM 保证底层可行性。

## 4. 反事实数据

数据入口：

`codebase/SkyEngine/experiment/skycausal/results/routing_opd_probe_10maps_3seeds_queries.jsonl`

数据规模：

- 学生访问状态：2528；
- 有教师 outcome 的状态：600；
- 成功的随机 probe outcome：490；
- refinement 有正收益：208；
- 零收益或负收益：392。

相比只有固定阈值 outcome 的 v0 数据：

- v0：112 条 outcome，98 正、14 非正；
- probe：600 条 outcome，208 正、392 非正。

随机 probe 明显缓解了“模型只看到困难正例”的选择偏差。

## 5. PyTorch 网络

实现：

`codebase/SkyEngine/experiment/skycausal/intervention_net.py`

训练镜像：

`codebase/SkyEngine/experiment/skycausal/training.dockerfile`

网络是共享 MLP 编码器和三个任务头：

1. `benefit_head`：预测 refinement 是否缩短轨迹；
2. `delta_quantile_head`：预测轨迹缩短量的 P10/P50/P90；
3. `cost_head`：预测教师查询 wall-clock。

输入包含 16 个查询前可观测特征：

- 地图尺寸和障碍密度；
- active AGV 数；
- 重复 dock 数、重定位目标数、dock 邻域 idle 数；
- Manhattan/BFS 距离统计；
- start/goal junction 比例；
- 初始 LaCAM 轨迹长度；
- base query 时间。

Checkpoint：

`codebase/SkyEngine/experiment/skycausal/models/intervention_mlp_opd_v1.pt`

## 6. 预验证结果

训练地图：`0000` 至 `0007`。

未见验证地图：`0008`、`0009`。

| 指标 | v0，无随机 probe | v1，加入随机 probe |
|---|---:|---:|
| Train outcomes | 89 | 495 |
| Validation outcomes | 23 | 105 |
| Validation accuracy | 65.2% | 80.0% |
| Validation precision | 65.2% | 60.0% |
| Validation recall | 100.0% | 37.5% |
| Delta MAE | 5.20 steps | 0.85 steps |
| Query-cost MAE | 0.153s | 0.047s |

v0 的 accuracy 等于正例率，实际退化为“全部查询”。v1 能拒绝多数无收益查询，并显著改善收益量和成本预测。

## 7. 如何解释当前结果

### 可以说明

1. 学生访问状态上的随机教师 probe 能显著改善 outcome 覆盖。
2. 简单 PyTorch 多任务网络已经包含可泛化到未见地图的预测信号。
3. 轨迹收益和查询成本可以同时建模，为预算决策提供基础。

### 不能说明

1. v1 尚未在线替代固定阈值，不能声称减少查询后仍保持 30/30 完成。
2. 当前 probe 率为 20%，不是完整随机对照，仍存在部分选择偏差。
3. 数据只来自 J10P5M6、4 AGV 和 10 张迷宫。
4. MLP 还没有利用显式图拓扑，跨尺寸泛化能力未验证。
5. 当前不是 RL 结果；没有必要为了术语使用 RL。

## 8. 下一轮训练建议

1. 将 v1 作为行为克隆/干预预测初始化，不立即使用 RL。
2. 在线策略先采用保守规则：
   - 预测 P10 收益大于 0；
   - 预测 P50 收益/成本超过预算阈值；
   - 对 OOD 或高不确定状态回退固定 40-step teacher。
3. 使用受控 5%–10% probe 持续收集学生新分布数据，形成真正的迭代 OPD。
4. 在线比较固定阈值、MLP 门控和 oracle outcome 三个查询策略。
5. 只有在序列预算分配明显需要长期信用分配时，再引入 Offline RL/IQL；当前监督学习更稳定、更可解释。
6. Beam search 优先用于高层 dock reservation 和机器选择，不修改底层安全求解。
