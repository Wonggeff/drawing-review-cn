# -*- coding: utf-8 -*-
"""Produce the consolidated per-discipline issue register (03) from the merged table."""
import os, re, csv
from collections import Counter, defaultdict
sys_out = None
import os, sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import cfg  # 路径配置见 common.py / config.json
D = cfg.findings_dir
OUT = cfg.out_dir

rows = list(csv.DictReader(open(os.path.join(D, "_merged.csv"), encoding="utf-8-sig")))

def norm_cls(s):
    s = (s or "").strip()
    m = re.match(r"^([ABCD])", s)
    return m.group(1) if m else "?"

def norm_sev(s):
    s = (s or "").strip()
    for k in ("高", "中", "低"):
        if k in s:
            return k
    return "?"

for r in rows:
    r["类别N"] = norm_cls(r["类别"])
    r["严重N"] = norm_sev(r["严重程度"])

by_src = Counter(r["来源"] for r in rows)
by_cls = Counter(r["类别N"] for r in rows)
by_sev = Counter(r["严重N"] for r in rows)

# 分册代号 -> 显示名（默认专业级；可在 config.json 的 cluster_names 里改为具体单体）
SRCNAME = {
    "A01": "建筑·分册一", "A02": "建筑·分册二", "A03": "建筑·分册三", "A04": "建筑·分册四",
    "A05": "建筑·分册五", "A06": "建筑·分册六", "A07": "建筑·分册七", "A08": "建筑·分册八",
    "I01": "室内装修（一组）", "I02": "室内装修（二组）",
    "S01": "结构", "S09": "基坑支护", "M01": "给排水与电气", "M02": "暖通与智能化",
    "L01": "景观园林与亮化", "L02": "景观园林（二组）",
}
_cn = getattr(cfg, "_v", {}).get("cluster_names") if hasattr(cfg, "_v") else None
if isinstance(_cn, dict):
    SRCNAME.update(_cn)

md = []
md.append("# %s 施工图图纸会审问题明细清单（分专业）" % cfg.project_name)
md.append("")
md.append("> 本清单为《02_图纸会审问题清单.md》的配套明细，收录 14 个专业分册逐条审查结果，共 **%d 条**。" % len(rows))
md.append("> 每条均载明：图号/图名、位置（轴线／标高／房间）、问题描述、类别（A 设计错误／B 图纸矛盾／C 深度不足／D 施工建议）、严重程度（高／中／低）、建议处理措施、依据。")
md.append("> 编号规则：专业代号-序号（JZ 建筑、ZS 装修、JG 结构、JK 基坑、JD 机电、JGL 景观）。原始报告见 `_findings/` 目录。")
md.append("")
md.append("## 一、总体统计")
md.append("")
md.append("| 来源 | 审查范围 | 条数 |")
md.append("|---|---|---|")
for k in ["A01","A02","A03","A04","A05","A06","A07","I01","I02","S01","S09","M01","M02","L01"]:
    md.append("| %s | %s | %d |" % (k, SRCNAME.get(k, k), by_src.get(k, 0)))
md.append("| **合计** |  | **%d** |" % len(rows))
md.append("")
md.append("| 类别 | 条数 | ｜ | 严重程度 | 条数 |")
md.append("|---|---|---|---|---|")
md.append("| A 设计错误 | %d | ｜ | 高 | %d |" % (by_cls.get("A", 0), by_sev.get("高", 0)))
md.append("| B 图纸矛盾 | %d | ｜ | 中 | %d |" % (by_cls.get("B", 0), by_sev.get("中", 0)))
md.append("| C 深度不足 | %d | ｜ | 低 | %d |" % (by_cls.get("C", 0), by_sev.get("低", 0)))
md.append("| D 施工建议 | %d | ｜ | 未标注 | %d |" % (by_cls.get("D", 0), by_sev.get("?", 0)))
md.append("")
md.append("## 二、问题明细")
md.append("")
md.append("| 统一编号 | 专业 | 图号/图名 | 位置 | 问题描述 | 类别 | 严重程度 | 建议处理措施 | 依据 |")
md.append("|---|---|---|---|---|---|---|---|---|")

def esc(s):
    return (s or "").replace("|", "／").replace("\n", " ").strip()

for r in rows:
    md.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
        r["统一编号"], esc(r["专业"]), esc(r["图号图名"]), esc(r["位置"]), esc(r["问题描述"]),
        r["类别N"], r["严重N"], esc(r["建议处理措施"]), esc(r["依据"])))

open(os.path.join(OUT, "03_各专业问题明细清单.md"), "w", encoding="utf-8").write("\n".join(md))
print("wrote 03, rows =", len(rows))
print("类:", dict(by_cls), "严重:", dict(by_sev))
