# 开放式 Solver Catalog 与真实 FJSP Probe 首轮实现记录

日期：2026-08-11

状态：最小 catalog、真实 FJSP shadow probe、preflight-only calibration runner 已实现；
9/9 历史 fixture immutable preflight 通过；新 calibration cohort 仍被协议阻断。

## 一、本轮目标

本轮只实现开放式元搜索的第一个最小闭环：

```text
Solver Manifest
-> Solver Catalog
-> SolverOption
-> OnlineFJSPGateway
-> StatelessFJSPOrchestrationAdapter
-> TwoStageInstrumentationRunner.run_live_single
-> OptionProbeResult
```

首批只覆盖：

```text
CP-SAT
DE
PSO
```

本轮没有接入 MAPF，没有执行 solver switching，没有训练选择器，也没有访问新的
calibration、pilot 或 confirmation cohort。

## 二、新增实现

### 2.1 Solver Manifest

新增：

```text
experiment/skycausal/solver_manifest.py
```

每个 manifest 统一声明：

```text
solver id/version
domain
algorithm
service URL
immutable image digest
config schema
default config
budget range
capabilities
safe switch boundary
runtime budget/seed binding
resource requirements
admission tier
```

参数校验不依赖求解器专用控制器分支，当前支持：

```text
object
array
integer
number
string
boolean
required
enum
minimum/maximum
additional_properties
```

### 2.2 Solver Catalog

新增：

```text
experiment/skycausal/solver_catalog.py
```

提供：

```text
从目录发现 manifest
拒绝重复 solver id
按 domain/capability 筛选
创建动态 SolverOption
校验 option 与 manifest hash
生成稳定 catalog hash
```

新增求解器不需要扩充 controller 固定输出维度。

### 2.3 首批 FJSP manifests

新增：

```text
experiment/skycausal/manifests/fjsp/fjsp.cp_sat.json
experiment/skycausal/manifests/fjsp/fjsp.de.json
experiment/skycausal/manifests/fjsp/fjsp.pso.json
```

三份 manifest 绑定 Two-Stage freeze 镜像：

```text
CP-SAT:
  sha256:56e8c4c529bc33e110e27b5d84b4b03246375355223dac2863a7ff12433e75c4

DE:
  sha256:04b346e3e08af14a9a13f5a425b703de2884a53de7a0e8b34f97d42d8e8248ab

PSO:
  sha256:12e8f6d18212dc5e23b4d1ad4ed8b2c3d103fea478be9437f0ccbeca30925016
```

当前 manifest 明确标记：

```text
admission_tier = shadow
budget_range_status = development_candidate_not_calibrated
```

因此 `500..12000 ms` 只是开发候选范围，不是正式冻结的 probe grid。

### 2.4 真实 FJSP Probe Evaluator

新增：

```text
experiment/skycausal/orchestration_probe_evaluator.py
```

`FJSPOrchestrationProbeEvaluator` 会：

```text
校验 SolverOption 和 manifest
-> 注入成对 planning seed
-> 按 manifest 绑定 runtime budget
-> 创建真实 OnlineFJSPGateway
-> 创建 StatelessFJSPOrchestrationAdapter
-> 运行 live shadow stage
-> 观察 solver progress
-> 在 guard 处请求 cooperative stop
-> 导出并认证 incumbent
-> cleanup 和 audit
-> 返回 OptionProbeResult
```

它直接复用现有 `TwoStageInstrumentationRunner.run_live_single`，没有复制第二套 deadline
和 cleanup 生命周期。

探测语义当前固定为：

```text
fresh_stateless_restart
```

同一候选的重复 probe 是新的无状态运行，不冒充 native continuation。

## 三、采样 seed 公平性修正

原 v0 使用：

```text
planning_seed = planning_seed_base + global_probe_index
```

这会导致不同候选的第一次 probe 使用不同 seed，随机性可能被误判为算法差异。

本轮改为：

```text
planning_seed = planning_seed_base + candidate_visit_index
```

结果是：

```text
所有候选第一次 probe 使用同一 seed
所有候选第二次 probe 使用下一相同 seed
```

sampler config 新增：

```text
planning_seed_policy = paired_by_candidate_visit
```

每次 attempt 记录：

```text
candidate_visit_index
planning_seed
```

## 四、可复现 catalog hashes

仓库 manifest 的 base catalog：

```text
catalog:
e137cb32a68dee7daf07865487d90134d4bd5a30f6bac0ccaedd3224022a8c56
```

各 manifest：

```text
fjsp.cp_sat:
58946854efe58aa536f2c5bdcbfb1ca19fc005939ef674c6d5db86fec5280b17

fjsp.de:
e285efc676a2d52fb7a03a1210cab0378883f0ba27af5a4036bba5ab4a5a236d

fjsp.pso:
b7dca86269dffb085bb248e3343da59489d94ac475723bfaa0c2ca7fe47ce26d
```

`.gitignore` 已增加精确例外，使这些 JSON manifest 可进入版本控制；其他 JSON ignore
规则不变。

## 五、新增测试

新增：

```text
test/skycausal/test_solver_catalog.py
test/skycausal/test_orchestration_probe_evaluator.py
```

覆盖：

```text
三份冻结 manifest 可加载
manifest hash 防篡改
未知参数拒绝
参数范围校验
runtime seed 和 budget binding
capability admission
增加新 solver 不修改 controller schema
option 与 manifest hash 绑定
正常完成返回 certified probe
运行中 solver 在 guard 处 cooperative stop
无 incumbent 计 algorithmic failure
失败后 active request 清零
probe 不能超过 option budget
```

同时更新 `test_portfolio_sampling.py`，验证成对 seed policy。

相关测试结果：

```text
Ran 104 tests
OK
```

测试范围包括：

```text
portfolio sampling
solver catalog
real probe evaluator fixture
FJSP adapter
orchestration contract
trajectory
two-stage instrumentation
two-stage pilot/freeze protocol
cooperative preflight
```

## 六、历史 fixture 真实服务 smoke

### 6.1 范围

只使用历史开发输入：

```text
fixture:
artifacts/skycausal_fjsp_freeze_validation_v0_257dfb5c_7524e82d/
residual_problem.json

residual problem hash:
da6425ed05ef48a1f0499735c0ad202298e26d891bb2e2869faad489850d302e

snapshot hash:
92539be29998bbe3ae96de8295e9081ef26df239fabda50ae641f79004363226

scope hash:
eb76aee155a4a808c20beb094e58245797d63a1a2bab4150445b0c90c1860782
```

临时启动三份 exact freeze image，使用独立 localhost 端口。现有 publication 容器没有
停止或修改。运行结束后，临时容器已删除。

### 6.2 Smoke 配置

```text
probe budget: 1500 ms
cooperative finalize reserve: 250 ms
poll interval: 10 ms
mode: shadow only
```

因为临时 endpoint 替换为 localhost，smoke catalog hash 为：

```text
a746b6374f3243bb00a48179bed961efc7f9602b0d48480ee9eaabafb290405d
```

它与仓库 base catalog hash 不同，这是 endpoint provenance 的预期结果。

### 6.3 结果

| Solver | 状态 | 完成方式 | 目标值 | 端到端耗时 | 首个 incumbent | finalization |
|---|---|---|---:|---:|---:|---:|
| CP-SAT | completed | normal completion | 38 | 442.276 ms | 363.655 ms | N/A |
| DE | completed | cooperative stop | 38 | 1324.421 ms | 127.370 ms | 47.726 ms |
| PSO | completed | cooperative stop | 38 | 1350.535 ms | 121.753 ms | 68.399 ms |

三次运行：

```text
feasible = true
deadline_overrun = false
certified bundle = present
final active_request_count = 0
```

### 6.4 正确解释

本 smoke 只能证明：

```text
真实 HTTP 调用可用
progress observation 可用
normal completion 可认证
cooperative stop 可认证
cleanup 后请求归零
OptionProbeResult 可由真实 adapter 生成
```

本 smoke 不能证明：

```text
1500 ms 是合理正式预算
三个 solver 存在质量互补
MCTS 有价值
某 solver 更优
结果可用于论文
```

三个 solver 在该单一 fixture 上都得到 `38`，不提供选择价值证据。

本次 smoke 由开发命令直接执行，尚未通过冻结 runner 生成完整 immutable artifact；
本文只记录摘要，不把它升级为正式证据。

## 七、当前完成度

```text
P1 Solver Manifest:                DONE
P1 Solver Catalog:                 DONE
P1 CP-SAT/DE/PSO manifests:        DONE
P2 OrchestrationProbeEvaluator:    DONE
P2 fixture/contract tests:         DONE
P2 historical real-service smoke:  DONE
calibration v0 preflight protocol:  DONE
protocol/implementation SHA bind:   DONE
validate/estimate runner:           DONE
historical preflight runner:        DONE
immutable preflight artifact:       9/9 PASS
resume/checksum verification:       PASS

new calibration cohort:            NOT ACCESSED
probe budget freeze:               NOT DONE
MCTS value experiment:             NOT AUTHORIZED
MAPF probe evaluator:              NOT STARTED
```

### 7.1 冻结 preflight artifact

路径：

```text
artifacts/skycausal_fjsp_probe_preflight_v0_2fdc3349/
```

关键身份：

```text
protocol SHA256:
2fdc33493e7bbd9cf6b48b5585fe3117e43d2c92a86da5896c5ccaf5cfe25ade

summary hash:
00d69476d6412aa18458fcd09f8e5dd238098f42cdc5cc3f8a8c1768b1e24f71

checksums hash:
c2d9a130774fa0eaa53ce51290c303c83ab223fa3bd8eaa4160c559d23315d87
```

Gate：

```text
record_count:                 9/9
completed_count:              9/9
feasible_count:               9/9
deadline_overrun_count:         0
schedule_audit_failure_count:   0
health_failure_count:           0
orphan_request_count:           0
```

三次重复摘要：

| Solver | Objectives | 平均端到端耗时 | 完成方式 |
|---|---|---:|---|
| CP-SAT | 38 / 38 / 38 | 335.724 ms | 3 次正常完成 |
| DE | 38 / 38 / 38 | 1310.356 ms | 3 次协作停止 |
| PSO | 40 / 38 / 40 | 1333.180 ms | 3 次协作停止 |

PSO 的波动只说明 stochastic trajectory 确实需要重复和成对 seed，不能在单一历史
fixture 上形成求解器优劣结论。

### 7.2 runner 当前权限

已允许：

```text
--validate-only
--estimate-workload
--historical-preflight
--resume
```

协议强制拒绝：

```text
--capture-only
--execute
--analyze-only
```

当前预估：

```text
future calibration clusters: 16
solver count:                 3
budget points:                5
replicates:                   3
maximum requests:           720
maximum service hours:     0.44
```

相关 SkyCausal 全量回归：

```text
Ran 343 tests
OK
```

## 八、下一步（在线主实验修正版）

v0 已由 artifact hash 冻结，禁止原地修改授权。原计划紧接着创建 capture-only
协议并访问 `600..639`；经在线研究目标复核，该任务降级为辅助轨迹校准，不再是最高
优先级。

新的实施顺序：

```text
1. 定义连续物理时钟和当前安全执行前缀
2. 定义 commit-time freshness audit、重对齐和局部修复
3. 实现最小 online episode runner
4. 用历史 development fixture 通过在线基础设施 Gate
5. 再将 600..639 用于受控快照诊断和预算校准
6. 把冻结后的分配器放回完整在线 episode
```

受控 snapshot 仍有价值，但不能支撑“系统符合在线动态制造要求”的主结论。论文实验
结构以
[`20260811_SkyCausal论文实验设计章节结构_在线主实验修正版.md`](20260811_SkyCausal论文实验设计章节结构_在线主实验修正版.md)
为准。
