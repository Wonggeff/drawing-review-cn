# -*- coding: utf-8 -*-
"""Merge all per-discipline findings markdown tables into one unified review issue list."""
import sys, os, re, glob, csv
sys.stdout.reconfigure(encoding="utf-8")

import os, sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import cfg  # 路径配置见 common.py / config.json
D = cfg.findings_dir
OUT = cfg.out_dir

# 分册代号 -> (审查范围显示名, 统一编号前缀)
# 默认只给专业级名称；若想显示具体单体，在 config.json 里加：
#   "cluster_names": {"A03": "建筑（主楼·展堂）"}
DEFAULT_CLUSTER = {
    "A01": ("建筑·分册一", "JZ"), "A02": ("建筑·分册二", "JZ"),
    "A03": ("建筑·分册三", "JZ"), "A04": ("建筑·分册四", "JZ"),
    "A05": ("建筑·分册五", "JZ"), "A06": ("建筑·分册六", "JZ"),
    "A07": ("建筑·分册七", "JZ"), "A08": ("建筑·分册八", "JZ"),
    "I01": ("室内装修（一组）", "ZS"), "I02": ("室内装修（二组）", "ZS"),
    "S01": ("结构", "JG"), "S09": ("基坑支护", "JK"),
    "M01": ("给排水与电气", "JD"), "M02": ("暖通与智能化", "JD"),
    "L01": ("景观园林与亮化", "JGL"), "L02": ("景观园林（二组）", "JGL"),
}
_cn = getattr(cfg, "_v", {}).get("cluster_names") if hasattr(cfg, "_v") else None
CLUSTER = dict(DEFAULT_CLUSTER)
if isinstance(_cn, dict):
    for _k, _v in _cn.items():
        CLUSTER[_k] = (_v, CLUSTER.get(_k, (_v, "QT"))[1])

def split_row(line):
    line = line.strip()
    if not line.startswith("|"):
        return None
    cells = [c.strip() for c in line.strip("|").split("|")]
    return cells

def numkey(s):
    m = re.search(r"(\d{1,3})\s*$", s or "")
    return int(m.group(1)) if m else 0

rows_out = []
for path in sorted(glob.glob(os.path.join(D, "*.md"))):
    base = os.path.basename(path)
    if base.startswith("_"):
        continue
    key = base.split("_")[0]
    cluster, prefix = CLUSTER.get(key, (base, "QT"))
    n = 0
    for line in open(path, encoding="utf-8"):
        cells = split_row(line)
        if not cells or len(cells) < 8:
            continue
        if cells[0] in ("序号", "---", ":---") or set(cells[0]) <= set("-: "):
            continue
        # expect: 序号|专业|图号/图名|位置|问题描述|类别|严重程度|建议|依据
        # 序号可能是纯数字(1 / 01)或带前缀(A01-01 / S-01 / M02-28 / I01-64 / L01-74)
        if not re.match(r"^[A-Za-z]{0,5}\d{0,3}[-\s]?\d{1,3}$", cells[0]):
            continue
        # 类别列必须是 A/B/C/D 组合，用以排除非问题表格
        if not re.match(r"^[ABCD]\s*[/、,，]?\s*[ABCD]?", cells[5] or ""):
            continue
        n += 1
        rows_out.append({
            "来源": key,
            "审查范围": cluster,
            "原序号": cells[0],
            "专业": cells[1] if len(cells) > 1 else "",
            "图号图名": cells[2] if len(cells) > 2 else "",
            "位置": cells[3] if len(cells) > 3 else "",
            "问题描述": cells[4] if len(cells) > 4 else "",
            "类别": cells[5] if len(cells) > 5 else "",
            "严重程度": cells[6] if len(cells) > 6 else "",
            "建议处理措施": cells[7] if len(cells) > 7 else "",
            "依据": cells[8] if len(cells) > 8 else "",
        })
    print("%-28s %s -> %d rows" % (base, key, n))

# unified numbering
order = {"A01":1,"A02":2,"A03":3,"A04":4,"A05":5,"A06":6,"A07":7,"I01":8,"I02":9,
         "S01":10,"S09":11,"M01":12,"M02":13,"L01":14}
rows_out.sort(key=lambda r: (order.get(r["来源"], 99), numkey(r["原序号"])))
for i, r in enumerate(rows_out, 1):
    r["统一编号"] = "%s-%03d" % (CLUSTER.get(r["来源"], ("", "QT"))[1], i)

with open(os.path.join(OUT, "_findings", "_merged.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["统一编号","来源","审查范围","专业","图号图名","位置","问题描述","类别","严重程度","建议处理措施","依据"])
    w.writeheader()
    for r in rows_out:
        w.writerow({k: r.get(k, "") for k in w.fieldnames})

# markdown
lines = ["| 统一编号 | 专业 | 图号/图名 | 位置 | 问题描述 | 类别 | 严重程度 | 建议处理措施 | 依据 |",
         "|---|---|---|---|---|---|---|---|---|"]
for r in rows_out:
    def esc(s):
        return (s or "").replace("|", "／").replace("\n", " ").strip()
    lines.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
        r["统一编号"], esc(r["专业"]), esc(r["图号图名"]), esc(r["位置"]), esc(r["问题描述"]),
        esc(r["类别"]), esc(r["严重程度"]), esc(r["建议处理措施"]), esc(r["依据"])))
open(os.path.join(OUT, "_findings", "_merged.md"), "w", encoding="utf-8").write("\n".join(lines))

from collections import Counter
c = Counter((r["来源"], r["类别"], r["严重程度"]) for r in rows_out)
print("\n=== 统计 ===")
by_src = Counter(r["来源"] for r in rows_out)
by_cls = Counter(r["类别"].split()[0] if r["类别"] else "?" for r in rows_out)
by_sev = Counter(r["严重程度"].split()[0] if r["严重程度"] else "?" for r in rows_out)
print("按来源:", dict(by_src))
print("按类别:", dict(by_cls))
print("按严重程度:", dict(by_sev))
print("总计:", len(rows_out))
