# SYNC — 多机同步与服务器迁移指南

> 谁在什么时候读：换机器、换服务器、或不确定"我改的东西到底同步了没有"的时候。
> 服务器一次性重建看 `RESTORE.md`（一键 `bootstrap.sh`）；本文件讲**同步思路与日常纪律**。

## 一、同步架构：什么走 git，什么不走

**原则：git 只管"可再生的成果"（代码/论文/文献/文档），大体积原始产物走物理迁移。**

| 仓库（github.com/skyrimforest/） | 内容 | 关键分支 | 同步方式 |
|---|---|---|---|
| **Graduation**（本仓库） | 论文 tex/pdf、文献库、调研与管理文档、战役证据 jsonl、bootstrap 工具链 | main | **文档总闸门，所有非代码成果进这里** |
| SkyEngine-research | 科研实验代码（sky_research） | 0901icaps1（方向1战役）+ 0901llmdiag（方向7）+ 其余方向链 | 每次实验/修改即 commit+push |
| SkyEngine | 引擎主体 | trae/skycausal-research；0902dedupe（三层屏障修复）；0901softcommit | 改引擎才推 |
| SkyEngine-FJSP / SkyEngine-MAPF | 求解器/路由微服务 | trae/skycausal-evolution | 基本不动 |
| （worktree）SkyEngine-confirmation-v2-1 | SkyEngine@0902dedupe 的 worktree，实验用引擎 | — | 不单独同步，`git worktree add` 重建 |

**git 之外（clone 得不到，跨机用 rsync/U盘）：**

| 内容 | 大小 | 迁移命令示例 |
|---|---|---|
| `artifacts/`（旧实验原始产物） | 983MB | `rsync -avP artifacts/ server:/path/260601天工论文准备/artifacts/` |
| `codebase/sky_research/results/` | ~144MB | 同上（战役证据 jsonl 已收录本仓库 results/，一般无需迁移） |
| `SkyEngine/.env` 等密钥 | - | 永不入库；新机从 `.env.example` 复制后手填 |
| docker 镜像（fjsp/mapf 微服务） | - | 首选服务器上按 `SkyEngine/SETUP_GUIDE.md` 重建；应急可 `docker save \| ssh srv 'docker load'` |

## 二、日常同步纪律（两条铁律）

1. **代码**：改了 sky_research / SkyEngine → 在对应仓库 commit + push（沿用现行分支链惯例，一个实验一提交，pilot 原始数据随提交入库）。
2. **文档/文献/论文**：改了论文 tex、新增文献 PDF、写了调研笔记 → **同步拷贝进本仓库对应目录**（不是软链）→ commit + push Graduation。

本仓库目录 ↔ 工作区源头对照：

| 本仓库目录 | 工作区源头 |
|---|---|
| `paper-icaps2027/` | `论文_1_闭环在线协同/icaps/` |
| `paper_2..7_*/` | `论文_N_*` 下的 tex/pdf/bib |
| `papers/<方向>/` | 论文工作区文档（调研/构思 md） |
| `literature/<方向>/` | `research/N_*/papers/`（PDF + manifest） |
| `research-notes/` | `research/` 的笔记与历史结果 |
| `templates/` | 南大模板/毕业论文模板 |
| `results/` | 战役证据 jsonl（closeloop/results_icaps 等） |

**LLM API 密钥**：服务器上放 `.env` 或 shell export（`LLM_BASE_URL / LLM_API_KEY / LLM_MODEL`），永不入库。

## 三、换机器 / 新服务器

```bash
# 一次性（前置: git + ssh-key 加入 GitHub 账号）
bash bootstrap.sh ~/proj          # 重建全部文档+代码+worktree，详见 RESTORE.md
# 之后按 RESTORE.md「实验栈启动」拉 docker；论文编译 sh scripts/latex-build.sh <tex>
```

## 四、推完自检（30 秒）

```bash
git -C <sky_research> status -sb     # 应无 ahead/behind
git -C <本仓库> status -sb
git -C <SkyEngine> log --branches --not --remotes --oneline   # 应为空
```

## 变更记录

- 2026-09-04: 文献库 7_LLM诊断解释 扩至 32 篇 PDF（pypdf 标题验证）+ manifest + fetch 脚本；
  新增 `papers/7_LLM调度诊断/归因范式精读_20260904.md`；bootstrap.sh 增拉 0901llmdiag 分支。
