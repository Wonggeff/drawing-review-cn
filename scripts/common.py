# -*- coding: utf-8 -*-
"""drawing-review-cn 统一路径配置。

优先级（从高到低）：
  1. 环境变量 DRAWING_REVIEW_*（如 DRAWING_REVIEW_ROOT）
  2. 环境变量 DRAWING_REVIEW_CONFIG 指向的 json 文件
  3. 当前工作目录下的 config.json
  4. 本文件同级目录下的 config.json
  5. 内置默认值（相对路径）

用法：
    from common import cfg
    ROOT = cfg.drawing_root
    OUT  = cfg.render_dir

初始化配置：
    python common.py --init            # 在脚本同级目录生成 config.json
    python common.py --init --here     # 在 CWD 生成 config.json
    python common.py --show            # 打印当前生效配置与解析后绝对路径
"""
from __future__ import annotations

import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))

# key -> (默认值, 环境变量后缀, 说明)
SPEC = {
    "drawing_root": ("./drawings", "ROOT", "施工图根目录（内含各专业分册子目录）"),
    "render_dir": ("./_render", "RENDER", "图纸渲染 PNG 输出目录"),
    "extract_dir": ("./_extract", "EXTRACT", "PDF 文字层提取输出目录"),
    "dwgtext_dir": ("./_dwgtext", "DWGTEXT", "DWG 全量文字输出目录"),
    "findings_dir": ("./_findings", "FINDINGS", "各专业分册问题报告目录"),
    "ledger_dir": ("./_ledger", "LEDGER", "图纸台账输出目录"),
    "ext_dir": ("./_render_ext", "EXT", "外部 PDF（变更单/地勘附图等）渲染目录"),
    "out_dir": (".", "OUT", "交付物（清单/记录表）输出目录"),
    "dup_subdir": ("", "DUP", "需跳过的重复归档子目录名（相对 drawing_root，可留空）"),
    "main_issue_md": ("02_图纸会审问题清单.md", "MAINMD", "主件问题清单文件名（make_docs 用）"),
    "config_path": ("config.json", "CONFIG", "配置文件路径"),
    # ---- 工程信息（写入会审记录表，非路径） ----
    "project_name": ("（请填写工程名称）", "PROJECT", "工程名称"),
    "project_location": ("", "LOCATION", "建设地点"),
    "client": ("", "CLIENT", "建设单位"),
    "designer": ("", "DESIGNER", "设计单位"),
    "surveyor": ("", "SURVEYOR", "勘察单位"),
    "reviewer": ("", "REVIEWER", "施工图审查机构"),
}

# 非路径类键：不做相对路径解析
NONPATH = {"dup_subdir", "main_issue_md", "config_path",
           "project_name", "project_location", "client", "designer", "surveyor", "reviewer"}


class Config:
    def __init__(self, values: dict, source: str):
        self._v = values
        self.source = source

    # ---- 原始值 ----
    def raw(self, key: str) -> str:
        return self._v.get(key, SPEC[key][0])

    # ---- 解析为绝对路径 ----
    def path(self, key: str) -> str:
        base = os.path.dirname(os.path.abspath(self._v.get("__config_file__", os.path.join(_HERE, "config.json"))))
        v = self.raw(key)
        if not v:
            return ""
        return v if os.path.isabs(v) else os.path.normpath(os.path.join(base, v))

    # ---- 便捷属性 ----
    @property
    def drawing_root(self) -> str: return self.path("drawing_root")
    @property
    def render_dir(self) -> str: return self.path("render_dir")
    @property
    def extract_dir(self) -> str: return self.path("extract_dir")
    @property
    def dwgtext_dir(self) -> str: return self.path("dwgtext_dir")
    @property
    def findings_dir(self) -> str: return self.path("findings_dir")
    @property
    def ledger_dir(self) -> str: return self.path("ledger_dir")
    @property
    def ext_dir(self) -> str: return self.path("ext_dir")
    @property
    def out_dir(self) -> str: return self.path("out_dir")
    @property
    def dup_subdir(self) -> str: return self.raw("dup_subdir")
    @property
    def main_issue_md(self) -> str:
        return os.path.join(self.out_dir, self.raw("main_issue_md"))

    # ---- 工程信息 ----
    @property
    def project_name(self) -> str: return self.raw("project_name") or "（请填写工程名称）"
    @property
    def project_location(self) -> str: return self.raw("project_location")
    @property
    def client(self) -> str: return self.raw("client")
    @property
    def designer(self) -> str: return self.raw("designer")
    @property
    def surveyor(self) -> str: return self.raw("surveyor")
    @property
    def reviewer(self) -> str: return self.raw("reviewer")
    @property
    def render_manifest(self) -> str:
        return os.path.join(self.render_dir, "_manifest.json")
    @property
    def dwg_manifest(self) -> str:
        return os.path.join(self.dwgtext_dir, "_manifest.csv")
    @property
    def merged_csv(self) -> str:
        return os.path.join(self.findings_dir, "_merged.csv")

    def ensure_dirs(self):
        for k in ("render_dir", "extract_dir", "dwgtext_dir", "findings_dir", "ledger_dir", "ext_dir", "out_dir"):
            d = self.path(k)
            if d:
                os.makedirs(d, exist_ok=True)

    def as_dict(self) -> dict:
        return {k: self.raw(k) for k in SPEC if k != "config_path"}

    def describe(self) -> str:
        lines = ["配置来源: %s" % self.source, ""]
        keys = [k for k in self.as_dict()]
        w = max(len(k) for k in keys)
        for k in keys:
            v = self.raw(k) if k in NONPATH else self.path(k)
            lines.append("  %-*s = %s" % (w, k, v))
        extra = sorted(k for k in self._v if not k.startswith("_") and k not in SPEC)
        if extra:
            lines.append("")
            lines.append("  扩展键（自定义）:")
            for k in extra:
                lines.append("  %-*s = %s" % (w, k, self._v[k]))
        return "\n".join(lines)


def _load() -> Config:
    # 1/2) 环境变量
    env = {k: os.environ.get("DRAWING_REVIEW_" + s) for k, (_, s, _) in SPEC.items()}
    env = {k: v for k, v in env.items() if v}
    # 配置文件
    cf = os.environ.get("DRAWING_REVIEW_CONFIG")
    cands = []
    if cf:
        cands.append(cf)
    cands.append(os.path.join(os.getcwd(), "config.json"))
    cands.append(os.path.join(_HERE, "config.json"))
    data, used = {}, None
    for c in cands:
        if c and os.path.isfile(c):
            try:
                data = json.load(open(c, encoding="utf-8"))
                used = c
                break
            except Exception as e:
                print("[common] 读取 %s 失败：%s" % (c, e), file=sys.stderr)
    values = {k: SPEC[k][0] for k in SPEC}
    # 已知键与自定义键都保留：cluster_names / discipline_rules / sensitive_patterns
    # 这类扩展键不在 SPEC 里，但脚本会通过 cfg._v 读取，因此不能按 SPEC 过滤掉。
    # 以 "_" 开头的键视为配置文件里的注释，直接忽略。
    values.update({k: v for k, v in data.items() if not str(k).startswith("_")})
    values.update(env)
    if used:
        values["__config_file__"] = used
    src = []
    if used:
        src.append("配置文件 " + used)
    if env:
        src.append("环境变量 " + ",".join(sorted(env)))
    return Config(values, "; ".join(src) if src else "内置默认值")


cfg = _load()


def _init(here: bool = False):
    dst = os.path.join(os.getcwd() if here else _HERE, "config.json")
    if os.path.exists(dst):
        print("已存在，未覆盖：%s" % dst)
        return
    json.dump({k: SPEC[k][0] for k in SPEC if k != "config_path"},
              open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("已生成：%s" % dst)
    print("请修改 drawing_root 指向你的施工图根目录。")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    args = sys.argv[1:]
    if "--init" in args:
        _init("--here" in args)
    else:
        print(cfg.describe())
