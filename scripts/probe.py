# -*- coding: utf-8 -*-
"""单张 PDF 文字层探测：判断该图能否靠文字层分析，还是必须渲染读图。

用法：
    python probe.py                               # 自动抽样（各专业分册各取 1 张）
    python probe.py "子目录/文件名.pdf" [...]      # 指定图纸（相对 drawing_root 的路径）
"""
import sys, os, random
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import cfg  # 路径配置见 common.py / config.json
import pymupdf

ROOT = cfg.drawing_root


def sample(n_per_dir=1, limit=12):
    """按两级目录抽样，便于快速了解整个图纸集的文字层情况。"""
    buckets = {}
    for dp, dn, fn in os.walk(ROOT):
        pdfs = [f for f in fn if f.lower().endswith(".pdf")]
        if not pdfs:
            continue
        rel_dir = os.path.relpath(dp, ROOT)
        key = os.sep.join(rel_dir.split(os.sep)[:2])
        buckets.setdefault(key, []).extend(os.path.join(rel_dir, f) for f in pdfs)
    picked = []
    for k in sorted(buckets):
        picked.extend(random.sample(buckets[k], min(n_per_dir, len(buckets[k]))))
    return picked[:limit]


def probe(rel):
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p):
        print("MISSING:", rel)
        return
    d = pymupdf.open(p)
    pg = d[0]
    txt = pg.get_text("text")
    print("=" * 100)
    print("FILE:", rel)
    print("pages:", d.page_count, "| text chars:", len(txt),
          "| images:", len(pg.get_images(full=True)), "| drawings:", len(pg.get_drawings()))
    if len(txt) < 50:
        print(">>> 无文字层：该图必须渲染后图像识读")
    else:
        print(txt[:1200])
    d.close()


if __name__ == "__main__":
    targets = sys.argv[1:] or sample()
    print("抽样 %d 张\n" % len(targets))
    for t in targets:
        probe(t)
