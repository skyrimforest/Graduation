# 动态 FJSP-AGV 四事件 MARL 论文元数据

## 书目信息

- 题名：Real-Time Scheduling for Flexible Job Shop With AGVs Using
  Multiagent Reinforcement Learning and Efficient Action Decoding
- 作者：Yuxin Li, Qingzheng Wang, Xinyu Li, Liang Gao, Ling Fu, Yanbin Yu,
  Wei Zhou
- 期刊：IEEE Transactions on Systems, Man, and Cybernetics: Systems
- 年份：2025
- 卷期页码：55(3), 2120-2132
- DOI：<https://doi.org/10.1109/TSMC.2024.3520381>
- IEEE 文档号：10829984
- 出版日期：2025-01-07

## 与本项目的关系

该文把动态 FJSP-AGV 建模为多智能体实时调度，联合处理：

1. task selection；
2. machine allocation；
3. AGV allocation；
4. 四类 disturbance events 下的恢复策略。

它是 SkyCausal 四事件建模、动作解码和 MARL baseline 的核心出发点。SkyCausal
需要在其基础上额外验证显式无碰撞 MAPF、真实空载/载货运输、统一事件动作契约、
solver portfolio 和严格 wall-clock budget。

## 获取状态

截至 2026-08-06：

- DOI、作者、卷期页码和摘要已通过 IEEE、OpenAlex 与 Semantic Scholar 交叉核验；
- OpenAlex 标记该论文为 closed access，未发现作者公开 manuscript；
- 已通过 Nanjing University 机构授权取得完整 13 页 PDF；
- 本地文件：`research/papers/2025_Li_DFJSP_AGV_MARL.pdf`；
- SHA256：
  `b9004ce988f9c655dcfac08db8a5401737660fdf64cfa4e07707b296f3574d71`；
- PDF footer 记录机构授权，因此该文件仅用于本地研究，不作为公开分发版本。

复验命令：

```bash
pdfinfo 2025_Li_DFJSP_AGV_MARL.pdf
pdftotext 2025_Li_DFJSP_AGV_MARL.pdf -
shasum -a 256 2025_Li_DFJSP_AGV_MARL.pdf
```
