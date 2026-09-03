# 相关论文原文

首次整理日期：2026-07-12；核心文献复核日期：2026-08-04。

## 核心出发点

1. `2025_DyRo-MCTS_Dynamic_Job_Shop_Scheduling.pdf`
   - [arXiv:2509.21902](https://arxiv.org/abs/2509.21902)
   - [OpenReview 评审记录](https://openreview.net/forum?id=wr3J8niaos)
   - 状态：已下载并通过 `pdfinfo`、`pdftotext` 校验，共 16 页；
   - SHA256：
     `306e8578c0d544f83f0cb0a90ba89ca7262882690d4d75dd897bfff8168e09c8`；
   - 作用：动态到达下的鲁棒在线 MCTS、offline policy prior 和决策预算基线。
2. *Real-Time Scheduling for Flexible Job Shop With AGVs Using Multiagent
   Reinforcement Learning and Efficient Action Decoding*
   - [DOI](https://doi.org/10.1109/TSMC.2024.3520381)
   - 本地元数据：
     [`metadata/2025_Li_DFJSP_AGV_MARL.md`](metadata/2025_Li_DFJSP_AGV_MARL.md)
   - 本地文件：`2025_Li_DFJSP_AGV_MARL.pdf`；
   - 状态：已通过机构授权下载，并通过 `pdfinfo`、`pdftotext` 校验，共 13 页；
   - SHA256：
     `b9004ce988f9c655dcfac08db8a5401737660fdf64cfa4e07707b296f3574d71`；
   - 访问边界：PDF footer 记录 Nanjing University 授权，不得作为公开分发版本；
   - 作用：动态 FJSP-AGV 的 task/machine/AGV 多智能体调度和四事件实验基线。

两篇文献的 BibTeX 见
[`core_literature.bib`](core_literature.bib)。不得把出版商错误页、摘要页或不完整
PDF 当作论文原文提交。

## 已下载

1. `2024_HGS_Learning-enabled_FJSP_Scalable_Smart_Manufacturing.pdf`  
   [arXiv 页面](https://arxiv.org/abs/2402.08979)；用于异构图状态表示、FJSPT 和规模泛化对比。
2. `2024_Offline_RL_for_Job-Shop_Scheduling.pdf`  
   [arXiv 页面](https://arxiv.org/abs/2410.15714)；用于行为克隆、离线强化学习和专家数据设计对比。
3. `2024_CP_Deep_Learning_Dynamic_FJSP.pdf`  
   [arXiv 页面](https://arxiv.org/abs/2403.09249)；用于学习模型与 CP/可行性修复结合的对比。
4. `2025_MARL_Flexible_Shop_Scheduling_Survey.pdf`  
   [Frontiers 页面](https://doi.org/10.3389/fieng.2025.1611512)；用于 MARL 调度研究综述和实验规范参考。

## 因果分析文献（2026-08-26 新增）

对应论文因果章三层识别设计（`../20260826_切换因果分析_方法调研与三层设计.md`），
BibTeX 见 [`causal_literature.bib`](causal_literature.bib)，均已通过
`pdftotext` 首页核验标题与作者：

1. `2604.01325v1.pdf`（Laudy 2026，DTCF）：数字孪生反事实形式化——L2
   配对克隆层的理论依据；
2. `2212.06355.pdf`（Uehara et al. 2022）：OPE 综述——L4 离策略评估与
   propensity 记录设计的依据；
3. `1503.02834.pdf`（Dudík et al. 2014，Statistical Science）：doubly
   robust 策略评估与学习；
4. `1911.06854.pdf`（Voloshin et al. 2021）：OPE 估计量实证比较；
5. `2009.00148.pdf`（Bojinov, Simchi-Levi & Zhao 2023，Management
   Science）：switchback 实验设计——干扰下的实验设计参考（在线部署阶段）；
6. `1706.03461.pdf`（Künzel et al. 2019，PNAS）：CATE 元学习器
   （T/S/X-learner）；
7. `1510.04342.pdf`（Wager & Athey 2018，JASA）：因果森林；
8. `2021_Bellot_Synthetic_Controls_Continuous_Time.pdf`（Bellot & van
   der Schaar 2021，ICML）：连续时间合成控制——相关工作定位引用。

未能下载（如实登记，不伪造文件）：

- [CausalML 教材（Chernozhukov et al.）](https://causalmlbook.org)：
  站点 TLS 握手拒绝（服务端问题），按在线版引用；
- [CRN 方差缩减经典（Management Science）](https://dl.acm.org/doi/abs/10.1287/mnsc.45.11.1570)：
  付费墙，标题待核实后再补 BibTeX。

## 相关页面但暂未下载

以下论文页面可以访问，但其 PDF 下载接口返回 403，因此暂不生成伪造的本地文件：

- [Learning-guided Rolling Horizon Optimization for Long-Horizon FJSP](https://openreview.net/forum?id=Aly68Y5Es0)
- [RESCHED: Rethinking FJSP from a Transformer-Based Architecture](https://openreview.net/forum?id=s5pWbwf2tk)
- [Towards Generalizable Multi-Policy Optimization with Self-Evolution for Job Scheduling](https://openreview.net/forum?id=VPm6afl0Sc)
- [FJSP-AGV cooperative agent DRL](https://doi.org/10.1016/j.eswa.2025.128142)（出版商页面/可能需要机构权限）

## 使用建议

复现时先阅读 HGS 和 Offline RL 两篇，分别对应 SkyEngine 的图状态表示和专家轨迹/蒸馏训练；再阅读 CP-DL 论文，确定 Assigner 输出后如何通过规则或约束求解器做可行性校验。
