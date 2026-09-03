const pptxgen = require("/opt/homebrew/lib/node_modules/pptxgenjs");

const p = new pptxgen();
p.layout = "LAYOUT_WIDE";
p.author = "SkyResearch";
p.title = "Breakable Commitments — 论文内审";

// ---- palette: 车间夜班钢青 × 信号橙 ----
const BG_DARK = "0F1E2E", BG = "FFFFFF";
const PRIMARY = "155E75", PRIMARY_DK = "0B3D4D", TINT = "E3F0F5", TINT2 = "BFDCE6";
const ACCENT = "EA580C", TEXT = "1E293B", MUTED = "64748B", LIGHT = "F1F5F9", HAIR = "D8E2E8";
const F = "Microsoft YaHei";
const W = 13.33, H = 7.5, M = 0.6;

const bu = () => ({ code: "25B8", indent: 12 });
let pageNum = 0;

function content(title, sub) {
  pageNum += 1;
  const s = p.addSlide();
  s.background = { color: BG };
  s.addText(String(pageNum).padStart(2, "0"), { x: W - 1.15, y: 0.32, w: 0.7, h: 0.4, fontSize: 13, fontFace: F, color: TINT2, bold: true, align: "right", margin: 0 });
  s.addText(title, { x: M, y: 0.42, w: W - 2 * M - 0.8, h: 0.62, fontSize: 29, fontFace: F, color: PRIMARY_DK, bold: true, margin: 0 });
  if (sub) s.addText(sub, { x: M, y: 1.06, w: W - 2 * M, h: 0.4, fontSize: 15, fontFace: F, color: MUTED, margin: 0 });
  return s;
}
function hair(s, x, y, w) {
  s.addShape(p.shapes.LINE, { x, y, w, h: 0, line: { color: HAIR, width: 1 } });
}
function stat(s, x, y, w, big, label, color = PRIMARY_DK) {
  s.addText(big, { x, y, w, h: 1.05, fontSize: 54, fontFace: F, color, bold: true, align: "center", margin: 0 });
  s.addText(label, { x, y: y + 1.08, w, h: 0.75, fontSize: 13.5, fontFace: F, color: MUTED, align: "center", margin: 0 });
}

// ============ S1 封面（深） ============
{
  pageNum += 1;
  const s = p.addSlide();
  s.background = { color: BG_DARK };
  s.addText("ICAPS 2027 投稿内审 · 先给自己讲明白，再给别人讲明白", { x: M, y: 1.15, w: W - 2 * M, h: 0.4, fontSize: 15, fontFace: F, color: TINT2, margin: 0 });
  s.addText("可打破的承诺", { x: M, y: 1.9, w: W - 2 * M, h: 1.5, fontSize: 66, fontFace: F, color: "FFFFFF", bold: true, margin: 0 });
  s.addText([
    { text: "Breakable Commitments", options: { color: ACCENT, bold: true, breakLine: true } },
    { text: "智能车间「调度 × 多车路径」耦合系统的重规划死锁与解锁", options: { color: LIGHT } },
  ], { x: M, y: 3.55, w: W - 2 * M, h: 1.1, fontSize: 21, fontFace: F, margin: 0, paraSpaceAfter: 6 });
  hair(s, M, 5.15, W - 2 * M);
  s.addText("FJSP × MAPF · SkyEngine 全栈 · 1209 集实验 · 2026-09", { x: M, y: 5.35, w: W - 2 * M, h: 0.4, fontSize: 14, fontFace: F, color: MUTED, margin: 0 });
  s.addText("诊断死锁 → 投影抽象 → 两级定理 → 反直觉定律 → 决策策略", { x: M, y: 6.15, w: W - 2 * M, h: 0.45, fontSize: 15, fontFace: F, color: TINT2, margin: 0 });
  s.addNotes("开场白：这篇论文不是『我们算法更好』，而是回答一个被所有人跳过的问题——在真实系统里，改计划这件事本身能不能执行。一句话先记住：闭环不等于总是重规划，闭环等于保留重规划的能力，并且只在值钱时用。");
}

// ============ S2 一句话论点 ============
{
  const s = content("一句话论点", "如果只记住一页，就记这页");
  s.addText([
    { text: "闭环 ≠ 总是重规划", options: { color: PRIMARY_DK, bold: true, breakLine: true } },
    { text: "闭环 = 保留重规划的能力 + 只在它值钱时用", options: { color: ACCENT, bold: true } },
  ], { x: M, y: 2.1, w: W - 2 * M, h: 1.9, fontSize: 40, fontFace: F, align: "center", margin: 0, paraSpaceAfter: 12 });
  const cards = [
    ["53% → 99%", "修好承诺编码后\n修订激活率"],
    ["143 : 12", "扰动场景下『不动』完胜\n『总是重规划』(配对)"],
    ["1.3%", "value-aware 触发器的\n实际重规划率"],
  ];
  cards.forEach((c, i) => {
    const x = M + i * (3.94 + 0.35);
    s.addShape(p.shapes.ROUNDED_RECTANGLE, { x, y: 4.45, w: 3.94, h: 1.95, fill: { color: TINT }, rectRadius: 0.06, line: { type: "none" } });
    s.addText(c[0], { x, y: 4.7, w: 3.94, h: 0.75, fontSize: 32, fontFace: F, color: PRIMARY_DK, bold: true, align: "center", margin: 0 });
    s.addText(c[1], { x: x + 0.2, y: 5.5, w: 3.54, h: 0.8, fontSize: 13.5, fontFace: F, color: MUTED, align: "center", margin: 0 });
  });
  s.addNotes("三个数字就是全文骨架：先修好机制（99%），然后发现多数时候别用（143:12），最后学会什么时候用（1.3%）。后面每一页都是给这三个数字补证据。");
}

// ============ S3 背景系统 ============
{
  const s = content("耦合车间：三层分工，一个致命接口", "SkyEngine 全栈 —— 调度与路径在这里相遇");
  const boxes = [
    ["调度员 · CP-SAT", "工序 → 机器指派与排序\n产出：按计划时刻放行的运输单"],
    ["派单员 · Assigner", "运输任务 → 空闲 AGV\n（最近邻 / 匈牙利 / 学习式）"],
    ["导航员 · EECBS", "网格地图无碰撞路径\n21×21 迷宫 / 开阔地图"],
  ];
  boxes.forEach((b, i) => {
    const x = M + i * (3.6 + 0.55);
    s.addShape(p.shapes.ROUNDED_RECTANGLE, { x, y: 2.0, w: 3.6, h: 1.75, fill: { color: i === 0 ? PRIMARY : TINT }, rectRadius: 0.06, line: { type: "none" } });
    s.addText(b[0], { x: x + 0.2, y: 2.2, w: 3.2, h: 0.45, fontSize: 17, fontFace: F, bold: true, color: i === 0 ? "FFFFFF" : PRIMARY_DK, margin: 0 });
    s.addText(b[1], { x: x + 0.2, y: 2.72, w: 3.2, h: 0.9, fontSize: 12.5, fontFace: F, color: i === 0 ? TINT2 : MUTED, margin: 0 });
    if (i < 2) s.addText("→", { x: x + 3.62, y: 2.6, w: 0.5, h: 0.5, fontSize: 24, fontFace: F, color: TINT2, align: "center", margin: 0 });
  });
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: M, y: 4.25, w: W - 2 * M, h: 1.35, fill: { color: "FDEBE0" }, rectRadius: 0.06, line: { type: "none" } });
  s.addText([
    { text: "耦合界面：", options: { bold: true, color: ACCENT } },
    { text: "『料什么时候真正到机器口』——由拥堵的路由层决定，而调度层的计划假设它准时。两个世界的缝隙就在这一秒。", options: { color: TEXT } },
  ], { x: M + 0.3, y: 4.5, w: W - 2 * M - 0.6, h: 0.85, fontSize: 16, fontFace: F, margin: 0 });
  s.addText("FJSP：柔性作业车间调度（NP难） × MAPF：多智能体路径规划（NP难）——两半各自成熟，耦合无人能改", { x: M, y: 6.0, w: W - 2 * M, h: 0.4, fontSize: 13, fontFace: F, color: MUTED, margin: 0 });
  s.addNotes("给听众建立画面：机器负责加工，AGV 负责搬运，三层各司其职。关键不是三层多复杂，而是中间那句话——计划里的到达时间是估计的，真实的到达时间被路上的拥堵决定。整篇论文的病就藏在这个缝里。");
}

// ============ S4 问题 ============
{
  const s = content("问题：闭环喊了三年，改计划却从没被执行过", "");
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: M, y: 1.5, w: 5.9, h: 2.6, fill: { color: TINT }, rectRadius: 0.06, line: { type: "none" } });
  s.addText("文献的口号", { x: M + 0.3, y: 1.75, w: 5.3, h: 0.4, fontSize: 16, fontFace: F, bold: true, color: PRIMARY_DK, margin: 0 });
  s.addText([
    { text: "「车间系统要闭环重规划」", options: { bullet: bu(), breakLine: true } },
    { text: "最新框架（Li 2026, Sensors）：一次成型 + 执行期只修路由，闭环列为未来工作", options: { bullet: bu(), breakLine: true } },
    { text: "引擎其实留了修订 API——只是没人调用", options: { bullet: bu() } },
  ], { x: M + 0.3, y: 2.25, w: 5.3, h: 1.7, fontSize: 13.5, fontFace: F, color: TEXT, margin: 0, paraSpaceAfter: 8 });
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 6.85, y: 1.5, w: 5.9, h: 2.6, fill: { color: "FDEBE0" }, rectRadius: 0.06, line: { type: "none" } });
  s.addText("接上闭环触发器之后（SOTA 同款一次成型设定）", { x: 7.15, y: 1.75, w: 5.3, h: 0.4, fontSize: 16, fontFace: F, bold: true, color: ACCENT, margin: 0 });
  s.addText([
    { text: "在基线承诺编码上接好触发器", options: { bullet: bu(), breakLine: true } },
    { text: "试点：触发修订 → 激活 0/40 全拒", options: { bullet: bu(), breakLine: true } },
    { text: "受控对照：基线编码激活率仅 53%", options: { bullet: bu() } },
  ], { x: 7.15, y: 2.25, w: 5.3, h: 1.7, fontSize: 13.5, fontFace: F, color: TEXT, margin: 0, paraSpaceAfter: 8 });
  s.addText([
    { text: "真正的问题不是「怎么触发重规划」，而是：", options: { color: MUTED, breakLine: true } },
    { text: "在执行到一半的系统里，一次合法的改计划，为什么根本走不通？", options: { color: PRIMARY_DK, bold: true } },
  ], { x: M, y: 4.6, w: W - 2 * M, h: 1.2, fontSize: 19, fontFace: F, align: "center", margin: 0, paraSpaceAfter: 8 });
  s.addNotes("转折点：我们不是先知先觉去研究承诺——是写完触发器一跑，40 次修订全被拒，才回头挖根因。这个顺序本身就是论文叙事：先撞墙，再解剖墙。");
}

// ============ S5 病灶链条 ============
{
  const s = content("机理：不是解不动，是「说不出来」", "现行承诺编码（encode-or-veto，此类栈的标准做法）的传导链");
  const steps = [
    ["系统里有一单在途", "工序在机器口排队\n或 AGV 正载着料"],
    ["编码器卡住", "算不出后继工序的\n释放时刻 & 料源位置"],
    ["扔进黑名单", "丢入 unresolved 集合\n不尝试任何保守替代"],
    ["一票否决", "execution_ready=False\n整次修订拒绝激活"],
  ];
  steps.forEach((st, i) => {
    const x = M + i * (2.78 + 0.32);
    const last = i === 3;
    s.addShape(p.shapes.ROUNDED_RECTANGLE, { x, y: 2.1, w: 2.78, h: 1.8, fill: { color: last ? ACCENT : TINT }, rectRadius: 0.05, line: { type: "none" } });
    s.addText(String(i + 1), { x: x + 0.15, y: 2.2, w: 0.6, h: 0.4, fontSize: 20, fontFace: F, bold: true, color: last ? "FFFFFF" : TINT2, margin: 0 });
    s.addText(st[0], { x: x + 0.15, y: 2.6, w: 2.5, h: 0.45, fontSize: 15.5, fontFace: F, bold: true, color: last ? "FFFFFF" : PRIMARY_DK, margin: 0 });
    s.addText(st[1], { x: x + 0.15, y: 3.08, w: 2.5, h: 0.7, fontSize: 11.5, fontFace: F, color: last ? "FFF3EA" : MUTED, margin: 0 });
    if (i < 3) s.addText("→", { x: x + 2.78, y: 2.72, w: 0.34, h: 0.5, fontSize: 20, fontFace: F, color: TINT2, align: "center", margin: 0 });
  });
  s.addText([
    { text: "求解器（CP-SAT）根本没有机会说「不」——问题在送进它手里之前就被判了死缓。", options: { color: TEXT, bold: true, breakLine: true } },
    { text: "只要车间里有一单活儿干到一半（生产中的常态），任何改计划都会被否决。", options: { color: MUTED } },
  ], { x: M, y: 4.45, w: W - 2 * M, h: 1.1, fontSize: 17, fontFace: F, align: "center", margin: 0, paraSpaceAfter: 8 });
  s.addText("同一堵墙撞了三次：扰动修订、订单到达修订、周期刷新——全部同因（方向1/4/6实验互证）", { x: M, y: 5.95, w: W - 2 * M, h: 0.4, fontSize: 13, fontFace: F, color: MUTED, align: "center", margin: 0 });
  s.addNotes("这页是全文最重要的机制图：承诺一致性这条好规矩，被实现成了『表达不出来就全盘否决』。听众只要记住『黑名单一票否决』，后面的解法就顺理成章。");
}

// ============ S6 掩盖 ============
{
  const s = content("为什么没人发现：被『被动鲁棒性』掩盖", "一次成型的现行范式平时足够好——这正是盲区所在");
  stat(s, M + 0.6, 1.8, 3.6, "4–14%", "200 步单机停机下\n一次成型计划的退化", PRIMARY_DK);
  const rows = [
    ["孤立故障", "计划自身的松弛把停机吸收掉——不需要改计划，看起来一切正常"],
    ["加工方差 ±10%", "退化系数 D ∈ [1.00, 1.15]——依然看不见问题"],
    ["订单流（新工件）", "计划里根本没有这些活儿 → 后到工件整批饿死（试点吞吐 24.4 → 0.24）"],
  ];
  rows.forEach((r, i) => {
    const y = 1.85 + i * 1.28;
    hair(s, 5.4, y - 0.12, W - M - 5.4);
    s.addText(r[0], { x: 5.4, y, w: 2.5, h: 0.5, fontSize: 16.5, fontFace: F, bold: true, color: r[0].includes("订单") ? ACCENT : PRIMARY_DK, margin: 0 });
    s.addText(r[1], { x: 5.4, y: y + 0.42, w: W - M - 5.4, h: 0.62, fontSize: 13, fontFace: F, color: TEXT, margin: 0 });
  });
  hair(s, 5.4, 5.6, W - M - 5.4);
  s.addText("教训：只在弱扰动下测试闭环系统，永远测不出重规划通路是死的。", { x: M, y: 6.15, w: W - 2 * M, h: 0.5, fontSize: 16, fontFace: F, color: ACCENT, bold: true, align: "center", margin: 0 });
  s.addNotes("这页解释『为什么这是个新发现』：不是没人想要闭环，是系统的被动鲁棒性把病藏得严严实实——直到订单流来了一次总爆发。也顺带回答『为什么你测 200 步停机没问题还敢说机制坏了』。");
}

// ============ S7 创新1a 投影抽象 ============
{
  const s = content("创新 ①（抽象）：把承诺变成一次「投影」", "κ(p) = ( μ, l, r )：在哪台机器 · 料在哪 · 最早何时能开工");
  const cols = [
    ["精确投影", "μ, l, r 全部精确", "理想但常不可得\n（运输剩余时间未知）", TINT, PRIMARY_DK],
    ["保守投影  ← 本文", "μ, l 精确 + r̄ ≥ r", "机器可精确反查\n开工时刻只给安全下界", PRIMARY, "FFFFFF"],
    ["全有全无 ← 旧栈", "算不出 → 整体否决", "unresolved 黑名单\n一票否决激活", "FDEBE0", "B03A0A"],
  ];
  cols.forEach((c, i) => {
    const x = M + i * (3.85 + 0.28);
    const mine = i === 1;
    s.addShape(p.shapes.ROUNDED_RECTANGLE, { x, y: 2.0, w: 3.85, h: 2.75, fill: { color: c[3] }, rectRadius: 0.06, line: mine ? { color: ACCENT, width: 2 } : { type: "none" }, shadow: mine ? { type: "outer", color: "000000", blur: 8, offset: 2, angle: 45, opacity: 0.18 } : undefined });
    s.addText(c[0], { x: x + 0.25, y: 2.25, w: 3.35, h: 0.5, fontSize: 19, fontFace: F, bold: true, color: c[4], margin: 0 });
    s.addText(c[1], { x: x + 0.25, y: 2.85, w: 3.35, h: 0.45, fontSize: 14.5, fontFace: F, bold: true, color: mine ? "FFFFFF" : PRIMARY_DK, margin: 0 });
    s.addText(c[2], { x: x + 0.25, y: 3.4, w: 3.35, h: 1.1, fontSize: 12.5, fontFace: F, color: mine ? TINT2 : MUTED, margin: 0 });
  });
  s.addText([
    { text: "μ 和 l 的精确反查：排队工序 → 就在那台机器的输入队列里；在途工序 → 运输单上的目的地坐标对回机器位置。", options: { color: TEXT, breakLine: true } },
    { text: "抽象与具体引擎无关：任何「按释放时刻派单 + 物理等料」的仿真栈都适用；SkyEngine 上的落地只要 ~90 行（部署证据，非贡献本身）。", options: { color: MUTED } },
  ], { x: M, y: 5.15, w: W - 2 * M, h: 1.4, fontSize: 14.5, fontFace: F, margin: 0, paraSpaceAfter: 8 });
  s.addNotes("回应『这不就是修了个 bug 吗』：bug 只是一次全有全无投影的失败；我们的贡献是把投影补全成保守投影——一个可迁移的概念。90 行是落地轻量的证据，放在脚注位置，不再当卖点。");
}

// ============ S8 创新1b 两级定理 ============
{
  const s = content("创新 ①（定理）：两级可靠性", "罚金参数 Δpen 调错会怎样？——答案分两层");
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: M, y: 1.75, w: 5.9, h: 2.9, fill: { color: PRIMARY }, rectRadius: 0.06, line: { type: "none" } });
  s.addText("P1 · 执行安全（无条件）", { x: M + 0.3, y: 1.95, w: 5.3, h: 0.45, fontSize: 17, fontFace: F, bold: true, color: "FFFFFF", margin: 0 });
  s.addText([
    { text: "释放时刻只管「发运输单」；AGV 到了料没到会物理等待；机器只加工已到料的工序。", options: { color: TINT2, breakLine: true } },
    { text: "⇒ 无论 Δpen 设多小，都不会物料未到就开工。最坏情形：AGV 提前到取货点蹲着（浪费运力，不出事故）。", options: { color: "FFFFFF", bold: true } },
  ], { x: M + 0.3, y: 2.45, w: 5.3, h: 2.0, fontSize: 13.5, fontFace: F, margin: 0, paraSpaceAfter: 10 });
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 6.85, y: 1.75, w: 5.9, h: 2.9, fill: { color: TINT }, rectRadius: 0.06, line: { type: "none" } });
  s.addText("P2 · 计划有效（有条件）", { x: 7.15, y: 1.95, w: 5.3, h: 0.45, fontSize: 17, fontFace: F, bold: true, color: PRIMARY_DK, margin: 0 });
  s.addText([
    { text: "若剩余运输时间 ≤ Δpen 且队列 FIFO：修订计划的每个开工时刻都可行（r̄ ≥ r）。", options: { color: TEXT, breakLine: true } },
    { text: "极端拥堵击穿假设时：退回 P1 的保护——计划变陈旧，但执行仍安全。", options: { color: MUTED } },
  ], { x: 7.15, y: 2.45, w: 5.3, h: 2.0, fontSize: 13.5, fontFace: F, margin: 0, paraSpaceAfter: 10 });
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: M, y: 4.95, w: W - 2 * M, h: 1.55, fill: { color: "FDEBE0" }, rectRadius: 0.06, line: { type: "none" } });
  s.addText([
    { text: "实证压力测试：Δpen = 10（默认值的 1/20）", options: { bold: true, color: ACCENT, breakLine: true } },
    { text: "全部 episode 完工 · 修订正常激活 · 零执行违规 · makespan 优雅退化（1392–3801）——与 P1 预测逐条吻合", options: { color: TEXT } },
  ], { x: M + 0.3, y: 5.15, w: W - 2 * M - 0.6, h: 1.2, fontSize: 14.5, fontFace: F, margin: 0, paraSpaceAfter: 6 });
  s.addNotes("这页回应审稿人最锋利的问题：Δpen=200 凭什么是安全上界？答案是不需要它是——执行安全不依赖它（P1），只有计划精度依赖它（P2）。『调错参数只会让车白跑，不会让货抢跑』这句话讲给自己听一遍就懂了。");
}

// ============ S9 修复效果 ============
{
  const s = content("改进效果：数字说话（对比基线编码）", "");
  stat(s, M, 1.7, 2.9, "99%", "触发级激活率\n（2401 次触发，旧 53%）");
  stat(s, M + 3.15, 1.7, 2.9, "0", "到达修订失败\n（72 集流式全零；旧 1–18/格）");
  stat(s, M + 6.3, 1.7, 2.9, "+31%", "大车间吞吐\n（mk05，受控对照）");
  stat(s, M + 9.45, 1.7, 2.9, "10/10", "完工保证\n（最差格旧 7/10）", ACCENT);
  hair(s, M, 4.15, W - 2 * M);
  s.addText([
    { text: "同一个 90 行的编码补丁，把「改计划」从结构性不可能变成随时可执行。", options: { color: PRIMARY_DK, bold: true, breakLine: true } },
    { text: "配套交付：引擎分支 0901softcommit（opt-in 开关，旧行为逐位保留）+ 全部原始数据入库。", options: { color: MUTED } },
  ], { x: M, y: 4.55, w: W - 2 * M, h: 1.3, fontSize: 17, fontFace: F, align: "center", margin: 0, paraSpaceAfter: 10 });
  s.addNotes("注意口径：99% 是触发级激活率（E1-E3），0 是到达级修订失败（E6）——两个指标在论文里分开命名，避免被审稿人抓数字打架。");
}

// ============ S10 创新2 反定律（图） ============
{
  const s = content("创新 ②（定律）：扰动来了，最好别改计划", "1101 集主战役 · 删失按 4096 插补（消除幸存者偏差）· 配对 Wilcoxon p<0.0001");
  s.addChart(p.charts.BAR, [
    { name: "不动（static）", labels: ["S1 单次故障", "S4 强故障", "S3 持续随机"], values: [1003, 1017, 1618] },
    { name: "总是重规划（full）", labels: ["S1 单次故障", "S4 强故障", "S3 持续随机"], values: [1309, 1333, 2281] },
  ], {
    x: M, y: 1.8, w: 7.6, h: 4.3, barDir: "col",
    chartColors: [PRIMARY_DK, TINT2],
    chartArea: { fill: { color: "FFFFFF" } },
    catAxisLabelColor: MUTED, valAxisLabelColor: MUTED,
    valAxisTitle: "makespan（步，越低越好）", showValAxisTitle: true, valAxisTitleFontSize: 12, valAxisTitleColor: MUTED,
    valGridLine: { color: "EDF2F5", size: 0.5 }, catGridLine: { style: "none" },
    showValue: true, dataLabelPosition: "outEnd", dataLabelColor: TEXT, dataLabelFontSize: 11,
    showLegend: true, legendPos: "b", legendColor: MUTED, legendFontSize: 12,
  });
  s.addText([
    { text: "配对战绩", options: { bold: true, color: PRIMARY_DK, fontSize: 16, breakLine: true } },
    { text: "不动 vs 重规划", options: { color: MUTED, breakLine: true, fontSize: 12 } },
    { text: "143 : 12", options: { color: PRIMARY_DK, bold: true, fontSize: 40, breakLine: true } },
    { text: "（61 平，n=216）", options: { color: MUTED, fontSize: 12, breakLine: true } },
    { text: "扰动遗憾：1.00–1.06 vs 1.25–2.25", options: { color: TEXT, fontSize: 13, breakLine: true } },
    { text: "⇒ 松弛即鲁棒：扰动响应就该开环", options: { color: ACCENT, bold: true, fontSize: 15 } },
  ], { x: 8.6, y: 2.1, w: 4.1, h: 3.8, fontFace: F, margin: 0, paraSpaceAfter: 10 });
  s.addText("Source: E1+E2 主战役（864 集）；static=一次成型 CP-SAT，full=事件触发全域修订", { x: M, y: 6.45, w: 7.6, h: 0.35, fontSize: 11, fontFace: F, color: MUTED, margin: 0 });
  s.addNotes("反直觉的核心一页：把重规划修好之后系统地测，扰动场景下『什么都不做』全面碾压『总是重规划』——保守释放界要付 25–125% 的溢价，而松弛本来就够用。这不是负结果，是一条定律。");
}

// ============ S11 诚实修正 ============
{
  const s = content("一页科研诚信：我们撤回过自己的头条数字", "");
  s.addText("68×", { x: M, y: 1.9, w: 3.4, h: 1.3, fontSize: 72, fontFace: F, color: MUTED, bold: true, margin: 0 });
  s.addText("试点期的「吞吐恢复 68 倍」\n已从全文撤回", { x: M, y: 3.3, w: 3.4, h: 0.9, fontSize: 14, fontFace: F, color: MUTED, margin: 0 });
  s.addShape(p.shapes.LINE, { x: M + 0.3, y: 2.15, w: 2.8, h: 0.6, line: { color: ACCENT, width: 3 } });
  const steps = [
    ["试点看到", "订单流下吞吐崩塌 100 倍（24.4→0.24）"],
    ["扩容受控实验", "同引擎 legacy vs soft 对照——发现旧数字混入了激活 walker bug"],
    ["重写结论", "受控效应 = 零失败 + 完工保证 + 大车间 +23~31%；全文四处撤回 68×"],
  ];
  steps.forEach((st, i) => {
    const y = 1.95 + i * 1.35;
    hair(s, 4.7, y - 0.14, W - M - 4.7);
    s.addText(st[0], { x: 4.7, y, w: 2.6, h: 0.45, fontSize: 16, fontFace: F, bold: true, color: PRIMARY_DK, margin: 0 });
    s.addText(st[1], { x: 4.7, y: y + 0.44, w: W - M - 4.7, h: 0.6, fontSize: 13, fontFace: F, color: TEXT, margin: 0 });
  });
  hair(s, 4.7, 5.9, W - M - 4.7);
  s.addText("审稿人复现不出的数字一个都不能留——E6 受控对照（81 集）就是为这一页而生。", { x: M, y: 6.3, w: W - 2 * M, h: 0.45, fontSize: 15.5, fontFace: F, color: ACCENT, bold: true, align: "center", margin: 0 });
  s.addNotes("为什么专门留一页讲撤稿：外部评审第一轮就问了『数字打架』。与其被动解释，不如把修正过程写成方法的一部分——扩容实验的价值就在这里。给自己讲：下一次再看到惊人的倍数，先问对照干净吗。");
}

// ============ S12 创新3 myopic ============
{
  const s = content("创新 ③（策略）：value-aware 触发器", "不改算法、不训练模型——用引擎自带的确定性快照回放做反事实前滚");
  const flow = [
    ["扰动事件", "机器故障/恢复\n触发决策点"],
    ["拍快照", "全系统状态\n（含随机种子）"],
    ["双分支前滚", "A：维持现状\nB：先修订再走\n同种子各 60 步"],
    ["比进度 Δ", "完工工序数之差\nprogB − progA"],
    ["Δ > 0 才动手", "否则什么都不做\n间隔重新起算"],
  ];
  flow.forEach((f, i) => {
    const x = M + i * (2.22 + 0.26);
    const last = i === 4;
    s.addShape(p.shapes.ROUNDED_RECTANGLE, { x, y: 1.85, w: 2.22, h: 1.75, fill: { color: last ? ACCENT : TINT }, rectRadius: 0.05, line: { type: "none" } });
    s.addText(f[0], { x: x + 0.12, y: 2.0, w: 1.98, h: 0.62, fontSize: 14, fontFace: F, bold: true, color: last ? "FFFFFF" : PRIMARY_DK, margin: 0 });
    s.addText(f[1], { x: x + 0.12, y: 2.66, w: 1.98, h: 0.85, fontSize: 10.5, fontFace: F, color: last ? "FFF3EA" : MUTED, margin: 0 });
    if (i < 4) s.addText("→", { x: x + 2.2, y: 2.42, w: 0.3, h: 0.4, fontSize: 17, fontFace: F, color: TINT2, align: "center", margin: 0 });
  });
  s.addText([
    { text: "E7 · 108 集（astar 路由域）", options: { bold: true, color: PRIMARY_DK, fontSize: 15, breakLine: true } },
    { text: "453 次评估 → 仅 6 次真正重规划（1.3%）", options: { color: ACCENT, bold: true, fontSize: 19, breakLine: true } },
    { text: "插补 makespan：myopic 2876 ＜ static 3018 ＜ full 3466", options: { color: TEXT, fontSize: 14, breakLine: true } },
    { text: "配对：14:9 胜 static · 21:6 胜 full；S4 强故障下 2039 vs 2296（−11%）", options: { color: TEXT, fontSize: 13, breakLine: true } },
    { text: "「绝大多数时候同意别动，少数时刻精准出手」——双赢两个极端", options: { color: PRIMARY_DK, bold: true, fontSize: 15 } },
  ], { x: M, y: 4.05, w: W - 2 * M, h: 2.3, fontFace: F, margin: 0, paraSpaceAfter: 9 });
  s.addNotes("这页把论文闭环：定律说多数时候别重规划，myopic 用行动证明它——而且比两个极端都好。关键卖点是 1.3%：它赢不是靠多改计划，是靠改对了 6 次。");
}

// ============ S13 天眼之问 ============
{
  const s = content("自我批判：myopic 偷看未来了吗？", "外部评审第二轮的必问题——我们先用实验回答自己");
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: M, y: 1.7, w: 5.9, h: 3.1, fill: { color: TINT }, rectRadius: 0.06, line: { type: "none" } });
  s.addText("泄漏拆解", { x: M + 0.3, y: 1.9, w: 5.3, h: 0.4, fontSize: 16, fontFace: F, bold: true, color: PRIMARY_DK, margin: 0 });
  s.addText([
    { text: "分支间共享同一条未来事件带 = 合法的 CRN 方差缩减 ✓", options: { bullet: bu(), breakLine: true } },
    { text: "但真实时间线也从同一恢复点继续 → rollout 预演的正是将来真实发生的带（clairvoyant 嫌疑）", options: { bullet: bu(), breakLine: true } },
    { text: "S1/S4（确定性排程故障）：H 步内无随机性 → 零泄漏，前瞻 = MPC 式仿真预测，可部署 ✓", options: { bullet: bu(), breakLine: true } },
    { text: "S3（随机故障）：存在真泄漏 ✗", options: { bullet: bu() } },
  ], { x: M + 0.3, y: 2.35, w: 5.3, h: 2.3, fontSize: 12.5, fontFace: F, color: TEXT, margin: 0, paraSpaceAfter: 7 });
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 6.85, y: 1.7, w: 5.9, h: 3.1, fill: { color: "FDEBE0" }, rectRadius: 0.06, line: { type: "none" } });
  s.addText("补验方案（进行中）", { x: 7.15, y: 1.9, w: 5.3, h: 0.4, fontSize: 16, fontFace: F, bold: true, color: ACCENT, margin: 0 });
  s.addText([
    { text: "leak-free 变体：分支 rollout 前重播种独立未来带（分支间仍共享采样带保住 CRN），真实线走原带", options: { bullet: bu(), breakLine: true } },
    { text: "预期：S1/S4 数字不动（可部署性直接得证）；S3 若退化 → 诚实报 oracle 上界 + 可部署版两行数字", options: { bullet: bu(), breakLine: true } },
    { text: "反手加分项：量化「前瞻信息的价值」", options: { bullet: bu() } },
  ], { x: 7.15, y: 2.35, w: 5.3, h: 2.3, fontSize: 12.5, fontFace: F, color: TEXT, margin: 0, paraSpaceAfter: 7 });
  s.addText("原则：方法有效性问题用实验回答，不用修辞回答。", { x: M, y: 5.35, w: W - 2 * M, h: 0.5, fontSize: 16.5, fontFace: F, color: PRIMARY_DK, bold: true, align: "center", margin: 0 });
  s.addNotes("这页是给评审的预演：他们最锋利的一刀我们已经先捅给自己了。快照恢复了 RNG 状态是事实，S1/S4 天然干净、S3 有泄漏也是事实——leak-free 对照跑完就知道杀伤力多大。");
}

// ============ S14 路由敏感性 ============
{
  const s = content("附加发现：路由后端决定耦合系统的天花板", "E5 · 只换路由服务镜像，其余全部相同");
  stat(s, M, 1.8, 3.7, "400–800", "C++ EECBS\n（生产级基线）", PRIMARY_DK);
  stat(s, M + 4.0, 1.8, 3.7, "≈3900", "Python LaCAM\n（近活锁，4/36 报错）", "B45309");
  stat(s, M + 8.0, 1.8, 3.7, "22/36", "Python PIBT\n（直接失败）", ACCENT);
  hair(s, M, 4.35, W - 2 * M);
  s.addText([
    { text: "同一调度策略、同一协议、同一地图——滚动闭环的瓶颈是路由后端的单次重规划延迟。", options: { color: TEXT, bold: true, breakLine: true } },
    { text: "与消融研究互证：K≥4 时路由层是分层协同的结合约束（greedy+EECBS ≈ CP-SAT+EECBS）。", options: { color: MUTED } },
  ], { x: M, y: 4.7, w: W - 2 * M, h: 1.2, fontSize: 16, fontFace: F, align: "center", margin: 0, paraSpaceAfter: 8 });
  s.addNotes("这页给 MAPF 背景的评审看：我们不声称 MAPF 算法贡献，但给出一个 MAPF 社区关心的系统级事实——后端延迟差异能把耦合系统从 800 步打到 3900 步。");
}

// ============ S15 弧线与卖点 ============
{
  const s = content("论文弧线：一条完整的贡献链", "");
  const arc = ["诊断死锁", "投影抽象", "两级定理", "反直觉定律", "决策策略"];
  arc.forEach((a, i) => {
    const x = M + i * (2.26 + 0.24);
    s.addShape(p.shapes.CHEVRON, { x, y: 1.75, w: 2.26, h: 0.95, fill: { color: i === 4 ? ACCENT : PRIMARY }, line: { type: "none" } });
    s.addText(a, { x, y: 1.75, w: 2.26, h: 0.95, fontSize: 15.5, fontFace: F, bold: true, color: "FFFFFF", align: "center", valign: "middle", margin: 0 });
  });
  s.addText("三句话卖点（评审语）", { x: M, y: 3.1, w: W - 2 * M, h: 0.4, fontSize: 15, fontFace: F, bold: true, color: MUTED, margin: 0 });
  const sells = [
    ["1", "闭环重规划可以在优化开始之前就失败——因为执行承诺在残差规划模型里不可表示。"],
    ["2", "保守承诺投影让重规划可执行，且保住执行安全（两级定理）。"],
    ["3", "一旦真的可以重规划，惊人结论是：多数扰动根本不该触发它；value-aware 选择式重规划在测试域胜过两个极端。"],
  ];
  sells.forEach((t, i) => {
    const y = 3.6 + i * 0.92;
    s.addShape(p.shapes.OVAL, { x: M, y: y + 0.06, w: 0.5, h: 0.5, fill: { color: i === 2 ? ACCENT : PRIMARY }, line: { type: "none" } });
    s.addText(t[0], { x: M, y: y + 0.06, w: 0.5, h: 0.5, fontSize: 16, fontFace: F, bold: true, color: "FFFFFF", align: "center", valign: "middle", margin: 0 });
    s.addText(t[1], { x: M + 0.72, y, w: W - 2 * M - 0.72, h: 0.8, fontSize: 15.5, fontFace: F, color: TEXT, margin: 0 });
  });
  s.addText("定位：execution semantics 论文（ICAPS 主场），不是 MAPF 算法论文", { x: M, y: 6.5, w: W - 2 * M, h: 0.4, fontSize: 14, fontFace: F, color: MUTED, align: "center", margin: 0 });
  s.addNotes("五步弧线就是我们答辩的骨架：每一步都有对应章节、定理或实验相。第三句卖点是评审原话的浓缩，也是标题 Breakable Commitments 的全部含义。");
}

// ============ S16 收尾（深） ============
{
  pageNum += 1;
  const s = p.addSlide();
  s.background = { color: BG_DARK };
  s.addText("现状与打法", { x: M, y: 0.55, w: W - 2 * M, h: 0.7, fontSize: 32, fontFace: F, bold: true, color: "FFFFFF", margin: 0 });
  const cols = [
    ["已完成", ["1209 集七相实验（E1–E7）", "引擎修复分支 0901softcommit", "投影抽象 + P1/P2 双定理 + Δpen 实证", "myopic 策略：双赢两极（1.3% 重规划率）"], TINT],
    ["待办", ["leak-free 对照（S3 泄漏补验）", "ICAPS-27 官方模板换壳（预计 12 月截稿）", "英文润色 + 引用扩到 30+", "措辞降调：『测试域内优于两极』"], TINT],
  ];
  cols.forEach((c, i) => {
    const x = M + i * 6.1;
    s.addText(c[0], { x, y: 1.55, w: 5.9, h: 0.45, fontSize: 18, fontFace: F, bold: true, color: i === 0 ? "FFFFFF" : ACCENT, margin: 0 });
    s.addText(c[1].map((t, j) => ({ text: t, options: { bullet: bu(), breakLine: j < c[1].length - 1 } })), { x, y: 2.1, w: 5.7, h: 2.4, fontSize: 13.5, fontFace: F, color: c[2], margin: 0, paraSpaceAfter: 9 });
  });
  hair(s, M, 4.85, W - 2 * M);
  s.addText("ICAPS 2027 · Columbia, SC · 2027-06-27 → 07-02 · 预计截稿 2026-12 上旬", { x: M, y: 5.1, w: W - 2 * M, h: 0.45, fontSize: 15, fontFace: F, color: TINT2, margin: 0 });
  s.addText([
    { text: "外部评审模拟：7 / 6 / 5–6", options: { bold: true, color: "FFFFFF", fontSize: 17, breakLine: true } },
    { text: "「中了不意外，没中更可能是 reviewer variance，而不是论文不够格」——冲这个判断去投。", options: { color: TINT2, fontSize: 14 } },
  ], { x: M, y: 5.8, w: W - 2 * M, h: 1.1, fontFace: F, margin: 0, paraSpaceAfter: 8 });
  s.addNotes("收尾给听众行动指令：这篇论文现在的状态是『值得投主会』，剩下的三件事（leak-free、模板、润色）都是收尾工程。问一句：还有什么你想让我先补的？");
}

p.writeFile({ fileName: "/Users/bytedance/project/learn/flex_manufacture/260601天工论文准备/论文_1_闭环在线协同/icaps/BreakableCommitments_先给自己讲明白.pptx" })
  .then(() => console.log("done " + pageNum + " slides"));
