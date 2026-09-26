# -*- coding: utf-8 -*-
"""Search the DWG text dumps (GBK-encoded) for a keyword; print matching files and lines."""
import sys, os, glob
sys.stdout.reconfigure(encoding="utf-8")
import os, sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import cfg  # 路径配置见 common.py / config.json
D = cfg.dwgtext_dir
kw = sys.argv[1]
limit = int(sys.argv[2]) if len(sys.argv) > 2 else 40
ctx = int(sys.argv[3]) if len(sys.argv) > 3 else 0
hits = 0
for p in sorted(glob.glob(os.path.join(D, "*.txt"))):
    try:
        txt = open(p, "rb").read().decode("gbk", errors="replace")
    except Exception:
        continue
    lines = txt.splitlines()
    mine = [(i, l) for i, l in enumerate(lines) if kw in l]
    if not mine:
        continue
    hits += 1
    print("### " + os.path.basename(p) + "  (" + str(len(mine)) + " hits)")
    for i, l in mine[:limit]:
        if ctx:
            for j in range(max(0, i - ctx), min(len(lines), i + ctx + 1)):
                print("   " + lines[j][:300])
            print("   ---")
        else:
            print("   " + l[:300])
    if hits > 30:
        break
print("files with hits: %d" % hits)
