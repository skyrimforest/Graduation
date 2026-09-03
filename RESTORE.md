# RESTORE — 在新服务器上重建工作区

本仓库（Graduation）+ 4 个代码仓库即可完整重建全部文档与代码。
在一台装好 `git` 的机器上执行：

```bash
bash bootstrap.sh [目标根目录]     # 默认 ./flex_manufacture
```

## 仓库与分支布局

```
<ROOT>/flex_manufacture/
├── 260601天工论文准备/            ← 本仓库 (skyrimforest/Graduation, main)
│   ├── paper-icaps2027/           ICAPS 主论文 v1/v2 + 图表 + 讲稿
│   ├── paper_2..7_*               六个后续方向中文初稿
│   ├── papers/                    论文工作区: 1~7号方向 + 反事实模拟/LLMEnvolve/LLMSchedule/毕业论文_天工
│   ├── research-notes/            研究笔记: 历史结果54篇 + 方向README + 阶段设计/评审包
│   ├── literature/                文献库: common(通用49MB) + 各方向专题 PDF
│   ├── reports/                   汇报PPT + 调研报告 + 创新点构思 + PPT生成脚本
│   ├── templates/                 南大模板(NJUThesis) + 毕业论文模板
│   ├── results/                   战役证据 jsonl: E1-E8 + 消融 + pilot
│   ├── latex/ scripts/            论文编译工具链 (Dockerfile + latex-build.sh)
│   └── codebase/
│       ├── SkyEngine/             ← skyrimforest/SkyEngine, 分支 trae/skycausal-research (引擎主体)
│       │                            另含关键分支: 0902dedupe(三层屏障10个修复提交), 0901softcommit
│       ├── SkyEngine-confirmation-v2-1/   ← 0902dedupe 的 git worktree(可重建)
│       ├── SkyEngine-FJSP/        ← skyrimforest/SkyEngine-FJSP, 分支 trae/skycausal-evolution (FJSP求解器)
│       ├── SkyEngine-MAPF/        ← skyrimforest/SkyEngine-MAPF, 分支 trae/skycausal-evolution (MAPF路由器)
│       └── sky_research/          ← skyrimforest/SkyEngine-research, 分支 0901icaps1 (战役runner/分析/可视化)
```

## git 之外的内容（clone 不会得到）

| 内容 | 大小 | 说明 |
|---|---|---|
| `artifacts/` | 983MB | 实验运行原始产物（json/log/pkl/jsonl），仅在需重跑分析时物理迁移 |
| `sky_research/results/` | ~144MB | 全量运行日志与可视化；**证据 jsonl 已收录本仓库 `results/`** |
| `SkyEngine/.env` | - | 从 `.env.example` 复制后填写密钥，永不入库 |
| docker 镜像 / `dataset/` | - | 按 SkyEngine 内 SETUP_GUIDE.md 重新构建 |

## 论文编译

```bash
sh scripts/latex-build.sh <dir>/article_xxx.tex    # 或
docker compose -f compose.latex.yaml up            # 见 LATEX.md
```

## 实验栈启动（SkyEngine）

1. `cp SkyEngine/.env.example SkyEngine/.env` 并填写密钥
2. 按 `SkyEngine/SETUP_GUIDE.md` / `AGENT_GUIDE.md` 构建 docker 镜像并拉起
   FJSP / MAPF / sim 微服务
3. 修复开关（0902dedupe 分支）：`AGV_TRANSFER_DEDUPE` / `AGV_CELL_RESERVE` /
   `AGV_SAMECELL_SKIP` / `AGV_PARK_DISCIPLINE` / `AGV_ASSIGN_LOSS_GUARD`，
   全部置 0 可精确复现旧行为（消融基线）
4. 战役复跑：`sky_research/closeloop/run_full.py`（主战役）、`pilot_ab.py`（双臂）、
   `pilot_abl.py`（五臂消融）、`vis/make_frames.py`（帧生成）
