# 方向2 统一基准评测 — 文献包

对应论文：`论文_2_统一基准评测/article_bench_v1_cn.tex`（SkyBench-1 基准）
代码：`codebase/sky_research` 分支 `0901bench`

## 本地 PDF（papers/）

| 文件 | 引用 | 用途 |
|------|------|------|
| Li2026_JSP_MAPF_framework_Sensors.pdf | li2026framework | ❌下载失败(MDPI反爬,406B HTML占位)，最接近的对照工作；全文已通过网页版阅读 |
| LaCAM_AAAI2023.pdf | okumura2023lacam | MAPF 求解器基线 |
| LaCAMstar_IJCAI2023.pdf | okumura2023lacamstar | MAPF 求解器基线（arXiv版） |
| MAPF-GPT_AAAI2025.pdf | andreychuk2025mapfgpt | 学习式 MAPF 前沿 |
| MAPD_token_passing_AAMAS2017.pdf | ma2017mapd | 终身 MAPF/MAPD 奠基 |
| L2D_NeurIPS2020.pdf | zhang2020l2d | DRL-FJSP 奠基 |
| STT-CBS_2020.pdf | （方向6复用） | 随机行程时间鲁棒 MAPF |
| K-CBS_IJCAI2022.pdf | （方向5/6复用） | 动力学约束 MAPF |
| SILLM_lifelong_2024.pdf | （方向4复用） | 万级机器人终身 MAPF |
| HeurAgenix_2025.pdf | （方向7复用） | LLM 启发式生成 |
| CO-Bench_AAAI2026.pdf | （方向7复用） | LLM 组合优化基准 |

## 仅引用未下载（付费墙/反爬）

- Brandimarte (1993) mk 实例族, Annals of OR —— 实例数据在
  `codebase/SkyEngine-FJSP/data/fjsp-instances-main/brandimarte/`
- Dauzère-Pérès & Paulli (2024) EJOR FJSP 综述
- Xin et al. (2025) FITEE FJSP-PT 综述
- Smit et al. (2025) C&OR GNN-for-JSP 综述
- Fahmy et al. (2008) 有限缓冲死锁
- De Sousa et al. (2024) IEEE Access FJS-BTC
- JobShopLab (github.com/proto-lab-rojobshoplab)
