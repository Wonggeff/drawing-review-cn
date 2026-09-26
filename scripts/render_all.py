# -*- coding: utf-8 -*-
"""Render every unique review-set PDF page to PNG for visual drawing review."""
import sys, os, json, re, hashlib, time
sys.stdout.reconfigure(encoding="utf-8")
import pymupdf

import os, sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import cfg  # 路径配置见 common.py / config.json
ROOT = cfg.drawing_root
OUT = cfg.render_dir
os.makedirs(OUT, exist_ok=True)

# nested duplicate folder to skip
DUP = cfg.dup_subdir

pdfs = []
for dp, dn, fn in os.walk(ROOT):
    for f in fn:
        if f.lower().endswith(".pdf"):
            pdfs.append(os.path.join(dp, f))
pdfs.sort()

uniq = [p for p in pdfs if DUP not in os.path.relpath(p, ROOT)]
print("all:", len(pdfs), "unique:", len(uniq), flush=True)

manifest = []
t0 = time.time()
for i, path in enumerate(uniq):
    rel = os.path.relpath(path, ROOT)
    h = hashlib.md5(rel.encode("utf-8")).hexdigest()[:12]
    safe = re.sub(r'[\\/:*?"<>|]', "_", rel.rsplit(".", 1)[0])[:80]
    try:
        doc = pymupdf.open(path)
    except Exception as e:
        manifest.append({"rel": rel, "error": str(e)})
        continue
    files = []
    for pno in range(doc.page_count):
        pg = doc[pno]
        # rotate-normalised pixmap
        zoom = 2.0
        mat = pymupdf.Matrix(zoom, zoom)
        try:
            pix = pg.get_pixmap(matrix=mat)
        except Exception as e:
            continue
        name = "%s__p%02d.png" % (h, pno + 1)
        pix.save(os.path.join(OUT, name))
        files.append(name)
    manifest.append({"rel": rel, "hash": h, "label": safe, "pages": doc.page_count, "files": files})
    doc.close()
    if (i + 1) % 25 == 0:
        el = time.time() - t0
        print("rendered %d/%d  elapsed %.0fs  eta %.0fs" % (i + 1, len(uniq), el, el / (i + 1) * (len(uniq) - i - 1)), flush=True)

json.dump(manifest, open(os.path.join(OUT, "_manifest.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("done", time.time() - t0)
