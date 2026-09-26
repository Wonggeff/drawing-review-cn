# -*- coding: utf-8 -*-
"""Search all DWG text dumps and report the source drawing (from manifest)."""
import sys, os, csv, glob, re
sys.stdout.reconfigure(encoding="utf-8")
import os, sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import cfg  # 路径配置见 common.py / config.json
D = cfg.dwgtext_dir
mp = os.path.join(D, "_manifest.csv")
man = {}
if os.path.exists(mp):
    for row in csv.DictReader(open(mp, encoding="utf-8-sig")):
        man[row["key"]] = row["rel"]

kw = sys.argv[1]
limit = int(sys.argv[2]) if len(sys.argv) > 2 else 12
scope = sys.argv[3] if len(sys.argv) > 3 else ""
files = sorted(glob.glob(os.path.join(D, "*.txt")))
n = 0
for p in files:
    key = os.path.basename(p)[:-4]
    rel = man.get(key, key)
    if scope and scope not in rel:
        continue
    txt = open(p, "rb").read().decode("gbk", errors="replace")
    lines = [l for l in txt.splitlines() if kw in l]
    if not lines:
        continue
    n += 1
    print("### %s" % rel)
    for l in lines[:limit]:
        # strip coords for readability
        print("    " + l[:260])
print("== files with hits: %d ==" % n)
