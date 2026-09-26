# -*- coding: utf-8 -*-
import sys, os, hashlib
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8")
import os, sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import cfg  # 路径配置见 common.py / config.json
ROOT = cfg.drawing_root
NEST = os.sep + "施工图设计汇总（审图机构盖章）" + os.sep
q = sys.argv[1] if len(sys.argv) > 1 else ""
if not q:
    print("用法：python dupscan.py <路径片段>"); sys.exit(1)
rows = []
for dp, dn, fn in os.walk(ROOT):
    for f in fn:
        if not f.lower().endswith(".pdf"):
            continue
        p = os.path.join(dp, f)
        rel = os.path.relpath(p, ROOT)
        # skip the nested duplicate "施工图设计汇总（审图机构盖章）" copy
        if "1、PDF施工图设计汇总（审图机构盖章）" + os.sep + "施工图设计汇总（审图机构盖章）" + os.sep in rel:
            continue
        parts = rel.split(os.sep)
        folder = parts[1] if len(parts) > 2 else ""
        if folder != q:
            continue
        h = hashlib.md5(open(p, "rb").read()).hexdigest()
        rows.append((rel, h, os.path.getsize(p)))
rows.sort()
g = defaultdict(list)
for rel, h, s in rows:
    g[h].append(rel)
print("files:", len(rows), " unique-content:", len(g))
for h, rs in sorted(g.items()):
    if len(rs) > 1:
        print("DUP", h[:10], "x%d" % len(rs))
        for r in rs:
            print("     ", r.split(os.sep)[-1])
