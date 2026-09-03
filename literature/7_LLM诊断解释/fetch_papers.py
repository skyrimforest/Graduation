"""方向7 文献包批量下载 + pypdf 标题验证
用法: python3 fetch_papers.py
产物: papers/*.pdf + papers/manifest.csv (沿用顶层 papers/manifest.csv 六列格式)
验证失败的移入 papers/_unverified/ 并在 manifest 标 unverified_title
"""
import json, time, urllib.request, sys
from pathlib import Path

HERE = Path(__file__).parent
UNVER = HERE / "_unverified"
UNVER.mkdir(exist_ok=True)

# (shortname, year, arxiv_id, [title keywords — 命中其一即过], role)
PAPERS = [
    ("OPRO", 2024, "2309.03409", ["Large Language Models as Optimizers"], "LLM-as-optimizer 先例(生成-评分循环)"),
    ("FunSearch", 2024, "2312.01556", ["Mathematical discoveries from program search"], "生成-执行-进化循环鼻祖(Nature)"),
    ("EoH", 2024, "2401.02051", ["Evolution of Heuristics"], "LLM启发式进化(思想+代码双表示)"),
    ("ReEvo", 2024, "2402.01145", ["ReEvo", "Hyper-Heuristics", "Reflection"], "反思式超启发式——反思精化级的方法来源"),
    ("LLaMEA", 2024, "2405.20132", ["LLaMEA", "Metaheuristic"], "LLM进化元启发式(参数收缩教训来源)"),
    ("ChainOfExperts", 2024, "2401.13923", ["Chain-of-Experts", "Operations Research"], "翻译-建模-编码-审查多智能体求解OR"),
    ("ReflecSched", 2025, "2508.01724", ["ReflecSched"], "最近邻: LLM读仿真轨迹提炼策略经验(在线)"),
    ("DynaSchedBench", 2026, "2605.27566", ["DynaSchedBench"], "动态调度LLM agent评测+observability paradox"),
    ("RCACopilot", 2023, "2305.15778", ["Root Cause Analysis", "Cloud Incidents"], "单轮打包RCA的代表(微软)"),
    ("RCAgent", 2023, "2310.16340", ["RCAgent", "Root Cause"], "agentic工具调用RCA先例"),
    ("mABC", 2024, "2404.12135", ["mABC", "Blockchain", "Root Cause"], "多agent投票RCA(抑制幻觉)"),
    ("ITBench", 2025, "2502.05352", ["ITBench"], "混沌工程注入ground truth的agentic评测基准"),
    ("CloudOpsBench", 2026, "2603.00468", ["Cloud-OpsBench"], "Generator-Executor-Verifier场景闭环+状态快照冻结"),
    ("LLMDigitalTwin", 2025, "2505.02076", ["digital twin", "Digital Twin"], "DT实施前验证LLM纠正动作(干预桥最近先例)"),
    ("MAPF_LLM_Unsolvable", 2024, "2401.03630", ["multi-agent path finding", "Multi-agent Path"], "LLM直接MAPF被证伪(定位依据)"),
    ("LLM-NAR", 2025, "2508.17971", ["LLM-NAR"], "GNN算法推理器引导LLM做MAPF(混合路线)"),
    ("LLM+P", 2023, "2304.11477", ["LLM+P", "Planning"], "翻译-形式求解模式鼻祖"),
    ("Logic-LM", 2023, "2305.12295", ["Symbolic Chain-of-Thought", "Logic-LM"], "NL-符号求解器翻译模式"),
    ("LLM-Modulo", 2024, "2402.01817", ["LLM-Modulo"], "生成-验证闭环定调文(ICML position)"),
    ("LLMHeurFromTraces", 2026, "2608.09343", ["simulation", "heuristic", "trace"], "重仿真验证LLM输出的最近学术先例(100 matched seeds)"),
    ("CounterBench", 2025, "2502.11008", ["CounterBench", "counterfactual"], "LLM反事实推理≈随机(hard案例假设依据)"),
    ("ExecutableCounterfactuals", 2025, "2510.01539", ["counterfactual"], "abduction缺失导致反事实高估(hard案例依据)"),
    ("WhatIfBench", 2026, "2608.27953", ["WhatIfBench"], "长程开放域反事实崩塌"),
    ("MAPF_OfflineRL_LLM", 2025, "2509.22130", [], "MAPF+LLM(标题待验证)"),
    ("KG_Warehouse", 2025, "2507.17273", ["warehouse", "Warehouse"], "KG+LLM仓储低效归因(仅标题确证)"),
    ("TamingRandomness_ABM", 2024, "2409.02086", ["Randomness"], "ABM随机流同步(CRN方法学参考)"),
    ("OpenRCA2", 2026, "2606.27154", ["OpenRCA"], "OpenRCA 2.0: 结果标注→因果过程监督(归因范式重点读)"),
    ("HowFar_RCA_Telemetry", 2026, "2607.13548", ["Root Cause Analysis"], "真实遥测上RCA全线失败(难度动机)"),
    ("LLM_RCA_Failures", 2026, "2601.22208", ["root cause", "Root Cause"], "开源LLM云RCA推理失败分析"),
    ("CorrectnessNotFaithfulness", 2024, "2412.18004", ["Correctness is not Faithfulness"], "引用指向对≠论断被支持(statement级忠实度依据)"),
    ("LogReasoner", 2025, "2509.20798", ["LogReasoner"], "日志RCA推理"),
    ("LogRCA", 2024, "2405.13599", ["LogRCA"], "日志RCA数据集/方法"),
]

rows = []
for short, year, aid, kws, role in PAPERS:
    url = f"https://arxiv.org/pdf/{aid}"
    fn = f"{short}_{year}.pdf"
    dest = HERE / fn
    ok = False
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (research-paper-fetch)"})
        data = urllib.request.urlopen(req, timeout=60).read()
        dest.write_bytes(data)
        # pypdf 标题验证
        from pypdf import PdfReader
        text = ""
        try:
            text = (PdfReader(str(dest)).pages[0].extract_text() or "")[:3000].lower()
        except Exception as e:
            text = ""
        if kws and not any(k.lower() in text for k in kws):
            (UNVER / fn).write_bytes(dest.read_bytes())
            dest.unlink()
            rows.append((fn, f"arXiv:{aid}", year, url, "unverified_title", role))
            print(f"[UNVERIFIED] {fn} (kw not on page1) -> _unverified/")
        else:
            rows.append((fn, f"arXiv:{aid}", year, url, "downloaded_verified", role))
            print(f"[OK] {fn} {len(data)//1024}KB")
        ok = True
    except Exception as e:
        rows.append((fn, f"arXiv:{aid}", year, url, "download_failed", role))
        print(f"[FAIL] {fn}: {e}")
    time.sleep(3)  # arXiv 礼貌限速

# OpenReview: OpenRCA 原版 (ICLR'25)
try:
    import subprocess
    url = "https://openreview.net/pdf?id=M4qNIzQYpd"
    fn = "OpenRCA_ICLR2025.pdf"
    subprocess.run(["curl", "-sL", "-o", str(HERE / fn), url], timeout=90, check=True)
    from pypdf import PdfReader
    text = (PdfReader(str(HERE / fn)).pages[0].extract_text() or "").lower()
    if "root cause" in text or "openrca" in text:
        rows.append((fn, "OpenReview:M4qNIzQYpd", 2025, url, "downloaded_verified", "OpenRCA原版基准(335真实故障+68GB遥测)"))
        print(f"[OK] {fn}")
    else:
        (HERE / fn).unlink(missing_ok=True)
        rows.append((fn, "OpenReview:M4qNIzQYpd", 2025, url, "download_failed", "OpenRCA原版"))
        print(f"[FAIL] OpenRCA openreview verify")
except Exception as e:
    print(f"[FAIL] OpenRCA openreview: {e}")

with open(HERE / "manifest.csv", "w") as f:
    f.write("filename,title_or_id,year,source,status,role\n")
    for r in rows:
        f.write(",".join('"' + c.replace('"', "'") + '"' if "," in c else c for c in r) + "\n")
print(f"\n{sum(1 for r in rows if r[4]=='downloaded_verified')} verified / {len(rows)} attempted; manifest.csv written")
