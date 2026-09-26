# -*- coding: utf-8 -*-
"""Map a substring of a drawing's relative path to its rendered PNG path(s)."""
import sys, os, json, hashlib, re
sys.stdout.reconfigure(encoding="utf-8")
import os, sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import cfg  # 路径配置见 common.py / config.json
ROOT = cfg.drawing_root
OUT = cfg.render_dir
DUP = cfg.dup_subdir

q = sys.argv[1] if len(sys.argv) > 1 else ""
limit = int(sys.argv[2]) if len(sys.argv) > 2 else 200
only_rendered = ("--all" not in sys.argv)

rows = []
for dp, dn, fn in os.walk(ROOT):
    for f in fn:
        if not f.lower().endswith(".pdf"):
            continue
        p = os.path.join(dp, f)
        rel = os.path.relpath(p, ROOT)
        if DUP in rel:
            continue
        if q and q not in rel:
            continue
        h = hashlib.md5(rel.encode("utf-8")).hexdigest()[:12]
        try:
            import pymupdf
            d = pymupdf.open(p); npg = d.page_count; d.close()
        except Exception:
            npg = 1
        pngs = [os.path.join(OUT, "%s__p%02d.png" % (h, i + 1)) for i in range(npg)]
        rows.append((rel, pngs, npg))
rows.sort()
n = 0
for rel, pngs, npg in rows:
    n += 1
    if n > limit:
        break
    ok = [x for x in pngs if os.path.exists(x)]
    if only_rendered and not ok:
        continue
    print("REL: " + rel + ("  [pages=%d]" % npg))
    for x in ok:
        print("  " + x)
    if not ok:
        print("  (not rendered yet)")
print("matched %d drawings" % n)
