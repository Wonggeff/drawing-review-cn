# -*- coding: utf-8 -*-
"""Render arbitrary PDFs (outside the 图纸 tree) to PNG for inspection."""
import sys, os
sys.stdout.reconfigure(encoding="utf-8")
import pymupdf
import os, sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import cfg  # 路径配置见 common.py / config.json
OUT = cfg.ext_dir
os.makedirs(OUT, exist_ok=True)
for i, p in enumerate(sys.argv[1:]):
    d = pymupdf.open(p)
    for pno in range(d.page_count):
        pg = d[pno]
        pix = pg.get_pixmap(matrix=pymupdf.Matrix(2.2, 2.2))
        name = os.path.basename(p).rsplit(".", 1)[0] + "__p%02d.png" % (pno + 1)
        name = "".join(c if c not in '\\/:*?"<>|' else "_" for c in name)
        outp = os.path.join(OUT, name)
        pix.save(outp)
        print(outp, pix.width, "x", pix.height)
    d.close()
