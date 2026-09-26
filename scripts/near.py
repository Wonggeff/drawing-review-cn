# -*- coding: utf-8 -*-
"""Print all DWG text near a coordinate for a given drawing (window search)."""
import sys, os, glob, re
sys.stdout.reconfigure(encoding="utf-8")
import os, sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import cfg  # 路径配置见 common.py / config.json
D = cfg.dwgtext_dir
kw = sys.argv[1]
cx, cy = float(sys.argv[2]), float(sys.argv[3])
half = float(sys.argv[4]) if len(sys.argv) > 4 else 20000
for p in sorted(glob.glob(os.path.join(D, "*.txt"))):
    txt = open(p, "rb").read().decode("gbk", errors="replace")
    head = txt.splitlines()[0] if txt.splitlines() else ""
    if kw not in head:
        continue
    print("### " + head)
    rows = []
    for line in txt.splitlines():
        if not (line.startswith("TEXT|") or line.startswith("MTEXT|")):
            continue
        parts = line.split("|", 3)
        if len(parts) < 4:
            continue
        m = re.match(r"\(([-0-9.eE+]+) ([-0-9.eE+]+)", parts[2])
        if not m:
            continue
        x, y = float(m.group(1)), float(m.group(2))
        if abs(x - cx) < half and abs(y - cy) < half:
            rows.append((y, x, parts[3]))
    rows.sort(key=lambda r: (-r[0], r[1]))
    for y, x, t in rows:
        print("   y=%-10.0f x=%-12.0f %s" % (y, x, t[:200]))
    break
