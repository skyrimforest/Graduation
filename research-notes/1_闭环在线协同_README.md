# 方向1 闭环在线协同 — 文献包

对应论文：`论文_1_闭环在线协同/article_closeloop_v1_cn.tex`
代码：`codebase/sky_research` 分支 `0901closeloop`（closeloop/orchestrator.py = 恢复编排器）

## 本地 PDF（papers/）

| 文件 | 引用 | 相关性 |
|------|------|--------|
| RHCR_Li_AAAI2021.pdf | li2021rhcr | 滚动时域碰撞解决（路由层闭环的对照范式） |
| MAPF_LNS2_Li_AAAI2022.pdf | li2022lns2 | 大邻域搜索修复（κ=局部修复的 MAPF 侧对应物） |
| RL-RH-PP_lifelong_2026.pdf | — | 学习引导优先级（方向3复用） |
| K-CBS（在方向2包） | — | 动力学约束（方向5/6复用） |

## 仅引用未下载（付费墙）

- Li et al. 2026 Sensors（在方向2包，MDPI 反爬）
- Lu et al. 2025 C&IE 动态 FJSP+AGV 故障（ScienceDirect 付费墙；arXiv ID 未知，勿猜）
- 数字孪生+MAPPO 动态 FJSP（Taylor & Francis 付费墙）
- 经典 rescheduling 综述（Ouelhadj & Petrovic 2008 等）

## 教训记录

下载论文必须逐个用 pypdf 验证标题——本包曾因猜测 arXiv ID 混入两篇完全不相关
的论文（已删除）。后续方向一律"搜索→官方链接→下载→验证"。
