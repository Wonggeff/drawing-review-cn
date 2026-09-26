# -*- coding: utf-8 -*-
"""Reconstruct a DWG table region: print TEXT/MTEXT entries sorted by y (desc) then x (asc)."""
import sys, os, glob, re
sys.stdout.reconfigure(encoding="utf-8")
import os, sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import cfg  # 路径配置见 common.py / config.json
D = cfg.dwgtext_dir
kw = sys.argv[1]
x0, x1, y0, y1 = [float(v) for v in sys.argv[2:6]]
# note y0 > y1 typically (y descending); accept either order
if y0 < y1:
    y0, y1 = y1, y0
p = None
for q in sorted(glob.glob(os.path.join(D, "*.txt"))):
    t = open(q, "rb").read().decode("gbk", errors="replace")
    if kw in (t.splitlines()[0] if t.splitlines() else ""):
        p = q
        break
if p is None:
    print("no file matching", kw)
    sys.exit(1)
print("### " + os.path.basename(p))
rows = []
for line in open(p, "rb").read().decode("gbk", errors="replace").splitlines():
    if not (line.startswith("TEXT|") or line.startswith("MTEXT|")):
        continue
    parts = line.split("|", 3)
    if len(parts) < 4:
        continue
    m = re.match(r"\(([-0-9.eE+]+) ([-0-9.eE+]+)", parts[2])
    if not m:
        continue
    x, y = float(m.group(1)), float(m.group(2))
    if x0 <= x <= x1 and y1 <= y <= y0:
        rows.append((y, x, parts[3].strip()))
rows.sort(key=lambda r: (-r[0], r[1]))
lasty = None
for y, x, t in rows:
    if lasty is None or abs(y - lasty) > 1.0:
        print("")
        print("--- y=%.0f" % y)
        lasty = y
    print("    x=%-12.0f %s" % (x, t[:200]))
print("rows: %d" % len(rows))
