# -*- coding: utf-8 -*-
"""发布前自检：扫描仓库内所有文本文件，检查是否含"不该开源"的内容。

为什么需要它：本技能来自真实项目，很容易在脚本注释、示例命令、案例文档里
残留项目名、单位名、地点、设计号、图纸编号、单体名称等。这类残留不会导致程序出错，
但会把项目信息带进公开仓库。

**本脚本不硬编码任何项目名**，敏感词从下面三处依次读取（先命中者优先，可叠加）：
  1. 命令行：python prescan.py 某某项目 某某设计院 "某某路"
  2. 本地文件 sensitive.txt（每行一个词，# 开头为注释）——**建议加入 .gitignore**
  3. config.json 的 "sensitive_patterns": ["词1", "词2"]

用法：
    python prescan.py                      # 只用 sensitive.txt / config.json
    python prescan.py 项目名 单位名        # 追加临时词
    python prescan.py --staged             # 只扫描 git 已暂存的文件（pre-commit 用）
    python prescan.py --history            # 额外扫描全部历史提交（发布公开仓库前必做）
    python prescan.py --json report.json   # 输出 JSON 报告

退出码：0 = 干净；1 = 有命中（可挂到 pre-push 钩子上）。

注意：**工作区干净不等于仓库干净**。被删掉的敏感文件仍留在旧提交里，`git push --force`
之后旧提交依旧能按 SHA 匿名读取（除非删除并重建仓库）。所以发布前务必用 `--history`。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import cfg  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)          # 仓库根 = scripts 的上级

TEXT_EXT = (".md", ".py", ".ps1", ".json", ".txt", ".yml", ".yaml", ".toml",
            ".cfg", ".ini", ".lsp", ".scr", ".sh", ".bat", ".c", ".h", ".js", ".ts")

# 扫描时跳过的文件名（本地敏感词清单、本地配置文件——它们本来就含真实信息）
# 注意：本脚本自身不跳过，否则它自己的注释/示例里残留项目名就查不出来了。
SKIP_NAMES = {"sensitive.txt", "config.json"}
# 加载敏感词时跳过的文件名
LOAD_SKIP = {"config.json"}
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", "_render",
             "_render_ext", "_dwgtext", "_extract", "_findings", "_ledger", "_tmp", "drawings"}


def load_patterns(cli_words):
    pats = list(cli_words)
    # sensitive.txt
    for cand in (os.path.join(REPO, "sensitive.txt"), os.path.join(os.getcwd(), "sensitive.txt")):
        if os.path.isfile(cand) and os.path.basename(cand) not in LOAD_SKIP:
            for line in open(cand, encoding="utf-8"):
                line = line.strip()
                if line and not line.startswith("#"):
                    pats.append(line)
            break
    # config.json
    extra = getattr(cfg, "_v", {}).get("sensitive_patterns")
    if isinstance(extra, list):
        pats.extend(str(x) for x in extra)
    # 去重保序
    seen, out = set(), []
    for p in pats:
        if p and p not in seen:
            seen.add(p)
            out.append(p)
    return out


def staged_files():
    git = git_exe()
    if not git:
        print("× 未能调用 git，改为全量扫描", file=sys.stderr)
        return None
    try:
        r = subprocess.run([git, "diff", "--cached", "--name-only"],
                           cwd=REPO, capture_output=True, text=True, timeout=30)
        if r.returncode == 0:
            return [os.path.join(REPO, p.strip()) for p in r.stdout.splitlines() if p.strip()]
    except Exception:
        pass
    print("× 未能调用 git，改为全量扫描", file=sys.stderr)
    return None


def walk_files():
    out = []
    for dp, dn, fn in os.walk(REPO):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for f in fn:
            if f in SKIP_NAMES:
                continue
            if f.lower().endswith(TEXT_EXT):
                out.append(os.path.join(dp, f))
    return out


def scan(files, patterns):
    hits = []
    for p in files:
        if not os.path.isfile(p):
            continue
        if os.path.basename(p) in SKIP_NAMES:
            continue
        try:
            text = open(p, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        lines = text.splitlines()
        for pat in patterns:
            for m in re.finditer(re.escape(pat), text):
                ln = text[:m.start()].count("\n") + 1
                hits.append({
                    "file": os.path.relpath(p, REPO).replace("\\", "/"),
                    "line": ln,
                    "pattern": pat,
                    "text": lines[ln - 1].strip()[:160] if ln <= len(lines) else "",
                })
    return hits


def git_exe():
    for git in ("git", r"D:\Program Files\Git\cmd\git.exe", r"C:\Program Files\Git\cmd\git.exe"):
        try:
            r = subprocess.run([git, "--version"], capture_output=True, text=True, timeout=30)
            if r.returncode == 0:
                return git
        except Exception:
            continue
    return None


def history_hits(patterns):
    """扫描全部 git 历史（所有提交）——工作区干净不代表历史干净。

    强推（--force）之后旧提交仍然能按 SHA 被匿名读取，因此发布前必须查历史。
    """
    git = git_exe()
    if not git:
        print("× 未找到 git，无法扫描历史", file=sys.stderr)
        return []
    try:
        revs = subprocess.run([git, "rev-list", "--all"], cwd=REPO,
                              capture_output=True, text=True, timeout=120).stdout.split()
    except Exception as e:
        print("× 读取提交列表失败：%s" % e, file=sys.stderr)
        return []
    if not revs:
        print("（仓库还没有任何提交）")
        return []
    rx = "|".join(re.escape(p) for p in patterns)
    hits = []
    print("扫描 %d 个提交的历史…\n" % len(revs))
    for rev in revs:
        try:
            r = subprocess.run([git, "grep", "-I", "-l", "-E", rx, rev], cwd=REPO,
                               capture_output=True, text=True, timeout=180)
        except Exception:
            continue
        for line in r.stdout.splitlines():
            if ":" in line:
                revname, path = line.split(":", 1)
                hits.append({"commit": revname.strip(), "file": path.strip()})
    return hits


def main():
    ap = argparse.ArgumentParser(description="发布前敏感词自检（不硬编码任何项目名）")
    ap.add_argument("words", nargs="*", help="临时追加的敏感词")
    ap.add_argument("--staged", action="store_true", help="只扫描 git 已暂存文件")
    ap.add_argument("--history", action="store_true",
                    help="额外扫描全部 git 历史提交（发布公开仓库前强烈建议加上）")
    ap.add_argument("--json", metavar="PATH", help="输出 JSON 报告")
    args = ap.parse_args()

    patterns = load_patterns(args.words)
    if not patterns:
        print("未提供任何敏感词。请用下列任一方式提供：\n")
        print("  1) python prescan.py 项目名 单位名 \"地点\"")
        print("  2) 在仓库根写 sensitive.txt（每行一个词，# 为注释），并加入 .gitignore")
        print("  3) config.json 里加 \"sensitive_patterns\": [\"词1\", \"词2\"]")
        print("\n仓库根建议的 sensitive.txt 示例：\n")
        print("  # 项目名称 / 建设单位 / 设计单位 / 勘察单位 / 审图机构 / 地点 / 设计号 / 单体名称")
        return 0

    files = staged_files() if args.staged else walk_files()
    if files is None:
        files = walk_files()
    print("扫描 %d 个文件，敏感词 %d 个…\n" % (len(files), len(patterns)))

    hits = scan(files, patterns)
    if hits:
        by_file = {}
        for h in hits:
            by_file.setdefault(h["file"], []).append(h)
        print("× 发现 %d 处命中，涉及 %d 个文件：\n" % (len(hits), len(by_file)))
        for f in sorted(by_file):
            print("· %s  (%d 处)" % (f, len(by_file[f])))
            for h in by_file[f][:12]:
                print("    L%-5d [%s] %s" % (h["line"], h["pattern"], h["text"]))
            if len(by_file[f]) > 12:
                print("    …（其余 %d 处略）" % (len(by_file[f]) - 12))
        print("\n请清理上述内容后再发布。")
    else:
        print("√ 当前文件未发现敏感内容")

    hist = history_hits(patterns) if args.history else []
    if args.history:
        if hist:
            print("\n× 历史提交中发现 %d 处（强推不会清除它们，需删除并重建仓库）：\n" % len(hist))
            for h in hist:
                print("  %s  %s" % (h["commit"][:7], h["file"]))
        else:
            print("\n√ 历史提交未发现敏感内容")

    total = len(hits) + len(hist)
    if args.json:
        json.dump({"files": hits, "history": hist},
                  open(args.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("已写报告：%s" % args.json)
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
