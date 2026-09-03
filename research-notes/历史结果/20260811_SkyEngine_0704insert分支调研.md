# SkyEngine `0704insert` 分支调研

日期：2026-08-11

调研对象：

- GitHub 分支：<https://github.com/skyrimforest/SkyEngine/tree/0704insert>
- 分支提交：`527bc18032aa5e53e882e11daaad3181e81bdff6`
- 插单核心提交：`595243c1e4378f56ccd3f46de00989bb89ff2ab8`
- 对照仓库：当前本地 `codebase/SkyEngine` 与 `codebase/SkyEngine-FJSP`

## 1. 结论

`0704insert` 的研究方向是正确的：它尝试将“运行中插入新订单”建模为一个完整的在线
制造事件，而不是简单地向列表追加一个 Job。分支已经设计并部分实现：

```text
HTTP 批量插单
→ 线程安全排队
→ 构造剩余 FJSP
→ 调用 PSO 重排
→ 将新 Job 加入物理环境
→ 特急任务抢占普通加工
→ SSE/JSONL 状态与事件观测
```

但该分支不能视为已经打通的可运行产品链路。代码级与运行时审计确认两个 P0 阻断：

1. `sim_server._run_loop()` 调用了不存在的 `_drain_pending_inserts()`，`/sim/play`
   后第一个物理步立即进入 `error`；
2. SkyEngine 客户端固定调用 FJSP `POST /replan`，但 `SkyEngine-FJSP` 源码和本机
   `skyengine-fjsp-pso:latest` 镜像都没有该路由。

因此当前准确状态是：

```text
插单数据结构、状态机、抢占局部语义和单元测试已存在；
在线主循环与远程重排服务契约没有闭合；
没有端到端证据证明一个插入订单能完成运输和加工。
```

这也解释了为什么当前 SkyCausal 实验虽然继承了该分支，却没有直接使用
`sim_server` 插单链路。

## 2. 分支基线

GitHub 页面和 Git 审计结果一致：

```text
branch:        0704insert
head:          527bc18032aa5e53e882e11daaad3181e81bdff6
latest commit: Merge remote-tracking branch 'origin/hjy' into 0704insert
relative main: 69 commits ahead, 1 commit behind
```

插单核心提交 `595243c` 修改 11 个文件：

```text
992 insertions
192 deletions
```

主要文件：

```text
sim_server.py
sky_executor/grid_factory/factory/assign_env.py
sky_executor/grid_factory/factory/Utils/structure.py
sky_executor/grid_factory/factory/Component/JobSolver/http_solver/http_job_solver.py
sky_executor/grid_factory/factory/Component/Assigner/nearest_assigner/assigner.py
sky_executor/utils/diff.py
test/env_test/test_job_insertion.py
test/env_test/test_urgent_preemption.py
```

当前本地 `SkyEngine` HEAD 是该分支的后代：

```text
0704insert → 当前 HEAD：63 个后续非 merge commit
```

更关键的是，当前 [sim_server.py](../codebase/SkyEngine/sim_server.py) 与
`0704insert` 中的文件 SHA256 完全相同：

```text
b526407ee57b4722684416f02064888daa676988a2fbe699ef6adac421315af8
```

所以以下 `sim_server` 问题不仅存在于远程分支，也仍存在于当前本地项目。

## 3. 已实现的架构

### 3.1 插单入口

[SimulationManager.enqueue_insert_jobs](../codebase/SkyEngine/sim_server.py#L649-L709)
提供：

- 仅在 episode 运行期间接受请求；
- 第一版限制为 `PSO + nearest`；
- 单次支持 1 到 20 个 Job；
- 每个 Job 支持 1 到 20 道工序；
- 校验候选机器、重复机器和正加工时间；
- 支持部分接受，坏 Job 不阻断同批其他 Job；
- 使用锁生成唯一 `request_id` 和 `job_id`；
- 将请求放入 `_pending_inserts`，不在 HTTP 线程直接修改环境。

请求实际格式是：

```json
{
  "machines": 6,
  "jobs": [
    [
      [
        {"machine": 0, "processing": 3},
        {"machine": 1, "processing": 5}
      ]
    ]
  ],
  "extensions": {
    "job_metadata": [
      {
        "name": "urgent-order",
        "priority": 200,
        "due_in_steps": 30
      }
    ]
  }
}
```

### 3.2 插单状态机

每个插单请求维护：

```text
queued
→ replanning
→ scheduled
→ transporting
→ processing
→ completed
```

异常状态是：

```text
failed
```

状态、`revision`、延迟、Job ID 和错误信息会进入：

- `/sim/state`；
- `/stream/events`；
- `/stream/metrics`；
- episode `events.jsonl`。

### 3.3 剩余问题构造

[_build_replan_problem](../codebase/SkyEngine/sim_server.py#L719-L815) 会读取当前物理状态：

- 已完成、加工中、暂停中的工序；
- 机器当前加工和输入队列；
- 特急预约；
- 已分配和运输中的任务；
- 前序工序完成时间；
- 当前机器可用时间；
- 新插入 Job 的候选机器、加工时间、优先级和交期。

它尝试冻结已经承诺的部分，仅将仍为 `PENDING` 的剩余工序交给远程求解器。

该思想与当前 SkyCausal 的 `ResidualFJSPProblem` 相同，但两套 schema 和实现彼此独立。

### 3.4 特急抢占

当新 Job 的 `priority >= 200` 时，分支允许暂停普通加工：

```text
普通工序 PROCESSING
→ 记录已加工时间
→ 计算 remaining_proc_time
→ 状态改为 SUSPENDED
→ 放入 machine.suspended_ops
→ 特急任务优先执行
→ 普通工序恢复且不重新采样加工时间
```

相关状态字段包括：

```text
Operation.remaining_proc_time
Operation.accumulated_process_time
Operation.preemption_count
Machine.suspended_ops
Machine.urgent_reservations
```

`NearestAssigner` 也被改成先按优先级分层，再在最高优先级任务内部按距离选择。

### 3.5 可观测性

`DiffEmitter` 增加：

```text
job_inserted
job_preempted
job_resumed
urgent_job_arrival
job_replan_started
job_replan_completed
job_replan_failed
job_insertion_phase_changed
```

这部分设计可以保留，适合作为在线控制面和论文事件审计的观测层。

## 4. 已确认的阻断问题

### P0-1：在线主循环调用不存在的方法

[sim_server.py:L1253-L1265](../codebase/SkyEngine/sim_server.py#L1253-L1265) 同时出现：

```python
self._drain_pending_inserts()
...
self._drain_insert_queue()
```

但 `SimulationManager` 只定义了 `_drain_insert_queue()`，没有定义
`_drain_pending_inserts()`。

实际运行最小复现：

```text
AttributeError:
'SimulationManager' object has no attribute '_drain_pending_inserts'

episode_status = error
running = False
```

这不是只有收到插单请求才触发的问题。`_run_loop()` 每步无条件调用它，所以普通
`POST /sim/play` 也会在第一步失败。

该问题看起来来自两版插单实现合并后的残留：

- `_pending_inserts` 和 `_insert_lock` 在 `__init__` 中重复初始化；
- 旧注释保留 `_drain_pending_inserts` 名称；
- 新实现方法名改为 `_drain_insert_queue`；
- 主循环同时保留了旧调用和新调用。

### P0-2：FJSP `/replan` 服务端不存在

[HTTPJobSolver.replan](../codebase/SkyEngine/sky_executor/grid_factory/factory/Component/JobSolver/http_solver/http_job_solver.py#L101-L116)
固定调用：

```text
POST http://fjsp:8002/replan
```

但 `SkyEngine-FJSP` 当前 PSO server 只有：

```text
/health
/solve
/progress/<request_id>
/stop/<request_id>
/cancel/<request_id>
/init
/plan
/reset
```

本机实际镜像 `skyengine-fjsp-pso:latest` 的 Flask `url_map` 也没有 `/replan`。

因此修复 P0-1 后，插单会进入：

```text
queued → replanning → failed
```

### P0-3：抢占元数据没有端到端传递

`HTTPJobSolver._serialize_obs()` 只发送：

```text
job_id
op_id
候选机器
加工时间
```

没有发送：

```text
priority
request_id
due
release
当前工序状态
```

PSO `/plan` 返回的 `transfer_requests` 也没有 `priority` 和 `request_id`。因此普通
`/plan` 链路构造出的 `RoutingTask.priority` 会使用默认值 0，无法触发
`priority >= 200` 的特急抢占逻辑。

除非未来 `/replan` 在服务端维护一套额外状态并输出完整字段，否则当前抢占只在局部
单元测试成立，不能证明端到端成立。

## 5. 其他工程问题

### 5.1 重排激活不是原子的

[_drain_insert_queue](../codebase/SkyEngine/sim_server.py#L830-L870) 在远程调用成功后直接：

1. append 新 Job；
2. 修改 `hash_operations`；
3. 删除待分配和缓冲运输；
4. 修改 observation；
5. 增加 epoch 和 revision。

如果第 2 到第 4 步中途异常，没有状态快照和回滚。现有测试只覆盖“远程 solver
调用前失败时环境不变”，没有覆盖“局部写入后失败”。

当前项目已有 `PlanRevisionActivator` 的快照、校验、激活和回滚机制，应复用该机制，
不应继续扩展这套直接变异逻辑。

### 5.2 设计文档与代码契约不一致

分支中的 `0704插单spec重构.md` 写的是：

- `machines` 可省略；
- 扩展字段为 `release_offsets/due_times/priorities`；
- 保留 `POST /sim/insert_job` 单数兼容接口。

实际代码是：

- `machines` 强制必填且必须等于当前机器数；
- 扩展字段是 `extensions.job_metadata`；
- 只提供 `POST /sim/insert_jobs`；
- 错误通过 HTTP 200 内的 `status=error` 表达，而不是文档中的 HTTP 400。

文档验收清单仍全部未勾选，不能作为完成证据。

### 5.3 单元测试覆盖制造局部语义，没有覆盖在线闭环

分支新增的 10 个测试当前全部通过：

```text
10 passed
```

覆盖：

- 部分接受；
- 并发 ID 唯一；
- 机器数校验；
- solver 失败前环境不变；
- 当前加工、机器队列和运输目的地冻结；
- 普通工序被特急任务暂停；
- 特急任务不可抢占另一特急任务；
- 暂停工序恢复时不重新采样。

没有覆盖：

- `SimulationManager._run_loop()`；
- `/sim/create → /sim/play → /sim/insert_jobs`；
- FJSP `/replan`；
- 插单后的 AGV 运输；
- 插入 Job 最终完成；
- Docker 三服务联调；
- reset、stop 与插单并发；
- 激活中途失败回滚。

这正是“10 个测试通过，但主循环仍然第一步崩溃”的原因。

### 5.4 Docker 在线模式当前不能直接启动

[docker-compose-online.yaml](../codebase/SkyEngine/docker-compose-online.yaml) 还有三项前置问题：

1. 要求外部网络 `skyengine-net`，当前本机不存在；
2. 默认镜像 `skyengine-online:latest` 当前本机不存在；
3. `online.dockerfile` 复制 `pyproject-online.toml`，但 `.dockerignore` 没有放行该文件，
   干净构建上下文会排除它。

此外 compose 用 bind mount 覆盖镜像内 `sim_server.py` 和 `sky_executor`，不适合正式
实验的不可变镜像复现。

## 6. 与当前 SkyCausal 的关系

### 6.1 已继承

当前项目已经继承：

- `Job/Operation.priority`；
- 工序暂停、剩余加工时间和恢复；
- 机器紧急预约；
- 事件 diff；
- `sim_server` 插单 API 原型；
- 动态 Job 对 episode 终止条件的影响。

当前 `assign_env.py` 后续还增加了取货点、空载/载货运输和不可撤销已装载运输语义。

### 6.2 当前实验没有使用

当前 SkyCausal cohort 直接在宿主机创建 `GridFactoryEnv` 和 `Coordinator`，没有启动
`sim_server`。动态事件来自实验控制器，不经过：

```text
POST /sim/insert_jobs
→ SimulationManager
→ SSE 状态机
```

因此分支中的两个 P0 问题没有污染此前 cohort 结果，但也意味着此前实验不能作为
`0704insert` 在线 API 的验证证据。

### 6.3 与论文主链路的语义冲突

当前论文链路强调：

```text
已加工工序冻结
已装载运输不可撤销
提交前 freshness/rebase
PlanRevision 原子激活
```

`0704insert` 则允许 `priority >= 200` 的任务中断加工中的普通工序。这不是简单实现
差异，而是不同的制造干预权限。

论文中若采用抢占，必须把它建模为显式能力和有成本动作：

```text
preempt_current_operation = true/false
preemption_setup_cost
lost_work_or_resume_cost
maximum_preemption_count
eligible_machine/operation set
```

不能默认所有 solver 都拥有抢占权限。

## 7. 推荐整合方式

不建议修补 `HTTPJobSolver.replan()` 后继续维护第二套重排系统。建议将分支的“控制面”
与当前 SkyCausal 的“安全计划修订面”合并：

```text
POST /sim/insert_jobs
→ 校验并生成 InsertionEvent
→ 线程安全入队
→ 最新物理状态加入新 Job
→ build_residual_problem
→ OnlineFJSPMetaController
→ 多 solver probe / MCTS 分配
→ freshness/rebase
→ PlanRevisionActivator 原子激活
→ SSE 更新 queued/replanning/scheduled/...
```

组件处理建议：

| `0704insert` 组件 | 建议 |
|---|---|
| `/sim/insert_jobs` 输入校验 | 保留并统一 schema |
| 插单请求 ID、状态机、SSE 事件 | 保留 |
| `_pending_inserts` 队列 | 保留，删除重复初始化和旧方法调用 |
| `_build_replan_problem` | 替换为 `build_residual_problem` |
| `HTTPJobSolver.replan` | 删除，改走 Solver Catalog 和 `/solve` |
| 直接 append/清理运输队列 | 改由 `PlanRevisionActivator` 校验与回滚 |
| `priority >= 200` 抢占 | 变成显式 capability/action |
| PSO + nearest 硬限制 | 改为 capability-driven 准入 |
| 插单 metrics 和事件 | 保留并加入 cohort outcome |

## 8. 最小修复与验证顺序

如果目标是先恢复在线产品链路，建议严格按以下顺序：

1. 删除不存在的 `_drain_pending_inserts()` 调用和重复字段初始化；
2. 增加“主循环至少推进 1 步”的回归测试；
3. 冻结统一 `InsertJobsRequest` schema，并同步 API、文档和前端；
4. 将插单事件接入 `OnlineFJSPMetaController`，不新增私有 `/replan` 协议；
5. 使用 `PlanRevisionActivator` 完成原子激活和失败回滚；
6. 让 `priority/request_id/due/release` 贯穿 residual problem、solver artifact 和运输任务；
7. 明确抢占 capability 与成本；
8. 修复在线 Docker 构建、外部网络和不可变镜像；
9. 新增单容器、三容器和完整 episode 三层测试；
10. 最后再将插单状态作为论文在线动态事件 cohort。

## 9. 最终评价

`0704insert` 最有价值的部分不是 PSO 专用重排代码，而是它明确了：

```text
插单是一个有生命周期、有物理后果、有可观测状态的在线制造事件。
```

当前项目应吸收：

- 插单 API；
- 请求队列；
- 状态机；
- 优先级和可选抢占语义；
- SSE/JSONL 审计。

但重排、候选选择、新鲜度检查和计划提交必须统一到现有 SkyCausal
`ResidualFJSPProblem + PortfolioMetaAction + PlanRevisionActivator` 主链路，避免继续
维护两套不一致且都访问底层可变状态的在线调度实现。
