# -*- coding: utf-8 -*-
"""Summarise extraction results: which drawing folders yielded text, which are image-only."""
import json, os, re
from collections import defaultdict

import os, sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import cfg  # 路径配置见 common.py / config.json
OUT = cfg.extract_dir
recs = json.load(open(os.path.join(OUT, "_index.json"), encoding="utf-8"))

# group by top-level discipline folder under 图纸 root
groups = defaultdict(lambda: {"n": 0, "chars": 0, "empty": 0, "pages": 0})
for r in recs:
    rel = r["rel"]
    parts = rel.split("\\")
    # discipline = first 1-2 components
    if len(parts) >= 2 and parts[0].startswith("1、"): 
        key = parts[0] + " / " + parts[1]
        if len(parts) >= 3 and parts[1].startswith("施工图设计文件"):
            key = parts[0] + " / " + parts[1]
    else:
        key = parts[0]
    g = groups[key]
    g["n"] += 1
    g["chars"] += r.get("chars", 0)
    g["pages"] += r.get("pages", 0)
    if r.get("chars", 0) < 50:
        g["empty"] += 1

print("%-70s %5s %6s %9s %9s" % ("group", "pdfs", "empty", "pages", "chars"))
for k in sorted(groups):
    g = groups[k]
    print("%-70s %5d %6d %9d %9d" % (k[:68], g["n"], g["empty"], g["pages"], g["chars"]))

print()
print("=== image-only sample (by folder) ===")
byfolder = defaultdict(list)
for r in recs:
    if r.get("chars", 0) < 50:
        d = os.path.dirname(r["rel"])
        byfolder[d].append(os.path.basename(r["rel"]))
for d in sorted(byfolder):
    print("%-100s %d" % (d[-98:], len(byfolder[d])))
