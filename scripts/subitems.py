# -*- coding: utf-8 -*-
"""Extract the 子项概况 tables from the 通用设计说明 DWG dump."""
import sys, os, glob, re
sys.stdout.reconfigure(encoding="utf-8")
import os, sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import cfg  # 路径配置见 common.py / config.json
D = cfg.dwgtext_dir
p = None
for q in sorted(glob.glob(os.path.join(D, "*.txt"))):
    t = open(q, "rb").read().decode("gbk", errors="replace")
    if "通用设计说明" in (t.splitlines()[0] if t.splitlines() else ""):
        p = q; break
assert p, "not found"

items = []
for line in open(p, "rb").read().decode("gbk", errors="replace").splitlines():
    if not (line.startswith("TEXT|") or line.startswith("MTEXT|")):
        continue
    parts = line.split("|", 3)
    if len(parts) < 4:
        continue
    m = re.match(r"\(([-0-9.eE+]+) ([-0-9.eE+]+)", parts[2])
    if not m:
        continue
    items.append((float(m.group(2)), float(m.group(1)), parts[3].strip()))

hdr = re.compile(r"^(\d{1,2})#\s*([\u4e00-\u9fa5A-Za-z0-9]+)")
headers = [(y, x, t) for y, x, t in items if hdr.match(t)]
headers.sort(key=lambda r: (-r[0], r[1]))
print("=== building headers ===")
for y, x, t in headers:
    print("  y=%.0f x=%.0f  %s" % (y, x, t))

# group by column (x)
cols = {}
for y, x, t in headers:
    key = round(x / 2000)
    cols.setdefault(key, []).append((y, x, t))
print("\n=== column x-centers ===")
for k in sorted(cols):
    xs = [c[1] for c in cols[k]]
    print("  col x~%.0f  count=%d" % (sum(xs) / len(xs), len(cols[k])))

# for each column, print the table rows between that header and the next header in the same column
print("\n=== tables ===")
for k in sorted(cols):
    lst = sorted(cols[k], key=lambda r: -r[0])
    for i, (y, x, t) in enumerate(lst):
        ynext = lst[i + 1][0] if i + 1 < len(lst) else (y - 20000)
        print("\n## " + t + "   (x=%.0f)" % x)
        rows = []
        for yy, xx, tt in items:
            if ynext + 100 < yy < y - 100 and x - 400 < xx < x + 16000:
                rows.append((yy, xx, tt))
        rows.sort(key=lambda r: (-r[0], r[1]))
        lasty = None
        buf = []
        for yy, xx, tt in rows:
            if lasty is None or abs(yy - lasty) > 1.0:
                if buf: print("    " + " | ".join(buf))
                buf = [tt]
                lasty = yy
            else:
                buf.append(tt)
        if buf: print("    " + " | ".join(buf))
