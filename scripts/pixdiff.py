# -*- coding: utf-8 -*-
"""像素级图纸比对：判定“两张图是否为同一张”“是否大幅套用”“是否张冠李戴”。

背景：中国施工图常见“说明类图纸套用他单体”“原始建筑平面图实为平面图副本”。
这类问题的客观证据就是像素差异比例——差异 <1% 基本可判为同一张图。

用法：
    # 1) 比对两张图（按路径片段定位，取第 1 页）
    python pixdiff.py "某分册\\X-01" "某分册\\Y-01"

    # 2) 指定页 / 只比对图签区（右侧 18% 宽度）
    python pixdiff.py "<A片段>" "<B片段>" --page 2
    python pixdiff.py "<A片段>" "<B片段>" --title

    # 3) 批量：对一批图纸两两比对，列出高度相似对，并输出报表
    python pixdiff.py --all "某分册" --min-sim 95 --report report.md --csv report.csv

性能设计：
    · numpy 向量化差异计算（无 numpy 时自动退化为纯 Python，略慢）
    · 页面位图**只渲染一次**并缓存（批量模式下把 O(N²) 次渲染降为 O(N) 次）
    · 两级筛选：先比 64×64 缩略图，明显不同的直接跳过，只对候选对做全分辨率比对
    · 渲染阶段可选多线程并行（--jobs）
"""
from __future__ import annotations

import os
import re
import sys
import csv
import time
import itertools
from concurrent.futures import ThreadPoolExecutor

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import cfg  # 路径配置见 common.py / config.json

import pymupdf

try:
    import numpy as np
    HAS_NUMPY = True
except Exception:
    np = None
    HAS_NUMPY = False

ROOT = cfg.drawing_root
ZOOM = 1.5          # 比对用渲染倍率，够用且快
PIXEL_TOL = 40      # 灰度差阈值（> 此值计为差异像素）
THUMB = 64          # 一级筛选缩略图边长
THUMB_TOL = 10      # 缩略图平均灰度差阈值（超过则判为不同图，跳过全分辨率比对）
                    # 施工图大面积留白，缩略图均值差异很小；阈值取 8~12 较合适，
                    # 太松则预筛失效（全部进入全分辨率比对），太紧则漏检。可用 --thumb-tol 调整。


# ----------------------------------------------------------------------------- 定位
def locate(frag: str, limit: int = 8):
    """按路径片段定位 PDF；片段用 | 分隔表示“同时命中”。"""
    parts = [p for p in frag.split("|") if p]
    hits = []
    for dp, _dn, fn in os.walk(ROOT):
        for f in fn:
            if not f.lower().endswith(".pdf"):
                continue
            rel = os.path.relpath(os.path.join(dp, f), ROOT)
            if cfg.dup_subdir and rel.startswith(cfg.dup_subdir):
                continue
            if all(p in rel for p in parts):
                hits.append(rel)
    hits.sort()
    return hits[:limit]


# ----------------------------------------------------------------------------- 渲染与缓存
_cache: dict = {}


def render_gray(path: str, page: int = 1, title_only: bool = False, zoom: float = ZOOM):
    """渲染为灰度位图，返回 numpy 二维数组（无 numpy 时返回 (bytes,w,h)）。结果缓存。"""
    key = (path, page, title_only, zoom)
    if key in _cache:
        return _cache[key]
    full = os.path.join(ROOT, path)
    d = pymupdf.open(full)
    if page < 1 or page > d.page_count:
        d.close()
        _cache[key] = None
        return None
    pg = d[page - 1]
    r = pg.rect
    clip = pymupdf.Rect(r.x0 + r.width * 0.82, r.y0, r.x1, r.y1) if title_only else None
    pix = pg.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), clip=clip, colorspace=pymupdf.csGRAY)
    w, h = pix.width, pix.height
    if HAS_NUMPY:
        arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(h, w)
        out = arr
    else:
        out = (pix.samples, w, h)
    d.close()
    _cache[key] = out
    return out


def thumb(a):
    """把位图块平均降采样为 THUMB×THUMB，用于一级快速筛选。"""
    if HAS_NUMPY:
        h, w = a.shape
        bh, bw = max(h // THUMB, 1), max(w // THUMB, 1)
        hh, ww = bh * THUMB, bw * THUMB
        return a[:hh, :ww].reshape(THUMB, bh, THUMB, bw).mean(axis=(1, 3))
    data, w, h = a
    step = max(w // THUMB, 1)
    out = []
    for ty in range(THUMB):
        for tx in range(THUMB):
            y, x = ty * step, tx * step
            out.append(data[y * w + x])
    return out


def diff_pct(a, b, tol=PIXEL_TOL):
    """返回 (差异像素占比, 相似度)。numpy 向量化；无 numpy 时逐点（隔行隔列采样）。"""
    if a is None or b is None:
        return None
    if HAS_NUMPY:
        h = min(a.shape[0], b.shape[0])
        w = min(a.shape[1], b.shape[1])
        if h == 0 or w == 0:
            return None
        d = np.abs(a[:h, :w].astype(np.int16) - b[:h, :w].astype(np.int16))
        pct = 100.0 * float(np.count_nonzero(d > tol)) / (h * w)
    else:
        da, wa, ha = a
        db, wb, hb = b
        w, h = min(wa, wb), min(ha, hb)
        diff = tot = 0
        for y in range(0, h, 2):
            ra, rb = y * wa, y * wb
            for x in range(0, w, 2):
                tot += 1
                if abs(da[ra + x] - db[rb + x]) > tol:
                    diff += 1
        pct = 100.0 * diff / max(tot, 1)
    return pct, 100.0 - pct


def thumb_near(ta, tb):
    """一级筛选：缩略图是否足够接近（可能为同图/套用）。"""
    if ta is None or tb is None:
        return False
    if HAS_NUMPY:
        h = min(ta.shape[0], tb.shape[0])
        w = min(ta.shape[1], tb.shape[1])
        return float(np.abs(ta[:h, :w] - tb[:h, :w]).mean()) <= THUMB_TOL
    return max(abs(x - y) for x, y in zip(ta, tb)) <= THUMB_TOL


def verdict(pct: float) -> str:
    if pct < 1.0:
        return "★★ 实为同一张图（仅图签/标题不同）"
    if pct < 5.0:
        return "★ 大幅套用（少数条目被修改）"
    if pct < 15.0:
        return "部分相似（同一设计意图的不同表达）"
    return "不同图纸"


# ----------------------------------------------------------------------------- 主流程
def main(argv):
    global THUMB_TOL
    page, title_only, all_mode = 1, False, None
    min_sim, report, csvout, jobs = 95.0, None, None, 4
    frags, i = [], 0
    while i < len(argv):
        a = argv[i]
        if a == "--page":
            page = int(argv[i + 1]); i += 2; continue
        if a == "--title":
            title_only = True; i += 1; continue
        if a == "--all":
            all_mode = argv[i + 1]; i += 2; continue
        if a == "--min-sim":
            min_sim = float(argv[i + 1]); i += 2; continue
        if a == "--jobs":
            jobs = max(1, int(argv[i + 1])); i += 2; continue
        if a == "--thumb-tol":
            THUMB_TOL = float(argv[i + 1]); i += 2; continue
        if a == "--report":
            report = argv[i + 1]; i += 2; continue
        if a == "--csv":
            csvout = argv[i + 1]; i += 2; continue
        frags.append(a); i += 1

    if all_mode:
        batch(all_mode, page, title_only, min_sim, report, csvout, jobs)
        return

    if len(frags) != 2:
        print(__doc__)
        return
    A, B = locate(frags[0]), locate(frags[1])
    if not A or not B:
        print("未命中：%s / %s" % (frags[0], frags[1]))
        return
    if len(A) > 1 or len(B) > 1:
        print("提示：片段命中多张，取第一张。")
    a, b = A[0], B[0]
    r = diff_pct(render_gray(a, page, title_only), render_gray(b, page, title_only))
    if not r:
        print("比对失败（页码超出范围？）")
        return
    pct, sim = r
    print("A: %s" % a)
    print("B: %s" % b)
    print("第 %d 页%s" % (page, "（仅图签区）" if title_only else ""))
    print("差异像素占比：%.2f%%    相似度：%.2f%%" % (pct, sim))
    print("判定：%s" % verdict(pct))


def batch(frag, page, title_only, min_sim, report, csvout, jobs):
    files = locate(frag, limit=1000)
    n = len(files)
    if n < 2:
        print("命中不足 2 张：%s" % frag)
        return
    pairs = n * (n - 1) // 2
    t0 = time.time()
    print("命中 %d 张图纸，待比对 %d 对（第 %d 页%s）" % (n, pairs, page, "，仅图签区" if title_only else ""))

    # --- 1) 渲染（只渲染一次，多线程） ---
    print("渲染中（%d 线程）…" % jobs)
    with ThreadPoolExecutor(max_workers=jobs) as ex:
        list(ex.map(lambda f: render_gray(f, page, title_only), files))
    ok = [f for f in files if render_gray(f, page, title_only) is not None]
    print("渲染完成：%d/%d 张可用，用时 %.1fs" % (len(ok), n, time.time() - t0))

    # --- 2) 缩略图一级筛选 ---
    thumbs = {f: thumb(render_gray(f, page, title_only)) for f in ok}
    cand = []
    for a, b in itertools.combinations(ok, 2):
        if thumb_near(thumbs[a], thumbs[b]):
            cand.append((a, b))
    print("一级筛选（缩略图阈值 %.1f）：%d 对候选（跳过 %d 对）" % (THUMB_TOL, len(cand), pairs - len(cand)))

    # --- 3) 全分辨率比对 ---
    found = []
    for k, (a, b) in enumerate(cand, 1):
        r = diff_pct(render_gray(a, page, title_only), render_gray(b, page, title_only))
        if r and r[1] >= min_sim:
            found.append((r[0], r[1], a, b))
        if k % 500 == 0:
            print("  … %d/%d" % (k, len(cand)))
    found.sort()
    dt = time.time() - t0

    for pct, sim, a, b in found:
        print("差异 %5.2f%%  相似 %5.2f%%  %s\n            ↔ %s" % (pct, sim, a, b))
    print("\n共 %d 对相似度 ≥ %.1f%%（总用时 %.1fs）" % (len(found), min_sim, dt))

    # --- 4) 报表 ---
    if report:
        write_md(report, frag, page, title_only, min_sim, n, len(cand), found, dt)
        print("已写 Markdown 报表：%s" % report)
    if csvout:
        with open(csvout, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(["差异像素占比(%)", "相似度(%)", "判定", "图纸A", "图纸B"])
            for pct, sim, a, b in found:
                w.writerow(["%.2f" % pct, "%.2f" % sim, verdict(pct), a, b])
        print("已写 CSV：%s" % csvout)


def write_md(path, frag, page, title_only, min_sim, n, cand, found, dt):
    L = []
    L.append("# 图纸内容相似度比对报表\n")
    L.append("| 项 | 值 |\n|---|---|\n")
    L.append("| 检索范围 | `%s` |\n" % frag)
    L.append("| 页码 / 区域 | 第 %d 页%s |\n" % (page, "，仅图签区" if title_only else ""))
    L.append("| 命中图纸 | %d 张 |\n" % n)
    L.append("| 一级筛选候选对 | %d 对 |\n" % cand)
    L.append("| 高度相似对（相似度 ≥ %.1f%%） | **%d 对** |\n" % (min_sim, len(found)))
    L.append("| 用时 | %.1f s |\n" % dt)
    L.append("\n> 判定标准：差异 <1% 可判为同一张图（仅图签不同）；1%～5% 为大幅套用；"
             "5%～15% 为部分相似；>15% 为不同图纸。\n")
    L.append("\n## 相似图对明细\n\n")
    L.append("| # | 差异(%) | 相似度(%) | 判定 | 图纸 A | 图纸 B |\n|---|---|---|---|---|---|\n")
    for k, (pct, sim, a, b) in enumerate(found, 1):
        L.append("| %d | %.2f | %.2f | %s | `%s` | `%s` |\n" % (k, pct, sim, verdict(pct), a, b))
    if not found:
        L.append("| — | — | — | 未发现高度相似图对 | — | — |\n")
    open(path, "w", encoding="utf-8").write("".join(L))


if __name__ == "__main__":
    main(sys.argv[1:])
