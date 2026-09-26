# -*- coding: utf-8 -*-
"""Dump one DWG text file to readable UTF-8 stdout by matching a substring in its DWGNAME."""
import sys, os, glob
sys.stdout.reconfigure(encoding="utf-8")
import os, sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import cfg  # 路径配置见 common.py / config.json
D = cfg.dwgtext_dir
kw = sys.argv[1]
for p in sorted(glob.glob(os.path.join(D, "*.txt"))):
    txt = open(p, "rb").read().decode("gbk", errors="replace")
    first = txt.splitlines()[0] if txt.splitlines() else ""
    if kw in first or kw in os.path.basename(p):
        print("### FILE:", os.path.basename(p), "->", first)
        print(txt)
        print("### END")
        break
else:
    print("no DWG text dump yet matching", kw)
