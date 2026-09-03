# SkyEngine `0704insert` 项目调研报告

## 1. 调研范围

| 项目 | 内容 |
|---|---|
| 仓库 | [skyrimforest/SkyEngine](https://github.com/skyrimforest/SkyEngine) |
| 目标分支 | [`0704insert`](https://github.com/skyrimforest/SkyEngine/tree/0704insert) |
| 固定快照 | [`527bc18032aa5e53e882e11daaad3181e81bdff6`](https://github.com/skyrimforest/SkyEngine/commit/527bc18032aa5e53e882e11daaad3181e81bdff6) |
| 快照时间 | 2026-07-18 |
| 调研时间 | 2026-08-11 |
| 调研方法 | GitHub 页面核对、完整分支源码阅读、提交历史分析、依赖检查、静态编译、定向测试与入口烟测 |

本报告只分析上述 SkyEngine 仓库，不引用、不比较其他本地项目的代码、架构或实验结论。

## 2. 结论摘要

SkyEngine（README 中称“天工”）是一个面向柔性制造的联合仿真与调度研究原型。它把以下三个决策问题放进同一离散时间环境：

1. **FJSP 作业调度**：为每道工序选择机器并生成搬运请求。
2. **AGV 任务分配**：将待搬运工序分配给空闲 AGV。
3. **MAPF 路径规划**：为多个 AGV 逐步生成网格移动动作。

项目真正的核心不是 README 所描述的完整企业平台，而是 Python 实现的制造仿真执行内核 `GridFactoryEnv`、三类可替换求解组件、FastAPI 在线控制服务以及一组实验和训练脚本。FJSP、MAPF 的高级算法通常作为外部 Docker 镜像通过 HTTP 接入，仓库本身不包含这些算法服务的完整实现。

`0704insert` 分支的突出增量是运行时异常、加工时间波动、动态插单、特急单抢占、SSE 事件流和在线仿真管理。局部功能已有测试支撑，但当前分支存在阻断级集成回归，不能视为开箱即用版本：

- `/sim/play` 启动后会因调用不存在的 `_drain_pending_inserts()` 立即失败。
- 默认 `run.py` 依赖仓库中不存在的 `dataset/fjsp/` 目录。
- 在线依赖文件声明了 FastAPI，但锁文件未包含 FastAPI。
- 训练模块缺少已引用的模型源码，并且未声明 PyTorch 依赖。

综合判断：**适合作为联合制造仿真和算法接入的研究代码基础，不适合直接按 README 作为可交付平台部署。**

## 3. 仓库概况

固定快照共 1,137 个受 Git 管理的文件，其中：

- `dataset/`：892 个文件，包含 FJSP、JSSP、MAPF 和 Pogema benchmark 数据或第三方代码。
- `sky_executor/`：95 个文件，核心仿真执行代码。
- `experiment/`：91 个文件，实验、蒸馏、MoE、GRPO/PPO 等探索代码。
- `test/`：19 个文件，近期主要覆盖异常、插单、生命周期、指标与系统烟测。
- `trainer/`：10 个文件，强化学习训练器入口。

GitHub 显示的 C++ 占比主要来自随数据集引入的 MAPF benchmark，不代表核心引擎使用 C++。核心实现基本为 Python。

该分支相对 `main` 为 **69 个提交领先、1 个提交落后**。最近一轮功能开发集中在 2026 年 7 月，主要包括：

- 在线仿真重置隔离；
- 手动和随机异常注入；
- 加工时间随机采样；
- SSE 历史事件回放；
- 批量插单；
- PSO 重规划；
- 优先级 200 的特急工序抢占。

## 4. 总体架构

```text
外部调用方
   |
   +-- 实验模式: run.py + 环境变量
   |
   +-- 在线模式: sim_server.py + HTTP/SSE
                       |
                       v
                  Coordinator
          +------------+-------------+
          |            |             |
          v            v             v
      JobSolver     Assigner     RouteSolver
      FJSP计划      AGV分配       MAPF动作
          |            |             |
          +------------+-------------+
                       |
                       v
                GridFactoryEnv
                       |
          +------------+-------------+
          |            |             |
       Job/Machine   AGV Task      Pogema Grid
       加工状态      搬运状态       多智能体移动
          |            |             |
          +------------+-------------+
                       |
          +------------+-------------+
          |                          |
   ExceptionInjector             MetricsHub
   故障/障碍/恢复                指标/奖励/热力图
```

### 4.1 控制层

项目提供两个主要入口：

- [`run.py`](https://github.com/skyrimforest/SkyEngine/blob/527bc18032aa5e53e882e11daaad3181e81bdff6/run.py)：环境变量驱动的单 episode 实验脚本，执行完退出。
- [`sim_server.py`](https://github.com/skyrimforest/SkyEngine/blob/527bc18032aa5e53e882e11daaad3181e81bdff6/sim_server.py)：FastAPI 长驻服务，提供创建、播放、暂停、重置、停止、异常注入、插单和 SSE 推流。

两者并未共享统一的配置解析层：

- `run.py` 读取 `DATA_DIR/fjsp/*.json` 和 `DATA_DIR/mapf/*.yaml`。
- `sim_server.py` 直接接收前端式 JSON，解析 `topology`、`agvs`、`jobs`、`exception_config` 和 `processing_time_config`。

这导致实验模式和在线模式的输入契约、默认值及可运行性并不完全一致。

### 4.2 协调层

[`Coordinator`](https://github.com/skyrimforest/SkyEngine/blob/527bc18032aa5e53e882e11daaad3181e81bdff6/sky_executor/grid_factory/factory/Component/Coordinator/coordinator.py#L24-L98) 每个时间步依次调用：

1. `JobSolver.plan(job_observation)`：生成机器决策和 `transfer_requests`。
2. `Assigner.plan(task_observation)`：将可搬运任务分配给 AGV。
3. `RouteSolver.plan(agent_observation)`：为 AGV 生成下一步动作。

最终动作被统一打包为：

```python
{
    "job_actions": job_decision,
    "assign_actions": assign_decision,
    "agent_actions": route_decision,
}
```

三类组件均使用注册表和工厂创建，扩展新算法的接口比较直接。

### 4.3 执行层

[`GridFactoryEnv`](https://github.com/skyrimforest/SkyEngine/blob/527bc18032aa5e53e882e11daaad3181e81bdff6/sky_executor/grid_factory/factory/grid_factory_env.py#L32-L217) 是 PettingZoo `ParallelEnv`，底层包装 Pogema 的 lifelong MAPF 环境。

单步执行顺序为：

1. `job_step`：接收求解器产生的搬运请求。
2. `task_step`：检查工序前置约束、推进机器加工、分配或交付 AGV 任务。
3. `Pogema.step`：执行 AGV 网格移动。
4. `MetricsHub.on_step_end`：统一计算指标和奖励。

环境对外提供三组观测：

- `job_observation`：Job 和 Machine；
- `task_observation`：Machine、待分配搬运、AGV、异常 epoch 等；
- `agent_observation`：Pogema 路径规划观测。

核心状态实际由 [`PogemaLifeLongWithAssign`](https://github.com/skyrimforest/SkyEngine/blob/527bc18032aa5e53e882e11daaad3181e81bdff6/sky_executor/grid_factory/factory/assign_env.py) 维护，包括机器队列、工序状态、搬运缓冲池、AGV 当前任务、异常状态和统计量。

## 5. 核心领域模型

主要数据结构位于 [`structure.py`](https://github.com/skyrimforest/SkyEngine/blob/527bc18032aa5e53e882e11daaad3181e81bdff6/sky_executor/grid_factory/factory/Utils/structure.py)：

| 模型 | 关键职责 |
|---|---|
| `Operation` | 候选机器、标称/实际加工时间、优先级、交期、加工状态、抢占和时间戳 |
| `Job` | 顺序工序集合、释放时间、交期、优先级、插单请求 ID、完成时间 |
| `Machine` | 当前工序、输入队列、暂停工序、特急预留、故障状态和加工历史 |
| `RoutingTask` | 工序搬运任务、起终点、候选机器、优先级和运输时间戳 |
| `AGV` | 位置、当前任务、完成任务、故障状态和移动统计 |

工序生命周期主要为：

```text
PENDING -> 运输 -> 机器输入队列 -> PROCESSING -> FINISHED
                              |
                              +-> SUSPENDED -> PROCESSING
                                  （仅特急抢占场景）
```

工序顺序约束由执行环境在搬运前检查：`op_id == 0` 可直接搬运，后续工序必须等待前一道工序 `FINISHED`。

## 6. 可替换算法组件

在固定快照中，注册表实际可发现的组件如下。

### 6.1 JobSolver

| 名称 | 实现方式 | 特点 |
|---|---|---|
| `greedy` | 本地 Python | 首次调用生成固定离线计划，之后按时间释放搬运；不适合运行中新增 Job |
| `http` | 外部 HTTP 服务 | 每步向 `/plan` 发送 Job/Machine 全量状态；PSO 插单时额外调用 `/replan` |

README 和 Compose 注释中出现的 `best`、`drl` 等名称不是本仓库 JobSolver 注册表中的本地实现，而是外部镜像或历史配置概念。

### 6.2 RouteSolver

| 名称 | 实现方式 | 特点 |
|---|---|---|
| `astar` | 本地 Python | 每个 AGV 基于局部观测独立 A*；默认还带 0.2 随机动作率 |
| `http` | 外部 HTTP 服务 | 将 Pogema 观测递归转为 JSON，调用外部 `/plan` |

本地 A* 不是严格的联合 MAPF 最优求解器。它把其他 AGV 当作动态障碍，适合基线和仿真推进，不保证消除所有多智能体冲突。

### 6.3 Assigner

当前注册了 12 种任务分配器：

```text
adaptive_coupling, coupling_hungarian, fifo, greedy,
hungarian, least_congestion, load_balance, nearest,
nn, random, sjt, urgency
```

`nearest`、`greedy` 等可以仅依赖 NumPy 运行；匈牙利匹配在 SciPy 不可用时回退到贪心。`nn` 在实例化时需要 PyTorch 和缺失的 `Utils/model` 源码，因此当前快照不可用。

## 7. `0704insert` 分支的关键能力

### 7.1 运行时插单

在线服务提供 `POST /sim/insert_jobs`。请求主要形态为：

```json
{
  "machines": 3,
  "jobs": [
    [
      [
        {"machine": 0, "processing": 5},
        {"machine": 1, "processing": 7}
      ],
      [
        {"machine": 2, "processing": 4}
      ]
    ]
  ],
  "extensions": {
    "job_metadata": [
      {
        "name": "urgent-order",
        "priority": 200,
        "due_in_steps": 40
      }
    ]
  }
}
```

实现特点：

- 单次接受 1 至 20 个 Job，每个 Job 最多 20 道工序。
- 支持逐 Job 校验和部分接受。
- 服务端分配连续 `job_id` 和 `request_id`。
- 当前只允许 `PSO + nearest` 组合。
- 插单请求进入线程安全队列，在仿真线程内调用 FJSP 服务 `/replan`。
- 已经开始加工、已进入机器队列、已运输的工序被冻结；其余待执行工序参与重规划。
- 插单阶段会跟踪 `queued -> replanning -> scheduled -> transporting -> processing -> completed`。

相关实现见 [`sim_server.py:624-900`](https://github.com/skyrimforest/SkyEngine/blob/527bc18032aa5e53e882e11daaad3181e81bdff6/sim_server.py#L624-L900)。

### 7.2 特急单抢占

优先级达到 200 的工序可在目标机器上抢占普通工序：

- 普通工序保存剩余加工时间并进入 `suspended_ops`；
- 机器为正在运输的特急工序设置 `urgent_reservations`；
- 特急工序优先从机器输入队列取出；
- 被暂停工序恢复时沿用剩余时间，不重新采样加工时长。

该行为有 4 个定向测试覆盖，见 [`test_urgent_preemption.py`](https://github.com/skyrimforest/SkyEngine/blob/527bc18032aa5e53e882e11daaad3181e81bdff6/test/env_test/test_urgent_preemption.py)。

### 7.3 运行时异常

[`ExceptionInjector`](https://github.com/skyrimforest/SkyEngine/blob/527bc18032aa5e53e882e11daaad3181e81bdff6/sky_executor/grid_factory/factory/Events/exception_injector.py) 支持：

- 机器故障与自动修复；
- AGV 故障与自动恢复；
- 临时障碍及到期移除；
- 固定时间表、概率触发、预设场景和 JSONL replay；
- 手动注入与手动清除；
- 通过 epoch 和事件记录让求解器观察状态变化；
- 临时障碍可检查地图连通性，避免切断可行区域。

### 7.4 加工时间不确定性

[`ProcessingTimeSampler`](https://github.com/skyrimforest/SkyEngine/blob/527bc18032aa5e53e882e11daaad3181e81bdff6/sky_executor/grid_factory/factory/Utils/processing_time.py) 在工序开始加工时采样实际时长，同时保留标称时长供调度使用。

支持 fixed、uniform、discrete uniform、normal、triangular 及其乘数形式，并可按全局、机器或工序覆盖。

### 7.5 指标和奖励

`MetricsHub` 每步聚合三类指标：

- FJSP：机器利用率、非加工时间、负载方差、机器前排队时间；
- MAPF：交换冲突、带任务停滞、AGV 利用率、行驶和等待时间、轨迹热力图；
- 耦合：实际运输相对 BFS 最短路的延迟、机器等待来料比例、完工率和 makespan。

默认奖励将停滞、交换冲突、机器利用率作为稠密项，将 makespan、运输延迟和来料等待作为 episode 终局项。

## 8. 在线 API

| 方法 | 路径 | 用途 |
|---|---|---|
| `POST` | `/sim/create` | 根据 JSON 配置创建环境和 Coordinator |
| `POST` | `/sim/play` | 启动或恢复仿真 |
| `POST` | `/sim/pause` | 暂停仿真 |
| `POST` | `/sim/reset` | 重置 episode |
| `POST` | `/sim/stop` | 停止仿真 |
| `POST` | `/sim/exception/inject` | 注入机器、AGV 或障碍异常 |
| `POST` | `/sim/exception/clear` | 清除异常 |
| `POST` | `/sim/insert_jobs` | 批量插单 |
| `GET` | `/sim/state` | 查询运行状态及插单支持情况 |
| `GET` | `/health` | 健康检查 |
| `GET` | `/stream/state` | SSE 状态帧 |
| `GET` | `/stream/metrics` | SSE 指标流 |
| `GET` | `/stream/events` | SSE 业务事件流 |

每个 SSE 订阅者使用独立有界队列，晚连接者会收到最新状态或历史事件。Episode 事件以 JSONL 写入 `SKY_LOG_DIR/<run_id>/events.jsonl`，结束时补充 `summary.json`。

接口没有认证、授权、限流或租户隔离设计，应只部署在受信网络内。

## 9. 部署方式与外部依赖

### 9.1 实验模式

[`docker-compose.yaml`](https://github.com/skyrimforest/SkyEngine/blob/527bc18032aa5e53e882e11daaad3181e81bdff6/docker-compose.yaml) 编排：

- `engine`：运行 `run.py`；
- `fjsp`：外部 FJSP 算法镜像；
- `mapf`：外部 MAPF 算法镜像。

Engine 通过 Docker 内网调用 `fjsp:8002` 和 `mapf:8001`。默认配置声明 GPU reservation，并引用 `skyengine-fjsp-pso:latest`、`skyengine-mapf-gpt:latest` 等本仓库无法构建的镜像。

### 9.2 在线模式

[`docker-compose-online.yaml`](https://github.com/skyrimforest/SkyEngine/blob/527bc18032aa5e53e882e11daaad3181e81bdff6/docker-compose-online.yaml) 使用 `sim_server.py`，对外暴露 8080，并要求预先存在外部网络：

```bash
docker network create skyengine-net
```

在线模式同样依赖外部 FJSP/MAPF 镜像。插单还要求 FJSP PSO 镜像实现 `/replan` 契约，仅有 `/plan` 的普通镜像不能完成插单。

### 9.3 Python 依赖

基础环境要求 Python 3.11，主要依赖 Pogema、PettingZoo、Gymnasium、OR-Tools、NumPy、Matplotlib、Requests 和 Uvicorn。

依赖管理当前分裂为：

- `pyproject.toml`：基础环境，不含 FastAPI、PyTorch、SciPy 和 pytest；
- `pyproject-online.toml`：额外声明 FastAPI；
- `uv.lock`：按基础 `pyproject.toml` 生成，未锁定 FastAPI；
- `requirements.txt`：空文件。

因此基础引擎依赖可安装，但在线服务、训练和测试需要额外修复或补充依赖。

## 10. 实际验证结果

所有验证均基于固定提交 `527bc180`。

| 验证项 | 结果 | 说明 |
|---|---|---|
| GitHub 分支和提交核对 | 通过 | 分支存在，HEAD 为 `527bc180` |
| `python -m compileall` | 通过 | Python 文件无语法错误 |
| 三类工厂注册表导入 | 通过 | 发现 2 个 JobSolver、2 个 RouteSolver、12 个 Assigner |
| Docker Compose 配置解析 | 通过 | 两个 Compose 文件均能通过 `docker compose config` |
| 异常、加工时间、插单、抢占定向测试 | 通过 | 27 个测试全部通过 |
| 全量 pytest 收集 | 失败 | 5 个测试模块因缺少 `dataset/fjsp/` 在收集期报错 |
| 默认 `uv run python run.py` | 失败 | `FileNotFoundError: dataset/fjsp` |
| 在线主循环烟测 | 失败 | `_drain_pending_inserts` 方法不存在 |
| 在线锁文件检查 | 失败 | `pyproject-online.toml` 与 `uv.lock` 不一致 |
| 基础环境导入 FastAPI | 失败 | `ModuleNotFoundError: fastapi` |
| 导入 `trainer` | 失败 | 首先缺少 `torch`，同时模型源码目录不存在 |

## 11. 主要问题与风险

### 11.1 P0：在线主循环不可运行

[`sim_server.py:1257`](https://github.com/skyrimforest/SkyEngine/blob/527bc18032aa5e53e882e11daaad3181e81bdff6/sim_server.py#L1253-L1265) 调用：

```python
self._drain_pending_inserts()
```

但当前类中只有 `_drain_insert_queue()`，没有 `_drain_pending_inserts()`。实测调用 `play()` 后线程立即抛出 `AttributeError`，状态变为 `error`。

这是两版插单实现合并后遗留的旧调用。近期插单单测直接测试队列和重规划方法，没有覆盖真实 `_run_loop`，因此未发现该回归。

### 11.2 P0：默认实验数据路径无效

`run.py` 固定读取 `DATA_DIR/fjsp`，Compose 默认挂载仓库 `./dataset`，但固定快照只有 `dataset/fjsp-instances`，没有 `dataset/fjsp`，也没有默认的 `J10P5M6.json` 或 `J20P10M10.json`。

结果是 README 所暗示的默认运行方式和 Compose 默认参数均不能直接启动。

### 11.3 P0：在线镜像依赖未锁定

`online.dockerfile` 将 `pyproject-online.toml` 复制为 `pyproject.toml`，随后用基础版 `uv.lock` 执行 `uv sync --frozen`。实际检查显示锁文件需要更新，而且冻结环境中无法导入 FastAPI。

容器启动命令再次使用非 frozen 的 `uv run`，可能在运行期联网补装依赖，但这破坏了镜像可复现性和离线启动能力。

### 11.4 P1：训练链路不完整

`trainer/` 实现了 REINFORCE、PPO、GRPO、DQN 和蒸馏器，但：

- `pyproject.toml` 没有声明 PyTorch；
- `trainer/__init__.py` 引用的 `sky_executor/.../Utils/model/*.py` 不存在；
- `experiment/train_grpo.py` 引用的 `learned_assigner` 路径不存在；
- `packet_examples` 引用的 `sky_executor.packet_factory` 不存在。

这些目录更接近尚未清理的研发快照，而非可复现训练发行物。

### 11.5 P1：测试不能作为集成质量门禁

仓库没有 GitHub Actions 或其他 CI 配置。部分所谓 test 文件在模块导入时直接创建环境或执行实验，导致 pytest 收集依赖外部数据和运行状态。

当前测试能够证明近期局部模块行为，但不能证明：

- 在线 HTTP 主流程可用；
- Docker 三服务组合可用；
- 插单从 API 到 episode 完成全链路可用；
- 默认数据和默认配置可复现。

### 11.6 P1：项目边界和文档不清晰

- README 主要是产品愿景，没有安装、输入格式、API、依赖和已知限制。
- `version_history.MD` 仍称当前分支为 `feature0522`，已过时。
- `explore/` 中部分文档描述的是方案或历史版本，不能代表最终代码。
- 同时存在 `assign_env.py` 和较旧的 `grid_factory.py`，两者都定义同名环境类，容易误读。
- 根目录遗留 4 个以提交短哈希命名的空文件。
- 仓库根目录没有 `.dockerignore`。

### 11.7 P1：许可证不明确

仓库根目录没有 LICENSE。数据子目录各自带有许可证，但不能据此推断 SkyEngine 自有源代码的授权方式。对外使用、二次分发或商用前必须由作者明确许可。

## 12. 工程成熟度判断

| 维度 | 判断 |
|---|---|
| 问题建模 | 较完整，覆盖 Job、Operation、Machine、AGV、搬运和网格移动 |
| 模块化 | 较好，三类算法均有工厂和统一接口 |
| 动态场景 | 较丰富，支持故障、临时障碍、时间波动和插单 |
| 可观测性 | 较好，具备指标、热力图、SSE 和 JSONL 事件 |
| 单元测试 | 局部功能有覆盖，近期特性质量尚可 |
| 集成测试 | 不足，入口级回归未被发现 |
| 可复现性 | 较差，默认数据、外部镜像和锁文件不闭合 |
| 训练能力 | 代码量较多，但当前快照不可直接运行 |
| 文档 | 产品描述多，工程使用文档不足 |
| 生产可用性 | 低，缺少认证、CI、许可证和稳定发布流程 |

## 13. 建议修复顺序

1. **恢复在线主循环**：删除旧 `_drain_pending_inserts()` 调用或统一成唯一插单队列入口，并增加 `create -> play -> 至少推进一帧` 的回归测试。
2. **统一数据契约**：确定 `dataset/fjsp` 与 `dataset/fjsp-instances` 的唯一目录规范，提交最小可运行样例。
3. **统一依赖和锁文件**：将基础、在线、训练、测试拆成明确 dependency groups，重新生成锁文件。
4. **建立最小 CI**：至少执行 compileall、27 个局部测试、默认单机 episode 和在线 API 一帧烟测。
5. **明确外部求解器协议**：版本化 `/health`、`/plan`、`/replan` 的请求响应 schema，并说明镜像获取方式。
6. **清理失效模块**：修复或移除缺失的模型、PacketFactory、旧环境副本和不可运行示例。
7. **补齐工程文档和许可证**：把 README 改为可验证的安装、运行、API、数据与限制说明。

## 14. 最终评价

SkyEngine 的技术价值主要在于：它已经形成了一个可扩展的 FJSP、AGV 分配和 MAPF 联合执行模型，并进一步加入了动态异常、加工时间不确定性和特急插单。这些能力比单纯的静态调度 benchmark 更接近真实制造仿真研究。

但固定快照同时呈现出典型的研发分支状态：局部功能推进快，跨入口契约和可复现工程没有同步收口。当前最合理的使用方式是把它视为**研究原型和执行内核源码**，先修复 P0 问题并建立最小集成测试，再考虑算法评估、平台接入或对外部署。

