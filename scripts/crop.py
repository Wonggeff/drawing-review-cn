# -*- coding: utf-8 -*-
"""Crop & re-render a region of a review-set drawing at high resolution.
Usage: python crop.py <rel-substring> <x0> <y0> <x1> <y1> [out.png] [zoom] [page]
Coordinates are fractions 0..1 of the page (left, top, right, bottom)."""
import sys, os, hashlib
sys.stdout.reconfigure(encoding="utf-8")
import pymupdf

import os, sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import cfg  # 路径配置见 common.py / config.json
ROOT = cfg.drawing_root
OUT = cfg.render_dir
DUP = cfg.dup_subdir

q = sys.argv[1]
x0, y0, x1, y1 = [float(v) for v in sys.argv[2:6]]
out = sys.argv[6] if len(sys.argv) > 6 else os.path.join(OUT, "crop.png")
zoom = float(sys.argv[7]) if len(sys.argv) > 7 else 4.0
pageno = int(sys.argv[8]) - 1 if len(sys.argv) > 8 else 0

hits = []
for dp, dn, fn in os.walk(ROOT):
    for f in fn:
        if not f.lower().endswith(".pdf"):
            continue
        rel = os.path.relpath(os.path.join(dp, f), ROOT)
        if DUP in rel or q not in rel:
            continue
        hits.append((rel, os.path.join(dp, f)))
hits.sort()
if not hits:
    print("NO MATCH for", q)
    sys.exit(1)
if len(hits) > 1:
    print("multiple matches:")
    for r, p in hits:
        print("   ", r)
rel, path = hits[0]
print("using:", rel)
doc = pymupdf.open(path)
pg = doc[pageno]
r = pg.rect
clip = pymupdf.Rect(r.x0 + x0 * r.width, r.y0 + y0 * r.height, r.x0 + x1 * r.width, r.y0 + y1 * r.height)
pix = pg.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), clip=clip)
pix.save(out)
print(out, pix.width, "x", pix.height)
doc.close()
