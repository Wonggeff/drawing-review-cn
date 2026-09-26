# -*- coding: utf-8 -*-
"""Build the drawing register (图纸台账) from the stamped review-set PDF inventory and
flag numbering anomalies, missing sequence numbers, duplicates and version issues."""
import sys, os, re, json, csv
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8")

import os, sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import cfg  # 路径配置见 common.py / config.json
ROOT = cfg.drawing_root
OUT = cfg.ledger_dir
os.makedirs(OUT, exist_ok=True)
DUP = cfg.dup_subdir

rows = []
for dp, dn, fn in os.walk(ROOT):
    for f in fn:
        if not f.lower().endswith(".pdf"):
            continue
        rel = os.path.relpath(os.path.join(dp, f), ROOT)
        if rel.startswith(DUP):
            continue
        rows.append(rel)
rows.sort()

# discipline detection
# 关键：按**目录名**中出现的关键词判断专业（而不是匹配某个特定平台的文件夹前缀），
# 这样无论图纸根目录结构、分册命名方式如何都能识别。
# 顺序重要：越具体的排前面（"室内装修"要早于"建筑"，"海绵"要早于"给排水"）。
DISCIPLINE_RULES = [
    ("室内装修", "室内装修"), ("精装修", "室内装修"), ("装修", "室内装修"), ("装饰", "室内装修"),
    ("基坑", "基坑支护"), ("支护", "基坑支护"),
    ("节能", "节能计算书"),
    ("智能化", "智能化"), ("弱电", "智能化"), ("自控", "智能化"),
    ("暖通", "暖通"), ("空调", "暖通"), ("通风", "暖通"),
    ("景观", "景观园林"), ("园林", "景观园林"), ("绿化", "景观园林"),
    ("海绵", "海绵城市"),
    ("给排水", "给排水"), ("给水", "给排水"), ("排水", "给排水"),
    ("电气", "电气"), ("强电", "电气"), ("照明", "电气"),
    ("结构", "结构"),
    ("建筑", "建筑"),
]

# 若你的分册命名无法被上表识别，在 config.json 里加
#   "discipline_rules": {"目录名关键词": "专业名"}
# 自定义规则优先于上表。
_extra = getattr(cfg, "_v", {}).get("discipline_rules") if hasattr(cfg, "_v") else None
if isinstance(_extra, dict):
    DISCIPLINE_RULES = sorted(_extra.items(), key=lambda kv: -len(kv[0])) + DISCIPLINE_RULES


def discipline(rel):
    """先只在目录名里找关键词（避免被文件名里的专业词误判）；找不到再退回整条路径。"""
    d = os.path.dirname(rel)
    for k, v in DISCIPLINE_RULES:
        if k in d:
            return v
    for k, v in DISCIPLINE_RULES:
        if k in rel:
            return v
    return "其他"

# extract 图号 pattern: e.g. XX-01-01, XX- 05, 01#-XX- 05, XYZ-01-01
NUM = re.compile(r"([0-9]{1,3}#)?-?([A-Z]{2,4})[-\s]*([0-9]{2})")

ledger = []
for rel in rows:
    base = os.path.basename(rel).rsplit(".pdf", 1)[0]
    d = discipline(rel)
    m = NUM.search(base)
    code = m.group(0).strip("-# ") if m else ""
    ledger.append({
        "discipline": d,
        "rel": rel,
        "file": os.path.basename(rel),
        "folder": os.path.dirname(rel),
        "code": code,
    })

with open(os.path.join(OUT, "ledger.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["discipline", "code", "file", "folder", "rel"])
    w.writeheader()
    for r in ledger:
        w.writerow({k: r[k] for k in ["discipline", "code", "file", "folder", "rel"]})

# ---- reports ----
print("=" * 100)
print("按专业统计（唯一图纸数）")
by = defaultdict(int)
for r in ledger:
    by[r["discipline"]] += 1
for k in sorted(by, key=lambda x: -by[x]):
    print("  %-12s %4d" % (k, by[k]))
print("  合计 %d" % len(ledger))

print()
print("=" * 100)
print("同一单体/分册内文件名重复（可能重复出图或版本混淆）")
seen = defaultdict(list)
for r in ledger:
    seen[r["file"]].append(r["rel"])
dups = {k: v for k, v in seen.items() if len(v) > 1}
for k in sorted(dups):
    print("  %s  x%d" % (k, len(dups[k])))
    for v in dups[k]:
        print("      " + v)
print("  重复文件名组数：%d" % len(dups))

print()
print("=" * 100)
print("同一文件夹内图号（code）重复")
byfolder = defaultdict(list)
for r in ledger:
    if r["code"]:
        byfolder[r["folder"]].append((r["code"], r["file"]))
for fol in sorted(byfolder):
    codes = defaultdict(list)
    for c, f in byfolder[fol]:
        codes[c].append(f)
    bad = {c: fs for c, fs in codes.items() if len(fs) > 1}
    if bad:
        print("  " + fol)
        for c, fs in sorted(bad.items()):
            print("      图号 %-22s -> %s" % (c, " | ".join(fs)))

print()
print("=" * 100)
print("建筑专业各单体图纸张数")
b = defaultdict(int)
for r in ledger:
    if r["discipline"] == "建筑":
        parts = r["folder"].split("\\")
        key = parts[-1] if len(parts) > 1 else r["folder"]
        b[key] += 1
for k in sorted(b):
    print("  %-50s %3d" % (k, b[k]))
