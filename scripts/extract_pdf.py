# -*- coding: utf-8 -*-
"""Extract text from all project PDFs into a corpus for drawing-review analysis."""
import os, sys, json, io, re
import pymupdf

import os, sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import cfg  # 路径配置见 common.py / config.json
ROOT = cfg.drawing_root
OUT = cfg.extract_dir
os.makedirs(OUT, exist_ok=True)

def safe(name):
    return re.sub(r'[\\/:*?"<>|]', "_", name)

records = []
pdfs = []
for dirpath, dirnames, filenames in os.walk(ROOT):
    for fn in filenames:
        if fn.lower().endswith(".pdf"):
            pdfs.append(os.path.join(dirpath, fn))

pdfs.sort()
print("total pdfs:", len(pdfs))

index_lines = []
for i, path in enumerate(pdfs):
    rel = os.path.relpath(path, ROOT)
    try:
        doc = pymupdf.open(path)
    except Exception as e:
        records.append({"rel": rel, "error": str(e)})
        continue
    pages = []
    for pno in range(doc.page_count):
        page = doc[pno]
        txt = page.get_text("text")
        pages.append(txt)
    total_chars = sum(len(p) for p in pages)
    rec = {
        "rel": rel,
        "pages": doc.page_count,
        "chars": total_chars,
        "size": os.path.getsize(path),
    }
    records.append(rec)
    # write individual text file
    outname = safe(rel.replace("\\", "__").rsplit(".pdf", 1)[0]) + ".txt"
    outp = os.path.join(OUT, outname)
    with open(outp, "w", encoding="utf-8") as f:
        for pno, txt in enumerate(pages):
            f.write("\n===== PAGE %d =====\n" % (pno + 1))
            f.write(txt)
    doc.close()
    index_lines.append("%s\tpages=%d\tchars=%d" % (rel, rec["pages"], rec["chars"]))
    if (i + 1) % 50 == 0:
        print("processed", i + 1, flush=True)

with open(os.path.join(OUT, "_index.json"), "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=1)
with open(os.path.join(OUT, "_index.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(index_lines))

print("done")
zero = [r for r in records if r.get("chars", 0) < 50]
print("files with almost no text (likely scanned):", len(zero))
for r in zero[:40]:
    print("  ", r.get("rel"), r.get("chars"), r.get("pages"))
