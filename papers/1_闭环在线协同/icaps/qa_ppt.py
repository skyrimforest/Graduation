"""PPT 程序化 QA: 文本溢出(按字符预算估算) + 形状出界 + 文本框重叠."""
from pptx import Presentation
from pptx.util import Emu

PATH = "/Users/bytedance/project/learn/flex_manufacture/260601天工论文准备/论文_1_闭环在线协同/icaps/BreakableCommitments_先给自己讲明白.pptx"
prs = Presentation(PATH)
EMU_IN = 914400
W, H = prs.slide_width / EMU_IN, prs.slide_height / EMU_IN
print(f"canvas {W:.2f}x{H:.2f}, slides={len(prs.slides.__iter__.__self__._sldIdLst)}")

def walk(shapes):
    for s in shapes:
        if s.shape_type == 6:
            yield from walk(s.shapes)
        elif s.has_text_frame:
            yield s

issues = 0
for idx, slide in enumerate(prs.slides, 1):
    for s in walk(slide.shapes):
        if not s.text_frame.text.strip():
            continue
        x, y = s.left / EMU_IN, s.top / EMU_IN
        w, h = s.width / EMU_IN, s.height / EMU_IN
        # 出界
        if x < -0.05 or y < -0.05 or x + w > W + 0.05 or y + h > H + 0.05:
            print(f"[S{idx}] OUT-OF-BOUNDS: '{s.text_frame.text[:18]}' box=({x:.2f},{y:.2f},{w:.2f},{h:.2f})")
            issues += 1
        # 溢出估算: CJK 全角按 1em, 拉丁按 0.55em; 行高 1.35
        for para in s.text_frame.paragraphs:
            txt = "".join(r.text for r in para.runs)
            if not txt:
                continue
            sizes = [r.font.size.pt for r in para.runs if r.font.size]
            fs = max(sizes) if sizes else 18
            em = fs / 72
            width_units = sum(1.0 if ord(c) > 0x2E80 else 0.55 for c in txt)
            text_w = width_units * em
            lines = max(1, int(text_w / max(w - 0.1, 0.3)) + (1 if text_w % max(w - 0.1, 0.3) > 0.01 else 0))
            need_h = lines * em * 1.35
            if need_h > h + 0.06:
                print(f"[S{idx}] OVERFLOW? fs={fs:.0f} lines~{lines} need={need_h:.2f} have={h:.2f}: '{txt[:24]}'")
                issues += 1
print("issues:", issues)
