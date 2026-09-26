# -*- coding: utf-8 -*-
"""List rendered drawings (rel path) filtered by substring."""
import sys, os, hashlib
sys.stdout.reconfigure(encoding="utf-8")
import os, sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import cfg  # 路径配置见 common.py / config.json
ROOT = cfg.drawing_root
OUT = cfg.render_dir
DUP = cfg.dup_subdir
q = sys.argv[1] if len(sys.argv) > 1 else ""
rows = []
for dp, dn, fn in os.walk(ROOT):
    for f in fn:
        if not f.lower().endswith(".pdf"):
            continue
        rel = os.path.relpath(os.path.join(dp, f), ROOT)
        if DUP in rel or (q and q not in rel):
            continue
        h = hashlib.md5(rel.encode("utf-8")).hexdigest()[:12]
        rows.append((rel, h))
rows.sort()
rend = set(os.listdir(OUT))
done = 0
for rel, h in rows:
    ok = any(x.startswith(h + "__") for x in rend)
    if ok:
        done += 1
    print(("OK  " if ok else "--  ") + rel)
print("rendered %d / %d in filter" % (done, len(rows)))
