# -*- coding: utf-8 -*-
"""生成技术文章配图（示意性质，不含任何真实项目数据）。"""
import os
import sys
sys.stdout.reconfigure(encoding="utf-8")
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
os.makedirs(OUT, exist_ok=True)

FONTS = [
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\msyhbd.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
    r"C:\Windows\Fonts\simsun.ttc",
]
FB = next((f for f in FONTS if os.path.exists(f)), None)


def font(size, bold=False):
    cands = [r"C:\Windows\Fonts\msyhbd.ttc", r"C:\Windows\Fonts\simhei.ttf"] if bold else FONTS
    for f in cands:
        if os.path.exists(f):
            try:
                return ImageFont.truetype(f, size)
            except Exception:
                continue
    return ImageFont.load_default()


INK = (32, 38, 48)
MUTED = (110, 120, 135)
BLUE = (31, 78, 121)
LBLUE = (222, 235, 247)
GREEN = (46, 125, 90)
LGREEN = (226, 242, 233)
RED = (191, 54, 47)
LRED = (253, 233, 231)
AMBER = (176, 122, 20)
LAMBER = (253, 244, 222)
GREY = (238, 241, 245)


def canvas(w, h, bg=(255, 255, 255)):
    im = Image.new("RGB", (w, h), bg)
    return im, ImageDraw.Draw(im)


def rrect(d, box, fill=None, outline=None, r=10, width=2):
    d.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def ctext(d, box, text, f, fill=INK, anchor="mm"):
    d.text(((box[0] + box[2]) / 2, (box[1] + box[3]) / 2), text, font=f, fill=fill, anchor=anchor)


def arrow(d, p1, p2, color=MUTED, width=3, head=9):
    d.line([p1, p2], fill=color, width=width)
    import math
    ang = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
    for s in (-1, 1):
        a = ang + s * 2.6
        d.line([p2, (p2[0] + head * math.cos(a), p2[1] + head * math.sin(a))], fill=color, width=width)


# ---------------------------------------------------------------- 图 1：七步流程
def fig1():
    W, H = 1560, 700
    im, d = canvas(W, H)
    d.text((48, 40), "图纸会审标准化流程（七步）", font=font(34, True), fill=BLUE)
    d.text((48, 90), "drawing-review-cn · 主代理负责 ③⑤⑥⑦，专业分册并行派发子代理 ④",
           font=font(19), fill=MUTED)

    steps = [
        ("① 图纸台账", "ledger.py", "分册张数 / 重名 / 重号缺号", LBLUE, BLUE),
        ("② 取证能力", "extract_pdf · batch_dump · render_all",
         "文字层探测 / DWG 全量文字 / 渲染读图", LBLUE, BLUE),
        ("③ 基础图通读", "总说明 · 总平面 · 防火 · 防水",
         "项目级矛盾在这一步暴露", LGREEN, GREEN),
        ("④ 专业分册并行", "子代理 ×14 分册",
         "9 列统一格式输出", LGREEN, GREEN),
        ("⑤ 跨专业核查", "20 项对撞表",
         "主代理亲做，不可外包", LAMBER, AMBER),
        ("⑥ 合并分级", "merge_findings · make03",
         "统一编号 + 统计 + 分级", LAMBER, AMBER),
        ("⑦ 交付物", "make_docs",
         "清单 + 明细 + 记录表", LRED, RED),
    ]
    bw, bh = 196, 288
    gap = 14
    x0 = 44
    y0 = 190
    for i, (title, script, desc, bg, fg) in enumerate(steps):
        x = x0 + i * (bw + gap)
        rrect(d, (x, y0, x + bw, y0 + bh), fill=bg, outline=fg, r=14, width=3)
        d.ellipse((x + bw / 2 - 22, y0 + 20, x + bw / 2 + 22, y0 + 64), fill=fg)
        ctext(d, (x + bw / 2 - 22, y0 + 20, x + bw / 2 + 22, y0 + 64), str(i + 1),
              font(24, True), fill=(255, 255, 255))
        # 标题换行
        t = title.split(" ", 1)[1]
        ctext(d, (x, y0 + 74, x + bw, y0 + 122), t, font(21, True), fill=fg)
        # 脚本名换行
        words, line, lines = script.split(" · "), "", []
        for w in words:
            if len(line + w) > 15 and line:
                lines.append(line)
                line = w + " · "
            else:
                line += w + " · "
        lines.append(line.rstrip(" ·"))
        yy = y0 + 132
        for ln in lines[:3]:
            ctext(d, (x, yy, x + bw, yy + 26), ln, font(14), fill=MUTED)
            yy += 26
        # 描述换行
        yy += 4
        cur = ""
        for ch in desc:
            if len(cur) >= 12:
                ctext(d, (x, yy, x + bw, yy + 24), cur, font(15), fill=INK)
                yy += 24
                cur = ""
            cur += ch
        if cur:
            ctext(d, (x, yy, x + bw, yy + 24), cur, font(15), fill=INK)
        if i < len(steps) - 1:
            arrow(d, (x + bw + 2, y0 + bh / 2), (x + bw + gap - 2, y0 + bh / 2), color=fg, width=3)

    rrect(d, (44, 512, 1516, 652), fill=GREY, outline=(210, 216, 224), r=14, width=2)
    d.text((70, 532), "证据链要求", font=font(22, True), fill=BLUE)
    for i, t in enumerate([
        "① 图号/图名 + 部位（轴线·标高·房间）+ 具体数值与对比  ② 盖章 PDF 优先于设计院 CAD",
        "③ 关键结论在盖章 PDF 上放大复核 + DWG 文字交叉验证    ④ 张冠李戴用像素差异比例量化",
    ]):
        d.text((70, 568 + i * 32), t, font=font(18), fill=INK)
    im.save(os.path.join(OUT, "fig1-workflow.png"))
    print("fig1-workflow.png")


# ---------------------------------------------------------------- 图 2：基准标高错配
def fig2():
    W, H = 1500, 760
    im, d = canvas(W, H)
    d.text((48, 40), "跨专业对撞：装修说明的基准标高 vs 单体实际基准", font=font(32, True), fill=BLUE)
    d.text((48, 88), "同一项目各单体 ±0.000 对应绝对标高不同；装修分册说明却大面积照抄其中一个单体的数值",
           font=font(19), fill=MUTED)

    # 坐标轴
    ax_x0, ax_x1 = 150, 1400
    ax_y = 620
    lo, hi = 37.5, 42.8

    def ypos(v):
        return ax_y - (v - lo) / (hi - lo) * 400

    d.line([(ax_x0, ax_y), (ax_x1, ax_y)], fill=INK, width=2)
    for v in [38.0, 39.0, 40.0, 41.0, 42.0]:
        y = ypos(v)
        d.line([(ax_x0 - 8, y), (ax_x0, y)], fill=INK, width=2)
        d.text((ax_x0 - 16, y), "%.1f" % v, font=font(16), fill=MUTED, anchor="rm")
        d.line([(ax_x0, y), (ax_x1, y)], fill=(233, 237, 242), width=1)
    d.text((60, 240), "绝对标高\n(m)", font=font(17), fill=MUTED, anchor="lm")

    items = [("A", 38.30, 42.15), ("B", 38.30, 42.15), ("C", 39.45, 42.15),
             ("D", 40.25, 42.35), ("E", 41.55, 42.35)]
    bw = 150
    for i, (name, real, used) in enumerate(items):
        x = 220 + i * 232
        y_real, y_used = ypos(real), ypos(used)
        # 实际基准（实心）
        d.line([(x, ax_y), (x, y_real)], fill=BLUE, width=3)
        d.ellipse((x - 11, y_real - 11, x + 11, y_real + 11), fill=BLUE)
        d.text((x, y_real - 26), "%.2f" % real, font=font(17, True), fill=BLUE, anchor="mm")
        # 装修说明采用值（空心红）
        d.line([(x + 34, ax_y), (x + 34, y_used)], fill=(220, 160, 155), width=2)
        d.ellipse((x + 34 - 11, y_used - 11, x + 34 + 11, y_used + 11),
                  fill=(255, 255, 255), outline=RED, width=3)
        d.text((x + 34, y_used - 28), "%.2f" % used, font=font(17, True), fill=RED, anchor="mm")
        # 差值标注
        gap = used - real
        if gap > 0.05:
            d.text((x + 62, (y_real + y_used) / 2), "差 %.2f m" % gap,
                   font=font(18, True), fill=RED, anchor="lm")
        d.text((x + 17, ax_y + 18), "单体 %s" % name, font=font(20, True), fill=INK, anchor="mm")

    # 图例
    rrect(d, (150, 660, 1400, 726), fill=GREY, outline=(214, 220, 228), r=10, width=2)
    d.ellipse((176, 680, 196, 700), fill=BLUE)
    d.text((206, 690), "单体建施/结构图标注的实际 ±0.000", font=font(17), fill=INK, anchor="lm")
    d.ellipse((640, 680, 660, 700), fill=(255, 255, 255), outline=RED, width=3)
    d.text((670, 690), "装修分册说明「±0.00 相当于绝对标高」采用值", font=font(17), fill=INK, anchor="lm")
    d.text((1180, 690), "→ 最大错配 3.85 m", font=font(18, True), fill=RED, anchor="lm")
    im.save(os.path.join(OUT, "fig2-datum-mismatch.png"))
    print("fig2-datum-mismatch.png")


# ---------------------------------------------------------------- 图 3：像素差异判读
def fig3():
    W, H = 1500, 720
    im, d = canvas(W, H)
    d.text((48, 40), "像素差异比例作为“图纸套用 / 张冠李戴”的客观证据", font=font(32, True), fill=BLUE)
    d.text((48, 88), "pixdiff.py：灰度差 > 阈值的像素占比；差异 <1% 基本可判为同一张图（仅图签不同）",
           font=font(19), fill=MUTED)

    bx0, bx1 = 620, 1190
    rows = [
        ("装修材料表 A 对比 B", 0.16, "实为同一张图", LRED, RED),
        ("装修说明 A 对比 B", 0.27, "实为同一张图", LRED, RED),
        ("平面图 对比 原始建筑平面图", 0.70, "实为同一张图", LRED, RED),
        ("说明 对比 构造做法表（同单体）", 3.9, "大幅套用", LAMBER, AMBER),
        ("不同单体同类图纸", 23.9, "不同图纸", LGREEN, GREEN),
    ]
    y = 170
    mx = 30.0
    for name, v, verdict, bg, fg in rows:
        rrect(d, (60, y, 1440, y + 74), fill=bg, outline=fg, r=10, width=2)
        d.text((84, y + 37), name, font=font(19), fill=INK, anchor="lm")
        w = (bx1 - bx0) * min(v, mx) / mx
        d.rectangle((bx0, y + 22, bx0 + max(w, 4), y + 52), fill=fg)
        d.text((bx0 + max(w, 4) + 14, y + 37), "%.2f%%" % v, font=font(18, True), fill=fg, anchor="lm")
        d.text((1400, y + 37), verdict, font=font(19, True), fill=fg, anchor="rm")
        y += 88

    # 阈值线
    for v, lab in [(1.0, "1%"), (5.0, "5%"), (15.0, "15%")]:
        x = bx0 + (bx1 - bx0) * v / mx
        d.line([(x, 150), (x, y - 20)], fill=(120, 130, 145), width=2)
        d.text((x, 136), lab, font=font(15), fill=MUTED, anchor="mm")
    d.text((84, y + 6), "← 差异像素占比（横轴上限 30%）", font=font(16), fill=MUTED)
    im.save(os.path.join(OUT, "fig3-pixdiff.png"))
    print("fig3-pixdiff.png")


if __name__ == "__main__":
    print("font:", FB)
    fig1()
    fig2()
    fig3()
